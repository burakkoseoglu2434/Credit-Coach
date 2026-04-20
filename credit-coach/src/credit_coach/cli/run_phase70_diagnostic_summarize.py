from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
from PIL import Image, ImageDraw

from credit_coach.utils.run_context import load_config


@dataclass(frozen=True)
class RunInputs:
    audit_root: Path
    small_config: Path
    large_config: Path


def _safe_float(value: Any, default: float = float("nan")) -> float:
    try:
        if value is None:
            return float(default)
        if isinstance(value, (int, float, np.floating)) and not math.isnan(float(value)):
            return float(value)
        text = str(value).strip()
        if not text:
            return float(default)
        return float(text)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return int(default)
        return int(value)
    except Exception:
        return int(default)


def _infer_dataset_label(run_dir_name: str) -> str:
    # Canonical Phase 70 folder naming:
    # - S1_small_n300_seed42 / S2_small_...
    # - W1a_large_... / W2a_large_... / W3a_large_...
    name = run_dir_name.lower()
    if run_dir_name.startswith("S") or "_small_" in name:
        return "small"
    if run_dir_name.startswith("W") or "_large_" in name:
        return "large"
    raise ValueError(f"Cannot infer dataset label (small/large) from run dir: {run_dir_name}")


def _infer_wave_bucket(run_dir_name: str) -> str:
    token = run_dir_name.split("_", 1)[0].strip()
    if token.startswith("S"):
        return "S"
    if token.startswith("W1"):
        return "W1"
    if token.startswith("W2"):
        return "W2"
    if token.startswith("W3"):
        return "W3"
    return token or "unknown"


def _resolve_split_summary_path(*, base_config: Path) -> Path:
    cfg = load_config(base_config)
    splits_root = Path(cfg.get("paths", {}).get("splits", "data/splits"))
    project_root = base_config.resolve().parents[1]  # .../credit-coach/configs/<file>.yaml -> .../credit-coach
    if not splits_root.is_absolute():
        splits_root = (project_root / splits_root).resolve()
    return splits_root / "split_summary.json"


def _population_total_rows_from_split_summary(split_summary_path: Path) -> int:
    if not split_summary_path.exists():
        raise FileNotFoundError(f"Missing split_summary.json: {split_summary_path}")
    payload = json.loads(split_summary_path.read_text(encoding="utf-8"))
    train_rows = _safe_int(payload.get("train_rows"), 0)
    test_rows = _safe_int(payload.get("test_rows"), 0)
    return int(train_rows + test_rows)


def _population_total_rows_from_processed_root(processed_root: Path) -> int:
    train_path = processed_root / "train.parquet"
    test_path = processed_root / "test.parquet"
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError(f"Missing train/test parquet under: {processed_root}")
    train_rows = int(pq.ParquetFile(train_path).metadata.num_rows)
    test_rows = int(pq.ParquetFile(test_path).metadata.num_rows)
    return int(train_rows + test_rows)


def _resolve_population_total_rows(
    *,
    base_config: Path,
    fallback_config: Path | None,
) -> tuple[int, str, str]:
    """
    Returns (population_total_rows, source, reference_path).

    Deterministic priority:
    1) splits_root/split_summary.json (preferred)
    2) processed_root parquet metadata (train/test row counts)
    3) fallback_config (repeat 1->2) if provided
    """
    cfg = load_config(base_config)
    project_root = base_config.resolve().parents[1]

    split_summary_path = _resolve_split_summary_path(base_config=base_config)
    if split_summary_path.exists():
        return (
            _population_total_rows_from_split_summary(split_summary_path),
            "split_summary",
            str(split_summary_path),
        )

    processed_root = Path(cfg.get("paths", {}).get("processed_data", "data/processed"))
    if not processed_root.is_absolute():
        processed_root = (project_root / processed_root).resolve()
    try:
        return (
            _population_total_rows_from_processed_root(processed_root),
            "parquet_metadata",
            str(processed_root),
        )
    except Exception:
        pass

    if fallback_config is not None and fallback_config != base_config:
        rows, source, ref = _resolve_population_total_rows(base_config=fallback_config, fallback_config=None)
        return rows, f"fallback:{source}", ref

    return 0, "missing", str(split_summary_path)


def _write_histogram(
    values: np.ndarray,
    *,
    out_path: Path,
    bins: np.ndarray,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    counts, _ = np.histogram(values, bins=bins)
    max_count = int(counts.max()) if counts.size else 0

    width, height = 900, 520
    margin = 40
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # Axes
    draw.line((margin, height - margin, width - margin, height - margin), fill=(0, 0, 0), width=2)
    draw.line((margin, margin, margin, height - margin), fill=(0, 0, 0), width=2)

    if max_count <= 0 or counts.size == 0:
        img.save(out_path)
        return

    plot_w = width - 2 * margin
    plot_h = height - 2 * margin
    n_bins = int(counts.size)
    bar_w = max(1, int(plot_w / n_bins))
    color = (42, 110, 166)  # deterministic blue

    for idx, c in enumerate(counts.tolist()):
        x0 = margin + idx * bar_w
        x1 = min(width - margin, x0 + bar_w - 1)
        bar_h = int((c / max_count) * plot_h)
        y0 = height - margin - bar_h
        y1 = height - margin - 1
        if bar_h > 0 and x1 > x0:
            draw.rectangle((x0, y0, x1, y1), fill=color, outline=None)

    img.save(out_path)


def _write_ecdf(
    values: np.ndarray,
    *,
    out_path: Path,
    xlim: tuple[float, float] | None,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    values = np.sort(values)
    if values.size == 0:
        xs = np.asarray([0.0])
        ys = np.asarray([0.0])
    else:
        xs = values
        ys = (np.arange(1, values.size + 1) / float(values.size)).astype(float)

    width, height = 900, 520
    margin = 40
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # Axes
    draw.line((margin, height - margin, width - margin, height - margin), fill=(0, 0, 0), width=2)
    draw.line((margin, margin, margin, height - margin), fill=(0, 0, 0), width=2)

    if xlim is None:
        xmin = float(xs.min()) if xs.size else 0.0
        xmax = float(xs.max()) if xs.size else 1.0
    else:
        xmin, xmax = float(xlim[0]), float(xlim[1])
    if xmax <= xmin:
        xmax = xmin + 1e-6

    plot_w = width - 2 * margin
    plot_h = height - 2 * margin
    color = (27, 138, 90)  # deterministic green

    # Downsample deterministically if too many points (keeps file size stable).
    max_points = 4000
    if xs.size > max_points:
        idxs = np.linspace(0, xs.size - 1, max_points).astype(int)
        xs_plot = xs[idxs]
        ys_plot = ys[idxs]
    else:
        xs_plot = xs
        ys_plot = ys

    pts: list[tuple[int, int]] = []
    for x, y in zip(xs_plot.tolist(), ys_plot.tolist(), strict=False):
        if not np.isfinite(x) or not np.isfinite(y):
            continue
        x_clamped = min(max(float(x), xmin), xmax)
        y_clamped = min(max(float(y), 0.0), 1.0)
        px = int(margin + ((x_clamped - xmin) / (xmax - xmin)) * plot_w)
        py = int((height - margin) - (y_clamped * plot_h))
        pts.append((px, py))

    if len(pts) >= 2:
        draw.line(pts, fill=color, width=2, joint="curve")

    img.save(out_path)


def _quantiles(values: np.ndarray, qs: list[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {f"p{int(q*100):02d}": float("nan") for q in qs}
    out: dict[str, float] = {}
    for q in qs:
        out[f"p{int(q*100):02d}"] = float(np.quantile(arr, q))
    return out


def _load_run_metrics(run_dir: Path) -> dict[str, Any]:
    metrics_path = run_dir / "cohort_metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing cohort_metrics.json: {metrics_path}")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    return metrics


def _load_customer_columns(customer_path: Path) -> dict[str, Any]:
    if not customer_path.exists():
        raise FileNotFoundError(f"Missing customer_level_analysis.csv: {customer_path}")

    approval_gap: list[float] = []
    recoverability_score: list[float] = []
    recoverable_flag_true = 0
    recourse_full_true = 0
    valid_path_true = 0
    recoverable_full_mode_n = 0
    row_count = 0

    with customer_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_count += 1
            gap = _safe_float(row.get("approval_gap"))
            if np.isfinite(gap):
                approval_gap.append(float(gap))

            score = _safe_float(row.get("recoverability_score"))
            if np.isfinite(score):
                recoverability_score.append(float(score))

            if _safe_int(row.get("recoverable_flag"), 0) == 1:
                recoverable_flag_true += 1
            if str(row.get("recourse_mode", "")).strip() == "full":
                recourse_full_true += 1
            if _safe_int(row.get("has_valid_path_flag"), 0) == 1:
                valid_path_true += 1
            if str(row.get("primary_population", "")).strip() == "recoverable_full_mode":
                recoverable_full_mode_n += 1

    denom = float(row_count) if row_count > 0 else float("nan")
    return {
        "row_count": int(row_count),
        "approval_gap": np.asarray(approval_gap, dtype=float),
        "recoverability_score": np.asarray(recoverability_score, dtype=float),
        "recoverable_flag_rate": float(recoverable_flag_true / denom) if row_count > 0 else float("nan"),
        "recourse_mode_full_rate": float(recourse_full_true / denom) if row_count > 0 else float("nan"),
        "valid_path_exists_rate": float(valid_path_true / denom) if row_count > 0 else float("nan"),
        "recoverable_full_mode_n": int(recoverable_full_mode_n),
        "approval_gap_ge_0p20_rate": float((np.asarray(approval_gap, dtype=float) >= 0.20).mean())
        if approval_gap
        else float("nan"),
    }


def _extract_required_metrics(
    *,
    run_dir: Path,
    dataset_label: str,
    base_config_path: Path,
    fallback_config_path: Path | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    metrics = _load_run_metrics(run_dir)
    customer_path = run_dir / "customer_level_analysis.csv"
    customer_cols = _load_customer_columns(customer_path)

    sampling = metrics.get("sampling", {})
    overall = metrics.get("overall", {})
    population_metrics = metrics.get("population_metrics", {})
    global_denied = population_metrics.get("global_denied", {})
    recoverable_full = population_metrics.get("recoverable_full_mode", {})

    # Deterministic denied_rate proxy using unique denied availability + population total rows.
    # Note: if large processed roots are not prepared (e.g. audit_TEST), we fall back to small config.
    population_total_rows, population_total_rows_source, population_total_rows_ref = _resolve_population_total_rows(
        base_config=base_config_path,
        fallback_config=fallback_config_path,
    )
    unique_denied_available = _safe_int(sampling.get("unique_denied_available"), 0)
    denied_rate = float(unique_denied_available / population_total_rows) if population_total_rows > 0 else float("nan")

    approval_gap_q = _quantiles(customer_cols["approval_gap"], [0.10, 0.25, 0.50, 0.75, 0.90])

    trust = {
        "selected_invalid_winner_count": _safe_int(overall.get("selected_invalid_winner_count"), 0),
        "selected_surface_drift_count": _safe_int(overall.get("selected_surface_drift_count"), 0),
        "operator_packet_contradiction_count": _safe_int(overall.get("operator_packet_contradiction_count"), 0),
    }

    required = {
        "run_dir": str(run_dir),
        "run_name": run_dir.name,
        "dataset": dataset_label,
        "wave": _infer_wave_bucket(run_dir.name),
        "n_customers_requested": _safe_int(sampling.get("requested_n"), _safe_int(metrics.get("evaluation", {}).get("sample_size"), 0)),
        "sample_seed": _safe_int(metrics.get("evaluation", {}).get("sample_seed"), 0),
        "with_replacement": bool(sampling.get("with_replacement", False)),
        "manifest_mode": bool(sampling.get("manifest_mode", False)),
        "manifest_path": str(sampling.get("manifest_path", "")),
        "unique_denied_available": unique_denied_available,
        "population_total_rows": int(population_total_rows),
        "population_total_rows_source": str(population_total_rows_source),
        "denied_rate": float(denied_rate),
        "approval_gap_p10": float(approval_gap_q["p10"]),
        "approval_gap_p25": float(approval_gap_q["p25"]),
        "approval_gap_p50": float(approval_gap_q["p50"]),
        "approval_gap_p75": float(approval_gap_q["p75"]),
        "approval_gap_p90": float(approval_gap_q["p90"]),
        "approval_gap_ge_0p20_rate": float(customer_cols["approval_gap_ge_0p20_rate"]),
        "threshold_reach_possible_rate": _safe_float(global_denied.get("threshold_reach_possible_rate"), float("nan")),
        "recoverable_flag_rate": float(customer_cols["recoverable_flag_rate"]),
        "recourse_mode_full_rate": float(customer_cols["recourse_mode_full_rate"]),
        "valid_path_exists_rate": float(customer_cols["valid_path_exists_rate"]),
        "movement_rate_global": _safe_float(global_denied.get("movement_rate"), float("nan")),
        "movement_rate_recoverable_full": _safe_float(recoverable_full.get("movement_rate"), float("nan")),
        "recoverable_full_mode_n": int(customer_cols["recoverable_full_mode_n"]),
        **trust,
    }

    aux = {
        "population_total_rows_ref": str(population_total_rows_ref),
        "cohort_metrics_path": str(run_dir / "cohort_metrics.json"),
        "customer_level_analysis_path": str(customer_path),
    }
    return required, aux


def _wave_means(metrics_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    numeric_cols = [
        "denied_rate",
        "approval_gap_p10",
        "approval_gap_p25",
        "approval_gap_p50",
        "approval_gap_p75",
        "approval_gap_p90",
        "approval_gap_ge_0p20_rate",
        "threshold_reach_possible_rate",
        "recoverable_flag_rate",
        "recourse_mode_full_rate",
        "valid_path_exists_rate",
        "movement_rate_global",
        "movement_rate_recoverable_full",
        "recoverable_full_mode_n",
        "selected_invalid_winner_count",
        "selected_surface_drift_count",
        "operator_packet_contradiction_count",
    ]
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in metrics_rows:
        key = (str(row.get("dataset", "")), str(row.get("wave", "")))
        buckets.setdefault(key, []).append(row)

    out: list[dict[str, Any]] = []
    for (dataset, wave) in sorted(buckets.keys()):
        rows = buckets[(dataset, wave)]
        summary: dict[str, Any] = {"dataset": dataset, "wave": wave}
        for col in numeric_cols:
            vals: list[float] = []
            for r in rows:
                v = _safe_float(r.get(col))
                if np.isfinite(v):
                    vals.append(float(v))
            summary[col] = float(np.mean(vals)) if vals else float("nan")
        out.append(summary)
    return out


def _failure_mode_detector(metrics_rows: list[dict[str, Any]], wave_means: list[dict[str, Any]]) -> dict[str, Any]:
    def mean(dataset: str, wave: str, col: str) -> float:
        for row in wave_means:
            if row.get("dataset") == dataset and row.get("wave") == wave:
                return _safe_float(row.get(col))
        return float("nan")

    # D) Scaling/trust break: any trust counter > 0 in any large-data wave
    large = [r for r in metrics_rows if str(r.get("dataset")) == "large"]
    trust_cols = [
        "selected_invalid_winner_count",
        "selected_surface_drift_count",
        "operator_packet_contradiction_count",
    ]
    trust_broken = False
    if large:
        for col in trust_cols:
            if any(int(_safe_int(r.get(col), 0)) > 0 for r in large):
                trust_broken = True
                break

    small_p50 = mean("small", "S", "approval_gap_p50")
    small_p90 = mean("small", "S", "approval_gap_p90")
    small_share = mean("small", "S", "approval_gap_ge_0p20_rate")
    small_thr = mean("small", "S", "threshold_reach_possible_rate")
    small_valid = mean("small", "S", "valid_path_exists_rate")

    large_w1_p50 = mean("large", "W1", "approval_gap_p50")
    large_w1_p90 = mean("large", "W1", "approval_gap_p90")
    large_w1_share = mean("large", "W1", "approval_gap_ge_0p20_rate")
    large_w1_thr = mean("large", "W1", "threshold_reach_possible_rate")
    large_w1_valid = mean("large", "W1", "valid_path_exists_rate")

    # A) Population shift
    A = bool(
        (np.isfinite(small_p50) and np.isfinite(large_w1_p50) and (large_w1_p50 - small_p50) >= 0.05)
        or (np.isfinite(small_p90) and np.isfinite(large_w1_p90) and (large_w1_p90 - small_p90) >= 0.07)
        or (np.isfinite(small_share) and np.isfinite(large_w1_share) and (large_w1_share - small_share) >= 0.10)
    )

    # B) Recoverability collapse
    B = bool(
        (np.isfinite(small_thr) and np.isfinite(large_w1_thr) and (large_w1_thr - small_thr) <= -0.10)
        or (np.isfinite(small_thr) and np.isfinite(large_w1_thr) and small_thr > 0.0 and large_w1_thr <= 0.5 * small_thr)
    )

    # C) Planner/path failure
    C = bool(
        (np.isfinite(small_valid) and np.isfinite(large_w1_valid) and (large_w1_valid - small_valid) <= -0.10)
        or (
            np.isfinite(small_valid)
            and np.isfinite(large_w1_valid)
            and small_valid > 0.0
            and large_w1_valid <= 0.6 * small_valid
        )
    )

    # E) Movement concentration failure (only if recoverable_full_mode sample size >= 30).
    def sep(wave: str) -> float:
        rec = mean("large", wave, "movement_rate_recoverable_full")
        glb = mean("large", wave, "movement_rate_global")
        if not (np.isfinite(rec) and np.isfinite(glb)):
            return float("nan")
        return float(rec - glb)

    rec_n_w2 = mean("large", "W2", "recoverable_full_mode_n")
    rec_n_w3 = mean("large", "W3", "recoverable_full_mode_n")
    sep_w2 = sep("W2")
    sep_w3 = sep("W3")
    sep_delta_w2_w3 = float("nan")
    if np.isfinite(sep_w2) and np.isfinite(sep_w3):
        sep_delta_w2_w3 = float(sep_w3 - sep_w2)

    E = bool(
        np.isfinite(rec_n_w2)
        and np.isfinite(rec_n_w3)
        and (rec_n_w2 >= 30.0 and rec_n_w3 >= 30.0)
        and (
            (np.isfinite(sep_w2) and np.isfinite(sep_w3) and (sep_w2 <= 0.02 and sep_w3 <= 0.02))
            or (np.isfinite(sep_delta_w2_w3) and sep_delta_w2_w3 <= -0.03)
        )
    )

    return {
        "A_population_shift": A,
        "B_recoverability_collapse": B,
        "C_planner_path_failure": C,
        "D_scaling_trust_break": trust_broken,
        "E_movement_concentration_failure": E,
        "separation_w2": sep_w2,
        "separation_w3": sep_w3,
        "separation_delta_w2_w3": sep_delta_w2_w3,
    }


def _scale_instability_flags(wave_means: list[dict[str, Any]]) -> dict[str, Any]:
    # Compare large W1->W2 and W2->W3 with deterministic thresholds.
    def get(wave: str, col: str) -> float:
        for row in wave_means:
            if row.get("dataset") == "large" and row.get("wave") == wave:
                return _safe_float(row.get(col))
        return float("nan")

    def rate_instability(prev: float, curr: float) -> bool:
        if not (np.isfinite(prev) and np.isfinite(curr)):
            return False
        delta = abs(curr - prev)
        return bool(delta > max(0.03, 0.25 * abs(prev)))

    def gap_instability(prev: float, curr: float, threshold: float) -> bool:
        if not (np.isfinite(prev) and np.isfinite(curr)):
            return False
        return bool(abs(curr - prev) > threshold)

    cols = [
        "threshold_reach_possible_rate",
        "recoverable_flag_rate",
        "recourse_mode_full_rate",
        "valid_path_exists_rate",
        "movement_rate_global",
        "movement_rate_recoverable_full",
    ]
    out: dict[str, Any] = {"rate_instability": {}, "approval_gap_instability": {}}
    for (prev_wave, curr_wave) in [("W1", "W2"), ("W2", "W3")]:
        out["rate_instability"][f"{prev_wave}_to_{curr_wave}"] = {
            col: rate_instability(get(prev_wave, col), get(curr_wave, col)) for col in cols
        }
        out["approval_gap_instability"][f"{prev_wave}_to_{curr_wave}"] = {
            "approval_gap_p50": gap_instability(get(prev_wave, "approval_gap_p50"), get(curr_wave, "approval_gap_p50"), 0.03),
            "approval_gap_p90": gap_instability(get(prev_wave, "approval_gap_p90"), get(curr_wave, "approval_gap_p90"), 0.05),
        }
    return out


def _write_scale_stability_report(
    *,
    out_path: Path,
    metrics_rows: list[dict[str, Any]],
    wave_means: list[dict[str, Any]],
    detector: dict[str, Any],
    instability: dict[str, Any],
    missing_runs: list[str],
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    def fmt(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        try:
            f = float(value)
            if math.isnan(f):
                return "nan"
            return f"{f:.6f}"
        except Exception:
            return str(value)

    def _md_table(table_rows: list[dict[str, Any]], cols: list[str]) -> list[str]:
        header = "| " + " | ".join(cols) + " |"
        sep = "| " + " | ".join(["---"] * len(cols)) + " |"
        out_lines: list[str] = []
        for r in table_rows:
            cells = []
            for c in cols:
                v = r.get(c)
                if isinstance(v, str):
                    cells.append(v)
                else:
                    cells.append(fmt(v))
            out_lines.append("| " + " | ".join(cells) + " |")
        return [header, sep, *out_lines]

    lines: list[str] = []
    lines.append("# Phase 70.0 — Large-Data Diagnostic Audit (descriptive, deterministic)")
    lines.append("")

    lines.append("## Run Inventory")
    for run_name in [r["run_name"] for r in sorted(metrics_rows, key=lambda r: (r["dataset"], r["wave"], r["run_name"]))]:
        lines.append(f"- {run_name}")
    lines.append("")

    lines.append("## Wave Means (used for detectors/stability)")
    wave_view: list[dict[str, Any]] = []
    for row in wave_means:
        out = dict(row)
        out["separation"] = _safe_float(out.get("movement_rate_recoverable_full")) - _safe_float(out.get("movement_rate_global"))
        wave_view.append(out)
    lines.extend(
        _md_table(
            wave_view,
            [
                "dataset",
                "wave",
                "denied_rate",
                "approval_gap_p50",
                "approval_gap_p90",
                "approval_gap_ge_0p20_rate",
                "threshold_reach_possible_rate",
                "recoverable_flag_rate",
                "recourse_mode_full_rate",
                "valid_path_exists_rate",
                "movement_rate_global",
                "movement_rate_recoverable_full",
                "separation",
                "recoverable_full_mode_n",
            ],
        )
    )
    lines.append("")

    lines.append("## Failure-Mode Detector Flags (A–E)")
    for key in [
        "A_population_shift",
        "B_recoverability_collapse",
        "C_planner_path_failure",
        "D_scaling_trust_break",
        "E_movement_concentration_failure",
    ]:
        lines.append(f"- {key}: {fmt(detector.get(key))}")
    lines.append(f"- separation_w2: {fmt(detector.get('separation_w2'))}")
    lines.append(f"- separation_w3: {fmt(detector.get('separation_w3'))}")
    lines.append(f"- separation_delta_w2_w3: {fmt(detector.get('separation_delta_w2_w3'))}")
    lines.append("")

    lines.append("## Run Validity Notes")
    invalid_notes: list[str] = []
    for row in sorted(metrics_rows, key=lambda r: (r["dataset"], r["wave"], r["run_name"])):
        if bool(row.get("manifest_mode")):
            invalid_notes.append(
                f"- {row.get('run_name')}: manifest_mode=true (manifest_path={row.get('manifest_path')})"
            )
        # Wave protocol expects n in [200, ...] for W1, but we only flag; we do not stop.
        n_req = _safe_int(row.get("n_customers_requested"), 0)
        if str(row.get("dataset")) == "large" and str(row.get("wave")) == "W1" and n_req < 200:
            invalid_notes.append(f"- {row.get('run_name')}: requested_n={n_req} (<200) → not a Wave-1 scale run")
    if invalid_notes:
        lines.extend(invalid_notes)
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Scale Instability Flags (Large only)")
    lines.append("- rate_instability:")
    for step, mapping in instability.get("rate_instability", {}).items():
        lines.append(f"  - {step}: {mapping}")
    lines.append("- approval_gap_instability:")
    for step, mapping in instability.get("approval_gap_instability", {}).items():
        lines.append(f"  - {step}: {mapping}")
    lines.append("")

    lines.append("## Final Decision (exactly one)")
    if missing_runs:
        lines.append("- decision: NOT_YET_ADMISSIBLE (missing required runs; see notes below)")
    else:
        if bool(detector.get("D_scaling_trust_break")):
            decision = "Go to engineering hardening"
        elif bool(detector.get("E_movement_concentration_failure")):
            decision = "System cannot concentrate movement on recoverables in this population"
        elif bool(detector.get("B_recoverability_collapse")) or bool(detector.get("C_planner_path_failure")):
            decision = "System logic insufficient for new population"
        else:
            decision = "Evidence issue, not system issue"
        lines.append(f"- decision: {decision}")
    lines.append("")

    lines.append("## Notes")
    lines.append("- This report is descriptive only. It does not propose fixes, tuning, or causal claims.")
    if missing_runs:
        lines.append("- W2/W3 run klasörleri eksik olduğu için:")
        lines.append("  - scale instability değerlendirmesi incomplete")
        lines.append("  - movement concentration failure değerlendirmesi incomplete")
        lines.append("  - final 4-way decision gate not yet admissible")
        lines.append("")
        lines.append("## Next Required Runs")
        for name in missing_runs:
            lines.append(f"- {name}")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _build_trust_summary(metrics_rows: list[dict[str, Any]]) -> dict[str, Any]:
    trust_cols = ["selected_invalid_winner_count", "selected_surface_drift_count", "operator_packet_contradiction_count"]
    broken_runs: list[str] = []
    runs: list[dict[str, Any]] = []
    for row in sorted(metrics_rows, key=lambda r: (r.get("dataset", ""), r.get("wave", ""), r.get("run_name", ""))):
        counters = {col: int(_safe_int(row.get(col), 0)) for col in trust_cols}
        broken = any(value > 0 for value in counters.values())
        runs.append(
            {
                "run_name": str(row.get("run_name", "")),
                "dataset": str(row.get("dataset", "")),
                "wave": str(row.get("wave", "")),
                "run_dir": str(row.get("run_dir", "")),
                **counters,
                "trust_broken": bool(broken),
            }
        )
        if broken:
            broken_runs.append(str(row.get("run_dir", "")))

    return {
        "trust_broken": bool(len(broken_runs) > 0),
        "broken_runs": broken_runs,
        "runs": runs,
    }


def _write_distribution_plots_by_dataset_wave(
    *,
    out_dir: Path,
    dataset: str,
    wave: str,
    approval_gap_values: np.ndarray,
    recoverability_score_values: np.ndarray,
) -> None:
    # Required naming contract:
    # - approval_gap_hist_<dataset>_<wave>.png
    # - approval_gap_ecdf_<dataset>_<wave>.png
    # - recoverability_score_hist_<dataset>_<wave>.png
    plots_dir = out_dir / "distribution_plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    approval_bins = np.linspace(0.0, 0.80, 81)
    rec_bins = np.linspace(0.0, 1.00, 51)

    _write_histogram(
        approval_gap_values,
        out_path=plots_dir / f"approval_gap_hist_{dataset}_{wave}.png",
        bins=approval_bins,
    )
    _write_ecdf(
        approval_gap_values,
        out_path=plots_dir / f"approval_gap_ecdf_{dataset}_{wave}.png",
        xlim=(0.0, 0.80),
    )
    _write_histogram(
        recoverability_score_values,
        out_path=plots_dir / f"recoverability_score_hist_{dataset}_{wave}.png",
        bins=rec_bins,
    )


def _find_latest_audit_root(project_root: Path) -> Path:
    eval_root = project_root / "artifacts" / "evaluations"
    candidates = sorted(eval_root.glob("v26_phase70_large_data_diagnostic_audit_*"))
    if not candidates:
        raise FileNotFoundError(f"No audit roots found under: {eval_root}")
    return candidates[-1]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 70.0 diagnostic: aggregate per-wave metrics + plots + trust summary")
    p.add_argument(
        "--audit_root",
        type=str,
        default="",
        help="Audit root directory containing run subdirectories (default: latest matching v26_phase70_large_data_diagnostic_audit_*)",
    )
    p.add_argument("--small_config", type=str, default="configs/default.yaml", help="Base config used for small runs")
    p.add_argument("--large_config", type=str, default="configs/lendingclub_full.yaml", help="Base config used for large runs")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[3]

    def _normalize_repo_prefixed(path: Path) -> Path:
        # Accept both:
        # - artifacts/evaluations/...
        # - credit-coach/artifacts/evaluations/... (repo-root prefixed)
        parts = list(path.parts)
        if parts and parts[0] == project_root.name:
            return Path(*parts[1:])
        return path

    audit_root = Path(str(args.audit_root)).expanduser()
    if not str(args.audit_root).strip():
        audit_root = _find_latest_audit_root(project_root)
    audit_root = _normalize_repo_prefixed(audit_root)
    if not audit_root.is_absolute():
        audit_root = (project_root / audit_root).resolve()

    small_config = Path(str(args.small_config)).expanduser()
    small_config = _normalize_repo_prefixed(small_config)
    if not small_config.is_absolute():
        small_config = (project_root / small_config).resolve()

    large_config = Path(str(args.large_config)).expanduser()
    large_config = _normalize_repo_prefixed(large_config)
    if not large_config.is_absolute():
        large_config = (project_root / large_config).resolve()

    inputs = RunInputs(audit_root=audit_root, small_config=small_config, large_config=large_config)

    if not inputs.audit_root.exists():
        raise FileNotFoundError(f"Audit root not found: {inputs.audit_root}")

    run_dirs = sorted([p for p in inputs.audit_root.iterdir() if p.is_dir()])
    if not run_dirs:
        raise FileNotFoundError(f"No run directories found under: {inputs.audit_root}")

    metric_rows: list[dict[str, Any]] = []
    aux_rows: list[dict[str, Any]] = []

    # For required dataset+wave distribution plots, we aggregate approval_gap + recoverability_score
    # across replicates for each (dataset, wave) bucket.
    plot_acc: dict[tuple[str, str], dict[str, list[float]]] = {}

    for run_dir in run_dirs:
        if not (run_dir / "cohort_metrics.json").exists():
            continue
        if not (run_dir / "customer_level_analysis.csv").exists():
            continue

        try:
            dataset_label = _infer_dataset_label(run_dir.name)
        except ValueError:
            # Non-canonical folders (e.g., smoke runs) may exist under the audit root.
            # Deterministically ignore them rather than failing the whole summarize step.
            continue
        base_config = inputs.small_config if dataset_label == "small" else inputs.large_config
        required, aux = _extract_required_metrics(
            run_dir=run_dir,
            dataset_label=dataset_label,
            base_config_path=base_config,
            fallback_config_path=inputs.small_config,
        )
        metric_rows.append(required)
        aux_rows.append({"run_dir": str(run_dir), **aux})

        # Accumulate per dataset-wave arrays for plots (deterministic bins; no data-fitting).
        wave = _infer_wave_bucket(run_dir.name)
        # Collapse all small to wave=S for plotting.
        if dataset_label == "small":
            wave = "S"

        customer_cols = _load_customer_columns(run_dir / "customer_level_analysis.csv")
        approval_gap = customer_cols["approval_gap"]
        rec_score = customer_cols["recoverability_score"]
        key = (dataset_label, wave)
        plot_acc.setdefault(key, {"approval_gap": [], "recoverability_score": []})
        plot_acc[key]["approval_gap"].extend(np.asarray(approval_gap, dtype=float).tolist())
        plot_acc[key]["recoverability_score"].extend(np.asarray(rec_score, dtype=float).tolist())

    if not metric_rows:
        raise FileNotFoundError(f"No runnable artifact dirs found under: {inputs.audit_root}")

    # Normalize wave labels: small => S; large => W1/W2/W3.
    for row in metric_rows:
        row["wave"] = _infer_wave_bucket(str(row.get("run_name", "")))
        if str(row.get("dataset")) == "small":
            row["wave"] = "S"

    out_csv = inputs.audit_root / "diagnostic_metrics_by_wave.csv"
    # Deterministic column order; include required metrics first.
    cols = [
        "run_dir",
        "run_name",
        "dataset",
        "wave",
        "n_customers_requested",
        "sample_seed",
        "with_replacement",
        "unique_denied_available",
        "denied_rate",
        "approval_gap_p10",
        "approval_gap_p25",
        "approval_gap_p50",
        "approval_gap_p75",
        "approval_gap_p90",
        "approval_gap_ge_0p20_rate",
        "threshold_reach_possible_rate",
        "recoverable_flag_rate",
        "recourse_mode_full_rate",
        "valid_path_exists_rate",
        "movement_rate_global",
        "movement_rate_recoverable_full",
        "recoverable_full_mode_n",
        "selected_invalid_winner_count",
        "selected_surface_drift_count",
        "operator_packet_contradiction_count",
        "population_total_rows",
        "population_total_rows_source",
    ]
    rows_sorted = sorted(metric_rows, key=lambda r: (r.get("dataset", ""), r.get("wave", ""), r.get("run_name", "")))
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for row in rows_sorted:
            writer.writerow(row)

    trust_summary = _build_trust_summary(rows_sorted)
    (inputs.audit_root / "trust_summary.json").write_text(
        json.dumps(trust_summary, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    wave_means = _wave_means(rows_sorted)
    detector = _failure_mode_detector(rows_sorted, wave_means)
    instability = _scale_instability_flags(wave_means)  # type: ignore[arg-type]

    # Required distribution plots by dataset-wave.
    for (dataset, wave), payload in sorted(plot_acc.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        _write_distribution_plots_by_dataset_wave(
            out_dir=inputs.audit_root,
            dataset=dataset,
            wave=wave,
            approval_gap_values=np.asarray(payload["approval_gap"], dtype=float),
            recoverability_score_values=np.asarray(payload["recoverability_score"], dtype=float),
        )

    expected_required = [
        "S1_small_n300_seed42",
        "S2_small_n300_seed43",
        "W1a_large_n300_seed42",
        "W1b_large_n300_seed43",
        "W2a_large_n3000_seed42",
        "W2b_large_n3000_seed43",
        "W3a_large_n20000_seed42",
    ]
    expected_optional = [
        "W3b_large_n20000_seed43",
    ]
    observed = {str(r.get("run_name", "")) for r in rows_sorted}
    missing_required = [name for name in expected_required if name not in observed]
    missing_optional = [name for name in expected_optional if name not in observed]
    missing_runs = missing_required + [f"optional {name}" for name in missing_optional]

    report_path = inputs.audit_root / "scale_stability_report.md"
    _write_scale_stability_report(
        out_path=report_path,
        metrics_rows=rows_sorted,
        wave_means=wave_means,
        detector=detector,
        instability=instability,
        missing_runs=missing_runs,
    )


if __name__ == "__main__":
    main()
