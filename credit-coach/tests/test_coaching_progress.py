from __future__ import annotations

from credit_coach.coaching.loop import run_weekly_coaching_loop
from credit_coach.coaching.progress import classify_progress


def test_progress_labels():
    assert classify_progress(-0.03) == "improving"
    assert classify_progress(0.0) == "stagnant"
    assert classify_progress(0.05) == "deteriorating"


def test_weekly_loop_output():
    out = run_weekly_coaching_loop(
        base_pd=0.4,
        tau=0.35,
        weeks=4,
        macro_shock_week=3,
        random_state=7,
        action_dropout_prob=0.0,
    )
    assert len(out) == 4
    assert "replan" in out.columns
    assert {"planned_actions", "executed_actions", "remaining_actions", "execution_rate"}.issubset(out.columns)
