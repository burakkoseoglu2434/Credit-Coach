from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from credit_coach.data.schema import PlanAction
from credit_coach.recourse.action_space import get_action_metadata

ConstraintStatus = Literal["valid", "repaired", "provisional", "invalid"]


@dataclass
class ActionConstraintResult:
    actions: list[PlanAction]
    status: ConstraintStatus
    reason: str | None
    trace: list[dict[str, Any]]


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _merge_reason(base: str | None, extra: str) -> str:
    if not base:
        return extra
    if extra in base.split("|"):
        return base
    return f"{base}|{extra}"


def _merge_flags(flags: list[str], extra: str) -> list[str]:
    out = list(flags)
    if extra not in out:
        out.append(extra)
    return out


def _group_id_for_action(action: PlanAction, index: int) -> str:
    raw = str(getattr(action, "action_group_id", "") or "").strip()
    if raw:
        return raw
    key = str(getattr(action, "action_key", "") or "").strip()
    if key:
        return key
    return f"{getattr(action, 'feature_name', 'action')}:{index}"


def _action_metadata_for_instance(action: PlanAction) -> dict[str, Any]:
    action_month = max(1, int(getattr(action, "time_months", 1) or 1))
    return get_action_metadata(
        str(getattr(action, "feature_name", "")),
        action_month=action_month,
        action_group_id=str(getattr(action, "action_group_id", "") or "") or None,
    )


def _context_tags(action_context: dict[str, Any] | None) -> set[str]:
    action_context = action_context or {}
    tags: set[str] = set()
    annual_inc = _safe_float(action_context.get("annual_inc"))
    dti = _safe_float(action_context.get("dti"))
    verification_status = str(action_context.get("verification_status", "") or "").strip().lower()

    if annual_inc is not None and annual_inc >= 40_000.0 and (dti is None or dti <= 40.0):
        tags.add("stable_income")
    if verification_status not in {"", "0", "false", "none", "nan", "not_verified"}:
        tags.add("income_verified")
    return tags


def _group_drop_priority(group_actions: list[PlanAction]) -> tuple[int, int, int, float, str]:
    requires_approval = int(
        any(bool(getattr(action, "requires_institutional_approval", False)) for action in group_actions)
    )
    semantic_only = int(
        any(bool(getattr(action, "approval_pending_semantic_only", False)) for action in group_actions)
    )
    earliest_month = max(1, min(int(getattr(action, "time_months", 1) or 1) for action in group_actions))
    total_cost = sum(float(getattr(action, "estimated_cost_usd", 0.0) or 0.0) for action in group_actions)
    action_key = str(getattr(group_actions[0], "action_key", "") or getattr(group_actions[0], "feature_name", ""))
    return (semantic_only, requires_approval, earliest_month, total_cost, action_key)


def _group_conflict_keys(group_actions: list[PlanAction]) -> set[str]:
    keys: set[str] = set()
    for action in group_actions:
        action_key = str(getattr(action, "action_key", "") or "").strip()
        if action_key:
            keys.add(action_key)
        keys.update(str(tag).strip() for tag in getattr(action, "conflict_tags", []) if str(tag).strip())
    return keys


def _group_action_keys(group_actions: list[PlanAction]) -> set[str]:
    keys: set[str] = set()
    for action in group_actions:
        action_key = str(getattr(action, "action_key", "") or "").strip()
        if action_key:
            keys.add(action_key)
    return keys


def _append_trace(
    trace: list[dict[str, Any]],
    *,
    event_type: str,
    action: PlanAction,
    action_group_id: str,
    reason_code: str,
    related_action_key: str | None = None,
    related_group_id: str | None = None,
) -> None:
    trace.append(
        {
            "event_type": event_type,
            "action_key": str(getattr(action, "action_key", "") or ""),
            "action_class": str(getattr(action, "action_class", "") or ""),
            "action_group_id": action_group_id,
            "feature_name": str(getattr(action, "feature_name", "") or ""),
            "time_months": int(getattr(action, "time_months", 1) or 1),
            "reason_code": reason_code,
            "related_action_key": str(related_action_key or ""),
            "related_group_id": str(related_group_id or ""),
            "original_action_status": str(getattr(action, "action_status", "") or ""),
        }
    )


def enforce_action_constraints(
    actions: list[PlanAction],
    *,
    action_context: dict[str, Any] | None = None,
) -> ActionConstraintResult:
    if not actions:
        return ActionConstraintResult(actions=[], status="valid", reason=None, trace=[])

    trace: list[dict[str, Any]] = []
    grouped: dict[str, list[PlanAction]] = {}
    group_order: list[str] = []
    for idx, action in enumerate(actions):
        group_id = _group_id_for_action(action, idx)
        if group_id not in grouped:
            grouped[group_id] = []
            group_order.append(group_id)
        grouped[group_id].append(action)

    context_tags = _context_tags(action_context)
    provided_tags: set[str] = set(context_tags)
    for group_id, group_actions in grouped.items():
        group_tags: set[str] = set()
        for action in group_actions:
            meta = _action_metadata_for_instance(action)
            group_tags.update(str(tag).strip() for tag in meta.get("provides_tags", []) if str(tag).strip())
        if group_tags:
            provided_tags.update(group_tags)

    dropped_groups: dict[str, str] = {}
    invalid_combination_seen = False

    for group_id in group_order:
        group_actions = grouped[group_id]
        required_tags = {
            str(tag).strip()
            for action in group_actions
            for tag in getattr(action, "prerequisite_tags", [])
            if str(tag).strip()
        }
        missing = sorted(tag for tag in required_tags if tag not in provided_tags)
        if not missing:
            continue
        invalid_combination_seen = True
        reason_code = f"missing_prerequisite:{missing[0]}"
        dropped_groups[group_id] = reason_code
        for action in group_actions:
            _append_trace(
                trace,
                event_type="repair_dropped",
                action=action,
                action_group_id=group_id,
                reason_code=reason_code,
            )

    kept_group_ids = [group_id for group_id in group_order if group_id not in dropped_groups]
    changed = True
    while changed:
        changed = False
        for left_idx, left_group_id in enumerate(kept_group_ids):
            if left_group_id in dropped_groups:
                continue
            left_actions = grouped[left_group_id]
            left_conflicts = _group_conflict_keys(left_actions)
            left_keys = _group_action_keys(left_actions)
            for right_group_id in kept_group_ids[left_idx + 1 :]:
                if right_group_id in dropped_groups:
                    continue
                right_actions = grouped[right_group_id]
                right_conflicts = _group_conflict_keys(right_actions)
                right_keys = _group_action_keys(right_actions)
                if not ((left_conflicts & right_keys) or (right_conflicts & left_keys)):
                    continue
                invalid_combination_seen = True
                drop_group_id = max(
                    (left_group_id, right_group_id),
                    key=lambda group_id: _group_drop_priority(grouped[group_id]),
                )
                keep_group_id = right_group_id if drop_group_id == left_group_id else left_group_id
                related_key = str(getattr(grouped[keep_group_id][0], "action_key", "") or "")
                reason_code = f"conflict_with:{related_key or keep_group_id}"
                dropped_groups[drop_group_id] = reason_code
                for action in grouped[drop_group_id]:
                    _append_trace(
                        trace,
                        event_type="repair_dropped",
                        action=action,
                        action_group_id=drop_group_id,
                        reason_code=reason_code,
                        related_action_key=related_key,
                        related_group_id=keep_group_id,
                    )
                changed = True
                break
            if changed:
                kept_group_ids = [group_id for group_id in group_order if group_id not in dropped_groups]
                break

    repaired_actions: list[PlanAction] = []
    provisional_trace_count = 0
    for idx, action in enumerate(actions):
        group_id = _group_id_for_action(action, idx)
        if group_id in dropped_groups:
            continue
        updated = action
        needs_provisional = bool(getattr(action, "requires_institutional_approval", False)) or bool(
            getattr(action, "approval_pending_semantic_only", False)
        )
        if needs_provisional:
            reason_code = (
                "approval_pending_semantic_only"
                if bool(getattr(action, "approval_pending_semantic_only", False))
                else "requires_institutional_approval"
            )
            updated = updated.model_copy(
                update={
                    "action_status": "provisional",
                    "action_status_reason": _merge_reason(
                        getattr(updated, "action_status_reason", None),
                        reason_code,
                    ),
                    "diagnostic_flags": _merge_flags(list(getattr(updated, "diagnostic_flags", [])), reason_code),
                }
            )
            provisional_trace_count += 1
            _append_trace(
                trace,
                event_type="approval_pending",
                action=updated,
                action_group_id=group_id,
                reason_code=reason_code,
            )
        repaired_actions.append(updated)

    if not repaired_actions:
        reasons = sorted({reason for reason in dropped_groups.values() if reason})
        return ActionConstraintResult(
            actions=[],
            status="invalid",
            reason="|".join(reasons) if reasons else "invalid_action_combination",
            trace=trace,
        )

    if provisional_trace_count > 0:
        reasons = sorted({entry["reason_code"] for entry in trace if entry.get("event_type") == "approval_pending"})
        status: ConstraintStatus = "provisional"
        reason = "|".join(reasons) if reasons else "approval_pending"
    elif dropped_groups:
        reasons = sorted({reason for reason in dropped_groups.values() if reason})
        status = "repaired"
        reason = "|".join(reasons) if reasons else "repair_applied"
    else:
        status = "valid"
        reason = None

    if invalid_combination_seen and status == "valid":
        status = "repaired"
        reason = "repair_applied"

    return ActionConstraintResult(
        actions=repaired_actions,
        status=status,
        reason=reason,
        trace=trace,
    )
