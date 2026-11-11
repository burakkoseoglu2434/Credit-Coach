# ruff: noqa: E501  (report prose is long on purpose)
"""Target-segment report (calibration split and gap months; the TEST split is never loaded):
strongest-path resilience label by p_point - threshold bucket, delta in {0 (inside the band), 0.03},
dti update off. Also states, from the live config/files, which delta the API and the UI use.

Usage: python -m credit_coach.target_segment   (writes docs/demo_target_segment.md)
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
from credit_coach.recourse import PlanVar, hazirla, load_demo_catalog
from credit_coach.recourse import sec_from_scores as sec
from credit_coach.recourse_gap_report import gap_frame
from credit_coach.recourse_report import _pct, vektorler
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.report_deltas import delta_etiketi, delta_notu, report_deltas, varsayilan_delta
from credit_coach.resilience_report import DELTAS, LABELS, PERIODS, strongest
from credit_coach.scoring_service import LABELS as BUCKETS
from credit_coach.scoring_service import bucket
from credit_coach.support import load_support, violations

REPORT = ROOT / "docs" / "demo_target_segment.md"
MISSING = (
    "Ham veri bulunamadı: {path}\n"
    "Bu rapor ham LendingClub CSV dosyasına ihtiyaç duyar (başvuru özellikleri ve skorlama)."
)
COLS = ("PLAN_YOK", *LABELS)

# one rejected record: (p_point - threshold bucket, label per path type that has a plan)
Rec = tuple[str, dict[str, str]]


def collect(frame: pd.DataFrame, sc, pol, support, kat) -> dict[float, list[Rec]]:
    thr = pol.onay_esigi
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
            kova = bucket(bs.p_point - thr)
            for d in DELTAS:
                res = sec(b, h, bs, cs, pol, support, kat, d)
                labels = (
                    {y.yol_tipi: y.dayaniklilik for y in res.sonuc.yollar}
                    if isinstance(res.sonuc, PlanVar)
                    else {}
                )
                out[d].append((kova, labels))
    return out


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


def delta_facts() -> list[str]:
    """Where the default delta lives and where it is (not) visible; read from the live files."""
    kat = load_demo_catalog()
    openapi = (ROOT / "frontend" / "openapi.json").read_text()
    src = ROOT / "frontend" / "src" / "components"
    ui_yerleri = [
        yer
        for yer, dosya in (("sonuç sayfası", "Sonuc.tsx"), ("toplu özet", "Toplu.tsx"))
        if (src / dosya).exists() and "guvenlik_payi" in (src / dosya).read_text()
    ]
    api_gorunur = (
        'evet: `guvenlik_payi` alanı (değer, "varsayım" etiketi, kaynak ADR-007)'
        if "guvenlik_payi" in openapi
        else "hayır (yanıt şemasında δ alanı yok)"
    )
    ui_gorunur = (
        "evet: "
        + " ve ".join(ui_yerleri)
        + " (API değeri olduğu gibi gösterilir, arayüz hesaplamaz)"
        if ui_yerleri
        else 'hayır (arayüz δ değerini göstermez; metinlerde yalnızca "güvenli payla" ifadesi geçer)'
    )
    return [
        "| öğe | değer / durum |",
        "|---|---|",
        f"| Varsayılan δ | {kat.delta:g} (etiket: {str(kat.raw['delta']['etiket']).replace('|', chr(92) + '|')}) |",
        "| Tanımlandığı yer | `configs/catalog/demo_v0.yaml`, `delta.deger`; `bundle.lock.json` bu dosyanın hash'ini taşır; türetme kuralı `docs/adr/007-safety-margin.md` |",
        "| API'nin kullandığı değer | `/score` ve `/batch`, `sec_from_scores` çağrısına δ vermez; motor katalogdaki varsayılanı kullanır (`recourse.sec`, `delta=None`) |",
        f"| API yanıtında görünür mü | {api_gorunur}; ayrıca dolaylı iz: `surumler.katalog_sha256` |",
        f"| Arayüzde görünür mü | {ui_gorunur} |",
        "| Bu raporun sütunları | "
        + ", ".join(delta_etiketi(d, kat) for d in report_deltas(kat))
        + " |",
    ]


def render(data: dict[str, dict[float, list[Rec]]], kat, pol) -> str:
    g = [
        "| dilim | δ | kova (p_point − eşik) | reddedilen | PLAN_YOK | GUCLU | KOSULLU | ZAYIF |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for p in PERIODS:
        for d in sorted(data[p]):
            recs = data[p][d]
            for kova in [*BUCKETS, "tümü"]:
                sub = [r for r in recs if kova == "tümü" or r[0] == kova]
                if not sub:
                    continue
                c = Counter(strongest(lab) for _k, lab in sub)
                n = len(sub)
                g.append(
                    f"| {p} | {delta_etiketi(d, kat)} | {kova} | {n} "
                    + " ".join(f"| {_pct(c[k], n)}" for k in COLS)
                    + " |"
                )
    L = [
        f"# Demo v0: hedef segment (p_point − eşik kovasına göre en güçlü yol etiketi; {varsayilan_delta(kat)})",
        "",
        KURGUSAL_VEREN,
        "",
        delta_notu(kat),
        "",
        "Kapsam: kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08); test dilimi "
        f"kullanılmadı. Reddedilen = v1 REJECTED (destek içi). dti güncellemesi kapalı. Eşik {pol.onay_esigi:.4f}, "
        f"band {pol.band:.4f}. Etiket = kaydın planı olan yolları içinde en güçlü olanı.",
        "",
        *tablo(
            "1. Kovaya göre en güçlü yol etiketi",
            "Modelin bugünkü risk tahmininin eşiğe uzaklığına göre, reddedilen kayıtların hangi payında hiç plan çıkmadığı (PLAN_YOK) ve planı olanlarda en güçlü yolun etiketi.",
            "Kova bir hedef kitle ya da öncelik önerisi değildir; etiket planın gerçekte işe yarayacağını söylemez, gerçek etki payı bilinmiyor.",
            g,
        ),
        *tablo(
            "2. Varsayılan δ: API ve arayüz",
            "API ve arayüzün plan ararken hangi δ'yı kullandığı ve bu değerin nerede görünür olduğu; değerler canlı dosyalardan okundu.",
            "δ ölçülmüş bir kapsama değil, ADR-007 kuralıyla türetilen bir varsayımdır; varsayılan δ bu raporda ayrı bir sütun olarak yer alır.",
            delta_facts(),
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
