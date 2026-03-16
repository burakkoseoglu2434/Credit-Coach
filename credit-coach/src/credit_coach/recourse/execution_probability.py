from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Mapping, Sequence

from credit_coach.data.schema import PlanAction, PlanRecord


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

    income_bonus = (_bounded_linear(income, lower=25_000.0, upper=125_000.0) - 0.5) * 0.12
    dti_penalty = (1.0 - _bounded_linear(dti, lower=5.0, upper=45.0) - 0.5) * 0.10
    util_penalty = (1.0 - _bounded_linear(utilization, lower=5.0, upper=90.0) - 0.5) * 0.06
    verification_bonus = 0.04 if verification > 0 else 0.0
    return float(income_bonus + dti_penalty + util_penalty + verification_bonus)


def _action_class_anchor(action: PlanAction) -> float:
    action_class = str(getattr(action, "action_class", "") or "").strip().lower()
    if action_class == "behavioral":
        return 0.72
    if action_class == "structural":
        return 0.58
    if action_class == "institutional":
        return 0.42
    return 0.55


def estimate_action_execution_probability(
    action: PlanAction,
    *,
    plan_action_count: int,
    customer_context: Mapping[str, Any] | None = None,
    segment_context: Mapping[str, Any] | None = None,
) -> tuple[float | None, float | None]:
    if bool(getattr(action, "approval_pending_semantic_only", False)) or bool(
        getattr(action, "requires_institutional_approval", False)
    ):
        approval_prob = _clamp(
            _action_class_anchor(action)
            - 0.10
            - (0.02 * max(0, _safe_int(getattr(action, "time_months", 1), 1) - 1))
            - (0.015 * max(0, int(plan_action_count) - 1)),
            lo=0.05,
            hi=0.85,
        )
        return None, float(approval_prob)

    probability = _action_class_anchor(action)
    probability -= 0.025 * max(0, _safe_int(getattr(action, "time_months", 1), 1) - 1)
    probability -= 0.00008 * max(0.0, _safe_float(getattr(action, "estimated_cost_usd", 0.0), 0.0))
    probability -= 0.02 * max(0, int(plan_action_count) - 1)
    probability += _customer_context_adjustment(customer_context)

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
        probability -= 0.03

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
    approval_pending_count = 0

    for index, action in enumerate(actions):
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
        else:
            approval_pending_count += 1

    if not group_members:
        return {
            "plan_execution_probability": 0.0,
            "mean_action_execution_probability": 0.0,
            "nominal_action_probability_mean": 0.0,
            "executable_action_count": 0,
            "executable_action_group_count": 0,
            "approval_pending_action_count": int(approval_pending_count),
        }

    group_probabilities: dict[str, float] = {}
    for key, probabilities in group_members.items():
        if not probabilities:
            continue
        group_penalty = max(0.70, 1.0 - (0.05 * max(0, len(probabilities) - 1)))
        group_probability = min(probabilities) * group_penalty
        group_probabilities[key] = float(_clamp(group_probability, lo=0.05, hi=0.95))

    for index, action in enumerate(actions):
        key = _group_key(action, index)
        action.action_group_execution_probability = group_probabilities.get(key)

    group_values = list(group_probabilities.values())
    geometric_mean = math.prod(group_values) ** (1.0 / max(1, len(group_values)))
    load_penalty = max(0.35, 1.0 - (0.08 * max(0, len(group_values) - 1)))
    plan_probability = float(_clamp(geometric_mean * load_penalty, lo=0.02, hi=0.95))

    return {
        "plan_execution_probability": plan_probability,
        "mean_action_execution_probability": float(sum(executable_action_probabilities) / max(1, len(executable_action_probabilities))),
        "nominal_action_probability_mean": float(sum(group_values) / max(1, len(group_values))),
        "executable_action_count": int(len(executable_action_probabilities)),
        "executable_action_group_count": int(len(group_values)),
        "approval_pending_action_count": int(approval_pending_count),
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
    plan.mean_action_execution_probability = float(probability_bundle.get("mean_action_execution_probability", 0.0))
    plan.executable_action_count = int(probability_bundle.get("executable_action_count", 0))
    plan.executable_action_group_count = int(probability_bundle.get("executable_action_group_count", 0))
    plan.approval_pending_action_count = int(probability_bundle.get("approval_pending_action_count", 0))

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
