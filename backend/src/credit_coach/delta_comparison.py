# ruff: noqa: E501  (report prose is long on purpose)
"""Side-by-side label distributions for the old default delta (0.02) and the current default
(catalog, 0.012): calibration split and gap months, all rejected records and by
p_point - threshold bucket. The TEST split is never loaded. The old default is shown only for
comparison and is labelled as such.

Usage: python -m credit_coach.delta_comparison   (writes docs/demo_delta_comparison.md)
"""

from __future__ import annotations

import sys
from collections import Counter

import pandas as pd

from credit_coach import baseline
from credit_coach.bundle import ROOT
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.modeling import dev_frame
from credit_coach.policy import load_policy
from credit_coach.recourse import load_demo_catalog
from credit_coach.recourse_gap_report import gap_frame
from credit_coach.recourse_report import _pct
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.report_deltas import fmt
from credit_coach.resilience_report import MISSING, PERIODS, strongest
from credit_coach.scoring_service import LABELS as BUCKETS
from credit_coach.support import load_support
from credit_coach.target_segment import COLS, collect

REPORT = ROOT / "docs" / "demo_delta_comparison.md"
OLD_DELTA = 0.02  # previous default, kept only for this comparison


def deltas() -> tuple[float, float]:
    return OLD_DELTA, float(load_demo_catalog().delta)


def _row(kova: str, recs: list, old: float, new: float, data: dict) -> str:
    n = len(data[old]) if kova == "tümü" else sum(1 for k, _ in recs if k == kova)
    cells = []
    for d in (old, new):
        sub = data[d] if kova == "tümü" else [r for r in data[d] if r[0] == kova]
        data_c = Counter(strongest(lab) for _k, lab in sub)
        cells.append((data_c, len(sub)))
    out = [kova, f"{n}"]
    for k in COLS:
        for c, m in cells:
            out.append(f"{c[k]} ({_pct(c[k], m)})")
    return "| " + " | ".join(out) + " |"


def render(data: dict[str, dict[float, list]]) -> str:
    old, new = deltas()
    lo, ln = f"δ = {fmt(old)} (eski varsayılan)", f"δ = {fmt(new)} (varsayılan)"
    head = ["| kova (p_point − eşik) | reddedilen |"]
    sep = ["|---|---|"]
    for k in COLS:
        head.append(f" {k} {lo} | {k} {ln} |")
        sep.append("---|---|")
    L = [
        "# Demo v0: δ = 0,02 (eski varsayılan) ve δ = 0,012 (varsayılan) yan yana",
        "",
        KURGUSAL_VEREN,
        "",
        f"Varsayılan δ = {fmt(new)} (`configs/catalog/demo_v0.yaml`, `delta.deger`, varsayım, ADR-007). "
        f"δ = {fmt(old)} önceki varsayılandır ve yalnızca karşılaştırma içindir; API ve arayüz onu kullanmaz.",
        "",
        "Kapsam: kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08); test dilimi "
        "kullanılmadı. Reddedilen = v1 REJECTED (destek içi). dti güncellemesi kapalı. Etiket = kaydın planı olan yolları içinde en güçlü olanı. "
        "Hücre: kayıt sayısı (oran).",
        "",
    ]
    for p in PERIODS:
        recs = data[p]
        L += [f"## {p}", "", "".join(head), "".join(sep)]
        for kova in (*BUCKETS, "tümü"):
            L.append(_row(kova, recs[new], old, new, recs))
        L += [
            "",
            "> **Bu tablo ne demek:** Aynı reddedilen kayıtlar için iki δ'da, planı olmayanların (PLAN_YOK) ve planı olanlarda en güçlü yolun etiketinin sayısı; 'tümü' satırı tüm reddedilenleri verir.",
            "",
            "> **Ne DEMEK DEĞİL:** Hangi δ'nın doğru olduğunu ya da etiketlerin gerçekte işe yarayacağını göstermez; δ bir varsayımdır (ADR-007), gerçek etki payı bilinmiyor.",
            "",
        ]
    return "\n".join(L) + "\n"


def build(csv_path=None) -> str:
    pol, support, kat = load_policy("v1"), load_support(), load_demo_catalog()
    sc = ModelScorer()
    dev = dev_frame(pd.read_csv(csv_path or baseline.CSV))
    frames = {"kalibrasyon": dev[dev["split"] == "calibration"], "boşluk": gap_frame()}
    assert all("test" not in set(f["split"]) for f in frames.values())
    data = {p: collect(f, sc, pol, support, kat, deltas()) for p, f in frames.items()}
    return render(data)


def main() -> int:
    if not baseline.CSV.exists():
        print(MISSING.format(path=baseline.CSV), file=sys.stderr)
        return 2
    text = build(baseline.CSV)
    REPORT.write_text(text)
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
