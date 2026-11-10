import numpy as np
import pytest
from sklearn.metrics import brier_score_loss

from credit_coach.calibration import (
    ece,
    fit_platt,
    fit_venn_abers,
    predict_interval,
    predict_platt,
)
from tests.test_features import CSV

MODEL = CSV.parents[3] / "backend/.models/pd_monotone.json"
CAL = CSV.parents[3] / "backend/.models/venn_abers.joblib"


def _miscalibrated(n=6000, seed=0):
    rng = np.random.default_rng(seed)
    true_p = rng.beta(1.5, 8, n)
    y = (rng.random(n) < true_p).astype(int)
    score = np.clip(true_p**0.6, 0, 1)  # systematically over-predicts
    return score, y


def test_intervals_are_valid():
    s, y = _miscalibrated()
    va = fit_venn_abers(s[:3000], y[:3000])
    low, high, point = predict_interval(va, s[3000:])
    assert ((0 <= low) & (low <= high) & (high <= 1)).all()
    assert ((low <= point) & (point <= high)).all()


def test_intervals_valid_for_extreme_scores():
    s, y = _miscalibrated()
    va = fit_venn_abers(s, y)
    low, high, _ = predict_interval(va, np.array([0.0, 1.0, 0.5, 1e-9, 1 - 1e-9]))
    assert ((0 <= low) & (low <= high) & (high <= 1)).all()


def test_calibration_improves_brier_and_ece_out_of_sample():
    s, y = _miscalibrated()
    va = fit_venn_abers(s[:3000], y[:3000])
    _, _, point = predict_interval(va, s[3000:])
    platt = predict_platt(fit_platt(s[:3000], y[:3000]), s[3000:])
    raw_b = brier_score_loss(y[3000:], s[3000:])
    assert brier_score_loss(y[3000:], point) < raw_b
    assert brier_score_loss(y[3000:], platt) < raw_b
    assert ece(point, y[3000:]) < ece(s[3000:], y[3000:])


def test_more_calibration_data_gives_narrower_intervals():
    s, y = _miscalibrated(n=12000)
    grid = np.linspace(0.05, 0.6, 50)
    w = []
    for n in (300, 6000):
        low, high, _ = predict_interval(fit_venn_abers(s[:n], y[:n]), grid)
        w.append((high - low).mean())
    assert w[1] < w[0]


def test_ece_zero_for_perfect_calibration():
    p = np.repeat([0.2, 0.8], 5000)
    y = np.r_[np.tile([1, 0, 0, 0, 0], 1000), np.tile([1, 1, 1, 1, 0], 1000)]
    assert ece(p, y) == pytest.approx(0.0, abs=1e-9)
