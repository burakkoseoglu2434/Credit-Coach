# ruff: noqa: E501  (report prose is long on purpose)
"""Portfolio report (demo v0): calibration and gap months, delta in {0 (inside the band), 0.03},
dti update off. Needs the raw LendingClub CSV (labels for the worst-case table). The TEST split is
never loaded here; its numbers are cited from docs/week2_report.md.

Usage: make report   (python -m credit_coach.portfolio_report)
"""

from __future__ import annotations

import statistics
import sys

import pandas as pd

from credit_coach import baseline
from credit_coach.bundle import ROOT
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.modeling import dev_frame
from credit_coach.policy import load_policy
from credit_coach.recourse import PATH_ORDER, load_demo_catalog
from credit_coach.recourse_bucket_report import LABELS
from credit_coach.recourse_gap_report import gap_frame
from credit_coach.recourse_report import _pct, run
from credit_coach.recourse_scorers import ModelScorer
from credit_coach.recourse_worstcase import evaluate
from credit_coach.report_deltas import delta_etiketi, delta_notu, report_deltas, varsayilan_delta
from credit_coach.support import load_support

REPORT = ROOT / "docs" / "demo_portfolio_report.md"
PERIODS = ("kalibrasyon", "boşluk")
MISSING = (
    "Ham veri bulunamadı: {path}\n"
    "Bu rapor, gözlenen temerrüt oranları için ham LendingClub CSV dosyasındaki etiketlere ihtiyaç "
    "duyar. Dosyayı yukarıdaki yola koyun; v2 kodunun geri kalanı (make demo) ham veri istemez."
)


def _rate(bad: int, n: int) -> str:
    return f"{100 * bad / n:.2f}%" if n else "-"


def build(csv_path=None) -> str:
    pol, support, kat = load_policy("v1"), load_support(), load_demo_catalog()
    sc = ModelScorer()
    dev = dev_frame(pd.read_csv(csv_path or baseline.CSV))
    frames = {
        "kalibrasyon": dev[dev["split"] == "calibration"],
        "boşluk": gap_frame(),
    }
    assert all("test" not in set(f["split"]) for f in frames.values())
    ds = report_deltas(kat)
    run_res = {p: run(f, deltas=ds) for p, f in frames.items()}
    wc_res = {p: evaluate(f, sc, pol, support, kat, ds) for p, f in frames.items()}

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

    L = [
        f"# Demo v0: portföy raporu ({varsayilan_delta(kat)})",
        "",
        KURGUSAL_VEREN,
        "",
        delta_notu(kat),
        "",
        "Kapsam: kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08). "
        f"Onay eşiği (PD) {pol.onay_esigi:.4f}, band {pol.band:.4f}. dti güncellemesi kapalı. "
        "Etiketler (gözlenen temerrüt) yalnızca değerlendirme içindir, karar yoluna girmez.",
        "",
        "**Test dilimi (2015-09..12) bu raporda yeniden çalıştırılmadı.** Tek seferlik test sonuçları "
        "`docs/week2_report.md` içindedir (ham model AUC 0,6906; onay oranı 0,3860; onaylananlarda "
        "gözlenen temerrüt 0,0677). Test dilimi bir kez kullanıldı ve ayar için kullanılamaz.",
        "",
        "Plan = en az bir yol türü için geçerli plan (ADR-006). δ = 0'da etkin kesim eşik − band'dır "
        "(yakınlık bandı karar kuralı R2 tarafından zaten uygulanır).",
        "",
    ]

    # 1. decision distribution
    g = [
        "| dilim | kayıt | destek dışı | onay | koşullu | ret | ret payı (destek içi) |",
        "|---|---|---|---|---|---|---|",
    ]
    for p in PERIODS:
        c = run_res[p]["counts"]
        ins = c["n_calibration"] - c["out_of_support"]
        g.append(
            f"| {p} | {c['n_calibration']} | {c['out_of_support']} | {c['base_APPROVED']} | "
            f"{c['base_CONDITIONAL']} | {c['base_REJECTED']} | {_pct(c['base_REJECTED'], ins)} |"
        )
    L += tablo(
        "1. Karar dağılımı (politika v1)",
        "v1 politikasının bu aylardaki başvuruları nasıl ayırdığı; sayılar karar sayısıdır.",
        "Bu, bir kurumun gerçek onay oranı ya da güncel başvurular için bir tahmin değildir; model 2012-15 ABD verisiyle eğitildi ve eşik kurgusal tek fiyatlı kredi vereni temsil eder.",
        g,
    )

    # 2. valid plan rate
    g = [
        "| dilim | δ | reddedilen | en az bir yolda plan | müşteri | karma | kurum | PLAN_YOK |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for p in PERIODS:
        n = run_res[p]["counts"]["rejected"]
        for d in ds:
            pl = run_res[p]["plan_n"][(d, False)]
            g.append(
                f"| {p} | {delta_etiketi(d, kat)} | {n} | {_pct(pl['any'], n)} "
                + " ".join(f"| {_pct(pl[('path', t)], n)}" for t in PATH_ORDER)
                + f" | {_pct(n - pl['any'], n)} |"
            )
    L += tablo(
        "2. Geçerli plan oranı (reddedilenler içinde)",
        "Reddedilen kayıtların, katalogdaki iki eylemle modele göre eşiğin güvenli payla altına inen bir plana sahip olan payı.",
        "Plan bulunması, kişinin bu değişikliği yapabileceği, yapacağı ya da sonucun gerçekleşeceği anlamına gelmez; etki doğrulanmadı ve model bir ilişki ölçer.",
        g,
    )

    # 3. path sets
    sets = sorted(
        {
            s[1]
            for p in PERIODS
            for pl in run_res[p]["plan_n"].values()
            for s in pl
            if isinstance(s, tuple) and s[0] == "set"
        }
    )
    g = [
        "| dilim | δ | PLAN_YOK | " + " | ".join("+".join(s) for s in sets) + " |",
        "|---|---|---|" + "---|" * len(sets),
    ]
    for p in PERIODS:
        n = run_res[p]["counts"]["rejected"]
        for d in ds:
            pl = run_res[p]["plan_n"][(d, False)]
            g.append(
                f"| {p} | {delta_etiketi(d, kat)} | {_pct(n - pl['any'], n)} "
                + " ".join(f"| {_pct(pl[('set', s)], n)}" for s in sets)
                + " |"
            )
    L += tablo(
        "3. Yol dağılımı (kayıt başına hangi yol türlerinde plan var)",
        "Aynı kaydın birden çok yol türünde planı olabilir; sütunlar yol türü kümeleridir.",
        "Yollar birbiriyle sıralanmadı; bir yolun diğerinden iyi olduğu anlamına gelmez.",
        g,
    )

    # 4. median cost
    g = ["| dilim | δ | müşteri | karma | kurum |", "|---|---|---|---|---|"]
    for p in PERIODS:
        for d in ds:
            cells = []
            for t in PATH_ORDER:
                v = run_res[p]["costs"].get(((d, False), t), [])
                cells.append(f"{statistics.median(v):,.0f} USD (n={len(v)})" if v else "-")
            g.append(f"| {p} | {delta_etiketi(d, kat)} | " + " | ".join(cells) + " |")
    L += tablo(
        "4. Yol başına medyan USD maliyeti (varsayım)",
        "Yolun en ucuz geçerli planının USD tutarının medyanı; tutar nakit çıkışı ya da karşılanmayan talep olarak varsayıldı.",
        "Maliyet ölçülmedi; iki maliyet türü 1 USD = 1 USD varsayımıyla aynı birimde gösterildi. Gerçek bir başvuranın maliyetini göstermez.",
        g,
    )

    # 5. buckets
    g = [
        "| dilim | δ | kova (p_point − eşik) | reddedilen | geçerli plan oranı |",
        "|---|---|---|---|---|",
    ]
    for p in PERIODS:
        rb = wc_res[p]["rej_bucket"]
        for d in ds:
            for lab in LABELS:
                if rb.get(lab):
                    n_valid = wc_res[p]["cells"][d].get(lab, [0, 0])[0]
                    g.append(
                        f"| {p} | {delta_etiketi(d, kat)} | {lab} | {rb[lab]} | {_pct(n_valid, rb[lab])} |"
                    )
    L += tablo(
        "5. Geçerli plan oranı, p_point − eşik kovalarına göre",
        "Eşiğe uzaklık arttıkça planı olan kayıt payının nasıl değiştiği.",
        "Kova, kişinin ne kadar çaba göstermesi gerektiğini ölçmez; yalnızca modelin bugünkü risk tahmininin eşiğe uzaklığıdır.",
        g,
    )

    # 6. worst case
    g = ["| dilim | δ | kova | plan'lı reddedilen | gözlenen temerrüt |", "|---|---|---|---|---|"]
    for p in PERIODS:
        for d in ds:
            for key in [*LABELS, "tümü"]:
                n, bad = wc_res[p]["cells"][d].get(key, [0, 0])
                if n:
                    g.append(f"| {p} | {delta_etiketi(d, kat)} | {key} | {n} | {_rate(bad, n)} |")
    g += [
        "",
        "Karşılaştırma: onaylananların gözlenen temerrüt oranı.",
        "",
        "| dilim | onaylanan | gözlenen temerrüt |",
        "|---|---|---|",
    ]
    for p in PERIODS:
        a = wc_res[p]["approved"]
        g.append(f"| {p} | {a['n']} | {_rate(a['bad'], a['n'])} |")
    L += tablo(
        "6. En kötü durum: planı olan reddedilenlerin ORİJİNAL gözlenen temerrüt oranı",
        "Plan bulunan kayıtlar, plan uygulanmadan bugünkü hâlleriyle gözlenen temerrüt oranına sahiptir; plan bulunması, kayıtların güvenli olduğunu değil, modelin eşiğin altına inen bir değişiklik bulduğunu söyler.",
        "Bu oran planın sonucu değildir: plan uygulanmış kişilerin sonuçları gözlenmedi. Orijinal oran, onaylananlarınkinden belirgin yüksek olduğu için planın etkisi doğrulanmış sayılmaz.",
        g,
    )
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    csv_path = baseline.CSV
    if not csv_path.exists():
        print(MISSING.format(path=csv_path), file=sys.stderr)
        return 2
    text = build(csv_path)
    REPORT.write_text(text)
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
