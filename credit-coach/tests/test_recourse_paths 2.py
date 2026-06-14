from __future__ import annotations

from credit_coach.data.schema import PlanAction, PlanRecord
from credit_coach.coaching.planner import choose_best_plan
from credit_coach.recourse.action_space import get_action_template
from credit_coach.recourse.pathing import build_recourse_path_records, summarize_path_metrics


def _action(action_key: str, *, feature_name: str | None = None) -> PlanAction:
    template = get_action_template(action_key)
    feature = feature_name or template.primary_target_feature_name or template.primary_features_impacted[0]
    current_value = 100.0
    target_value = 90.0
    if action_key in {"increase_regular_income", "credit_limit_adjustment"}:
        current_value = 50.0
        target_value = 60.0
    return PlanAction(
        feature_name=feature,
        current_value=current_value,
        target_value=target_value,
        delta=target_value - current_value,
        time_months=3,
        estimated_cost_usd=25.0,
        action_key=action_key,
        action_class=template.action_class,
        action_family=template.action_family,
        action_title=template.title,
        requires_institutional_approval=template.requires_institutional_approval,
        institutional_approval_state=template.institutional_approval_state,
        approval_pending_semantic_only=template.approval_pending_semantic_only,
        offer_type=template.offer_type,
        requires_acceptance=template.requires_acceptance,
        offer_family=template.offer_family,
        offer_scoring_profile=template.offer_scoring_profile,
        term_generation_rule=template.term_generation_rule,
        offer_policy_arm=template.offer_policy_arm,
    )


def _plan(
    plan_id: str,
    action: PlanAction,
    *,
    source: str = "internal",
    status: str = "APPROVED",
    predicted_pd: float = 0.24,
    score: float = 10.0,
    horizon: int = 6,
    strategy: str = "balanced",
    offer_plan: bool = False,
    rankable_offer_count: int = 0,
    executable_action_count: int = 1,
    approval_pending_action_count: int = 0,
) -> PlanRecord:
    return PlanRecord(
        plan_id=plan_id,
        customer_id="cust-path",
        run_id="run-path",
        horizon_months=horizon,
        strategy=strategy,
        actions=[action],
        plan_source=source,  # type: ignore[arg-type]
        predicted_pd=predicted_pd,
        score=score,
        robust_score=score,
        status=status,  # type: ignore[arg-type]
        offer_plan=offer_plan,
        rankable_offer_count=rankable_offer_count,
        executable_action_count=executable_action_count,
        approval_pending_action_count=approval_pending_action_count,
        plan_execution_probability=0.75,
    )


def test_build_recourse_path_records_collapses_near_duplicate_customer_only_plans() -> None:
    customer_a = _plan(
        "plan-customer-a",
        _action("limit_credit_usage"),
        source="internal",
        status="APPROVED",
        predicted_pd=0.22,
        horizon=3,
        strategy="conservative",
    )
    customer_b = _plan(
        "plan-customer-b",
        _action("limit_credit_usage"),
        source="dice",
        status="NEEDS_REVIEW",
        predicted_pd=0.27,
        horizon=12,
        strategy="aggressive",
    )
    institution = _plan(
        "plan-institution",
        _action("credit_limit_adjustment"),
        source="rule",
        status="APPROVED",
        predicted_pd=0.21,
        offer_plan=True,
        rankable_offer_count=1,
    )

    paths = build_recourse_path_records(
        [customer_a, customer_b, institution],
        selected_plan_id="plan-institution",
        base_pd=0.40,
        tau=0.35,
    )

    assert len(paths) == 2
    customer_path = next(path for path in paths if path.path_type == "customer_only")
    institution_path = next(path for path in paths if path.path_type == "institution_assisted")

    assert set(customer_path.member_plan_ids) == {"plan-customer-a", "plan-customer-b"}
    assert customer_path.representative_plan_id == "plan-customer-a"
    assert institution_path.selected_path_flag is True
    assert customer_a.path_id == customer_b.path_id
    assert customer_a.path_type == "customer_only"
    assert institution.path_type == "institution_assisted"


def test_build_recourse_path_records_classifies_customer_institution_and_hybrid_paths() -> None:
    customer = _plan("plan-customer", _action("limit_credit_usage"), source="internal", status="APPROVED")
    institution = _plan(
        "plan-institution",
        _action("credit_limit_adjustment"),
        source="rule",
        status="APPROVED",
        offer_plan=True,
        rankable_offer_count=1,
    )
    hybrid = _plan(
        "plan-hybrid",
        _action("debt_consolidation"),
        source="rule",
        status="APPROVED",
        predicted_pd=0.23,
        offer_plan=True,
        rankable_offer_count=1,
    )

    paths = build_recourse_path_records(
        [customer, institution, hybrid],
        selected_plan_id="plan-hybrid",
        base_pd=0.42,
        tau=0.35,
    )
    metrics = summarize_path_metrics(paths)

    assert {path.path_type for path in paths} == {
        "customer_only",
        "institution_assisted",
        "hybrid",
    }
    assert metrics["path_count"] == 3
    assert metrics["rankable_path_count"] == 3
    assert metrics["multi_path_flag"] == 1
    assert metrics["selected_path_type"] == "hybrid"
    assert metrics["institution_action_rate"] == 2 / 3
    assert metrics["non_utilization_action_rate"] == 2 / 3
    assert metrics["action_diversity_index"] > 0.0


def test_build_recourse_path_records_keeps_approval_shell_paths_non_rankable() -> None:
    actionable = _plan("plan-actionable", _action("limit_credit_usage"), source="internal", status="APPROVED")
    shell_action = _action("credit_limit_adjustment")
    shell_action.approval_pending_semantic_only = True
    shell_action.institutional_approval_state = "pending"
    shell = _plan(
        "plan-shell",
        shell_action,
        source="rule",
        status="NEEDS_REVIEW",
        offer_plan=True,
        executable_action_count=0,
        approval_pending_action_count=1,
    )

    paths = build_recourse_path_records(
        [actionable, shell],
        selected_plan_id="plan-actionable",
        base_pd=0.39,
        tau=0.35,
    )
    metrics = summarize_path_metrics(paths)

    shell_path = next(path for path in paths if "plan-shell" in path.member_plan_ids)
    assert shell_path.rankable_flag is False
    assert shell_path.path_rank is None
    assert shell.path_rankable_flag is False
    assert metrics["path_count"] == 2
    assert metrics["rankable_path_count"] == 1
    assert metrics["multi_path_flag"] == 0


def test_build_recourse_path_records_stays_aligned_with_movement_ranked_selection() -> None:
    customer = _plan(
        "plan-customer-threshold",
        _action("limit_credit_usage"),
        source="internal",
        status="APPROVED",
        predicted_pd=0.34,
    )
    customer.nominal_pd_improvement = 0.09
    customer.expected_pd_improvement = 0.0495
    customer.plan_execution_probability = 0.55
    customer.mean_group_difficulty_score = 0.36
    customer.peak_group_difficulty_score = 0.42
    customer.follow_through_readiness_label = "moderate"

    hybrid = _plan(
        "plan-hybrid-weak",
        _action("debt_consolidation"),
        source="rule",
        status="APPROVED",
        predicted_pd=0.36,
        offer_plan=True,
        rankable_offer_count=1,
        approval_pending_action_count=1,
    )
    hybrid.nominal_pd_improvement = 0.07
    hybrid.expected_pd_improvement = 0.056
    hybrid.plan_execution_probability = 0.80
    hybrid.approval_dependent_plan_probability = 0.60
    hybrid.mean_group_difficulty_score = 0.20
    hybrid.peak_group_difficulty_score = 0.25
    hybrid.follow_through_readiness_label = "high"

    best = choose_best_plan(
        [hybrid, customer],
        base_pd=0.43,
        tau=0.35,
        denied_mode=True,
        movement_ranking_enabled=True,
    )
    paths = build_recourse_path_records(
        [hybrid, customer],
        selected_plan_id=best.plan_id,
        base_pd=0.43,
        tau=0.35,
        denied_mode=True,
        movement_ranking_enabled=True,
    )

    assert best.plan_id == "plan-customer-threshold"
    assert paths[0].representative_plan_id == "plan-customer-threshold"
    assert paths[0].path_type == "customer_only"
    assert paths[0].selected_path_flag is True
