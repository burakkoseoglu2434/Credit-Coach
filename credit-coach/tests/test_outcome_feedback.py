from __future__ import annotations

from credit_coach.data.schema import DecisionOutcomeRecord
from credit_coach.storage import db as db_module
from credit_coach.storage.db import init_db
from credit_coach.storage.repository import (
    load_decision_learning_dataset,
    compute_policy_outcome_deltas,
    save_decision_outcome,
    summarize_decision_logging,
    summarize_decision_outcomes,
    summarize_outcome_ingestion,
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


def test_decision_logging_and_learning_readiness_summaries(monkeypatch, tmp_path):
    _init_test_db(monkeypatch, tmp_path)
    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="d1",
            run_id="r16",
            customer_id="c1",
            policy_arm="control",
            policy_arm_profile={
                "offer_family": "control",
                "scoring_profile": "control",
                "term_generation_rule": "",
            },
            candidate_set_id="r16:c1",
            selected_plan_id="plan-1",
            selected_plan_status="APPROVED",
            selected_offer_type="installment_terms",
            selection_propensity=1.0,
            propensity_source="deterministic_fallback",
            reason_codes=["selected_best_plan"],
            recommended_plan_flag=True,
            selected_plan_policy_label="stabilize_first",
            trajectory_status="on_track",
            approved=True,
            predicted_pd=0.21,
            plan_execution_probability=0.72,
            offer_acceptance_probability=0.48,
            combined_plan_realization_probability=0.3456,
            action_completed=True,
            offer_accepted=True,
            observed_payment_ratio_90d=0.92,
            observed_recovery_amount_90d=140.0,
            observed_default_90d=0,
            observed_margin_90d=95.0,
        )
    )
    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="d2",
            run_id="r16",
            customer_id="c2",
            policy_arm="treatment",
            candidate_set_id="",
            selected_plan_id="",
            selected_plan_status="",
            selection_propensity=1.0,
            propensity_source="deterministic_fallback",
            reason_codes=[],
            recommended_plan_flag=False,
            approved=False,
            observed_default_90d=None,
            observed_margin_90d=None,
        )
    )

    decision_logging = summarize_decision_logging()
    ingestion = summarize_outcome_ingestion(window_days=90)
    learning_df = load_decision_learning_dataset(window_days=90)

    assert decision_logging["total_decisions"] == 2
    assert decision_logging["complete_decision_logs"] == 1
    assert decision_logging["decision_log_completeness"] == 0.5
    assert ingestion["reward_90d_coverage"] == 0.5
    assert ingestion["learning_readiness_status_distribution"]["learning_ready"]["count"] == 1
    assert ingestion["learning_readiness_status_distribution"]["partial_learning_ready"]["count"] == 0
    assert ingestion["learning_readiness_status_distribution"]["descriptive_only"]["count"] == 1
    assert set(learning_df["learning_readiness_status"]) == {"learning_ready", "descriptive_only"}


def test_decision_learning_dataset_preserves_selected_path_realization_context(monkeypatch, tmp_path):
    _init_test_db(monkeypatch, tmp_path)
    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="d-realize-1",
            run_id="r67",
            customer_id="c67",
            policy_arm="treatment",
            candidate_set_id="r67:c67",
            selected_plan_id="plan-67",
            selected_plan_status="APPROVED",
            selected_path_id="path-67",
            selected_path_type="hybrid",
            selected_path_movement_strength="strong",
            recourse_mode="full",
            recoverable_flag=True,
            movement_score=0.84,
            threshold_reach_probability=0.63,
            selection_propensity=1.0,
            propensity_source="deterministic_fallback",
            reason_codes=["selected_best_plan"],
            recommended_plan_flag=True,
            approved=False,
            observed_default_90d=0,
            observed_margin_90d=42.0,
        )
    )

    learning_df = load_decision_learning_dataset(window_days=90)
    row = learning_df.iloc[0].to_dict()

    assert row["selected_path_id"] == "path-67"
    assert row["selected_path_type"] == "hybrid"
    assert row["selected_path_movement_strength"] == "strong"
    assert row["recourse_mode"] == "full"
    assert row["recoverable_flag"] is True
    assert row["movement_score"] == 0.84
    assert row["threshold_reach_probability"] == 0.63
