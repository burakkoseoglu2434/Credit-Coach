# ruff: noqa: E501  (report prose is long on purpose)
"""Resilience-label distribution (calibration split and gap months; the TEST split is never
loaded): delta in {0 (inside the band), 0.03}, dti update off.

Usage: python -m credit_coach.resilience_report   (writes docs/demo_resilience_labels.md)
"""

from __future__ import annotations

import sys
from collections import Counter

import pandas as pd

from credit_coach import baseline
from credit_coach.bundle import ROOT
from credit_coach.contract import OuterStatus, parse_input
from credit_coach.decision_engine import decide_with_support
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.modeling import dev_frame
from credit_coach.policy import load_policy
from credit_coach.recourse import PATH_ORDER, Katalog, PlanVar, hazirla, load_demo_catalog
from credit_coach.recourse import sec_from_scores as sec
from credit_coach.recourse_gap_report import gap_frame
from credit_coach.recourse_report import _pct, vektorler
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.support import load_support, violations

REPORT = ROOT / "docs" / "demo_resilience_labels.md"
DELTAS = (0.0, 0.03)
DELTA_LABEL = {0.0: "δ = 0 (band içi: etkin kesim eşik − band)", 0.03: "δ = 0,03"}
PERIODS = ("kalibrasyon", "boşluk")
LABELS = ("GUCLU", "KOSULLU", "ZAYIF")
MISSING = (
    "Ham veri bulunamadı: {path}\n"
    "Bu rapor ham LendingClub CSV dosyasına ihtiyaç duyar (başvuru özellikleri ve skorlama)."
)

# one record: label per path type that has a plan ({} = PLAN_YOK)
Rec = dict[str, str]


def collect(frame: pd.DataFrame, sc, pol, support, kat) -> dict[float, list[Rec]]:
    out: dict[float, list[Rec]] = {d: [] for d in DELTAS}
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
                res = sec(b, h, bs, cs, pol, support, kat, d)
                out[d].append(
                    {y.yol_tipi: y.dayaniklilik for y in res.sonuc.yollar}
                    if isinstance(res.sonuc, PlanVar)
                    else {}
                )
    return out


def strongest(rec: Rec) -> str:
    """Strongest label over the record's paths, or PLAN_YOK."""
    if not rec:
        return "PLAN_YOK"
    return min(rec.values(), key=LABELS.index)


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


def render(data: dict[str, dict[float, list[Rec]]], kat: Katalog, pol) -> str:
    g1 = [
        "| dilim | δ | reddedilen | PLAN_YOK | GUCLU | KOSULLU | ZAYIF |",
        "|---|---|---|---|---|---|---|",
    ]
    g2 = [
        "| dilim | δ | yol | planı olan kayıt | GUCLU | KOSULLU | ZAYIF |",
        "|---|---|---|---|---|---|---|",
    ]
    for p in PERIODS:
        for d in DELTAS:
            recs = data[p][d]
            c = Counter(strongest(r) for r in recs)
            n = len(recs)
            g1.append(
                f"| {p} | {DELTA_LABEL[d]} | {n} | {c['PLAN_YOK']} ({_pct(c['PLAN_YOK'], n)}) "
                + " ".join(f"| {c[k]} ({_pct(c[k], n)})" for k in LABELS)
                + " |"
            )
            for t in PATH_ORDER:
                lab = Counter(r[t] for r in recs if t in r)
                m = sum(lab.values())
                g2.append(
                    f"| {p} | {DELTA_LABEL[d]} | {t} | {m} "
                    + " ".join(f"| {lab[k]} ({_pct(lab[k], m)})" for k in LABELS)
                    + " |"
                )
    g3 = [
        "| etiket | koşul (min_phi) | durum |",
        "|---|---|---|",
        f"| GUCLU | ≤ {kat.guclu_en_fazla:.2f} | varsayım |",
        f"| KOSULLU | > {kat.guclu_en_fazla:.2f} ve ≤ {kat.kosullu_en_fazla:.2f} | varsayım |",
        f"| ZAYIF | > {kat.kosullu_en_fazla:.2f} | varsayım |",
    ]
    L = [
        "# Demo v0: dayanıklılık etiketi dağılımı",
        "",
        KURGUSAL_VEREN,
        "",
        "Kapsam: kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08); test "
        "dilimi kullanılmadı. Reddedilen = v1 REJECTED (destek içi). dti güncellemesi kapalı. "
        f"Eşik {pol.onay_esigi:.4f}, band {pol.band:.4f}.",
        "",
        *tablo(
            "1. Kayıt başına en güçlü yolun etiketi (reddedilenler içinde)",
            "Her reddedilen kayıt için, planı olan yollar içinde en güçlü etiketin dağılımı; planı "
            "olmayanlar PLAN_YOK'ta sayılır.",
            "GUCLU, planın gerçekte işe yarayacağı anlamına gelmez; yalnızca modelin öngördüğü "
            "etkinin yarısı ya da daha azının yeterli olduğunu söyler. Gerçek etki payı bilinmiyor.",
            g1,
        ),
        *tablo(
            "2. Yol türüne göre etiket dağılımı",
            "Her yol türünün en ucuz geçerli planının etiketi; yalnızca o yolda planı olan kayıtlar sayılır.",
            "Yollar birbiriyle sıralanmadı; bir yol türünde çok GUCLU etiketin olması o yolun diğerinden "
            "iyi olduğunu göstermez.",
            g2,
        ),
        *tablo(
            "3. Etiket eşikleri",
            "Etiketin hangi minimum etki payı aralığına karşılık geldiği (yapılandırmadan okunur).",
            "Eşikler ölçülmedi; insan kararıdır ve varsayımdır.",
            g3,
        ),
    ]
    return "\n".join(L) + "\n"


def build(csv_path=None) -> str:
    pol, support, kat = load_policy("v1"), load_support(), load_demo_catalog()
    sc = ModelScorer()
    dev = dev_frame(pd.read_csv(csv_path or baseline.CSV))
    frames = {"kalibrasyon": dev[dev["split"] == "calibration"], "boşluk": gap_frame()}
    assert all("test" not in set(f["split"]) for f in frames.values())
    data = {p: collect(f, sc, pol, support, kat) for p, f in frames.items()}
    return render(data, kat, pol)


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
