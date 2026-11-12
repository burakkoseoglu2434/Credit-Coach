"""E2 yardımcıları: ağırlıklı SMD, bootstrap adımı, test kilidi (sentetik veri)."""

import numpy as np

from credit_coach.ecom import e2_criteo as e2
from credit_coach.ecom import uplift as U


def test_weighted_smd_unit_weights_matches_formula():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(1000, 2)).astype(np.float32)
    t = rng.integers(0, 2, 1000)
    got = e2.weighted_smd(x, t, np.ones(1000))
    a, b = x[t == 1, 0].astype(float), x[t == 0, 0].astype(float)
    want = (a.mean() - b.mean()) / np.sqrt((a.var() + b.var()) / 2)
    assert np.isclose(got[0], want)


def test_weighting_removes_constructed_imbalance():
    rng = np.random.default_rng(1)
    x = rng.normal(size=(20000, 1))
    ps = 1 / (1 + np.exp(-x[:, 0]))
    t = (rng.random(20000) < ps).astype(int)
    w = np.where(t == 1, 1 / ps, 1 / (1 - ps))
    raw = abs(e2.weighted_smd(x, t, np.ones(20000))[0])
    adj = abs(e2.weighted_smd(x, t, w)[0])
    assert raw > 0.5 and adj < 0.05


def test_boot_iteration_returns_all_metrics():
    rng = np.random.default_rng(2)
    n = 2000
    y, t, tau = rng.integers(0, 2, n).astype(float), rng.integers(0, 2, n), rng.normal(size=n)
    rid = np.arange(n)
    order = U.rank_order(tau, rid)
    out, pol = e2.boot_iteration(
        {"T": tau},
        {"T": order},
        {"T": U.decile_of(order)},
        y,
        t,
        np.ones(n),
        [(np.ones(n), 0.001)],
        0.5,
        y,
    )
    q, s, g, fark = out["T"]
    assert np.isfinite([q, s, g]).all() and fark.shape == (10,)
    assert len(pol) == 1


def test_criteo_test_run_refuses_when_lock_exists(tmp_path, monkeypatch):
    lock = tmp_path / "test_run_criteo.lock"
    lock.write_text("{}")
    monkeypatch.setattr(e2, "LOCK_PATH", lock)
    assert e2.cmd_test() == 1
