from __future__ import annotations

from credit_coach.data.schema import PlanRecord
from credit_coach.macro.reliability import (
    compute_effective_reliability,
    compute_robust_anchor_pd,
    evaluate_reliability_from_pd,
    resolve_reliability_settings,
)
from credit_coach.safety.feasibility import check_actions_feasible
from credit_coach.safety.statistical import estimate_prediction_ci


def _with_reason(base: str, extra: str | None) -> str:
    if not extra:
        return base
    return f"{base}; {extra}"


def validate_plan(
    plan: PlanRecord,
    tau: float,
    alpha: float,
    bootstrap_b: int = 500,
    *,
    scenarios: list[dict] | None = None,
    threshold_shift_per_msi_unit: float = 0.0,
    robust_objective: str = "cvar",
    robust_cvar_quantile: float = 0.9,
    min_reliability: float | None = None,
    min_worst_risk_margin: float | None = None,
    uncertainty_cfg: dict | None = None,
    segment_context: dict | None = None,
) -> PlanRecord:
    actions = [a.model_dump() for a in plan.actions]
    feasible, reason = check_actions_feasible(actions)
    if not feasible:
        plan.status = "REJECTED"
        plan.status_reason = reason
        return plan

    base_pd = float(plan.predicted_pd if plan.predicted_pd is not None else 1.0)
    uncertainty_cfg = uncertainty_cfg or {}
    method = str(uncertainty_cfg.get("primary_method", "bootstrap")).strip().lower() or "bootstrap"
    sigma = float(uncertainty_cfg.get("bootstrap_sigma", 0.03))
    random_state = int(uncertainty_cfg.get("random_state", 42))
    rel_settings = resolve_reliability_settings(
        uncertainty_cfg=uncertainty_cfg,
        segment_context=segment_context,
    )
    reliability_gate_mode = str(rel_settings.get("mode", "hard"))
    reliability_soft_weight = float(rel_settings.get("soft_weight", 0.5))
    reliability_soft_scale = float(rel_settings.get("soft_scale", 0.02))
    min_rel_override = rel_settings.get("min_reliability_override")
    conformal_cfg = uncertainty_cfg.get("conformal", {}) if isinstance(uncertainty_cfg.get("conformal", {}), dict) else {}
    conformal_residual_quantile = float(conformal_cfg.get("residual_quantile", 0.06))
    conformal_min_width = float(conformal_cfg.get("min_width", 0.005))
    conformal_calibration_path = conformal_cfg.get("calibration_artifact_path")
    conformal_adaptive_by_score = bool(conformal_cfg.get("adaptive_by_score", False))
    conformal_adaptive_mode = str(conformal_cfg.get("adaptive_mode", "cap"))
    conformal_adaptive_blend = float(conformal_cfg.get("adaptive_blend", 1.0))
    conformal_adaptive_gap_weight = float(conformal_cfg.get("adaptive_gap_weight", 0.0))
    conformal_max_width_raw = conformal_cfg.get("max_width")
    conformal_max_width = float(conformal_max_width_raw) if conformal_max_width_raw is not None else None
    profile_cfg = uncertainty_cfg.get("profiles", {}) if isinstance(uncertainty_cfg.get("profiles", {}), dict) else {}
    risk_band = str((segment_context or {}).get("risk_band", "")).strip() or None
    denied_mode = bool((segment_context or {}).get("denied_mode", False))

    if method == "hybrid":
        ci_low_b, ci_high_b = estimate_prediction_ci(
            base_pd=base_pd,
            b=bootstrap_b,
            alpha=alpha,
            random_state=random_state,
            sigma=sigma,
            method="bootstrap",
            conformal_residual_quantile=conformal_residual_quantile,
            conformal_min_width=conformal_min_width,
            conformal_calibration_path=conformal_calibration_path,
            conformal_adaptive_by_score=conformal_adaptive_by_score,
            conformal_adaptive_mode=conformal_adaptive_mode,
            conformal_adaptive_blend=conformal_adaptive_blend,
            conformal_adaptive_gap_weight=conformal_adaptive_gap_weight,
            conformal_max_width=conformal_max_width,
            risk_band=risk_band,
            denied_mode=denied_mode,
            uncertainty_profiles=profile_cfg,
        )
        ci_low_c, ci_high_c = estimate_prediction_ci(
            base_pd=base_pd,
            b=bootstrap_b,
            alpha=alpha,
            random_state=random_state,
            sigma=sigma,
            method="conformal",
            conformal_residual_quantile=conformal_residual_quantile,
            conformal_min_width=conformal_min_width,
            conformal_calibration_path=conformal_calibration_path,
            conformal_adaptive_by_score=conformal_adaptive_by_score,
            conformal_adaptive_mode=conformal_adaptive_mode,
            conformal_adaptive_blend=conformal_adaptive_blend,
            conformal_adaptive_gap_weight=conformal_adaptive_gap_weight,
            conformal_max_width=conformal_max_width,
            risk_band=risk_band,
            denied_mode=denied_mode,
            uncertainty_profiles=profile_cfg,
        )
        ci_low = float(min(ci_low_b, ci_low_c))
        ci_high = float(max(ci_high_b, ci_high_c))
    else:
        ci_low, ci_high = estimate_prediction_ci(
            base_pd=base_pd,
            b=bootstrap_b,
            alpha=alpha,
            random_state=random_state,
            sigma=sigma,
            method=method,
            conformal_residual_quantile=conformal_residual_quantile,
            conformal_min_width=conformal_min_width,
            conformal_calibration_path=conformal_calibration_path,
            conformal_adaptive_by_score=conformal_adaptive_by_score,
            conformal_adaptive_mode=conformal_adaptive_mode,
            conformal_adaptive_blend=conformal_adaptive_blend,
            conformal_adaptive_gap_weight=conformal_adaptive_gap_weight,
            conformal_max_width=conformal_max_width,
            risk_band=risk_band,
            denied_mode=denied_mode,
            uncertainty_profiles=profile_cfg,
        )
    plan.ci_low = ci_low
    plan.ci_high = ci_high
    plan.alpha_used = alpha
    plan.risk_margin = float(tau - ci_high)

    rel_report = evaluate_reliability_from_pd(
        base_pd=base_pd,
        tau=tau,
        scenarios=scenarios or [],
        threshold_shift_per_msi_unit=threshold_shift_per_msi_unit,
        cvar_quantile=robust_cvar_quantile,
        reliability_soft_scale=reliability_soft_scale,
    )
    reliability_hard = float(rel_report.get("reliability_hard", rel_report.get("reliability", 0.0)))
    reliability_soft = float(rel_report.get("reliability_soft", reliability_hard))
    reliability_effective = compute_effective_reliability(
        rel_report,
        mode=reliability_gate_mode,
        soft_weight=reliability_soft_weight,
    )
    plan.reliability = float(reliability_effective)
    plan.robust_worst_risk_margin = float(rel_report.get("worst_risk_margin", 0.0))
    plan.robust_method = robust_objective
    plan.robust_anchor_pd = compute_robust_anchor_pd(rel_report, objective=robust_objective)
    plan.robust_margin = float(tau - float(plan.robust_anchor_pd))
    if plan.robust_score is None:
        # Fallback: robust score mevcut degilse nominal score korunur.
        plan.robust_score = float(plan.score if plan.score is not None else 0.0)

    if ci_high <= tau:
        status = "APPROVED"
        reason_txt = f"CI upper bound below decision threshold ({method})"
    else:
        status = "NEEDS_REVIEW"
        reason_txt = f"CI upper bound exceeds threshold ({method})"

    min_reliability_effective = min_reliability
    if min_rel_override is not None:
        min_reliability_effective = (
            float(min_rel_override)
            if min_reliability_effective is None
            else float(min(min_reliability_effective, float(min_rel_override)))
        )

    if min_reliability_effective is not None and float(plan.reliability) < float(min_reliability_effective):
        if reliability_gate_mode in {"soft", "blend"}:
            rel_detail = (
                f"reliability(mode={reliability_gate_mode}) {plan.reliability:.4f} "
                f"[hard={reliability_hard:.4f}, soft={reliability_soft:.4f}]"
            )
        else:
            rel_detail = f"reliability {plan.reliability:.4f}"
        status = "NEEDS_REVIEW"
        reason_txt = _with_reason(
            reason_txt,
            f"{rel_detail} below min {float(min_reliability_effective):.4f}",
        )

    if min_worst_risk_margin is not None and float(plan.robust_worst_risk_margin) < float(min_worst_risk_margin):
        status = "NEEDS_REVIEW"
        reason_txt = _with_reason(
            reason_txt,
            (
                f"worst_risk_margin {float(plan.robust_worst_risk_margin):.4f} below "
                f"min {float(min_worst_risk_margin):.4f}"
            ),
        )

    plan.status = status
    plan.status_reason = reason_txt
    return plan
