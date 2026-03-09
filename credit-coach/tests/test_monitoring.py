from __future__ import annotations

import pandas as pd

from credit_coach.ops.monitoring import compute_feature_psi_report, summarize_operational_health


def test_monitoring_summary_and_alerts():
    ref = pd.DataFrame({"f1": [0.1, 0.2, 0.3], "f2": [1.0, 1.0, 1.0]})
    cur = pd.DataFrame({"f1": [0.9, 1.0, 1.1], "f2": [1.0, 1.0, 1.0]})
    psi = compute_feature_psi_report(ref, cur, feature_cols=["f1", "f2"], bins=5)
    assert "psi" in psi.columns

    plans = pd.DataFrame({"status": ["NEEDS_REVIEW", "REJECTED"], "risk_margin": [-0.02, -0.01]})
    fairness = pd.DataFrame({"approval_gap": [0.2]})
    shock = pd.DataFrame({"reliability": [0.4, 0.5]})
    thresholds = {
        "min_approval_rate": 0.6,
        "min_avg_risk_margin": 0.0,
        "min_reliability": 0.7,
        "max_fairness_gap": 0.1,
        "psi_warn": 0.1,
        "psi_fail": 0.2,
    }
    fairness_stress = pd.DataFrame(
        {
            "scenario": ["base", "combined_stress"],
            "high_stress": [0, 1],
            "approval_gap": [0.05, 0.25],
        }
    )
    summary, alerts = summarize_operational_health(
        plans,
        fairness,
        shock,
        psi,
        thresholds,
        fairness_stress_df=fairness_stress,
    )
    assert summary["approval_rate"] < 0.6
    assert summary["high_stress_fairness_gap"] >= 0.25
    assert any(a.get("metric") == "high_stress_fairness_gap" for a in alerts)
    assert len(alerts) >= 3
