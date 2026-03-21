from __future__ import annotations

import json

import numpy as np
import pandas as pd

from credit_coach.cli.run_recourse import _build_customer_roadmap, _effective_recourse_search, _plan_to_row
from credit_coach.data.schema import PlanAction, PlanRecord, TrajectoryCheckpoint, TrajectoryPhase
from credit_coach.evaluation.fairness import build_group_advantage_penalties, lookup_group_penalty
from credit_coach.recourse.generator import PlanGenConfig, generate_plan_record
from credit_coach.recourse.execution_probability import (
    estimate_action_execution_probability,
    estimate_plan_execution_probability,
)
from credit_coach.recourse.offer_optimization import annotate_offer_optimization
from credit_coach.safety.statistical import estimate_prediction_ci


class _DummyModel:
    def predict_proba(self, x):
        df = x if isinstance(x, pd.DataFrame) else pd.DataFrame(x)
        inc = pd.to_numeric(df.get("annual_inc", pd.Series([50_000.0] * len(df))), errors="coerce").fillna(50_000.0)
        util = pd.to_numeric(df.get("revol_util", pd.Series([50.0] * len(df))), errors="coerce").fillna(50.0)
        p = (0.75 - (inc / 250000.0) + (util / 500.0)).clip(0.05, 0.99).to_numpy()
        return np.column_stack([1.0 - p, p])


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
    assert float(plan.nominal_pd_improvement or 0.0) >= 0.0
    assert float(plan.expected_pd_improvement or 0.0) >= 0.0
    assert int(plan.executable_action_count) >= 1
    assert int(plan.executable_action_group_count) >= 1
    assert all(action.action_group_execution_probability is not None for action in plan.actions)
    assert all(action.action_execution_probability is not None for action in plan.actions)
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
                    institutional_approval_state="approved",
                    offer_type="installment_terms",
                    offer_terms={
                        "payment_delta_monthly": -120.0,
                        "discount_amount": 0.0,
                        "discount_pct": 0.0,
                        "term_extension_months": 6,
                        "interest_rate_delta": -0.25,
                        "grace_period_weeks": 2,
                        "requires_acceptance": True,
                        "requires_institutional_approval": False,
                    },
                    offer_terms_complete=True,
                    requires_acceptance=True,
                    offer_family="payment_relief",
                    offer_scoring_profile="installment_terms_v1",
                    term_generation_rule="installment_terms_v1",
                    offer_policy_arm="installment_terms_policy_v1",
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
    )

    roadmap = _build_customer_roadmap(
        customer_id="cust-18",
        base_pd=0.44,
        tau=0.35,
        best=plan,
        best_source="internal",
        row=pd.Series({"revol_util": 71.0}),
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

    assert "narrative" in roadmap
    assert roadmap["narrative"]["executive_summary"]["decision_view"]["label"]["en"] == "Approval-ready view"
    assert roadmap["narrative"]["steps"][0]["step_id"] == "limit_credit_usage:phase_1_stabilize"
    assert roadmap["narrative"]["steps"][0]["action_summary"]["tr"]
    assert "credit utilization" in roadmap["narrative"]["steps"][0]["expected_outcome"]["en"]
    assert roadmap["narrative"]["checkpoints"][1]["review_action"]["en"]
    assert roadmap["phases"][0]["steps"][0]["primary_numeric_target"]["metric_key"] == "credit_utilization_pct"
    assert roadmap["phases"][0]["steps"][0]["primary_numeric_target"]["generation_notes"] == ["auto_populated_fallback"]
    assert roadmap["narrative"]["technical_reveal"]["feature_changes"][0]["feature_name"] == "revol_util"
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
