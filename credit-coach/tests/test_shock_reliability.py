from __future__ import annotations

import pandas as pd

from credit_coach.macro.reliability import evaluate_reliability_from_pd
from credit_coach.macro.shock_sim import run_shock_reliability


def test_evaluate_reliability_from_pd_with_scenarios():
    scenarios = [
        {"name": "mild", "changes": {"interest_rate": 1.0}},
        {"name": "stress", "changes": {"interest_rate": 3.0, "unemployment_rate": 2.0}},
    ]
    out = evaluate_reliability_from_pd(
        base_pd=0.30,
        tau=0.35,
        scenarios=scenarios,
        threshold_shift_per_msi_unit=-0.02,
    )
    assert 0.0 <= out["reliability"] <= 1.0
    assert 0.0 <= out["reliability_soft"] <= 1.0
    assert out["worst_stressed_pd"] >= out["avg_stressed_pd"]
    assert out["worst_risk_margin"] <= 0.35


def test_run_shock_reliability_adds_columns():
    plans = pd.DataFrame({"predicted_pd": [0.2, 0.4]})
    scenarios = [{"name": "shock", "changes": {"interest_rate": 2.0}}]
    out = run_shock_reliability(plans, tau=0.35, scenarios=scenarios, threshold_shift_per_msi_unit=-0.02)
    assert {"reliability", "reliability_soft", "worst_risk_margin", "avg_stressed_pd", "worst_stressed_pd"}.issubset(
        out.columns
    )
