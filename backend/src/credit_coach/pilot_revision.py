# ruff: noqa: E501  (report prose is long on purpose)
"""Pilot protocol revision 1 (post-hoc): minimum detectable effect, nominal principal and loss tail,
candidate flow. Calibration split and gap months only; the TEST split is never loaded. Engine, policy,
catalog and cost.yaml are untouched.

The "Revizyon tanımı" part of docs/pilot_protocol_v0.md was written and committed BEFORE this
computation; this module keeps it verbatim and regenerates only the "Revizyon sonuçları" part. The
text above the revision section is not touched. Also rewrites configs/pilot.yaml (labels + revizyon_1).

Usage: python -m credit_coach.pilot_revision
"""

from __future__ import annotations

import math
import sys
from statistics import NormalDist

import numpy as np
import pandas as pd
import yaml

from credit_coach import baseline
from credit_coach.counteroffer_economics import (
    DELTAS,
    PHIS,
    Cand,
    Cost,
    collect,
    d_label,
    load_cost,
    pick,
    tablo,
    usd,
)
from credit_coach.modeling import dev_frame
from credit_coach.pilot_protocol import (
    ALPHA,
    CONFIG,
    REPORT,
    SEGMENTS,
    moments,
    pre_hurdle_mean,
)
from credit_coach.policy import load_policy
from credit_coach.recourse import load_demo_catalog
from credit_coach.recourse_gap_report import gap_frame
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.support import load_support

REV_START = "## Revizyon 1 (sonradan)"
RES_START = "### Revizyon sonuçları"
POWER = 0.8
N_REV = (250, 500, 1000, 2000)
SCALES = (1.0, 0.1, 0.01)
ACCEPT_REV = (1.0, 0.7, 0.5, 0.3)
MC_REPS = 20_000
MC_SEED = 7
MC_CHUNK = 1000
PERCENTILES = (5, 1)
RULE_LABEL = "varsayım, kural çıktısı, uygulanabilir değil"
MISSING = (
    "Ham veri bulunamadı: {path}\n"
    "Bu rapor ham LendingClub CSV dosyasına ihtiyaç duyar (başvuru özellikleri ve skorlama)."
)


# ---- calculation ---------------------------------------------------------------------------


def z_total(power: float = POWER, alpha: float = ALPHA) -> float:
    return NormalDist().inv_cdf(1 - alpha) + NormalDist().inv_cdf(power)


def mde(sd0: float, n: int) -> float:
    """Smallest mean per-loan excess-over-hurdle return detectable with n funded loans."""
    return z_total() * sd0 / math.sqrt(n)


def phi_for(mu_min: float, mu_by_phi: list[tuple[float, float]]) -> tuple[float | None, str]:
    """φ whose mean μ(φ) equals mu_min, by linear interpolation on the φ grid. (value, text)."""
    pts = sorted(mu_by_phi)
    if mu_min <= pts[0][1]:
        return None, "≤ 0,00"
    if mu_min > pts[-1][1]:
        return None, ">1,00"
    for (p0, m0), (p1, m1) in zip(pts, pts[1:], strict=False):
        if m0 <= mu_min <= m1:
            phi = p0 + (p1 - p0) * (mu_min - m0) / (m1 - m0)
            return phi, f"{phi:.2f}".replace(".", ",")
    raise AssertionError((mu_min, pts))


def loss_tail(
    sub: list[Cand], n: int, c: Cost, reps: int = MC_REPS, seed: int = MC_SEED
) -> dict[str, float]:
    """Monte Carlo of the n-loan portfolio total at φ = 0: lower percentiles of the excess-over-hurdle
    total and of the pre-hurdle net total (records drawn with replacement, Bernoulli outcomes)."""
    rng = np.random.default_rng(seed)
    l_ = np.array([r.l_new for r in sub])
    p0 = np.array([r.p0 for r in sub])
    over = np.empty(reps)
    pre = np.empty(reps)
    done = 0
    while done < reps:
        m = min(MC_CHUNK, reps - done)
        idx = rng.integers(0, len(sub), size=(m, n))
        y = rng.random((m, n)) < p0[idx]
        ll = l_[idx]
        r_pre = ll * np.where(y, -c.kayip, c.getiri)
        pre[done : done + m] = r_pre.sum(axis=1)
        over[done : done + m] = pre[done : done + m] - c.hurdle * ll.sum(axis=1)
        done += m
    out: dict[str, float] = {}
    for q in PERCENTILES:
        out[f"over_p{q}"] = float(np.percentile(over, q))
        out[f"pre_p{q}"] = float(np.percentile(pre, q))
    return out


def months_to_fill(n: int, per_month: float, scale: float, accept: float) -> float | None:
    rate = per_month * scale * accept
    return n / rate if rate > 0 else None


def revision_config(cfg_old: dict, ref_rows: list[dict]) -> dict:
    """Old rule outputs relabelled; revision values in a separate section."""
    lab = "varsayım"
    cfg = {k: v for k, v in cfg_old.items()}
    for k in ("pilot_kredi_sayisi", "kredi_basina_tavan_usd", "butce_tavani_usd"):
        cfg[k] = {**cfg[k], "etiket": RULE_LABEL}
    cfg["butce_tavani_usd"]["not"] = (
        "N × tavan nominal anaparadır; kayıp ya da kayıp üst sınırı değildir. Yerine revizyon_1 bölümü."
    )
    cfg["revizyon_1"] = {
        "etiket": lab,
        "kaynak": "docs/pilot_protocol_v0.md, Revizyon 1 (sonradan)",
        "n_izgarasi": {"deger": list(N_REV), "etiket": lab},
        "guc": {"deger": POWER, "etiket": lab},
        "alfa": {"deger": ALPHA, "etiket": lab},
        "zarar_kuyrugu_yuzdelikleri": {"deger": list(PERCENTILES), "etiket": lab},
        "monte_carlo": {"deger": {"tekrar": MC_REPS, "tohum": MC_SEED}, "etiket": lab},
        "musteri_olcegi_izgarasi": {"deger": list(SCALES), "etiket": lab},
        "kabul_orani_izgarasi": {"deger": list(ACCEPT_REV), "etiket": lab},
        "referans": {
            "segment": "(ii) GUCLU+KOSULLU",
            "delta": DELTAS[0],
            "n_basina": ref_rows,
            "etiket": lab,
            "not": "nominal anapara kayıp değildir; zarar kuyruğu φ = 0 senaryosunda Monte Carlo yüzdeliğidir (USD, negatif = kayıp)",
        },
    }
    return cfg


# ---- rendering -----------------------------------------------------------------------------


def split_doc(doc: str) -> tuple[str, str]:
    """(text before the revision-results part, including the committed definition; '')."""
    i = doc.index(REV_START)
    j = doc.find(RES_START, i)
    head = doc[: j if j >= 0 else len(doc)].rstrip() + "\n"
    return head, doc[j:] if j >= 0 else ""


def rows_for(pool: dict[float, list[Cand]], c: Cost):
    for d in DELTAS:
        for seg, labs in SEGMENTS.items():
            sub = pick(pool[d], labs)
            if sub:
                yield d, seg, sub


def seg_count(per_month: dict[str, dict[float, list[Cand]]], m: str, d: float, labs) -> int:
    return len(pick(per_month[m][d], labs))


def render_results(
    per_month: dict[str, dict[float, list[Cand]]], c: Cost, kat
) -> tuple[str, list[dict]]:
    months = sorted(per_month)
    pool = {d: [r for m in months for r in per_month[m][d]] for d in DELTAS}
    mde_t = [
        "| δ | segment | kayıt | N | σ₀ (USD) | μ_min (USD) | μ_min / ort. L' | μ(1,00) (USD) | karşılık gelen φ |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    nom_t = [
        "| δ | segment | N | nominal anapara (USD) | beklenen hurdle üstü toplam, φ = 0 (USD) | hurdle üstü alt %5 (USD) | hurdle üstü alt %1 (USD) | beklenen hurdle öncesi net, φ = 0 (USD) | hurdle öncesi net alt %5 (USD) | hurdle öncesi net alt %1 (USD) | hurdle öncesi net alt %1 / nominal anapara |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    avg_t = [
        "| δ | segment | aday, toplam | ay sayısı | aylık ortalama aday | aylık min | aylık maks |",
        "|---|---|---|---|---|---|---|",
    ]
    flow_t = [
        "| δ | segment | ölçek | kabul | "
        + " | ".join(f"N = {n:,}: gereken ay" for n in N_REV)
        + " |",
        "|---|---|---|---|" + "---|" * len(N_REV),
    ]
    ref_rows: list[dict] = []
    first_seg = next(iter(SEGMENTS))
    for d in DELTAS:
        for seg, labs in SEGMENTS.items():
            sub = pick(pool[d], labs)
            if not sub:
                continue
            head = f"| {d_label(d, kat)} | {seg} |"
            mean_l = float(np.mean([r.l_new for r in sub]))
            mu0, sd0 = moments(sub, 0.0, c)
            mu_by = [(phi, moments(sub, phi, c)[0]) for phi in PHIS]
            mu1 = dict(mu_by)[1.0]
            for n in N_REV:
                mm = mde(sd0, n)
                _phi, txt = phi_for(mm, mu_by)
                mde_t.append(
                    f"{head} {len(sub)} | {n:,} | {sd0:,.1f} | {mm:,.1f} | {100 * mm / mean_l:.1f}% | {mu1:,.1f} | {txt} |"
                )
                tail = loss_tail(sub, n, c)
                nominal = n * mean_l
                nom_t.append(
                    f"{head} {n:,} | {usd(nominal)} | {usd(n * mu0)} | {usd(tail['over_p5'])} | {usd(tail['over_p1'])} | "
                    f"{usd(n * pre_hurdle_mean(sub, 0.0, c))} | {usd(tail['pre_p5'])} | {usd(tail['pre_p1'])} | "
                    f"{100 * tail['pre_p1'] / nominal:.1f}% |"
                )
                if seg == first_seg and d == DELTAS[0]:
                    ref_rows.append(
                        {
                            "n": n,
                            "nominal_anapara_usd": round(nominal),
                            "hurdle_ustu_alt_yuzde5_usd": round(tail["over_p5"]),
                            "hurdle_ustu_alt_yuzde1_usd": round(tail["over_p1"]),
                            "hurdle_oncesi_alt_yuzde5_usd": round(tail["pre_p5"]),
                            "hurdle_oncesi_alt_yuzde1_usd": round(tail["pre_p1"]),
                        }
                    )
            counts = [seg_count(per_month, m, d, labs) for m in months]
            assert sum(counts) == len(sub)
            per_m = sum(counts) / len(months)
            avg_t.append(
                f"{head} {sum(counts):,} | {len(months)} | {per_m:,.1f} | {min(counts)} | {max(counts)} |"
            )
            for s in SCALES:
                for a in ACCEPT_REV:
                    cells = [months_to_fill(n, per_m, s, a) for n in N_REV]
                    flow_t.append(
                        f"{head} %{s * 100:g} | {a:.2f} | "
                        + " | ".join("-" if x is None else f"{x:,.1f}" for x in cells)
                        + " |"
                    )
    L = [
        RES_START,
        "",
        f"Test dilimi kullanılmadı. Havuz: kalibrasyon dilimi ve boşluk ayları birleşik ({', '.join(months)}). Hurdle üstü değer ile hurdle öncesi net sonuç ayrı büyüklüklerdir; hurdle üstü değer nakit kayıp değildir. Monte Carlo: {MC_REPS:,} tekrar, tohum {MC_SEED}.",
        "",
        *tablo(
            "R1. En küçük saptanabilir etki (MDE)",
            "Tek kollu pilotta, H0: E[R] ≤ 0'ı tek yönlü α = 0,05 ve %80 güçle reddetmek için N fonlanan kredide gereken en küçük kredi başına ortalama hurdle üstü getiri (μ_min) ve bunun φ senaryosundaki karşılığı.",
            'μ_min ölçülmüş bir etki değil, N\'ye bağlı bir eşiktir; φ bilinmeyen bir etki payıdır ve ">1,00" modelin öngördüğü payın tamamının bile eşiği geçmediği anlamına gelir; σ₀, φ = 0 senaryosundan alındı.',
            mde_t,
        ),
        *tablo(
            "R2. Nominal anapara ve zarar kuyruğu (φ = 0)",
            "N kredilik portföy için nominal anapara (N × ort. L') ve φ = 0 senaryosunda toplam sonucun alt %5 ve alt %1 yüzdelikleri (hurdle üstü ve hurdle öncesi net).",
            "Nominal anapara kayıp değildir; yüzdelikler Monte Carlo ve cost.yaml ortalamalarına dayanır, gerçek bir kayıp tahmini ya da üst sınırı değildir; hurdle üstü değer nakit kayıp değildir.",
            nom_t,
        ),
        *tablo(
            "R3. Aylık aday akışı",
            "Kalibrasyon ve boşluk aylarında, segment ve δ başına aylık aday sayısı (toplam, ortalama, en küçük ve en büyük ay).",
            "Bu sayılar bu verideki aylık akıştır; bir kredi verenin gerçek başvuru akışı ya da teklifi kabul edecek kişi sayısı değildir.",
            avg_t,
        ),
        *tablo(
            "R4. N krediyi doldurmak için gereken ay",
            "Aylık ortalama aday × müşteri ölçeği × kabul oranına göre, N fonlanan krediye ulaşmak için gereken ay (ölçek %100 = bu verideki akış).",
            "Akış sabit varsayıldı (mevsimsellik yok); 36 aylık sonuç gecikmesi bu süreye eklenmemiştir; kabul oranı bilinmiyor.",
            flow_t,
        ),
    ]
    return "\n".join(L) + "\n", ref_rows


def build(csv_path=None, doc: str | None = None) -> tuple[str, list[dict]]:
    pol, support, kat = load_policy("v1"), load_support(), load_demo_catalog()
    assert abs(DELTAS[0] - kat.delta) < 1e-12, (DELTAS, kat.delta)
    sc = ModelScorer()
    dev = dev_frame(pd.read_csv(csv_path or baseline.CSV))
    frames = [dev[dev["split"] == "calibration"], gap_frame()]
    assert all("test" not in set(f["split"]) for f in frames)
    per_month: dict[str, dict[float, list[Cand]]] = {}
    for f in frames:
        for m, grp in f.groupby(f["issue_date"].dt.to_period("M"), sort=True):
            per_month[str(m)] = collect(grp, sc, pol, support, kat)[0]
    head, _old = split_doc(doc if doc is not None else REPORT.read_text(encoding="utf-8"))
    res, ref_rows = render_results(per_month, load_cost(), kat)
    return head + "\n" + res, ref_rows


def main(argv: list[str] | None = None) -> int:
    if not baseline.CSV.exists():
        print(MISSING.format(path=baseline.CSV), file=sys.stderr)
        return 2
    text, ref_rows = build(baseline.CSV)
    REPORT.write_text(text, encoding="utf-8")
    cfg_old = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    CONFIG.write_text(
        "# Pilot varsayımları (öneri; etiket: varsayım). docs/pilot_protocol_v0.md kurallarıyla üretildi.\n"
        + yaml.safe_dump(revision_config(cfg_old, ref_rows), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"wrote {REPORT} and {CONFIG}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
