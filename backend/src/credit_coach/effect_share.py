# ruff: noqa: E501  (report prose is long on purpose)
"""Effect-share sensitivity (calibration split and gap months; the TEST split is never loaded).

For every rejected record and every plan that is valid in the model (engine, delta fixed):
  Delta = p_before - p_after_model        (both p_high)
  p_after_real(phi) = p_before - phi * Delta,  phi in {0.25, 0.50, 0.75, 1.00}
A plan counts as valid at phi when p_after_real < threshold - max(delta, band). The band term is
the same one the decision rule R2 applies: at delta = 0 the effective cut is threshold - band.
phi = 1 therefore reproduces the engine; smaller phi can only remove plans, so only plans that
are valid at phi = 1 need to be kept.

Usage: python -m credit_coach.effect_share   (writes docs/demo_effect_share.md)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

from credit_coach import baseline
from credit_coach.bundle import ROOT
from credit_coach.contract import OuterStatus, parse_input
from credit_coach.decision_engine import decide_with_support
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.modeling import dev_frame
from credit_coach.policy import Policy, load_policy
from credit_coach.recourse import (
    PATH_ORDER,
    hazirla,
    imza,
    load_demo_catalog,
    sec_from_scores,
    yol_tipi,
)
from credit_coach.recourse_gap_report import gap_frame
from credit_coach.recourse_report import _pct, vektorler
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.scoring_service import LABELS, bucket
from credit_coach.support import load_support, violations

REPORT = ROOT / "docs" / "demo_effect_share.md"
PHIS = (0.25, 0.50, 0.75, 1.00)
DELTAS = (0.0, 0.03)
DELTA_LABEL = {0.0: "δ = 0 (band içi: etkin kesim eşik − band)", 0.03: "δ = 0,03"}
PERIODS = ("kalibrasyon", "boşluk")
PERCENTILES = (5, 25, 50, 75, 95)


# ---- pure functions (CI-tested) ----------------------------------------------------------


def cut(thr: float, delta: float, band: float) -> float:
    """Validity cut: p_after < thr - max(delta, band) (R2 already rules out the band)."""
    return thr - max(delta, band)


def p_after_real(p_before: float, dp: float, phi: float) -> float:
    return p_before - phi * dp


def phi_min(p_before: float, dp: float, kesim: float) -> float:
    """Smallest effect share at which the plan reaches the cut (infimum: valid for phi > this)."""
    return (p_before - kesim) / dp


@dataclass(frozen=True)
class Kayit:
    bucket: str  # p_point - threshold bucket of the baseline score
    p_before: float  # baseline p_high
    planlar: tuple[tuple[str, float], ...]  # (path type, Delta) of every plan valid at phi = 1


def valid_at(k: Kayit, phi: float, kesim: float, tip: str | None = None) -> bool:
    return any(
        p_after_real(k.p_before, dp, phi) < kesim for t, dp in k.planlar if tip is None or t == tip
    )


def min_phi(k: Kayit, kesim: float, tip: str | None = None) -> float | None:
    """Minimum effect share over the record's plans (None when no plan is valid at phi = 1)."""
    vals = [phi_min(k.p_before, dp, kesim) for t, dp in k.planlar if tip is None or t == tip]
    return min(vals) if vals else None


# ---- data collection (needs the raw CSV) -------------------------------------------------


def collect(frame: pd.DataFrame, sc: ModelScorer, pol: Policy, support, kat) -> dict:
    thr = pol.onay_esigi
    kayitlar: dict[float, list[Kayit]] = {d: [] for d in DELTAS}
    for _m, grp in frame.groupby(frame["issue_date"].dt.to_period("M"), sort=True):
        tarih = grp["issue_date"].iloc[0]
        recs = vektorler(grp)
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
        hz = [hazirla(b, kat) for b, _s in rej]
        flat = [a.vektor for _t, tum in hz for a in tum]
        sk = sc.skorla_toplu(flat, tarih) if flat else []
        pos = 0
        for (b, bs), h in zip(rej, hz, strict=True):
            n = len(h[1])
            cs = sk[pos : pos + n]
            pos += n
            for d in DELTAS:
                res = sec_from_scores(b, h, bs, cs, pol, support, kat, d)
                planlar = tuple(
                    (yol_tipi(imza([e for e, _ in a.eylemler], kat)), bs.p_high - s2.p_high)
                    for a, s2 in res.gecerli
                )
                kayitlar[d].append(Kayit(bucket(bs.p_point - thr), bs.p_high, planlar))
    return kayitlar


# ---- tables -------------------------------------------------------------------------------


def _phi(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def tablo(baslik: str, anlami: str, anlam_degil: str, govde: list[str]) -> list[str]:
    return [
        f"## {baslik}",
        "",
        *govde,
        "",
        f"> **Bu tablo ne demek:** {anlami}",
        "",
        f"> **Ne DEMEK DEĞİL:** {anlam_degil}",
        "",
    ]


def rate_tables(data: dict[str, dict[float, list[Kayit]]], pol: Policy) -> list[str]:
    L: list[str] = []
    g = [
        "| dilim | δ | φ | reddedilen | en az bir yolda plan | müşteri | karma | kurum |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for p in PERIODS:
        for d in DELTAS:
            ks, kesim = data[p][d], cut(pol.onay_esigi, d, pol.band)
            for phi in PHIS:
                n = len(ks)
                any_ = sum(valid_at(k, phi, kesim) for k in ks)
                per = [sum(valid_at(k, phi, kesim, t) for k in ks) for t in PATH_ORDER]
                g.append(
                    f"| {p} | {DELTA_LABEL[d]} | {_phi(phi)} | {n} | {_pct(any_, n)} "
                    + " ".join(f"| {_pct(v, n)}" for v in per)
                    + " |"
                )
    L += tablo(
        "1. Geçerli planı olan reddedilen oranı, etki payı φ'ye göre",
        "Modelin öngördüğü risk düşüşünün yalnızca φ kadarı gerçekleşseydi, hâlâ eşiğin "
        "(δ ile) altına inen planı olan reddedilen payı. φ = 1,00 satırı motorun sonucudur.",
        "φ gerçek etkinin ölçüsü değildir; gerçek etki doğrulanmadı ve φ'nin hangi değerde "
        "olduğu bilinmiyor. Bir satır, o etki payında planın işe yarayacağını söylemez.",
        g,
    )
    g = [
        "| dilim | δ | kova (p_point − eşik) | reddedilen | φ = 0,25 | φ = 0,50 | φ = 0,75 | φ = 1,00 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for p in PERIODS:
        for d in DELTAS:
            ks, kesim = data[p][d], cut(pol.onay_esigi, d, pol.band)
            for lab in LABELS:
                sub = [k for k in ks if k.bucket == lab]
                if sub:
                    g.append(
                        f"| {p} | {DELTA_LABEL[d]} | {lab} | {len(sub)} "
                        + " ".join(
                            f"| {_pct(sum(valid_at(k, phi, kesim) for k in sub), len(sub))}"
                            for phi in PHIS
                        )
                        + " |"
                    )
    L += tablo(
        "2. Geçerli plan oranı, p_point − eşik kovasına ve φ'ye göre",
        "Eşiğe uzaklık ve etki payı birlikte değiştiğinde planı olan kayıt payı.",
        "Kova, ne kadar çaba gerektiğini ölçmez; yalnızca modelin bugünkü risk tahmininin "
        "eşiğe uzaklığıdır.",
        g,
    )
    return L


def min_phi_tables(data: dict[str, dict[float, list[Kayit]]], pol: Policy) -> list[str]:
    g = [
        "| dilim | δ | reddedilen | φ = 1,00'de plan var | φ = 1,00'de plan yok | "
        + " | ".join(f"%{q}" for q in PERCENTILES)
        + " | ortalama |",
        "|---|---|---|---|---|" + "---|" * (len(PERCENTILES) + 1),
    ]
    for p in PERIODS:
        for d in DELTAS:
            ks, kesim = data[p][d], cut(pol.onay_esigi, d, pol.band)
            vals = [v for k in ks if (v := min_phi(k, kesim)) is not None]
            n = len(ks)
            qs = np.percentile(vals, PERCENTILES) if vals else [float("nan")] * len(PERCENTILES)
            g.append(
                f"| {p} | {DELTA_LABEL[d]} | {n} | {len(vals)} ({_pct(len(vals), n)}) | "
                f"{n - len(vals)} ({_pct(n - len(vals), n)}) | "
                + " | ".join(_phi(float(q)) for q in qs)
                + f" | {_phi(float(np.mean(vals))) if vals else '-'} |"
            )
    g += [
        "",
        "Yol türüne göre medyan gereken φ (yalnızca o yolda planı olan kayıtlar):",
        "",
        "| dilim | δ | müşteri | karma | kurum |",
        "|---|---|---|---|---|",
    ]
    for p in PERIODS:
        for d in DELTAS:
            ks, kesim = data[p][d], cut(pol.onay_esigi, d, pol.band)
            cells = []
            for t in PATH_ORDER:
                v = [x for k in ks if (x := min_phi(k, kesim, t)) is not None]
                cells.append(f"{_phi(float(np.median(v)))} (n={len(v)})" if v else "-")
            g.append(f"| {p} | {DELTA_LABEL[d]} | " + " | ".join(cells) + " |")
    return tablo(
        "3. Planın geçerli olması için gereken minimum etki payı φ",
        "Her reddedilen kayıt için, en az bir planının eşiğin (δ ile) altına inmesi için modelin "
        "öngördüğü düşüşün en az hangi kesrinin gerçekleşmesi gerektiği; dağılım bu kesirlerin "
        "yüzdelikleridir. φ = 1,00'de bile planı olmayan kayıtlar ayrı sayılır.",
        "Düşük bir değer, planın gerçekte işe yarayacağı anlamına gelmez; yalnızca eşiğe "
        "uzaklığın modelin öngördüğü düşüşe oranıdır. Gereken φ'nin altında kalan gerçek etki "
        "planı geçersiz kılar, ama gerçek etkinin ne olduğu bu raporda bilinmiyor.",
        g,
    )


def build(csv_path=None) -> str:
    pol, support, kat = load_policy("v1"), load_support(), load_demo_catalog()
    sc = ModelScorer()
    dev = dev_frame(pd.read_csv(csv_path or baseline.CSV))
    frames = {"kalibrasyon": dev[dev["split"] == "calibration"], "boşluk": gap_frame()}
    assert all("test" not in set(f["split"]) for f in frames.values())
    data = {p: collect(f, sc, pol, support, kat) for p, f in frames.items()}
    L = [
        "# Demo v0: etki payı duyarlılık eğrisi",
        "",
        KURGUSAL_VEREN,
        "",
        "Kapsam: kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08); "
        "test dilimi kullanılmadı. Reddedilen = v1 REJECTED (destek içi). dti güncellemesi kapalı.",
        "",
        "Tanım: model içi plan etkisi Δ = p_önce − p_sonra_model (ikisi de p_high). Gerçek etki payı "
        "φ için p_sonra_gerçek = p_önce − φ·Δ. Plan, p_sonra_gerçek < eşik − δ olduğunda geçerli "
        f"sayılır; eşik {pol.onay_esigi:.4f}, band {pol.band:.4f}. δ = 0'da etkin kesim "
        "eşik − band'dır (karar kuralı R2). φ = 1,00 motorun mevcut sonucuyla aynıdır.",
        "",
        *rate_tables(data, pol),
        *min_phi_tables(data, pol),
    ]
    return "\n".join(L) + "\n"


MISSING = (
    "Ham veri bulunamadı: {path}\n"
    "Bu rapor ham LendingClub CSV dosyasına ihtiyaç duyar (başvuru özellikleri ve skorlama)."
)


def main(argv: list[str] | None = None) -> int:
    if not baseline.CSV.exists():
        print(MISSING.format(path=baseline.CSV), file=sys.stderr)
        return 2
    text = build(baseline.CSV)
    REPORT.write_text(text)
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
