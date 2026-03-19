from __future__ import annotations

import math

import numpy as np
import pandas as pd

from credit_coach.coaching.messaging import reason_codes
from credit_coach.coaching.progress import classify_progress
from credit_coach.coaching.reviewer import evaluate_replan
from credit_coach.macro.shock_scenarios import scenario_pd_shift
from credit_coach.recourse.execution_probability import classify_execution_scenario
from credit_coach.recourse.trajectory import (
    TRAJECTORY_JUMP_THRESHOLD,
    checkpoint_type_for_week,
)


def _default_shock_scenario() -> dict:
    return {"changes": {"interest_rate": 3.0, "unemployment_rate": 2.0}}


def _planned_actions_this_week(remaining_actions: int, weeks_left: int, max_weekly_actions: int) -> int:
    if remaining_actions <= 0:
        return 0
    plan = int(math.ceil(remaining_actions / max(1, weeks_left)))
    return int(max(1, min(max_weekly_actions, plan)))


def _phase_for_week(week: int) -> str:
    w = max(1, int(week))
    if w <= 4:
        return "phase_1_stabilize"
    if w <= 12:
        return "phase_2_build"
    return "phase_3_optimize"


def _next_review_week(week: int, review_weeks: tuple[int, ...]) -> int:
    w = max(1, int(week))
    for review_week in review_weeks:
        if w <= int(review_week):
            return int(review_week)
    return int(review_weeks[-1]) if review_weeks else w


def run_weekly_coaching_loop(
    base_pd: float,
    tau: float,
    weeks: int = 4,
    macro_shock_week: int = 3,
    improving_threshold: float = -0.02,
    stagnant_threshold: float = 0.02,
    *,
    plan_action_count: int = 6,
    target_pd: float | None = None,
    action_dropout_prob: float = 0.15,
    execution_noise_std: float = 0.003,
    action_effect_per_step: float = 0.005,
    ci_buffer: float = 0.02,
    random_state: int = 42,
    max_missed_actions: int = 2,
    status_deteriorating: bool = True,
    ci_exceed_tau: bool = True,
    missed_actions_enabled: bool = True,
    max_weekly_actions: int = 3,
    macro_shock_schedule: dict[int, dict] | None = None,
    min_robust_margin: float | None = None,
    scheduled_actions_by_week: dict[int, int] | None = None,
    review_weeks: tuple[int, ...] = (4, 12, 24),
    financial_inertia: float = 0.18,
) -> pd.DataFrame:
    """
    Sequential weekly coaching simulation.

    - Multi-step state transition (predicted_pd_t -> predicted_pd_{t+1})
    - Action execution model (dropout + noise)
    - Dynamic review/replan triggers
    """
    rng = np.random.default_rng(random_state)
    rows: list[dict] = []

    weeks = max(1, int(weeks))
    current_pd = float(max(0.0, min(1.0, base_pd)))
    adaptive_target = float(max(0.0, min(1.0, target_pd if target_pd is not None else max(0.0, tau - 0.02))))
    remaining_actions = max(0, int(plan_action_count))
    missed_streak = 0
    review_weeks = tuple(sorted({max(1, int(week)) for week in review_weeks})) or (4, 12, 24)
    scheduled_actions_by_week = {
        max(1, int(week)): max(0, int(count))
        for week, count in (scheduled_actions_by_week or {}).items()
    }
    trajectory_status_state = "on_track"
    current_phase_state = "phase_1_stabilize"
    next_review_state = _next_review_week(1, review_weeks)
    phase_transition_reason_state = "initial_plan"
    replanned_from_phase_state: str | None = None

    for w in range(1, weeks + 1):
        weeks_left = weeks - w + 1
        planned_actions = int(scheduled_actions_by_week.get(w, 0))
        if planned_actions <= 0:
            planned_actions = _planned_actions_this_week(remaining_actions, weeks_left, max_weekly_actions)
        planned_actions = int(min(max(0, planned_actions), max_weekly_actions, remaining_actions))
        phase_boundary_review = bool(w in review_weeks)
        phase_for_week = _phase_for_week(w)

        shock_scenario = None
        if macro_shock_schedule and w in macro_shock_schedule:
            shock_scenario = macro_shock_schedule[w]
        elif macro_shock_week > 0 and w == macro_shock_week:
            shock_scenario = _default_shock_scenario()

        shock_delta = float(scenario_pd_shift(shock_scenario)) if shock_scenario else 0.0

        missed_action = bool(planned_actions > 0 and rng.random() < float(max(0.0, min(1.0, action_dropout_prob))))
        executed_actions = 0 if missed_action else min(remaining_actions, planned_actions)
        if executed_actions > 0:
            remaining_actions = max(0, remaining_actions - executed_actions)

        target_pull = max(0.0, (current_pd - adaptive_target) / max(1, weeks_left))
        action_gain = float(executed_actions) * float(action_effect_per_step)
        inertia_dampener = max(0.20, 1.0 - (float(financial_inertia) * max(0.0, current_pd)))
        deterministic_improvement = (action_gain + (0.5 * target_pull)) * inertia_dampener
        noise = float(rng.normal(loc=0.0, scale=float(max(0.0, execution_noise_std))))

        next_pd = float(np.clip(current_pd - deterministic_improvement + shock_delta + noise, 0.0, 1.0))
        ci_high = float(min(1.0, next_pd + ci_buffer + (0.01 if missed_action else 0.0)))
        robust_margin = float(tau - (next_pd + max(0.0, shock_delta)))
        delta = float(next_pd - current_pd)
        label = classify_progress(delta, improving_threshold, stagnant_threshold)

        if missed_action:
            missed_streak += 1
        else:
            missed_streak = 0

        execution_scenario = classify_execution_scenario(
            float(executed_actions / max(1, planned_actions)) if planned_actions > 0 else 1.0
        )

        replan, replan_reasons = evaluate_replan(
            progress_label=label,
            ci_high=ci_high,
            tau=tau,
            missed_actions_streak=missed_streak,
            max_missed_actions=max_missed_actions,
            status_deteriorating=status_deteriorating,
            ci_exceed_tau=ci_exceed_tau,
            missed_actions_enabled=missed_actions_enabled,
            robust_margin=robust_margin,
            min_robust_margin=min_robust_margin,
        )

        checkpoint_type = checkpoint_type_for_week(w) if phase_boundary_review else ""
        severe_deterioration = bool(next_pd > current_pd + TRAJECTORY_JUMP_THRESHOLD)
        gate_pass = bool(next_pd <= float(tau))
        if gate_pass:
            checkpoint_status = "on_track"
        elif severe_deterioration or execution_scenario == "failed_execution":
            checkpoint_status = "missed"
        else:
            checkpoint_status = "at_risk"

        if replan and phase_boundary_review:
            # Hybrid transition model: adapt only at canonical review boundaries.
            adaptive_target = float(max(0.0, min(adaptive_target, next_pd - 0.01, tau - 0.01)))
            if remaining_actions > 0:
                remaining_actions = min(int(plan_action_count), remaining_actions + 1)
            degraded_boundary = bool(
                (
                    w > 4
                    and severe_deterioration
                )
                or (
                    checkpoint_status == "missed"
                    and execution_scenario == "failed_execution"
                    and w > 4
                    and missed_streak > int(max_missed_actions)
                )
            )
            trajectory_status_state = "degraded" if degraded_boundary else "needs_replan"
            current_phase_state = phase_for_week
            next_review_state = int(w)
            phase_transition_reason_state = "|".join(replan_reasons) if replan_reasons else "review_boundary_replan"
            replanned_from_phase_state = phase_for_week
        elif phase_boundary_review:
            trajectory_status_state = "on_track"
            current_phase_state = _phase_for_week(min(weeks, w + 1))
            next_review_state = _next_review_week(w + 1, review_weeks)
            phase_transition_reason_state = "checkpoint_clear"
            replanned_from_phase_state = None
        if w == weeks and execution_scenario == "failed_execution" and trajectory_status_state != "needs_replan":
            trajectory_status_state = "degraded"
            current_phase_state = phase_for_week
            next_review_state = int(review_weeks[-1])
            phase_transition_reason_state = "execution_failed"
            replanned_from_phase_state = None

        msg_codes = reason_codes(
            progress_label=label,
            replan=replan,
            ci_high=ci_high,
            tau=tau,
            replan_reasons=replan_reasons,
        )

        rows.append(
            {
                "week": w,
                "predicted_pd": next_pd,
                "ci_high": ci_high,
                "delta_p": delta,
                "progress": label,
                "replan": int(replan),
                "replan_reasons": "|".join(replan_reasons),
                "reason_codes": "|".join(msg_codes),
                "planned_actions": int(planned_actions),
                "executed_actions": int(executed_actions),
                "remaining_actions": int(remaining_actions),
                "missed_action": int(missed_action),
                "missed_actions_streak": int(missed_streak),
                "execution_rate": float(executed_actions / max(1, planned_actions)) if planned_actions > 0 else 1.0,
                "execution_scenario": execution_scenario,
                "shock_delta": shock_delta,
                "target_pd": adaptive_target,
                "robust_margin": robust_margin,
                "phase_boundary_review": int(phase_boundary_review),
                "checkpoint_type": str(checkpoint_type),
                "checkpoint_status": str(checkpoint_status),
                "current_phase": str(current_phase_state),
                "next_review_week": int(next_review_state),
                "trajectory_status": str(trajectory_status_state),
                "phase_transition_reason": str(phase_transition_reason_state),
                "replanned_from_phase": str(replanned_from_phase_state or ""),
            }
        )
        current_pd = next_pd

    return pd.DataFrame(rows)
