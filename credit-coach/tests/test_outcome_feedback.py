from __future__ import annotations

import pandas as pd

from credit_coach.cli.run_outcome_feedback import _ingest_action_events_csv, main as run_outcome_feedback_main
from credit_coach.data.schema import DecisionActionExecutionEventRecord
from credit_coach.data.schema import DecisionOutcomeRecord
from credit_coach.storage import db as db_module
from credit_coach.storage.db import init_db
from credit_coach.storage.repository import (
    compute_policy_outcome_deltas,
    load_decision_action_execution_events,
    load_decision_learning_dataset,
    save_decision_action_execution_event,
    save_decision_outcome,
    summarize_action_execution,
    summarize_decision_logging,
    summarize_outcome_realization,
    summarize_decision_outcomes,
    summarize_outcome_ingestion,
    summarize_path_realization,
    summarize_realization_evaluation,
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


def test_decision_action_execution_events_append_and_filter(monkeypatch, tmp_path):
    _init_test_db(monkeypatch, tmp_path)
    save_decision_action_execution_event(
        DecisionActionExecutionEventRecord(
            decision_id="d-evt-1",
            customer_id="c-evt",
            selected_plan_id="plan-evt",
            selected_path_id="path-evt",
            action_key="call_servicer",
            event_type="attempted",
            event_at=pd.Timestamp("2026-04-10T08:00:00Z").to_pydatetime(),
            event_source="manual_review",
            evidence_reference="ticket-1",
        )
    )
    save_decision_action_execution_event(
        DecisionActionExecutionEventRecord(
            decision_id="d-evt-1",
            customer_id="c-evt",
            selected_plan_id="plan-evt",
            selected_path_id="path-evt",
            action_key="call_servicer",
            event_type="completed",
            event_at=pd.Timestamp("2026-04-12T08:00:00Z").to_pydatetime(),
            event_source="batch_refresh",
            evidence_reference="ticket-2",
        )
    )
    save_decision_action_execution_event(
        DecisionActionExecutionEventRecord(
            decision_id="d-evt-2",
            customer_id="c-evt-2",
            selected_plan_id="plan-evt-2",
            selected_path_id="path-evt-2",
            action_key="reduce_balance",
            event_type="blocked",
            event_at=pd.Timestamp("2026-04-11T08:00:00Z").to_pydatetime(),
            event_source="self_report",
            evidence_reference=None,
        )
    )

    all_events = load_decision_action_execution_events()
    filtered = load_decision_action_execution_events(decision_id="d-evt-1")

    assert len(all_events) == 3
    assert filtered["event_type"].tolist() == ["attempted", "completed"]
    assert filtered["event_source"].tolist() == ["manual_review", "batch_refresh"]
    assert filtered["evidence_reference"].tolist() == ["ticket-1", "ticket-2"]


def test_ingest_action_events_csv_appends_selected_action_events(monkeypatch, tmp_path):
    _init_test_db(monkeypatch, tmp_path)
    csv_path = tmp_path / "action_events.csv"
    pd.DataFrame(
        [
            {
                "decision_id": "d-csv-1",
                "customer_id": "c-csv-1",
                "selected_plan_id": "plan-csv-1",
                "selected_path_id": "path-csv-1",
                "action_key": "call_servicer",
                "event_type": "attempted",
                "event_at": "2026-04-10T09:00:00Z",
                "event_source": "batch_refresh",
                "evidence_reference": "batch-1",
            },
            {
                "decision_id": "d-csv-1",
                "customer_id": "c-csv-1",
                "selected_plan_id": "plan-csv-1",
                "selected_path_id": "path-csv-1",
                "action_key": "call_servicer",
                "event_type": "completed",
                "event_at": "2026-04-13T09:00:00Z",
                "event_source": "manual_review",
                "evidence_reference": "review-1",
            },
        ]
    ).to_csv(csv_path, index=False)

    inserted = _ingest_action_events_csv(csv_path)
    events = load_decision_action_execution_events(decision_id="d-csv-1")

    assert inserted == 2
    assert events["event_type"].tolist() == ["attempted", "completed"]
    assert events["selected_path_id"].tolist() == ["path-csv-1", "path-csv-1"]


def test_realization_summaries_derive_deterministic_status_and_labels(monkeypatch, tmp_path):
    _init_test_db(monkeypatch, tmp_path)
    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="d-realized",
            run_id="r67",
            customer_id="c1",
            policy_arm="treatment",
            selected_plan_id="plan-1",
            selected_path_id="path-1",
            selected_path_type="customer_only",
            selected_path_movement_strength="strong",
            recourse_mode="full",
            recoverable_flag=True,
            movement_score=0.91,
            threshold_reach_probability=0.62,
            plan_execution_probability=0.85,
            combined_plan_realization_probability=0.58,
            decision_status="CONDITIONAL",
            approved=False,
            action_completed=True,
            observed_default_90d=0,
            observed_margin_90d=55.0,
        )
    )
    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="d-blocked",
            run_id="r67",
            customer_id="c2",
            policy_arm="treatment",
            selected_plan_id="plan-2",
            selected_path_id="path-2",
            selected_path_type="hybrid",
            selected_path_movement_strength="moderate",
            recourse_mode="full",
            recoverable_flag=True,
            movement_score=0.53,
            threshold_reach_probability=0.36,
            plan_execution_probability=0.7,
            combined_plan_realization_probability=0.4,
            decision_status="REJECTED",
            approved=False,
            observed_default_90d=1,
        )
    )
    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="d-pending",
            run_id="r67",
            customer_id="c3",
            policy_arm="control",
            selected_plan_id="plan-3",
            selected_path_id="path-3",
            selected_path_type="institution_assisted",
            selected_path_movement_strength="weak",
            recourse_mode="limited",
            recoverable_flag=False,
            movement_score=0.12,
            threshold_reach_probability=0.08,
            plan_execution_probability=0.15,
            combined_plan_realization_probability=0.05,
            decision_status="REJECTED",
            approved=False,
        )
    )
    save_decision_action_execution_event(
        DecisionActionExecutionEventRecord(
            decision_id="d-realized",
            customer_id="c1",
            selected_plan_id="plan-1",
            selected_path_id="path-1",
            action_key="reduce_balance",
            event_type="attempted",
            event_at=pd.Timestamp("2026-04-10T09:00:00Z").to_pydatetime(),
            event_source="batch_refresh",
            evidence_reference="evt-1",
        )
    )
    save_decision_action_execution_event(
        DecisionActionExecutionEventRecord(
            decision_id="d-realized",
            customer_id="c1",
            selected_plan_id="plan-1",
            selected_path_id="path-1",
            action_key="reduce_balance",
            event_type="completed",
            event_at=pd.Timestamp("2026-04-12T09:00:00Z").to_pydatetime(),
            event_source="manual_review",
            evidence_reference="evt-2",
        )
    )
    save_decision_action_execution_event(
        DecisionActionExecutionEventRecord(
            decision_id="d-blocked",
            customer_id="c2",
            selected_plan_id="plan-2",
            selected_path_id="path-2",
            action_key="call_servicer",
            event_type="blocked",
            event_at=pd.Timestamp("2026-04-11T09:00:00Z").to_pydatetime(),
            event_source="self_report",
            evidence_reference="evt-3",
        )
    )

    action_summary = summarize_action_execution()
    path_summary = summarize_path_realization(window_days=90)
    outcome_summary = summarize_outcome_realization(window_days=90)
    realization_evaluation = summarize_realization_evaluation(window_days=90)

    realized_action = action_summary[action_summary["decision_id"] == "d-realized"].iloc[0].to_dict()
    assert realized_action["action_status"] == "completed"
    assert realized_action["event_count"] == 2

    path_rows = {row["decision_id"]: row for row in path_summary["rows"]}
    assert path_rows["d-realized"]["path_realization_status"] == "realized"
    assert path_rows["d-blocked"]["path_realization_status"] == "blocked"
    assert path_rows["d-pending"]["path_realization_status"] == "pending_observation"
    assert path_summary["path_realization_rate"] == 0.333333
    assert path_summary["observation_coverage_rate"] == 0.666667

    outcome_rows = {row["decision_id"]: row for row in outcome_summary["rows"]}
    assert outcome_rows["d-realized"]["outcome_realization_label"] == "threshold_reached"
    assert outcome_rows["d-blocked"]["outcome_realization_label"] == "negative_outcome"
    assert outcome_rows["d-pending"]["outcome_realization_label"] == "pending_observation"
    assert outcome_summary["action_execution_rate"] == 0.666667
    assert outcome_summary["threshold_reach_realization_rate"] == 0.333333
    assert outcome_summary["negative_outcome_rate"] == 0.333333
    assert outcome_rows["d-realized"]["evaluation_population"] == "recoverable_full_mode"
    assert outcome_rows["d-pending"]["evaluation_population"] == "non_recoverable_limited_mode"

    by_population = {
        row["group_key"]: row for row in realization_evaluation["recoverable_vs_limited_summary"]
    }
    assert by_population["recoverable_full_mode"]["realized_movement_rate"] == 0.5
    assert by_population["recoverable_full_mode"]["threshold_reach_realization_rate"] == 0.5
    assert by_population["non_recoverable_limited_mode"]["realized_movement_rate"] == 0.0
    assert realization_evaluation["predicted_vs_observed"]["overall"]["combined_realization_gap"] == -0.01
    assert realization_evaluation["recoverable_vs_limited_comparison"]["realized_movement_rate_delta"] == 0.5


def test_run_outcome_feedback_writes_realization_artifacts(monkeypatch, tmp_path):
    _init_test_db(monkeypatch, tmp_path)
    save_decision_outcome(
        DecisionOutcomeRecord(
            decision_id="d-run",
            run_id="r-run",
            customer_id="c-run",
            policy_arm="treatment",
            selected_plan_id="plan-run",
            selected_path_id="path-run",
            decision_status="APPROVED",
            approved=True,
            action_completed=True,
            observed_default_90d=0,
            observed_margin_90d=75.0,
        )
    )
    save_decision_action_execution_event(
        DecisionActionExecutionEventRecord(
            decision_id="d-run",
            customer_id="c-run",
            selected_plan_id="plan-run",
            selected_path_id="path-run",
            action_key="reduce_balance",
            event_type="completed",
            event_at=pd.Timestamp("2026-04-10T09:00:00Z").to_pydatetime(),
            event_source="manual_review",
            evidence_reference="evt-run",
        )
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["run_outcome_feedback.py", "--window_days", "90"])
    run_outcome_feedback_main()

    action_execution_files = list(tmp_path.rglob("action_execution_summary.csv"))
    path_realization_files = list(tmp_path.rglob("path_realization_summary.json"))
    outcome_realization_files = list(tmp_path.rglob("outcome_realization_summary.json"))

    assert len(action_execution_files) == 1
    assert len(path_realization_files) == 1
    assert len(outcome_realization_files) == 1

    action_execution_df = pd.read_csv(action_execution_files[0])
    path_realization_payload = pd.read_json(path_realization_files[0], typ="series")
    outcome_realization_payload = pd.read_json(outcome_realization_files[0], typ="series")

    assert action_execution_df["action_status"].tolist() == ["completed"]
    assert float(path_realization_payload["path_realization_rate"]) == 1.0
    assert float(outcome_realization_payload["approval_realization_rate"]) == 1.0
