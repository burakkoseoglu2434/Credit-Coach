from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from credit_coach.cli.run_phase_experiment_suite import (
    _build_phase_behavior_aware_summary,
    _build_phase_candidate_quality_summary,
    _build_phase_candidate_source_breakdown,
    _build_phase_decision_logging_summary,
    _build_phase_fairness_breakdown,
    _build_phase_high_risk_tuning_summary,
    _build_phase_portfolio_validation_review,
    _build_phase_portfolio_validation_summary,
    _build_learning_loop_summary,
    _build_phase_offer_optimization_summary,
    _build_phase_trajectory_policy_label_breakdown,
    _build_phase_trajectory_summary,
    _build_phase_trajectory_transition_breakdown,
    _build_suite_impact_attribution_summary,
    _kpi_checks,
    _render_release_review_summary,
    _seed_contract_snapshot,
    _train_cmd,
)
from credit_coach.ops.kpi_contract import (
    LIFT_KPI_THRESHOLD_KEYS,
    RELIABILITY_KPI_THRESHOLD_KEYS,
    build_release_evidence_pack,
    evaluate_kpi_checks,
    list_failed_kpi_checks,
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


def test_shared_kpi_checks_use_runner_stable_failed_check_names() -> None:
    metrics = {
        "denied_to_approved_lift": 0.02,
        "denied_high_risk_lift": 0.01,
        "denied_gate_pass_rate": 0.02,
        "denied_reliability_violation_rate": 0.80,
        "latency_p95_ms": 900.0,
        "latency_p99_ms": 3000.0,
        "error_rate": 0.02,
        "trajectory_gate_pass_rate_4w": 0.0,
        "trajectory_gate_pass_rate_12w": 0.01,
        "trajectory_gate_pass_rate_24w": 0.01,
        "trajectory_partial_progress_rate": 0.05,
        "trajectory_median_time_to_gate_pass_days": 400.0,
    }
    evaluations = evaluate_kpi_checks(
        metrics,
        _thresholds(),
        threshold_keys=(*LIFT_KPI_THRESHOLD_KEYS, *RELIABILITY_KPI_THRESHOLD_KEYS),
    )
    failed = list_failed_kpi_checks(evaluations)
    assert failed[:3] == [
        "denied_to_approved_lift",
        "denied_high_risk_lift",
        "denied_gate_pass_rate",
    ]
    assert "trajectory_median_time_to_gate_pass_days" in failed


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


def test_release_review_summary_is_derived_from_acceptance_summary() -> None:
    review = _render_release_review_summary(
        milestone_acceptance_summary={
            "acceptance_status": "PILOT_ONLY",
            "release_decision": "LIMITED_GO",
            "acceptance_eligible": True,
            "broad_rollout_allowed": False,
            "evidence_level": "seeded_suite",
            "lift_pass": True,
            "reliability_pass": True,
            "fairness_seed_pass_count": 4,
            "seed_count": 5,
            "primary_fairness_metric": "equalized_odds_gap_delta",
            "worst_primary_fairness_gap": 0.012,
            "phase": "phase-09",
            "milestone": "v1.1",
            "runner_type": "suite",
            "model_version": "model-123",
            "model_freeze_mode": "explicit_model_version",
            "dominant_fail_segment_key": "mid|q1|stress",
            "dominant_fail_candidate_source": "internal",
            "supporting_artifacts": {"release_decision_json": "tables/release_decision.json"},
            "telemetry_gate_status": "degraded",
            "telemetry_failure_reason": "missing_artifact",
            "telemetry_success_rate": 0.0,
            "telemetry_ingest_lag_s": 0.0,
            "release_pack_summary": {
                "pack_status": "degraded",
                "pack_acceptance_eligible": False,
                "required_artifacts": {
                    "telemetry_export_json": "tables/telemetry_export.json",
                    "milestone_acceptance_summary_json": "tables/milestone_acceptance_summary.json",
                },
                "optional_artifacts": {
                    "release_decision_json": "tables/release_decision.json",
                },
                "missing_artifacts": ["tables/telemetry_export.json"],
            },
            "outcome_feedback_summary": {
                "comparison_status": "baseline_missing",
                "outcome_feedback_confidence": "tentative",
                "best_proxy_improving_arm": {},
                "worst_proxy_regressing_arm": {},
                "approval_rate_delta": 0.0,
                "default_rate_90d_delta": 0.0,
                "avg_margin_90d_delta": 0.0,
            },
            "learning_loop_summary": {
                "decision_log_completeness": 0.95,
                "learning_readiness_status_distribution": {
                    "descriptive_only": {"count": 5, "share": 0.1},
                    "partial_learning_ready": {"count": 10, "share": 0.2},
                    "learning_ready": {"count": 35, "share": 0.7},
                },
                "reward_90d_coverage": 0.7,
                "ope_confidence": "strong",
                "comparison_status": "treatment_vs_control",
                "preferred_policy_signal": {
                    "policy_arm": "treatment",
                    "signal": "supports_treatment",
                },
                "preferred_policy_metric_labels": {
                    "approval_rate": "supports_treatment",
                    "default_rate_90d": "supports_treatment",
                    "avg_margin_90d": "mixed",
                },
            },
            "offer_optimization_summary": {
                "canonical_metrics": {
                    "offer_plan_rate": 0.42,
                    "rankable_offer_rate": 0.28,
                    "offer_acceptance_probability_mean": 0.53,
                    "combined_plan_realization_probability_mean": 0.31,
                    "expected_recovery_proxy": 4.1,
                    "approval_rate_proxy_delta": 0.02,
                    "default_rate_90d_proxy_delta": -0.01,
                    "avg_margin_90d_proxy_delta": 18.0,
                    "governance_safe_offer_rate": 0.24,
                    "dominant_offer_type": "installment_terms",
                }
            },
            "trajectory_summary": {
                "primary_checkpoint_week": 4,
                "canonical_metrics": {
                    "trajectory_gate_pass_rate_4w": 0.12,
                    "trajectory_gate_pass_rate_12w": 0.18,
                    "trajectory_gate_pass_rate_24w": 0.22,
                    "trajectory_partial_progress_rate": 0.31,
                    "trajectory_soft_regression_penalty_mean": 0.05,
                    "trajectory_on_track_rate": 0.66,
                    "trajectory_needs_replan_rate": 0.20,
                    "trajectory_degraded_rate": 0.14,
                },
                "dominant_transition_reason": "phase_1_checkpoint_missed",
            },
        }
    )
    assert "PILOT_ONLY" in review
    assert "LIMITED_GO" in review
    assert "Evidence Status: degraded" in review
    assert "Telemetry Readiness" in review
    assert "Release Pack Completeness" in review
    assert "Outcome Feedback Summary" in review
    assert "Learning Loop Summary" in review
    assert "Offer Optimization Summary" in review
    assert "Trajectory Summary" in review
    assert "installment_terms" in review
    assert "phase_1_checkpoint_missed" in review
    assert "supports_treatment" in review
    assert "release_decision_json" in review


def test_release_evidence_pack_marks_missing_required_telemetry_artifact() -> None:
    pack = build_release_evidence_pack(
        runner_type="suite",
        phase="phase-11",
        milestone="v1.1",
        release_decision="LIMITED_GO",
        acceptance_status="PILOT_ONLY",
        evidence_level="seeded_suite",
        evidence_status="complete",
        acceptance_eligible=True,
        required_artifacts={
            "kpi_contract_snapshot_json": "tables/kpi_contract_snapshot.json",
            "milestone_acceptance_summary_json": "tables/milestone_acceptance_summary.json",
            "telemetry_export_json": "tables/telemetry_export.json",
        },
        optional_artifacts={
            "release_decision_json": "tables/release_decision.json",
        },
        existing_artifacts=[
            "tables/kpi_contract_snapshot.json",
            "tables/milestone_acceptance_summary.json",
            "tables/release_decision.json",
        ],
    )

    assert pack["pack_status"] == "degraded"
    assert pack["pack_acceptance_eligible"] is False
    assert "tables/telemetry_export.json" in pack["missing_artifacts"]
    assert pack["required_artifacts"]["telemetry_export_json"] == "tables/telemetry_export.json"


def test_build_phase_candidate_quality_summary_uses_locked_population_contract() -> None:
    scale_df = pd.DataFrame(
        [
            {
                "candidate_quality_population": "denied",
                "candidate_quality_secondary_population": "high_risk_denied",
                "candidate_pool_diversity_index": 0.40,
                "candidate_source_entropy": 0.20,
                "best_source_internal_rate": 0.50,
                "best_source_dice_rate": 0.30,
                "best_source_rule_rate": 0.20,
                "best_source_fallback_rate": 0.00,
                "high_risk_denied_candidate_pool_diversity_index": 0.25,
                "high_risk_denied_candidate_source_entropy": 0.10,
                "high_risk_denied_best_source_internal_rate": 0.60,
                "high_risk_denied_best_source_dice_rate": 0.40,
                "high_risk_denied_best_source_rule_rate": 0.00,
                "high_risk_denied_best_source_fallback_rate": 0.00,
            },
            {
                "candidate_quality_population": "denied",
                "candidate_quality_secondary_population": "high_risk_denied",
                "candidate_pool_diversity_index": 0.60,
                "candidate_source_entropy": 0.40,
                "best_source_internal_rate": 0.40,
                "best_source_dice_rate": 0.40,
                "best_source_rule_rate": 0.10,
                "best_source_fallback_rate": 0.10,
                "high_risk_denied_candidate_pool_diversity_index": 0.35,
                "high_risk_denied_candidate_source_entropy": 0.20,
                "high_risk_denied_best_source_internal_rate": 0.50,
                "high_risk_denied_best_source_dice_rate": 0.30,
                "high_risk_denied_best_source_rule_rate": 0.10,
                "high_risk_denied_best_source_fallback_rate": 0.10,
            },
        ]
    )

    summary = _build_phase_candidate_quality_summary(scale_df)

    assert summary["candidate_quality_population"] == "denied"
    assert summary["candidate_quality_secondary_population"] == "high_risk_denied"
    assert summary["canonical_metrics"]["candidate_pool_diversity_index"] == 0.5
    assert summary["canonical_metrics"]["best_source_internal_rate"] == 0.45
    assert summary["secondary_metrics"]["candidate_pool_diversity_index"] == 0.30
    assert summary["secondary_metrics"]["best_source_dice_rate"] == 0.35


def test_build_phase_behavior_aware_summary_uses_locked_population_contract() -> None:
    scale_df = pd.DataFrame(
        [
            {
                "mean_plan_execution_probability": 0.60,
                "expected_pd_improvement": 0.05,
                "partial_execution_rate": 0.40,
                "failed_execution_rate": 0.10,
                "mixed_execution_rate": 0.30,
                "expected_partial_progress_rate": 0.50,
                "high_risk_denied_mean_plan_execution_probability": 0.55,
                "high_risk_denied_expected_pd_improvement": 0.04,
                "high_risk_denied_partial_execution_rate": 0.45,
                "high_risk_denied_failed_execution_rate": 0.15,
                "high_risk_denied_mixed_execution_rate": 0.30,
                "high_risk_denied_expected_partial_progress_rate": 0.40,
            },
            {
                "mean_plan_execution_probability": 0.40,
                "expected_pd_improvement": 0.03,
                "partial_execution_rate": 0.60,
                "failed_execution_rate": 0.20,
                "mixed_execution_rate": 0.40,
                "expected_partial_progress_rate": 0.30,
                "high_risk_denied_mean_plan_execution_probability": 0.35,
                "high_risk_denied_expected_pd_improvement": 0.02,
                "high_risk_denied_partial_execution_rate": 0.65,
                "high_risk_denied_failed_execution_rate": 0.25,
                "high_risk_denied_mixed_execution_rate": 0.40,
                "high_risk_denied_expected_partial_progress_rate": 0.20,
            },
        ]
    )

    summary = _build_phase_behavior_aware_summary(scale_df)

    assert summary["canonical_population"] == "denied"
    assert summary["secondary_population"] == "high_risk_denied"
    assert summary["canonical_metrics"]["mean_plan_execution_probability"] == 0.5
    assert summary["canonical_metrics"]["mixed_execution_rate"] == 0.35
    assert summary["secondary_metrics"]["mean_plan_execution_probability"] == 0.45
    assert "partial_execution_breakdown_csv" in summary["supporting_artifacts"]


def test_build_phase_offer_optimization_summary_uses_locked_contract() -> None:
    scale_df = pd.DataFrame(
        [
            {
                "offer_plan_rate": 0.40,
                "rankable_offer_rate": 0.30,
                "offer_acceptance_probability_mean": 0.55,
                "combined_plan_realization_probability_mean": 0.28,
                "expected_recovery_proxy": 3.8,
                "approval_rate_proxy_delta": 0.02,
                "default_rate_90d_proxy_delta": -0.01,
                "avg_margin_90d_proxy_delta": 14.0,
                "governance_safe_offer_rate": 0.20,
                "dominant_offer_type": "installment_terms",
            },
            {
                "offer_plan_rate": 0.60,
                "rankable_offer_rate": 0.50,
                "offer_acceptance_probability_mean": 0.45,
                "combined_plan_realization_probability_mean": 0.25,
                "expected_recovery_proxy": 4.2,
                "approval_rate_proxy_delta": 0.03,
                "default_rate_90d_proxy_delta": -0.015,
                "avg_margin_90d_proxy_delta": 16.0,
                "governance_safe_offer_rate": 0.30,
                "dominant_offer_type": "installment_terms",
            },
        ]
    )

    summary = _build_phase_offer_optimization_summary(scale_df)

    assert summary["canonical_population"] == "denied"
    assert summary["seed_count"] == 2
    assert summary["canonical_metrics"]["offer_plan_rate"] == 0.5
    assert summary["canonical_metrics"]["dominant_offer_type"] == "installment_terms"
    assert "offer_acceptance_breakdown_csv" in summary["supporting_artifacts"]


def test_build_phase_trajectory_summary_uses_locked_checkpoint_contract() -> None:
    scale_df = pd.DataFrame(
        [
            {
                "trajectory_gate_pass_rate_4w": 0.20,
                "trajectory_gate_pass_rate_12w": 0.25,
                "trajectory_gate_pass_rate_24w": 0.30,
                "trajectory_partial_progress_rate": 0.40,
                "trajectory_median_time_to_gate_pass_days": 56.0,
                "trajectory_soft_regression_penalty_mean": 0.08,
                "trajectory_on_track_rate": 0.70,
                "trajectory_needs_replan_rate": 0.20,
                "trajectory_degraded_rate": 0.10,
                "trajectory_stabilize_first_rate": 0.50,
                "trajectory_balanced_progress_rate": 0.35,
                "trajectory_long_horizon_heavy_rate": 0.15,
                "high_risk_denied_trajectory_gate_pass_rate_4w": 0.12,
                "high_risk_denied_trajectory_gate_pass_rate_12w": 0.16,
                "high_risk_denied_trajectory_gate_pass_rate_24w": 0.18,
                "high_risk_denied_trajectory_partial_progress_rate": 0.24,
                "high_risk_denied_trajectory_median_time_to_gate_pass_days": 70.0,
                "high_risk_denied_trajectory_soft_regression_penalty_mean": 0.10,
                "high_risk_denied_trajectory_on_track_rate": 0.55,
                "high_risk_denied_trajectory_needs_replan_rate": 0.30,
                "high_risk_denied_trajectory_degraded_rate": 0.15,
                "trajectory_dominant_transition_reason": "phase_1_checkpoint_missed",
            },
            {
                "trajectory_gate_pass_rate_4w": 0.10,
                "trajectory_gate_pass_rate_12w": 0.15,
                "trajectory_gate_pass_rate_24w": 0.20,
                "trajectory_partial_progress_rate": 0.30,
                "trajectory_median_time_to_gate_pass_days": 84.0,
                "trajectory_soft_regression_penalty_mean": 0.12,
                "trajectory_on_track_rate": 0.60,
                "trajectory_needs_replan_rate": 0.25,
                "trajectory_degraded_rate": 0.15,
                "trajectory_stabilize_first_rate": 0.45,
                "trajectory_balanced_progress_rate": 0.30,
                "trajectory_long_horizon_heavy_rate": 0.25,
                "high_risk_denied_trajectory_gate_pass_rate_4w": 0.08,
                "high_risk_denied_trajectory_gate_pass_rate_12w": 0.12,
                "high_risk_denied_trajectory_gate_pass_rate_24w": 0.16,
                "high_risk_denied_trajectory_partial_progress_rate": 0.20,
                "high_risk_denied_trajectory_median_time_to_gate_pass_days": 91.0,
                "high_risk_denied_trajectory_soft_regression_penalty_mean": 0.14,
                "high_risk_denied_trajectory_on_track_rate": 0.48,
                "high_risk_denied_trajectory_needs_replan_rate": 0.34,
                "high_risk_denied_trajectory_degraded_rate": 0.18,
                "trajectory_dominant_transition_reason": "phase_1_checkpoint_missed",
            },
        ]
    )

    summary = _build_phase_trajectory_summary(scale_df)

    assert summary["primary_checkpoint_week"] == 4
    assert summary["checkpoint_priority_order"] == [4, 12, 24]
    assert summary["canonical_metrics"]["trajectory_gate_pass_rate_4w"] == 0.15
    assert summary["canonical_metrics"]["trajectory_soft_regression_penalty_mean"] == 0.1
    assert summary["secondary_metrics"]["trajectory_on_track_rate"] == 0.515
    assert summary["dominant_transition_reason"] == "phase_1_checkpoint_missed"
    assert "trajectory_transition_breakdown_csv" in summary["supporting_artifacts"]


def test_build_phase_portfolio_validation_summary_uses_locked_phase17_contract() -> None:
    summary = _build_phase_portfolio_validation_summary(
        [
            {
                "population_sizes": {
                    "full_evaluation_population": 100,
                    "denied": 60,
                    "high_risk_denied": 20,
                },
                "canonical_metrics": {
                    "raw_plan_coverage": 0.8,
                    "valid_plan_coverage": 0.6,
                    "governance_safe_plan_coverage": 0.5,
                    "product_ready_plan_coverage": 0.4,
                    "no_plan_rate": 0.2,
                    "reality_gap_flag_rate": 0.15,
                },
                "secondary_metrics": {
                    "raw_plan_coverage": 0.7,
                    "valid_plan_coverage": 0.5,
                },
                "reality_gap_summary": {
                    "reality_gap_flag_rate": 0.15,
                    "dominant_reality_gap_reason": "engine_native_action_flag",
                    "product_ready_drop_due_to_reality_gap": 0.25,
                    "multi_flag_exposure": 0.08,
                    "severity_split": {"mild": 0.05, "moderate": 0.07, "severe": 0.03},
                },
                "strongest_segments": [
                    {"segment_label": "risk_band:near", "product_ready_plan_coverage": 0.5},
                ],
                "weakest_segments": [
                    {"segment_label": "stress_band:high", "product_ready_plan_coverage": 0.2},
                ],
                "highest_offer_needed_segment": {"segment_label": "offer_needed_segment:offer_needed"},
                "lowest_product_ready_segment": {"segment_label": "stress_band:high"},
                "segment_story": {
                    "where_engine_works": "risk_band:near",
                    "where_engine_struggles": "stress_band:high",
                    "where_offer_is_required": "offer_needed_segment:offer_needed",
                    "where_narrative_breaks": "recoverability_segment:hard_to_recover",
                },
                "demo_representativeness": {
                    "demo_representativeness_verdict": "representative",
                    "demo_fit_confidence": "strong",
                    "demo_case_segment": "risk_band=near|income_band=q1|stress_band=base|recoverability_segment=recoverable",
                    "segment_size": 24,
                    "demo_case_segment_share": 0.24,
                    "segment_product_ready_rate": 0.41,
                    "segment_offer_dependency": 0.18,
                    "product_ready_alignment": True,
                    "cohort_vs_demo_delta": {
                        "plan_execution_probability": 0.02,
                        "early_checkpoint_health_rate": 0.01,
                        "product_ready_rate": 0.03,
                    },
                    "narrative": "demo aligns with cohort",
                },
            },
            {
                "population_sizes": {
                    "full_evaluation_population": 120,
                    "denied": 70,
                    "high_risk_denied": 25,
                },
                "canonical_metrics": {
                    "raw_plan_coverage": 0.7,
                    "valid_plan_coverage": 0.5,
                    "governance_safe_plan_coverage": 0.4,
                    "product_ready_plan_coverage": 0.3,
                    "no_plan_rate": 0.3,
                    "reality_gap_flag_rate": 0.2,
                },
                "secondary_metrics": {
                    "raw_plan_coverage": 0.6,
                    "valid_plan_coverage": 0.4,
                },
                "reality_gap_summary": {
                    "reality_gap_flag_rate": 0.2,
                    "dominant_reality_gap_reason": "engine_native_action_flag",
                    "product_ready_drop_due_to_reality_gap": 0.35,
                    "multi_flag_exposure": 0.12,
                    "severity_split": {"mild": 0.06, "moderate": 0.08, "severe": 0.06},
                },
                "strongest_segments": [
                    {"segment_label": "risk_band:near", "product_ready_plan_coverage": 0.4},
                ],
                "weakest_segments": [
                    {"segment_label": "stress_band:high", "product_ready_plan_coverage": 0.1},
                ],
                "highest_offer_needed_segment": {"segment_label": "offer_needed_segment:offer_needed"},
                "lowest_product_ready_segment": {"segment_label": "stress_band:high"},
                "segment_story": {
                    "where_engine_works": "risk_band:near",
                    "where_engine_struggles": "stress_band:high",
                    "where_offer_is_required": "offer_needed_segment:offer_needed",
                    "where_narrative_breaks": "recoverability_segment:hard_to_recover",
                },
                "demo_representativeness": {
                    "demo_representativeness_verdict": "representative",
                    "demo_fit_confidence": "strong",
                    "demo_case_segment": "risk_band=near|income_band=q1|stress_band=base|recoverability_segment=recoverable",
                    "segment_size": 26,
                    "demo_case_segment_share": 0.26,
                    "segment_product_ready_rate": 0.39,
                    "segment_offer_dependency": 0.20,
                    "product_ready_alignment": True,
                    "cohort_vs_demo_delta": {
                        "plan_execution_probability": 0.01,
                        "early_checkpoint_health_rate": 0.02,
                        "product_ready_rate": 0.01,
                    },
                    "narrative": "demo aligns with cohort",
                },
            },
        ]
    )

    assert summary["seed_count"] == 2
    assert summary["canonical_population"] == "full_evaluation_population"
    assert summary["canonical_metrics"]["raw_plan_coverage"] == 0.75
    assert summary["canonical_metrics"]["product_ready_plan_coverage"] == 0.35
    assert summary["reality_gap_summary"]["dominant_reality_gap_reason"] == "engine_native_action_flag"
    assert summary["demo_representativeness"]["demo_representativeness_verdict"] == "representative"
    assert "portfolio_validation_summary_json" in summary["supporting_artifacts"]


def test_build_phase_portfolio_validation_review_stays_executive_facing() -> None:
    review = _build_phase_portfolio_validation_review(
        {
            "canonical_metrics": {
                "raw_plan_coverage": 0.82,
                "valid_plan_coverage": 0.58,
                "governance_safe_plan_coverage": 0.47,
                "product_ready_plan_coverage": 0.33,
                "no_plan_rate": 0.18,
            },
            "reality_gap_summary": {
                "reality_gap_flag_rate": 0.21,
                "dominant_reality_gap_reason": "engine_native_action_flag",
                "product_ready_drop_due_to_reality_gap": 0.29,
            },
            "strongest_segments": [{"segment_label": "risk_band:near", "product_ready_plan_coverage": 0.46}],
            "weakest_segments": [{"segment_label": "stress_band:high", "product_ready_plan_coverage": 0.11}],
            "segment_story": {
                "where_engine_works": "risk_band:near",
                "where_engine_struggles": "stress_band:high",
                "where_offer_is_required": "offer_needed_segment:offer_needed",
                "where_narrative_breaks": "recoverability_segment:hard_to_recover",
            },
            "demo_representativeness": {
                "demo_representativeness_verdict": "optimistic",
                "demo_fit_confidence": "moderate",
                "demo_case_segment_share": 0.14,
                "product_ready_alignment": False,
                "narrative": "demo overstates portfolio reality",
            },
        }
    )

    assert "Portfolio Validation Review" in review
    assert "Coverage Funnel" in review
    assert "Where engine works" in review
    assert "demo overstates portfolio reality" in review


def test_build_phase_candidate_source_breakdown_emits_seed_and_rollup_views() -> None:
    breakdown = _build_phase_candidate_source_breakdown(
        [
            pd.DataFrame(
                [
                    {
                        "seed": 42,
                        "population": "denied",
                        "candidate_source": "internal",
                        "count": 6,
                        "share": 0.6,
                        "population_size": 10,
                    },
                    {
                        "seed": 42,
                        "population": "high_risk_denied",
                        "candidate_source": "dice",
                        "count": 2,
                        "share": 0.4,
                        "population_size": 5,
                    },
                ]
            ),
            pd.DataFrame(
                [
                    {
                        "seed": 43,
                        "population": "denied",
                        "candidate_source": "internal",
                        "count": 5,
                        "share": 0.5,
                        "population_size": 10,
                    }
                ]
            ),
        ]
    )

    assert set(breakdown["breakdown_type"]) == {"seed_population_source", "population_source_rollup"}
    denied_rollup = breakdown[
        (breakdown["breakdown_type"] == "population_source_rollup")
        & (breakdown["population"] == "denied")
        & (breakdown["candidate_source"] == "internal")
    ]
    assert int(denied_rollup.iloc[0]["count"]) == 11
    assert float(denied_rollup.iloc[0]["share"]) == 0.55


def test_phase_trajectory_breakdowns_emit_seed_and_rollup_views() -> None:
    transition_breakdown = _build_phase_trajectory_transition_breakdown(
        [
            pd.DataFrame(
                [
                    {
                        "seed": 42,
                        "population": "denied",
                        "risk_band": "mid",
                        "trajectory_status": "needs_replan",
                        "current_phase": "phase_1_stabilize",
                        "phase_transition_reason": "phase_1_checkpoint_missed",
                        "count": 6,
                        "mean_next_review_week": 12.0,
                        "mean_soft_regression_penalty": 0.12,
                        "share": 0.30,
                    }
                ]
            )
        ]
    )
    policy_breakdown = _build_phase_trajectory_policy_label_breakdown(
        [
            pd.DataFrame(
                [
                    {
                        "seed": 42,
                        "population": "denied",
                        "risk_band": "mid",
                        "trajectory_policy_label": "stabilize_first",
                        "count": 8,
                        "mean_policy_score": 0.67,
                        "share": 0.40,
                    }
                ]
            )
        ]
    )

    assert set(transition_breakdown["breakdown_type"]) == {
        "seed_population_trajectory_transition",
        "population_trajectory_transition_rollup",
    }
    assert set(policy_breakdown["breakdown_type"]) == {
        "seed_population_trajectory_policy_label",
        "population_trajectory_policy_label_rollup",
    }


def test_build_phase_high_risk_tuning_summary_marks_low_activation_as_diagnostic() -> None:
    scale_df = pd.DataFrame(
        [
            {
                "denied_high_risk_lift": 0.04,
                "high_risk_profile_applied_rate": 0.01,
                "high_risk_reachability_rate": 0.10,
                "trajectory_partial_progress_rate": 0.15,
            },
            {
                "denied_high_risk_lift": -0.01,
                "high_risk_profile_applied_rate": 0.02,
                "high_risk_reachability_rate": 0.08,
                "trajectory_partial_progress_rate": 0.12,
            },
        ]
    )

    summary = _build_phase_high_risk_tuning_summary(scale_df, release_decision="NO_GO")

    assert summary["evidence_status"] == "diagnostic_only"
    assert "activation_below_min_floor" in summary["diagnostic_reasons"]
    assert "seed_direction_unstable" in summary["diagnostic_reasons"]
    assert "release_gate_not_satisfied" in summary["diagnostic_reasons"]


def test_build_suite_impact_attribution_summary_is_tentative_without_control_baseline() -> None:
    summary = _build_suite_impact_attribution_summary(
        phase_name="phase-10",
        aggregate={
            "mean_denied_to_approved_lift": 0.12,
            "mean_denied_high_risk_lift": 0.05,
            "mean_equalized_odds_gap_delta": 0.004,
            "mean_denied_reliability_violation_rate": 0.18,
            "mean_high_risk_reachability_rate": 0.20,
            "mean_trajectory_partial_progress_rate": 0.25,
            "mean_candidate_source_entropy": 0.33,
            "mean_best_source_internal_rate": 0.44,
            "mean_best_source_dice_rate": 0.36,
            "mean_best_source_rule_rate": 0.12,
            "mean_best_source_fallback_rate": 0.08,
        },
        evidence_level="seeded_suite",
        evidence_status="complete",
        seed_count=5,
    )

    assert summary["comparative_impact_confidence"] == "tentative"
    assert summary["diagnostic_only"] is True
    assert summary["diagnostic_reason"] == "control_variant_baseline_not_available_in_suite_runner"


def test_phase_decision_logging_summary_aggregates_weighted_coverage() -> None:
    summary = _build_phase_decision_logging_summary(
        [
            {
                "total_decisions": 10,
                "complete_decision_logs": 8,
                "decision_log_completeness": 0.8,
                "policy_metadata_coverage": 0.9,
                "selection_propensity_coverage": 1.0,
                "candidate_set_coverage": 0.8,
                "reason_code_coverage": 0.7,
                "recommended_plan_rate": 0.6,
                "propensity_source_breakdown": {"deterministic_fallback": 10},
            },
            {
                "total_decisions": 20,
                "complete_decision_logs": 10,
                "decision_log_completeness": 0.5,
                "policy_metadata_coverage": 0.6,
                "selection_propensity_coverage": 1.0,
                "candidate_set_coverage": 0.5,
                "reason_code_coverage": 0.4,
                "recommended_plan_rate": 0.3,
                "propensity_source_breakdown": {"deterministic_fallback": 20},
            },
        ]
    )

    assert summary["seed_count"] == 2
    assert summary["total_decisions"] == 30
    assert summary["complete_decision_logs"] == 18
    assert float(summary["decision_log_completeness"]) == 0.6
    assert summary["propensity_source_breakdown"]["deterministic_fallback"] == 30


def test_build_learning_loop_summary_surfaces_preferred_policy_metric_labels() -> None:
    summary = _build_learning_loop_summary(
        decision_logging_summary={"decision_log_completeness": 0.88, "total_decisions": 50, "complete_decision_logs": 44},
        outcome_ingestion_summary={
            "reward_90d_coverage": 0.72,
            "learning_readiness_status_distribution": {
                "descriptive_only": {"count": 5, "share": 0.1},
                "partial_learning_ready": {"count": 10, "share": 0.2},
                "learning_ready": {"count": 35, "share": 0.7},
            },
        },
        off_policy_evaluation={
            "ope_confidence": "strong",
            "comparison_status": "treatment_vs_control",
            "canonical_proxy_metrics": ["approval_rate", "default_rate_90d", "avg_margin_90d"],
            "preferred_policy_signal": {
                "policy_arm": "treatment",
                "signal": "supports_treatment",
                "ope_confidence": "strong",
            },
            "comparisons": [
                {
                    "policy_arm": "treatment",
                    "metric_labels": {
                        "approval_rate": "supports_treatment",
                        "default_rate_90d": "supports_treatment",
                        "avg_margin_90d": "mixed",
                    },
                }
            ],
        },
    )

    assert summary["decision_log_completeness"] == 0.88
    assert summary["reward_90d_coverage"] == 0.72
    assert summary["preferred_policy_signal"]["policy_arm"] == "treatment"
    assert summary["preferred_policy_metric_labels"]["approval_rate"] == "supports_treatment"
