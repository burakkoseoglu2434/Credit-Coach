from __future__ import annotations

import pandas as pd

from credit_coach.macro.reliability import evaluate_reliability_from_pd


def run_shock_reliability(
    plans_df: pd.DataFrame,
    tau: float,
    scenarios: list[dict],
    threshold_shift_per_msi_unit: float = 0.0,
) -> pd.DataFrame:
    out = plans_df.copy()
    evaluated = out["predicted_pd"].apply(
        lambda p: evaluate_reliability_from_pd(
            base_pd=float(p),
            tau=tau,
            scenarios=scenarios,
            threshold_shift_per_msi_unit=threshold_shift_per_msi_unit,
        )
    )
    out["reliability"] = evaluated.apply(lambda v: v["reliability"])
    out["reliability_soft"] = evaluated.apply(lambda v: v.get("reliability_soft", v["reliability"]))
    out["worst_risk_margin"] = evaluated.apply(lambda v: v["worst_risk_margin"])
    out["avg_stressed_pd"] = evaluated.apply(lambda v: v["avg_stressed_pd"])
    out["worst_stressed_pd"] = evaluated.apply(lambda v: v["worst_stressed_pd"])
    return out
