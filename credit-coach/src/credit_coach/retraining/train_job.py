from __future__ import annotations

from credit_coach.model.calibrate import calibrate_classifier
from credit_coach.model.evaluate import evaluate_binary_classifier
from credit_coach.model.predict import predict_proba_pd
from credit_coach.model.train import get_training_backend_info, train_risk_model


def train_challenger(x_train, y_train, x_test, y_test, model_type: str, params: dict, tau: float):
    model, backend = train_risk_model(x_train, y_train, model_type=model_type, params=params)
    calibrator = calibrate_classifier(model, x_test, y_test, method="isotonic")
    y_prob = predict_proba_pd(model, calibrator, x_test)
    metrics = evaluate_binary_classifier(y_test, y_prob, tau=tau)
    metrics["model_backend"] = backend
    backend_info = get_training_backend_info(model)
    metrics["requested_backend"] = backend_info.get("requested_backend")
    metrics["backend_reason"] = backend_info.get("backend_reason")
    metrics["fallback_reason"] = backend_info.get("fallback_reason")
    return model, calibrator, metrics
