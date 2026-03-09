from __future__ import annotations

import pandas as pd

from credit_coach.evaluation.fairness import (
    adverse_impact_ratio,
    approval_gap,
    equalized_odds_gap,
    false_positive_rate_gap,
    true_positive_rate_gap,
)
from credit_coach.evaluation.metrics import compute_recourse_metrics


def test_metrics_and_fairness():
    plans = pd.DataFrame(
        {
            "predicted_pd": [0.2, 0.4, 0.3],
            "status": ["APPROVED", "NEEDS_REVIEW", "APPROVED"],
            "risk_margin": [0.1, -0.05, 0.02],
            "cost": [100, 200, 150],
            "action_count": [2, 3, 1],
            "proximity_l1": [1.0, 1.5, 0.5],
        }
    )
    m = compute_recourse_metrics(plans, tau=0.35)
    assert m["plan_count"] == 3
    assert 0.0 <= m["validity"] <= 1.0
    assert m["avg_actions"] > 0.0
    assert m["avg_proximity"] > 0.0

    scored = pd.DataFrame(
        {
            "g": [0, 0, 1, 1],
            "approve": [1, 0, 1, 1],
            "y_true": [1, 0, 1, 0],
            "pred_default": [1, 0, 1, 1],
        }
    )
    gap = approval_gap(scored, group_col="g", approval_col="approve")
    air = adverse_impact_ratio(scored, group_col="g", approval_col="approve")
    tpr_gap = true_positive_rate_gap(scored, group_col="g", y_true_col="y_true", y_pred_col="pred_default")
    fpr_gap = false_positive_rate_gap(scored, group_col="g", y_true_col="y_true", y_pred_col="pred_default")
    eo_gap = equalized_odds_gap(scored, group_col="g", y_true_col="y_true", y_pred_col="pred_default")
    assert gap >= 0.0
    assert 0.0 <= air <= 1.0
    assert tpr_gap >= 0.0
    assert fpr_gap >= 0.0
    assert eo_gap >= 0.0
