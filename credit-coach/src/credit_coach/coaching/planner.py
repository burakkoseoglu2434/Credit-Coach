from __future__ import annotations

from typing import Any

from credit_coach.data.schema import PlanRecord

_STATUS_PRIORITY = {
    "APPROVED": 0,
    "NEEDS_REVIEW": 1,
    "REJECTED": 2,
    "ERROR": 3,
}
_CONSTRAINT_PRIORITY = {
    "valid": 0,
    "repaired": 1,
    "provisional": 2,
    "invalid": 3,
}


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)


def _safe_int(v, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


def _plan_cost(plan: PlanRecord) -> float:
    total = 0.0
    for action in plan.actions:
        total += _safe_float(getattr(action, "estimated_cost_usd", 0.0), 0.0)
    return float(total)


def _plan_execution_probability(plan: PlanRecord) -> float:
    execution_probability = getattr(plan, "plan_execution_probability", None)
    if execution_probability is None:
        return 0.0
    return max(0.0, min(1.0, _safe_float(execution_probability, 0.0)))


def _nominal_pd_improvement(plan: PlanRecord, *, base_pd: float | None, tau: float | None) -> float:
    explicit = getattr(plan, "nominal_pd_improvement", None)
    if explicit is not None:
        return max(0.0, _safe_float(explicit, 0.0))
    predicted_pd = getattr(plan, "predicted_pd", None)
    if predicted_pd is None:
        return 0.0
    if base_pd is not None:
        return max(0.0, float(base_pd) - float(predicted_pd))
    if tau is not None:
        return max(0.0, float(tau) - float(predicted_pd))
    return 0.0


def _expected_pd_improvement(plan: PlanRecord, *, base_pd: float | None, tau: float | None) -> float:
    explicit = getattr(plan, "expected_pd_improvement", None)
    if explicit is not None:
        return max(0.0, _safe_float(explicit, 0.0))
    return float(_plan_execution_probability(plan) * _nominal_pd_improvement(plan, base_pd=base_pd, tau=tau))


def _phase_action_shares(plan: PlanRecord) -> tuple[float, float, float]:
    actions = list(plan.actions)
    if not actions:
        return 0.0, 0.0, 0.0
    total = float(len(actions))
    phase1 = sum(1 for action in actions if _safe_int(getattr(action, "time_months", 1), 1) <= 1)
    phase2 = sum(1 for action in actions if _safe_int(getattr(action, "time_months", 1), 1) <= 3)
    return float(phase1 / total), float(phase2 / total), 1.0


def _trajectory_checkpoint_pds(plan: PlanRecord, *, base_pd: float | None, tau: float | None) -> tuple[float, float, float]:
    checkpoint_map: dict[int, float] = {}
    for checkpoint in list(getattr(plan, "trajectory_checkpoints", [])):
        week = _safe_int(getattr(checkpoint, "week", 0), 0)
        predicted_pd = getattr(checkpoint, "predicted_pd", None)
        if week > 0 and predicted_pd is not None:
            checkpoint_map[int(week)] = _safe_float(predicted_pd, 1.0)
    if checkpoint_map:
        pd4 = checkpoint_map.get(4, checkpoint_map.get(12, checkpoint_map.get(24, _safe_float(base_pd, 1.0))))
        pd12 = checkpoint_map.get(12, checkpoint_map.get(24, pd4))
        pd24 = checkpoint_map.get(24, checkpoint_map.get(12, pd12))
        return float(pd4), float(pd12), float(pd24)

    starting_pd = _safe_float(base_pd, _safe_float(tau, 1.0))
    final_pd = _safe_float(getattr(plan, "predicted_pd", None), starting_pd)
    total_improvement = max(0.0, starting_pd - final_pd)
    phase1_share, phase2_share, _ = _phase_action_shares(plan)
    pd4 = starting_pd - (total_improvement * max(0.15, phase1_share))
    pd12 = starting_pd - (total_improvement * max(0.45, phase2_share))
    pd24 = final_pd
    return float(pd4), float(pd12), float(pd24)


def _phase_aware_priority_score(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    segment_context: dict[str, Any] | None = None,
) -> float:
    pd4, pd12, pd24 = _trajectory_checkpoint_pds(plan, base_pd=base_pd, tau=tau)
    starting_pd = _safe_float(base_pd, max(pd4, pd12, pd24))
    early_improvement = max(0.0, starting_pd - pd4)
    mid_improvement = max(0.0, starting_pd - pd12)
    long_improvement = max(0.0, starting_pd - pd24)
    pass4 = 1.0 if tau is not None and pd4 <= float(tau) else 0.0
    pass12 = 1.0 if tau is not None and pd12 <= float(tau) else 0.0
    pass24 = 1.0 if tau is not None and pd24 <= float(tau) else 0.0
    regression_tolerance = 0.01
    regression_penalty = max(0.0, pd12 - (pd4 + regression_tolerance)) + max(0.0, pd24 - (pd12 + regression_tolerance))
    phase1_share, phase2_share, _ = _phase_action_shares(plan)
    early_health_ok = bool(pass4 > 0.0 or early_improvement >= max(0.03, 0.35 * max(long_improvement, 0.01)))
    risk_band = str((segment_context or {}).get("risk_band", "")).strip().lower()
    if risk_band == "high":
        weights = (0.70, 0.20, 0.10)
    else:
        weights = (0.55, 0.30, 0.15)
    long_bonus_multiplier = 1.0 if early_health_ok else 0.20
    score = (
        (weights[0] * ((early_improvement * 100.0) + (8.0 * pass4) + (5.0 * phase1_share)))
        + (weights[1] * ((mid_improvement * 100.0) + (5.0 * pass12) + (3.0 * phase2_share)))
        + (weights[2] * long_bonus_multiplier * ((long_improvement * 100.0) + (4.0 * pass24)))
        - (35.0 * regression_penalty)
    )
    if not early_health_ok:
        score -= 8.0
    return float(score)


def _trajectory_policy_label(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    segment_context: dict[str, Any] | None = None,
) -> str:
    pd4, pd12, pd24 = _trajectory_checkpoint_pds(plan, base_pd=base_pd, tau=tau)
    starting_pd = _safe_float(base_pd, max(pd4, pd12, pd24))
    early_improvement = max(0.0, starting_pd - pd4)
    long_improvement = max(0.0, starting_pd - pd24)
    phase1_share, _, _ = _phase_action_shares(plan)
    early_gate_ok = bool(tau is not None and pd4 <= float(tau))
    early_health_ok = bool(early_gate_ok or early_improvement >= max(0.03, 0.35 * max(long_improvement, 0.01)))
    if not early_health_ok and long_improvement > max(0.05, early_improvement + 0.02):
        return "long_horizon_heavy"
    if early_gate_ok or phase1_share >= 0.5:
        return "stabilize_first"
    return "balanced_progress"


def _annotate_trajectory_policy(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    segment_context: dict[str, Any] | None = None,
) -> None:
    plan.trajectory_policy_score = _phase_aware_priority_score(
        plan,
        base_pd=base_pd,
        tau=tau,
        segment_context=segment_context,
    )
    plan.trajectory_policy_label = _trajectory_policy_label(
        plan,
        base_pd=base_pd,
        tau=tau,
        segment_context=segment_context,
    )


def _short_term_action_signal(plan: PlanRecord, short_term_cfg: dict | None) -> float:
    short_term_cfg = short_term_cfg or {}
    if not bool(short_term_cfg.get("enabled", False)):
        return 0.0
    actions = list(plan.actions)
    if not actions:
        return 0.0
    phase1_cutoff_month = max(1, int(_safe_float(short_term_cfg.get("phase1_cutoff_month", 1), 1)))
    phase2_cutoff_month = max(phase1_cutoff_month, int(_safe_float(short_term_cfg.get("phase2_cutoff_month", 3), 3)))
    phase1_share_weight = max(0.0, _safe_float(short_term_cfg.get("phase1_share_weight", 1.0), 1.0))
    phase2_share_weight = max(0.0, _safe_float(short_term_cfg.get("phase2_share_weight", 0.35), 0.35))
    min_phase1_actions = max(0, int(_safe_float(short_term_cfg.get("min_phase1_actions", 1), 1)))

    action_months = [max(1, int(_safe_float(getattr(a, "time_months", 1), 1))) for a in actions]
    total = float(max(1, len(action_months)))
    phase1_count = int(sum(1 for m in action_months if m <= phase1_cutoff_month))
    phase2_count = int(sum(1 for m in action_months if m <= phase2_cutoff_month))
    phase1_share = float(phase1_count / total)
    phase2_share = float(phase2_count / total)

    scarcity_penalty = 0.0
    if phase1_count < int(min_phase1_actions):
        scarcity_penalty = float(min_phase1_actions - phase1_count)
    return float((phase1_share_weight * phase1_share) + (phase2_share_weight * phase2_share) - scarcity_penalty)


def _status_priority(status: str | None) -> int:
    key = str(status or "").strip().upper()
    return int(_STATUS_PRIORITY.get(key, 4))


def _prefer_non_rejected(plans: list[PlanRecord]) -> list[PlanRecord]:
    preferred = [p for p in plans if _status_priority(getattr(p, "status", "")) <= _STATUS_PRIORITY["NEEDS_REVIEW"]]
    return preferred if preferred else plans


def _constraint_priority(plan: PlanRecord) -> int:
    key = str(getattr(plan, "constraint_status", "valid") or "valid").strip().lower()
    return int(_CONSTRAINT_PRIORITY.get(key, 4))


def _prefer_constraint_eligible(plans: list[PlanRecord]) -> list[PlanRecord]:
    preferred = [p for p in plans if _constraint_priority(p) <= _CONSTRAINT_PRIORITY["repaired"]]
    return preferred if preferred else plans


def _ci_high_with_fallback(plan: PlanRecord, tau: float | None) -> float:
    if plan.ci_high is not None:
        return float(plan.ci_high)
    if plan.predicted_pd is not None:
        return float(plan.predicted_pd)
    if tau is not None:
        return float(tau) + 1.0
    return 1.0


def _reliability_with_fallback(plan: PlanRecord) -> float:
    if plan.reliability is not None:
        return float(plan.reliability)
    return 0.0


def _worst_margin_with_fallback(plan: PlanRecord) -> float:
    if plan.robust_worst_risk_margin is not None:
        return float(plan.robust_worst_risk_margin)
    return -1.0


def _gate_pass_score(
    plan: PlanRecord,
    *,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> float:
    ci_margin = 0.0
    if tau is not None and plan.ci_high is not None:
        ci_margin = float(tau) - float(plan.ci_high)

    rel_margin = 0.0
    if min_reliability is not None and plan.reliability is not None:
        rel_margin = float(plan.reliability) - float(min_reliability)

    worst_margin = 0.0
    if min_worst_risk_margin is not None and plan.robust_worst_risk_margin is not None:
        worst_margin = float(plan.robust_worst_risk_margin) - float(min_worst_risk_margin)

    return float((0.6 * ci_margin) + (0.25 * rel_margin) + (0.15 * worst_margin))


def _gate_violations(
    plan: PlanRecord,
    *,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> tuple[float, float, float]:
    ci_violation = 0.0
    if tau is not None:
        ci_violation = max(0.0, _ci_high_with_fallback(plan, tau) - float(tau))

    rel_violation = 0.0
    if min_reliability is not None:
        rel_violation = max(0.0, float(min_reliability) - _reliability_with_fallback(plan))

    worst_violation = 0.0
    if min_worst_risk_margin is not None:
        worst_violation = max(0.0, float(min_worst_risk_margin) - _worst_margin_with_fallback(plan))
    return float(ci_violation), float(rel_violation), float(worst_violation)


def _gate_margins(
    plan: PlanRecord,
    *,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> tuple[float, float, float]:
    ci_margin = 0.0
    if tau is not None:
        ci_margin = float(tau) - _ci_high_with_fallback(plan, tau)

    rel_margin = 0.0
    if min_reliability is not None:
        rel_margin = _reliability_with_fallback(plan) - float(min_reliability)

    worst_margin = 0.0
    if min_worst_risk_margin is not None:
        worst_margin = _worst_margin_with_fallback(plan) - float(min_worst_risk_margin)
    return float(ci_margin), float(rel_margin), float(worst_margin)


def _gate_total_violation(
    plan: PlanRecord,
    *,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> float:
    ci_v, rel_v, worst_v = _gate_violations(
        plan,
        tau=tau,
        min_reliability=min_reliability,
        min_worst_risk_margin=min_worst_risk_margin,
    )
    return float(ci_v + rel_v + worst_v)


def _normalize_denied_weights(raw: dict | None) -> dict[str, float]:
    raw = raw or {}
    defaults = {
        "ci": 0.45,
        "reliability": 0.30,
        "worst_margin": 0.20,
        "cost": 0.03,
        "sparsity": 0.02,
        "nominal_margin": 0.20,
        "reliability_margin_bonus": 0.20,
        "worst_margin_bonus": 0.10,
        "short_term": 0.15,
    }
    return {k: max(0.0, _safe_float(raw.get(k, v), v)) for k, v in defaults.items()}


def _normalize_high_risk_weights(raw: dict | None) -> dict[str, float]:
    raw = raw or {}
    defaults = {
        "pd_improvement": 0.55,
        "gate_pass": 0.20,
        "residual_pd": 0.25,
        "ci": 0.35,
        "reliability": 0.20,
        "worst_margin": 0.20,
        "cost": 0.03,
        "sparsity": 0.02,
        "short_term": 0.20,
    }
    return {k: max(0.0, _safe_float(raw.get(k, v), v)) for k, v in defaults.items()}


def _denied_priority_score(
    plan: PlanRecord,
    *,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
    denied_objective_cfg: dict | None,
) -> float:
    denied_objective_cfg = denied_objective_cfg or {}
    weights = _normalize_denied_weights(denied_objective_cfg.get("weights", {}))
    short_term_signal = _short_term_action_signal(
        plan,
        denied_objective_cfg.get("short_term", {})
        if isinstance(denied_objective_cfg.get("short_term", {}), dict)
        else {},
    )
    squared = bool(denied_objective_cfg.get("squared_violation", True))
    exponent = 2 if squared else 1
    penalty_scale = max(0.0, _safe_float(denied_objective_cfg.get("penalty_scale", 140.0), 140.0))

    ci_v, rel_v, worst_v = _gate_violations(
        plan,
        tau=tau,
        min_reliability=min_reliability,
        min_worst_risk_margin=min_worst_risk_margin,
    )
    loss = (
        (weights["ci"] * (ci_v**exponent))
        + (weights["reliability"] * (rel_v**exponent))
        + (weights["worst_margin"] * (worst_v**exponent))
        + (weights["cost"] * _plan_cost(plan) * 0.001)
        + (weights["sparsity"] * float(len(plan.actions)))
    )
    nominal_margin = 0.0
    if tau is not None and plan.predicted_pd is not None:
        nominal_margin = max(0.0, float(tau) - float(plan.predicted_pd))
    bonus = weights["nominal_margin"] * nominal_margin
    rel_margin = 0.0
    if min_reliability is not None and plan.reliability is not None:
        rel_margin = max(0.0, float(plan.reliability) - float(min_reliability))
    worst_margin = 0.0
    if min_worst_risk_margin is not None and plan.robust_worst_risk_margin is not None:
        worst_margin = max(0.0, float(plan.robust_worst_risk_margin) - float(min_worst_risk_margin))
    bonus += (weights["reliability_margin_bonus"] * rel_margin) + (weights["worst_margin_bonus"] * worst_margin)
    bonus += weights["short_term"] * short_term_signal
    pass_bonus = 10.0 if plan.status == "APPROVED" else 0.0
    return float(pass_bonus + (bonus * 100.0) - (loss * penalty_scale))


def _high_risk_priority_score(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
    high_risk_objective_cfg: dict | None,
) -> float:
    high_risk_objective_cfg = high_risk_objective_cfg or {}
    weights = _normalize_high_risk_weights(high_risk_objective_cfg.get("weights", {}))
    short_term_signal = _short_term_action_signal(
        plan,
        high_risk_objective_cfg.get("short_term", {})
        if isinstance(high_risk_objective_cfg.get("short_term", {}), dict)
        else {},
    )
    penalty_scale = max(0.0, _safe_float(high_risk_objective_cfg.get("penalty_scale", 80.0), 80.0))
    hard_gate = bool(high_risk_objective_cfg.get("hard_gate", True))
    hard_violation_penalty = max(0.0, _safe_float(high_risk_objective_cfg.get("hard_violation_penalty", 120.0), 120.0))

    pd_improvement = 0.0
    if base_pd is not None and plan.predicted_pd is not None:
        pd_improvement = max(0.0, float(base_pd) - float(plan.predicted_pd))

    residual_pd = 0.0
    if tau is not None and plan.predicted_pd is not None:
        residual_pd = max(0.0, float(plan.predicted_pd) - float(tau))

    ci_margin = 0.0
    rel_margin = 0.0
    worst_margin = 0.0
    ci_v = 0.0
    rel_v = 0.0
    worst_v = 0.0

    if tau is not None:
        ci_h = _ci_high_with_fallback(plan, tau)
        ci_margin = float(tau) - ci_h
        ci_v = max(0.0, ci_h - float(tau))
    if min_reliability is not None:
        rel = _reliability_with_fallback(plan)
        rel_margin = rel - float(min_reliability)
        rel_v = max(0.0, float(min_reliability) - rel)
    if min_worst_risk_margin is not None:
        worst = _worst_margin_with_fallback(plan)
        worst_margin = worst - float(min_worst_risk_margin)
        worst_v = max(0.0, float(min_worst_risk_margin) - worst)

    gate_pass = float((0.6 * ci_margin) + (0.25 * rel_margin) + (0.15 * worst_margin))
    violation = (
        (weights["ci"] * ci_v)
        + (weights["reliability"] * rel_v)
        + (weights["worst_margin"] * worst_v)
    )
    cost_pen = (weights["cost"] * _plan_cost(plan) * 0.001) + (weights["sparsity"] * float(len(plan.actions)))

    score = (
        (weights["pd_improvement"] * pd_improvement * 100.0)
        + (weights["gate_pass"] * gate_pass * 100.0)
        + (weights["short_term"] * short_term_signal * 100.0)
        - (weights["residual_pd"] * residual_pd * 100.0)
        - (penalty_scale * violation)
        - cost_pen
    )
    if hard_gate and (ci_v > 0.0 or rel_v > 0.0 or worst_v > 0.0):
        score -= float(hard_violation_penalty * (1.0 + ci_v + rel_v + worst_v))
    elif hard_gate:
        score += float(hard_violation_penalty * 0.05)
    if plan.status == "APPROVED":
        score += 20.0
    return float(score)


def _denied_sort_key(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
    denied_objective_cfg: dict[str, Any] | None,
    fairness_penalty: float = 0.0,
) -> tuple:
    fairness_cfg = (
        denied_objective_cfg.get("fairness_balance", {})
        if isinstance((denied_objective_cfg or {}).get("fairness_balance", {}), dict)
        else {}
    )
    fairness_enabled = bool(fairness_cfg.get("enabled", False))
    fairness_penalty_threshold = max(0.0, _safe_float(fairness_cfg.get("penalty_threshold", 0.01), 0.01))
    advantaged_cost_scale = max(0.0, _safe_float(fairness_cfg.get("advantaged_cost_scale", 0.50), 0.50))
    disadvantaged_gate_bonus = max(0.0, _safe_float(fairness_cfg.get("disadvantaged_gate_bonus", 0.20), 0.20))
    ci_margin, rel_margin, worst_margin = _gate_margins(
        plan,
        tau=tau,
        min_reliability=min_reliability,
        min_worst_risk_margin=min_worst_risk_margin,
    )
    base_priority = _denied_priority_score(
        plan,
        tau=tau,
        min_reliability=min_reliability,
        min_worst_risk_margin=min_worst_risk_margin,
        denied_objective_cfg=denied_objective_cfg,
    )
    if fairness_enabled:
        if float(fairness_penalty) > fairness_penalty_threshold:
            base_priority -= float(fairness_penalty) * advantaged_cost_scale * (_plan_cost(plan) * 0.01)
        else:
            base_priority += disadvantaged_gate_bonus * max(
                0.0,
                _gate_pass_score(
                    plan,
                    tau=tau,
                    min_reliability=min_reliability,
                    min_worst_risk_margin=min_worst_risk_margin,
                ),
            ) * 10.0
    return (
        _constraint_priority(plan),
        _status_priority(plan.status),
        _gate_total_violation(
            plan,
            tau=tau,
            min_reliability=min_reliability,
            min_worst_risk_margin=min_worst_risk_margin,
        ),
        -ci_margin,
        -rel_margin,
        -worst_margin,
        -_safe_float(getattr(plan, "trajectory_policy_score", 0.0), 0.0),
        -_expected_pd_improvement(plan, base_pd=base_pd, tau=tau),
        -_plan_execution_probability(plan),
        int(len(plan.actions)),
        _plan_cost(plan),
        plan.predicted_pd or 1.0,
        -float(base_priority),
    )


def _high_risk_sort_key(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
    high_risk_objective_cfg: dict[str, Any] | None,
    fairness_penalty: float = 0.0,
    denied_objective_cfg: dict[str, Any] | None = None,
) -> tuple:
    fairness_cfg = (
        denied_objective_cfg.get("fairness_balance", {})
        if isinstance((denied_objective_cfg or {}).get("fairness_balance", {}), dict)
        else {}
    )
    fairness_enabled = bool(fairness_cfg.get("enabled", False))
    fairness_penalty_threshold = max(0.0, _safe_float(fairness_cfg.get("penalty_threshold", 0.01), 0.01))
    advantaged_cost_scale = max(0.0, _safe_float(fairness_cfg.get("advantaged_cost_scale", 0.50), 0.50))
    disadvantaged_gate_bonus = max(0.0, _safe_float(fairness_cfg.get("disadvantaged_gate_bonus", 0.20), 0.20))

    high_violation = 0.0
    if tau is not None:
        high_violation += max(0.0, _ci_high_with_fallback(plan, tau) - float(tau))
    if min_reliability is not None:
        high_violation += max(0.0, float(min_reliability) - _reliability_with_fallback(plan))
    if min_worst_risk_margin is not None:
        high_violation += max(0.0, float(min_worst_risk_margin) - _worst_margin_with_fallback(plan))
    base_priority = _high_risk_priority_score(
        plan,
        base_pd=base_pd,
        tau=tau,
        min_reliability=min_reliability,
        min_worst_risk_margin=min_worst_risk_margin,
        high_risk_objective_cfg=high_risk_objective_cfg,
    )
    if fairness_enabled:
        if float(fairness_penalty) > fairness_penalty_threshold:
            base_priority -= float(fairness_penalty) * advantaged_cost_scale * (_plan_cost(plan) * 0.01)
        else:
            base_priority += disadvantaged_gate_bonus * max(
                0.0,
                _gate_pass_score(
                    plan,
                    tau=tau,
                    min_reliability=min_reliability,
                    min_worst_risk_margin=min_worst_risk_margin,
                ),
            ) * 10.0
    return (
        _constraint_priority(plan),
        _status_priority(plan.status),
        float(high_violation),
        -_safe_float(getattr(plan, "trajectory_policy_score", 0.0), 0.0),
        -_expected_pd_improvement(plan, base_pd=base_pd, tau=tau),
        -_plan_execution_probability(plan),
        -float(base_priority),
        int(len(plan.actions)),
        _plan_cost(plan),
        plan.predicted_pd or 1.0,
    )


def choose_best_plan(
    plans: list[PlanRecord],
    *,
    base_pd: float | None = None,
    tau: float | None = None,
    min_reliability: float | None = None,
    min_worst_risk_margin: float | None = None,
    fairness_penalty: float = 0.0,
    denied_mode: bool = False,
    segment_context: dict[str, Any] | None = None,
    denied_objective_cfg: dict[str, Any] | None = None,
) -> PlanRecord:
    if not plans:
        raise ValueError("No plans provided")
    for plan in plans:
        _annotate_trajectory_policy(
            plan,
            base_pd=base_pd,
            tau=tau,
            segment_context=segment_context,
        )
    candidates = _prefer_non_rejected(_prefer_constraint_eligible(plans))

    # fairness_penalty remains part of generator scoring, but plan selection
    # enforces a deterministic user-facing tie-break rule.
    _ = max(0.0, _safe_float(fairness_penalty, 0.0))
    denied_enabled = bool((denied_objective_cfg or {}).get("enabled", False))
    high_risk_cfg = (
        (denied_objective_cfg or {}).get("high_risk_objective", {})
        if isinstance((denied_objective_cfg or {}).get("high_risk_objective", {}), dict)
        else {}
    )
    high_risk_enabled = bool(high_risk_cfg.get("enabled", False))
    risk_band = str((segment_context or {}).get("risk_band", "")).strip().lower()
    is_denied_base = bool(base_pd is not None and tau is not None and float(base_pd) > float(tau))
    if denied_enabled and high_risk_enabled and risk_band == "high" and is_denied_base:
        return sorted(
            candidates,
            key=lambda p: _high_risk_sort_key(
                p,
                base_pd=base_pd,
                tau=tau,
                min_reliability=min_reliability,
                min_worst_risk_margin=min_worst_risk_margin,
                high_risk_objective_cfg=high_risk_cfg,
                fairness_penalty=float(fairness_penalty),
                denied_objective_cfg=denied_objective_cfg,
            ),
        )[0]

    if denied_mode and denied_enabled:
        return sorted(
            candidates,
            key=lambda p: _denied_sort_key(
                p,
                base_pd=base_pd,
                tau=tau,
                min_reliability=min_reliability,
                min_worst_risk_margin=min_worst_risk_margin,
                denied_objective_cfg=denied_objective_cfg,
                fairness_penalty=float(fairness_penalty),
            ),
        )[0]

    return sorted(
        candidates,
        key=lambda p: (
            _constraint_priority(p),
            _status_priority(p.status),
            -_gate_pass_score(
                p,
                tau=tau,
                min_reliability=min_reliability,
                min_worst_risk_margin=min_worst_risk_margin,
            ),
            -_safe_float(getattr(p, "trajectory_policy_score", 0.0), 0.0),
            -_expected_pd_improvement(p, base_pd=base_pd, tau=tau),
            -_plan_execution_probability(p),
            int(len(p.actions)),
            _plan_cost(p),
            p.predicted_pd or 1.0,
            -(p.robust_score if p.robust_score is not None else (p.score or -1e9)),
        ),
    )[0]
