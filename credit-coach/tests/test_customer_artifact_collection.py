from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from credit_coach.cli import run_customer_artifact_collection as collector
from credit_coach.cli.run_recourse import (
    CustomerArtifactBundle,
    CustomerRecourseRunResult,
    _build_customer_roadmap,
    _plan_to_row,
    build_customer_artifact_bundle,
    write_customer_artifact_bundle,
)
from credit_coach.coaching.planner import BestPlanSelectionResult
from credit_coach.data.schema import PlanAction, PlanRecord, TrajectoryCheckpoint, TrajectoryPhase
from credit_coach.recourse.pathing import build_recourse_path_records


class _DummyModel:
    def predict_proba(self, x):
        frame = x if isinstance(x, pd.DataFrame) else pd.DataFrame(x)
        income = pd.to_numeric(frame.get("annual_inc", pd.Series([50_000.0] * len(frame))), errors="coerce").fillna(50_000.0)
        util = pd.to_numeric(frame.get("revol_util", pd.Series([50.0] * len(frame))), errors="coerce").fillna(50.0)
        pd_values = (0.72 - (income / 250000.0) + (util / 500.0)).clip(0.05, 0.99).to_numpy()
        return pd.DataFrame({"good": 1.0 - pd_values, "bad": pd_values}).to_numpy()


def _selection_result(plan: PlanRecord | None) -> BestPlanSelectionResult:
    if plan is None:
        return BestPlanSelectionResult(
            best_plan=None,
            selection_outcome="no_valid_winner",
            selection_stage="no_valid_winner",
            invalid_candidates_removed_count=2,
            preferred_pool_invalid_exhausted=True,
            no_valid_candidate_available=True,
            selected_from_widened_valid_pool=False,
        )
    return BestPlanSelectionResult(
        best_plan=plan,
        selection_outcome="selected_valid_winner",
        selection_stage="preferred_valid",
        invalid_candidates_removed_count=0,
        preferred_pool_invalid_exhausted=False,
        no_valid_candidate_available=False,
        selected_from_widened_valid_pool=False,
    )


def test_selection_frame_denied_first_near_prioritizes_denied_then_fills_near() -> None:
    frame = pd.DataFrame(
        {
            "source_row_index": [10, 11, 12, 13, 14],
            "customer_id": ["c-10", "c-11", "c-12", "c-13", "c-14"],
        }
    )
    base_pd = pd.Series([0.62, 0.49, 0.37, 0.34, 0.12], dtype=float)

    selected = collector._selection_frame(
        input_df=frame,
        base_pd=base_pd,
        tau=0.35,
        n_customers=4,
        sample_seed=7,
        cohort_policy="denied_first_near",
        segment_caps_cfg={},
    )

    assert list(selected["selection_reason"])[:3] == ["denied", "denied", "denied"]
    assert selected.iloc[3]["selection_reason"] == "near_fill"
    assert int(selected["denied_base"].astype(int).sum()) == 3
    assert list(selected["batch_index"]) == [0, 1, 2, 3]


def test_collection_parity_failure_marks_internal_review_and_external_conditional() -> None:
    bundle = CustomerArtifactBundle(
        customer_id="cust-parity",
        plans_df=pd.DataFrame([{"plan_id": "plan-a", "action_count": 1}]),
        roadmap={
            "customer_id": "cust-parity",
            "best_plan_id": "plan-a",
            "best_plan_source": "internal",
            "phases": [
                {
                    "phase_id": "phase_1_stabilize",
                    "steps": [{"step_id": "step-1"}],
                }
            ],
            "checkpoints": [
                {"week": 4, "status": "at_risk"},
                {"week": 12, "status": "on_track"},
                {"week": 24, "status": "on_track"},
            ],
            "summary": {
                "decision_status": "APPROVED",
                "decision_status_internal": "APPROVED",
                "decision_policy_version": "v2.1_phase_40_5",
                "best_plan_id": "plan-a",
                "best_constraint_status": "valid",
                "plan_contract_pass": 1,
                "credit_readiness_stage": "week_4",
                "plan_execution_probability": 0.62,
                "approval_dependent_plan_probability": 0.62,
                "offer_acceptance_probability": 0.0,
                "combined_plan_realization_probability": 0.62,
                "expected_pd_improvement": 0.03,
                "nominal_pd_improvement": 0.05,
                "local_explainability_confidence": 0.8,
                "offer_plan": 0,
                "rankable_offer_count": 0,
                "approval_pending_action_count": 0,
            },
        },
        roadmap_steps_df=pd.DataFrame(
            [
                {"customer_id": "cust-parity", "best_plan_id": "plan-a", "action_key": "limit_credit_usage"},
            ]
        ),
        metrics_summary={"customer_id": "cust-parity", "best_plan_id": "plan-a", "best_plan_source": "internal"},
    )
    metrics_row = {
        "customer_id": "cust-parity",
        "best_plan_id": "plan-a",
        "best_plan_source": "internal",
        "decision_status": "APPROVED",
        "decision_status_internal": "APPROVED",
        "selected_decision_status": "APPROVED",
        "selected_plan_status_internal": "",
        "selected_recommendation_text": "",
        "selected_recommendation_source": "selected_plan",
        "selected_action_count": 1,
        "selected_recommendation_projection_version": "v2.2_phase_47",
        "credit_readiness_stage": "week_4",
        "plan_execution_probability": 0.62,
        "approval_dependent_plan_probability": 0.62,
        "offer_acceptance_probability": 0.0,
        "combined_plan_realization_probability": 0.62,
        "best_action_count": 99,
        "zero_step_flag": 0,
        "checkpoint_status_4w": "at_risk",
        "checkpoint_status_12w": "on_track",
        "checkpoint_status_24w": "on_track",
        "raw_contract_pass": 1,
        "parity_pass": 1,
        "data_issue_flag": 0,
    }
    plans_df = pd.DataFrame(
        [
            {"plan_id": "plan-a", "selected_best_flag": 1},
        ]
    )

    parity = collector._validate_customer_artifact_parity(
        bundle=bundle,
        metrics_row=metrics_row,
        plans_df=plans_df,
        steps_df=bundle.roadmap_steps_df,
    )
    assert parity["parity_pass"] == 0
    assert "best_action_count" in parity["parity_mismatch_fields"]

    collector._apply_collection_parity_classification(
        bundle,
        mismatch_fields=parity["parity_mismatch_fields"],
    )
    summary = bundle.roadmap["summary"]
    assert summary["decision_status"] == "CONDITIONAL"
    assert summary["decision_status_internal"] == "NEEDS_REVIEW"
    assert int(summary["parity_pass"]) == 0
    assert int(summary["data_issue_flag"]) == 1
    assert "parity_mismatch" in summary["data_issue_codes"]


def test_augment_plans_df_marks_best_dice_candidate_with_plan_stage() -> None:
    bundle = CustomerArtifactBundle(
        customer_id="cust-dice",
        plans_df=pd.DataFrame(),
        roadmap={
            "customer_id": "cust-dice",
            "best_plan_id": "plan-dice",
            "best_plan_source": "dice",
            "phases": [{"phase_id": "phase_1_stabilize", "steps": [{"step_id": "step-1"}]}],
            "checkpoints": [
                {"week": 4, "status": "at_risk"},
                {"week": 12, "status": "on_track"},
                {"week": 24, "status": "on_track"},
            ],
            "summary": {
                "decision_status": "CONDITIONAL",
                "decision_status_internal": "CONDITIONAL",
                "decision_policy_version": "v2.1_phase_40_5",
                "best_plan_id": "plan-dice",
                "best_constraint_status": "valid",
                "plan_contract_pass": 1,
                "credit_readiness_stage": "week_12",
                "plan_execution_probability": 0.61,
                "approval_dependent_plan_probability": 0.61,
                "offer_acceptance_probability": 0.0,
                "combined_plan_realization_probability": 0.61,
                "expected_pd_improvement": 0.03,
                "nominal_pd_improvement": 0.05,
                "local_explainability_confidence": 0.75,
                "offer_plan": 0,
                "rankable_offer_count": 0,
                "approval_pending_action_count": 0,
            },
        },
        roadmap_steps_df=pd.DataFrame(),
        metrics_summary={"customer_id": "cust-dice", "best_plan_id": "plan-dice", "best_plan_source": "dice"},
    )
    selection_row = pd.Series(
        {
            "batch_index": 0,
            "source_row_index": 11,
            "customer_id": "cust-dice",
            "selection_reason": "pilot_mixed",
            "cohort_policy": "pilot_mixed",
            "cohort_bucket": "near_threshold",
            "selection_policy_name": "pilot_mixed",
            "selection_fill_behavior": "quota_first_deterministic_soft_fill",
        }
    )
    plans_df = pd.DataFrame(
        [
            {"plan_id": "plan-internal", "plan_source": "internal", "plan_stage": "validated", "action_count": 1},
            {"plan_id": "plan-dice", "plan_source": "dice", "plan_stage": "candidate_only", "action_count": 1},
        ]
    )

    augmented = collector._augment_plans_df(
        collection_run_id="run-collection",
        selection_row=selection_row,
        plans_df=plans_df,
        bundle=bundle,
    )

    best_row = augmented.loc[augmented["plan_id"] == "plan-dice"].iloc[0]
    assert int(best_row["selected_best_flag"]) == 1
    assert best_row["plan_source"] == "dice"
    assert best_row["plan_stage"] == "candidate_only"
    assert best_row["selected_decision_status"] == "CONDITIONAL"
    assert best_row["selected_recommendation_source"] == "selected_plan"
    assert int(best_row["selected_action_count"]) == 1


def test_validate_customer_artifact_parity_accepts_no_valid_winner_without_selected_row() -> None:
    bundle = CustomerArtifactBundle(
        customer_id="cust-none",
        plans_df=pd.DataFrame([{"plan_id": "plan-a", "action_count": 1}]),
        roadmap={
            "customer_id": "cust-none",
            "best_plan_id": None,
            "best_plan_source": None,
            "phases": [],
            "checkpoints": [
                {"week": 4, "status": "unknown"},
                {"week": 12, "status": "unknown"},
                {"week": 24, "status": "unknown"},
            ],
            "summary": {
                "decision_status": "REJECTED",
                "decision_status_internal": "REJECTED",
                "decision_policy_version": "v2.1_phase_40_5",
                "best_plan_id": None,
                "best_constraint_status": "",
                "plan_contract_pass": 0,
                "credit_readiness_stage": "not_ready_yet",
                "plan_execution_probability": 0.0,
                "approval_dependent_plan_probability": 0.0,
                "offer_acceptance_probability": 0.0,
                "combined_plan_realization_probability": 0.0,
                "selection_outcome": "no_valid_winner",
                "selection_stage": "no_valid_winner",
                "invalid_candidates_removed_count": 2,
                "preferred_pool_invalid_exhausted": 1,
                "no_valid_candidate_available": 1,
                "selected_from_widened_valid_pool": 0,
            },
        },
        roadmap_steps_df=pd.DataFrame(columns=["customer_id", "best_plan_id", "action_key"]),
        metrics_summary={"customer_id": "cust-none", "best_plan_id": "", "best_plan_source": ""},
    )
    metrics_row = {
        "customer_id": "cust-none",
        "best_plan_id": "",
        "best_plan_source": "",
        "decision_status": "REJECTED",
        "decision_status_internal": "REJECTED",
        "selected_decision_status": "REJECTED",
        "selected_plan_status_internal": "",
        "selected_recommendation_text": "",
        "selected_recommendation_source": "empty_state",
        "selected_action_count": 0,
        "selected_recommendation_projection_version": "v2.2_phase_47",
        "credit_readiness_stage": "not_ready_yet",
        "plan_execution_probability": 0.0,
        "approval_dependent_plan_probability": 0.0,
        "offer_acceptance_probability": 0.0,
        "combined_plan_realization_probability": 0.0,
        "best_action_count": 0,
        "zero_step_flag": 1,
        "checkpoint_status_4w": "unknown",
        "checkpoint_status_12w": "unknown",
        "checkpoint_status_24w": "unknown",
        "raw_contract_pass": 1,
        "parity_pass": 1,
        "data_issue_flag": 0,
        "selection_outcome": "no_valid_winner",
        "selection_stage": "no_valid_winner",
        "invalid_candidates_removed_count": 2,
        "preferred_pool_invalid_exhausted": 1,
        "no_valid_candidate_available": 1,
        "selected_from_widened_valid_pool": 0,
    }
    parity = collector._validate_customer_artifact_parity(
        bundle=bundle,
        metrics_row=metrics_row,
        plans_df=pd.DataFrame([{"plan_id": "plan-a", "selected_best_flag": 0}]),
        steps_df=bundle.roadmap_steps_df,
    )

    assert parity["parity_pass"] == 1
    assert parity["parity_mismatch_fields"] == []


def test_validate_customer_artifact_parity_rejects_selected_dice_winner_that_is_not_eligible() -> None:
    bundle = CustomerArtifactBundle(
        customer_id="cust-dice-invalid",
        plans_df=pd.DataFrame([{"plan_id": "dice-plan", "action_count": 1}]),
        roadmap={
            "customer_id": "cust-dice-invalid",
            "best_plan_id": "dice-plan",
            "best_plan_source": "dice",
            "phases": [{"phase_id": "phase_1_stabilize", "steps": [{"step_id": "step-1"}]}],
            "checkpoints": [
                {"week": 4, "status": "at_risk"},
                {"week": 12, "status": "on_track"},
                {"week": 24, "status": "on_track"},
            ],
            "summary": {
                "decision_status": "CONDITIONAL",
                "decision_status_internal": "CONDITIONAL",
                "decision_policy_version": "v2.2_phase_46",
                "best_plan_id": "dice-plan",
                "best_constraint_status": "valid",
                "plan_contract_pass": 1,
                "credit_readiness_stage": "week_12",
                "plan_execution_probability": 0.58,
                "approval_dependent_plan_probability": 0.58,
                "offer_acceptance_probability": 0.0,
                "combined_plan_realization_probability": 0.58,
                "best_action_count": 1,
                "zero_step_flag": 0,
            },
        },
        roadmap_steps_df=pd.DataFrame([{"customer_id": "cust-dice-invalid", "best_plan_id": "dice-plan", "action_key": "limit_credit_usage"}]),
        metrics_summary={"customer_id": "cust-dice-invalid", "best_plan_id": "dice-plan", "best_plan_source": "dice"},
    )
    metrics_row = {
        "customer_id": "cust-dice-invalid",
        "best_plan_id": "dice-plan",
        "best_plan_source": "dice",
        "decision_status": "CONDITIONAL",
        "decision_status_internal": "CONDITIONAL",
        "selected_decision_status": "CONDITIONAL",
        "selected_plan_status_internal": "",
        "selected_recommendation_text": "",
        "selected_recommendation_source": "selected_plan",
        "selected_action_count": 1,
        "selected_recommendation_projection_version": "v2.2_phase_47",
        "credit_readiness_stage": "week_12",
        "plan_execution_probability": 0.58,
        "approval_dependent_plan_probability": 0.58,
        "offer_acceptance_probability": 0.0,
        "combined_plan_realization_probability": 0.58,
        "best_action_count": 1,
        "zero_step_flag": 0,
        "checkpoint_status_4w": "at_risk",
        "checkpoint_status_12w": "on_track",
        "checkpoint_status_24w": "on_track",
        "raw_contract_pass": 1,
        "parity_pass": 1,
        "data_issue_flag": 0,
        "selection_outcome": "selected_valid_winner",
        "selection_stage": "preferred_valid",
        "invalid_candidates_removed_count": 0,
        "preferred_pool_invalid_exhausted": 0,
        "no_valid_candidate_available": 0,
        "selected_from_widened_valid_pool": 0,
    }
    plans_df = pd.DataFrame(
        [
            {
                "plan_id": "dice-plan",
                "plan_source": "dice",
                "selected_best_flag": 1,
                "recommendation_validity_status": "valid",
                "dice_contender_eligible": 0,
                "dice_annotation_complete": 0,
                "dice_semantic_quality_status": "invalid",
            }
        ]
    )

    parity = collector._validate_customer_artifact_parity(
        bundle=bundle,
        metrics_row=metrics_row,
        plans_df=plans_df,
        steps_df=bundle.roadmap_steps_df,
    )

    assert parity["parity_pass"] == 0
    assert "selected_best_dice_ineligible" in parity["parity_mismatch_fields"]
    assert "selected_best_dice_annotation_incomplete" in parity["parity_mismatch_fields"]
    assert "selected_best_dice_semantic_invalid" in parity["parity_mismatch_fields"]


def test_collection_summary_markdown_reports_dice_lane_rates() -> None:
    selection_df = pd.DataFrame(
        [
            {
                "customer_id": "cust-1",
                "selection_reason": "pilot",
                "denied_base": 1,
                "risk_band": "near",
            }
        ]
    )
    metrics_df = pd.DataFrame(
        [
            {
                "decision_status": "CONDITIONAL",
                "best_action_count": 1,
                "best_cost_usd": 12.0,
                "best_plan_execution_probability": 0.61,
                "candidate_source_entropy": 0.2,
                "candidate_pool_diversity_index": 0.3,
                "candidate_non_empty_count": 2,
                "candidate_pool_count": 3,
                "best_plan_source": "dice",
                "offer_ready_contender_share": 0.0,
                "provisional_offer_share": 0.0,
                "approval_shell_only_share": 0.0,
                "hard_invalid_plan_rate": 0.0,
                "numeric_warning_rate": 0.1,
                "best_plan_warning_rate": 1.0,
                "selected_invalid_winner_flag": 0,
                "selection_outcome": "selected_valid_winner",
                "selected_from_widened_valid_pool": 0,
                "preferred_pool_invalid_exhausted": 0,
                "directional_invalid_count": 0,
                "economic_warning_count": 1,
                "critical_field_null_count": 0,
                "missing_checkpoint_status_count": 0,
                "raw_contract_pass": 1,
                "parity_pass": 1,
                "data_issue_flag": 0,
                "dice_candidate_count": 2,
                "dice_contender_eligible_count": 1,
                "dice_invalid_candidate_count": 1,
                "dice_warning_candidate_count": 1,
                "dice_all_candidates_ineligible": 0,
                "dice_fallback_flag": 1,
                "selected_dice_flag": 1,
                "selected_dice_valid_flag": 1,
                "operator_selected_decision_status": "CONDITIONAL",
                "operator_rendered_blocker_count": 1,
                "operator_rendered_action_count": 1,
                "operator_top_blocker_codes_json": json.dumps(["driver:realization_anchor"]),
                "operator_first_action_blocker_codes_json": json.dumps(["driver:realization_anchor"]),
                "operator_upgrade_condition_text": "realization_anchor 0.40 -> 0.50",
                "operator_readiness_render_mode": "conditional_time_gate",
                "operator_fallback_blocker_suppressed": 0,
                "selected_recommendation_source": "selected_plan",
            }
        ]
    )
    steps_df = pd.DataFrame([{"action_key": "limit_credit_usage", "action_class": "behavioral"}])

    markdown = collector._collection_summary_markdown(
        selection_df=selection_df,
        metrics_df=metrics_df,
        steps_df=steps_df,
        manifest_rel_root="tables/customer_artifact_collection",
        selection_metadata={
            "selection_policy_name": "pilot_mixed",
            "selection_fill_behavior": "quota",
            "cohort_purpose": "test",
        },
        funnel_summary={
            "approved_share": 0.0,
            "conditional_share": 1.0,
            "rejected_share": 0.0,
            "internal_needs_review_share": 0.0,
            "approve_plus_conditional_share": 1.0,
            "conditional_to_approved_potential": 0.0,
        },
        readiness_summary={"distribution": {"week_12": {"count": 1}}},
        calibration_summary={"policy_version_evaluated": "v2.2", "candidate_policy_versions_compared": [], "baseline_policy_metrics": {}},
        outcome_rule_summary={"candidate_outcome_rule_versions_compared": [], "recommended_outcome_rule_status": "no_safe_uplift"},
        operator_briefing={"priority_queues": [], "dominant_blockers": [], "conditional_hotspots": [], "offer_hotspots": [], "review_guidance": [], "health_note": ""},
        movement_guardrail_summary={
            "dominant_movement_bottleneck": "structural_cohort_limited",
            "movement_guardrail_summary": "The cohort is structurally too far from near-term movement.",
            "promotion_blocker_summary": "No candidate family created promotable movement under the shipped trust and risk guardrails.",
            "threshold_family": {"status": "no_movement"},
            "offer_readiness_family": {"status": "no_movement"},
            "trust_guardrails": {"regression_detected": False},
            "recommendation_space": {
                "signal_score": 1,
                "top_blocker_title": "Expected impact is still too small",
                "non_empty_contender_share": 0.6667,
                "approval_shell_only_share": 0.0,
            },
            "structural_cohort": {
                "signal_score": 3,
                "top_blocker_title": "Most files are too far from near-term readiness",
                "not_ready_share": 1.0,
                "near_term_readiness_share": 0.0,
                "offer_ready_contender_share": 0.0,
                "high_risk_share": 0.0,
            },
        },
    )

    assert "## DICE Lane" in markdown
    assert "DICE candidate count: 2" in markdown
    assert "Selected DICE valid rate: 1.0000" in markdown
    assert "## Operator Packet Coherence" in markdown
    assert "Approved with blocker count: 0" in markdown
    assert "Recommended candidate status: no_safe_uplift" in markdown
    assert "## Outcome Rules" in markdown
    assert "## Funnel Guardrails" in markdown
    assert "Dominant movement bottleneck: structural_cohort_limited" in markdown
    assert "## Movement Diagnosis" in markdown
    assert "Policy profile catalog:" in markdown
    assert "Policy recommendation summary:" in markdown


def test_customer_artifact_bundle_matches_single_customer_row_shape(tmp_path: Path) -> None:
    action = PlanAction(
        feature_name="revol_util",
        current_value=71.0,
        target_value=52.0,
        delta=-19.0,
        time_months=1,
        estimated_cost_usd=15.0,
        action_key="limit_credit_usage",
        action_class="behavioral",
        action_title="Limit credit usage",
        action_group_id="limit_credit_usage:phase_1_stabilize",
        action_execution_probability=0.66,
        difficulty_score=0.41,
        difficulty_label="moderate",
        difficulty_drivers={
            "burden": 0.2,
            "horizon": 0.1,
            "action_class": 0.3,
            "coordination_load": 0.1,
        },
        approval_friction=0.0,
        diagnostic_flags=["utilization_relief"],
    )
    plan = PlanRecord(
        plan_id="bundle-plan",
        customer_id="cust-bundle",
        run_id="run-bundle",
        horizon_months=6,
        strategy="balanced",
        actions=[action],
        phases=[
            TrajectoryPhase(
                phase_id="phase_1_stabilize",
                phase_title="Ilk 4 Hafta - Stabilizasyon",
                target_window_weeks="1-4",
                target_window_months=[1],
                review_week=4,
                target_pd=0.40,
                gate_pass_target=False,
                steps=[action],
            ),
            TrajectoryPhase(
                phase_id="phase_2_build",
                phase_title="1-3 Ay - Guclendirme",
                target_window_weeks="5-12",
                target_window_months=[2, 3],
                review_week=12,
                target_pd=0.32,
                gate_pass_target=True,
                steps=[],
            ),
            TrajectoryPhase(
                phase_id="phase_3_optimize",
                phase_title="3-6 Ay - Optimizasyon",
                target_window_weeks="13-24",
                target_window_months=[4, 5, 6],
                review_week=24,
                target_pd=0.30,
                gate_pass_target=True,
                steps=[],
            ),
        ],
        trajectory_checkpoints=[
            TrajectoryCheckpoint(
                week=4,
                month=1,
                phase_id="phase_1_stabilize",
                checkpoint_type="primary",
                checkpoint_label="early_stabilization",
                predicted_pd=0.40,
                pd_delta_vs_base=0.04,
                gate_pass_estimate=0,
                checkpoint_priority=1,
                status="at_risk",
            ),
            TrajectoryCheckpoint(
                week=12,
                month=3,
                phase_id="phase_2_build",
                checkpoint_type="confirmation",
                checkpoint_label="approval_readiness",
                predicted_pd=0.32,
                pd_delta_vs_base=0.12,
                gate_pass_estimate=1,
                checkpoint_priority=2,
                status="on_track",
            ),
            TrajectoryCheckpoint(
                week=24,
                month=6,
                phase_id="phase_3_optimize",
                checkpoint_type="stability",
                checkpoint_label="durable_optimization",
                predicted_pd=0.30,
                pd_delta_vs_base=0.14,
                gate_pass_estimate=1,
                checkpoint_priority=3,
                status="on_track",
            ),
        ],
        predicted_pd=0.30,
        score=0.2,
        robust_score=0.2,
        status="APPROVED",
        constraint_status="valid",
        trajectory_status="on_track",
        next_review_week=4,
        plan_execution_probability=0.66,
        mean_group_difficulty_score=0.41,
        peak_group_difficulty_score=0.41,
        dominant_difficulty_label="moderate",
        follow_through_readiness_label="moderate",
    )

    roadmap = _build_customer_roadmap(
        customer_id="cust-bundle",
        base_pd=0.44,
        tau=0.35,
        best=plan,
        best_source="internal",
        selection_result=_selection_result(plan),
        row=pd.Series({"revol_util": 71.0}),
        model=_DummyModel(),
        calibrator=None,
        feature_cols=["revol_util"],
        local_reason_bundle={
            "reasons": [{"feature": "revol_util", "direction": "increase_risk", "abs_contribution": 0.2}],
            "meta": {"explainability_confidence": 0.8, "stability_score": 0.9, "baseline_drift_l1": 0.02},
        },
    )
    path_records = build_recourse_path_records(
        [plan],
        selected_plan_id=plan.plan_id,
        base_pd=0.44,
        tau=0.35,
    )
    bundle = build_customer_artifact_bundle(
        customer_id="cust-bundle",
        model_version="model-001",
        base_pd=0.44,
        search_profile={"is_denied_target": True, "search_cfg": {"time_budget_ms": 0}},
        segment_context={"income_band": "q2", "risk_band": "high", "segment_caps_applied": False},
        validated=[plan],
        candidate_pool=[plan],
        best=plan,
        best_source="internal",
        selection_result=_selection_result(plan),
        roadmap=roadmap,
        msi=0.2,
        alpha=0.05,
        robust_objective="cvar",
        robust_cvar_quantile=0.9,
        local_reason_bundle={
            "reasons": [{"feature": "revol_util"}],
            "meta": {"explainability_confidence": 0.8, "stability_score": 0.9, "baseline_drift_l1": 0.02},
        },
        adverse_action_reasons=[{"feature": "revol_util"}],
        dice_backend="skipped",
        dice_records=[],
        dice_telemetry={"method_requested": "random", "method_used": "skipped", "fallback_reason": "skipped_by_policy"},
        search_elapsed_ms=12.5,
        fairness_penalty=0.0,
        decision_log_record={"decision_id": "d-1", "selection_propensity": 1.0},
        decision_log_summary={"decision_log_completeness": 1.0},
        path_records=path_records,
    )

    expected_plan_row = _plan_to_row(plan)
    expected_plan_row["plan_stage"] = "validated"
    assert bundle.plans_df.to_dict(orient="records")[0] == expected_plan_row
    assert bundle.roadmap_steps_df.iloc[0]["customer_id"] == "cust-bundle"
    assert bundle.metrics_summary["best_plan_id"] == "bundle-plan"
    assert bundle.metrics_summary["selected_path_id"] == plan.path_id
    assert bundle.metrics_summary["selected_path_type"] == "customer_only"
    assert bundle.metrics_summary["selected_path_customer_summary"]
    assert bundle.metrics_summary["selected_path_operator_summary"]
    assert bundle.metrics_summary["selected_path_render_version"] == "phase59_action_semantics_rendering_v1"
    assert not bundle.paths_df.empty
    first_path = bundle.paths_df.iloc[0].to_dict()
    assert first_path["customer_summary"]["en"]
    assert first_path["operator_summary"]["en"]
    assert first_path["render_version"] == "phase59_action_semantics_rendering_v1"

    out_dir = tmp_path / "raw" / "cust-bundle"
    paths = write_customer_artifact_bundle(bundle, out_dir)
    assert paths["plans_json"].exists()
    assert paths["roadmap_json"].exists()
    assert paths["metrics_json"].exists()
    assert paths["paths_json"].exists()
    assert paths["roadmap_steps_csv"].exists()


def test_run_customer_artifact_collection_emits_raw_and_flat_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processed_root = tmp_path / "processed"
    processed_root.mkdir(parents=True, exist_ok=True)

    features_path = tmp_path / "features.yaml"
    features_path.write_text(
        yaml.safe_dump({"features": ["annual_inc", "revol_util"], "target": {"name": "loan_status"}}),
        encoding="utf-8",
    )
    base_config = tmp_path / "base.yaml"
    base_config.write_text(
        yaml.safe_dump({"features_config": str(features_path), "paths": {"processed_data": str(processed_root)}}),
        encoding="utf-8",
    )
    model_config = tmp_path / "model.yaml"
    model_config.write_text(
        yaml.safe_dump({"decision": {"tau_0": 0.35}, "registry": {"path": str(tmp_path / "models")}}),
        encoding="utf-8",
    )
    recourse_config = tmp_path / "recourse.yaml"
    recourse_config.write_text(yaml.safe_dump({"segment_caps": {}}), encoding="utf-8")
    causality_config = tmp_path / "causality.yaml"
    causality_config.write_text(yaml.safe_dump({"graph": {"output_path": str(tmp_path / "graph.json")}}), encoding="utf-8")
    safety_config = tmp_path / "safety.yaml"
    safety_config.write_text(yaml.safe_dump({}), encoding="utf-8")
    macro_config = tmp_path / "macro.yaml"
    macro_config.write_text(yaml.safe_dump({}), encoding="utf-8")

    train_df = pd.DataFrame(
        [
            {"annual_inc": 50000.0, "revol_util": 55.0, "loan_status": 0},
            {"annual_inc": 62000.0, "revol_util": 42.0, "loan_status": 0},
        ]
    )
    test_df = pd.DataFrame(
        [
            {"customer_id": "cust-1", "annual_inc": 25000.0, "revol_util": 88.0, "loan_status": 1},
            {"customer_id": "cust-2", "annual_inc": 32000.0, "revol_util": 74.0, "loan_status": 1},
            {"customer_id": "cust-3", "annual_inc": 54000.0, "revol_util": 44.0, "loan_status": 0},
            {"customer_id": "cust-4", "annual_inc": 90000.0, "revol_util": 18.0, "loan_status": 0},
        ]
    )
    train_df.to_parquet(processed_root / "train.parquet", index=False)
    test_csv = processed_root / "test.csv"
    test_df.to_csv(test_csv, index=False)

    monkeypatch.setattr(
        collector,
        "load_model_bundle",
        lambda **kwargs: (_DummyModel(), None, {"model_version": "model-001"}, None),
    )
    monkeypatch.setattr(
        collector,
        "predict_proba_pd",
        lambda model, calibrator, frame: pd.to_numeric(frame["revol_util"], errors="coerce").fillna(0.0).div(100.0).to_numpy(),
    )
    monkeypatch.setattr(collector, "run_rex_adapter", lambda *args, **kwargs: {})

    def _fake_customer_result(**kwargs):
        customer_id = str(kwargs["customer_id"])
        plans_df = pd.DataFrame(
            [
                {"plan_id": f"{customer_id}-plan-a", "plan_score": 0.4, "plan_source": "internal", "plan_stage": "validated"},
                {"plan_id": f"{customer_id}-plan-b", "plan_score": 0.3, "plan_source": "dice", "plan_stage": "candidate_only"},
            ]
        )
        steps_df = pd.DataFrame(
            [
                {
                    "customer_id": customer_id,
                    "best_plan_id": f"{customer_id}-plan-a",
                    "phase_id": "phase_1_stabilize",
                    "phase_title": "Stabilize",
                    "target_window_weeks": "1-4",
                    "action_key": "limit_credit_usage",
                    "action_class": "behavioral",
                    "action_title": "Limit credit usage",
                    "action_group_id": f"{customer_id}:phase_1",
                    "composite_action": 0,
                    "feature_name": "revol_util",
                    "metric_key": "credit_utilization_pct",
                    "unit": "percentage_points",
                    "current_value": 70.0,
                    "target_value": 45.0,
                    "delta": -25.0,
                    "time_months": 1,
                    "due_month": 1,
                    "direction": "decrease",
                    "generation_notes_json": "[]",
                    "estimated_cost_usd": 25.0,
                    "requires_institutional_approval": 0,
                    "approval_pending_semantic_only": 0,
                    "action_status": "valid",
                    "constraint_family": "",
                    "constraint_reason_codes_json": "[]",
                    "was_clipped": 0,
                    "repair_applied": 0,
                    "dependency_gate": 0,
                    "semantic_preserved": True,
                },
                {
                    "customer_id": customer_id,
                    "best_plan_id": f"{customer_id}-plan-a",
                    "phase_id": "phase_2_build",
                    "phase_title": "Build",
                    "target_window_weeks": "5-12",
                    "action_key": "pay_down_revolving_balance",
                    "action_class": "structural",
                    "action_title": "Pay down balance",
                    "action_group_id": f"{customer_id}:phase_2",
                    "composite_action": 0,
                    "feature_name": "revol_util",
                    "metric_key": "credit_utilization_pct",
                    "unit": "percentage_points",
                    "current_value": 45.0,
                    "target_value": 35.0,
                    "delta": -10.0,
                    "time_months": 3,
                    "due_month": 3,
                    "direction": "decrease",
                    "generation_notes_json": "[]",
                    "estimated_cost_usd": 55.0,
                    "requires_institutional_approval": 0,
                    "approval_pending_semantic_only": 0,
                    "action_status": "valid",
                    "constraint_family": "",
                    "constraint_reason_codes_json": "[\"capacity_cap\"]",
                    "was_clipped": 1,
                    "repair_applied": 0,
                    "dependency_gate": 0,
                    "semantic_preserved": True,
                },
            ]
        )
        bundle = CustomerArtifactBundle(
            customer_id=customer_id,
            plans_df=plans_df,
            roadmap={
                "customer_id": customer_id,
                "best_plan_id": f"{customer_id}-plan-a",
                "best_plan_source": "internal",
                "summary": {
                    "decision_status": "CONDITIONAL",
                    "decision_status_internal": "NEEDS_REVIEW",
                    "decision_policy_version": "v2.1_phase_40_5",
                    "best_plan_id": f"{customer_id}-plan-a",
                    "best_constraint_status": "valid",
                    "plan_contract_pass": 1,
                    "credit_readiness_stage": "week_12",
                    "plan_execution_probability": 0.61,
                    "approval_dependent_plan_probability": None,
                    "offer_acceptance_probability": None,
                    "combined_plan_realization_probability": None,
                    "expected_pd_improvement": 0.03,
                    "nominal_pd_improvement": 0.05,
                    "local_explainability_confidence": 0.75,
                    "offer_plan": 0,
                    "rankable_offer_count": 0,
                    "approval_pending_action_count": 0,
                },
                "phases": [
                    {
                        "phase_id": "phase_1_stabilize",
                        "steps": [{"step_id": f"{customer_id}:step-1"}],
                    },
                    {
                        "phase_id": "phase_2_build",
                        "steps": [{"step_id": f"{customer_id}:step-2"}],
                    },
                ],
                "checkpoints": [
                    {"week": 4, "status": "at_risk"},
                    {"week": 12, "status": "on_track"},
                    {"week": 24, "status": "on_track"},
                ],
            },
            roadmap_steps_df=steps_df,
            metrics_summary={
                "customer_id": customer_id,
                "best_status": "NEEDS_REVIEW",
                "best_plan_id": f"{customer_id}-plan-a",
                "best_plan_source": "internal",
                "plan_count": 2,
                "approved_count": 0,
                "denied_target_mode": True,
            },
        )
        return CustomerRecourseRunResult(
            bundle=bundle,
            local_reason_bundle={"reasons": [], "meta": {}},
            adverse_action_reasons=[],
            dice_df=pd.DataFrame(),
            dice_records=[],
            dice_backend="skipped",
            dice_telemetry={"method_requested": "random", "method_used": "skipped", "fallback_reason": "skipped_by_policy"},
            candidate_pool_df=pd.DataFrame(),
            decision_log_record={"decision_id": f"decision-{customer_id}", "selection_propensity": 1.0},
            decision_log_summary={"decision_log_completeness": 1.0},
        )

    monkeypatch.setattr(collector, "generate_customer_recourse_artifacts", _fake_customer_result)

    run_ctx = collector.main(
        [
            "--base_config",
            str(base_config),
            "--model_config",
            str(model_config),
            "--recourse_config",
            str(recourse_config),
            "--causality_config",
            str(causality_config),
            "--safety_config",
            str(safety_config),
            "--macro_config",
            str(macro_config),
            "--input_data_path",
            str(test_csv),
            "--input_data_format",
            "csv",
            "--n_customers",
            "3",
            "--cohort_policy",
            "denied_first_near",
            "--artifact_root",
            str(tmp_path / "runs"),
        ]
    )

    collection_root = run_ctx.tables_dir / "customer_artifact_collection"
    raw_dirs = [path for path in (collection_root / "raw").iterdir() if path.is_dir()]
    assert len(raw_dirs) == 3
    for raw_dir in raw_dirs:
        assert (raw_dir / "customer_roadmap.json").exists()
        assert (raw_dir / "plans.json").exists()
        assert (raw_dir / "metrics.json").exists()
        assert (raw_dir / "customer_roadmap_steps.csv").exists()

    metrics_df = pd.read_csv(collection_root / "flat" / "customer_metrics.csv")
    plans_df = pd.read_csv(collection_root / "flat" / "customer_plans.csv")
    steps_df = pd.read_csv(collection_root / "flat" / "customer_roadmap_steps.csv")
    selection_df = pd.read_csv(collection_root / "flat" / "customer_selection.csv")
    assert len(metrics_df) == 3
    assert len(plans_df) == 6
    assert len(steps_df) == 6
    assert len(selection_df) == 3
    assert (collection_root / "collection_manifest.json").exists()
    assert (collection_root / "collection_summary.md").exists()
    assert (collection_root / "operator_review_briefing.md").exists()
    operator_dirs = [path for path in (collection_root / "operator_packets").iterdir() if path.is_dir()]
    assert len(operator_dirs) == 3
    for operator_dir in operator_dirs:
        assert (operator_dir / "operator_packet.json").exists()
        assert (operator_dir / "operator_packet.md").exists()
    assert (collection_root / "calibration" / "funnel_summary.json").exists()
    assert (collection_root / "calibration" / "readiness_distribution.csv").exists()
    assert (collection_root / "calibration" / "status_by_readiness.csv").exists()
    assert (collection_root / "calibration" / "policy_comparison.csv").exists()
    assert (collection_root / "calibration" / "decision_shift_matrix.csv").exists()
    assert (collection_root / "calibration" / "segment_breakdown.csv").exists()
    assert (collection_root / "calibration" / "outcome_rule_comparison.csv").exists()
    assert (collection_root / "calibration" / "outcome_rule_shift_matrix.csv").exists()
    assert (collection_root / "calibration" / "outcome_rule_customer_effects.csv").exists()
    assert (collection_root / "calibration" / "outcome_rule_profile_catalog.json").exists()
    assert (collection_root / "calibration" / "outcome_rule_recommendation_summary.json").exists()
    assert (collection_root / "calibration" / "policy_baseline_selection.json").exists()
    assert (collection_root / "calibration" / "policy_candidate_disposition.csv").exists()
    assert (collection_root / "calibration" / "movement_guardrail_summary.json").exists()
    assert (collection_root / "calibration" / "movement_promotion_blockers.csv").exists()
    assert (collection_root / "calibration" / "movement_bottleneck_breakdown.csv").exists()
    assert (collection_root / "calibration" / "movement_ceiling_breakdown.csv").exists()
    assert (collection_root / "calibration" / "movement_guardrail_review.md").exists()
    assert (collection_root / "calibration" / "calibration_review.md").exists()
    assert set(metrics_df["decision_status"]) == {"CONDITIONAL"}
    assert set(metrics_df["decision_status_internal"]) == {"CONDITIONAL"}
    assert set(metrics_df["decision_policy_version"]) == {"v2.1_phase_40_5"}
    assert set(metrics_df["conditional_type"]) == {"TIME_GATED"}
    assert (metrics_df["decision_confidence"] > 0).all()
    assert (metrics_df["expected_readiness"] == "week_12").all()
    assert metrics_df["upgrade_condition"].fillna("").astype(str).str.len().gt(0).all()
    assert (metrics_df["best_action_count"] == 2).all()
    assert (metrics_df["parity_pass"] == 1).all()
    assert (metrics_df["raw_contract_pass"] == 1).all()
    assert (metrics_df["data_issue_flag"] == 0).all()
    assert (metrics_df["checkpoint_status_4w"] == "at_risk").all()
    assert "data_issue_codes_json" in metrics_df.columns
    assert "offer_needed_flag" in metrics_df.columns
    assert "candidate_pool_diversity_index" in metrics_df.columns
    assert "candidate_source_entropy" in metrics_df.columns
    assert "path_count" in metrics_df.columns
    assert "rankable_path_count" in metrics_df.columns
    assert "multi_path_flag" in metrics_df.columns
    assert "action_diversity_index" in metrics_df.columns
    assert "non_utilization_action_rate" in metrics_df.columns
    assert "institution_action_rate" in metrics_df.columns
    assert "best_execution_aware_value" in metrics_df.columns
    assert "candidate_source_internal_count" in metrics_df.columns
    assert "candidate_source_internal_present" in metrics_df.columns
    assert "candidate_non_empty_count" in metrics_df.columns
    assert "candidate_approval_shell_only_count" in metrics_df.columns
    assert "candidate_empty_removed_count" in metrics_df.columns
    assert "offer_ready_contender_share" in metrics_df.columns
    assert "provisional_offer_share" in metrics_df.columns
    assert "approval_shell_only_share" in metrics_df.columns
    assert "recommendation_validity_status" in metrics_df.columns
    assert "recommendation_invalid_action_count" in metrics_df.columns
    assert "recommendation_warning_action_count" in metrics_df.columns
    assert "recommendation_sanity_flag" in metrics_df.columns
    assert "hard_invalid_plan_rate" in metrics_df.columns
    assert "numeric_warning_rate" in metrics_df.columns
    assert "best_plan_warning_rate" in metrics_df.columns
    assert "directional_invalid_count" in metrics_df.columns
    assert "economic_warning_count" in metrics_df.columns
    assert "best_contender_bucket" in metrics_df.columns
    assert "best_offer_maturity" in metrics_df.columns
    assert "operator_packet_relpath" in metrics_df.columns
    assert "operator_top_blocker_codes_json" in metrics_df.columns
    assert "operator_next_best_action_keys_json" in metrics_df.columns
    assert "operator_rendered_action_count" in metrics_df.columns
    assert "operator_rendered_blocker_count" in metrics_df.columns
    assert "operator_first_action_blocker_codes_json" in metrics_df.columns
    assert "operator_upgrade_condition_text" in metrics_df.columns
    assert "operator_blocker_render_source" in metrics_df.columns
    assert "operator_action_render_source" in metrics_df.columns
    assert "operator_readiness_render_mode" in metrics_df.columns
    assert "operator_packet_coherence_codes_json" in metrics_df.columns
    assert "operator_fallback_blocker_suppressed" in metrics_df.columns
    assert "operator_offer_state_en" in metrics_df.columns
    assert "operator_downside_risk_en" in metrics_df.columns
    assert "selected_outcome_rule_applied" in metrics_df.columns
    assert "selected_outcome_rule_profile_version" in metrics_df.columns
    assert "selected_outcome_rule_source" in metrics_df.columns
    assert "selected_outcome_rule_transition" in metrics_df.columns
    assert "selected_outcome_rule_note" in metrics_df.columns
    assert "operator_selected_outcome_rule_note_en" in metrics_df.columns
    assert "selected_best_flag" in plans_df.columns
    assert "plan_step_count" in plans_df.columns
    assert "plan_contract_pass" in plans_df.columns
    assert "plan_stage" in plans_df.columns
    assert "recommendation_validity_status" in plans_df.columns
    assert "recommendation_validity_codes_json" in plans_df.columns
    assert "recommendation_sanity_flag" in plans_df.columns
    assert "recommendation_validity_status" in steps_df.columns
    assert "recommendation_validity_codes_json" in steps_df.columns
    assert "recommendation_sanity_flag" in steps_df.columns
    assert "cohort_bucket" in selection_df.columns
    assert "selection_policy_name" in selection_df.columns
    assert "selection_fill_behavior" in selection_df.columns

    manifest = json.loads((collection_root / "collection_manifest.json").read_text(encoding="utf-8"))
    assert "contract_health" in manifest
    assert "source_mix_summary" in manifest
    assert "plan_quality_summary" in manifest
    assert "raw_flat_mismatch_count" in manifest["contract_health"]
    assert manifest["selection_policy_name"] == "denied_first_near"
    assert "funnel_summary" in manifest
    assert "readiness_summary" in manifest
    assert "calibration_summary" in manifest
    assert "calibration_files" in manifest
    assert "operator_files" in manifest
    assert "operator_packet_coherence_summary" in manifest
    assert "operator_briefing_summary" in manifest
    assert "candidate_policy_versions_compared" in manifest
    assert "candidate_outcome_rule_versions_compared" in manifest
    assert "recommended_outcome_rule_status" in manifest
    assert "outcome_rule_summary" in manifest
    assert "preferred_demo_profile" in manifest
    assert "fallback_demo_profile" in manifest
    assert "policy_baseline_selection_reason" in manifest
    assert "threshold_family_promotion_status" in manifest
    assert "outcome_rule_family_promotion_status" in manifest
    assert "next_milestone_focus" in manifest
    assert "policy_baseline_selection" in manifest
    assert "dominant_movement_bottleneck" in manifest
    assert "movement_guardrail_summary" in manifest
    assert "promotion_blocker_summary" in manifest
    assert "phase_60_evidence_version" in manifest
    assert "phase_60_overall_movement_conclusion" in manifest
    assert "phase_60_overall_trust_conclusion" in manifest
    assert "phase_60_files" in manifest
    assert set(manifest["funnel_summary"]).issuperset(
        {"approved_share", "conditional_share", "rejected_share", "internal_needs_review_share"}
    )
    assert set(manifest["plan_quality_summary"]).issuperset(
        {"hard_invalid_plan_rate", "numeric_warning_rate", "best_plan_warning_rate"}
    )
    assert set(manifest["operator_packet_coherence_summary"]).issuperset(
        {
            "approved_with_blocker_count",
            "approved_with_action_count",
            "approved_with_upgrade_condition_count",
            "empty_state_with_action_count",
            "action_blocker_mismatch_count",
            "readiness_decision_mismatch_count",
            "fallback_blocker_suppressed_count",
        }
    )
    assert "movement_guardrail_summary_json" in manifest["calibration_files"]
    assert "policy_baseline_selection_json" in manifest["calibration_files"]
    assert "policy_candidate_disposition_csv" in manifest["calibration_files"]
    assert "movement_promotion_blockers_csv" in manifest["calibration_files"]
    assert "movement_bottleneck_breakdown_csv" in manifest["calibration_files"]
    assert "movement_ceiling_breakdown_csv" in manifest["calibration_files"]
    assert "movement_guardrail_review_md" in manifest["calibration_files"]
    assert "cohort_evidence_summary_json" in manifest["phase_60_files"]
    assert "trust_regression_table_csv" in manifest["phase_60_files"]
    assert (collection_root / "phase_60" / "phase_60_collection_cohort_evidence_summary.json").exists()
    assert (collection_root / "phase_60" / "phase_60_collection_cohort_evidence_summary.md").exists()

    summary_md = (collection_root / "collection_summary.md").read_text(encoding="utf-8")
    review_md = (collection_root / "calibration" / "calibration_review.md").read_text(encoding="utf-8")
    movement_review_md = (collection_root / "calibration" / "movement_guardrail_review.md").read_text(encoding="utf-8")
    assert "## Contract Health" in summary_md
    assert "Decision status distribution" in summary_md
    assert "## Decision Funnel" in summary_md
    assert "## Readiness" in summary_md
    assert "## Calibration" in summary_md
    assert "## Outcome Rules" in summary_md
    assert "## Baseline Selection" in summary_md
    assert "## Funnel Guardrails" in summary_md
    assert "## Movement Diagnosis" in summary_md
    assert "## Planner Source Mix" in summary_md
    assert "## Planner Quality" in summary_md
    assert "Hard-invalid plan rate" in summary_md
    assert "Numeric warning rate" in summary_md
    assert "## Phase 60 Cohort Evidence" in summary_md
    assert "## Operator Packet Coherence" in summary_md
    assert "## Operator Review" in summary_md
    assert "Likely-to-upgrade-soon queue" in summary_md
    assert "analysis-only" in review_md
    assert "## Outcome Rules" in review_md
    assert "# Movement Guardrail Review" in movement_review_md
    assert "Preferred demo profile" in summary_md


def test_run_customer_artifact_collection_falls_back_to_sample_csv_when_processed_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processed_root = tmp_path / "processed"
    processed_root.mkdir(parents=True, exist_ok=True)

    features_path = tmp_path / "features.yaml"
    features_path.write_text(
        yaml.safe_dump({"features": ["annual_inc", "revol_util"], "target": {"name": "loan_status"}}),
        encoding="utf-8",
    )
    base_config = tmp_path / "base.yaml"
    base_config.write_text(
        yaml.safe_dump(
            {
                "features_config": str(features_path),
                "paths": {"processed_data": str(processed_root)},
                "prepare_data": {"test_size": 0.2, "random_state": 42, "out_of_time": False},
            }
        ),
        encoding="utf-8",
    )
    model_config = tmp_path / "model.yaml"
    model_config.write_text(
        yaml.safe_dump({"decision": {"tau_0": 0.35}, "registry": {"path": str(tmp_path / "models")}}),
        encoding="utf-8",
    )
    recourse_config = tmp_path / "recourse.yaml"
    recourse_config.write_text(yaml.safe_dump({"segment_caps": {}}), encoding="utf-8")
    causality_config = tmp_path / "causality.yaml"
    causality_config.write_text(yaml.safe_dump({"graph": {"output_path": str(tmp_path / "graph.json")}}), encoding="utf-8")
    safety_config = tmp_path / "safety.yaml"
    safety_config.write_text(yaml.safe_dump({}), encoding="utf-8")
    macro_config = tmp_path / "macro.yaml"
    macro_config.write_text(yaml.safe_dump({}), encoding="utf-8")

    sample_csv = tmp_path / "sample.csv"
    sample_df = pd.DataFrame(
        [
            {"annual_inc": 25000.0, "revol_util": 88.0, "loan_status": 1},
            {"annual_inc": 32000.0, "revol_util": 74.0, "loan_status": 1},
            {"annual_inc": 54000.0, "revol_util": 44.0, "loan_status": 0},
            {"annual_inc": 90000.0, "revol_util": 18.0, "loan_status": 0},
        ]
    )
    pd.concat([sample_df] * 10, ignore_index=True).to_csv(sample_csv, index=False)

    monkeypatch.setattr(collector, "_default_collection_sample_csv_path", lambda **kwargs: sample_csv)
    monkeypatch.setattr(
        collector,
        "load_model_bundle",
        lambda **kwargs: (_DummyModel(), None, {"model_version": "model-001"}, None),
    )
    monkeypatch.setattr(
        collector,
        "predict_proba_pd",
        lambda model, calibrator, frame: pd.to_numeric(frame["revol_util"], errors="coerce").fillna(0.0).div(100.0).to_numpy(),
    )
    monkeypatch.setattr(collector, "run_rex_adapter", lambda *args, **kwargs: {})

    def _fake_customer_result(**kwargs):
        customer_id = str(kwargs["customer_id"])
        bundle = CustomerArtifactBundle(
            customer_id=customer_id,
            plans_df=pd.DataFrame(
                [
                    {"plan_id": f"{customer_id}-plan-a", "plan_score": 0.4, "plan_source": "internal", "plan_stage": "validated"},
                ]
            ),
            roadmap={
                "customer_id": customer_id,
                "best_plan_id": f"{customer_id}-plan-a",
                "best_plan_source": "internal",
                "summary": {
                    "decision_status": "CONDITIONAL",
                    "decision_status_internal": "CONDITIONAL",
                    "decision_policy_version": "v2.1_phase_40_5",
                    "decision_confidence": 0.61,
                    "decision_reason_summary": "Fallback sample cohort",
                    "decision_reason_primary": "TIME_GATED",
                    "best_plan_id": f"{customer_id}-plan-a",
                    "best_plan_source": "internal",
                    "best_constraint_status": "valid",
                    "plan_contract_pass": 1,
                    "credit_readiness_stage": "week_4",
                    "expected_readiness": "week_4",
                    "plan_execution_probability": 0.62,
                    "approval_dependent_plan_probability": 0.62,
                    "offer_acceptance_probability": 0.0,
                    "combined_plan_realization_probability": 0.62,
                    "expected_pd_improvement": 0.03,
                    "nominal_pd_improvement": 0.05,
                    "local_explainability_confidence": 0.8,
                    "best_action_count": 1,
                    "zero_step_flag": 0,
                    "raw_contract_pass": 1,
                    "parity_pass": 1,
                    "data_issue_flag": 0,
                    "offer_plan": 0,
                    "rankable_offer_count": 0,
                    "approval_pending_action_count": 0,
                    "checkpoint_status_4w": "at_risk",
                    "checkpoint_status_12w": "on_track",
                    "checkpoint_status_24w": "on_track",
                },
                "phases": [{"phase_id": "phase_1_stabilize", "steps": [{"step_id": "step-1"}]}],
                "checkpoints": [{"week": 4, "status": "at_risk"}],
            },
            roadmap_steps_df=pd.DataFrame(
                [
                    {
                        "customer_id": customer_id,
                        "best_plan_id": f"{customer_id}-plan-a",
                        "phase_id": "phase_1_stabilize",
                        "phase_title": "Stabilize",
                        "target_window_weeks": "1-4",
                        "action_key": "limit_credit_usage",
                        "action_class": "behavioral",
                        "action_title": "Limit credit usage",
                        "action_group_id": f"{customer_id}:phase_1",
                        "composite_action": 0,
                        "feature_name": "revol_util",
                        "metric_key": "credit_utilization_pct",
                        "unit": "percentage_points",
                        "current_value": 70.0,
                        "target_value": 45.0,
                        "delta": -25.0,
                        "time_months": 1,
                        "due_month": 1,
                        "direction": "decrease",
                        "generation_notes_json": "[]",
                        "estimated_cost_usd": 25.0,
                        "requires_institutional_approval": 0,
                        "approval_pending_semantic_only": 0,
                        "action_status": "valid",
                        "constraint_family": "",
                        "constraint_reason_codes_json": "[]",
                        "was_clipped": 0,
                        "repair_applied": 0,
                        "dependency_gate": 0,
                        "semantic_preserved": True,
                    }
                ]
            ),
            metrics_summary={
                "customer_id": customer_id,
                "best_plan_id": f"{customer_id}-plan-a",
                "best_plan_source": "internal",
                "decision_status": "CONDITIONAL",
                "decision_status_internal": "CONDITIONAL",
                "credit_readiness_stage": "week_4",
                "raw_contract_pass": 1,
                "parity_pass": 1,
                "data_issue_flag": 0,
            },
        )
        return CustomerRecourseRunResult(
            bundle=bundle,
            local_reason_bundle={"reasons": [], "meta": {}},
            adverse_action_reasons=[],
            dice_df=pd.DataFrame(),
            dice_records=[],
            dice_backend="skipped",
            dice_telemetry={"method_requested": "random", "method_used": "skipped", "fallback_reason": "sample_fallback_test"},
            candidate_pool_df=pd.DataFrame(),
            decision_log_record={"decision_id": f"decision-{customer_id}", "selection_propensity": 1.0},
            decision_log_summary={"decision_log_completeness": 1.0},
        )

    monkeypatch.setattr(collector, "generate_customer_recourse_artifacts", _fake_customer_result)

    run_ctx = collector.main(
        [
            "--base_config",
            str(base_config),
            "--model_config",
            str(model_config),
            "--recourse_config",
            str(recourse_config),
            "--causality_config",
            str(causality_config),
            "--safety_config",
            str(safety_config),
            "--macro_config",
            str(macro_config),
            "--n_customers",
            "6",
            "--artifact_root",
            str(tmp_path / "runs"),
        ]
    )

    collection_root = run_ctx.tables_dir / "customer_artifact_collection"
    metrics_df = pd.read_csv(collection_root / "flat" / "customer_metrics.csv")

    assert len(metrics_df) == 6
    assert metrics_df["customer_id"].astype(str).str.startswith("sample_test_").all()
    assert (collection_root / "collection_summary.md").exists()
