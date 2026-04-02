from __future__ import annotations

import pandas as pd

from credit_coach.evaluation import decision_calibration as cal


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

    assert {"policy_version", "analysis_only", "false_positive_proxy_delta", "approve_plus_conditional_share_delta"}.issubset(comparison.columns)
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
