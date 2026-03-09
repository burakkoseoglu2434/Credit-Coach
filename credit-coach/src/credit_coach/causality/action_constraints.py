from __future__ import annotations

from credit_coach.causality.graph_utils import get_parents


def causal_penalty(actions: list[dict], graph: dict, penalty_weight: float = 0.3) -> float:
    acted = {a.get("feature_name") for a in actions}
    penalty = 0.0
    for action in actions:
        feature = action.get("feature_name")
        parents = get_parents(graph, feature)
        if parents and not any(p in acted for p in parents):
            penalty += penalty_weight
    return float(penalty)
