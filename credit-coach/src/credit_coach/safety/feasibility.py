from __future__ import annotations

from credit_coach.recourse.action_space import get_action_spec


def check_actions_feasible(actions: list[dict]) -> tuple[bool, str | None]:
    for a in actions:
        feature = a.get("feature_name")
        spec = get_action_spec(feature)
        if not spec.actionable:
            return False, f"{feature} is not actionable"

        current = a.get("current_value")
        target = a.get("target_value")
        if current is None or target is None:
            return False, f"{feature} has missing current/target"

        delta = target - current
        if spec.direction == "increase" and delta < 0:
            return False, f"{feature} direction violation: expected increase"
        if spec.direction == "decrease" and delta > 0:
            return False, f"{feature} direction violation: expected decrease"

        if spec.min_val is not None and target < spec.min_val:
            return False, f"{feature} below min bound"
        if spec.max_val is not None and target > spec.max_val:
            return False, f"{feature} above max bound"

    return True, None
