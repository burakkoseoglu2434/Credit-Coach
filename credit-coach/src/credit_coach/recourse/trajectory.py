from __future__ import annotations

from typing import Any, Iterable

import pandas as pd

from credit_coach.data.schema import PlanAction, PlanRecord, TrajectoryCheckpoint, TrajectoryPhase
from credit_coach.model.predict import predict_proba_pd

CANONICAL_CHECKPOINT_WEEKS: tuple[int, int, int] = (4, 12, 24)
TRAJECTORY_MINOR_DRIFT_TOLERANCE = 0.01
TRAJECTORY_JUMP_THRESHOLD = 0.03

PHASE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "phase_id": "phase_1_stabilize",
        "phase_title": "0-4 Hafta - Stabilizasyon",
        "target_window_weeks": "1-4",
        "target_window_months": [1],
        "review_week": 4,
        "checkpoint_month": 1,
        "checkpoint_type": "primary",
        "checkpoint_label": "4w_primary",
        "target_ratio": 0.45,
    },
    {
        "phase_id": "phase_2_build",
        "phase_title": "1-3 Ay - Guclendirme",
        "target_window_weeks": "5-12",
        "target_window_months": [2, 3],
        "review_week": 12,
        "checkpoint_month": 3,
        "checkpoint_type": "confirmation",
        "checkpoint_label": "12w_confirmation",
        "target_ratio": 0.75,
    },
    {
        "phase_id": "phase_3_optimize",
        "phase_title": "3-6 Ay - Optimizasyon",
        "target_window_weeks": "13-24",
        "target_window_months": [4, 5, 6],
        "review_week": 24,
        "checkpoint_month": 6,
        "checkpoint_type": "stability",
        "checkpoint_label": "24w_stability",
        "target_ratio": 1.00,
    },
)

_PHASE_SPEC_BY_ID = {str(spec["phase_id"]): spec for spec in PHASE_SPECS}


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


def list_phase_specs() -> tuple[dict[str, Any], ...]:
    return PHASE_SPECS


def phase_id_for_month(month: int) -> str:
    m = max(1, int(month))
    if m <= 1:
        return "phase_1_stabilize"
    if m <= 3:
        return "phase_2_build"
    return "phase_3_optimize"


def phase_title(phase_id: str) -> str:
    spec = _PHASE_SPEC_BY_ID.get(str(phase_id))
    return str(spec["phase_title"]) if spec else str(phase_id)


def phase_review_week(phase_id: str) -> int:
    spec = _PHASE_SPEC_BY_ID.get(str(phase_id))
    return int(spec["review_week"]) if spec else 24


def phase_window_weeks(phase_id: str) -> str:
    spec = _PHASE_SPEC_BY_ID.get(str(phase_id))
    return str(spec["target_window_weeks"]) if spec else ""


def phase_window_months(phase_id: str) -> list[int]:
    spec = _PHASE_SPEC_BY_ID.get(str(phase_id))
    if not spec:
        return []
    return [int(month) for month in spec.get("target_window_months", [])]


def checkpoint_type_for_week(week: int) -> str:
    spec = next((item for item in PHASE_SPECS if int(item["review_week"]) == int(week)), None)
    if spec is None:
        raise ValueError(f"Unsupported canonical checkpoint week: {week}")
    return str(spec["checkpoint_type"])


def resolve_action_phase_id(action: PlanAction) -> str:
    phase_id = str(getattr(action, "phase_id", "") or "").strip()
    if phase_id in _PHASE_SPEC_BY_ID:
        return phase_id
    return phase_id_for_month(_safe_int(getattr(action, "time_months", 1), 1))


def ordered_actions(actions: Iterable[PlanAction]) -> list[PlanAction]:
    return sorted(
        list(actions),
        key=lambda action: (
            max(1, _safe_int(getattr(action, "time_months", 1), 1)),
            str(getattr(action, "feature_name", "") or ""),
        ),
    )


def build_canonical_phases(
    actions: Iterable[PlanAction],
    *,
    base_pd: float | None = None,
    predicted_pd: float | None = None,
    tau: float | None = None,
) -> list[TrajectoryPhase]:
    ordered = ordered_actions(actions)
    nominal_improvement = max(0.0, _safe_float(base_pd, 0.0) - _safe_float(predicted_pd, _safe_float(base_pd, 0.0)))
    phases: list[TrajectoryPhase] = []
    for spec in PHASE_SPECS:
        phase_id = str(spec["phase_id"])
        steps: list[PlanAction] = []
        for action in ordered:
            resolved_phase_id = resolve_action_phase_id(action)
            if resolved_phase_id != phase_id:
                continue
            if str(getattr(action, "phase_id", "") or "") != phase_id:
                action = action.model_copy(update={"phase_id": phase_id})
            steps.append(action)
        target_pd = None
        if predicted_pd is not None and base_pd is not None:
            target_pd = max(
                float(predicted_pd),
                float(base_pd) - (nominal_improvement * float(spec.get("target_ratio", 1.0))),
            )
        elif predicted_pd is not None:
            target_pd = float(predicted_pd)
        gate_pass_target = bool(target_pd is not None and tau is not None and float(target_pd) <= float(tau))
        phases.append(
            TrajectoryPhase(
                phase_id=phase_id,
                phase_title=str(spec["phase_title"]),
                target_window_weeks=str(spec["target_window_weeks"]),
                target_window_months=[int(month) for month in spec["target_window_months"]],
                review_week=int(spec["review_week"]),
                target_pd=target_pd,
                gate_pass_target=gate_pass_target,
                steps=list(steps),
            )
        )
    return phases


def apply_plan_until_month(
    row: pd.Series,
    plan: PlanRecord,
    *,
    month: int,
) -> pd.Series:
    m = max(1, int(month))
    x = row.copy()
    for action in ordered_actions(plan.actions):
        feature = str(getattr(action, "feature_name", "") or "").strip()
        if not feature or feature not in x.index:
            continue
        action_month = max(1, _safe_int(getattr(action, "time_months", m), m))
        if action_month > m:
            continue
        try:
            x[feature] = float(getattr(action, "target_value"))
        except Exception:
            continue
    return x


def predict_plan_pd_at_month(
    *,
    row: pd.Series,
    plan: PlanRecord,
    month: int,
    model: Any,
    calibrator: Any,
    feature_cols: list[str],
) -> float:
    x_m = apply_plan_until_month(row, plan, month=month)
    x_input = pd.DataFrame([x_m[feature_cols].values], columns=feature_cols)
    return float(predict_proba_pd(model, calibrator, x_input)[0])


def build_nominal_trajectory_checkpoints(
    *,
    row: pd.Series,
    plan: PlanRecord,
    base_pd: float,
    tau: float,
    model: Any,
    calibrator: Any,
    feature_cols: list[str],
) -> list[TrajectoryCheckpoint]:
    checkpoints: list[TrajectoryCheckpoint] = []
    for priority, spec in enumerate(PHASE_SPECS, start=1):
        month = int(spec["checkpoint_month"])
        predicted_pd = predict_plan_pd_at_month(
            row=row,
            plan=plan,
            month=month,
            model=model,
            calibrator=calibrator,
            feature_cols=feature_cols,
        )
        checkpoints.append(
            TrajectoryCheckpoint(
                week=int(spec["review_week"]),
                month=month,
                phase_id=str(spec["phase_id"]),
                checkpoint_type=str(spec["checkpoint_type"]),
                checkpoint_label=str(spec["checkpoint_label"]),
                predicted_pd=float(predicted_pd),
                pd_delta_vs_base=float(max(0.0, float(base_pd) - float(predicted_pd))),
                gate_pass_estimate=int(float(predicted_pd) <= float(tau)),
                checkpoint_priority=int(priority),
                status="at_risk",
            )
        )
    return finalize_trajectory_checkpoints(checkpoints, base_pd=base_pd, tau=tau)


def _expected_checkpoint_status(
    *,
    checkpoint: TrajectoryCheckpoint,
    base_pd: float,
    tau: float,
    previous_pd: float | None,
) -> str:
    predicted_pd = _safe_float(getattr(checkpoint, "predicted_pd", base_pd), base_pd)
    if predicted_pd <= float(tau) and int(getattr(checkpoint, "gate_pass_estimate", 0) or 0) == 1:
        return "on_track"
    if previous_pd is not None and predicted_pd > float(previous_pd) + TRAJECTORY_JUMP_THRESHOLD:
        return "missed"
    if predicted_pd > float(base_pd) + TRAJECTORY_MINOR_DRIFT_TOLERANCE:
        return "missed"
    return "at_risk"


def finalize_trajectory_checkpoints(
    checkpoints: Iterable[TrajectoryCheckpoint],
    *,
    base_pd: float,
    tau: float,
) -> list[TrajectoryCheckpoint]:
    finalized: list[TrajectoryCheckpoint] = []
    previous_pd = float(base_pd)
    for checkpoint in sorted(list(checkpoints), key=lambda item: int(getattr(item, "week", 0) or 0)):
        week = int(getattr(checkpoint, "week", 0) or 0)
        expected_type = checkpoint_type_for_week(week)
        expected_label = next(
            str(spec["checkpoint_label"])
            for spec in PHASE_SPECS
            if int(spec["review_week"]) == week
        )
        predicted_pd = _safe_float(getattr(checkpoint, "predicted_pd", base_pd), base_pd)
        non_monotonic_flag = bool(predicted_pd > float(previous_pd) + TRAJECTORY_MINOR_DRIFT_TOLERANCE)
        trajectory_jump_flag = bool(predicted_pd > float(previous_pd) + TRAJECTORY_JUMP_THRESHOLD)
        expected_status = _expected_checkpoint_status(
            checkpoint=checkpoint,
            base_pd=base_pd,
            tau=tau,
            previous_pd=previous_pd,
        )
        raw_status = str(getattr(checkpoint, "status", "") or "").strip()
        checkpoint_inconsistency_flag = bool(
            str(getattr(checkpoint, "checkpoint_type", "") or expected_type) != expected_type
            or str(getattr(checkpoint, "checkpoint_label", "") or expected_label) != expected_label
            or (raw_status not in {"", "at_risk"} and raw_status != expected_status)
        )
        finalized.append(
            checkpoint.model_copy(
                update={
                    "checkpoint_type": expected_type,
                    "checkpoint_label": expected_label,
                    "status": expected_status,
                    "trajectory_jump_flag": trajectory_jump_flag,
                    "non_monotonic_flag": non_monotonic_flag,
                    "checkpoint_inconsistency_flag": checkpoint_inconsistency_flag,
                }
            )
        )
        previous_pd = predicted_pd
    return finalized


def summarize_trajectory_consistency(checkpoints: Iterable[TrajectoryCheckpoint]) -> dict[str, Any]:
    ordered = sorted(list(checkpoints), key=lambda item: int(getattr(item, "week", 0) or 0))
    checkpoint_map = {
        int(getattr(item, "week", 0) or 0): item
        for item in ordered
    }
    primary = checkpoint_map.get(4)
    confirmation = checkpoint_map.get(12)
    stability = checkpoint_map.get(24)
    return {
        "primary_checkpoint_status": str(getattr(primary, "status", "missed") or "missed"),
        "confirmation_checkpoint_status": str(getattr(confirmation, "status", "missed") or "missed"),
        "stability_checkpoint_status": str(getattr(stability, "status", "missed") or "missed"),
        "weak_early_health": bool(str(getattr(primary, "status", "missed") or "missed") != "on_track"),
        "trajectory_jump_flag": bool(any(bool(getattr(item, "trajectory_jump_flag", False)) for item in ordered)),
        "non_monotonic_flag": bool(any(bool(getattr(item, "non_monotonic_flag", False)) for item in ordered)),
        "checkpoint_inconsistency_flag": bool(
            any(bool(getattr(item, "checkpoint_inconsistency_flag", False)) for item in ordered)
        ),
    }


def infer_initial_trajectory_state(checkpoints: Iterable[TrajectoryCheckpoint]) -> dict[str, Any]:
    _ = list(checkpoints)
    return {
        "trajectory_status": "on_track",
        "current_phase": "phase_1_stabilize",
        "next_review_week": 4,
        "phase_transition_reason": "initial_plan",
        "replanned_from_phase": None,
    }


def attach_canonical_trajectory(
    plan: PlanRecord,
    *,
    row: pd.Series,
    base_pd: float,
    tau: float,
    model: Any,
    calibrator: Any,
    feature_cols: list[str],
) -> PlanRecord:
    plan.phases = build_canonical_phases(
        plan.actions,
        base_pd=base_pd,
        predicted_pd=getattr(plan, "predicted_pd", None),
        tau=tau,
    )
    plan.trajectory_checkpoints = build_nominal_trajectory_checkpoints(
        row=row,
        plan=plan,
        base_pd=base_pd,
        tau=tau,
        model=model,
        calibrator=calibrator,
        feature_cols=feature_cols,
    )
    state = infer_initial_trajectory_state(plan.trajectory_checkpoints)
    plan.trajectory_status = str(state["trajectory_status"])
    plan.current_phase = str(state["current_phase"])
    plan.next_review_week = int(state["next_review_week"])
    plan.phase_transition_reason = str(state["phase_transition_reason"])
    plan.replanned_from_phase = state["replanned_from_phase"]
    return plan
