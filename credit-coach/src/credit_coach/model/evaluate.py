from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    roc_auc_score,
    roc_curve,
)


def expected_calibration_error(y_true, y_prob, n_bins: int = 10) -> float:
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for i in range(n_bins):
        left = bins[i]
        right = bins[i + 1]
        mask = (y_prob >= left) & (y_prob < right) if i < n_bins - 1 else (y_prob >= left) & (y_prob <= right)
        if not np.any(mask):
            continue
        acc = float(np.mean(y_true[mask]))
        conf = float(np.mean(y_prob[mask]))
        ece += (np.sum(mask) / n) * abs(acc - conf)
    return float(ece)


def ks_statistic(y_true, y_prob) -> float:
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    return float(np.max(np.abs(tpr - fpr)))


def evaluate_binary_classifier(y_true, y_prob, tau: float) -> dict[str, float]:
    y_pred = (np.asarray(y_prob) >= tau).astype(int)
    auc = roc_auc_score(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)
    f1 = f1_score(y_true, y_pred)
    brier = brier_score_loss(y_true, y_prob)
    ece = expected_calibration_error(y_true, y_prob)
    ks = ks_statistic(y_true, y_prob)

    return {
        "auc": float(auc),
        "gini": float(2 * auc - 1),
        "pr_auc": float(pr_auc),
        "f1": float(f1),
        "brier": float(brier),
        "ece": float(ece),
        "ks": float(ks),
        "tau": float(tau),
    }
