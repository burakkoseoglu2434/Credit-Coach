from __future__ import annotations

import pandas as pd

from credit_coach.recourse.dice_baseline import _heuristic_actions


def test_heuristic_actions_respect_feature_direction() -> None:
    row = pd.Series(
        {
            "loan_amnt": 12000.0,
            "installment": 420.0,
            "verification_status": 1.0,
        }
    )
    actions = _heuristic_actions(
        row=row,
        actionable_features=["loan_amnt", "installment", "verification_status"],
        max_actions=3,
    )
    by_feat = {a["feature_name"]: a for a in actions}
    assert by_feat["loan_amnt"]["target_value"] < by_feat["loan_amnt"]["current_value"]
    assert by_feat["installment"]["target_value"] < by_feat["installment"]["current_value"]
    assert by_feat["verification_status"]["target_value"] > by_feat["verification_status"]["current_value"]


def test_heuristic_actions_snap_term_to_supported_month_buckets() -> None:
    row = pd.Series({"term": 60.0})
    actions = _heuristic_actions(
        row=row,
        actionable_features=["term"],
        max_actions=1,
    )
    assert len(actions) == 1
    assert actions[0]["target_value"] == 36.0


def test_heuristic_actions_applies_action_budget() -> None:
    row = pd.Series({"loan_amnt": 12000.0, "installment": 420.0})
    actions = _heuristic_actions(
        row=row,
        actionable_features=["loan_amnt", "installment"],
        max_actions=1,
    )
    assert len(actions) == 1
