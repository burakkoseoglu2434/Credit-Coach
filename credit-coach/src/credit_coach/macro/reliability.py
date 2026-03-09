from __future__ import annotations

import math
from typing import Any

from credit_coach.macro.shock_scenarios import scenario_pd_shift


def _scenario_severity(scenario: dict) -> float:
    changes = scenario.get("changes", {})
    sev = 0.0
    sev += abs(float(changes.get("interest_rate", 0.0))) / 10.0
    sev += abs(float(changes.get("unemployment_rate", 0.0))) / 10.0
    sev += abs(float(changes.get("inflation_rate", 0.0))) / 20.0
    sev += abs(float(changes.get("credit_spread", 0.0))) / 10.0
    sev += abs(float(changes.get("gdp_growth", 0.0))) / 10.0
    return float(max(0.0, min(1.0, sev)))


def _stressed_tau(tau: float, scenario: dict, threshold_shift_per_msi_unit: float) -> float:
    severity = _scenario_severity(scenario)
    shifted = float(tau + (threshold_shift_per_msi_unit * severity))
    return float(max(0.01, min(0.99, shifted)))


def scenario_severity(scenario: dict) -> float:
    return _scenario_severity(scenario)


def stressed_tau_for_scenario(
    tau: float,
    scenario: dict,
    threshold_shift_per_msi_unit: float,
) -> float:
    return _stressed_tau(tau, scenario, threshold_shift_per_msi_unit)


def _tail_mean(values: list[float], tail_quantile: float) -> float:
    if not values:
        return 0.0
    q = float(max(0.5, min(0.999, tail_quantile)))
    ordered = sorted(float(v) for v in values)
    start = int(math.floor(q * (len(ordered) - 1)))
    tail = ordered[start:]
    return float(sum(tail) / max(1, len(tail)))


def _sigmoid(x: float) -> float:
    z = max(-60.0, min(60.0, float(x)))
    return float(1.0 / (1.0 + math.exp(-z)))


def _soft_pass_from_margin(margin: float, scale: float) -> float:
    safe_scale = max(1e-6, float(scale))
    return _sigmoid(float(margin) / safe_scale)


def compute_effective_reliability(
    reliability_report: dict[str, float],
    *,
    mode: str = "hard",
    soft_weight: float = 0.5,
) -> float:
    mode_s = str(mode or "hard").strip().lower() or "hard"
    hard = float(reliability_report.get("reliability_hard", reliability_report.get("reliability", 0.0)))
    soft = float(reliability_report.get("reliability_soft", hard))
    w = min(1.0, max(0.0, float(soft_weight)))
    if mode_s == "soft":
        return float(soft)
    if mode_s == "blend":
        return float(((1.0 - w) * hard) + (w * soft))
    return float(hard)


def resolve_reliability_settings(
    *,
    uncertainty_cfg: dict[str, Any] | None,
    segment_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = uncertainty_cfg if isinstance(uncertainty_cfg, dict) else {}
    risk_band = str((segment_context or {}).get("risk_band", "")).strip().lower()
    denied_mode = bool((segment_context or {}).get("denied_mode", False))

    mode = str(cfg.get("reliability_gate_mode", "hard")).strip().lower() or "hard"
    soft_weight = min(1.0, max(0.0, float(cfg.get("reliability_soft_weight", 0.5))))
    soft_scale = max(1e-6, float(cfg.get("reliability_soft_scale", 0.02)))
    min_reliability_override = None

    profiles = cfg.get("reliability_profiles", {}) if isinstance(cfg.get("reliability_profiles", {}), dict) else {}

    def _apply_profile(raw: dict[str, Any]) -> None:
        nonlocal mode, soft_weight, soft_scale, min_reliability_override
        if not isinstance(raw, dict):
            return
        if "mode" in raw:
            mode = str(raw.get("mode", mode)).strip().lower() or mode
        if "soft_weight" in raw:
            soft_weight = min(1.0, max(0.0, float(raw.get("soft_weight", soft_weight))))
        if "soft_scale" in raw:
            soft_scale = max(1e-6, float(raw.get("soft_scale", soft_scale)))
        if "min_reliability" in raw and raw.get("min_reliability") is not None:
            min_reliability_override = float(raw.get("min_reliability"))

    _apply_profile(profiles.get("default", {}))
    if denied_mode:
        _apply_profile(profiles.get("denied", {}))
    if risk_band:
        _apply_profile(profiles.get(risk_band, {}))
    return {
        "mode": mode,
        "soft_weight": float(soft_weight),
        "soft_scale": float(soft_scale),
        "min_reliability_override": min_reliability_override,
    }


def evaluate_reliability_from_pd(
    base_pd: float,
    tau: float,
    scenarios: list[dict],
    threshold_shift_per_msi_unit: float = 0.0,
    cvar_quantile: float = 0.9,
    reliability_soft_scale: float = 0.02,
) -> dict[str, float]:
    if not scenarios:
        margin = float(tau - base_pd)
        reliability_hard = float(base_pd <= tau)
        reliability_soft = _soft_pass_from_margin(margin, reliability_soft_scale)
        return {
            "reliability": reliability_hard,
            "reliability_hard": reliability_hard,
            "reliability_soft": reliability_soft,
            "worst_risk_margin": margin,
            "avg_stressed_pd": float(base_pd),
            "worst_stressed_pd": float(base_pd),
            "cvar_stressed_pd": float(base_pd),
            "avg_stressed_tau": float(tau),
            "robust_margin_worst": margin,
            "robust_margin_cvar": float(tau - base_pd),
        }

    stressed_pds: list[float] = []
    stressed_taus: list[float] = []
    margins: list[float] = []
    soft_passes: list[float] = []
    passes = 0

    for s in scenarios:
        stressed_pd = min(1.0, base_pd + scenario_pd_shift(s))
        tau_s = _stressed_tau(tau, s, threshold_shift_per_msi_unit)
        margin = float(tau_s - stressed_pd)
        stressed_pds.append(float(stressed_pd))
        stressed_taus.append(float(tau_s))
        margins.append(margin)
        soft_passes.append(_soft_pass_from_margin(margin, reliability_soft_scale))
        if stressed_pd <= tau_s:
            passes += 1

    worst_pd = float(max(stressed_pds))
    cvar_pd = _tail_mean(stressed_pds, tail_quantile=cvar_quantile)
    avg_tau = float(sum(stressed_taus) / len(stressed_taus))
    reliability_hard = float(passes / len(scenarios))
    reliability_soft = float(sum(soft_passes) / max(1, len(soft_passes)))

    return {
        "reliability": reliability_hard,
        "reliability_hard": reliability_hard,
        "reliability_soft": reliability_soft,
        "worst_risk_margin": float(min(margins)),
        "avg_stressed_pd": float(sum(stressed_pds) / len(stressed_pds)),
        "worst_stressed_pd": worst_pd,
        "cvar_stressed_pd": float(cvar_pd),
        "avg_stressed_tau": avg_tau,
        "robust_margin_worst": float(avg_tau - worst_pd),
        "robust_margin_cvar": float(avg_tau - cvar_pd),
    }


def compute_reliability_from_pd(
    base_pd: float,
    tau: float,
    scenarios: list[dict],
    threshold_shift_per_msi_unit: float = 0.0,
) -> float:
    out = evaluate_reliability_from_pd(
        base_pd=base_pd,
        tau=tau,
        scenarios=scenarios,
        threshold_shift_per_msi_unit=threshold_shift_per_msi_unit,
    )
    return float(out["reliability"])


def compute_robust_anchor_pd(
    reliability_report: dict[str, float],
    objective: str = "cvar",
) -> float:
    obj = str(objective).strip().lower()
    if obj == "worst_case":
        return float(reliability_report.get("worst_stressed_pd", 1.0))
    return float(reliability_report.get("cvar_stressed_pd", reliability_report.get("worst_stressed_pd", 1.0)))
