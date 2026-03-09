from __future__ import annotations

from typing import Any


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
      - min_target / max_target
      - freeze_if_current_below / freeze_if_current_above
      - round_to_int
    """
    if not isinstance(profile, dict) or not profile:
        return float(target_value)
    if not _as_bool(profile.get("enabled", True), default=True):
        return float(target_value)

    defaults = profile.get("defaults", {}) if isinstance(profile.get("defaults", {}), dict) else {}
    per_feature = profile.get("features", {}) if isinstance(profile.get("features", {}), dict) else {}
    feature_rule = per_feature.get(feature_name, {})
    if not isinstance(feature_rule, dict):
        feature_rule = {}
    rule = _merge_rules(defaults, feature_rule)

    current = float(current_value)
    out = float(target_value)
    horizon = max(1, int(horizon_months))

    freeze_below = _as_float(rule.get("freeze_if_current_below"))
    if freeze_below is not None and current < freeze_below:
        return current
    freeze_above = _as_float(rule.get("freeze_if_current_above"))
    if freeze_above is not None and current > freeze_above:
        return current

    min_target = _as_float(rule.get("min_target"))
    max_target = _as_float(rule.get("max_target"))
    if min_target is not None:
        out = max(min_target, out)
    if max_target is not None:
        out = min(max_target, out)

    segment_mult = _resolve_segment_multiplier(
        feature_name=feature_name,
        segment_context=segment_context,
    )

    max_rel = _as_float(rule.get("max_relative_change"))
    if max_rel is not None and max_rel >= 0:
        max_delta = max(abs(current), 1.0) * max_rel * float(segment_mult)
        out = max(current - max_delta, min(current + max_delta, out))

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

    if out >= current and max_inc is not None and max_inc >= 0:
        out = min(out, current + max_inc)
    if out < current and max_dec is not None and max_dec >= 0:
        out = max(out, current - max_dec)

    if _as_bool(rule.get("round_to_int"), default=False):
        out = float(round(out))

    return float(out)
