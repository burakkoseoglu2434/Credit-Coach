"""Week 2.5: run the frozen pipeline on the TEST split exactly once and report. No tuning.

Safeguards: refuses to run if the bundle lock does not verify or if the report already exists
(the test split is consumed once). Uses only frozen artifacts under bundle/ and configs/.
"""

from __future__ import annotations

import json
import subprocess

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from xgboost import XGBClassifier

from credit_coach.baseline import CSV
from credit_coach.bundle import LOCK_PATH, ROOT, verify_lock
from credit_coach.calibration import ece, fit_venn_abers, predict_interval
from credit_coach.decision import (
    DecisionConfig,
    approval_threshold,
    decide,
    load_cost,
    total_hurdle,
)
from credit_coach.labels import KURGUSAL_VEREN
from credit_coach.modeling import design_matrix, dev_frame, split_xy
from credit_coach.split import assign_split, cohort

REPORT = ROOT / "docs" / "week2_report.md"
EXPECTED = (0.67, 0.71)


def guard() -> None:
    if REPORT.exists():
        raise SystemExit("test split already consumed: docs/week2_report.md exists")
    problems = verify_lock(json.loads(LOCK_PATH.read_text()))
    if problems:
        raise SystemExit(f"bundle does not verify: {problems}")
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    if dirty:
        raise SystemExit(f"working tree not clean, refusing to touch the test split:\n{dirty}")


def main() -> None:
    guard()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    cost = load_cost()
    dec = yaml.safe_load((ROOT / "configs" / "decision.yaml").read_text())
    gain, loss = cost["saglam_kredi_getirisi"]["mean"], cost["temerrut_kaybi"]["mean"]
    hurdle = total_hurdle(cost)
    thr = approval_threshold(gain, loss, hurdle)
    cfg = DecisionConfig(
        thr,
        dec["band"]["deger"],
        tuple(map(tuple, dec["zayif_destek_skor_araliklari"])),
        dec["zayif_destek_esik_yakinligi_carpani"],
    )

    raw = pd.read_csv(CSV)
    X_tr, _, _, _ = split_xy(dev_frame(raw))  # only for column order and category levels
    _, cats = design_matrix(dev_frame(raw).query("split == 'train'"))
    label = assign_split(raw)
    te = cohort(raw).loc[label[label == "test"].index]
    X_te = design_matrix(te, cats)[0][X_tr.columns]
    y = te["target"].astype(int).to_numpy()

    model = XGBClassifier()
    model.load_model(ROOT / "bundle" / "pd_monotone.json")
    s = model.predict_proba(X_te)[:, 1]
    cal = np.load(ROOT / "bundle" / "calibration_data.npz")
    low, high, point = predict_interval(fit_venn_abers(cal["scores"], cal["labels"].astype(int)), s)
    decisions = decide(low, high, s, cfg, point)

    width = high - low
    q = np.quantile(width, [0.05, 0.5, 0.95, 0.99])
    rate = {k: float((decisions == k).mean()) for k in ("onay", "insana_git", "onay_degil")}
    appr = decisions == "onay"
    res = {
        "n": len(y),
        "bad_rate": float(y.mean()),
        "mean_pd_point": float(point.mean()),
        "auc_raw_model": float(roc_auc_score(y, s)),
        "auc_calibrated_point": float(roc_auc_score(y, point)),
        "brier_raw": float(brier_score_loss(y, np.clip(s, 1e-6, 1 - 1e-6))),
        "brier_calibrated": float(brier_score_loss(y, np.clip(point, 1e-6, 1 - 1e-6))),
        "logloss_calibrated": float(log_loss(y, np.clip(point, 1e-6, 1 - 1e-6))),
        "ece_raw": ece(s, y),
        "ece_calibrated": ece(point, y),
        "width_p05_p50_p95_p99": [float(x) for x in q],
        "decision_rates": rate,
        "approved_default_rate": float(y[appr].mean()) if appr.any() else None,
        "threshold": thr,
        "hurdle": hurdle,
        "band": cfg.band,
    }
    auc = res["auc_raw_model"]
    verdict = (
        "içinde"
        if EXPECTED[0] <= auc <= EXPECTED[1]
        else "altında"
        if auc < EXPECTED[0]
        else "üstünde"
    )
    REPORT.write_text(
        "# Hafta 2.5: tek seferlik test raporu\n\n" + KURGUSAL_VEREN + "\n\n"
        f"Test dilimi (2015-09..2015-12, 36 ay) {res['n']} kayıt, gözlenen temerrüt oranı "
        f"{res['bad_rate']:.4f}. Dondurulmuş paket (bundle.lock.json doğrulandı), git "
        f"`{commit[:10]}`. Test dilimi yalnızca bir kez çalıştırıldı; hiçbir ayar yapılmadı.\n\n"
        "| Metrik | Değer |\n|---|---|\n"
        f"| Out-of-time AUC (ham model) | {res['auc_raw_model']:.4f} |\n"
        f"| AUC (kalibre nokta tahmini) | {res['auc_calibrated_point']:.4f} |\n"
        f"| Brier (ham / kalibre) | {res['brier_raw']:.4f} / {res['brier_calibrated']:.4f} |\n"
        f"| LogLoss (kalibre) | {res['logloss_calibrated']:.4f} |\n"
        f"| ECE (ham / kalibre) | {res['ece_raw']:.4f} / {res['ece_calibrated']:.4f} |\n"
        f"| Ort. kalibre PD / gözlenen oran | {res['mean_pd_point']:.4f} / "
        f"{res['bad_rate']:.4f} |\n"
        f"| Aralık genişliği (5/50/95/99. yüzdelik) | " + " / ".join(f"{x:.4f}" for x in q) + " |\n"
        f"| Onay eşiği (hurdle {hurdle:.2f}) | {thr:.4f} |\n"
        f"| Onay oranı | {rate['onay']:.4f} |\n"
        f"| İnsana git oranı | {rate['insana_git']:.4f} |\n"
        f"| Onay değil oranı | {rate['onay_degil']:.4f} |\n"
        f"| Onaylananlarda gözlenen temerrüt | {res['approved_default_rate']} |\n\n"
        f"Beklenti 0,67-0,71 ile karşılaştırma: ham model AUC {auc:.4f}, beklentinin {verdict}. "
        "Nedenine dair tahmin yürütülmedi, yalnızca raporlandı.\n"
    )
    print(REPORT.read_text())


if __name__ == "__main__":
    main()
