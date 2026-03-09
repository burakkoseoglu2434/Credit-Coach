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
