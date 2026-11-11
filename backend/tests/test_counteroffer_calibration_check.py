import numpy as np
import pytest

from credit_coach.bundle import ROOT
from credit_coach.counteroffer_calibration_check import (
    SEED,
    B,
    boot_idx,
    bucket_of,
    edges,
    mean_diff,
    phi_ci_text,
    phi_text,
    render,
    slope_terms,
)
from credit_coach.counteroffer_economics import (
    Cand,
    Cost,
    break_even,
    load_cost,
    total,
)
from credit_coach.recourse import load_demo_catalog

C = Cost(getiri=0.2, kayip=0.4, hurdle=0.1)


def cands(n=300, seed=1):
    r = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        p0 = float(r.uniform(0.05, 0.3))
        out.append(
            Cand(
                "GUCLU",
                float(r.integers(1, 20) * 500),
                p0,
                p0 - float(r.uniform(0.01, 0.08)),
                int(r.random() < p0),
            )
        )
    return out


def test_bootstrap_is_reproducible_and_has_the_documented_shape():
    a, b = boot_idx(50), boot_idx(50)
    assert a.shape == (B, 50) and B == 2000 and SEED == 7
    assert (a == b).all()


def test_mean_diff_is_observed_minus_predicted_and_interval_brackets_it():
    sub = cands()
    p, y, d, (lo, hi) = mean_diff(sub)
    assert d == pytest.approx(y - p)
    assert lo <= d <= hi


def test_edges_and_buckets_follow_the_quintile_rule():
    x = np.arange(100, dtype=float)
    e = edges(x)
    assert e == pytest.approx([19.8, 39.6, 59.4, 79.2])
    counts = np.bincount([bucket_of(v, e) for v in x], minlength=5)
    assert counts.tolist() == [20, 20, 20, 20, 20]
    assert (
        bucket_of(99.0, e) == 4 and bucket_of(e[0], e) == 1
    )  # lower bound belongs to the upper bucket


def test_observed_break_even_is_the_root_of_observed_start_plus_model_slope():
    sub = cands()
    a, s = slope_terms(sub, C)
    t0, sl = float(a.sum()), float(s.sum())
    assert sl > 0
    # slope term equals the model's change of the total per unit phi
    assert sl == pytest.approx(total(sub, 1.0, C) - total(sub, 0.0, C))
    if t0 < 0:
        v = -t0 / sl
        txt = phi_text(t0, sl)
        assert txt == (">1,00" if v > 1 else f"{v:.2f}".replace(".", ","))


def test_phi_text_edge_cases():
    assert phi_text(5.0, 10.0) == "≤ 0,00"
    assert phi_text(-25.0, 10.0) == ">1,00"
    assert phi_text(-5.0, 10.0) == "0,50"


def test_phi_interval_text_has_two_ends():
    a, s = slope_terms(cands(), C)
    t = phi_ci_text(a, s)
    assert t.startswith("[") and ";" in t


def test_model_start_break_even_agrees_with_the_grid_interpolation():
    sub = cands()
    # observed start replaced by the model start (phi = 0 totals) gives the earlier report's root
    t = [total(sub, p, C) for p in (0.0, 0.25, 0.5, 0.75, 1.0)]
    s = t[-1] - t[0]
    if t[0] < 0 < t[-1]:
        assert break_even(t) == pytest.approx(-t[0] / s)


def test_render_keeps_the_committed_definition_verbatim():
    data = {
        "kalibrasyon": {0.012: cands(), 0.03: []},
        "boşluk": {0.012: cands(150), 0.03: cands(40)},
    }
    tanim = "## Tanım\n\nmetin\n"
    out = render(data, load_cost(), load_demo_catalog(), tanim)
    assert tanim.rstrip() in out
    assert "n < 100" in out and "segment" in out


def test_definition_names_the_preregistered_rules():
    doc = (ROOT / "docs" / "demo_counteroffer_calibration_check.md").read_text(encoding="utf-8")
    for token in (
        "2000 tekrar",
        "seed 7",
        "%20, %40, %60, %80",
        "n < 100",
        "Eğim varsayımı",
        "−T_gözlenen / S",
    ):
        assert token in doc


def test_report_break_even_follows_from_its_own_totals():
    doc = (ROOT / "docs" / "demo_counteroffer_calibration_check.md").read_text(encoding="utf-8")
    sec = doc.split("## 3. ", 1)[1]
    rows = 0
    for ln in sec.splitlines():
        c = [x.strip() for x in ln.strip("|").split("|")]
        if len(c) != 8 or not c[3].isdigit() or c[3] == "0":
            continue
        t0, t1 = (float(c[i].replace(",", "")) for i in (4, 5))
        v = -t0 / (t1 - t0)
        expect = "≤ 0,00" if t0 >= 0 else (">1,00" if v > 1 else f"{v:.2f}".replace(".", ","))
        assert c[6] == expect, (ln, expect)
        rows += 1
    assert rows == 10
