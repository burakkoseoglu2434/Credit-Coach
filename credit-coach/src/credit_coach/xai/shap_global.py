from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _fallback_importance(model, x: pd.DataFrame) -> pd.DataFrame:
    if hasattr(model, "feature_importances_"):
        values = np.asarray(model.feature_importances_)
    elif hasattr(model, "coef_"):
        values = np.abs(np.asarray(model.coef_).reshape(-1))
    else:
        values = np.std(x.values, axis=0)

    imp = pd.DataFrame({"feature": x.columns, "importance": values})
    return imp.sort_values("importance", ascending=False).reset_index(drop=True)


def compute_global_importance(model, x: pd.DataFrame, max_samples: int = 2000) -> pd.DataFrame:
    sample = x.sample(n=min(len(x), max_samples), random_state=42) if len(x) > max_samples else x

    try:
        import shap

        explainer = shap.Explainer(model, sample)
        shap_values = explainer(sample)
        vals = np.abs(shap_values.values)
        if vals.ndim == 3:
            vals = vals[:, :, 1]
        mean_abs = vals.mean(axis=0)
        imp = pd.DataFrame({"feature": sample.columns, "importance": mean_abs})
        return imp.sort_values("importance", ascending=False).reset_index(drop=True)
    except Exception:
        return _fallback_importance(model, sample)


def _rank_alignment_score(base_rank: list[str], other_rank: list[str], top_n: int = 10) -> float:
    if top_n <= 0:
        return 1.0
    base_top = base_rank[:top_n]
    other_top = other_rank[:top_n]
    inter = len(set(base_top).intersection(other_top))
    return float(inter / max(1, top_n))


def compute_global_importance_stability(
    model,
    x: pd.DataFrame,
    *,
    max_samples: int = 2000,
    bootstrap_rounds: int = 5,
    random_state: int = 42,
    top_n: int = 10,
) -> dict:
    """
    Global importance + bootstrap stability metadata.
    """
    base = compute_global_importance(model, x, max_samples=max_samples)
    base_rank = base["feature"].tolist()
    base_map = {row.feature: float(row.importance) for row in base.itertuples(index=False)}

    rng = np.random.default_rng(random_state)
    align_scores: list[float] = []
    drift_scores: list[float] = []

    rounds = max(0, int(bootstrap_rounds))
    n = len(x)
    if rounds > 0 and n > 1:
        denom = float(np.mean(np.abs(list(base_map.values()))) + 1e-9)
        for _ in range(rounds):
            idx = rng.integers(0, n, size=n)
            sampled = x.iloc[idx].reset_index(drop=True)
            imp = compute_global_importance(model, sampled, max_samples=max_samples)
            rank = imp["feature"].tolist()
            align_scores.append(_rank_alignment_score(base_rank, rank, top_n=top_n))

            current_map = {row.feature: float(row.importance) for row in imp.itertuples(index=False)}
            diffs = [abs(base_map.get(f, 0.0) - current_map.get(f, 0.0)) for f in base_rank]
            drift_scores.append(float(np.mean(diffs) / denom))

    stability = float(np.mean(align_scores)) if align_scores else 1.0
    baseline_drift = float(np.mean(drift_scores)) if drift_scores else 0.0
    confidence = float(np.clip(1.0 - (0.5 * baseline_drift) - (0.5 * (1.0 - stability)), 0.0, 1.0))

    return {
        "importance": base,
        "meta": {
            "stability_score": stability,
            "baseline_drift_l1": baseline_drift,
            "explainability_confidence": confidence,
            "bootstrap_rounds": rounds,
            "top_n_alignment": int(top_n),
        },
    }


def save_global_importance_plot(importance_df: pd.DataFrame, out_dir: str | Path, top_n: int = 20) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    top = importance_df.head(top_n).iloc[::-1]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top["feature"], top["importance"])
    ax.set_title("Global Feature Importance")
    ax.set_xlabel("Importance")
    fig.tight_layout()

    out_path = out / "shap_global_top20.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path

