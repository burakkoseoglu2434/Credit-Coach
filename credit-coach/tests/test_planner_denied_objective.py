from __future__ import annotations

from credit_coach.coaching.planner import choose_best_plan
from credit_coach.data.schema import PlanAction, PlanRecord, TrajectoryCheckpoint


def _mk_plan(
    plan_id: str,
    *,
    ci_high: float,
    reliability: float,
    worst_margin: float,
    predicted_pd: float,
    robust_score: float,
    status: str = "NEEDS_REVIEW",
    constraint_status: str = "valid",
    time_months: int = 3,
) -> PlanRecord:
    p = PlanRecord(
        plan_id=plan_id,
        customer_id="c1",
        run_id="r1",
        horizon_months=6,
        strategy="balanced",
        actions=[
            PlanAction(
                feature_name="dti",
                current_value=30.0,
                target_value=28.0,
                delta=-2.0,
                time_months=int(time_months),
                estimated_cost_usd=50.0,
            )
        ],
        predicted_pd=predicted_pd,
        robust_score=robust_score,
        score=robust_score,
        constraint_status=constraint_status,
        status=status,
    )
    p.ci_high = ci_high
    p.reliability = reliability
    p.robust_worst_risk_margin = worst_margin
    p.plan_execution_probability = 0.5
    p.nominal_pd_improvement = max(0.0, 0.60 - predicted_pd)
    p.expected_pd_improvement = float(p.plan_execution_probability * p.nominal_pd_improvement)
    return p


def _checkpoint(
    *,
    week: int,
    phase_id: str,
    checkpoint_type: str,
    predicted_pd: float,
    gate_pass_estimate: int,
    checkpoint_priority: int,
    status: str,
) -> TrajectoryCheckpoint:
    return TrajectoryCheckpoint(
        week=week,
        month={4: 1, 12: 3, 24: 6}[week],
        phase_id=phase_id,
        checkpoint_type=checkpoint_type,
        checkpoint_label=f"{week}w_{checkpoint_type}",
        predicted_pd=predicted_pd,
        pd_delta_vs_base=max(0.0, 0.60 - predicted_pd),
        gate_pass_estimate=gate_pass_estimate,
        checkpoint_priority=checkpoint_priority,
        status=status,
    )


def test_choose_best_plan_denied_mode_prefers_lower_gate_violations():
    better_gate = _mk_plan(
        "p_better_gate",
        ci_high=0.36,
        reliability=0.68,
        worst_margin=-0.08,
        predicted_pd=0.34,
        robust_score=5.0,
    )
    higher_raw_score = _mk_plan(
        "p_higher_raw_score",
        ci_high=0.45,
        reliability=0.40,
        worst_margin=-0.20,
        predicted_pd=0.30,
        robust_score=999.0,
    )

    best = choose_best_plan(
        [higher_raw_score, better_gate],
        tau=0.35,
        min_reliability=0.70,
        min_worst_risk_margin=-0.05,
        denied_mode=True,
        denied_objective_cfg={
            "enabled": True,
            "penalty_scale": 120.0,
            "squared_violation": True,
            "weights": {
                "ci": 0.5,
                "reliability": 0.3,
                "worst_margin": 0.2,
                "cost": 0.0,
                "sparsity": 0.0,
                "nominal_margin": 0.0,
            },
        },
    )
    assert best.plan_id == "p_better_gate"


def test_choose_best_plan_denied_mode_still_prioritizes_approved():
    approved = _mk_plan(
        "p_approved",
        ci_high=0.30,
        reliability=0.80,
        worst_margin=0.01,
        predicted_pd=0.29,
        robust_score=1.0,
        status="APPROVED",
    )
    needs_review = _mk_plan(
        "p_review",
        ci_high=0.33,
        reliability=0.78,
        worst_margin=-0.01,
        predicted_pd=0.30,
        robust_score=100.0,
        status="NEEDS_REVIEW",
    )

    best = choose_best_plan(
        [needs_review, approved],
        tau=0.35,
        min_reliability=0.70,
        min_worst_risk_margin=-0.05,
        denied_mode=True,
        denied_objective_cfg={"enabled": True},
    )
    assert best.plan_id == "p_approved"


def test_choose_best_plan_high_risk_objective_prefers_larger_pd_improvement():
    weaker = _mk_plan(
        "p_weaker",
        ci_high=0.92,
        reliability=0.10,
        worst_margin=-0.70,
        predicted_pd=0.84,
        robust_score=99.0,
        status="NEEDS_REVIEW",
    )
    stronger = _mk_plan(
        "p_stronger",
        ci_high=0.70,
        reliability=0.20,
        worst_margin=-0.50,
        predicted_pd=0.58,
        robust_score=1.0,
        status="NEEDS_REVIEW",
    )

    best = choose_best_plan(
        [weaker, stronger],
        base_pd=0.90,
        tau=0.35,
        min_reliability=0.60,
        min_worst_risk_margin=-0.10,
        denied_mode=True,
        segment_context={"risk_band": "high"},
        denied_objective_cfg={
            "enabled": True,
            "high_risk_objective": {
                "enabled": True,
                "penalty_scale": 80.0,
                "weights": {
                    "pd_improvement": 0.65,
                    "gate_pass": 0.10,
                    "residual_pd": 0.25,
                },
            },
        },
    )
    assert best.plan_id == "p_stronger"


def test_choose_best_plan_high_risk_objective_works_without_denied_mode_flag():
    weaker = _mk_plan(
        "p_weaker",
        ci_high=0.95,
        reliability=0.10,
        worst_margin=-0.80,
        predicted_pd=0.90,
        robust_score=20.0,
        status="NEEDS_REVIEW",
    )
    stronger = _mk_plan(
        "p_stronger",
        ci_high=0.80,
        reliability=0.15,
        worst_margin=-0.60,
        predicted_pd=0.70,
        robust_score=1.0,
        status="NEEDS_REVIEW",
    )
    best = choose_best_plan(
        [weaker, stronger],
        base_pd=0.95,
        tau=0.35,
        min_reliability=0.60,
        min_worst_risk_margin=-0.10,
        denied_mode=False,
        segment_context={"risk_band": "high"},
        denied_objective_cfg={
            "enabled": True,
            "high_risk_objective": {"enabled": True},
        },
    )
    assert best.plan_id == "p_stronger"


def test_choose_best_plan_high_risk_objective_penalizes_missing_gate_fields():
    missing = _mk_plan(
        "p_missing",
        ci_high=0.40,
        reliability=0.70,
        worst_margin=-0.05,
        predicted_pd=0.30,
        robust_score=500.0,
        status="NEEDS_REVIEW",
    )
    missing.ci_high = None
    missing.reliability = None
    missing.robust_worst_risk_margin = None

    complete = _mk_plan(
        "p_complete",
        ci_high=0.42,
        reliability=0.65,
        worst_margin=-0.08,
        predicted_pd=0.33,
        robust_score=1.0,
        status="NEEDS_REVIEW",
    )

    best = choose_best_plan(
        [missing, complete],
        base_pd=0.90,
        tau=0.35,
        min_reliability=0.60,
        min_worst_risk_margin=-0.10,
        denied_mode=True,
        segment_context={"risk_band": "high"},
        denied_objective_cfg={
            "enabled": True,
            "high_risk_objective": {"enabled": True},
        },
    )
    assert best.plan_id == "p_complete"


def test_choose_best_plan_prefers_checkpoint_safe_trajectory_story():
    strong_early = _mk_plan(
        "p_strong_early",
        ci_high=0.34,
        reliability=0.78,
        worst_margin=-0.02,
        predicted_pd=0.30,
        robust_score=5.0,
        status="NEEDS_REVIEW",
        time_months=1,
    )
    strong_early.trajectory_checkpoints = [
        _checkpoint(
            week=4,
            phase_id="phase_1_stabilize",
            checkpoint_type="primary",
            predicted_pd=0.34,
            gate_pass_estimate=1,
            checkpoint_priority=1,
            status="on_track",
        ),
        _checkpoint(
            week=12,
            phase_id="phase_2_build",
            checkpoint_type="confirmation",
            predicted_pd=0.32,
            gate_pass_estimate=1,
            checkpoint_priority=2,
            status="on_track",
        ),
        _checkpoint(
            week=24,
            phase_id="phase_3_optimize",
            checkpoint_type="stability",
            predicted_pd=0.30,
            gate_pass_estimate=1,
            checkpoint_priority=3,
            status="on_track",
        ),
    ]
    strong_early.plan_execution_probability = 0.72
    strong_early.expected_pd_improvement = float(
        strong_early.plan_execution_probability * strong_early.nominal_pd_improvement
    )

    late_heavy = _mk_plan(
        "p_late_heavy",
        ci_high=0.31,
        reliability=0.75,
        worst_margin=-0.01,
        predicted_pd=0.28,
        robust_score=8.0,
        status="NEEDS_REVIEW",
        time_months=6,
    )
    late_heavy.trajectory_checkpoints = [
        _checkpoint(
            week=4,
            phase_id="phase_1_stabilize",
            checkpoint_type="primary",
            predicted_pd=0.48,
            gate_pass_estimate=0,
            checkpoint_priority=1,
            status="at_risk",
        ),
        _checkpoint(
            week=12,
            phase_id="phase_2_build",
            checkpoint_type="confirmation",
            predicted_pd=0.36,
            gate_pass_estimate=0,
            checkpoint_priority=2,
            status="at_risk",
        ),
        _checkpoint(
            week=24,
            phase_id="phase_3_optimize",
            checkpoint_type="stability",
            predicted_pd=0.28,
            gate_pass_estimate=1,
            checkpoint_priority=3,
            status="on_track",
        ),
    ]
    late_heavy.plan_execution_probability = 0.32
    late_heavy.expected_pd_improvement = float(
        late_heavy.plan_execution_probability * late_heavy.nominal_pd_improvement
    )

    best = choose_best_plan(
        [late_heavy, strong_early],
        base_pd=0.60,
        tau=0.35,
        segment_context={"risk_band": "mid"},
    )

    assert best.plan_id == "p_strong_early"
    assert late_heavy.trajectory_policy_label == "long_horizon_heavy"


def test_choose_best_plan_prefers_non_rejected_when_available():
    rejected = _mk_plan(
        "p_rejected",
        ci_high=0.20,
        reliability=0.95,
        worst_margin=0.10,
        predicted_pd=0.20,
        robust_score=999.0,
        status="REJECTED",
    )
    needs_review = _mk_plan(
        "p_needs_review",
        ci_high=0.42,
        reliability=0.65,
        worst_margin=-0.08,
        predicted_pd=0.34,
        robust_score=1.0,
        status="NEEDS_REVIEW",
    )

    best = choose_best_plan(
        [rejected, needs_review],
        tau=0.35,
        min_reliability=0.60,
        min_worst_risk_margin=-0.10,
        denied_mode=True,
        denied_objective_cfg={"enabled": True},
    )
    assert best.plan_id == "p_needs_review"


def test_choose_best_plan_prefers_stabilize_first_over_long_horizon_heavy_when_gates_match():
    stabilize_first = _mk_plan(
        "p_stabilize_first",
        ci_high=0.34,
        reliability=0.75,
        worst_margin=-0.02,
        predicted_pd=0.30,
        robust_score=2.0,
        time_months=1,
    )
    long_horizon = _mk_plan(
        "p_long_horizon",
        ci_high=0.34,
        reliability=0.75,
        worst_margin=-0.02,
        predicted_pd=0.28,
        robust_score=100.0,
        time_months=6,
    )

    best = choose_best_plan(
        [long_horizon, stabilize_first],
        base_pd=0.60,
        tau=0.35,
        min_reliability=0.70,
        min_worst_risk_margin=-0.05,
    )

    assert best.plan_id == "p_stabilize_first"
    assert best.trajectory_policy_label == "stabilize_first"
    assert long_horizon.trajectory_policy_label in {"balanced_progress", "long_horizon_heavy"}


def test_choose_best_plan_denied_mode_prefers_phase1_when_short_term_enabled():
    slower = _mk_plan(
        "p_slow",
        ci_high=0.40,
        reliability=0.72,
        worst_margin=-0.03,
        predicted_pd=0.31,
        robust_score=10.0,
        time_months=3,
    )
    faster = _mk_plan(
        "p_fast",
        ci_high=0.40,
        reliability=0.72,
        worst_margin=-0.03,
        predicted_pd=0.31,
        robust_score=10.0,
        time_months=1,
    )

    best = choose_best_plan(
        [slower, faster],
        tau=0.35,
        min_reliability=0.70,
        min_worst_risk_margin=-0.05,
        denied_mode=True,
        denied_objective_cfg={
            "enabled": True,
            "weights": {
                "ci": 0.5,
                "reliability": 0.3,
                "worst_margin": 0.2,
                "cost": 0.0,
                "sparsity": 0.0,
                "nominal_margin": 0.2,
                "short_term": 0.8,
            },
            "short_term": {
                "enabled": True,
                "phase1_cutoff_month": 1,
                "phase2_cutoff_month": 3,
            },
        },
    )
    assert best.plan_id == "p_fast"


def test_choose_best_plan_prefers_non_provisional_constraint_status_when_scores_match():
    provisional = _mk_plan(
        "p_provisional",
        ci_high=0.34,
        reliability=0.78,
        worst_margin=-0.02,
        predicted_pd=0.30,
        robust_score=50.0,
        status="NEEDS_REVIEW",
        constraint_status="provisional",
    )
    valid = _mk_plan(
        "p_valid",
        ci_high=0.34,
        reliability=0.78,
        worst_margin=-0.02,
        predicted_pd=0.30,
        robust_score=50.0,
        status="NEEDS_REVIEW",
        constraint_status="valid",
    )

    best = choose_best_plan(
        [provisional, valid],
        tau=0.35,
        min_reliability=0.70,
        min_worst_risk_margin=-0.05,
        denied_mode=True,
        denied_objective_cfg={"enabled": True},
    )
    assert best.plan_id == "p_valid"


def test_choose_best_plan_uses_expected_pd_improvement_after_gate_filters():
    lower_expected = _mk_plan(
        "p_lower_expected",
        ci_high=0.34,
        reliability=0.78,
        worst_margin=-0.02,
        predicted_pd=0.30,
        robust_score=50.0,
        status="NEEDS_REVIEW",
    )
    lower_expected.plan_execution_probability = 0.25
    lower_expected.nominal_pd_improvement = 0.05
    lower_expected.expected_pd_improvement = 0.0125

    higher_expected = _mk_plan(
        "p_higher_expected",
        ci_high=0.34,
        reliability=0.78,
        worst_margin=-0.02,
        predicted_pd=0.30,
        robust_score=50.0,
        status="NEEDS_REVIEW",
    )
    higher_expected.plan_execution_probability = 0.80
    higher_expected.nominal_pd_improvement = 0.05
    higher_expected.expected_pd_improvement = 0.04

    best = choose_best_plan(
        [lower_expected, higher_expected],
        base_pd=0.35,
        tau=0.35,
        min_reliability=0.70,
        min_worst_risk_margin=-0.05,
        denied_mode=True,
        denied_objective_cfg={"enabled": True},
    )
    assert best.plan_id == "p_higher_expected"


def test_choose_best_plan_high_risk_uses_execution_probability_as_non_blocking_tiebreak():
    lower_probability = _mk_plan(
        "p_lower_probability",
        ci_high=0.60,
        reliability=0.62,
        worst_margin=-0.04,
        predicted_pd=0.58,
        robust_score=10.0,
        status="NEEDS_REVIEW",
    )
    higher_probability = _mk_plan(
        "p_higher_probability",
        ci_high=0.60,
        reliability=0.62,
        worst_margin=-0.04,
        predicted_pd=0.58,
        robust_score=10.0,
        status="NEEDS_REVIEW",
    )
    lower_probability.plan_execution_probability = 0.25
    lower_probability.nominal_pd_improvement = 0.32
    lower_probability.expected_pd_improvement = 0.08
    higher_probability.plan_execution_probability = 0.75
    higher_probability.nominal_pd_improvement = 0.32
    higher_probability.expected_pd_improvement = 0.24

    best = choose_best_plan(
        [lower_probability, higher_probability],
        base_pd=0.90,
        tau=0.35,
        min_reliability=0.60,
        min_worst_risk_margin=-0.10,
        denied_mode=True,
        segment_context={"risk_band": "high"},
        denied_objective_cfg={
            "enabled": True,
            "high_risk_objective": {"enabled": True},
        },
    )
    assert best.plan_id == "p_higher_probability"


def test_choose_best_plan_prefers_execution_aware_truth_over_nominal_only_upside():
    higher_nominal = _mk_plan(
        "p_higher_nominal",
        ci_high=0.34,
        reliability=0.78,
        worst_margin=-0.02,
        predicted_pd=0.28,
        robust_score=20.0,
        status="NEEDS_REVIEW",
    )
    higher_nominal.plan_execution_probability = 0.20
    higher_nominal.nominal_pd_improvement = 0.12
    higher_nominal.expected_pd_improvement = 0.024

    more_defensible = _mk_plan(
        "p_more_defensible",
        ci_high=0.34,
        reliability=0.78,
        worst_margin=-0.02,
        predicted_pd=0.31,
        robust_score=20.0,
        status="NEEDS_REVIEW",
    )
    more_defensible.plan_execution_probability = 0.72
    more_defensible.nominal_pd_improvement = 0.06
    more_defensible.expected_pd_improvement = 0.0432

    best = choose_best_plan(
        [higher_nominal, more_defensible],
        base_pd=0.40,
        tau=0.35,
        min_reliability=0.70,
        min_worst_risk_margin=-0.05,
        denied_mode=True,
        denied_objective_cfg={"enabled": True},
    )
    assert best.plan_id == "p_more_defensible"


def test_choose_best_plan_high_risk_penalizes_provisional_contenders_hard() -> None:
    provisional = _mk_plan(
        "p_provisional",
        ci_high=0.58,
        reliability=0.64,
        worst_margin=-0.05,
        predicted_pd=0.57,
        robust_score=5.0,
        status="NEEDS_REVIEW",
        constraint_status="provisional",
    )
    provisional.plan_execution_probability = 0.74
    provisional.nominal_pd_improvement = 0.28
    provisional.expected_pd_improvement = 0.2072
    provisional.approval_pending_action_count = 1
    provisional.approval_dependent_plan_probability = 0.32

    valid = _mk_plan(
        "p_valid",
        ci_high=0.58,
        reliability=0.64,
        worst_margin=-0.05,
        predicted_pd=0.59,
        robust_score=5.0,
        status="NEEDS_REVIEW",
        constraint_status="valid",
    )
    valid.plan_execution_probability = 0.63
    valid.nominal_pd_improvement = 0.24
    valid.expected_pd_improvement = 0.1512

    best = choose_best_plan(
        [provisional, valid],
        base_pd=0.90,
        tau=0.35,
        min_reliability=0.60,
        min_worst_risk_margin=-0.10,
        denied_mode=True,
        segment_context={"risk_band": "high"},
        denied_objective_cfg={
            "enabled": True,
            "high_risk_objective": {"enabled": True},
        },
    )
    assert best.plan_id == "p_valid"
