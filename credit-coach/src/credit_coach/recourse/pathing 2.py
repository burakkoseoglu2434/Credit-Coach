from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

from credit_coach.coaching.planner import (
    annotate_plan_planner_quality,
    canonical_plan_source,
    choose_best_plan,
)
from credit_coach.data.schema import PathType, PlanRecord, RecoursePathRecord
from credit_coach.recourse.action_space import get_action_template

_VALID_OFFER_MATURITY = {"none", "inactive", "provisional", "active_rankable"}
_LEGACY_OWNER_BY_CLASS = {
    "behavioral": "customer",
    "structural": "hybrid",
    "institutional": "institution",
}
_PATH_TYPE_ORDER = {
    "customer_only": 0,
    "institution_assisted": 1,
    "hybrid": 2,
}


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _visible_actions(plan: PlanRecord) -> list[Any]:
    visible: list[Any] = []
    for action in list(getattr(plan, "actions", []) or []):
        if _safe_text(getattr(action, "action_status", "")).lower() == "invalid":
            continue
        if any(
            _safe_text(getattr(action, field, ""))
            for field in ("action_key", "action_title", "action_family", "action_class")
        ):
            visible.append(action)
    return visible


def _action_owner(action: Any) -> str:
    action_key = _safe_text(getattr(action, "action_key", ""))
    if action_key:
        try:
            return _safe_text(get_action_template(action_key).action_owner)
        except Exception:
            pass
    legacy_class = _safe_text(getattr(action, "action_class", "")).lower()
    if legacy_class in _LEGACY_OWNER_BY_CLASS:
        return _LEGACY_OWNER_BY_CLASS[legacy_class]
    if bool(getattr(action, "requires_institutional_approval", False)):
        return "institution"
    return ""


def _action_category(action: Any) -> str:
    action_key = _safe_text(getattr(action, "action_key", ""))
    if action_key:
        try:
            return _safe_text(get_action_template(action_key).action_category)
        except Exception:
            pass
    return ""


def _primary_metric_key(action: Any) -> str:
    target = getattr(action, "primary_numeric_target", None)
    metric_key = _safe_text(getattr(target, "metric_key", ""))
    if metric_key:
        return metric_key
    return _safe_text(getattr(action, "feature_name", ""))


def _normalized_offer_maturity(plan: PlanRecord) -> str:
    explicit = _safe_text(getattr(plan, "offer_maturity", "")).lower()
    if explicit in _VALID_OFFER_MATURITY:
        return explicit
    if not bool(getattr(plan, "offer_plan", False)):
        return "none"
    if int(getattr(plan, "approval_pending_action_count", 0) or 0) > 0:
        return "provisional"
    if int(getattr(plan, "rankable_offer_count", 0) or 0) > 0:
        return "active_rankable"
    return "inactive"


def derive_path_type(plan: PlanRecord) -> PathType:
    annotate_plan_planner_quality(plan)
    actions = _visible_actions(plan)
    owners = {_action_owner(action) for action in actions if _action_owner(action)}
    if "hybrid" in owners:
        return "hybrid"
    if "customer" in owners and "institution" in owners:
        return "hybrid"
    if "institution" in owners:
        return "institution_assisted"
    return "customer_only"


def build_path_signature(plan: PlanRecord, *, path_type: PathType | None = None) -> str:
    annotate_plan_planner_quality(plan)
    resolved_path_type = path_type or derive_path_type(plan)
    actions = _visible_actions(plan)
    action_keys = sorted({_safe_text(getattr(action, "action_key", "")) for action in actions if _safe_text(getattr(action, "action_key", ""))})
    action_owners = sorted({_action_owner(action) for action in actions if _action_owner(action)})
    metric_keys = sorted({_primary_metric_key(action) for action in actions if _primary_metric_key(action)})
    offer_families = sorted({_safe_text(getattr(action, "offer_family", "")) for action in actions if _safe_text(getattr(action, "offer_family", ""))})
    offer_types = sorted({_safe_text(getattr(action, "offer_type", "")) for action in actions if _safe_text(getattr(action, "offer_type", ""))})
    requires_approval = sorted(
        {
            int(bool(getattr(action, "requires_institutional_approval", False)))
            for action in actions
        }
    )
    payload = {
        "path_type": str(resolved_path_type),
        "action_keys": action_keys,
        "action_owners": action_owners,
        "metric_keys": metric_keys,
        "offer_plan": int(bool(getattr(plan, "offer_plan", False))),
        "offer_maturity": _normalized_offer_maturity(plan),
        "requires_institutional_approval": requires_approval,
        "offer_families": offer_families,
        "offer_types": offer_types,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _path_id(customer_id: str, signature: str) -> str:
    digest = hashlib.sha1(f"{customer_id}|{signature}".encode("utf-8")).hexdigest()[:12]
    return f"{customer_id}_path_{digest}"


def _plan_rankable(plan: PlanRecord) -> bool:
    annotate_plan_planner_quality(plan)
    return _safe_text(getattr(plan, "contender_bucket", "")).upper() == "ACTIONABLE"


def _choose_representative(plans: list[PlanRecord], **ranking_kwargs: Any) -> PlanRecord | None:
    if not plans:
        return None
    result = choose_best_plan(plans, **ranking_kwargs)
    return result.best_plan


def _rank_representatives(representatives: list[PlanRecord], **ranking_kwargs: Any) -> list[PlanRecord]:
    remaining = list(representatives)
    ranked: list[PlanRecord] = []
    while remaining:
        best = _choose_representative(remaining, **ranking_kwargs)
        if best is None:
            break
        ranked.append(best)
        remaining = [plan for plan in remaining if plan.plan_id != best.plan_id]
    ranked.extend(remaining)
    return ranked


def _path_action_sets(paths: list[RecoursePathRecord], *, rankable_only: bool = True) -> list[set[str]]:
    selected = [path for path in paths if (path.rankable_flag or not rankable_only)]
    return [set(path.action_keys) for path in selected if path.action_keys]


def path_action_diversity_index(paths: list[RecoursePathRecord], *, rankable_only: bool = True) -> float:
    action_sets = _path_action_sets(paths, rankable_only=rankable_only)
    if len(action_sets) <= 1:
        return 0.0
    distances: list[float] = []
    for idx, left in enumerate(action_sets):
        for right in action_sets[idx + 1:]:
            union = len(left | right)
            if union <= 0:
                distances.append(0.0)
                continue
            distances.append(float(1.0 - (len(left & right) / union)))
    if not distances:
        return 0.0
    return float(sum(distances) / len(distances))


def summarize_path_metrics(paths: list[RecoursePathRecord]) -> dict[str, Any]:
    rankable = [path for path in paths if path.rankable_flag]
    rankable_count = len(rankable)
    type_counts = Counter(str(path.path_type) for path in rankable)
    non_utilization_count = int(
        sum(
            1
            for path in rankable
            if any(category and category != "utilization_capacity" for category in path.action_categories)
        )
    )
    institution_count = int(
        sum(1 for path in rankable if str(path.path_type) in {"institution_assisted", "hybrid"})
    )
    selected = next((path for path in paths if path.selected_path_flag), None)
    return {
        "path_count": int(len(paths)),
        "rankable_path_count": int(rankable_count),
        "multi_path_flag": int(rankable_count > 1),
        "customer_only_path_count": int(type_counts.get("customer_only", 0)),
        "institution_assisted_path_count": int(type_counts.get("institution_assisted", 0)),
        "hybrid_path_count": int(type_counts.get("hybrid", 0)),
        "action_diversity_index": float(path_action_diversity_index(paths, rankable_only=True)),
        "non_utilization_action_rate": float(non_utilization_count / max(1, rankable_count)),
        "institution_action_rate": float(institution_count / max(1, rankable_count)),
        "selected_path_id": _safe_text(getattr(selected, "path_id", "")),
        "selected_path_type": _safe_text(getattr(selected, "path_type", "")),
        "selected_path_rank": int(getattr(selected, "path_rank", 0) or 0),
    }


def build_recourse_path_records(
    plans: list[PlanRecord],
    *,
    selected_plan_id: str | None = None,
    **ranking_kwargs: Any,
) -> list[RecoursePathRecord]:
    grouped: dict[str, list[PlanRecord]] = {}
    ordered_group_ids: list[str] = []
    for plan in plans:
        annotate_plan_planner_quality(plan)
        plan.path_id = None
        plan.path_type = None
        plan.path_signature = None
        plan.path_rankable_flag = False
        plan.path_representative_flag = False
        plan.path_rank = None
        if _safe_text(getattr(plan, "contender_bucket", "")).upper() == "EMPTY":
            continue
        path_type = derive_path_type(plan)
        signature = build_path_signature(plan, path_type=path_type)
        path_id = _path_id(_safe_text(getattr(plan, "customer_id", "")), signature)
        plan.path_id = path_id
        plan.path_type = path_type
        plan.path_signature = signature
        plan.path_rankable_flag = _plan_rankable(plan)
        if path_id not in grouped:
            grouped[path_id] = []
            ordered_group_ids.append(path_id)
        grouped[path_id].append(plan)

    path_records: list[RecoursePathRecord] = []
    representatives: list[PlanRecord] = []
    records_by_id: dict[str, RecoursePathRecord] = {}
    for path_id in ordered_group_ids:
        members = grouped[path_id]
        representative = _choose_representative([plan for plan in members if _plan_rankable(plan)], **ranking_kwargs)
        if representative is not None:
            representative.path_representative_flag = True
            representatives.append(representative)
        visible_actions = [action for member in members for action in _visible_actions(member)]
        action_keys = sorted({_safe_text(getattr(action, "action_key", "")) for action in visible_actions if _safe_text(getattr(action, "action_key", ""))})
        action_owners = sorted({_action_owner(action) for action in visible_actions if _action_owner(action)})
        action_categories = sorted({_action_category(action) for action in visible_actions if _action_category(action)})
        primary_metric_keys = sorted({_primary_metric_key(action) for action in visible_actions if _primary_metric_key(action)})
        source_counts = Counter(canonical_plan_source(plan) for plan in members)
        path_record = RecoursePathRecord(
            path_id=path_id,
            customer_id=_safe_text(getattr(members[0], "customer_id", "")),
            path_type=members[0].path_type or derive_path_type(members[0]),
            path_signature=members[0].path_signature or build_path_signature(members[0]),
            rankable_flag=bool(representative is not None),
            representative_plan_id=_safe_text(getattr(representative, "plan_id", "")) or None,
            representative_plan_source=canonical_plan_source(representative) if representative is not None else None,
            representative_contender_bucket=_safe_text(getattr(representative, "contender_bucket", "")) or None,
            member_plan_ids=[_safe_text(getattr(plan, "plan_id", "")) for plan in members if _safe_text(getattr(plan, "plan_id", ""))],
            member_plan_count=int(len(members)),
            member_source_counts={str(key): int(value) for key, value in sorted(source_counts.items())},
            action_keys=action_keys,
            action_owners=action_owners,
            action_categories=action_categories,
            primary_metric_keys=primary_metric_keys,
            offer_plan=bool(any(bool(getattr(plan, "offer_plan", False)) for plan in members)),
            offer_maturity=(
                _normalized_offer_maturity(representative)
                if representative is not None
                else _normalized_offer_maturity(members[0])
            ),
            selected_path_flag=False,
        )
        path_records.append(path_record)
        records_by_id[path_id] = path_record

    for rank, representative in enumerate(_rank_representatives(representatives, **ranking_kwargs), start=1):
        path_id = _safe_text(getattr(representative, "path_id", ""))
        if not path_id:
            continue
        record = records_by_id.get(path_id)
        if record is None:
            continue
        record.path_rank = rank
        for member in grouped.get(path_id, []):
            member.path_rank = rank

    selected_path_id = ""
    if _safe_text(selected_plan_id):
        for plan in plans:
            if _safe_text(getattr(plan, "plan_id", "")) == _safe_text(selected_plan_id):
                selected_path_id = _safe_text(getattr(plan, "path_id", ""))
                break
    for record in path_records:
        record.selected_path_flag = bool(selected_path_id) and record.path_id == selected_path_id

    return sorted(
        path_records,
        key=lambda record: (
            0 if record.path_rank is not None else 1,
            int(record.path_rank or 10**9),
            _PATH_TYPE_ORDER.get(str(record.path_type), 99),
            record.path_id,
        ),
    )
