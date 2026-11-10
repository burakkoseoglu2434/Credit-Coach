import numpy as np
import pandas as pd
import pytest

from credit_coach.features import load_manifest
from credit_coach.leakage import (
    LeakageError,
    assert_columns_allowed,
    auc,
    build_training_matrix,
    high_auc_features,
    single_feature_aucs,
)
from tests.test_features import CSV

MANIFEST = load_manifest()
FORBIDDEN = [c.ad for c in MANIFEST if not c.izin_verilen]
NAMED = ["int_rate", "grade", "sub_grade", "debt_settlement_flag"]
POST = [c.ad for c in MANIFEST if c.sinif == "POST_ORIGINATION"]


def test_named_and_post_origination_columns_are_forbidden_in_manifest():
    assert set(NAMED) <= set(FORBIDDEN)
    assert set(POST) <= set(FORBIDDEN)


def test_allowed_columns_pass():
    assert_columns_allowed([c.ad for c in MANIFEST if c.izin_verilen])


@pytest.mark.parametrize("col", FORBIDDEN)
def test_negative_every_forbidden_column_is_caught(col):
    allowed = [c.ad for c in MANIFEST if c.izin_verilen]
    with pytest.raises(LeakageError, match=col):
        assert_columns_allowed([*allowed, col])


def test_negative_unknown_column_is_caught():
    with pytest.raises(LeakageError):
        assert_columns_allowed(["not_in_manifest"])


def test_negative_forbidden_columns_added_to_matrix_fail():
    """Deliberately widen a real-shaped matrix with the named forbidden + post columns."""
    allowed = [c.ad for c in MANIFEST if c.izin_verilen]
    X = pd.DataFrame(np.zeros((3, len(allowed))), columns=allowed)
    for col in [*NAMED, *POST]:
        X[col] = 0
    with pytest.raises(LeakageError) as e:
        assert_columns_allowed(X.columns)
    for col in [*NAMED, *POST]:
        assert col in str(e.value)


def test_auc_detects_perfect_and_random_features():
    rng = np.random.default_rng(0)
    y = pd.Series(rng.integers(0, 2, 5000))
    assert auc(y + 0.0, y) == pytest.approx(1.0)
    assert auc(pd.Series(rng.normal(size=5000)), y) < 0.55


def test_high_auc_features_warns_on_leaky_feature():
    rng = np.random.default_rng(1)
    y = pd.Series(rng.integers(0, 2, 2000))
    X = pd.DataFrame(
        {"leaky": y * 10 + rng.normal(size=2000) * 0.1, "noise": rng.normal(size=2000)}
    )
    with pytest.warns(UserWarning, match="leaky"):
        flagged = high_auc_features(single_feature_aucs(X, y))
    assert flagged == ["leaky"]


@pytest.mark.skipif(not CSV.exists(), reason="raw data not available locally")
def test_real_training_matrix_uses_only_allowed_columns_and_reports_auc():
    df = pd.read_csv(CSV)
    X, y = build_training_matrix(df, "train")
    assert_columns_allowed(X.columns)
    assert len(X) == len(y) > 0
    aucs = single_feature_aucs(X, y)
    ranked = sorted(aucs.items(), key=lambda kv: -kv[1])[:5]
    print("top single-feature AUCs:", ranked)
    high_auc_features(aucs)  # warning only, never fails
