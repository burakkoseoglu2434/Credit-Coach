from __future__ import annotations

from typing import Any, Mapping

from credit_coach.data.schema import PlanAction, PlanRecord
from credit_coach.recourse.action_space import get_action_spec

_EPSILON = 1e-6
_DECREASE_METRICS = {
    "credit_utilization_pct",
    "monthly_payment_amount",
    "requested_loan_amount",
    "debt_to_income_pct",
    "delinquent_balance_amount",
}
_INCREASE_METRICS = {
    "documented_income_amount",
    "credit_limit_amount",
    "bankcard_limit_amount",
    "total_high_credit_limit_amount",
}
_LIMIT_METRICS = {
    "credit_limit_amount",
    "bankcard_limit_amount",
    "total_high_credit_limit_amount",
}


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except Exception:
        return default


def _context_float(customer_context: Mapping[str, Any] | None, *keys: str) -> float | None:
    if not isinstance(customer_context, Mapping):
        return None
    for key in keys:
        if key in customer_context:
            value = _safe_float(customer_context.get(key), None)
            if value is not None:
                return value
    return None


def _metric_direction(action: PlanAction) -> str:
    target = getattr(action, "primary_numeric_target", None)
    metric_key = str(getattr(target, "metric_key", "") or "").strip()
    if metric_key in _DECREASE_METRICS:
        return "decrease"
    if metric_key in _INCREASE_METRICS:
        return "increase"
    spec = get_action_spec(str(getattr(action, "feature_name", "") or ""))
    return str(getattr(spec, "direction", "any") or "any")


def _institution_mislabel(action: PlanAction) -> bool:
    action_class = str(getattr(action, "action_class", "") or "").strip().lower()
    if action_class not in {"behavioral", "structural"}:
        return False
    if bool(getattr(action, "requires_institutional_approval", False)):
        return True
    if bool(getattr(action, "approval_pending_semantic_only", False)):
        return True
    target = getattr(action, "primary_numeric_target", None)
    metric_key = str(getattr(target, "metric_key", "") or "").strip()
    return metric_key in _LIMIT_METRICS


def _utilization_paydown_ratio(action: PlanAction, customer_context: Mapping[str, Any] | None) -> float | None:
    target = getattr(action, "primary_numeric_target", None)
    if target is None:
        return None
    current_pct = _safe_float(getattr(target, "current_value", None), None)
    target_pct = _safe_float(getattr(target, "target_value", None), None)
    if current_pct is None or target_pct is None:
        return None
    current_ratio = current_pct / 100.0
    target_ratio = target_pct / 100.0
    current_balance = _context_float(customer_context, "revol_bal")
    inferred_limit = None
    if current_balance is not None and current_balance > 0.0 and current_ratio > 0.0:
        inferred_limit = current_balance / current_ratio
    if inferred_limit is None:
        inferred_limit = _context_float(customer_context, "total_rev_hi_lim", "total_bc_limit", "tot_hi_cred_lim")
    if inferred_limit is None or inferred_limit <= 0.0:
        return None
    if current_balance is None:
        current_balance = current_ratio * inferred_limit
    if current_balance <= 0.0:
        return None
    target_balance = target_ratio * inferred_limit
    paydown = max(0.0, current_balance - target_balance)
    return float(paydown / current_balance)


def _monthly_income(customer_context: Mapping[str, Any] | None) -> float | None:
    annual_inc = _context_float(customer_context, "annual_inc")
    if annual_inc is None or annual_inc <= 0.0:
        return None
    return float(annual_inc / 12.0)


def _warning_codes_for_action(
    action: PlanAction,
    *,
    customer_context: Mapping[str, Any] | None,
) -> list[str]:
    target = getattr(action, "primary_numeric_target", None)
    if target is None:
        return []
    metric_key = str(getattr(target, "metric_key", "") or "").strip()
    current_value = _safe_float(getattr(target, "current_value", None), None)
    target_value = _safe_float(getattr(target, "target_value", None), None)
    if current_value is None or target_value is None or current_value <= 0.0:
        if metric_key != "debt_to_income_pct":
            return []

    codes: set[str] = set()
    if metric_key == "credit_utilization_pct" and current_value is not None:
        improvement = max(0.0, current_value - target_value)
        if improvement > 25.0:
            codes.add("feasibility_band_exceeded")
            codes.add("economic_delta_implausible" if improvement > 35.0 else "economic_delta_large")
        paydown_ratio = _utilization_paydown_ratio(action, customer_context)
        if paydown_ratio is not None and paydown_ratio > 0.75:
            codes.add("economic_delta_implausible" if paydown_ratio > 0.90 else "economic_delta_large")
    elif metric_key == "monthly_payment_amount" and current_value is not None and current_value > 0.0:
        reduction_ratio = max(0.0, current_value - target_value) / current_value
        if reduction_ratio > 0.60:
            codes.add("feasibility_band_exceeded")
            codes.add("economic_delta_implausible" if reduction_ratio > 0.75 else "economic_delta_large")
    elif metric_key == "requested_loan_amount" and current_value is not None and current_value > 0.0:
        reduction_ratio = max(0.0, current_value - target_value) / current_value
        if reduction_ratio > 0.40:
            codes.add("feasibility_band_exceeded")
            codes.add("economic_delta_implausible" if reduction_ratio > 0.60 else "economic_delta_large")
    elif metric_key == "documented_income_amount" and current_value is not None and current_value > 0.0:
        increase_ratio = max(0.0, target_value - current_value) / current_value
        if increase_ratio > 0.20:
            codes.add("feasibility_band_exceeded")
            codes.add("economic_delta_implausible" if increase_ratio > 0.35 else "economic_delta_large")
    elif metric_key == "debt_to_income_pct":
        if current_value is not None:
            improvement = max(0.0, current_value - target_value)
            if improvement > 10.0:
                codes.add("feasibility_band_exceeded")
                codes.add("economic_delta_implausible" if improvement > 15.0 else "economic_delta_large")
        monthly_income = _monthly_income(customer_context)
        if current_value is not None and monthly_income is not None and monthly_income > 0.0:
            monthly_relief = max(0.0, ((current_value - target_value) / 100.0) * monthly_income)
            relief_ratio = monthly_relief / monthly_income
            if relief_ratio > 0.25:
                codes.add("economic_delta_implausible" if relief_ratio > 0.40 else "economic_delta_large")
    elif metric_key in _LIMIT_METRICS and current_value is not None and current_value > 0.0:
        increase_ratio = max(0.0, target_value - current_value) / current_value
        if increase_ratio > 0.25:
            codes.add("feasibility_band_exceeded")
            codes.add("economic_delta_implausible" if increase_ratio > 0.50 else "economic_delta_large")
    return sorted(codes)


def annotate_action_recommendation_validity(
    action: PlanAction,
    *,
    customer_context: Mapping[str, Any] | None = None,
) -> PlanAction:
    target = getattr(action, "primary_numeric_target", None)
    if target is None:
        action.recommendation_validity_status = "invalid" if _institution_mislabel(action) else "valid"
        action.recommendation_validity_codes = ["customer_institution_mislabel"] if _institution_mislabel(action) else []
        action.recommendation_sanity_flag = bool(action.recommendation_validity_codes)
        action.recommendation_warning_penalty = 0.0
        return action

    current_value = _safe_float(getattr(target, "current_value", None), None)
    target_value = _safe_float(getattr(target, "target_value", None), None)
    direction = _metric_direction(action)
    hard_codes: list[str] = []

    if _institution_mislabel(action):
        hard_codes.append("customer_institution_mislabel")

    if current_value is not None and target_value is not None:
        if abs(target_value - current_value) <= _EPSILON:
            hard_codes.append("no_effect_target")
        elif direction == "decrease" and target_value > current_value:
            hard_codes.append("directional_worsens_risk")
        elif direction == "increase" and target_value < current_value:
            hard_codes.append("directional_worsens_risk")

    if hard_codes:
        action.recommendation_validity_status = "invalid"
        action.recommendation_validity_codes = sorted(set(hard_codes))
        action.recommendation_sanity_flag = True
        action.recommendation_warning_penalty = 0.0
        return action

    warning_codes = _warning_codes_for_action(action, customer_context=customer_context)
    warning_count = len(warning_codes)
    action.recommendation_validity_status = "warning" if warning_count > 0 else "valid"
    action.recommendation_validity_codes = warning_codes
    action.recommendation_sanity_flag = warning_count > 0
    action.recommendation_warning_penalty = 0.0 if warning_count == 0 else float(min(20, 12 + (8 * max(0, warning_count - 1))))
    return action


def annotate_plan_recommendation_validity(
    plan: PlanRecord,
    *,
    customer_context: Mapping[str, Any] | None = None,
) -> PlanRecord:
    annotated_actions: list[PlanAction] = []
    invalid_count = 0
    warning_count = 0
    warning_penalty = 0.0
    codes: set[str] = set()
    for action in list(getattr(plan, "actions", []) or []):
        annotated = annotate_action_recommendation_validity(action, customer_context=customer_context)
        annotated_actions.append(annotated)
        status = str(getattr(annotated, "recommendation_validity_status", "") or "").strip().lower()
        if status == "invalid":
            invalid_count += 1
        elif status == "warning":
            warning_count += 1
            warning_penalty += float(getattr(annotated, "recommendation_warning_penalty", 0.0) or 0.0)
        codes.update(str(code) for code in list(getattr(annotated, "recommendation_validity_codes", []) or []) if str(code))

    plan.actions = annotated_actions
    plan.recommendation_invalid_action_count = int(invalid_count)
    plan.recommendation_warning_action_count = int(warning_count)
    plan.recommendation_warning_penalty = float(warning_penalty)
    plan.recommendation_validity_codes = sorted(codes)
    if invalid_count > 0:
        plan.recommendation_validity_status = "invalid"
        plan.recommendation_sanity_flag = True
    elif warning_count > 0:
        plan.recommendation_validity_status = "warning"
        plan.recommendation_sanity_flag = True
    else:
        plan.recommendation_validity_status = "valid"
        plan.recommendation_sanity_flag = False
    return plan


def filter_invalid_numeric_plans(plans: list[PlanRecord]) -> tuple[list[PlanRecord], list[PlanRecord]]:
    kept: list[PlanRecord] = []
    removed: list[PlanRecord] = []
    for plan in plans:
        status = str(getattr(plan, "recommendation_validity_status", "") or "valid").strip().lower()
        if status == "invalid":
            removed.append(plan)
        else:
            kept.append(plan)
    return kept, removed


def recommendation_warning_penalty(plan: PlanRecord) -> float:
    return float(getattr(plan, "recommendation_warning_penalty", 0.0) or 0.0)
