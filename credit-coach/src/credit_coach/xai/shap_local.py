from __future__ import annotations

import numpy as np
import pandas as pd


def _fallback_local_contrib(model, x_row: pd.Series) -> np.ndarray:
    values = x_row.values.astype(float)
    if hasattr(model, "coef_"):
        coef = np.asarray(model.coef_).reshape(-1)
        if len(coef) == len(values):
            return coef * values
    return np.abs(values)


def _compute_local_contrib(
    model,
    row_df: pd.DataFrame,
    background_df: pd.DataFrame | None = None,
) -> tuple[np.ndarray, str]:
    try:
        import shap

        background = background_df if background_df is not None and len(background_df) > 0 else row_df
        explainer = shap.Explainer(model, background)
        shap_values = explainer(row_df)
        vals = np.asarray(shap_values.values)
        if vals.ndim == 3:
            vals = vals[:, :, 1]
        if vals.ndim == 2:
            vals = vals[0]
        return vals.astype(float), "shap"
    except Exception:
        return _fallback_local_contrib(model, row_df.iloc[0]), "fallback"


def _reasons_from_contrib(features: list[str], values: np.ndarray, contrib: np.ndarray, top_k: int) -> list[dict]:
    idx = np.argsort(np.abs(contrib))[::-1][:top_k]
    result = []
    for i in idx:
        c = float(contrib[i])
        result.append(
            {
                "feature": features[i],
                "value": float(values[i]),
                "contribution": c,
                "abs_contribution": float(abs(c)),
                "direction": "increase_risk" if c > 0 else "decrease_risk",
            }
        )
    return result


def compute_local_topk_reasons(
    model,
    x_row: pd.Series,
    top_k: int = 10,
    background_df: pd.DataFrame | None = None,
) -> list[dict]:
    features = list(x_row.index)
    row_df = pd.DataFrame([x_row.values], columns=features)
    values = row_df.iloc[0].astype(float).values
    contrib, _ = _compute_local_contrib(model, row_df, background_df=background_df)
    return _reasons_from_contrib(features, values, contrib, top_k)


def compute_local_reason_bundle(
    model,
    x_row: pd.Series,
    *,
    top_k: int = 10,
    perturbations: int = 6,
    noise_std: float = 0.01,
    random_state: int = 42,
    background_df: pd.DataFrame | None = None,
) -> dict:
    """
    Local explanation + stability metadata.

    Returns:
        {
          "reasons": [...],
          "meta": {
            "method": "shap"|"fallback",
            "stability_score": [0,1],
            "baseline_drift_l1": >=0,
            "explainability_confidence": [0,1],
            "perturbation_count": int
          }
        }
    """
    features = list(x_row.index)
    row_df = pd.DataFrame([x_row.values], columns=features)
    base_values = row_df.iloc[0].astype(float).values
    base_contrib, method = _compute_local_contrib(model, row_df, background_df=background_df)
    reasons = _reasons_from_contrib(features, base_values, base_contrib, top_k)
    base_top_set = {r["feature"] for r in reasons}

    rng = np.random.default_rng(random_state)
    jac_scores: list[float] = []
    drift_scores: list[float] = []
    num_pert = max(0, int(perturbations))

    if num_pert > 0:
        base_scale = np.maximum(np.abs(base_values), 1.0)
        denom = float(np.mean(np.abs(base_contrib)) + 1e-9)
        for _ in range(num_pert):
            noise = rng.normal(loc=0.0, scale=float(noise_std), size=len(base_values)) * base_scale
            perturbed_values = base_values + noise
            perturbed_df = pd.DataFrame([perturbed_values], columns=features)
            pert_contrib, _ = _compute_local_contrib(model, perturbed_df, background_df=background_df)
            pert_reasons = _reasons_from_contrib(features, perturbed_values, pert_contrib, top_k)
            pert_top_set = {r["feature"] for r in pert_reasons}

            inter = len(base_top_set.intersection(pert_top_set))
            union = max(1, len(base_top_set.union(pert_top_set)))
            jac_scores.append(float(inter / union))
            drift_scores.append(float(np.mean(np.abs(base_contrib - pert_contrib)) / denom))

    stability = float(np.mean(jac_scores)) if jac_scores else 1.0
    baseline_drift = float(np.mean(drift_scores)) if drift_scores else 0.0
    confidence = float(np.clip(1.0 - (0.5 * baseline_drift) - (0.5 * (1.0 - stability)), 0.0, 1.0))

    return {
        "reasons": reasons,
        "meta": {
            "method": method,
            "stability_score": stability,
            "baseline_drift_l1": baseline_drift,
            "explainability_confidence": confidence,
            "perturbation_count": num_pert,
        },
    }
