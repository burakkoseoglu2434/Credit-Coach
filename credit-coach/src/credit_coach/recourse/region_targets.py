from __future__ import annotations


def get_target_pd(strategy: str, tau: float) -> float:
    strategy = strategy.lower()
    if strategy == "conservative":
        return max(tau - 0.02, 0.01)
    if strategy == "aggressive":
        return max(tau - 0.10, 0.01)
    return max(tau - 0.05, 0.01)
