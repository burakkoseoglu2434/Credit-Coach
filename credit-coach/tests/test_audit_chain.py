from __future__ import annotations

from credit_coach.data.schema import DecisionOutcomeRecord, ModelRunRecord, PlanAction, PlanRecord
from credit_coach.storage import db as db_module
from credit_coach.storage.db import get_session, init_db
from credit_coach.storage.models import AuditEventORM
from credit_coach.storage.repository import (
    get_audit_events,
    save_decision_outcome,
    save_model_run,
    save_plan,
    verify_audit_chain,
)


def _init_test_db(monkeypatch, tmp_path) -> None:
    db_file = tmp_path / "audit_chain.db"
    db_url = f"sqlite:///{db_file}"
    monkeypatch.setenv("DB_URL", db_url)
    db_module._engine = None
    db_module._SessionFactory = None
    init_db(db_url=db_url)


def test_audit_chain_passes_then_detects_tamper(monkeypatch, tmp_path):
    _init_test_db(monkeypatch, tmp_path)

    save_model_run(
        ModelRunRecord(
            run_id="run_001",
            model_version="v1",
            run_type="train",
            config_hash="cfg_hash",
            metrics={"auc": 0.91},
            tau_used=0.35,
        )
    )

    save_plan(
        PlanRecord(
            plan_id="plan_001",
            customer_id="cust_001",
            run_id="run_001",
            horizon_months=6,
            strategy="balanced",
            actions=[
                PlanAction(
                    feature_name="dti",
                    current_value=30.0,
                    target_value=25.0,
                    delta=-5.0,
                    time_months=3,
                    estimated_cost_usd=250.0,
                )
            ],
            predicted_pd=0.20,
            status="APPROVED",
        )
    )

    ok, issues = verify_audit_chain()
    assert ok is True
    assert issues == []
    events = get_audit_events()
    assert len(events) >= 2
    assert events[0]["prev_hash"] is None

    with get_session() as session:
        row = session.query(AuditEventORM).order_by(AuditEventORM.id.asc()).first()
        assert row is not None
        row.payload_json = '{"tampered": true}'
        session.commit()

    ok_after_tamper, issues_after_tamper = verify_audit_chain()
    assert ok_after_tamper is False
    assert len(issues_after_tamper) >= 1


def test_audit_chain_accepts_richer_decision_outcome_logging(monkeypatch, tmp_path):
    _init_test_db(monkeypatch, tmp_path)

    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="decision_001",
            run_id="run_001",
            customer_id="cust_001",
            policy_arm="treatment",
            policy_arm_profile={"offer_family": "installment"},
            candidate_set_id="run_001:cust_001",
            selected_plan_id="plan_001",
            selected_plan_status="APPROVED",
            selected_offer_type="installment_terms",
            selection_propensity=1.0,
            propensity_source="deterministic_fallback",
            reason_codes=["selected_best_plan"],
            recommended_plan_flag=True,
            plan_execution_probability=0.64,
            offer_acceptance_probability=0.52,
            combined_plan_realization_probability=0.3328,
            approved=True,
            observed_default_90d=0,
            observed_margin_90d=85.0,
        )
    )

    ok, issues = verify_audit_chain()
    assert ok is True
    assert issues == []
    events = get_audit_events()
    assert any(event["event_type"] == "decision_outcome_saved" for event in events)
