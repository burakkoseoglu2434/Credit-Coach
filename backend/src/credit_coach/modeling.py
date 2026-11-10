"""Model data preparation and baselines. The TEST split is never loaded here."""

from __future__ import annotations

import numpy as np
import pandas as pd
import yaml
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from credit_coach.features import MANIFEST_PATH, allowed_features
from credit_coach.leakage import assert_columns_allowed
from credit_coach.split import assign_split, cohort

SEED = 42
DEV_SPLITS = ("train", "calibration")  # test is excluded by construction
CATEGORICAL = {
    "purpose": None,
    "home_ownership": None,
    "application_type": None,
}
# term is constant inside the 36-month cohort; fico_range_high == fico_range_low + 4.
DROPPED = ("term", "fico_range_high")


def dev_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Cohort rows in train/calibration only, with `split` and `issue_date` columns."""
    label = assign_split(df)
    c = cohort(df)
    keep = label.isin(DEV_SPLITS)
    out = c.loc[keep.index[keep]].assign(split=label[keep])
    assert set(out["split"]) <= set(DEV_SPLITS)
    return out


def _emp_length(s: pd.Series) -> pd.Series:
    t = s.str.extract(r"(\d+)")[0].astype(float)
    return t.where(~s.str.contains("<", na=False), 0.0)


def design_matrix(rows: pd.DataFrame, categories: dict[str, list[str]] | None = None):
    """Allowed features -> numeric design matrix. Returns (X, categories used)."""
    cols = [c for c in allowed_features() if c not in DROPPED]
    assert_columns_allowed(cols)
    X = rows[cols].copy()
    X["emp_length"] = _emp_length(rows["emp_length"])
    ecl = pd.to_datetime(rows["earliest_cr_line"], format="%b-%Y")
    X["credit_history_months"] = (
        (rows["issue_date"].dt.year - ecl.dt.year) * 12
        + (rows["issue_date"].dt.month - ecl.dt.month)
    ).astype(float)
    X = X.drop(columns="earliest_cr_line")
    cats = categories or {c: sorted(rows[c].dropna().unique()) for c in CATEGORICAL}
    for c, levels in cats.items():
        for lv in levels:
            X[f"{c}={lv}"] = (rows[c] == lv).astype(float)
        X = X.drop(columns=c)
    return X.astype(float), cats


def split_xy(dev: pd.DataFrame):
    tr, ca = dev[dev["split"] == "train"], dev[dev["split"] == "calibration"]
    X_tr, cats = design_matrix(tr)
    X_ca, _ = design_matrix(ca, cats)
    return X_tr, tr["target"].astype(int), X_ca[X_tr.columns], ca["target"].astype(int)


def logistic_baseline() -> object:
    return make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(C=1.0, max_iter=2000, random_state=SEED),
    )


def xgb_params() -> dict:
    return dict(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=50,
        tree_method="hist",
        random_state=SEED,
        n_jobs=1,
        eval_metric="logloss",
    )


def unconstrained_xgb() -> XGBClassifier:
    return XGBClassifier(**xgb_params())


def metrics(model, X, y) -> dict[str, float]:
    p = model.predict_proba(X)[:, 1]
    return {
        "auc": float(roc_auc_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p)),
        "mean_pd": float(np.mean(p)),
    }


MONOTONE_PATH = MANIFEST_PATH.parents[0] / "monotone.yaml"


def load_monotone(path=MONOTONE_PATH) -> dict[str, int]:
    raw = yaml.safe_load(path.read_text())
    out = {f["ad"]: int(f["yon"]) for f in raw["features"]}
    for f in raw["features"]:
        if f["yon"] not in (-1, 0, 1) or not f["gerekce"].strip():
            raise ValueError(f"bad monotone entry: {f['ad']}")
    return out


def monotone_constraints(columns, path=MONOTONE_PATH) -> tuple[int, ...]:
    """Constraint vector aligned to design-matrix columns; every column must be accounted for."""
    raw = yaml.safe_load(path.read_text())
    table, prefixes = load_monotone(path), tuple(raw["unconstrained_prefixes"])
    out = []
    for c in columns:
        if c in table:
            out.append(table[c])
        elif c.startswith(prefixes):
            out.append(0)
        else:
            raise ValueError(f"no monotone decision for column {c}")
    return tuple(out)
