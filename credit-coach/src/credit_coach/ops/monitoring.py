from __future__ import annotations

from typing import Any

import pandas as pd

from credit_coach.macro.drift_detect import compute_psi


def compute_feature_psi_report(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    feature_cols: list[str],
    bins: int = 10,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for col in feature_cols:
        if col not in reference_df.columns or col not in current_df.columns:
            continue
        psi = compute_psi(reference_df[col], current_df[col], bins=bins)
        rows.append({"feature": col, "psi": float(psi)})
    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=["feature", "psi"])
    return out.sort_values("psi", ascending=False).reset_index(drop=True)


def summarize_operational_health(
    plans_df: pd.DataFrame,
    fairness_df: pd.DataFrame,
    shock_df: pd.DataFrame,
    psi_report: pd.DataFrame,
    thresholds: dict[str, float],
    fairness_stress_df: pd.DataFrame | None = None,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    approval_rate = float((plans_df.get("status", pd.Series(dtype=str)) == "APPROVED").mean()) if not plans_df.empty else 0.0
    avg_risk_margin = float(plans_df.get("risk_margin", pd.Series([0.0] * max(len(plans_df), 1))).mean()) if not plans_df.empty else 0.0
    avg_reliability = float(shock_df.get("reliability", pd.Series([0.0] * max(len(shock_df), 1))).mean()) if not shock_df.empty else 0.0
    fairness_gap = float(fairness_df.get("approval_gap", pd.Series([0.0])).iloc[0]) if not fairness_df.empty else 0.0
    max_psi = float(psi_report["psi"].max()) if not psi_report.empty else 0.0

    high_stress_fairness_gap = 0.0
    if fairness_stress_df is not None and not fairness_stress_df.empty:
        hs = fairness_stress_df[fairness_stress_df.get("high_stress", pd.Series([0] * len(fairness_stress_df))).astype(int) == 1]
        if not hs.empty and "approval_gap" in hs.columns:
            high_stress_fairness_gap = float(hs["approval_gap"].max())

    summary = {
        "approval_rate": approval_rate,
        "avg_risk_margin": avg_risk_margin,
        "avg_reliability": avg_reliability,
        "fairness_gap": fairness_gap,
        "high_stress_fairness_gap": high_stress_fairness_gap,
        "max_psi": max_psi,
    }

    alerts: list[dict[str, Any]] = []

    if approval_rate < float(thresholds.get("min_approval_rate", 0.6)):
        alerts.append({"metric": "approval_rate", "severity": "HIGH", "value": approval_rate, "reason": "Below minimum threshold"})
    if avg_risk_margin < float(thresholds.get("min_avg_risk_margin", 0.0)):
        alerts.append({"metric": "avg_risk_margin", "severity": "HIGH", "value": avg_risk_margin, "reason": "Risk margin below threshold"})
    if avg_reliability < float(thresholds.get("min_reliability", 0.7)):
        alerts.append({"metric": "avg_reliability", "severity": "HIGH", "value": avg_reliability, "reason": "Shock reliability below threshold"})
    max_fairness_gap = float(thresholds.get("max_fairness_gap", 0.1))
    if fairness_gap > max_fairness_gap:
        alerts.append({"metric": "fairness_gap", "severity": "HIGH", "value": fairness_gap, "reason": "Fairness gap above threshold"})

    hs_gap_threshold = float(thresholds.get("max_high_stress_fairness_gap", max_fairness_gap))
    if high_stress_fairness_gap > hs_gap_threshold:
        alerts.append(
            {
                "metric": "high_stress_fairness_gap",
                "severity": "HIGH",
                "value": high_stress_fairness_gap,
                "reason": "High-stress fairness gap above threshold",
            }
        )

    psi_warn = float(thresholds.get("psi_warn", 0.1))
    psi_fail = float(thresholds.get("psi_fail", 0.2))
    if max_psi > psi_fail:
        alerts.append({"metric": "max_psi", "severity": "HIGH", "value": max_psi, "reason": "Drift above fail threshold"})
    elif max_psi > psi_warn:
        alerts.append({"metric": "max_psi", "severity": "MEDIUM", "value": max_psi, "reason": "Drift above warning threshold"})

    return summary, alerts

