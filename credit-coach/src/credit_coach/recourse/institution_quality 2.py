from __future__ import annotations

from typing import Any

from credit_coach.coaching.planner import annotate_plan_planner_quality
from credit_coach.data.schema import PlanAction, PlanRecord


RULE_QUALITY_GATE_VERSION = "phase_57_v1"
_RULE_WARNING_PENALTY_PER_CODE = 8.0
_RULE_WARNING_PENALTY_CAP = 16.0
_VALID_CONSTRAINT_STATUSES = {"valid", "repaired", "provisional"}
_GENERIC_ACTION_TITLE_SENTINELS = {
    "",
    "action",
    "unknown action",
    "generic action",
}


def _is_non_empty_text(value: Any) -> bool:
    return bool(str(value or "").strip())


def _primary_numeric_target_complete(action: PlanAction) -> bool:
    target = getattr(action, "primary_numeric_target", None)
    if target is None:
        return False
    return (
        _is_non_empty_text(getattr(target, "metric_key", None))
        and _is_non_empty_text(getattr(target, "unit", None))
        and _is_non_empty_text(getattr(target, "direction", None))
    )


def _requires_primary_numeric_target(action: PlanAction) -> bool:
    return bool(getattr(action, "action_key", None))


def _requires_offer_truth(action: PlanAction) -> bool:
    return bool(
        getattr(action, "offer_required_flag", False)
        or getattr(action, "requires_institutional_approval", False)
        or getattr(action, "requires_acceptance", False)
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
    if _requires_offer_truth(action) and getattr(action, "offer_contract", None) is None:
        return True
    if _requires_offer_truth(action) and not _is_non_empty_text(getattr(action, "offer_feasibility", None)):
        return True
    if getattr(action, "recommendation_validity_status", None) is None:
        return True
    return False


def _customer_institution_role_confusion(action: PlanAction) -> bool:
    institution_signal = bool(
        getattr(action, "offer_required_flag", False)
        or getattr(action, "requires_institutional_approval", False)
        or getattr(action, "approval_pending_semantic_only", False)
    )
    action_class = str(getattr(action, "action_class", "") or "").strip().lower()
    return institution_signal and action_class not in {"institutional", "structural"}


def _generic_action_title(action: PlanAction) -> bool:
    title = str(getattr(action, "action_title", "") or "").strip().lower()
    if title in _GENERIC_ACTION_TITLE_SENTINELS:
        return True
    key = str(getattr(action, "action_key", "") or "").strip().lower().replace("_", " ")
    return bool(title and key and title == key)


def annotate_rule_candidate_quality(
    plan: PlanRecord,
    *,
    quality_gate_version: str = RULE_QUALITY_GATE_VERSION,
) -> PlanRecord:
    if str(getattr(plan, "plan_source", "") or "").strip().lower() != "rule":
        return plan

    annotate_plan_planner_quality(plan)
    actionable_actions = [
        action
        for action in list(getattr(plan, "actions", []) or [])
        if str(getattr(action, "action_status", "valid") or "valid").strip().lower() != "invalid"
    ]
    semantic_codes: set[str] = set()
    warning_codes: set[str] = set()
    annotation_complete = True

    if not actionable_actions:
        semantic_codes.add("zero_actionable_step")

    for action in actionable_actions:
        if _missing_required_annotation(action):
            annotation_complete = False
            semantic_codes.add("missing_required_annotation")
            if _requires_primary_numeric_target(action) and not _primary_numeric_target_complete(action):
                semantic_codes.add("missing_primary_numeric_target")
            if _requires_offer_truth(action) and getattr(action, "offer_contract", None) is None:
                semantic_codes.add("missing_offer_contract")
            if _requires_offer_truth(action) and not _is_non_empty_text(getattr(action, "offer_feasibility", None)):
                semantic_codes.add("missing_offer_feasibility")
        if _customer_institution_role_confusion(action):
            semantic_codes.add("customer_institution_role_confusion")
        if not _is_non_empty_text(getattr(action, "action_title", None)) or not _is_non_empty_text(
            getattr(action, "action_family", None)
        ):
            semantic_codes.add("non_renderable_recommendation")
        if _generic_action_title(action):
            warning_codes.add("generic_action_text_fallback")

    recommendation_status = str(getattr(plan, "recommendation_validity_status", "") or "valid").strip().lower()
    constraint_status = str(getattr(plan, "constraint_status", "") or "valid").strip().lower()
    contender_bucket = str(getattr(plan, "contender_bucket", "") or "").strip().upper()

    if contender_bucket == "APPROVAL_SHELL_ONLY":
        warning_codes.add("approval_shell_only")

    if semantic_codes or not annotation_complete:
        semantic_status = "invalid"
    elif warning_codes:
        semantic_status = "warning"
    else:
        semantic_status = "valid"

    contender_eligible = bool(
        annotation_complete
        and semantic_status != "invalid"
        and recommendation_status != "invalid"
        and constraint_status in _VALID_CONSTRAINT_STATUSES
        and contender_bucket == "ACTIONABLE"
    )

    warning_penalty = 0.0
    if warning_codes:
        warning_penalty = min(
            _RULE_WARNING_PENALTY_CAP,
            _RULE_WARNING_PENALTY_PER_CODE * len(warning_codes),
        )

    plan.rule_annotation_complete = bool(annotation_complete)
    plan.rule_semantic_quality_status = semantic_status
    plan.rule_semantic_quality_codes = sorted(semantic_codes | warning_codes)
    plan.rule_contender_eligible = bool(contender_eligible)
    plan.rule_semantic_warning_penalty = float(warning_penalty)
    plan.rule_quality_gate_version = str(quality_gate_version)
    return plan


def split_rule_planner_eligible(plans: list[PlanRecord]) -> tuple[list[PlanRecord], list[PlanRecord]]:
    eligible: list[PlanRecord] = []
    ineligible: list[PlanRecord] = []
    for plan in plans:
        if str(getattr(plan, "plan_source", "") or "").strip().lower() == "rule" and not bool(
            getattr(plan, "rule_contender_eligible", False)
        ):
            ineligible.append(plan)
            continue
        eligible.append(plan)
    return eligible, ineligible
