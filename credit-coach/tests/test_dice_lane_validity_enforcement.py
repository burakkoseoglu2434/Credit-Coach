from __future__ import annotations

import pandas as pd

from credit_coach.cli.run_recourse import _plan_to_row
from credit_coach.data.schema import PlanAction, PlanRecord, PrimaryNumericTarget
from credit_coach.recourse.dice_quality import (
    annotate_dice_candidate_quality,
    classify_dice_backend_class,
    split_dice_planner_eligible,
    summarize_dice_candidate_metrics,
)


def _make_action() -> PlanAction:
    return PlanAction(
        feature_name="loan_amnt",
        current_value=12000.0,
        target_value=10000.0,
        delta=-2000.0,
        time_months=1,
        estimated_cost_usd=12.0,
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
        recommendation_validity_codes=[],
    )


def _make_plan(*, plan_id: str, actions: list[PlanAction], plan_source: str = "dice") -> PlanRecord:
    return PlanRecord(
        plan_id=plan_id,
        customer_id="cust-dice",
        run_id="run-dice",
        horizon_months=6,
        strategy="balanced",
        actions=actions,
        predicted_pd=0.29,
        score=0.18,
        robust_score=0.18,
        status="APPROVED",
        constraint_status="valid",
        plan_source=plan_source,
        recommendation_validity_status="valid",
        plan_execution_probability=0.64,
    )


def test_classify_dice_backend_class_maps_native_fallback_and_skipped() -> None:
    assert classify_dice_backend_class("dice") == "native"
    assert classify_dice_backend_class("heuristic_fallback_timeout") == "heuristic_fallback"
    assert classify_dice_backend_class("skipped") == "skipped"
    assert classify_dice_backend_class("") == "skipped"


def test_annotate_dice_candidate_quality_marks_missing_primary_target_invalid() -> None:
    plan = _make_plan(plan_id="dice-invalid", actions=[_make_action()])
    plan.actions[0].primary_numeric_target = None

    annotated = annotate_dice_candidate_quality(plan, backend_class="native")

    assert annotated.dice_annotation_complete is False
    assert annotated.dice_semantic_quality_status == "invalid"
    assert annotated.dice_contender_eligible is False
    assert "missing_required_annotation" in annotated.dice_semantic_quality_codes
    assert "missing_primary_numeric_target" in annotated.dice_semantic_quality_codes


def test_heuristic_fallback_backend_is_warning_but_can_remain_eligible() -> None:
    plan = _make_plan(plan_id="dice-warning", actions=[_make_action()])

    annotated = annotate_dice_candidate_quality(plan, backend_class="heuristic_fallback_timeout")

    assert annotated.dice_backend_class == "heuristic_fallback"
    assert annotated.dice_annotation_complete is True
    assert annotated.dice_semantic_quality_status == "warning"
    assert annotated.dice_contender_eligible is True
    assert annotated.dice_semantic_warning_penalty > 0.0
    assert "heuristic_fallback_backend" in annotated.dice_semantic_quality_codes


def test_split_dice_planner_eligible_preserves_visibility_but_filters_ineligible_dice() -> None:
    clean_dice = annotate_dice_candidate_quality(_make_plan(plan_id="dice-clean", actions=[_make_action()]), backend_class="native")
    invalid_dice = _make_plan(plan_id="dice-bad", actions=[_make_action()])
    invalid_dice.actions[0].primary_numeric_target = None
    invalid_dice = annotate_dice_candidate_quality(invalid_dice, backend_class="native")
    internal_plan = _make_plan(plan_id="internal-clean", actions=[_make_action()], plan_source="internal")

    eligible, removed = split_dice_planner_eligible([clean_dice, invalid_dice, internal_plan])

    assert [plan.plan_id for plan in eligible] == ["dice-clean", "internal-clean"]
    assert [plan.plan_id for plan in removed] == ["dice-bad"]


def test_summarize_dice_candidate_metrics_and_plan_row_emit_phase_46_truth() -> None:
    clean_dice = annotate_dice_candidate_quality(_make_plan(plan_id="dice-clean", actions=[_make_action()]), backend_class="native")
    warning_dice = annotate_dice_candidate_quality(
        _make_plan(plan_id="dice-warning", actions=[_make_action()]),
        backend_class="heuristic_fallback_timeout",
    )
    invalid_dice = _make_plan(plan_id="dice-invalid", actions=[_make_action()])
    invalid_dice.actions[0].primary_numeric_target = None
    invalid_dice = annotate_dice_candidate_quality(invalid_dice, backend_class="native")

    metrics = summarize_dice_candidate_metrics(
        [clean_dice, warning_dice, invalid_dice],
        selected_plan=clean_dice,
    )

    assert metrics["dice_candidate_count"] == 3
    assert metrics["dice_contender_eligible_count"] == 2
    assert metrics["dice_invalid_candidate_count"] == 1
    assert metrics["dice_warning_candidate_count"] == 1
    assert metrics["selected_dice_valid_flag"] == 1

    row = _plan_to_row(warning_dice)
    assert row["dice_backend_class"] == "heuristic_fallback"
    assert int(row["dice_annotation_complete"]) == 1
    assert row["dice_semantic_quality_status"] == "warning"
    assert int(row["dice_contender_eligible"]) == 1


def test_annotate_dice_candidate_quality_rejects_support_only_group_candidate() -> None:
    support_only = PlanAction(
        feature_name="term",
        current_value=60.0,
        target_value=36.0,
        delta=-24.0,
        time_months=3,
        estimated_cost_usd=20.0,
        action_key="refinance",
        action_class="structural",
        action_family="debt_restructuring",
        action_title="Refinance or restructure debt",
        action_group_id="refinance:phase_2_build",
        checkpoint_metric="term -> 36.000000",
        recommendation_validity_status="valid",
        recommendation_validity_codes=[],
    )
    plan = _make_plan(plan_id="dice-support-only", actions=[support_only])

    annotated = annotate_dice_candidate_quality(plan, backend_class="native")

    assert annotated.dice_annotation_complete is True
    assert annotated.dice_semantic_quality_status == "invalid"
    assert annotated.dice_contender_eligible is False
    assert "missing_action_group_primary_target" in annotated.dice_semantic_quality_codes
    assert "support_only_without_primary_target" in annotated.dice_semantic_quality_codes


def test_annotate_dice_candidate_quality_accepts_deterministic_verification_state_candidate() -> None:
    verification = PlanAction(
        feature_name="verification_status",
        current_value=1.0,
        target_value=2.0,
        delta=1.0,
        time_months=1,
        estimated_cost_usd=5.0,
        action_key="verify_income_documentation",
        action_class="behavioral",
        action_family="cashflow_management",
        action_title="Complete income verification",
        action_group_id="verify_income_documentation:phase_1_stabilize",
        checkpoint_metric="verification_status -> 2.000000",
        primary_numeric_target=PrimaryNumericTarget(
            metric_key="income_verification_state",
            unit="boolean_state",
            current_value=1.0,
            target_value=2.0,
            delta_value=1.0,
            due_month=1,
            direction="increase",
        ),
        recommendation_validity_status="valid",
        recommendation_validity_codes=[],
    )
    plan = _make_plan(plan_id="dice-verification", actions=[verification])

    annotated = annotate_dice_candidate_quality(plan, backend_class="native")

    assert annotated.dice_annotation_complete is True
    assert annotated.dice_semantic_quality_status == "valid"
    assert annotated.dice_contender_eligible is True
