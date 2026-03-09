from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from statistics import NormalDist

import numpy as np


def bootstrap_prediction_ci(
    base_pd: float,
    b: int = 500,
    alpha: float = 0.05,
    random_state: int = 42,
    sigma: float = 0.03,
) -> tuple[float, float]:
    rng = np.random.default_rng(random_state)
    draws = rng.normal(loc=base_pd, scale=sigma, size=b)
    draws = np.clip(draws, 0.0, 1.0)
    low = float(np.quantile(draws, alpha / 2))
    high = float(np.quantile(draws, 1.0 - alpha / 2))
    return low, high


def conformal_prediction_ci(
    base_pd: float,
    *,
    alpha: float = 0.05,
    conformal_residual_quantile: float = 0.06,
    conformal_min_width: float = 0.005,
    calibration_artifact_path: str | None = None,
    adaptive_by_score: bool = False,
    adaptive_mode: str = "cap",
    adaptive_blend: float = 1.0,
    adaptive_gap_weight: float = 0.0,
    conformal_max_width: float | None = None,
    width_multiplier: float = 1.0,
) -> tuple[float, float]:
    # Split-conformal style symmetric band, optionally driven by calibration artifact.
    a = float(max(1e-6, min(0.49, alpha)))
    width = float(conformal_residual_quantile)
    if calibration_artifact_path:
        width = _lookup_conformal_width(calibration_artifact_path, alpha=a, fallback=width)

    if adaptive_by_score and calibration_artifact_path:
        local_width, local_gap = _lookup_score_band_width(
            calibration_artifact_path,
            alpha=a,
            base_pd=float(base_pd),
        )
        if local_width is not None:
            mode = str(adaptive_mode).strip().lower() or "cap"
            if mode == "replace":
                width = float(local_width)
            elif mode == "blend":
                blend = float(max(0.0, min(1.0, adaptive_blend)))
                width = float((1.0 - blend) * float(width) + blend * float(local_width))
            else:
                # cap mode: never exceed the base conformal width.
                width = float(min(float(width), float(local_width)))
        if local_gap is not None and float(adaptive_gap_weight) > 0.0:
            width = float(width + (float(adaptive_gap_weight) * float(local_gap)))

    width = float(width) * max(0.0, float(width_multiplier))
    min_width = float(conformal_min_width) * max(0.0, float(width_multiplier))
    width = max(min_width, width)
    if conformal_max_width is not None:
        width = min(width, max(0.0, float(conformal_max_width)))
    low = float(max(0.0, min(1.0, base_pd - width)))
    high = float(max(0.0, min(1.0, base_pd + width)))
    return low, high


def estimate_prediction_ci(
    base_pd: float,
    *,
    b: int = 500,
    alpha: float = 0.05,
    random_state: int = 42,
    sigma: float = 0.03,
    method: str = "bootstrap",
    conformal_residual_quantile: float = 0.06,
    conformal_min_width: float = 0.005,
    conformal_calibration_path: str | None = None,
    conformal_adaptive_by_score: bool = False,
    conformal_adaptive_mode: str = "cap",
    conformal_adaptive_blend: float = 1.0,
    conformal_adaptive_gap_weight: float = 0.0,
    conformal_max_width: float | None = None,
    risk_band: str | None = None,
    denied_mode: bool = False,
    uncertainty_profiles: dict | None = None,
) -> tuple[float, float]:
    profile_cfg = uncertainty_profiles if isinstance(uncertainty_profiles, dict) else {}
    band_cfg = profile_cfg.get(str(risk_band), {}) if risk_band is not None else {}
    if not isinstance(band_cfg, dict):
        band_cfg = {}
    width_multiplier = float(band_cfg.get("width_multiplier", 1.0))
    sigma_multiplier = float(band_cfg.get("sigma_multiplier", 1.0))
    alpha_multiplier = float(band_cfg.get("alpha_multiplier", 1.0))
    if bool(denied_mode):
        width_multiplier *= float(profile_cfg.get("denied_width_multiplier", 1.0))
        sigma_multiplier *= float(profile_cfg.get("denied_sigma_multiplier", 1.0))
        alpha_multiplier *= float(profile_cfg.get("denied_alpha_multiplier", 1.0))
    width_multiplier = max(0.1, width_multiplier)
    sigma_multiplier = max(0.1, sigma_multiplier)
    effective_alpha = float(max(1e-6, min(0.49, float(alpha) * alpha_multiplier)))
    effective_sigma = float(max(1e-6, float(sigma) * sigma_multiplier))

    m = str(method).strip().lower()
    if m in {"conformal", "conformal_adaptive"}:
        adaptive_enabled = bool(conformal_adaptive_by_score or (m == "conformal_adaptive"))
        return conformal_prediction_ci(
            base_pd=base_pd,
            alpha=effective_alpha,
            conformal_residual_quantile=float(conformal_residual_quantile) * width_multiplier,
            conformal_min_width=float(conformal_min_width) * width_multiplier,
            calibration_artifact_path=conformal_calibration_path,
            adaptive_by_score=adaptive_enabled,
            adaptive_mode=conformal_adaptive_mode,
            adaptive_blend=conformal_adaptive_blend,
            adaptive_gap_weight=conformal_adaptive_gap_weight,
            conformal_max_width=conformal_max_width,
            width_multiplier=width_multiplier,
        )
    return bootstrap_prediction_ci(
        base_pd=base_pd,
        b=b,
        alpha=effective_alpha,
        random_state=random_state,
        sigma=effective_sigma,
    )


@lru_cache(maxsize=8)
def _load_conformal_calibration(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _lookup_conformal_width(path: str, *, alpha: float, fallback: float) -> float:
    payload = _load_conformal_calibration(path)
    if not payload:
        return float(fallback)
    qmap = payload.get("residual_quantiles", {})
    if not isinstance(qmap, dict) or not qmap:
        return float(fallback)

    target = float(max(1e-6, min(0.49, alpha)))
    chosen = None
    chosen_dist = float("inf")
    for k, v in qmap.items():
        try:
            a = float(k)
            width = float(v)
        except Exception:
            continue
        dist = abs(a - target)
        if dist < chosen_dist:
            chosen = width
            chosen_dist = dist
    if chosen is None:
        return float(fallback)
    return float(max(0.0, chosen))


def _lookup_score_band_width(path: str, *, alpha: float, base_pd: float) -> tuple[float | None, float | None]:
    payload = _load_conformal_calibration(path)
    if not payload:
        return None, None

    edges = payload.get("score_bin_edges")
    widths_map = payload.get("score_bin_widths")
    gaps = payload.get("score_bin_gaps", [])
    if not isinstance(edges, list) or len(edges) < 2:
        return None, None
    if not isinstance(widths_map, dict) or not widths_map:
        return None, None

    target = float(max(1e-6, min(0.49, alpha)))
    chosen_key: str | None = None
    chosen_dist = float("inf")
    for k in widths_map.keys():
        try:
            a = float(k)
        except Exception:
            continue
        dist = abs(a - target)
        if dist < chosen_dist:
            chosen_key = str(k)
            chosen_dist = dist

    if chosen_key is None:
        return None, None
    widths = widths_map.get(chosen_key)
    if not isinstance(widths, list) or not widths:
        return None, None

    try:
        edges_arr = np.asarray([float(v) for v in edges], dtype=float)
    except Exception:
        return None, None
    if edges_arr.ndim != 1 or len(edges_arr) < 2:
        return None, None

    # edges length is bin_count+1. np.searchsorted gives insertion index.
    idx = int(np.searchsorted(edges_arr, float(base_pd), side="right") - 1)
    idx = max(0, min(idx, len(widths) - 1))
    try:
        width = float(max(0.0, float(widths[idx])))
    except Exception:
        return None, None

    gap = None
    if isinstance(gaps, list) and len(gaps) > idx:
        try:
            gap = float(max(0.0, float(gaps[idx])))
        except Exception:
            gap = None
    return width, gap


def normal_two_sided_half_width(alpha: float, p_hat: float, n: int) -> float:
    # Normal approximation half width for Bernoulli mean uncertainty.
    a = float(max(1e-6, min(0.49, alpha)))
    z = float(NormalDist().inv_cdf(1.0 - (a / 2.0)))
    p = float(max(1e-6, min(1.0 - 1e-6, p_hat)))
    nn = int(max(1, n))
    se = float(np.sqrt((p * (1.0 - p)) / float(nn)))
    return float(max(0.0, z * se))
