from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from credit_coach.model.evaluate import evaluate_binary_classifier
from credit_coach.model.train import train_risk_model


def test_train_and_evaluate_smoke():
    rng = np.random.default_rng(42)
    x = pd.DataFrame(rng.normal(size=(200, 5)), columns=[f"f{i}" for i in range(5)])
    y = (x["f0"] + x["f1"] * 0.3 + rng.normal(scale=0.5, size=200) > 0).astype(int)

    model, backend = train_risk_model(x, y, model_type="xgboost", params={"random_state": 42})
    prob = model.predict_proba(x)[:, 1]
    m = evaluate_binary_classifier(y, prob, tau=0.5)

    assert backend in {"xgboost", "logistic_regression", "logistic_regression_lbfgs"}
    assert 0.5 <= m["auc"] <= 1.0


def test_train_invalid_backend_raises():
    x = pd.DataFrame({"f1": [0.0, 1.0], "f2": [1.0, 0.0]})
    y = pd.Series([0, 1])
    with pytest.raises(ValueError):
        train_risk_model(x, y, model_type="unsupported", params={})
