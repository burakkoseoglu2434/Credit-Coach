from __future__ import annotations

from credit_coach.coaching.loop import run_weekly_coaching_loop
from credit_coach.coaching.reviewer import evaluate_replan


def test_sequential_loop_replan_on_missed_actions():
    out = run_weekly_coaching_loop(
        base_pd=0.32,
        tau=0.35,
        weeks=4,
        macro_shock_week=0,
        plan_action_count=6,
        action_dropout_prob=1.0,  # force misses
        random_state=42,
        max_missed_actions=1,
    )
    assert len(out) == 4
    assert int(out["replan"].sum()) >= 1
    assert int(out["missed_action"].sum()) == 4
    assert "missed_actions_streak" in out.columns
    assert "replan_reasons" in out.columns


def test_evaluate_replan_with_robust_margin_gate():
    replan, reasons = evaluate_replan(
        progress_label="stagnant",
        ci_high=0.30,
        tau=0.35,
        missed_actions_streak=0,
        robust_margin=-0.10,
        min_robust_margin=-0.05,
    )
    assert replan is True
    assert "robust_margin_below_gate" in reasons

