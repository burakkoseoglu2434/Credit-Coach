from __future__ import annotations

from argparse import Namespace

import pandas as pd

from credit_coach.cli.run_production_smoke import build_smoke_gate_rows


def _args(**overrides) -> Namespace:
    base = {
        "min_denied_to_approved_lift": 0.05,
        "min_denied_high_risk_lift": 0.03,
        "min_denied_gate_pass_rate": 0.08,
        "max_denied_reliability_violation_rate": 0.40,
        "max_approval_gap_delta": 0.01,
        "max_equalized_odds_gap_delta": 0.01,
        "max_p95_latency_ms": 500.0,
        "max_p99_latency_ms": 2000.0,
        "max_error_rate": 0.005,
        "min_last_k_validity": 0.70,
        "min_last_k_safe_rate": 0.60,
        "min_last_k_avg_risk_margin": 0.0,
        "max_fairness_gap": 0.10,
        "max_high_stress_fairness_gap": 0.10,
        "max_recourse_success_gap": 0.10,
        "max_recourse_cost_gap": 500.0,
        "min_trajectory_gate_pass_rate_4w": 0.03,
        "min_trajectory_gate_pass_rate_12w": 0.06,
        "min_trajectory_gate_pass_rate_24w": 0.09,
        "min_trajectory_partial_progress_rate": 0.20,
        "max_trajectory_median_time_to_gate_pass_days": 168.0,
        "min_approval_rate": 0.60,
        "max_psi": 0.25,
        "min_avg_reliability": 0.70,
        "min_telemetry_success_rate": 0.99,
        "max_telemetry_ingest_lag_s": 60.0,
        "require_telemetry_enabled": False,
    }
    base.update(overrides)
    return Namespace(**base)


def test_build_smoke_gate_rows_passes():
    batch_summary = {
        "denied_to_approved_lift": 0.08,
        "denied_high_risk_lift": 0.04,
        "denied_count": 100,
        "denied_with_gate_pass_plan": 10,
        "denied_reliability_violation_rate": 0.20,
        "latency_p95_ms": 420.0,
        "latency_p99_ms": 1800.0,
        "error_rate": 0.003,
        "trajectory_gate_pass_rate_4w": 0.05,
        "trajectory_gate_pass_rate_12w": 0.09,
        "trajectory_gate_pass_rate_24w": 0.13,
        "trajectory_partial_progress_rate": 0.35,
        "trajectory_median_time_to_gate_pass_days": 84.0,
    }
    batch_fairness_change = pd.DataFrame([{"approval_gap_delta": 0.005, "equalized_odds_gap_delta": 0.004}])
    benchmark = pd.DataFrame(
        [{"method": "our", "last_k_validity": 0.95, "last_k_safe_rate": 0.90, "last_k_avg_risk_margin": 0.15}]
    )
    monitoring = pd.DataFrame([{"approval_rate": 0.85, "max_psi": 0.08, "avg_reliability": 0.93}])
    fairness = pd.DataFrame([{"approval_gap": 0.06}])
    fairness_stress = pd.DataFrame([{"high_stress": 1, "approval_gap": 0.07}])
    telemetry = {"enabled": False, "status": "disabled", "exported": False, "send_success_rate": 0.0, "ingest_lag_s_p95": 0.0}

    rows = build_smoke_gate_rows(
        batch_summary=batch_summary,
        batch_fairness_change_df=batch_fairness_change,
        benchmark_df=benchmark,
        monitoring_df=monitoring,
        fairness_df=fairness,
        fairness_stress_df=fairness_stress,
        telemetry_payload=telemetry,
        audit_ok=True,
        audit_issue_count=0,
        args=_args(),
    )
    out = pd.DataFrame(rows)
    assert len(out) == 8
    assert (out["status"] == "PASS").all()
    recourse_row = out[out["gate_id"] == "G0B_RECOURSE_FUNNEL"].iloc[0]
    assert recourse_row["status"] == "PASS"


def test_build_smoke_gate_rows_detects_failures():
    batch_summary = {
        "denied_to_approved_lift": 0.01,
        "denied_high_risk_lift": 0.0,
        "denied_count": 100,
        "denied_with_gate_pass_plan": 2,
        "denied_reliability_violation_rate": 0.95,
        "latency_p95_ms": 800.0,
        "latency_p99_ms": 3500.0,
        "error_rate": 0.02,
        "trajectory_gate_pass_rate_4w": 0.0,
        "trajectory_gate_pass_rate_12w": 0.01,
        "trajectory_gate_pass_rate_24w": 0.01,
        "trajectory_partial_progress_rate": 0.05,
        "trajectory_median_time_to_gate_pass_days": 365.0,
    }
    batch_fairness_change = pd.DataFrame([{"approval_gap_delta": 0.03, "equalized_odds_gap_delta": 0.02}])
    benchmark = pd.DataFrame(
        [{"method": "our", "last_k_validity": 0.65, "last_k_safe_rate": 0.40, "last_k_avg_risk_margin": -0.2}]
    )
    monitoring = pd.DataFrame([{"approval_rate": 0.50, "max_psi": 0.40, "avg_reliability": 0.40}])
    fairness = pd.DataFrame([{"approval_gap": 0.18}])
    fairness_stress = pd.DataFrame([{"high_stress": 1, "approval_gap": 0.22}])
    telemetry = {"enabled": False, "status": "disabled", "exported": False, "send_success_rate": 0.0, "ingest_lag_s_p95": 999.0}

    rows = build_smoke_gate_rows(
        batch_summary=batch_summary,
        batch_fairness_change_df=batch_fairness_change,
        benchmark_df=benchmark,
        monitoring_df=monitoring,
        fairness_df=fairness,
        fairness_stress_df=fairness_stress,
        telemetry_payload=telemetry,
        audit_ok=False,
        audit_issue_count=2,
        args=_args(require_telemetry_enabled=True),
    )
    out = pd.DataFrame(rows)
    assert len(out) == 8
    assert (out["status"] == "FAIL").all()
    recourse_row = out[out["gate_id"] == "G0B_RECOURSE_FUNNEL"].iloc[0]
    assert recourse_row["status"] == "FAIL"


def test_build_smoke_gate_rows_prefers_sync_latency_when_available():
    batch_summary = {
        "denied_to_approved_lift": 0.09,
        "denied_high_risk_lift": 0.04,
        "denied_count": 100,
        "denied_with_gate_pass_plan": 10,
        "denied_reliability_violation_rate": 0.30,
        "latency_p95_ms": 1200.0,
        "latency_p99_ms": 1800.0,
        "sync_latency_p95_ms": 420.0,
        "sync_latency_p99_ms": 700.0,
        "error_rate": 0.0,
        "trajectory_gate_pass_rate_4w": 0.05,
        "trajectory_gate_pass_rate_12w": 0.09,
        "trajectory_gate_pass_rate_24w": 0.12,
        "trajectory_partial_progress_rate": 0.30,
        "trajectory_median_time_to_gate_pass_days": 84.0,
    }
    batch_fairness_change = pd.DataFrame([{"approval_gap_delta": 0.0, "equalized_odds_gap_delta": 0.0}])
    benchmark = pd.DataFrame(
        [{"method": "our", "last_k_validity": 0.95, "last_k_safe_rate": 0.90, "last_k_avg_risk_margin": 0.15}]
    )
    monitoring = pd.DataFrame([{"approval_rate": 0.85, "max_psi": 0.08, "avg_reliability": 0.93}])
    fairness = pd.DataFrame([{"approval_gap": 0.06}])
    fairness_stress = pd.DataFrame([{"high_stress": 1, "approval_gap": 0.07}])
    telemetry = {"enabled": False, "status": "disabled", "exported": False, "send_success_rate": 0.0, "ingest_lag_s_p95": 0.0}

    rows = build_smoke_gate_rows(
        batch_summary=batch_summary,
        batch_fairness_change_df=batch_fairness_change,
        benchmark_df=benchmark,
        monitoring_df=monitoring,
        fairness_df=fairness,
        fairness_stress_df=fairness_stress,
        telemetry_payload=telemetry,
        audit_ok=True,
        audit_issue_count=0,
        args=_args(),
    )
    out = pd.DataFrame(rows)
    g0 = out[out["gate_id"] == "G0_BATCH_RECOURSE_KPI"].iloc[0]
    assert g0["status"] == "PASS"
    assert "latency_mode" in g0["details_json"]
