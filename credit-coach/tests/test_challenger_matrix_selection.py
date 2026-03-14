from __future__ import annotations

import pandas as pd

from credit_coach.cli.run_model_challenger_matrix import (
    _build_variant_model_cfg,
    _select_champion,
)


def test_build_variant_model_cfg_logistic_disables_xgboost_flag():
    base_model_cfg = {
        "model": {
            "type": "xgboost",
            "params": {
                "allow_xgboost": True,
                "monotone_constraints": {"dti": 1},
            },
        },
        "calibration": {"method": "isotonic"},
    }
    variant = {
        "variant_id": "logistic_sigmoid",
        "force_backend": "logistic_regression",
        "calibration_method": "sigmoid",
        "monotonic_constraints": {},
    }

    out = _build_variant_model_cfg(base_model_cfg=base_model_cfg, variant=variant)
    assert out["model"]["type"] == "logistic_regression"
    assert bool(out["model"]["params"]["allow_xgboost"]) is False
    assert out["model"]["params"]["monotone_constraints"] == {}
    assert out["calibration"]["method"] == "sigmoid"


def test_select_champion_prefers_gate_passing_variant_over_higher_lift():
    summary_df = pd.DataFrame(
        [
            {
                "variant_id": "higher_lift_but_bad_fairness",
                "mean_denied_to_approved_lift": 0.14,
                "mean_denied_high_risk_lift": 0.07,
                "mean_high_risk_reachability_rate": 0.22,
                "mean_fairness_approval_gap_after": 0.18,
                "mean_latency_p95_ms": 250.0,
                "mean_latency_p99_ms": 900.0,
                "mean_error_rate": 0.001,
            },
            {
                "variant_id": "slightly_lower_lift_gate_pass",
                "mean_denied_to_approved_lift": 0.12,
                "mean_denied_high_risk_lift": 0.05,
                "mean_high_risk_reachability_rate": 0.18,
                "mean_fairness_approval_gap_after": 0.05,
                "mean_latency_p95_ms": 300.0,
                "mean_latency_p99_ms": 1000.0,
                "mean_error_rate": 0.001,
            },
        ]
    )
    thresholds = {
        "min_denied_to_approved_lift": 0.09,
        "min_denied_high_risk_lift": 0.03,
        "max_fairness_gap": 0.10,
        "max_p95_latency_ms": 500.0,
        "max_p99_latency_ms": 2000.0,
        "max_error_rate": 0.005,
    }

    champion, ranked = _select_champion(summary_df, thresholds)
    assert champion == "slightly_lower_lift_gate_pass"
    assert bool(ranked.iloc[0]["_gate_all_pass"]) is True
    assert str(ranked.iloc[0]["variant_id"]) == "slightly_lower_lift_gate_pass"


def test_select_champion_chooses_lower_violation_score_when_all_fail():
    summary_df = pd.DataFrame(
        [
            {
                "variant_id": "fails_hard",
                "mean_denied_to_approved_lift": 0.03,
                "mean_denied_high_risk_lift": 0.00,
                "mean_high_risk_reachability_rate": 0.01,
                "mean_fairness_approval_gap_after": 0.20,
                "mean_latency_p95_ms": 900.0,
                "mean_latency_p99_ms": 3000.0,
                "mean_error_rate": 0.02,
            },
            {
                "variant_id": "fails_less",
                "mean_denied_to_approved_lift": 0.08,
                "mean_denied_high_risk_lift": 0.02,
                "mean_high_risk_reachability_rate": 0.05,
                "mean_fairness_approval_gap_after": 0.12,
                "mean_latency_p95_ms": 520.0,
                "mean_latency_p99_ms": 2100.0,
                "mean_error_rate": 0.006,
            },
        ]
    )
    thresholds = {
        "min_denied_to_approved_lift": 0.09,
        "min_denied_high_risk_lift": 0.03,
        "max_fairness_gap": 0.10,
        "max_p95_latency_ms": 500.0,
        "max_p99_latency_ms": 2000.0,
        "max_error_rate": 0.005,
    }

    champion, ranked = _select_champion(summary_df, thresholds)
    assert champion == "fails_less"
    assert bool(ranked.iloc[0]["_gate_all_pass"]) is False
    assert float(ranked.iloc[0]["_gate_violation_score"]) <= float(ranked.iloc[1]["_gate_violation_score"])


def test_select_champion_respects_trajectory_gates_from_contract():
    summary_df = pd.DataFrame(
        [
            {
                "variant_id": "high_lift_but_no_trajectory",
                "mean_denied_to_approved_lift": 0.20,
                "mean_denied_high_risk_lift": 0.09,
                "mean_high_risk_reachability_rate": 0.30,
                "mean_denied_reliability_violation_rate": 0.20,
                "mean_fairness_approval_gap_after": 0.05,
                "mean_fairness_equalized_odds_gap_after": 0.05,
                "mean_recourse_success_gap": 0.05,
                "mean_latency_p95_ms": 350.0,
                "mean_latency_p99_ms": 900.0,
                "mean_error_rate": 0.0,
                "mean_trajectory_gate_pass_rate_4w": 0.0,
                "mean_trajectory_gate_pass_rate_12w": 0.04,
                "mean_trajectory_gate_pass_rate_24w": 0.05,
                "mean_trajectory_partial_progress_rate": 0.15,
                "mean_trajectory_median_time_to_gate_pass_days": 200.0,
            },
            {
                "variant_id": "slightly_lower_lift_with_trajectory",
                "mean_denied_to_approved_lift": 0.16,
                "mean_denied_high_risk_lift": 0.07,
                "mean_high_risk_reachability_rate": 0.24,
                "mean_denied_reliability_violation_rate": 0.20,
                "mean_fairness_approval_gap_after": 0.05,
                "mean_fairness_equalized_odds_gap_after": 0.05,
                "mean_recourse_success_gap": 0.05,
                "mean_latency_p95_ms": 350.0,
                "mean_latency_p99_ms": 900.0,
                "mean_error_rate": 0.0,
                "mean_trajectory_gate_pass_rate_4w": 0.04,
                "mean_trajectory_gate_pass_rate_12w": 0.08,
                "mean_trajectory_gate_pass_rate_24w": 0.10,
                "mean_trajectory_partial_progress_rate": 0.25,
                "mean_trajectory_median_time_to_gate_pass_days": 84.0,
            },
        ]
    )
    thresholds = {
        "min_denied_to_approved_lift": 0.09,
        "min_denied_high_risk_lift": 0.03,
        "max_denied_reliability_violation_rate": 0.40,
        "max_fairness_gap": 0.10,
        "max_recourse_success_gap": 0.10,
        "max_p95_latency_ms": 500.0,
        "max_p99_latency_ms": 2000.0,
        "max_error_rate": 0.005,
        "min_trajectory_gate_pass_rate_4w": 0.03,
        "min_trajectory_gate_pass_rate_12w": 0.06,
        "min_trajectory_gate_pass_rate_24w": 0.09,
        "min_trajectory_partial_progress_rate": 0.20,
        "max_trajectory_median_time_to_gate_pass_days": 168.0,
    }

    champion, ranked = _select_champion(summary_df, thresholds)
    assert champion == "slightly_lower_lift_with_trajectory"
    assert bool(ranked.iloc[0]["_gate_all_pass"]) is True
    assert str(ranked.iloc[0]["variant_id"]) == "slightly_lower_lift_with_trajectory"


def test_select_champion_respects_equalized_odds_delta_gate():
    summary_df = pd.DataFrame(
        [
            {
                "variant_id": "high_lift_bad_eo_delta",
                "mean_denied_to_approved_lift": 0.15,
                "mean_denied_high_risk_lift": 0.08,
                "mean_high_risk_reachability_rate": 0.20,
                "mean_denied_reliability_violation_rate": 0.10,
                "mean_fairness_approval_gap_after": 0.05,
                "mean_fairness_approval_gap_delta": 0.005,
                "mean_fairness_equalized_odds_gap_delta": 0.03,
                "mean_high_stress_approval_gap_after": 0.05,
                "mean_recourse_success_gap": 0.05,
                "mean_latency_p95_ms": 300.0,
                "mean_latency_p99_ms": 900.0,
                "mean_error_rate": 0.0,
                "mean_trajectory_gate_pass_rate_4w": 0.04,
                "mean_trajectory_gate_pass_rate_12w": 0.08,
                "mean_trajectory_gate_pass_rate_24w": 0.10,
                "mean_trajectory_partial_progress_rate": 0.25,
                "mean_trajectory_median_time_to_gate_pass_days": 120.0,
            },
            {
                "variant_id": "slightly_lower_lift_good_eo_delta",
                "mean_denied_to_approved_lift": 0.13,
                "mean_denied_high_risk_lift": 0.07,
                "mean_high_risk_reachability_rate": 0.19,
                "mean_denied_reliability_violation_rate": 0.10,
                "mean_fairness_approval_gap_after": 0.05,
                "mean_fairness_approval_gap_delta": 0.005,
                "mean_fairness_equalized_odds_gap_delta": 0.005,
                "mean_high_stress_approval_gap_after": 0.05,
                "mean_recourse_success_gap": 0.05,
                "mean_latency_p95_ms": 300.0,
                "mean_latency_p99_ms": 900.0,
                "mean_error_rate": 0.0,
                "mean_trajectory_gate_pass_rate_4w": 0.04,
                "mean_trajectory_gate_pass_rate_12w": 0.08,
                "mean_trajectory_gate_pass_rate_24w": 0.10,
                "mean_trajectory_partial_progress_rate": 0.25,
                "mean_trajectory_median_time_to_gate_pass_days": 120.0,
            },
        ]
    )
    thresholds = {
        "min_denied_to_approved_lift": 0.09,
        "min_denied_high_risk_lift": 0.03,
        "max_denied_reliability_violation_rate": 0.40,
        "max_approval_gap_delta": 0.01,
        "max_equalized_odds_gap_delta": 0.01,
        "max_high_stress_fairness_gap": 0.10,
        "max_recourse_success_gap": 0.10,
        "max_fairness_gap": 0.10,
        "max_p95_latency_ms": 500.0,
        "max_p99_latency_ms": 2000.0,
        "max_error_rate": 0.005,
        "min_trajectory_gate_pass_rate_4w": 0.03,
        "min_trajectory_gate_pass_rate_12w": 0.06,
        "min_trajectory_gate_pass_rate_24w": 0.09,
        "min_trajectory_partial_progress_rate": 0.20,
        "max_trajectory_median_time_to_gate_pass_days": 168.0,
    }

    champion, ranked = _select_champion(summary_df, thresholds)
    assert champion == "slightly_lower_lift_good_eo_delta"
    assert str(ranked.iloc[0]["variant_id"]) == "slightly_lower_lift_good_eo_delta"


def test_select_champion_prefers_go_release_over_limited_go_variant():
    summary_df = pd.DataFrame(
        [
            {
                "variant_id": "limited_go_high_lift",
                "release_decision": "LIMITED_GO",
                "mean_denied_to_approved_lift": 0.16,
                "mean_denied_high_risk_lift": 0.08,
                "mean_high_risk_reachability_rate": 0.24,
                "mean_fairness_approval_gap_after": 0.05,
                "mean_latency_p95_ms": 300.0,
                "mean_latency_p99_ms": 900.0,
                "mean_error_rate": 0.0,
            },
            {
                "variant_id": "go_lower_lift",
                "release_decision": "GO",
                "mean_denied_to_approved_lift": 0.14,
                "mean_denied_high_risk_lift": 0.06,
                "mean_high_risk_reachability_rate": 0.21,
                "mean_fairness_approval_gap_after": 0.05,
                "mean_latency_p95_ms": 310.0,
                "mean_latency_p99_ms": 910.0,
                "mean_error_rate": 0.0,
            },
        ]
    )
    thresholds = {
        "min_denied_to_approved_lift": 0.09,
        "min_denied_high_risk_lift": 0.03,
        "max_fairness_gap": 0.10,
        "max_p95_latency_ms": 500.0,
        "max_p99_latency_ms": 2000.0,
        "max_error_rate": 0.005,
    }

    champion, ranked = _select_champion(summary_df, thresholds)
    assert champion == "go_lower_lift"
    assert bool(ranked.iloc[0]["_promotion_eligible"]) is True
    assert bool(ranked.iloc[1]["_promotion_eligible"]) is False
