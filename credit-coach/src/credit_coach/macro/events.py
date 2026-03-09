from __future__ import annotations


def get_event_delta(event_name: str | None) -> dict[str, float]:
    if not event_name:
        return {"tau_shift": 0.0, "alpha_shift": 0.0}

    mapping = {
        "policy_tightening": {"tau_shift": -0.01, "alpha_shift": -0.01},
        "market_volatility": {"tau_shift": -0.02, "alpha_shift": -0.02},
        "none": {"tau_shift": 0.0, "alpha_shift": 0.0},
    }
    return mapping.get(event_name, mapping["none"])
