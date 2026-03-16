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
    DecisionOutcomeORM,
    MacroSnapshotORM,
    ModelRunORM,
    PlanRecordORM,
)
from credit_coach.utils.hashing import hash_chain_event

logger = logging.getLogger(__name__)


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
                "action": action,
            },
        )
        session.commit()
    return record_id


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
