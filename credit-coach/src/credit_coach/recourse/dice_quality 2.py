from __future__ import annotations

from typing import Any

from credit_coach.data.schema import PlanAction, PlanRecord
from credit_coach.recourse.action_space import (
    get_action_template,
    get_dice_generatable_features,
    get_numeric_target_metadata,
)


DICE_QUALITY_GATE_VERSION = "phase_56_v1"
_DICE_SEMANTIC_WARNING_PENALTY_PER_CODE = 8.0
_DICE_SEMANTIC_WARNING_PENALTY_CAP = 16.0
_VALID_CONSTRAINT_STATUSES = {"valid", "repaired", "provisional"}
_GENERIC_ACTION_TITLE_SENTINELS = {
    "",
    "action",
    "unknown action",
    "generic action",
}


def classify_dice_backend_class(backend: str | None) -> str:
    text = str(backend or "").strip().lower()
    if not text or text == "skipped":
        return "skipped"
    if text.startswith("heuristic_fallback"):
        return "heuristic_fallback"
    return "native"


def _is_non_empty_text(value: Any) -> bool:
    return bool(str(value or "").strip())


def _is_actionable(action: PlanAction) -> bool:
    return str(getattr(action, "action_status", "valid") or "valid").strip().lower() != "invalid"


def _requires_primary_numeric_target(action: PlanAction) -> bool:
    numeric_meta = get_numeric_target_metadata(
        str(getattr(action, "feature_name", "") or ""),
        action_month=max(1, int(getattr(action, "time_months", 1) or 1)),
        allow_mapped_feature=True,
    )
    return bool(numeric_meta.get("is_primary_target"))


def _primary_numeric_target_complete(action: PlanAction) -> bool:
    target = getattr(action, "primary_numeric_target", None)
    if target is None:
        return False
    return (
        _is_non_empty_text(getattr(target, "metric_key", None))
        and _is_non_empty_text(getattr(target, "unit", None))
        and _is_non_empty_text(getattr(target, "direction", None))
    )


def _requires_offer_contract(action: PlanAction) -> bool:
    return bool(
        getattr(action, "requires_institutional_approval", False)
        or getattr(action, "approval_pending_semantic_only", False)
        or _is_non_empty_text(getattr(action, "offer_type", None))
        or _is_non_empty_text(getattr(action, "offer_family", None))
        or _is_non_empty_text(getattr(action, "offer_policy_arm", None))
        or bool(getattr(action, "requires_acceptance", False))
    )


def _has_customer_action(actionable_actions: list[PlanAction]) -> bool:
    return any(
        str(getattr(action, "action_class", "") or "").strip().lower() != "institutional"
        and not bool(getattr(action, "approval_pending_semantic_only", False))
        for action in actionable_actions
    )


def _missing_required_annotation(action: PlanAction) -> bool:
    if not _is_non_empty_text(getattr(action, "action_key", None)):
        return True
    if not _is_non_empty_text(getattr(action, "action_class", None)):
        return True
    if not _is_non_empty_text(getattr(action, "action_family", None)):
        return True
    if not _is_non_empty_text(getattr(action, "action_title", None)):
        return True
    if not _is_non_empty_text(getattr(action, "action_group_id", None)):
        return True
    if not _is_non_empty_text(getattr(action, "checkpoint_metric", None)):
        return True
    if _requires_primary_numeric_target(action) and not _primary_numeric_target_complete(action):
        return True
    if _requires_offer_contract(action) and getattr(action, "offer_contract", None) is None:
        return True
    if getattr(action, "recommendation_validity_status", None) is None:
        return True
    return False


def _customer_institution_role_confusion(action: PlanAction) -> bool:
    institution_signal = bool(
        getattr(action, "requires_institutional_approval", False)
        or getattr(action, "approval_pending_semantic_only", False)
        or _requires_offer_contract(action)
    )
    return institution_signal and str(getattr(action, "action_class", "") or "").strip().lower() != "institutional"


def _generic_action_title(action: PlanAction) -> bool:
    title = str(getattr(action, "action_title", "") or "").strip().lower()
    if title in _GENERIC_ACTION_TITLE_SENTINELS:
        return True
    key = str(getattr(action, "action_key", "") or "").strip().lower().replace("_", " ")
    return bool(title and key and title == key)


def _outside_phase56_dice_contract(action: PlanAction) -> bool:
    feature_name = str(getattr(action, "feature_name", "") or "")
    return feature_name not in set(get_dice_generatable_features([feature_name]))


def _categorical_transition_ambiguous(action: PlanAction) -> bool:
    numeric_meta = get_numeric_target_metadata(
        str(getattr(action, "feature_name", "") or ""),
        action_month=max(1, int(getattr(action, "time_months", 1) or 1)),
        allow_mapped_feature=True,
    )
    if str(numeric_meta.get("unit") or "") != "boolean_state":
        return False
    current_value = float(getattr(action, "current_value", 0.0) or 0.0)
    target_value = float(getattr(action, "target_value", current_value) or current_value)
    if abs(current_value - round(current_value)) > 1e-9:
        return True
    if abs(target_value - round(target_value)) > 1e-9:
        return True
    direction = str(numeric_meta.get("direction") or "")
    if direction == "increase" and target_value < current_value:
        return True
    if direction == "decrease" and target_value > current_value:
        return True
    return False


def _group_primary_semantic_codes(actionable_actions: list[PlanAction]) -> set[str]:
    by_action_key: dict[str, set[str]] = {}
    for action in actionable_actions:
        action_key = str(getattr(action, "action_key", "") or "").strip()
        feature_name = str(getattr(action, "feature_name", "") or "").strip()
        if not action_key or not feature_name:
            continue
        by_action_key.setdefault(action_key, set()).add(feature_name)

    semantic_codes: set[str] = set()
    for action_key, feature_names in by_action_key.items():
        try:
            template = get_action_template(action_key)
        except KeyError:
            continue
        if len(template.primary_features_impacted) <= 1:
            continue
        primary_target = str(template.primary_target_feature_name or "").strip()
        if primary_target and primary_target not in feature_names:
            semantic_codes.add("missing_action_group_primary_target")
            semantic_codes.add("support_only_without_primary_target")
    return semantic_codes


def annotate_dice_candidate_quality(
    plan: PlanRecord,
    *,
    backend_class: str | None,
    quality_gate_version: str = DICE_QUALITY_GATE_VERSION,
) -> PlanRecord:
    if str(getattr(plan, "plan_source", "") or "").strip().lower() != "dice":
        return plan

    normalized_backend = classify_dice_backend_class(backend_class or getattr(plan, "dice_backend_class", None))
    actionable_actions = [action for action in list(getattr(plan, "actions", [])) if _is_actionable(action)]
    semantic_codes: set[str] = set()
    warning_codes: set[str] = set()
    annotation_complete = True

    if not actionable_actions:
        semantic_codes.add("zero_actionable_step")

    actionable_families: set[str] = set()
    for action in actionable_actions:
        if _missing_required_annotation(action):
            annotation_complete = False
            semantic_codes.add("missing_required_annotation")
            if _requires_primary_numeric_target(action) and not _primary_numeric_target_complete(action):
                semantic_codes.add("missing_primary_numeric_target")
        if _customer_institution_role_confusion(action):
            semantic_codes.add("customer_institution_role_confusion")
        if _outside_phase56_dice_contract(action):
            semantic_codes.add("outside_phase56_dice_contract")
        if _categorical_transition_ambiguous(action):
            semantic_codes.add("non_deterministic_categorical_transition")
        if not _is_non_empty_text(getattr(action, "action_title", None)) or not _is_non_empty_text(
            getattr(action, "action_family", None)
        ):
            semantic_codes.add("non_renderable_recommendation")
        if _generic_action_title(action):
            warning_codes.add("generic_action_text_fallback")
        family_key = str(getattr(action, "action_family", "") or getattr(action, "feature_name", "") or "").strip()
        if family_key:
            actionable_families.add(family_key)

    semantic_codes |= _group_primary_semantic_codes(actionable_actions)

    if normalized_backend == "heuristic_fallback":
        warning_codes.add("heuristic_fallback_backend")
    if actionable_actions and not _has_customer_action(actionable_actions):
        warning_codes.add("institution_only_without_customer_action")
    if len(actionable_actions) > 1 and len(actionable_families) == 1:
        warning_codes.add("narrow_metric_family_collapse")

    if semantic_codes or not annotation_complete:
        semantic_status = "invalid"
    elif warning_codes:
        semantic_status = "warning"
    else:
        semantic_status = "valid"

    semantic_warning_penalty = 0.0
    if warning_codes:
        semantic_warning_penalty = min(
            _DICE_SEMANTIC_WARNING_PENALTY_CAP,
            _DICE_SEMANTIC_WARNING_PENALTY_PER_CODE * len(warning_codes),
        )

    recommendation_status = str(getattr(plan, "recommendation_validity_status", "") or "valid").strip().lower()
    constraint_status = str(getattr(plan, "constraint_status", "") or "valid").strip().lower()
    contender_eligible = bool(
        normalized_backend != "skipped"
        and recommendation_status != "invalid"
        and annotation_complete
        and semantic_status != "invalid"
        and actionable_actions
        and constraint_status in _VALID_CONSTRAINT_STATUSES
    )

    plan.dice_backend_class = normalized_backend
    plan.dice_annotation_complete = bool(annotation_complete)
    plan.dice_semantic_quality_status = semantic_status
    plan.dice_semantic_quality_codes = sorted(semantic_codes | warning_codes)
    plan.dice_contender_eligible = bool(contender_eligible)
    plan.dice_semantic_warning_penalty = float(semantic_warning_penalty)
    plan.dice_quality_gate_version = str(quality_gate_version)
    return plan


def dice_candidate_is_invalid(plan: PlanRecord) -> bool:
    if str(getattr(plan, "plan_source", "") or "").strip().lower() != "dice":
        return False
    return bool(
        classify_dice_backend_class(getattr(plan, "dice_backend_class", None)) == "skipped"
        or not bool(getattr(plan, "dice_annotation_complete", False))
        or str(getattr(plan, "dice_semantic_quality_status", "") or "").strip().lower() == "invalid"
        or str(getattr(plan, "recommendation_validity_status", "") or "valid").strip().lower() == "invalid"
    )


def dice_candidate_is_warning(plan: PlanRecord) -> bool:
    if str(getattr(plan, "plan_source", "") or "").strip().lower() != "dice":
        return False
    if dice_candidate_is_invalid(plan):
        return False
    return bool(
        str(getattr(plan, "dice_semantic_quality_status", "") or "").strip().lower() == "warning"
        or str(getattr(plan, "recommendation_validity_status", "") or "valid").strip().lower() == "warning"
    )


def selected_dice_is_clean(plan: PlanRecord | None) -> bool:
    if plan is None or str(getattr(plan, "plan_source", "") or "").strip().lower() != "dice":
        return False
    return bool(
        getattr(plan, "dice_contender_eligible", False)
        and getattr(plan, "dice_annotation_complete", False)
        and str(getattr(plan, "dice_semantic_quality_status", "") or "").strip().lower() != "invalid"
        and str(getattr(plan, "recommendation_validity_status", "") or "valid").strip().lower() != "invalid"
    )


def summarize_dice_candidate_metrics(
    dice_records: list[PlanRecord],
    *,
    selected_plan: PlanRecord | None = None,
) -> dict[str, Any]:
    candidate_count = int(len(dice_records))
    eligible_count = int(sum(1 for plan in dice_records if bool(getattr(plan, "dice_contender_eligible", False))))
    invalid_count = int(sum(1 for plan in dice_records if dice_candidate_is_invalid(plan)))
    warning_count = int(sum(1 for plan in dice_records if dice_candidate_is_warning(plan)))
    fallback_count = int(
        sum(
            1
            for plan in dice_records
            if classify_dice_backend_class(getattr(plan, "dice_backend_class", None)) == "heuristic_fallback"
        )
    )
    selected_dice_flag = int(
        selected_plan is not None and str(getattr(selected_plan, "plan_source", "") or "").strip().lower() == "dice"
    )
    selected_dice_valid_flag = int(selected_dice_flag == 1 and selected_dice_is_clean(selected_plan))
    return {
        "dice_candidate_count": candidate_count,
        "dice_contender_eligible_count": eligible_count,
        "dice_invalid_candidate_count": invalid_count,
        "dice_warning_candidate_count": warning_count,
        "dice_all_candidates_ineligible": int(candidate_count > 0 and eligible_count == 0),
        "dice_fallback_candidate_count": fallback_count,
        "dice_fallback_flag": int(fallback_count > 0),
        "selected_dice_flag": selected_dice_flag,
        "selected_dice_valid_flag": selected_dice_valid_flag,
        "selected_dice_annotation_complete_flag": int(
            selected_dice_flag == 1 and bool(getattr(selected_plan, "dice_annotation_complete", False))
        ),
        "selected_dice_semantic_invalid_flag": int(
            selected_dice_flag == 1
            and str(getattr(selected_plan, "dice_semantic_quality_status", "") or "").strip().lower() == "invalid"
        ),
    }


def split_dice_planner_eligible(plans: list[PlanRecord]) -> tuple[list[PlanRecord], list[PlanRecord]]:
    eligible: list[PlanRecord] = []
    ineligible: list[PlanRecord] = []
    for plan in plans:
        if str(getattr(plan, "plan_source", "") or "").strip().lower() == "dice" and not bool(
            getattr(plan, "dice_contender_eligible", False)
        ):
            ineligible.append(plan)
            continue
        eligible.append(plan)
    return eligible, ineligible
