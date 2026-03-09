from __future__ import annotations

import json

from credit_coach.safety.statistical import estimate_prediction_ci


def test_estimate_prediction_ci_uses_conformal_calibration_artifact(tmp_path):
    payload = {
        "model_version": "m1",
        "sample_count": 100,
        "residual_quantiles": {
            "0.0500": 0.02,
            "0.1000": 0.01,
        },
    }
    p = tmp_path / "conformal_calibration.json"
    p.write_text(json.dumps(payload), encoding="utf-8")

    low, high = estimate_prediction_ci(
        0.40,
        alpha=0.05,
        method="conformal",
        conformal_residual_quantile=0.10,
        conformal_min_width=0.005,
        conformal_calibration_path=str(p),
    )
    assert abs(low - 0.38) < 1e-9
    assert abs(high - 0.42) < 1e-9


def test_estimate_prediction_ci_adaptive_score_band_cap(tmp_path):
    payload = {
        "model_version": "m2",
        "sample_count": 100,
        "residual_quantiles": {
            "0.0500": 0.50,
        },
        "score_bin_edges": [0.0, 0.5, 1.0],
        "score_bin_widths": {"0.0500": [0.03, 0.08]},
        "score_bin_gaps": [0.01, 0.02],
    }
    p = tmp_path / "conformal_calibration.json"
    p.write_text(json.dumps(payload), encoding="utf-8")

    low, high = estimate_prediction_ci(
        0.40,
        alpha=0.05,
        method="conformal",
        conformal_residual_quantile=0.10,
        conformal_min_width=0.005,
        conformal_calibration_path=str(p),
        conformal_adaptive_by_score=True,
        conformal_adaptive_mode="cap",
    )
    assert abs(low - 0.37) < 1e-9
    assert abs(high - 0.43) < 1e-9


def test_estimate_prediction_ci_applies_max_width_cap(tmp_path):
    payload = {
        "model_version": "m3",
        "sample_count": 100,
        "residual_quantiles": {
            "0.0500": 0.30,
        },
    }
    p = tmp_path / "conformal_calibration.json"
    p.write_text(json.dumps(payload), encoding="utf-8")

    low, high = estimate_prediction_ci(
        0.40,
        alpha=0.05,
        method="conformal",
        conformal_residual_quantile=0.10,
        conformal_min_width=0.005,
        conformal_calibration_path=str(p),
        conformal_max_width=0.05,
    )
    assert abs(low - 0.35) < 1e-9
    assert abs(high - 0.45) < 1e-9
