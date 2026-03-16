from __future__ import annotations

import pandas as pd

from credit_coach.cli.run_model_challenger_matrix import (
    _aggregate_variant_metrics,
    _build_challenger_behavior_aware_summary,
    _build_challenger_candidate_source_breakdown,
    _build_challenger_impact_summary,
    _build_challenger_trajectory_summary,
    _build_variant_model_cfg,
    _build_variant_release_payloads,
    _select_champion,
)
from credit_coach.ops.kpi_contract import build_release_evidence_pack


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


def test_aggregate_variant_metrics_carries_candidate_quality_means():
    runs_df = pd.DataFrame(
        [
            {
                "variant_id": "control",
                "candidate_pool_diversity_index": 0.40,
                "candidate_source_entropy": 0.20,
                "high_risk_profile_applied_rate": 0.06,
                "best_source_internal_rate": 0.50,
                "best_source_dice_rate": 0.30,
                "best_source_rule_rate": 0.10,
                "best_source_fallback_rate": 0.10,
                "mean_plan_execution_probability": 0.40,
                "expected_pd_improvement": 0.03,
                "partial_execution_rate": 0.55,
                "failed_execution_rate": 0.15,
                "mixed_execution_rate": 0.40,
                "expected_partial_progress_rate": 0.22,
                "trajectory_soft_regression_penalty_mean": 0.08,
                "trajectory_on_track_rate": 0.62,
                "trajectory_needs_replan_rate": 0.24,
                "trajectory_degraded_rate": 0.14,
                "trajectory_stabilize_first_rate": 0.50,
            },
            {
                "variant_id": "control",
                "candidate_pool_diversity_index": 0.60,
                "candidate_source_entropy": 0.40,
                "high_risk_profile_applied_rate": 0.08,
                "best_source_internal_rate": 0.30,
                "best_source_dice_rate": 0.50,
                "best_source_rule_rate": 0.10,
                "best_source_fallback_rate": 0.10,
                "mean_plan_execution_probability": 0.60,
                "expected_pd_improvement": 0.05,
                "partial_execution_rate": 0.35,
                "failed_execution_rate": 0.05,
                "mixed_execution_rate": 0.30,
                "expected_partial_progress_rate": 0.28,
                "trajectory_soft_regression_penalty_mean": 0.12,
                "trajectory_on_track_rate": 0.58,
                "trajectory_needs_replan_rate": 0.28,
                "trajectory_degraded_rate": 0.16,
                "trajectory_stabilize_first_rate": 0.46,
            },
        ]
    )

    summary = _aggregate_variant_metrics(runs_df)
    assert float(summary.iloc[0]["mean_candidate_pool_diversity_index"]) == 0.5
    assert float(summary.iloc[0]["mean_candidate_source_entropy"]) == 0.3
    assert float(summary.iloc[0]["mean_high_risk_profile_applied_rate"]) == 0.07
    assert float(summary.iloc[0]["mean_best_source_dice_rate"]) == 0.4
    assert float(summary.iloc[0]["mean_plan_execution_probability"]) == 0.5
    assert float(summary.iloc[0]["mean_expected_pd_improvement"]) == 0.04
    assert float(summary.iloc[0]["mean_trajectory_soft_regression_penalty_mean"]) == 0.1
    assert float(summary.iloc[0]["mean_trajectory_on_track_rate"]) == 0.6


def test_build_challenger_behavior_aware_summary_exposes_champion_metrics():
    ranked_summary_df = pd.DataFrame(
        [
            {
                "variant_id": "challenger",
                "seed_count": 5,
                "mean_plan_execution_probability": 0.62,
                "mean_expected_pd_improvement": 0.041,
                "mean_partial_execution_rate": 0.36,
                "mean_failed_execution_rate": 0.08,
                "mean_mixed_execution_rate": 0.28,
                "mean_expected_partial_progress_rate": 0.44,
                "evidence_status": "complete",
            }
        ]
    )
    runs_df = pd.DataFrame([{"variant_id": "challenger", "seed": 42}])

    summary = _build_challenger_behavior_aware_summary(ranked_summary_df, runs_df)

    assert summary["champion_variant"] == "challenger"
    assert summary["champion_summary"]["mean_plan_execution_probability"] == 0.62
    assert summary["champion_summary"]["failed_execution_rate"] == 0.08
    assert "execution_probability_breakdown_csv" in summary["supporting_artifacts"]


def test_build_challenger_trajectory_summary_exposes_champion_metrics() -> None:
    ranked_summary_df = pd.DataFrame(
        [
            {
                "variant_id": "challenger",
                "seed_count": 5,
                "mean_trajectory_gate_pass_rate_4w": 0.18,
                "mean_trajectory_gate_pass_rate_12w": 0.24,
                "mean_trajectory_gate_pass_rate_24w": 0.31,
                "mean_trajectory_partial_progress_rate": 0.38,
                "mean_trajectory_median_time_to_gate_pass_days": 63.0,
                "mean_trajectory_soft_regression_penalty_mean": 0.07,
                "mean_trajectory_on_track_rate": 0.61,
                "mean_trajectory_needs_replan_rate": 0.23,
                "mean_trajectory_degraded_rate": 0.16,
                "mean_trajectory_stabilize_first_rate": 0.54,
                "mean_trajectory_balanced_progress_rate": 0.31,
                "mean_trajectory_long_horizon_heavy_rate": 0.15,
                "evidence_status": "complete",
            }
        ]
    )
    runs_df = pd.DataFrame(
        [
            {
                "variant_id": "challenger",
                "seed": 42,
                "trajectory_dominant_transition_reason": "phase_1_checkpoint_missed",
            }
        ]
    )

    summary = _build_challenger_trajectory_summary(ranked_summary_df, runs_df)

    assert summary["champion_variant"] == "challenger"
    assert summary["champion_summary"]["trajectory_gate_pass_rate_4w"] == 0.18
    assert summary["champion_summary"]["trajectory_stabilize_first_rate"] == 0.54
    assert summary["champion_summary"]["dominant_transition_reason"] == "phase_1_checkpoint_missed"
    assert "trajectory_transition_breakdown_csv" in summary["supporting_artifacts"]


def test_build_challenger_candidate_source_breakdown_emits_variant_rollups():
    breakdown = _build_challenger_candidate_source_breakdown(
        [
            pd.DataFrame(
                [
                    {
                        "variant_id": "control",
                        "seed": 42,
                        "population": "denied",
                        "candidate_source": "internal",
                        "count": 6,
                        "share": 0.6,
                        "population_size": 10,
                    }
                ]
            ),
            pd.DataFrame(
                [
                    {
                        "variant_id": "control",
                        "seed": 43,
                        "population": "denied",
                        "candidate_source": "internal",
                        "count": 4,
                        "share": 0.4,
                        "population_size": 10,
                    }
                ]
            ),
        ]
    )

    assert set(breakdown["breakdown_type"]) == {
        "variant_seed_population_source",
        "variant_population_source_rollup",
    }
    rollup = breakdown[
        (breakdown["breakdown_type"] == "variant_population_source_rollup")
        & (breakdown["variant_id"] == "control")
        & (breakdown["population"] == "denied")
        & (breakdown["candidate_source"] == "internal")
    ]
    assert int(rollup.iloc[0]["count"]) == 10
    assert float(rollup.iloc[0]["share"]) == 0.5


def test_build_challenger_impact_summary_uses_control_baseline_with_strong_confidence():
    ranked_summary_df = pd.DataFrame(
        [
            {
                "variant_id": "challenger",
                "seed_count": 5,
                "evidence_level": "seeded_challenger",
                "evidence_status": "complete",
                "release_decision": "GO",
                "acceptance_status": "ACCEPTED",
                "mean_denied_to_approved_lift": 0.14,
                "mean_denied_high_risk_lift": 0.06,
                "mean_denied_reliability_violation_rate": 0.15,
                "mean_fairness_equalized_odds_gap_delta": 0.003,
                "mean_high_risk_reachability_rate": 0.25,
                "mean_trajectory_partial_progress_rate": 0.29,
                "mean_candidate_source_entropy": 0.36,
                "mean_best_source_internal_rate": 0.35,
                "mean_best_source_dice_rate": 0.50,
                "mean_best_source_rule_rate": 0.10,
                "mean_best_source_fallback_rate": 0.05,
            },
            {
                "variant_id": "control_logistic_isotonic",
                "seed_count": 5,
                "evidence_level": "seeded_challenger",
                "evidence_status": "complete",
                "release_decision": "GO",
                "acceptance_status": "ACCEPTED",
                "mean_denied_to_approved_lift": 0.10,
                "mean_denied_high_risk_lift": 0.04,
                "mean_denied_reliability_violation_rate": 0.20,
                "mean_fairness_equalized_odds_gap_delta": 0.006,
                "mean_high_risk_reachability_rate": 0.20,
                "mean_trajectory_partial_progress_rate": 0.24,
                "mean_candidate_source_entropy": 0.30,
                "mean_best_source_internal_rate": 0.55,
                "mean_best_source_dice_rate": 0.25,
                "mean_best_source_rule_rate": 0.10,
                "mean_best_source_fallback_rate": 0.10,
            },
        ]
    )
    runs_df = pd.DataFrame(
        [
            {
                "variant_id": "control_logistic_isotonic",
                "seed": 42,
                "denied_to_approved_lift": 0.09,
                "denied_high_risk_lift": 0.03,
                "fairness_equalized_odds_gap_delta": 0.006,
                "denied_reliability_violation_rate": 0.22,
                "high_risk_reachability_rate": 0.19,
                "trajectory_partial_progress_rate": 0.23,
                "candidate_source_entropy": 0.29,
            },
            {
                "variant_id": "control_logistic_isotonic",
                "seed": 43,
                "denied_to_approved_lift": 0.11,
                "denied_high_risk_lift": 0.05,
                "fairness_equalized_odds_gap_delta": 0.006,
                "denied_reliability_violation_rate": 0.18,
                "high_risk_reachability_rate": 0.21,
                "trajectory_partial_progress_rate": 0.25,
                "candidate_source_entropy": 0.31,
            },
            {
                "variant_id": "challenger",
                "seed": 42,
                "denied_to_approved_lift": 0.13,
                "denied_high_risk_lift": 0.05,
                "fairness_equalized_odds_gap_delta": 0.004,
                "denied_reliability_violation_rate": 0.17,
                "high_risk_reachability_rate": 0.24,
                "trajectory_partial_progress_rate": 0.28,
                "candidate_source_entropy": 0.35,
            },
            {
                "variant_id": "challenger",
                "seed": 43,
                "denied_to_approved_lift": 0.15,
                "denied_high_risk_lift": 0.07,
                "fairness_equalized_odds_gap_delta": 0.002,
                "denied_reliability_violation_rate": 0.13,
                "high_risk_reachability_rate": 0.26,
                "trajectory_partial_progress_rate": 0.30,
                "candidate_source_entropy": 0.37,
            },
        ]
    )

    summary = _build_challenger_impact_summary(
        ranked_summary_df,
        runs_df,
        control_variant="control_logistic_isotonic",
        champion_variant="challenger",
    )

    champion = summary["champion_summary"]
    assert champion["comparative_impact_confidence"] == "strong"
    assert champion["primary_axes"]["denied_high_risk_lift"]["label"] == "helped"
    assert champion["primary_axes"]["denied_reliability_violation_rate"]["label"] == "helped"
    assert champion["source_mix_deltas"]["best_source_dice_rate"] == 0.25


def test_challenger_release_evidence_snapshot_uses_tables_relative_paths():
    snapshot = build_release_evidence_pack(
        runner_type="challenger",
        release_decision="GO",
        acceptance_status="ACCEPTED",
        evidence_level="seeded_challenger",
        evidence_status="complete",
        acceptance_eligible=True,
        required_artifacts={
            "kpi_contract_snapshot_json": "tables/kpi_contract_snapshot.json",
            "challenger_matrix_decision_json": "tables/challenger_matrix_decision.json",
        },
        optional_artifacts={
            "challenger_matrix_variant_summary_csv": "tables/challenger_matrix_variant_summary.csv",
        },
        existing_artifacts=[
            "tables/kpi_contract_snapshot.json",
            "tables/challenger_matrix_decision.json",
            "tables/challenger_matrix_variant_summary.csv",
        ],
    )

    assert snapshot["pack_status"] == "complete"
    assert snapshot["pack_acceptance_eligible"] is True
    assert snapshot["required_artifacts"]["kpi_contract_snapshot_json"].startswith("tables/")


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


def test_build_variant_release_payloads_marks_single_seed_evidence_degraded() -> None:
    runs_df = pd.DataFrame(
        [
            {
                "variant_id": "single_seed_variant",
                "seed": 42,
                "model_version": "model-123",
                "model_freeze_mode": "explicit_model_version",
                "denied_count": 100.0,
                "denied_with_gate_pass_plan": 10.0,
                "denied_to_approved_lift": 0.12,
                "denied_high_risk_lift": 0.05,
                "denied_reliability_violation_rate": 0.20,
                "latency_p95_ms": 300.0,
                "latency_p99_ms": 900.0,
                "error_rate": 0.0,
                "fairness_approval_gap_after": 0.05,
                "fairness_approval_gap_delta": 0.005,
                "fairness_equalized_odds_gap_delta": 0.005,
                "high_stress_approval_gap_after": 0.05,
                "recourse_success_gap": 0.05,
                "trajectory_gate_pass_rate_4w": 0.04,
                "trajectory_gate_pass_rate_12w": 0.08,
                "trajectory_gate_pass_rate_24w": 0.10,
                "trajectory_partial_progress_rate": 0.25,
                "trajectory_median_time_to_gate_pass_days": 90.0,
            }
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

    release_df = _build_variant_release_payloads(runs_df, thresholds=thresholds, breakdown_frames=[])
    row = release_df.iloc[0]
    assert str(row["evidence_level"]) == "single_run_fallback"
    assert bool(row["acceptance_eligible"]) is False
    assert bool(row["promotion_eligible"]) is False
    assert str(row["degraded_reason"]) == "insufficient_repeated_seeded_evidence"


def test_select_champion_prefers_acceptance_eligible_go_over_degraded_go() -> None:
    summary_df = pd.DataFrame(
        [
            {
                "variant_id": "degraded_go_high_lift",
                "release_decision": "GO",
                "acceptance_eligible": False,
                "promotion_eligible": False,
                "mean_denied_to_approved_lift": 0.18,
                "mean_denied_high_risk_lift": 0.09,
                "mean_high_risk_reachability_rate": 0.26,
                "mean_fairness_approval_gap_after": 0.04,
                "mean_latency_p95_ms": 280.0,
                "mean_latency_p99_ms": 850.0,
                "mean_error_rate": 0.0,
            },
            {
                "variant_id": "acceptance_eligible_go",
                "release_decision": "GO",
                "acceptance_eligible": True,
                "promotion_eligible": True,
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
    assert champion == "acceptance_eligible_go"
    assert bool(ranked.iloc[0]["_promotion_eligible"]) is True
    assert bool(ranked.iloc[1]["_promotion_eligible"]) is False
