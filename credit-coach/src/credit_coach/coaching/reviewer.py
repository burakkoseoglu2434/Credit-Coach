from __future__ import annotations


def evaluate_replan(
    progress_label: str,
    ci_high: float,
    tau: float,
    missed_actions_streak: int,
    *,
    max_missed_actions: int = 2,
    status_deteriorating: bool = True,
    ci_exceed_tau: bool = True,
    missed_actions_enabled: bool = True,
    robust_margin: float | None = None,
    min_robust_margin: float | None = None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if status_deteriorating and progress_label == "deteriorating":
        reasons.append("deteriorating_progress")

    if ci_exceed_tau and ci_high > tau:
        reasons.append("ci_exceeds_tau")

    if missed_actions_enabled and missed_actions_streak >= max_missed_actions:
        reasons.append("missed_actions_streak")

    if robust_margin is not None and min_robust_margin is not None and float(robust_margin) < float(min_robust_margin):
        reasons.append("robust_margin_below_gate")

    return len(reasons) > 0, reasons


def needs_replan(
    progress_label: str,
    ci_high: float,
    tau: float,
    missed_actions_streak: int,
    max_missed_actions: int = 2,
) -> bool:
    """
    Backward-compatible bool API.
    """
    replan, _ = evaluate_replan(
        progress_label=progress_label,
        ci_high=ci_high,
        tau=tau,
        missed_actions_streak=missed_actions_streak,
        max_missed_actions=max_missed_actions,
    )
    return replan

