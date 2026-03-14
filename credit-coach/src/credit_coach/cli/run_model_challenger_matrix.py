from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from credit_coach.ops.kpi_contract import load_kpi_thresholds
from credit_coach.ops.release_decision import (
    GO,
    aggregate_release_metrics,
    evaluate_release_decision,
    evaluate_seed_kpi_contract,
)
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_model_challenger_matrix")

_VARIANTS: tuple[dict[str, Any], ...] = (
    {
        "variant_id": "control_logistic_isotonic",
        "force_backend": "logistic_regression",
        "calibration_method": "isotonic",
        "monotonic_constraints": {},
    },
    {
        "variant_id": "logistic_sigmoid",
        "force_backend": "logistic_regression",
        "calibration_method": "sigmoid",
        "monotonic_constraints": {},
    },
    {
        "variant_id": "xgboost_monotonic_isotonic",
        "force_backend": "xgboost",
        "calibration_method": "isotonic",
        "monotonic_constraints": {
            "annual_inc": -1,
            "dti": 1,
            "revol_util": 1,
            "last_fico_range_high": -1,
            "last_fico_range_low": -1,
            "acc_now_delinq": 1,
            "delinq_amnt": 1,
            "collections_12_mths_ex_med": 1,
        },
    },
    {
        "variant_id": "xgboost_monotonic_sigmoid",
        "force_backend": "xgboost",
        "calibration_method": "sigmoid",
        "monotonic_constraints": {
            "annual_inc": -1,
            "dti": 1,
            "revol_util": 1,
            "last_fico_range_high": -1,
            "last_fico_range_low": -1,
            "acc_now_delinq": 1,
            "delinq_amnt": 1,
            "collections_12_mths_ex_med": 1,
        },
    },
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run model/calibration challenger matrix with high-risk recourse KPIs")
    p.add_argument("--base_config", type=str, default="configs/default.yaml")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--recourse_config", type=str, default="configs/experiments/recourse_phaseb_hybrid_v2.yaml")
    p.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    p.add_argument("--safety_config", type=str, default="configs/safety.yaml")
    p.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    p.add_argument("--n_customers", type=int, default=1000)
    p.add_argument("--sample_seeds", type=str, default="42,43,44,45,46")
    p.add_argument("--n_workers", type=int, default=5)
    p.add_argument("--log_every", type=int, default=100)
    p.add_argument("--kpi_contract", type=str, default="configs/kpi_contract.yaml")
    p.add_argument("--execute", action="store_true")
    return p.parse_args()


def _parse_seeds(raw: str) -> list[int]:
    vals = [s.strip() for s in str(raw).split(",") if s.strip()]
    seeds = [int(v) for v in vals]
    if not seeds:
        raise ValueError("sample_seeds cannot be empty")
    return seeds


def _extract_run_id(log_text: str) -> str:
    matches = re.findall(r"artifacts/runs/([0-9]{8}_[0-9]{6}_[0-9a-f]+_[0-9a-f]+)", log_text)
    return matches[0] if matches else ""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _build_variant_model_cfg(
    *,
    base_model_cfg: dict[str, Any],
    variant: dict[str, Any],
) -> dict[str, Any]:
    out = deepcopy(base_model_cfg)
    model_cfg = out.get("model", {}) if isinstance(out.get("model", {}), dict) else {}
    model_cfg = dict(model_cfg)
    params = model_cfg.get("params", {}) if isinstance(model_cfg.get("params", {}), dict) else {}
    params = dict(params)

    backend = str(variant["force_backend"])
    if backend == "xgboost":
        model_cfg["type"] = "xgboost"
        params["allow_xgboost"] = True
        params["monotone_constraints"] = deepcopy(variant.get("monotonic_constraints", {}))
    else:
        model_cfg["type"] = "logistic_regression"
        params["allow_xgboost"] = False
        params["monotone_constraints"] = {}

    model_cfg["params"] = params
    out["model"] = model_cfg

    calibration_cfg = out.get("calibration", {}) if isinstance(out.get("calibration", {}), dict) else {}
    calibration_cfg = dict(calibration_cfg)
    calibration_cfg["method"] = str(variant["calibration_method"])
    out["calibration"] = calibration_cfg
    return out


def _run_cmd(*, cmd: list[str], cwd: Path, env: dict[str, str], label: str) -> tuple[str, str]:
    logger.info("Running %s: %s", label, " ".join(cmd))
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    log_text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    if proc.returncode != 0:
        raise RuntimeError(f"{label} failed (code={proc.returncode})\n{log_text[-4000:]}")
    run_id = _extract_run_id(log_text)
    if not run_id:
        raise RuntimeError(f"{label} succeeded but run_id could not be parsed")
    return run_id, log_text


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _aggregate_variant_metrics(df: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        "auc",
        "pr_auc",
        "denied_to_approved_lift",
        "denied_high_risk_lift",
        "high_risk_reachability_rate",
        "denied_reliability_violation_rate",
        "fairness_approval_gap_delta",
        "fairness_approval_gap_after",
        "fairness_equalized_odds_gap_delta",
        "fairness_equalized_odds_gap_after",
        "high_stress_approval_gap_after",
        "recourse_success_gap",
        "latency_p95_ms",
        "latency_p99_ms",
        "error_rate",
        "trajectory_gate_pass_rate_4w",
        "trajectory_gate_pass_rate_12w",
        "trajectory_gate_pass_rate_24w",
        "trajectory_partial_progress_rate",
        "trajectory_median_time_to_gate_pass_days",
    ]
    available = [c for c in metric_cols if c in df.columns]
    grouped = (
        df.groupby("variant_id", dropna=False)[available]
        .mean(numeric_only=True)
        .reset_index()
        .rename(columns={c: f"mean_{c}" for c in available})
    )
    grouped["seed_count"] = df.groupby("variant_id").size().values
    return grouped


def _gate_violation_score(row: pd.Series, thresholds: dict[str, Any]) -> tuple[float, int]:
    # 0 = no violation, higher = worse. Score is normalized by threshold distance.
    violations: list[float] = []
    checks = 0

    def _max_violation(metric: str, key: str) -> None:
        nonlocal checks
        if metric not in row or key not in thresholds:
            return
        try:
            val = float(row.get(metric, 0.0))
            thr = float(thresholds.get(key, 0.0))
        except Exception:
            return
        checks += 1
        if val > thr:
            denom = max(abs(thr), 1e-9)
            violations.append((val - thr) / denom)

    def _min_violation(metric: str, key: str) -> None:
        nonlocal checks
        if metric not in row or key not in thresholds:
            return
        try:
            val = float(row.get(metric, 0.0))
            thr = float(thresholds.get(key, 0.0))
        except Exception:
            return
        checks += 1
        if val < thr:
            denom = max(abs(thr), 1e-9)
            violations.append((thr - val) / denom)

    _min_violation("mean_denied_to_approved_lift", "min_denied_to_approved_lift")
    _min_violation("mean_denied_high_risk_lift", "min_denied_high_risk_lift")
    _max_violation("mean_denied_reliability_violation_rate", "max_denied_reliability_violation_rate")
    _max_violation("mean_fairness_approval_gap_delta", "max_approval_gap_delta")
    _max_violation("mean_fairness_equalized_odds_gap_delta", "max_equalized_odds_gap_delta")
    _max_violation("mean_fairness_approval_gap_after", "max_fairness_gap")
    _max_violation("mean_high_stress_approval_gap_after", "max_high_stress_fairness_gap")
    _max_violation("mean_recourse_success_gap", "max_recourse_success_gap")
    _max_violation("mean_latency_p95_ms", "max_p95_latency_ms")
    _max_violation("mean_latency_p99_ms", "max_p99_latency_ms")
    _max_violation("mean_error_rate", "max_error_rate")
    _min_violation("mean_trajectory_gate_pass_rate_4w", "min_trajectory_gate_pass_rate_4w")
    _min_violation("mean_trajectory_gate_pass_rate_12w", "min_trajectory_gate_pass_rate_12w")
    _min_violation("mean_trajectory_gate_pass_rate_24w", "min_trajectory_gate_pass_rate_24w")
    _min_violation("mean_trajectory_partial_progress_rate", "min_trajectory_partial_progress_rate")
    _max_violation("mean_trajectory_median_time_to_gate_pass_days", "max_trajectory_median_time_to_gate_pass_days")
    return float(sum(violations)), int(len(violations))


def _select_champion(summary_df: pd.DataFrame, thresholds: dict[str, Any]) -> tuple[str, pd.DataFrame]:
    ranked = summary_df.copy()
    violation_scores: list[float] = []
    violation_counts: list[int] = []
    for _, row in ranked.iterrows():
        score, cnt = _gate_violation_score(row, thresholds)
        violation_scores.append(score)
        violation_counts.append(cnt)

    ranked["_gate_violation_score"] = violation_scores
    ranked["_gate_failed_check_count"] = violation_counts
    ranked["_gate_all_pass"] = ranked["_gate_failed_check_count"] == 0
    decision_rank = {"GO": 0, "LIMITED_GO": 1, "NO_GO": 2}
    if "release_decision" in ranked.columns:
        release_decisions = ranked["release_decision"].fillna("NO_GO").astype(str)
    else:
        release_decisions = pd.Series(["NO_GO"] * len(ranked), index=ranked.index, dtype="object")
    ranked["_release_rank"] = release_decisions.map(decision_rank).fillna(2).astype(int)
    ranked["_promotion_eligible"] = release_decisions == GO
    ranked["_score_a"] = -ranked.get("mean_denied_high_risk_lift", 0.0)
    ranked["_score_b"] = -ranked.get("mean_high_risk_reachability_rate", 0.0)
    ranked["_score_c"] = -ranked.get("mean_denied_to_approved_lift", 0.0)
    ranked["_score_d"] = ranked.get("mean_fairness_approval_gap_after", 1.0)
    ranked["_score_e"] = ranked.get("mean_latency_p99_ms", 999999.0)
    ranked = ranked.sort_values(
        [
            "_release_rank",
            "_gate_all_pass",
            "_gate_failed_check_count",
            "_gate_violation_score",
            "_score_a",
            "_score_b",
            "_score_c",
            "_score_d",
            "_score_e",
        ],
        ascending=[True, False, True, True, True, True, True, True, True],
    ).reset_index(drop=True)
    return str(ranked.iloc[0]["variant_id"]), ranked


def _seed_contract_from_challenger_row(row: pd.Series, thresholds: dict[str, Any]) -> dict[str, Any]:
    denied_count = float(row.get("denied_count", 0.0))
    denied_with_gate_pass_plan = float(row.get("denied_with_gate_pass_plan", 0.0))
    summary = {
        "denied_count": denied_count,
        "denied_with_gate_pass_plan": denied_with_gate_pass_plan,
        "denied_to_approved_lift": float(row.get("denied_to_approved_lift", 0.0)),
        "denied_high_risk_lift": float(row.get("denied_high_risk_lift", 0.0)),
        "denied_reliability_violation_rate": float(row.get("denied_reliability_violation_rate", 0.0)),
        "sync_latency_p95_ms": float(row.get("latency_p95_ms", 0.0)),
        "sync_latency_p99_ms": float(row.get("latency_p99_ms", 0.0)),
        "error_rate": float(row.get("error_rate", 0.0)),
        "fairness_approval_gap_after": float(row.get("fairness_approval_gap_after", 0.0)),
        "trajectory_gate_pass_rate_4w": float(row.get("trajectory_gate_pass_rate_4w", 0.0)),
        "trajectory_gate_pass_rate_12w": float(row.get("trajectory_gate_pass_rate_12w", 0.0)),
        "trajectory_gate_pass_rate_24w": float(row.get("trajectory_gate_pass_rate_24w", 0.0)),
        "trajectory_partial_progress_rate": float(row.get("trajectory_partial_progress_rate", 0.0)),
        "trajectory_median_time_to_gate_pass_days": float(row.get("trajectory_median_time_to_gate_pass_days", 9_999.0)),
    }
    fair_metrics = {
        "approval_gap_delta": float(row.get("fairness_approval_gap_delta", 0.0)),
        "equalized_odds_gap_delta": float(row.get("fairness_equalized_odds_gap_delta", 0.0)),
        "high_stress_fairness_gap_after": float(row.get("high_stress_approval_gap_after", 0.0)),
        "recourse_success_gap": float(row.get("recourse_success_gap", 0.0)),
        "fairness_gap_after": float(row.get("fairness_approval_gap_after", 0.0)),
    }
    return evaluate_seed_kpi_contract(summary, fair_metrics, thresholds)


def _build_variant_release_payloads(
    runs_df: pd.DataFrame,
    *,
    thresholds: dict[str, Any],
    breakdown_frames: list[pd.DataFrame],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for variant_id, variant_runs in runs_df.groupby("variant_id", dropna=False):
        seed_rows = [_seed_contract_from_challenger_row(row, thresholds) for _, row in variant_runs.iterrows()]
        breakdown_rows: list[dict[str, Any]] = []
        for frame in breakdown_frames:
            if frame.empty or str(frame["variant_id"].iloc[0]) != str(variant_id):
                continue
            breakdown_rows.extend(frame.to_dict(orient="records"))
        aggregate = aggregate_release_metrics(seed_rows, thresholds=thresholds, breakdown_rows=breakdown_rows)
        release_payload = evaluate_release_decision(aggregate, thresholds)
        rows.append(
            {
                "variant_id": str(variant_id),
                "release_decision": str(release_payload["decision"]),
                "pilot_eligible": bool(release_payload["pilot_eligible"]),
                "promotion_eligible": bool(release_payload["decision"] == GO),
                "fairness_seed_pass_count": int(aggregate["fairness_seed_pass_count"]),
                "fairness_seed_total": int(aggregate["fairness_seed_total"]),
                "dominant_fail_segment_key": str(aggregate.get("dominant_fail_segment_key", "")),
                "dominant_fail_candidate_source": str(aggregate.get("dominant_fail_candidate_source", "")),
                "dominant_fail_segment_share": float(aggregate.get("dominant_fail_segment_share", 0.0)),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    seeds = _parse_seeds(args.sample_seeds)
    root = _project_root()

    base_cfg = load_config(args.base_config)
    model_cfg = load_config(args.model_config)
    recourse_cfg = load_config(args.recourse_config)
    causality_cfg = load_config(args.causality_config)
    safety_cfg = load_config(args.safety_config)
    macro_cfg = load_config(args.macro_config)
    kpi_thresholds = load_kpi_thresholds(args.kpi_contract)

    run_ctx = create_run_context(
        {
            "mode": "challenger_matrix",
            "seeds": seeds,
            "n_customers": int(args.n_customers),
            "variants": [v["variant_id"] for v in _VARIANTS],
            "execute": bool(args.execute),
            "kpi_contract": str(args.kpi_contract),
        },
        base_artifact_dir="artifacts/runs",
    )

    variant_plan_rows = []
    for v in _VARIANTS:
        variant_plan_rows.append(
            {
                "variant_id": str(v["variant_id"]),
                "backend": str(v["force_backend"]),
                "calibration_method": str(v["calibration_method"]),
                "seed_count": int(len(seeds)),
            }
        )
    variant_plan_df = pd.DataFrame(variant_plan_rows)
    variant_plan_path = run_ctx.tables_dir / "challenger_variant_plan.csv"
    variant_plan_df.to_csv(variant_plan_path, index=False)

    if not bool(args.execute):
        logger.info("Execution disabled. Variant plan exported: %s", variant_plan_path)
        run_ctx.save_metrics({"execute": False, "variant_count": int(len(_VARIANTS)), "seed_count": int(len(seeds))})
        return

    run_rows: list[dict[str, Any]] = []
    breakdown_frames: list[pd.DataFrame] = []

    for variant in _VARIANTS:
        variant_id = str(variant["variant_id"])
        variant_model_cfg = _build_variant_model_cfg(base_model_cfg=model_cfg, variant=variant)
        variant_cfg_path = run_ctx.tables_dir / f"model_variant_{variant_id}.yaml"
        variant_cfg_path.write_text(yaml.safe_dump(variant_model_cfg, sort_keys=False, allow_unicode=False), encoding="utf-8")

        for seed in seeds:
            env = os.environ.copy()
            env["CREDIT_COACH_FORCE_BACKEND"] = str(variant["force_backend"])
            env["CREDIT_COACH_ALLOW_XGB"] = "1" if str(variant["force_backend"]) == "xgboost" else "0"

            train_cmd = [
                sys.executable,
                "-m",
                "credit_coach.cli.run_train",
                "--base_config",
                str(args.base_config),
                "--config",
                str(variant_cfg_path),
            ]
            train_run_id, train_log = _run_cmd(
                cmd=train_cmd,
                cwd=root,
                env=env,
                label=f"train[{variant_id}][seed={seed}]",
            )

            batch_cmd = [
                sys.executable,
                "-m",
                "credit_coach.cli.run_batch_recourse_eval",
                "--n_customers",
                str(int(args.n_customers)),
                "--sample_seed",
                str(int(seed)),
                "--log_every",
                str(int(args.log_every)),
                "--n_workers",
                str(int(args.n_workers)),
                "--base_config",
                str(args.base_config),
                "--model_config",
                str(args.model_config),
                "--recourse_config",
                str(args.recourse_config),
                "--causality_config",
                str(args.causality_config),
                "--safety_config",
                str(args.safety_config),
                "--macro_config",
                str(args.macro_config),
            ]
            batch_run_id, batch_log = _run_cmd(
                cmd=batch_cmd,
                cwd=root,
                env=env,
                label=f"batch[{variant_id}][seed={seed}]",
            )

            train_metrics_path = root / "artifacts" / "models" / train_run_id / "metrics.json"
            batch_metrics_path = root / "artifacts" / "runs" / batch_run_id / "metrics.json"
            batch_breakdown_path = root / "artifacts" / "runs" / batch_run_id / "tables" / "fairness_failure_breakdown.csv"
            train_metrics = _load_json(train_metrics_path)
            batch_metrics = _load_json(batch_metrics_path)
            if batch_breakdown_path.exists():
                breakdown_df = pd.read_csv(batch_breakdown_path)
                if not breakdown_df.empty:
                    breakdown_df["variant_id"] = variant_id
                    breakdown_df["seed"] = int(seed)
                    breakdown_frames.append(breakdown_df)
            raw_p95 = float(batch_metrics.get("latency_p95_ms", 0.0))
            raw_p99 = float(batch_metrics.get("latency_p99_ms", 0.0))
            sync_p95 = batch_metrics.get("sync_latency_p95_ms")
            sync_p99 = batch_metrics.get("sync_latency_p99_ms")
            use_sync_latency = (
                sync_p95 is not None
                and sync_p99 is not None
                and float(sync_p95) > 0.0
                and float(sync_p99) > 0.0
            )
            eff_p95 = float(sync_p95) if use_sync_latency else raw_p95
            eff_p99 = float(sync_p99) if use_sync_latency else raw_p99

            row = {
                "variant_id": variant_id,
                "seed": int(seed),
                "train_run_id": train_run_id,
                "batch_run_id": batch_run_id,
                "backend": str(variant["force_backend"]),
                "calibration_method": str(variant["calibration_method"]),
                "auc": float(train_metrics.get("auc", 0.0)),
                "pr_auc": float(train_metrics.get("pr_auc", 0.0)),
                "denied_count": float(batch_metrics.get("denied_count", 0.0)),
                "denied_with_gate_pass_plan": float(batch_metrics.get("denied_with_gate_pass_plan", 0.0)),
                "denied_to_approved_lift": float(batch_metrics.get("denied_to_approved_lift", 0.0)),
                "denied_high_risk_lift": float(batch_metrics.get("denied_high_risk_lift", 0.0)),
                "high_risk_reachability_rate": float(batch_metrics.get("high_risk_reachability_rate", 0.0)),
                "denied_reliability_violation_rate": float(batch_metrics.get("denied_reliability_violation_rate", 0.0)),
                "fairness_approval_gap_before": float(batch_metrics.get("fairness_approval_gap_before", 0.0)),
                "fairness_approval_gap_after": float(batch_metrics.get("fairness_approval_gap_after", 0.0)),
                "fairness_approval_gap_delta": float(
                    batch_metrics.get("fairness_approval_gap_after", 0.0)
                    - batch_metrics.get("fairness_approval_gap_before", 0.0)
                ),
                "fairness_equalized_odds_gap_before": float(
                    batch_metrics.get("fairness_equalized_odds_gap_before", 0.0)
                ),
                "fairness_equalized_odds_gap_after": float(batch_metrics.get("fairness_equalized_odds_gap_after", 0.0)),
                "fairness_equalized_odds_gap_delta": float(
                    batch_metrics.get("fairness_equalized_odds_gap_after", 0.0)
                    - batch_metrics.get("fairness_equalized_odds_gap_before", 0.0)
                ),
                "high_stress_approval_gap_after": float(batch_metrics.get("high_stress_approval_gap_after", 0.0)),
                "recourse_success_gap": float(batch_metrics.get("recourse_success_gap", 0.0)),
                "latency_p95_ms": eff_p95,
                "latency_p99_ms": eff_p99,
                "latency_mode": "sync" if use_sync_latency else "end_to_end",
                "latency_p95_ms_raw": raw_p95,
                "latency_p99_ms_raw": raw_p99,
                "error_rate": float(batch_metrics.get("error_rate", 0.0)),
                "trajectory_gate_pass_rate_4w": float(batch_metrics.get("trajectory_gate_pass_rate_4w", 0.0)),
                "trajectory_gate_pass_rate_12w": float(batch_metrics.get("trajectory_gate_pass_rate_12w", 0.0)),
                "trajectory_gate_pass_rate_24w": float(batch_metrics.get("trajectory_gate_pass_rate_24w", 0.0)),
                "trajectory_partial_progress_rate": float(batch_metrics.get("trajectory_partial_progress_rate", 0.0)),
                "trajectory_median_time_to_gate_pass_days": float(batch_metrics.get("trajectory_median_time_to_gate_pass_days", 9_999.0)),
            }
            run_rows.append(row)

            (run_ctx.tables_dir / f"challenger_train_{variant_id}_{seed}.log").write_text(train_log, encoding="utf-8")
            (run_ctx.tables_dir / f"challenger_batch_{variant_id}_{seed}.log").write_text(batch_log, encoding="utf-8")

    runs_df = pd.DataFrame(run_rows)
    runs_path = run_ctx.tables_dir / "challenger_matrix_runs.csv"
    runs_df.to_csv(runs_path, index=False)

    summary_df = _aggregate_variant_metrics(runs_df)
    if summary_df.empty:
        raise RuntimeError("No challenger summary rows produced")
    release_df = _build_variant_release_payloads(runs_df, thresholds=kpi_thresholds, breakdown_frames=breakdown_frames)
    if not release_df.empty:
        summary_df = summary_df.merge(release_df, on="variant_id", how="left")
    summary_path = run_ctx.tables_dir / "challenger_matrix_variant_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    champion_variant, ranked_summary_df = _select_champion(summary_df, kpi_thresholds)
    ranked_summary_path = run_ctx.tables_dir / "challenger_matrix_variant_summary_ranked.csv"
    ranked_summary_df.to_csv(ranked_summary_path, index=False)
    control_variant = "control_logistic_isotonic"
    control_row = ranked_summary_df[ranked_summary_df["variant_id"] == control_variant]
    champ_row = ranked_summary_df[ranked_summary_df["variant_id"] == champion_variant]

    deltas = {}
    if not control_row.empty and not champ_row.empty:
        c = control_row.iloc[0].to_dict()
        t = champ_row.iloc[0].to_dict()
        for key in (
            "mean_denied_high_risk_lift",
            "mean_high_risk_reachability_rate",
            "mean_denied_to_approved_lift",
            "mean_fairness_approval_gap_after",
            "mean_latency_p99_ms",
        ):
            deltas[f"{key}_delta_vs_control"] = float(t.get(key, 0.0) - c.get(key, 0.0))

    ranked_variants = []
    for _, r in ranked_summary_df.iterrows():
        ranked_variants.append(
            {
                "variant_id": str(r.get("variant_id", "")),
                "release_decision": str(r.get("release_decision", "NO_GO")),
                "pilot_eligible": bool(r.get("pilot_eligible", False)),
                "promotion_eligible": bool(r.get("_promotion_eligible", False)),
                "gate_all_pass": bool(r.get("_gate_all_pass", False)),
                "gate_failed_check_count": int(r.get("_gate_failed_check_count", 0)),
                "gate_violation_score": float(r.get("_gate_violation_score", 0.0)),
            }
        )

    summary_payload = {
        "champion_variant": champion_variant,
        "control_variant": control_variant,
        "variant_count": int(ranked_summary_df.shape[0]),
        "seed_count": int(len(seeds)),
        "kpi_contract": str(args.kpi_contract),
        "champion_release_decision": str(champ_row.iloc[0].get("release_decision", "NO_GO")) if not champ_row.empty else "NO_GO",
        "champion_pilot_eligible": bool(champ_row.iloc[0].get("pilot_eligible", False)) if not champ_row.empty else False,
        "champion_promotion_eligible": bool(champ_row.iloc[0].get("_promotion_eligible", False)) if not champ_row.empty else False,
        "champion_gate_all_pass": bool(champ_row.iloc[0].get("_gate_all_pass", False)) if not champ_row.empty else False,
        "champion_gate_failed_check_count": int(champ_row.iloc[0].get("_gate_failed_check_count", 0))
        if not champ_row.empty
        else 0,
        "champion_gate_violation_score": float(champ_row.iloc[0].get("_gate_violation_score", 0.0))
        if not champ_row.empty
        else 0.0,
        "deltas_vs_control": deltas,
        "ranked_variants": ranked_variants,
    }
    decision_path = run_ctx.tables_dir / "challenger_matrix_decision.json"
    decision_path.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    run_ctx.save_metrics(
        {
            "champion_variant": champion_variant,
            "variant_count": int(ranked_summary_df.shape[0]),
            "seed_count": int(len(seeds)),
            "champion_mean_denied_high_risk_lift": float(
                champ_row.iloc[0].get("mean_denied_high_risk_lift", 0.0)
            )
            if not champ_row.empty
            else 0.0,
            "champion_gate_all_pass": bool(champ_row.iloc[0].get("_gate_all_pass", False))
            if not champ_row.empty
            else False,
            "champion_gate_violation_score": float(champ_row.iloc[0].get("_gate_violation_score", 0.0))
            if not champ_row.empty
            else 0.0,
        }
    )
    logger.info("Challenger matrix completed. champion=%s", champion_variant)
    logger.info("Outputs: %s %s %s %s", runs_path, summary_path, ranked_summary_path, decision_path)


if __name__ == "__main__":
    main()
