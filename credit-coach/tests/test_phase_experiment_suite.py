from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from credit_coach.cli.run_phase_experiment_suite import (
    _build_phase_fairness_breakdown,
    _kpi_checks,
    _seed_contract_snapshot,
    _train_cmd,
)


def _thresholds() -> dict[str, float]:
    return {
        "min_denied_to_approved_lift": 0.09,
        "min_denied_high_risk_lift": 0.03,
        "min_denied_gate_pass_rate": 0.08,
        "max_denied_reliability_violation_rate": 0.40,
        "max_approval_gap_delta": 0.01,
        "max_equalized_odds_gap_delta": 0.01,
        "max_p95_latency_ms": 500.0,
        "max_p99_latency_ms": 2000.0,
        "max_error_rate": 0.005,
        "max_fairness_gap": 0.10,
        "max_high_stress_fairness_gap": 0.10,
        "max_recourse_success_gap": 0.10,
        "min_trajectory_gate_pass_rate_4w": 0.03,
        "min_trajectory_gate_pass_rate_12w": 0.06,
        "min_trajectory_gate_pass_rate_24w": 0.09,
        "min_trajectory_partial_progress_rate": 0.20,
        "max_trajectory_median_time_to_gate_pass_days": 168.0,
    }


def test_kpi_checks_passes_when_trajectory_and_core_metrics_meet_contract() -> None:
    summary = {
        "denied_count": 100,
        "denied_with_gate_pass_plan": 10,
        "denied_to_approved_lift": 0.11,
        "denied_high_risk_lift": 0.05,
        "denied_reliability_violation_rate": 0.20,
        "sync_latency_p95_ms": 450.0,
        "sync_latency_p99_ms": 1100.0,
        "error_rate": 0.0,
        "fairness_approval_gap_after": 0.08,
        "trajectory_gate_pass_rate_4w": 0.04,
        "trajectory_gate_pass_rate_12w": 0.07,
        "trajectory_gate_pass_rate_24w": 0.10,
        "trajectory_partial_progress_rate": 0.30,
        "trajectory_median_time_to_gate_pass_days": 84.0,
    }
    fair = {
        "approval_gap_delta": 0.0,
        "equalized_odds_gap_delta": 0.0,
        "high_stress_approval_gap_after": 0.09,
        "recourse_success_gap": 0.05,
    }
    ok, failed = _kpi_checks(summary, fair, _thresholds())
    assert ok is True
    assert failed == ""


def test_kpi_checks_fails_when_trajectory_gate_is_below_threshold() -> None:
    summary = {
        "denied_count": 100,
        "denied_with_gate_pass_plan": 10,
        "denied_to_approved_lift": 0.11,
        "denied_high_risk_lift": 0.05,
        "denied_reliability_violation_rate": 0.20,
        "sync_latency_p95_ms": 450.0,
        "sync_latency_p99_ms": 1100.0,
        "error_rate": 0.0,
        "fairness_approval_gap_after": 0.08,
        "trajectory_gate_pass_rate_4w": 0.0,
        "trajectory_gate_pass_rate_12w": 0.02,
        "trajectory_gate_pass_rate_24w": 0.05,
        "trajectory_partial_progress_rate": 0.10,
        "trajectory_median_time_to_gate_pass_days": 200.0,
    }
    fair = {
        "approval_gap_delta": 0.0,
        "equalized_odds_gap_delta": 0.0,
        "high_stress_approval_gap_after": 0.09,
        "recourse_success_gap": 0.05,
    }
    ok, failed = _kpi_checks(summary, fair, _thresholds())
    assert ok is False
    assert "trajectory_gate_pass_rate_4w" in failed
    assert "trajectory_gate_pass_rate_12w" in failed
    assert "trajectory_gate_pass_rate_24w" in failed
    assert "trajectory_partial_progress_rate" in failed
    assert "trajectory_median_time_to_gate_pass_days" in failed


def test_seed_contract_snapshot_exposes_split_lift_reliability_and_fairness_states() -> None:
    summary = {
        "denied_count": 100,
        "denied_with_gate_pass_plan": 10,
        "denied_to_approved_lift": 0.11,
        "denied_high_risk_lift": 0.05,
        "denied_reliability_violation_rate": 0.20,
        "sync_latency_p95_ms": 450.0,
        "sync_latency_p99_ms": 1100.0,
        "error_rate": 0.0,
        "fairness_approval_gap_after": 0.08,
        "trajectory_gate_pass_rate_4w": 0.04,
        "trajectory_gate_pass_rate_12w": 0.07,
        "trajectory_gate_pass_rate_24w": 0.10,
        "trajectory_partial_progress_rate": 0.30,
        "trajectory_median_time_to_gate_pass_days": 84.0,
    }
    fair = {
        "approval_gap_delta": 0.0,
        "equalized_odds_gap_delta": 0.008,
        "high_stress_approval_gap_after": 0.09,
        "recourse_success_gap": 0.05,
    }
    snapshot = _seed_contract_snapshot(summary, fair, _thresholds())
    assert snapshot["lift_pass"] is True
    assert snapshot["reliability_pass"] is True
    assert snapshot["fairness_seed_pass"] is True
    assert snapshot["primary_fairness_metric"] == "equalized_odds_gap_delta"
    assert snapshot["primary_fail_reason"] == ""
    assert float(snapshot["worst_fairness_gap"]) == 0.008


def test_seed_contract_snapshot_marks_fairness_seed_fail_separately() -> None:
    summary = {
        "denied_count": 100,
        "denied_with_gate_pass_plan": 10,
        "denied_to_approved_lift": 0.11,
        "denied_high_risk_lift": 0.05,
        "denied_reliability_violation_rate": 0.20,
        "sync_latency_p95_ms": 450.0,
        "sync_latency_p99_ms": 1100.0,
        "error_rate": 0.0,
        "fairness_approval_gap_after": 0.08,
        "trajectory_gate_pass_rate_4w": 0.04,
        "trajectory_gate_pass_rate_12w": 0.07,
        "trajectory_gate_pass_rate_24w": 0.10,
        "trajectory_partial_progress_rate": 0.30,
        "trajectory_median_time_to_gate_pass_days": 84.0,
    }
    fair = {
        "approval_gap_delta": 0.0,
        "equalized_odds_gap_delta": 0.02,
        "high_stress_approval_gap_after": 0.09,
        "recourse_success_gap": 0.05,
    }
    snapshot = _seed_contract_snapshot(summary, fair, _thresholds())
    assert snapshot["lift_pass"] is True
    assert snapshot["reliability_pass"] is True
    assert snapshot["fairness_seed_pass"] is False
    assert snapshot["primary_fail_reason"] == "equalized_odds_gap_delta"
    assert "equalized_odds_gap_delta" in snapshot["failed_checks"]


def test_build_phase_fairness_breakdown_emits_required_breakdown_views() -> None:
    breakdown = _build_phase_fairness_breakdown(
        seed_rows=[
            {
                "seed": 42,
                "primary_fail_reason": "equalized_odds_gap_delta",
                "worst_fairness_gap": 0.012,
                "high_stress_fairness_gap_after": 0.08,
            }
        ],
        seed_breakdowns=[
            pd.DataFrame(
                [
                    {
                        "seed": 42,
                        "group_bucket": "RENT",
                        "risk_band": "mid",
                        "income_band": "q1",
                        "candidate_source": "internal",
                        "best_source": "internal",
                        "stress_band": "base",
                        "canonical_segment_key": "mid|q1|base",
                        "n_rows": 10,
                        "denied_rows": 8,
                        "failure_severity_score": 0.7,
                        "failure_weight": 0.7,
                    }
                ]
            )
        ],
    )
    assert set(breakdown["breakdown_type"]) >= {
        "segment_candidate_source",
        "seed_segment",
        "high_stress_segment",
        "seed_primary_fail_reason",
        "risk_band_source_rollup",
    }
    assert "canonical_segment_key" in breakdown.columns
    assert "candidate_source" in breakdown.columns


def test_train_cmd_uses_base_and_model_config_paths() -> None:
    args = SimpleNamespace(
        base_config="configs/default.yaml",
        model_config="configs/model.yaml",
    )
    cmd = _train_cmd(args)
    assert len(cmd) >= 3
    assert cmd[1:3] == ["-m", "credit_coach.cli.run_train"]
    assert "--base_config" in cmd
    assert "--config" in cmd
    assert "configs/default.yaml" in cmd
    assert "configs/model.yaml" in cmd
