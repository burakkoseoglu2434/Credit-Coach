"""Demo v0 recourse report on the GAP months (2015-01, 02, 07, 08) next to the calibration split.

No labels are used. The test split is never loaded: only rows labelled `gap` by the split config
are taken, and the run asserts that no `test` row is present.

Usage: python -m credit_coach.recourse_gap_report   (writes docs/demo_recourse_gap_months.md)
"""

from __future__ import annotations

import statistics
import sys

import pandas as pd

from credit_coach.baseline import CSV
from credit_coach.bundle import ROOT
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.recourse import PATH_ORDER, LevelStatus, load_demo_catalog
from credit_coach.recourse_report import DELTAS, _pct, run
from credit_coach.split import assign_split, cohort

REPORT = ROOT / "docs" / "demo_recourse_gap_months.md"
GAP_MONTHS = ("2015-01", "2015-02", "2015-07", "2015-08")
NAMES = ("kalibrasyon", "boşluk")


def gap_frame() -> pd.DataFrame:
    raw = pd.read_csv(CSV)
    label = assign_split(raw)
    c = cohort(raw)
    frame = c.loc[label.index[label == "gap"]].assign(split="gap")
    months = set(frame["issue_date"].dt.strftime("%Y-%m"))
    assert months == set(GAP_MONTHS), months
    assert "test" not in set(frame["split"])
    return frame


def render(res: dict[str, dict]) -> str:
    kat = load_demo_catalog()
    cal, gap = res["kalibrasyon"], res["boşluk"]
    L = [
        "# Demo v0: recourse, boşluk ayları ve kalibrasyon yan yana",
        "",
        KURGUSAL_VEREN,
        "",
        "Boşluk ayları: 2015-01, 02, 07, 08 (etiket kullanılmadı, test dilimi yüklenmedi). "
        "Maliyet ve süre varsayımdır.",
        "",
        "## Küme",
        "",
        "| Büyüklük | kalibrasyon | boşluk |",
        "|---|---|---|",
    ]
    for label, key in (
        ("Kayıt", "n_calibration"),
        ("Destek dışı", "out_of_support"),
        ("v1 APPROVED", "base_APPROVED"),
        ("v1 CONDITIONAL", "base_CONDITIONAL"),
        ("v1 REJECTED (destek içi)", "base_REJECTED"),
    ):
        L.append(f"| {label} | {cal['counts'][key]} | {gap['counts'][key]} |")

    L += [
        "",
        "## Geçerli planı olan reddedilen oranı",
        "",
        "| δ | dti | dilim | en az bir yol | customer | hybrid | institution | PLAN_YOK |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for d in DELTAS:
        for dti in (False, True):
            for nm in NAMES:
                r = res[nm]
                p, n = r["plan_n"][(d, dti)], r["counts"]["rejected"]
                L.append(
                    f"| {d:g} | {'açık' if dti else 'kapalı'} | {nm} | {_pct(p['any'], n)} "
                    + " ".join(f"| {_pct(p[('path', t)], n)}" for t in PATH_ORDER)
                    + f" | {_pct(n - p['any'], n)} |"
                )

    L += [
        "",
        "## Eylem seviyesi başına durum (kayıt payı, reddedilenler içinde)",
        "",
        "| δ | dti | dilim | eylem | seviye | " + " | ".join(s.value for s in LevelStatus) + " |",
        "|---|---|---|---|---|" + "---|" * len(LevelStatus),
    ]
    for d in DELTAS:
        for dti in (False, True):
            for nm in NAMES:
                r = res[nm]
                n = r["counts"]["rejected"]
                lv = r["levels"][(d, dti)]
                for e in kat.eylemler:
                    for s in e.seviyeler:
                        cells = " ".join(
                            f"| {_pct(lv[(e.id, s.id, st.value)], n)}" for st in LevelStatus
                        )
                        L.append(
                            f"| {d:g} | {'açık' if dti else 'kapalı'} | {nm} | {e.id} | {s.id} "
                            + cells
                            + " |"
                        )

    L += [
        "",
        "## Yol başına medyan USD maliyeti (varsayım)",
        "",
        "| δ | dti | dilim | customer | hybrid | institution |",
        "|---|---|---|---|---|---|",
    ]
    for d in DELTAS:
        for dti in (False, True):
            for nm in NAMES:
                cells = []
                for t in PATH_ORDER:
                    v = res[nm]["costs"].get(((d, dti), t), [])
                    cells.append(f"{statistics.median(v):,.0f} (n={len(v)})" if v else "-")
                L.append(
                    f"| {d:g} | {'açık' if dti else 'kapalı'} | {nm} | " + " | ".join(cells) + " |"
                )
    return "\n".join(L) + "\n"


def main() -> int:
    res = {"kalibrasyon": run(), "boşluk": run(gap_frame())}
    text = render(res)
    REPORT.write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
