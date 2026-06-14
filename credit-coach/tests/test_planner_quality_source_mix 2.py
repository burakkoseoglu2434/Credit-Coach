from __future__ import annotations

from credit_coach.cli.run_recourse import _plan_to_row
from credit_coach.coaching.planner import (
    annotate_plan_planner_quality,
    candidate_source_counts,
    candidate_source_presence_flags,
    choose_best_plan,
    classify_plan_contender,
    filter_empty_contenders,
    filter_selectable_contenders,
)
from credit_coach.data.schema import PlanAction, PlanRecord


def _action(
    *,
    feature_name: str = "revol_util",
    current_value: float = 72.0,
    target_value: float = 50.0,
    action_key: str | None = "limit_credit_usage",
    action_title: str | None = "Limit credit usage",
    action_class: str | None = "behavioral",
    approval_pending_semantic_only: bool = False,
) -> PlanAction:
    return PlanAction(
        feature_name=feature_name,
        current_value=current_value,
        target_value=target_value,
        delta=target_value - current_value,
        time_months=1,
        estimated_cost_usd=25.0,
        action_key=action_key,
        action_title=action_title,
        action_class=action_class,
        approval_pending_semantic_only=approval_pending_semantic_only,
    )


def _plan(
    plan_id: str,
    *,
    plan_source: str | None,
    actions: list[PlanAction],
    predicted_pd: float,
    expected_pd_improvement: float,
    plan_execution_probability: float = 0.55,
    robust_score: float = 0.2,
    status: str = "NEEDS_REVIEW",
    constraint_status: str = "valid",
    executable_action_count: int | None = None,
    approval_pending_action_count: int = 0,
    offer_plan: bool = False,
    rankable_offer_count: int = 0,
) -> PlanRecord:
    return PlanRecord(
        plan_id=plan_id,
        customer_id="cust-1",
        run_id="run-1",
        horizon_months=6,
        strategy="balanced",
        actions=actions,
        plan_source=plan_source,
        predicted_pd=predicted_pd,
        score=robust_score,
        robust_score=robust_score,
        status=status,
        constraint_status=constraint_status,
        plan_execution_probability=plan_execution_probability,
        expected_pd_improvement=expected_pd_improvement,
        executable_action_count=len(actions) if executable_action_count is None else executable_action_count,
        approval_pending_action_count=approval_pending_action_count,
        offer_plan=offer_plan,
        rankable_offer_count=rankable_offer_count,
    )


def test_candidate_source_counts_prefers_explicit_plan_source() -> None:
    plans = [
        _plan("run_dice_like_name", plan_source="internal", actions=[_action()], predicted_pd=0.34, expected_pd_improvement=0.03),
        _plan("run_rule_like_name", plan_source="rule", actions=[_action()], predicted_pd=0.35, expected_pd_improvement=0.02),
        _plan("run_fallback_like_name", plan_source="fallback", actions=[_action()], predicted_pd=0.37, expected_pd_improvement=0.01),
    ]

    counts = candidate_source_counts(plans)
    presence = candidate_source_presence_flags(plans)

    assert counts == {"internal": 1, "dice": 0, "rule": 1, "fallback": 1}
    assert presence == {"internal": 1, "dice": 0, "rule": 1, "fallback": 1}


def test_filter_empty_contenders_removes_zero_and_semantic_empty_but_keeps_approval_shell() -> None:
    zero_action = _plan("zero", plan_source="internal", actions=[], predicted_pd=0.45, expected_pd_improvement=0.0)
    semantic_empty = _plan(
        "semantic-empty",
        plan_source="dice",
        actions=[_action(action_key=None, action_title=None, action_class=None)],
        predicted_pd=0.42,
        expected_pd_improvement=0.01,
    )
    approval_shell = _plan(
        "approval-shell",
        plan_source="rule",
        actions=[_action(action_class="institutional", approval_pending_semantic_only=True)],
        predicted_pd=0.40,
        expected_pd_improvement=0.02,
        executable_action_count=0,
        approval_pending_action_count=1,
        offer_plan=True,
    )
    actionable = _plan(
        "actionable",
        plan_source="internal",
        actions=[_action()],
        predicted_pd=0.33,
        expected_pd_improvement=0.04,
    )

    kept, removed = filter_empty_contenders([zero_action, semantic_empty, approval_shell, actionable])

    assert [plan.plan_id for plan in kept] == ["approval-shell", "actionable"]
    assert sorted(plan.plan_id for plan in removed) == ["semantic-empty", "zero"]
    assert classify_plan_contender(zero_action) == ("EMPTY", "ZERO_ACTION")
    assert classify_plan_contender(semantic_empty) == ("EMPTY", "SEMANTIC_EMPTY")
    assert classify_plan_contender(approval_shell) == ("APPROVAL_SHELL_ONLY", None)


def test_filter_selectable_contenders_excludes_approval_shell_only_candidates() -> None:
    approval_shell = _plan(
        "approval-shell",
        plan_source="rule",
        actions=[_action(action_class="institutional", approval_pending_semantic_only=True)],
        predicted_pd=0.39,
        expected_pd_improvement=0.02,
        executable_action_count=0,
        approval_pending_action_count=1,
        offer_plan=True,
    )
    actionable = _plan(
        "actionable",
        plan_source="internal",
        actions=[_action()],
        predicted_pd=0.33,
        expected_pd_improvement=0.04,
    )

    kept, removed = filter_selectable_contenders([approval_shell, actionable])

    assert [plan.plan_id for plan in kept] == ["actionable"]
    assert [plan.plan_id for plan in removed] == ["approval-shell"]


def test_choose_best_plan_prefers_internal_on_near_tie() -> None:
    internal = _plan(
        "internal-plan",
        plan_source="internal",
        actions=[_action()],
        predicted_pd=0.331,
        expected_pd_improvement=0.024,
        plan_execution_probability=0.56,
        robust_score=0.24,
    )
    dice = _plan(
        "dice-plan",
        plan_source="dice",
        actions=[_action()],
        predicted_pd=0.329,
        expected_pd_improvement=0.026,
        plan_execution_probability=0.57,
        robust_score=0.25,
    )

    best = choose_best_plan([dice, internal], base_pd=0.40, tau=0.35)

    assert best.plan_id == "internal-plan"


def test_choose_best_plan_does_not_override_materially_better_dice_candidate() -> None:
    internal = _plan(
        "internal-plan",
        plan_source="internal",
        actions=[_action()],
        predicted_pd=0.340,
        expected_pd_improvement=0.020,
        plan_execution_probability=0.50,
        robust_score=0.20,
    )
    dice = _plan(
        "dice-plan",
        plan_source="dice",
        actions=[_action()],
        predicted_pd=0.300,
        expected_pd_improvement=0.050,
        plan_execution_probability=0.66,
        robust_score=0.35,
    )

    best = choose_best_plan([internal, dice], base_pd=0.40, tau=0.35)

    assert best.plan_id == "dice-plan"


def test_plan_to_row_serializes_phase42_planner_fields() -> None:
    plan = annotate_plan_planner_quality(
        _plan(
            "row-plan",
            plan_source="internal",
            actions=[_action()],
            predicted_pd=0.31,
            expected_pd_improvement=0.04,
            offer_plan=True,
            rankable_offer_count=1,
        )
    )

    row = _plan_to_row(plan)

    assert row["plan_source"] == "internal"
    assert row["contender_bucket"] == "ACTIONABLE"
    assert row["empty_candidate_reason"] == ""
    assert row["approval_shell_only_flag"] == 0
    assert row["offer_maturity"] == "active_rankable"


def test_choose_best_plan_movement_mode_prefers_customer_only_on_near_tie() -> None:
    customer_only = _plan(
        "customer-only-plan",
        plan_source="internal",
        actions=[_action(action_key="limit_credit_usage")],
        predicted_pd=0.33,
        expected_pd_improvement=0.045,
        plan_execution_probability=0.64,
        robust_score=0.22,
        status="APPROVED",
    )
    customer_only.nominal_pd_improvement = 0.08
    customer_only.mean_group_difficulty_score = 0.28
    customer_only.peak_group_difficulty_score = 0.33
    customer_only.follow_through_readiness_label = "moderate"

    institution_assisted = _plan(
        "institution-assisted-plan",
        plan_source="internal",
        actions=[_action(action_key="credit_limit_adjustment", action_class="institutional")],
        predicted_pd=0.329,
        expected_pd_improvement=0.046,
        plan_execution_probability=0.63,
        robust_score=0.23,
        status="APPROVED",
        offer_plan=True,
        rankable_offer_count=1,
        approval_pending_action_count=1,
    )
    institution_assisted.nominal_pd_improvement = 0.081
    institution_assisted.approval_dependent_plan_probability = 0.58
    institution_assisted.mean_group_difficulty_score = 0.31
    institution_assisted.peak_group_difficulty_score = 0.36
    institution_assisted.follow_through_readiness_label = "moderate"

    best = choose_best_plan(
        [institution_assisted, customer_only],
        base_pd=0.43,
        tau=0.35,
        denied_mode=True,
        movement_ranking_enabled=True,
    )

    assert best.plan_id == "customer-only-plan"
    assert "CUSTOMER_ONLY_TIEBREAK" in customer_only.movement_rank_reason_codes
    assert "INSTITUTION_DEPENDENCY_PENALTY" in institution_assisted.movement_rank_reason_codes
