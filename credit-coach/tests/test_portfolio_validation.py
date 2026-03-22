from __future__ import annotations

import json

import pandas as pd

from credit_coach.evaluation.portfolio_validation import (
    aggregate_portfolio_breakdown,
    aggregate_portfolio_validation_summaries,
    build_portfolio_validation_artifacts,
    build_product_confidence_snapshot,
    render_portfolio_validation_review,
)


def _semantic_phases_json() -> str:
    return json.dumps(
        [
            {
                "phase_id": "phase_1_stabilize",
                "phase_title": "Stabilize",
                "steps": [
                    {
                        "feature_name": "revol_util",
                        "action_key": "reduce_card_utilization",
                        "action_title": "Reduce card utilization",
                        "action_class": "behavioral",
                        "action_group_id": "reduce_card_utilization|phase_1_stabilize",
                        "primary_numeric_target": {
                            "metric_key": "credit_utilization_pct",
                            "unit": "percentage_points",
                            "current_value": 68.0,
                            "target_value": 45.0,
                            "delta_value": -23.0,
                            "due_month": 3,
                            "direction": "decrease",
                        },
                    }
                ],
            }
        ]
    )


def _engine_native_phases_json() -> str:
    return json.dumps(
        [
            {
                "phase_id": "phase_1_stabilize",
                "phase_title": "Stabilize",
                "steps": [
                    {
                        "feature_name": "last_fico_range_high",
                        "current_value": 610.0,
                        "target_value": 680.0,
                        "delta": 70.0,
                    }
                ],
            }
        ]
    )


def _offer_semantic_phases_json() -> str:
    return json.dumps(
        [
            {
                "phase_id": "phase_1_stabilize",
                "phase_title": "Stabilize",
                "steps": [
                    {
                        "feature_name": "installment",
                        "action_key": "accept_restructure_offer",
                        "action_title": "Accept restructure offer",
                        "action_class": "institutional",
                        "action_group_id": "accept_restructure_offer|phase_1_stabilize",
                        "primary_numeric_target": {
                            "metric_key": "monthly_payment_amount",
                            "unit": "currency",
                            "current_value": 1000.0,
                            "target_value": 500.0,
                            "delta_value": -500.0,
                            "due_month": 1,
                            "direction": "decrease",
                        },
                    }
                ],
            }
        ]
    )


def _checkpoint_json(*, pd_4w: float, pd_12w: float, pd_24w: float) -> str:
    return json.dumps(
        [
            {
                "week": 4,
                "month": 1,
                "phase_id": "phase_1_stabilize",
                "predicted_pd": pd_4w,
                "gate_pass_estimate": int(pd_4w <= 0.35),
            },
            {
                "week": 12,
                "month": 3,
                "phase_id": "phase_2_build",
                "predicted_pd": pd_12w,
                "gate_pass_estimate": int(pd_12w <= 0.35),
            },
            {
                "week": 24,
                "month": 6,
                "phase_id": "phase_3_optimize",
                "predicted_pd": pd_24w,
                "gate_pass_estimate": int(pd_24w <= 0.35),
            },
        ]
    )


def _base_row(customer_id: str) -> dict[str, object]:
    return {
        "customer_id": customer_id,
        "denied_base": 1,
        "risk_band": "near",
        "income_band": "q1",
        "stress_band": "base",
        "base_pd": 0.45,
        "had_any_candidate": 1,
        "candidate_pool_count": 3,
        "best_plan_id": f"{customer_id}_plan",
        "best_status": "APPROVED",
        "best_constraint_status": "valid",
        "best_action_count": 1,
        "best_cost_usd": 80.0,
        "best_plan_execution_probability": 0.80,
        "best_nominal_pd_improvement": 0.10,
        "best_expected_pd_improvement": 0.07,
        "best_offer_plan": 0,
        "best_rankable_offer": 0,
        "best_governance_safe_offer": 0,
        "best_offer_type": "",
        "best_offer_acceptance_probability": 0.0,
        "best_combined_plan_realization_probability": 0.0,
        "best_ci_high": 0.30,
        "best_reliability": 0.90,
        "best_worst_risk_margin": 0.05,
        "fairness_guard_demoted": 0,
        "trajectory_status": "on_track",
        "trajectory_policy_label": "stabilize_first",
        "trajectory_phase_transition_reason": "checkpoint_met",
        "trajectory_soft_regression_penalty": 0.0,
        "trajectory_pd_4w": 0.32,
        "trajectory_pd_12w": 0.28,
        "trajectory_pd_24w": 0.24,
        "trajectory_gate_pass_4w": 1,
        "trajectory_gate_pass_12w": 1,
        "trajectory_gate_pass_24w": 1,
        "best_phases_json": _semantic_phases_json(),
        "best_timeline_steps_json": "[]",
        "best_trajectory_checkpoints_json": _checkpoint_json(pd_4w=0.32, pd_12w=0.28, pd_24w=0.24),
        "action_realism_infeasible_plan_count": 0,
        "best_failed_execution": 0,
        "best_mixed_execution": 0,
    }


def test_build_portfolio_validation_artifacts_distinguishes_coverage_layers() -> None:
    rows = []
    ready_row = _base_row("ready")
    rows.append(ready_row)

    fairness_row = _base_row("fairness")
    fairness_row["fairness_guard_demoted"] = 1
    fairness_row["best_status"] = "NEEDS_REVIEW"
    rows.append(fairness_row)

    engine_native_row = _base_row("native")
    engine_native_row["best_phases_json"] = _engine_native_phases_json()
    engine_native_row["best_plan_execution_probability"] = 0.72
    rows.append(engine_native_row)

    invalid_row = _base_row("invalid")
    invalid_row["best_constraint_status"] = "invalid"
    invalid_row["best_status"] = "REJECTED"
    invalid_row["best_ci_high"] = 0.40
    rows.append(invalid_row)

    no_plan_row = _base_row("none")
    no_plan_row["had_any_candidate"] = 0
    no_plan_row["candidate_pool_count"] = 0
    no_plan_row["best_plan_id"] = ""
    no_plan_row["best_status"] = "ERROR"
    no_plan_row["best_constraint_status"] = "invalid"
    no_plan_row["best_action_count"] = 0
    no_plan_row["best_phases_json"] = "[]"
    no_plan_row["best_trajectory_checkpoints_json"] = "[]"
    rows.append(no_plan_row)

    artifacts = build_portfolio_validation_artifacts(
        pd.DataFrame(rows),
        tau=0.35,
        reliability_threshold_by_risk_band={"default": 0.7, "near": 0.7},
    )

    summary = artifacts["summary"]
    assert summary["canonical_population"] == "full_evaluation_population"
    assert summary["secondary_population"] == "denied"
    assert summary["canonical_metrics"]["raw_plan_coverage"] == 0.8
    assert summary["canonical_metrics"]["valid_plan_coverage"] == 0.6
    assert summary["canonical_metrics"]["governance_safe_plan_coverage"] == 0.4
    assert summary["canonical_metrics"]["product_ready_plan_coverage"] == 0.2
    assert summary["canonical_metrics"]["no_plan_rate"] == 0.2
    assert summary["reality_gap_summary"]["dominant_reality_gap_reason"] == "engine_native_action_flag"
    assert summary["product_proof"]["proof_verdict"] == "mixed"
    assert summary["product_proof"]["proof_confidence"] == "weak"
    assert summary["product_proof"]["phase17_delta"]["comparison_story"] == "mixed_change"

    coverage_breakdown = artifacts["coverage_breakdown"]
    assert coverage_breakdown["count"].tolist() == [4, 3, 2, 1]

    drop_breakdown = artifacts["coverage_drop_breakdown"]
    assert set(drop_breakdown["transition"]) == {
        "raw_to_valid",
        "valid_to_governance_safe",
        "governance_safe_to_product_ready",
    }
    assert "rejected" in set(drop_breakdown[drop_breakdown["transition"] == "raw_to_valid"]["reason"])
    assert "fairness" in set(drop_breakdown[drop_breakdown["transition"] == "valid_to_governance_safe"]["reason"])
    assert "action_not_interpretable" in set(
        drop_breakdown[drop_breakdown["transition"] == "governance_safe_to_product_ready"]["reason"]
    )


def test_build_portfolio_validation_artifacts_emits_numeric_impact_contract() -> None:
    behavioral_row = _base_row("numeric_behavioral")
    behavioral_row["risk_band"] = "near"
    behavioral_row["best_nominal_pd_improvement"] = 0.10
    behavioral_row["best_expected_pd_improvement"] = 0.08

    offer_row = _base_row("numeric_offer")
    offer_row["risk_band"] = "high"
    offer_row["trajectory_gate_pass_4w"] = 0
    offer_row["trajectory_gate_pass_12w"] = 1
    offer_row["trajectory_pd_4w"] = 0.39
    offer_row["trajectory_pd_12w"] = 0.31
    offer_row["trajectory_pd_24w"] = 0.27
    offer_row["best_trajectory_checkpoints_json"] = _checkpoint_json(pd_4w=0.39, pd_12w=0.31, pd_24w=0.27)
    offer_row["best_offer_plan"] = 1
    offer_row["best_rankable_offer"] = 1
    offer_row["best_governance_safe_offer"] = 1
    offer_row["best_offer_type"] = "restructure"
    offer_row["best_offer_acceptance_probability"] = 0.50
    offer_row["best_combined_plan_realization_probability"] = 0.30
    offer_row["best_nominal_pd_improvement"] = 0.12
    offer_row["best_expected_pd_improvement"] = 0.09
    offer_row["best_phases_json"] = _offer_semantic_phases_json()

    artifacts = build_portfolio_validation_artifacts(
        pd.DataFrame([behavioral_row, offer_row]),
        tau=0.35,
        reliability_threshold_by_risk_band={"default": 0.7, "near": 0.7, "high": 0.7},
    )

    summary = artifacts["summary"]
    canonical_metrics = summary["canonical_metrics"]
    numeric_impact = summary["numeric_impact"]

    assert canonical_metrics["numeric_plan_coverage"] == 1.0
    assert canonical_metrics["requested_change_burden"] == 0.633333
    assert canonical_metrics["nominal_portfolio_payoff"] == 0.11
    assert canonical_metrics["execution_aware_portfolio_payoff"] == 0.058
    assert canonical_metrics["portfolio_payoff"] == 0.058
    assert canonical_metrics["execution_aware_realization"] == 0.527273
    assert canonical_metrics["realization_gap"] == 0.052
    assert canonical_metrics["nominal_offer_supported_payoff"] == 0.06
    assert canonical_metrics["realized_offer_supported_payoff"] == 0.018
    assert canonical_metrics["offer_supported_realization_share"] == 0.310345
    assert canonical_metrics["payoff_per_unit_burden"] == 0.091579

    assert numeric_impact["headline_metrics"]["numeric_plan_coverage"] == 1.0
    assert numeric_impact["headline_metrics"]["portfolio_payoff"] == 0.058
    calibration_validation = summary["calibration_validation"]
    assert calibration_validation["headline_metrics"]["realism_clean_plan_rate"] == 0.0
    assert calibration_validation["headline_metrics"]["false_optimism_exposure"] == 0.5
    assert calibration_validation["headline_metrics"]["unstable_target_range_exposure"] == 0.5
    assert calibration_validation["headline_metrics"]["validated_execution_aware_carry_through"] == 0.527273
    assert calibration_validation["supporting_metrics"]["narrow_distribution_exposure"] == 0.5
    assert (
        numeric_impact["segment_priority"]["highest_payoff_segment"]["segment_label"]
        == "risk_band:near"
    )
    assert (
        numeric_impact["segment_priority"]["highest_burden_low_realization_segment"]["segment_label"]
        == "recoverability_segment:recoverable"
    )
    assert (
        numeric_impact["segment_priority"]["offer_dependent_segment"]["segment_label"]
        == "offer_needed_segment:offer_needed"
    )

    numeric_breakdown = artifacts["numeric_impact_breakdown"]
    assert float(numeric_breakdown.iloc[0]["execution_aware_portfolio_payoff"]) == 0.058
    validation_breakdown = artifacts["calibration_validation_breakdown"]
    assert float(validation_breakdown.iloc[0]["false_optimism_exposure"]) == 0.5

    unit_breakdown = artifacts["numeric_unit_family_breakdown"]
    assert set(unit_breakdown["unit_family"]) == {"currency", "percentage_points"}
    assert "false_optimism_exposure" in unit_breakdown.columns


def test_portfolio_validation_demo_fit_can_mark_demo_narrow() -> None:
    rows = []
    for idx in range(8):
        row = _base_row(f"near_{idx}")
        row["risk_band"] = "mid"
        row["income_band"] = "q2"
        row["stress_band"] = "base"
        rows.append(row)
    for idx in range(2):
        row = _base_row(f"demo_{idx}")
        row["risk_band"] = "near"
        row["income_band"] = "q1"
        row["stress_band"] = "base"
        row["trajectory_gate_pass_4w"] = 0
        row["trajectory_gate_pass_12w"] = 1
        row["trajectory_pd_4w"] = 0.40
        row["trajectory_pd_12w"] = 0.30
        row["trajectory_pd_24w"] = 0.28
        row["best_trajectory_checkpoints_json"] = _checkpoint_json(pd_4w=0.40, pd_12w=0.30, pd_24w=0.28)
        rows.append(row)

    demo_case = {
        "customer": {
            "risk_band": "near",
            "income_band": "q1",
        },
        "summary": {
            "decision_status": "APPROVED",
            "plan_execution_probability": 0.74,
            "approval_ready_4w": False,
            "approval_ready_12w": True,
            "approval_ready_24w": True,
            "offer_acceptance_probability": 0.0,
        },
        "phases": [{"phase_id": "phase_1_stabilize"}],
        "checkpoints": [{"week": 4, "approval_ready": False}],
    }

    artifacts = build_portfolio_validation_artifacts(
        pd.DataFrame(rows),
        tau=0.35,
        reliability_threshold_by_risk_band={"default": 0.7, "near": 0.7, "mid": 0.7},
        demo_case=demo_case,
    )

    demo_fit = artifacts["demo_representativeness"]
    assert demo_fit["demo_representativeness_verdict"] == "narrow"
    assert demo_fit["demo_fit_confidence"] == "weak"
    assert demo_fit["demo_case_segment_share"] == 0.2
    assert "recoverability_segment=recoverable" in demo_fit["demo_case_segment"]


def test_build_portfolio_validation_artifacts_tracks_provisional_drop_reason() -> None:
    row = _base_row("provisional")
    row["best_constraint_status"] = "provisional"
    row["best_status"] = "NEEDS_REVIEW"

    artifacts = build_portfolio_validation_artifacts(
        pd.DataFrame([row]),
        tau=0.35,
        reliability_threshold_by_risk_band={"default": 0.7, "near": 0.7},
    )

    drop_breakdown = artifacts["coverage_drop_breakdown"]
    raw_to_valid = drop_breakdown[drop_breakdown["transition"] == "raw_to_valid"]
    assert "provisional" in set(raw_to_valid["reason"])


def test_render_portfolio_validation_review_is_business_first() -> None:
    summary = {
        "canonical_metrics": {
            "raw_plan_coverage": 0.8,
            "valid_plan_coverage": 0.6,
            "governance_safe_plan_coverage": 0.4,
            "product_ready_plan_coverage": 0.2,
            "no_plan_rate": 0.2,
            "mean_nominal_pd_improvement": 0.09,
            "execution_weighted_expected_improvement": 0.05,
            "high_uplift_low_follow_through_rate": 0.22,
            "mean_group_difficulty_score": 0.51,
            "low_follow_through_readiness_rate": 0.26,
        },
        "reality_gap_summary": {
            "reality_gap_flag_rate": 0.3,
            "dominant_reality_gap_reason": "engine_native_action_flag",
            "product_ready_drop_due_to_reality_gap": 0.5,
        },
        "strongest_segments": [{"segment_label": "risk_band:near", "product_ready_plan_coverage": 0.5}],
        "weakest_segments": [{"segment_label": "risk_band:high", "product_ready_plan_coverage": 0.1}],
        "numeric_impact": {
            "headline_metrics": {
                "numeric_plan_coverage": 0.56,
                "requested_change_burden": 0.41,
                "execution_aware_realization": 0.62,
                "portfolio_payoff": 0.034,
            },
            "supporting_metrics": {
                "realization_gap": 0.021,
                "offer_supported_realization_share": 0.28,
            },
            "segment_priority": {
                "highest_payoff_segment": {"segment_label": "risk_band:near"},
                "highest_burden_low_realization_segment": {"segment_label": "recoverability_segment:recoverable"},
                "offer_dependent_segment": {"segment_label": "offer_needed_segment:offer_needed"},
            },
        },
        "calibration_validation": {
            "headline_metrics": {
                "realism_clean_plan_rate": 0.31,
                "false_optimism_exposure": 0.22,
                "unstable_target_range_exposure": 0.18,
                "validated_execution_aware_carry_through": 0.62,
            },
            "supporting_metrics": {
                "narrow_distribution_exposure": 0.41,
            },
            "segment_priority": {
                "highest_realism_segment": {"segment_label": "risk_band:near"},
                "highest_optimism_segment": {"segment_label": "risk_band:high"},
                "highest_instability_segment": {"segment_label": "recoverability_segment:hard_to_recover"},
                "narrowest_unit_family": {"unit_family": "percentage_points"},
            },
            "distribution_story": {"stability_status": "watch"},
        },
        "segment_story": {
            "where_engine_works": "risk_band:near",
            "where_engine_struggles": "risk_band:high",
            "where_offer_is_required": "offer_needed_segment:offer_needed",
            "where_narrative_breaks": "recoverability_segment:hard_to_recover",
        },
        "behavior_story": {
            "primary_segment_lens": "risk_band",
        },
        "demo_representativeness": {
            "demo_representativeness_verdict": "optimistic",
            "demo_fit_confidence": "moderate",
            "demo_case_segment_share": 0.12,
            "product_ready_alignment": False,
            "narrative": "demo overstates portfolio reality",
        },
    }

    review = render_portfolio_validation_review(summary)

    assert "Portfolio Validation Review" in review
    assert "Coverage Funnel" in review
    assert "Reality Gap" in review
    assert "Behavior Reality" in review
    assert "Numeric Impact" in review
    assert "Calibration & Validation" in review
    assert "Numeric Segment Strategy" in review
    assert "Mean group difficulty score" in review
    assert "Segment Story" in review
    assert "Demo Fit" in review
    assert "demo overstates portfolio reality" in review


def test_aggregate_portfolio_validation_summaries_can_report_more_honest_but_narrower() -> None:
    summary = aggregate_portfolio_validation_summaries(
        [
            {
                "population_sizes": {
                    "full_evaluation_population": 250,
                    "denied": 150,
                    "high_risk_denied": 80,
                },
                "canonical_metrics": {
                    "raw_plan_coverage": 0.72,
                    "valid_plan_coverage": 0.54,
                    "governance_safe_plan_coverage": 0.44,
                    "product_ready_plan_coverage": 0.28,
                    "no_plan_rate": 0.28,
                    "numeric_plan_coverage": 0.54,
                    "requested_change_burden": 0.42,
                    "nominal_portfolio_payoff": 0.061,
                    "execution_aware_portfolio_payoff": 0.043,
                    "portfolio_payoff": 0.043,
                    "execution_aware_realization": 0.704918,
                    "realization_gap": 0.018,
                    "payoff_per_unit_burden": 0.102381,
                    "nominal_offer_supported_payoff": 0.022,
                    "realized_offer_supported_payoff": 0.011,
                    "offer_supported_realization_share": 0.255814,
                    "realism_clean_plan_rate": 0.34,
                    "false_optimism_exposure": 0.17,
                    "unstable_target_range_exposure": 0.14,
                    "narrow_distribution_exposure": 0.43,
                    "execution_weighted_expected_improvement": 0.05,
                    "mean_group_difficulty_score": 0.47,
                    "low_follow_through_readiness_rate": 0.22,
                    "weak_4w_health_rate": 0.31,
                    "delayed_trajectory_rate": 0.27,
                    "long_horizon_heavy_rate": 0.11,
                    "reality_gap_flag_rate": 0.09,
                },
                "secondary_metrics": {
                    "raw_plan_coverage": 0.64,
                    "valid_plan_coverage": 0.45,
                },
                "reality_gap_summary": {
                    "reality_gap_flag_rate": 0.09,
                    "dominant_reality_gap_reason": "narrative_gap_flag",
                    "product_ready_drop_due_to_reality_gap": 0.18,
                    "multi_flag_exposure": 0.04,
                    "severity_split": {"mild": 0.04, "moderate": 0.03, "severe": 0.02},
                },
                "demo_representativeness": {
                    "demo_representativeness_verdict": "representative",
                    "demo_fit_confidence": "moderate",
                    "demo_case_segment": "risk_band=near",
                    "segment_size": 60,
                    "demo_case_segment_share": 0.24,
                    "segment_product_ready_rate": 0.27,
                    "segment_offer_dependency": 0.22,
                    "product_ready_alignment": True,
                    "cohort_vs_demo_delta": {
                        "plan_execution_probability": 0.01,
                        "early_checkpoint_health_rate": -0.02,
                        "product_ready_rate": -0.01,
                    },
                    "narrative": "demo aligns with cohort",
                },
            }
        ],
        phase17_baseline={
            "product_ready_plan_coverage": 0.35,
            "governance_safe_plan_coverage": 0.45,
            "execution_aware_value": 0.045,
            "weak_4w_health_rate": 0.50,
            "reality_gap_flag_rate": 0.175,
        },
    )

    proof = summary["product_proof"]
    assert proof["proof_verdict"] == "promising"
    assert proof["proof_confidence"] == "moderate"
    assert proof["phase17_delta"]["comparison_story"] == "more_honest_but_narrower"
    assert proof["phase17_delta"]["credibility_direction"] == "improved"
    assert summary["numeric_impact"]["headline_metrics"]["numeric_plan_coverage"] == 0.54
    assert summary["calibration_validation"]["headline_metrics"]["realism_clean_plan_rate"] == 0.34
    assert summary["calibration_validation"]["supporting_metrics"]["false_optimism_exposure_drift"] == 0.0


def test_aggregate_portfolio_validation_summaries_tracks_validation_drift() -> None:
    summary = aggregate_portfolio_validation_summaries(
        [
            {
                "canonical_metrics": {
                    "realism_clean_plan_rate": 0.42,
                    "false_optimism_exposure": 0.14,
                    "unstable_target_range_exposure": 0.11,
                    "narrow_distribution_exposure": 0.38,
                    "execution_aware_realization": 0.67,
                },
                "calibration_validation_story": {
                    "highest_realism_segment": {"segment_label": "risk_band:near"},
                },
            },
            {
                "canonical_metrics": {
                    "realism_clean_plan_rate": 0.24,
                    "false_optimism_exposure": 0.33,
                    "unstable_target_range_exposure": 0.27,
                    "narrow_distribution_exposure": 0.56,
                    "execution_aware_realization": 0.52,
                },
                "calibration_validation_story": {
                    "highest_realism_segment": {"segment_label": "risk_band:near"},
                },
            },
        ]
    )

    calibration_validation = summary["calibration_validation"]
    assert calibration_validation["supporting_metrics"]["realism_clean_plan_rate_drift"] == 0.18
    assert calibration_validation["supporting_metrics"]["false_optimism_exposure_drift"] == 0.19
    assert calibration_validation["distribution_story"]["stability_status"] == "drifting"


def test_build_product_confidence_snapshot_keeps_product_proof_separate_from_trust_layer() -> None:
    snapshot = build_product_confidence_snapshot(
        {
            "product_proof": {
                "proof_verdict": "mixed",
                "proof_confidence": "moderate",
                "headline_metrics": {
                    "product_ready_plan_coverage": {"current": 0.31, "baseline": 0.35, "delta": -0.04, "higher_is_better": True},
                    "governance_safe_plan_coverage": {"current": 0.43, "baseline": 0.45, "delta": -0.02, "higher_is_better": True},
                    "execution_aware_value": {"current": 0.048, "baseline": 0.045, "delta": 0.003, "higher_is_better": True},
                },
                "supporting_metrics": {
                    "weak_4w_health_rate": {"current": 0.29, "baseline": 0.50, "delta": -0.21, "higher_is_better": False},
                    "delayed_trajectory_rate": {"current": 0.27, "higher_is_better": False},
                    "long_horizon_heavy_rate": {"current": 0.11, "higher_is_better": False},
                    "reality_gap_flag_rate": {"current": 0.12, "baseline": 0.175, "delta": -0.055, "higher_is_better": False},
                },
                "phase17_delta": {
                    "baseline_name": "phase17_canonical_portfolio_snapshot",
                    "comparison_story": "more_honest_but_narrower",
                    "credibility_direction": "improved",
                    "summary": "Proof is narrower than Phase 17, but more honest on early health and reality-gap pressure.",
                },
                "demo_fit_annotation": {
                    "demo_representativeness_verdict": "narrow",
                    "demo_fit_confidence": "weak",
                    "demo_case_segment_share": 0.12,
                    "product_ready_alignment": True,
                    "narrative": "demo reflects a narrow segment",
                },
            }
        },
        decision_logging_summary={"decision_log_completeness": 0.92},
        outcome_ingestion_summary={
            "reward_90d_coverage": 0.74,
            "learning_readiness_status_distribution": {"learning_ready": {"share": 0.53}},
        },
        off_policy_evaluation={
            "comparison_status": "treatment_vs_control",
            "ope_confidence": "strong",
            "preferred_policy_signal": {"policy_arm": "installment_policy_v2", "signal": "supports_treatment"},
        },
    )

    assert snapshot["proof_verdict"] == "mixed"
    assert snapshot["proof_confidence"] == "moderate"
    assert snapshot["phase17_delta"]["comparison_story"] == "more_honest_but_narrower"
    assert snapshot["supporting_trust_layer"]["learning"]["decision_log_completeness"] == 0.92
    assert snapshot["supporting_trust_layer"]["ope"]["ope_confidence"] == "strong"


def test_aggregate_portfolio_helpers_keep_seed_and_rollup_contracts() -> None:
    summary = aggregate_portfolio_validation_summaries(
        [
            {
                "population_sizes": {
                    "full_evaluation_population": 100,
                    "denied": 60,
                    "high_risk_denied": 20,
                },
                "canonical_metrics": {
                    "raw_plan_coverage": 0.8,
                    "product_ready_plan_coverage": 0.3,
                },
                "secondary_metrics": {
                    "raw_plan_coverage": 0.7,
                },
                "reality_gap_summary": {
                    "reality_gap_flag_rate": 0.2,
                    "dominant_reality_gap_reason": "engine_native_action_flag",
                    "product_ready_drop_due_to_reality_gap": 0.4,
                    "multi_flag_exposure": 0.1,
                    "severity_split": {"mild": 0.1, "moderate": 0.07, "severe": 0.03},
                },
                "demo_representativeness": {
                    "demo_representativeness_verdict": "representative",
                    "demo_fit_confidence": "strong",
                    "demo_case_segment": "risk_band=near",
                    "segment_size": 25,
                    "demo_case_segment_share": 0.25,
                    "segment_product_ready_rate": 0.32,
                    "segment_offer_dependency": 0.18,
                    "product_ready_alignment": True,
                    "cohort_vs_demo_delta": {
                        "plan_execution_probability": 0.01,
                        "early_checkpoint_health_rate": 0.02,
                        "product_ready_rate": 0.03,
                    },
                    "narrative": "demo aligns with cohort",
                },
            },
            {
                "population_sizes": {
                    "full_evaluation_population": 120,
                    "denied": 70,
                    "high_risk_denied": 24,
                },
                "canonical_metrics": {
                    "raw_plan_coverage": 0.6,
                    "product_ready_plan_coverage": 0.2,
                },
                "secondary_metrics": {
                    "raw_plan_coverage": 0.5,
                },
                "reality_gap_summary": {
                    "reality_gap_flag_rate": 0.3,
                    "dominant_reality_gap_reason": "engine_native_action_flag",
                    "product_ready_drop_due_to_reality_gap": 0.5,
                    "multi_flag_exposure": 0.2,
                    "severity_split": {"mild": 0.1, "moderate": 0.1, "severe": 0.1},
                },
                "demo_representativeness": {
                    "demo_representativeness_verdict": "representative",
                    "demo_fit_confidence": "strong",
                    "demo_case_segment": "risk_band=near",
                    "segment_size": 35,
                    "demo_case_segment_share": 0.35,
                    "segment_product_ready_rate": 0.28,
                    "segment_offer_dependency": 0.22,
                    "product_ready_alignment": True,
                    "cohort_vs_demo_delta": {
                        "plan_execution_probability": 0.03,
                        "early_checkpoint_health_rate": 0.01,
                        "product_ready_rate": 0.02,
                    },
                    "narrative": "demo aligns with cohort",
                },
            },
        ]
    )

    assert summary["seed_count"] == 2
    assert summary["canonical_metrics"]["raw_plan_coverage"] == 0.7
    assert summary["canonical_metrics"]["product_ready_plan_coverage"] == 0.25
    assert summary["demo_representativeness"]["demo_representativeness_verdict"] == "representative"
    assert summary["demo_representativeness"]["segment_size"] == 30

    breakdown = aggregate_portfolio_breakdown(
        [
            pd.DataFrame(
                [
                    {"seed": 1, "population": "full", "segment_axis": "risk_band", "segment_value": "near", "count": 10, "share": 0.5},
                ]
            ),
            pd.DataFrame(
                [
                    {"seed": 2, "population": "full", "segment_axis": "risk_band", "segment_value": "near", "count": 12, "share": 0.6},
                ]
            ),
        ],
        group_columns=["population", "segment_axis", "segment_value"],
        value_columns={"count": "sum", "share": "mean"},
        breakdown_type_seed="seed_segment",
        breakdown_type_rollup="segment_rollup",
    )
    assert set(breakdown["breakdown_type"]) == {"seed_segment", "segment_rollup"}
    rollup = breakdown[breakdown["breakdown_type"] == "segment_rollup"].iloc[0]
    assert int(rollup["count"]) == 22
    assert float(rollup["share"]) == 0.55


def test_build_portfolio_validation_artifacts_handles_missing_brownfield_columns() -> None:
    row = _base_row("missing_cols")
    row.pop("fairness_guard_demoted")
    row.pop("stress_band")

    artifacts = build_portfolio_validation_artifacts(
        pd.DataFrame([row]),
        tau=0.35,
        reliability_threshold_by_risk_band={"default": 0.7, "near": 0.7},
    )

    assert artifacts["summary"]["canonical_metrics"]["raw_plan_coverage"] == 1.0
    assert artifacts["summary"]["canonical_metrics"]["product_ready_plan_coverage"] == 1.0
