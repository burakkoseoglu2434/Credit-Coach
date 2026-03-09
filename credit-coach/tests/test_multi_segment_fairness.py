from __future__ import annotations

import pandas as pd

from credit_coach.evaluation.fairness import compute_multi_segment_fairness


def test_compute_multi_segment_fairness_returns_rows():
    df = pd.DataFrame(
        {
            "home_ownership": ["rent", "rent", "own", "own", "mortgage", "mortgage"],
            "income_band": ["q1", "q2", "q1", "q2", "q3", "q4"],
            "risk_band": ["near", "mid", "near", "high", "mid", "high"],
            "approve": [0, 1, 0, 1, 1, 0],
            "y_true": [1, 0, 1, 0, 0, 1],
            "pred_default": [1, 0, 1, 0, 0, 1],
        }
    )
    out = compute_multi_segment_fairness(
        df,
        segment_sets=[["home_ownership"], ["income_band", "risk_band"]],
        min_segment_n=1,
    )
    assert not out.empty
    assert {"segment_id", "approval_gap", "equalized_odds_gap", "segment_coverage_rate"} <= set(out.columns)
    assert (out["segment_coverage_rate"] > 0).all()
