from __future__ import annotations

import numpy as np
import pandas as pd

from credit_coach.recourse.dice_baseline import generate_dice_counterfactual_actions


class DummyModel:
    def predict_proba(self, x):
        n = len(x)
        p = np.full(n, 0.4, dtype=float)
        return np.column_stack([1.0 - p, p])


def test_generate_dice_counterfactual_actions_fallback():
    train = pd.DataFrame(
        {
            "f1": [0.0, 1.0, 0.0, 1.0],
            "f2": [1.0, 0.0, 1.0, 0.0],
            "target": [0, 1, 0, 1],
        }
    )
    model = DummyModel()
    row = train.iloc[0]

    # Invalid target column intentionally forces fallback branch.
    action_sets, backend, telemetry = generate_dice_counterfactual_actions(
        row=row,
        feature_cols=["f1", "f2"],
        actionable_features=["f1", "f2"],
        model=model,
        calibrator=None,
        train_df=train,
        target_col="missing_target",
    )
    assert action_sets
    assert isinstance(action_sets[0], list)
    assert backend.startswith("heuristic_fallback")
    assert telemetry["fallback_reason"] == "missing_target_col"
