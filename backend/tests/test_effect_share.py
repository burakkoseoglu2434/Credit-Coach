import pytest
from hypothesis import HealthCheck, given, settings

from credit_coach.effect_share import (
    PHIS,
    Kayit,
    cut,
    min_phi,
    p_after_real,
    phi_min,
    valid_at,
)
from credit_coach.policy import load_policy
from credit_coach.recourse import imza, plan_bul, yol_tipi
from credit_coach.scoring_service import bucket
from tests.test_recourse import KAT, POLICY, SUPPORT, deltas, records, scorers

THR, BAND = POLICY.onay_esigi, POLICY.band
SETTINGS = settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])


def test_cut_is_threshold_minus_the_larger_of_delta_and_band():
    assert cut(THR, 0.0, BAND) == THR - BAND
    assert cut(THR, 0.03, BAND) == THR - 0.03
    assert cut(THR, 0.001, BAND) == THR - BAND


def test_phi_min_is_where_the_plan_reaches_the_cut():
    p_before, dp, kesim = 0.20, 0.15, 0.10
    phi = phi_min(p_before, dp, kesim)
    assert phi == pytest.approx((0.20 - 0.10) / 0.15)
    assert p_after_real(p_before, dp, phi) == pytest.approx(kesim)


def test_validity_flips_exactly_at_phi_min():
    k = Kayit("x", 0.20, (("customer", 0.15),))
    kesim = 0.10
    phi = phi_min(0.20, 0.15, kesim)
    assert not valid_at(k, phi, kesim)  # strict inequality: only phi above the infimum is valid
    assert valid_at(k, phi + 1e-9, kesim)
    assert not valid_at(k, phi - 1e-9, kesim)


def test_path_filter_and_empty_plans():
    k = Kayit("x", 0.20, (("customer", 0.02), ("institution", 0.15)))
    assert valid_at(k, 1.0, 0.10, "institution") and not valid_at(k, 1.0, 0.10, "customer")
    assert min_phi(k, 0.10, "customer") == pytest.approx(0.10 / 0.02)
    assert min_phi(Kayit("x", 0.2, ()), 0.1) is None


@SETTINGS
@given(records(), scorers, deltas)
def test_phi_one_reproduces_the_engine_and_smaller_phi_only_removes_plans(b, sc, d):
    base_s = sc.skorla_toplu([b])[0]
    if base_s.p_high < THR:  # not a rejected record
        return
    res = plan_bul(b, None, sc, POLICY, SUPPORT, KAT, d)
    planlar = tuple(
        (yol_tipi(imza([e for e, _ in a.eylemler], KAT)), base_s.p_high - s.p_high)
        for a, s in res.gecerli
    )
    k = Kayit(bucket(base_s.p_point - THR), base_s.p_high, planlar)
    kesim = cut(THR, d, BAND)
    # phi = 1 reproduces the engine: a plan exists exactly when the engine found one
    assert valid_at(k, 1.0, kesim) == bool(res.gecerli)
    # the validity set only grows with phi
    flags = [valid_at(k, phi, kesim) for phi in PHIS]
    assert flags == sorted(flags)
    # every engine-valid plan has a minimum phi inside (0, 1)
    for _t, dp in planlar:
        assert 0 < phi_min(k.p_before, dp, kesim) < 1


def test_phi_one_cut_matches_the_policy_object():
    assert load_policy("v1").onay_esigi == THR
