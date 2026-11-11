# ruff: noqa: E501  (report prose is long on purpose)
"""Pilot protocol v0: sample-size and exposure calculation for a single-arm, capped, randomly
selected counteroffer pilot. Calibration split and gap months only; the TEST split is never loaded.
Engine, policy, catalog and cost.yaml are untouched.

The design and method sections of docs/pilot_protocol_v0.md were written and committed BEFORE this
computation; the report keeps them verbatim. Writes docs/pilot_protocol_v0.md and configs/pilot.yaml.

Usage: python -m credit_coach.pilot_protocol
"""

from __future__ import annotations

import math
import sys
from statistics import NormalDist

import numpy as np
import pandas as pd
import yaml

from credit_coach import baseline
from credit_coach.bundle import ROOT
from credit_coach.counteroffer_economics import (
    DELTAS,
    PHIS,
    Cand,
    Cost,
    collect,
    d_label,
    load_cost,
    p_phi,
    pick,
    tablo,
    usd,
)
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.modeling import dev_frame
from credit_coach.policy import load_policy
from credit_coach.recourse import load_demo_catalog
from credit_coach.recourse_gap_report import gap_frame
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.support import load_support

REPORT = ROOT / "docs" / "pilot_protocol_v0.md"
CONFIG = ROOT / "configs" / "pilot.yaml"
ALPHA = 0.05
POWERS = (0.8, 0.9)
ACCEPT = (0.3, 0.5, 0.7)
N_GRID = (100, 250, 500, 1000, 2000)
STOP_RATIO = -0.05
SEGMENTS = {
    "(ii) GUCLU+KOSULLU": frozenset({"GUCLU", "KOSULLU"}),
    "(iii) planı geçerli olan hepsi": frozenset({"GUCLU", "KOSULLU", "ZAYIF"}),
}
REF = ("(ii) GUCLU+KOSULLU", 0.012, 0.50, 0.8)  # segment, δ, φ, power for the reference pilot size
START, CUT, CUT_FALLBACK = "## Tasarım", "## Sonuçlar", "## Hukuk ve uyum"
MISSING = (
    "Ham veri bulunamadı: {path}\n"
    "Bu rapor ham LendingClub CSV dosyasına ihtiyaç duyar (başvuru özellikleri ve skorlama)."
)


# ---- calculation ---------------------------------------------------------------------------


def moments(sub: list[Cand], phi: float, c: Cost) -> tuple[float, float]:
    """(mean, sd) of the per-loan excess-over-hurdle return R for one randomly chosen record."""
    a, b = c.getiri - c.hurdle, c.getiri + c.kayip
    l_ = np.array([r.l_new for r in sub])
    p = np.array([p_phi(r, phi) for r in sub])
    mu = float((l_ * (a - b * p)).mean())
    e2 = float((l_**2 * (p * (a - b) ** 2 + (1 - p) * a**2)).mean())
    return mu, math.sqrt(max(e2 - mu**2, 0.0))


def pre_hurdle_mean(sub: list[Cand], phi: float, c: Cost) -> float:
    """Mean per-loan result BEFORE the hurdle (cash view, approximate): L' (getiri - p (getiri + kayip))."""
    return float(
        np.mean([r.l_new * (c.getiri - p_phi(r, phi) * (c.getiri + c.kayip)) for r in sub])
    )


def n_required(mu: float, sd: float, power: float, alpha: float = ALPHA) -> int | None:
    if mu <= 0:
        return None
    z = NormalDist().inv_cdf(1 - alpha) + NormalDist().inv_cdf(power)
    return math.ceil((z * sd / mu) ** 2)


def offers(n: int, accept: float) -> int:
    return math.ceil(n / accept)


def worst_case(n: int, l_: float, c: Cost) -> tuple[float, float]:
    """All n loans default: (excess over hurdle, result before hurdle), both negative USD."""
    return -n * l_ * (c.kayip + c.hurdle), -n * l_ * c.kayip


def round_up(x: float, step: int) -> int:
    return int(math.ceil(x / step) * step)


def reference(pool: dict[float, list[Cand]], c: Cost) -> dict:
    seg, d, phi, power = REF
    sub = pick(pool[d], SEGMENTS[seg])
    mu, sd = moments(sub, phi, c)
    n = n_required(mu, sd, power)
    assert n is not None
    n_pilot = round_up(n, 100)
    tavan = round_up(float(np.percentile([r.l_new for r in sub], 90)), 500)
    return {
        "pilot_kredi_sayisi": n_pilot,
        "kredi_basina_tavan_usd": tavan,
        "butce_tavani_usd": n_pilot * tavan,
        "durdurma_esigi": STOP_RATIO,
    }


def config_doc(ref: dict) -> dict:
    lab = "varsayım"
    return {
        "version": 1,
        "etiket": lab,
        "kaynak": "docs/pilot_protocol_v0.md (kurallar), counteroffer_economics aday havuzu",
        "pilot_kredi_sayisi": {"deger": ref["pilot_kredi_sayisi"], "etiket": lab},
        "kredi_basina_tavan_usd": {"deger": ref["kredi_basina_tavan_usd"], "etiket": lab},
        "butce_tavani_usd": {"deger": ref["butce_tavani_usd"], "etiket": lab},
        "durdurma_esigi": {
            "deger": ref["durdurma_esigi"],
            "etiket": lab,
            "tanim": "gerçekleşen kümülatif hurdle öncesi net sonuç / fonlanan toplam anapara; altına düşerse yeni fonlama durur",
        },
        "alfa": {"deger": ALPHA, "etiket": lab},
        "guc": {"deger": list(POWERS), "etiket": lab},
        "phi_izgarasi": {"deger": list(PHIS), "etiket": lab},
        "kabul_orani_izgarasi": {"deger": list(ACCEPT), "etiket": lab},
    }


# ---- rendering -----------------------------------------------------------------------------


def definition_text(doc: str) -> str:
    start = doc.index(START)
    end = doc.find(CUT, start)
    if end < 0:
        end = doc.find(CUT_FALLBACK, start)
    return doc[start : end if end >= 0 else len(doc)].rstrip() + "\n"


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


LEGAL = [
    "Bu liste hukuki görüş değildir; karar verilmemiştir. Kredi verenin yargı alanı bilinmiyor (veri 2012-15 ABD verisidir); sorular bir hukuk ve uyum uzmanına yöneltilmek üzere yazıldı.",
    "",
    "1. **Karşı teklif bildirimi.** Reddedilen bir başvuruya daha düşük tutarlı karşı teklif sunulduğunda, olumsuz karar bildirimi ile karşı teklif hangi sırayla, hangi içerik ve sürelerle iletilmelidir? Teklif reddedilir ya da yanıtsız kalırsa ayrı bir bildirim gerekir mi?",
    "2. **Deneysel kredi onayı.** Politika gereği reddedilecek başvurulardan rastgele seçilenlere kredi sunmak hangi izin, kayıt ve izleme koşullarına bağlıdır? Rastgele seçimin, seçilmeyen ya da seçilen gruplar arasındaki farklı etki bakımından nasıl belgelenmesi gerekir? Pilot için düzenleyiciye bildirim ya da izin gerekir mi?",
    "3. **Olumsuz karar bildirimi.** Reddedilen başvuruya gönderilen bildirimde hangi gerekçelerin, hangi ayrıntıyla ve modelin kullanıldığı bilgisinin yer alması gerekir? Karşı teklifin tutarı ve dayanağı bu bildirimin parçası mıdır?",
    "4. **Katılımcıya bilgi.** Müşteriye teklifin bir pilotun parçası olduğu söylenmeli midir? Pilot verisinin saklanması ve sonradan analizi için hangi rıza ve saklama koşulları geçerlidir?",
    "5. **Koşullar.** Karşı teklif yalnızca tutarı değiştiriyorsa (faiz ve vade aynı) bu, ayrı bir kredi ürünü ya da farklı bir fiyatlama sayılır mı?",
]

LIMITS = [
    "- **36 aylık sonuç gecikmesi.** Gerçekleşen getiri vade sonunda bilinir; birincil çıktı pilot başladıktan yaklaşık 36 ay sonra ölçülebilir. Durdurma kuralı fonlama bittikten sonra devreye girebilir; fonlanan anapara pilot başında taahhüt edilir, bu yüzden asıl koruma bütçe tavanıdır.",
    "- **Erken gösterge çalışması yok.** Vadeden önce karar vermeye yarayacak göstergeler (geç ödeme, ilk temerrüt zamanı) ayrı bir çalışma gerektirir ve bu belgede yapılmadı.",
    "- **Seçilim ve kabul farkı.** Teklifi kabul edenlerin teklif edilenlerden farklı olması (örneğin daha düşük risk ya da daha yüksek ihtiyaç) güç hesabına ve sonuca yansır; kabul oranı yalnızca teklif sayısını ölçekler, kabul edenlerin temerrüt oranını değiştirmez varsayılmıştır.",
    "- **2012-15 ABD verisi.** Havuz ve olasılıklar bu dönemin kredilerinden gelir; bugünkü bir kredi veren için geçerliliği doğrulanmadı.",
    "- **Varsayımlar.** getiri, temerrüt kaybı ve hurdle `configs/cost.yaml`'daki varsayımlardır; φ ölçülmüş bir etki değil, bir senaryo parametresidir; normal yaklaşım küçük N ve çarpık R için yaklaşıktır.",
]


def render(pool: dict[float, list[Cand]], c: Cost, kat, tanim: str) -> tuple[str, dict]:
    ref = reference(pool, c)
    pars = [
        "| parametre | değer | kaynak |",
        "|---|---|---|",
        f"| getiri | {c.getiri:.4f} | `configs/cost.yaml`, `saglam_kredi_getirisi.mean` (varsayım) |",
        f"| temerrüt kaybı | {c.kayip:.4f} | `configs/cost.yaml`, `temerrut_kaybi.mean` (varsayım) |",
        f"| hurdle (toplam) | {c.hurdle:.4f} | `configs/cost.yaml` (tez varsayımı) |",
        f"| a = getiri − hurdle | {c.getiri - c.hurdle:.4f} | |",
        f"| b = getiri + temerrüt kaybı | {c.getiri + c.kayip:.4f} | |",
        f"| α (tek yönlü) | {ALPHA} | tasarım |",
        "| z (α = 0,05; güç %80; güç %90) | "
        + "; ".join(f"{NormalDist().inv_cdf(q):.4f}" for q in (1 - ALPHA, 0.8, 0.9))
        + " | `statistics.NormalDist` |",
    ]
    pool_t = [
        "| δ | segment | kayıt (havuz) | ort. L' (USD) | L' %90 (USD) | L' en büyük (USD) |",
        "|---|---|---|---|---|---|",
    ]
    mom = [
        "| δ | segment | φ | μ (USD) | σ (USD) | σ / ort. L' | μ / ort. L' |",
        "|---|---|---|---|---|---|---|",
    ]
    pw = [
        "| δ | segment | φ | N, güç %80 | N, güç %90 |",
        "|---|---|---|---|---|",
    ]
    of = [
        "| δ | segment | φ | güç | "
        + " | ".join(f"teklif, kabul {a:g}" for a in ACCEPT).replace(".", ",")
        + " |",
        "|---|---|---|---|" + "---|" * len(ACCEPT),
    ]
    wc = [
        "| δ | segment | N | ort. L' (USD) | L' tavan (USD) | beklenen hurdle üstü toplam, φ = 0 (USD) | beklenen hurdle öncesi net toplam, φ = 0 (USD) | en kötü: hurdle üstü, ort. L' (USD) | en kötü: hurdle üstü, tavan (USD) | en kötü: hurdle öncesi net, ort. L' (USD) | en kötü: hurdle öncesi net, tavan (USD) |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for d in DELTAS:
        for seg, labs in SEGMENTS.items():
            sub = pick(pool[d], labs)
            n = len(sub)
            head = f"| {d_label(d, kat)} | {seg} |"
            if n == 0:
                continue
            ls = np.array([r.l_new for r in sub])
            mean_l = float(ls.mean())
            pool_t.append(
                f"{head} {n} | {usd(mean_l)} | {usd(float(np.percentile(ls, 90)))} | {usd(float(ls.max()))} |"
            )
            for phi in PHIS:
                mu, sd = moments(sub, phi, c)
                mom.append(
                    f"{head} {phi:.2f} | {mu:,.1f} | {sd:,.1f} | {pct(sd / mean_l)} | {pct(mu / mean_l)} |"
                )
                ns = [n_required(mu, sd, g) for g in POWERS]
                pw.append(
                    f"{head} {phi:.2f} | "
                    + " | ".join(f"{x:,}" if x else "tanımsız (μ ≤ 0)" for x in ns)
                    + " |"
                )
                for g, x in zip(POWERS, ns, strict=True):
                    if x:
                        of.append(
                            f"{head} {phi:.2f} | {int(g * 100)} | "
                            + " | ".join(f"{offers(x, a):,}" for a in ACCEPT)
                            + " |"
                        )
            mu0, _ = moments(sub, 0.0, c)
            pre0 = pre_hurdle_mean(sub, 0.0, c)
            for nn in sorted({*N_GRID, ref["pilot_kredi_sayisi"]}):
                w_mean = worst_case(nn, mean_l, c)
                w_cap = worst_case(nn, float(ref["kredi_basina_tavan_usd"]), c)
                wc.append(
                    f"{head} {nn:,} | {usd(mean_l)} | {ref['kredi_basina_tavan_usd']:,} | {usd(nn * mu0)} | {usd(nn * pre0)} | "
                    f"{usd(w_mean[0])} | {usd(w_cap[0])} | {usd(w_mean[1])} | {usd(w_cap[1])} |"
                )
    rec = [
        "| öğe | değer | kural |",
        "|---|---|---|",
        f"| `pilot_kredi_sayisi` | {ref['pilot_kredi_sayisi']:,} | (ii) GUCLU+KOSULLU, δ = 0,012, φ = 0,50, güç %80 için gereken N, sonraki 100'e yukarı yuvarlanmış |",
        f"| `kredi_basina_tavan_usd` | {ref['kredi_basina_tavan_usd']:,} | aynı havuzda L' %90'lık dilimi, sonraki 500 USD'ye yukarı yuvarlanmış |",
        f"| `butce_tavani_usd` | {ref['butce_tavani_usd']:,} | `pilot_kredi_sayisi` × `kredi_basina_tavan_usd` |",
        f"| `durdurma_esigi` | {STOP_RATIO:.2f} | gerçekleşen kümülatif hurdle öncesi net sonuç / fonlanan toplam anapara bu değerin altına düşerse yeni fonlama durur |",
    ]
    L = [
        "# Pilot protokolü v0: tek kollu, tavanlı, rastgele seçilmiş karşı teklif pilotu",
        "",
        KURGUSAL_VEREN,
        "",
        tanim.rstrip(),
        "",
        CUT,
        "",
        "Test dilimi kullanılmadı. Havuz: kalibrasyon dilimi ve boşluk ayları birleşik. Hurdle üstü değer ile hurdle öncesi net sonuç ayrı büyüklüklerdir; hurdle üstü değer nakit kayıp değildir.",
        "",
        *tablo(
            "1. Parametreler",
            "Hesapta kullanılan getiri, temerrüt kaybı, hurdle, α ve z değerleri.",
            "Bu değerler ölçülmüş fiyatlama değil varsayımdır; gerçek bir kurumun getirisini ya da kaybını göstermez.",
            pars,
        ),
        *tablo(
            "2. Aday havuzu",
            "δ ve segment başına havuzdaki kayıt sayısı ve karşı teklif tutarı L' dağılımı.",
            "Havuz bir öneri listesi değildir; havuzdaki bir kişinin teklifi kabul edeceği anlamına gelmez.",
            pool_t,
        ),
        *tablo(
            "3. Kredi başına getiri: ortalama ve standart sapma",
            "φ senaryosu başına, rastgele seçilmiş bir kredinin hurdle üstü getirisinin ortalaması (μ) ve standart sapması (σ), L' ağırlıklı Bernoulli sonuçla.",
            "μ gerçekleşen kâr değildir; p_point = p_önce − φ·Δ_point senaryosuna ve cost.yaml varsayımlarına bağlıdır, φ bilinmeyen bir etki payıdır.",
            mom,
        ),
        *tablo(
            "4. Gereken fonlanan kredi sayısı",
            "H0: E[R] ≤ 0'ı tek yönlü α = 0,05 ile reddetmek için, senaryo μ ve σ altında, %80 ve %90 güçle gereken fonlanan kredi sayısı.",
            "Gerçekte φ'nin senaryodaki değer olacağı anlamına gelmez; μ ≤ 0 olan senaryoda pozitif ortalama beklenmediği için N tanımsızdır.",
            pw,
        ),
        *tablo(
            "5. Teklif edilecek kişi sayısı",
            "Fonlanacak kredi sayısını, kabul oranına bölerek bulunan teklif sayısı.",
            "Kabul oranı bilinmiyor; teklifi kabul edenlerin teklif edilenlerden farklı olabileceği hesaba katılmadı.",
            of,
        ),
        *tablo(
            "6. φ = 0 senaryosu ve en kötü durum",
            "φ = 0'da (karşı teklif riski değiştirmez) N kredi için beklenen toplam hurdle üstü değer ve hurdle öncesi net sonuç; en kötü durumda tüm kredilerin temerrüde düşmesi, ort. L' ve kredi başına tavanla.",
            "Hurdle üstü değer nakit kayıp değildir (hurdle asgari marj, fon maliyeti ve işletme giderini içerir); en kötü durum tüm kredilerin aynı anda temerrüde düşmesidir ve olası bir sonuç tahmini değil bir üst sınırdır.",
            wc,
        ),
        *tablo(
            "7. Bütçe tavanı ve durdurma kuralı önerisi",
            "Tasarımdaki kurallarla hesaplanan değerler; `configs/pilot.yaml` dosyasına `varsayım` etiketiyle yazıldı.",
            "Bunlar bir kredi verenin risk iştahını temsil etmez; öneridir ve bir yetkili tarafından belirlenmelidir.",
            rec,
        ),
        "## Hukuk ve uyum",
        "",
        *LEGAL,
        "",
        "## Sınırlar",
        "",
        *LIMITS,
    ]
    return "\n".join(L) + "\n", ref


def build(csv_path=None, doc: str | None = None) -> tuple[str, dict]:
    pol, support, kat = load_policy("v1"), load_support(), load_demo_catalog()
    assert abs(DELTAS[0] - kat.delta) < 1e-12, (DELTAS, kat.delta)
    sc = ModelScorer()
    dev = dev_frame(pd.read_csv(csv_path or baseline.CSV))
    frames = {"kalibrasyon": dev[dev["split"] == "calibration"], "boşluk": gap_frame()}
    assert all("test" not in set(f["split"]) for f in frames.values())
    per = {k: collect(f, sc, pol, support, kat)[0] for k, f in frames.items()}
    pool = {d: [r for k in frames for r in per[k][d]] for d in DELTAS}
    tanim = definition_text(doc if doc is not None else REPORT.read_text(encoding="utf-8"))
    return render(pool, load_cost(), kat, tanim)


def main(argv: list[str] | None = None) -> int:
    if not baseline.CSV.exists():
        print(MISSING.format(path=baseline.CSV), file=sys.stderr)
        return 2
    text, ref = build(baseline.CSV)
    REPORT.write_text(text, encoding="utf-8")
    CONFIG.write_text(
        "# Pilot varsayımları (öneri; etiket: varsayım). docs/pilot_protocol_v0.md kurallarıyla üretildi.\n"
        + yaml.safe_dump(config_doc(ref), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"wrote {REPORT} and {CONFIG}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
