"""Scorer implementations for the recourse engine.

SyntheticScorer: small deterministic monotone scorer for tests (CI has no model).
ModelScorer: frozen bundle model + Venn-Abers calibrator refit from bundle/calibration_data.npz.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from credit_coach.recourse import Skor

# sign follows configs/monotone.yaml; loan_amnt is unconstrained in the model, so its term is a
# test knob (loan_mode) rather than a claim about the real model.
_TERMS = {
    "revol_util": (+1.0, 100.0, 2.0),
    "dti": (+1.0, 40.0, 1.5),
    "fico_range_low": (-1.0, 200.0, 2.0),
    "annual_inc": (-1.0, 150000.0, 1.0),
    "revol_bal": (+1.0, 50000.0, 0.3),
    "tot_cur_bal": (+1.0, 300000.0, 0.1),
    "total_bal_ex_mort": (+1.0, 100000.0, 0.1),
}


class SyntheticScorer:
    """p = sigmoid(bias + sum w*sign*x/scale), +-width interval. `loan_mode`:
    "mild_up" (default, risk grows with amount), "kink" (risk RISES when the amount is cut below
    `kink_at`, a non-monotone shape used to test deep-level invalidation), "flat"."""

    def __init__(
        self,
        bias: float = -4.0,
        width: float = 0.01,
        loan_mode: str = "mild_up",
        kink_at: float = 8000.0,
    ) -> None:
        self.bias, self.width, self.loan_mode, self.kink_at = bias, width, loan_mode, kink_at

    def _z(self, v: Mapping[str, Any]) -> float:
        z = self.bias
        for name, (sign, scale, w) in _TERMS.items():
            x = v.get(name)
            if x is not None:
                if name == "fico_range_low":
                    x = x - 660.0
                z += w * sign * x / scale
        ln = v.get("loan_amnt")
        if ln is not None:
            if self.loan_mode == "mild_up":
                z += 0.5 * ln / 35000.0
            elif self.loan_mode == "kink":
                z += 0.5 * ln / 35000.0 + (3.0 if ln < self.kink_at else 0.0)
        return z

    def skorla_toplu(self, vektorler: Sequence[Mapping[str, Any]], tarih: Any = None) -> list[Skor]:
        out = []
        for v in vektorler:
            p = 1.0 / (1.0 + math.exp(-self._z(v)))
            lo, hi = max(0.0, p - self.width), min(1.0, p + self.width)
            out.append(Skor(lo, p, hi, p))
        return out


class ModelScorer:
    """Real scorer: monotone XGBoost bundle model + Venn-Abers refit on the calibration split.

    `tarih` is the application date (a pandas Timestamp) used for credit_history_months.
    """

    def __init__(self) -> None:
        import numpy as np
        from xgboost import XGBClassifier

        from credit_coach.bundle import ROOT
        from credit_coach.calibration import fit_venn_abers
        from credit_coach.support import load_support

        self.model = XGBClassifier()
        self.model.load_model(ROOT / "bundle" / "pd_monotone.json")
        cal = np.load(ROOT / "bundle" / "calibration_data.npz")
        self.va = fit_venn_abers(cal["scores"], cal["labels"].astype(int))
        self.categories = {
            k: sorted(v)
            for k, v in load_support().kategorik.items()
            if k in ("purpose", "home_ownership", "application_type")
        }

    def skorla_toplu(self, vektorler: Sequence[Mapping[str, Any]], tarih: Any) -> list[Skor]:
        import pandas as pd

        from credit_coach.calibration import predict_interval
        from credit_coach.modeling import design_matrix

        rows = pd.DataFrame(list(vektorler))
        rows["issue_date"] = pd.Timestamp(tarih)
        X, _ = design_matrix(rows, self.categories)
        names = self.model.get_booster().feature_names
        if names:
            X = X[names]
        ham = self.model.predict_proba(X)[:, 1]
        lo, hi, pt = predict_interval(self.va, ham)
        return [
            Skor(float(a), float(c), float(b), float(h))
            for a, b, c, h in zip(lo, hi, pt, ham, strict=True)
        ]
