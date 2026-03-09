from __future__ import annotations

import numpy as np
import pandas as pd

from credit_coach.xai.shap_global import compute_global_importance_stability
from credit_coach.xai.shap_local import compute_local_reason_bundle


class DummyLinearModel:
    coef_ = np.array([[0.3, -0.2, 0.1, 0.05]])


def test_compute_local_reason_bundle_fields_and_bounds():
    model = DummyLinearModel()
    row = pd.Series({"f1": 0.2, "f2": 1.1, "f3": 0.4, "f4": 3.0})
    bundle = compute_local_reason_bundle(
        model,
        row,
        top_k=3,
        perturbations=5,
        noise_std=0.02,
        random_state=123,
    )
    reasons = bundle["reasons"]
    meta = bundle["meta"]

    assert len(reasons) == 3
    assert {"feature", "value", "contribution", "abs_contribution", "direction"}.issubset(reasons[0].keys())
    assert meta["method"] in {"shap", "fallback"}
    assert 0.0 <= meta["stability_score"] <= 1.0
    assert meta["baseline_drift_l1"] >= 0.0
    assert 0.0 <= meta["explainability_confidence"] <= 1.0
    assert meta["perturbation_count"] == 5


def test_compute_global_importance_stability_fields_and_bounds():
    model = DummyLinearModel()
    x = pd.DataFrame(
        {
            "f1": np.linspace(0, 1, 50),
            "f2": np.linspace(1, 0, 50),
            "f3": np.sin(np.linspace(0, 2, 50)),
            "f4": np.cos(np.linspace(0, 2, 50)),
        }
    )
    report = compute_global_importance_stability(
        model,
        x,
        max_samples=50,
        bootstrap_rounds=4,
        random_state=7,
        top_n=3,
    )
    imp = report["importance"]
    meta = report["meta"]

    assert not imp.empty
    assert {"feature", "importance"}.issubset(imp.columns)
    assert 0.0 <= meta["stability_score"] <= 1.0
    assert meta["baseline_drift_l1"] >= 0.0
    assert 0.0 <= meta["explainability_confidence"] <= 1.0
    assert meta["bootstrap_rounds"] == 4

