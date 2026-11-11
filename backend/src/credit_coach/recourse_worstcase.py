"""Observed default rate of rejected records that have a valid plan (labels used ONLY for this
evaluation), by p_point - threshold bucket, for calibration and gap months.

delta in {0, 0.03}, dti update off. The test split is never loaded.

Usage: python -m credit_coach.recourse_worstcase   (writes docs/demo_recourse_worstcase.md)
"""

from __future__ import annotations

import sys
from collections import defaultdict

import pandas as pd

from credit_coach.baseline import CSV
from credit_coach.bundle import ROOT
from credit_coach.contract import OuterStatus, parse_input
from credit_coach.decision_engine import decide_with_support
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.modeling import dev_frame
from credit_coach.policy import load_policy
from credit_coach.recourse import PlanVar, hazirla, load_demo_catalog, sec_from_scores
from credit_coach.recourse_bucket_report import LABELS, bucket
from credit_coach.recourse_gap_report import gap_frame
from credit_coach.recourse_report import vektorler
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.support import load_support, violations

REPORT = ROOT / "docs" / "demo_recourse_worstcase.md"
DELTAS = (0.0, 0.03)


def _rate(bad: int, n: int) -> str:
    return f"{100 * bad / n:.2f}%" if n else "-"


def evaluate(frame: pd.DataFrame, sc: ModelScorer, pol, support, kat) -> dict:
    thr = pol.onay_esigi
    approved = {"n": 0, "bad": 0}
    rej_bucket: dict[str, int] = defaultdict(int)  # all rejected records per bucket
    cells: dict = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # (delta) -> bucket -> [n, bad]
    for _m, grp in frame.groupby(frame["issue_date"].dt.to_period("M"), sort=True):
        tarih = grp["issue_date"].iloc[0]
        recs = vektorler(grp)
        y = grp["target"].astype(int).tolist()
        base = sc.skorla_toplu(recs, tarih)
        rej = []
        for b, s, yy in zip(recs, base, y, strict=True):
            if violations(b, support):
                continue
            g = parse_input(
                {
                    "basvuru": b,
                    "p_low": s.p_low,
                    "p_point": s.p_point,
                    "p_high": s.p_high,
                    "ham_skor": s.ham_skor,
                    "politika_surumu": "v1",
                    "plan_available": None,
                }
            )
            d = decide_with_support(g, pol, support).dis_durum
            if d is OuterStatus.APPROVED:
                approved["n"] += 1
                approved["bad"] += yy
            elif d is OuterStatus.REJECTED:
                rej.append((b, s, yy))
        for _b, s_, _y in rej:
            rej_bucket[bucket(s_.p_point - thr)] += 1
        hz = [hazirla(b, kat) for b, _s, _y in rej]
        sk = sc.skorla_toplu([a.vektor for _t, tum in hz for a in tum], tarih)
        pos = 0
        for (b, bs, yy), h in zip(rej, hz, strict=True):
            n = len(h[1])
            cs = sk[pos : pos + n]
            pos += n
            for d in DELTAS:
                res = sec_from_scores(b, h, bs, cs, pol, support, kat, d)
                if isinstance(res.sonuc, PlanVar):
                    for key in (bucket(bs.p_point - thr), "tümü"):
                        cells[d][key][0] += 1
                        cells[d][key][1] += yy
    return {"approved": approved, "cells": cells, "rej_bucket": dict(rej_bucket)}


def main() -> int:
    pol, support, kat = load_policy("v1"), load_support(), load_demo_catalog()
    sc = ModelScorer()
    dev = dev_frame(pd.read_csv(CSV))
    cal = dev[dev["split"] == "calibration"]
    assert set(cal["split"]) == {"calibration"}
    res = {
        "kalibrasyon": evaluate(cal, sc, pol, support, kat),
        "boşluk": evaluate(gap_frame(), sc, pol, support, kat),
    }
    L = [
        "# Demo v0: geçerli planı olan reddedilenlerin gözlenen temerrüt oranı",
        "",
        KURGUSAL_VEREN,
        "",
        "Etiketler yalnızca değerlendirme içindir, karar yoluna girmez. Test dilimi yüklenmedi. "
        "Reddedilen = v1 REJECTED (destek içi); plan = en az bir yolda geçerli plan "
        "(dti güncellemesi kapalı).",
        "",
        f"Onay eşiği (PD): {pol.onay_esigi:.4f}",
        "",
        "## Yanında: onaylananların gözlenen oranı",
        "",
        "| dilim | onaylanan | gözlenen temerrüt |",
        "|---|---|---|",
    ]
    for nm, r in res.items():
        a = r["approved"]
        L.append(f"| {nm} | {a['n']} | {_rate(a['bad'], a['n'])} |")
    L += [
        "",
        "## Geçerli planı olan reddedilenler: p_point − eşik kovasına göre",
        "",
        "| dilim | δ | kova | plan'lı reddedilen | gözlenen temerrüt |",
        "|---|---|---|---|---|",
    ]
    for nm, r in res.items():
        for d in DELTAS:
            for key in [*LABELS, "tümü"]:
                n, bad = r["cells"][d].get(key, [0, 0])
                if n:
                    L.append(f"| {nm} | {d:g} | {key} | {n} | {_rate(bad, n)} |")
    text = "\n".join(L) + "\n"
    REPORT.write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
