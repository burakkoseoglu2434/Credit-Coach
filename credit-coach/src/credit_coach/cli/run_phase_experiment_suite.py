from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from credit_coach.evaluation.fairness import build_canonical_segment_key
from credit_coach.evaluation.portfolio_validation import (
    aggregate_portfolio_breakdown,
    aggregate_portfolio_validation_summaries,
    render_portfolio_validation_review,
)
from credit_coach.model.registry import build_frozen_model_manifest, resolve_model_manifest
from credit_coach.ops.kpi_contract import (
    build_comparative_impact_summary,
    build_kpi_contract_snapshot,
    build_milestone_acceptance_summary,
    build_release_evidence_pack,
    load_kpi_thresholds,
    render_milestone_acceptance_review,
)
from credit_coach.ops.release_decision import (
    aggregate_release_metrics,
    build_pilot_guardrails,
    build_rollback_conditions,
    evaluate_release_decision,
    evaluate_seed_kpi_contract,
)
from credit_coach.storage.repository import CANONICAL_PROXY_METRICS
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_phase_experiment_suite")
_HIGH_RISK_ACTIVATION_FLOOR = 0.05


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run phase experiment suite (quick + 1000x5 scale)")
    p.add_argument("--phase_name", type=str, default="phase_exec")
    p.add_argument("--base_config", type=str, default="configs/default.yaml")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--recourse_config", type=str, default="configs/experiments/recourse_phaseb_hybrid_v2.yaml")
    p.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    p.add_argument("--safety_config", type=str, default="configs/safety.yaml")
    p.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    p.add_argument("--kpi_contract", type=str, default="configs/kpi_contract.yaml")
    p.add_argument("--quick_n", type=int, default=200)
    p.add_argument("--quick_seed", type=int, default=42)
    p.add_argument("--scale_n", type=int, default=1000)
    p.add_argument("--scale_seeds", type=str, default="42,43,44,45,46")
    p.add_argument("--n_workers", type=int, default=5)
    p.add_argument("--log_every", type=int, default=100)
    p.add_argument(
        "--skip_train_before_batch",
        action="store_true",
        help="If set, phase suite reuses current model artifacts and does not run train once at start.",
    )
    p.add_argument("--milestone", type=str, default="current")
    p.add_argument("--model_version", type=str, default="")
    p.add_argument("--model_manifest", type=str, default="")
    p.add_argument("--execute", action="store_true")
    return p.parse_args()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _parse_seeds(raw: str) -> list[int]:
    vals = [x.strip() for x in str(raw).split(",") if x.strip()]
    seeds = [int(v) for v in vals]
    if not seeds:
        raise ValueError("scale_seeds cannot be empty")
    return seeds


def _extract_run_id(text: str) -> str:
    m = re.findall(r"artifacts/runs/([0-9]{8}_[0-9]{6}_[0-9a-f]+_[0-9a-f]+)", text)
    return m[0] if m else ""


def _latest_optional_artifact(pattern: str) -> Path | None:
    candidates = sorted(Path("artifacts/runs").glob(pattern))
    if not candidates:
        return None
    return candidates[-1]


def _mirror_artifact(source: Path | None, destination: Path) -> bool:
    if source is None or not source.exists():
        return False
    destination.write_bytes(source.read_bytes())
    return True


def _run_cmd(*, cmd: list[str], cwd: Path, env: dict[str, str], label: str) -> tuple[str, str]:
    logger.info("Running %s: %s", label, " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, text=True, capture_output=True, check=False)
    out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    if proc.returncode != 0:
        raise RuntimeError(f"{label} failed (code={proc.returncode})\n{out[-4000:]}")
    run_id = _extract_run_id(out)
    if not run_id:
        raise RuntimeError(f"{label} succeeded but run_id not found")
    return run_id, out


def _batch_cmd(
    args: argparse.Namespace,
    *,
    n_customers: int,
    seed: int,
    model_version: str = "",
    model_manifest: str = "",
) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "credit_coach.cli.run_batch_recourse_eval",
        "--n_customers",
        str(int(n_customers)),
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
    if str(model_version).strip():
        cmd.extend(["--model_version", str(model_version).strip()])
    if str(model_manifest).strip():
        cmd.extend(["--model_manifest", str(model_manifest).strip()])
    return cmd


def _train_cmd(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        "-m",
        "credit_coach.cli.run_train",
        "--base_config",
        str(args.base_config),
        "--config",
        str(args.model_config),
    ]


def _smoke_cmd(args: argparse.Namespace, *, batch_run_id: str) -> list[str]:
    root = _project_root()
    base = root / "artifacts" / "runs" / batch_run_id / "tables"
    return [
        sys.executable,
        "-m",
        "credit_coach.cli.run_production_smoke",
        "--kpi_contract",
        str(args.kpi_contract),
        "--batch_summary_json",
        str(base / "batch_summary.json"),
        "--batch_fairness_change_csv",
        str(base / "batch_fairness_change.csv"),
    ]


def _build_registry_path(root: Path, model_cfg_path: str) -> Path:
    model_cfg = load_config(model_cfg_path) if Path(model_cfg_path).exists() else {}
    registry_path = Path(model_cfg.get("registry", {}).get("path", "artifacts/models"))
    if not registry_path.is_absolute():
        registry_path = root / registry_path
    return registry_path


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _round_metric(value: Any, *, digits: int = 6) -> float:
    try:
        metric = float(value)
    except Exception:
        return 0.0
    if pd.isna(metric):
        return 0.0
    return round(metric, digits)


def _build_phase_decision_logging_summary(seed_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    if not seed_summaries:
        return {
            "seed_count": 0,
            "total_decisions": 0,
            "complete_decision_logs": 0,
            "decision_log_completeness": 0.0,
            "policy_metadata_coverage": 0.0,
            "selection_propensity_coverage": 0.0,
            "candidate_set_coverage": 0.0,
            "reason_code_coverage": 0.0,
            "recommended_plan_rate": 0.0,
            "propensity_source_breakdown": {},
        }

    total_decisions = int(sum(int(summary.get("total_decisions", 0)) for summary in seed_summaries))
    complete_decision_logs = int(sum(int(summary.get("complete_decision_logs", 0)) for summary in seed_summaries))
    weighted_denominator = max(1, total_decisions)

    def _weighted_average(key: str) -> float:
        numerator = 0.0
        for summary in seed_summaries:
            total = int(summary.get("total_decisions", 0))
            numerator += float(summary.get(key, 0.0)) * float(total)
        return _round_metric(numerator / float(weighted_denominator))

    propensity_source_breakdown: dict[str, int] = {}
    for summary in seed_summaries:
        breakdown = summary.get("propensity_source_breakdown", {})
        if not isinstance(breakdown, dict):
            continue
        for key, value in breakdown.items():
            propensity_source_breakdown[str(key)] = propensity_source_breakdown.get(str(key), 0) + int(value)

    return {
        "seed_count": int(len(seed_summaries)),
        "total_decisions": total_decisions,
        "complete_decision_logs": complete_decision_logs,
        "decision_log_completeness": _weighted_average("decision_log_completeness"),
        "policy_metadata_coverage": _weighted_average("policy_metadata_coverage"),
        "selection_propensity_coverage": _weighted_average("selection_propensity_coverage"),
        "candidate_set_coverage": _weighted_average("candidate_set_coverage"),
        "reason_code_coverage": _weighted_average("reason_code_coverage"),
        "recommended_plan_rate": _weighted_average("recommended_plan_rate"),
        "propensity_source_breakdown": propensity_source_breakdown,
    }


def _build_learning_loop_summary(
    *,
    decision_logging_summary: Mapping[str, Any] | None,
    outcome_ingestion_summary: Mapping[str, Any] | None,
    off_policy_evaluation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    decision_logging = dict(decision_logging_summary or {})
    ingestion = dict(outcome_ingestion_summary or {})
    ope = dict(off_policy_evaluation or {})
    readiness_distribution = (
        ingestion.get("learning_readiness_status_distribution", {})
        if isinstance(ingestion.get("learning_readiness_status_distribution", {}), dict)
        else {}
    )
    preferred_policy_signal = ope.get("preferred_policy_signal", {})
    if not isinstance(preferred_policy_signal, Mapping):
        preferred_policy_signal = {}
    preferred_policy_arm = str(preferred_policy_signal.get("policy_arm", ""))
    preferred_metric_labels: dict[str, str] = {}
    comparisons = ope.get("comparisons", [])
    if isinstance(comparisons, list):
        for comparison in comparisons:
            if not isinstance(comparison, Mapping):
                continue
            if str(comparison.get("policy_arm", "")) != preferred_policy_arm:
                continue
            labels = comparison.get("metric_labels", {})
            if isinstance(labels, Mapping):
                preferred_metric_labels = {str(key): str(value) for key, value in labels.items()}
            break
    return {
        "decision_log_completeness": _round_metric(decision_logging.get("decision_log_completeness", 0.0)),
        "decision_log_total": int(decision_logging.get("total_decisions", 0)),
        "complete_decision_logs": int(decision_logging.get("complete_decision_logs", 0)),
        "learning_readiness_status_distribution": readiness_distribution,
        "reward_90d_coverage": _round_metric(ingestion.get("reward_90d_coverage", 0.0)),
        "ope_confidence": str(ope.get("ope_confidence", "tentative")),
        "comparison_status": str(ope.get("comparison_status", "not_available")),
        "preferred_policy_signal": dict(preferred_policy_signal),
        "preferred_policy_metric_labels": preferred_metric_labels,
        "canonical_proxy_metrics": list(ope.get("canonical_proxy_metrics", CANONICAL_PROXY_METRICS)),
    }


def _kpi_checks(summary: dict[str, Any], fair_row: dict[str, Any], thresholds: dict[str, Any]) -> tuple[bool, str]:
    snapshot = _seed_contract_snapshot(summary, fair_row, thresholds)
    return bool(snapshot["all_pass"]), str(snapshot["failed_checks"])


def _seed_contract_snapshot(
    summary: dict[str, Any],
    fair_row: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    return evaluate_seed_kpi_contract(summary, fair_row, thresholds)


def _build_phase_fairness_breakdown(
    *,
    seed_rows: list[dict[str, Any]],
    seed_breakdowns: list[pd.DataFrame],
) -> pd.DataFrame:
    output_rows: list[dict[str, Any]] = []
    snapshots_by_seed = {int(row["seed"]): row for row in seed_rows if "seed" in row}

    for breakdown_df in seed_breakdowns:
        if breakdown_df.empty:
            continue
        seed = int(breakdown_df["seed"].iloc[0])
        snapshot = snapshots_by_seed.get(seed, {})
        working = breakdown_df.copy()
        if "candidate_source" not in working.columns and "best_source" in working.columns:
            working["candidate_source"] = working["best_source"]
        if "stress_band" not in working.columns:
            working["stress_band"] = "base"
        if "canonical_segment_key" not in working.columns:
            working["canonical_segment_key"] = working.apply(
                lambda row: build_canonical_segment_key(
                    risk_band=row.get("risk_band", "unknown"),
                    income_band=row.get("income_band", "unknown"),
                    stress_band=row.get("stress_band", "base"),
                ),
                axis=1,
            )
        if "failure_weight" not in working.columns:
            working["failure_weight"] = working.get("failure_severity_score", 0.0)
        if "fairness_guard_demoted_rate" not in working.columns:
            working["fairness_guard_demoted_rate"] = 0.0
        working["seed"] = int(seed)
        working["breakdown_type"] = "segment_candidate_source"
        output_rows.extend(working.to_dict(orient="records"))

        segment_rollup = (
            working.groupby(["seed", "canonical_segment_key", "risk_band", "income_band", "stress_band"], dropna=False)
            .agg(
                n_rows=("n_rows", "sum"),
                denied_rows=("denied_rows", "sum"),
                failure_weight=("failure_weight", "sum"),
                failure_severity_score=("failure_severity_score", "sum"),
                fairness_guard_demoted_rate=("fairness_guard_demoted_rate", "mean"),
            )
            .reset_index()
        )
        for row in segment_rollup.to_dict(orient="records"):
            output_rows.append(
                {
                    **row,
                    "breakdown_type": "seed_segment",
                    "candidate_source": "",
                    "best_source": "",
                    "group_bucket": "",
                    "primary_fail_reason": str(snapshot.get("primary_fail_reason", "")),
                }
            )

        risk_source_rollup = (
            working.groupby(["seed", "risk_band", "candidate_source"], dropna=False)
            .agg(
                n_rows=("n_rows", "sum"),
                denied_rows=("denied_rows", "sum"),
                failure_weight=("failure_weight", "sum"),
                failure_severity_score=("failure_severity_score", "sum"),
            )
            .reset_index()
        )
        for row in risk_source_rollup.to_dict(orient="records"):
            output_rows.append(
                {
                    **row,
                    "breakdown_type": "risk_band_source_rollup",
                    "income_band": "",
                    "stress_band": "base",
                    "group_bucket": "",
                    "best_source": row.get("candidate_source", ""),
                    "canonical_segment_key": build_canonical_segment_key(
                        risk_band=row.get("risk_band", "unknown"),
                        income_band="all",
                        stress_band="base",
                    ),
                    "primary_fail_reason": str(snapshot.get("primary_fail_reason", "")),
                }
            )

        high_stress_weight = float(snapshot.get("high_stress_fairness_gap_after", 0.0))
        if high_stress_weight > 0.0:
            for row in segment_rollup.to_dict(orient="records"):
                output_rows.append(
                    {
                        **row,
                        "breakdown_type": "high_stress_segment",
                        "candidate_source": "",
                        "best_source": "",
                        "group_bucket": "",
                        "stress_band": "high_stress",
                        "canonical_segment_key": build_canonical_segment_key(
                            risk_band=row.get("risk_band", "unknown"),
                            income_band=row.get("income_band", "unknown"),
                            stress_band="high_stress",
                        ),
                        "failure_weight": float(row.get("failure_weight", 0.0)) * high_stress_weight,
                        "primary_fail_reason": "high_stress_fairness_gap_after",
                    }
                )

        dominant_row = working.sort_values(
            ["failure_weight", "n_rows", "canonical_segment_key"],
            ascending=[False, False, True],
        ).head(1)
        dominant_segment_key = ""
        dominant_candidate_source = ""
        if not dominant_row.empty:
            dominant_segment_key = str(dominant_row.iloc[0].get("canonical_segment_key", ""))
            dominant_candidate_source = str(dominant_row.iloc[0].get("candidate_source", ""))
        output_rows.append(
            {
                "seed": int(seed),
                "breakdown_type": "seed_primary_fail_reason",
                "primary_fail_reason": str(snapshot.get("primary_fail_reason", "")),
                "failure_weight": float(snapshot.get("worst_fairness_gap", 0.0)),
                "failure_severity_score": float(snapshot.get("worst_fairness_gap", 0.0)),
                "canonical_segment_key": dominant_segment_key,
                "candidate_source": dominant_candidate_source,
                "best_source": dominant_candidate_source,
                "risk_band": "",
                "income_band": "",
                "stress_band": "",
                "group_bucket": "",
                "n_rows": 0,
                "denied_rows": 0,
            }
        )

    if not output_rows:
        return pd.DataFrame(
            columns=[
                "seed",
                "breakdown_type",
                "canonical_segment_key",
                "candidate_source",
                "primary_fail_reason",
                "failure_weight",
            ]
        )

    return pd.DataFrame(output_rows)


def _build_phase_candidate_quality_summary(scale_df: pd.DataFrame) -> dict[str, Any]:
    metric_fields = (
        "candidate_pool_diversity_index",
        "candidate_source_entropy",
        "best_source_internal_rate",
        "best_source_dice_rate",
        "best_source_rule_rate",
        "best_source_fallback_rate",
    )
    secondary_fields = tuple(f"high_risk_denied_{field}" for field in metric_fields)
    if scale_df.empty:
        return {
            "candidate_quality_population": "denied",
            "candidate_quality_secondary_population": "high_risk_denied",
            "source_catalog": ["internal", "dice", "rule", "fallback"],
            "seed_count": 0,
            "canonical_metrics": {field: 0.0 for field in metric_fields},
            "secondary_metrics": {field.replace("high_risk_denied_", ""): 0.0 for field in secondary_fields},
        }
    canonical_metrics = {
        field: _round_metric(pd.to_numeric(scale_df.get(field, pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean())
        for field in metric_fields
    }
    secondary_metrics = {
        field.replace("high_risk_denied_", ""): _round_metric(
            pd.to_numeric(scale_df.get(field, pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean()
        )
        for field in secondary_fields
    }
    return {
        "candidate_quality_population": str(scale_df.get("candidate_quality_population", pd.Series(["denied"])).iloc[0]),
        "candidate_quality_secondary_population": str(
            scale_df.get("candidate_quality_secondary_population", pd.Series(["high_risk_denied"])).iloc[0]
        ),
        "source_catalog": ["internal", "dice", "rule", "fallback"],
        "seed_count": int(len(scale_df)),
        "canonical_metrics": canonical_metrics,
        "secondary_metrics": secondary_metrics,
    }


def _build_phase_behavior_aware_summary(scale_df: pd.DataFrame) -> dict[str, Any]:
    metric_fields = (
        "mean_plan_execution_probability",
        "expected_pd_improvement",
        "partial_execution_rate",
        "failed_execution_rate",
        "mixed_execution_rate",
        "expected_partial_progress_rate",
    )
    secondary_fields = tuple(f"high_risk_denied_{field}" for field in metric_fields)
    if scale_df.empty:
        return {
            "canonical_population": "denied",
            "secondary_population": "high_risk_denied",
            "seed_count": 0,
            "canonical_metrics": {field: 0.0 for field in metric_fields},
            "secondary_metrics": {field.replace("high_risk_denied_", ""): 0.0 for field in secondary_fields},
            "supporting_artifacts": {
                "execution_probability_breakdown_csv": "tables/execution_probability_breakdown.csv",
                "partial_execution_breakdown_csv": "tables/partial_execution_breakdown.csv",
            },
        }
    canonical_metrics = {
        field: _round_metric(pd.to_numeric(scale_df.get(field, pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean())
        for field in metric_fields
    }
    secondary_metrics = {
        field.replace("high_risk_denied_", ""): _round_metric(
            pd.to_numeric(scale_df.get(field, pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean()
        )
        for field in secondary_fields
    }
    return {
        "canonical_population": "denied",
        "secondary_population": "high_risk_denied",
        "seed_count": int(len(scale_df)),
        "canonical_metrics": canonical_metrics,
        "secondary_metrics": secondary_metrics,
        "supporting_artifacts": {
            "execution_probability_breakdown_csv": "tables/execution_probability_breakdown.csv",
            "partial_execution_breakdown_csv": "tables/partial_execution_breakdown.csv",
        },
    }


def _build_phase_offer_optimization_summary(scale_df: pd.DataFrame) -> dict[str, Any]:
    metric_fields = (
        "offer_plan_rate",
        "rankable_offer_rate",
        "offer_acceptance_probability_mean",
        "combined_plan_realization_probability_mean",
        "expected_recovery_proxy",
        "approval_rate_proxy_delta",
        "default_rate_90d_proxy_delta",
        "avg_margin_90d_proxy_delta",
        "governance_safe_offer_rate",
    )
    if scale_df.empty:
        return {
            "canonical_population": "denied",
            "seed_count": 0,
            "canonical_metrics": {field: 0.0 for field in metric_fields} | {"dominant_offer_type": ""},
            "supporting_artifacts": {
                "offer_type_breakdown_csv": "tables/offer_type_breakdown.csv",
                "offer_policy_arm_breakdown_csv": "tables/offer_policy_arm_breakdown.csv",
                "offer_acceptance_breakdown_csv": "tables/offer_acceptance_breakdown.csv",
                "offer_proxy_impact_breakdown_csv": "tables/offer_proxy_impact_breakdown.csv",
            },
        }
    dominant_offer_type = ""
    if "dominant_offer_type" in scale_df.columns:
        dominant = scale_df["dominant_offer_type"].fillna("").astype(str)
        dominant = dominant[dominant != ""]
        if not dominant.empty:
            dominant_offer_type = str(dominant.value_counts().idxmax())
    canonical_metrics = {
        field: _round_metric(pd.to_numeric(scale_df.get(field, pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean())
        for field in metric_fields
    }
    canonical_metrics["dominant_offer_type"] = dominant_offer_type
    return {
        "canonical_population": "denied",
        "seed_count": int(len(scale_df)),
        "canonical_metrics": canonical_metrics,
        "supporting_artifacts": {
            "offer_type_breakdown_csv": "tables/offer_type_breakdown.csv",
            "offer_policy_arm_breakdown_csv": "tables/offer_policy_arm_breakdown.csv",
            "offer_acceptance_breakdown_csv": "tables/offer_acceptance_breakdown.csv",
            "offer_proxy_impact_breakdown_csv": "tables/offer_proxy_impact_breakdown.csv",
        },
    }


def _build_phase_offer_breakdown(
    seed_breakdowns: list[pd.DataFrame],
    *,
    group_columns: list[str],
    breakdown_type_seed: str,
    breakdown_type_rollup: str,
    value_columns: dict[str, str],
) -> pd.DataFrame:
    if not seed_breakdowns:
        return pd.DataFrame(columns=["seed", *group_columns, *value_columns.keys(), "breakdown_type"])
    frames: list[pd.DataFrame] = []
    for breakdown_df in seed_breakdowns:
        if breakdown_df.empty or "seed" not in breakdown_df.columns:
            continue
        working = breakdown_df.copy()
        working["breakdown_type"] = breakdown_type_seed
        frames.append(working)
    if not frames:
        return pd.DataFrame(columns=["seed", *group_columns, *value_columns.keys(), "breakdown_type"])
    combined = pd.concat(frames, ignore_index=True, sort=False)
    agg_spec: dict[str, str] = {}
    for column, agg_fn in value_columns.items():
        agg_spec[column] = agg_fn
    if "count" in combined.columns and "count" not in agg_spec:
        agg_spec["count"] = "sum"
    rollup = combined.groupby(group_columns, dropna=False).agg(agg_spec).reset_index()
    rollup["seed"] = -1
    rollup["breakdown_type"] = breakdown_type_rollup
    return pd.concat([combined, rollup], ignore_index=True, sort=False)


def _build_phase_trajectory_summary(scale_df: pd.DataFrame) -> dict[str, Any]:
    metric_fields = (
        "trajectory_gate_pass_rate_4w",
        "trajectory_gate_pass_rate_12w",
        "trajectory_gate_pass_rate_24w",
        "trajectory_partial_progress_rate",
        "trajectory_median_time_to_gate_pass_days",
        "trajectory_soft_regression_penalty_mean",
        "trajectory_on_track_rate",
        "trajectory_needs_replan_rate",
        "trajectory_degraded_rate",
        "trajectory_stabilize_first_rate",
        "trajectory_balanced_progress_rate",
        "trajectory_long_horizon_heavy_rate",
    )
    secondary_fields = tuple(f"high_risk_denied_{field}" for field in metric_fields[:-3])
    if scale_df.empty:
        return {
            "canonical_population": "denied",
            "secondary_population": "high_risk_denied",
            "primary_checkpoint_week": 4,
            "checkpoint_priority_order": [4, 12, 24],
            "seed_count": 0,
            "canonical_metrics": {field: 0.0 for field in metric_fields},
            "secondary_metrics": {field.replace("high_risk_denied_", ""): 0.0 for field in secondary_fields},
            "dominant_transition_reason": "",
            "supporting_artifacts": {
                "trajectory_transition_breakdown_csv": "tables/trajectory_transition_breakdown.csv",
                "trajectory_policy_label_breakdown_csv": "tables/trajectory_policy_label_breakdown.csv",
                "trajectory_gate_by_risk_band_csv": "tables/trajectory_gate_by_risk_band.csv",
                "trajectory_gate_by_income_band_csv": "tables/trajectory_gate_by_income_band.csv",
                "trajectory_phase_action_mix_csv": "tables/trajectory_phase_action_mix.csv",
            },
        }
    canonical_metrics = {
        field: _round_metric(pd.to_numeric(scale_df.get(field, pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean())
        for field in metric_fields
    }
    secondary_metrics = {
        field.replace("high_risk_denied_", ""): _round_metric(
            pd.to_numeric(scale_df.get(field, pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean()
        )
        for field in secondary_fields
    }
    dominant_transition_reason = ""
    if "trajectory_dominant_transition_reason" in scale_df.columns:
        reasons = scale_df["trajectory_dominant_transition_reason"].fillna("").astype(str)
        reasons = reasons[reasons != ""]
        if not reasons.empty:
            dominant_transition_reason = str(reasons.value_counts().idxmax())
    return {
        "canonical_population": "denied",
        "secondary_population": "high_risk_denied",
        "primary_checkpoint_week": 4,
        "checkpoint_priority_order": [4, 12, 24],
        "seed_count": int(len(scale_df)),
        "canonical_metrics": canonical_metrics,
        "secondary_metrics": secondary_metrics,
        "dominant_transition_reason": dominant_transition_reason,
        "supporting_artifacts": {
            "trajectory_transition_breakdown_csv": "tables/trajectory_transition_breakdown.csv",
            "trajectory_policy_label_breakdown_csv": "tables/trajectory_policy_label_breakdown.csv",
            "trajectory_gate_by_risk_band_csv": "tables/trajectory_gate_by_risk_band.csv",
            "trajectory_gate_by_income_band_csv": "tables/trajectory_gate_by_income_band.csv",
            "trajectory_phase_action_mix_csv": "tables/trajectory_phase_action_mix.csv",
        },
    }


def _build_phase_portfolio_validation_summary(seed_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    return aggregate_portfolio_validation_summaries(seed_summaries)


def _build_phase_portfolio_validation_review(summary: Mapping[str, Any]) -> str:
    return render_portfolio_validation_review(summary)


def _build_phase_trajectory_transition_breakdown(seed_breakdowns: list[pd.DataFrame]) -> pd.DataFrame:
    if not seed_breakdowns:
        return pd.DataFrame(
            columns=[
                "seed",
                "population",
                "risk_band",
                "trajectory_status",
                "current_phase",
                "phase_transition_reason",
                "count",
                "mean_next_review_week",
                "mean_soft_regression_penalty",
                "share",
                "breakdown_type",
            ]
        )
    frames: list[pd.DataFrame] = []
    for breakdown_df in seed_breakdowns:
        if breakdown_df.empty or "seed" not in breakdown_df.columns:
            continue
        working = breakdown_df.copy()
        working["breakdown_type"] = "seed_population_trajectory_transition"
        frames.append(working)
    if not frames:
        return pd.DataFrame(
            columns=[
                "seed",
                "population",
                "risk_band",
                "trajectory_status",
                "current_phase",
                "phase_transition_reason",
                "count",
                "mean_next_review_week",
                "mean_soft_regression_penalty",
                "share",
                "breakdown_type",
            ]
        )
    combined = pd.concat(frames, ignore_index=True)
    rollup = (
        combined.groupby(
            ["population", "risk_band", "trajectory_status", "current_phase", "phase_transition_reason"],
            dropna=False,
        )
        .agg(
            count=("count", "sum"),
            mean_next_review_week=("mean_next_review_week", "mean"),
            mean_soft_regression_penalty=("mean_soft_regression_penalty", "mean"),
            share=("share", "mean"),
        )
        .reset_index()
    )
    rollup["seed"] = -1
    rollup["breakdown_type"] = "population_trajectory_transition_rollup"
    return pd.concat([combined, rollup], ignore_index=True, sort=False)


def _build_phase_trajectory_policy_label_breakdown(seed_breakdowns: list[pd.DataFrame]) -> pd.DataFrame:
    if not seed_breakdowns:
        return pd.DataFrame(
            columns=[
                "seed",
                "population",
                "risk_band",
                "trajectory_policy_label",
                "count",
                "mean_policy_score",
                "share",
                "breakdown_type",
            ]
        )
    frames: list[pd.DataFrame] = []
    for breakdown_df in seed_breakdowns:
        if breakdown_df.empty or "seed" not in breakdown_df.columns:
            continue
        working = breakdown_df.copy()
        working["breakdown_type"] = "seed_population_trajectory_policy_label"
        frames.append(working)
    if not frames:
        return pd.DataFrame(
            columns=[
                "seed",
                "population",
                "risk_band",
                "trajectory_policy_label",
                "count",
                "mean_policy_score",
                "share",
                "breakdown_type",
            ]
        )
    combined = pd.concat(frames, ignore_index=True)
    rollup = (
        combined.groupby(["population", "risk_band", "trajectory_policy_label"], dropna=False)
        .agg(
            count=("count", "sum"),
            mean_policy_score=("mean_policy_score", "mean"),
            share=("share", "mean"),
        )
        .reset_index()
    )
    rollup["seed"] = -1
    rollup["breakdown_type"] = "population_trajectory_policy_label_rollup"
    return pd.concat([combined, rollup], ignore_index=True, sort=False)


def _build_phase_trajectory_gate_rollup(
    seed_breakdowns: list[pd.DataFrame],
    *,
    group_column: str,
) -> pd.DataFrame:
    if not seed_breakdowns:
        return pd.DataFrame(
            columns=[
                "seed",
                group_column,
                "population",
                "denied_count",
                "gate_pass_rate_4w",
                "gate_pass_rate_12w",
                "gate_pass_rate_24w",
                "partial_progress_rate",
                "median_pd_delta_24w",
                "breakdown_type",
            ]
        )
    frames: list[pd.DataFrame] = []
    for breakdown_df in seed_breakdowns:
        if breakdown_df.empty or "seed" not in breakdown_df.columns or group_column not in breakdown_df.columns:
            continue
        working = breakdown_df.copy()
        working["population"] = "denied"
        working["breakdown_type"] = f"seed_trajectory_gate_by_{group_column}"
        frames.append(working)
    if not frames:
        return pd.DataFrame(
            columns=[
                "seed",
                group_column,
                "population",
                "denied_count",
                "gate_pass_rate_4w",
                "gate_pass_rate_12w",
                "gate_pass_rate_24w",
                "partial_progress_rate",
                "median_pd_delta_24w",
                "breakdown_type",
            ]
        )
    combined = pd.concat(frames, ignore_index=True)
    rollup = (
        combined.groupby(["population", group_column], dropna=False)
        .agg(
            denied_count=("denied_count", "sum"),
            gate_pass_rate_4w=("gate_pass_rate_4w", "mean"),
            gate_pass_rate_12w=("gate_pass_rate_12w", "mean"),
            gate_pass_rate_24w=("gate_pass_rate_24w", "mean"),
            partial_progress_rate=("partial_progress_rate", "mean"),
            median_pd_delta_24w=("median_pd_delta_24w", "mean"),
        )
        .reset_index()
    )
    rollup["seed"] = -1
    rollup["breakdown_type"] = f"population_trajectory_gate_by_{group_column}_rollup"
    return pd.concat([combined, rollup], ignore_index=True, sort=False)


def _build_phase_trajectory_phase_action_mix(seed_breakdowns: list[pd.DataFrame]) -> pd.DataFrame:
    columns = [
        "seed",
        "phase_1_action_count_p50",
        "phase_2_action_count_p50",
        "phase_3_action_count_p50",
        "phase_1_action_count_p95",
        "phase_2_action_count_p95",
        "phase_3_action_count_p95",
        "breakdown_type",
    ]
    if not seed_breakdowns:
        return pd.DataFrame(columns=columns)
    frames: list[pd.DataFrame] = []
    for breakdown_df in seed_breakdowns:
        if breakdown_df.empty or "seed" not in breakdown_df.columns:
            continue
        working = breakdown_df.copy()
        working["breakdown_type"] = "seed_trajectory_phase_action_mix"
        frames.append(working)
    if not frames:
        return pd.DataFrame(columns=columns)
    combined = pd.concat(frames, ignore_index=True)
    numeric_cols = [
        "phase_1_action_count_p50",
        "phase_2_action_count_p50",
        "phase_3_action_count_p50",
        "phase_1_action_count_p95",
        "phase_2_action_count_p95",
        "phase_3_action_count_p95",
    ]
    rollup = {col: _round_metric(pd.to_numeric(combined[col], errors="coerce").fillna(0.0).mean()) for col in numeric_cols}
    rollup_df = pd.DataFrame([{**rollup, "seed": -1, "breakdown_type": "trajectory_phase_action_mix_rollup"}])
    return pd.concat([combined, rollup_df], ignore_index=True, sort=False)


def _build_phase_execution_probability_breakdown(seed_breakdowns: list[pd.DataFrame]) -> pd.DataFrame:
    if not seed_breakdowns:
        return pd.DataFrame(
            columns=[
                "seed",
                "population",
                "risk_band",
                "best_source",
                "count",
                "mean_plan_execution_probability",
                "expected_pd_improvement",
                "nominal_pd_improvement",
                "breakdown_type",
            ]
        )
    frames: list[pd.DataFrame] = []
    for breakdown_df in seed_breakdowns:
        if breakdown_df.empty or "seed" not in breakdown_df.columns:
            continue
        working = breakdown_df.copy()
        working["breakdown_type"] = "seed_probability_population_source"
        frames.append(working)
    if not frames:
        return pd.DataFrame(
            columns=[
                "seed",
                "population",
                "risk_band",
                "best_source",
                "count",
                "mean_plan_execution_probability",
                "expected_pd_improvement",
                "nominal_pd_improvement",
                "breakdown_type",
            ]
        )
    combined = pd.concat(frames, ignore_index=True)
    rollup = (
        combined.groupby(["population", "risk_band", "best_source"], dropna=False)
        .agg(
            count=("count", "sum"),
            mean_plan_execution_probability=("mean_plan_execution_probability", "mean"),
            expected_pd_improvement=("expected_pd_improvement", "mean"),
            nominal_pd_improvement=("nominal_pd_improvement", "mean"),
        )
        .reset_index()
    )
    rollup["seed"] = -1
    rollup["breakdown_type"] = "population_probability_source_rollup"
    return pd.concat([combined, rollup], ignore_index=True, sort=False)


def _build_phase_partial_execution_breakdown(seed_breakdowns: list[pd.DataFrame]) -> pd.DataFrame:
    if not seed_breakdowns:
        return pd.DataFrame(
            columns=[
                "seed",
                "population",
                "risk_band",
                "execution_scenario",
                "count",
                "share",
                "mean_execution_rate",
                "expected_partial_progress_rate",
                "max_missed_actions_streak",
                "breakdown_type",
            ]
        )
    frames: list[pd.DataFrame] = []
    for breakdown_df in seed_breakdowns:
        if breakdown_df.empty or "seed" not in breakdown_df.columns:
            continue
        working = breakdown_df.copy()
        working["breakdown_type"] = "seed_population_execution_scenario"
        frames.append(working)
    if not frames:
        return pd.DataFrame(
            columns=[
                "seed",
                "population",
                "risk_band",
                "execution_scenario",
                "count",
                "share",
                "mean_execution_rate",
                "expected_partial_progress_rate",
                "max_missed_actions_streak",
                "breakdown_type",
            ]
        )
    combined = pd.concat(frames, ignore_index=True)
    rollup = (
        combined.groupby(["population", "risk_band", "execution_scenario"], dropna=False)
        .agg(
            count=("count", "sum"),
            share=("share", "mean"),
            mean_execution_rate=("mean_execution_rate", "mean"),
            expected_partial_progress_rate=("expected_partial_progress_rate", "mean"),
            max_missed_actions_streak=("max_missed_actions_streak", "max"),
        )
        .reset_index()
    )
    rollup["seed"] = -1
    rollup["breakdown_type"] = "population_execution_scenario_rollup"
    return pd.concat([combined, rollup], ignore_index=True, sort=False)


def _build_phase_candidate_source_breakdown(seed_breakdowns: list[pd.DataFrame]) -> pd.DataFrame:
    if not seed_breakdowns:
        return pd.DataFrame(
            columns=["seed", "population", "candidate_source", "count", "share", "population_size", "breakdown_type"]
        )
    frames: list[pd.DataFrame] = []
    for breakdown_df in seed_breakdowns:
        if breakdown_df.empty:
            continue
        working = breakdown_df.copy()
        if "seed" not in working.columns:
            continue
        working["breakdown_type"] = "seed_population_source"
        frames.append(working)
    if not frames:
        return pd.DataFrame(
            columns=["seed", "population", "candidate_source", "count", "share", "population_size", "breakdown_type"]
        )
    combined = pd.concat(frames, ignore_index=True)
    rollup = (
        combined.groupby(["population", "candidate_source"], dropna=False)
        .agg(
            count=("count", "sum"),
            share=("share", "mean"),
            population_size=("population_size", "sum"),
        )
        .reset_index()
    )
    rollup["seed"] = -1
    rollup["breakdown_type"] = "population_source_rollup"
    if "share" in rollup.columns:
        rollup["share"] = pd.to_numeric(rollup["share"], errors="coerce").fillna(0.0).round(6)
    return pd.concat([combined, rollup], ignore_index=True, sort=False)


def _seed_direction_consistent(values: pd.Series) -> bool:
    series = pd.to_numeric(values, errors="coerce").fillna(0.0)
    positive = int((series > 1e-9).sum())
    negative = int((series < -1e-9).sum())
    nonzero = positive + negative
    if nonzero == 0:
        return True
    return max(positive, negative) >= ((nonzero // 2) + 1)


def _build_phase_high_risk_tuning_summary(
    scale_df: pd.DataFrame,
    *,
    release_decision: str,
) -> dict[str, Any]:
    if scale_df.empty:
        return {
            "primary_metric": "denied_high_risk_lift",
            "primary_metric_value": 0.0,
            "high_risk_profile_applied_rate": 0.0,
            "activation_floor": _HIGH_RISK_ACTIVATION_FLOOR,
            "meaningful_activation": False,
            "directional_consistency": False,
            "positive_seed_count": 0,
            "negative_seed_count": 0,
            "evidence_status": "diagnostic_only",
            "diagnostic_reasons": ["missing_seeded_rows"],
            "supporting_metrics": {
                "high_risk_reachability_rate": 0.0,
                "trajectory_partial_progress_rate": 0.0,
            },
        }

    primary_series = pd.to_numeric(scale_df.get("denied_high_risk_lift", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    activation_rate = _round_metric(
        pd.to_numeric(scale_df.get("high_risk_profile_applied_rate", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean()
    )
    supporting_metrics = {
        "high_risk_reachability_rate": _round_metric(
            pd.to_numeric(scale_df.get("high_risk_reachability_rate", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean()
        ),
        "trajectory_partial_progress_rate": _round_metric(
            pd.to_numeric(scale_df.get("trajectory_partial_progress_rate", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean()
        ),
    }
    positive_seed_count = int((primary_series > 1e-9).sum())
    negative_seed_count = int((primary_series < -1e-9).sum())
    diagnostic_reasons: list[str] = []
    if activation_rate < _HIGH_RISK_ACTIVATION_FLOOR:
        diagnostic_reasons.append("activation_below_min_floor")
    if not _seed_direction_consistent(primary_series):
        diagnostic_reasons.append("seed_direction_unstable")
    if str(release_decision).strip().upper() == "NO_GO":
        diagnostic_reasons.append("release_gate_not_satisfied")
    if supporting_metrics["high_risk_reachability_rate"] <= 0.0:
        diagnostic_reasons.append("reachability_signal_not_positive")
    if supporting_metrics["trajectory_partial_progress_rate"] <= 0.0:
        diagnostic_reasons.append("trajectory_signal_not_positive")
    return {
        "primary_metric": "denied_high_risk_lift",
        "primary_metric_value": _round_metric(primary_series.mean()),
        "high_risk_profile_applied_rate": activation_rate,
        "activation_floor": _HIGH_RISK_ACTIVATION_FLOOR,
        "meaningful_activation": bool(activation_rate >= _HIGH_RISK_ACTIVATION_FLOOR),
        "directional_consistency": _seed_direction_consistent(primary_series),
        "positive_seed_count": positive_seed_count,
        "negative_seed_count": negative_seed_count,
        "evidence_status": "strong_evidence" if not diagnostic_reasons else "diagnostic_only",
        "diagnostic_reasons": diagnostic_reasons,
        "supporting_metrics": supporting_metrics,
    }


def _build_suite_impact_attribution_summary(
    *,
    phase_name: str,
    aggregate: dict[str, Any],
    evidence_level: str,
    evidence_status: str,
    seed_count: int,
) -> dict[str, Any]:
    return build_comparative_impact_summary(
        subject_label=str(phase_name),
        baseline_label="control_variant_unavailable",
        subject_metrics={
            "denied_to_approved_lift": aggregate.get("mean_denied_to_approved_lift", 0.0),
            "denied_high_risk_lift": aggregate.get("mean_denied_high_risk_lift", 0.0),
            "equalized_odds_gap_delta": aggregate.get("mean_equalized_odds_gap_delta", 0.0),
            "denied_reliability_violation_rate": aggregate.get("mean_denied_reliability_violation_rate", 0.0),
            "high_risk_reachability_rate": aggregate.get("mean_high_risk_reachability_rate", 0.0),
            "trajectory_partial_progress_rate": aggregate.get("mean_trajectory_partial_progress_rate", 0.0),
            "candidate_source_entropy": aggregate.get("mean_candidate_source_entropy", 0.0),
        },
        baseline_metrics=None,
        evidence_level=evidence_level,
        evidence_status=evidence_status,
        seed_count=seed_count,
        baseline_type="control_variant",
        diagnostic_reason="control_variant_baseline_not_available_in_suite_runner",
        metadata={
            "source_mix_snapshot": {
                "best_source_internal_rate": _round_metric(aggregate.get("mean_best_source_internal_rate", 0.0)),
                "best_source_dice_rate": _round_metric(aggregate.get("mean_best_source_dice_rate", 0.0)),
                "best_source_rule_rate": _round_metric(aggregate.get("mean_best_source_rule_rate", 0.0)),
                "best_source_fallback_rate": _round_metric(aggregate.get("mean_best_source_fallback_rate", 0.0)),
            }
        },
    )


def _render_release_review_summary(
    *,
    milestone_acceptance_summary: dict[str, Any],
) -> str:
    return render_milestone_acceptance_review(milestone_acceptance_summary)


def main() -> None:
    args = parse_args()
    seeds = _parse_seeds(args.scale_seeds)
    thresholds = load_kpi_thresholds(args.kpi_contract)
    root = _project_root()
    registry_path = _build_registry_path(root, args.model_config)
    explicit_model_version = str(args.model_version).strip()
    explicit_model_manifest = str(args.model_manifest).strip()
    if (explicit_model_version or explicit_model_manifest) and not bool(args.skip_train_before_batch):
        raise ValueError("Explicit model selectors require --skip_train_before_batch so suite execution stays unambiguous")

    run_ctx = create_run_context(
        {
            "mode": "phase_experiment_suite",
            "phase_name": str(args.phase_name),
            "quick_n": int(args.quick_n),
            "quick_seed": int(args.quick_seed),
            "scale_n": int(args.scale_n),
            "scale_seeds": seeds,
            "execute": bool(args.execute),
            "recourse_config": str(args.recourse_config),
        },
        base_artifact_dir="artifacts/runs",
    )

    if not args.execute:
        dry = {
            "train_once_cmd": _train_cmd(args),
            "quick_batch_cmd": _batch_cmd(
                args,
                n_customers=int(args.quick_n),
                seed=int(args.quick_seed),
                model_version=explicit_model_version,
                model_manifest=explicit_model_manifest,
            ),
            "scale_batch_cmd_template": _batch_cmd(
                args,
                n_customers=int(args.scale_n),
                seed=seeds[0],
                model_version=explicit_model_version,
                model_manifest=explicit_model_manifest,
            ),
            "scale_seeds": seeds,
            "skip_train_before_batch": bool(args.skip_train_before_batch),
            "requested_model_version": explicit_model_version,
            "requested_model_manifest": explicit_model_manifest,
        }
        (run_ctx.tables_dir / "phase_suite_dry_run.json").write_text(json.dumps(dry, indent=2, ensure_ascii=False), encoding="utf-8")
        run_ctx.save_metrics({"execute": False, "seed_count": len(seeds)})
        logger.info("Dry-run saved: %s", run_ctx.tables_dir / "phase_suite_dry_run.json")
        return

    outcome_feedback_summary_source = _latest_optional_artifact("*/tables/outcome_feedback_summary.json")
    outcome_policy_summary_source = _latest_optional_artifact("*/tables/outcome_policy_summary.csv")
    outcome_policy_deltas_source = _latest_optional_artifact("*/tables/outcome_policy_deltas.json")
    outcome_ingestion_summary_source = _latest_optional_artifact("*/tables/outcome_ingestion_summary.json")
    off_policy_evaluation_source = _latest_optional_artifact("*/tables/off_policy_evaluation.json")
    outcome_learning_dataset_source = _latest_optional_artifact("*/tables/outcome_learning_dataset.csv")
    mirrored_outcome_feedback = _mirror_artifact(
        outcome_feedback_summary_source,
        run_ctx.tables_dir / "outcome_feedback_summary.json",
    )
    mirrored_outcome_policy_summary = _mirror_artifact(
        outcome_policy_summary_source,
        run_ctx.tables_dir / "outcome_policy_summary.csv",
    )
    mirrored_outcome_policy_deltas = _mirror_artifact(
        outcome_policy_deltas_source,
        run_ctx.tables_dir / "outcome_policy_deltas.json",
    )
    mirrored_outcome_ingestion_summary = _mirror_artifact(
        outcome_ingestion_summary_source,
        run_ctx.tables_dir / "outcome_ingestion_summary.json",
    )
    mirrored_off_policy_evaluation = _mirror_artifact(
        off_policy_evaluation_source,
        run_ctx.tables_dir / "off_policy_evaluation.json",
    )
    mirrored_outcome_learning_dataset = _mirror_artifact(
        outcome_learning_dataset_source,
        run_ctx.tables_dir / "outcome_learning_dataset.csv",
    )
    outcome_feedback_summary = (
        json.loads((run_ctx.tables_dir / "outcome_feedback_summary.json").read_text(encoding="utf-8"))
        if mirrored_outcome_feedback
        else {}
    )
    outcome_ingestion_summary = (
        json.loads((run_ctx.tables_dir / "outcome_ingestion_summary.json").read_text(encoding="utf-8"))
        if mirrored_outcome_ingestion_summary
        else {}
    )
    off_policy_evaluation = (
        json.loads((run_ctx.tables_dir / "off_policy_evaluation.json").read_text(encoding="utf-8"))
        if mirrored_off_policy_evaluation
        else {}
    )

    env = dict(os.environ)
    env.setdefault("MPLCONFIGDIR", "/tmp/mplcache")
    env.setdefault("TQDM_DISABLE", "1")

    train_run_id = ""
    resolved_model_manifest: dict[str, Any]
    if not bool(args.skip_train_before_batch):
        train_run_id, train_log = _run_cmd(
            cmd=_train_cmd(args),
            cwd=root,
            env=env,
            label="train_once",
        )
        (run_ctx.tables_dir / "train_once.log").write_text(train_log, encoding="utf-8")
        resolved_model_manifest = resolve_model_manifest(
            base_path=registry_path,
            model_version=train_run_id,
        )
    elif explicit_model_version or explicit_model_manifest:
        resolved_model_manifest = resolve_model_manifest(
            base_path=registry_path,
            model_version=explicit_model_version or None,
            manifest_path=explicit_model_manifest or None,
        )
    else:
        resolved_model_manifest = resolve_model_manifest(base_path=registry_path)
    frozen_model_manifest = build_frozen_model_manifest(
        resolved_model_manifest,
        project_root=root,
        resolved_by_runner="run_phase_experiment_suite",
        training_run_id=train_run_id or str(resolved_model_manifest.get("model_version", "")).strip(),
    )
    (run_ctx.tables_dir / "frozen_model_manifest.json").write_text(
        json.dumps(frozen_model_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    quick_run_id, quick_log = _run_cmd(
        cmd=_batch_cmd(
            args,
            n_customers=int(args.quick_n),
            seed=int(args.quick_seed),
            model_manifest=str(resolved_model_manifest.get("manifest_path", "")),
        ),
        cwd=root,
        env=env,
        label="quick_batch",
    )
    (run_ctx.tables_dir / "quick_batch.log").write_text(quick_log, encoding="utf-8")

    quick_smoke_run_id, quick_smoke_log = _run_cmd(
        cmd=_smoke_cmd(args, batch_run_id=quick_run_id),
        cwd=root,
        env=env,
        label="quick_smoke",
    )
    (run_ctx.tables_dir / "quick_smoke.log").write_text(quick_smoke_log, encoding="utf-8")

    quick_summary = _load_json(root / "artifacts" / "runs" / quick_run_id / "tables" / "batch_summary.json")
    quick_fair = pd.read_csv(root / "artifacts" / "runs" / quick_run_id / "tables" / "batch_fairness_change.csv").iloc[0].to_dict()
    quick_snapshot = _seed_contract_snapshot(quick_summary, quick_fair, thresholds)
    quick_ok = bool(quick_snapshot["all_pass"])
    quick_failed = str(quick_snapshot["failed_checks"])
    quick_payload = {
        "run_id": quick_run_id,
        "smoke_run_id": quick_smoke_run_id,
        "all_pass": bool(quick_ok),
        "failed_checks": quick_failed,
        "lift_pass": bool(quick_snapshot["lift_pass"]),
        "reliability_pass": bool(quick_snapshot["reliability_pass"]),
        "fairness_seed_pass": bool(quick_snapshot["fairness_seed_pass"]),
        "primary_fail_reason": str(quick_snapshot["primary_fail_reason"]),
        "worst_fairness_gap": float(quick_snapshot["worst_fairness_gap"]),
        "model_version": str(resolved_model_manifest.get("model_version", "")),
        "model_freeze_mode": str(resolved_model_manifest.get("freeze_mode", "implicit_latest")),
    }
    (run_ctx.tables_dir / "phase_quick_summary.json").write_text(json.dumps(quick_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    scale_rows: list[dict[str, Any]] = []
    seed_breakdowns: list[pd.DataFrame] = []
    seed_candidate_source_breakdowns: list[pd.DataFrame] = []
    seed_execution_probability_breakdowns: list[pd.DataFrame] = []
    seed_partial_execution_breakdowns: list[pd.DataFrame] = []
    seed_offer_type_breakdowns: list[pd.DataFrame] = []
    seed_offer_policy_arm_breakdowns: list[pd.DataFrame] = []
    seed_offer_acceptance_breakdowns: list[pd.DataFrame] = []
    seed_offer_proxy_impact_breakdowns: list[pd.DataFrame] = []
    seed_trajectory_transition_breakdowns: list[pd.DataFrame] = []
    seed_trajectory_policy_label_breakdowns: list[pd.DataFrame] = []
    seed_trajectory_gate_by_risk_breakdowns: list[pd.DataFrame] = []
    seed_trajectory_gate_by_income_breakdowns: list[pd.DataFrame] = []
    seed_trajectory_phase_action_mix_breakdowns: list[pd.DataFrame] = []
    seed_portfolio_validation_summaries: list[dict[str, Any]] = []
    seed_portfolio_coverage_breakdowns: list[pd.DataFrame] = []
    seed_portfolio_coverage_drop_breakdowns: list[pd.DataFrame] = []
    seed_portfolio_reality_gap_breakdowns: list[pd.DataFrame] = []
    seed_portfolio_segment_breakdowns: list[pd.DataFrame] = []
    seed_portfolio_offer_diagnostics: list[pd.DataFrame] = []
    seed_portfolio_behavior_comparisons: list[pd.DataFrame] = []
    seed_portfolio_trajectory_class_breakdowns: list[pd.DataFrame] = []
    seed_demo_representativeness_summaries: list[dict[str, Any]] = []
    seed_decision_logging_summaries: list[dict[str, Any]] = []
    for seed in seeds:
        run_id, run_log = _run_cmd(
            cmd=_batch_cmd(
                args,
                n_customers=int(args.scale_n),
                seed=int(seed),
                model_manifest=str(resolved_model_manifest.get("manifest_path", "")),
            ),
            cwd=root,
            env=env,
            label=f"scale_batch_seed_{seed}",
        )
        (run_ctx.tables_dir / f"scale_seed_{seed}.log").write_text(run_log, encoding="utf-8")

        summary = _load_json(root / "artifacts" / "runs" / run_id / "tables" / "batch_summary.json")
        fair_row = pd.read_csv(root / "artifacts" / "runs" / run_id / "tables" / "batch_fairness_change.csv").iloc[0].to_dict()
        breakdown_df = _load_csv(root / "artifacts" / "runs" / run_id / "tables" / "fairness_failure_breakdown.csv")
        candidate_quality_summary = _load_json(
            root / "artifacts" / "runs" / run_id / "tables" / "candidate_quality_summary.json"
        )
        candidate_source_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "candidate_source_breakdown.csv"
        )
        behavior_aware_summary = _load_json(
            root / "artifacts" / "runs" / run_id / "tables" / "behavior_aware_summary.json"
        )
        offer_optimization_summary = _load_json(
            root / "artifacts" / "runs" / run_id / "tables" / "offer_optimization_summary.json"
        )
        trajectory_summary = _load_json(root / "artifacts" / "runs" / run_id / "tables" / "trajectory_summary.json")
        portfolio_validation_summary = _load_json(
            root / "artifacts" / "runs" / run_id / "tables" / "portfolio_validation_summary.json"
        )
        execution_probability_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "execution_probability_breakdown.csv"
        )
        partial_execution_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "partial_execution_breakdown.csv"
        )
        offer_type_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "offer_type_breakdown.csv"
        )
        offer_policy_arm_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "offer_policy_arm_breakdown.csv"
        )
        offer_acceptance_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "offer_acceptance_breakdown.csv"
        )
        offer_proxy_impact_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "offer_proxy_impact_breakdown.csv"
        )
        trajectory_transition_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "trajectory_transition_breakdown.csv"
        )
        trajectory_policy_label_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "trajectory_policy_label_breakdown.csv"
        )
        trajectory_gate_by_risk_band = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "trajectory_gate_by_risk_band.csv"
        )
        trajectory_gate_by_income_band = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "trajectory_gate_by_income_band.csv"
        )
        trajectory_phase_action_mix = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "trajectory_phase_action_mix.csv"
        )
        portfolio_coverage_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "portfolio_coverage_breakdown.csv"
        )
        portfolio_coverage_drop_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "portfolio_coverage_drop_breakdown.csv"
        )
        portfolio_reality_gap_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "portfolio_reality_gap_breakdown.csv"
        )
        portfolio_segment_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "portfolio_segment_breakdown.csv"
        )
        portfolio_offer_diagnostics = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "portfolio_offer_diagnostics.csv"
        )
        portfolio_behavior_comparison = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "portfolio_behavior_comparison.csv"
        )
        portfolio_trajectory_class_breakdown = _load_csv(
            root / "artifacts" / "runs" / run_id / "tables" / "portfolio_trajectory_class_breakdown.csv"
        )
        demo_representativeness_summary = _load_json(
            root / "artifacts" / "runs" / run_id / "tables" / "demo_representativeness_summary.json"
        )
        decision_logging_summary = _load_json(
            root / "artifacts" / "runs" / run_id / "tables" / "decision_logging_summary.json"
        )
        canonical_candidate_metrics = (
            candidate_quality_summary.get("canonical_metrics", {})
            if isinstance(candidate_quality_summary.get("canonical_metrics", {}), dict)
            else {}
        )
        secondary_candidate_metrics = (
            candidate_quality_summary.get("secondary_metrics", {})
            if isinstance(candidate_quality_summary.get("secondary_metrics", {}), dict)
            else {}
        )
        canonical_behavior_metrics = (
            behavior_aware_summary.get("canonical_metrics", {})
            if isinstance(behavior_aware_summary.get("canonical_metrics", {}), dict)
            else {}
        )
        secondary_behavior_metrics = (
            behavior_aware_summary.get("secondary_metrics", {})
            if isinstance(behavior_aware_summary.get("secondary_metrics", {}), dict)
            else {}
        )
        canonical_offer_metrics = (
            offer_optimization_summary.get("canonical_metrics", {})
            if isinstance(offer_optimization_summary.get("canonical_metrics", {}), dict)
            else {}
        )
        canonical_trajectory_metrics = (
            trajectory_summary.get("canonical_metrics", {})
            if isinstance(trajectory_summary.get("canonical_metrics", {}), dict)
            else {}
        )
        secondary_trajectory_metrics = (
            trajectory_summary.get("secondary_metrics", {})
            if isinstance(trajectory_summary.get("secondary_metrics", {}), dict)
            else {}
        )
        canonical_portfolio_metrics = (
            portfolio_validation_summary.get("canonical_metrics", {})
            if isinstance(portfolio_validation_summary.get("canonical_metrics", {}), dict)
            else {}
        )
        secondary_portfolio_metrics = (
            portfolio_validation_summary.get("secondary_metrics", {})
            if isinstance(portfolio_validation_summary.get("secondary_metrics", {}), dict)
            else {}
        )
        snapshot = _seed_contract_snapshot(summary, fair_row, thresholds)
        scale_rows.append(
            {
                "seed": int(seed),
                "run_id": run_id,
                "model_version": str(summary.get("model_version", resolved_model_manifest.get("model_version", ""))),
                "model_freeze_mode": str(summary.get("model_freeze_mode", resolved_model_manifest.get("freeze_mode", "implicit_latest"))),
                "all_pass": int(snapshot["all_pass"]),
                "failed_checks": str(snapshot["failed_checks"]),
                "lift_pass": int(snapshot["lift_pass"]),
                "reliability_pass": int(snapshot["reliability_pass"]),
                "fairness_seed_pass": int(snapshot["fairness_seed_pass"]),
                "primary_fairness_metric": str(snapshot["primary_fairness_metric"]),
                "primary_fail_reason": str(snapshot["primary_fail_reason"]),
                "worst_fairness_gap": float(snapshot["worst_fairness_gap"]),
                "denied_to_approved_lift": float(summary.get("denied_to_approved_lift", 0.0)),
                "denied_high_risk_lift": float(summary.get("denied_high_risk_lift", 0.0)),
                "high_risk_reachability_rate": float(summary.get("high_risk_reachability_rate", 0.0)),
                "denied_reliability_violation_rate": float(summary.get("denied_reliability_violation_rate", 0.0)),
                "sync_latency_p95_ms": float(summary.get("sync_latency_p95_ms", summary.get("latency_p95_ms", 0.0))),
                "sync_latency_p99_ms": float(summary.get("sync_latency_p99_ms", summary.get("latency_p99_ms", 0.0))),
                "equalized_odds_gap_delta": float(snapshot["equalized_odds_gap_delta"]),
                "approval_gap_delta": float(snapshot["approval_gap_delta"]),
                "recourse_success_gap": float(snapshot["recourse_success_gap"]),
                "fairness_gap_after": float(snapshot["fairness_gap_after"]),
                "high_stress_fairness_gap_after": float(snapshot["high_stress_fairness_gap_after"]),
                "fairness_guard_demotion_count": int(summary.get("fairness_guard_demotion_count", 0)),
                "fairness_guard_stop_reason": str(summary.get("fairness_guard_stop_reason", "")),
                "error_rate": float(summary.get("error_rate", 0.0)),
                "trajectory_gate_pass_rate_4w": float(summary.get("trajectory_gate_pass_rate_4w", 0.0)),
                "trajectory_gate_pass_rate_12w": float(summary.get("trajectory_gate_pass_rate_12w", 0.0)),
                "trajectory_gate_pass_rate_24w": float(summary.get("trajectory_gate_pass_rate_24w", 0.0)),
                "trajectory_partial_progress_rate": float(summary.get("trajectory_partial_progress_rate", 0.0)),
                "trajectory_median_time_to_gate_pass_days": float(summary.get("trajectory_median_time_to_gate_pass_days", 9_999.0)),
                "trajectory_soft_regression_penalty_mean": float(
                    canonical_trajectory_metrics.get(
                        "trajectory_soft_regression_penalty_mean",
                        summary.get("trajectory_soft_regression_penalty_mean", 0.0),
                    )
                ),
                "trajectory_on_track_rate": float(
                    canonical_trajectory_metrics.get(
                        "trajectory_on_track_rate",
                        summary.get("trajectory_on_track_rate", 0.0),
                    )
                ),
                "trajectory_needs_replan_rate": float(
                    canonical_trajectory_metrics.get(
                        "trajectory_needs_replan_rate",
                        summary.get("trajectory_needs_replan_rate", 0.0),
                    )
                ),
                "trajectory_degraded_rate": float(
                    canonical_trajectory_metrics.get(
                        "trajectory_degraded_rate",
                        summary.get("trajectory_degraded_rate", 0.0),
                    )
                ),
                "trajectory_dominant_transition_reason": str(
                    trajectory_summary.get(
                        "dominant_transition_reason",
                        summary.get("trajectory_dominant_transition_reason", ""),
                    )
                ),
                "trajectory_stabilize_first_rate": float(
                    canonical_trajectory_metrics.get(
                        "trajectory_stabilize_first_rate",
                        summary.get("trajectory_stabilize_first_rate", 0.0),
                    )
                ),
                "trajectory_balanced_progress_rate": float(
                    canonical_trajectory_metrics.get(
                        "trajectory_balanced_progress_rate",
                        summary.get("trajectory_balanced_progress_rate", 0.0),
                    )
                ),
                "trajectory_long_horizon_heavy_rate": float(
                    canonical_trajectory_metrics.get(
                        "trajectory_long_horizon_heavy_rate",
                        summary.get("trajectory_long_horizon_heavy_rate", 0.0),
                    )
                ),
                "high_risk_denied_trajectory_gate_pass_rate_4w": float(
                    secondary_trajectory_metrics.get(
                        "trajectory_gate_pass_rate_4w",
                        summary.get("high_risk_denied_trajectory_gate_pass_rate_4w", 0.0),
                    )
                ),
                "high_risk_denied_trajectory_gate_pass_rate_12w": float(
                    secondary_trajectory_metrics.get(
                        "trajectory_gate_pass_rate_12w",
                        summary.get("high_risk_denied_trajectory_gate_pass_rate_12w", 0.0),
                    )
                ),
                "high_risk_denied_trajectory_gate_pass_rate_24w": float(
                    secondary_trajectory_metrics.get(
                        "trajectory_gate_pass_rate_24w",
                        summary.get("high_risk_denied_trajectory_gate_pass_rate_24w", 0.0),
                    )
                ),
                "high_risk_denied_trajectory_partial_progress_rate": float(
                    secondary_trajectory_metrics.get(
                        "trajectory_partial_progress_rate",
                        summary.get("high_risk_denied_trajectory_partial_progress_rate", 0.0),
                    )
                ),
                "high_risk_denied_trajectory_median_time_to_gate_pass_days": float(
                    secondary_trajectory_metrics.get(
                        "trajectory_median_time_to_gate_pass_days",
                        summary.get("high_risk_denied_trajectory_median_time_to_gate_pass_days", 9_999.0),
                    )
                ),
                "high_risk_denied_trajectory_soft_regression_penalty_mean": float(
                    secondary_trajectory_metrics.get(
                        "trajectory_soft_regression_penalty_mean",
                        summary.get("high_risk_denied_trajectory_soft_regression_penalty_mean", 0.0),
                    )
                ),
                "high_risk_denied_trajectory_on_track_rate": float(
                    secondary_trajectory_metrics.get(
                        "trajectory_on_track_rate",
                        summary.get("high_risk_denied_trajectory_on_track_rate", 0.0),
                    )
                ),
                "high_risk_denied_trajectory_needs_replan_rate": float(
                    secondary_trajectory_metrics.get(
                        "trajectory_needs_replan_rate",
                        summary.get("high_risk_denied_trajectory_needs_replan_rate", 0.0),
                    )
                ),
                "high_risk_denied_trajectory_degraded_rate": float(
                    secondary_trajectory_metrics.get(
                        "trajectory_degraded_rate",
                        summary.get("high_risk_denied_trajectory_degraded_rate", 0.0),
                    )
                ),
                "high_risk_profile_applied_rate": float(summary.get("high_risk_profile_applied_rate", 0.0)),
                "decision_log_completeness": float(decision_logging_summary.get("decision_log_completeness", 0.0)),
                "candidate_quality_population": str(candidate_quality_summary.get("canonical_population", "denied")),
                "candidate_quality_secondary_population": str(
                    candidate_quality_summary.get("secondary_population", "high_risk_denied")
                ),
                "candidate_pool_diversity_index": float(
                    canonical_candidate_metrics.get("candidate_pool_diversity_index", summary.get("denied_candidate_pool_diversity_index", 0.0))
                ),
                "candidate_source_entropy": float(
                    canonical_candidate_metrics.get("candidate_source_entropy", summary.get("denied_candidate_source_entropy", 0.0))
                ),
                "best_source_internal_rate": float(
                    canonical_candidate_metrics.get("best_source_internal_rate", summary.get("denied_best_source_internal_rate", 0.0))
                ),
                "best_source_dice_rate": float(
                    canonical_candidate_metrics.get("best_source_dice_rate", summary.get("denied_best_source_dice_rate", 0.0))
                ),
                "best_source_rule_rate": float(
                    canonical_candidate_metrics.get("best_source_rule_rate", summary.get("denied_best_source_rule_rate", 0.0))
                ),
                "best_source_fallback_rate": float(
                    canonical_candidate_metrics.get("best_source_fallback_rate", summary.get("denied_best_source_fallback_rate", 0.0))
                ),
                "high_risk_denied_candidate_pool_diversity_index": float(
                    secondary_candidate_metrics.get(
                        "candidate_pool_diversity_index",
                        summary.get("high_risk_denied_candidate_pool_diversity_index", 0.0),
                    )
                ),
                "high_risk_denied_candidate_source_entropy": float(
                    secondary_candidate_metrics.get(
                        "candidate_source_entropy",
                        summary.get("high_risk_denied_candidate_source_entropy", 0.0),
                    )
                ),
                "high_risk_denied_best_source_internal_rate": float(
                    secondary_candidate_metrics.get(
                        "best_source_internal_rate",
                        summary.get("high_risk_denied_best_source_internal_rate", 0.0),
                    )
                ),
                "high_risk_denied_best_source_dice_rate": float(
                    secondary_candidate_metrics.get(
                        "best_source_dice_rate",
                        summary.get("high_risk_denied_best_source_dice_rate", 0.0),
                    )
                ),
                "high_risk_denied_best_source_rule_rate": float(
                    secondary_candidate_metrics.get(
                        "best_source_rule_rate",
                        summary.get("high_risk_denied_best_source_rule_rate", 0.0),
                    )
                ),
                "high_risk_denied_best_source_fallback_rate": float(
                    secondary_candidate_metrics.get(
                        "best_source_fallback_rate",
                        summary.get("high_risk_denied_best_source_fallback_rate", 0.0),
                    )
                ),
                "mean_plan_execution_probability": float(
                    canonical_behavior_metrics.get(
                        "mean_plan_execution_probability",
                        summary.get("mean_plan_execution_probability", 0.0),
                    )
                ),
                "expected_pd_improvement": float(
                    canonical_behavior_metrics.get(
                        "expected_pd_improvement",
                        summary.get("expected_pd_improvement", 0.0),
                    )
                ),
                "partial_execution_rate": float(
                    canonical_behavior_metrics.get(
                        "partial_execution_rate",
                        summary.get("partial_execution_rate", 0.0),
                    )
                ),
                "failed_execution_rate": float(
                    canonical_behavior_metrics.get(
                        "failed_execution_rate",
                        summary.get("failed_execution_rate", 0.0),
                    )
                ),
                "mixed_execution_rate": float(
                    canonical_behavior_metrics.get(
                        "mixed_execution_rate",
                        summary.get("mixed_execution_rate", 0.0),
                    )
                ),
                "expected_partial_progress_rate": float(
                    canonical_behavior_metrics.get(
                        "expected_partial_progress_rate",
                        summary.get("expected_partial_progress_rate", 0.0),
                    )
                ),
                "high_risk_denied_mean_plan_execution_probability": float(
                    secondary_behavior_metrics.get(
                        "mean_plan_execution_probability",
                        summary.get("high_risk_denied_mean_plan_execution_probability", 0.0),
                    )
                ),
                "high_risk_denied_expected_pd_improvement": float(
                    secondary_behavior_metrics.get(
                        "expected_pd_improvement",
                        summary.get("high_risk_denied_expected_pd_improvement", 0.0),
                    )
                ),
                "high_risk_denied_partial_execution_rate": float(
                    secondary_behavior_metrics.get(
                        "partial_execution_rate",
                        summary.get("high_risk_denied_partial_execution_rate", 0.0),
                    )
                ),
                "high_risk_denied_failed_execution_rate": float(
                    secondary_behavior_metrics.get(
                        "failed_execution_rate",
                        summary.get("high_risk_denied_failed_execution_rate", 0.0),
                    )
                ),
                "high_risk_denied_mixed_execution_rate": float(
                    secondary_behavior_metrics.get(
                        "mixed_execution_rate",
                        summary.get("high_risk_denied_mixed_execution_rate", 0.0),
                    )
                ),
                "high_risk_denied_expected_partial_progress_rate": float(
                    secondary_behavior_metrics.get(
                        "expected_partial_progress_rate",
                        summary.get("high_risk_denied_expected_partial_progress_rate", 0.0),
                    )
                ),
                "offer_plan_rate": float(
                    canonical_offer_metrics.get("offer_plan_rate", summary.get("offer_plan_rate", 0.0))
                ),
                "rankable_offer_rate": float(
                    canonical_offer_metrics.get("rankable_offer_rate", summary.get("rankable_offer_rate", 0.0))
                ),
                "offer_acceptance_probability_mean": float(
                    canonical_offer_metrics.get(
                        "offer_acceptance_probability_mean",
                        summary.get("offer_acceptance_probability_mean", 0.0),
                    )
                ),
                "combined_plan_realization_probability_mean": float(
                    canonical_offer_metrics.get(
                        "combined_plan_realization_probability_mean",
                        summary.get("combined_plan_realization_probability_mean", 0.0),
                    )
                ),
                "expected_recovery_proxy": float(
                    canonical_offer_metrics.get("expected_recovery_proxy", summary.get("expected_recovery_proxy", 0.0))
                ),
                "approval_rate_proxy_delta": float(
                    canonical_offer_metrics.get("approval_rate_proxy_delta", summary.get("approval_rate_proxy_delta", 0.0))
                ),
                "default_rate_90d_proxy_delta": float(
                    canonical_offer_metrics.get(
                        "default_rate_90d_proxy_delta",
                        summary.get("default_rate_90d_proxy_delta", 0.0),
                    )
                ),
                "avg_margin_90d_proxy_delta": float(
                    canonical_offer_metrics.get(
                        "avg_margin_90d_proxy_delta",
                        summary.get("avg_margin_90d_proxy_delta", 0.0),
                    )
                ),
                "governance_safe_offer_rate": float(
                    canonical_offer_metrics.get(
                        "governance_safe_offer_rate",
                        summary.get("governance_safe_offer_rate", 0.0),
                    )
                ),
                "dominant_offer_type": str(
                    canonical_offer_metrics.get("dominant_offer_type", summary.get("dominant_offer_type", ""))
                ),
                "portfolio_raw_plan_coverage": float(
                    canonical_portfolio_metrics.get("raw_plan_coverage", 0.0)
                ),
                "portfolio_valid_plan_coverage": float(
                    canonical_portfolio_metrics.get("valid_plan_coverage", 0.0)
                ),
                "portfolio_governance_safe_plan_coverage": float(
                    canonical_portfolio_metrics.get("governance_safe_plan_coverage", 0.0)
                ),
                "portfolio_product_ready_plan_coverage": float(
                    canonical_portfolio_metrics.get("product_ready_plan_coverage", 0.0)
                ),
                "portfolio_no_plan_rate": float(
                    canonical_portfolio_metrics.get("no_plan_rate", 0.0)
                ),
                "portfolio_reality_gap_flag_rate": float(
                    canonical_portfolio_metrics.get("reality_gap_flag_rate", 0.0)
                ),
                "portfolio_mean_nominal_pd_improvement": float(
                    canonical_portfolio_metrics.get("mean_nominal_pd_improvement", 0.0)
                ),
                "portfolio_execution_weighted_expected_improvement": float(
                    canonical_portfolio_metrics.get("execution_weighted_expected_improvement", 0.0)
                ),
                "portfolio_early_checkpoint_health_rate": float(
                    canonical_portfolio_metrics.get("early_checkpoint_health_rate", 0.0)
                ),
                "portfolio_delayed_only_rate": float(
                    canonical_portfolio_metrics.get("delayed_only_rate", 0.0)
                ),
                "portfolio_long_horizon_heavy_rate": float(
                    canonical_portfolio_metrics.get("long_horizon_heavy_rate", 0.0)
                ),
                "portfolio_replan_risk_rate": float(
                    canonical_portfolio_metrics.get("replan_risk_rate", 0.0)
                ),
                "portfolio_secondary_raw_plan_coverage": float(
                    secondary_portfolio_metrics.get("raw_plan_coverage", 0.0)
                ),
                "portfolio_secondary_valid_plan_coverage": float(
                    secondary_portfolio_metrics.get("valid_plan_coverage", 0.0)
                ),
                "portfolio_secondary_governance_safe_plan_coverage": float(
                    secondary_portfolio_metrics.get("governance_safe_plan_coverage", 0.0)
                ),
                "portfolio_secondary_product_ready_plan_coverage": float(
                    secondary_portfolio_metrics.get("product_ready_plan_coverage", 0.0)
                ),
                "portfolio_dominant_reality_gap_reason": str(
                    portfolio_validation_summary.get("reality_gap_summary", {}).get("dominant_reality_gap_reason", "")
                ),
                "portfolio_where_engine_works": str(
                    portfolio_validation_summary.get("segment_story", {}).get("where_engine_works", "")
                ),
                "portfolio_where_engine_struggles": str(
                    portfolio_validation_summary.get("segment_story", {}).get("where_engine_struggles", "")
                ),
                "demo_representativeness_verdict": str(
                    demo_representativeness_summary.get("demo_representativeness_verdict", "")
                ),
                "demo_fit_confidence": str(
                    demo_representativeness_summary.get("demo_fit_confidence", "")
                ),
                "demo_case_segment_share": float(
                    demo_representativeness_summary.get("demo_case_segment_share", 0.0)
                ),
                "demo_segment_product_ready_rate": float(
                    demo_representativeness_summary.get("segment_product_ready_rate", 0.0)
                ),
                "demo_product_ready_alignment": int(
                    bool(demo_representativeness_summary.get("product_ready_alignment", False))
                ),
            }
        )
        if not breakdown_df.empty:
            breakdown_df["seed"] = int(seed)
            breakdown_df["primary_fail_reason"] = str(snapshot["primary_fail_reason"])
            seed_breakdowns.append(breakdown_df)
        if not candidate_source_breakdown.empty:
            candidate_source_breakdown["seed"] = int(seed)
            seed_candidate_source_breakdowns.append(candidate_source_breakdown)
        if not execution_probability_breakdown.empty:
            execution_probability_breakdown["seed"] = int(seed)
            seed_execution_probability_breakdowns.append(execution_probability_breakdown)
        if not partial_execution_breakdown.empty:
            partial_execution_breakdown["seed"] = int(seed)
            seed_partial_execution_breakdowns.append(partial_execution_breakdown)
        if not offer_type_breakdown.empty:
            offer_type_breakdown["seed"] = int(seed)
            seed_offer_type_breakdowns.append(offer_type_breakdown)
        if not offer_policy_arm_breakdown.empty:
            offer_policy_arm_breakdown["seed"] = int(seed)
            seed_offer_policy_arm_breakdowns.append(offer_policy_arm_breakdown)
        if not offer_acceptance_breakdown.empty:
            offer_acceptance_breakdown["seed"] = int(seed)
            seed_offer_acceptance_breakdowns.append(offer_acceptance_breakdown)
        if not offer_proxy_impact_breakdown.empty:
            offer_proxy_impact_breakdown["seed"] = int(seed)
            seed_offer_proxy_impact_breakdowns.append(offer_proxy_impact_breakdown)
        if not trajectory_transition_breakdown.empty:
            trajectory_transition_breakdown["seed"] = int(seed)
            seed_trajectory_transition_breakdowns.append(trajectory_transition_breakdown)
        if not trajectory_policy_label_breakdown.empty:
            trajectory_policy_label_breakdown["seed"] = int(seed)
            seed_trajectory_policy_label_breakdowns.append(trajectory_policy_label_breakdown)
        if not trajectory_gate_by_risk_band.empty:
            trajectory_gate_by_risk_band["seed"] = int(seed)
            seed_trajectory_gate_by_risk_breakdowns.append(trajectory_gate_by_risk_band)
        if not trajectory_gate_by_income_band.empty:
            trajectory_gate_by_income_band["seed"] = int(seed)
            seed_trajectory_gate_by_income_breakdowns.append(trajectory_gate_by_income_band)
        if not trajectory_phase_action_mix.empty:
            trajectory_phase_action_mix["seed"] = int(seed)
            seed_trajectory_phase_action_mix_breakdowns.append(trajectory_phase_action_mix)
        if portfolio_validation_summary:
            seed_portfolio_validation_summaries.append(dict(portfolio_validation_summary))
        if not portfolio_coverage_breakdown.empty:
            portfolio_coverage_breakdown["seed"] = int(seed)
            seed_portfolio_coverage_breakdowns.append(portfolio_coverage_breakdown)
        if not portfolio_coverage_drop_breakdown.empty:
            portfolio_coverage_drop_breakdown["seed"] = int(seed)
            seed_portfolio_coverage_drop_breakdowns.append(portfolio_coverage_drop_breakdown)
        if not portfolio_reality_gap_breakdown.empty:
            portfolio_reality_gap_breakdown["seed"] = int(seed)
            seed_portfolio_reality_gap_breakdowns.append(portfolio_reality_gap_breakdown)
        if not portfolio_segment_breakdown.empty:
            portfolio_segment_breakdown["seed"] = int(seed)
            seed_portfolio_segment_breakdowns.append(portfolio_segment_breakdown)
        if not portfolio_offer_diagnostics.empty:
            portfolio_offer_diagnostics["seed"] = int(seed)
            seed_portfolio_offer_diagnostics.append(portfolio_offer_diagnostics)
        if not portfolio_behavior_comparison.empty:
            portfolio_behavior_comparison["seed"] = int(seed)
            seed_portfolio_behavior_comparisons.append(portfolio_behavior_comparison)
        if not portfolio_trajectory_class_breakdown.empty:
            portfolio_trajectory_class_breakdown["seed"] = int(seed)
            seed_portfolio_trajectory_class_breakdowns.append(portfolio_trajectory_class_breakdown)
        if demo_representativeness_summary:
            seed_demo_representativeness_summaries.append(dict(demo_representativeness_summary))
        if decision_logging_summary:
            seed_decision_logging_summaries.append(dict(decision_logging_summary))

    scale_df = pd.DataFrame(scale_rows).sort_values("seed").reset_index(drop=True)
    scale_path = run_ctx.tables_dir / "phase_scale_seed_summary.csv"
    scale_df.to_csv(scale_path, index=False)
    phase_breakdown_df = _build_phase_fairness_breakdown(seed_rows=scale_rows, seed_breakdowns=seed_breakdowns)
    phase_breakdown_path = run_ctx.tables_dir / "fairness_failure_breakdown.csv"
    phase_breakdown_df.to_csv(phase_breakdown_path, index=False)
    phase_candidate_quality_summary = _build_phase_candidate_quality_summary(scale_df)
    candidate_quality_summary_path = run_ctx.tables_dir / "candidate_quality_summary.json"
    candidate_quality_summary_path.write_text(
        json.dumps(phase_candidate_quality_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    phase_candidate_source_breakdown = _build_phase_candidate_source_breakdown(seed_candidate_source_breakdowns)
    candidate_source_breakdown_path = run_ctx.tables_dir / "candidate_source_breakdown.csv"
    phase_candidate_source_breakdown.to_csv(candidate_source_breakdown_path, index=False)
    phase_behavior_aware_summary = _build_phase_behavior_aware_summary(scale_df)
    behavior_aware_summary_path = run_ctx.tables_dir / "behavior_aware_summary.json"
    behavior_aware_summary_path.write_text(
        json.dumps(phase_behavior_aware_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    phase_execution_probability_breakdown = _build_phase_execution_probability_breakdown(
        seed_execution_probability_breakdowns
    )
    execution_probability_breakdown_path = run_ctx.tables_dir / "execution_probability_breakdown.csv"
    phase_execution_probability_breakdown.to_csv(execution_probability_breakdown_path, index=False)
    phase_partial_execution_breakdown = _build_phase_partial_execution_breakdown(
        seed_partial_execution_breakdowns
    )
    partial_execution_breakdown_path = run_ctx.tables_dir / "partial_execution_breakdown.csv"
    phase_partial_execution_breakdown.to_csv(partial_execution_breakdown_path, index=False)
    phase_offer_optimization_summary = _build_phase_offer_optimization_summary(scale_df)
    offer_optimization_summary_path = run_ctx.tables_dir / "offer_optimization_summary.json"
    offer_optimization_summary_path.write_text(
        json.dumps(phase_offer_optimization_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    phase_offer_type_breakdown = _build_phase_offer_breakdown(
        seed_offer_type_breakdowns,
        group_columns=["population", "risk_band", "offer_type"],
        breakdown_type_seed="seed_population_offer_type",
        breakdown_type_rollup="population_offer_type_rollup",
        value_columns={"count": "sum", "share": "mean", "mean_expected_recovery_proxy": "mean"},
    )
    offer_type_breakdown_path = run_ctx.tables_dir / "offer_type_breakdown.csv"
    phase_offer_type_breakdown.to_csv(offer_type_breakdown_path, index=False)
    phase_offer_policy_arm_breakdown = _build_phase_offer_breakdown(
        seed_offer_policy_arm_breakdowns,
        group_columns=[
            "population",
            "risk_band",
            "offer_policy_arm",
            "offer_family",
            "offer_scoring_profile",
            "term_generation_rule",
        ],
        breakdown_type_seed="seed_population_offer_policy_arm",
        breakdown_type_rollup="population_offer_policy_arm_rollup",
        value_columns={"count": "sum", "share": "mean"},
    )
    offer_policy_arm_breakdown_path = run_ctx.tables_dir / "offer_policy_arm_breakdown.csv"
    phase_offer_policy_arm_breakdown.to_csv(offer_policy_arm_breakdown_path, index=False)
    phase_offer_acceptance_breakdown = _build_phase_offer_breakdown(
        seed_offer_acceptance_breakdowns,
        group_columns=["population", "risk_band", "income_band", "offer_type"],
        breakdown_type_seed="seed_population_offer_acceptance",
        breakdown_type_rollup="population_offer_acceptance_rollup",
        value_columns={
            "count": "sum",
            "mean_offer_acceptance_probability": "mean",
            "mean_combined_plan_realization_probability": "mean",
        },
    )
    offer_acceptance_breakdown_path = run_ctx.tables_dir / "offer_acceptance_breakdown.csv"
    phase_offer_acceptance_breakdown.to_csv(offer_acceptance_breakdown_path, index=False)
    phase_offer_proxy_impact_breakdown = _build_phase_offer_breakdown(
        seed_offer_proxy_impact_breakdowns,
        group_columns=["population", "offer_type", "offer_policy_arm"],
        breakdown_type_seed="seed_population_offer_proxy_impact",
        breakdown_type_rollup="population_offer_proxy_impact_rollup",
        value_columns={
            "count": "sum",
            "approval_rate_proxy_delta": "mean",
            "default_rate_90d_proxy_delta": "mean",
            "avg_margin_90d_proxy_delta": "mean",
            "expected_recovery_proxy": "mean",
            "governance_safe_offer_rate": "mean",
        },
    )
    offer_proxy_impact_breakdown_path = run_ctx.tables_dir / "offer_proxy_impact_breakdown.csv"
    phase_offer_proxy_impact_breakdown.to_csv(offer_proxy_impact_breakdown_path, index=False)
    phase_trajectory_summary = _build_phase_trajectory_summary(scale_df)
    trajectory_summary_path = run_ctx.tables_dir / "trajectory_summary.json"
    trajectory_summary_path.write_text(
        json.dumps(phase_trajectory_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    phase_trajectory_transition_breakdown = _build_phase_trajectory_transition_breakdown(
        seed_trajectory_transition_breakdowns
    )
    trajectory_transition_breakdown_path = run_ctx.tables_dir / "trajectory_transition_breakdown.csv"
    phase_trajectory_transition_breakdown.to_csv(trajectory_transition_breakdown_path, index=False)
    phase_trajectory_policy_label_breakdown = _build_phase_trajectory_policy_label_breakdown(
        seed_trajectory_policy_label_breakdowns
    )
    trajectory_policy_label_breakdown_path = run_ctx.tables_dir / "trajectory_policy_label_breakdown.csv"
    phase_trajectory_policy_label_breakdown.to_csv(trajectory_policy_label_breakdown_path, index=False)
    phase_trajectory_gate_by_risk = _build_phase_trajectory_gate_rollup(
        seed_trajectory_gate_by_risk_breakdowns,
        group_column="risk_band",
    )
    trajectory_gate_by_risk_path = run_ctx.tables_dir / "trajectory_gate_by_risk_band.csv"
    phase_trajectory_gate_by_risk.to_csv(trajectory_gate_by_risk_path, index=False)
    phase_trajectory_gate_by_income = _build_phase_trajectory_gate_rollup(
        seed_trajectory_gate_by_income_breakdowns,
        group_column="income_band",
    )
    trajectory_gate_by_income_path = run_ctx.tables_dir / "trajectory_gate_by_income_band.csv"
    phase_trajectory_gate_by_income.to_csv(trajectory_gate_by_income_path, index=False)
    phase_trajectory_phase_action_mix = _build_phase_trajectory_phase_action_mix(
        seed_trajectory_phase_action_mix_breakdowns
    )
    trajectory_phase_action_mix_path = run_ctx.tables_dir / "trajectory_phase_action_mix.csv"
    phase_trajectory_phase_action_mix.to_csv(trajectory_phase_action_mix_path, index=False)
    phase_portfolio_validation_summary = _build_phase_portfolio_validation_summary(
        seed_portfolio_validation_summaries
    )
    portfolio_validation_summary_path = run_ctx.tables_dir / "portfolio_validation_summary.json"
    portfolio_validation_summary_path.write_text(
        json.dumps(phase_portfolio_validation_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    phase_portfolio_coverage_breakdown = aggregate_portfolio_breakdown(
        seed_portfolio_coverage_breakdowns,
        group_columns=["population", "funnel_stage"],
        value_columns={"count": "sum", "share": "mean"},
        breakdown_type_seed="seed_portfolio_coverage",
        breakdown_type_rollup="portfolio_coverage_rollup",
    )
    portfolio_coverage_breakdown_path = run_ctx.tables_dir / "portfolio_coverage_breakdown.csv"
    phase_portfolio_coverage_breakdown.to_csv(portfolio_coverage_breakdown_path, index=False)
    phase_portfolio_coverage_drop_breakdown = aggregate_portfolio_breakdown(
        seed_portfolio_coverage_drop_breakdowns,
        group_columns=["population", "transition", "reason"],
        value_columns={"count": "sum", "share_of_source": "mean"},
        breakdown_type_seed="seed_portfolio_coverage_drop",
        breakdown_type_rollup="portfolio_coverage_drop_rollup",
    )
    portfolio_coverage_drop_breakdown_path = run_ctx.tables_dir / "portfolio_coverage_drop_breakdown.csv"
    phase_portfolio_coverage_drop_breakdown.to_csv(portfolio_coverage_drop_breakdown_path, index=False)
    phase_portfolio_reality_gap_breakdown = aggregate_portfolio_breakdown(
        seed_portfolio_reality_gap_breakdowns,
        group_columns=["population", "flag", "severity", "breakdown_type"],
        value_columns={"count": "sum", "share": "mean", "severity_share": "mean"},
        breakdown_type_seed="seed_portfolio_reality_gap",
        breakdown_type_rollup="portfolio_reality_gap_rollup",
    )
    portfolio_reality_gap_breakdown_path = run_ctx.tables_dir / "portfolio_reality_gap_breakdown.csv"
    phase_portfolio_reality_gap_breakdown.to_csv(portfolio_reality_gap_breakdown_path, index=False)
    phase_portfolio_segment_breakdown = aggregate_portfolio_breakdown(
        seed_portfolio_segment_breakdowns,
        group_columns=["population", "segment_axis", "segment_value"],
        value_columns={
            "count": "sum",
            "share": "mean",
            "raw_plan_coverage": "mean",
            "valid_plan_coverage": "mean",
            "governance_safe_plan_coverage": "mean",
            "product_ready_plan_coverage": "mean",
            "reality_gap_flag_rate": "mean",
            "offer_plan_rate": "mean",
            "rankable_offer_rate": "mean",
            "governance_safe_offer_rate": "mean",
            "mean_plan_execution_probability": "mean",
            "mean_nominal_pd_improvement": "mean",
            "execution_weighted_expected_improvement": "mean",
            "early_healthy_rate": "mean",
            "delayed_only_rate": "mean",
            "long_horizon_heavy_rate": "mean",
            "replan_prone_rate": "mean",
        },
        breakdown_type_seed="seed_portfolio_segment",
        breakdown_type_rollup="portfolio_segment_rollup",
    )
    portfolio_segment_breakdown_path = run_ctx.tables_dir / "portfolio_segment_breakdown.csv"
    phase_portfolio_segment_breakdown.to_csv(portfolio_segment_breakdown_path, index=False)
    phase_portfolio_offer_diagnostics = aggregate_portfolio_breakdown(
        seed_portfolio_offer_diagnostics,
        group_columns=["population", "offer_needed_segment", "dominant_offer_type"],
        value_columns={
            "count": "sum",
            "share": "mean",
            "offer_plan_rate": "mean",
            "rankable_offer_rate": "mean",
            "governance_safe_offer_rate": "mean",
            "offer_acceptance_probability_mean": "mean",
            "combined_realization_rate": "mean",
        },
        breakdown_type_seed="seed_portfolio_offer_diagnostics",
        breakdown_type_rollup="portfolio_offer_diagnostics_rollup",
    )
    portfolio_offer_diagnostics_path = run_ctx.tables_dir / "portfolio_offer_diagnostics.csv"
    phase_portfolio_offer_diagnostics.to_csv(portfolio_offer_diagnostics_path, index=False)
    phase_portfolio_behavior_comparison = aggregate_portfolio_breakdown(
        seed_portfolio_behavior_comparisons,
        group_columns=["population", "slice_type", "slice_value"],
        value_columns={
            "count": "sum",
            "mean_plan_execution_probability": "mean",
            "nominal_pd_improvement": "mean",
            "execution_weighted_expected_improvement": "mean",
            "execution_weighted_gap_vs_nominal": "mean",
            "mixed_execution_exposure": "mean",
            "failed_execution_exposure": "mean",
        },
        breakdown_type_seed="seed_portfolio_behavior_comparison",
        breakdown_type_rollup="portfolio_behavior_comparison_rollup",
    )
    portfolio_behavior_comparison_path = run_ctx.tables_dir / "portfolio_behavior_comparison.csv"
    phase_portfolio_behavior_comparison.to_csv(portfolio_behavior_comparison_path, index=False)
    phase_portfolio_trajectory_class_breakdown = aggregate_portfolio_breakdown(
        seed_portfolio_trajectory_class_breakdowns,
        group_columns=["population", "trajectory_class"],
        value_columns={
            "count": "sum",
            "share": "mean",
            "gate_pass_rate_4w": "mean",
            "gate_pass_rate_12w": "mean",
            "gate_pass_rate_24w": "mean",
            "product_ready_plan_coverage": "mean",
        },
        breakdown_type_seed="seed_portfolio_trajectory_class",
        breakdown_type_rollup="portfolio_trajectory_class_rollup",
    )
    portfolio_trajectory_class_breakdown_path = run_ctx.tables_dir / "portfolio_trajectory_class_breakdown.csv"
    phase_portfolio_trajectory_class_breakdown.to_csv(portfolio_trajectory_class_breakdown_path, index=False)
    demo_representativeness_summary = phase_portfolio_validation_summary.get("demo_representativeness", {})
    demo_representativeness_summary_path = run_ctx.tables_dir / "demo_representativeness_summary.json"
    demo_representativeness_summary_path.write_text(
        json.dumps(demo_representativeness_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    portfolio_validation_review = _build_phase_portfolio_validation_review(phase_portfolio_validation_summary)
    portfolio_validation_review_path = run_ctx.tables_dir / "portfolio_validation_review.md"
    portfolio_validation_review_path.write_text(
        portfolio_validation_review,
        encoding="utf-8",
    )
    phase_decision_logging_summary = _build_phase_decision_logging_summary(seed_decision_logging_summaries)
    decision_logging_summary_path = run_ctx.tables_dir / "decision_logging_summary.json"
    decision_logging_summary_path.write_text(
        json.dumps(phase_decision_logging_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    learning_loop_summary = _build_learning_loop_summary(
        decision_logging_summary=phase_decision_logging_summary,
        outcome_ingestion_summary=outcome_ingestion_summary,
        off_policy_evaluation=off_policy_evaluation,
    )

    aggregate = {
        "seed_count": int(len(scale_df)),
        "pass_count": int(scale_df["all_pass"].sum()),
        "model_version": str(resolved_model_manifest.get("model_version", "")),
        "model_freeze_mode": str(resolved_model_manifest.get("freeze_mode", "implicit_latest")),
        "frozen_model_manifest_path": "tables/frozen_model_manifest.json",
        **aggregate_release_metrics(
            scale_df.to_dict(orient="records"),
            thresholds=thresholds,
            breakdown_rows=phase_breakdown_df.to_dict(orient="records"),
        ),
        "mean_denied_to_approved_lift": float(scale_df["denied_to_approved_lift"].mean()),
        "mean_denied_high_risk_lift": float(scale_df["denied_high_risk_lift"].mean()),
        "mean_high_risk_reachability_rate": float(scale_df["high_risk_reachability_rate"].mean()),
        "mean_denied_reliability_violation_rate": float(scale_df["denied_reliability_violation_rate"].mean()),
        "mean_sync_latency_p95_ms": float(scale_df["sync_latency_p95_ms"].mean()),
        "mean_sync_latency_p99_ms": float(scale_df["sync_latency_p99_ms"].mean()),
        "mean_equalized_odds_gap_delta": float(scale_df["equalized_odds_gap_delta"].mean()),
        "mean_approval_gap_delta": float(scale_df["approval_gap_delta"].mean()),
        "mean_recourse_success_gap": float(scale_df["recourse_success_gap"].mean()),
        "mean_fairness_gap_after": float(scale_df["fairness_gap_after"].mean()),
        "mean_high_stress_fairness_gap_after": float(scale_df["high_stress_fairness_gap_after"].mean()),
        "max_fairness_guard_demotion_count": int(scale_df["fairness_guard_demotion_count"].max()),
        "mean_error_rate": float(scale_df["error_rate"].mean()),
        "decision_log_completeness": float(phase_decision_logging_summary["decision_log_completeness"]),
        "mean_trajectory_gate_pass_rate_4w": float(scale_df["trajectory_gate_pass_rate_4w"].mean()),
        "mean_trajectory_gate_pass_rate_12w": float(scale_df["trajectory_gate_pass_rate_12w"].mean()),
        "mean_trajectory_gate_pass_rate_24w": float(scale_df["trajectory_gate_pass_rate_24w"].mean()),
        "mean_trajectory_partial_progress_rate": float(scale_df["trajectory_partial_progress_rate"].mean()),
        "mean_trajectory_median_time_to_gate_pass_days": float(scale_df["trajectory_median_time_to_gate_pass_days"].mean()),
        "mean_trajectory_soft_regression_penalty_mean": float(scale_df["trajectory_soft_regression_penalty_mean"].mean()),
        "mean_trajectory_on_track_rate": float(scale_df["trajectory_on_track_rate"].mean()),
        "mean_trajectory_needs_replan_rate": float(scale_df["trajectory_needs_replan_rate"].mean()),
        "mean_trajectory_degraded_rate": float(scale_df["trajectory_degraded_rate"].mean()),
        "trajectory_dominant_transition_reason": str(phase_trajectory_summary["dominant_transition_reason"]),
        "mean_trajectory_stabilize_first_rate": float(scale_df["trajectory_stabilize_first_rate"].mean()),
        "mean_trajectory_balanced_progress_rate": float(scale_df["trajectory_balanced_progress_rate"].mean()),
        "mean_trajectory_long_horizon_heavy_rate": float(scale_df["trajectory_long_horizon_heavy_rate"].mean()),
        "mean_high_risk_denied_trajectory_gate_pass_rate_4w": float(
            scale_df["high_risk_denied_trajectory_gate_pass_rate_4w"].mean()
        ),
        "mean_high_risk_denied_trajectory_gate_pass_rate_12w": float(
            scale_df["high_risk_denied_trajectory_gate_pass_rate_12w"].mean()
        ),
        "mean_high_risk_denied_trajectory_gate_pass_rate_24w": float(
            scale_df["high_risk_denied_trajectory_gate_pass_rate_24w"].mean()
        ),
        "mean_high_risk_denied_trajectory_partial_progress_rate": float(
            scale_df["high_risk_denied_trajectory_partial_progress_rate"].mean()
        ),
        "mean_high_risk_denied_trajectory_median_time_to_gate_pass_days": float(
            scale_df["high_risk_denied_trajectory_median_time_to_gate_pass_days"].mean()
        ),
        "mean_high_risk_denied_trajectory_soft_regression_penalty_mean": float(
            scale_df["high_risk_denied_trajectory_soft_regression_penalty_mean"].mean()
        ),
        "mean_high_risk_denied_trajectory_on_track_rate": float(
            scale_df["high_risk_denied_trajectory_on_track_rate"].mean()
        ),
        "mean_high_risk_denied_trajectory_needs_replan_rate": float(
            scale_df["high_risk_denied_trajectory_needs_replan_rate"].mean()
        ),
        "mean_high_risk_denied_trajectory_degraded_rate": float(
            scale_df["high_risk_denied_trajectory_degraded_rate"].mean()
        ),
        "mean_high_risk_profile_applied_rate": float(scale_df["high_risk_profile_applied_rate"].mean()),
        "candidate_quality_population": str(phase_candidate_quality_summary["candidate_quality_population"]),
        "candidate_quality_secondary_population": str(
            phase_candidate_quality_summary["candidate_quality_secondary_population"]
        ),
        "mean_candidate_pool_diversity_index": float(scale_df["candidate_pool_diversity_index"].mean()),
        "mean_candidate_source_entropy": float(scale_df["candidate_source_entropy"].mean()),
        "mean_best_source_internal_rate": float(scale_df["best_source_internal_rate"].mean()),
        "mean_best_source_dice_rate": float(scale_df["best_source_dice_rate"].mean()),
        "mean_best_source_rule_rate": float(scale_df["best_source_rule_rate"].mean()),
        "mean_best_source_fallback_rate": float(scale_df["best_source_fallback_rate"].mean()),
        "mean_high_risk_denied_candidate_pool_diversity_index": float(
            scale_df["high_risk_denied_candidate_pool_diversity_index"].mean()
        ),
        "mean_high_risk_denied_candidate_source_entropy": float(
            scale_df["high_risk_denied_candidate_source_entropy"].mean()
        ),
        "mean_high_risk_denied_best_source_internal_rate": float(
            scale_df["high_risk_denied_best_source_internal_rate"].mean()
        ),
        "mean_high_risk_denied_best_source_dice_rate": float(scale_df["high_risk_denied_best_source_dice_rate"].mean()),
        "mean_high_risk_denied_best_source_rule_rate": float(scale_df["high_risk_denied_best_source_rule_rate"].mean()),
        "mean_high_risk_denied_best_source_fallback_rate": float(
            scale_df["high_risk_denied_best_source_fallback_rate"].mean()
        ),
        "mean_plan_execution_probability": float(scale_df["mean_plan_execution_probability"].mean()),
        "mean_expected_pd_improvement": float(scale_df["expected_pd_improvement"].mean()),
        "mean_partial_execution_rate": float(scale_df["partial_execution_rate"].mean()),
        "mean_failed_execution_rate": float(scale_df["failed_execution_rate"].mean()),
        "mean_mixed_execution_rate": float(scale_df["mixed_execution_rate"].mean()),
        "mean_expected_partial_progress_rate": float(scale_df["expected_partial_progress_rate"].mean()),
        "mean_high_risk_denied_plan_execution_probability": float(
            scale_df["high_risk_denied_mean_plan_execution_probability"].mean()
        ),
        "mean_high_risk_denied_expected_pd_improvement": float(
            scale_df["high_risk_denied_expected_pd_improvement"].mean()
        ),
        "mean_high_risk_denied_partial_execution_rate": float(
            scale_df["high_risk_denied_partial_execution_rate"].mean()
        ),
        "mean_high_risk_denied_failed_execution_rate": float(
            scale_df["high_risk_denied_failed_execution_rate"].mean()
        ),
        "mean_high_risk_denied_mixed_execution_rate": float(
            scale_df["high_risk_denied_mixed_execution_rate"].mean()
        ),
        "mean_high_risk_denied_expected_partial_progress_rate": float(
            scale_df["high_risk_denied_expected_partial_progress_rate"].mean()
        ),
        "mean_offer_plan_rate": float(scale_df["offer_plan_rate"].mean()),
        "mean_rankable_offer_rate": float(scale_df["rankable_offer_rate"].mean()),
        "mean_offer_acceptance_probability": float(scale_df["offer_acceptance_probability_mean"].mean()),
        "mean_combined_plan_realization_probability": float(
            scale_df["combined_plan_realization_probability_mean"].mean()
        ),
        "mean_expected_recovery_proxy": float(scale_df["expected_recovery_proxy"].mean()),
        "mean_approval_rate_proxy_delta": float(scale_df["approval_rate_proxy_delta"].mean()),
        "mean_default_rate_90d_proxy_delta": float(scale_df["default_rate_90d_proxy_delta"].mean()),
        "mean_avg_margin_90d_proxy_delta": float(scale_df["avg_margin_90d_proxy_delta"].mean()),
        "mean_governance_safe_offer_rate": float(scale_df["governance_safe_offer_rate"].mean()),
        "dominant_offer_type": str(phase_offer_optimization_summary["canonical_metrics"]["dominant_offer_type"]),
        "portfolio_raw_plan_coverage": float(scale_df["portfolio_raw_plan_coverage"].mean()),
        "portfolio_valid_plan_coverage": float(scale_df["portfolio_valid_plan_coverage"].mean()),
        "portfolio_governance_safe_plan_coverage": float(
            scale_df["portfolio_governance_safe_plan_coverage"].mean()
        ),
        "portfolio_product_ready_plan_coverage": float(
            scale_df["portfolio_product_ready_plan_coverage"].mean()
        ),
        "portfolio_no_plan_rate": float(scale_df["portfolio_no_plan_rate"].mean()),
        "portfolio_reality_gap_flag_rate": float(scale_df["portfolio_reality_gap_flag_rate"].mean()),
        "portfolio_mean_nominal_pd_improvement": float(scale_df["portfolio_mean_nominal_pd_improvement"].mean()),
        "portfolio_execution_weighted_expected_improvement": float(
            scale_df["portfolio_execution_weighted_expected_improvement"].mean()
        ),
        "portfolio_early_checkpoint_health_rate": float(scale_df["portfolio_early_checkpoint_health_rate"].mean()),
        "portfolio_delayed_only_rate": float(scale_df["portfolio_delayed_only_rate"].mean()),
        "portfolio_long_horizon_heavy_rate": float(scale_df["portfolio_long_horizon_heavy_rate"].mean()),
        "portfolio_replan_risk_rate": float(scale_df["portfolio_replan_risk_rate"].mean()),
        "portfolio_secondary_raw_plan_coverage": float(scale_df["portfolio_secondary_raw_plan_coverage"].mean()),
        "portfolio_secondary_valid_plan_coverage": float(scale_df["portfolio_secondary_valid_plan_coverage"].mean()),
        "portfolio_secondary_governance_safe_plan_coverage": float(
            scale_df["portfolio_secondary_governance_safe_plan_coverage"].mean()
        ),
        "portfolio_secondary_product_ready_plan_coverage": float(
            scale_df["portfolio_secondary_product_ready_plan_coverage"].mean()
        ),
        "portfolio_dominant_reality_gap_reason": str(
            phase_portfolio_validation_summary.get("reality_gap_summary", {}).get("dominant_reality_gap_reason", "")
        ),
        "portfolio_where_engine_works": str(
            phase_portfolio_validation_summary.get("segment_story", {}).get("where_engine_works", "")
        ),
        "portfolio_where_engine_struggles": str(
            phase_portfolio_validation_summary.get("segment_story", {}).get("where_engine_struggles", "")
        ),
        "demo_representativeness_verdict": str(
            demo_representativeness_summary.get("demo_representativeness_verdict", "")
        ),
        "demo_fit_confidence": str(demo_representativeness_summary.get("demo_fit_confidence", "")),
        "demo_case_segment_share": float(demo_representativeness_summary.get("demo_case_segment_share", 0.0)),
        "demo_segment_product_ready_rate": float(
            demo_representativeness_summary.get("segment_product_ready_rate", 0.0)
        ),
        "demo_product_ready_alignment": float(
            1.0 if bool(demo_representativeness_summary.get("product_ready_alignment", False)) else 0.0
        ),
    }
    (run_ctx.tables_dir / "phase_scale_aggregate.json").write_text(json.dumps(aggregate, indent=2, ensure_ascii=False), encoding="utf-8")
    release_payload = evaluate_release_decision(aggregate, thresholds)
    (run_ctx.tables_dir / "release_decision.json").write_text(
        json.dumps(release_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    phase_high_risk_tuning_summary = _build_phase_high_risk_tuning_summary(
        scale_df,
        release_decision=str(release_payload["decision"]),
    )
    (run_ctx.tables_dir / "high_risk_tuning_summary.json").write_text(
        json.dumps(phase_high_risk_tuning_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    if release_payload["decision"] == "LIMITED_GO":
        (run_ctx.tables_dir / "pilot_guardrails.json").write_text(
            json.dumps(build_pilot_guardrails(aggregate), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (run_ctx.tables_dir / "rollback_conditions.json").write_text(
            json.dumps(build_rollback_conditions(aggregate, thresholds), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    supporting_artifacts = {
        "phase_quick_summary_json": "tables/phase_quick_summary.json",
        "phase_scale_seed_summary_csv": "tables/phase_scale_seed_summary.csv",
        "phase_scale_aggregate_json": "tables/phase_scale_aggregate.json",
        "fairness_failure_breakdown_csv": "tables/fairness_failure_breakdown.csv",
        "candidate_quality_summary_json": "tables/candidate_quality_summary.json",
        "candidate_source_breakdown_csv": "tables/candidate_source_breakdown.csv",
        "behavior_aware_summary_json": "tables/behavior_aware_summary.json",
        "execution_probability_breakdown_csv": "tables/execution_probability_breakdown.csv",
        "partial_execution_breakdown_csv": "tables/partial_execution_breakdown.csv",
        "offer_optimization_summary_json": "tables/offer_optimization_summary.json",
        "offer_type_breakdown_csv": "tables/offer_type_breakdown.csv",
        "offer_policy_arm_breakdown_csv": "tables/offer_policy_arm_breakdown.csv",
        "offer_acceptance_breakdown_csv": "tables/offer_acceptance_breakdown.csv",
        "offer_proxy_impact_breakdown_csv": "tables/offer_proxy_impact_breakdown.csv",
        "trajectory_summary_json": "tables/trajectory_summary.json",
        "trajectory_transition_breakdown_csv": "tables/trajectory_transition_breakdown.csv",
        "trajectory_policy_label_breakdown_csv": "tables/trajectory_policy_label_breakdown.csv",
        "trajectory_gate_by_risk_band_csv": "tables/trajectory_gate_by_risk_band.csv",
        "trajectory_gate_by_income_band_csv": "tables/trajectory_gate_by_income_band.csv",
        "trajectory_phase_action_mix_csv": "tables/trajectory_phase_action_mix.csv",
        "portfolio_validation_summary_json": "tables/portfolio_validation_summary.json",
        "portfolio_coverage_breakdown_csv": "tables/portfolio_coverage_breakdown.csv",
        "portfolio_coverage_drop_breakdown_csv": "tables/portfolio_coverage_drop_breakdown.csv",
        "portfolio_reality_gap_breakdown_csv": "tables/portfolio_reality_gap_breakdown.csv",
        "portfolio_segment_breakdown_csv": "tables/portfolio_segment_breakdown.csv",
        "portfolio_offer_diagnostics_csv": "tables/portfolio_offer_diagnostics.csv",
        "portfolio_behavior_comparison_csv": "tables/portfolio_behavior_comparison.csv",
        "portfolio_trajectory_class_breakdown_csv": "tables/portfolio_trajectory_class_breakdown.csv",
        "demo_representativeness_summary_json": "tables/demo_representativeness_summary.json",
        "portfolio_validation_review_md": "tables/portfolio_validation_review.md",
        "high_risk_tuning_summary_json": "tables/high_risk_tuning_summary.json",
        "generator_policy_impact_json": "tables/generator_policy_impact.json",
        "decision_logging_summary_json": "tables/decision_logging_summary.json",
        "release_decision_json": "tables/release_decision.json",
        "frozen_model_manifest_json": "tables/frozen_model_manifest.json",
        "release_evidence_pack_json": "tables/release_evidence_pack.json",
    }
    if mirrored_outcome_feedback:
        supporting_artifacts["outcome_feedback_summary_json"] = "tables/outcome_feedback_summary.json"
    if mirrored_outcome_ingestion_summary:
        supporting_artifacts["outcome_ingestion_summary_json"] = "tables/outcome_ingestion_summary.json"
    if mirrored_off_policy_evaluation:
        supporting_artifacts["off_policy_evaluation_json"] = "tables/off_policy_evaluation.json"
    if mirrored_outcome_learning_dataset:
        supporting_artifacts["outcome_learning_dataset_csv"] = "tables/outcome_learning_dataset.csv"
    if mirrored_outcome_policy_summary:
        supporting_artifacts["outcome_policy_summary_csv"] = "tables/outcome_policy_summary.csv"
    if mirrored_outcome_policy_deltas:
        supporting_artifacts["outcome_policy_deltas_json"] = "tables/outcome_policy_deltas.json"
    if release_payload["decision"] == "LIMITED_GO":
        supporting_artifacts["pilot_guardrails_json"] = "tables/pilot_guardrails.json"
        supporting_artifacts["rollback_conditions_json"] = "tables/rollback_conditions.json"

    seed_count = int(len(scale_df))
    evidence_level = "seeded_suite" if seed_count > 1 else "single_run_fallback"
    acceptance_eligible = bool(frozen_model_manifest.get("acceptance_eligible", False)) and seed_count > 1
    evidence_status = "complete"
    degraded_reason = ""
    missing_artifacts: list[str] = []
    if seed_count <= 1:
        evidence_level = "single_run_fallback"
        evidence_status = "degraded"
        acceptance_eligible = False
        degraded_reason = "insufficient_repeated_seeded_evidence"
        missing_artifacts.append("repeated_seeded_evidence")
    elif not bool(frozen_model_manifest.get("acceptance_eligible", False)):
        evidence_status = "degraded"
        degraded_reason = "implicit_latest_model_freeze"

    impact_attribution_summary = _build_suite_impact_attribution_summary(
        phase_name=str(args.phase_name),
        aggregate=aggregate,
        evidence_level=evidence_level,
        evidence_status=evidence_status,
        seed_count=seed_count,
    )
    (run_ctx.tables_dir / "generator_policy_impact.json").write_text(
        json.dumps(impact_attribution_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    kpi_contract_snapshot = build_kpi_contract_snapshot(
        runner_type="suite",
        release_payload=release_payload,
        aggregate_metrics=aggregate,
        evidence_level=evidence_level,
        acceptance_eligible=acceptance_eligible,
        supporting_artifacts=supporting_artifacts,
        model_version=str(resolved_model_manifest.get("model_version", "")),
        model_freeze_mode=str(resolved_model_manifest.get("freeze_mode", "implicit_latest")),
        evidence_status=evidence_status,
        degraded_reason=degraded_reason,
        missing_artifacts=missing_artifacts,
        metadata={
            "phase_name": str(args.phase_name),
            "train_run_id": str(train_run_id),
            "frozen_model_manifest_path": "tables/frozen_model_manifest.json",
            "candidate_quality_summary": phase_candidate_quality_summary,
            "behavior_aware_summary": phase_behavior_aware_summary,
            "offer_optimization_summary": phase_offer_optimization_summary,
            "trajectory_summary": phase_trajectory_summary,
            "portfolio_validation_summary": phase_portfolio_validation_summary,
            "demo_representativeness_summary": demo_representativeness_summary,
            "high_risk_tuning_summary": phase_high_risk_tuning_summary,
            "impact_attribution_summary": impact_attribution_summary,
            "decision_logging_summary": phase_decision_logging_summary,
            "outcome_feedback_summary": outcome_feedback_summary,
            "outcome_ingestion_summary": outcome_ingestion_summary,
            "off_policy_evaluation": off_policy_evaluation,
            "learning_loop_summary": learning_loop_summary,
        },
    )
    (run_ctx.tables_dir / "kpi_contract_snapshot.json").write_text(
        json.dumps(kpi_contract_snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    milestone_acceptance_summary = build_milestone_acceptance_summary(
        phase=str(args.phase_name),
        milestone=str(args.milestone),
        runner_type="suite",
        release_payload=release_payload,
        aggregate_metrics=aggregate,
        evidence_level=evidence_level,
        acceptance_eligible=acceptance_eligible,
        supporting_artifacts=supporting_artifacts,
        model_version=str(resolved_model_manifest.get("model_version", "")),
        model_freeze_mode=str(resolved_model_manifest.get("freeze_mode", "implicit_latest")),
        evidence_status=evidence_status,
        degraded_reason=degraded_reason,
        missing_artifacts=missing_artifacts,
        metadata={
            "candidate_quality_summary": phase_candidate_quality_summary,
            "behavior_aware_summary": phase_behavior_aware_summary,
            "offer_optimization_summary": phase_offer_optimization_summary,
            "trajectory_summary": phase_trajectory_summary,
            "portfolio_validation_summary": phase_portfolio_validation_summary,
            "demo_representativeness_summary": demo_representativeness_summary,
            "high_risk_tuning_summary": phase_high_risk_tuning_summary,
            "impact_attribution_summary": impact_attribution_summary,
            "decision_logging_summary": phase_decision_logging_summary,
            "outcome_feedback_summary": outcome_feedback_summary,
            "outcome_ingestion_summary": outcome_ingestion_summary,
            "off_policy_evaluation": off_policy_evaluation,
            "learning_loop_summary": learning_loop_summary,
        },
    )
    milestone_acceptance_review = render_milestone_acceptance_review(milestone_acceptance_summary)
    (run_ctx.tables_dir / "milestone_acceptance_summary.json").write_text(
        json.dumps(milestone_acceptance_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (run_ctx.tables_dir / "milestone_acceptance_review.md").write_text(
        milestone_acceptance_review,
        encoding="utf-8",
    )
    (run_ctx.tables_dir / "release_review_summary.md").write_text(
        _render_release_review_summary(
            milestone_acceptance_summary=milestone_acceptance_summary,
        ),
        encoding="utf-8",
    )
    required_release_artifacts = {
        "kpi_contract_snapshot_json": "tables/kpi_contract_snapshot.json",
        "milestone_acceptance_summary_json": "tables/milestone_acceptance_summary.json",
        "phase_scale_seed_summary_csv": "tables/phase_scale_seed_summary.csv",
        "phase_scale_aggregate_json": "tables/phase_scale_aggregate.json",
        "fairness_failure_breakdown_csv": "tables/fairness_failure_breakdown.csv",
        "candidate_quality_summary_json": "tables/candidate_quality_summary.json",
        "candidate_source_breakdown_csv": "tables/candidate_source_breakdown.csv",
        "behavior_aware_summary_json": "tables/behavior_aware_summary.json",
        "execution_probability_breakdown_csv": "tables/execution_probability_breakdown.csv",
        "partial_execution_breakdown_csv": "tables/partial_execution_breakdown.csv",
        "offer_optimization_summary_json": "tables/offer_optimization_summary.json",
        "offer_type_breakdown_csv": "tables/offer_type_breakdown.csv",
        "offer_policy_arm_breakdown_csv": "tables/offer_policy_arm_breakdown.csv",
        "offer_acceptance_breakdown_csv": "tables/offer_acceptance_breakdown.csv",
        "offer_proxy_impact_breakdown_csv": "tables/offer_proxy_impact_breakdown.csv",
        "trajectory_summary_json": "tables/trajectory_summary.json",
        "trajectory_transition_breakdown_csv": "tables/trajectory_transition_breakdown.csv",
        "trajectory_policy_label_breakdown_csv": "tables/trajectory_policy_label_breakdown.csv",
        "portfolio_validation_summary_json": "tables/portfolio_validation_summary.json",
        "portfolio_coverage_breakdown_csv": "tables/portfolio_coverage_breakdown.csv",
        "portfolio_coverage_drop_breakdown_csv": "tables/portfolio_coverage_drop_breakdown.csv",
        "portfolio_reality_gap_breakdown_csv": "tables/portfolio_reality_gap_breakdown.csv",
        "portfolio_segment_breakdown_csv": "tables/portfolio_segment_breakdown.csv",
        "portfolio_offer_diagnostics_csv": "tables/portfolio_offer_diagnostics.csv",
        "portfolio_behavior_comparison_csv": "tables/portfolio_behavior_comparison.csv",
        "portfolio_trajectory_class_breakdown_csv": "tables/portfolio_trajectory_class_breakdown.csv",
        "demo_representativeness_summary_json": "tables/demo_representativeness_summary.json",
        "telemetry_export_json": "tables/telemetry_export.json",
        "milestone_acceptance_review_md": "tables/milestone_acceptance_review.md",
    }
    optional_release_artifacts = {
        "release_decision_json": "tables/release_decision.json",
        "release_review_summary_md": "tables/release_review_summary.md",
        "frozen_model_manifest_json": "tables/frozen_model_manifest.json",
        "high_risk_tuning_summary_json": "tables/high_risk_tuning_summary.json",
        "generator_policy_impact_json": "tables/generator_policy_impact.json",
        "decision_logging_summary_json": "tables/decision_logging_summary.json",
        "trajectory_gate_by_risk_band_csv": "tables/trajectory_gate_by_risk_band.csv",
        "trajectory_gate_by_income_band_csv": "tables/trajectory_gate_by_income_band.csv",
        "trajectory_phase_action_mix_csv": "tables/trajectory_phase_action_mix.csv",
        "portfolio_validation_review_md": "tables/portfolio_validation_review.md",
    }
    if mirrored_outcome_feedback:
        optional_release_artifacts["outcome_feedback_summary_json"] = "tables/outcome_feedback_summary.json"
    if mirrored_outcome_ingestion_summary:
        optional_release_artifacts["outcome_ingestion_summary_json"] = "tables/outcome_ingestion_summary.json"
    if mirrored_off_policy_evaluation:
        optional_release_artifacts["off_policy_evaluation_json"] = "tables/off_policy_evaluation.json"
    if mirrored_outcome_learning_dataset:
        optional_release_artifacts["outcome_learning_dataset_csv"] = "tables/outcome_learning_dataset.csv"
    if mirrored_outcome_policy_summary:
        optional_release_artifacts["outcome_policy_summary_csv"] = "tables/outcome_policy_summary.csv"
    if mirrored_outcome_policy_deltas:
        optional_release_artifacts["outcome_policy_deltas_json"] = "tables/outcome_policy_deltas.json"
    if release_payload["decision"] == "LIMITED_GO":
        optional_release_artifacts["pilot_guardrails_json"] = "tables/pilot_guardrails.json"
        optional_release_artifacts["rollback_conditions_json"] = "tables/rollback_conditions.json"
    release_evidence_pack = build_release_evidence_pack(
        runner_type="suite",
        phase=str(args.phase_name),
        milestone=str(args.milestone),
        release_decision=str(milestone_acceptance_summary["release_decision"]),
        acceptance_status=str(milestone_acceptance_summary["acceptance_status"]),
        evidence_level=str(milestone_acceptance_summary["evidence_level"]),
        evidence_status=str(milestone_acceptance_summary["evidence_status"]),
        acceptance_eligible=bool(milestone_acceptance_summary["acceptance_eligible"]),
        required_artifacts=required_release_artifacts,
        optional_artifacts=optional_release_artifacts,
        existing_artifacts=[
            f"tables/{path.name}"
            for path in run_ctx.tables_dir.iterdir()
            if path.is_file()
        ],
    )
    (run_ctx.tables_dir / "release_evidence_pack.json").write_text(
        json.dumps(release_evidence_pack, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    milestone_acceptance_summary["release_pack_summary"] = {
        "pack_status": str(release_evidence_pack["pack_status"]),
        "pack_acceptance_eligible": bool(release_evidence_pack["pack_acceptance_eligible"]),
        "required_artifacts": dict(release_evidence_pack["required_artifacts"]),
        "optional_artifacts": dict(release_evidence_pack["optional_artifacts"]),
        "missing_artifacts": list(release_evidence_pack["missing_artifacts"]),
    }
    milestone_acceptance_review = render_milestone_acceptance_review(milestone_acceptance_summary)
    (run_ctx.tables_dir / "milestone_acceptance_summary.json").write_text(
        json.dumps(milestone_acceptance_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (run_ctx.tables_dir / "milestone_acceptance_review.md").write_text(
        milestone_acceptance_review,
        encoding="utf-8",
    )
    (run_ctx.tables_dir / "release_review_summary.md").write_text(
        _render_release_review_summary(
            milestone_acceptance_summary=milestone_acceptance_summary,
        ),
        encoding="utf-8",
    )

    run_ctx.save_metrics(
        {
            "phase_name": str(args.phase_name),
            "train_run_id": train_run_id,
            "skip_train_before_batch": bool(args.skip_train_before_batch),
            "model_version": str(resolved_model_manifest.get("model_version", "")),
            "model_freeze_mode": str(resolved_model_manifest.get("freeze_mode", "implicit_latest")),
            "quick_run_id": quick_run_id,
            "quick_all_pass": bool(quick_ok),
            "quick_lift_pass": bool(quick_snapshot["lift_pass"]),
            "quick_reliability_pass": bool(quick_snapshot["reliability_pass"]),
            "quick_fairness_seed_pass": bool(quick_snapshot["fairness_seed_pass"]),
            "scale_pass_count": int(scale_df["all_pass"].sum()),
            "scale_seed_count": int(len(scale_df)),
            "scale_fairness_seed_pass_count": int(aggregate["fairness_seed_pass_count"]),
            "release_decision": str(release_payload["decision"]),
            "acceptance_status": str(milestone_acceptance_summary["acceptance_status"]),
            "acceptance_eligible": bool(milestone_acceptance_summary["acceptance_eligible"]),
            "evidence_level": str(milestone_acceptance_summary["evidence_level"]),
            "scale_mean_denied_to_approved_lift": float(scale_df["denied_to_approved_lift"].mean()),
            "scale_mean_denied_high_risk_lift": float(scale_df["denied_high_risk_lift"].mean()),
            "scale_mean_equalized_odds_gap_delta": float(scale_df["equalized_odds_gap_delta"].mean()),
            "scale_mean_recourse_success_gap": float(scale_df["recourse_success_gap"].mean()),
            "scale_mean_trajectory_gate_pass_rate_4w": float(scale_df["trajectory_gate_pass_rate_4w"].mean()),
            "scale_mean_trajectory_gate_pass_rate_12w": float(scale_df["trajectory_gate_pass_rate_12w"].mean()),
            "scale_mean_trajectory_gate_pass_rate_24w": float(scale_df["trajectory_gate_pass_rate_24w"].mean()),
            "scale_mean_trajectory_partial_progress_rate": float(scale_df["trajectory_partial_progress_rate"].mean()),
            "scale_mean_trajectory_soft_regression_penalty_mean": float(
                scale_df["trajectory_soft_regression_penalty_mean"].mean()
            ),
            "scale_mean_trajectory_on_track_rate": float(scale_df["trajectory_on_track_rate"].mean()),
            "scale_mean_trajectory_needs_replan_rate": float(scale_df["trajectory_needs_replan_rate"].mean()),
            "scale_mean_trajectory_degraded_rate": float(scale_df["trajectory_degraded_rate"].mean()),
            "scale_mean_high_risk_profile_applied_rate": float(scale_df["high_risk_profile_applied_rate"].mean()),
            "scale_mean_candidate_pool_diversity_index": float(scale_df["candidate_pool_diversity_index"].mean()),
            "scale_mean_candidate_source_entropy": float(scale_df["candidate_source_entropy"].mean()),
            "decision_log_completeness": float(phase_decision_logging_summary["decision_log_completeness"]),
            "reward_90d_coverage": float(learning_loop_summary["reward_90d_coverage"]),
            "ope_confidence": str(learning_loop_summary["ope_confidence"]),
        }
    )

    logger.info("Phase experiment suite completed. quick_run_id=%s", quick_run_id)
    logger.info(
        "Outputs: %s %s %s %s",
        run_ctx.tables_dir / "phase_quick_summary.json",
        scale_path,
        phase_breakdown_path,
        run_ctx.tables_dir / "release_decision.json",
    )


if __name__ == "__main__":
    main()
