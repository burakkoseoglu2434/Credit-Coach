from __future__ import annotations


def classify_progress(delta_p: float, improving_threshold: float = -0.02, stagnant_threshold: float = 0.02) -> str:
    if delta_p < improving_threshold:
        return "improving"
    if delta_p <= stagnant_threshold:
        return "stagnant"
    return "deteriorating"
