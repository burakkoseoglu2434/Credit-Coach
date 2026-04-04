from __future__ import annotations

import inspect
import threading
import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from credit_coach.model.predict import predict_proba_pd
from credit_coach.recourse.action_space import (
    get_action_spec,
    get_dice_generation_metadata,
    normalize_dice_target_value,
)

_ALLOWED_DICE_METHODS = ("random", "genetic", "kdtree")
_ALLOWED_DICE_METHOD_SET = set(_ALLOWED_DICE_METHODS)
_DICE_CACHE_LOCK = threading.Lock()
_DICE_RUNTIME_CACHE: dict[tuple, "_DiceRuntime"] = {}


class _ModelProxy:
    def __init__(self, model, calibrator, feature_cols: list[str]):
        self.model = model
        self.calibrator = calibrator
        self.feature_cols = feature_cols

    def predict_proba(self, x):
        df = x if isinstance(x, pd.DataFrame) else pd.DataFrame(x, columns=self.feature_cols)
        p = predict_proba_pd(self.model, self.calibrator, df[self.feature_cols])
        return np.column_stack([1.0 - p, p])

    def predict(self, x):
        return (self.predict_proba(x)[:, 1] >= 0.5).astype(int)


@dataclass
class _DiceRuntime:
    data_obj: object
    model_obj: object
    continuous_features: list[str]
    categorical_features: list[str]
    explainers: dict[str, object] = field(default_factory=dict)


def _heuristic_actions(
    row: pd.Series,
    actionable_features: list[str],
    max_actions: int = 2,
) -> list[dict]:
    actions: list[dict] = []
    max_actions = max(1, int(max_actions))
    for feat in actionable_features:
        if len(actions) >= max_actions:
            break
        if feat not in row.index:
            continue
        try:
            spec = get_action_spec(feat)
            dice_meta = get_dice_generation_metadata(feat)
        except Exception:
            continue
        if not bool(dice_meta["dice_generatable"]):
            continue
        current = float(row[feat])
        base_step = max(abs(float(spec.step)), max(1.0, abs(current) * 0.05))
        if spec.direction == "increase":
            target = current + base_step
        elif spec.direction == "decrease":
            target = current - base_step
        else:
            target = current * 0.95
        if spec.min_val is not None:
            target = max(float(spec.min_val), float(target))
        if spec.max_val is not None:
            target = min(float(spec.max_val), float(target))
        target = normalize_dice_target_value(
            feat,
            current_value=current,
            target_value=float(target),
        )
        if abs(float(target) - current) <= 1e-9:
            continue
        actions.append(
            {
                "feature_name": feat,
                "current_value": current,
                "target_value": float(target),
            }
        )
    return actions


def _fallback_response(
    row: pd.Series,
    actionable_features: list[str],
    *,
    reason: str,
    method_requested: str,
    method_used: str,
    max_actions: int,
    exception_type: str | None = None,
    exception_message: str | None = None,
    method_attempts: list[dict] | None = None,
) -> tuple[list[list[dict]], str, dict]:
    actions = [_heuristic_actions(row, actionable_features, max_actions=max_actions)]
    changed = sorted({a["feature_name"] for a in actions[0]})
    attempts = method_attempts or [{"method": method_used, "status": "fallback"}]
    telemetry = {
        "method_requested": method_requested,
        "method_used": method_used,
        "fallback_reason": reason,
        "exception_type": exception_type,
        "exception_message": exception_message,
        "action_set_count": len(actions),
        "changed_features_union": changed,
        "changed_feature_union_count": len(changed),
        "attempted_method_count": len(attempts),
        "attempted_methods": [a.get("method") for a in attempts],
        "method_attempts": attempts,
    }
    return actions, f"heuristic_fallback_{reason}", telemetry


def _normalize_dice_method(method: str) -> str:
    m = str(method).strip().lower()
    return m if m in _ALLOWED_DICE_METHOD_SET else "random"


def _method_attempt_order(method: str, *, enable_method_fallback: bool) -> list[str]:
    if not enable_method_fallback:
        return [method]
    return [method] + [m for m in _ALLOWED_DICE_METHODS if m != method]


def _build_generate_kwargs(
    generate_fn,
    *,
    query_df: pd.DataFrame,
    total_cfs: int,
    safe_actionable: list[str],
    random_seed: int,
    stopping_threshold: float | None = None,
) -> dict:
    params = inspect.signature(generate_fn).parameters
    has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    kwargs = {
        "total_CFs": int(max(1, total_cfs)),
        "desired_class": 0,
        "features_to_vary": safe_actionable,
    }
    if "query_instance" in params:
        kwargs["query_instance"] = query_df
    elif "query_instances" in params:
        kwargs["query_instances"] = query_df
    else:
        # Keep backward compatibility for wrappers that accept **kwargs.
        kwargs["query_instance"] = query_df

    # Some DiCE backends (notably kdtree wrappers) expose **kwargs but still
    # reject random_seed. Only pass it when explicitly declared.
    if "random_seed" in params:
        kwargs["random_seed"] = random_seed
    if stopping_threshold is not None and ("stopping_threshold" in params or has_var_kw):
        kwargs["stopping_threshold"] = float(stopping_threshold)
    if "verbose" in params or has_var_kw:
        kwargs["verbose"] = False
    return kwargs


def _prepare_dice_dataframe(
    train_df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    data_df = train_df[feature_cols + [target_col]].copy()
    continuous_features: list[str] = []
    categorical_features: list[str] = []

    for col in feature_cols:
        if pd.api.types.is_numeric_dtype(data_df[col]):
            data_df[col] = pd.to_numeric(data_df[col], errors="coerce").fillna(float(data_df[col].median()))
            continuous_features.append(col)
        else:
            data_df[col] = data_df[col].astype("string").fillna("MISSING")
            categorical_features.append(col)

    return data_df, continuous_features, categorical_features


def _runtime_cache_key(
    *,
    model,
    calibrator,
    train_df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
) -> tuple:
    return (
        id(model),
        id(calibrator),
        id(train_df),
        tuple(feature_cols),
        str(target_col),
    )


def _get_or_build_runtime(
    *,
    dice_ml,
    model,
    calibrator,
    train_df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
) -> _DiceRuntime:
    key = _runtime_cache_key(
        model=model,
        calibrator=calibrator,
        train_df=train_df,
        feature_cols=feature_cols,
        target_col=target_col,
    )
    with _DICE_CACHE_LOCK:
        cached = _DICE_RUNTIME_CACHE.get(key)
    if cached is not None:
        return cached

    data_df, continuous_features, categorical_features = _prepare_dice_dataframe(train_df, feature_cols, target_col)
    data_obj = dice_ml.Data(
        dataframe=data_df,
        continuous_features=continuous_features,
        outcome_name=target_col,
    )
    model_obj = dice_ml.Model(
        model=_ModelProxy(model, calibrator, feature_cols),
        backend="sklearn",
        model_type="classifier",
    )
    runtime = _DiceRuntime(
        data_obj=data_obj,
        model_obj=model_obj,
        continuous_features=continuous_features,
        categorical_features=categorical_features,
    )
    with _DICE_CACHE_LOCK:
        _DICE_RUNTIME_CACHE[key] = runtime
    return runtime


def _extract_action_sets(
    *,
    query: pd.DataFrame,
    cf_df: pd.DataFrame,
    actionable_features: list[str],
    max_actions: int,
) -> list[list[dict]]:
    base = query.iloc[0]
    action_sets: list[list[dict]] = []
    for _, cf_row in cf_df.iterrows():
        actions = []
        for feat in actionable_features:
            if feat not in cf_row.index:
                continue
            try:
                dice_meta = get_dice_generation_metadata(feat)
            except Exception:
                continue
            if not bool(dice_meta["dice_generatable"]):
                continue
            current = float(base[feat])
            target = normalize_dice_target_value(
                feat,
                current_value=current,
                target_value=float(cf_row[feat]),
            )
            if abs(target - current) < 1e-9:
                continue
            actions.append(
                {
                    "feature_name": feat,
                    "current_value": current,
                    "target_value": target,
                }
            )
            if len(actions) >= max_actions:
                break
        if actions:
            action_sets.append(actions)
    return action_sets


def _invoke_with_timeout(
    fn,
    *,
    kwargs: dict,
    timeout_s: float | None,
):
    if timeout_s is None or timeout_s <= 0:
        return fn(**kwargs), False

    result_holder: dict[str, object] = {}
    error_holder: dict[str, Exception] = {}
    done = threading.Event()

    def _runner() -> None:
        try:
            result_holder["value"] = fn(**kwargs)
        except Exception as exc:
            error_holder["error"] = exc
        finally:
            done.set()

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    finished = done.wait(timeout=float(timeout_s))
    if not finished:
        return None, True
    if "error" in error_holder:
        raise error_holder["error"]
    return result_holder.get("value"), False


def generate_dice_counterfactual_actions(
    row: pd.Series,
    feature_cols: list[str],
    actionable_features: list[str],
    model,
    calibrator,
    train_df: pd.DataFrame,
    target_col: str,
    total_cfs: int = 3,
    random_seed: int = 42,
    dice_method: str = "random",
    max_actions: int = 4,
    enable_method_fallback: bool = True,
    timeout_ms: int = 0,
    stopping_threshold: float | None = None,
) -> tuple[list[list[dict]], str, dict]:
    query = pd.DataFrame([row[feature_cols].to_dict()])
    requested_method = str(dice_method).strip().lower() or "random"
    used_method = _normalize_dice_method(requested_method)
    if requested_method not in _ALLOWED_DICE_METHOD_SET:
        return _fallback_response(
            row=row,
            actionable_features=actionable_features,
            reason="invalid_method",
            method_requested=requested_method,
            method_used=used_method,
            max_actions=max_actions,
        )

    if target_col not in train_df.columns:
        return _fallback_response(
            row=row,
            actionable_features=actionable_features,
            reason="missing_target_col",
            method_requested=requested_method,
            method_used=used_method,
            max_actions=max_actions,
        )

    safe_actionable = [f for f in actionable_features if f in feature_cols]
    if not safe_actionable:
        return _fallback_response(
            row=row,
            actionable_features=feature_cols,
            reason="no_actionable_features",
            method_requested=requested_method,
            method_used=used_method,
            max_actions=max_actions,
        )

    try:
        import dice_ml

        runtime = _get_or_build_runtime(
            dice_ml=dice_ml,
            model=model,
            calibrator=calibrator,
            train_df=train_df,
            feature_cols=feature_cols,
            target_col=target_col,
        )
        data_df = train_df[feature_cols + [target_col]]
        continuous_features = runtime.continuous_features
        categorical_features = runtime.categorical_features
        query_df = query.copy()
        for col in continuous_features:
            query_df[col] = pd.to_numeric(query_df[col], errors="coerce").fillna(float(data_df[col].median()))
        for col in categorical_features:
            query_df[col] = query_df[col].astype("string").fillna("MISSING")
        method_attempts: list[dict] = []
        last_exception: Exception | None = None
        last_non_error_reason: str | None = None
        start_ts = time.perf_counter()
        timeout_ms = int(timeout_ms or 0)
        methods_to_try = _method_attempt_order(
            used_method,
            enable_method_fallback=bool(enable_method_fallback),
        )
        for method in methods_to_try:
            try:
                remaining_timeout_s = None
                if timeout_ms > 0:
                    elapsed_ms = float((time.perf_counter() - start_ts) * 1000.0)
                    remaining_ms = float(timeout_ms) - elapsed_ms
                    if remaining_ms <= 0:
                        last_non_error_reason = "timeout"
                        method_attempts.append({"method": method, "status": "timeout"})
                        break
                    remaining_timeout_s = max(0.001, remaining_ms / 1000.0)
                with _DICE_CACHE_LOCK:
                    exp = runtime.explainers.get(method)
                if exp is None:
                    exp = dice_ml.Dice(runtime.data_obj, runtime.model_obj, method=method)
                    with _DICE_CACHE_LOCK:
                        runtime.explainers[method] = exp
                kwargs = _build_generate_kwargs(
                    exp.generate_counterfactuals,
                    query_df=query_df,
                    total_cfs=total_cfs,
                    safe_actionable=safe_actionable,
                    random_seed=random_seed,
                    stopping_threshold=stopping_threshold,
                )
                cfs, did_timeout = _invoke_with_timeout(
                    exp.generate_counterfactuals,
                    kwargs=kwargs,
                    timeout_s=remaining_timeout_s,
                )
                if did_timeout:
                    last_non_error_reason = "timeout"
                    method_attempts.append({"method": method, "status": "timeout"})
                    continue
                cf_df = cfs.cf_examples_list[0].final_cfs_df
                if cf_df is None or cf_df.empty:
                    last_non_error_reason = "empty_dice"
                    method_attempts.append({"method": method, "status": "empty"})
                    continue

                action_sets = _extract_action_sets(
                    query=query_df,
                    cf_df=cf_df,
                    actionable_features=safe_actionable,
                    max_actions=max_actions,
                )
                if not action_sets:
                    last_non_error_reason = "no_action"
                    method_attempts.append({"method": method, "status": "no_action"})
                    continue

                method_attempts.append({"method": method, "status": "success"})
                changed = sorted({a["feature_name"] for actions in action_sets for a in actions})
                telemetry = {
                    "method_requested": requested_method,
                    "method_used": method,
                    "fallback_reason": None,
                    "exception_type": None,
                    "exception_message": None,
                    "action_set_count": len(action_sets),
                    "changed_features_union": changed,
                    "changed_feature_union_count": len(changed),
                    "continuous_feature_count": len(continuous_features),
                    "categorical_feature_count": len(categorical_features),
                    "features_to_vary_count": len(safe_actionable),
                    "attempted_method_count": len(method_attempts),
                    "attempted_methods": [a.get("method") for a in method_attempts],
                    "method_attempts": method_attempts,
                    "timeout_ms": timeout_ms,
                }
                return action_sets, "dice", telemetry
            except Exception as exc:
                last_exception = exc
                method_attempts.append(
                    {
                        "method": method,
                        "status": "error",
                        "exception_type": exc.__class__.__name__,
                    }
                )

        fallback_reason = last_non_error_reason or "error"
        last_method = methods_to_try[-1] if methods_to_try else used_method
        return _fallback_response(
            row=row,
            actionable_features=safe_actionable,
            reason=fallback_reason,
            method_requested=requested_method,
            method_used=last_method,
            max_actions=max_actions,
            exception_type=last_exception.__class__.__name__ if last_exception else None,
            exception_message=str(last_exception) if last_exception else None,
            method_attempts=method_attempts,
        )
    except Exception as exc:
        return _fallback_response(
            row=row,
            actionable_features=safe_actionable,
            reason="error",
            method_requested=requested_method,
            method_used=used_method,
            max_actions=max_actions,
            exception_type=exc.__class__.__name__,
            exception_message=str(exc),
        )


def generate_dice_like_baseline(
    row: pd.Series,
    feature_cols: list[str],
    actionable_features: list[str],
    max_actions: int = 2,
) -> list[dict]:
    # Backward-compatible helper; returns only one baseline action set.
    return _heuristic_actions(row, actionable_features, max_actions=max_actions)
