from __future__ import annotations

import pandas as pd

from credit_coach.evaluation.metrics import (
    compute_rolling_window_recourse_metrics,
    summarize_last_k_windows,
)


def test_compute_rolling_window_recourse_metrics():
    plans = pd.DataFrame(
        {
            "week": [1, 2, 3, 4, 5, 6],
            "predicted_pd": [0.20, 0.25, 0.40, 0.30, 0.22, 0.28],
            "status": ["APPROVED", "APPROVED", "NEEDS_REVIEW", "APPROVED", "APPROVED", "APPROVED"],
            "risk_margin": [0.15, 0.10, -0.05, 0.05, 0.13, 0.07],
            "cost": [100, 120, 200, 130, 110, 115],
            "action_count": [2, 2, 3, 2, 1, 2],
            "proximity_l1": [1.0, 1.1, 1.8, 1.2, 0.8, 1.0],
        }
    )
    out = compute_rolling_window_recourse_metrics(plans, tau=0.35, window_size=3, step_size=2, order_col="week")
    assert len(out) >= 2
    assert {"window_id", "start_idx", "end_idx", "validity", "safe_rate", "avg_risk_margin"}.issubset(out.columns)


def test_summarize_last_k_windows():
    rolling = pd.DataFrame(
        {
            "window_id": [1, 2, 3, 4],
            "validity": [0.8, 0.9, 1.0, 0.7],
            "safe_rate": [0.6, 0.7, 0.9, 0.8],
            "avg_risk_margin": [0.01, 0.02, 0.03, -0.01],
        }
    )
    s = summarize_last_k_windows(rolling, last_k=3)
    assert s["last_k_used"] == 3.0
    assert 0.0 <= s["last_k_validity"] <= 1.0
    assert "last_k_avg_risk_margin" in s

