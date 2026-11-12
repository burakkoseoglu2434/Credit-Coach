"""E1 yardımcıları: bölme, Qini, eğim, politika değeri, belirlenimcilik, test kilidi."""

import numpy as np

from credit_coach.ecom import e1_hillstrom as e1
from credit_coach.ecom import uplift as U


def test_stratified_split_is_deterministic_and_keeps_strata_shares():
    rng = np.random.default_rng(0)
    strata = rng.integers(0, 4, 10_000)
    a, b = U.stratified_split(strata), U.stratified_split(strata)
    assert U.split_hash(a) == U.split_hash(b)
    assert U.split_hash(a) != U.split_hash(U.stratified_split(strata, seed=1))
    for s in range(4):
        lab = a[strata == s]
        shares = np.bincount(lab, minlength=3) / len(lab)
        assert np.allclose(shares, U.FRACS, atol=0.001)


def _synthetic(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 3))
    t = rng.integers(0, 2, n)
    effect = 0.3 * (x[:, 0] > 0)
    y = (rng.random(n) < 0.2 + effect * t).astype(float)
    return x, t, y, effect


def test_qini_rewards_correct_ranking():
    x, t, y, effect = _synthetic()
    rid, w = np.arange(len(y)), np.ones(len(y))
    good = U.qini(U.rank_order(effect, rid), y, t, w)[0]
    bad = U.qini(U.rank_order(-effect, rid), y, t, w)[0]
    assert good > 0 > bad


def test_tau_is_bit_identical_across_runs_for_both_families():
    x, t, y, _ = _synthetic()
    for aile in ("T", "TO"):
        cfg = U.Config(aile, 0.1, 7, 50)
        a = U.fit_predict_tau(cfg, x, y, t, 0.5, x, binary=True)
        b = U.fit_predict_tau(cfg, x, y, t, 0.5, x, binary=True)
        assert np.array_equal(a.view(np.uint64), b.view(np.uint64))


def test_calibration_slope_and_overall_gap():
    tab = {"tau_hat": np.arange(10.0), "tau_obs": 2 * np.arange(10.0) + 1, "boyut": np.ones(10)}
    assert np.isclose(U.calibration_slope(tab), 2.0)
    y, t, w = np.array([1.0, 0.0, 1.0, 1.0]), np.array([1, 1, 0, 0]), np.ones(4)
    assert np.isclose(U.overall_gap(np.full(4, -0.5), y, t, w), 0.0)


def test_policy_value_send_all_and_none():
    y, t, w = np.array([10.0, 0.0, 4.0, 0.0]), np.array([1, 1, 0, 0]), np.ones(4)
    # herkese: tedavi satırları 1/p ağırlıklı
    assert np.isclose(U.policy_value(np.ones(4), y, t, w, 0.5, 0.3, 0.1), (3 - 0.1 - 0.1) * 2 / 4)
    assert np.isclose(U.policy_value(np.zeros(4), y, t, w, 0.5, 0.3, 0.1), 1.2 * 2 / 4)


def test_grid_has_at_most_twelve_combinations():
    assert len(U.grid()) <= 12
    assert {c.aile for c in U.grid()} == {"T", "TO"}


def test_test_run_refuses_when_lock_exists(tmp_path, monkeypatch):
    lock = tmp_path / "test_run_hillstrom.lock"
    lock.write_text("{}")
    monkeypatch.setattr(e1, "LOCK_PATH", lock)
    assert e1.cmd_test() == 1
