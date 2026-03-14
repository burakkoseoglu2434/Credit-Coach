from __future__ import annotations

import pandas as pd

from credit_coach.evaluation.fairness import build_canonical_segment_key, build_recourse_fairness_bundle, classify_primary_fairness_fail_reason


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


def test_build_canonical_segment_key_includes_stress_band():
    key = build_canonical_segment_key(risk_band="mid", income_band="q1", stress_band="high_stress")
    assert key == "mid|q1|high_stress"


def test_classify_primary_fairness_fail_reason_prefers_equalized_odds_first():
    reason = classify_primary_fairness_fail_reason(
        {
            "equalized_odds_gap_delta": 0.02,
            "high_stress_fairness_gap_after": 0.50,
            "recourse_success_gap": 0.20,
        },
        {
            "max_equalized_odds_gap_delta": 0.01,
            "max_high_stress_fairness_gap": 0.10,
            "max_recourse_success_gap": 0.10,
        },
    )
    assert reason == "equalized_odds_gap_delta"
