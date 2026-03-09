from __future__ import annotations

import os
from typing import Any

from sklearn.linear_model import LogisticRegression


def _safe_fallback_model(random_state: int = 42) -> LogisticRegression:
    # liblinear keeps runtime simple in constrained environments.
    return LogisticRegression(max_iter=1000, n_jobs=1, solver="liblinear", random_state=random_state)


def _set_backend_info(model, *, requested: str, backend: str, reason: str, fallback_reason: str | None = None):
    setattr(model, "_credit_coach_requested_backend", requested)
    setattr(model, "_credit_coach_backend", backend)
    setattr(model, "_credit_coach_backend_reason", reason)
    setattr(model, "_credit_coach_fallback_reason", fallback_reason)


def get_training_backend_info(model) -> dict[str, str | None]:
    return {
        "requested_backend": getattr(model, "_credit_coach_requested_backend", None),
        "model_backend": getattr(model, "_credit_coach_backend", None),
        "backend_reason": getattr(model, "_credit_coach_backend_reason", None),
        "fallback_reason": getattr(model, "_credit_coach_fallback_reason", None),
    }


def _normalize_monotone_constraints(
    raw_constraints: Any,
    feature_names: list[str],
) -> str | None:
    if raw_constraints is None:
        return None

    if isinstance(raw_constraints, str):
        return raw_constraints

    if isinstance(raw_constraints, dict):
        ordered = [int(raw_constraints.get(name, 0)) for name in feature_names]
        return "(" + ",".join(str(v) for v in ordered) + ")"

    if isinstance(raw_constraints, (list, tuple)):
        values = [int(v) for v in raw_constraints]
        if len(values) != len(feature_names):
            raise ValueError(
                f"monotone_constraints length mismatch: {len(values)} != {len(feature_names)}"
            )
        return "(" + ",".join(str(v) for v in values) + ")"

    raise ValueError(f"Unsupported monotone_constraints type: {type(raw_constraints).__name__}")


def _train_xgboost(x_train, y_train, params: dict[str, Any]):
    import xgboost as xgb

    safe_params = dict(params)
    seed = int(safe_params.get("random_state", 42))
    safe_params.setdefault("n_jobs", 1)
    safe_params.setdefault("nthread", 1)
    safe_params.setdefault("random_state", seed)
    safe_params.setdefault("seed", seed)
    safe_params.setdefault("eval_metric", "auc")
    safe_params.setdefault("use_label_encoder", False)
    safe_params.setdefault("tree_method", "hist")

    mono = _normalize_monotone_constraints(
        raw_constraints=safe_params.get("monotone_constraints"),
        feature_names=list(getattr(x_train, "columns", [])),
    )
    if mono is not None:
        safe_params["monotone_constraints"] = mono

    model = xgb.XGBClassifier(**safe_params)
    model.fit(x_train, y_train)
    return model


def train_risk_model(x_train, y_train, model_type: str, params: dict[str, Any]):
    """
    Train risk model with deterministic backend selection.

    Environment override:
    - CREDIT_COACH_FORCE_BACKEND=xgboost|logistic_regression
    - CREDIT_COACH_ALLOW_XGB=1 enables xgboost execution in constrained environments.
    """
    forced = os.getenv("CREDIT_COACH_FORCE_BACKEND", "").strip().lower()
    requested = forced or str(model_type).lower()
    fallback_on_error = bool(params.get("fallback_on_error", True))
    allow_xgb = os.getenv("CREDIT_COACH_ALLOW_XGB", "0") == "1" or bool(params.get("allow_xgboost", False))
    seed = int(params.get("random_state", 42))

    if requested not in {"xgboost", "logistic_regression"}:
        raise ValueError(f"Unsupported model_type/backend: {requested}")

    if requested == "xgboost":
        if not allow_xgb:
            if not fallback_on_error:
                raise RuntimeError("xgboost requested but disabled by policy (set allow_xgboost/CREDIT_COACH_ALLOW_XGB)")
            model = _safe_fallback_model(random_state=seed)
            model.fit(x_train, y_train)
            _set_backend_info(
                model,
                requested=requested,
                backend="logistic_regression",
                reason="fallback_to_logistic",
                fallback_reason="xgboost_disabled_by_policy",
            )
            return model, "logistic_regression"

        try:
            model = _train_xgboost(x_train, y_train, params)
            _set_backend_info(
                model,
                requested=requested,
                backend="xgboost",
                reason="xgboost_trained",
            )
            return model, "xgboost"
        except Exception as exc:
            if not fallback_on_error:
                raise
            model = _safe_fallback_model(random_state=seed)
            model.fit(x_train, y_train)
            _set_backend_info(
                model,
                requested=requested,
                backend="logistic_regression",
                reason="fallback_to_logistic",
                fallback_reason=f"xgboost_error:{exc.__class__.__name__}",
            )
            return model, "logistic_regression"

    # requested logistic
    try:
        model = _safe_fallback_model(random_state=seed)
        model.fit(x_train, y_train)
        _set_backend_info(
            model,
            requested=requested,
            backend="logistic_regression",
            reason="requested_logistic_regression",
        )
        return model, "logistic_regression"
    except Exception:
        model = LogisticRegression(max_iter=2000, solver="lbfgs", random_state=seed)
        model.fit(x_train, y_train)
        _set_backend_info(
            model,
            requested=requested,
            backend="logistic_regression_lbfgs",
            reason="logistic_liblinear_failed_lbfgs_used",
        )
        return model, "logistic_regression_lbfgs"

