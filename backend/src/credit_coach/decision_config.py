"""Compute band width and weak-support ranges (calibration split only) and export bundle data.

Independent of the hurdle: no approval rates are computed here.
"""

from __future__ import annotations

import shutil

import numpy as np
import pandas as pd
import yaml
from xgboost import XGBClassifier

from credit_coach.baseline import CSV
from credit_coach.bundle import ROOT
from credit_coach.calibration import fit_venn_abers, predict_interval
from credit_coach.modeling import dev_frame, split_xy
from credit_coach.train_monotone import MODEL_PATH

DECISION_YAML = ROOT / "configs" / "decision.yaml"
BUNDLE = ROOT / "bundle"


def main() -> None:
    dev = dev_frame(pd.read_csv(CSV))
    _, _, X_ca, y_ca = split_xy(dev)
    months = dev.loc[X_ca.index, "issue_date"].dt.month.to_numpy()
    y = y_ca.to_numpy()
    model = XGBClassifier()
    model.load_model(MODEL_PATH)
    s = model.predict_proba(X_ca)[:, 1]

    low, high, point = (np.zeros(len(s)) for _ in range(3))
    for m in np.unique(months):
        te = months == m
        va = fit_venn_abers(s[~te], y[~te])
        low[te], high[te], point[te] = predict_interval(va, s[te])

    drift = {
        int(m): float(point[months == m].mean() - y[months == m].mean()) for m in np.unique(months)
    }
    band = max(abs(v) for v in drift.values())

    dec = pd.qcut(pd.Series(s), 10, labels=False, duplicates="drop")
    g = (
        pd.DataFrame({"s": s, "w": high - low, "dec": dec})
        .groupby("dec")
        .agg(s_min=("s", "min"), s_max=("s", "max"), width=("w", "mean"))
    )
    weak = g[g["width"] > 2 * g["width"].median()]

    DECISION_YAML.write_text(
        "# Karar yapılandırması: kalibrasyon diliminden, hurdle'dan bağımsız (ADR-003).\n"
        + yaml.safe_dump(
            {
                "version": 1,
                "band": {
                    "deger": band,
                    "kural": "kalibrasyon diliminde aylık |ort. kalibre PD - gözlenen oran| "
                    "en büyüğü",
                    "aylik_kayma": drift,
                },
                "zayif_destek_skor_araliklari": [
                    [float(r.s_min), float(r.s_max)] for _, r in weak.iterrows()
                ],
                "zayif_destek_kurali": "ondalık ort. aralık genişliği > 2 x ondalık medyanı",
            },
            allow_unicode=True,
            sort_keys=False,
        )
    )
    BUNDLE.mkdir(exist_ok=True)
    shutil.copyfile(MODEL_PATH, BUNDLE / "pd_monotone.json")
    np.savez_compressed(BUNDLE / "calibration_data.npz", scores=s, labels=y.astype(np.int8))
    print(DECISION_YAML.read_text())


if __name__ == "__main__":
    main()
