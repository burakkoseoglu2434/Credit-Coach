"""Venn-Abers PD intervals and a Platt comparison. Fit on the calibration split only."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from venn_abers import VennAbers

EPS = 1e-6


def _two_col(s: np.ndarray) -> np.ndarray:
    s = np.clip(np.asarray(s, dtype=float), 0.0, 1.0)
    return np.c_[1 - s, s]


def fit_venn_abers(scores: np.ndarray, y: np.ndarray) -> VennAbers:
    va = VennAbers()
    va.fit(_two_col(scores), np.asarray(y, dtype=int))
    return va


def predict_interval(
    va: VennAbers, scores: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (p_low, p_high, p_point) with 0 <= low <= point <= high <= 1."""
    point, p0p1 = va.predict_proba(_two_col(scores))
    low, high = p0p1[:, 0], p0p1[:, 1]
    low, high = np.clip(np.minimum(low, high), 0, 1), np.clip(np.maximum(low, high), 0, 1)
    point = np.clip(point[:, 1], low, high)
    return low, high, point


def fit_platt(scores: np.ndarray, y: np.ndarray) -> LogisticRegression:
    z = _logit(scores).reshape(-1, 1)
    return LogisticRegression(C=1e6, max_iter=1000).fit(z, np.asarray(y, dtype=int))


def predict_platt(platt: LogisticRegression, scores: np.ndarray) -> np.ndarray:
    return platt.predict_proba(_logit(scores).reshape(-1, 1))[:, 1]


def _logit(s: np.ndarray) -> np.ndarray:
    s = np.clip(np.asarray(s, dtype=float), EPS, 1 - EPS)
    return np.log(s / (1 - s))


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    """Expected calibration error with equal-frequency bins."""
    order = np.argsort(p, kind="stable")
    p, y = np.asarray(p)[order], np.asarray(y)[order]
    chunks = np.array_split(np.arange(len(p)), bins)
    return float(sum(len(i) / len(p) * abs(p[i].mean() - y[i].mean()) for i in chunks if len(i)))
