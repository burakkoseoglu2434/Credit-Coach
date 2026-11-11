import itertools
import math
from statistics import NormalDist

import pytest
import yaml

from credit_coach.bundle import ROOT
from credit_coach.counteroffer_economics import Cand, Cost, total
from credit_coach.pilot_protocol import (
    CONFIG,
    START,
    config_doc,
    definition_text,
    moments,
    n_required,
    offers,
    pre_hurdle_mean,
    round_up,
    worst_case,
)

C = Cost(getiri=0.2, kayip=0.4, hurdle=0.1)  # a = 0.1, b = 0.6


def rec(l_new=1000.0, p0=0.2, p1=0.1):
    return Cand("GUCLU", l_new, p0, p1, 0)


def test_single_record_moments_match_the_bernoulli_formula():
    r = rec(l_new=2000.0, p0=0.2, p1=0.1)
    mu, sd = moments([r], 0.0, C)
    assert mu == pytest.approx(2000 * (0.1 - 0.6 * 0.2))
    assert sd == pytest.approx(2000 * 0.6 * math.sqrt(0.2 * 0.8))
    mu1, _ = moments([r], 1.0, C)
    assert mu1 == pytest.approx(2000 * (0.1 - 0.6 * 0.1))


def test_mixture_variance_matches_brute_force_enumeration():
    rs = [rec(1000.0, 0.1, 0.05), rec(3000.0, 0.3, 0.2)]
    mu, sd = moments(rs, 0.5, C)
    ps = [r.p0 - 0.5 * (r.p0 - r.p1) for r in rs]
    ev = 0.0
    ev2 = 0.0
    for i, ys in itertools.product(range(2), itertools.product((0, 1), repeat=1)):
        r, p, y = rs[i], ps[i], ys[0]
        prob = 0.5 * (p if y else 1 - p)
        val = r.l_new * ((1 - y) * 0.2 - y * 0.4 - 0.1)
        ev += prob * val
        ev2 += prob * val**2
    assert mu == pytest.approx(ev)
    assert sd == pytest.approx(math.sqrt(ev2 - ev**2))


def test_mean_equals_the_economics_report_total_per_record():
    rs = [rec(1000.0, 0.25, 0.1), rec(500.0, 0.15, 0.14), rec(3000.0, 0.3, 0.2)]
    for phi in (0.0, 0.5, 1.0):
        assert moments(rs, phi, C)[0] == pytest.approx(total(rs, phi, C) / len(rs))


def test_sample_size_formula_and_undefined_case():
    z = NormalDist().inv_cdf(0.95) + NormalDist().inv_cdf(0.8)
    assert n_required(10.0, 100.0, 0.8) == math.ceil((z * 10) ** 2)
    assert n_required(0.0, 100.0, 0.8) is None and n_required(-1.0, 1.0, 0.9) is None
    assert n_required(10.0, 100.0, 0.9) > n_required(10.0, 100.0, 0.8)


def test_offers_round_up_and_worst_case_signs():
    assert offers(100, 0.3) == 334 and offers(100, 0.5) == 200
    over, cash = worst_case(10, 1000.0, C)
    assert over == pytest.approx(-10 * 1000 * 0.5) and cash == pytest.approx(-10 * 1000 * 0.4)
    assert over < cash < 0  # excess over hurdle is the larger (negative) number: not the cash loss


def test_pre_hurdle_mean_is_hurdle_over_plus_hurdle_share():
    rs = [rec(1000.0, 0.2, 0.1), rec(2000.0, 0.1, 0.05)]
    mu, _ = moments(rs, 0.0, C)
    mean_l = sum(r.l_new for r in rs) / len(rs)
    assert pre_hurdle_mean(rs, 0.0, C) == pytest.approx(mu + C.hurdle * mean_l)


def test_round_up_steps():
    assert round_up(101, 100) == 200 and round_up(100, 100) == 100 and round_up(7001, 500) == 7500


def test_config_is_labelled_as_assumption():
    d = config_doc(
        {
            "pilot_kredi_sayisi": 100,
            "kredi_basina_tavan_usd": 5000,
            "butce_tavani_usd": 500000,
            "durdurma_esigi": -0.05,
        }
    )
    assert d["etiket"] == "varsayım"
    for k in (
        "pilot_kredi_sayisi",
        "kredi_basina_tavan_usd",
        "butce_tavani_usd",
        "durdurma_esigi",
        "alfa",
    ):
        assert d[k]["etiket"] == "varsayım"


def test_definition_section_is_kept_verbatim():
    doc = (ROOT / "docs" / "pilot_protocol_v0.md").read_text(encoding="utf-8")
    d = definition_text(doc)
    assert d.startswith(START) and "## Sonuçlar" not in d
    assert "tek yönlü" in d and "−%5" in d and "NAKİT KAYIP DEĞİLDİR" in d
    assert definition_text(d + "\n## Sonuçlar\nx") == d


def test_pilot_config_exists_and_matches_the_report_once_generated():
    if not CONFIG.exists():
        pytest.skip("report not generated yet")
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    doc = (ROOT / "docs" / "pilot_protocol_v0.md").read_text(encoding="utf-8")
    assert cfg["etiket"] == "varsayım"
    assert f"{cfg['pilot_kredi_sayisi']['deger']:,}" in doc
    assert f"{cfg['butce_tavani_usd']['deger']:,}" in doc
    assert (
        cfg["butce_tavani_usd"]["deger"]
        == cfg["pilot_kredi_sayisi"]["deger"] * cfg["kredi_basina_tavan_usd"]["deger"]
    )


def test_pool_note_only_when_the_rule_output_exceeds_the_pool():
    from credit_coach.pilot_protocol import pool_note

    assert pool_note(1000, 2000) == ""
    assert "büyüktür" in pool_note(23600, 7167) and "23,600" in pool_note(23600, 7167)
