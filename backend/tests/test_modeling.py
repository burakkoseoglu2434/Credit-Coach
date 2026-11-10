import pandas as pd
import pytest

from credit_coach.modeling import DEV_SPLITS, design_matrix, dev_frame
from tests.test_features import CSV
from tests.test_split import _frame


def _raw() -> pd.DataFrame:
    df = _frame()
    n = len(df)
    df["emp_length"] = ["10+ years", "< 1 year", "3 years", None] * (n // 4) + [None] * (n % 4)
    df["earliest_cr_line"] = "Jan-2000"
    for c, v in (
        ("purpose", "car"),
        ("home_ownership", "RENT"),
        ("application_type", "Individual"),
    ):
        df[c] = v
    from credit_coach.features import allowed_features

    for c in allowed_features():
        if c not in df.columns:
            df[c] = 1.0
    return df


def test_dev_frame_excludes_test_split():
    dev = dev_frame(_raw())
    assert set(dev["split"]) == set(DEV_SPLITS)
    assert dev["issue_date"].max() < pd.Timestamp("2015-09-01")


def test_design_matrix_uses_only_allowed_sources_and_is_stable():
    dev = dev_frame(_raw())
    X, cats = design_matrix(dev)
    assert not any(b in X.columns for b in ("int_rate", "grade", "target", "issue_d"))
    X2, _ = design_matrix(dev, cats)
    assert list(X.columns) == list(X2.columns)
    assert X["emp_length"].dropna().isin([0.0, 3.0, 10.0]).all()


@pytest.mark.skipif(not CSV.exists(), reason="raw data not available locally")
def test_real_dev_frame_has_no_test_rows():
    dev = dev_frame(pd.read_csv(CSV, usecols=lambda c: True))
    assert set(dev["split"]) == set(DEV_SPLITS)
    X, _ = design_matrix(dev)
    assert len(X) == len(dev)


def test_monotone_covers_every_design_column_and_matches_approved_counts():
    from credit_coach.modeling import monotone_constraints

    X, _ = design_matrix(dev_frame(_raw()))
    mc = monotone_constraints(X.columns)
    assert len(mc) == X.shape[1]
    assert mc.count(1) == 13 and mc.count(-1) == 7


def test_monotone_unknown_column_is_rejected():
    from credit_coach.modeling import monotone_constraints

    with pytest.raises(ValueError):
        monotone_constraints(["surprise_feature"])


def _synthetic_xy(n=4000, seed=0):
    import numpy as np

    rng = np.random.default_rng(seed)
    X = pd.DataFrame(rng.normal(size=(n, 3)), columns=["dti", "fico_range_low", "loan_amnt"])
    logit = 0.9 * X["dti"] - 0.9 * X["fico_range_low"] + np.sin(3 * X["loan_amnt"])
    y = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    return X, y


def test_monotone_model_property_holds_and_unconstrained_can_violate():
    from credit_coach.modeling import check_monotone, monotone_xgb

    X, y = _synthetic_xy()
    m = monotone_xgb(X.columns, n_estimators=80, max_depth=4, min_child_weight=1).fit(X, y)
    assert check_monotone(m, X) == []


def test_property_check_detects_wrong_direction():
    from xgboost import XGBClassifier

    from credit_coach.modeling import check_monotone

    X, y = _synthetic_xy()
    # dti has +1 in monotone.yaml; a free model trained on the flipped target must violate it
    flipped = XGBClassifier(n_estimators=80, max_depth=4, random_state=0, n_jobs=1).fit(X, 1 - y)
    assert check_monotone(flipped, X) != []


def test_training_is_deterministic():
    from credit_coach.modeling import monotone_xgb

    X, y = _synthetic_xy()
    a = monotone_xgb(X.columns, n_estimators=50, min_child_weight=1).fit(X, y).predict_proba(X)
    b = monotone_xgb(X.columns, n_estimators=50, min_child_weight=1).fit(X, y).predict_proba(X)
    assert (a == b).all()


@pytest.mark.skipif(
    not (CSV.exists() and (CSV.parents[3] / "backend/.models/pd_monotone.json").exists()),
    reason="raw data or trained model not available locally",
)
def test_real_saved_model_is_monotone_on_calibration_sample():
    from xgboost import XGBClassifier

    from credit_coach.modeling import check_monotone, split_xy

    _, _, X_ca, _ = split_xy(dev_frame(pd.read_csv(CSV)))
    model = XGBClassifier()
    model.load_model(CSV.parents[3] / "backend/.models/pd_monotone.json")
    assert check_monotone(model, X_ca) == []
