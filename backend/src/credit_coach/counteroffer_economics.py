# ruff: noqa: E501  (report prose is long on purpose)
"""Expected excess profit of the institution-path counteroffer (loan amount reduction).

Calibration split and gap months only; the TEST split is never loaded. Engine, policy and catalog
are untouched: plans and labels come from the existing `sec_from_scores` (p_high rule). The
economic value uses the POINT estimate (p_point), which is kept separate from that rule.

The definition section of docs/demo_counteroffer_economics.md was written and committed BEFORE
this computation; the report keeps it verbatim.

Usage: python -m credit_coach.counteroffer_economics   (writes docs/demo_counteroffer_economics.md)
"""

from __future__ import annotations

import sys
from typing import NamedTuple

import pandas as pd
import yaml

from credit_coach import baseline
from credit_coach.bundle import ROOT
from credit_coach.contract import OuterStatus, parse_input
from credit_coach.decision import COST_PATH, total_hurdle
from credit_coach.decision_engine import decide_with_support
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.modeling import dev_frame
from credit_coach.policy import load_policy
from credit_coach.recourse import PlanVar, hazirla, load_demo_catalog
from credit_coach.recourse import sec_from_scores as sec
from credit_coach.recourse_gap_report import gap_frame
from credit_coach.recourse_report import vektorler
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.support import load_support, violations

REPORT = ROOT / "docs" / "demo_counteroffer_economics.md"
PERIODS = ("kalibrasyon", "boşluk")
PHIS = (0.0, 0.25, 0.50, 0.75, 1.00)
DELTAS = (0.012, 0.03)  # 0.012 = catalog default (asserted in build)
SEGMENTS: dict[str, frozenset[str]] = {
    "(i) GUCLU": frozenset({"GUCLU"}),
    "(ii) GUCLU+KOSULLU": frozenset({"GUCLU", "KOSULLU"}),
    "(iii) planı geçerli olan hepsi": frozenset({"GUCLU", "KOSULLU", "ZAYIF"}),
}
MISSING = (
    "Ham veri bulunamadı: {path}\n"
    "Bu rapor ham LendingClub CSV dosyasına ihtiyaç duyar (başvuru özellikleri ve skorlama)."
)
DEF_START, DEF_END = "## Tanım", "## Sonuçlar"


class Cand(NamedTuple):
    """One rejected record whose institution-path plan is valid."""

    label: str  # resilience label of that plan (p_high rule)
    l_new: float  # L', new loan amount (USD)
    p0: float  # p_point before
    p1: float  # p_point after the plan
    y: int  # observed outcome (evaluation only): 1 = default


class Cost(NamedTuple):
    getiri: float
    kayip: float
    hurdle: float


def load_cost() -> Cost:
    doc = yaml.safe_load(COST_PATH.read_text())
    return Cost(
        float(doc["saglam_kredi_getirisi"]["mean"]),
        float(doc["temerrut_kaybi"]["mean"]),
        total_hurdle(doc),
    )


# ---- value ---------------------------------------------------------------------------------


def unit_value(p: float, c: Cost) -> float:
    """Per USD of L': (1 - p) * getiri - p * temerrüt_kaybı - hurdle."""
    return (1 - p) * c.getiri - p * c.kayip - c.hurdle


def p_phi(r: Cand, phi: float) -> float:
    return r.p0 - phi * (r.p0 - r.p1)


def value(r: Cand, phi: float, c: Cost) -> float:
    return r.l_new * unit_value(p_phi(r, phi), c)


def observed_value(r: Cand, c: Cost) -> float:
    return r.l_new * unit_value(float(r.y), c)


def pick(cands: list[Cand], labels: frozenset[str]) -> list[Cand]:
    return [r for r in cands if r.label in labels]


def total(cands: list[Cand], phi: float, c: Cost) -> float:
    return sum(value(r, phi, c) for r in cands)


def break_even(totals: list[float], phis: tuple[float, ...] = PHIS) -> float | None:
    """φ where the total crosses zero, linear interpolation between neighbouring grid points.
    None when the sign does not change on the grid."""
    pts = list(zip(phis, totals, strict=True))
    for (a, ta), (b, tb) in zip(pts, pts[1:], strict=False):
        if ta == 0.0:
            return a
        if (ta < 0) != (tb < 0) or tb == 0.0:
            return a + (b - a) * (0.0 - ta) / (tb - ta)
    return None


def break_even_text(totals: list[float]) -> str:
    be = break_even(totals)
    if be is not None:
        return f"{be:.3f}"
    return "yok (ızgarada toplam ≥ 0)" if totals[0] >= 0 else "yok (ızgarada toplam < 0)"


# ---- collection ----------------------------------------------------------------------------


def collect(
    frame: pd.DataFrame, sc, pol, support, kat, deltas: tuple[float, ...] = DELTAS
) -> tuple[dict[float, list[Cand]], int]:
    """Institution-path candidates per δ, and the number of v1-REJECTED (in-support) records."""
    out: dict[float, list[Cand]] = {d: [] for d in deltas}
    n_rej = 0
    for _m, grp in frame.groupby(frame["issue_date"].dt.to_period("M"), sort=True):
        tarih = grp["issue_date"].iloc[0]
        recs = vektorler(grp)
        ys = grp["target"].astype(int).tolist()
        base = sc.skorla_toplu(recs, tarih)
        rej = []
        for b, s, y in zip(recs, base, ys, strict=True):
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
                rej.append((b, s, y))
        n_rej += len(rej)
        hz = [hazirla(b, kat) for b, _s, _y in rej]
        flat = [a.vektor for _t, tum in hz for a in tum]
        sk = sc.skorla_toplu(flat, tarih) if flat else []
        pos = 0
        for (b, bs, y), h in zip(rej, hz, strict=True):
            n = len(h[1])
            cs = sk[pos : pos + n]
            pos += n
            for d in deltas:
                res = sec(b, h, bs, cs, pol, support, kat, d)
                if not isinstance(res.sonuc, PlanVar):
                    continue
                yol = next((p for p in res.sonuc.yollar if p.yol_tipi == "institution"), None)
                if yol is None:
                    continue
                assert [e for e, _ in yol.eylemler] == ["loan_amount_reduction"], yol.eylemler
                aday = next(a for a, _s in res.gecerli if a.plan_id == yol.plan_id)
                out[d].append(
                    Cand(
                        yol.dayaniklilik,
                        float(aday.vektor["loan_amnt"]),
                        float(bs.p_point),
                        float(yol.p_point),
                        y,
                    )
                )
    return out, n_rej


# ---- rendering -----------------------------------------------------------------------------


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


def usd(x: float) -> str:
    return f"{x:,.0f}"


def definition_text(doc: str) -> str:
    """The committed definition section, verbatim."""
    start = doc.index(DEF_START)
    end = doc.find(DEF_END, start)
    return doc[start : end if end >= 0 else len(doc)].rstrip() + "\n"


def d_label(d: float, kat) -> str:
    return f"{d:g}" + (" (varsayılan)" if abs(d - kat.delta) < 1e-12 else "")


def render(
    data: dict[str, dict[float, list[Cand]]], n_rej: dict[str, int], c: Cost, kat, tanim: str
) -> str:
    grid = [
        "| dilim | δ | segment | φ | kayıt | ort. L' (USD) | toplam beklenen fazla kâr (USD) | kayıt başına (USD) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    be = [
        "| dilim | δ | segment | kayıt | başa-baş φ |",
        "|---|---|---|---|---|",
    ]
    ck = [
        "| dilim | δ | segment | kayıt | ort. p_point (önce) | gözlenen temerrüt oranı | toplam, p_point (φ = 0) | toplam, gözlenen | kayıt başına, p_point | kayıt başına, gözlenen |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    nd = [
        "| dilim | δ | segment | kayıt | Δ_point ≤ 0 olan kayıt | ort. Δ_point |",
        "|---|---|---|---|---|---|",
    ]
    for per in PERIODS:
        for d in DELTAS:
            cands = data[per][d]
            for seg, labs in SEGMENTS.items():
                sub = pick(cands, labs)
                n = len(sub)
                mean_l = sum(r.l_new for r in sub) / n if n else 0.0
                tots = []
                for phi in PHIS:
                    t = total(sub, phi, c)
                    tots.append(t)
                    grid.append(
                        f"| {per} | {d_label(d, kat)} | {seg} | {phi:.2f} | {n} | {usd(mean_l)} | {usd(t)} | "
                        + (f"{t / n:,.1f}" if n else "-")
                        + " |"
                    )
                be.append(f"| {per} | {d_label(d, kat)} | {seg} | {n} | {break_even_text(tots)} |")
                t_obs = sum(observed_value(r, c) for r in sub)
                ck.append(
                    f"| {per} | {d_label(d, kat)} | {seg} | {n} | "
                    + (
                        f"{sum(r.p0 for r in sub) / n:.4f} | {sum(r.y for r in sub) / n:.4f} | "
                        if n
                        else "- | - | "
                    )
                    + f"{usd(tots[0])} | {usd(t_obs)} | "
                    + (f"{tots[0] / n:,.1f} | {t_obs / n:,.1f} |" if n else "- | - |")
                )
                neg = sum(1 for r in sub if r.p0 - r.p1 <= 0)
                nd.append(
                    f"| {per} | {d_label(d, kat)} | {seg} | {n} | {neg} | "
                    + (f"{sum(r.p0 - r.p1 for r in sub) / n:.4f} |" if n else "- |")
                )
    cohort = [
        "| dilim | v1 REJECTED (destek içi) | "
        + " | ".join(f"δ = {d_label(d, kat)}: kurum yolu planı geçerli" for d in DELTAS)
        + " |",
        "|---|---|" + "---|" * len(DELTAS),
    ]
    for per in PERIODS:
        cohort.append(
            f"| {per} | {n_rej[per]} | " + " | ".join(str(len(data[per][d])) for d in DELTAS) + " |"
        )
    par = [
        "| parametre | değer | kaynak |",
        "|---|---|---|",
        f"| getiri | {c.getiri:.4f} | `configs/cost.yaml`, `saglam_kredi_getirisi.mean` (varsayım) |",
        f"| temerrüt kaybı | {c.kayip:.4f} | `configs/cost.yaml`, `temerrut_kaybi.mean` (varsayım) |",
        f"| hurdle (toplam) | {c.hurdle:.4f} | `configs/cost.yaml`, asgari marj + fon maliyeti + işletme gideri (tez varsayımı) |",
        f"| birim değer, p = 0 | {unit_value(0.0, c):.4f} | getiri − hurdle |",
        f"| başa-baş p | {(c.getiri - c.hurdle) / (c.getiri + c.kayip):.4f} | (getiri − hurdle) / (getiri + temerrüt kaybı) |",
    ]
    L = [
        "# Demo v0: kurum yolu karşı teklifinin beklenen fazla kârı",
        "",
        KURGUSAL_VEREN,
        "",
        tanim.rstrip(),
        "",
        DEF_END,
        "",
        "Test dilimi kullanılmadı. Müşteri kabul oranı 1 varsayılır; toplamlar ve kayıt başına değer kabul oranıyla doğrusal ölçeklenir. Kayıt sayıları tam sayıdır, USD değerleri yuvarlanmıştır.",
        "",
        *tablo(
            "1. Parametreler",
            "Hesapta kullanılan getiri, temerrüt kaybı ve hurdle; yapılandırmadan okundu.",
            "Bu değerler ölçülmüş fiyatlama değil, varsayımdır; gerçek bir kurumun getirisini ya da kaybını göstermez.",
            par,
        ),
        *tablo(
            "2. Aday kümesi",
            "Dilim başına v1 tarafından reddedilen kayıt sayısı ve δ başına, kurum yolu (karşı teklif) planı geçerli olan kayıt sayısı.",
            "Aday kümesi bir öneri listesi değildir; müşterinin teklifi kabul edeceği anlamına gelmez.",
            cohort,
        ),
        *tablo(
            "3. Segment × φ × δ",
            "Her segment, φ ve δ için kayıt sayısı, ortalama yeni tutar, nokta tahminiyle toplam beklenen fazla kâr ve kayıt başına değer; reddetmenin değeri 0 alındı.",
            "Gerçekleşen kâr değildir; p_point = p_önce − φ·Δ_point varsayımına ve cost.yaml varsayımlarına bağlıdır, φ bilinmeyen bir etki payıdır.",
            grid,
        ),
        *tablo(
            "4. Başa-baş φ",
            "Segment ve δ başına toplam beklenen fazla kârın sıfır olduğu φ; ızgara noktaları arasında doğrusal enterpolasyon.",
            "Gerçek etki payının bu değeri aşacağı ya da aşmayacağı anlamına gelmez; tek başına bir karar kuralı değildir.",
            be,
        ),
        *tablo(
            "5. Çapraz kontrol: φ = 0, p_point ile gözlenen sonuç",
            "φ = 0'da aynı değer formülünün, modelin nokta tahmini ile kaydın gözlenen sonucu (etiketler yalnızca değerlendirme için) kullanılarak hesaplanmış hâli yan yana.",
            "Gözlenen sonuç kaydın özgün kredi tutarındaki sonucudur, L' tutarında bir sonucu ölçmez; iki sütunun yakınlığı etki payı hakkında bilgi vermez.",
            ck,
        ),
        *tablo(
            "6. Δ_point ≤ 0 olan kayıtlar",
            "Planın nokta tahmininde düşüş göstermeyen (Δ_point ≤ 0) kayıt sayısı ve ortalama Δ_point; formül bu kayıtlara da olduğu gibi uygulandı.",
            "Bu sayı etiket ya da geçerlilik kuralının bir parçası değildir; o kural p_high üzerindedir ve burada değiştirilmedi.",
            nd,
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
    data, n_rej = {}, {}
    for per, f in frames.items():
        data[per], n_rej[per] = collect(f, sc, pol, support, kat)
    tanim = definition_text(doc if doc is not None else REPORT.read_text(encoding="utf-8"))
    return render(data, n_rej, load_cost(), kat, tanim)


def main(argv: list[str] | None = None) -> int:
    if not baseline.CSV.exists():
        print(MISSING.format(path=baseline.CSV), file=sys.stderr)
        return 2
    text = build(baseline.CSV)
    REPORT.write_text(text, encoding="utf-8")
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
