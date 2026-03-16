from __future__ import annotations

from credit_coach.data.schema import DecisionOutcomeRecord
from credit_coach.storage import db as db_module
from credit_coach.storage.db import init_db
from credit_coach.storage.repository import (
    compute_policy_outcome_deltas,
    save_decision_outcome,
    summarize_decision_outcomes,
)


def _init_test_db(monkeypatch, tmp_path) -> None:
    db_file = tmp_path / "outcome_feedback.db"
    db_url = f"sqlite:///{db_file}"
    monkeypatch.setenv("DB_URL", db_url)
    db_module._engine = None
    db_module._SessionFactory = None
    init_db(db_url=db_url)


def test_outcome_feedback_summary_and_deltas(monkeypatch, tmp_path):
    _init_test_db(monkeypatch, tmp_path)
    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="d1",
            run_id="r1",
            customer_id="c1",
            policy_arm="control",
            approved=True,
            observed_default_90d=1,
            observed_margin_90d=-50.0,
        )
    )
    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="d2",
            run_id="r1",
            customer_id="c2",
            policy_arm="treatment",
            approved=True,
            observed_default_90d=0,
            observed_margin_90d=120.0,
        )
    )
    summary = summarize_decision_outcomes(window_days=90)
    assert len(summary) == 2
    deltas = compute_policy_outcome_deltas(window_days=90)
    assert deltas["has_control"] is True
    assert deltas["has_treatment"] is True
    assert deltas["comparison_status"] == "treatment_vs_control"
    assert deltas["outcome_feedback_confidence"] == "strong"
    assert deltas["default_rate_90d_delta"] < 0.0
    assert deltas["best_proxy_improving_arm"]["policy_arm"] == "treatment"
    assert deltas["policy_arm_summaries"][0]["policy_arm_profile"]
    assert "policy_arm_profile" in deltas["comparisons"][0]
    assert deltas["comparisons"][0]["proxy_labels"]["approval_rate"] == "no_material_change"


def test_outcome_feedback_supports_multi_arm_control_comparisons(monkeypatch, tmp_path):
    _init_test_db(monkeypatch, tmp_path)
    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="d1",
            run_id="r1",
            customer_id="c1",
            policy_arm="control",
            approved=True,
            observed_default_90d=1,
            observed_margin_90d=10.0,
        )
    )
    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="d2",
            run_id="r1",
            customer_id="c2",
            policy_arm="treatment",
            approved=True,
            observed_default_90d=0,
            observed_margin_90d=100.0,
        )
    )
    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="d3",
            run_id="r1",
            customer_id="c3",
            policy_arm="pilot_b",
            approved=False,
            observed_default_90d=1,
            observed_margin_90d=-30.0,
        )
    )

    deltas = compute_policy_outcome_deltas(window_days=90)

    assert deltas["comparison_status"] == "treatment_vs_control"
    assert len(deltas["comparisons"]) == 2
    assert deltas["best_proxy_improving_arm"]["policy_arm"] == "treatment"
    assert deltas["worst_proxy_regressing_arm"]["policy_arm"] == "pilot_b"
    assert deltas["best_proxy_improving_arm"]["policy_arm_profile"]["offer_family"] == "generic_treatment"


def test_outcome_feedback_falls_back_to_baseline_missing_without_control(monkeypatch, tmp_path):
    _init_test_db(monkeypatch, tmp_path)
    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="d1",
            run_id="r1",
            customer_id="c1",
            policy_arm="treatment",
            approved=True,
            observed_default_90d=0,
            observed_margin_90d=50.0,
        )
    )

    deltas = compute_policy_outcome_deltas(window_days=90)

    assert deltas["comparison_status"] == "baseline_missing"
    assert deltas["outcome_feedback_confidence"] == "tentative"
    assert deltas["comparisons"] == []
    assert deltas["policy_arm_summaries"][0]["policy_arm"] == "treatment"
