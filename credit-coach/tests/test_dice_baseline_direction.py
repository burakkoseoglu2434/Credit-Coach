from __future__ import annotations

import pandas as pd

from credit_coach.recourse.dice_baseline import _heuristic_actions


def test_heuristic_actions_respect_feature_direction() -> None:
    row = pd.Series(
        {
            "annual_inc": 50000.0,
            "dti": 20.0,
            "revol_util": 45.0,
        }
    )
    actions = _heuristic_actions(
        row=row,
        actionable_features=["annual_inc", "dti", "revol_util"],
        max_actions=3,
    )
    by_feat = {a["feature_name"]: a for a in actions}
    assert by_feat["annual_inc"]["target_value"] > by_feat["annual_inc"]["current_value"]
    assert by_feat["dti"]["target_value"] < by_feat["dti"]["current_value"]
    assert by_feat["revol_util"]["target_value"] < by_feat["revol_util"]["current_value"]


def test_heuristic_actions_applies_action_budget() -> None:
    row = pd.Series({"annual_inc": 50000.0, "dti": 20.0})
    actions = _heuristic_actions(
        row=row,
        actionable_features=["annual_inc", "dti"],
        max_actions=1,
    )
    assert len(actions) == 1
