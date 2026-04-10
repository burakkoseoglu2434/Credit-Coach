from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from credit_coach.data.schema import DecisionActionExecutionEventRecord, DecisionOutcomeRecord
from credit_coach.evaluation.off_policy import evaluate_off_policy
from credit_coach.storage.db import init_db
from credit_coach.storage.repository import (
    load_decision_action_execution_events,
    load_decision_learning_dataset,
    compute_policy_outcome_deltas,
    save_decision_action_execution_event,
    save_decision_outcome,
    summarize_action_execution,
    summarize_decision_logging,
    summarize_decision_outcomes,
    summarize_outcome_realization,
    summarize_outcome_ingestion,
    summarize_path_realization,
    summarize_realization_evaluation,
)
from credit_coach.utils.run_context import create_run_context

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_outcome_feedback")


def _json_default(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


def _format_metric(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.1%}"


def _build_outcome_realization_report(
    *,
    evaluation_summary: dict[str, Any],
) -> str:
    overall = dict(evaluation_summary.get("overall", {}))
    predicted_vs_observed = dict(evaluation_summary.get("predicted_vs_observed", {}))
    comparison = dict(evaluation_summary.get("recoverable_vs_limited_comparison", {}))
    populations = {
        str(item.get("group_key", "")): dict(item)
        for item in evaluation_summary.get("recoverable_vs_limited_summary", [])
        if isinstance(item, dict)
    }
    recoverable_full = populations.get("recoverable_full_mode", {})
    limited_control = populations.get("non_recoverable_limited_mode", {})
    overall_predicted = dict(predicted_vs_observed.get("overall", {}))

    lines = [
        "# Outcome Realization Report",
        "",
        "This report is descriptive and not causal.",
        "It summarizes observed execution and realized outcome signals from selected-path decisions and does not claim that recommendations caused the observed results or that the current policy delivered business uplift.",
        "",
        "## Overview",
        "",
        f"- Window: {int(evaluation_summary.get('window_days', 90))} days",
        f"- Decisions observed: {int(overall.get('total_decisions', 0))}",
        f"- Observation coverage: {_format_metric(overall.get('observation_coverage_rate'))}",
        f"- Action execution rate: {_format_metric(overall.get('action_execution_rate'))}",
        f"- Realized movement rate: {_format_metric(overall.get('realized_movement_rate'))}",
        f"- Threshold-reaching realization rate: {_format_metric(overall.get('threshold_reach_realization_rate'))}",
        f"- Approval realization rate: {_format_metric(overall.get('approval_realization_rate'))}",
        f"- Negative outcome rate: {_format_metric(overall.get('negative_outcome_rate'))}",
        f"- Evidence status: {str(overall.get('evidence_status', 'no_data'))}",
        "",
        "## Recoverable Vs Limited",
        "",
    ]
    if recoverable_full:
        lines.extend(
            [
                f"- Recoverable / full mode decisions: {int(recoverable_full.get('total_decisions', 0))}",
                f"- Recoverable / full mode observation coverage: {_format_metric(recoverable_full.get('observation_coverage_rate'))}",
                f"- Recoverable / full mode realized movement rate: {_format_metric(recoverable_full.get('realized_movement_rate'))}",
                f"- Recoverable / full mode threshold-reaching realization rate: {_format_metric(recoverable_full.get('threshold_reach_realization_rate'))}",
                f"- Recoverable / full mode evidence status: {str(recoverable_full.get('evidence_status', 'no_data'))}",
            ]
        )
    else:
        lines.append("- Recoverable / full mode slice: not observed in this run")
    if limited_control:
        lines.extend(
            [
                f"- Non-recoverable / limited mode decisions: {int(limited_control.get('total_decisions', 0))}",
                f"- Non-recoverable / limited mode observation coverage: {_format_metric(limited_control.get('observation_coverage_rate'))}",
                f"- Non-recoverable / limited mode realized movement rate: {_format_metric(limited_control.get('realized_movement_rate'))}",
                f"- Non-recoverable / limited mode threshold-reaching realization rate: {_format_metric(limited_control.get('threshold_reach_realization_rate'))}",
                f"- Non-recoverable / limited mode evidence status: {str(limited_control.get('evidence_status', 'no_data'))}",
            ]
        )
    else:
        lines.append("- Non-recoverable / limited mode slice: not observed in this run")
    if comparison.get("recoverable_full_mode_present") and comparison.get("non_recoverable_limited_mode_present"):
        lines.extend(
            [
                f"- Realized movement delta (recoverable full minus limited): {_format_metric(comparison.get('realized_movement_rate_delta'))}",
                f"- Threshold-reaching delta (recoverable full minus limited): {_format_metric(comparison.get('threshold_reach_realization_rate_delta'))}",
                f"- Observation coverage delta (recoverable full minus limited): {_format_metric(comparison.get('observation_coverage_rate_delta'))}",
            ]
        )
    else:
        lines.append("- Direct recoverable-vs-limited deltas are not available because one side of the control slice is missing")

    lines.extend(
        [
            "",
            "## Predicted Vs Observed",
            "",
            f"- Mean predicted plan execution probability: {_format_metric(overall_predicted.get('mean_plan_execution_probability'))}",
            f"- Observed action execution rate: {_format_metric(overall_predicted.get('observed_action_execution_rate'))}",
            f"- Plan execution gap (observed minus predicted): {_format_metric(overall_predicted.get('plan_execution_gap'))}",
            f"- Mean predicted combined realization probability: {_format_metric(overall_predicted.get('mean_combined_plan_realization_probability'))}",
            f"- Observed realized movement rate: {_format_metric(overall_predicted.get('observed_realized_movement_rate'))}",
            f"- Combined realization gap (observed minus predicted): {_format_metric(overall_predicted.get('combined_realization_gap'))}",
            f"- Mean predicted threshold reach probability: {_format_metric(overall_predicted.get('mean_threshold_reach_probability'))}",
            f"- Observed threshold-reaching realization rate: {_format_metric(overall_predicted.get('observed_threshold_reach_realization_rate'))}",
            f"- Threshold-reaching gap (observed minus predicted): {_format_metric(overall_predicted.get('threshold_reach_gap'))}",
            "",
            "## Guardrails",
            "",
            "- Sparse or pending observations should not be read as proof of success, failure, or policy uplift.",
            "- These comparisons are calibration-style evidence only; they are not causal attribution and they do not prove that a selected action produced an observed outcome.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest delayed decision outcomes and publish policy delta report")
    p.add_argument("--outcomes_csv", type=str, default="", help="Optional CSV to upsert outcomes")
    p.add_argument("--action_events_csv", type=str, default="", help="Optional CSV to append selected-action events")
    p.add_argument("--window_days", type=int, default=90)
    return p.parse_args()


def _optional_str(row: pd.Series, column: str) -> str:
    if column not in row or pd.isna(row[column]):
        return ""
    return str(row[column]).strip()


def _optional_float(row: pd.Series, column: str) -> float | None:
    if column not in row or pd.isna(row[column]):
        return None
    try:
        return float(row[column])
    except Exception:
        return None


def _optional_int(row: pd.Series, column: str) -> int | None:
    if column not in row or pd.isna(row[column]):
        return None
    try:
        return int(row[column])
    except Exception:
        return None


def _optional_bool(row: pd.Series, column: str) -> bool | None:
    if column not in row or pd.isna(row[column]):
        return None
    value = row[column]
    if isinstance(value, bool):
        return value
    try:
        if isinstance(value, (int, float)):
            return bool(int(value))
    except Exception:
        pass
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    return None


def _optional_datetime(row: pd.Series, column: str) -> datetime | None:
    if column not in row or pd.isna(row[column]):
        return None
    try:
        parsed = pd.to_datetime(row[column], utc=True)
    except Exception:
        return None
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime()


def _optional_json_dict(row: pd.Series, column: str) -> dict[str, str]:
    raw = _optional_str(row, column)
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
        if isinstance(loaded, dict):
            return {str(key): str(value or "") for key, value in loaded.items() if str(value or "")}
    except Exception:
        pass
    return {}


def _optional_reason_codes(row: pd.Series, column: str = "reason_codes") -> list[str]:
    raw = _optional_str(row, column)
    if not raw:
        return []
    if raw.startswith("["):
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, list):
                return [str(item).strip() for item in loaded if str(item).strip()]
        except Exception:
            pass
    return [piece for piece in (part.strip() for part in raw.replace(",", "|").split("|")) if piece]


def _ingest_csv(path: Path) -> int:
    df = pd.read_csv(path)
    required = {"decision_id", "run_id", "customer_id"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    inserted = 0
    for _, row in df.iterrows():
        rec = DecisionOutcomeRecord(
            decision_id=str(row["decision_id"]),
            run_id=str(row["run_id"]),
            customer_id=str(row["customer_id"]),
            policy_arm=str(row.get("policy_arm", "control")),
            policy_arm_profile=_optional_json_dict(row, "policy_arm_profile"),
            candidate_set_id=_optional_str(row, "candidate_set_id"),
            selected_plan_id=_optional_str(row, "selected_plan_id"),
            selected_plan_status=_optional_str(row, "selected_plan_status"),
            selected_path_id=_optional_str(row, "selected_path_id") or None,
            selected_path_type=_optional_str(row, "selected_path_type") or None,
            selected_path_movement_strength=_optional_str(row, "selected_path_movement_strength") or None,
            selected_offer_type=_optional_str(row, "selected_offer_type") or None,
            selection_propensity=_optional_float(row, "selection_propensity") or 1.0,
            propensity_source=_optional_str(row, "propensity_source") or "deterministic_fallback",
            reason_codes=_optional_reason_codes(row),
            recommended_plan_flag=bool(_optional_bool(row, "recommended_plan_flag") or False),
            selected_plan_policy_label=_optional_str(row, "selected_plan_policy_label") or None,
            trajectory_status=_optional_str(row, "trajectory_status") or None,
            recourse_mode=_optional_str(row, "recourse_mode") or None,
            recoverable_flag=_optional_bool(row, "recoverable_flag"),
            movement_score=_optional_float(row, "movement_score"),
            threshold_reach_probability=_optional_float(row, "threshold_reach_probability"),
            decision_status=str(row.get("decision_status", "UNKNOWN")),
            approved=bool(int(row.get("approved", 0))),
            predicted_pd=(float(row["predicted_pd"]) if "predicted_pd" in row and pd.notna(row["predicted_pd"]) else None),
            plan_execution_probability=_optional_float(row, "plan_execution_probability"),
            offer_acceptance_probability=_optional_float(row, "offer_acceptance_probability"),
            combined_plan_realization_probability=_optional_float(row, "combined_plan_realization_probability"),
            action_completed=_optional_bool(row, "action_completed"),
            offer_accepted=_optional_bool(row, "offer_accepted"),
            observed_payment_ratio_90d=_optional_float(row, "observed_payment_ratio_90d"),
            observed_recovery_amount_90d=_optional_float(row, "observed_recovery_amount_90d"),
            observed_default_30d=(int(row["observed_default_30d"]) if "observed_default_30d" in row and pd.notna(row["observed_default_30d"]) else None),
            observed_default_60d=(int(row["observed_default_60d"]) if "observed_default_60d" in row and pd.notna(row["observed_default_60d"]) else None),
            observed_default_90d=(int(row["observed_default_90d"]) if "observed_default_90d" in row and pd.notna(row["observed_default_90d"]) else None),
            observed_margin_90d=(float(row["observed_margin_90d"]) if "observed_margin_90d" in row and pd.notna(row["observed_margin_90d"]) else None),
        )
        save_decision_outcome(rec)
        inserted += 1
    return inserted


def _ingest_action_events_csv(path: Path) -> int:
    df = pd.read_csv(path)
    required = {"decision_id", "customer_id", "selected_plan_id", "action_key", "event_type", "event_at", "event_source"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    inserted = 0
    for _, row in df.iterrows():
        event_at = _optional_datetime(row, "event_at")
        if event_at is None:
            raise ValueError("action_events_csv contains invalid or missing event_at")
        rec = DecisionActionExecutionEventRecord(
            decision_id=str(row["decision_id"]),
            customer_id=str(row["customer_id"]),
            selected_plan_id=str(row["selected_plan_id"]),
            selected_path_id=_optional_str(row, "selected_path_id") or None,
            action_key=str(row["action_key"]),
            event_type=str(row["event_type"]).strip().lower(),
            event_at=event_at,
            event_source=str(row["event_source"]).strip(),
            evidence_reference=_optional_str(row, "evidence_reference") or None,
        )
        save_decision_action_execution_event(rec)
        inserted += 1
    return inserted


def main() -> None:
    args = parse_args()
    init_db()
    run_ctx = create_run_context(
        {
            "window_days": int(args.window_days),
            "outcomes_csv": str(args.outcomes_csv),
            "action_events_csv": str(args.action_events_csv),
        },
        base_artifact_dir="artifacts/runs",
    )

    ingested = 0
    action_events_ingested = 0
    if args.outcomes_csv:
        ingested = _ingest_csv(Path(args.outcomes_csv))
    if args.action_events_csv:
        action_events_ingested = _ingest_action_events_csv(Path(args.action_events_csv))

    summary_df = summarize_decision_outcomes(window_days=int(args.window_days))
    decision_logging_summary = summarize_decision_logging()
    outcome_ingestion_summary = summarize_outcome_ingestion(window_days=int(args.window_days))
    learning_dataset = load_decision_learning_dataset(window_days=int(args.window_days))
    action_events = load_decision_action_execution_events()
    action_execution_summary = summarize_action_execution()
    path_realization_summary = summarize_path_realization(window_days=int(args.window_days))
    outcome_realization_summary = summarize_outcome_realization(window_days=int(args.window_days))
    realization_evaluation = summarize_realization_evaluation(window_days=int(args.window_days))
    deltas = compute_policy_outcome_deltas(window_days=int(args.window_days))
    off_policy_evaluation = evaluate_off_policy(learning_dataset, baseline_arm="control")

    summary_out = run_ctx.tables_dir / "outcome_policy_summary.csv"
    deltas_out = run_ctx.tables_dir / "outcome_policy_deltas.json"
    outcome_feedback_out = run_ctx.tables_dir / "outcome_feedback_summary.json"
    decision_logging_out = run_ctx.tables_dir / "decision_logging_summary.json"
    ingestion_out = run_ctx.tables_dir / "outcome_ingestion_summary.json"
    learning_dataset_out = run_ctx.tables_dir / "outcome_learning_dataset.csv"
    action_events_out = run_ctx.tables_dir / "action_execution_events.csv"
    action_execution_summary_out = run_ctx.tables_dir / "action_execution_summary.csv"
    path_realization_summary_out = run_ctx.tables_dir / "path_realization_summary.json"
    outcome_realization_summary_out = run_ctx.tables_dir / "outcome_realization_summary.json"
    realization_evaluation_out = run_ctx.tables_dir / "outcome_realization_evaluation.json"
    realization_report_out = run_ctx.tables_dir / "outcome_realization_report.md"
    off_policy_out = run_ctx.tables_dir / "off_policy_evaluation.json"
    summary_df.to_csv(summary_out, index=False)
    deltas_out.write_text(json.dumps(deltas, indent=2, ensure_ascii=False), encoding="utf-8")
    outcome_feedback_out.write_text(json.dumps(deltas, indent=2, ensure_ascii=False), encoding="utf-8")
    decision_logging_out.write_text(json.dumps(decision_logging_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    ingestion_out.write_text(json.dumps(outcome_ingestion_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    learning_dataset.to_csv(learning_dataset_out, index=False)
    action_events.to_csv(action_events_out, index=False)
    action_execution_summary.to_csv(action_execution_summary_out, index=False)
    path_realization_summary_out.write_text(
        json.dumps(path_realization_summary, indent=2, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
    outcome_realization_summary_out.write_text(
        json.dumps(outcome_realization_summary, indent=2, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
    realization_evaluation_out.write_text(
        json.dumps(realization_evaluation, indent=2, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
    realization_report_out.write_text(
        _build_outcome_realization_report(evaluation_summary=realization_evaluation),
        encoding="utf-8",
    )
    off_policy_out.write_text(json.dumps(off_policy_evaluation, indent=2, ensure_ascii=False), encoding="utf-8")
    populations = {
        str(item.get("group_key", "")): dict(item)
        for item in realization_evaluation.get("recoverable_vs_limited_summary", [])
        if isinstance(item, dict)
    }
    predicted_vs_observed = dict(realization_evaluation.get("predicted_vs_observed", {}))
    overall_predicted = dict(predicted_vs_observed.get("overall", {}))
    run_ctx.save_metrics(
        {
            "window_days": int(args.window_days),
            "ingested_records": int(ingested),
            "action_events_ingested": int(action_events_ingested),
            "action_execution_rate": float(outcome_realization_summary.get("action_execution_rate", 0.0)),
            "path_realization_rate": float(outcome_realization_summary.get("path_realization_rate", 0.0)),
            "realized_movement_rate": float(outcome_realization_summary.get("realized_movement_rate", 0.0)),
            "approval_realization_rate": float(outcome_realization_summary.get("approval_realization_rate", 0.0)),
            "negative_outcome_rate": float(outcome_realization_summary.get("negative_outcome_rate", 0.0)),
            "realization_observation_coverage_rate": float(
                outcome_realization_summary.get("observation_coverage_rate", 0.0)
            ),
            "realization_evidence_status": str(realization_evaluation.get("overall", {}).get("evidence_status", "no_data")),
            "recoverable_full_realized_movement_rate": float(
                populations.get("recoverable_full_mode", {}).get("realized_movement_rate", 0.0)
            ),
            "limited_control_realized_movement_rate": float(
                populations.get("non_recoverable_limited_mode", {}).get("realized_movement_rate", 0.0)
            ),
            "predicted_execution_gap": float(overall_predicted.get("plan_execution_gap", 0.0) or 0.0),
            "predicted_combined_realization_gap": float(
                overall_predicted.get("combined_realization_gap", 0.0) or 0.0
            ),
            "policy_arm_count": int(summary_df["policy_arm"].nunique()) if not summary_df.empty else 0,
            "comparison_status": str(deltas.get("comparison_status", "no_data")),
            "outcome_feedback_confidence": str(deltas.get("outcome_feedback_confidence", "tentative")),
            "approval_rate_delta": float(deltas.get("approval_rate_delta", 0.0)),
            "default_rate_90d_delta": float(deltas.get("default_rate_90d_delta", 0.0)),
            "avg_margin_90d_delta": float(deltas.get("avg_margin_90d_delta", 0.0)),
            "decision_log_completeness": float(decision_logging_summary.get("decision_log_completeness", 0.0)),
            "reward_90d_coverage": float(outcome_ingestion_summary.get("reward_90d_coverage", 0.0)),
            "ope_confidence": str(off_policy_evaluation.get("ope_confidence", "tentative")),
        }
    )
    logger.info("Outcome feedback summary: %s", summary_out)
    logger.info("Outcome policy deltas: %s", deltas_out)
    logger.info("Outcome feedback machine-readable summary: %s", outcome_feedback_out)
    logger.info("Decision logging summary: %s", decision_logging_out)
    logger.info("Outcome ingestion summary: %s", ingestion_out)
    logger.info("Outcome learning dataset: %s", learning_dataset_out)
    logger.info("Action execution events: %s", action_events_out)
    logger.info("Action execution summary: %s", action_execution_summary_out)
    logger.info("Path realization summary: %s", path_realization_summary_out)
    logger.info("Outcome realization summary: %s", outcome_realization_summary_out)
    logger.info("Outcome realization evaluation: %s", realization_evaluation_out)
    logger.info("Outcome realization report: %s", realization_report_out)
    logger.info("Off-policy evaluation summary: %s", off_policy_out)


if __name__ == "__main__":
    main()
