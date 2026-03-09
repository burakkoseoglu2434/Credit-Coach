from __future__ import annotations

from credit_coach.cli.run_high_risk_ab import (
    _extract_run_id,
    _kpi_gate_snapshot,
    _metric_rows,
    _riskband_rows,
)


def test_extract_run_id_from_logs():
    text = "RunContext artifact dir ready: artifacts/runs/20260307_172423_df1dd8_cceee1\nmore logs"
    assert _extract_run_id(text) == "20260307_172423_df1dd8_cceee1"


def test_metric_rows_directionality():
    control = {
        "denied_to_approved_lift": 0.02,
        "denied_high_risk_lift": 0.0,
        "latency_p99_ms": 2500.0,
        "error_rate": 0.0,
        "fairness_approval_gap_after": 0.09,
        "fairness_equalized_odds_gap_after": 0.11,
        "recourse_success_gap": 0.07,
        "recourse_cost_gap": 20.0,
    }
    treatment = {
        "denied_to_approved_lift": 0.03,
        "denied_high_risk_lift": 0.01,
        "latency_p99_ms": 2200.0,
        "error_rate": 0.0,
        "fairness_approval_gap_after": 0.08,
        "fairness_equalized_odds_gap_after": 0.10,
        "recourse_success_gap": 0.06,
        "recourse_cost_gap": 15.0,
    }
    df = _metric_rows(control, treatment)
    lift_row = df[df["metric"] == "denied_to_approved_lift"].iloc[0]
    assert int(lift_row["improved"]) == 1
    p99_row = df[df["metric"] == "latency_p99_ms"].iloc[0]
    assert int(p99_row["improved"]) == 1


def test_riskband_rows_union():
    c = {"near": 0.1, "high": 0.0}
    t = {"near": 0.15, "mid": 0.02}
    df = _riskband_rows(c, t)
    assert set(df["risk_band"].tolist()) == {"near", "mid", "high"}


def test_kpi_gate_snapshot():
    summary = {
        "denied_to_approved_lift": 0.051,
        "denied_high_risk_lift": 0.031,
        "latency_p95_ms": 320.0,
        "latency_p99_ms": 1900.0,
        "error_rate": 0.001,
        "fairness_approval_gap_after": 0.08,
    }
    thresholds = {
        "min_denied_to_approved_lift": 0.05,
        "min_denied_high_risk_lift": 0.03,
        "max_p95_latency_ms": 500.0,
        "max_p99_latency_ms": 2000.0,
        "max_error_rate": 0.005,
        "max_fairness_gap": 0.10,
    }
    snap = _kpi_gate_snapshot(summary, thresholds)
    assert snap["all_pass"] is True
