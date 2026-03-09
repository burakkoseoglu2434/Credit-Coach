from __future__ import annotations

import pandas as pd

from credit_coach.evaluation.fairness import build_recourse_fairness_bundle


def test_build_recourse_fairness_bundle():
    df = pd.DataFrame(
        {
            "group": ["A", "A", "B", "B"],
            "denied_base": [1, 1, 1, 1],
            "gate_pass_any_candidate": [1, 0, 1, 1],
            "best_cost_usd": [100.0, 120.0, 80.0, 90.0],
            "best_horizon_months": [6, 6, 3, 3],
        }
    )
    out = build_recourse_fairness_bundle(
        df.rename(columns={"group": "group_bucket"}),
        group_col="group_bucket",
    )
    assert out["recourse_success_gap"] > 0.0
    assert out["recourse_cost_gap"] >= 0.0
    assert out["recourse_horizon_gap"] >= 0.0
