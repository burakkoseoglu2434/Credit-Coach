"""The δ comparison document: its default-δ column must equal the published reports."""

import re

from credit_coach.bundle import ROOT
from credit_coach.delta_comparison import OLD_DELTA, deltas

DOC = (ROOT / "docs" / "demo_delta_comparison.md").read_text(encoding="utf-8")
SEGMENT = (ROOT / "docs" / "demo_target_segment.md").read_text(encoding="utf-8")


def _total_row(text: str, section: str) -> list[str]:
    block = text.split(f"## {section}\n", 1)[1].split("\n## ", 1)[0]
    row = next(ln for ln in block.splitlines() if ln.startswith("| tümü"))
    return [c.strip() for c in row.strip("|").split("|")]


def _segment_default(period: str) -> list[str]:
    row = next(
        ln
        for ln in SEGMENT.splitlines()
        if ln.startswith(f"| {period} | δ = 0,012 (demo varsayılanı) | tümü")
    )
    return [c.strip() for c in row.strip("|").split("|")][3:]  # n, plan_yok, guclu, ...


def test_old_default_is_labelled_and_default_comes_from_the_catalog():
    assert OLD_DELTA == 0.02
    assert deltas()[0] == 0.02
    assert "eski varsayılan" in DOC


def test_default_delta_columns_equal_target_segment_totals():
    for period in ("kalibrasyon", "boşluk"):
        cells = _total_row(DOC, period)
        n = cells[1]
        default = [cells[i] for i in (3, 5, 7, 9)]  # PLAN_YOK, GUCLU, KOSULLU, ZAYIF at δ=0,012
        pct = [re.search(r"\(([\d.]+%)\)", c).group(1) for c in default]
        seg = _segment_default(period)
        assert seg[0] == n
        assert seg[1:] == pct
