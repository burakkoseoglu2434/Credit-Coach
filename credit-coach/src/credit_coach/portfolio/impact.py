from __future__ import annotations

import pandas as pd


def estimate_portfolio_pd_reduction(before_pd: pd.Series, after_pd: pd.Series) -> float:
    return float(before_pd.mean() - after_pd.mean())
