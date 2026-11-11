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


def test_min_phi_table_reports_percentiles_and_records_without_a_plan():
    import numpy as np

    from credit_coach import effect_share as es

    kesim = THR - BAND
    ks = [
        Kayit("a", 0.20, (("customer", 0.15),)),
        Kayit("b", 0.20, (("customer", 0.50), ("institution", 0.20))),
        Kayit("c", 0.20, ()),  # no plan at phi = 1
    ]
    data = {p: {0.0: ks, 0.03: ks} for p in es.PERIODS}
    text = "\n".join(es.min_phi_tables(data, POLICY))
    assert "Bu tablo ne demek" in text and "Ne DEMEK DEĞİL" in text
    assert "2 (66.7%)" in text and "1 (33.3%)" in text  # with a plan / without a plan
    per_record = [min_phi(k, kesim) for k in ks[:2]]
    assert per_record[1] == pytest.approx(
        min(phi_min(0.20, 0.50, kesim), phi_min(0.20, 0.20, kesim))
    )
    median = f"{np.percentile(per_record, 50):.2f}".replace(".", ",")
    assert f"| {median} |" in text
