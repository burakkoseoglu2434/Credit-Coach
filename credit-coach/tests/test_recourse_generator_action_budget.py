from __future__ import annotations

import numpy as np
import pandas as pd

from credit_coach.recourse.generator import PlanGenConfig, generate_plan_record


class _DummyModel:
    def predict_proba(self, x):
        df = x if isinstance(x, pd.DataFrame) else pd.DataFrame(x)
        inc = pd.to_numeric(df.get("annual_inc", pd.Series([50000.0] * len(df))), errors="coerce").fillna(50000.0)
        p = (0.7 - (inc / 200000.0)).clip(0.05, 0.99).to_numpy()
        return np.column_stack([1.0 - p, p])


def test_action_budget_applies_after_noop_filtering() -> None:
    row = pd.Series(
        {
            "acc_now_delinq": 0.0,
            "annual_inc": 50000.0,
            "dti": 25.0,
        }
    )
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
        candidate_features=["acc_now_delinq", "annual_inc"],
        topk=2,
        robust_cfg={"enabled": False},
        search_cfg={
            "action_budget": {"enabled": True, "max_actions": 1},
            "min_abs_action_delta": 1e-6,
        },
    )
    assert len(plan.actions) == 1
    assert plan.actions[0].feature_name == "annual_inc"


def test_phase1_fast_track_forces_early_timing_and_larger_step() -> None:
    row = pd.Series(
        {
            "annual_inc": 50000.0,
            "dti": 25.0,
            "revol_util": 55.0,
        }
    )
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
        candidate_features=["dti"],
        topk=1,
        robust_cfg={"enabled": False},
        search_cfg={
            "denied_mode": True,
            "phase1_fast_track": {
                "enabled": True,
                "denied_only": True,
                "high_risk_only": False,
                "prioritized_features": ["dti"],
                "step_multiplier": 2.0,
                "force_phase1_month": True,
            },
        },
    )
    assert len(plan.actions) == 1
    action = plan.actions[0]
    assert action.feature_name == "dti"
    assert int(action.time_months) == 1
    assert float(action.delta) <= -2.0


def test_generate_plan_record_tracks_clipped_action_realism_diagnostics() -> None:
    row = pd.Series(
        {
            "annual_inc": 50_000.0,
            "dti": 25.0,
        }
    )
    runtime_diag: dict[str, object] = {}
    plan = generate_plan_record(
        customer_id="c3",
        run_id="r3",
        row=row,
        model=_DummyModel(),
        calibrator=None,
        feature_cols=list(row.index),
        horizon_months=6,
        strategy="balanced",
        graph=None,
        cfg=PlanGenConfig(tau=0.35),
        candidate_features=["annual_inc"],
        topk=1,
        robust_cfg={"enabled": False},
        runtime_diag=runtime_diag,
        search_cfg={
            "min_abs_action_delta": 1e-6,
        },
        feasibility_profile={
            "enabled": True,
            "features": {
                "annual_inc": {
                    "income_growth_cap": 0.01,
                }
            },
        },
    )
    assert len(plan.actions) == 1
    action = plan.actions[0]
    assert action.feature_name == "annual_inc"
    assert action.action_status == "clipped"
    assert "income_growth_cap" in action.diagnostic_flags
    assert int(runtime_diag["action_realism_clipped_action_count"]) == 1
    assert int(runtime_diag["action_realism_valid_action_count"]) == 0
    assert int(runtime_diag["action_realism_rejected_action_count"]) == 0
    events = runtime_diag["action_realism_events"]
    assert isinstance(events, list)
    assert len(events) == 1
    assert events[0]["status"] == "clipped"


def test_generate_plan_record_marks_infeasible_when_only_action_is_rejected() -> None:
    row = pd.Series(
        {
            "annual_inc": 24_000.0,
            "revol_bal": 12_000.0,
        }
    )
    runtime_diag: dict[str, object] = {}
    plan = generate_plan_record(
        customer_id="c4",
        run_id="r4",
        row=row,
        model=_DummyModel(),
        calibrator=None,
        feature_cols=list(row.index),
        horizon_months=6,
        strategy="aggressive",
        graph=None,
        cfg=PlanGenConfig(tau=0.35),
        candidate_features=["revol_bal"],
        topk=1,
        robust_cfg={"enabled": False},
        runtime_diag=runtime_diag,
        search_cfg={
            "min_abs_action_delta": 1e-6,
        },
        feasibility_profile={
            "enabled": True,
            "features": {
                "revol_bal": {
                    "financial_capacity_ratio": 0.01,
                }
            },
        },
    )
    assert plan.actions == []
    assert int(runtime_diag["action_realism_rejected_action_count"]) == 1
    assert int(runtime_diag["action_realism_infeasible_plan_count"]) == 1
    events = runtime_diag["action_realism_events"]
    assert isinstance(events, list)
    assert len(events) == 1
    assert events[0]["status"] == "rejected"
    assert "financial_capacity_ratio" in events[0]["reason_codes"]
