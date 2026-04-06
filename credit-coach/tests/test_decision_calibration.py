from __future__ import annotations

import pandas as pd

from credit_coach.evaluation import decision_calibration as cal
from credit_coach.evaluation.recoverability import recoverability_risk_band


def _work_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"_frame_position": 0, "source_row_index": 100, "customer_id": "c-0", "base_pd": 0.18, "denied_base": False, "risk_band": "near", "pilot_bucket": "approved_like"},
            {"_frame_position": 1, "source_row_index": 101, "customer_id": "c-1", "base_pd": 0.26, "denied_base": False, "risk_band": "near", "pilot_bucket": "approved_like"},
            {"_frame_position": 2, "source_row_index": 102, "customer_id": "c-2", "base_pd": 0.31, "denied_base": False, "risk_band": "near", "pilot_bucket": "near_threshold"},
            {"_frame_position": 3, "source_row_index": 103, "customer_id": "c-3", "base_pd": 0.36, "denied_base": True, "risk_band": "near", "pilot_bucket": "near_threshold"},
            {"_frame_position": 4, "source_row_index": 104, "customer_id": "c-4", "base_pd": 0.44, "denied_base": True, "risk_band": "near", "pilot_bucket": "near_threshold"},
            {"_frame_position": 5, "source_row_index": 105, "customer_id": "c-5", "base_pd": 0.50, "denied_base": True, "risk_band": "mid", "pilot_bucket": "denied_mid_pressure"},
            {"_frame_position": 6, "source_row_index": 106, "customer_id": "c-6", "base_pd": 0.56, "denied_base": True, "risk_band": "mid", "pilot_bucket": "denied_mid_pressure"},
            {"_frame_position": 7, "source_row_index": 107, "customer_id": "c-7", "base_pd": 0.68, "denied_base": True, "risk_band": "high", "pilot_bucket": "denied_high_pressure"},
            {"_frame_position": 8, "source_row_index": 108, "customer_id": "c-8", "base_pd": 0.72, "denied_base": True, "risk_band": "high", "pilot_bucket": "denied_high_pressure"},
            {"_frame_position": 9, "source_row_index": 109, "customer_id": "c-9", "base_pd": 0.76, "denied_base": True, "risk_band": "high", "pilot_bucket": "denied_high_pressure"},
        ]
    )


def test_select_initial_cohort_pilot_mixed_sets_quota_metadata() -> None:
    result = cal.select_initial_cohort(
        work=_work_frame(),
        requested_n=6,
        sample_seed=11,
        cohort_policy="pilot_mixed",
    )

    assert len(result.selected) == 6
    assert set(result.selected["cohort_policy"]) == {"pilot_mixed"}
    assert set(result.selected["selection_policy_name"]) == {"pilot_mixed"}
    assert set(result.selected["selection_fill_behavior"]) == {"quota_first_deterministic_soft_fill"}
    assert result.metadata["cohort_definition"]["bucket_weights"]["near_threshold"] == 30
    assert result.metadata["cohort_purpose"].startswith("Pilot-ready mixed cohort")
    assert result.selected["cohort_bucket"].isin(cal.PILOT_MIX_BUCKET_ORDER).all()


def test_select_initial_cohort_ops_queue_replay_preserves_order() -> None:
    result = cal.select_initial_cohort(
        work=_work_frame(),
        requested_n=4,
        sample_seed=99,
        cohort_policy="ops_queue_replay",
    )

    assert list(result.selected["source_row_index"]) == [100, 101, 102, 103]
    assert set(result.selected["selection_reason"]) == {"queue_replay"}
    assert result.metadata["selection_fill_behavior"] == "order_preserving_replay"


def test_rebalance_offer_needed_selection_balances_two_pass_subset() -> None:
    selection_df = _work_frame().head(6).copy()
    selection_df["selection_reason"] = "broad"
    selection_df["cohort_policy"] = "offer_needed_balanced"
    selection_df["cohort_bucket"] = selection_df["pilot_bucket"]
    selection_df["selection_policy_name"] = "offer_needed_balanced"
    selection_df["selection_fill_behavior"] = "two_pass_deterministic_rebalance"
    selection_df["batch_index"] = range(len(selection_df))
    metrics_df = pd.DataFrame(
        [
            {"source_row_index": 100, "customer_id": "c-0", "offer_needed_flag": "offer_needed"},
            {"source_row_index": 101, "customer_id": "c-1", "offer_needed_flag": "offer_needed"},
            {"source_row_index": 102, "customer_id": "c-2", "offer_needed_flag": "offer_needed"},
            {"source_row_index": 103, "customer_id": "c-3", "offer_needed_flag": "no_offer_needed"},
            {"source_row_index": 104, "customer_id": "c-4", "offer_needed_flag": "no_offer_needed"},
            {"source_row_index": 105, "customer_id": "c-5", "offer_needed_flag": "no_offer_needed"},
        ]
    )

    selected, metadata = cal.rebalance_offer_needed_selection(
        selection_df=selection_df,
        metrics_df=metrics_df,
        requested_n=4,
        sample_seed=5,
    )

    counts = selected["offer_needed_flag"].value_counts().to_dict()
    assert len(selected) == 4
    assert counts["offer_needed"] == 2
    assert counts["no_offer_needed"] == 2
    assert metadata["offer_needed_rebalance_applied"] is True


def test_build_selection_work_frame_adds_phase_61_gap_fields() -> None:
    input_df = pd.DataFrame(
        [
            {"customer_id": "c-near"},
            {"customer_id": "c-mid"},
            {"customer_id": "c-high"},
        ]
    )
    base_pd = pd.Series([0.40, 0.52, 0.68], dtype=float)

    work = cal.build_selection_work_frame(
        input_df=input_df,
        base_pd=base_pd,
        tau=0.35,
        risk_band_fn=lambda value, tau, segment_caps_cfg: recoverability_risk_band(
            approval_gap=max(0.0, float(value) - float(tau)),
            near_upper=float(segment_caps_cfg["risk_band_thresholds"]["near_upper"]),
            mid_upper=float(segment_caps_cfg["risk_band_thresholds"]["mid_upper"]),
        ),
        segment_caps_cfg={"risk_band_thresholds": {"near_upper": 0.10, "mid_upper": 0.25}},
        customer_id_getter=lambda row, fallback: str(row.get("customer_id") or fallback),
    )

    assert list(work["approval_gap"].round(6)) == [0.05, 0.17, 0.33]
    assert list(work["normalized_gap"].round(6)) == [0.2, 0.68, 1.0]
    assert list(work["recoverability_bucket"]) == ["near_threshold", "mid_risk", "structural_limited"]
    assert list(work["recoverability_score"].round(6)) == [0.8, 0.32, 0.0]


def test_build_funnel_and_status_by_readiness_reuses_phase_40_5_taxonomy() -> None:
    metrics_df = pd.DataFrame(
        [
            {"decision_status": "APPROVED", "decision_status_internal": "APPROVED", "expected_readiness": "week_4", "decision_confidence": 0.72, "realization_anchor": 0.71, "expected_pd_improvement": 0.03},
            {"decision_status": "CONDITIONAL", "decision_status_internal": "CONDITIONAL", "expected_readiness": "week_12", "decision_confidence": 0.51, "realization_anchor": 0.48, "expected_pd_improvement": 0.02},
            {"decision_status": "REJECTED", "decision_status_internal": "REJECTED", "expected_readiness": "not_ready", "decision_confidence": 0.20, "realization_anchor": 0.08, "expected_pd_improvement": 0.0},
            {"decision_status": "CONDITIONAL", "decision_status_internal": "NEEDS_REVIEW", "expected_readiness": "unknown_review", "decision_confidence": 0.35, "realization_anchor": 0.41, "expected_pd_improvement": 0.02},
        ]
    )

    funnel = cal.build_funnel_summary(metrics_df)
    readiness = cal.build_readiness_distribution(metrics_df)
    cross_tab = cal.build_status_by_readiness(metrics_df)

    assert funnel["approved_share"] == 0.25
    assert funnel["conditional_share"] == 0.5
    assert funnel["rejected_share"] == 0.25
    assert funnel["internal_needs_review_share"] == 0.25
    assert set(readiness["expected_readiness"]) == set(cal.READINESS_ORDER)
    assert cross_tab.loc[cross_tab["expected_readiness"] == "week_4", "share_given_readiness"].sum() == 1.0
    assert cross_tab.loc[cross_tab["expected_readiness"] == "unknown_review", "share_given_readiness"].sum() == 1.0


def test_build_policy_comparison_emits_analysis_only_candidates_and_shift_matrix() -> None:
    metrics_df = pd.DataFrame(
        [
            {
                "decision_status": "APPROVED",
                "decision_status_internal": "APPROVED",
                "decision_confidence": 0.72,
                "expected_readiness": "week_4",
                "realization_anchor": 0.62,
                "expected_pd_improvement": 0.03,
                "strong_execution_flag": 1,
                "offer_maturity": "none",
                "offer_plan": 0,
                "risk_band": "near",
                "conditional_type": "",
            },
            {
                "decision_status": "CONDITIONAL",
                "decision_status_internal": "CONDITIONAL",
                "decision_confidence": 0.58,
                "expected_readiness": "week_12",
                "realization_anchor": 0.44,
                "expected_pd_improvement": 0.02,
                "strong_execution_flag": 0,
                "offer_maturity": "none",
                "offer_plan": 0,
                "risk_band": "mid",
                "conditional_type": "TIME_GATED",
            },
            {
                "decision_status": "CONDITIONAL",
                "decision_status_internal": "NEEDS_REVIEW",
                "decision_confidence": 0.33,
                "expected_readiness": "unknown_review",
                "realization_anchor": 0.40,
                "expected_pd_improvement": 0.02,
                "strong_execution_flag": 0,
                "offer_maturity": "provisional",
                "offer_plan": 1,
                "risk_band": "high",
                "conditional_type": "DATA_ISSUE",
                "data_issue_flag": 1,
                "raw_contract_pass": 0,
            },
            {
                "decision_status": "REJECTED",
                "decision_status_internal": "REJECTED",
                "decision_confidence": 0.12,
                "expected_readiness": "not_ready",
                "realization_anchor": 0.05,
                "expected_pd_improvement": 0.0,
                "strong_execution_flag": 0,
                "offer_maturity": "none",
                "offer_plan": 0,
                "risk_band": "high",
                "conditional_type": "",
                "zero_step_flag": 1,
                "best_action_count": 0,
            },
        ]
    )

    payload = cal.build_policy_comparison(metrics_df, policy_version_evaluated="v2.1_phase_40_5")
    comparison = payload["policy_comparison"]
    shift_matrix = payload["decision_shift_matrix"]
    segment_breakdown = payload["segment_breakdown"]
    recommendation = payload["policy_recommendation_summary"]
    catalog = payload["policy_profile_catalog"]

    assert {
        "policy_version",
        "analysis_only",
        "false_positive_proxy_delta",
        "approve_plus_conditional_share_delta",
        "rejected_to_conditional_count",
        "conditional_to_approved_count",
        "direct_rejected_to_approved_count",
    }.issubset(comparison.columns)
    assert "v2.1_phase_40_5" in set(comparison["policy_version"])
    assert set(comparison.loc[comparison["analysis_only"] == 1, "policy_version"]) == {
        "analysis_mild_relax_v2_3a",
        "analysis_relaxed_v2_3a",
        "analysis_strict_control_v2_3a",
    }
    assert {"recommendation_status", "recommendation_reason", "profile_role", "promotion_target"}.issubset(comparison.columns)
    assert not shift_matrix.empty
    assert {"from_status", "to_status", "count", "share"}.issubset(shift_matrix.columns)
    assert "decision_confidence_band" in set(segment_breakdown["segment_axis"])
    assert recommendation["recommended_candidate_status"] in {"shortlisted", "no_safe_uplift"}
    assert catalog["catalog_version"] == cal.POLICY_PROFILE_CATALOG_VERSION
    assert catalog["profiles"][0]["policy_version"] == "v2.1_phase_40_5"


def test_build_movement_guardrail_evidence_identifies_structural_bottleneck() -> None:
    metrics_df = pd.DataFrame(
        [
            {
                "decision_status": "REJECTED",
                "selected_decision_status": "REJECTED",
                "expected_readiness": "not_ready",
                "risk_band": "high",
                "candidate_pool_count": 2,
                "candidate_non_empty_count": 1,
                "approval_shell_only_share": 0.10,
                "offer_ready_contender_share": 0.0,
                "provisional_offer_share": 0.0,
                "selected_invalid_winner_flag": 0,
                "selected_dice_flag": 0,
                "selected_dice_valid_flag": 0,
                "operator_selected_decision_status": "REJECTED",
                "operator_rendered_blocker_count": 1,
                "operator_rendered_action_count": 0,
                "operator_upgrade_condition_text": "",
                "operator_top_blocker_codes_json": "[]",
                "operator_first_action_blocker_codes_json": "[]",
                "operator_readiness_render_mode": "rejected_not_ready",
                "selection_outcome": "selected_valid_winner",
            },
            {
                "decision_status": "REJECTED",
                "selected_decision_status": "REJECTED",
                "expected_readiness": "not_ready",
                "risk_band": "high",
                "candidate_pool_count": 2,
                "candidate_non_empty_count": 1,
                "approval_shell_only_share": 0.20,
                "offer_ready_contender_share": 0.0,
                "provisional_offer_share": 0.0,
                "selected_invalid_winner_flag": 0,
                "selected_dice_flag": 0,
                "selected_dice_valid_flag": 0,
                "operator_selected_decision_status": "REJECTED",
                "operator_rendered_blocker_count": 1,
                "operator_rendered_action_count": 0,
                "operator_upgrade_condition_text": "",
                "operator_top_blocker_codes_json": "[]",
                "operator_first_action_blocker_codes_json": "[]",
                "operator_readiness_render_mode": "rejected_not_ready",
                "selection_outcome": "selected_valid_winner",
            },
            {
                "decision_status": "REJECTED",
                "selected_decision_status": "REJECTED",
                "expected_readiness": "week_24",
                "risk_band": "near",
                "candidate_pool_count": 2,
                "candidate_non_empty_count": 1,
                "approval_shell_only_share": 0.10,
                "offer_ready_contender_share": 0.0,
                "provisional_offer_share": 0.0,
                "selected_invalid_winner_flag": 0,
                "selected_dice_flag": 0,
                "selected_dice_valid_flag": 0,
                "operator_selected_decision_status": "REJECTED",
                "operator_rendered_blocker_count": 1,
                "operator_rendered_action_count": 0,
                "operator_upgrade_condition_text": "",
                "operator_top_blocker_codes_json": "[]",
                "operator_first_action_blocker_codes_json": "[]",
                "operator_readiness_render_mode": "rejected_not_ready",
                "selection_outcome": "selected_valid_winner",
            },
        ]
    )
    policy_comparison_df = pd.DataFrame(
        [
            {
                "policy_version": "v2.1_phase_40_5",
                "analysis_only": 0,
                "recommendation_status": "baseline",
                "recommendation_reason": "baseline",
                "approve_plus_conditional_share_delta": 0.0,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 0,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
                "north_star_pass": False,
            },
            {
                "policy_version": "analysis_mild_relax_v2_3a",
                "analysis_only": 1,
                "recommendation_status": "blocked",
                "recommendation_reason": "No bounded APPROVED + CONDITIONAL uplift over the shipped baseline.",
                "approve_plus_conditional_share_delta": 0.0,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 0,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
                "north_star_pass": False,
            },
        ]
    )
    outcome_rule_comparison_df = pd.DataFrame(
        [
            {
                "outcome_rule_profile_version": "v2.1_phase_40_5",
                "analysis_only": 0,
                "recommendation_status": "baseline",
                "recommendation_reason": "baseline",
                "approve_plus_conditional_share_delta": 0.0,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 0,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
                "north_star_pass": False,
            },
            {
                "outcome_rule_profile_version": "analysis_offer_support_v2_3b",
                "analysis_only": 1,
                "recommendation_status": "blocked",
                "recommendation_reason": "No bounded offer/readiness-driven outcome movement was created.",
                "approve_plus_conditional_share_delta": 0.0,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 0,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
                "north_star_pass": False,
            },
        ]
    )

    payload = cal.build_movement_guardrail_evidence(
        metrics_df,
        policy_comparison_df=policy_comparison_df,
        policy_recommendation_summary={"recommended_candidate_status": "no_safe_uplift"},
        outcome_rule_comparison_df=outcome_rule_comparison_df,
        outcome_rule_recommendation_summary={"recommended_outcome_rule_status": "no_safe_uplift"},
        operator_briefing={
            "dominant_blockers": [
                {
                    "blocker_code": "reason:TIME_BLOCK",
                    "title": "Most files are too far from near-term readiness.",
                }
            ]
        },
    )

    summary = payload["movement_guardrail_summary"]
    assert summary["movement_guardrail_version"] == cal.MOVEMENT_GUARDRAIL_VERSION
    assert summary["dominant_movement_bottleneck"] == "structural_cohort_limited"
    assert summary["threshold_family"]["status"] == "no_movement"
    assert summary["offer_readiness_family"]["status"] == "no_movement"
    assert summary["structural_cohort"]["signal_score"] >= 2
    assert payload["movement_promotion_blockers"].shape[0] == 2
    assert set(payload["movement_bottleneck_breakdown"]["diagnosis_family"]) == {
        "threshold_policy",
        "offer_readiness",
        "recommendation_space",
        "structural_cohort",
        "trust_guardrails",
    }
    review_md = cal.build_movement_guardrail_review_markdown(summary)
    assert "Dominant bottleneck: structural_cohort_limited" in review_md


def test_build_policy_profile_catalog_mirrors_shipped_baseline_and_locked_candidates() -> None:
    catalog = cal.build_policy_profile_catalog(policy_version_evaluated="v2.1_phase_40_5")

    assert catalog["catalog_version"] == "v2.3_phase_49"
    assert [profile["policy_version"] for profile in catalog["profiles"]] == [
        "v2.1_phase_40_5",
        "analysis_mild_relax_v2_3a",
        "analysis_relaxed_v2_3a",
        "analysis_strict_control_v2_3a",
    ]
    baseline = catalog["profiles"][0]
    assert baseline["approved_realization_min"] == 0.5
    assert baseline["approved_improvement_min"] == 0.02
    assert baseline["approved_confidence_min"] == 0.6
    assert baseline["conditional_realization_min"] == 0.2
    assert baseline["conditional_improvement_min"] == 0.01
    assert baseline["conditional_confidence_min"] == 0.4


def test_recommend_candidate_policy_returns_no_safe_uplift_when_all_candidates_are_blocked() -> None:
    comparison_df = pd.DataFrame(
        [
            {
                "policy_version": "v2.1_phase_40_5",
                "analysis_only": 0,
                "profile_role": "baseline",
                "promotion_target": False,
                "approve_plus_conditional_share_delta": 0.0,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "approved_share_delta": 0.0,
            },
            {
                "policy_version": "analysis_relaxed_v2_3a",
                "analysis_only": 1,
                "profile_role": "candidate",
                "promotion_target": True,
                "approve_plus_conditional_share_delta": 0.01,
                "false_positive_proxy_delta": 0.02,
                "internal_needs_review_share_delta": 0.0,
                "approved_share_delta": 0.0,
            },
            {
                "policy_version": "analysis_strict_control_v2_3a",
                "analysis_only": 1,
                "profile_role": "control",
                "promotion_target": False,
                "approve_plus_conditional_share_delta": -0.01,
                "false_positive_proxy_delta": -0.01,
                "internal_needs_review_share_delta": -0.01,
                "approved_share_delta": -0.01,
            },
        ]
    )

    summary = cal.recommend_candidate_policy(comparison_df)

    assert summary["recommended_candidate_status"] == "no_safe_uplift"
    assert summary["recommended_candidate_policy_version"] == ""
    assert "guardrail" in summary["recommended_candidate_reason"].lower() or "control profile" in summary["recommended_candidate_reason"].lower()


def test_recommend_candidate_policy_shortlists_best_safe_candidate() -> None:
    comparison_df = pd.DataFrame(
        [
            {
                "policy_version": "v2.1_phase_40_5",
                "analysis_only": 0,
                "profile_role": "baseline",
                "promotion_target": False,
                "approve_plus_conditional_share_delta": 0.0,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "approved_share_delta": 0.0,
            },
            {
                "policy_version": "analysis_mild_relax_v2_3a",
                "analysis_only": 1,
                "profile_role": "candidate",
                "promotion_target": True,
                "approve_plus_conditional_share_delta": 0.01,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "approved_share_delta": 0.005,
            },
            {
                "policy_version": "analysis_relaxed_v2_3a",
                "analysis_only": 1,
                "profile_role": "candidate",
                "promotion_target": True,
                "approve_plus_conditional_share_delta": 0.02,
                "false_positive_proxy_delta": 0.005,
                "internal_needs_review_share_delta": 0.01,
                "approved_share_delta": 0.008,
            },
        ]
    )

    summary = cal.recommend_candidate_policy(comparison_df)

    assert summary["recommended_candidate_status"] == "shortlisted"
    assert summary["recommended_candidate_policy_version"] == "analysis_relaxed_v2_3a"
    assert "guardrails remain within limits" in summary["recommended_candidate_reason"]


def test_build_outcome_rule_catalog_is_locked_and_deterministic() -> None:
    catalog = cal.build_outcome_rule_catalog(policy_version_evaluated="v2.1_phase_40_5")

    assert catalog["catalog_version"] == cal.OUTCOME_RULE_CATALOG_VERSION
    assert catalog["policy_version_evaluated"] == "v2.1_phase_40_5"
    assert [profile["outcome_rule_profile_version"] for profile in catalog["profiles"]] == [
        "analysis_offer_support_v2_3b",
        "analysis_readiness_support_v2_3b",
        "analysis_offer_readiness_combo_v2_3b",
    ]


def test_build_outcome_rule_comparison_enforces_one_step_movement() -> None:
    metrics_df = pd.DataFrame(
        [
            {
                "source_row_index": 1,
                "customer_id": "offer-reject",
                "decision_status": "REJECTED",
                "decision_status_internal": "REJECTED",
                "decision_confidence": 0.50,
                "expected_readiness": "week_12",
                "realization_anchor": 0.32,
                "expected_pd_improvement": 0.015,
                "raw_contract_pass": 1,
                "parity_pass": 1,
                "plan_contract_pass": 1,
                "best_action_count": 1,
                "offer_plan": 1,
                "offer_maturity": "active_rankable",
                "rankable_offer_count": 1,
                "approval_pending_action_count": 0,
                "offer_acceptance_probability": 0.35,
                "approval_dependent_plan_probability": 0.60,
                "combined_plan_realization_probability": 0.36,
                "conditional_type": "",
            },
            {
                "source_row_index": 2,
                "customer_id": "readiness-reject",
                "decision_status": "REJECTED",
                "decision_status_internal": "REJECTED",
                "decision_confidence": 0.50,
                "expected_readiness": "week_12",
                "realization_anchor": 0.31,
                "expected_pd_improvement": 0.018,
                "raw_contract_pass": 1,
                "parity_pass": 1,
                "plan_contract_pass": 1,
                "best_action_count": 1,
                "offer_plan": 0,
                "offer_maturity": "none",
                "rankable_offer_count": 0,
                "approval_pending_action_count": 0,
                "offer_acceptance_probability": 0.0,
                "approval_dependent_plan_probability": 0.31,
                "combined_plan_realization_probability": 0.31,
                "approval_ready_12w": 1,
                "conditional_type": "",
            },
            {
                "source_row_index": 3,
                "customer_id": "offer-conditional",
                "decision_status": "CONDITIONAL",
                "decision_status_internal": "CONDITIONAL",
                "decision_confidence": 0.58,
                "expected_readiness": "week_4",
                "realization_anchor": 0.48,
                "expected_pd_improvement": 0.022,
                "raw_contract_pass": 1,
                "parity_pass": 1,
                "plan_contract_pass": 1,
                "best_action_count": 1,
                "offer_plan": 1,
                "offer_maturity": "active_rankable",
                "rankable_offer_count": 1,
                "approval_pending_action_count": 0,
                "offer_acceptance_probability": 0.40,
                "approval_dependent_plan_probability": 0.74,
                "combined_plan_realization_probability": 0.55,
                "conditional_type": "OFFER_GATED",
            },
            {
                "source_row_index": 4,
                "customer_id": "baseline-approved",
                "decision_status": "APPROVED",
                "decision_status_internal": "APPROVED",
                "decision_confidence": 0.72,
                "expected_readiness": "week_4",
                "realization_anchor": 0.66,
                "expected_pd_improvement": 0.03,
                "raw_contract_pass": 1,
                "parity_pass": 1,
                "plan_contract_pass": 1,
                "best_action_count": 1,
                "offer_plan": 0,
                "offer_maturity": "none",
                "rankable_offer_count": 0,
                "approval_pending_action_count": 0,
                "offer_acceptance_probability": 0.0,
                "approval_dependent_plan_probability": 0.66,
                "combined_plan_realization_probability": 0.66,
                "conditional_type": "",
            },
        ]
    )

    payload = cal.build_outcome_rule_comparison(metrics_df, policy_version_evaluated="v2.1_phase_40_5")

    comparison = payload["outcome_rule_comparison"]
    effects = payload["outcome_rule_customer_effects"]
    recommendation = payload["outcome_rule_recommendation_summary"]

    assert set(comparison.loc[comparison["analysis_only"] == 1, "outcome_rule_profile_version"]) == {
        "analysis_offer_support_v2_3b",
        "analysis_readiness_support_v2_3b",
        "analysis_offer_readiness_combo_v2_3b",
    }
    assert int(comparison.loc[comparison["analysis_only"] == 1, "direct_rejected_to_approved_count"].sum()) == 0
    assert (
        effects.loc[
            (effects["outcome_rule_profile_version"] == "analysis_offer_support_v2_3b")
            & (effects["customer_id"] == "offer-reject"),
            "candidate_decision_status",
        ]
        .iloc[0]
        == "CONDITIONAL"
    )
    assert (
        effects.loc[
            (effects["outcome_rule_profile_version"] == "analysis_readiness_support_v2_3b")
            & (effects["customer_id"] == "readiness-reject"),
            "candidate_decision_status",
        ]
        .iloc[0]
        == "CONDITIONAL"
    )
    assert (
        effects.loc[
            (effects["outcome_rule_profile_version"] == "analysis_offer_support_v2_3b")
            & (effects["customer_id"] == "offer-conditional"),
            "candidate_decision_status",
        ]
        .iloc[0]
        == "APPROVED"
    )
    assert recommendation["recommended_outcome_rule_status"] == "shortlisted"
    assert recommendation["recommended_outcome_rule_profile_version"] in {
        "analysis_offer_support_v2_3b",
        "analysis_offer_readiness_combo_v2_3b",
    }


def test_recommend_outcome_rule_returns_no_safe_uplift_when_guardrails_fail() -> None:
    comparison_df = pd.DataFrame(
        [
            {
                "outcome_rule_profile_version": "v2.1_phase_40_5",
                "analysis_only": 0,
                "profile_role": "baseline",
                "approve_plus_conditional_share_delta": 0.0,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 0,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
            },
            {
                "outcome_rule_profile_version": "analysis_offer_support_v2_3b",
                "analysis_only": 1,
                "profile_role": "candidate",
                "approve_plus_conditional_share_delta": 0.02,
                "false_positive_proxy_delta": 0.02,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 1,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
            },
            {
                "outcome_rule_profile_version": "analysis_offer_readiness_combo_v2_3b",
                "analysis_only": 1,
                "profile_role": "candidate",
                "approve_plus_conditional_share_delta": 0.01,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 0,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
            },
        ]
    )

    summary = cal.recommend_outcome_rule(comparison_df)

    assert summary["recommended_outcome_rule_status"] == "no_safe_uplift"
    assert summary["recommended_outcome_rule_profile_version"] == ""


def test_build_policy_baseline_selection_prefers_shipped_baseline_for_no_safe_uplift() -> None:
    policy_comparison_df = pd.DataFrame(
        [
            {
                "policy_version": "v2.1_phase_40_5",
                "analysis_only": 0,
                "recommendation_status": "baseline",
                "recommendation_reason": "baseline",
                "approve_plus_conditional_share_delta": 0.0,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 0,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
                "promotion_target": False,
                "profile_role": "baseline",
            },
            {
                "policy_version": "analysis_mild_relax_v2_3a",
                "analysis_only": 1,
                "recommendation_status": "blocked",
                "recommendation_reason": "No bounded APPROVED + CONDITIONAL uplift over the shipped baseline.",
                "approve_plus_conditional_share_delta": 0.0,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 0,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
                "promotion_target": True,
                "profile_role": "candidate",
            },
        ]
    )
    outcome_rule_comparison_df = pd.DataFrame(
        [
            {
                "outcome_rule_profile_version": "v2.1_phase_40_5",
                "analysis_only": 0,
                "recommendation_status": "baseline",
                "recommendation_reason": "baseline",
                "approve_plus_conditional_share_delta": 0.0,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 0,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
                "promotion_target": False,
                "profile_role": "baseline",
            },
            {
                "outcome_rule_profile_version": "analysis_offer_support_v2_3b",
                "analysis_only": 1,
                "recommendation_status": "blocked",
                "recommendation_reason": "No bounded offer/readiness-driven outcome movement was created.",
                "approve_plus_conditional_share_delta": 0.0,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 0,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
                "promotion_target": True,
                "profile_role": "candidate",
            },
        ]
    )

    selection = cal.build_policy_baseline_selection(
        policy_version_evaluated="v2.1_phase_40_5",
        policy_recommendation_summary={
            "candidate_policy_versions_compared": ["analysis_mild_relax_v2_3a"],
            "recommended_candidate_status": "no_safe_uplift",
            "recommended_candidate_policy_version": "",
        },
        outcome_rule_recommendation_summary={
            "candidate_outcome_rule_versions_compared": ["analysis_offer_support_v2_3b"],
            "recommended_outcome_rule_status": "no_safe_uplift",
            "recommended_outcome_rule_profile_version": "",
        },
        movement_guardrail_summary={
            "dominant_movement_bottleneck": "structural_cohort_limited",
            "movement_guardrail_summary": "Neither threshold nor offer/readiness candidates created safe movement; this cohort appears structurally too far from near-term movement.",
            "promotion_blocker_summary": "No candidate family created promotable movement under the shipped trust and risk guardrails.",
        },
        policy_comparison_df=policy_comparison_df,
        outcome_rule_comparison_df=outcome_rule_comparison_df,
    )

    assert selection["policy_baseline_selection_version"] == cal.POLICY_BASELINE_SELECTION_VERSION
    assert selection["preferred_demo_profile"] == cal.PREFERRED_DEMO_PROFILE
    assert selection["fallback_demo_profile"] == cal.FALLBACK_DEMO_PROFILE
    assert selection["selection_mode"] == "shared_runtime_baseline"
    assert selection["preferred_runtime_policy_version"] == "v2.1_phase_40_5"
    assert selection["threshold_family_promotion_status"] == "no_safe_uplift"
    assert selection["outcome_rule_family_promotion_status"] == "no_safe_uplift"
    assert selection["dominant_movement_bottleneck"] == "structural_cohort_limited"
    assert "shipped live baseline" in selection["policy_baseline_selection_reason"]
    assert selection["next_milestone_focus"] == "expand_movement_levers"
    assert selection["candidate_disposition_count"] == 2


def test_build_policy_candidate_disposition_marks_shortlisted_candidates_as_not_adopted() -> None:
    policy_comparison_df = pd.DataFrame(
        [
            {
                "policy_version": "v2.1_phase_40_5",
                "analysis_only": 0,
                "recommendation_status": "baseline",
                "recommendation_reason": "baseline",
                "approve_plus_conditional_share_delta": 0.0,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 0,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
                "profile_role": "baseline",
                "promotion_target": False,
            },
            {
                "policy_version": "analysis_relaxed_v2_3a",
                "analysis_only": 1,
                "recommendation_status": "shortlisted",
                "recommendation_reason": "Bounded yield uplift is positive while Phase 49 proxy guardrails remain within limits.",
                "approve_plus_conditional_share_delta": 0.02,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 1,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
                "profile_role": "candidate",
                "promotion_target": True,
                "north_star_pass": True,
            },
        ]
    )
    outcome_rule_comparison_df = pd.DataFrame(
        [
            {
                "outcome_rule_profile_version": "v2.1_phase_40_5",
                "analysis_only": 0,
                "recommendation_status": "baseline",
                "recommendation_reason": "baseline",
                "approve_plus_conditional_share_delta": 0.0,
                "false_positive_proxy_delta": 0.0,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 0,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
                "profile_role": "baseline",
                "promotion_target": False,
            },
            {
                "outcome_rule_profile_version": "analysis_offer_support_v2_3b",
                "analysis_only": 1,
                "recommendation_status": "blocked",
                "recommendation_reason": "False-positive proxy regression exceeds the Phase 50 guardrail.",
                "approve_plus_conditional_share_delta": 0.02,
                "false_positive_proxy_delta": 0.02,
                "internal_needs_review_share_delta": 0.0,
                "rejected_to_conditional_count": 1,
                "conditional_to_approved_count": 0,
                "direct_rejected_to_approved_count": 0,
                "profile_role": "candidate",
                "promotion_target": True,
            },
        ]
    )

    disposition = cal.build_policy_candidate_disposition(
        policy_comparison_df=policy_comparison_df,
        outcome_rule_comparison_df=outcome_rule_comparison_df,
    )

    assert set(disposition["candidate_family"]) == {"threshold_policy", "offer_readiness_rule"}
    shortlisted = disposition.loc[disposition["candidate_profile_version"] == "analysis_relaxed_v2_3a"].iloc[0]
    blocked = disposition.loc[disposition["candidate_profile_version"] == "analysis_offer_support_v2_3b"].iloc[0]

    assert int(shortlisted["movement_created"]) == 1
    assert int(shortlisted["guardrail_blocked"]) == 0
    assert "analysis-only" in shortlisted["non_adoption_reason"]
    assert blocked["blocker_code"] == "false_positive_proxy_guardrail"
    assert int(blocked["guardrail_blocked"]) == 1
    assert blocked["non_adoption_reason"] == "False-positive proxy regression exceeds the Phase 50 guardrail."
