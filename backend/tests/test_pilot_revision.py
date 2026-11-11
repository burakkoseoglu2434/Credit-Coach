import math
from statistics import NormalDist

import pytest
import yaml

from credit_coach.bundle import ROOT
from credit_coach.counteroffer_economics import Cand, Cost
from credit_coach.pilot_protocol import CONFIG, moments
from credit_coach.pilot_revision import (
    RES_START,
    REV_START,
    RULE_LABEL,
    loss_tail,
    mde,
    months_to_fill,
    phi_for,
    revision_config,
    split_doc,
    z_total,
)

C = Cost(getiri=0.2, kayip=0.4, hurdle=0.1)
DOC = ROOT / "docs" / "pilot_protocol_v0.md"


def rec(l_new=1000.0, p0=0.2, p1=0.1):
    return Cand("GUCLU", l_new, p0, p1, 0)


def test_mde_formula_and_scaling_with_n():
    z = NormalDist().inv_cdf(0.95) + NormalDist().inv_cdf(0.8)
    assert z_total() == pytest.approx(z)
    assert mde(100.0, 400) == pytest.approx(z * 100.0 / 20.0)
    assert mde(100.0, 100) == pytest.approx(2 * mde(100.0, 400))


def test_mde_is_consistent_with_the_sample_size_formula():
    from credit_coach.pilot_protocol import n_required

    sd, n = 1870.0, 1000
    mu = mde(sd, n)
    assert n_required(mu, sd, 0.8) in (n, n + 1)  # ceil of the same quantity


def test_phi_interpolation_inside_and_outside_the_grid():
    grid = [(0.0, -60.0), (0.25, -30.0), (0.5, 0.0), (0.75, 30.0), (1.0, 60.0)]
    assert phi_for(15.0, grid)[1] == "0,62"
    assert phi_for(-30.0 + 1e-9, grid)[0] == pytest.approx(0.25, abs=1e-6)
    assert phi_for(60.0, grid)[1] == "1,00"
    assert phi_for(61.0, grid)[1] == ">1,00"
    assert phi_for(-60.0, grid)[1] == "≤ 0,00"


def test_mean_is_linear_in_phi_so_interpolation_is_exact():
    rs = [rec(1000.0, 0.25, 0.1), rec(3000.0, 0.15, 0.14)]
    grid = [(phi, moments(rs, phi, C)[0]) for phi in (0.0, 0.25, 0.5, 0.75, 1.0)]
    target = moments(rs, 0.4, C)[0]
    assert phi_for(target, grid)[0] == pytest.approx(0.4)


def test_loss_tail_is_deterministic_and_seeded():
    rs = [rec(1000.0, 0.2, 0.1), rec(2000.0, 0.3, 0.2)]
    a = loss_tail(rs, 50, C, reps=2000)
    assert a == loss_tail(rs, 50, C, reps=2000)
    assert a != loss_tail(rs, 50, C, reps=2000, seed=8)


def test_loss_tail_without_default_risk_has_no_tail():
    rs = [rec(1000.0, 0.0, 0.0)]
    t = loss_tail(rs, 10, C, reps=500)
    assert t["pre_p1"] == pytest.approx(10 * 1000 * 0.2)
    assert t["over_p1"] == pytest.approx(10 * 1000 * (0.2 - 0.1))


def test_loss_tail_matches_the_normal_approximation_for_a_large_portfolio():
    rs = [rec(1000.0, 0.2, 0.1), rec(2000.0, 0.1, 0.05), rec(1500.0, 0.3, 0.2)]
    n = 400
    mu, sd = moments(rs, 0.0, C)
    t = loss_tail(rs, n, C, reps=20000)
    approx5 = n * mu + NormalDist().inv_cdf(0.05) * sd * math.sqrt(n)
    assert t["over_p5"] == pytest.approx(approx5, rel=0.05, abs=abs(n * sd) * 0.02)
    assert t["over_p1"] < t["over_p5"] < n * mu
    assert t["pre_p5"] > t["over_p5"]  # hurdle-before total is the larger number


def test_months_to_fill():
    assert months_to_fill(250, 100.0, 1.0, 0.5) == pytest.approx(5.0)
    assert months_to_fill(250, 100.0, 0.01, 1.0) == pytest.approx(250.0)
    assert months_to_fill(250, 0.0, 1.0, 1.0) is None


def test_config_keeps_values_but_relabels_the_rule_outputs():
    old = {
        "version": 1,
        "etiket": "varsayım",
        "pilot_kredi_sayisi": {"deger": 100, "etiket": "varsayım"},
        "kredi_basina_tavan_usd": {"deger": 5000, "etiket": "varsayım"},
        "butce_tavani_usd": {"deger": 500000, "etiket": "varsayım"},
        "durdurma_esigi": {"deger": -0.05, "etiket": "varsayım"},
    }
    new = revision_config(old, [{"n": 250}])
    for k in ("pilot_kredi_sayisi", "kredi_basina_tavan_usd", "butce_tavani_usd"):
        assert new[k]["deger"] == old[k]["deger"] and new[k]["etiket"] == RULE_LABEL
    assert new["durdurma_esigi"]["etiket"] == "varsayım"
    assert new["revizyon_1"]["etiket"] == "varsayım" and new["revizyon_1"]["referans"]["n_basina"]
    assert revision_config(new, [{"n": 250}])["revizyon_1"] == new["revizyon_1"]  # idempotent


def test_revision_definition_is_kept_and_the_old_text_is_untouched():
    doc = DOC.read_text(encoding="utf-8")
    head, tail = split_doc(doc)
    assert REV_START in head and "### Revizyon tanımı" in head
    assert head.startswith("# Pilot protokolü v0")
    assert split_doc(head + "\n" + RES_START + "\nx")[0] == head
    assert tail == "" or tail.startswith(RES_START)
    for token in ("MDE", "20.000 tekrar", "Tohum 7", "ürün ya da risk bazlı fiyat farkı yoktur"):
        assert token.lower() in head.lower()


def test_generated_config_and_report_agree_once_generated():
    if not CONFIG.exists():
        pytest.skip("config not generated")
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if "revizyon_1" not in cfg:
        pytest.skip("revision not generated yet")
    doc = DOC.read_text(encoding="utf-8")
    assert cfg["butce_tavani_usd"]["etiket"] == RULE_LABEL
    assert RES_START in doc and "R1." in doc and "R4." in doc
    for row in cfg["revizyon_1"]["referans"]["n_basina"]:
        assert f"{row['n']:,}" in doc
