from __future__ import annotations

import pandas as pd

from credit_coach.evaluation.off_policy import evaluate_off_policy


def test_off_policy_evaluation_marks_baseline_missing_without_control() -> None:
    learning_df = pd.DataFrame(
        [
            {
                "policy_arm": "treatment",
                "selection_propensity": 0.5,
                "approved": True,
                "observed_default_90d": 0,
                "observed_margin_90d": 120.0,
            }
        ]
    )

    evaluation = evaluate_off_policy(learning_df)

    assert evaluation["comparison_status"] == "baseline_missing"
    assert evaluation["ope_confidence"] == "tentative"
    assert evaluation["comparisons"] == []


def test_off_policy_evaluation_prefers_treatment_with_strong_coverage() -> None:
    rows = []
    for idx in range(40):
        rows.append(
            {
                "policy_arm": "control",
                "policy_arm_profile": {"offer_family": "control"},
                "selection_propensity": 0.5,
                "approved": False,
                "observed_default_90d": 1,
                "observed_margin_90d": -25.0,
                "decision_id": f"c{idx}",
            }
        )
        rows.append(
            {
                "policy_arm": "treatment",
                "policy_arm_profile": {"offer_family": "installment"},
                "selection_propensity": 0.5,
                "approved": True,
                "observed_default_90d": 0,
                "observed_margin_90d": 125.0,
                "decision_id": f"t{idx}",
            }
        )
    learning_df = pd.DataFrame(rows)

    evaluation = evaluate_off_policy(learning_df)

    assert evaluation["comparison_status"] == "treatment_vs_control"
    assert evaluation["ope_confidence"] == "strong"
    assert evaluation["preferred_policy_signal"]["policy_arm"] == "treatment"
    assert evaluation["preferred_policy_signal"]["signal"] == "supports_treatment"
    comparison = evaluation["comparisons"][0]
    assert comparison["ope_confidence"] == "strong"
    assert comparison["metric_labels"]["approval_rate"] == "supports_treatment"
    assert comparison["metric_labels"]["default_rate_90d"] == "supports_treatment"
    assert comparison["metric_labels"]["avg_margin_90d"] == "supports_treatment"


def test_off_policy_evaluation_degrades_for_weak_propensities_and_reward_coverage() -> None:
    learning_df = pd.DataFrame(
        [
            {
                "policy_arm": "control",
                "selection_propensity": 0.5,
                "approved": True,
                "observed_default_90d": 1,
                "observed_margin_90d": 10.0,
            },
            {
                "policy_arm": "control",
                "selection_propensity": 0.5,
                "approved": False,
                "observed_default_90d": None,
                "observed_margin_90d": None,
            },
            {
                "policy_arm": "treatment",
                "selection_propensity": 0.01,
                "approved": True,
                "observed_default_90d": None,
                "observed_margin_90d": None,
            },
            {
                "policy_arm": "treatment",
                "selection_propensity": 0.01,
                "approved": False,
                "observed_default_90d": 0,
                "observed_margin_90d": None,
            },
        ]
    )

    evaluation = evaluate_off_policy(learning_df)

    assert evaluation["comparison_status"] == "treatment_vs_control"
    assert evaluation["ope_confidence"] == "degraded"
    comparison = evaluation["comparisons"][0]
    assert comparison["ope_confidence"] == "degraded"
    assert comparison["metric_labels"]["default_rate_90d"] == "insufficient_evidence"
