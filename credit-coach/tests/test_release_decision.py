from __future__ import annotations

from credit_coach.ops.kpi_contract import (
    ACCEPTED,
    PILOT_ONLY,
    build_kpi_contract_snapshot,
    build_milestone_acceptance_summary,
    render_milestone_acceptance_review,
)
from credit_coach.ops.release_decision import (
    GO,
    LIMITED_GO,
    NO_GO,
    aggregate_release_metrics,
    evaluate_fairness_seed_pass,
    evaluate_release_decision,
)


def _thresholds() -> dict[str, float]:
    return {
        "max_approval_gap_delta": 0.01,
        "max_equalized_odds_gap_delta": 0.01,
        "max_fairness_gap": 0.10,
        "max_high_stress_fairness_gap": 0.10,
        "max_recourse_success_gap": 0.10,
    }


def test_evaluate_fairness_seed_pass_uses_primary_and_guardrail_metrics() -> None:
    snapshot = evaluate_fairness_seed_pass(
        {
            "equalized_odds_gap_delta": 0.009,
            "high_stress_fairness_gap_after": 0.08,
            "recourse_success_gap": 0.07,
            "approval_gap_delta": 0.20,
            "fairness_gap_after": 0.50,
        },
        _thresholds(),
    )
    assert snapshot["fairness_seed_pass"] is True
    assert snapshot["primary_fail_reason"] == "approval_gap_delta"
    assert snapshot["primary_fairness_metric"] == "equalized_odds_gap_delta"


def test_evaluate_fairness_seed_pass_fails_when_equalized_odds_gap_exceeds_threshold() -> None:
    snapshot = evaluate_fairness_seed_pass(
        {
            "equalized_odds_gap_delta": 0.02,
            "high_stress_fairness_gap_after": 0.08,
            "recourse_success_gap": 0.07,
        },
        _thresholds(),
    )
    assert snapshot["fairness_seed_pass"] is False
    assert snapshot["primary_fail_reason"] == "equalized_odds_gap_delta"
    assert snapshot["within_limited_go_cap"] is False


def test_aggregate_release_metrics_captures_counts_and_dominant_segment() -> None:
    metrics = aggregate_release_metrics(
        [
            {
                "lift_pass": True,
                "reliability_pass": True,
                "fairness_seed_pass": True,
                "worst_fairness_gap": 0.005,
                "high_stress_fairness_gap_after": 0.03,
                "recourse_success_gap": 0.02,
            },
            {
                "lift_pass": True,
                "reliability_pass": True,
                "fairness_seed_pass": False,
                "worst_fairness_gap": 0.012,
                "high_stress_fairness_gap_after": 0.06,
                "recourse_success_gap": 0.05,
                "primary_fail_reason": "equalized_odds_gap_delta",
            },
        ],
        thresholds=_thresholds(),
        breakdown_rows=[
            {
                "breakdown_type": "segment_candidate_source",
                "canonical_segment_key": "mid|q1|stress",
                "candidate_source": "internal",
                "failure_weight": 0.7,
            },
            {
                "breakdown_type": "segment_candidate_source",
                "canonical_segment_key": "mid|q2|stress",
                "candidate_source": "dice",
                "failure_weight": 0.3,
            },
        ],
    )
    assert metrics["fairness_seed_pass_count"] == 1
    assert metrics["fairness_seed_total"] == 2
    assert metrics["dominant_fail_segment_key"] == "mid|q1|stress"
    assert metrics["dominant_fail_candidate_source"] == "internal"
    assert float(metrics["dominant_fail_segment_share"]) == 0.7


def test_evaluate_release_decision_returns_go_for_all_green() -> None:
    decision = evaluate_release_decision(
        {
            "lift_pass": True,
            "reliability_pass": True,
            "fairness_seed_pass_count": 5,
            "fairness_seed_total": 5,
            "worst_fairness_gap": 0.009,
            "dominant_fail_segment_share": 0.0,
        },
        _thresholds(),
    )
    assert decision["decision"] == GO
    assert decision["smoke_pass"] is True
    assert decision["pilot_eligible"] is False


def test_evaluate_release_decision_returns_limited_go_for_localized_single_seed_fail() -> None:
    decision = evaluate_release_decision(
        {
            "lift_pass": True,
            "reliability_pass": True,
            "fairness_seed_pass_count": 4,
            "fairness_seed_total": 5,
            "worst_fairness_gap": 0.012,
            "worst_high_stress_fairness_gap_after": 0.12,
            "worst_recourse_success_gap": 0.10,
            "supporting_guardrails_within_limited_cap": True,
            "dominant_fail_segment_share": 0.71,
            "dominant_fail_segment_key": "mid|q1|stress",
            "dominant_fail_candidate_source": "internal",
        },
        _thresholds(),
    )
    assert decision["decision"] == LIMITED_GO
    assert decision["smoke_pass"] is False
    assert decision["pilot_eligible"] is True
    assert decision["max_traffic_pct"] == 5


def test_evaluate_release_decision_returns_no_go_when_lift_fails() -> None:
    decision = evaluate_release_decision(
        {
            "lift_pass": False,
            "reliability_pass": True,
            "fairness_seed_pass_count": 5,
            "fairness_seed_total": 5,
            "worst_fairness_gap": 0.0,
            "dominant_fail_segment_share": 0.0,
        },
        _thresholds(),
    )
    assert decision["decision"] == NO_GO
    assert decision["decision_reason"] == "lift_fail"


def test_milestone_acceptance_summary_maps_go_to_accepted() -> None:
    summary = build_milestone_acceptance_summary(
        phase="phase-09",
        milestone="v1.1",
        runner_type="suite",
        release_payload={"decision": GO, "smoke_pass": True, "pilot_eligible": False, "broad_rollout_allowed": True},
        aggregate_metrics={
            "seed_count": 5,
            "fairness_seed_pass_count": 5,
            "lift_pass": True,
            "reliability_pass": True,
            "worst_fairness_gap": 0.008,
            "dominant_fail_segment_key": "",
            "dominant_fail_candidate_source": "",
        },
        evidence_level="seeded_suite",
        acceptance_eligible=True,
        supporting_artifacts={"phase_scale_aggregate_json": "tables/phase_scale_aggregate.json"},
        model_version="model-123",
        model_freeze_mode="explicit_model_version",
    )
    assert summary["acceptance_status"] == ACCEPTED
    assert summary["release_decision"] == GO
    assert summary["broad_rollout_allowed"] is True


def test_milestone_acceptance_summary_keeps_limited_go_pilot_only_when_not_eligible() -> None:
    summary = build_milestone_acceptance_summary(
        phase="phase-09",
        milestone="v1.1",
        runner_type="suite",
        release_payload={
            "decision": LIMITED_GO,
            "smoke_pass": False,
            "pilot_eligible": True,
            "broad_rollout_allowed": False,
        },
        aggregate_metrics={
            "seed_count": 5,
            "fairness_seed_pass_count": 4,
            "lift_pass": True,
            "reliability_pass": True,
            "worst_fairness_gap": 0.012,
            "dominant_fail_segment_key": "mid|q1|stress",
            "dominant_fail_candidate_source": "internal",
        },
        evidence_level="seeded_suite",
        acceptance_eligible=False,
        evidence_status="degraded",
        degraded_reason="implicit_latest_model_freeze",
        supporting_artifacts={"release_decision_json": "tables/release_decision.json"},
        model_version="model-123",
        model_freeze_mode="implicit_latest",
    )
    review = render_milestone_acceptance_review(summary)
    assert summary["acceptance_status"] == PILOT_ONLY
    assert summary["acceptance_eligible"] is False
    assert summary["broad_rollout_allowed"] is False
    assert "implicit_latest_model_freeze" in review


def test_kpi_contract_snapshot_carries_degraded_evidence_fields() -> None:
    snapshot = build_kpi_contract_snapshot(
        runner_type="smoke",
        release_payload={
            "decision": GO,
            "smoke_pass": True,
            "pilot_eligible": False,
            "broad_rollout_allowed": True,
            "telemetry_status": "success",
            "telemetry_gate_status": "healthy",
            "telemetry_failure_reason": "",
            "telemetry_success_rate": 1.0,
            "telemetry_ingest_lag_s": 12.0,
            "telemetry_required_for_broad_rollout": True,
            "telemetry_required_for_pilot": True,
            "telemetry_artifact_path": "tables/telemetry_export.json",
        },
        aggregate_metrics={"lift_pass": True, "reliability_pass": True, "fairness_seed_pass_count": 1, "fairness_seed_total": 1},
        evidence_level="single_run_fallback",
        acceptance_eligible=False,
        evidence_status="degraded",
        degraded_reason="missing_repeated_seeded_evidence",
        missing_artifacts=["phase_scale_aggregate.json"],
        fallback_source="batch_summary_json",
        supporting_artifacts={"kpi_snapshot_json": "tables/kpi_snapshot.json"},
    )
    assert snapshot["release_decision"] == GO
    assert snapshot["evidence_level"] == "single_run_fallback"
    assert snapshot["acceptance_eligible"] is False
    assert snapshot["broad_rollout_allowed"] is False
    assert snapshot["fallback_source"] == "batch_summary_json"
    assert snapshot["telemetry_gate_status"] == "healthy"
    assert snapshot["telemetry_artifact_path"] == "tables/telemetry_export.json"
