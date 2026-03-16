from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

from credit_coach.data.schema import PlanAction, PlanRecord

ACTIVE_OFFER_APPROVAL_STATES = {"approved", "not_required"}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return int(default)
        return int(value)
    except Exception:
        return int(default)


def _safe_str(value: Any, default: str = "") -> str:
    raw = str(value or "").strip()
    return raw if raw else str(default)


def _clamp(value: float, *, lo: float = 0.0, hi: float = 1.0) -> float:
    return float(min(max(float(value), lo), hi))


def _offer_group_key(action: PlanAction, index: int) -> str:
    group_id = _safe_str(getattr(action, "action_group_id", ""))
    if group_id:
        return group_id
    action_key = _safe_str(getattr(action, "action_key", ""))
    if action_key:
        return action_key
    return f"offer:{index}:{_safe_str(getattr(action, 'feature_name', ''))}"


def approval_state_for_action(action: PlanAction) -> str:
    state = _safe_str(getattr(action, "institutional_approval_state", ""), "unknown").lower()
    return state if state else "unknown"


def is_offer_action(action: PlanAction) -> bool:
    return bool(_safe_str(getattr(action, "offer_type", "")))


def is_rankable_offer_action(action: PlanAction) -> bool:
    if not is_offer_action(action):
        return False
    if not bool(getattr(action, "offer_terms_complete", False)):
        return False
    return approval_state_for_action(action) in ACTIVE_OFFER_APPROVAL_STATES


def build_offer_contract(
    action_meta: Mapping[str, Any],
    *,
    current_value: float,
    target_value: float,
    action_month: int,
    action_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    offer_type = _safe_str(action_meta.get("offer_type", ""))
    if not offer_type:
        return {
            "offer_type": None,
            "offer_terms": {},
            "offer_terms_complete": False,
            "requires_acceptance": False,
            "institutional_approval_state": _safe_str(action_meta.get("institutional_approval_state", "not_required")),
            "offer_family": None,
            "offer_scoring_profile": None,
            "term_generation_rule": None,
            "offer_policy_arm": None,
        }

    context = dict(action_context or {})
    current_abs = abs(_safe_float(current_value, 0.0))
    target_abs = abs(_safe_float(target_value, 0.0))
    requested_delta = float(target_value - current_value)
    requires_acceptance = bool(action_meta.get("requires_acceptance", False))
    approval_state = _safe_str(action_meta.get("institutional_approval_state", "unknown"), "unknown").lower()

    payment_delta_monthly = 0.0
    discount_amount = 0.0
    discount_pct = 0.0
    term_extension_months = 0
    interest_rate_delta = 0.0
    grace_period_weeks = 0
    offer_terms_complete = False

    if offer_type == "discount_offer":
        discount_amount = max(0.0, current_abs - target_abs)
        discount_pct = float(discount_amount / max(current_abs, 1.0))
        grace_period_weeks = max(0, min(4, _safe_int(action_month, 1)))
        offer_terms_complete = bool(discount_amount > 0.0)
    elif offer_type == "installment_terms":
        delinquency_anchor = max(
            current_abs,
            abs(_safe_float(context.get("delinq_amnt"), 0.0)),
            abs(_safe_float(context.get("installment"), 0.0)),
        )
        payment_delta_monthly = -max(25.0, delinquency_anchor / max(3.0, float(action_month) * 2.0))
        term_extension_months = max(3, int(max(1, action_month) * 2))
        interest_rate_delta = -0.25 if _safe_float(context.get("int_rate"), 0.0) > 0.0 else 0.0
        stress_band = _safe_str(context.get("stress_band", "")).lower()
        high_stress_flag = bool(context.get("high_stress_flag", False))
        grace_period_weeks = 2 if high_stress_flag or stress_band in {"stress", "high_stress"} else 1
        offer_terms_complete = True
    elif offer_type == "credit_limit_adjustment":
        approval_state = "pending"
        offer_terms_complete = False

    offer_terms = {
        "payment_delta_monthly": float(payment_delta_monthly),
        "discount_amount": float(discount_amount),
        "discount_pct": float(discount_pct),
        "term_extension_months": int(term_extension_months),
        "interest_rate_delta": float(interest_rate_delta),
        "grace_period_weeks": int(grace_period_weeks),
        "requires_acceptance": bool(requires_acceptance),
        "requires_institutional_approval": bool(action_meta.get("requires_institutional_approval", False)),
    }
    return {
        "offer_type": offer_type,
        "offer_terms": offer_terms,
        "offer_terms_complete": bool(offer_terms_complete),
        "requires_acceptance": bool(requires_acceptance),
        "institutional_approval_state": approval_state,
        "offer_family": _safe_str(action_meta.get("offer_family", "")) or None,
        "offer_scoring_profile": _safe_str(action_meta.get("offer_scoring_profile", "")) or None,
        "term_generation_rule": _safe_str(action_meta.get("term_generation_rule", "")) or None,
        "offer_policy_arm": _safe_str(action_meta.get("offer_policy_arm", "")) or None,
    }


def _rankable_offer_groups(actions: Sequence[PlanAction]) -> dict[str, list[PlanAction]]:
    groups: dict[str, list[PlanAction]] = defaultdict(list)
    for index, action in enumerate(actions):
        if not is_rankable_offer_action(action):
            continue
        groups[_offer_group_key(action, index)].append(action)
    return groups


def estimate_offer_acceptance_probability(
    action: PlanAction,
    *,
    plan: PlanRecord,
    customer_context: Mapping[str, Any] | None = None,
    segment_context: Mapping[str, Any] | None = None,
) -> float:
    offer_type = _safe_str(getattr(action, "offer_type", ""))
    terms = getattr(action, "offer_terms", {}) if isinstance(getattr(action, "offer_terms", {}), Mapping) else {}
    anchor = {
        "discount_offer": 0.56,
        "installment_terms": 0.64,
        "credit_limit_adjustment": 0.48,
    }.get(offer_type, 0.50)

    payment_delta_monthly = _safe_float(terms.get("payment_delta_monthly"), 0.0)
    discount_pct = _safe_float(terms.get("discount_pct"), 0.0)
    term_extension_months = _safe_int(terms.get("term_extension_months"), 0)
    interest_rate_delta = _safe_float(terms.get("interest_rate_delta"), 0.0)
    grace_period_weeks = _safe_int(terms.get("grace_period_weeks"), 0)
    action_burden = max(0, int(getattr(plan, "executable_action_group_count", 0) or 0))
    trajectory_label = _safe_str(getattr(plan, "trajectory_policy_label", "")).lower()

    probability = float(anchor)
    probability += min(0.18, max(0.0, -payment_delta_monthly) / 600.0)
    probability += min(0.16, max(0.0, discount_pct) * 0.45)
    probability += min(0.08, max(0, term_extension_months) / 24.0)
    probability += min(0.08, max(0, grace_period_weeks) / 8.0)
    probability += min(0.10, max(0.0, -interest_rate_delta) * 0.08)
    probability -= 0.03 * max(0, action_burden - 1)

    risk_band = _safe_str((segment_context or {}).get("risk_band", "")).lower()
    if risk_band == "high":
        probability -= 0.05
    elif risk_band == "mid":
        probability -= 0.02
    elif risk_band == "low":
        probability += 0.01

    income_band = _safe_str((segment_context or {}).get("income_band", (customer_context or {}).get("income_band", ""))).lower()
    if income_band in {"q1", "low", "low_income"}:
        probability += 0.05
    elif income_band in {"q4", "high", "high_income"}:
        probability -= 0.02

    stress_band = _safe_str((segment_context or {}).get("stress_band", "")).lower()
    high_stress_flag = bool((segment_context or {}).get("high_stress_flag", False))
    if high_stress_flag or stress_band in {"stress", "high_stress"}:
        probability += 0.05

    if trajectory_label == "stabilize_first":
        probability += 0.03
    elif trajectory_label == "long_horizon_heavy":
        probability -= 0.03

    return _clamp(probability, lo=0.05, hi=0.95)


def _offer_proxy_deltas(
    action: PlanAction,
    *,
    plan_execution_probability: float,
    offer_acceptance_probability: float,
) -> dict[str, float]:
    terms = getattr(action, "offer_terms", {}) if isinstance(getattr(action, "offer_terms", {}), Mapping) else {}
    combined = float(plan_execution_probability * offer_acceptance_probability)
    payment_relief = max(0.0, -_safe_float(terms.get("payment_delta_monthly"), 0.0))
    discount_pct = max(0.0, _safe_float(terms.get("discount_pct"), 0.0))
    discount_amount = max(0.0, _safe_float(terms.get("discount_amount"), 0.0))
    grace_period_weeks = max(0, _safe_int(terms.get("grace_period_weeks"), 0))
    term_extension_months = max(0, _safe_int(terms.get("term_extension_months"), 0))
    interest_rate_delta = _safe_float(terms.get("interest_rate_delta"), 0.0)

    approval_delta = (0.05 * combined) + min(0.05, payment_relief / 1500.0) + min(0.04, discount_pct * 0.20)
    default_delta = (
        (-0.03 * combined)
        - min(0.02, payment_relief / 2000.0)
        - min(0.015, grace_period_weeks / 16.0)
        - min(0.01, max(0.0, -interest_rate_delta) * 0.05)
        + max(0.0, discount_pct - 0.40) * 0.05
    )
    margin_delta = (
        (45.0 * combined)
        - (0.30 * discount_amount)
        - (6.0 * grace_period_weeks)
        + (1.5 * term_extension_months)
        - (20.0 * max(0.0, -interest_rate_delta))
    )
    return {
        "approval_rate_proxy_delta": float(approval_delta),
        "default_rate_90d_proxy_delta": float(default_delta),
        "avg_margin_90d_proxy_delta": float(margin_delta),
    }


def annotate_offer_optimization(
    plan: PlanRecord,
    *,
    customer_context: Mapping[str, Any] | None = None,
    segment_context: Mapping[str, Any] | None = None,
) -> PlanRecord:
    offer_actions = [action for action in list(plan.actions) if is_offer_action(action)]
    plan.offer_plan = bool(offer_actions)
    if not offer_actions:
        plan.rankable_offer_count = 0
        plan.governance_safe_offer = False
        plan.dominant_offer_type = None
        plan.offer_policy_arm = None
        plan.offer_family = None
        plan.offer_scoring_profile = None
        plan.term_generation_rule = None
        plan.offer_acceptance_probability = None
        plan.combined_plan_realization_probability = None
        plan.expected_recovery_proxy = 0.0
        plan.approval_rate_proxy_delta = 0.0
        plan.default_rate_90d_proxy_delta = 0.0
        plan.avg_margin_90d_proxy_delta = 0.0
        return plan

    rankable_groups = _rankable_offer_groups(offer_actions)
    rankable_offer_count = int(len(rankable_groups))
    plan.rankable_offer_count = rankable_offer_count

    primary_action = None
    if rankable_groups:
        primary_group_actions = next(iter(rankable_groups.values()))
        primary_action = primary_group_actions[0]
    else:
        primary_action = offer_actions[0]

    plan.dominant_offer_type = _safe_str(getattr(primary_action, "offer_type", "")) or None
    plan.offer_policy_arm = _safe_str(getattr(primary_action, "offer_policy_arm", "")) or None
    plan.offer_family = _safe_str(getattr(primary_action, "offer_family", "")) or None
    plan.offer_scoring_profile = _safe_str(getattr(primary_action, "offer_scoring_profile", "")) or None
    plan.term_generation_rule = _safe_str(getattr(primary_action, "term_generation_rule", "")) or None

    if rankable_offer_count <= 0 or primary_action is None or not is_rankable_offer_action(primary_action):
        plan.offer_acceptance_probability = None
        plan.combined_plan_realization_probability = None
        plan.expected_recovery_proxy = 0.0
        plan.approval_rate_proxy_delta = 0.0
        plan.default_rate_90d_proxy_delta = 0.0
        plan.avg_margin_90d_proxy_delta = 0.0
        plan.governance_safe_offer = False
        return plan

    if int(getattr(plan, "executable_action_group_count", 0) or 0) == 0:
        plan.plan_execution_probability = 1.0

    plan_execution_probability = _clamp(_safe_float(getattr(plan, "plan_execution_probability", 0.0), 0.0), lo=0.0, hi=1.0)
    offer_acceptance_probability = estimate_offer_acceptance_probability(
        primary_action,
        plan=plan,
        customer_context=customer_context,
        segment_context=segment_context,
    )
    proxy_deltas = _offer_proxy_deltas(
        primary_action,
        plan_execution_probability=plan_execution_probability,
        offer_acceptance_probability=offer_acceptance_probability,
    )
    combined = _clamp(plan_execution_probability * offer_acceptance_probability, lo=0.0, hi=1.0)
    expected_recovery_proxy = (
        (proxy_deltas["approval_rate_proxy_delta"] * 100.0)
        + ((-proxy_deltas["default_rate_90d_proxy_delta"]) * 120.0)
        + (proxy_deltas["avg_margin_90d_proxy_delta"] / 50.0)
    )

    plan.offer_acceptance_probability = float(offer_acceptance_probability)
    plan.combined_plan_realization_probability = float(combined)
    plan.expected_recovery_proxy = float(expected_recovery_proxy)
    plan.approval_rate_proxy_delta = float(proxy_deltas["approval_rate_proxy_delta"])
    plan.default_rate_90d_proxy_delta = float(proxy_deltas["default_rate_90d_proxy_delta"])
    plan.avg_margin_90d_proxy_delta = float(proxy_deltas["avg_margin_90d_proxy_delta"])
    plan.governance_safe_offer = bool(
        rankable_offer_count > 0
        and str(getattr(plan, "constraint_status", "valid")).strip().lower() in {"valid", "repaired"}
        and str(getattr(plan, "status", "PENDING")).strip().upper() in {"APPROVED", "NEEDS_REVIEW", "PENDING"}
        and str(getattr(plan, "trajectory_status", "on_track")).strip().lower() != "degraded"
    )
    return plan
