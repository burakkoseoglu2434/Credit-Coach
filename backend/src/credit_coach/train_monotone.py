"""Week 2.2: tune on inner train validation, ablate constrained vs unconstrained, log to MLflow.

The TEST split is never loaded. The calibration split is used only to report validation AUC.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
from pathlib import Path

import mlflow
import pandas as pd
from sklearn.metrics import roc_auc_score

from credit_coach.baseline import CSV
from credit_coach.features import MANIFEST_PATH
from credit_coach.modeling import (
    SEED,
    check_monotone,
    dev_frame,
    inner_masks,
    metrics,
    monotone_xgb,
    split_xy,
    xgb_params,
)
from credit_coach.split import SPLIT_CONFIG_PATH

ROOT = MANIFEST_PATH.parents[1]
MONOTONE = MANIFEST_PATH.parent / "monotone.yaml"
BACKEND = ROOT / "backend"
MODEL_PATH = BACKEND / ".models" / "pd_monotone.json"
REPORT = ROOT / "docs" / "week2_validation.md"
GRID = {"max_depth": [3, 5], "n_estimators": [300, 600], "min_child_weight": [50, 300]}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    return head + ("-dirty" if dirty else "")


def tune(make, X, y, issue_date) -> tuple[dict, list[dict]]:
    fit, dev = inner_masks(issue_date)
    results = []
    for md, ne, mcw in itertools.product(*GRID.values()):
        p = {"max_depth": md, "n_estimators": ne, "min_child_weight": mcw}
        m = make(X.columns, **p) if make is monotone_xgb else make(**p)
        m.fit(X[fit], y[fit])
        results.append(
            {**p, "inner_auc": float(roc_auc_score(y[dev], m.predict_proba(X[dev])[:, 1]))}
        )
    best = max(results, key=lambda r: r["inner_auc"])
    return {k: best[k] for k in GRID}, results


def _unc(**p):
    from xgboost import XGBClassifier

    return XGBClassifier(**{**xgb_params(), **p})


def main() -> None:
    dev = dev_frame(pd.read_csv(CSV))
    X_tr, y_tr, X_ca, y_ca = split_xy(dev)
    issue = dev.loc[X_tr.index, "issue_date"]

    best_m, grid_m = tune(monotone_xgb, X_tr, y_tr, issue)
    best_u, grid_u = tune(lambda cols=None, **p: _unc(**p), X_tr, y_tr, issue)

    mono = monotone_xgb(X_tr.columns, **best_m).fit(X_tr, y_tr)
    unc = _unc(**best_u).fit(X_tr, y_tr)
    m_cal, u_cal = metrics(mono, X_ca, y_ca), metrics(unc, X_ca, y_ca)
    violations = check_monotone(mono, X_ca)
    cost = u_cal["auc"] - m_cal["auc"]

    MODEL_PATH.parent.mkdir(exist_ok=True)
    mono.save_model(MODEL_PATH)

    mlflow.set_tracking_uri(f"sqlite:///{BACKEND / '.mlflow' / 'mlflow.db'}")
    (BACKEND / ".mlflow").mkdir(exist_ok=True)
    mlflow.set_experiment("credit-coach-pd")
    with mlflow.start_run(run_name="monotone-xgb"):
        mlflow.log_params({f"mono_{k}": v for k, v in best_m.items()} | {"seed": SEED})
        mlflow.log_params(
            {
                "git_commit": git_commit(),
                "features_manifest_sha256": sha(MANIFEST_PATH),
                "monotone_sha256": sha(MONOTONE),
                "split_yaml_sha256": sha(SPLIT_CONFIG_PATH),
                "n_features": X_tr.shape[1],
                "train_rows": len(X_tr),
                "calibration_rows": len(X_ca),
            }
        )
        mlflow.log_artifact(str(SPLIT_CONFIG_PATH))
        mlflow.log_artifact(str(MANIFEST_PATH))
        mlflow.log_artifact(str(MONOTONE))
        mlflow.log_metrics({f"cal_{k}": v for k, v in m_cal.items()})
        mlflow.log_metrics(
            {
                "unconstrained_cal_auc": u_cal["auc"],
                "monotonic_cost_auc": cost,
                "monotone_violations": float(len(violations)),
            }
        )
        mlflow.xgboost.log_model(mono, name="model", registered_model_name="credit-coach-pd")

    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(
        "# Hafta 2.2: doğrulama raporu (test dilimi kullanılmadı)\n\n"
        "- Ayar: yalnızca train içi zaman doğrulaması (fit ≤ 2014-03, dev ≥ 2014-07), "
        f"seed {SEED}\n"
        f"- Seçilen (monoton): {json.dumps(best_m)}\n"
        f"- Seçilen (kısıtsız): {json.dumps(best_u)}\n\n"
        "| Model | Kalibrasyon AUC | Brier | LogLoss |\n|---|---|---|---|\n"
        f"| Monoton XGBoost | {m_cal['auc']:.4f} | {m_cal['brier']:.4f} "
        f"| {m_cal['logloss']:.4f} |\n"
        f"| Kısıtsız XGBoost | {u_cal['auc']:.4f} | {u_cal['brier']:.4f} "
        f"| {u_cal['logloss']:.4f} |\n\n"
        f"Kısıtın maliyeti (kısıtsız AUC - monoton AUC): {cost:+.4f}\n\n"
        f"Monotonluk ihlali veren özellik: {violations or 'yok'}\n\n"
        "## Izgara (iç doğrulama AUC)\n\n"
        + "\n".join(f"- mono {r}" for r in grid_m)
        + "\n"
        + "\n".join(f"- unc {r}" for r in grid_u)
        + "\n"
    )
    print(
        json.dumps(
            {
                "mono": m_cal,
                "unc": u_cal,
                "cost": cost,
                "violations": violations,
                "best_mono": best_m,
                "best_unc": best_u,
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
