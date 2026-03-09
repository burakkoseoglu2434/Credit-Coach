from __future__ import annotations

import numpy as np
import pandas as pd

from credit_coach.xai.shap_local import compute_local_topk_reasons


class DummyLinearModel:
    coef_ = np.array([[0.2, -0.1, 0.05]])


def test_local_topk_reasons_shape_and_fields():
    x = pd.DataFrame(
        {
            "f1": [0.1, 0.2, 0.3, 0.4],
            "f2": [1.0, 0.8, 0.6, 0.4],
            "f3": [3.0, 3.5, 4.0, 4.5],
        }
    )
    model = DummyLinearModel()

    reasons = compute_local_topk_reasons(model, x.iloc[0], top_k=2)
    assert len(reasons) == 2
    assert {"feature", "value", "contribution", "abs_contribution", "direction"}.issubset(reasons[0].keys())
