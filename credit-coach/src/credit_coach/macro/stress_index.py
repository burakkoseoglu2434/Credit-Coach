from __future__ import annotations

from credit_coach.data.schema import MacroSnapshot


def _clip01(v: float) -> float:
    return max(0.0, min(1.0, v))


def compute_macro_stress_index(snapshot: MacroSnapshot, weights: dict[str, float]) -> float:
    # Lightweight normalization for demo range mapping.
    vals = {
        "interest_rate": snapshot.interest_rate / 100.0,
        "unemployment_rate": snapshot.unemployment_rate / 30.0,
        "gdp_growth": snapshot.gdp_growth / 10.0,
        "inflation_rate": snapshot.inflation_rate / 100.0,
        "credit_spread": snapshot.credit_spread / 20.0,
    }
    score = 0.0
    for k, w in weights.items():
        score += float(w) * float(vals.get(k, 0.0))
    return _clip01(score)
