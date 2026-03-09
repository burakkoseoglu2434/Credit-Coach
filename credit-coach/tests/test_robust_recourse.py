from __future__ import annotations

import numpy as np
import pandas as pd

from credit_coach.data.schema import PlanAction, PlanRecord
from credit_coach.recourse.generator import PlanGenConfig, generate_plan_record
from credit_coach.safety.validator import validate_plan


class _DummyModel:
    def predict_proba(self, x):
        df = x if isinstance(x, pd.DataFrame) else pd.DataFrame(x)
        dti = pd.to_numeric(df.get("dti", pd.Series([20.0] * len(df))), errors="coerce").fillna(20.0)
        p = (0.15 + (dti / 200.0)).clip(0.01, 0.99).to_numpy()
        return np.column_stack([1.0 - p, p])


def test_generate_plan_record_with_robust_score():
    row = pd.Series(
        {
            "annual_inc": 60000.0,
            "dti": 28.0,
            "revol_bal": 12000.0,
            "verification_status": 1.0,
        }
    )
    scenarios = [
        {"name": "mild", "changes": {"interest_rate": 1.0}},
        {"name": "stress", "changes": {"interest_rate": 3.0, "unemployment_rate": 2.0}},
    ]

    plan = generate_plan_record(
        customer_id="c1",
        run_id="r1",
        row=row,
        model=_DummyModel(),
        calibrator=None,
        feature_cols=list(row.index),
        horizon_months=6,
        strategy="balanced",
        graph=None,
        cfg=PlanGenConfig(tau=0.35),
        candidate_features=["dti", "annual_inc", "revol_bal"],
        topk=3,
        scenarios=scenarios,
        threshold_shift_per_msi_unit=-0.02,
        robust_cfg={
            "enabled": True,
            "objective": "cvar",
            "cvar_quantile": 0.9,
            "weights": {"nominal_margin": 0.3, "reliability": 0.5, "robust_margin": 0.2},
        },
    )

    assert plan.robust_score is not None
    assert plan.score == plan.robust_score
    assert plan.robust_method == "cvar"
    assert plan.robust_anchor_pd is not None
    assert plan.robust_margin is not None
    assert plan.robust_worst_risk_margin is not None
    assert 0.0 <= float(plan.reliability or 0.0) <= 1.0


def test_validate_plan_reliability_gate():
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
        predicted_pd=0.34,
        score=10.0,
    )
    scenarios = [
        {"name": "stress1", "changes": {"interest_rate": 5.0, "unemployment_rate": 2.0}},
        {"name": "stress2", "changes": {"interest_rate": 4.0, "credit_spread": 2.0}},
    ]
    out = validate_plan(
        plan,
        tau=0.35,
        alpha=0.05,
        bootstrap_b=100,
        scenarios=scenarios,
        threshold_shift_per_msi_unit=-0.02,
        robust_objective="worst_case",
        min_reliability=1.0,
    )
    assert out.status == "NEEDS_REVIEW"
    assert out.status_reason is not None and "reliability" in out.status_reason
    assert out.robust_method == "worst_case"
    assert out.robust_anchor_pd is not None


def test_generate_plan_record_with_weekly_denied_optimizer():
    row = pd.Series(
        {
            "annual_inc": 52000.0,
            "dti": 32.0,
            "revol_bal": 14000.0,
            "verification_status": 1.0,
        }
    )
    scenarios = [
        {"name": "stress", "changes": {"interest_rate": 3.0, "unemployment_rate": 2.0}},
    ]
    plan = generate_plan_record(
        customer_id="c2",
        run_id="r2",
        row=row,
        model=_DummyModel(),
        calibrator=None,
        feature_cols=list(row.index),
        horizon_months=6,
        strategy="balanced",
        graph=None,
        cfg=PlanGenConfig(tau=0.35),
        candidate_features=["dti", "annual_inc", "revol_bal"],
        topk=3,
        scenarios=scenarios,
        threshold_shift_per_msi_unit=-0.02,
        robust_cfg={
            "enabled": True,
            "objective": "cvar",
            "cvar_quantile": 0.9,
            "min_reliability": 0.7,
            "min_worst_risk_margin": -0.05,
            "gate_objective": {
                "alpha": 0.05,
                "violation_weights": {"ci": 0.5, "reliability": 0.3, "worst_margin": 0.2},
            },
            "denied_objective": {
                "enabled": True,
                "only_denied": True,
                "weights": {
                    "ci": 0.5,
                    "reliability": 0.3,
                    "worst_margin": 0.2,
                    "cost": 0.0,
                    "sparsity": 0.0,
                    "nominal_margin": 0.1,
                },
            },
        },
        search_cfg={
            "denied_mode": True,
            "adaptive_steps": {"enabled": True},
            "weekly_optimizer": {
                "enabled": True,
                "only_denied": True,
                "weeks": 4,
                "max_weekly_actions": 2,
                "weekly_step_scale": 0.5,
                "min_weekly_improvement": 0.0,
                "optimize_for_gate": True,
                "objective_bootstrap_b": 40,
            },
        },
    )
    assert len(plan.actions) >= 1
    assert plan.robust_score is not None
