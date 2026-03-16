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
    DecisionOutcomeRecord,
    MacroSnapshot,
    ModelRunRecord,
    PlanRecord,
)
from credit_coach.storage.db import get_session
from credit_coach.storage.models import (
    AuditEventORM,
    CustomerSnapshotORM,
    DecisionOutcomeContextORM,
    DecisionOutcomeORM,
    MacroSnapshotORM,
    ModelRunORM,
    PlanRecordORM,
)
from credit_coach.utils.hashing import hash_chain_event

logger = logging.getLogger(__name__)

CANONICAL_PROXY_METRICS = ["approval_rate", "default_rate_90d", "avg_margin_90d"]
LEARNING_READINESS_STATES = ["descriptive_only", "partial_learning_ready", "learning_ready"]


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
        "selected_offer_type": "",
        "selection_propensity": None,
        "propensity_source": "",
        "reason_codes": None,
        "recommended_plan_flag": False,
        "selected_plan_policy_label": "",
        "trajectory_status": "",
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

    for column in ["decision_id", "run_id", "customer_id", "policy_arm", "candidate_set_id", "selected_plan_id", "selected_plan_status", "selected_offer_type", "propensity_source", "selected_plan_policy_label", "trajectory_status"]:
        df[column] = df[column].map(_clean_str)

    df["reason_codes_list"] = df["reason_codes"].map(_normalize_reason_codes)
    df["reason_codes_count"] = df["reason_codes_list"].map(len).astype(int)
    df["selection_propensity"] = pd.to_numeric(df["selection_propensity"], errors="coerce")
    for column in [
        "predicted_pd",
        "plan_execution_probability",
        "offer_acceptance_probability",
        "combined_plan_realization_probability",
        "observed_payment_ratio_90d",
        "observed_recovery_amount_90d",
        "observed_margin_90d",
    ]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in ["observed_default_30d", "observed_default_60d", "observed_default_90d"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in ["recommended_plan_flag", "approved", "action_completed", "offer_accepted"]:
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

    context_by_decision_id = {str(row.decision_id): row for row in context_rows}
    rows: list[dict[str, Any]] = []
    for row in outcome_rows:
        context = context_by_decision_id.get(str(row.decision_id))
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
                "selected_offer_type": _clean_str(getattr(context, "selected_offer_type", "")),
                "selection_propensity": _safe_float(getattr(context, "selection_propensity", None)),
                "propensity_source": _clean_str(getattr(context, "propensity_source", "")),
                "reason_codes": list(getattr(context, "reason_codes", [])) if context is not None else [],
                "recommended_plan_flag": bool(getattr(context, "recommended_plan_flag", False)) if context is not None else False,
                "selected_plan_policy_label": _clean_str(getattr(context, "selected_plan_policy_label", "")),
                "trajectory_status": _clean_str(getattr(context, "trajectory_status", "")),
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
                "action": action,
            },
        )
        session.commit()
    return record_id


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
