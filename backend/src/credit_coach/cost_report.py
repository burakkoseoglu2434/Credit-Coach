"""Write configs/cost.yaml and docs/week2_cost.md from the TRAIN window of the raw file.

Usage: CREDIT_COACH_RAW_LC=/path/accepted_2007_to_2018Q4.csv python -m credit_coach.cost_report
"""

from __future__ import annotations

import os

import yaml

from credit_coach.cost import (
    LABEL,
    break_even_pd,
    clean,
    cost_stats,
    load_train_outcomes,
    sensitivity,
)
from credit_coach.features import MANIFEST_PATH
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.split import load_split_config

ROOT = MANIFEST_PATH.parents[1]
COST_YAML = MANIFEST_PATH.parent / "cost.yaml"
REPORT = ROOT / "docs" / "week2_cost.md"

HEADER = """\
# Maliyet varsayımları (onay eşiği için).
# BU ALANLAR MODEL GİRDİSİ DEĞİLDİR: funded_amnt, total_rec_prncp, total_rec_int, recoveries ve
# loan_status kredi sonrası sonuçlardır (yasak sütunlar). Yalnızca maliyet kalibrasyonunda,
# ayrı bir yükleyiciyle ve yalnızca EĞİTİM diliminden okunur; eğitim matrisine girmez.
# Kalibrasyon ve test dilimlerinin sonuçlarına bakılmaz.
"""


def main() -> None:
    raw = os.environ["CREDIT_COACH_RAW_LC"]
    cfg = load_split_config()
    df = load_train_outcomes(raw, cfg)
    s = clean(cost_stats(df))
    gain_m, gain_md = s["yield_good"]["mean"], s["yield_good"]["median"]
    loss_m, loss_md = s["default_net_loss"]["mean"], s["default_net_loss"]["median"]
    be = {"mean": break_even_pd(gain_m, loss_m), "median": break_even_pd(gain_md, loss_md)}
    w = cfg.splits["train"]
    old = yaml.safe_load(COST_YAML.read_text()) if COST_YAML.exists() else {}
    doc = {
        "version": 1,
        "etiket": LABEL,
        "kaynak_pencere": {
            "term": cfg.term,
            "issue_d_start": w.start,
            "issue_d_end": w.end,
            "sonuclanmis_kredi": s["n_resolved"],
            "temerrut_orani": s["bad_rate"],
        },
        "lgd": {
            "etiket": LABEL,
            **s["lgd"],
            "formul": "(funded_amnt - total_rec_prncp - recoveries) / funded_amnt, "
            "temerrütlü krediler",
        },
        "saglam_kredi_getirisi": {
            "etiket": LABEL,
            **s["yield_good"],
            "formul": "total_rec_int / funded_amnt, tam ödenen krediler",
        },
        "temerrutte_tahsil_edilen_faiz": {
            "etiket": LABEL,
            **s["interest_on_defaults"],
            "formul": "total_rec_int / funded_amnt, temerrütlü krediler",
        },
        "temerrut_kaybi": {
            "etiket": LABEL,
            **s["default_net_loss"],
            "formul": "LGD - tahsil edilen faiz / funded_amnt",
        },
        "onay_esigi_referans": {
            "etiket": LABEL,
            "formul": "PD* = getiri / (getiri + kayip); PD <= PD* ise onay",
            "break_even_pd_mean": be["mean"],
            "break_even_pd_median": be["median"],
            "birincil": "mean",
        },
        "hurdle": old.get("hurdle"),  # kullanıcı değerleri korunur
        "ret_esigi": None,  # 4. haftada recourse fizibilitesinden türetilecek
    }
    COST_YAML.write_text(HEADER + yaml.safe_dump(doc, allow_unicode=True, sort_keys=False))

    lines = [
        "# Hafta 2.4: maliyet varsayımları ve onay eşiği duyarlılığı",
        "",
        KURGUSAL_VEREN,
        "",
        f"Kaynak: yalnızca eğitim penceresi ({w.start}..{w.end}, {cfg.term}), "
        f"{s['n_resolved']} sonuçlanmış kredi, temerrüt oranı {s['bad_rate']:.4f}. {LABEL}.",
        "",
        "| Büyüklük | Ortalama | Medyan | n |",
        "|---|---|---|---|",
    ]
    for k, name in (
        ("lgd", "LGD"),
        ("yield_good", "Sağlam kredi getirisi"),
        ("interest_on_defaults", "Temerrütte tahsil edilen faiz"),
        ("default_net_loss", "Temerrüt kaybı (LGD - faiz)"),
    ):
        lines.append(f"| {name} | {s[k]['mean']:.4f} | {s[k]['median']:.4f} | {s[k]['n']} |")
    lines += ["", f"Break-even PD* (ortalama): {be['mean']:.4f}, (medyan): {be['median']:.4f}", ""]
    for label, g, l_ in (("ortalama", gain_m, loss_m), ("medyan", gain_md, loss_md)):
        lines += [
            f"## Duyarlılık ({label}; LGD/kayıp ±%20, getiri ±%20)",
            "",
            sensitivity(g, l_).round(4).to_markdown(),
            "",
        ]
    REPORT.write_text("\n".join(lines))
    print(REPORT.read_text())


if __name__ == "__main__":
    main()
