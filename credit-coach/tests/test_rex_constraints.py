from __future__ import annotations

import pandas as pd

from credit_coach.causality.action_constraints import causal_penalty
from credit_coach.causality.rex_runner import run_rex_adapter


def test_rex_runner_and_penalty(tmp_path):
    df = pd.DataFrame(
        {
            "a": [1, 2, 3, 4, 5],
            "b": [2, 4, 6, 8, 10],
            "c": [5, 4, 3, 2, 1],
        }
    )
    graph = run_rex_adapter(df, ["a", "b", "c"], min_edge_weight=0.1, output_path=tmp_path / "g.json")
    assert len(graph["nodes"]) == 3

    actions = [{"feature_name": "b"}]
    p = causal_penalty(actions, graph, penalty_weight=0.3)
    assert p >= 0.0
