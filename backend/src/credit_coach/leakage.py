"""Leakage guards: allowed-column check for training matrices and single-feature AUC scan."""

from __future__ import annotations

import warnings
from collections.abc import Iterable

import pandas as pd

from credit_coach.features import Column, allowed_features
from credit_coach.split import ORDER, assign_split, cohort

AUC_WARN_THRESHOLD = 0.85


class LeakageError(ValueError):
    """A column outside the manifest's allowed set reached a training matrix."""


def assert_columns_allowed(columns: Iterable[str], manifest: list[Column] | None = None) -> None:
    allowed = set(allowed_features(manifest))
    bad = sorted(set(columns) - allowed)
    if bad:
        raise LeakageError(f"columns not allowed in training matrix: {bad}")


def build_training_matrix(
    df: pd.DataFrame, split: str = "train", manifest: list[Column] | None = None
) -> tuple[pd.DataFrame, pd.Series]:
    """Select allowed features for one time split. Also returns the target."""
    if split not in ORDER:
        raise ValueError(f"unknown split {split}")
    label = assign_split(df)
    rows = cohort(df).loc[label[label == split].index]
    cols = allowed_features(manifest)
    X = rows[cols]
    assert_columns_allowed(X.columns, manifest)
    return X, rows["target"].astype(int)


def auc(x: pd.Series, y: pd.Series) -> float:
    """Direction-free AUC of a single numeric feature vs binary target (rank based)."""
    m = x.notna()
    x, y = x[m], y[m]
    n1 = int(y.sum())
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0 or x.nunique() < 2:
        return 0.5
    r = x.rank(method="average")
    a = (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    return float(max(a, 1 - a))


def single_feature_aucs(X: pd.DataFrame, y: pd.Series) -> dict[str, float]:
    """Per-feature AUC. Text columns are encoded by in-sample target mean (low-cardinality only)."""
    out: dict[str, float] = {}
    for c in X.columns:
        s = X[c]
        if not pd.api.types.is_numeric_dtype(s):
            s = s.map(y.groupby(s).mean())
        out[c] = auc(s, y)
    return out


def high_auc_features(aucs: dict[str, float], threshold: float = AUC_WARN_THRESHOLD) -> list[str]:
    flagged = sorted(k for k, v in aucs.items() if v > threshold)
    if flagged:
        warnings.warn(f"single-feature AUC > {threshold}: {flagged}", UserWarning, stacklevel=2)
    return flagged
