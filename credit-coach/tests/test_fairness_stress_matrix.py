from __future__ import annotations

import pandas as pd

from credit_coach.evaluation.fairness import build_fairness_stress_matrix


def test_build_fairness_stress_matrix_outputs():
    scored = pd.DataFrame(
        {
            "group_bucket": ["A", "A", "B", "B"],
            "y_true": [1, 0, 1, 0],
        }
    )
    proba = pd.Series([0.20, 0.30, 0.40, 0.50])
    scenarios = [
        {"name": "mild", "changes": {"interest_rate": 1.0}},
        {"name": "combined_stress", "changes": {"interest_rate": 5.0, "unemployment_rate": 3.0}},
    ]

    out = build_fairness_stress_matrix(
        scored_base=scored,
        proba=proba,
        tau=0.35,
        scenarios=scenarios,
        threshold_shift_per_msi_unit=-0.02,
        group_col="group_bucket",
        high_stress_severity=0.6,
    )
    assert len(out) == 3  # base + 2 scenarios
    assert {
        "scenario",
        "scenario_pd_shift",
        "scenario_severity",
        "high_stress",
        "tau_used",
        "approval_gap",
        "adverse_impact_ratio",
        "equalized_odds_gap",
    }.issubset(out.columns)
    assert (out["scenario"] == "base").any()

