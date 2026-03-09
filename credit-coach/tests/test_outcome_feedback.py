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
    assert deltas["default_rate_90d_delta"] < 0.0
