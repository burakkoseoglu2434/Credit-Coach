"""Week 2.3: Venn-Abers calibration on the calibration split (test split never loaded).

Honest metrics use leave-one-month-out on the calibration split (time-contiguous folds).
The final calibrator is fit on the whole calibration split and linked to the MLflow run.
"""

from __future__ import annotations

import hashlib

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import mlflow  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import brier_score_loss, log_loss  # noqa: E402
from xgboost import XGBClassifier  # noqa: E402

from credit_coach.baseline import CSV  # noqa: E402
from credit_coach.calibration import (  # noqa: E402
    ece,
    fit_platt,
    fit_venn_abers,
    predict_interval,
    predict_platt,
)
from credit_coach.modeling import dev_frame, split_xy  # noqa: E402
from credit_coach.train_monotone import BACKEND, MODEL_PATH, ROOT  # noqa: E402

CAL_PATH = BACKEND / ".models" / "venn_abers.joblib"
REPORT = ROOT / "docs" / "week2_calibration.md"
PLOT = ROOT / "docs" / "week2_reliability.png"


def _metrics(p: np.ndarray, y: np.ndarray) -> dict[str, float]:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {"brier": brier_score_loss(y, p), "logloss": log_loss(y, p), "ece": ece(p, y)}


def main() -> None:
    dev = dev_frame(pd.read_csv(CSV))
    _, _, X_ca, y_ca = split_xy(dev)
    months = dev.loc[X_ca.index, "issue_date"].dt.month.to_numpy()
    y = y_ca.to_numpy()
    model = XGBClassifier()
    model.load_model(MODEL_PATH)
    s = model.predict_proba(X_ca)[:, 1]

    low, high, point, platt = (np.zeros(len(s)) for _ in range(4))
    for m in np.unique(months):
        te, tr = months == m, months != m
        va = fit_venn_abers(s[tr], y[tr])
        low[te], high[te], point[te] = predict_interval(va, s[te])
        platt[te] = predict_platt(fit_platt(s[tr], y[tr]), s[te])
    res = {"raw": _metrics(s, y), "platt": _metrics(platt, y), "venn_abers": _metrics(point, y)}
    width = high - low
    q = np.quantile(width, [0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
    in_interval = float((y.mean() >= low.min()) and (y.mean() <= high.max()))

    # support analysis: width by raw-score decile
    dec = pd.qcut(pd.Series(s), 10, labels=False, duplicates="drop")
    tab = pd.DataFrame({"s": s, "w": width, "low": low, "high": high, "dec": dec})
    g = tab.groupby("dec").agg(
        n=("s", "size"), s_min=("s", "min"), s_max=("s", "max"), width=("w", "mean")
    )
    thresh = 2 * g["width"].median()
    weak = g[g["width"] > thresh]

    # final calibrator and persistence
    final = fit_venn_abers(s, y)
    CAL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(final, CAL_PATH)
    digest = hashlib.sha256(CAL_PATH.read_bytes()).hexdigest()
    f_low, f_high, _ = predict_interval(final, s)
    assert ((0 <= f_low) & (f_low <= f_high) & (f_high <= 1)).all()

    # reliability diagram (equal-frequency bins, out-of-fold)
    fig, ax = plt.subplots(figsize=(5, 5))
    for name, p in (("ham model", s), ("Platt", platt), ("Venn-Abers", point)):
        o = np.argsort(p, kind="stable")
        chunks = np.array_split(o, 10)
        ax.plot([p[c].mean() for c in chunks], [y[c].mean() for c in chunks], "o-", label=name)
    ax.plot([0, 0.5], [0, 0.5], "k--", label="ideal")
    ax.set_xlabel("tahmin edilen PD")
    ax.set_ylabel("gözlenen temerrüt oranı")
    ax.legend()
    PLOT.parent.mkdir(exist_ok=True)
    fig.savefig(PLOT, dpi=120, bbox_inches="tight")

    lines = [
        "# Hafta 2.3: kalibrasyon raporu (test dilimi kullanılmadı)",
        "",
        f"Kalibrasyon dilimi: {len(s)} kayıt, gözlenen temerrüt oranı {y.mean():.4f}. "
        "Metrikler leave-one-month-out (zaman bitişik 4 kat) ile, yani kalibratörün görmediği "
        "aylar üzerinde hesaplandı.",
        "",
        "| Yöntem | Brier | LogLoss | ECE |",
        "|---|---|---|---|",
        *[
            f"| {k} | {v['brier']:.4f} | {v['logloss']:.4f} | {v['ece']:.4f} |"
            for k, v in res.items()
        ],
        "",
        "## PD aralığı genişliği (p_high - p_low, katlar dışı)",
        "",
        "| yüzdelik | 5 | 25 | 50 | 75 | 95 | 99 |",
        "|---|---|---|---|---|---|---|",
        "| genişlik | " + " | ".join(f"{x:.4f}" for x in q) + " |",
        "",
        "## Ham skor ondalığına göre genişlik (veri desteği)",
        "",
        "| ondalık | n | skor min | skor max | ort. genişlik |",
        "|---|---|---|---|---|",
        *[
            f"| {i} | {int(r.n)} | {r.s_min:.3f} | {r.s_max:.3f} | {r.width:.4f} |"
            for i, r in g.iterrows()
        ],
        "",
        f"Zayıf destek bölgesi (ort. genişlik > 2 × ondalık medyanı = {thresh:.4f}): "
        + (
            ", ".join(
                f"ondalık {i} (skor {r.s_min:.3f}-{r.s_max:.3f}, n={int(r.n)})"
                for i, r in weak.iterrows()
            )
            or "yok"
        ),
        "",
        f"Son kalibratör (tüm kalibrasyon dilimi): aralıklar geçerli (0 ≤ low ≤ high ≤ 1), "
        f"sha256 {digest[:16]}…",
        "",
        "![güvenilirlik](week2_reliability.png)",
        "",
    ]
    REPORT.write_text("\n".join(lines))

    mlflow.set_tracking_uri(f"sqlite:///{BACKEND / '.mlflow' / 'mlflow.db'}")
    run = mlflow.search_runs(experiment_names=["credit-coach-pd"], order_by=["start_time DESC"])
    with mlflow.start_run(run_id=run.iloc[0]["run_id"]):
        mlflow.log_artifact(str(CAL_PATH), artifact_path="calibrator")
        mlflow.log_artifact(str(REPORT))
        mlflow.log_artifact(str(PLOT))
        mlflow.log_param("calibrator_sha256", digest)
        mlflow.log_metrics(
            {f"cal_va_{k}": v for k, v in res["venn_abers"].items()}
            | {"cal_va_width_median": float(q[2])}
        )
    print(REPORT.read_text())
    del in_interval


if __name__ == "__main__":
    main()
