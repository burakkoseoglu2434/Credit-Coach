from __future__ import annotations

from sklearn.calibration import CalibratedClassifierCV


def calibrate_classifier(
    model,
    x_cal,
    y_cal,
    method: str = "isotonic",
) -> CalibratedClassifierCV:
    calibrator = CalibratedClassifierCV(estimator=model, method=method, cv="prefit")
    calibrator.fit(x_cal, y_cal)
    return calibrator
