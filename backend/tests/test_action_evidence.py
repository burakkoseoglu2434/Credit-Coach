import pytest
from hypothesis import HealthCheck, given, settings

from credit_coach.recourse import PlanVar, plan_bul
from tests.test_recourse import KAT, POLICY, SUPPORT, deltas, records, scorers

SETTINGS = settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
BY_ID = {e.id: e for e in KAT.eylemler}


def test_revolving_paydown_is_an_identity_for_balance_and_a_model_relation_for_risk():
    e = BY_ID["revolving_paydown"]
    assert (e.eylem_turu, e.bakiye_kullanim_etkisi, e.risk_etkisi) == ("musteri_eylemi", "K", "M")


def test_loan_amount_reduction_is_a_counter_offer_with_a_model_relation_for_risk():
    e = BY_ID["loan_amount_reduction"]
    assert (e.eylem_turu, e.bakiye_kullanim_etkisi, e.risk_etkisi) == ("karsi_teklif", None, "M")


def test_counter_offer_label_follows_the_owner():
    for e in KAT.eylemler:
        assert (e.eylem_turu == "karsi_teklif") == (e.sahip == "institution"), e.id


def test_every_action_has_a_closed_evidence_label():
    for e in KAT.eylemler:
        assert e.bakiye_kullanim_etkisi in {"K", None} and e.risk_etkisi == "M"


@SETTINGS
@given(records(), scorers, deltas)
def test_plans_carry_the_evidence_of_each_of_their_actions(b, sc, d):
    res = plan_bul(b, None, sc, POLICY, SUPPORT, KAT, d)
    if not isinstance(res.sonuc, PlanVar):
        return
    for y in res.sonuc.yollar:
        assert [x.eylem for x in y.eylem_kanitlari] == [e for e, _ in y.eylemler]
        for x in y.eylem_kanitlari:
            e = BY_ID[x.eylem]
            assert (x.eylem_turu, x.bakiye_kullanim_etkisi, x.risk_etkisi) == (
                e.eylem_turu,
                e.bakiye_kullanim_etkisi,
                e.risk_etkisi,
            )
        if "loan_amount_reduction" in [e for e, _ in y.eylemler]:
            assert y.yol_tipi in {"hybrid", "institution"}


def test_catalog_without_evidence_is_refused(tmp_path):
    import yaml

    from credit_coach.recourse import DEMO_CATALOG_PATH, load_demo_catalog

    raw = yaml.safe_load(DEMO_CATALOG_PATH.read_text())
    del raw["eylemler"][0]["kanit"]
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(raw, allow_unicode=True))
    with pytest.raises(KeyError):
        load_demo_catalog(p)
