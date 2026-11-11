import dataclasses

import pytest
import yaml
from hypothesis import HealthCheck, given, settings

from credit_coach.bundle import ROOT
from credit_coach.recourse import PlanVar, dayaniklilik_etiketi, plan_bul
from tests.test_recourse import KAT, POLICY, SUPPORT, deltas, records, scorers

SETTINGS = settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])


def test_label_boundaries_are_inclusive_on_the_stronger_side():
    f = lambda x: dayaniklilik_etiketi(x, KAT)  # noqa: E731
    assert f(0.0) == "GUCLU" and f(0.50) == "GUCLU"
    assert f(0.5000001) == "KOSULLU" and f(0.75) == "KOSULLU"
    assert f(0.7500001) == "ZAYIF" and f(1.0) == "ZAYIF"


def test_thresholds_come_from_the_config_and_are_labelled_as_assumptions():
    raw = yaml.safe_load((ROOT / "configs" / "catalog" / "demo_v0.yaml").read_text())
    d = raw["dayaniklilik"]
    assert (d["guclu_en_fazla"], d["kosullu_en_fazla"]) == (0.50, 0.75)
    assert "varsayım" in d["etiket"]
    assert (KAT.guclu_en_fazla, KAT.kosullu_en_fazla) == (0.50, 0.75)


def test_changing_the_config_thresholds_changes_the_label():
    strict = dataclasses.replace(KAT, guclu_en_fazla=0.30, kosullu_en_fazla=0.60)
    assert dayaniklilik_etiketi(0.40, KAT) == "GUCLU"
    assert dayaniklilik_etiketi(0.40, strict) == "KOSULLU"
    assert dayaniklilik_etiketi(0.70, strict) == "ZAYIF"


@pytest.mark.parametrize("g,k", [(0.8, 0.7), (0.0, 0.5), (0.5, 1.5), (0.5, 0.5)])
def test_invalid_thresholds_are_refused(g, k):
    bad = dataclasses.replace(KAT, guclu_en_fazla=g, kosullu_en_fazla=k)
    with pytest.raises(ValueError):
        dayaniklilik_etiketi(0.4, bad)


@SETTINGS
@given(records(), scorers, deltas)
def test_every_plan_carries_the_label_its_min_phi_implies(b, sc, d):
    res = plan_bul(b, None, sc, POLICY, SUPPORT, KAT, d)
    if not isinstance(res.sonuc, PlanVar):
        return
    for y in res.sonuc.yollar:
        assert y.dayaniklilik == dayaniklilik_etiketi(y.min_phi, KAT)
        assert y.dayaniklilik in {"GUCLU", "KOSULLU", "ZAYIF"}
        assert y.dayaniklilik_etiketi == "varsayım"
