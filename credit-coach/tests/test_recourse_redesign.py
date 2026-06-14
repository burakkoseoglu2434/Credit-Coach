from __future__ import annotations

import json
from math import isclose

import numpy as np
import pandas as pd

from credit_coach.cli.run_recourse import (
    _build_customer_roadmap,
    _effective_recourse_search,
    _normalize_customer_roadmap_contract,
    _plan_to_row,
    build_customer_artifact_bundle,
)
from credit_coach.coaching.planner import BestPlanSelectionResult
from credit_coach.data.schema import OfferContract, PlanAction, PlanRecord, PrimaryNumericTarget, TrajectoryCheckpoint, TrajectoryPhase, RecoursePathRecord
from credit_coach.evaluation.fairness import build_group_advantage_penalties, lookup_group_penalty
from credit_coach.recourse.generator import PlanGenConfig, generate_plan_record
from credit_coach.recourse.execution_probability import (
    estimate_action_execution_probability,
    estimate_plan_execution_probability,
)
from credit_coach.recourse.dice_quality import annotate_dice_candidate_quality
from credit_coach.recourse.offer_optimization import annotate_offer_optimization
from credit_coach.safety.statistical import estimate_prediction_ci


class _DummyModel:
    def predict_proba(self, x):
        df = x if isinstance(x, pd.DataFrame) else pd.DataFrame(x)
        inc = pd.to_numeric(df.get("annual_inc", pd.Series([50_000.0] * len(df))), errors="coerce").fillna(50_000.0)
        util = pd.to_numeric(df.get("revol_util", pd.Series([50.0] * len(df))), errors="coerce").fillna(50.0)
        p = (0.75 - (inc / 250000.0) + (util / 500.0)).clip(0.05, 0.99).to_numpy()
        return np.column_stack([1.0 - p, p])


def _selection_result(plan: PlanRecord | None) -> BestPlanSelectionResult:
    if plan is None:
        return BestPlanSelectionResult(
            best_plan=None,
            selection_outcome="no_valid_winner",
            selection_stage="no_valid_winner",
            invalid_candidates_removed_count=1,
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


def test_effective_recourse_search_denied_target_profile():
    rec_cfg = {
        "adaptive_steps": {"enabled": True},
        "weekly_optimizer": {"enabled": True, "only_denied": True},
        "denied_target": {
            "enabled": True,
            "activation_margin": 0.0,
            "topk_multiplier": 2.0,
            "min_topk": 12,
            "horizons": [3, 12],
            "strategies": ["balanced", "aggressive"],
            "strict_min_reliability": 0.8,
            "strict_min_worst_risk_margin": -0.01,
            "dice_total_cfs_multiplier": 2.0,
            "dice_max_actions_multiplier": 1.5,
        },
    }
    search, robust, dice = _effective_recourse_search(
        base_pd=0.52,
        tau=0.35,
        topk=8,
        horizons=[3, 6, 12],
        strategies=["conservative", "balanced", "aggressive"],
        robust_cfg={"min_reliability": 0.7, "min_worst_risk_margin": -0.05},
        dice_cfg={"total_cfs": 3, "max_actions": 4},
        rec_cfg=rec_cfg,
    )
    assert search["is_denied_target"] is True
    assert search["search_cfg"]["denied_mode"] is True
    assert search["search_cfg"]["weekly_optimizer"]["enabled"] is True
    assert search["topk"] >= 12
    assert search["horizons"] == [3, 12]
    assert search["strategies"] == ["balanced", "aggressive"]
    assert robust["min_reliability"] >= 0.8
    assert robust["min_worst_risk_margin"] >= -0.01
    assert dice["total_cfs"] >= 6
    assert dice["max_actions"] >= 6


def test_effective_recourse_search_adaptive_only_denied():
    rec_cfg = {
        "adaptive_steps": {"enabled": True, "only_denied": True},
        "weekly_optimizer": {"enabled": True, "only_denied": True},
        "denied_target": {"enabled": True, "activation_margin": 0.0},
    }
    search_ok, _, _ = _effective_recourse_search(
        base_pd=0.20,
        tau=0.35,
        topk=8,
        horizons=[3, 6, 12],
        strategies=["conservative", "balanced", "aggressive"],
        robust_cfg={},
        dice_cfg={},
        rec_cfg=rec_cfg,
    )
    assert search_ok["is_denied_target"] is False
    assert search_ok["search_cfg"]["adaptive_steps"]["enabled"] is False
    assert search_ok["search_cfg"]["weekly_optimizer"]["enabled"] is False

    search_denied, _, _ = _effective_recourse_search(
        base_pd=0.50,
        tau=0.35,
        topk=8,
        horizons=[3, 6, 12],
        strategies=["conservative", "balanced", "aggressive"],
        robust_cfg={},
        dice_cfg={},
        rec_cfg=rec_cfg,
    )
    assert search_denied["is_denied_target"] is True
    assert search_denied["search_cfg"]["adaptive_steps"]["enabled"] is True
    assert search_denied["search_cfg"]["weekly_optimizer"]["enabled"] is True


def test_group_advantage_penalties():
    scored = pd.DataFrame(
        {
            "g": ["A", "A", "B", "B", "C", "C"],
            "approve": [1, 1, 1, 0, 0, 0],
        }
    )
    penalties = build_group_advantage_penalties(scored, group_col="g", approval_col="approve", tolerance=0.0)
    assert penalties["A"] > penalties["B"] > penalties["C"] - 1e-12
    assert lookup_group_penalty("A", penalties) > 0.0
    assert lookup_group_penalty("missing", penalties) == 0.0


def test_estimate_prediction_ci_conformal_and_hybrid_bounds():
    low_c, high_c = estimate_prediction_ci(
        0.4,
        alpha=0.05,
        method="conformal",
        conformal_residual_quantile=0.05,
        conformal_min_width=0.01,
    )
    low_b, high_b = estimate_prediction_ci(
        0.4,
        alpha=0.05,
        method="bootstrap",
        b=200,
        sigma=0.02,
    )
    assert 0.0 <= low_c <= high_c <= 1.0
    assert 0.0 <= low_b <= high_b <= 1.0
    assert (high_c - low_c) >= 0.02


def test_generate_plan_record_repairs_conflicting_action_bundle():
    row = pd.Series(
        {
            "annual_inc": 55_000.0,
            "dti": 22.0,
            "revol_bal": 12_000.0,
            "tot_coll_amt": 2_500.0,
        }
    )
    plan = generate_plan_record(
        customer_id="c1",
        run_id="r1",
        row=row,
        model=_DummyModel(),
        calibrator=None,
        feature_cols=list(row.index),
        horizon_months=6,
        strategy="balanced",
        graph=None,
        cfg=PlanGenConfig(tau=0.35),
        candidate_features=["revol_bal", "tot_coll_amt"],
        topk=2,
        robust_cfg={"enabled": False},
        search_cfg={"min_abs_action_delta": 1e-6},
    )
    assert plan.constraint_status == "repaired"
    assert plan.actions
    assert all(action.action_key != "settlement_discount" for action in plan.actions)
    assert any(str(entry.get("reason_code", "")).startswith("conflict_with:") for entry in plan.constraint_trace)
    assert any(str(entry.get("constraint_family", "")) == "interaction" for entry in plan.constraint_trace)


def test_generate_plan_record_marks_approval_required_action_provisional():
    row = pd.Series(
        {
            "annual_inc": 50_000.0,
            "dti": 21.0,
            "total_rev_hi_lim": 6_000.0,
        }
    )
    plan = generate_plan_record(
        customer_id="c2",
        run_id="r2",
        row=row,
        model=_DummyModel(),
        calibrator=None,
        feature_cols=list(row.index),
        horizon_months=6,
        strategy="balanced",
        graph=None,
        cfg=PlanGenConfig(tau=0.35),
        candidate_features=["total_rev_hi_lim"],
        topk=1,
        robust_cfg={"enabled": False},
        search_cfg={"min_abs_action_delta": 1e-6},
    )
    assert plan.constraint_status == "provisional"
    assert len(plan.actions) == 1
    assert plan.actions[0].action_status == "provisional"
    assert plan.actions[0].constraint_family == "dependency"
    assert plan.actions[0].dependency_gate is True
    assert "offer_terms_incomplete" in plan.actions[0].diagnostic_flags
    assert plan.actions[0].action_execution_probability is None
    assert float(plan.actions[0].approval_dependent_probability or 0.0) > 0.0
    assert plan.actions[0].offer_contract is not None
    assert plan.actions[0].offer_contract.offer_type == "credit_limit_adjustment"
    assert plan.actions[0].offer_contract.offer_terms_complete is False
    assert plan.actions[0].offer_contract.requires_institutional_approval is True
    assert plan.actions[0].offer_contract.institutional_approval_state == "pending"


def test_plan_action_builds_nested_offer_contract_from_flat_fields():
    action = PlanAction(
        feature_name="delinq_amnt",
        current_value=2400.0,
        target_value=1200.0,
        delta=-1200.0,
        time_months=3,
        estimated_cost_usd=25.0,
        action_key="installment_plan",
        action_class="institutional",
        action_title="Request installment plan",
        offer_type="installment_terms",
        offer_terms={
            "payment_delta_monthly": -120.0,
            "term_extension_months": 6,
            "grace_period_weeks": 2,
            "custom_note": "pilot_extension",
        },
        offer_terms_complete=True,
        requires_acceptance=True,
        requires_institutional_approval=False,
        institutional_approval_state="approved",
        offer_family="payment_relief",
        offer_scoring_profile="installment_terms_v1",
        term_generation_rule="installment_terms_v1",
        offer_policy_arm="installment_terms_policy_v1",
    )

    assert action.offer_contract is not None
    assert action.offer_contract.offer_type == "installment_terms"
    assert action.offer_contract.offer_family == "payment_relief"
    assert action.offer_contract.offer_terms_complete is True
    assert action.offer_contract.requires_acceptance is True
    assert action.offer_contract.offer_terms.term_extension_months == 6
    assert action.offer_contract.offer_terms.extensions["custom_note"] == "pilot_extension"


def test_plan_action_backfills_flat_offer_fields_from_nested_contract():
    action = PlanAction(
        feature_name="delinq_amnt",
        current_value=2400.0,
        target_value=1200.0,
        delta=-1200.0,
        time_months=3,
        estimated_cost_usd=25.0,
        action_key="installment_plan",
        action_class="institutional",
        action_title="Request installment plan",
        offer_contract=OfferContract(
            offer_type="installment_terms",
            offer_family="payment_relief",
            offer_terms={
                "payment_delta_monthly": -120.0,
                "term_extension_months": 6,
                "grace_period_weeks": 2,
            },
            offer_terms_complete=True,
            requires_acceptance=True,
            requires_institutional_approval=False,
            institutional_approval_state="approved",
            offer_policy_arm="installment_terms_policy_v1",
            offer_scoring_profile="installment_terms_v1",
            term_generation_rule="installment_terms_v1",
        ),
    )

    assert action.offer_type == "installment_terms"
    assert action.offer_terms_complete is True
    assert action.requires_acceptance is True
    assert action.offer_family == "payment_relief"
    assert action.offer_policy_arm == "installment_terms_policy_v1"
    assert isclose(float(action.offer_terms["payment_delta_monthly"]), -120.0)


def test_generate_plan_record_emits_execution_probability_contract():
    row = pd.Series(
        {
            "annual_inc": 68_000.0,
            "dti": 31.0,
            "revol_bal": 11_000.0,
            "revol_util": 58.0,
        }
    )
    plan = generate_plan_record(
        customer_id="c3",
        run_id="r3",
        row=row,
        model=_DummyModel(),
        calibrator=None,
        feature_cols=list(row.index),
        horizon_months=6,
        strategy="balanced",
        graph=None,
        cfg=PlanGenConfig(tau=0.35),
        candidate_features=["dti", "revol_bal"],
        topk=2,
        robust_cfg={"enabled": False},
        search_cfg={"min_abs_action_delta": 1e-6},
        base_pd=0.52,
    )
    assert float(plan.plan_execution_probability or 0.0) > 0.0
    assert float(plan.mean_action_execution_probability or 0.0) > 0.0
    assert float(plan.mean_group_difficulty_score or 0.0) > 0.0
    assert float(plan.peak_group_difficulty_score or 0.0) > 0.0
    assert str(plan.dominant_difficulty_label or "") in {"low", "moderate", "high"}
    assert str(plan.follow_through_readiness_label or "") in {"low", "moderate", "high"}
    assert float(plan.nominal_pd_improvement or 0.0) >= 0.0
    assert float(plan.expected_pd_improvement or 0.0) >= 0.0
    assert int(plan.executable_action_count) >= 1
    assert int(plan.executable_action_group_count) >= 1
    assert all(action.action_group_execution_probability is not None for action in plan.actions)
    assert all(action.action_execution_probability is not None for action in plan.actions)
    assert all(action.difficulty_score is not None for action in plan.actions)
    assert all(str(action.difficulty_label or "") in {"low", "moderate", "high"} for action in plan.actions)
    assert all({"burden", "horizon", "action_class", "coordination_load"} <= set(action.difficulty_drivers.keys()) for action in plan.actions)
    assert all(action.business_view is not None for action in plan.actions)
    assert all(action.technical_view is not None for action in plan.actions)
    assert all(action.business_view.action_key == action.action_key for action in plan.actions)
    assert all(action.technical_view.feature_name == action.feature_name for action in plan.actions)
    primary_targets = [action.primary_numeric_target for action in plan.actions if action.primary_numeric_target is not None]
    assert primary_targets
    assert any(target.metric_key in {"debt_to_income_pct", "revolving_balance_amount"} for target in primary_targets)
    assert all(target.direction == "decrease" for target in primary_targets)
    assert all("semantic_sanity_only" in target.generation_notes for target in primary_targets)
    assert all("phase_32_feasibility_pending" in target.generation_notes for target in primary_targets)
    assert all(target.raw_generation_basis["source_feature_name"] for target in primary_targets)
    assert all(target.raw_generation_basis["requested_target_value"] != 0.0 for target in primary_targets)
    assert [phase.phase_id for phase in plan.phases] == [
        "phase_1_stabilize",
        "phase_2_build",
        "phase_3_optimize",
    ]
    assert int(plan.phases[0].review_week) == 4
    assert int(plan.phases[1].review_week) == 12
    assert int(plan.phases[2].review_week) == 24
    assert [checkpoint.week for checkpoint in plan.trajectory_checkpoints] == [4, 12, 24]
    assert str(plan.trajectory_status) == "on_track"
    assert str(plan.current_phase) == "phase_1_stabilize"
    assert int(plan.next_review_week or 0) == 4


def test_execution_probability_defaults_lower_for_long_high_burden_actions():
    short_action = PlanAction(
        feature_name="revol_util",
        current_value=72.0,
        target_value=60.0,
        delta=-12.0,
        time_months=1,
        estimated_cost_usd=15.0,
        action_key="limit_credit_usage",
        action_class="behavioral",
        action_title="Limit credit usage",
    )
    long_action = PlanAction(
        feature_name="revol_util",
        current_value=72.0,
        target_value=45.0,
        delta=-27.0,
        time_months=6,
        estimated_cost_usd=240.0,
        action_key="limit_credit_usage",
        action_class="behavioral",
        action_title="Limit credit usage",
    )

    short_prob, _ = estimate_action_execution_probability(short_action, plan_action_count=1)
    long_prob, _ = estimate_action_execution_probability(long_action, plan_action_count=1)

    assert float(short_prob or 0.0) > float(long_prob or 0.0)
    assert float(long_prob or 0.0) < 0.5
    assert float(short_action.difficulty_score or 0.0) < float(long_action.difficulty_score or 0.0)
    assert str(long_action.difficulty_label or "") in {"moderate", "high"}


def test_invalid_or_semantic_break_actions_do_not_emit_difficulty_truth():
    invalid_action = PlanAction(
        feature_name="dti",
        current_value=30.0,
        target_value=20.0,
        delta=-10.0,
        time_months=3,
        estimated_cost_usd=40.0,
        action_status="invalid",
    )
    semantic_break_action = PlanAction(
        feature_name="revol_util",
        current_value=70.0,
        target_value=55.0,
        delta=-15.0,
        time_months=2,
        estimated_cost_usd=20.0,
        action_status="repaired",
        semantic_preserved=False,
    )

    invalid_prob, invalid_approval = estimate_action_execution_probability(invalid_action, plan_action_count=1)
    broken_prob, broken_approval = estimate_action_execution_probability(semantic_break_action, plan_action_count=1)

    assert invalid_prob is None and invalid_approval is None
    assert invalid_action.difficulty_score is None
    assert invalid_action.difficulty_label is None
    assert invalid_action.difficulty_drivers == {}
    assert invalid_action.approval_friction is None
    assert broken_prob is None and broken_approval is None
    assert semantic_break_action.difficulty_score is None
    assert semantic_break_action.difficulty_label is None


def test_execution_probability_uses_weighted_min_average_for_composite_groups():
    actions = [
        PlanAction(
            feature_name="dti",
            current_value=32.0,
            target_value=29.0,
            delta=-3.0,
            time_months=1,
            estimated_cost_usd=20.0,
            action_key="cut_fixed_expenses",
            action_class="behavioral",
            action_title="Cut fixed expenses",
            action_group_id="stabilize_cashflow",
        ),
        PlanAction(
            feature_name="revol_bal",
            current_value=14000.0,
            target_value=11000.0,
            delta=-3000.0,
            time_months=3,
            estimated_cost_usd=140.0,
            action_key="pay_down_revolving_balance",
            action_class="structural",
            action_title="Pay down revolving balance",
            action_group_id="stabilize_cashflow",
        ),
    ]

    bundle = estimate_plan_execution_probability(actions)

    member_probabilities = [float(action.action_execution_probability or 0.0) for action in actions]
    group_probability = float(actions[0].action_group_execution_probability or 0.0)

    assert group_probability > min(member_probabilities)
    assert group_probability < max(member_probabilities)
    assert float(bundle["plan_execution_probability"]) <= group_probability


def test_execution_probability_keeps_approval_dependent_realization_separate():
    actions = [
        PlanAction(
            feature_name="revol_util",
            current_value=68.0,
            target_value=55.0,
            delta=-13.0,
            time_months=1,
            estimated_cost_usd=10.0,
            action_key="limit_credit_usage",
            action_class="behavioral",
            action_title="Limit credit usage",
            action_group_id="limit_credit_usage:phase_1_stabilize",
        ),
        PlanAction(
            feature_name="total_rev_hi_lim",
            current_value=6000.0,
            target_value=8000.0,
            delta=2000.0,
            time_months=2,
            estimated_cost_usd=0.0,
            action_key="evaluate_limit_adjustment",
            action_class="institutional",
            action_title="Evaluate limit adjustment",
            action_group_id="limit_adjustment:m2",
            requires_institutional_approval=True,
            institutional_approval_state="pending",
            approval_pending_semantic_only=True,
        ),
    ]

    bundle = estimate_plan_execution_probability(actions)

    assert float(bundle["plan_execution_probability"]) > 0.0
    assert float(bundle["approval_dependent_plan_probability"] or 0.0) > 0.0
    assert float(bundle["mean_approval_dependent_probability"] or 0.0) > 0.0
    assert actions[1].difficulty_score is not None
    assert float(actions[1].approval_friction or 0.0) > 0.0
    assert bundle["follow_through_readiness_label"] in {"low", "moderate", "high"}
    assert int(bundle["approval_pending_action_count"]) == 1


def test_annotate_offer_optimization_emits_combined_realization_contract():
    plan = annotate_offer_optimization(
        PlanRecord(
            plan_id="offer-plan",
            customer_id="c4",
            run_id="r4",
            horizon_months=6,
            strategy="balanced",
            actions=[
                PlanAction(
                    feature_name="delinq_amnt",
                    current_value=2400.0,
                    target_value=1200.0,
                    delta=-1200.0,
                    time_months=2,
                    estimated_cost_usd=25.0,
                    action_key="installment_plan",
                    action_class="institutional",
                    action_title="Request installment plan",
                    action_group_id="installment_plan:phase_2_build",
                    offer_contract=OfferContract(
                        offer_type="installment_terms",
                        offer_family="payment_relief",
                        offer_terms={
                            "payment_delta_monthly": -120.0,
                            "discount_amount": 0.0,
                            "discount_pct": 0.0,
                            "term_extension_months": 6,
                            "interest_rate_delta": -0.25,
                            "grace_period_weeks": 2,
                        },
                        offer_terms_complete=True,
                        requires_acceptance=True,
                        requires_institutional_approval=False,
                        institutional_approval_state="approved",
                        offer_scoring_profile="installment_terms_v1",
                        term_generation_rule="installment_terms_v1",
                        offer_policy_arm="installment_terms_policy_v1",
                    ),
                )
            ],
            predicted_pd=0.41,
            score=0.12,
            robust_score=0.12,
            status="NEEDS_REVIEW",
            constraint_status="valid",
            trajectory_status="on_track",
            executable_action_group_count=1,
            plan_execution_probability=0.65,
        ),
        customer_context={"income_band": "q1"},
        segment_context={"risk_band": "high", "stress_band": "stress"},
    )

    assert plan.offer_plan is True
    assert plan.rankable_offer_count == 1
    assert float(plan.offer_acceptance_probability or 0.0) > 0.0
    assert float(plan.combined_plan_realization_probability or 0.0) > 0.0
    assert float(plan.expected_recovery_proxy or 0.0) > 0.0
    assert plan.offer_policy_arm == "installment_terms_policy_v1"
    assert plan.governance_safe_offer is True
    assert plan.actions[0].offer_contract is not None
    assert plan.actions[0].offer_contract.offer_type == "installment_terms"
    assert plan.actions[0].offer_contract.offer_family == "payment_relief"
    assert plan.actions[0].offer_contract.offer_terms.term_extension_months == 6


def test_annotate_offer_optimization_keeps_approval_pending_offer_non_rankable():
    plan = annotate_offer_optimization(
        PlanRecord(
            plan_id="offer-approval-pending",
            customer_id="cust-offer-pending",
            run_id="run-offer-pending",
            horizon_months=6,
            strategy="balanced",
            actions=[
                PlanAction(
                    feature_name="total_rev_hi_lim",
                    current_value=6000.0,
                    target_value=7200.0,
                    delta=1200.0,
                    time_months=3,
                    estimated_cost_usd=12.0,
                    action_key="credit_limit_adjustment",
                    action_class="institutional",
                    action_title="Request credit limit adjustment",
                    action_group_id="credit_limit_adjustment:phase_2_build",
                    offer_contract=OfferContract(
                        offer_type="credit_limit_adjustment",
                        offer_family="limit_management",
                        offer_terms={"grace_period_weeks": 0},
                        offer_terms_complete=False,
                        requires_acceptance=False,
                        requires_institutional_approval=True,
                        institutional_approval_state="pending",
                        offer_scoring_profile="credit_limit_adjustment_v1",
                        term_generation_rule="credit_limit_adjustment_terms_v1",
                        offer_policy_arm="credit_limit_adjustment_policy_v1",
                    ),
                    action_status="provisional",
                    dependency_gate=True,
                )
            ],
            predicted_pd=0.44,
            score=0.10,
            robust_score=0.10,
            status="NEEDS_REVIEW",
            constraint_status="provisional",
            trajectory_status="on_track",
            executable_action_group_count=0,
            approval_pending_action_count=1,
            approval_dependent_plan_probability=0.42,
        ),
        customer_context={"income_band": "q2"},
        segment_context={"risk_band": "mid"},
    )

    assert plan.offer_plan is True
    assert plan.rankable_offer_count == 0
    assert plan.offer_acceptance_probability is None
    assert plan.combined_plan_realization_probability is None
    assert plan.governance_safe_offer is False
    assert plan.dominant_offer_type == "credit_limit_adjustment"


def test_build_customer_roadmap_emits_sibling_narrative_layer():
    action = PlanAction(
        feature_name="revol_util",
        current_value=71.0,
        target_value=52.0,
        delta=-19.0,
        time_months=1,
        estimated_cost_usd=0.0,
        action_key="limit_credit_usage",
        action_class="behavioral",
        action_title="Limit credit usage",
        action_group_id="limit_credit_usage:phase_1_stabilize",
        action_execution_probability=0.68,
        difficulty_score=0.41,
        difficulty_label="moderate",
        difficulty_drivers={
            "burden": 0.2,
            "horizon": 0.1,
            "action_class": 0.35,
            "coordination_load": 0.0,
        },
        approval_friction=0.0,
        diagnostic_flags=["utilization_relief"],
    )
    plan = PlanRecord(
        plan_id="roadmap-plan",
        customer_id="cust-18",
        run_id="run-18",
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
        plan_execution_probability=0.68,
        mean_group_difficulty_score=0.41,
        peak_group_difficulty_score=0.41,
        dominant_difficulty_label="moderate",
        follow_through_readiness_label="moderate",
    )

    roadmap = _build_customer_roadmap(
        customer_id="cust-18",
        base_pd=0.44,
        tau=0.35,
        best=plan,
        best_source="internal",
        selection_result=_selection_result(plan),
        row=pd.Series({"revol_util": 71.0, "revol_bal": 7100.0, "total_rev_hi_lim": 10000.0}),
        model=_DummyModel(),
        calibrator=None,
        feature_cols=["revol_util"],
        local_reason_bundle={
            "reasons": [
                {"feature": "revol_util", "direction": "increase_risk", "abs_contribution": 0.26},
            ],
            "meta": {
                "explainability_confidence": 0.82,
                "stability_score": 0.9,
                "baseline_drift_l1": 0.04,
            },
        },
    )

    assert roadmap["summary"]["decision_status"] == "APPROVED"
    assert roadmap["summary"]["expected_readiness"] == "now"
    assert "narrative" in roadmap
    assert roadmap["narrative"]["executive_summary"]["decision_view"]["label"]["en"] == "Approval-ready view"
    assert roadmap["narrative"]["executive_summary"]["summary_line"]["en"] == roadmap["summary"]["decision_reason_summary"]
    assert roadmap["narrative"]["steps"][0]["step_id"] == "limit_credit_usage:phase_1_stabilize"
    assert roadmap["narrative"]["steps"][0]["action_summary"]["tr"]
    assert "revolving-balance paydown" in roadmap["narrative"]["steps"][0]["primary_recommendation"]["en"]
    assert "credit utilization" in roadmap["narrative"]["steps"][0]["expected_outcome"]["en"]
    assert "within this month" in roadmap["narrative"]["steps"][0]["expected_outcome"]["en"]
    assert roadmap["phases"][0]["steps"][0]["difficulty_label"] == "moderate"
    assert roadmap["summary"]["follow_through_readiness_label"] == "moderate"
    assert roadmap["summary"]["dominant_difficulty_label"] == "moderate"
    assert roadmap["narrative"]["checkpoints"][1]["review_action"]["en"]
    assert roadmap["phases"][0]["steps"][0]["primary_numeric_target"]["metric_key"] == "credit_utilization_pct"
    assert roadmap["phases"][0]["steps"][0]["primary_numeric_target"]["generation_notes"] == ["auto_populated_fallback"]
    assert roadmap["narrative"]["technical_reveal"]["feature_changes"][0]["feature_name"] == "revol_util"
    assert roadmap["narrative"]["technical_reveal"]["primary_numeric_targets"][0]["primary_numeric_target"]["metric_key"] == "credit_utilization_pct"
    assert roadmap["narrative"]["technical_reveal"]["decision_details"]["decision_status_internal"] == "APPROVED"
    assert roadmap["narrative"]["technical_reveal"]["decision_details"]["expected_readiness"] == "now"
    assert "%" not in roadmap["narrative"]["executive_summary"]["follow_through_readiness"]["description"]["en"]
    assert action.business_view.action_family == "utilization"
    assert action.technical_view.feature_name == "revol_util"


def test_plan_to_row_serializes_primary_numeric_target_in_timeline():
    action = PlanAction(
        feature_name="installment",
        current_value=510.0,
        target_value=450.0,
        delta=-60.0,
        time_months=3,
        estimated_cost_usd=12.0,
        action_key="refinance",
        action_class="structural",
        action_title="Refinance or restructure debt",
        action_group_id="refinance:phase_2_build",
    )
    plan = PlanRecord(
        plan_id="timeline-plan",
        customer_id="cust-31",
        run_id="run-31",
        horizon_months=6,
        strategy="balanced",
        actions=[action],
        predicted_pd=0.33,
        score=0.19,
        robust_score=0.19,
        status="APPROVED",
        constraint_status="valid",
        trajectory_status="on_track",
    )

    row = _plan_to_row(plan)
    timeline_steps = json.loads(row["timeline_steps_json"])

    assert len(timeline_steps) == 1
    assert timeline_steps[0]["primary_numeric_target"]["metric_key"] == "monthly_payment_amount"
    assert timeline_steps[0]["primary_numeric_target"]["unit"] == "currency"
    assert timeline_steps[0]["primary_numeric_target"]["generation_notes"] == ["auto_populated_fallback"]


def test_build_customer_artifact_bundle_normalizes_contract_safe_summary_fields():
    action = PlanAction(
        feature_name="revol_util",
        current_value=71.0,
        target_value=52.0,
        delta=-19.0,
        time_months=1,
        estimated_cost_usd=10.0,
        action_key="limit_credit_usage",
        action_class="behavioral",
        action_title="Limit credit usage",
        action_group_id="limit_credit_usage:phase_1_stabilize",
    )
    plan = PlanRecord(
        plan_id="contract-plan",
        customer_id="cust-contract",
        run_id="run-contract",
        horizon_months=6,
        strategy="balanced",
        actions=[action],
        predicted_pd=0.31,
        score=0.18,
        robust_score=0.18,
        status="NEEDS_REVIEW",
        constraint_status="valid",
        trajectory_status="on_track",
        plan_execution_probability=0.64,
    )
    roadmap = _build_customer_roadmap(
        customer_id="cust-contract",
        base_pd=0.44,
        tau=0.35,
        best=plan,
        best_source="internal",
        selection_result=_selection_result(plan),
        row=pd.Series({"revol_util": 71.0}),
        model=_DummyModel(),
        calibrator=None,
        feature_cols=["revol_util"],
        local_reason_bundle={"reasons": [], "meta": {}},
    )
    roadmap["summary"]["approval_dependent_plan_probability"] = None
    roadmap["summary"]["offer_acceptance_probability"] = None
    roadmap["summary"]["combined_plan_realization_probability"] = None
    roadmap["checkpoints"][0]["status"] = ""

    bundle = build_customer_artifact_bundle(
        customer_id="cust-contract",
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
        local_reason_bundle={"reasons": [], "meta": {}},
        adverse_action_reasons=[],
        dice_backend="skipped",
        dice_records=[],
        dice_telemetry={"method_requested": "random", "method_used": "skipped", "fallback_reason": "policy"},
        search_elapsed_ms=10.0,
        fairness_penalty=0.0,
        decision_log_record={"decision_id": "d-40-1", "selection_propensity": 1.0},
        decision_log_summary={"decision_log_completeness": 1.0},
    )

    summary = bundle.roadmap["summary"]
    assert summary["decision_status"] == "CONDITIONAL"
    assert summary["decision_status_internal"] == "NEEDS_REVIEW"
    assert summary["decision_policy_version"] == "v2.1_phase_40_5"
    assert isclose(float(summary["approval_dependent_plan_probability"]), 0.64)
    assert isclose(float(summary["offer_acceptance_probability"]), 0.0)
    assert isclose(float(summary["combined_plan_realization_probability"]), 0.64)
    assert int(summary["critical_field_null_count"]) == 0
    assert summary["checkpoint_status_4w"] == "unknown"
    assert int(summary["raw_contract_pass"]) == 0
    assert int(summary["data_issue_flag"]) == 1
    assert "missing_required_field" not in summary["data_issue_codes"]
    assert "checkpoint_status_missing" in summary["data_issue_codes"]
    assert bundle.metrics_summary["decision_status"] == "REJECTED"
    assert bundle.metrics_summary["decision_status_internal"] == "REJECTED"
    assert bundle.metrics_summary["checkpoint_status_4w"] == "unknown"


def test_normalize_customer_roadmap_contract_recomputes_critical_fields_after_backfill() -> None:
    normalized = _normalize_customer_roadmap_contract(
        {
            "customer_id": "cust-normalize",
            "phases": [{"phase_id": "phase_1_stabilize", "steps": [{"step_id": "step-1"}]}],
            "checkpoints": [
                {"week": 4, "status": "at_risk"},
                {"week": 12, "status": "on_track"},
                {"week": 24, "status": "on_track"},
            ],
            "summary": {
                "decision_status": "CONDITIONAL",
                "credit_readiness_stage": "week_12",
                "plan_execution_probability": 0.61,
                "approval_dependent_plan_probability": None,
                "offer_acceptance_probability": None,
                "combined_plan_realization_probability": None,
                "critical_field_null_count": 3,
                "raw_contract_pass": 0,
            },
        }
    )
    summary = normalized["summary"]

    assert isclose(float(summary["approval_dependent_plan_probability"]), 0.61)
    assert isclose(float(summary["offer_acceptance_probability"]), 0.0)
    assert isclose(float(summary["combined_plan_realization_probability"]), 0.61)
    assert int(summary["critical_field_null_count"]) == 0
    assert int(summary["raw_contract_pass"]) == 1
    assert "missing_required_field" not in summary["data_issue_codes"]


def test_build_customer_artifact_bundle_zero_step_always_rejects():
    plan = PlanRecord(
        plan_id="zero-step-plan",
        customer_id="cust-zero",
        run_id="run-zero",
        horizon_months=6,
        strategy="balanced",
        actions=[],
        predicted_pd=0.46,
        score=0.05,
        robust_score=0.05,
        status="NEEDS_REVIEW",
        constraint_status="valid",
        trajectory_status="on_track",
        plan_execution_probability=0.41,
    )
    roadmap = {
        "customer_id": "cust-zero",
        "base_pd": 0.46,
        "tau": 0.35,
        "best_plan_id": "zero-step-plan",
        "best_plan_source": "internal",
        "best_status": "NEEDS_REVIEW",
        "phases": [],
        "checkpoints": [
            {"week": 4, "status": "at_risk"},
            {"week": 12, "status": "at_risk"},
            {"week": 24, "status": "missed"},
        ],
        "summary": {
            "decision_status": "NEEDS_REVIEW",
            "credit_readiness_stage": "not_ready_yet",
            "plan_execution_probability": 0.41,
            "approval_dependent_plan_probability": None,
            "offer_acceptance_probability": None,
            "combined_plan_realization_probability": None,
        },
    }

    bundle = build_customer_artifact_bundle(
        customer_id="cust-zero",
        model_version="model-001",
        base_pd=0.46,
        search_profile={"is_denied_target": True, "search_cfg": {"time_budget_ms": 0}},
        segment_context={"income_band": "q1", "risk_band": "high", "segment_caps_applied": False},
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
        local_reason_bundle={"reasons": [], "meta": {}},
        adverse_action_reasons=[],
        dice_backend="skipped",
        dice_records=[],
        dice_telemetry={"method_requested": "random", "method_used": "skipped", "fallback_reason": "policy"},
        search_elapsed_ms=9.0,
        fairness_penalty=0.0,
        decision_log_record={"decision_id": "d-40-2", "selection_propensity": 1.0},
        decision_log_summary={"decision_log_completeness": 1.0},
    )

    summary = bundle.roadmap["summary"]
    assert summary["decision_status"] == "REJECTED"
    assert summary["decision_status_internal"] == "REJECTED"
    assert int(summary["zero_step_flag"]) == 1
    assert int(summary["best_action_count"]) == 0
    assert "zero_step_no_path" in summary["data_issue_codes"]
    assert bundle.metrics_summary["decision_status"] == "REJECTED"


def test_build_customer_artifact_bundle_serializes_full_candidate_pool_with_plan_stage() -> None:
    action = PlanAction(
        feature_name="revol_util",
        current_value=68.0,
        target_value=52.0,
        delta=-16.0,
        time_months=1,
        estimated_cost_usd=14.0,
        action_key="limit_credit_usage",
        action_class="behavioral",
        action_title="Limit credit usage",
        action_group_id="limit_credit_usage:phase_1_stabilize",
        action_execution_probability=0.67,
    )
    internal_plan = PlanRecord(
        plan_id="internal-plan",
        customer_id="cust-source",
        run_id="run-source",
        horizon_months=6,
        strategy="balanced",
        actions=[action],
        predicted_pd=0.33,
        score=0.18,
        robust_score=0.18,
        status="APPROVED",
        constraint_status="valid",
        plan_source="internal",
        plan_execution_probability=0.67,
    )
    dice_plan = PlanRecord(
        plan_id="dice-plan",
        customer_id="cust-source",
        run_id="run-source",
        horizon_months=6,
        strategy="aggressive",
        actions=[action],
        predicted_pd=0.31,
        score=0.19,
        robust_score=0.19,
        status="APPROVED",
        constraint_status="valid",
        plan_source="dice",
        plan_execution_probability=0.69,
    )
    roadmap = _build_customer_roadmap(
        customer_id="cust-source",
        base_pd=0.44,
        tau=0.35,
        best=dice_plan,
        best_source="dice",
        selection_result=_selection_result(dice_plan),
        row=pd.Series({"revol_util": 68.0}),
        model=_DummyModel(),
        calibrator=None,
        feature_cols=["revol_util"],
        local_reason_bundle={"reasons": [], "meta": {"explainability_confidence": 0.82}},
    )

    bundle = build_customer_artifact_bundle(
        customer_id="cust-source",
        model_version="model-001",
        base_pd=0.44,
        search_profile={"is_denied_target": False, "search_cfg": {"time_budget_ms": 0}},
        segment_context={"income_band": "q2", "risk_band": "near", "segment_caps_applied": False},
        validated=[internal_plan],
        candidate_pool=[internal_plan, dice_plan],
        best=dice_plan,
        best_source="dice",
        selection_result=_selection_result(dice_plan),
        roadmap=roadmap,
        msi=0.2,
        alpha=0.05,
        robust_objective="cvar",
        robust_cvar_quantile=0.9,
        local_reason_bundle={"reasons": [], "meta": {"explainability_confidence": 0.82}},
        adverse_action_reasons=[],
        dice_backend="dice_ml",
        dice_records=[dice_plan],
        dice_telemetry={"method_requested": "genetic", "method_used": "genetic", "fallback_reason": ""},
        search_elapsed_ms=8.0,
        fairness_penalty=0.0,
        decision_log_record={"decision_id": "d-source", "selection_propensity": 1.0},
        decision_log_summary={"decision_log_completeness": 1.0},
        path_records=[
            RecoursePathRecord(
                path_id="path-1",
                customer_id="cust-123",
                path_type="customer_only",
                path_signature="increase_income",
                rankable_flag=True,
                path_rank=1,
                representative_plan_id="internal-plan",
                representative_plan_source="internal",
                representative_contender_bucket="ACTIONABLE",
                member_plan_ids=["internal-plan"],
                member_plan_count=1,
                member_source_counts={"internal": 1},
                action_keys=["increase_income"],
                action_owners=["customer"],
                action_categories=["income_growth"],
                primary_metric_keys=["annual_inc"],
                offer_plan=False,
                offer_maturity="none",
                selected_path_flag=True,
            )
        ],
    )

    plans = bundle.plans_df.set_index("plan_id")
    assert set(plans.index) == {"internal-plan", "dice-plan"}
    assert set(plans["plan_source"]) == {"internal", "dice"}
    assert plans.loc["internal-plan", "plan_stage"] == "validated"
    assert plans.loc["dice-plan", "plan_stage"] == "candidate_only"
    assert bundle.roadmap["summary"]["best_plan_source"] == "dice"
    assert bundle.roadmap["summary"]["selected_decision_status"] == bundle.roadmap["summary"]["decision_status"]
    assert bundle.roadmap["summary"]["selected_plan_status_internal"] == "APPROVED"
    assert bundle.roadmap["summary"]["selected_recommendation_source"] == "selected_plan"
    assert bundle.roadmap["summary"]["selected_action_count"] == 1


def test_build_customer_artifact_bundle_captures_dice_lane_metrics() -> None:
    internal_action = PlanAction(
        feature_name="annual_inc",
        current_value=55_000.0,
        target_value=58_000.0,
        delta=3_000.0,
        time_months=3,
        estimated_cost_usd=0.0,
        action_key="increase_income",
        action_class="behavioral",
        action_family="income_growth",
        action_title="Increase income",
        action_group_id="increase_income:phase_2_build",
        checkpoint_metric="annual_inc -> 58000.000000",
        recommendation_validity_status="valid",
    )
    dice_action = PlanAction(
        feature_name="loan_amnt",
        current_value=12000.0,
        target_value=10000.0,
        delta=-2000.0,
        time_months=1,
        estimated_cost_usd=16.0,
        action_key="adjust_requested_loan_amount",
        action_class="behavioral",
        action_family="application_sizing",
        action_title="Reduce requested loan amount",
        action_group_id="adjust_requested_loan_amount:phase_1_stabilize",
        checkpoint_metric="loan_amnt -> 10000.000000",
        primary_numeric_target=PrimaryNumericTarget(
            metric_key="requested_loan_amount",
            unit="currency",
            current_value=12000.0,
            target_value=10000.0,
            delta_value=-2000.0,
            due_month=1,
            direction="decrease",
        ),
        recommendation_validity_status="valid",
    )
    internal_plan = PlanRecord(
        plan_id="internal-best",
        customer_id="cust-dice-metrics",
        run_id="run-dice-metrics",
        horizon_months=6,
        strategy="balanced",
        actions=[internal_action],
        predicted_pd=0.31,
        score=0.14,
        robust_score=0.14,
        status="APPROVED",
        constraint_status="valid",
        plan_source="internal",
        recommendation_validity_status="valid",
        plan_execution_probability=0.61,
    )
    dice_plan = annotate_dice_candidate_quality(
        PlanRecord(
            plan_id="dice-visible",
            customer_id="cust-dice-metrics",
            run_id="run-dice-metrics",
            horizon_months=6,
            strategy="balanced",
            actions=[dice_action],
            predicted_pd=0.29,
            score=0.16,
            robust_score=0.16,
            status="APPROVED",
            constraint_status="valid",
            plan_source="dice",
            recommendation_validity_status="valid",
            plan_execution_probability=0.66,
        ),
        backend_class="heuristic_fallback_timeout",
    )
    roadmap = _build_customer_roadmap(
        customer_id="cust-dice-metrics",
        base_pd=0.44,
        tau=0.35,
        best=internal_plan,
        best_source="internal",
        selection_result=_selection_result(internal_plan),
        row=pd.Series({"annual_inc": 55_000.0, "loan_amnt": 12000.0}),
        model=_DummyModel(),
        calibrator=None,
        feature_cols=["annual_inc", "loan_amnt"],
        local_reason_bundle={"reasons": [], "meta": {"explainability_confidence": 0.82}},
    )

    bundle = build_customer_artifact_bundle(
        customer_id="cust-dice-metrics",
        model_version="model-001",
        base_pd=0.44,
        search_profile={"is_denied_target": False, "search_cfg": {"time_budget_ms": 0}},
        segment_context={"income_band": "q2", "risk_band": "near", "segment_caps_applied": False},
        validated=[internal_plan],
        candidate_pool=[internal_plan, dice_plan],
        best=internal_plan,
        best_source="internal",
        selection_result=_selection_result(internal_plan),
        roadmap=roadmap,
        msi=0.2,
        alpha=0.05,
        robust_objective="cvar",
        robust_cvar_quantile=0.9,
        local_reason_bundle={"reasons": [], "meta": {"explainability_confidence": 0.82}},
        adverse_action_reasons=[],
        dice_backend="heuristic_fallback_timeout",
        dice_records=[dice_plan],
        dice_telemetry={"method_requested": "genetic", "method_used": "genetic", "fallback_reason": "timeout"},
        search_elapsed_ms=8.0,
        fairness_penalty=0.0,
        decision_log_record={"decision_id": "d-source", "selection_propensity": 1.0},
        decision_log_summary={"decision_log_completeness": 1.0},
    )

    assert bundle.metrics_summary["dice_candidate_count"] == 1
    assert bundle.metrics_summary["dice_contender_eligible_count"] == 1
    assert bundle.metrics_summary["dice_warning_candidate_count"] == 1
    assert bundle.metrics_summary["dice_fallback_flag"] == 1
    assert bundle.metrics_summary["selected_dice_flag"] == 0
    assert bundle.metrics_summary["selected_dice_valid_rate"] == 1.0


def test_plan_to_row_serializes_nested_offer_contract_in_timeline():
    action = PlanAction(
        feature_name="delinq_amnt",
        current_value=2400.0,
        target_value=1200.0,
        delta=-1200.0,
        time_months=3,
        estimated_cost_usd=25.0,
        action_key="installment_plan",
        action_class="institutional",
        action_title="Request installment plan",
        action_group_id="installment_plan:phase_2_build",
        offer_contract=OfferContract(
            offer_type="installment_terms",
            offer_family="payment_relief",
            offer_terms={
                "payment_delta_monthly": -120.0,
                "term_extension_months": 6,
                "grace_period_weeks": 2,
            },
            offer_terms_complete=True,
            requires_acceptance=True,
            requires_institutional_approval=False,
            institutional_approval_state="approved",
            offer_policy_arm="installment_terms_policy_v1",
            offer_scoring_profile="installment_terms_v1",
            term_generation_rule="installment_terms_v1",
        ),
        action_execution_probability=0.64,
        approval_dependent_probability=0.0,
        action_group_execution_probability=0.64,
    )
    plan = PlanRecord(
        plan_id="offer-row-plan",
        customer_id="cust-offer-row",
        run_id="run-offer-row",
        horizon_months=6,
        strategy="balanced",
        actions=[action],
        predicted_pd=0.31,
        score=0.2,
        robust_score=0.2,
        status="NEEDS_REVIEW",
        constraint_status="valid",
    )

    row = _plan_to_row(plan)
    timeline_steps = json.loads(row["timeline_steps_json"])

    assert timeline_steps[0]["offer_contract"]["offer_type"] == "installment_terms"
    assert timeline_steps[0]["offer_contract"]["offer_terms"]["term_extension_months"] == 6
    assert timeline_steps[0]["offer_policy_arm"] == "installment_terms_policy_v1"
    assert timeline_steps[0]["action_execution_probability"] == 0.64
