from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


COVERAGE_DIAGNOSTICS_VERSION = "v1"
DEFAULT_GAP_CLOSURE_EPSILON = 0.05


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    text = str(value).strip()
    return text or default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return int(default)
        if pd.isna(value):
            return int(default)
    except Exception:
        pass
    try:
        return int(value)
    except Exception:
        return int(default)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        if pd.isna(value):
            return float(default)
    except Exception:
        pass
    try:
        return float(value)
    except Exception:
        return float(default)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _as_bool_flag(value: Any) -> int:
    return int(bool(_safe_int(value, 0)))


def _segment_from_recoverability_bucket(value: Any) -> str:
    bucket = _safe_text(value).strip().lower()
    if bucket == "structural_limited":
        return "hard_denied"
    if not bucket:
        return "unknown"
    return bucket


def _rate(numer: int, denom: int) -> float:
    if denom <= 0:
        return 0.0
    return round(float(numer) / float(denom), 6)


def _distribution(values: pd.Series) -> dict[str, float]:
    if values.empty:
        return {}
    normalized = values.astype(str).str.strip()
    normalized = normalized[normalized != ""]
    if normalized.empty:
        return {}
    return {str(k): round(float(v), 6) for k, v in normalized.value_counts(normalize=True).sort_index().items()}


@dataclass(frozen=True)
class CoverageDiagnosticsPaths:
    output_dir: Path
    customer_breakdown_csv: Path
    summary_json: Path
    reason_frequency_csv: Path
    empty_state_decomposition_json: Path


def _movement_positive(row: pd.Series) -> bool:
    movement_potential = _safe_text(row.get("movement_potential")).strip().lower()
    if movement_potential in {"weak", "strong"}:
        return True
    return bool(_as_bool_flag(row.get("path_reaches_threshold_flag")))


def _threshold_signal_present(row: pd.Series, *, gap_closure_epsilon: float) -> bool:
    if bool(_as_bool_flag(row.get("threshold_reach_possible"))):
        return True
    if bool(_as_bool_flag(row.get("path_reaches_threshold_flag"))):
        return True
    return _safe_float(row.get("max_gap_closure_rate"), 0.0) > float(gap_closure_epsilon)


def _trust_blocked(row: pd.Series) -> bool:
    return any(
        _as_bool_flag(row.get(flag))
        for flag in (
            "selected_invalid_winner_flag",
            "selected_surface_drift_flag",
            "operator_packet_contradiction_flag",
        )
    )


def assign_coverage_loss_bucket(
    row: pd.Series,
    *,
    gap_closure_epsilon: float,
) -> str:
    if _trust_blocked(row):
        return "trust_blocked"

    selected_source = _safe_text(row.get("selected_recommendation_source")).strip().lower()
    recommendation_mode = _safe_text(row.get("recommendation_mode")).strip().lower()
    if selected_source == "selected_plan" or recommendation_mode == "actionable":
        return "selected_plan_present"

    has_valid = bool(_as_bool_flag(row.get("has_valid_path_flag")))
    if not has_valid:
        return "no_valid_path"

    has_rankable = bool(_as_bool_flag(row.get("has_rankable_path_flag")))
    rankable_count = _safe_float(row.get("rankable_path_count"), 0.0)
    if (not has_rankable) or rankable_count <= 0.0:
        return "valid_but_not_rankable"

    movement_positive = _movement_positive(row)
    if not movement_positive:
        return "rankable_but_no_movement"

    threshold_signal = _threshold_signal_present(row, gap_closure_epsilon=gap_closure_epsilon)
    if not threshold_signal:
        return "movement_but_no_threshold_signal"

    recourse_mode = _safe_text(row.get("recourse_mode")).strip().lower()
    empty_state_flag = bool(_as_bool_flag(row.get("empty_state_flag")))
    if recourse_mode == "limited" or recommendation_mode == "informational":
        return "latent_value_but_gate_suppressed"
    if empty_state_flag or selected_source == "empty_state":
        return "post_gate_surface_collapsed_to_empty_state"
    return "latent_value_but_gate_suppressed"


def build_customer_breakdown(
    customer_df: pd.DataFrame,
    *,
    gap_closure_epsilon: float = DEFAULT_GAP_CLOSURE_EPSILON,
) -> pd.DataFrame:
    df = customer_df.copy()

    if "segment" not in df.columns:
        df["segment"] = df.get("recoverability_bucket", pd.Series([""] * len(df), dtype=object)).apply(
            _segment_from_recoverability_bucket
        )
    else:
        df["segment"] = df["segment"].apply(_safe_text).apply(_segment_from_recoverability_bucket)

    required_mode_columns = [
        "customer_id",
        "source_customer_id",
        "cohort_label",
        "recoverability_bucket",
        "segment",
        "recourse_mode",
        "recommendation_mode",
        "selected_recommendation_source",
        "empty_state_flag",
        "zero_action_flag",
        "has_valid_path_flag",
        "has_rankable_path_flag",
        "threshold_reach_possible",
        "path_reaches_threshold_flag",
        "movement_potential",
        "max_gap_closure_rate",
    ]
    for column in required_mode_columns:
        if column not in df.columns:
            df[column] = ""

    df["coverage_loss_bucket"] = df.apply(
        lambda row: assign_coverage_loss_bucket(row, gap_closure_epsilon=gap_closure_epsilon),
        axis=1,
    )

    df["coverage_loss_subreasons_json"] = df.apply(
        lambda row: _json_dumps(
            {
                "gap_closure_epsilon": float(gap_closure_epsilon),
                "movement_positive": _movement_positive(row),
                "threshold_signal_present": _threshold_signal_present(row, gap_closure_epsilon=gap_closure_epsilon),
            }
        ),
        axis=1,
    )

    ordered = [c for c in required_mode_columns if c in df.columns] + [
        "coverage_loss_bucket",
        "coverage_loss_subreasons_json",
    ]
    return df[ordered].copy()


def _summarize_breakdown(breakdown: pd.DataFrame) -> dict[str, Any]:
    total = int(len(breakdown))
    empty_state = int(pd.to_numeric(breakdown.get("empty_state_flag", 0), errors="coerce").fillna(0).astype(int).clip(0, 1).sum())
    actionable = int((breakdown.get("recommendation_mode", "").astype(str).str.strip().str.lower() == "actionable").sum())
    selected_plan = int((breakdown.get("selected_recommendation_source", "").astype(str).str.strip().str.lower() == "selected_plan").sum())
    return {
        "n_customers": total,
        "empty_state_rate": _rate(empty_state, total),
        "actionability_rate": _rate(actionable, total),
        "selected_plan_availability_rate": _rate(selected_plan, total),
        "recourse_mode_distribution": _distribution(breakdown.get("recourse_mode", pd.Series([], dtype=object))),
        "recommendation_mode_distribution": _distribution(breakdown.get("recommendation_mode", pd.Series([], dtype=object))),
        "selected_recommendation_source_distribution": _distribution(
            breakdown.get("selected_recommendation_source", pd.Series([], dtype=object))
        ),
        "coverage_loss_bucket_distribution": _distribution(breakdown.get("coverage_loss_bucket", pd.Series([], dtype=object))),
    }


def _reason_frequency(breakdown: pd.DataFrame) -> pd.DataFrame:
    df = breakdown.copy()
    df["segment"] = df.get("segment", "").astype(str).str.strip()
    df["coverage_loss_bucket"] = df.get("coverage_loss_bucket", "").astype(str).str.strip()
    df = df[(df["segment"] != "") & (df["coverage_loss_bucket"] != "")]
    if df.empty:
        return pd.DataFrame(columns=["segment", "coverage_loss_bucket", "count", "rate", "segment_total"])

    totals = df.groupby("segment", dropna=False).size().rename("segment_total").reset_index()
    counts = df.groupby(["segment", "coverage_loss_bucket"], dropna=False).size().rename("count").reset_index()
    merged = counts.merge(totals, on="segment", how="left")
    merged["rate"] = merged.apply(lambda r: _rate(int(r["count"]), int(r["segment_total"])), axis=1)
    return merged.sort_values(["segment", "count", "coverage_loss_bucket"], ascending=[True, False, True]).reset_index(drop=True)


def _empty_state_decomposition(breakdown: pd.DataFrame) -> dict[str, Any]:
    selected_source = breakdown.get("selected_recommendation_source", "").astype(str).str.strip().str.lower()
    empty_flag = pd.to_numeric(breakdown.get("empty_state_flag", 0), errors="coerce").fillna(0).astype(int).clip(0, 1)
    empty_mask = (empty_flag == 1) | (selected_source == "empty_state")

    def pack(df: pd.DataFrame) -> dict[str, Any]:
        total = int(len(df))
        bucket_counts = df.get("coverage_loss_bucket", pd.Series([], dtype=object)).astype(str).str.strip().value_counts().to_dict()
        return {
            "n_customers": total,
            "bucket_counts": {str(k): int(v) for k, v in bucket_counts.items()},
            "bucket_rates": {str(k): _rate(int(v), total) for k, v in bucket_counts.items()},
        }

    empty_df = breakdown[empty_mask].copy()
    payload: dict[str, Any] = {"overall": pack(empty_df), "by_segment": {}}
    for segment, seg_df in empty_df.groupby("segment", dropna=False):
        seg_key = _safe_text(segment, "unknown")
        payload["by_segment"][seg_key] = pack(seg_df)
    return payload


def write_coverage_diagnostics(
    *,
    customer_df: pd.DataFrame | None = None,
    customer_csv_path: str | Path | None = None,
    output_dir: str | Path,
    gap_closure_epsilon: float = DEFAULT_GAP_CLOSURE_EPSILON,
) -> CoverageDiagnosticsPaths:
    if customer_df is None:
        if not customer_csv_path:
            raise ValueError("Provide either customer_df or customer_csv_path")
        customer_df = pd.read_csv(Path(customer_csv_path))

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    breakdown = build_customer_breakdown(customer_df, gap_closure_epsilon=gap_closure_epsilon)

    breakdown_path = out_dir / "coverage_diagnostic_customer_breakdown.csv"
    breakdown.to_csv(breakdown_path, index=False)

    summary = {
        "coverage_diagnostics_version": COVERAGE_DIAGNOSTICS_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "thresholds": {"gap_closure_epsilon": float(gap_closure_epsilon)},
        "overall": _summarize_breakdown(breakdown),
        "by_segment": {
            segment: _summarize_breakdown(seg_df.copy())
            for segment, seg_df in breakdown.groupby("segment", dropna=False)
        },
    }
    summary_path = out_dir / "coverage_diagnostic_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    reason_frequency = _reason_frequency(breakdown)
    reason_frequency_path = out_dir / "coverage_reason_frequency.csv"
    reason_frequency.to_csv(reason_frequency_path, index=False)

    decomposition = _empty_state_decomposition(breakdown)
    decomposition_path = out_dir / "empty_state_decomposition.json"
    decomposition_path.write_text(
        json.dumps(decomposition, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return CoverageDiagnosticsPaths(
        output_dir=out_dir,
        customer_breakdown_csv=breakdown_path,
        summary_json=summary_path,
        reason_frequency_csv=reason_frequency_path,
        empty_state_decomposition_json=decomposition_path,
    )

