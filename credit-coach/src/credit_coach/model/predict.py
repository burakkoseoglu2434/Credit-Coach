from __future__ import annotations

import numpy as np


def predict_proba_pd(model, calibrator, x):
    if calibrator is not None:
        return calibrator.predict_proba(x)[:, 1]
    return model.predict_proba(x)[:, 1]


def apply_threshold(proba, tau: float) -> np.ndarray:
    return (proba <= tau).astype(int)
