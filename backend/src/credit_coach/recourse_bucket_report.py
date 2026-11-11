"""Valid-plan rate (delta=0.02, dti update off) by p_point - threshold bucket and by month.

Calibration split only; the test split is never loaded.

Usage: python -m credit_coach.recourse_bucket_report   (writes docs/demo_recourse_buckets.md)
"""

from __future__ import annotations

import sys
from collections import defaultdict

import pandas as pd

from credit_coach.baseline import CSV
from credit_coach.bundle import ROOT
from credit_coach.contract import OuterStatus, parse_input
from credit_coach.decision_engine import decide_with_support
from credit_coach.features import allowed_features, load_manifest
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.modeling import dev_frame
from credit_coach.policy import load_policy
from credit_coach.recourse import PATH_ORDER, PlanVar, hazirla, load_demo_catalog, sec_from_scores
from credit_coach.recourse_report import _pct, _vektor
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.support import load_support, violations

REPORT = ROOT / "docs" / "demo_recourse_buckets.md"
DELTA = 0.02
EDGES = [-1.0, 0.0, 0.01, 0.02, 0.03, 0.05, 0.10, 0.20, 9.0]
LABELS = [
    "< 0",
    "[0, 0,01)",
    "[0,01, 0,02)",
    "[0,02, 0,03)",
    "[0,03, 0,05)",
    "[0,05, 0,10)",
    "[0,10, 0,20)",
    ">= 0,20",
]


def bucket(x: float) -> str:
    for lo, hi, lab in zip(EDGES, EDGES[1:], LABELS, strict=True):
        if lo <= x < hi:
            return lab
    raise ValueError(x)


def main() -> int:
    pol, support, kat = load_policy("v1"), load_support(), load_demo_catalog()
    sc = ModelScorer()
    kinds = {c.ad: c.tip for c in load_manifest()}
    names = allowed_features()
    ca = dev_frame(pd.read_csv(CSV))
    ca = ca[ca["split"] == "calibration"]
    assert set(ca["split"]) == {"calibration"}
    thr = pol.onay_esigi
    by_bucket: dict[str, dict] = defaultdict(lambda: defaultdict(int))
    by_month: dict[str, dict] = defaultdict(lambda: defaultdict(int))
    for month, grp in ca.groupby(ca["issue_date"].dt.to_period("M"), sort=True):
        tarih = grp["issue_date"].iloc[0]
        recs = [_vektor(r, kinds, names) for r in grp[names].to_dict("records")]
        base = sc.skorla_toplu(recs, tarih)
        rej = []
        for b, s in zip(recs, base, strict=True):
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
            if decide_with_support(g, pol, support).dis_durum is OuterStatus.REJECTED:
                rej.append((b, s))
        hz = [hazirla(b, kat) for b, _ in rej]
        sk = sc.skorla_toplu([a.vektor for _t, tum in hz for a in tum], tarih)
        pos = 0
        for (b, bs), h in zip(rej, hz, strict=True):
            n = len(h[1])
            res = sec_from_scores(b, h, bs, sk[pos : pos + n], pol, support, kat, DELTA)
            pos += n
            for acc in (by_bucket[bucket(bs.p_point - thr)], by_month[str(month)]):
                acc["n"] += 1
                if isinstance(res.sonuc, PlanVar):
                    acc["any"] += 1
                    for y in res.sonuc.yollar:
                        acc[y.yol_tipi] += 1

    def table(title: str, keys: list[str], data: dict) -> list[str]:
        out = [
            f"## {title}",
            "",
            "| grup | reddedilen | en az bir yol | " + " | ".join(PATH_ORDER) + " |",
            "|---|---|---|" + "---|" * len(PATH_ORDER),
        ]
        for k in keys:
            d = data[k]
            out.append(
                f"| {k} | {d['n']} | {_pct(d['any'], d['n'])} "
                + " ".join(f"| {_pct(d[t], d['n'])}" for t in PATH_ORDER)
                + " |"
            )
        return out + [""]

    L = [
        "# Demo v0: geçerli plan oranı, p_point − eşik kovaları ve aylar (kalibrasyon)",
        "",
        KURGUSAL_VEREN,
        "",
        f"δ = {DELTA}, dti güncellemesi kapalı, reddedilen = v1 REJECTED (destek içi). "
        "Test dilimi yüklenmedi.",
        "",
    ]
    L += table(
        "p_point − eşik kovasına göre", [lab for lab in LABELS if lab in by_bucket], by_bucket
    )
    L += table("aya göre", sorted(by_month), by_month)
    text = "\n".join(L)
    REPORT.write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
