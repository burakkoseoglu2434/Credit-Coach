import dataclasses

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from credit_coach.baseline import CSV
from credit_coach.catalog import unit_errors
from credit_coach.contract import OuterStatus, parse_input
from credit_coach.decision_engine import decide_with_support
from credit_coach.decision_scenarios import in_support_basvuru
from credit_coach.policy import load_policy
from credit_coach.recourse import (
    PATH_ORDER,
    LevelStatus,
    PlanGereksiz,
    PlanVar,
    PlanYok,
    _plan_key,
    imza,
    load_demo_catalog,
    plan_bul,
    yol_tipi,
)
from credit_coach.recourse import etki as apply_effect
from credit_coach.recourse_scorers import SyntheticScorer
from credit_coach.support import Support, load_support, violations

SUPPORT = load_support()
POLICY = load_policy("v1")
KAT = load_demo_catalog()
SETTINGS = settings(max_examples=120, deadline=None, suppress_health_check=[HealthCheck.too_slow])
THR = POLICY.onay_esigi


def base(**changes):
    b = in_support_basvuru(SUPPORT)
    b.update(
        revol_util=95.0,
        revol_bal=20000.0,
        loan_amnt=15000.0,
        annual_inc=60000.0,
        fico_range_low=680.0,
        fico_range_high=684.0,
        total_bal_ex_mort=40000.0,
        tot_cur_bal=90000.0,
    )
    b.update(changes)
    return b


def run(b, scorer=None, support=SUPPORT, k=KAT, delta=None):
    return plan_bul(b, None, scorer or SyntheticScorer(), POLICY, support, k, delta)


def level(eylem, seviye):
    e = next(e for e in KAT.eylemler if e.id == eylem)
    return e, next(s for s in e.seviyeler if s.id == seviye)


# ---- catalog / effects -----------------------------------------------------------------


def test_demo_catalog_units_match_manifest():
    assert unit_errors(KAT.raw) == []


def test_paydown_identities():
    b = base()
    e, s = level("revolving_paydown", "util_50")
    et = apply_effect(e, s, b, KAT)
    assert et.guncel["revol_util"] == 50.0
    assert et.guncel["revol_bal"] == pytest.approx(20000 * 50 / 95)
    delta = 20000 - et.guncel["revol_bal"]
    assert et.maliyet_usd == pytest.approx(delta)
    assert et.guncel["total_bal_ex_mort"] == pytest.approx(40000 - delta)
    assert et.guncel["tot_cur_bal"] == pytest.approx(90000 - delta)
    assert "dti" not in et.guncel  # dti update is OFF by default


def test_dti_update_is_off_by_default_and_on_in_variant():
    b = base(dti=20.0)
    e, s = level("revolving_paydown", "util_50")
    assert KAT.dti_guncelle is False
    on = dataclasses.replace(KAT, dti_guncelle=True)
    et = apply_effect(e, s, b, on)
    delta = 20000 - 20000 * 50 / 95
    assert et.guncel["dti"] == pytest.approx(20.0 - 100 * 0.02 * delta / (60000 / 12))


def test_clipping_is_marked():
    b = base(total_bal_ex_mort=1000.0)
    e, s = level("revolving_paydown", "util_30")
    et = apply_effect(e, s, b, KAT)
    assert et.guncel["total_bal_ex_mort"] == 0.0 and "total_bal_ex_mort" in et.kirpildi


def test_not_applicable_cases():
    e, s = level("revolving_paydown", "util_70")
    assert apply_effect(e, s, base(revol_util=60.0), KAT) is None  # already below target
    assert apply_effect(e, s, base(revol_bal=0.0), KAT) is None
    assert apply_effect(e, s, base(revol_util=None), KAT) is None
    e, s = level("loan_amount_reduction", "amnt_50")
    assert apply_effect(e, s, base(loan_amnt=1500.0), KAT) is None  # 750 < min amount
    assert apply_effect(e, s, base(loan_amnt=20000.0), KAT).guncel["loan_amnt"] == 10000.0


# ---- engine basics ---------------------------------------------------------------------


def test_example_gives_plans_per_path_without_cross_ranking():
    r = run(base()).sonuc
    assert isinstance(r, PlanVar)
    types = [y.yol_tipi for y in r.yollar]
    assert types == [t for t in PATH_ORDER if t in types]  # display order, one per path
    assert len(set(types)) == len(types)


def test_out_of_support_base_gives_no_plan():
    r = run(base(dti=999.0)).sonuc
    assert isinstance(r, PlanYok) and r.bagli_kisitlar == (("BASVURU", ("DESTEK_DISI",)),)


def test_approved_base_needs_no_plan():
    low = base(revol_util=5.0, revol_bal=500.0, fico_range_low=800.0, fico_range_high=804.0)
    assert isinstance(run(low).sonuc, PlanGereksiz)


def test_deep_level_pd_increase_is_invalid_and_never_used():
    sc = SyntheticScorer(loan_mode="kink", kink_at=8000.0)
    res = run(base(), sc)
    assert res.teshis[("loan_amount_reduction", "amnt_50")] is LevelStatus.SEVIYE_GECERSIZ
    if isinstance(res.sonuc, PlanVar):
        for y in res.sonuc.yollar:
            assert ("loan_amount_reduction", "amnt_50") not in y.eylemler


def test_support_violating_result_is_invalid():
    narrow = dict(SUPPORT.sayisal)
    narrow["revol_util"] = (40.0, narrow["revol_util"][1])
    sup = Support(narrow, SUPPORT.kategorik, SUPPORT.sha256)
    res = run(base(), support=sup)
    assert res.teshis[("revolving_paydown", "util_30")] is LevelStatus.DESTEK_DISI
    assert res.teshis[("revolving_paydown", "util_70")] is not LevelStatus.DESTEK_DISI
    if isinstance(res.sonuc, PlanVar):
        for y in res.sonuc.yollar:
            assert ("revolving_paydown", "util_30") not in y.eylemler


def test_max_two_actions_and_delta_zero_cannot_beat_decide():
    k1 = dataclasses.replace(KAT, max_eylem=1)
    r = run(base(), k=k1).sonuc
    if isinstance(r, PlanVar):
        assert all(len(y.eylemler) == 1 for y in r.yollar)


# ---- properties ------------------------------------------------------------------------


@st.composite
def records(draw):
    b = base()
    b["revol_util"] = draw(st.floats(0, 150))
    b["revol_bal"] = draw(st.floats(0, 60000))
    b["loan_amnt"] = draw(st.floats(1000, 35000))
    b["annual_inc"] = draw(st.floats(20000, 200000))
    b["dti"] = draw(st.floats(0, 39))
    b["fico_range_low"] = float(draw(st.integers(660, 800)))
    b["fico_range_high"] = b["fico_range_low"] + 4
    b["total_bal_ex_mort"] = draw(st.floats(0, 100000))
    b["tot_cur_bal"] = draw(st.floats(0, 300000))
    return b


scorers = st.builds(
    SyntheticScorer,
    bias=st.floats(-5.0, -1.0),
    loan_mode=st.sampled_from(["mild_up", "kink", "flat"]),
    kink_at=st.floats(5000, 20000),
)
deltas = st.sampled_from([0.0, 0.01, 0.02, 0.03])


@SETTINGS
@given(records(), scorers, deltas)
def test_same_input_same_plan(b, sc, d):
    assert (
        run(b, sc, delta=d).sonuc.model_dump_json()
        == run(dict(b), sc, delta=d).sonuc.model_dump_json()
    )


@SETTINGS
@given(records(), scorers, deltas)
def test_invariants_on_every_accepted_plan(b, sc, d):
    res = run(b, sc, delta=d)
    if not isinstance(res.sonuc, PlanVar):
        return
    baz = sc.skorla_toplu([b])[0]
    for y in res.sonuc.yollar:
        # INVARIANT: decide_with_support(post-plan vector) == APPROVED
        a, s = next((a, s) for a, s in res.gecerli if a.plan_id == y.plan_id)
        g = parse_input(
            {
                "basvuru": dict(a.vektor),
                "p_low": s.p_low,
                "p_point": s.p_point,
                "p_high": s.p_high,
                "ham_skor": s.ham_skor,
                "politika_surumu": "v1",
                "plan_available": None,
            }
        )
        assert decide_with_support(g, POLICY, SUPPORT).dis_durum is OuterStatus.APPROVED
        assert y.p_high < THR - d and y.p_high <= baz.p_high  # valid-plan conditions
        assert violations(a.vektor, SUPPORT) == ()  # result vector inside the support
        for ea in y.eylemler:  # no ladder-invalid level in any plan
            assert res.teshis[ea] is not LevelStatus.SEVIYE_GECERSIZ
        # representative of its own path: cheapest valid plan with this signature
        assert y.imza == imza([e for e, _ in y.eylemler], KAT)
        assert y.yol_tipi == yol_tipi(y.imza)
        same = [
            x
            for x, _ in res.gecerli
            if yol_tipi(imza([e for e, _ in x.eylemler], KAT)) == y.yol_tipi
        ]
        assert y.plan_id == min(same, key=_plan_key).plan_id


@SETTINGS
@given(records(), scorers, deltas)
def test_no_plan_carries_no_numeric_promise(b, sc, d):
    r = run(b, sc, delta=d).sonuc
    if not isinstance(r, PlanYok):
        return
    dump = r.model_dump()
    assert set(dump) == {"durum", "bagli_kisitlar", "esige_uzaklik"}

    def numbers(x, path=""):
        if isinstance(x, bool):
            return []
        if isinstance(x, (int, float)):
            return [path]
        if isinstance(x, dict):
            return [p for k, v in x.items() for p in numbers(v, k)]
        if isinstance(x, (list, tuple)):
            return [p for v in x for p in numbers(v, path)]
        return []

    assert numbers(dump) in ([], ["esige_uzaklik"])
    for _action, reasons in r.bagli_kisitlar:
        assert all(x in {m.value for m in LevelStatus} | {"DESTEK_DISI"} for x in reasons)


@SETTINGS
@given(
    scorers,
    scorers,
    st.sampled_from(
        [
            ("revolving_paydown",),
            ("loan_amount_reduction",),
            ("loan_amount_reduction", "revolving_paydown"),
        ]
    ),
)
def test_signature_is_independent_of_scores_and_levels(_s1, _s2, ids):
    # imza() takes only action ids: scores, PD and levels cannot enter
    assert imza(ids, KAT) == imza(list(reversed(ids)), KAT)
    assert yol_tipi(imza(ids, KAT)) in PATH_ORDER


@SETTINGS
@given(records(), scorers, scorers)
def test_signature_of_a_plan_does_not_change_with_scorer(b, s1, s2):
    r1, r2 = run(b, s1), run(b, s2)
    sig = {
        y.plan_id: y.imza
        for res in (r1, r2)
        if isinstance(res.sonuc, PlanVar)
        for y in res.sonuc.yollar
    }
    for pid, s in sig.items():
        assert s == imza([p.split(":")[0] for p in pid.split("+")], KAT)


def test_synthetic_scorer_is_monotone_where_the_model_is():
    sc = SyntheticScorer()
    for name, step in (("revol_util", 10.0), ("dti", 5.0)):
        a, b = sc.skorla_toplu([base(**{name: 30.0}), base(**{name: 30.0 + step})])
        assert b.p_point > a.p_point
    a, b = sc.skorla_toplu([base(fico_range_low=680.0), base(fico_range_low=720.0)])
    assert b.p_point < a.p_point


# ---- real scorer (raw data, local only) ------------------------------------------------


@pytest.mark.skipif(not CSV.exists(), reason="raw data not available locally")
def test_model_scorer_reproduces_frozen_calibration_scores():
    import pandas as pd

    from credit_coach.bundle import ROOT
    from credit_coach.features import allowed_features
    from credit_coach.modeling import dev_frame
    from credit_coach.recourse_scorers import ModelScorer

    dev = dev_frame(pd.read_csv(CSV))
    ca = dev[dev["split"] == "calibration"]
    cal = np.load(ROOT / "bundle" / "calibration_data.npz")
    sc = ModelScorer()
    idx = np.arange(0, len(ca), 400)
    month = ca["issue_date"].iloc[0]
    sel = ca.iloc[idx][ca.iloc[idx]["issue_date"] == ca.iloc[idx]["issue_date"].iloc[0]]
    vec = [
        {k: (None if pd.isna(v) else v) for k, v in r.items()}
        for r in sel[allowed_features()].to_dict("records")
    ]
    got = sc.skorla_toplu(vec, sel["issue_date"].iloc[0])
    want = cal["scores"][[ca.index.get_loc(i) for i in sel.index]]
    assert np.allclose([g.ham_skor for g in got], want, atol=1e-6), month


class _BandScorer:
    """Baseline high risk; every candidate lands just under the threshold, inside the R2 band."""

    def skorla_toplu(self, vektorler, tarih=None):
        from credit_coach.recourse import Skor

        inside = Skor(THR - 0.0030, THR - 0.0020, THR - 0.0010, THR - 0.0020)
        return [Skor(0.20, 0.21, 0.22, 0.21)] + [inside for _ in vektorler[1:]]


def test_delta_zero_plan_inside_the_review_band_is_rejected_by_decide():
    # p_high < threshold holds, but R2 (threshold band) makes decide() NEEDS_REVIEW, so the
    # invariant "accepted plan => APPROVED" must reject it.
    res = run(base(), _BandScorer(), delta=0.0)
    assert isinstance(res.sonuc, PlanYok)
    assert res.gecerli == ()


class _ConstScorer:
    """Baseline high risk; every candidate gets the same triple x (p_low = p_point = p_high = x)."""

    def __init__(self, x: float) -> None:
        self.x = x

    def skorla_toplu(self, vektorler, tarih=None):
        from credit_coach.recourse import Skor

        return [Skor(0.30, 0.30, 0.30, 0.30)] + [
            Skor(self.x, self.x, self.x, self.x) for _ in vektorler[1:]
        ]


BAND = POLICY.band


@pytest.mark.parametrize("delta", [0.01, 0.02, 0.03])
def test_validity_flips_exactly_at_threshold_minus_delta(delta):
    cut = THR - delta
    assert isinstance(run(base(), _ConstScorer(cut - 1e-9), delta=delta).sonuc, PlanVar)
    assert isinstance(run(base(), _ConstScorer(cut), delta=delta).sonuc, PlanYok)  # strict <
    assert isinstance(run(base(), _ConstScorer(cut + 1e-9), delta=delta).sonuc, PlanYok)


def test_delta_zero_flips_at_threshold_minus_band_because_r2_dominates():
    # With delta = 0 the stated rule would be p_high < threshold, but decide() sends anything
    # within `band` of the threshold to NEEDS_REVIEW (R2), so the effective cut is thr - band.
    cut = THR - BAND
    assert isinstance(run(base(), _ConstScorer(cut - 1e-9), delta=0.0).sonuc, PlanVar)
    assert isinstance(run(base(), _ConstScorer(cut + 1e-9), delta=0.0).sonuc, PlanYok)
    assert isinstance(run(base(), _ConstScorer(THR - 1e-9), delta=0.0).sonuc, PlanYok)


def test_effective_cut_is_thr_minus_max_delta_band():
    # general statement: effective cut = thr - max(delta, band)
    for d in (0.0, 0.001, 0.0027, 0.01, 0.02, 0.03):
        cut = THR - max(d, BAND)
        assert isinstance(run(base(), _ConstScorer(cut - 1e-7), delta=d).sonuc, PlanVar), d
        assert isinstance(run(base(), _ConstScorer(cut + 1e-7), delta=d).sonuc, PlanYok), d
