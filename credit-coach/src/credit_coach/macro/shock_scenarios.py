from __future__ import annotations


def scenario_pd_shift(scenario: dict) -> float:
    changes = scenario.get("changes", {})
    shift = 0.0
    shift += 0.002 * abs(float(changes.get("interest_rate", 0.0)))
    shift += 0.003 * abs(float(changes.get("unemployment_rate", 0.0)))
    shift += 0.0015 * abs(float(changes.get("inflation_rate", 0.0)))
    shift += 0.0025 * abs(float(changes.get("credit_spread", 0.0)))
    shift += 0.002 * abs(float(changes.get("gdp_growth", 0.0)))
    return float(shift)
