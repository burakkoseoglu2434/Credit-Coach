"""ADR-007 measurement: monthly |calibrated mean PD - observed rate| over the calibration split and
the gap months; delta = largest drift rounded UP to 0.001. The TEST split is never loaded.

Usage: python -m credit_coach.safety_margin [--write-adr]
"""

from __future__ import annotations

import math
import sys

import pandas as pd

from credit_coach import baseline
from credit_coach.bundle import ROOT
from credit_coach.modeling import dev_frame
from credit_coach.recourse_gap_report import gap_frame
from credit_coach.recourse_report import vektorler
from credit_coach.recourse_scorers import ModelScorer

ADR = ROOT / "docs" / "adr" / "007-safety-margin.md"
START, END = "<!-- OLCUM-BASLANGIC -->", "<!-- OLCUM-BITIS -->"
MISSING = (
    "Ham veri bulunamadı: {path}\n"
    "Bu ölçüm ham LendingClub CSV dosyasına ihtiyaç duyar (gözlenen oranlar ve skorlama)."
)


def aylik_kayma(kalibre_ortalama: float, gozlenen: float) -> float:
    return abs(kalibre_ortalama - gozlenen)


def delta_kurali(kaymalar: list[float]) -> float:
    """ADR-007: largest monthly drift rounded UP to 0.001 (round() guards float noise)."""
    return math.ceil(round(max(kaymalar) * 1000, 9)) / 1000


def olc(csv_path=None, scorer=None) -> list[dict]:
    sc = scorer or ModelScorer()
    dev = dev_frame(pd.read_csv(csv_path or baseline.CSV))
    frames = {"kalibrasyon": dev[dev["split"] == "calibration"], "boşluk": gap_frame()}
    rows = []
    for dilim, f in frames.items():
        assert "test" not in set(f["split"])
        for ay, grp in f.groupby(f["issue_date"].dt.to_period("M"), sort=True):
            skorlar = sc.skorla_toplu(vektorler(grp), grp["issue_date"].iloc[0])
            m = sum(s.p_point for s in skorlar) / len(skorlar)
            g = float(grp["target"].astype(int).mean())
            rows.append(
                {
                    "ay": str(ay),
                    "dilim": dilim,
                    "n": len(grp),
                    "kalibre_ort": m,
                    "gozlenen": g,
                    "kayma": aylik_kayma(m, g),
                    "isaret": m - g,
                }
            )
    return sorted(rows, key=lambda r: r["ay"])


def render(rows: list[dict]) -> str:
    delta = delta_kurali([r["kayma"] for r in rows])
    en = max(rows, key=lambda r: r["kayma"])
    L = [
        START,
        "Ölçüm (`python -m credit_coach.safety_margin`; ham veri gerekir; test dilimi yok). "
        "Fark = kalibre ortalama PD − gözlenen oran:",
        "",
        "| ay | dilim | kayıt | kalibre ortalama PD | gözlenen oran | fark | aylık kayma |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        L.append(
            f"| {r['ay']} | {r['dilim']} | {r['n']} | {r['kalibre_ort']:.4f} | {r['gozlenen']:.4f} "
            f"| {r['isaret']:+.4f} | {r['kayma']:.4f} |"
        )
    L += [
        "",
        f"En büyük aylık kayma: **{en['kayma']:.6f}** ({en['ay']}, {en['dilim']}). "
        f"Kural: δ = ceil(1000 × {en['kayma']:.6f}) / 1000 = **{delta:.3f}**.",
        END,
    ]
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    if not baseline.CSV.exists():
        print(MISSING.format(path=baseline.CSV), file=sys.stderr)
        return 2
    text = render(olc(baseline.CSV))
    print(text)
    if "--write-adr" in argv:
        adr = ADR.read_text()
        if START in adr:
            adr = adr[: adr.index(START)] + text + adr[adr.index(END) + len(END) + 1 :]
        else:
            adr = adr.replace("Ölçüm henüz yapılmadı.\n", text)
        ADR.write_text(adr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
