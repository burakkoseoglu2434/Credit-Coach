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
    load_decision_learning_dataset,
    load_decision_action_execution_events,
    compute_policy_outcome_deltas,
    save_decision_action_execution_event,
    save_decision_outcome,
    summarize_decision_logging,
    summarize_decision_outcomes,
    summarize_outcome_ingestion,
)
from credit_coach.utils.run_context import create_run_context

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_outcome_feedback")


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
    deltas = compute_policy_outcome_deltas(window_days=int(args.window_days))
    off_policy_evaluation = evaluate_off_policy(learning_dataset, baseline_arm="control")

    summary_out = run_ctx.tables_dir / "outcome_policy_summary.csv"
    deltas_out = run_ctx.tables_dir / "outcome_policy_deltas.json"
    outcome_feedback_out = run_ctx.tables_dir / "outcome_feedback_summary.json"
    decision_logging_out = run_ctx.tables_dir / "decision_logging_summary.json"
    ingestion_out = run_ctx.tables_dir / "outcome_ingestion_summary.json"
    learning_dataset_out = run_ctx.tables_dir / "outcome_learning_dataset.csv"
    action_events_out = run_ctx.tables_dir / "action_execution_events.csv"
    off_policy_out = run_ctx.tables_dir / "off_policy_evaluation.json"
    summary_df.to_csv(summary_out, index=False)
    deltas_out.write_text(json.dumps(deltas, indent=2, ensure_ascii=False), encoding="utf-8")
    outcome_feedback_out.write_text(json.dumps(deltas, indent=2, ensure_ascii=False), encoding="utf-8")
    decision_logging_out.write_text(json.dumps(decision_logging_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    ingestion_out.write_text(json.dumps(outcome_ingestion_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    learning_dataset.to_csv(learning_dataset_out, index=False)
    action_events.to_csv(action_events_out, index=False)
    off_policy_out.write_text(json.dumps(off_policy_evaluation, indent=2, ensure_ascii=False), encoding="utf-8")
    run_ctx.save_metrics(
        {
            "window_days": int(args.window_days),
            "ingested_records": int(ingested),
            "action_events_ingested": int(action_events_ingested),
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
    logger.info("Off-policy evaluation summary: %s", off_policy_out)


if __name__ == "__main__":
    main()
