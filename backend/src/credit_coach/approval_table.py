# ruff: noqa: E501
"""Hurdle sensitivity on the CALIBRATION split only (leave-one-month-out intervals).

The test split is never loaded. Hurdle values are the pre-registered grid from the task and the
chosen 0.11; none were selected by looking at approval rates.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yaml
from xgboost import XGBClassifier

from credit_coach.baseline import CSV
from credit_coach.bundle import ROOT
from credit_coach.calibration import fit_venn_abers, predict_interval
from credit_coach.decision import (
    APPROVE,
    HUMAN,
    NOT_APPROVED,
    DecisionConfig,
    approval_threshold,
    decide,
    load_cost,
)
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.modeling import dev_frame, split_xy
from credit_coach.train_monotone import MODEL_PATH

GRID = (0.06, 0.09, 0.11, 0.13, 0.15)
REPORT = ROOT / "docs" / "week2_approval_sensitivity.md"


def summarize(decisions: np.ndarray, y: np.ndarray) -> dict[str, float]:
    out = {}
    for name, key in ((APPROVE, "onay"), (HUMAN, "insana"), (NOT_APPROVED, "onay_degil")):
        m = decisions == name
        out[f"{key}_orani"] = float(m.mean())
        out[f"{key}_temerrut"] = float(y[m].mean()) if m.any() else float("nan")
    return out


def table(low, high, s, point, y, gain, loss, band, weak, mult, grid=GRID) -> pd.DataFrame:
    rows = []
    for h in grid:
        thr = approval_threshold(gain, loss, h)
        cfg = DecisionConfig(thr, band, tuple(map(tuple, weak)), mult)
        rows.append({"hurdle": h, "esik": thr, **summarize(decide(low, high, s, cfg, point), y)})
    return pd.DataFrame(rows)


def main() -> None:
    cost = load_cost()
    dec = yaml.safe_load((ROOT / "configs" / "decision.yaml").read_text())
    gain, loss = cost["saglam_kredi_getirisi"]["mean"], cost["temerrut_kaybi"]["mean"]

    d = dev_frame(pd.read_csv(CSV))
    _, _, X_ca, y_ca = split_xy(d)
    months = d.loc[X_ca.index, "issue_date"].dt.month.to_numpy()
    y = y_ca.to_numpy()
    model = XGBClassifier()
    model.load_model(MODEL_PATH)
    s = model.predict_proba(X_ca)[:, 1]
    low, high, point = (np.zeros(len(s)) for _ in range(3))
    for m in np.unique(months):
        te = months == m
        low[te], high[te], point[te] = predict_interval(fit_venn_abers(s[~te], y[~te]), s[te])

    t = table(
        low,
        high,
        s,
        point,
        y,
        gain,
        loss,
        dec["band"]["deger"],
        dec["zayif_destek_skor_araliklari"],
        dec["zayif_destek_esik_yakinligi_carpani"],
    )
    fmt = t.copy()
    for c in fmt.columns[1:]:
        fmt[c] = fmt[c].map(lambda v: f"{v:.4f}")
    REPORT.write_text(
        "# Hafta 2.4: hurdle duyarlılığı (yalnızca kalibrasyon dilimi, test dilimi kullanılmadı)\n\n"
        + KURGUSAL_VEREN
        + "\n\n"
        f"Kalibrasyon dilimi {len(y)} kayıt, genel temerrüt oranı {y.mean():.4f}. Aralıklar "
        "leave-one-month-out. getiri/kayıp: eğitim dilimi ortalamaları "
        f"({gain:.4f} / {loss:.4f}). band {dec['band']['deger']:.4f}. Seçilen hurdle: 0.11 "
        "(onay oranlarına bakılmadan, ADR-003).\n\n"
        + fmt.to_markdown(index=False)
        + "\n\n`*_orani`: tüm başvurular içindeki pay. `*_temerrut`: o gruptaki gözlenen "
        "temerrüt oranı.\n"
    )
    print(REPORT.read_text())


if __name__ == "__main__":
    main()
