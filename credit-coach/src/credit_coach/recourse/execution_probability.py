from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Mapping, Sequence

from credit_coach.data.schema import PlanAction, PlanRecord
from credit_coach.recourse.offer_optimization import approval_state_for_action, is_offer_action, is_rankable_offer_action


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


def _clamp(value: float, *, lo: float = 0.0, hi: float = 1.0) -> float:
    return float(min(max(value, lo), hi))


def _bounded_linear(value: float, *, lower: float, upper: float) -> float:
    if upper <= lower:
        return 0.0
    return _clamp((value - lower) / (upper - lower), lo=0.0, hi=1.0)


def _customer_context_adjustment(customer_context: Mapping[str, Any] | None) -> float:
    if not isinstance(customer_context, Mapping):
        return 0.0
    income = _safe_float(customer_context.get("annual_inc"), 0.0)
    dti = _safe_float(customer_context.get("dti"), 0.0)
    utilization = _safe_float(customer_context.get("revol_util"), 0.0)
    verification = _safe_float(customer_context.get("verification_status"), 0.0)

    income_bonus = (_bounded_linear(income, lower=25_000.0, upper=125_000.0) - 0.5) * 0.10
    dti_penalty = (1.0 - _bounded_linear(dti, lower=5.0, upper=45.0) - 0.5) * 0.11
    util_penalty = (1.0 - _bounded_linear(utilization, lower=5.0, upper=90.0) - 0.5) * 0.08
    verification_bonus = 0.04 if verification > 0 else 0.0
    adjustment = float(income_bonus + dti_penalty + util_penalty + verification_bonus)
    return float(_clamp(adjustment, lo=-0.12, hi=0.05))


def _action_class_anchor(action: PlanAction) -> float:
    action_class = str(getattr(action, "action_class", "") or "").strip().lower()
    if action_class == "behavioral":
        return 0.68
    if action_class == "structural":
        return 0.52
    if action_class == "institutional":
        return 0.36
    return 0.48


def _burden_and_horizon_pressure(action: PlanAction, *, plan_action_count: int) -> tuple[float, float, float]:
    time_months = max(1, _safe_int(getattr(action, "time_months", 1), 1))
    cost = max(0.0, _safe_float(getattr(action, "estimated_cost_usd", 0.0), 0.0))
    action_class = str(getattr(action, "action_class", "") or "").strip().lower()

    horizon_pressure = _bounded_linear(float(time_months), lower=1.0, upper=6.0)
    burden_terms = [
        _bounded_linear(cost, lower=0.0, upper=250.0),
        _bounded_linear(float(max(0, int(plan_action_count) - 1)), lower=0.0, upper=4.0),
    ]
    if action_class == "structural":
        burden_terms.append(0.55)
    elif action_class == "institutional":
        burden_terms.append(0.75)
    else:
        burden_terms.append(0.35)
    burden_pressure = float(sum(burden_terms) / max(1, len(burden_terms)))
    interaction_penalty = float(horizon_pressure * burden_pressure)
    return float(horizon_pressure), float(burden_pressure), float(interaction_penalty)


def _semantic_ambiguity_penalty(action: PlanAction) -> float:
    penalty = 0.0
    if not str(getattr(action, "action_key", "") or "").strip():
        penalty += 0.04
    if not str(getattr(action, "action_title", "") or "").strip():
        penalty += 0.03
    if not str(getattr(action, "action_class", "") or "").strip():
        penalty += 0.04
    if not str(getattr(action, "feature_name", "") or "").strip():
        penalty += 0.03
    return float(penalty)


def _approval_probability(
    action: PlanAction,
    *,
    plan_action_count: int,
    customer_context: Mapping[str, Any] | None = None,
    segment_context: Mapping[str, Any] | None = None,
) -> float:
    probability = _action_class_anchor(action) - 0.12
    horizon_pressure, burden_pressure, interaction_penalty = _burden_and_horizon_pressure(
        action,
        plan_action_count=plan_action_count,
    )
    probability -= 0.03 * horizon_pressure
    probability -= 0.05 * burden_pressure
    probability -= 0.10 * interaction_penalty
    probability -= 0.015 * max(0, int(plan_action_count) - 1)
    probability -= _semantic_ambiguity_penalty(action)
    probability += min(0.02, max(0.0, _customer_context_adjustment(customer_context)))

    approval_state = approval_state_for_action(action)
    if approval_state == "unknown":
        probability = min(probability, 0.28)
    elif approval_state == "pending":
        probability -= 0.06

    if isinstance(segment_context, Mapping) and str(segment_context.get("risk_band", "")).strip().lower() == "high":
        probability -= 0.03

    return float(_clamp(probability, lo=0.03, hi=0.80))


def estimate_action_execution_probability(
    action: PlanAction,
    *,
    plan_action_count: int,
    customer_context: Mapping[str, Any] | None = None,
    segment_context: Mapping[str, Any] | None = None,
) -> tuple[float | None, float | None]:
    if is_offer_action(action):
        if is_rankable_offer_action(action):
            return None, None
        approval_prob = _approval_probability(
            action,
            plan_action_count=plan_action_count,
            customer_context=customer_context,
            segment_context=segment_context,
        )
        return None, float(approval_prob)

    if bool(getattr(action, "approval_pending_semantic_only", False)) or bool(
        getattr(action, "requires_institutional_approval", False)
    ):
        approval_prob = _approval_probability(
            action,
            plan_action_count=plan_action_count,
            customer_context=customer_context,
            segment_context=segment_context,
        )
        return None, float(approval_prob)

    probability = _action_class_anchor(action)
    horizon_pressure, burden_pressure, interaction_penalty = _burden_and_horizon_pressure(
        action,
        plan_action_count=plan_action_count,
    )
    probability -= 0.045 * horizon_pressure
    probability -= 0.09 * burden_pressure
    probability -= 0.23 * interaction_penalty
    probability -= 0.02 * max(0, int(plan_action_count) - 1)
    probability += _customer_context_adjustment(customer_context)
    probability -= _semantic_ambiguity_penalty(action)

    if str(getattr(action, "action_status", "valid") or "valid").strip().lower() == "clipped":
        probability -= 0.08
    if str(getattr(action, "action_status_reason", "") or "").strip():
        probability -= 0.01

    diagnostic_flags = {str(flag) for flag in getattr(action, "diagnostic_flags", [])}
    if "requires_institutional_approval" in diagnostic_flags:
        probability -= 0.05
    if any(flag.startswith("missing_prerequisite:") for flag in diagnostic_flags):
        probability -= 0.08
    if any(flag.startswith("conflict_with:") for flag in diagnostic_flags):
        probability -= 0.05

    if isinstance(segment_context, Mapping) and str(segment_context.get("risk_band", "")).strip().lower() == "high":
        probability -= 0.04

    return float(_clamp(probability, lo=0.05, hi=0.95)), None


def _group_key(action: PlanAction, index: int) -> str:
    action_group_id = str(getattr(action, "action_group_id", "") or "").strip()
    if action_group_id:
        return action_group_id
    return f"single:{index}:{getattr(action, 'feature_name', '')}"


def estimate_plan_execution_probability(
    actions: Sequence[PlanAction],
    *,
    customer_context: Mapping[str, Any] | None = None,
    segment_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not actions:
        return {
            "plan_execution_probability": 0.0,
            "mean_action_execution_probability": 0.0,
            "nominal_action_probability_mean": 0.0,
            "executable_action_count": 0,
            "executable_action_group_count": 0,
            "approval_pending_action_count": 0,
        }

    group_members: dict[str, list[float]] = defaultdict(list)
    executable_action_probabilities: list[float] = []
    approval_pending_probabilities: list[float] = []
    approval_pending_count = 0
    rankable_offer_count = 0
    offer_action_count = 0

    for index, action in enumerate(actions):
        if is_offer_action(action):
            offer_action_count += 1
            if is_rankable_offer_action(action):
                rankable_offer_count += 1
        action_prob, approval_prob = estimate_action_execution_probability(
            action,
            plan_action_count=len(actions),
            customer_context=customer_context,
            segment_context=segment_context,
        )
        action.action_execution_probability = action_prob
        action.approval_dependent_probability = approval_prob
        if action_prob is not None:
            executable_action_probabilities.append(float(action_prob))
            group_members[_group_key(action, index)].append(float(action_prob))
        elif approval_prob is not None:
            approval_pending_count += 1
            approval_pending_probabilities.append(float(approval_prob))

    if not group_members:
        return {
            "plan_execution_probability": 1.0 if rankable_offer_count > 0 else 0.0,
            "approval_dependent_plan_probability": (
                float(_clamp((math.prod(approval_pending_probabilities) ** (1.0 / max(1, len(approval_pending_probabilities)))) * max(0.30, 1.0 - (0.10 * max(0, len(approval_pending_probabilities) - 1))), lo=0.02, hi=0.80))
                if approval_pending_probabilities
                else None
            ),
            "mean_action_execution_probability": 0.0,
            "mean_approval_dependent_probability": (
                float(sum(approval_pending_probabilities) / max(1, len(approval_pending_probabilities)))
                if approval_pending_probabilities
                else None
            ),
            "nominal_action_probability_mean": 0.0,
            "executable_action_count": 0,
            "executable_action_group_count": 0,
            "approval_pending_action_count": int(approval_pending_count),
            "rankable_offer_count": int(rankable_offer_count),
            "offer_action_count": int(offer_action_count),
        }

    group_probabilities: dict[str, float] = {}
    for key, probabilities in group_members.items():
        if not probabilities:
            continue
        probability_min = min(probabilities)
        probability_mean = float(sum(probabilities) / max(1, len(probabilities)))
        hybrid_probability = (0.65 * probability_min) + (0.35 * probability_mean)
        group_penalty = max(0.68, 1.0 - (0.06 * max(0, len(probabilities) - 1)))
        if (probability_mean - probability_min) > 0.12:
            group_penalty -= 0.04
        floor_above_min = probability_min + (0.10 * max(0.0, probability_mean - probability_min))
        group_probability = max(floor_above_min, hybrid_probability * group_penalty)
        group_probabilities[key] = float(_clamp(group_probability, lo=0.05, hi=0.95))

    for index, action in enumerate(actions):
        key = _group_key(action, index)
        action.action_group_execution_probability = group_probabilities.get(key)

    group_values = list(group_probabilities.values())
    geometric_mean = math.prod(group_values) ** (1.0 / max(1, len(group_values)))
    blended_group_truth = (0.70 * geometric_mean) + (0.30 * min(group_values))
    load_penalty = max(0.30, 1.0 - (0.09 * max(0, len(group_values) - 1)))
    plan_probability = float(_clamp(blended_group_truth * load_penalty, lo=0.02, hi=0.92))
    approval_plan_probability = None
    if approval_pending_probabilities:
        approval_geometric_mean = math.prod(approval_pending_probabilities) ** (
            1.0 / max(1, len(approval_pending_probabilities))
        )
        approval_load_penalty = max(0.30, 1.0 - (0.10 * max(0, len(approval_pending_probabilities) - 1)))
        approval_plan_probability = float(
            _clamp(approval_geometric_mean * approval_load_penalty, lo=0.02, hi=0.80)
        )

    return {
        "plan_execution_probability": plan_probability,
        "approval_dependent_plan_probability": approval_plan_probability,
        "mean_action_execution_probability": float(sum(executable_action_probabilities) / max(1, len(executable_action_probabilities))),
        "mean_approval_dependent_probability": (
            float(sum(approval_pending_probabilities) / max(1, len(approval_pending_probabilities)))
            if approval_pending_probabilities
            else None
        ),
        "nominal_action_probability_mean": float(sum(group_values) / max(1, len(group_values))),
        "executable_action_count": int(len(executable_action_probabilities)),
        "executable_action_group_count": int(len(group_values)),
        "approval_pending_action_count": int(approval_pending_count),
        "rankable_offer_count": int(rankable_offer_count),
        "offer_action_count": int(offer_action_count),
    }


def annotate_plan_execution_probability(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    customer_context: Mapping[str, Any] | None = None,
    segment_context: Mapping[str, Any] | None = None,
) -> PlanRecord:
    probability_bundle = estimate_plan_execution_probability(
        list(plan.actions),
        customer_context=customer_context,
        segment_context=segment_context,
    )
    plan.plan_execution_probability = float(probability_bundle.get("plan_execution_probability", 0.0))
    plan.approval_dependent_plan_probability = probability_bundle.get("approval_dependent_plan_probability", None)
    plan.mean_action_execution_probability = float(probability_bundle.get("mean_action_execution_probability", 0.0))
    plan.mean_approval_dependent_probability = probability_bundle.get("mean_approval_dependent_probability", None)
    plan.executable_action_count = int(probability_bundle.get("executable_action_count", 0))
    plan.executable_action_group_count = int(probability_bundle.get("executable_action_group_count", 0))
    plan.approval_pending_action_count = int(probability_bundle.get("approval_pending_action_count", 0))
    plan.rankable_offer_count = int(probability_bundle.get("rankable_offer_count", 0))
    plan.offer_plan = bool(int(probability_bundle.get("offer_action_count", 0)) > 0)

    predicted_pd = _safe_float(getattr(plan, "predicted_pd", None), 0.0)
    nominal_pd_improvement = max(0.0, _safe_float(base_pd, predicted_pd) - predicted_pd)
    plan.nominal_pd_improvement = float(nominal_pd_improvement)
    plan.expected_pd_improvement = float(nominal_pd_improvement * float(plan.plan_execution_probability or 0.0))
    return plan


def classify_execution_scenario(execution_rate: float) -> str:
    rate = _clamp(_safe_float(execution_rate, 0.0), lo=0.0, hi=1.0)
    if rate >= 0.999:
        return "full_execution"
    if rate <= 0.34:
        return "failed_execution"
    return "mixed_execution"
