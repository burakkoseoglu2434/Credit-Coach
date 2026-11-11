import pytest

from credit_coach.bundle import ROOT
from credit_coach.counteroffer_economics import (
    DEF_END,
    DEF_START,
    PHIS,
    SEGMENTS,
    Cand,
    Cost,
    break_even,
    break_even_text,
    definition_text,
    load_cost,
    observed_value,
    p_phi,
    pick,
    total,
    unit_value,
    value,
)

C = Cost(getiri=0.2, kayip=0.4, hurdle=0.1)


def rec(label="GUCLU", l_new=1000.0, p0=0.2, p1=0.1, y=0):
    return Cand(label, l_new, p0, p1, y)


def test_unit_value_matches_the_formula_by_hand():
    # (1-0.2)*0.2 - 0.2*0.4 - 0.1 = 0.16 - 0.08 - 0.1 = -0.02
    assert unit_value(0.2, C) == pytest.approx(-0.02)
    assert unit_value(0.0, C) == pytest.approx(0.1)


def test_p_phi_endpoints_use_the_point_estimates():
    r = rec(p0=0.20, p1=0.08)
    assert p_phi(r, 0.0) == 0.20
    assert p_phi(r, 1.0) == pytest.approx(0.08)
    assert p_phi(r, 0.5) == pytest.approx(0.14)


def test_value_scales_with_the_new_amount_not_the_old_one():
    assert value(rec(l_new=2000.0), 0.0, C) == pytest.approx(2 * value(rec(l_new=1000.0), 0.0, C))


def test_total_is_linear_in_phi():
    rs = [
        rec(p0=0.25, p1=0.1, l_new=3000.0),
        rec(p0=0.15, p1=0.14, l_new=500.0),
        rec(p0=0.3, p1=0.31),
    ]
    t = [total(rs, phi, C) for phi in PHIS]
    steps = [b - a for a, b in zip(t, t[1:], strict=False)]
    assert steps == pytest.approx([steps[0]] * len(steps))


def test_break_even_interpolates_and_reports_no_crossing():
    assert break_even([-100.0, -50.0, 0.0, 50.0, 100.0]) == pytest.approx(0.5)
    assert break_even([-100.0, -60.0, -20.0, 20.0, 60.0]) == pytest.approx(0.625)
    assert break_even([10.0, 20.0, 30.0, 40.0, 50.0]) is None
    assert break_even([-10.0, -20.0, -30.0, -40.0, -50.0]) is None
    assert "≥ 0" in break_even_text([10.0, 20.0, 30.0, 40.0, 50.0])
    assert "< 0" in break_even_text([-1.0, -2.0, -3.0, -4.0, -5.0])


def test_break_even_equals_the_exact_root_of_the_linear_total():
    rs = [rec(p0=0.25, p1=0.05, l_new=3000.0), rec(p0=0.22, p1=0.12, l_new=1500.0)]
    t = [total(rs, phi, C) for phi in PHIS]
    slope = t[1] - t[0]
    exact = -t[0] / (slope / PHIS[1])
    assert break_even(t) == pytest.approx(exact)


def test_segments_are_nested_and_pick_by_the_plans_own_label():
    rs = [rec("GUCLU"), rec("KOSULLU"), rec("ZAYIF"), rec("ZAYIF")]
    a, b, c = (pick(rs, labs) for labs in SEGMENTS.values())
    assert (len(a), len(b), len(c)) == (1, 2, 4)


def test_observed_value_uses_the_outcome_not_the_prediction():
    good, bad = rec(y=0, l_new=1000.0), rec(y=1, l_new=1000.0)
    assert observed_value(good, C) == pytest.approx(1000 * (0.2 - 0.1))
    assert observed_value(bad, C) == pytest.approx(1000 * (-0.4 - 0.1))


def test_cost_comes_from_the_config():
    c = load_cost()
    assert c.hurdle == pytest.approx(0.11)
    assert 0 < c.getiri < 1 and 0 < c.kayip < 1


def test_definition_section_is_kept_verbatim():
    doc = (ROOT / "docs" / "demo_counteroffer_economics.md").read_text(encoding="utf-8")
    d = definition_text(doc)
    assert d.startswith(DEF_START)
    assert DEF_END not in d
    assert "p_high" in d and "p_point" in d and "kabul oranı 1" in d
    assert definition_text(doc + "\n" + DEF_END + "\nx") == d


def test_empty_segment_has_no_break_even():
    assert "boş" in break_even_text([0.0] * 5, 0)


def test_report_break_even_matches_its_own_grid_rows():
    doc = (ROOT / "docs" / "demo_counteroffer_economics.md").read_text(encoding="utf-8")
    grid: dict[tuple[str, str, str], list[float]] = {}
    for ln in doc.split("## 3. ", 1)[1].split("\n## 4. ", 1)[0].splitlines():
        c = [x.strip() for x in ln.strip("|").split("|")]
        if len(c) == 8 and c[3] in {f"{p:.2f}" for p in PHIS}:
            grid.setdefault((c[0], c[1], c[2]), []).append(float(c[6].replace(",", "")))
    assert len(grid) == 12
    for ln in doc.split("## 4. ", 1)[1].split("\n## 5. ", 1)[0].splitlines():
        c = [x.strip() for x in ln.strip("|").split("|")]
        if len(c) == 5 and (c[0], c[1], c[2]) in grid:
            if c[3] == "0":
                assert "boş" in c[4]
            else:
                assert float(c[4]) == pytest.approx(break_even(grid[(c[0], c[1], c[2])]), abs=0.002)
