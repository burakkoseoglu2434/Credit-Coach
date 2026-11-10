import numpy as np
import pytest

from credit_coach.decision import (
    APPROVE,
    HUMAN,
    NOT_APPROVED,
    DecisionConfig,
    approval_threshold,
    decide,
    expected_margin,
    total_hurdle,
)

G, L = 0.1666, 0.3519


def test_threshold_reduces_to_break_even_without_hurdle():
    assert approval_threshold(G, L, 0.0) == pytest.approx(G / (G + L))


def test_threshold_matches_rule_exactly():
    h = 0.03
    thr = approval_threshold(G, L, h)
    assert expected_margin(np.array([thr]), G, L)[0] == pytest.approx(h)
    p = np.linspace(0, 1, 2001)
    rule = expected_margin(p, G, L) >= h
    assert (rule == (p <= thr + 1e-12)).all()


def test_threshold_falls_as_hurdle_rises_and_clips_at_zero():
    ts = [approval_threshold(G, L, h) for h in (0, 0.02, 0.05, 0.1)]
    assert ts == sorted(ts, reverse=True)
    assert approval_threshold(G, L, G + 0.01) == 0.0


def test_total_hurdle_requires_all_assumptions():
    doc = {
        "hurdle": {k: {"deger": None} for k in ("asgari_marj", "fon_maliyeti", "isletme_gideri")}
    }
    with pytest.raises(ValueError):
        total_hurdle(doc)
    doc["hurdle"]["asgari_marj"]["deger"] = 0.02
    with pytest.raises(ValueError):
        total_hurdle(doc)


def test_total_hurdle_sums_fields():
    doc = {
        "hurdle": {
            k: {"deger": v}
            for k, v in (("asgari_marj", 0.02), ("fon_maliyeti", 0.05), ("isletme_gideri", 0.01))
        }
    }
    assert total_hurdle(doc) == pytest.approx(0.08)


CFG = DecisionConfig(threshold=0.20, band=0.01, weak_support_ranges=((0.0, 0.03),))


def test_interval_rule_cases():
    low = np.array([0.05, 0.19, 0.205, 0.215, 0.40, 0.01])
    high = np.array([0.06, 0.195, 0.21, 0.22, 0.41, 0.02])
    raw = np.array([0.05, 0.19, 0.2, 0.22, 0.4, 0.015])
    out = decide(low, high, raw, CFG)
    assert list(out) == [APPROVE, HUMAN, HUMAN, NOT_APPROVED, NOT_APPROVED, APPROVE]


def test_straddling_interval_always_goes_to_human():
    rng = np.random.default_rng(0)
    lo = rng.uniform(0.1, 0.3, 500)
    hi = lo + rng.uniform(0, 0.2, 500)
    out = decide(lo, hi, np.full(500, 0.5), CFG)
    straddle = (lo <= CFG.threshold) & (hi >= CFG.threshold)
    assert (out[straddle] == HUMAN).all()


def test_wider_band_never_reduces_human_count():
    rng = np.random.default_rng(1)
    lo = rng.uniform(0, 0.5, 2000)
    hi = lo + rng.uniform(0, 0.02, 2000)
    raw = np.full(2000, 0.5)
    counts = [
        (decide(lo, hi, raw, DecisionConfig(0.2, b)) == HUMAN).sum() for b in (0.0, 0.01, 0.05)
    ]
    assert counts == sorted(counts)


def test_state_sequence_is_ordered_as_pd_rises():
    p = np.linspace(0.01, 0.6, 600)
    out = decide(p - 0.002, p + 0.002, np.full(600, 0.5), DecisionConfig(0.2, 0.01))
    rank = {APPROVE: 0, HUMAN: 1, NOT_APPROVED: 2}
    r = [rank[x] for x in out]
    assert r == sorted(r)


def test_invalid_interval_rejected():
    with pytest.raises(ValueError):
        decide(np.array([0.3]), np.array([0.2]), np.array([0.2]), CFG)


def test_weak_support_far_from_threshold_is_not_sent_to_human():
    cfg = DecisionConfig(threshold=0.20, band=0.01, weak_support_ranges=((0.0, 0.5),))
    # PD 0.05 and 0.60 are in the weak range but far from the threshold (> 3 * band)
    out = decide(np.array([0.05, 0.60]), np.array([0.06, 0.61]), np.array([0.05, 0.4]), cfg)
    assert list(out) == [APPROVE, NOT_APPROVED]


def test_weak_support_near_threshold_goes_to_human():
    cfg = DecisionConfig(threshold=0.20, band=0.01, weak_support_ranges=((0.0, 0.5),))
    # PD 0.165: outside the plain band (0.035 > 0.01) but within 3 * band = 0.03? no (0.035 > 0.03)
    far = decide(np.array([0.164]), np.array([0.166]), np.array([0.165]), cfg)
    # PD 0.175: distance 0.025 <= 0.03, in weak range -> human, while not in plain band
    near = decide(np.array([0.174]), np.array([0.176]), np.array([0.175]), cfg)
    assert far[0] == APPROVE and near[0] == HUMAN


def test_near_threshold_outside_weak_range_stays_automatic():
    cfg = DecisionConfig(threshold=0.20, band=0.01, weak_support_ranges=((0.9, 1.0),))
    out = decide(np.array([0.174]), np.array([0.176]), np.array([0.175]), cfg)
    assert out[0] == APPROVE


def test_approval_rate_never_rises_with_hurdle():
    from credit_coach.approval_table import table

    rng = np.random.default_rng(3)
    s = rng.beta(1.5, 8, 5000)
    y = (rng.random(5000) < s).astype(int)
    t = table(
        s - 0.001, s + 0.001, s, s, y, 0.17, 0.35, 0.003, [], 3.0, grid=(0.0, 0.05, 0.11, 0.15)
    )
    assert (t["esik"].diff().dropna() < 0).all()
    assert (t["onay_orani"].diff().dropna() <= 1e-12).all()
    assert np.isclose(t[["onay_orani", "insana_orani", "onay_degil_orani"]].sum(axis=1), 1).all()
