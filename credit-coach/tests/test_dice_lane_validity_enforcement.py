from __future__ import annotations

import pandas as pd

from credit_coach.cli.run_recourse import _plan_to_row
from credit_coach.data.schema import PlanAction, PlanRecord
from credit_coach.recourse.dice_quality import (
    annotate_dice_candidate_quality,
    classify_dice_backend_class,
    split_dice_planner_eligible,
    summarize_dice_candidate_metrics,
)


def _make_action() -> PlanAction:
    return PlanAction(
        feature_name="revol_util",
        current_value=62.0,
        target_value=44.0,
        delta=-18.0,
        time_months=1,
        estimated_cost_usd=12.0,
        action_key="limit_credit_usage",
        action_class="behavioral",
        action_family="credit_utilization",
        action_title="Reduce utilization pressure",
        action_group_id="limit_credit_usage:phase_1_stabilize",
        checkpoint_metric="revol_util -> 44.000000",
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
