from __future__ import annotations

import numpy as np


def percentile_ci(values, alpha: float = 0.05) -> tuple[float, float]:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return 0.0, 0.0
    return float(np.quantile(arr, alpha / 2)), float(np.quantile(arr, 1 - alpha / 2))
