from __future__ import annotations

from typing import Any

_DEBT_PAYDOWN_FEATURES = {
    "revol_bal",
    "tot_cur_bal",
    "total_bal_ex_mort",
    "delinq_amnt",
    "tot_coll_amt",
}
_CREDIT_LIMIT_FEATURES = {
    "total_rev_hi_lim",
    "total_bc_limit",
    "tot_hi_cred_lim",
}
_UTILIZATION_FEATURES = {
    "revol_util",
}
_INCOME_FEATURES = {
    "annual_inc",
}
_SEMANTIC_RATIO_DEFAULTS = {
    "behavioral": 0.05,
    "structural": 0.35,
    "institutional": 0.50,
}
_CONSTRAINT_FAMILY_PRIORITY = {
    "semantic": 0,
    "documentation": 1,
    "dependency": 2,
    "interaction": 3,
    "capacity": 4,
    "policy": 5,
}
_CAPACITY_REASON_CODES = {
    "max_relative_change",
    "max_abs_increase",
    "max_abs_decrease",
    "income_growth_cap",
    "max_utilization_drop_ratio",
    "max_credit_limit_adjustment_ratio",
    "financial_capacity_ratio",
}
_POLICY_REASON_CODES = {
    "freeze_if_current_below",
    "freeze_if_current_above",
    "min_target_bound",
    "max_target_bound",
    "round_to_int",
}


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _merge_rules(defaults: dict[str, Any], feature_rule: dict[str, Any]) -> dict[str, Any]:
    out = dict(defaults or {})
    out.update(feature_rule or {})
    return out


def _resolve_segment_multiplier(
    *,
    feature_name: str,
    segment_context: dict[str, Any] | None,
) -> float:
    if not isinstance(segment_context, dict) or not segment_context:
        return 1.0
    if not _as_bool(segment_context.get("segment_caps_applied", False), default=False):
        return 1.0
    base_mult = _as_float(segment_context.get("cap_multiplier"))
    if base_mult is None:
        base_mult = 1.0

    feature_multipliers = (
        segment_context.get("feature_cap_multipliers", {})
        if isinstance(segment_context.get("feature_cap_multipliers", {}), dict)
        else {}
    )
    feat_mult = _as_float(feature_multipliers.get(feature_name))
    if feat_mult is None:
        feat_mult = 1.0

    combined = float(base_mult) * float(feat_mult)
    hard_min = _as_float(segment_context.get("cap_multiplier_min"))
    hard_max = _as_float(segment_context.get("cap_multiplier_max"))
    if hard_min is not None:
        combined = max(float(hard_min), combined)
    if hard_max is not None:
        combined = min(float(hard_max), combined)
    return float(max(0.0, combined))


def _append_reason(reason_codes: list[str], code: str, *, changed: bool) -> None:
    if not changed:
        return
    if code not in reason_codes:
        reason_codes.append(code)


def _semantic_ratio_threshold(rule: dict[str, Any], action_class: str | None) -> float:
    cls = str(action_class or "").strip().lower()
    field_map = {
        "behavioral": "min_behavioral_semantic_ratio",
        "structural": "min_structural_semantic_ratio",
        "institutional": "min_institutional_semantic_ratio",
    }
    threshold = _as_float(rule.get(field_map.get(cls, ""))) if cls in field_map else None
    if threshold is not None:
        return float(max(0.0, min(1.0, threshold)))
    return float(_SEMANTIC_RATIO_DEFAULTS.get(cls or "behavioral", 0.35))


def classify_constraint_family(reason_code: str | None) -> str | None:
    code = str(reason_code or "").strip()
    if not code:
        return None
    if code in {"semantic_noop_after_clip", "direction_inversion_after_clip", "semantic_loss_after_clip"}:
        return "semantic"
    if code.startswith("missing_mandatory_dependency_input"):
        return "documentation"
    if code in _CAPACITY_REASON_CODES or code.startswith("max_abs_increase_per_month") or code.startswith(
        "max_abs_decrease_per_month"
    ) or code == "max_monthly_change":
        return "capacity"
    if code in _POLICY_REASON_CODES:
        return "policy"
    return "policy"


def dominant_constraint_family(reason_codes: list[str]) -> str | None:
    families = [classify_constraint_family(code) for code in reason_codes]
    normalized = [family for family in families if family]
    if not normalized:
        return None
    return min(normalized, key=lambda family: (_CONSTRAINT_FAMILY_PRIORITY.get(family, 99), family))


def apply_target_feasibility_with_details(
    *,
    feature_name: str,
    current_value: float,
    target_value: float,
    horizon_months: int,
    profile: dict[str, Any] | None,
    segment_context: dict[str, Any] | None = None,
    action_class: str | None = None,
    action_context: dict[str, Any] | None = None,
    min_abs_effect: float = 1e-9,
) -> dict[str, Any]:
    current = float(current_value)
    requested = float(target_value)
    horizon = max(1, int(horizon_months))
    out = float(target_value)
    reason_codes: list[str] = []

    if not isinstance(profile, dict) or not profile:
        resolved_delta = float(out - current)
        return {
            "target_value": float(out),
            "requested_delta": float(requested - current),
            "resolved_delta": resolved_delta,
            "status": "valid",
            "was_clipped": False,
            "reason_codes": [],
            "constraint_family": None,
            "status_reason": None,
            "semantic_ratio": 1.0,
            "semantic_preserved": True,
        }
    if not _as_bool(profile.get("enabled", True), default=True):
        resolved_delta = float(out - current)
        return {
            "target_value": float(out),
            "requested_delta": float(requested - current),
            "resolved_delta": resolved_delta,
            "status": "valid",
            "was_clipped": False,
            "reason_codes": [],
            "constraint_family": None,
            "status_reason": None,
            "semantic_ratio": 1.0,
            "semantic_preserved": True,
        }

    defaults = profile.get("defaults", {}) if isinstance(profile.get("defaults", {}), dict) else {}
    per_feature = profile.get("features", {}) if isinstance(profile.get("features", {}), dict) else {}
    feature_rule = per_feature.get(feature_name, {})
    if not isinstance(feature_rule, dict):
        feature_rule = {}
    rule = _merge_rules(defaults, feature_rule)

    freeze_below = _as_float(rule.get("freeze_if_current_below"))
    if freeze_below is not None and current < freeze_below:
        out = current
        _append_reason(reason_codes, "freeze_if_current_below", changed=True)
    freeze_above = _as_float(rule.get("freeze_if_current_above"))
    if freeze_above is not None and current > freeze_above:
        out = current
        _append_reason(reason_codes, "freeze_if_current_above", changed=True)

    min_target = _as_float(rule.get("min_target"))
    if min_target is not None:
        prev = out
        out = max(min_target, out)
        _append_reason(reason_codes, "min_target_bound", changed=abs(out - prev) > 1e-12)
    max_target = _as_float(rule.get("max_target"))
    if max_target is not None:
        prev = out
        out = min(max_target, out)
        _append_reason(reason_codes, "max_target_bound", changed=abs(out - prev) > 1e-12)

    segment_mult = _resolve_segment_multiplier(
        feature_name=feature_name,
        segment_context=segment_context,
    )

    max_rel = _as_float(rule.get("max_relative_change"))
    if max_rel is not None and max_rel >= 0:
        prev = out
        max_delta = max(abs(current), 1.0) * max_rel * float(segment_mult)
        out = max(current - max_delta, min(current + max_delta, out))
        _append_reason(reason_codes, "max_relative_change", changed=abs(out - prev) > 1e-12)

    max_inc = _as_float(rule.get("max_abs_increase"))
    max_dec = _as_float(rule.get("max_abs_decrease"))
    if max_inc is not None and max_inc >= 0:
        max_inc = float(max_inc) * float(segment_mult)
    if max_dec is not None and max_dec >= 0:
        max_dec = float(max_dec) * float(segment_mult)

    per_month_inc = _as_float(rule.get("max_abs_increase_per_month"))
    if per_month_inc is not None and per_month_inc >= 0:
        scaled_inc = per_month_inc * float(horizon) * float(segment_mult)
        max_inc = min(max_inc, scaled_inc) if max_inc is not None else scaled_inc

    per_month_dec = _as_float(rule.get("max_abs_decrease_per_month"))
    if per_month_dec is not None and per_month_dec >= 0:
        scaled_dec = per_month_dec * float(horizon) * float(segment_mult)
        max_dec = min(max_dec, scaled_dec) if max_dec is not None else scaled_dec

    max_monthly_change = _as_float(rule.get("max_monthly_change"))
    if max_monthly_change is not None and max_monthly_change >= 0:
        monthly_cap = float(max_monthly_change) * float(horizon) * float(segment_mult)
        max_inc = min(max_inc, monthly_cap) if max_inc is not None else monthly_cap
        max_dec = min(max_dec, monthly_cap) if max_dec is not None else monthly_cap

    if out >= current and max_inc is not None and max_inc >= 0:
        prev = out
        out = min(out, current + max_inc)
        _append_reason(reason_codes, "max_abs_increase", changed=abs(out - prev) > 1e-12)
    if out < current and max_dec is not None and max_dec >= 0:
        prev = out
        out = max(out, current - max_dec)
        _append_reason(reason_codes, "max_abs_decrease", changed=abs(out - prev) > 1e-12)

    if feature_name in _INCOME_FEATURES:
        income_growth_cap = _as_float(rule.get("income_growth_cap"))
        if income_growth_cap is not None and income_growth_cap >= 0:
            prev = out
            out = min(out, current * (1.0 + float(income_growth_cap)))
            _append_reason(reason_codes, "income_growth_cap", changed=abs(out - prev) > 1e-12)

    if feature_name in _UTILIZATION_FEATURES:
        max_utilization_drop_ratio = _as_float(rule.get("max_utilization_drop_ratio"))
        if max_utilization_drop_ratio is not None and max_utilization_drop_ratio >= 0 and current > 0:
            prev = out
            max_drop = current * float(max_utilization_drop_ratio)
            out = max(out, current - max_drop)
            _append_reason(reason_codes, "max_utilization_drop_ratio", changed=abs(out - prev) > 1e-12)

    if feature_name in _CREDIT_LIMIT_FEATURES:
        max_credit_limit_adjustment_ratio = _as_float(rule.get("max_credit_limit_adjustment_ratio"))
        if max_credit_limit_adjustment_ratio is not None and max_credit_limit_adjustment_ratio >= 0 and current > 0:
            prev = out
            max_limit = current * (1.0 + float(max_credit_limit_adjustment_ratio))
            min_limit = current * max(0.0, 1.0 - float(max_credit_limit_adjustment_ratio))
            out = min(max_limit, max(min_limit, out))
            _append_reason(reason_codes, "max_credit_limit_adjustment_ratio", changed=abs(out - prev) > 1e-12)

    if feature_name in _DEBT_PAYDOWN_FEATURES:
        financial_capacity_ratio = _as_float(rule.get("financial_capacity_ratio"))
        annual_inc = _as_float((action_context or {}).get("annual_inc"))
        if (
            financial_capacity_ratio is not None
            and financial_capacity_ratio >= 0
            and annual_inc is None
            and out < current
        ):
            if "missing_mandatory_dependency_input:annual_inc" not in reason_codes:
                reason_codes.append("missing_mandatory_dependency_input:annual_inc")
        if (
            financial_capacity_ratio is not None
            and financial_capacity_ratio >= 0
            and annual_inc is not None
            and annual_inc > 0
            and out < current
        ):
            prev = out
            monthly_income = float(annual_inc) / 12.0
            max_paydown = monthly_income * float(financial_capacity_ratio) * float(horizon)
            out = max(out, current - max_paydown)
            _append_reason(reason_codes, "financial_capacity_ratio", changed=abs(out - prev) > 1e-12)

    if _as_bool(rule.get("round_to_int"), default=False):
        prev = out
        out = float(round(out))
        _append_reason(reason_codes, "round_to_int", changed=abs(out - prev) > 1e-12)

    requested_delta = float(requested - current)
    resolved_delta = float(out - current)
    was_clipped = abs(out - requested) > 1e-12
    semantic_ratio = 1.0
    if abs(requested_delta) > 1e-12:
        semantic_ratio = float(abs(resolved_delta) / abs(requested_delta))

    status = "clipped" if was_clipped else "valid"
    semantic_ratio_threshold = _semantic_ratio_threshold(rule, action_class)
    semantic_preserved = True

    if abs(requested_delta) > float(min_abs_effect):
        if abs(resolved_delta) <= float(min_abs_effect):
            status = "invalid"
            semantic_preserved = False
            if "semantic_noop_after_clip" not in reason_codes:
                reason_codes.append("semantic_noop_after_clip")
        elif requested_delta * resolved_delta < 0:
            status = "invalid"
            semantic_preserved = False
            if "direction_inversion_after_clip" not in reason_codes:
                reason_codes.append("direction_inversion_after_clip")
        elif was_clipped and semantic_ratio < semantic_ratio_threshold:
            status = "invalid"
            semantic_preserved = False
            if "semantic_loss_after_clip" not in reason_codes:
                reason_codes.append("semantic_loss_after_clip")
    if any(code.startswith("missing_mandatory_dependency_input") for code in reason_codes):
        status = "invalid"
        semantic_preserved = False

    status_reason = "|".join(reason_codes) if reason_codes else None
    return {
        "target_value": float(out),
        "requested_delta": float(requested_delta),
        "resolved_delta": float(resolved_delta),
        "status": status,
        "was_clipped": bool(was_clipped),
        "reason_codes": reason_codes,
        "constraint_family": dominant_constraint_family(reason_codes),
        "status_reason": status_reason,
        "semantic_ratio": float(semantic_ratio),
        "semantic_preserved": bool(semantic_preserved),
    }


def apply_target_feasibility(
    *,
    feature_name: str,
    current_value: float,
    target_value: float,
    horizon_months: int,
    profile: dict[str, Any] | None,
    segment_context: dict[str, Any] | None = None,
) -> float:
    """
    Apply feature-level recourse feasibility constraints.

    Supported rule keys:
      - max_relative_change
      - max_abs_increase / max_abs_decrease
      - max_abs_increase_per_month / max_abs_decrease_per_month
      - max_monthly_change
      - min_target / max_target
      - freeze_if_current_below / freeze_if_current_above
      - income_growth_cap
      - max_utilization_drop_ratio
      - max_credit_limit_adjustment_ratio
      - financial_capacity_ratio
      - round_to_int
    """
    result = apply_target_feasibility_with_details(
        feature_name=feature_name,
        current_value=current_value,
        target_value=target_value,
        horizon_months=horizon_months,
        profile=profile,
        segment_context=segment_context,
    )
    return float(result["target_value"])
