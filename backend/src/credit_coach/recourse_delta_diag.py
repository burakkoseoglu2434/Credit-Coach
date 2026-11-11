"""Delta diagnostic (calibration split only): is delta=0.01 vs 0.02 giving the same plans a
plateau of the Venn-Abers step function, or an implementation error?

Lists (1) the discrete p_high values the frozen calibrator can output near the threshold and
how many calibration records sit on each, (2) the p_high of every candidate plan of the rejected
calibration records, binned around the threshold.

Usage: python -m credit_coach.recourse_delta_diag   (writes docs/demo_recourse_delta_diag.md)
"""

from __future__ import annotations

import sys
from collections import Counter

import numpy as np
import pandas as pd

from credit_coach.baseline import CSV
from credit_coach.bundle import ROOT
from credit_coach.calibration import predict_interval
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.modeling import dev_frame
from credit_coach.policy import load_policy
from credit_coach.recourse import hazirla, load_demo_catalog
from credit_coach.recourse_report import vektorler
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.support import load_support, violations

REPORT = ROOT / "docs" / "demo_recourse_delta_diag.md"


def main() -> int:
    pol, support, kat = load_policy("v1"), load_support(), load_demo_catalog()
    thr, band = pol.onay_esigi, pol.band
    sc = ModelScorer()
    cal = np.load(ROOT / "bundle" / "calibration_data.npz")
    _lo, hi_all, _pt = predict_interval(sc.va, cal["scores"])
    vals = Counter(round(float(v), 10) for v in hi_all)

    dev = dev_frame(pd.read_csv(CSV))
    ca = dev[dev["split"] == "calibration"]
    cand_hi: list[float] = []
    cand_steps: Counter = Counter()
    n_rej = 0
    for _m, grp in ca.groupby(ca["issue_date"].dt.to_period("M"), sort=True):
        tarih = grp["issue_date"].iloc[0]
        recs = vektorler(grp)
        base = sc.skorla_toplu(recs, tarih)
        rej = [
            b
            for b, s in zip(recs, base, strict=True)
            if not violations(b, support) and s.p_high >= thr
        ]
        n_rej += len(rej)
        flat = [a.vektor for b in rej for a in hazirla(b, kat)[1]]
        for s in sc.skorla_toplu(flat, tarih):
            cand_hi.append(s.p_high)
            cand_steps[round(s.p_high, 10)] += 1
    ch = np.array(cand_hi)

    def n_in(a: float, b: float) -> int:
        return int(((ch >= a) & (ch < b)).sum())

    L = [
        "# Demo v0: δ tanısı (kalibrasyon dilimi)",
        "",
        KURGUSAL_VEREN,
        "",
        f"Eşik {thr:.6f}, band {band:.6f}. Reddedilen (p_high ≥ eşik, destek içi): {n_rej}. "
        f"Aday plan sayısı: {len(ch)}.",
        "",
        "## 1. Kalibratörün eşik civarındaki ayrık p_high değerleri",
        "",
        f"Kalibratörün kalibrasyon skorlarında ürettiği benzersiz p_high sayısı: {len(vals)}.",
        "",
        "| p_high | eşik − p_high | kalibrasyon kaydı sayısı |",
        "|---|---|---|",
    ]
    for v in sorted(vals):
        if thr - 0.04 < v < thr + 0.01:
            L.append(f"| {v:.6f} | {thr - v:+.6f} | {vals[v]} |")
    L += [
        "",
        "## 2. Aday planların p_after = p_high dağılımı (reddedilenler, dti kapalı)",
        "",
        "| aralık | aday sayısı |",
        "|---|---|",
        f"| [eşik−0,03, eşik−0,02) | {n_in(thr - 0.03, thr - 0.02)} |",
        f"| [eşik−0,02, eşik−0,01) | {n_in(thr - 0.02, thr - 0.01)} |",
        f"| [eşik−0,01, eşik−band) | {n_in(thr - 0.01, thr - band)} |",
        f"| [eşik−band, eşik) | {n_in(thr - band, thr)} |",
        f"| ≥ eşik | {int((ch >= thr).sum())} |",
        f"| < eşik−0,03 | {int((ch < thr - 0.03).sum())} |",
        "",
        "Aralıktaki ayrık p_after değerleri (eşik−0,04 ile eşik arası):",
        "",
        "| p_after | eşik − p_after | aday sayısı |",
        "|---|---|---|",
    ]
    for v in sorted(cand_steps):
        if thr - 0.04 < v < thr:
            L.append(f"| {v:.6f} | {thr - v:+.6f} | {cand_steps[v]} |")
    text = "\n".join(L) + "\n"
    REPORT.write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
