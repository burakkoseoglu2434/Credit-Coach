# ruff: noqa: E501  (report prose is long on purpose)
"""Calibration and selection check on the counteroffer candidate sets (calibration split and gap
months; the TEST split is never loaded). Engine, policy, catalog and cost.yaml are untouched.

The definition section of docs/demo_counteroffer_calibration_check.md was written and committed
BEFORE this computation; the report keeps it verbatim.

Usage: python -m credit_coach.counteroffer_calibration_check
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from credit_coach import baseline
from credit_coach.bundle import ROOT
from credit_coach.counteroffer_economics import (
    DEF_END,
    DELTAS,
    PERIODS,
    SEGMENTS,
    Cand,
    Cost,
    collect,
    d_label,
    definition_text,
    load_cost,
    pick,
    tablo,
    unit_value,
    usd,
)
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.modeling import dev_frame
from credit_coach.policy import load_policy
from credit_coach.recourse import load_demo_catalog
from credit_coach.recourse_gap_report import gap_frame
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.support import load_support

REPORT = ROOT / "docs" / "demo_counteroffer_calibration_check.md"
SEED, B = 7, 2000
MIN_BUCKET = 100
NB = 5
MISSING = (
    "Ham veri bulunamadı: {path}\n"
    "Bu rapor ham LendingClub CSV dosyasına ihtiyaç duyar (başvuru özellikleri ve skorlama)."
)


def boot_idx(n: int) -> np.ndarray:
    """(B, n) resample indices; the generator is restarted for every cell."""
    return np.random.default_rng(SEED).integers(0, n, size=(B, n))


def ci(stats: np.ndarray) -> tuple[float, float]:
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return float(lo), float(hi)


def mean_diff(sub: list[Cand]) -> tuple[float, float, float, tuple[float, float]]:
    """(mean p_point before, observed rate, observed - predicted, bootstrap CI of the difference)."""
    p = np.array([r.p0 for r in sub])
    y = np.array([r.y for r in sub], dtype=float)
    d = y - p
    return float(p.mean()), float(y.mean()), float(d.mean()), ci(d[boot_idx(len(sub))].mean(axis=1))


def edges(delta_point: np.ndarray) -> list[float]:
    return [float(x) for x in np.percentile(delta_point, [20, 40, 60, 80])]


def bucket_of(x: float, e: list[float]) -> int:
    """[e_k, e_k+1); the last bucket includes its upper bound."""
    return sum(1 for b in e if x >= b)


def slope_terms(sub: list[Cand], c: Cost) -> tuple[np.ndarray, np.ndarray]:
    a = np.array([r.l_new * unit_value(float(r.y), c) for r in sub])
    s = np.array([r.l_new * (r.p0 - r.p1) * (c.getiri + c.kayip) for r in sub])
    return a, s


def break_even_obs(t_obs: float, s: float) -> float:
    return -t_obs / s


def phi_text(t_obs: float, s: float) -> str:
    if t_obs >= 0:
        return "≤ 0,00"
    v = break_even_obs(t_obs, s)
    return ">1,00" if v > 1 else f"{v:.2f}".replace(".", ",")


def phi_ci_text(a: np.ndarray, s: np.ndarray) -> str:
    idx = boot_idx(len(a))
    t, sl = a[idx].sum(axis=1), s[idx].sum(axis=1)
    phis = -t / sl
    lo, hi = ci(phis)

    def f(v: float) -> str:
        return "≤ 0,00" if v <= 0 else (">1,00" if v > 1 else f"{v:.2f}".replace(".", ","))

    return f"[{f(lo)}; {f(hi)}]"


def f4(x: float) -> str:
    return f"{x:.4f}"


def f_ci(r: tuple[float, float]) -> str:
    return f"[{r[0]:+.4f}; {r[1]:+.4f}]"


def render(data: dict[str, dict[float, list[Cand]]], c: Cost, kat, tanim: str) -> str:
    t1 = [
        "| dilim | δ | segment | kayıt | ort. p_point (önce) | gözlenen temerrüt oranı | fark = gözlenen − tahmin | fark, bootstrap %95 aralığı |",
        "|---|---|---|---|---|---|---|---|",
    ]
    t2 = [
        "| dilim | δ | segment | kova | Δ_point aralığı | kayıt | ort. Δ_point | ort. p_point (önce) | gözlenen oran | fark = gözlenen − tahmin | fark, bootstrap %95 aralığı |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    t3 = [
        "| dilim | δ | segment | kayıt | T_gözlenen (USD) | T(1) (USD) | başa-baş φ | başa-baş φ, bootstrap %95 aralığı |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for per in PERIODS:
        for d in DELTAS:
            for seg, labs in SEGMENTS.items():
                sub = pick(data[per][d], labs)
                n = len(sub)
                head = f"| {per} | {d_label(d, kat)} | {seg} |"
                if n == 0:
                    t1.append(f"{head} 0 | - | - | - | - |")
                    t3.append(f"{head} 0 | - | - | - | - |")
                    t2.append(f"{head} - | - | 0 | - | - | - | - | - |")
                    continue
                p, y, df, rng = mean_diff(sub)
                t1.append(f"{head} {n} | {f4(p)} | {f4(y)} | {df:+.4f} | {f_ci(rng)} |")
                a, s = slope_terms(sub, c)
                t_obs, slope = float(a.sum()), float(s.sum())
                t3.append(
                    f"{head} {n} | {usd(t_obs)} | {usd(t_obs + slope)} | {phi_text(t_obs, slope)} | {phi_ci_text(a, s)} |"
                )
                if n < MIN_BUCKET:
                    t2.append(f"{head} n < {MIN_BUCKET} | - | {n} | - | - | - | - | - |")
                    continue
                dp = np.array([r.p0 - r.p1 for r in sub])
                e = edges(dp)
                bounds = [float(dp.min()), *e, float(dp.max())]
                which = np.array([bucket_of(x, e) for x in dp])
                for k in range(NB):
                    ks = [r for r, w in zip(sub, which, strict=True) if w == k]
                    if not ks:
                        t2.append(f"{head} {k + 1} | - | 0 | - | - | - | - | - |")
                        continue
                    pk, yk, dk, rk = mean_diff(ks)
                    close = "]" if k == NB - 1 else ")"
                    t2.append(
                        f"{head} {k + 1} | [{bounds[k]:.4f}; {bounds[k + 1]:.4f}{close} | {len(ks)} | "
                        f"{np.mean([r.p0 - r.p1 for r in ks]):.4f} | {f4(pk)} | {f4(yk)} | {dk:+.4f} | {f_ci(rk)} |"
                    )
    L = [
        "# Demo v0: karşı teklif adaylarında kalibrasyon ve seçilim kontrolü",
        "",
        KURGUSAL_VEREN,
        "",
        tanim.rstrip(),
        "",
        DEF_END,
        "",
        f"Test dilimi kullanılmadı. Bootstrap: {B} tekrar, seed {SEED}. Aday kümeleri `docs/demo_counteroffer_economics.md` ile aynıdır.",
        "",
        *tablo(
            "1. Segment içi kalibrasyon",
            "Aday kümelerinde modelin ortalama nokta tahmini ile gözlenen temerrüt oranı yan yana, farkın bootstrap aralığıyla.",
            "Fark, kümenin dışındaki kayıtlar ya da başka bir dilim için bir şey söylemez; aralık adayın seçilmesindeki belirsizliği içermez.",
            t1,
        ),
        *tablo(
            "2. Seçilim kontrolü: Δ_point kovaları",
            "Aday kayıtlar Δ_point'e göre beş eşit sayılı dilime ayrıldığında, her dilimde tahmin ve gözlenen oran farkı.",
            "Kova içi fark, Δ_point ile farkın nedenini göstermez; kovalar küçük kümelerde az kayıt içerir ve aralıklar geniştir.",
            t2,
        ),
        *tablo(
            "3. Gözlenen-temelli başa-baş φ",
            "φ = 0 başlangıcı gözlenen temerrütten, φ'ye bağlı değişim modelin Δ_point eğimiyle hesaplanan toplamın sıfır olduğu φ ve bootstrap aralığı.",
            "Eğim gözlenmedi, modelden alındı; '>1,00' etkinin tahmin edilenden büyük olması gerektiği bir senaryoyu gösterir, gerçek etkiyi ölçmez.",
            t3,
        ),
    ]
    return "\n".join(L) + "\n"


def build(csv_path=None, doc: str | None = None) -> str:
    pol, support, kat = load_policy("v1"), load_support(), load_demo_catalog()
    assert abs(DELTAS[0] - kat.delta) < 1e-12, (DELTAS, kat.delta)
    sc = ModelScorer()
    dev = dev_frame(pd.read_csv(csv_path or baseline.CSV))
    frames = {"kalibrasyon": dev[dev["split"] == "calibration"], "boşluk": gap_frame()}
    assert all("test" not in set(f["split"]) for f in frames.values())
    data = {per: collect(f, sc, pol, support, kat)[0] for per, f in frames.items()}
    tanim = definition_text(doc if doc is not None else REPORT.read_text(encoding="utf-8"))
    return render(data, load_cost(), kat, tanim)


def main(argv: list[str] | None = None) -> int:
    if not baseline.CSV.exists():
        print(MISSING.format(path=baseline.CSV), file=sys.stderr)
        return 2
    REPORT.write_text(build(baseline.CSV), encoding="utf-8")
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
