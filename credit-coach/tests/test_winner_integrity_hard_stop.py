from __future__ import annotations

import pandas as pd

from credit_coach.cli.run_recourse import _build_customer_roadmap, build_customer_artifact_bundle
from credit_coach.coaching.planner import choose_best_plan, filter_selectable_contenders
from credit_coach.data.schema import PlanAction, PlanRecord, PrimaryNumericTarget
from credit_coach.recourse.recommendation_validity import annotate_plan_recommendation_validity


class _DummyModel:
    def predict_proba(self, x):
        frame = x if isinstance(x, pd.DataFrame) else pd.DataFrame(x)
        pd_values = pd.to_numeric(frame.get("revol_util", pd.Series([50.0] * len(frame))), errors="coerce").fillna(50.0).div(100.0)
        return pd.DataFrame({"good": 1.0 - pd_values, "bad": pd_values}).to_numpy()


def _action(
    *,
    feature_name: str,
    metric_key: str,
    current_value: float,
    target_value: float,
    direction: str,
    action_key: str,
    action_class: str,
) -> PlanAction:
    return PlanAction(
        feature_name=feature_name,
        current_value=current_value,
        target_value=target_value,
        delta=target_value - current_value,
        time_months=1,
        estimated_cost_usd=25.0,
        action_key=action_key,
        action_class=action_class,
        primary_numeric_target=PrimaryNumericTarget(
            metric_key=metric_key,
            unit="currency" if metric_key == "monthly_payment_amount" else "percentage_points",
            current_value=current_value,
            target_value=target_value,
            delta_value=target_value - current_value,
            due_month=1,
            direction=direction,
        ),
    )


def _plan(
    plan_id: str,
    action: PlanAction,
    *,
    plan_source: str,
    predicted_pd: float,
    status: str = "NEEDS_REVIEW",
    constraint_status: str = "valid",
) -> PlanRecord:
    return annotate_plan_recommendation_validity(
        PlanRecord(
            plan_id=plan_id,
            customer_id="cust-1",
            run_id="run-1",
            horizon_months=6,
            strategy="balanced",
            actions=[action],
            plan_source=plan_source,
            predicted_pd=predicted_pd,
            robust_score=0.2,
            score=0.2,
            status=status,
            constraint_status=constraint_status,
            plan_execution_probability=0.55,
            expected_pd_improvement=0.02,
        )
    )


def test_choose_best_plan_widens_to_valid_constraint_pool_when_preferred_valid_is_exhausted() -> None:
    invalid_preferred = _plan(
        "dice-invalid",
        _action(
            feature_name="installment",
            metric_key="monthly_payment_amount",
            current_value=278.6,
            target_value=455.5,
            direction="decrease",
            action_key="refinance",
            action_class="structural",
        ),
        plan_source="dice",
        predicted_pd=0.28,
        status="NEEDS_REVIEW",
    )
    valid_rejected = _plan(
        "internal-valid",
        _action(
            feature_name="installment",
            metric_key="monthly_payment_amount",
            current_value=778.4,
            target_value=746.4,
            direction="decrease",
            action_key="refinance",
            action_class="structural",
        ),
        plan_source="internal",
        predicted_pd=0.30,
        status="REJECTED",
    )

    result = choose_best_plan([invalid_preferred, valid_rejected], base_pd=0.40, tau=0.35)

    assert result.best_plan is not None
    assert result.best_plan.plan_id == "internal-valid"
    assert result.selection_outcome == "selected_valid_winner"
    assert result.selection_stage == "widened_constraint_valid"
    assert result.invalid_candidates_removed_count == 1
    assert result.preferred_pool_invalid_exhausted is True
    assert result.selected_from_widened_valid_pool is True


def test_choose_best_plan_returns_no_valid_winner_when_all_candidates_are_invalid() -> None:
    invalid_one = _plan(
        "dice-invalid-1",
        _action(
            feature_name="revol_util",
            metric_key="credit_utilization_pct",
            current_value=32.6,
            target_value=43.1,
            direction="decrease",
            action_key="limit_credit_usage",
            action_class="behavioral",
        ),
        plan_source="dice",
        predicted_pd=0.33,
    )
    invalid_two = _plan(
        "dice-invalid-2",
        _action(
            feature_name="installment",
            metric_key="monthly_payment_amount",
            current_value=253.0,
            target_value=447.8,
            direction="decrease",
            action_key="refinance",
            action_class="structural",
        ),
        plan_source="dice",
        predicted_pd=0.34,
    )

    result = choose_best_plan([invalid_one, invalid_two], base_pd=0.40, tau=0.35)

    assert result.best_plan is None
    assert result.selection_outcome == "no_valid_winner"
    assert result.selection_stage == "no_valid_winner"
    assert result.invalid_candidates_removed_count == 2
    assert result.preferred_pool_invalid_exhausted is True
    assert result.no_valid_candidate_available is True


def test_build_customer_artifact_bundle_preserves_no_valid_winner_integrity() -> None:
    invalid_only = _plan(
        "dice-invalid",
        _action(
            feature_name="installment",
            metric_key="monthly_payment_amount",
            current_value=278.6,
            target_value=455.5,
            direction="decrease",
            action_key="refinance",
            action_class="structural",
        ),
        plan_source="dice",
        predicted_pd=0.29,
    )
    selection_result = choose_best_plan([invalid_only], base_pd=0.40, tau=0.35)

    roadmap = _build_customer_roadmap(
        customer_id="cust-none",
        base_pd=0.40,
        tau=0.35,
        best=selection_result.best_plan,
        best_source="",
        selection_result=selection_result,
        row=pd.Series({"revol_util": 70.0}),
        model=_DummyModel(),
        calibrator=None,
        feature_cols=["revol_util"],
        local_reason_bundle={"reasons": [], "meta": {"explainability_confidence": 0.7}},
    )
    bundle = build_customer_artifact_bundle(
        customer_id="cust-none",
        model_version="model-001",
        base_pd=0.40,
        search_profile={"is_denied_target": False, "search_cfg": {"time_budget_ms": 0}},
        segment_context={"income_band": "q2", "risk_band": "near", "segment_caps_applied": False},
        validated=[],
        candidate_pool=[invalid_only],
        best=selection_result.best_plan,
        best_source="",
        selection_result=selection_result,
        roadmap=roadmap,
        msi=0.2,
        alpha=0.05,
        robust_objective="cvar",
        robust_cvar_quantile=0.9,
        local_reason_bundle={"reasons": [], "meta": {"explainability_confidence": 0.7}},
        adverse_action_reasons=[],
        dice_backend="dice_ml",
        dice_records=[invalid_only],
        dice_telemetry={"method_requested": "random", "method_used": "dice_ml", "fallback_reason": ""},
        search_elapsed_ms=8.0,
        fairness_penalty=0.0,
        decision_log_record={"decision_id": "d-no-valid", "selection_propensity": 0.0},
        decision_log_summary={"decision_log_completeness": 1.0},
    )

    assert bundle.roadmap["summary"]["selection_outcome"] == "no_valid_winner"
    assert bundle.roadmap["summary"]["selection_stage"] == "no_valid_winner"
    assert bundle.roadmap["summary"]["best_plan_id"] is None
    assert bundle.roadmap["summary"]["plan_contract_pass"] == 0
    assert bundle.roadmap["summary"]["selected_recommendation_text"] is None
    assert bundle.roadmap["summary"]["selected_recommendation_source"] == "empty_state"
    assert bundle.roadmap["summary"]["selected_action_count"] == 0
    assert bundle.roadmap["summary"]["selected_path_customer_summary"] == ""
    assert bundle.roadmap["summary"]["selected_path_operator_summary"] == ""
    assert bundle.roadmap["summary"]["selected_path_render_version"] == ""
    assert bundle.roadmap_steps_df.empty
    assert bundle.metrics_summary["selection_outcome"] == "no_valid_winner"
    assert bundle.metrics_summary["best_plan_id"] == ""
    assert bundle.metrics_summary["selected_recommendation_source"] == "empty_state"
    assert bundle.metrics_summary["selected_path_customer_summary"] == ""
    assert bundle.metrics_summary["selected_path_operator_summary"] == ""
    assert bundle.metrics_summary["selected_path_render_version"] == ""
    assert bundle.paths_df.empty


def test_rule_approval_shell_does_not_displace_actionable_winner_candidates() -> None:
    approval_shell = _plan(
        "rule-shell",
        PlanAction(
            feature_name="total_rev_hi_lim",
            current_value=6000.0,
            target_value=7200.0,
            delta=1200.0,
            time_months=3,
            estimated_cost_usd=12.0,
            action_key="credit_limit_adjustment",
            action_class="institutional",
            action_family="limit_management",
            action_title="Request credit limit adjustment",
            action_group_id="credit_limit_adjustment:phase_2_build",
            requires_institutional_approval=True,
            institutional_approval_state="pending",
            approval_pending_semantic_only=True,
        ),
        plan_source="rule",
        predicted_pd=0.27,
        constraint_status="provisional",
    )
    approval_shell.executable_action_count = 0
    approval_shell.approval_pending_action_count = 1
    actionable = _plan(
        "internal-valid",
        _action(
            feature_name="revol_util",
            metric_key="credit_utilization_pct",
            current_value=72.0,
            target_value=52.0,
            direction="decrease",
            action_key="limit_credit_usage",
            action_class="behavioral",
        ),
        plan_source="internal",
        predicted_pd=0.30,
    )

    selectable, removed = filter_selectable_contenders([approval_shell, actionable])
    result = choose_best_plan(selectable, base_pd=0.40, tau=0.35)

    assert [plan.plan_id for plan in selectable] == ["internal-valid"]
    assert [plan.plan_id for plan in removed] == ["rule-shell"]
    assert result.best_plan is not None
    assert result.best_plan.plan_id == "internal-valid"
