from __future__ import annotations

import sys
import types

import pandas as pd
import pytest

from credit_coach.model.train import get_training_backend_info, train_risk_model


class _DummyXGBClassifier:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def fit(self, x, y):
        self.n_rows_ = len(x)
        self.n_cols_ = x.shape[1]
        return self

    def predict_proba(self, x):
        p = pd.Series([0.5] * len(x), dtype=float).values
        return __import__("numpy").column_stack([1.0 - p, p])


def test_xgb_monotone_constraints_dict(monkeypatch):
    fake_xgb = types.SimpleNamespace(XGBClassifier=_DummyXGBClassifier)
    monkeypatch.setitem(sys.modules, "xgboost", fake_xgb)
    monkeypatch.setenv("CREDIT_COACH_ALLOW_XGB", "1")

    x = pd.DataFrame({"f1": [1.0, 2.0, 3.0], "f2": [0.5, 0.2, 0.1], "f3": [7.0, 8.0, 9.0]})
    y = pd.Series([0, 1, 0])
    model, backend = train_risk_model(
        x,
        y,
        model_type="xgboost",
        params={
            "allow_xgboost": True,
            "random_state": 7,
            "monotone_constraints": {"f1": 1, "f2": -1},
        },
    )
    info = get_training_backend_info(model)
    assert backend == "xgboost"
    assert model.kwargs["monotone_constraints"] == "(1,-1,0)"
    assert model.kwargs["seed"] == 7
    assert info["backend_reason"] == "xgboost_trained"
    assert info["fallback_reason"] is None


def test_xgb_disabled_falls_back_with_reason(monkeypatch):
    monkeypatch.delenv("CREDIT_COACH_ALLOW_XGB", raising=False)
    monkeypatch.delenv("CREDIT_COACH_FORCE_BACKEND", raising=False)

    x = pd.DataFrame({"f1": [0.0, 1.0, 2.0], "f2": [1.0, 0.0, 1.0]})
    y = pd.Series([0, 1, 1])
    model, backend = train_risk_model(
        x,
        y,
        model_type="xgboost",
        params={"allow_xgboost": False, "fallback_on_error": True, "random_state": 99},
    )
    info = get_training_backend_info(model)
    assert backend == "logistic_regression"
    assert info["backend_reason"] == "fallback_to_logistic"
    assert info["fallback_reason"] == "xgboost_disabled_by_policy"


def test_monotone_length_mismatch_raises_when_no_fallback(monkeypatch):
    fake_xgb = types.SimpleNamespace(XGBClassifier=_DummyXGBClassifier)
    monkeypatch.setitem(sys.modules, "xgboost", fake_xgb)
    monkeypatch.setenv("CREDIT_COACH_ALLOW_XGB", "1")

    x = pd.DataFrame({"f1": [0.0, 1.0], "f2": [1.0, 0.0], "f3": [0.2, 0.4]})
    y = pd.Series([0, 1])
    with pytest.raises(ValueError):
        train_risk_model(
            x,
            y,
            model_type="xgboost",
            params={
                "allow_xgboost": True,
                "fallback_on_error": False,
                "monotone_constraints": [1, -1],  # len mismatch
            },
        )

