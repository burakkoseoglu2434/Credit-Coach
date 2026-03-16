from __future__ import annotations

from credit_coach.coaching.loop import run_weekly_coaching_loop
from credit_coach.coaching.reviewer import evaluate_replan
from credit_coach.recourse.execution_probability import classify_execution_scenario


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


def test_classify_execution_scenario_distinguishes_full_mixed_and_failed():
    assert classify_execution_scenario(1.0) == "full_execution"
    assert classify_execution_scenario(0.55) == "mixed_execution"
    assert classify_execution_scenario(0.10) == "failed_execution"


def test_weekly_loop_supports_mixed_execution_paths():
    out = run_weekly_coaching_loop(
        base_pd=0.48,
        tau=0.35,
        weeks=6,
        macro_shock_week=0,
        plan_action_count=6,
        action_dropout_prob=0.5,
        random_state=7,
    )
    mean_execution_rate = float(out["execution_rate"].mean())
    assert 0.0 < mean_execution_rate < 1.0
    assert classify_execution_scenario(mean_execution_rate) == "mixed_execution"


def test_weekly_loop_emits_phase_boundary_transition_state():
    out = run_weekly_coaching_loop(
        base_pd=0.52,
        tau=0.35,
        weeks=24,
        macro_shock_week=0,
        plan_action_count=6,
        action_dropout_prob=1.0,
        random_state=11,
        max_missed_actions=1,
        scheduled_actions_by_week={1: 2, 5: 2, 13: 2},
    )
    assert "trajectory_status" in out.columns
    assert "current_phase" in out.columns
    assert "next_review_week" in out.columns
    assert "phase_transition_reason" in out.columns
    week4 = out[out["week"] == 4].iloc[-1]
    assert str(week4["trajectory_status"]) == "needs_replan"
    assert str(week4["current_phase"]) == "phase_1_stabilize"
    assert int(week4["next_review_week"]) == 4
