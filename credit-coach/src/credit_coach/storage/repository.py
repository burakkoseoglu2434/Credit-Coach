"""
storage/repository.py
=====================
CRUD operasyonlari + zincirli audit event kayitlari.

Repository pattern: ORM detayi bu modulde kalir, cagirici kod Pydantic
sema/sade dict ile calisir.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from credit_coach.data.schema import (
    CustomerSnapshot,
    DecisionActionExecutionEventRecord,
    DecisionOutcomeRecord,
    MacroSnapshot,
    ModelRunRecord,
    PlanRecord,
)
from credit_coach.storage.db import get_session
from credit_coach.storage.models import (
    AuditEventORM,
    CustomerSnapshotORM,
    DecisionActionExecutionEventORM,
    DecisionOutcomeContextORM,
    DecisionOutcomeORM,
    DecisionOutcomeRealizationContextORM,
    MacroSnapshotORM,
    ModelRunORM,
    PlanRecordORM,
)
from credit_coach.utils.hashing import hash_chain_event

logger = logging.getLogger(__name__)

CANONICAL_PROXY_METRICS = ["approval_rate", "default_rate_90d", "avg_margin_90d"]
LEARNING_READINESS_STATES = ["descriptive_only", "partial_learning_ready", "learning_ready"]
ACTION_EXECUTION_STATUSES = ["attempted", "completed", "blocked", "reversed"]
PATH_REALIZATION_STATUSES = ["pending_observation", "attempted", "blocked", "realized"]
OUTCOME_REALIZATION_LABELS = [
    "pending_observation",
    "no_observed_progress",
    "partial_progress",
    "threshold_reached",
    "approval_realized",
    "negative_outcome",
]


def _build_audit_envelope(
    event_type: str,
    entity_id: str | None,
    run_id: str | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "event_type": event_type,
        "entity_id": entity_id,
        "run_id": run_id,
        "payload": payload,
    }


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _to_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(int(value))
    normalized = str(value).strip().lower()
    if normalized in {"", "nan", "none", "null"}:
        return None
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    return None


def _normalize_reason_codes(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_clean_str(item) for item in value if _clean_str(item)]
    if isinstance(value, tuple):
        return [_clean_str(item) for item in value if _clean_str(item)]
    raw = _clean_str(value)
    if not raw:
        return []
    if raw.startswith("["):
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, list):
                return [_clean_str(item) for item in loaded if _clean_str(item)]
        except Exception:
            pass
    parts = [piece.strip() for piece in raw.replace(",", "|").split("|")]
    return [piece for piece in parts if piece]


def _normalize_policy_arm_profile(value: Any) -> dict[str, str]:
    if isinstance(value, dict):
        return {str(key): _clean_str(val) for key, val in value.items() if _clean_str(val)}
    raw = _clean_str(value)
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
        if isinstance(loaded, dict):
            return {str(key): _clean_str(val) for key, val in loaded.items() if _clean_str(val)}
    except Exception:
        pass
    return {}


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    try:
        return float(value)
    except Exception:
        return None


def _round_metric(value: Any) -> float:
    return round(float(value or 0.0), 6)


def _iso_or_empty(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return _clean_str(value)


def _distribution(values: pd.Series, allowed: list[str]) -> dict[str, float]:
    if values.empty:
        return {key: 0.0 for key in allowed}
    counts = values.value_counts(dropna=False).to_dict()
    total = max(1, int(values.shape[0]))
    return {key: _round_metric(float(counts.get(key, 0)) / total) for key in allowed}


def _mean_or_none(values: pd.Series) -> float | None:
    numeric = pd.to_numeric(values, errors="coerce")
    numeric = numeric.dropna()
    if numeric.empty:
        return None
    return _round_metric(numeric.mean())


def _realization_population_key(recoverable_flag: Any, recourse_mode: Any) -> str:
    recoverable = _to_bool(recoverable_flag)
    mode = _clean_str(recourse_mode)
    if recoverable is True and mode == "full":
        return "recoverable_full_mode"
    if recoverable is False and mode == "limited":
        return "non_recoverable_limited_mode"
    if mode == "full":
        return "full_mode_other"
    if mode == "limited":
        return "limited_mode_other"
    return "uncategorized"


def _realization_population_label(population_key: str) -> str:
    labels = {
        "recoverable_full_mode": "Recoverable / Full Mode",
        "non_recoverable_limited_mode": "Non-Recoverable / Limited Mode",
        "full_mode_other": "Full Mode / Other",
        "limited_mode_other": "Limited Mode / Other",
        "uncategorized": "Uncategorized",
    }
    return labels.get(population_key, population_key.replace("_", " ").title())


def _realization_evidence_status(total_decisions: int, observation_coverage_rate: float) -> str:
    if total_decisions <= 0:
        return "no_data"
    if total_decisions < 3 or observation_coverage_rate < 0.5:
        return "sparse"
    if observation_coverage_rate < 0.85:
        return "partial"
    return "sufficient"


def _summarize_realization_group(
    rows_df: pd.DataFrame,
    *,
    group_key: str,
    group_label: str,
) -> dict[str, Any]:
    total = int(rows_df.shape[0])
    if total <= 0:
        return {
            "group_key": group_key,
            "group_label": group_label,
            "total_decisions": 0,
            "observed_decisions": 0,
            "observation_coverage_rate": 0.0,
            "pending_observation_rate": 0.0,
            "action_execution_rate": 0.0,
            "path_realization_rate": 0.0,
            "realized_movement_rate": 0.0,
            "threshold_reach_realization_rate": 0.0,
            "approval_realization_rate": 0.0,
            "negative_outcome_rate": 0.0,
            "mean_movement_score": None,
            "mean_threshold_reach_probability": None,
            "mean_plan_execution_probability": None,
            "mean_combined_plan_realization_probability": None,
            "plan_execution_gap": None,
            "combined_realization_gap": None,
            "threshold_reach_gap": None,
            "evidence_status": "no_data",
        }

    observation_coverage_rate = _round_metric(rows_df["observation_coverage_flag"].mean())
    action_execution_rate = _round_metric(
        rows_df["path_realization_status"].isin(["attempted", "blocked", "realized"]).mean()
    )
    path_realization_rate = _round_metric((rows_df["path_realization_status"] == "realized").mean())
    realized_movement_rate = _round_metric(
        rows_df["outcome_realization_label"].isin(["partial_progress", "threshold_reached", "approval_realized"]).mean()
    )
    threshold_reach_realization_rate = _round_metric(
        rows_df["outcome_realization_label"].isin(["threshold_reached", "approval_realized"]).mean()
    )
    approval_realization_rate = _round_metric((rows_df["outcome_realization_label"] == "approval_realized").mean())
    negative_outcome_rate = _round_metric((rows_df["outcome_realization_label"] == "negative_outcome").mean())
    mean_movement_score = _mean_or_none(rows_df["movement_score"])
    mean_threshold_reach_probability = _mean_or_none(rows_df["threshold_reach_probability"])
    mean_plan_execution_probability = _mean_or_none(rows_df["plan_execution_probability"])
    mean_combined_plan_realization_probability = _mean_or_none(rows_df["combined_plan_realization_probability"])
    return {
        "group_key": group_key,
        "group_label": group_label,
        "total_decisions": total,
        "observed_decisions": int(rows_df["observation_coverage_flag"].sum()),
        "observation_coverage_rate": observation_coverage_rate,
        "pending_observation_rate": _round_metric((rows_df["outcome_realization_label"] == "pending_observation").mean()),
        "action_execution_rate": action_execution_rate,
        "path_realization_rate": path_realization_rate,
        "realized_movement_rate": realized_movement_rate,
        "threshold_reach_realization_rate": threshold_reach_realization_rate,
        "approval_realization_rate": approval_realization_rate,
        "negative_outcome_rate": negative_outcome_rate,
        "mean_movement_score": mean_movement_score,
        "mean_threshold_reach_probability": mean_threshold_reach_probability,
        "mean_plan_execution_probability": mean_plan_execution_probability,
        "mean_combined_plan_realization_probability": mean_combined_plan_realization_probability,
        "plan_execution_gap": (
            _round_metric(action_execution_rate - mean_plan_execution_probability)
            if mean_plan_execution_probability is not None
            else None
        ),
        "combined_realization_gap": (
            _round_metric(realized_movement_rate - mean_combined_plan_realization_probability)
            if mean_combined_plan_realization_probability is not None
            else None
        ),
        "threshold_reach_gap": (
            _round_metric(threshold_reach_realization_rate - mean_threshold_reach_probability)
            if mean_threshold_reach_probability is not None
            else None
        ),
        "evidence_status": _realization_evidence_status(total, observation_coverage_rate),
    }


def _frame_from_records(records: pd.DataFrame | list[dict[str, Any]]) -> pd.DataFrame:
    if isinstance(records, pd.DataFrame):
        return records.copy(deep=True)
    return pd.DataFrame(list(records))


def build_learning_dataset_frame(
    records: pd.DataFrame | list[dict[str, Any]],
    *,
    window_days: int = 90,
) -> pd.DataFrame:
    _ = int(window_days)
    df = _frame_from_records(records)
    expected_defaults: dict[str, Any] = {
        "decision_id": "",
        "run_id": "",
        "customer_id": "",
        "policy_arm": "control",
        "candidate_set_id": "",
        "selected_plan_id": "",
        "selected_plan_status": "",
        "selected_path_id": "",
        "selected_path_type": "",
        "selected_path_movement_strength": "",
        "selected_offer_type": "",
        "selection_propensity": None,
        "propensity_source": "",
        "reason_codes": None,
        "recommended_plan_flag": False,
        "selected_plan_policy_label": "",
        "trajectory_status": "",
        "recourse_mode": "",
        "recoverable_flag": None,
        "movement_score": None,
        "threshold_reach_probability": None,
        "approved": False,
        "predicted_pd": None,
        "plan_execution_probability": None,
        "offer_acceptance_probability": None,
        "combined_plan_realization_probability": None,
        "action_completed": None,
        "offer_accepted": None,
        "observed_payment_ratio_90d": None,
        "observed_recovery_amount_90d": None,
        "observed_default_30d": None,
        "observed_default_60d": None,
        "observed_default_90d": None,
        "observed_margin_90d": None,
    }
    for column, default in expected_defaults.items():
        if column not in df.columns:
            df[column] = default

    for column in [
        "decision_id",
        "run_id",
        "customer_id",
        "policy_arm",
        "candidate_set_id",
        "selected_plan_id",
        "selected_plan_status",
        "selected_path_id",
        "selected_path_type",
        "selected_path_movement_strength",
        "selected_offer_type",
        "propensity_source",
        "selected_plan_policy_label",
        "trajectory_status",
        "recourse_mode",
    ]:
        df[column] = df[column].map(_clean_str)

    df["reason_codes_list"] = df["reason_codes"].map(_normalize_reason_codes)
    df["reason_codes_count"] = df["reason_codes_list"].map(len).astype(int)
    df["selection_propensity"] = pd.to_numeric(df["selection_propensity"], errors="coerce")
    for column in [
        "predicted_pd",
        "plan_execution_probability",
        "offer_acceptance_probability",
        "combined_plan_realization_probability",
        "movement_score",
        "threshold_reach_probability",
        "observed_payment_ratio_90d",
        "observed_recovery_amount_90d",
        "observed_margin_90d",
    ]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in ["observed_default_30d", "observed_default_60d", "observed_default_90d"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in ["recommended_plan_flag", "approved", "action_completed", "offer_accepted", "recoverable_flag"]:
        df[column] = df[column].map(_to_bool)

    df["policy_metadata_complete"] = (
        df["policy_arm"].ne("")
        & df["selection_propensity"].notna()
        & df["propensity_source"].ne("")
    )
    df["decision_log_complete"] = (
        df["policy_metadata_complete"]
        & df["candidate_set_id"].ne("")
        & df["selected_plan_id"].ne("")
        & df["selected_plan_status"].ne("")
        & (df["reason_codes_count"] > 0)
    )
    df["has_action_completion"] = df["action_completed"].notna()
    df["has_offer_acceptance"] = df["offer_accepted"].notna()
    df["has_payment_behavior"] = df["observed_payment_ratio_90d"].notna()
    df["has_recovery_outcome"] = df["observed_recovery_amount_90d"].notna()
    df["has_default_90d_outcome"] = df["observed_default_90d"].notna()
    df["has_margin_90d_outcome"] = df["observed_margin_90d"].notna()
    df["has_reward_proxy_90d"] = df["has_default_90d_outcome"] | df["has_margin_90d_outcome"]

    df["learning_readiness_status"] = "descriptive_only"
    df.loc[df["decision_log_complete"] | df["has_reward_proxy_90d"], "learning_readiness_status"] = "partial_learning_ready"
    df.loc[df["decision_log_complete"] & df["policy_metadata_complete"] & df["has_reward_proxy_90d"], "learning_readiness_status"] = "learning_ready"

    return df


def build_decision_logging_summary(records: pd.DataFrame | list[dict[str, Any]]) -> dict[str, Any]:
    df = build_learning_dataset_frame(records)
    total = int(len(df))
    complete_count = int(df["decision_log_complete"].astype(bool).sum()) if total else 0
    return {
        "total_decisions": total,
        "complete_decision_logs": complete_count,
        "decision_log_completeness": float(complete_count / max(1, total)),
        "policy_metadata_coverage": float(df["policy_metadata_complete"].astype(bool).mean()) if total else 0.0,
        "selection_propensity_coverage": float(df["selection_propensity"].notna().mean()) if total else 0.0,
        "candidate_set_coverage": float(df["candidate_set_id"].ne("").mean()) if total else 0.0,
        "reason_code_coverage": float((df["reason_codes_count"] > 0).mean()) if total else 0.0,
        "recommended_plan_rate": float(df["recommended_plan_flag"].fillna(False).astype(bool).mean()) if total else 0.0,
        "propensity_source_breakdown": (
            df["propensity_source"].replace("", "missing").value_counts(dropna=False).to_dict() if total else {}
        ),
    }


def build_outcome_ingestion_summary(
    records: pd.DataFrame | list[dict[str, Any]],
    *,
    window_days: int = 90,
) -> dict[str, Any]:
    df = build_learning_dataset_frame(records, window_days=window_days)
    total = int(len(df))
    status_distribution: dict[str, dict[str, float | int]] = {}
    for status in LEARNING_READINESS_STATES:
        count = int((df["learning_readiness_status"] == status).sum()) if total else 0
        status_distribution[status] = {
            "count": count,
            "share": float(count / max(1, total)),
        }
    return {
        "window_days": int(window_days),
        "total_records": total,
        "primary_learning_window_days": 90,
        "decision_log_completeness": float(df["decision_log_complete"].astype(bool).mean()) if total else 0.0,
        "reward_90d_coverage": float(df["has_reward_proxy_90d"].astype(bool).mean()) if total else 0.0,
        "default_90d_coverage": float(df["has_default_90d_outcome"].astype(bool).mean()) if total else 0.0,
        "margin_90d_coverage": float(df["has_margin_90d_outcome"].astype(bool).mean()) if total else 0.0,
        "has_action_completion_rate": float(df["has_action_completion"].astype(bool).mean()) if total else 0.0,
        "has_offer_acceptance_rate": float(df["has_offer_acceptance"].astype(bool).mean()) if total else 0.0,
        "has_payment_behavior_rate": float(df["has_payment_behavior"].astype(bool).mean()) if total else 0.0,
        "has_recovery_outcome_rate": float(df["has_recovery_outcome"].astype(bool).mean()) if total else 0.0,
        "learning_readiness_status_distribution": status_distribution,
    }


def _load_decision_outcome_rows() -> list[dict[str, Any]]:
    with get_session() as session:
        outcome_rows = session.query(DecisionOutcomeORM).all()
        context_rows = session.query(DecisionOutcomeContextORM).all()
        realization_rows = session.query(DecisionOutcomeRealizationContextORM).all()

    context_by_decision_id = {str(row.decision_id): row for row in context_rows}
    realization_by_decision_id = {str(row.decision_id): row for row in realization_rows}
    rows: list[dict[str, Any]] = []
    for row in outcome_rows:
        context = context_by_decision_id.get(str(row.decision_id))
        realization = realization_by_decision_id.get(str(row.decision_id))
        rows.append(
            {
                "decision_id": str(row.decision_id),
                "run_id": str(row.run_id),
                "customer_id": str(row.customer_id),
                "policy_arm": str(row.policy_arm),
                "policy_arm_profile": context.policy_arm_profile if context is not None else _policy_arm_profile(str(row.policy_arm)),
                "candidate_set_id": _clean_str(getattr(context, "candidate_set_id", "")),
                "selected_plan_id": _clean_str(getattr(context, "selected_plan_id", "")),
                "selected_plan_status": _clean_str(getattr(context, "selected_plan_status", "")),
                "selected_path_id": _clean_str(getattr(realization, "selected_path_id", "")),
                "selected_path_type": _clean_str(getattr(realization, "selected_path_type", "")),
                "selected_path_movement_strength": _clean_str(
                    getattr(realization, "selected_path_movement_strength", "")
                ),
                "selected_offer_type": _clean_str(getattr(context, "selected_offer_type", "")),
                "selection_propensity": _safe_float(getattr(context, "selection_propensity", None)),
                "propensity_source": _clean_str(getattr(context, "propensity_source", "")),
                "reason_codes": list(getattr(context, "reason_codes", [])) if context is not None else [],
                "recommended_plan_flag": bool(getattr(context, "recommended_plan_flag", False)) if context is not None else False,
                "selected_plan_policy_label": _clean_str(getattr(context, "selected_plan_policy_label", "")),
                "trajectory_status": _clean_str(getattr(context, "trajectory_status", "")),
                "recourse_mode": _clean_str(getattr(realization, "recourse_mode", "")),
                "recoverable_flag": getattr(realization, "recoverable_flag", None),
                "movement_score": _safe_float(getattr(realization, "movement_score", None)),
                "threshold_reach_probability": _safe_float(
                    getattr(realization, "threshold_reach_probability", None)
                ),
                "decision_status": str(row.decision_status),
                "approved": bool(row.approved),
                "predicted_pd": _safe_float(row.predicted_pd),
                "plan_execution_probability": _safe_float(getattr(context, "plan_execution_probability", None)),
                "offer_acceptance_probability": _safe_float(getattr(context, "offer_acceptance_probability", None)),
                "combined_plan_realization_probability": _safe_float(
                    getattr(context, "combined_plan_realization_probability", None)
                ),
                "action_completed": getattr(context, "action_completed", None),
                "offer_accepted": getattr(context, "offer_accepted", None),
                "observed_payment_ratio_90d": _safe_float(getattr(context, "observed_payment_ratio_90d", None)),
                "observed_recovery_amount_90d": _safe_float(getattr(context, "observed_recovery_amount_90d", None)),
                "observed_default_30d": row.observed_default_30d,
                "observed_default_60d": row.observed_default_60d,
                "observed_default_90d": row.observed_default_90d,
                "observed_margin_90d": _safe_float(row.observed_margin_90d),
                "observed_at": row.observed_at,
            }
        )
    return rows


def _latest_event_hash(session: Session) -> str | None:
    row = (
        session.query(AuditEventORM.event_hash)
        .order_by(AuditEventORM.id.desc())
        .first()
    )
    return row[0] if row is not None else None


def _append_audit_event(
    session: Session,
    event_type: str,
    payload: dict[str, Any],
    *,
    entity_id: str | None = None,
    run_id: str | None = None,
) -> int:
    prev_hash = _latest_event_hash(session)
    envelope = _build_audit_envelope(
        event_type=event_type,
        entity_id=entity_id,
        run_id=run_id,
        payload=payload,
    )
    event_hash = hash_chain_event(payload=envelope, prev_hash=prev_hash)

    orm = AuditEventORM(
        event_type=event_type,
        entity_id=entity_id,
        run_id=run_id,
        payload_json=json.dumps(payload, ensure_ascii=False),
        prev_hash=prev_hash,
        event_hash=event_hash,
    )
    session.add(orm)
    session.flush()
    return int(orm.id)


# ------------------------------------------------------------------ #
# CustomerSnapshot
# ------------------------------------------------------------------ #
def save_customer_snapshot(snapshot: CustomerSnapshot) -> int:
    orm = CustomerSnapshotORM(
        customer_id=snapshot.customer_id,
        snapshot_date=snapshot.snapshot_date,
        features_json=json.dumps(snapshot.features, ensure_ascii=False),
        risk_score=snapshot.risk_score,
        source=snapshot.source,
    )
    with get_session() as session:
        session.add(orm)
        session.flush()
        record_id = int(orm.id)
        _append_audit_event(
            session=session,
            event_type="customer_snapshot_saved",
            entity_id=snapshot.customer_id,
            payload={"snapshot_id": record_id, "source": snapshot.source},
        )
        session.commit()
    logger.debug("Saved CustomerSnapshot id=%d customer=%s", record_id, snapshot.customer_id)
    return record_id


# ------------------------------------------------------------------ #
# PlanRecord
# ------------------------------------------------------------------ #
def save_plan(plan: PlanRecord, snapshot_id: int | None = None) -> int:
    actions_data = [a.model_dump() for a in plan.actions]
    orm = PlanRecordORM(
        plan_id=plan.plan_id,
        customer_id=plan.customer_id,
        run_id=plan.run_id,
        snapshot_id=snapshot_id,
        horizon_months=plan.horizon_months,
        strategy=plan.strategy,
        actions_json=json.dumps(actions_data, ensure_ascii=False),
        predicted_pd=plan.predicted_pd,
        ci_low=plan.ci_low,
        ci_high=plan.ci_high,
        alpha_used=plan.alpha_used,
        risk_margin=plan.risk_margin,
        reliability=plan.reliability,
        causal_penalty=plan.causal_penalty,
        score=plan.score,
        status=plan.status,
        status_reason=plan.status_reason,
    )
    with get_session() as session:
        session.add(orm)
        session.flush()
        record_id = int(orm.id)
        _append_audit_event(
            session=session,
            event_type="plan_saved",
            entity_id=plan.plan_id,
            run_id=plan.run_id,
            payload={
                "customer_id": plan.customer_id,
                "horizon_months": int(plan.horizon_months),
                "strategy": str(plan.strategy),
                "status": str(plan.status),
                "predicted_pd": plan.predicted_pd,
                "action_count": len(plan.actions),
            },
        )
        session.commit()
    logger.debug("Saved PlanRecord id=%d plan_id=%s status=%s", record_id, plan.plan_id, plan.status)
    return record_id


def get_plans_for_customer(customer_id: str) -> list[dict]:
    with get_session() as session:
        rows = (
            session.query(PlanRecordORM)
            .filter(PlanRecordORM.customer_id == customer_id)
            .order_by(PlanRecordORM.created_at.desc())
            .all()
        )
        result = []
        for row in rows:
            result.append(
                {
                    "plan_id": row.plan_id,
                    "customer_id": row.customer_id,
                    "run_id": row.run_id,
                    "horizon_months": row.horizon_months,
                    "strategy": row.strategy,
                    "actions": row.actions,
                    "predicted_pd": row.predicted_pd,
                    "ci_low": row.ci_low,
                    "ci_high": row.ci_high,
                    "risk_margin": row.risk_margin,
                    "reliability": row.reliability,
                    "score": row.score,
                    "status": row.status,
                    "status_reason": row.status_reason,
                    "created_at": row.created_at.isoformat(),
                }
            )
    return result


# ------------------------------------------------------------------ #
# ModelRunRecord
# ------------------------------------------------------------------ #
def save_model_run(record: ModelRunRecord) -> int:
    orm = ModelRunORM(
        run_id=record.run_id,
        model_version=record.model_version,
        run_type=record.run_type,
        config_hash=record.config_hash,
        metrics_json=json.dumps(record.metrics, ensure_ascii=False),
        tau_used=record.tau_used,
        notes=record.notes,
    )
    with get_session() as session:
        session.add(orm)
        session.flush()
        record_id = int(orm.id)
        _append_audit_event(
            session=session,
            event_type="model_run_saved",
            entity_id=record.model_version,
            run_id=record.run_id,
            payload={
                "run_type": record.run_type,
                "config_hash": record.config_hash,
                "tau_used": record.tau_used,
                "metric_keys": sorted(record.metrics.keys()),
            },
        )
        session.commit()
    logger.debug("Saved ModelRun id=%d run_id=%s type=%s", record_id, record.run_id, record.run_type)
    return record_id


def get_latest_model_run(run_type: str = "train") -> dict | None:
    with get_session() as session:
        row = (
            session.query(ModelRunORM)
            .filter(ModelRunORM.run_type == run_type)
            .order_by(ModelRunORM.created_at.desc())
            .first()
        )
        if row is None:
            return None
        return {
            "run_id": row.run_id,
            "model_version": row.model_version,
            "run_type": row.run_type,
            "metrics": row.metrics,
            "tau_used": row.tau_used,
            "is_champion": row.is_champion,
            "created_at": row.created_at.isoformat(),
        }


# ------------------------------------------------------------------ #
# DecisionOutcome
# ------------------------------------------------------------------ #
def save_decision_outcome(record: DecisionOutcomeRecord) -> int:
    orm = DecisionOutcomeORM(
        decision_id=record.decision_id,
        run_id=record.run_id,
        customer_id=record.customer_id,
        policy_arm=record.policy_arm,
        decision_status=record.decision_status,
        approved=bool(record.approved),
        predicted_pd=record.predicted_pd,
        observed_default_30d=record.observed_default_30d,
        observed_default_60d=record.observed_default_60d,
        observed_default_90d=record.observed_default_90d,
        observed_margin_90d=record.observed_margin_90d,
        observed_at=record.observed_at,
    )
    with get_session() as session:
        existing = session.query(DecisionOutcomeORM).filter(DecisionOutcomeORM.decision_id == record.decision_id).first()
        if existing is not None:
            existing.run_id = record.run_id
            existing.customer_id = record.customer_id
            existing.policy_arm = record.policy_arm
            existing.decision_status = record.decision_status
            existing.approved = bool(record.approved)
            existing.predicted_pd = record.predicted_pd
            existing.observed_default_30d = record.observed_default_30d
            existing.observed_default_60d = record.observed_default_60d
            existing.observed_default_90d = record.observed_default_90d
            existing.observed_margin_90d = record.observed_margin_90d
            existing.observed_at = record.observed_at
            session.flush()
            record_id = int(existing.id)
            action = "updated"
        else:
            session.add(orm)
            session.flush()
            record_id = int(orm.id)
            action = "created"
        context_existing = (
            session.query(DecisionOutcomeContextORM)
            .filter(DecisionOutcomeContextORM.decision_id == record.decision_id)
            .first()
        )
        context_payload = {
            "run_id": record.run_id,
            "customer_id": record.customer_id,
            "candidate_set_id": _clean_str(record.candidate_set_id),
            "policy_arm_profile": _normalize_policy_arm_profile(record.policy_arm_profile),
            "selected_plan_id": _clean_str(record.selected_plan_id),
            "selected_plan_status": _clean_str(record.selected_plan_status),
            "selected_offer_type": _clean_str(record.selected_offer_type),
            "selection_propensity": _safe_float(record.selection_propensity),
            "propensity_source": _clean_str(record.propensity_source),
            "reason_codes": _normalize_reason_codes(record.reason_codes),
            "recommended_plan_flag": bool(record.recommended_plan_flag),
            "selected_plan_policy_label": _clean_str(record.selected_plan_policy_label),
            "trajectory_status": _clean_str(record.trajectory_status),
            "plan_execution_probability": _safe_float(record.plan_execution_probability),
            "offer_acceptance_probability": _safe_float(record.offer_acceptance_probability),
            "combined_plan_realization_probability": _safe_float(record.combined_plan_realization_probability),
            "action_completed": _to_bool(record.action_completed),
            "offer_accepted": _to_bool(record.offer_accepted),
            "observed_payment_ratio_90d": _safe_float(record.observed_payment_ratio_90d),
            "observed_recovery_amount_90d": _safe_float(record.observed_recovery_amount_90d),
        }
        realization_existing = (
            session.query(DecisionOutcomeRealizationContextORM)
            .filter(DecisionOutcomeRealizationContextORM.decision_id == record.decision_id)
            .first()
        )
        realization_payload = {
            "run_id": record.run_id,
            "customer_id": record.customer_id,
            "selected_plan_id": _clean_str(record.selected_plan_id),
            "selected_path_id": _clean_str(record.selected_path_id),
            "selected_path_type": _clean_str(record.selected_path_type),
            "selected_path_movement_strength": _clean_str(record.selected_path_movement_strength),
            "recourse_mode": _clean_str(record.recourse_mode),
            "recoverable_flag": _to_bool(record.recoverable_flag),
            "movement_score": _safe_float(record.movement_score),
            "threshold_reach_probability": _safe_float(record.threshold_reach_probability),
        }
        if context_existing is not None:
            context_existing.run_id = str(context_payload["run_id"])
            context_existing.customer_id = str(context_payload["customer_id"])
            context_existing.candidate_set_id = context_payload["candidate_set_id"] or None
            context_existing.policy_arm_profile = dict(context_payload["policy_arm_profile"])
            context_existing.selected_plan_id = context_payload["selected_plan_id"] or None
            context_existing.selected_plan_status = context_payload["selected_plan_status"] or None
            context_existing.selected_offer_type = context_payload["selected_offer_type"] or None
            context_existing.selection_propensity = context_payload["selection_propensity"]
            context_existing.propensity_source = context_payload["propensity_source"] or None
            context_existing.reason_codes = list(context_payload["reason_codes"])
            context_existing.recommended_plan_flag = bool(context_payload["recommended_plan_flag"])
            context_existing.selected_plan_policy_label = context_payload["selected_plan_policy_label"] or None
            context_existing.trajectory_status = context_payload["trajectory_status"] or None
            context_existing.plan_execution_probability = context_payload["plan_execution_probability"]
            context_existing.offer_acceptance_probability = context_payload["offer_acceptance_probability"]
            context_existing.combined_plan_realization_probability = context_payload[
                "combined_plan_realization_probability"
            ]
            context_existing.action_completed = context_payload["action_completed"]
            context_existing.offer_accepted = context_payload["offer_accepted"]
            context_existing.observed_payment_ratio_90d = context_payload["observed_payment_ratio_90d"]
            context_existing.observed_recovery_amount_90d = context_payload["observed_recovery_amount_90d"]
        else:
            context_existing = DecisionOutcomeContextORM(
                decision_id=record.decision_id,
                run_id=record.run_id,
                customer_id=record.customer_id,
            )
            context_existing.candidate_set_id = context_payload["candidate_set_id"] or None
            context_existing.policy_arm_profile = dict(context_payload["policy_arm_profile"])
            context_existing.selected_plan_id = context_payload["selected_plan_id"] or None
            context_existing.selected_plan_status = context_payload["selected_plan_status"] or None
            context_existing.selected_offer_type = context_payload["selected_offer_type"] or None
            context_existing.selection_propensity = context_payload["selection_propensity"]
            context_existing.propensity_source = context_payload["propensity_source"] or None
            context_existing.reason_codes = list(context_payload["reason_codes"])
            context_existing.recommended_plan_flag = bool(context_payload["recommended_plan_flag"])
            context_existing.selected_plan_policy_label = context_payload["selected_plan_policy_label"] or None
            context_existing.trajectory_status = context_payload["trajectory_status"] or None
            context_existing.plan_execution_probability = context_payload["plan_execution_probability"]
            context_existing.offer_acceptance_probability = context_payload["offer_acceptance_probability"]
            context_existing.combined_plan_realization_probability = context_payload[
                "combined_plan_realization_probability"
            ]
            context_existing.action_completed = context_payload["action_completed"]
            context_existing.offer_accepted = context_payload["offer_accepted"]
            context_existing.observed_payment_ratio_90d = context_payload["observed_payment_ratio_90d"]
            context_existing.observed_recovery_amount_90d = context_payload["observed_recovery_amount_90d"]
            session.add(context_existing)
        if realization_existing is not None:
            realization_existing.run_id = str(realization_payload["run_id"])
            realization_existing.customer_id = str(realization_payload["customer_id"])
            realization_existing.selected_plan_id = realization_payload["selected_plan_id"] or None
            realization_existing.selected_path_id = realization_payload["selected_path_id"] or None
            realization_existing.selected_path_type = realization_payload["selected_path_type"] or None
            realization_existing.selected_path_movement_strength = (
                realization_payload["selected_path_movement_strength"] or None
            )
            realization_existing.recourse_mode = realization_payload["recourse_mode"] or None
            realization_existing.recoverable_flag = realization_payload["recoverable_flag"]
            realization_existing.movement_score = realization_payload["movement_score"]
            realization_existing.threshold_reach_probability = realization_payload["threshold_reach_probability"]
        else:
            realization_existing = DecisionOutcomeRealizationContextORM(
                decision_id=record.decision_id,
                run_id=record.run_id,
                customer_id=record.customer_id,
            )
            realization_existing.selected_plan_id = realization_payload["selected_plan_id"] or None
            realization_existing.selected_path_id = realization_payload["selected_path_id"] or None
            realization_existing.selected_path_type = realization_payload["selected_path_type"] or None
            realization_existing.selected_path_movement_strength = (
                realization_payload["selected_path_movement_strength"] or None
            )
            realization_existing.recourse_mode = realization_payload["recourse_mode"] or None
            realization_existing.recoverable_flag = realization_payload["recoverable_flag"]
            realization_existing.movement_score = realization_payload["movement_score"]
            realization_existing.threshold_reach_probability = realization_payload["threshold_reach_probability"]
            session.add(realization_existing)
        _append_audit_event(
            session=session,
            event_type="decision_outcome_saved",
            entity_id=record.decision_id,
            run_id=record.run_id,
            payload={
                "policy_arm": str(record.policy_arm),
                "approved": bool(record.approved),
                "decision_status": str(record.decision_status),
                "observed_default_90d": record.observed_default_90d,
                "selected_plan_id": _clean_str(record.selected_plan_id),
                "candidate_set_id": _clean_str(record.candidate_set_id),
                "selection_propensity": _safe_float(record.selection_propensity),
                "propensity_source": _clean_str(record.propensity_source),
                "selected_path_id": _clean_str(record.selected_path_id),
                "action": action,
            },
        )
        session.commit()
    return record_id


def save_decision_action_execution_event(record: DecisionActionExecutionEventRecord) -> int:
    orm = DecisionActionExecutionEventORM(
        decision_id=record.decision_id,
        customer_id=record.customer_id,
        selected_plan_id=record.selected_plan_id,
        selected_path_id=_clean_str(record.selected_path_id) or None,
        action_key=record.action_key,
        event_type=record.event_type,
        event_at=record.event_at,
        event_source=_clean_str(record.event_source),
        evidence_reference=_clean_str(record.evidence_reference) or None,
    )
    with get_session() as session:
        session.add(orm)
        session.flush()
        record_id = int(orm.id)
        _append_audit_event(
            session=session,
            event_type="decision_action_execution_event_saved",
            entity_id=record.decision_id,
            payload={
                "event_id": record_id,
                "customer_id": record.customer_id,
                "selected_plan_id": record.selected_plan_id,
                "selected_path_id": _clean_str(record.selected_path_id),
                "action_key": record.action_key,
                "event_type": record.event_type,
                "event_source": _clean_str(record.event_source),
            },
        )
        session.commit()
    return record_id


def load_decision_action_execution_events(*, decision_id: str | None = None) -> pd.DataFrame:
    with get_session() as session:
        query = session.query(DecisionActionExecutionEventORM)
        if _clean_str(decision_id):
            query = query.filter(DecisionActionExecutionEventORM.decision_id == _clean_str(decision_id))
        rows = query.order_by(
            DecisionActionExecutionEventORM.event_at.asc(),
            DecisionActionExecutionEventORM.id.asc(),
        ).all()

    return pd.DataFrame(
        [
            {
                "event_id": int(row.id),
                "decision_id": str(row.decision_id),
                "customer_id": str(row.customer_id),
                "selected_plan_id": str(row.selected_plan_id),
                "selected_path_id": _clean_str(row.selected_path_id),
                "action_key": str(row.action_key),
                "event_type": str(row.event_type),
                "event_at": row.event_at,
                "event_source": str(row.event_source),
                "evidence_reference": _clean_str(row.evidence_reference),
            }
            for row in rows
        ]
    )


def summarize_action_execution(*, decision_id: str | None = None) -> pd.DataFrame:
    events = load_decision_action_execution_events(decision_id=decision_id)
    columns = [
        "decision_id",
        "customer_id",
        "selected_plan_id",
        "selected_path_id",
        "action_key",
        "action_status",
        "latest_event_type",
        "latest_event_at",
        "latest_event_source",
        "event_count",
        "attempted_event_count",
        "completed_event_count",
        "blocked_event_count",
        "reversed_event_count",
        "first_execution_at",
        "first_completed_at",
        "time_to_first_execution_days",
        "time_to_first_completed_action_days",
    ]
    if events.empty:
        return pd.DataFrame(columns=columns)

    events = events.copy(deep=True)
    events["decision_id"] = events["decision_id"].map(_clean_str)
    events["selected_plan_id"] = events["selected_plan_id"].map(_clean_str)
    events["selected_path_id"] = events["selected_path_id"].map(_clean_str)
    events["action_key"] = events["action_key"].map(_clean_str)
    events["event_type"] = events["event_type"].map(_clean_str).str.lower()
    events["event_source"] = events["event_source"].map(_clean_str)
    events["event_at"] = pd.to_datetime(events["event_at"], errors="coerce", utc=True)
    precedence = {"attempted": 1, "blocked": 2, "completed": 3, "reversed": 4}
    events["event_priority"] = events["event_type"].map(lambda value: precedence.get(value, 0))
    events = events.sort_values(
        by=["decision_id", "selected_plan_id", "selected_path_id", "action_key", "event_at", "event_priority", "event_id"],
        ascending=[True, True, True, True, True, True, True],
        kind="stable",
    )

    rows: list[dict[str, Any]] = []
    group_cols = ["decision_id", "customer_id", "selected_plan_id", "selected_path_id", "action_key"]
    for keys, group in events.groupby(group_cols, dropna=False):
        latest = group.iloc[-1]
        execution_events = group[group["event_type"].isin(["attempted", "completed", "reversed"])]
        completed_events = group[group["event_type"] == "completed"]
        rows.append(
            {
                "decision_id": keys[0],
                "customer_id": keys[1],
                "selected_plan_id": keys[2],
                "selected_path_id": keys[3],
                "action_key": keys[4],
                "action_status": str(latest["event_type"]),
                "latest_event_type": str(latest["event_type"]),
                "latest_event_at": latest["event_at"],
                "latest_event_source": str(latest["event_source"]),
                "event_count": int(group.shape[0]),
                "attempted_event_count": int((group["event_type"] == "attempted").sum()),
                "completed_event_count": int((group["event_type"] == "completed").sum()),
                "blocked_event_count": int((group["event_type"] == "blocked").sum()),
                "reversed_event_count": int((group["event_type"] == "reversed").sum()),
                "first_execution_at": execution_events["event_at"].min() if not execution_events.empty else pd.NaT,
                "first_completed_at": completed_events["event_at"].min() if not completed_events.empty else pd.NaT,
                # Decision-issued timestamps are not yet preserved on the outcome seam, so latency stays explicit-null.
                "time_to_first_execution_days": None,
                "time_to_first_completed_action_days": None,
            }
        )

    return pd.DataFrame(rows, columns=columns)


def summarize_path_realization(*, window_days: int = 90) -> dict[str, Any]:
    decision_rows = build_learning_dataset_frame(_load_decision_outcome_rows(), window_days=window_days)
    action_summary = summarize_action_execution()
    row_records: list[dict[str, Any]] = []
    if decision_rows.empty:
        return {
            "window_days": int(window_days),
            "total_decisions": 0,
            "path_realization_rate": 0.0,
            "blocked_path_rate": 0.0,
            "attempted_path_rate": 0.0,
            "observation_coverage_rate": 0.0,
            "path_realization_status_distribution": {key: 0.0 for key in PATH_REALIZATION_STATUSES},
            "rows": row_records,
        }

    for _, decision in decision_rows.iterrows():
        decision_id = _clean_str(decision.get("decision_id"))
        selected_path_id = _clean_str(decision.get("selected_path_id"))
        if action_summary.empty:
            scoped_actions = action_summary
        else:
            scoped_actions = action_summary[action_summary["decision_id"].eq(decision_id)]
            if selected_path_id:
                scoped_actions = scoped_actions[
                    scoped_actions["selected_path_id"].fillna("").astype(str).map(_clean_str).eq(selected_path_id)
                ]

        completed_signal = bool(decision.get("action_completed") is True) or (
            not scoped_actions.empty and scoped_actions["action_status"].eq("completed").any()
        )
        blocked_signal = (not completed_signal) and (
            (not scoped_actions.empty and scoped_actions["action_status"].eq("blocked").any())
        )
        attempted_signal = (not completed_signal) and (not blocked_signal) and (
            not scoped_actions.empty and scoped_actions["action_status"].isin(["attempted", "reversed"]).any()
        )
        if completed_signal:
            path_status = "realized"
        elif blocked_signal:
            path_status = "blocked"
        elif attempted_signal:
            path_status = "attempted"
        else:
            path_status = "pending_observation"

        coverage_flag = int(
            bool(decision.get("action_completed") is not None)
            or bool(decision.get("offer_accepted") is not None)
            or bool(decision.get("has_reward_proxy_90d"))
            or bool(decision.get("has_payment_behavior"))
            or bool(decision.get("has_recovery_outcome"))
            or (not scoped_actions.empty)
            or str(decision.get("decision_status", "")).upper() in {"APPROVED", "CONDITIONAL"}
        )
        row_records.append(
            {
                "decision_id": decision_id,
                "customer_id": _clean_str(decision.get("customer_id")),
                "selected_plan_id": _clean_str(decision.get("selected_plan_id")),
                "selected_path_id": selected_path_id,
                "selected_path_type": _clean_str(decision.get("selected_path_type")),
                "recourse_mode": _clean_str(decision.get("recourse_mode")),
                "recoverable_flag": _to_bool(decision.get("recoverable_flag")),
                "path_realization_status": path_status,
                "action_rows_observed": int(scoped_actions.shape[0]),
                "completed_action_count": int(scoped_actions["action_status"].eq("completed").sum()) if not scoped_actions.empty else 0,
                "blocked_action_count": int(scoped_actions["action_status"].eq("blocked").sum()) if not scoped_actions.empty else 0,
                "attempted_action_count": int(scoped_actions["action_status"].eq("attempted").sum()) if not scoped_actions.empty else 0,
                "reversed_action_count": int(scoped_actions["action_status"].eq("reversed").sum()) if not scoped_actions.empty else 0,
                "observation_coverage_flag": coverage_flag,
                "first_execution_at": scoped_actions["first_execution_at"].dropna().min() if not scoped_actions.empty else pd.NaT,
                "first_completed_at": scoped_actions["first_completed_at"].dropna().min() if not scoped_actions.empty else pd.NaT,
                "time_to_first_execution_days": None,
                "time_to_first_completed_action_days": None,
            }
        )

    rows_df = pd.DataFrame(row_records)
    statuses = rows_df["path_realization_status"] if not rows_df.empty else pd.Series(dtype=object)
    return {
        "window_days": int(window_days),
        "total_decisions": int(rows_df.shape[0]),
        "path_realization_rate": _round_metric((statuses == "realized").mean()) if not rows_df.empty else 0.0,
        "blocked_path_rate": _round_metric((statuses == "blocked").mean()) if not rows_df.empty else 0.0,
        "attempted_path_rate": _round_metric((statuses == "attempted").mean()) if not rows_df.empty else 0.0,
        "observation_coverage_rate": _round_metric(rows_df["observation_coverage_flag"].mean()) if not rows_df.empty else 0.0,
        "path_realization_status_distribution": _distribution(statuses, PATH_REALIZATION_STATUSES),
        "rows": [
            {
                **{key: value for key, value in row.items() if key not in {"first_execution_at", "first_completed_at"}},
                "first_execution_at": _iso_or_empty(row.get("first_execution_at")),
                "first_completed_at": _iso_or_empty(row.get("first_completed_at")),
            }
            for row in row_records
        ],
    }


def summarize_outcome_realization(*, window_days: int = 90) -> dict[str, Any]:
    decision_rows = build_learning_dataset_frame(_load_decision_outcome_rows(), window_days=window_days)
    path_summary = summarize_path_realization(window_days=window_days)
    path_rows = pd.DataFrame(path_summary.get("rows", []))
    row_records: list[dict[str, Any]] = []
    if decision_rows.empty:
        return {
            "window_days": int(window_days),
            "total_decisions": 0,
            "action_execution_rate": 0.0,
            "action_completion_rate": 0.0,
            "blocked_action_rate": 0.0,
            "path_realization_rate": 0.0,
            "realized_movement_rate": 0.0,
            "threshold_reach_realization_rate": 0.0,
            "approval_realization_rate": 0.0,
            "negative_outcome_rate": 0.0,
            "observation_coverage_rate": 0.0,
            "time_to_first_execution_days": None,
            "time_to_first_completed_action_days": None,
            "time_to_realized_outcome_days": None,
            "outcome_realization_label_distribution": {key: 0.0 for key in OUTCOME_REALIZATION_LABELS},
            "rows": row_records,
        }

    for _, decision in decision_rows.iterrows():
        decision_id = _clean_str(decision.get("decision_id"))
        path_row = (
            path_rows[path_rows["decision_id"].eq(decision_id)].iloc[0].to_dict()
            if not path_rows.empty and path_rows["decision_id"].eq(decision_id).any()
            else {}
        )
        decision_status = _clean_str(decision.get("decision_status")).upper()
        approved = bool(decision.get("approved"))
        default_90d = decision.get("observed_default_90d")
        payment_ratio = _safe_float(decision.get("observed_payment_ratio_90d"))
        margin_90d = _safe_float(decision.get("observed_margin_90d"))
        recovery_90d = _safe_float(decision.get("observed_recovery_amount_90d"))
        path_status = _clean_str(path_row.get("path_realization_status"))

        has_outcome_observation = bool(
            decision_status in {"APPROVED", "CONDITIONAL"}
            or approved
            or pd.notna(default_90d)
            or payment_ratio is not None
            or margin_90d is not None
            or recovery_90d is not None
            or path_status != "pending_observation"
        )

        if approved or decision_status == "APPROVED":
            label = "approval_realized"
        elif decision_status == "CONDITIONAL":
            label = "threshold_reached"
        elif (pd.notna(default_90d) and float(default_90d) >= 1.0) or (payment_ratio is not None and payment_ratio < 0.5):
            label = "negative_outcome"
        elif path_status == "realized" and (
            (pd.notna(default_90d) and float(default_90d) == 0.0)
            or (margin_90d is not None and margin_90d > 0.0)
            or (payment_ratio is not None and payment_ratio >= 1.0)
            or (recovery_90d is not None and recovery_90d > 0.0)
        ):
            label = "partial_progress"
        elif has_outcome_observation:
            label = "no_observed_progress"
        else:
            label = "pending_observation"

        row_records.append(
            {
                "decision_id": decision_id,
                "customer_id": _clean_str(decision.get("customer_id")),
                "selected_plan_id": _clean_str(decision.get("selected_plan_id")),
                "selected_path_id": _clean_str(decision.get("selected_path_id")),
                "selected_path_type": _clean_str(decision.get("selected_path_type")),
                "selected_path_movement_strength": _clean_str(decision.get("selected_path_movement_strength")),
                "recourse_mode": _clean_str(decision.get("recourse_mode")),
                "recoverable_flag": _to_bool(decision.get("recoverable_flag")),
                "evaluation_population": _realization_population_key(
                    decision.get("recoverable_flag"),
                    decision.get("recourse_mode"),
                ),
                "movement_score": _safe_float(decision.get("movement_score")),
                "threshold_reach_probability": _safe_float(decision.get("threshold_reach_probability")),
                "plan_execution_probability": _safe_float(decision.get("plan_execution_probability")),
                "combined_plan_realization_probability": _safe_float(
                    decision.get("combined_plan_realization_probability")
                ),
                "path_realization_status": path_status or "pending_observation",
                "outcome_realization_label": label,
                "observation_coverage_flag": int(bool(path_row.get("observation_coverage_flag")) or has_outcome_observation),
                "time_to_first_execution_days": None,
                "time_to_first_completed_action_days": None,
                "time_to_realized_outcome_days": None,
            }
        )

    rows_df = pd.DataFrame(row_records)
    labels = rows_df["outcome_realization_label"] if not rows_df.empty else pd.Series(dtype=object)
    return {
        "window_days": int(window_days),
        "total_decisions": int(rows_df.shape[0]),
        "action_execution_rate": _round_metric(rows_df["path_realization_status"].isin(["attempted", "blocked", "realized"]).mean()),
        "action_completion_rate": _round_metric((rows_df["path_realization_status"] == "realized").mean()),
        "blocked_action_rate": _round_metric((rows_df["path_realization_status"] == "blocked").mean()),
        "path_realization_rate": _round_metric((rows_df["path_realization_status"] == "realized").mean()),
        "realized_movement_rate": _round_metric(
            rows_df["outcome_realization_label"].isin(["partial_progress", "threshold_reached", "approval_realized"]).mean()
        ),
        "threshold_reach_realization_rate": _round_metric(
            rows_df["outcome_realization_label"].isin(["threshold_reached", "approval_realized"]).mean()
        ),
        "approval_realization_rate": _round_metric((rows_df["outcome_realization_label"] == "approval_realized").mean()),
        "negative_outcome_rate": _round_metric((rows_df["outcome_realization_label"] == "negative_outcome").mean()),
        "observation_coverage_rate": _round_metric(rows_df["observation_coverage_flag"].mean()),
        "time_to_first_execution_days": None,
        "time_to_first_completed_action_days": None,
        "time_to_realized_outcome_days": None,
        "outcome_realization_label_distribution": _distribution(labels, OUTCOME_REALIZATION_LABELS),
        "rows": row_records,
    }


def summarize_realization_evaluation(*, window_days: int = 90) -> dict[str, Any]:
    outcome_summary = summarize_outcome_realization(window_days=window_days)
    rows_df = pd.DataFrame(outcome_summary.get("rows", []))
    if rows_df.empty:
        empty_group = _summarize_realization_group(pd.DataFrame(), group_key="all_decisions", group_label="All Decisions")
        return {
            "window_days": int(window_days),
            "total_decisions": 0,
            "overall": empty_group,
            "recoverable_vs_limited_summary": [],
            "selected_path_type_summary": [],
            "selected_path_movement_strength_summary": [],
            "predicted_vs_observed": {
                "overall": {
                    "mean_plan_execution_probability": None,
                    "observed_action_execution_rate": 0.0,
                    "plan_execution_gap": None,
                    "mean_combined_plan_realization_probability": None,
                    "observed_realized_movement_rate": 0.0,
                    "combined_realization_gap": None,
                    "mean_threshold_reach_probability": None,
                    "observed_threshold_reach_realization_rate": 0.0,
                    "threshold_reach_gap": None,
                },
                "by_population": [],
            },
            "recoverable_vs_limited_comparison": {
                "recoverable_full_mode_present": False,
                "non_recoverable_limited_mode_present": False,
            },
        }

    rows_df = rows_df.copy(deep=True)
    for column in [
        "selected_path_type",
        "selected_path_movement_strength",
        "evaluation_population",
        "path_realization_status",
        "outcome_realization_label",
    ]:
        rows_df[column] = rows_df[column].map(_clean_str)
    rows_df["selected_path_type"] = rows_df["selected_path_type"].replace("", "unknown")
    rows_df["selected_path_movement_strength"] = rows_df["selected_path_movement_strength"].replace("", "unknown")
    rows_df["observation_coverage_flag"] = pd.to_numeric(rows_df["observation_coverage_flag"], errors="coerce").fillna(0).astype(int)

    overall = _summarize_realization_group(rows_df, group_key="all_decisions", group_label="All Decisions")

    population_order = [
        "recoverable_full_mode",
        "non_recoverable_limited_mode",
        "full_mode_other",
        "limited_mode_other",
        "uncategorized",
    ]
    population_summaries: list[dict[str, Any]] = []
    for population_key in population_order:
        group_df = rows_df[rows_df["evaluation_population"] == population_key]
        if group_df.empty:
            continue
        population_summaries.append(
            _summarize_realization_group(
                group_df,
                group_key=population_key,
                group_label=_realization_population_label(population_key),
            )
        )

    path_type_summaries: list[dict[str, Any]] = []
    for path_type in sorted(rows_df["selected_path_type"].dropna().unique().tolist()):
        group_df = rows_df[rows_df["selected_path_type"] == path_type]
        path_type_summaries.append(
            _summarize_realization_group(
                group_df,
                group_key=path_type,
                group_label=path_type.replace("_", " ").title(),
            )
        )

    movement_strength_order = ["strong", "moderate", "weak", "unknown"]
    movement_strength_summaries: list[dict[str, Any]] = []
    for movement_strength in movement_strength_order:
        group_df = rows_df[rows_df["selected_path_movement_strength"] == movement_strength]
        if group_df.empty:
            continue
        movement_strength_summaries.append(
            _summarize_realization_group(
                group_df,
                group_key=movement_strength,
                group_label=movement_strength.replace("_", " ").title(),
            )
        )

    predicted_vs_observed_overall = {
        "mean_plan_execution_probability": overall["mean_plan_execution_probability"],
        "observed_action_execution_rate": overall["action_execution_rate"],
        "plan_execution_gap": overall["plan_execution_gap"],
        "mean_combined_plan_realization_probability": overall["mean_combined_plan_realization_probability"],
        "observed_realized_movement_rate": overall["realized_movement_rate"],
        "combined_realization_gap": overall["combined_realization_gap"],
        "mean_threshold_reach_probability": overall["mean_threshold_reach_probability"],
        "observed_threshold_reach_realization_rate": overall["threshold_reach_realization_rate"],
        "threshold_reach_gap": overall["threshold_reach_gap"],
    }
    predicted_vs_observed_by_population = [
        {
            "group_key": summary["group_key"],
            "group_label": summary["group_label"],
            "total_decisions": summary["total_decisions"],
            "observation_coverage_rate": summary["observation_coverage_rate"],
            "evidence_status": summary["evidence_status"],
            "mean_plan_execution_probability": summary["mean_plan_execution_probability"],
            "observed_action_execution_rate": summary["action_execution_rate"],
            "plan_execution_gap": summary["plan_execution_gap"],
            "mean_combined_plan_realization_probability": summary["mean_combined_plan_realization_probability"],
            "observed_realized_movement_rate": summary["realized_movement_rate"],
            "combined_realization_gap": summary["combined_realization_gap"],
            "mean_threshold_reach_probability": summary["mean_threshold_reach_probability"],
            "observed_threshold_reach_realization_rate": summary["threshold_reach_realization_rate"],
            "threshold_reach_gap": summary["threshold_reach_gap"],
        }
        for summary in population_summaries
    ]

    comparison_lookup = {summary["group_key"]: summary for summary in population_summaries}
    recoverable_full = comparison_lookup.get("recoverable_full_mode")
    limited_control = comparison_lookup.get("non_recoverable_limited_mode")
    comparison_summary: dict[str, Any] = {
        "recoverable_full_mode_present": recoverable_full is not None,
        "non_recoverable_limited_mode_present": limited_control is not None,
    }
    if recoverable_full is not None and limited_control is not None:
        comparison_summary.update(
            {
                "realized_movement_rate_delta": _round_metric(
                    recoverable_full["realized_movement_rate"] - limited_control["realized_movement_rate"]
                ),
                "threshold_reach_realization_rate_delta": _round_metric(
                    recoverable_full["threshold_reach_realization_rate"]
                    - limited_control["threshold_reach_realization_rate"]
                ),
                "approval_realization_rate_delta": _round_metric(
                    recoverable_full["approval_realization_rate"] - limited_control["approval_realization_rate"]
                ),
                "observation_coverage_rate_delta": _round_metric(
                    recoverable_full["observation_coverage_rate"] - limited_control["observation_coverage_rate"]
                ),
                "plan_execution_gap_delta": (
                    _round_metric(recoverable_full["plan_execution_gap"] - limited_control["plan_execution_gap"])
                    if recoverable_full["plan_execution_gap"] is not None
                    and limited_control["plan_execution_gap"] is not None
                    else None
                ),
                "combined_realization_gap_delta": (
                    _round_metric(
                        recoverable_full["combined_realization_gap"] - limited_control["combined_realization_gap"]
                    )
                    if recoverable_full["combined_realization_gap"] is not None
                    and limited_control["combined_realization_gap"] is not None
                    else None
                ),
            }
        )

    return {
        "window_days": int(window_days),
        "total_decisions": int(rows_df.shape[0]),
        "overall": overall,
        "recoverable_vs_limited_summary": population_summaries,
        "selected_path_type_summary": path_type_summaries,
        "selected_path_movement_strength_summary": movement_strength_summaries,
        "predicted_vs_observed": {
            "overall": predicted_vs_observed_overall,
            "by_population": predicted_vs_observed_by_population,
        },
        "recoverable_vs_limited_comparison": comparison_summary,
    }


def summarize_decision_logging() -> dict[str, Any]:
    return build_decision_logging_summary(_load_decision_outcome_rows())


def load_decision_learning_dataset(*, window_days: int = 90) -> pd.DataFrame:
    return build_learning_dataset_frame(_load_decision_outcome_rows(), window_days=window_days)


def summarize_outcome_ingestion(*, window_days: int = 90) -> dict[str, Any]:
    return build_outcome_ingestion_summary(_load_decision_outcome_rows(), window_days=window_days)


def summarize_decision_outcomes(*, window_days: int = 90) -> pd.DataFrame:
    _ = int(window_days)
    with get_session() as session:
        rows = session.query(DecisionOutcomeORM).all()
    if not rows:
        return pd.DataFrame(
            columns=[
                "policy_arm",
                "decision_count",
                "approval_rate",
                "default_rate_90d",
                "avg_margin_90d",
            ]
        )
    df = pd.DataFrame(
        [
            {
                "policy_arm": str(r.policy_arm),
                "approved": int(bool(r.approved)),
                "observed_default_90d": float(r.observed_default_90d) if r.observed_default_90d is not None else None,
                "observed_margin_90d": float(r.observed_margin_90d) if r.observed_margin_90d is not None else None,
            }
            for r in rows
        ]
    )
    g = (
        df.groupby("policy_arm", dropna=False)
        .agg(
            decision_count=("approved", "size"),
            approval_rate=("approved", "mean"),
            default_rate_90d=("observed_default_90d", "mean"),
            avg_margin_90d=("observed_margin_90d", "mean"),
        )
        .reset_index()
    )
    return g


def _proxy_delta_label(delta: float, *, higher_is_better: bool) -> str:
    if abs(float(delta)) <= 1e-12:
        return "no_material_change"
    if higher_is_better:
        return "helped" if float(delta) > 0.0 else "harmed"
    return "helped" if float(delta) < 0.0 else "harmed"


def _proxy_overall_assessment(labels: list[str]) -> str:
    helped = any(label == "helped" for label in labels)
    harmed = any(label == "harmed" for label in labels)
    if helped and harmed:
        return "mixed"
    if helped:
        return "helped"
    if harmed:
        return "harmed"
    return "no_material_change"


def _policy_arm_profile(policy_arm: str) -> dict[str, str]:
    arm = str(policy_arm or "").strip()
    normalized = arm.lower()
    if not arm:
        return {
            "offer_family": "",
            "scoring_profile": "",
            "term_generation_rule": "",
        }
    if normalized == "control":
        return {
            "offer_family": "control",
            "scoring_profile": "control",
            "term_generation_rule": "",
        }
    if normalized == "treatment":
        return {
            "offer_family": "generic_treatment",
            "scoring_profile": "treatment",
            "term_generation_rule": "",
        }

    offer_family = "generic_offer"
    scoring_profile = arm
    term_generation_rule = ""

    if "discount" in normalized or "settlement" in normalized:
        offer_family = "hardship_relief"
        scoring_profile = "discount_offer_v1"
        term_generation_rule = "discount_offer_terms_v1"
    elif "installment" in normalized:
        offer_family = "payment_relief"
        scoring_profile = "installment_terms_v1"
        term_generation_rule = "installment_terms_v1"
    elif "limit" in normalized or "credit_limit" in normalized:
        offer_family = "limit_management"
        scoring_profile = "credit_limit_adjustment_v1"
        term_generation_rule = "credit_limit_adjustment_terms_v1"

    if "_policy_" in normalized and not term_generation_rule:
        term_generation_rule = arm.replace("_policy_", "_terms_")

    return {
        "offer_family": offer_family,
        "scoring_profile": scoring_profile,
        "term_generation_rule": term_generation_rule,
    }


def compute_policy_outcome_deltas(*, window_days: int = 90) -> dict[str, Any]:
    summary = summarize_decision_outcomes(window_days=window_days)
    if summary.empty:
        return {
            "window_days": int(window_days),
            "comparison_status": "no_data",
            "outcome_feedback_confidence": "tentative",
            "has_control": False,
            "has_treatment": False,
            "baseline_arm": "control",
            "canonical_proxy_metrics": ["approval_rate", "default_rate_90d", "avg_margin_90d"],
            "policy_arm_summaries": [],
            "comparisons": [],
            "best_proxy_improving_arm": {},
            "worst_proxy_regressing_arm": {},
            "approval_rate_delta": 0.0,
            "default_rate_90d_delta": 0.0,
            "avg_margin_90d_delta": 0.0,
        }
    policy_arm_summaries = [
        {
            "policy_arm": str(row["policy_arm"]),
            "policy_arm_profile": _policy_arm_profile(str(row["policy_arm"])),
            "decision_count": int(row["decision_count"]),
            "approval_rate": float(row["approval_rate"]),
            "default_rate_90d": float(row["default_rate_90d"]),
            "avg_margin_90d": float(row["avg_margin_90d"]),
        }
        for _, row in summary.iterrows()
    ]
    by_arm = {str(row["policy_arm"]): row for _, row in summary.iterrows()}
    control = by_arm.get("control")
    treatment = by_arm.get("treatment")
    if control is None:
        return {
            "window_days": int(window_days),
            "comparison_status": "baseline_missing",
            "outcome_feedback_confidence": "tentative",
            "has_control": False,
            "has_treatment": treatment is not None,
            "baseline_arm": "control",
            "canonical_proxy_metrics": ["approval_rate", "default_rate_90d", "avg_margin_90d"],
            "policy_arm_summaries": policy_arm_summaries,
            "comparisons": [],
            "best_proxy_improving_arm": {},
            "worst_proxy_regressing_arm": {},
            "approval_rate_delta": 0.0,
            "default_rate_90d_delta": 0.0,
            "avg_margin_90d_delta": 0.0,
        }
    comparisons: list[dict[str, Any]] = []
    for arm_name, arm_row in by_arm.items():
        if arm_name == "control":
            continue
        approval_delta = float(arm_row["approval_rate"] - control["approval_rate"])
        default_delta = float(arm_row["default_rate_90d"] - control["default_rate_90d"])
        margin_delta = float(arm_row["avg_margin_90d"] - control["avg_margin_90d"])
        proxy_labels = {
            "approval_rate": _proxy_delta_label(approval_delta, higher_is_better=True),
            "default_rate_90d": _proxy_delta_label(default_delta, higher_is_better=False),
            "avg_margin_90d": _proxy_delta_label(margin_delta, higher_is_better=True),
        }
        comparisons.append(
            {
                "policy_arm": str(arm_name),
                "policy_arm_profile": _policy_arm_profile(str(arm_name)),
                "baseline_arm": "control",
                "approval_rate_delta": approval_delta,
                "default_rate_90d_delta": default_delta,
                "avg_margin_90d_delta": margin_delta,
                "proxy_labels": proxy_labels,
                "overall_proxy_assessment": _proxy_overall_assessment(list(proxy_labels.values())),
                "_proxy_score": int(sum(1 if value == "helped" else -1 if value == "harmed" else 0 for value in proxy_labels.values())),
            }
        )

    def _comparison_rank(payload: dict[str, Any]) -> tuple[float, float, float, float, str]:
        return (
            float(payload.get("_proxy_score", 0)),
            float(payload.get("approval_rate_delta", 0.0)),
            float(-payload.get("default_rate_90d_delta", 0.0)),
            float(payload.get("avg_margin_90d_delta", 0.0)),
            str(payload.get("policy_arm", "")),
        )

    best_proxy_improving_arm = {}
    worst_proxy_regressing_arm = {}
    if comparisons:
        best_proxy_improving_arm = {
            key: value
            for key, value in max(comparisons, key=_comparison_rank).items()
            if not str(key).startswith("_")
        }
        worst_proxy_regressing_arm = {
            key: value
            for key, value in min(comparisons, key=_comparison_rank).items()
            if not str(key).startswith("_")
        }

    treatment_approval_delta = 0.0
    treatment_default_delta = 0.0
    treatment_margin_delta = 0.0
    if treatment is not None:
        treatment_approval_delta = float(treatment["approval_rate"] - control["approval_rate"])
        treatment_default_delta = float(treatment["default_rate_90d"] - control["default_rate_90d"])
        treatment_margin_delta = float(treatment["avg_margin_90d"] - control["avg_margin_90d"])

    return {
        "window_days": int(window_days),
        "has_control": True,
        "has_treatment": treatment is not None,
        "comparison_status": "treatment_vs_control" if treatment is not None else "control_comparison",
        "outcome_feedback_confidence": "strong" if comparisons else "tentative",
        "baseline_arm": "control",
        "canonical_proxy_metrics": ["approval_rate", "default_rate_90d", "avg_margin_90d"],
        "policy_arm_summaries": policy_arm_summaries,
        "comparisons": [
            {
                key: value
                for key, value in comparison.items()
                if not str(key).startswith("_")
            }
            for comparison in comparisons
        ],
        "best_proxy_improving_arm": best_proxy_improving_arm,
        "worst_proxy_regressing_arm": worst_proxy_regressing_arm,
        "approval_rate_delta": treatment_approval_delta,
        "default_rate_90d_delta": treatment_default_delta,
        "avg_margin_90d_delta": treatment_margin_delta,
    }


# ------------------------------------------------------------------ #
# MacroSnapshot
# ------------------------------------------------------------------ #
def save_macro_snapshot(snap: MacroSnapshot) -> int:
    orm = MacroSnapshotORM(
        snapshot_date=snap.snapshot_date,
        interest_rate=snap.interest_rate,
        unemployment_rate=snap.unemployment_rate,
        gdp_growth=snap.gdp_growth,
        inflation_rate=snap.inflation_rate,
        credit_spread=snap.credit_spread,
        macro_stress_index=snap.macro_stress_index,
        source=snap.source,
    )
    with get_session() as session:
        session.add(orm)
        session.flush()
        record_id = int(orm.id)
        _append_audit_event(
            session=session,
            event_type="macro_snapshot_saved",
            payload={
                "snapshot_date": snap.snapshot_date.isoformat(),
                "macro_stress_index": snap.macro_stress_index,
                "source": snap.source,
            },
        )
        session.commit()
    logger.debug("Saved MacroSnapshot id=%d date=%s", record_id, snap.snapshot_date)
    return record_id


# ------------------------------------------------------------------ #
# AuditEvent
# ------------------------------------------------------------------ #
def save_audit_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    entity_id: str | None = None,
    run_id: str | None = None,
) -> int:
    with get_session() as session:
        event_id = _append_audit_event(
            session=session,
            event_type=event_type,
            payload=payload,
            entity_id=entity_id,
            run_id=run_id,
        )
        session.commit()
    return event_id


def get_audit_events(limit: int | None = None) -> list[dict]:
    with get_session() as session:
        query = session.query(AuditEventORM).order_by(AuditEventORM.id.asc())
        if limit is not None and limit > 0:
            rows = query.limit(limit).all()
        else:
            rows = query.all()

    return [
        {
            "id": row.id,
            "event_type": row.event_type,
            "entity_id": row.entity_id,
            "run_id": row.run_id,
            "payload": row.payload,
            "prev_hash": row.prev_hash,
            "event_hash": row.event_hash,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


def verify_audit_chain() -> tuple[bool, list[dict[str, Any]]]:
    with get_session() as session:
        rows = session.query(AuditEventORM).order_by(AuditEventORM.id.asc()).all()

    issues: list[dict[str, Any]] = []
    expected_prev_hash: str | None = None

    for row in rows:
        payload = row.payload if isinstance(row.payload, dict) else {}
        envelope = _build_audit_envelope(
            event_type=row.event_type,
            entity_id=row.entity_id,
            run_id=row.run_id,
            payload=payload,
        )

        if row.prev_hash != expected_prev_hash:
            issues.append(
                {
                    "id": row.id,
                    "error": "prev_hash_mismatch",
                    "expected_prev_hash": expected_prev_hash,
                    "actual_prev_hash": row.prev_hash,
                }
            )

        recomputed_hash = hash_chain_event(payload=envelope, prev_hash=expected_prev_hash)
        if row.event_hash != recomputed_hash:
            issues.append(
                {
                    "id": row.id,
                    "error": "event_hash_mismatch",
                    "expected_event_hash": recomputed_hash,
                    "actual_event_hash": row.event_hash,
                }
            )

        expected_prev_hash = row.event_hash

    return len(issues) == 0, issues
