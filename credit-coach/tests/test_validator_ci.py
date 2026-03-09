from __future__ import annotations

from credit_coach.data.schema import PlanAction, PlanRecord
from credit_coach.safety.validator import validate_plan


def test_validator_sets_status():
    plan = PlanRecord(
        plan_id="p1",
        customer_id="c1",
        run_id="r1",
        horizon_months=3,
        strategy="balanced",
        actions=[
            PlanAction(
                feature_name="dti",
                current_value=30.0,
                target_value=28.0,
                delta=-2.0,
                time_months=3,
                estimated_cost_usd=100.0,
            )
        ],
        predicted_pd=0.2,
    )

    out = validate_plan(plan, tau=0.35, alpha=0.05, bootstrap_b=100)
    assert out.status in {"APPROVED", "NEEDS_REVIEW", "REJECTED"}
    assert out.ci_high is not None
    assert out.reliability is not None


def test_validator_applies_segment_uncertainty_profile():
    base_plan = PlanRecord(
        plan_id="p2",
        customer_id="c1",
        run_id="r1",
        horizon_months=3,
        strategy="balanced",
        actions=[
            PlanAction(
                feature_name="dti",
                current_value=30.0,
                target_value=28.0,
                delta=-2.0,
                time_months=3,
                estimated_cost_usd=100.0,
            )
        ],
        predicted_pd=0.25,
    )
    uncertainty_cfg = {
        "primary_method": "conformal",
        "conformal": {
            "residual_quantile": 0.04,
            "min_width": 0.01,
        },
        "profiles": {
            "near": {"width_multiplier": 1.0, "alpha_multiplier": 1.0},
            "high": {"width_multiplier": 1.5, "alpha_multiplier": 1.0},
        },
    }
    near = validate_plan(
        base_plan.model_copy(deep=True),
        tau=0.35,
        alpha=0.05,
        bootstrap_b=100,
        uncertainty_cfg=uncertainty_cfg,
        segment_context={"risk_band": "near", "denied_mode": True},
    )
    high = validate_plan(
        base_plan.model_copy(deep=True),
        tau=0.35,
        alpha=0.05,
        bootstrap_b=100,
        uncertainty_cfg=uncertainty_cfg,
        segment_context={"risk_band": "high", "denied_mode": True},
    )
    near_width = float(near.ci_high - near.ci_low)
    high_width = float(high.ci_high - high.ci_low)
    assert high_width > near_width


def test_validator_reliability_soft_mode_can_relax_hard_boundary_cases():
    base_plan = PlanRecord(
        plan_id="p3",
        customer_id="c1",
        run_id="r1",
        horizon_months=3,
        strategy="balanced",
        actions=[
            PlanAction(
                feature_name="dti",
                current_value=25.0,
                target_value=24.0,
                delta=-1.0,
                time_months=3,
                estimated_cost_usd=50.0,
            )
        ],
        predicted_pd=0.01,
    )
    scenarios = [
        {"name": "extreme", "changes": {"interest_rate": 200.0}},
        {"name": "base", "changes": {}},
    ]

    hard_out = validate_plan(
        base_plan.model_copy(deep=True),
        tau=0.35,
        alpha=0.05,
        bootstrap_b=100,
        scenarios=scenarios,
        min_reliability=0.60,
    )
    soft_out = validate_plan(
        base_plan.model_copy(deep=True),
        tau=0.35,
        alpha=0.05,
        bootstrap_b=100,
        scenarios=scenarios,
        min_reliability=0.60,
        uncertainty_cfg={
            "reliability_gate_mode": "soft",
            "reliability_soft_scale": 0.2,
        },
    )

    assert hard_out.status == "NEEDS_REVIEW"
    assert soft_out.reliability is not None
    assert float(soft_out.reliability) > float(hard_out.reliability or 0.0)


def test_validator_applies_risk_band_reliability_profile_override():
    base_plan = PlanRecord(
        plan_id="p4",
        customer_id="c1",
        run_id="r1",
        horizon_months=3,
        strategy="balanced",
        actions=[
            PlanAction(
                feature_name="dti",
                current_value=25.0,
                target_value=24.0,
                delta=-1.0,
                time_months=3,
                estimated_cost_usd=50.0,
            )
        ],
        predicted_pd=0.70,
    )
    out = validate_plan(
        base_plan,
        tau=0.35,
        alpha=0.05,
        bootstrap_b=100,
        scenarios=[{"name": "base", "changes": {}}],
        min_reliability=0.60,
        uncertainty_cfg={
            "reliability_gate_mode": "blend",
            "reliability_soft_weight": 1.0,
            "reliability_soft_scale": 0.20,
            "reliability_profiles": {
                "high": {"min_reliability": 0.01, "soft_weight": 1.0, "soft_scale": 0.20}
            },
        },
        segment_context={"risk_band": "high", "denied_mode": True},
    )
    assert out.reliability is not None
    assert float(out.reliability) > 0.0
