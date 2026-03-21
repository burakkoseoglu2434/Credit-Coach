from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

import numpy as np
import pandas as pd

from credit_coach.causality.action_constraints import causal_penalty
from credit_coach.data.schema import PlanAction, PlanRecord, PrimaryNumericTarget
from credit_coach.macro.reliability import (
    compute_effective_reliability,
    compute_robust_anchor_pd,
    evaluate_reliability_from_pd,
    resolve_reliability_settings,
)
from credit_coach.model.predict import predict_proba_pd
from credit_coach.recourse.action_space import (
    estimate_action_cost_usd,
    get_action_metadata,
    get_numeric_target_metadata,
    get_action_spec,
    get_actionable_features,
)
from credit_coach.recourse.action_constraints import enforce_action_constraints
from credit_coach.recourse.execution_probability import annotate_plan_execution_probability
from credit_coach.recourse.feasibility import apply_target_feasibility_with_details
from credit_coach.recourse.offer_optimization import annotate_offer_optimization, build_offer_contract
from credit_coach.recourse.region_targets import get_target_pd
from credit_coach.recourse.trajectory import attach_canonical_trajectory, phase_id_for_month
from credit_coach.safety.statistical import estimate_prediction_ci


@dataclass
class PlanGenConfig:
    tau: float
    causal_weight: float = 0.3


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


def _deadline_exceeded(deadline_ts: float | None) -> bool:
    return bool(deadline_ts is not None and time.perf_counter() >= float(deadline_ts))


def _mark_deadline_aborted(runtime_diag: dict[str, Any] | None) -> None:
    if runtime_diag is None:
        return
    runtime_diag["deadline_aborted"] = True


def _strategy_scale(strategy: str) -> float:
    strategy = strategy.lower()
    if strategy == "conservative":
        return 0.8
    if strategy == "aggressive":
        return 1.5
    return 1.0


def _horizon_scale(horizon_months: int) -> float:
    return {3: 0.8, 6: 1.0, 12: 1.25}.get(horizon_months, 1.0)


def _phase_id_for_month(month: int) -> str:
    return phase_id_for_month(month)


def _week_window_for_month(month: int) -> tuple[int, int]:
    m = max(1, int(month))
    start = int(((m - 1) * 4) + 1)
    end = int(m * 4)
    return start, end


def _make_plan_action(
    *,
    feature_name: str,
    current_value: float,
    target_value: float,
    requested_target_value: float | None = None,
    action_month: int,
    action_context: dict[str, Any] | None = None,
    action_status: str = "valid",
    action_status_reason: str | None = None,
    diagnostic_flags: list[str] | None = None,
) -> PlanAction:
    spec = get_action_spec(feature_name)
    phase_id = _phase_id_for_month(action_month)
    week_start, week_end = _week_window_for_month(action_month)
    action_meta = get_action_metadata(feature_name, action_month=action_month, action_phase=phase_id)
    offer_contract = build_offer_contract(
        action_meta,
        current_value=float(current_value),
        target_value=float(target_value),
        action_month=int(action_month),
        action_context=action_context,
    )
    numeric_target = _build_primary_numeric_target(
        feature_name=feature_name,
        current_value=float(current_value),
        requested_target_value=float(requested_target_value if requested_target_value is not None else target_value),
        action_month=int(action_month),
    )
    return PlanAction(
        feature_name=feature_name,
        current_value=float(current_value),
        target_value=float(target_value),
        delta=float(target_value - current_value),
        time_months=int(action_month),
        estimated_cost_usd=estimate_action_cost_usd(float(current_value), float(target_value), spec),
        phase_id=phase_id,
        week_start=int(week_start),
        week_end=int(week_end),
        checkpoint_metric=f"{feature_name} -> {float(target_value):.6f}",
        action_key=str(action_meta.get("action_key") or ""),
        action_class=action_meta.get("action_class"),
        action_family=str(action_meta.get("action_family") or "") or None,
        action_title=str(action_meta.get("action_title") or ""),
        action_description=str(action_meta.get("action_description") or ""),
        action_group_id=str(action_meta.get("action_group_id") or ""),
        primary_numeric_target=numeric_target,
        composite_action=bool(action_meta.get("composite_action", False)),
        requires_institutional_approval=bool(action_meta.get("requires_institutional_approval", False)),
        institutional_approval_state=offer_contract.get("institutional_approval_state"),
        approval_pending_semantic_only=bool(action_meta.get("approval_pending_semantic_only", False)),
        offer_type=offer_contract.get("offer_type"),
        offer_terms=dict(offer_contract.get("offer_terms", {})),
        offer_terms_complete=bool(offer_contract.get("offer_terms_complete", False)),
        requires_acceptance=bool(offer_contract.get("requires_acceptance", False)),
        offer_family=offer_contract.get("offer_family"),
        offer_scoring_profile=offer_contract.get("offer_scoring_profile"),
        term_generation_rule=offer_contract.get("term_generation_rule"),
        offer_policy_arm=offer_contract.get("offer_policy_arm"),
        prerequisite_tags=list(action_meta.get("prerequisite_tags", [])),
        conflict_tags=list(action_meta.get("conflict_tags", [])),
        action_status=str(action_status),
        action_status_reason=action_status_reason,
        diagnostic_flags=list(diagnostic_flags or []),
    )


def _sanitize_numeric_target_value(
    *,
    feature_name: str,
    current_value: float,
    requested_target_value: float,
) -> float:
    spec = get_action_spec(feature_name)
    out = _clip_target(spec, float(requested_target_value))
    if spec.direction == "decrease":
        out = min(float(current_value), out)
    elif spec.direction == "increase":
        out = max(float(current_value), out)
    return float(out)


def _build_primary_numeric_target(
    *,
    feature_name: str,
    current_value: float,
    requested_target_value: float,
    action_month: int,
) -> PrimaryNumericTarget | None:
    numeric_meta = get_numeric_target_metadata(feature_name, action_month=action_month)
    if not bool(numeric_meta.get("is_primary_target")):
        return None
    direction = str(numeric_meta.get("direction") or "")
    if direction not in {"increase", "decrease"}:
        return None
    sanitized_target = _sanitize_numeric_target_value(
        feature_name=feature_name,
        current_value=float(current_value),
        requested_target_value=float(requested_target_value),
    )
    notes = ["minimum_credible_change", "semantic_sanity_only", "phase_32_feasibility_pending"]
    rule_source = str(numeric_meta.get("rule_source") or "")
    notes.append("feature_override_metric" if rule_source == "feature_override" else "action_family_default_metric")
    return PrimaryNumericTarget(
        metric_key=str(numeric_meta.get("metric_key") or ""),
        unit=str(numeric_meta.get("unit") or ""),
        current_value=float(current_value),
        target_value=float(sanitized_target),
        delta_value=float(sanitized_target - float(current_value)),
        due_month=int(numeric_meta.get("due_month") or action_month),
        direction=direction,
        generation_notes=notes,
        raw_generation_basis={
            "source_feature_name": str(feature_name),
            "requested_target_value": float(requested_target_value),
            "sanitized_target_value": float(sanitized_target),
            "rule_source": rule_source,
        },
    )


def _build_action_context(row: pd.Series) -> dict[str, Any]:
    return {
        str(k): row.get(k)
        for k in row.index
    }


def _record_action_realism_event(
    action_realism_events: list[dict[str, Any]] | None,
    *,
    feature_name: str,
    action_month: int,
    status: str,
    detail: dict[str, Any],
) -> None:
    if action_realism_events is None:
        return
    phase_id = _phase_id_for_month(action_month)
    action_meta = get_action_metadata(feature_name, action_month=action_month, action_phase=phase_id)
    action_realism_events.append(
        {
            "feature_name": feature_name,
            "action_key": str(action_meta.get("action_key") or ""),
            "action_class": str(action_meta.get("action_class") or ""),
            "action_family": str(action_meta.get("action_family") or ""),
            "action_group_id": str(action_meta.get("action_group_id") or ""),
            "composite_action": bool(action_meta.get("composite_action", False)),
            "requires_institutional_approval": bool(action_meta.get("requires_institutional_approval", False)),
            "approval_pending_semantic_only": bool(action_meta.get("approval_pending_semantic_only", False)),
            "time_months": int(action_month),
            "status": str(status),
            "requested_delta": float(detail.get("requested_delta", 0.0)),
            "resolved_delta": float(detail.get("resolved_delta", 0.0)),
            "semantic_ratio": float(detail.get("semantic_ratio", 1.0)),
            "reason_codes": list(detail.get("reason_codes", [])),
            "status_reason": detail.get("status_reason"),
        }
    )


def _phase1_fast_track_context(
    *,
    phase1_cfg: dict[str, Any] | None,
    denied_mode: bool,
    segment_context: dict[str, Any] | None,
) -> tuple[bool, set[str], float, bool]:
    phase1_cfg = phase1_cfg or {}
    enabled = bool(phase1_cfg.get("enabled", False))
    if not enabled:
        return False, set(), 1.0, False
    if bool(phase1_cfg.get("denied_only", True)) and not bool(denied_mode):
        return False, set(), 1.0, False
    risk_band = str((segment_context or {}).get("risk_band", "")).strip().lower()
    if bool(phase1_cfg.get("high_risk_only", True)) and risk_band != "high":
        return False, set(), 1.0, False
    prioritized_raw = phase1_cfg.get("prioritized_features", [])
    prioritized = {
        str(v).strip()
        for v in prioritized_raw
        if str(v).strip()
    } if isinstance(prioritized_raw, list) else set()
    step_multiplier = max(1.0, _safe_float(phase1_cfg.get("step_multiplier", 1.4), 1.4))
    force_phase1_month = bool(phase1_cfg.get("force_phase1_month", True))
    return True, prioritized, float(step_multiplier), bool(force_phase1_month)


def _clip_target(spec, target: float) -> float:
    out = float(target)
    if spec.min_val is not None:
        out = max(float(spec.min_val), out)
    if spec.max_val is not None:
        out = min(float(spec.max_val), out)
    return float(out)


def _target_from_step(spec, current: float, step: float) -> float:
    if spec.direction == "decrease":
        target = current - abs(float(step))
    elif spec.direction == "increase":
        target = current + abs(float(step))
    else:
        target = current
    return _clip_target(spec, target)


def _pd_for_candidate(
    *,
    row: pd.Series,
    feature_cols: list[str],
    feature_name: str,
    target_value: float,
    model,
    calibrator,
) -> float:
    x = row.copy()
    x[feature_name] = float(target_value)
    x_input = pd.DataFrame([x[feature_cols].values], columns=feature_cols)
    return float(predict_proba_pd(model, calibrator, x_input)[0])


def _estimate_feature_sensitivity(
    *,
    row: pd.Series,
    selected_features: list[str],
    strategy: str,
    horizon_months: int,
    model,
    calibrator,
    feature_cols: list[str],
    adaptive_cfg: dict[str, Any],
) -> tuple[float, dict[str, float]]:
    baseline = pd.DataFrame([row[feature_cols].values], columns=feature_cols)
    baseline_pd = float(predict_proba_pd(model, calibrator, baseline)[0])
    s_scale = _strategy_scale(strategy)
    h_scale = _horizon_scale(horizon_months)

    sens: dict[str, float] = {}
    for feat in selected_features:
        spec = get_action_spec(feat)
        current = float(row[feat])
        step = float(spec.step) * s_scale * h_scale
        trial = _target_from_step(spec, current, step)
        delta = abs(float(trial - current))
        if delta <= 1e-9:
            sens[feat] = 0.0
            continue
        pd_trial = _pd_for_candidate(
            row=row,
            feature_cols=feature_cols,
            feature_name=feat,
            target_value=trial,
            model=model,
            calibrator=calibrator,
        )
        sens[feat] = float(abs(baseline_pd - pd_trial) / delta)

    max_s = max(sens.values()) if sens else 0.0
    gain = max(0.0, _safe_float(adaptive_cfg.get("sensitivity_gain", 0.5), 0.5))
    if max_s > 0:
        sens = {k: float(1.0 + gain * (v / max_s)) for k, v in sens.items()}
    else:
        sens = {k: 1.0 for k in selected_features}
    return baseline_pd, sens


def _adaptive_feature_target(
    *,
    row: pd.Series,
    feature_cols: list[str],
    feat: str,
    strategy: str,
    horizon_months: int,
    model,
    calibrator,
    baseline_pd: float,
    sensitivity_multiplier: float,
    target_pd: float,
    adaptive_cfg: dict[str, Any],
) -> tuple[float, float]:
    spec = get_action_spec(feat)
    current = float(row[feat])
    s_scale = _strategy_scale(strategy)
    h_scale = _horizon_scale(horizon_months)
    base_step = float(spec.step) * s_scale * h_scale
    if abs(base_step) <= 1e-12:
        return current, baseline_pd

    max_multiplier = max(1.0, _safe_float(adaptive_cfg.get("max_multiplier", 4.0), 4.0))
    growth = max(1.05, _safe_float(adaptive_cfg.get("growth_factor", 1.5), 1.5))
    attempts = max(1, int(_safe_float(adaptive_cfg.get("max_attempts_per_feature", 3), 3)))
    min_pd_improvement = max(0.0, _safe_float(adaptive_cfg.get("min_pd_improvement", 0.001), 0.001))
    required_share = max(0.0, _safe_float(adaptive_cfg.get("required_share_per_feature", 0.35), 0.35))

    total_needed = max(0.0, baseline_pd - float(target_pd))
    required_improvement = max(min_pd_improvement, total_needed * required_share)

    step_cap = abs(base_step) * max_multiplier
    initial_step = min(step_cap, abs(base_step) * max(1.0, float(sensitivity_multiplier)))
    step = max(abs(base_step), initial_step)

    best_target = _target_from_step(spec, current, step)
    best_pd = _pd_for_candidate(
        row=row,
        feature_cols=feature_cols,
        feature_name=feat,
        target_value=best_target,
        model=model,
        calibrator=calibrator,
    )
    best_improvement = baseline_pd - best_pd

    for attempt in range(1, attempts):
        if best_improvement >= required_improvement:
            break
        cand_step = min(step_cap, step * (growth**attempt))
        target = _target_from_step(spec, current, cand_step)
        if abs(target - current) <= 1e-9:
            continue
        cand_pd = _pd_for_candidate(
            row=row,
            feature_cols=feature_cols,
            feature_name=feat,
            target_value=target,
            model=model,
            calibrator=calibrator,
        )
        if cand_pd < best_pd:
            best_target = float(target)
            best_pd = float(cand_pd)
            best_improvement = baseline_pd - best_pd

    return float(best_target), float(best_pd)


def _build_actions(
    row: pd.Series,
    selected_features: list[str],
    strategy: str,
    horizon_months: int,
    *,
    model=None,
    calibrator=None,
    feature_cols: list[str] | None = None,
    target_pd: float | None = None,
    adaptive_cfg: dict[str, Any] | None = None,
    feasibility_profile: dict[str, Any] | None = None,
    segment_context: dict[str, Any] | None = None,
    phase1_cfg: dict[str, Any] | None = None,
    denied_mode: bool = False,
    min_abs_delta: float = 1e-9,
    deadline_ts: float | None = None,
    runtime_diag: dict[str, Any] | None = None,
    action_realism_events: list[dict[str, Any]] | None = None,
) -> list[PlanAction]:
    actions: list[PlanAction] = []
    adaptive_cfg = adaptive_cfg or {}
    action_context = _build_action_context(row)
    adaptive_enabled = bool(adaptive_cfg.get("enabled", False))
    can_adapt = adaptive_enabled and model is not None and feature_cols is not None and len(selected_features) > 0
    s_scale = _strategy_scale(strategy)
    h_scale = _horizon_scale(horizon_months)
    phase1_enabled, phase1_prioritized, phase1_step_multiplier, force_phase1_month = _phase1_fast_track_context(
        phase1_cfg=phase1_cfg,
        denied_mode=bool(denied_mode),
        segment_context=segment_context,
    )

    baseline_pd = None
    sensitivity: dict[str, float] = {}
    if can_adapt:
        if _deadline_exceeded(deadline_ts):
            _mark_deadline_aborted(runtime_diag)
            return actions
        baseline_pd, sensitivity = _estimate_feature_sensitivity(
            row=row,
            selected_features=selected_features,
            strategy=strategy,
            horizon_months=horizon_months,
            model=model,
            calibrator=calibrator,
            feature_cols=feature_cols or [],
            adaptive_cfg=adaptive_cfg,
        )

    for feat in selected_features:
        if _deadline_exceeded(deadline_ts):
            _mark_deadline_aborted(runtime_diag)
            break
        spec = get_action_spec(feat)
        current = float(row[feat])
        base_step = float(spec.step)
        step = base_step * s_scale * h_scale
        if phase1_enabled and feat in phase1_prioritized:
            step *= float(phase1_step_multiplier)
        target = _target_from_step(spec, current, step)
        requested_target = float(target)

        if can_adapt and baseline_pd is not None:
            tpd = float(target_pd if target_pd is not None else max(0.0, baseline_pd - 0.02))
            target, _ = _adaptive_feature_target(
                row=row,
                feature_cols=feature_cols or [],
                feat=feat,
                strategy=strategy,
                horizon_months=horizon_months,
                model=model,
                calibrator=calibrator,
                baseline_pd=float(baseline_pd),
                sensitivity_multiplier=float(sensitivity.get(feat, 1.0)),
                target_pd=tpd,
                adaptive_cfg=adaptive_cfg,
            )
            requested_target = float(target)

        detail = apply_target_feasibility_with_details(
            feature_name=feat,
            current_value=current,
            target_value=float(target),
            horizon_months=horizon_months,
            profile=feasibility_profile,
            segment_context=segment_context,
            action_class=spec.action_class,
            action_context=action_context,
            min_abs_effect=min_abs_delta,
        )
        target = float(detail["target_value"])
        target = _clip_target(spec, target)
        delta = target - current
        action_month = max(1, min(horizon_months, spec.time_months))
        if phase1_enabled and force_phase1_month and feat in phase1_prioritized:
            action_month = 1
        _record_action_realism_event(
            action_realism_events,
            feature_name=feat,
            action_month=action_month,
            status=str(detail["status"]),
            detail=detail,
        )
        if str(detail["status"]) == "rejected":
            continue
        if abs(float(delta)) <= float(min_abs_delta):
            continue
        actions.append(
            _make_plan_action(
                feature_name=feat,
                current_value=current,
                target_value=float(target),
                requested_target_value=float(requested_target),
                action_month=action_month,
                action_context=action_context,
                action_status=str(detail["status"]),
                action_status_reason=detail.get("status_reason"),
                diagnostic_flags=list(detail.get("reason_codes", [])),
            )
        )
    return actions


def _apply_actions(base_row: pd.Series, actions: list[PlanAction]) -> pd.Series:
    out = base_row.copy()
    for a in actions:
        out[a.feature_name] = a.target_value
    return out


def _plan_cost(actions: list[PlanAction]) -> float:
    return float(sum(a.estimated_cost_usd for a in actions))


def _score_plan(
    predicted_pd: float,
    tau: float,
    target_pd: float,
    cost: float,
    causal_pen: float,
) -> float:
    risk_gain = max(0.0, tau - predicted_pd) + max(0.0, target_pd - predicted_pd)
    return float((risk_gain * 100.0) - (cost * 0.001) - causal_pen)


def _normalize_robust_weights(raw: dict | None) -> tuple[float, float, float]:
    raw = raw or {}
    w_nominal = float(raw.get("nominal_margin", 0.35))
    w_reliability = float(raw.get("reliability", 0.45))
    w_robust = float(raw.get("robust_margin", 0.20))
    s = w_nominal + w_reliability + w_robust
    if s <= 0:
        return 0.35, 0.45, 0.20
    return w_nominal / s, w_reliability / s, w_robust / s


def _normalize_gate_weights(raw: dict | None) -> tuple[float, float, float]:
    raw = raw or {}
    w_ci = float(raw.get("ci", 0.5))
    w_rel = float(raw.get("reliability", 0.3))
    w_worst = float(raw.get("worst_margin", 0.2))
    s = w_ci + w_rel + w_worst
    if s <= 0:
        return 0.5, 0.3, 0.2
    return w_ci / s, w_rel / s, w_worst / s


def _gate_violation_penalty(
    *,
    ci_high: float,
    tau: float,
    reliability: float,
    min_reliability: float | None,
    worst_margin: float,
    min_worst_margin: float | None,
    weights: tuple[float, float, float],
) -> float:
    w_ci, w_rel, w_worst = weights
    ci_violation = max(0.0, float(ci_high) - float(tau))
    rel_violation = max(0.0, float(min_reliability) - float(reliability)) if min_reliability is not None else 0.0
    worst_violation = max(0.0, float(min_worst_margin) - float(worst_margin)) if min_worst_margin is not None else 0.0
    return float((w_ci * ci_violation) + (w_rel * rel_violation) + (w_worst * worst_violation))


def _violation_terms(
    *,
    ci_high: float,
    tau: float,
    reliability: float,
    min_reliability: float | None,
    worst_margin: float,
    min_worst_margin: float | None,
) -> tuple[float, float, float]:
    ci_violation = max(0.0, float(ci_high) - float(tau))
    rel_violation = max(0.0, float(min_reliability) - float(reliability)) if min_reliability is not None else 0.0
    worst_violation = max(0.0, float(min_worst_margin) - float(worst_margin)) if min_worst_margin is not None else 0.0
    return float(ci_violation), float(rel_violation), float(worst_violation)


def _normalize_denied_weights(raw: dict | None) -> dict[str, float]:
    raw = raw or {}
    defaults = {
        "ci": 0.45,
        "reliability": 0.30,
        "worst_margin": 0.20,
        "cost": 0.03,
        "sparsity": 0.02,
        "nominal_margin": 0.20,
        "short_term": 0.15,
    }
    out: dict[str, float] = {}
    for k, v in defaults.items():
        out[k] = max(0.0, float(raw.get(k, v)))
    return out


def _segment_adjusted_denied_weights(
    *,
    denied_cfg: dict,
    segment_context: dict[str, Any] | None,
) -> dict[str, float]:
    base = _normalize_denied_weights(denied_cfg.get("weights", {}) if isinstance(denied_cfg, dict) else {})
    if not isinstance(segment_context, dict):
        return base
    risk_band = str(segment_context.get("risk_band", ""))
    rb_map = (
        denied_cfg.get("risk_band_weight_multipliers", {})
        if isinstance(denied_cfg.get("risk_band_weight_multipliers", {}), dict)
        else {}
    )
    rb_weights = rb_map.get(risk_band, {})
    if not isinstance(rb_weights, dict):
        return base
    out = dict(base)
    for k in ("ci", "reliability", "worst_margin", "cost", "sparsity", "nominal_margin"):
        out[k] = max(0.0, float(out.get(k, 0.0) * float(rb_weights.get(k, 1.0))))
    return out


def _short_term_progress_signal(
    *,
    actions: list[PlanAction],
    base_pd: float | None,
    predicted_pd: float,
    denied_cfg: dict,
    segment_context: dict[str, Any] | None,
    denied_mode: bool,
) -> float:
    short_term_cfg = (
        denied_cfg.get("short_term", {})
        if isinstance(denied_cfg.get("short_term", {}), dict)
        else {}
    )
    if not bool(short_term_cfg.get("enabled", False)):
        return 0.0
    if bool(short_term_cfg.get("denied_only", True)) and not bool(denied_mode):
        return 0.0
    if base_pd is None:
        return 0.0
    if not actions:
        return 0.0

    phase1_cutoff_month = max(1, int(_safe_float(short_term_cfg.get("phase1_cutoff_month", 1), 1)))
    phase2_cutoff_month = max(phase1_cutoff_month, int(_safe_float(short_term_cfg.get("phase2_cutoff_month", 3), 3)))
    phase1_share_weight = max(0.0, _safe_float(short_term_cfg.get("phase1_share_weight", 1.0), 1.0))
    phase2_share_weight = max(0.0, _safe_float(short_term_cfg.get("phase2_share_weight", 0.35), 0.35))
    base_reduction_weight = max(0.0, _safe_float(short_term_cfg.get("base_reduction_weight", 0.25), 0.25))
    high_risk_multiplier = max(1.0, _safe_float(short_term_cfg.get("high_risk_multiplier", 1.15), 1.15))
    min_phase1_actions = max(0, int(_safe_float(short_term_cfg.get("min_phase1_actions", 1), 1)))

    months = [max(1, int(_safe_float(getattr(a, "time_months", 1), 1))) for a in actions]
    total = float(max(1, len(months)))
    phase1_count = int(sum(1 for m in months if m <= phase1_cutoff_month))
    phase2_count = int(sum(1 for m in months if m <= phase2_cutoff_month))
    phase1_share = float(phase1_count / total)
    phase2_share = float(phase2_count / total)
    pd_reduction = max(0.0, float(base_pd) - float(predicted_pd))

    timing_signal = (phase1_share_weight * phase1_share) + (phase2_share_weight * phase2_share)
    signal = (pd_reduction * base_reduction_weight) + timing_signal
    if phase1_count < min_phase1_actions:
        signal -= float(min_phase1_actions - phase1_count)

    risk_band = str((segment_context or {}).get("risk_band", "")).strip().lower()
    if denied_mode and risk_band == "high":
        signal *= float(high_risk_multiplier)
    return float(signal)


def _score_plan_denied_objective(
    *,
    predicted_pd: float,
    base_pd: float | None,
    tau: float,
    ci_high: float,
    reliability: float,
    worst_margin: float,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
    cost: float,
    action_count: int,
    causal_pen: float,
    fairness_penalty: float,
    fairness_weight: float,
    denied_cfg: dict,
    segment_context: dict[str, Any] | None = None,
    actions: list[PlanAction] | None = None,
    denied_mode: bool = False,
) -> float:
    weights = _segment_adjusted_denied_weights(
        denied_cfg=denied_cfg,
        segment_context=segment_context,
    )
    squared = bool(denied_cfg.get("squared_violation", True))
    exponent = 2 if squared else 1

    ci_violation, rel_violation, worst_violation = _violation_terms(
        ci_high=ci_high,
        tau=tau,
        reliability=reliability,
        min_reliability=min_reliability,
        worst_margin=worst_margin,
        min_worst_margin=min_worst_risk_margin,
    )
    violation_loss = (
        (weights["ci"] * (ci_violation**exponent))
        + (weights["reliability"] * (rel_violation**exponent))
        + (weights["worst_margin"] * (worst_violation**exponent))
    )
    operational_loss = (weights["cost"] * float(cost) * 0.001) + (weights["sparsity"] * float(max(0, int(action_count))))
    penalty_scale = max(0.0, float(denied_cfg.get("penalty_scale", 140.0)))

    nominal_margin = max(0.0, float(tau) - float(predicted_pd))
    bonus = float(weights["nominal_margin"]) * nominal_margin
    short_term_signal = _short_term_progress_signal(
        actions=list(actions or []),
        base_pd=base_pd,
        predicted_pd=predicted_pd,
        denied_cfg=denied_cfg,
        segment_context=segment_context,
        denied_mode=bool(denied_mode),
    )
    bonus += float(weights["short_term"]) * short_term_signal
    fairness_pen = max(0.0, float(fairness_penalty)) * max(0.0, float(fairness_weight))
    return float((bonus * 100.0) - ((violation_loss + operational_loss) * penalty_scale) - causal_pen - fairness_pen)


def _gate_objective_loss_for_pd(
    *,
    pd_value: float,
    tau: float,
    robust_cfg: dict,
    scenarios: list[dict] | None,
    threshold_shift_per_msi_unit: float,
    weekly_cfg: dict[str, Any] | None = None,
    segment_context: dict[str, Any] | None = None,
    denied_mode: bool = False,
) -> float:
    weekly_cfg = weekly_cfg or {}
    gate_cfg = robust_cfg.get("gate_objective", {}) if isinstance(robust_cfg.get("gate_objective", {}), dict) else {}
    uncertainty_cfg = gate_cfg.get("uncertainty", {}) if isinstance(gate_cfg.get("uncertainty", {}), dict) else {}
    ci_b = max(30, _safe_int(weekly_cfg.get("objective_bootstrap_b", 80), 80))
    ci_alpha = _safe_float(gate_cfg.get("alpha", 0.05), 0.05)
    ci_low, ci_high = estimate_prediction_ci(
        pd_value,
        b=ci_b,
        alpha=ci_alpha,
        method=str(uncertainty_cfg.get("method", "bootstrap")),
        sigma=float(uncertainty_cfg.get("sigma", 0.03)),
        conformal_residual_quantile=float(uncertainty_cfg.get("conformal_residual_quantile", 0.06)),
        conformal_min_width=float(uncertainty_cfg.get("conformal_min_width", 0.005)),
        conformal_calibration_path=uncertainty_cfg.get("calibration_artifact_path"),
        conformal_adaptive_by_score=bool(uncertainty_cfg.get("adaptive_by_score", False)),
        conformal_adaptive_mode=str(uncertainty_cfg.get("adaptive_mode", "cap")),
        conformal_adaptive_blend=float(uncertainty_cfg.get("adaptive_blend", 1.0)),
        conformal_adaptive_gap_weight=float(uncertainty_cfg.get("adaptive_gap_weight", 0.0)),
        conformal_max_width=(
            float(uncertainty_cfg.get("max_width"))
            if uncertainty_cfg.get("max_width") is not None
            else None
        ),
        risk_band=str((segment_context or {}).get("risk_band", "")).strip() or None,
        denied_mode=bool(denied_mode),
        uncertainty_profiles=(
            uncertainty_cfg.get("profiles", {})
            if isinstance(uncertainty_cfg.get("profiles", {}), dict)
            else {}
        ),
    )
    _ = ci_low

    cvar_quantile = _safe_float(robust_cfg.get("cvar_quantile", 0.9), 0.9)
    rel_settings = resolve_reliability_settings(
        uncertainty_cfg=uncertainty_cfg,
        segment_context=segment_context,
    )
    rel_report = evaluate_reliability_from_pd(
        base_pd=float(pd_value),
        tau=float(tau),
        scenarios=scenarios or [],
        threshold_shift_per_msi_unit=float(threshold_shift_per_msi_unit),
        cvar_quantile=float(cvar_quantile),
        reliability_soft_scale=float(rel_settings.get("soft_scale", 0.02)),
    )
    reliability = compute_effective_reliability(
        rel_report,
        mode=str(rel_settings.get("mode", "hard")),
        soft_weight=float(rel_settings.get("soft_weight", 0.5)),
    )
    worst_margin = float(rel_report.get("worst_risk_margin", float(tau) - float(pd_value)))

    min_rel = gate_cfg.get("min_reliability", robust_cfg.get("min_reliability"))
    min_rel_override = rel_settings.get("min_reliability_override")
    if min_rel_override is not None:
        min_rel = float(min_rel_override) if min_rel is None else float(min(float(min_rel), float(min_rel_override)))
    min_worst = gate_cfg.get("min_worst_risk_margin", robust_cfg.get("min_worst_risk_margin"))
    min_rel_f = float(min_rel) if min_rel is not None else None
    min_worst_f = float(min_worst) if min_worst is not None else None
    weights = _normalize_gate_weights(gate_cfg.get("violation_weights", {}))
    return _gate_violation_penalty(
        ci_high=float(ci_high),
        tau=float(tau),
        reliability=float(reliability),
        min_reliability=min_rel_f,
        worst_margin=float(worst_margin),
        min_worst_margin=min_worst_f,
        weights=weights,
    )


def _score_plan_robust(
    *,
    predicted_pd: float,
    tau: float,
    reliability: float,
    robust_margin: float,
    ci_high: float,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
    gate_weights: tuple[float, float, float],
    gate_penalty_scale: float,
    fairness_penalty: float,
    fairness_weight: float,
    cost: float,
    causal_pen: float,
    weights: tuple[float, float, float],
) -> float:
    w_nominal, w_rel, w_robust = weights
    nominal_margin = max(0.0, tau - predicted_pd)
    core = (w_nominal * nominal_margin) + (w_rel * reliability) + (w_robust * robust_margin)
    gate_penalty = _gate_violation_penalty(
        ci_high=ci_high,
        tau=tau,
        reliability=reliability,
        min_reliability=min_reliability,
        worst_margin=robust_margin,
        min_worst_margin=min_worst_risk_margin,
        weights=gate_weights,
    )
    fairness_pen = max(0.0, float(fairness_penalty)) * max(0.0, float(fairness_weight))
    return float((core * 100.0) - (gate_penalty * gate_penalty_scale) - (cost * 0.001) - causal_pen - fairness_pen)


def _normalize_candidate_features(
    candidate_features: list[str] | list[dict] | None,
    *,
    actionable: list[str],
    feature_cols: list[str],
    topk: int,
) -> list[str]:
    if not candidate_features:
        return []

    weighted: list[tuple[str, float]] = []
    for item in candidate_features:
        if isinstance(item, str):
            feat = item
            weight = 0.0
        elif isinstance(item, dict):
            feat = str(item.get("feature", "")).strip()
            weight = float(item.get("abs_contribution", item.get("weight", 0.0)) or 0.0)
        else:
            continue

        if feat and feat in actionable and feat in feature_cols:
            weighted.append((feat, weight))

    if not weighted:
        return []

    # SHAP katkısı varsa yuksek agirligi oncele; yoksa sirayi koru.
    if any(abs(w) > 0 for _, w in weighted):
        weighted.sort(key=lambda t: t[1], reverse=True)

    seen = set()
    ordered: list[str] = []
    for feat, _ in weighted:
        if feat in seen:
            continue
        seen.add(feat)
        ordered.append(feat)
        if len(ordered) >= topk:
            break
    return ordered


def _resolve_max_actions(search_cfg: dict | None) -> int | None:
    if not isinstance(search_cfg, dict):
        return None
    action_budget = search_cfg.get("action_budget", {})
    if not isinstance(action_budget, dict):
        return None
    if not bool(action_budget.get("enabled", False)):
        return None
    raw = action_budget.get("max_actions")
    try:
        max_actions = int(raw)
    except Exception:
        return None
    if max_actions <= 0:
        return None
    return max_actions


def _prune_actions(
    actions: list[PlanAction],
    *,
    max_actions: int | None,
    min_abs_delta: float,
) -> list[PlanAction]:
    kept = [a for a in actions if abs(float(a.delta)) > float(min_abs_delta)]
    if max_actions is not None and len(kept) > int(max_actions):
        kept = kept[: int(max_actions)]
    return kept


def _build_actions_weekly(
    row: pd.Series,
    selected_features: list[str],
    strategy: str,
    horizon_months: int,
    *,
    model,
    calibrator,
    feature_cols: list[str],
    target_pd: float,
    adaptive_cfg: dict[str, Any] | None = None,
    feasibility_profile: dict[str, Any] | None = None,
    segment_context: dict[str, Any] | None = None,
    phase1_cfg: dict[str, Any] | None = None,
    weekly_cfg: dict[str, Any] | None = None,
    denied_mode: bool = False,
    robust_cfg: dict | None = None,
    scenarios: list[dict] | None = None,
    threshold_shift_per_msi_unit: float = 0.0,
    tau: float = 0.35,
    min_abs_delta: float = 1e-9,
    deadline_ts: float | None = None,
    runtime_diag: dict[str, Any] | None = None,
    action_realism_events: list[dict[str, Any]] | None = None,
) -> list[PlanAction]:
    adaptive_cfg = adaptive_cfg or {}
    weekly_cfg = weekly_cfg or {}
    robust_cfg = robust_cfg or {}

    weeks = max(1, _safe_int(weekly_cfg.get("weeks", max(4, horizon_months * 4)), max(4, horizon_months * 4)))
    max_weekly_actions = max(1, _safe_int(weekly_cfg.get("max_weekly_actions", 2), 2))
    weekly_step_scale = max(0.05, _safe_float(weekly_cfg.get("weekly_step_scale", 0.35), 0.35))
    min_weekly_improvement = max(0.0, _safe_float(weekly_cfg.get("min_weekly_improvement", 0.0005), 0.0005))
    stop_when_target_hit = bool(weekly_cfg.get("stop_when_target_hit", True))
    optimize_for_gate = bool(weekly_cfg.get("optimize_for_gate", True)) and bool(denied_mode)

    can_adapt = bool(adaptive_cfg.get("enabled", False))
    phase1_enabled, phase1_prioritized, phase1_step_multiplier, force_phase1_month = _phase1_fast_track_context(
        phase1_cfg=phase1_cfg,
        denied_mode=bool(denied_mode),
        segment_context=segment_context,
    )
    baseline_pd = float(
        predict_proba_pd(model, calibrator, pd.DataFrame([row[feature_cols].values], columns=feature_cols))[0]
    )
    action_context = _build_action_context(row)
    sensitivity: dict[str, float] = {f: 1.0 for f in selected_features}
    if can_adapt and selected_features:
        _, sensitivity = _estimate_feature_sensitivity(
            row=row,
            selected_features=selected_features,
            strategy=strategy,
            horizon_months=horizon_months,
            model=model,
            calibrator=calibrator,
            feature_cols=feature_cols,
            adaptive_cfg=adaptive_cfg,
        )

    work_row = row.copy()
    s_scale = _strategy_scale(strategy)
    h_scale = _horizon_scale(horizon_months)

    for week in range(1, weeks + 1):
        if _deadline_exceeded(deadline_ts):
            _mark_deadline_aborted(runtime_diag)
            break
        base_pd = float(
            predict_proba_pd(model, calibrator, pd.DataFrame([work_row[feature_cols].values], columns=feature_cols))[0]
        )
        if stop_when_target_hit and base_pd <= float(target_pd):
            break

        base_gate_loss = None
        if optimize_for_gate:
            base_gate_loss = _gate_objective_loss_for_pd(
                pd_value=base_pd,
                tau=tau,
                robust_cfg=robust_cfg,
                scenarios=scenarios,
                threshold_shift_per_msi_unit=threshold_shift_per_msi_unit,
                weekly_cfg=weekly_cfg,
                segment_context=segment_context,
                denied_mode=bool(denied_mode),
            )

        stage_horizon = max(1, min(horizon_months, _safe_int(round((week / max(1, weeks)) * horizon_months), horizon_months)))
        candidates: list[tuple[float, str, float]] = []

        for feat in selected_features:
            if _deadline_exceeded(deadline_ts):
                _mark_deadline_aborted(runtime_diag)
                break
            spec = get_action_spec(feat)
            current = float(work_row[feat])
            step = float(spec.step) * s_scale * h_scale * weekly_step_scale * float(sensitivity.get(feat, 1.0))
            if phase1_enabled and feat in phase1_prioritized:
                step *= float(phase1_step_multiplier)
            target = _target_from_step(spec, current, step)
            requested_target = float(target)
            detail = apply_target_feasibility_with_details(
                feature_name=feat,
                current_value=current,
                target_value=float(target),
                horizon_months=stage_horizon,
                profile=feasibility_profile,
                segment_context=segment_context,
                action_class=spec.action_class,
                action_context=_build_action_context(work_row),
                min_abs_effect=min_abs_delta,
            )
            target = float(detail["target_value"])
            target = _clip_target(spec, float(target))
            if str(detail["status"]) == "rejected":
                continue
            if abs(float(target) - current) <= float(min_abs_delta):
                continue
            cand_pd = _pd_for_candidate(
                row=work_row,
                feature_cols=feature_cols,
                feature_name=feat,
                target_value=float(target),
                model=model,
                calibrator=calibrator,
            )
            if optimize_for_gate and base_gate_loss is not None:
                cand_loss = _gate_objective_loss_for_pd(
                    pd_value=float(cand_pd),
                    tau=tau,
                    robust_cfg=robust_cfg,
                    scenarios=scenarios,
                    threshold_shift_per_msi_unit=threshold_shift_per_msi_unit,
                    weekly_cfg=weekly_cfg,
                    segment_context=segment_context,
                    denied_mode=bool(denied_mode),
                )
                improvement = float(base_gate_loss - cand_loss)
            else:
                improvement = float(base_pd - float(cand_pd))

            if improvement >= min_weekly_improvement:
                candidates.append((improvement, feat, float(target)))

        if not candidates:
            break

        candidates.sort(key=lambda x: x[0], reverse=True)
        updates = candidates[:max_weekly_actions]
        for _, feat, target in updates:
            work_row[feat] = float(target)

    actions: list[PlanAction] = []
    for feat in selected_features:
        if _deadline_exceeded(deadline_ts):
            _mark_deadline_aborted(runtime_diag)
            break
        current = float(row[feat])
        target = float(work_row[feat])
        if abs(target - current) <= float(min_abs_delta):
            continue
        spec = get_action_spec(feat)
        detail = apply_target_feasibility_with_details(
            feature_name=feat,
            current_value=current,
            target_value=target,
            horizon_months=horizon_months,
            profile=feasibility_profile,
            segment_context=segment_context,
            action_class=spec.action_class,
            action_context=action_context,
            min_abs_effect=min_abs_delta,
        )
        final_target = float(detail["target_value"])
        final_target = _clip_target(spec, float(final_target))
        action_month = max(1, min(horizon_months, spec.time_months))
        if phase1_enabled and force_phase1_month and feat in phase1_prioritized:
            action_month = 1
        _record_action_realism_event(
            action_realism_events,
            feature_name=feat,
            action_month=action_month,
            status=str(detail["status"]),
            detail=detail,
        )
        if str(detail["status"]) == "rejected":
            continue
            if abs(final_target - current) <= float(min_abs_delta):
                continue
            actions.append(
                _make_plan_action(
                    feature_name=feat,
                    current_value=current,
                    target_value=float(final_target),
                    requested_target_value=float(requested_target),
                    action_month=action_month,
                    action_context=action_context,
                    action_status=str(detail["status"]),
                    action_status_reason=detail.get("status_reason"),
                    diagnostic_flags=list(detail.get("reason_codes", [])),
            )
        )

    if not actions and baseline_pd > float(target_pd):
        return _build_actions(
            row=row,
            selected_features=selected_features,
            strategy=strategy,
            horizon_months=horizon_months,
            model=model,
            calibrator=calibrator,
            feature_cols=feature_cols,
            target_pd=target_pd,
            adaptive_cfg=adaptive_cfg,
            feasibility_profile=feasibility_profile,
            segment_context=segment_context,
            phase1_cfg=phase1_cfg,
            denied_mode=bool(denied_mode),
            min_abs_delta=min_abs_delta,
            deadline_ts=deadline_ts,
            runtime_diag=runtime_diag,
            action_realism_events=action_realism_events,
        )
    return actions


def generate_plan_record(
    customer_id: str,
    run_id: str,
    row: pd.Series,
    model,
    calibrator,
    feature_cols: list[str],
    horizon_months: int,
    strategy: str,
    graph: dict | None,
    cfg: PlanGenConfig,
    candidate_features: list[str] | list[dict] | None = None,
    topk: int = 4,
    scenarios: list[dict] | None = None,
    threshold_shift_per_msi_unit: float = 0.0,
    robust_cfg: dict | None = None,
    search_cfg: dict | None = None,
    fairness_penalty: float = 0.0,
    feasibility_profile: dict[str, Any] | None = None,
    segment_context: dict[str, Any] | None = None,
    base_pd: float | None = None,
    deadline_ts: float | None = None,
    runtime_diag: dict[str, Any] | None = None,
) -> PlanRecord:
    actionable = get_actionable_features()
    selected = _normalize_candidate_features(
        candidate_features,
        actionable=actionable,
        feature_cols=feature_cols,
        topk=topk,
    )

    if not selected:
        selected = [f for f in feature_cols if f in actionable][:topk]

    robust_cfg = robust_cfg or {}
    search_cfg = search_cfg or {}
    max_actions = _resolve_max_actions(search_cfg)
    min_abs_delta = max(0.0, _safe_float(search_cfg.get("min_abs_action_delta", 1e-6), 1e-6))
    adaptive_cfg = search_cfg.get("adaptive_steps", {}) if isinstance(search_cfg.get("adaptive_steps", {}), dict) else {}
    weekly_cfg = search_cfg.get("weekly_optimizer", {}) if isinstance(search_cfg.get("weekly_optimizer", {}), dict) else {}
    phase1_cfg = search_cfg.get("phase1_fast_track", {}) if isinstance(search_cfg.get("phase1_fast_track", {}), dict) else {}
    denied_mode = bool(search_cfg.get("denied_mode", False))
    use_weekly = bool(weekly_cfg.get("enabled", False)) and (not bool(weekly_cfg.get("only_denied", True)) or denied_mode)
    action_realism_events: list[dict[str, Any]] = []
    target_pd = get_target_pd(strategy, cfg.tau)
    target_pd_margin_extra = max(0.0, _safe_float(search_cfg.get("target_pd_margin_extra", 0.0), 0.0))
    if target_pd_margin_extra > 0.0:
        # Allow policy-level tightening of target PD (e.g. disadvantaged denied-target uplift).
        target_pd = max(0.001, float(target_pd) - float(target_pd_margin_extra))
    if use_weekly:
        actions = _build_actions_weekly(
            row=row,
            selected_features=selected,
            strategy=strategy,
            horizon_months=horizon_months,
            model=model,
            calibrator=calibrator,
            feature_cols=feature_cols,
            target_pd=target_pd,
            adaptive_cfg=adaptive_cfg,
            feasibility_profile=feasibility_profile,
            segment_context=segment_context,
            phase1_cfg=phase1_cfg,
            weekly_cfg=weekly_cfg,
            denied_mode=denied_mode,
            robust_cfg=robust_cfg,
            scenarios=scenarios,
            threshold_shift_per_msi_unit=threshold_shift_per_msi_unit,
            tau=cfg.tau,
            min_abs_delta=min_abs_delta,
            deadline_ts=deadline_ts,
            runtime_diag=runtime_diag,
            action_realism_events=action_realism_events,
        )
    else:
        actions = _build_actions(
            row,
            selected,
            strategy=strategy,
            horizon_months=horizon_months,
            model=model,
            calibrator=calibrator,
            feature_cols=feature_cols,
            target_pd=target_pd,
            adaptive_cfg=adaptive_cfg,
            feasibility_profile=feasibility_profile,
            segment_context=segment_context,
            phase1_cfg=phase1_cfg,
            denied_mode=bool(denied_mode),
            min_abs_delta=min_abs_delta,
            deadline_ts=deadline_ts,
            runtime_diag=runtime_diag,
            action_realism_events=action_realism_events,
        )
    if runtime_diag is not None and action_realism_events:
        runtime_diag.setdefault("action_realism_events", []).extend(action_realism_events)
        runtime_diag["action_realism_valid_action_count"] = int(
            runtime_diag.get("action_realism_valid_action_count", 0)
            + sum(1 for event in action_realism_events if str(event.get("status")) == "valid")
        )
        runtime_diag["action_realism_clipped_action_count"] = int(
            runtime_diag.get("action_realism_clipped_action_count", 0)
            + sum(1 for event in action_realism_events if str(event.get("status")) == "clipped")
        )
        runtime_diag["action_realism_rejected_action_count"] = int(
            runtime_diag.get("action_realism_rejected_action_count", 0)
            + sum(1 for event in action_realism_events if str(event.get("status")) == "rejected")
        )
        if any(str(event.get("status")) == "rejected" for event in action_realism_events) and not actions:
            runtime_diag["action_realism_infeasible_plan_count"] = int(
                runtime_diag.get("action_realism_infeasible_plan_count", 0) + 1
            )
    actions = _prune_actions(
        actions,
        max_actions=max_actions,
        min_abs_delta=min_abs_delta,
    )
    constraint_result = enforce_action_constraints(
        actions,
        action_context=_build_action_context(row),
    )
    actions = list(constraint_result.actions)
    if runtime_diag is not None and constraint_result.trace:
        runtime_diag.setdefault("action_constraint_events", []).extend(constraint_result.trace)
        runtime_diag["action_constraint_repair_applied_count"] = int(
            runtime_diag.get("action_constraint_repair_applied_count", 0)
            + int(any(str(event.get("event_type", "")) == "repair_dropped" for event in constraint_result.trace))
        )
        runtime_diag["action_constraint_approval_pending_action_count"] = int(
            runtime_diag.get("action_constraint_approval_pending_action_count", 0)
            + sum(1 for event in constraint_result.trace if str(event.get("event_type", "")) == "approval_pending")
        )
        runtime_diag["action_constraint_invalid_combination_count"] = int(
            runtime_diag.get("action_constraint_invalid_combination_count", 0)
            + int(
                any(
                    str(event.get("reason_code", "")).startswith("conflict_with:")
                    or str(event.get("reason_code", "")).startswith("missing_prerequisite:")
                    for event in constraint_result.trace
                )
            )
        )
    x_prime = _apply_actions(row, actions)
    x_input = pd.DataFrame([x_prime[feature_cols].values], columns=feature_cols)
    pred_pd = float(predict_proba_pd(model, calibrator, x_input)[0])
    row_base_pd = (
        float(base_pd)
        if base_pd is not None
        else float(predict_proba_pd(model, calibrator, pd.DataFrame([row[feature_cols].values], columns=feature_cols))[0])
    )

    action_dicts = [a.model_dump() for a in actions]
    cpen = causal_penalty(action_dicts, graph, penalty_weight=cfg.causal_weight) if graph else 0.0
    cost = _plan_cost(actions)

    nominal_score = _score_plan(pred_pd, cfg.tau, target_pd, cost, cpen)
    robust_enabled = bool(robust_cfg.get("enabled", True))
    robust_method = str(robust_cfg.get("objective", "cvar")).strip().lower() or "cvar"
    cvar_quantile = float(robust_cfg.get("cvar_quantile", 0.9))
    rel_report = evaluate_reliability_from_pd(
        base_pd=pred_pd,
        tau=cfg.tau,
        scenarios=scenarios or [],
        threshold_shift_per_msi_unit=threshold_shift_per_msi_unit,
        cvar_quantile=cvar_quantile,
    )
    robust_anchor_pd = compute_robust_anchor_pd(rel_report, objective=robust_method)
    robust_margin = float(cfg.tau - robust_anchor_pd)
    gate_cfg = robust_cfg.get("gate_objective", {}) if isinstance(robust_cfg.get("gate_objective", {}), dict) else {}
    uncertainty_cfg = gate_cfg.get("uncertainty", {}) if isinstance(gate_cfg.get("uncertainty", {}), dict) else {}
    rel_settings = resolve_reliability_settings(
        uncertainty_cfg=uncertainty_cfg,
        segment_context=segment_context,
    )
    reliability = compute_effective_reliability(
        rel_report,
        mode=str(rel_settings.get("mode", "hard")),
        soft_weight=float(rel_settings.get("soft_weight", 0.5)),
    )

    obj_alpha = float(gate_cfg.get("alpha", 0.05))
    ci_low_obj, ci_high_obj = estimate_prediction_ci(
        pred_pd,
        b=int(uncertainty_cfg.get("bootstrap_b", 300)),
        alpha=obj_alpha,
        method=str(uncertainty_cfg.get("method", "bootstrap")),
        sigma=float(uncertainty_cfg.get("sigma", 0.03)),
        conformal_residual_quantile=float(uncertainty_cfg.get("conformal_residual_quantile", 0.06)),
        conformal_min_width=float(uncertainty_cfg.get("conformal_min_width", 0.005)),
        conformal_calibration_path=uncertainty_cfg.get("calibration_artifact_path"),
        conformal_adaptive_by_score=bool(uncertainty_cfg.get("adaptive_by_score", False)),
        conformal_adaptive_mode=str(uncertainty_cfg.get("adaptive_mode", "cap")),
        conformal_adaptive_blend=float(uncertainty_cfg.get("adaptive_blend", 1.0)),
        conformal_adaptive_gap_weight=float(uncertainty_cfg.get("adaptive_gap_weight", 0.0)),
        conformal_max_width=(
            float(uncertainty_cfg.get("max_width"))
            if uncertainty_cfg.get("max_width") is not None
            else None
        ),
        risk_band=str((segment_context or {}).get("risk_band", "")).strip() or None,
        denied_mode=bool(denied_mode),
        uncertainty_profiles=(
            uncertainty_cfg.get("profiles", {})
            if isinstance(uncertainty_cfg.get("profiles", {}), dict)
            else {}
        ),
    )
    _ = ci_low_obj
    min_rel = gate_cfg.get("min_reliability", robust_cfg.get("min_reliability"))
    min_rel_override = rel_settings.get("min_reliability_override")
    if min_rel_override is not None:
        min_rel = float(min_rel_override) if min_rel is None else float(min(float(min_rel), float(min_rel_override)))
    min_worst = gate_cfg.get("min_worst_risk_margin", robust_cfg.get("min_worst_risk_margin"))
    min_rel_f = float(min_rel) if min_rel is not None else None
    min_worst_f = float(min_worst) if min_worst is not None else None
    gate_weights = _normalize_gate_weights(gate_cfg.get("violation_weights", {}))
    gate_penalty_scale = max(0.0, float(gate_cfg.get("penalty_scale", 100.0)))
    fairness_weight = max(0.0, float(gate_cfg.get("fairness_weight", 0.0)))
    denied_obj_cfg = robust_cfg.get("denied_objective", {}) if isinstance(robust_cfg.get("denied_objective", {}), dict) else {}
    denied_obj_enabled = bool(denied_obj_cfg.get("enabled", False)) and (
        not bool(denied_obj_cfg.get("only_denied", True)) or denied_mode
    )

    if robust_enabled:
        if denied_obj_enabled:
            robust_score = _score_plan_denied_objective(
                predicted_pd=pred_pd,
                base_pd=row_base_pd,
                tau=cfg.tau,
                ci_high=ci_high_obj,
                reliability=reliability,
                worst_margin=float(rel_report.get("worst_risk_margin", cfg.tau - pred_pd)),
                min_reliability=min_rel_f,
                min_worst_risk_margin=min_worst_f,
                cost=cost,
                action_count=len(actions),
                causal_pen=float(cpen),
                fairness_penalty=fairness_penalty,
                fairness_weight=fairness_weight,
                denied_cfg=denied_obj_cfg,
                segment_context=segment_context,
                actions=actions,
                denied_mode=bool(denied_mode),
            )
        else:
            weights = _normalize_robust_weights(robust_cfg.get("weights", {}))
            robust_score = _score_plan_robust(
                predicted_pd=pred_pd,
                tau=cfg.tau,
                reliability=reliability,
                robust_margin=robust_margin,
                ci_high=ci_high_obj,
                min_reliability=min_rel_f,
                min_worst_risk_margin=min_worst_f,
                gate_weights=gate_weights,
                gate_penalty_scale=gate_penalty_scale,
                fairness_penalty=fairness_penalty,
                fairness_weight=fairness_weight,
                cost=cost,
                causal_pen=float(cpen),
                weights=weights,
            )
        final_score = robust_score
    else:
        robust_score = nominal_score
        final_score = nominal_score

    plan = PlanRecord(
        plan_id=f"{run_id}_{customer_id}_{horizon_months}_{strategy}",
        customer_id=customer_id,
        run_id=run_id,
        horizon_months=horizon_months,
        strategy=strategy,
        actions=actions,
        predicted_pd=pred_pd,
        reliability=reliability,
        robust_score=robust_score,
        robust_margin=robust_margin,
        robust_anchor_pd=robust_anchor_pd,
        robust_method=robust_method if robust_enabled else "disabled",
        robust_worst_risk_margin=float(rel_report.get("worst_risk_margin", cfg.tau - pred_pd)),
        causal_penalty=cpen,
        score=final_score,
        constraint_status=constraint_result.status,
        constraint_reason=constraint_result.reason,
        constraint_trace=list(constraint_result.trace),
        status="PENDING",
    )
    annotate_plan_execution_probability(
        plan,
        base_pd=row_base_pd,
        customer_context=_build_action_context(row),
        segment_context=segment_context,
    )
    attach_canonical_trajectory(
        plan,
        row=row,
        base_pd=row_base_pd,
        tau=cfg.tau,
        model=model,
        calibrator=calibrator,
        feature_cols=feature_cols,
    )
    annotate_offer_optimization(
        plan,
        customer_context=_build_action_context(row),
        segment_context=segment_context,
    )
    return plan


def generate_nine_plans(
    customer_id: str,
    run_id: str,
    row: pd.Series,
    model,
    calibrator,
    feature_cols: list[str],
    graph: dict | None,
    tau: float,
    horizons: list[int],
    strategies: list[str],
    candidate_features: list[str] | list[dict] | None = None,
    topk: int = 4,
    scenarios: list[dict] | None = None,
    threshold_shift_per_msi_unit: float = 0.0,
    robust_cfg: dict | None = None,
    search_cfg: dict | None = None,
    fairness_penalty: float = 0.0,
    feasibility_profile: dict[str, Any] | None = None,
    segment_context: dict[str, Any] | None = None,
    base_pd: float | None = None,
    deadline_ts: float | None = None,
    runtime_diag: dict[str, Any] | None = None,
) -> list[PlanRecord]:
    cfg = PlanGenConfig(tau=tau)
    plans: list[PlanRecord] = []
    deadline_aborted = False
    for h in horizons:
        if _deadline_exceeded(deadline_ts):
            deadline_aborted = True
            break
        for s in strategies:
            if _deadline_exceeded(deadline_ts):
                deadline_aborted = True
                break
            plans.append(
                generate_plan_record(
                    customer_id=customer_id,
                    run_id=run_id,
                    row=row,
                    model=model,
                    calibrator=calibrator,
                    feature_cols=feature_cols,
                    horizon_months=h,
                    strategy=s,
                    graph=graph,
                    cfg=cfg,
                    candidate_features=candidate_features,
                    topk=topk,
                    scenarios=scenarios,
                    threshold_shift_per_msi_unit=threshold_shift_per_msi_unit,
                    robust_cfg=robust_cfg,
                    search_cfg=search_cfg,
                    fairness_penalty=fairness_penalty,
                    feasibility_profile=feasibility_profile,
                    segment_context=segment_context,
                    base_pd=base_pd,
                    deadline_ts=deadline_ts,
                    runtime_diag=runtime_diag,
                )
            )
        if deadline_aborted:
            break
    if deadline_aborted:
        _mark_deadline_aborted(runtime_diag)
    return plans
