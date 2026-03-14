from __future__ import annotations

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
