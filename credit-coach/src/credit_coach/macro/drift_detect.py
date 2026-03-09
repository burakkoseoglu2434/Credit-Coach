from __future__ import annotations

import numpy as np
import pandas as pd


def compute_psi(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    e = pd.to_numeric(expected, errors="coerce").dropna().values
    a = pd.to_numeric(actual, errors="coerce").dropna().values
    if len(e) == 0 or len(a) == 0:
        return 0.0

    quantiles = np.linspace(0, 1, bins + 1)
    cutpoints = np.quantile(e, quantiles)
    cutpoints[0] = -np.inf
    cutpoints[-1] = np.inf

    e_counts, _ = np.histogram(e, bins=cutpoints)
    a_counts, _ = np.histogram(a, bins=cutpoints)

    e_pct = e_counts / max(e_counts.sum(), 1)
    a_pct = a_counts / max(a_counts.sum(), 1)

    eps = 1e-6
    psi = np.sum((e_pct - a_pct) * np.log((e_pct + eps) / (a_pct + eps)))
    return float(psi)
