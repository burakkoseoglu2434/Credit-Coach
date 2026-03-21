from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import pandas as pd

from credit_coach.causality.action_constraints import causal_penalty
from credit_coach.causality.graph_utils import load_graph
from credit_coach.causality.rex_runner import run_rex_adapter
from credit_coach.coaching.messaging import (
    build_adverse_action_reasons,
    build_customer_roadmap_narrative,
)
from credit_coach.coaching.planner import choose_best_plan
from credit_coach.data.ingest import load_feature_contract
from credit_coach.data.schema import PlanAction, PlanRecord
from credit_coach.evaluation.fairness import build_group_advantage_penalties, lookup_group_penalty
from credit_coach.macro.impact import dynamic_alpha
from credit_coach.macro.sources import load_macro_snapshot_mock
from credit_coach.macro.stress_index import compute_macro_stress_index
from credit_coach.model.predict import predict_proba_pd
from credit_coach.model.registry import load_model_bundle
from credit_coach.recourse.action_space import (
    estimate_action_cost_usd,
    get_action_metadata,
    get_action_spec,
    get_actionable_features,
)
from credit_coach.recourse.action_constraints import enforce_action_constraints
from credit_coach.recourse.dice_baseline import generate_dice_counterfactual_actions
from credit_coach.recourse.execution_probability import annotate_plan_execution_probability
from credit_coach.recourse.feasibility import apply_target_feasibility_with_details
from credit_coach.recourse.generator import generate_nine_plans
from credit_coach.recourse.offer_optimization import annotate_offer_optimization, build_offer_contract
from credit_coach.recourse.trajectory import (
    attach_canonical_trajectory,
    build_canonical_phases,
    build_nominal_trajectory_checkpoints,
    phase_id_for_month,
    phase_title,
    predict_plan_pd_at_month,
)
from credit_coach.safety.validator import validate_plan
from credit_coach.storage.repository import build_decision_logging_summary, save_plan
from credit_coach.utils.run_context import create_run_context, load_config
from credit_coach.xai.shap_local import compute_local_reason_bundle

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_recourse")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate recourse plans")
    p.add_argument("--customer_id", type=str, default="demo")
    p.add_argument("--row_index", type=int, default=0)
    p.add_argument("--explain_only", action="store_true")
    p.add_argument("--base_config", type=str, default="configs/default.yaml")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--recourse_config", type=str, default="configs/recourse.yaml")
    p.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    p.add_argument("--safety_config", type=str, default="configs/safety.yaml")
    p.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    p.add_argument("--model_version", type=str, default="")
    p.add_argument("--model_manifest", type=str, default="")
    return p.parse_args()


def _merge_dict(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge_dict(out[k], v)
        else:
            out[k] = v
    return out


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)


def _safe_int(v, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


def _compute_income_edges(values: pd.Series, quantiles: list[float]) -> tuple[float, float, float]:
    s = pd.to_numeric(values, errors="coerce").dropna()
    if s.empty:
        return (0.0, 0.0, 0.0)
    q = [max(0.0, min(1.0, float(v))) for v in quantiles]
    if len(q) != 3:
        q = [0.25, 0.50, 0.75]
    q1, q2, q3 = [float(s.quantile(v)) for v in q]
    return (q1, q2, q3)


def _income_band_from_value(value: float, edges: tuple[float, float, float]) -> str:
    q1, q2, q3 = edges
    v = float(value)
    if v <= q1:
        return "q1"
    if v <= q2:
        return "q2"
    if v <= q3:
        return "q3"
    return "q4"


def _risk_band_from_pd(base_pd: float, tau: float, segment_caps_cfg: dict) -> str:
    risk_cfg = (
        segment_caps_cfg.get("risk_band_thresholds", {})
        if isinstance(segment_caps_cfg.get("risk_band_thresholds", {}), dict)
        else {}
    )
    near_upper = max(0.01, float(risk_cfg.get("near_upper", 0.10)))
    mid_upper = max(float(near_upper), float(risk_cfg.get("mid_upper", 0.25)))
    d = float(base_pd) - float(tau)
    if d <= near_upper:
        return "near"
    if d <= mid_upper:
        return "mid"
    return "high"


def _build_segment_context(
    *,
    row: pd.Series,
    base_pd: float,
    tau: float,
    denied_mode: bool,
    segment_caps_cfg: dict,
    income_edges: tuple[float, float, float],
) -> dict:
    annual_inc = _safe_float(row.get("annual_inc"), 0.0)
    income_band = _income_band_from_value(annual_inc, income_edges)
    risk_band = _risk_band_from_pd(base_pd, tau, segment_caps_cfg)

    enabled = bool(segment_caps_cfg.get("enabled", False))
    denied_only = bool(segment_caps_cfg.get("denied_only", True))
    can_apply = enabled and (not denied_only or denied_mode)

    income_mult_map = (
        segment_caps_cfg.get("income_band_multipliers", {})
        if isinstance(segment_caps_cfg.get("income_band_multipliers", {}), dict)
        else {}
    )
    risk_mult_map = (
        segment_caps_cfg.get("risk_band_multipliers", {})
        if isinstance(segment_caps_cfg.get("risk_band_multipliers", {}), dict)
        else {}
    )
    m_income = float(income_mult_map.get(income_band, 1.0))
    m_risk = float(risk_mult_map.get(risk_band, 1.0))
    m_total = float(m_income * m_risk)

    max_mult = max(1.0, float(segment_caps_cfg.get("cap_multiplier_max", 2.2)))
    min_mult = max(0.0, float(segment_caps_cfg.get("cap_multiplier_min", 1.0)))
    m_total = min(max_mult, max(min_mult, m_total))
    if not can_apply:
        m_total = 1.0
        m_income = 1.0
        m_risk = 1.0

    feature_mults: dict[str, float] = {}
    feature_cfg = (
        segment_caps_cfg.get("feature_cap_multipliers", {})
        if isinstance(segment_caps_cfg.get("feature_cap_multipliers", {}), dict)
        else {}
    )
    for feat, feat_rules in feature_cfg.items():
        if not isinstance(feat_rules, dict):
            continue
        inc_m = float(feat_rules.get("income_band_multipliers", {}).get(income_band, 1.0)) if isinstance(
            feat_rules.get("income_band_multipliers", {}), dict
        ) else 1.0
        risk_m = float(feat_rules.get("risk_band_multipliers", {}).get(risk_band, 1.0)) if isinstance(
            feat_rules.get("risk_band_multipliers", {}), dict
        ) else 1.0
        feature_mults[str(feat)] = float(max(0.0, inc_m * risk_m))

    return {
        "income_band": income_band,
        "risk_band": risk_band,
        "segment_caps_applied": bool(can_apply and abs(m_total - 1.0) > 1e-12),
        "cap_multiplier_income": float(m_income),
        "cap_multiplier_risk": float(m_risk),
        "cap_multiplier": float(m_total),
        "cap_multiplier_min": float(min_mult),
        "cap_multiplier_max": float(max_mult),
        "feature_cap_multipliers": feature_mults,
    }


def _is_denied_target(base_pd: float, tau: float, denied_cfg: dict) -> bool:
    if not bool(denied_cfg.get("enabled", False)):
        return False
    margin = float(denied_cfg.get("activation_margin", 0.0))
    return float(base_pd) > float(tau) + margin


def _effective_recourse_search(
    *,
    base_pd: float,
    tau: float,
    topk: int,
    horizons: list[int],
    strategies: list[str],
    robust_cfg: dict,
    dice_cfg: dict,
    rec_cfg: dict,
) -> tuple[dict, dict, dict]:
    denied_cfg = rec_cfg.get("denied_target", {}) if isinstance(rec_cfg.get("denied_target", {}), dict) else {}
    action_budget_cfg = rec_cfg.get("action_budget", {}) if isinstance(rec_cfg.get("action_budget", {}), dict) else {}
    search_budget_cfg = rec_cfg.get("search_budget", {}) if isinstance(rec_cfg.get("search_budget", {}), dict) else {}
    adaptive_cfg_raw = rec_cfg.get("adaptive_steps", {}) if isinstance(rec_cfg.get("adaptive_steps", {}), dict) else {}
    weekly_cfg_raw = rec_cfg.get("weekly_optimizer", {}) if isinstance(rec_cfg.get("weekly_optimizer", {}), dict) else {}
    adaptive_cfg = dict(adaptive_cfg_raw)
    weekly_cfg = dict(weekly_cfg_raw)
    if bool(adaptive_cfg.get("only_denied", False)):
        adaptive_cfg["enabled"] = False
    if bool(weekly_cfg.get("only_denied", True)):
        weekly_cfg["enabled"] = False
    action_budget_enabled = bool(action_budget_cfg.get("enabled", False))
    max_actions_regular = int(action_budget_cfg.get("max_actions_regular", topk))
    max_actions_denied = int(action_budget_cfg.get("max_actions_denied", max(max_actions_regular, topk)))
    effective = {
        "is_denied_target": False,
        "topk": int(topk),
        "horizons": list(horizons),
        "strategies": list(strategies),
        "search_cfg": {
            "adaptive_steps": adaptive_cfg,
            "weekly_optimizer": weekly_cfg,
            "denied_mode": False,
            "action_budget": {
                "enabled": action_budget_enabled,
                "max_actions": max_actions_regular,
            },
            "time_budget_ms": int(search_budget_cfg.get("per_customer_time_budget_ms", 0)),
            "candidate_pool_max_size": int(search_budget_cfg.get("candidate_pool_max_size", 0)),
            "skip_dice_when_internal_approved": bool(search_budget_cfg.get("skip_dice_when_internal_approved", False)),
            "skip_dice_for_non_denied": bool(search_budget_cfg.get("skip_dice_for_non_denied", False)),
        },
    }
    robust_eff = dict(robust_cfg or {})
    dice_eff = dict(dice_cfg or {})

    if not _is_denied_target(base_pd, tau, denied_cfg):
        return effective, robust_eff, dice_eff

    effective["is_denied_target"] = True
    effective["search_cfg"]["denied_mode"] = True
    if bool(adaptive_cfg_raw.get("only_denied", False)):
        denied_adaptive = dict(adaptive_cfg_raw)
        denied_adaptive["enabled"] = bool(adaptive_cfg_raw.get("enabled", True))
        effective["search_cfg"]["adaptive_steps"] = denied_adaptive
    if bool(weekly_cfg_raw.get("only_denied", True)):
        denied_weekly = dict(weekly_cfg_raw)
        denied_weekly["enabled"] = bool(weekly_cfg_raw.get("enabled", True))
        effective["search_cfg"]["weekly_optimizer"] = denied_weekly
    topk_multiplier = max(1.0, float(denied_cfg.get("topk_multiplier", 1.5)))
    min_topk = max(1, int(denied_cfg.get("min_topk", topk)))
    effective["topk"] = max(min_topk, int(round(topk * topk_multiplier)))

    denied_horizons = denied_cfg.get("horizons", horizons)
    if isinstance(denied_horizons, list) and denied_horizons:
        filtered = [int(h) for h in denied_horizons if int(h) in (3, 6, 12)]
        if filtered:
            effective["horizons"] = filtered

    denied_strategies = denied_cfg.get("strategies", strategies)
    if isinstance(denied_strategies, list) and denied_strategies:
        filtered_s = [str(s) for s in denied_strategies if str(s) in {"conservative", "balanced", "aggressive"}]
        if filtered_s:
            effective["strategies"] = filtered_s

    robust_eff["min_reliability"] = float(denied_cfg.get("strict_min_reliability", robust_eff.get("min_reliability", 0.7)))
    robust_eff["min_worst_risk_margin"] = float(
        denied_cfg.get("strict_min_worst_risk_margin", robust_eff.get("min_worst_risk_margin", -0.05))
    )

    dice_eff["total_cfs"] = int(
        max(
            1,
            round(
                int(dice_eff.get("total_cfs", 3))
                * max(1.0, float(denied_cfg.get("dice_total_cfs_multiplier", 1.5)))
            ),
        )
    )
    dice_eff["max_actions"] = int(
        max(
            1,
            round(
                int(dice_eff.get("max_actions", 4))
                * max(1.0, float(denied_cfg.get("dice_max_actions_multiplier", 1.5)))
            ),
        )
    )
    denied_max_actions = int(denied_cfg.get("max_actions", max_actions_denied))
    effective["search_cfg"]["action_budget"] = {
        "enabled": action_budget_enabled,
        "max_actions": denied_max_actions,
    }
    return effective, robust_eff, dice_eff


def _plan_cost(plan: PlanRecord) -> float:
    return float(sum(float(a.estimated_cost_usd) for a in plan.actions))


def _plan_proximity_l1(plan: PlanRecord) -> float:
    return float(sum(abs(float(a.delta)) for a in plan.actions))


def _phase_id_for_month(month: int) -> str:
    return phase_id_for_month(month)


def _phase_title(phase_id: str) -> str:
    return phase_title(phase_id)


def _decision_log_record(
    *,
    run_id: str,
    customer_id: str,
    plan: PlanRecord,
) -> dict:
    policy_arm = str(getattr(plan, "offer_policy_arm", "") or "control")
    if policy_arm == "control":
        policy_arm_profile = {
            "offer_family": "control",
            "scoring_profile": "control",
            "term_generation_rule": "",
        }
    else:
        policy_arm_profile = {
            "offer_family": str(getattr(plan, "offer_family", "") or ""),
            "scoring_profile": str(getattr(plan, "offer_scoring_profile", "") or ""),
            "term_generation_rule": str(getattr(plan, "term_generation_rule", "") or ""),
        }
    reason_codes = []
    if str(plan.status_reason or "").strip():
        reason_codes.extend(piece for piece in str(plan.status_reason).split("|") if piece)
    if not reason_codes:
        reason_codes = ["selected_best_plan"]
    return {
        "decision_id": f"{run_id}_{customer_id}",
        "run_id": str(run_id),
        "customer_id": str(customer_id),
        "policy_arm": policy_arm,
        "policy_arm_profile": policy_arm_profile,
        "candidate_set_id": f"{run_id}:{customer_id}",
        "selected_plan_id": str(plan.plan_id),
        "selected_plan_status": str(plan.status),
        "selected_offer_type": str(getattr(plan, "dominant_offer_type", "") or ""),
        "selection_propensity": 1.0,
        "propensity_source": "deterministic_fallback",
        "reason_codes": reason_codes,
        "recommended_plan_flag": True,
        "selected_plan_policy_label": str(getattr(plan, "trajectory_policy_label", "") or ""),
        "trajectory_status": str(getattr(plan, "trajectory_status", "") or ""),
        "decision_status": str(plan.status),
        "approved": bool(str(plan.status) == "APPROVED"),
        "predicted_pd": _safe_float(getattr(plan, "predicted_pd", None), 0.0),
        "plan_execution_probability": (
            _safe_float(getattr(plan, "plan_execution_probability", 0.0), 0.0)
            if getattr(plan, "plan_execution_probability", None) is not None
            else None
        ),
        "mean_group_difficulty_score": (
            _safe_float(getattr(plan, "mean_group_difficulty_score", 0.0), 0.0)
            if getattr(plan, "mean_group_difficulty_score", None) is not None
            else None
        ),
        "peak_group_difficulty_score": (
            _safe_float(getattr(plan, "peak_group_difficulty_score", 0.0), 0.0)
            if getattr(plan, "peak_group_difficulty_score", None) is not None
            else None
        ),
        "dominant_difficulty_label": str(getattr(plan, "dominant_difficulty_label", "") or ""),
        "follow_through_readiness_label": str(getattr(plan, "follow_through_readiness_label", "") or ""),
        "approval_dependent_plan_probability": (
            _safe_float(getattr(plan, "approval_dependent_plan_probability", 0.0), 0.0)
            if getattr(plan, "approval_dependent_plan_probability", None) is not None
            else None
        ),
        "offer_acceptance_probability": (
            _safe_float(getattr(plan, "offer_acceptance_probability", 0.0), 0.0)
            if getattr(plan, "offer_acceptance_probability", None) is not None
            else None
        ),
        "combined_plan_realization_probability": (
            _safe_float(getattr(plan, "combined_plan_realization_probability", 0.0), 0.0)
            if getattr(plan, "combined_plan_realization_probability", None) is not None
            else None
        ),
    }


def _build_customer_roadmap(
    *,
    customer_id: str,
    base_pd: float,
    tau: float,
    best: PlanRecord,
    best_source: str,
    row: pd.Series,
    model,
    calibrator,
    feature_cols: list[str],
    local_reason_bundle: dict | None = None,
) -> dict:
    if not list(getattr(best, "phases", [])):
        best.phases = build_canonical_phases(
            best.actions,
            base_pd=base_pd,
            predicted_pd=getattr(best, "predicted_pd", None),
            tau=tau,
        )
    if not list(getattr(best, "trajectory_checkpoints", [])):
        best.trajectory_checkpoints = build_nominal_trajectory_checkpoints(
            row=row,
            plan=best,
            base_pd=base_pd,
            tau=tau,
            model=model,
            calibrator=calibrator,
            feature_cols=feature_cols,
        )

    phases: list[dict] = []
    for phase in list(getattr(best, "phases", [])):
        steps = []
        for step_idx, action in enumerate(list(getattr(phase, "steps", [])), start=1):
            step_id = (
                str(getattr(action, "action_group_id", "") or "")
                or str(getattr(action, "action_key", "") or "")
                or f"{getattr(phase, 'phase_id', 'phase')}_step_{step_idx}"
            )
            business_view = getattr(action, "business_view").model_dump(mode="json")
            technical_view = getattr(action, "technical_view").model_dump(mode="json")
            primary_numeric_target = getattr(action, "primary_numeric_target", None)
            steps.append(
                {
                    "step_id": step_id,
                    "action_key": str(business_view.get("action_key", "") or ""),
                    "action_class": str(business_view.get("action_class", "") or ""),
                    "action_family": str(business_view.get("action_family", "") or ""),
                    "action_title": str(business_view.get("action_title", "") or ""),
                    "action_description": str(business_view.get("action_description", "") or ""),
                    "action_group_id": str(business_view.get("action_group_id", "") or ""),
                    "business_view": business_view,
                    "technical_view": technical_view,
                    "primary_numeric_target": (
                        primary_numeric_target.model_dump(mode="json")
                        if primary_numeric_target is not None
                        else None
                    ),
                    "composite_action": int(bool(getattr(action, "composite_action", False))),
                    "time_months": int(max(1, _safe_int(getattr(action, "time_months", 1), 1))),
                    "estimated_cost_usd": _safe_float(getattr(action, "estimated_cost_usd", 0.0), 0.0),
                    "requires_institutional_approval": int(
                        bool(getattr(action, "requires_institutional_approval", False))
                    ),
                    "institutional_approval_state": str(getattr(action, "institutional_approval_state", "") or ""),
                    "approval_pending_semantic_only": int(
                        bool(getattr(action, "approval_pending_semantic_only", False))
                    ),
                    "offer_type": str(getattr(action, "offer_type", "") or ""),
                    "offer_terms": dict(getattr(action, "offer_terms", {}) or {}),
                    "offer_terms_complete": int(bool(getattr(action, "offer_terms_complete", False))),
                    "requires_acceptance": int(bool(getattr(action, "requires_acceptance", False))),
                    "offer_family": str(getattr(action, "offer_family", "") or ""),
                    "offer_scoring_profile": str(getattr(action, "offer_scoring_profile", "") or ""),
                    "term_generation_rule": str(getattr(action, "term_generation_rule", "") or ""),
                    "offer_policy_arm": str(getattr(action, "offer_policy_arm", "") or ""),
                    "plan_constraint_status": str(getattr(best, "constraint_status", "valid") or "valid"),
                    "action_status": str(getattr(action, "action_status", "") or ""),
                    "action_status_reason": str(getattr(action, "action_status_reason", "") or ""),
                    "constraint_family": str(getattr(action, "constraint_family", "") or ""),
                    "constraint_reason_codes": list(getattr(action, "constraint_reason_codes", [])),
                    "was_clipped": int(bool(getattr(action, "was_clipped", False))),
                    "repair_applied": int(bool(getattr(action, "repair_applied", False))),
                    "dependency_gate": int(bool(getattr(action, "dependency_gate", False))),
                    "semantic_preserved": getattr(action, "semantic_preserved", None),
                    "diagnostic_flags": list(getattr(action, "diagnostic_flags", [])),
                    "action_execution_probability": (
                        _safe_float(getattr(action, "action_execution_probability", 0.0), 0.0)
                        if getattr(action, "action_execution_probability", None) is not None
                        else None
                    ),
                    "approval_dependent_probability": (
                        _safe_float(getattr(action, "approval_dependent_probability", 0.0), 0.0)
                        if getattr(action, "approval_dependent_probability", None) is not None
                        else None
                    ),
                    "action_group_execution_probability": (
                        _safe_float(getattr(action, "action_group_execution_probability", 0.0), 0.0)
                        if getattr(action, "action_group_execution_probability", None) is not None
                        else None
                    ),
                    "difficulty_score": (
                        _safe_float(getattr(action, "difficulty_score", 0.0), 0.0)
                        if getattr(action, "difficulty_score", None) is not None
                        else None
                    ),
                    "difficulty_label": str(getattr(action, "difficulty_label", "") or ""),
                    "difficulty_drivers": dict(getattr(action, "difficulty_drivers", {}) or {}),
                    "approval_friction": (
                        _safe_float(getattr(action, "approval_friction", 0.0), 0.0)
                        if getattr(action, "approval_friction", None) is not None
                        else None
                    ),
                }
            )
        phases.append(
            {
                "phase_id": str(getattr(phase, "phase_id", "") or ""),
                "phase_title": str(getattr(phase, "phase_title", "") or ""),
                "target_window_weeks": str(getattr(phase, "target_window_weeks", "") or ""),
                "target_window_months": list(getattr(phase, "target_window_months", [])),
                "review_week": int(_safe_int(getattr(phase, "review_week", 4), 4)),
                "target_pd": (
                    _safe_float(getattr(phase, "target_pd", 0.0), 0.0)
                    if getattr(phase, "target_pd", None) is not None
                    else None
                ),
                "gate_pass_target": bool(getattr(phase, "gate_pass_target", False)),
                "action_count": int(len(steps)),
                "phase_cost_usd": float(sum(float(step.get("estimated_cost_usd", 0.0)) for step in steps)),
                "steps": steps,
            }
        )

    checkpoints: list[dict] = []
    for checkpoint in list(getattr(best, "trajectory_checkpoints", [])):
        checkpoint_week = int(_safe_int(getattr(checkpoint, "week", 0), 0))
        checkpoints.append(
            {
                "checkpoint_id": f"checkpoint_week_{checkpoint_week}",
                "week": checkpoint_week,
                "month": int(_safe_int(getattr(checkpoint, "month", 0), 0)),
                "phase_id": str(getattr(checkpoint, "phase_id", "") or ""),
                "checkpoint_type": str(getattr(checkpoint, "checkpoint_type", "") or ""),
                "checkpoint_label": str(getattr(checkpoint, "checkpoint_label", "") or ""),
                "predicted_pd": _safe_float(getattr(checkpoint, "predicted_pd", base_pd), base_pd),
                "pd_delta_vs_base": _safe_float(getattr(checkpoint, "pd_delta_vs_base", 0.0), 0.0),
                "gate_pass_estimate": int(_safe_int(getattr(checkpoint, "gate_pass_estimate", 0), 0)),
                "checkpoint_priority": int(_safe_int(getattr(checkpoint, "checkpoint_priority", 0), 0)),
                "status": str(getattr(checkpoint, "status", "") or ""),
                "trajectory_jump_flag": int(bool(getattr(checkpoint, "trajectory_jump_flag", False))),
                "non_monotonic_flag": int(bool(getattr(checkpoint, "non_monotonic_flag", False))),
                "checkpoint_inconsistency_flag": int(
                    bool(getattr(checkpoint, "checkpoint_inconsistency_flag", False))
                ),
            }
        )

    roadmap = {
        "customer_id": str(customer_id),
        "base_pd": float(base_pd),
        "tau": float(tau),
        "best_plan_id": str(best.plan_id),
        "best_plan_source": str(best_source),
        "best_status": str(best.status),
        "best_constraint_status": str(getattr(best, "constraint_status", "valid") or "valid"),
        "trajectory_status": str(getattr(best, "trajectory_status", "on_track") or "on_track"),
        "current_phase": str(getattr(best, "current_phase", "phase_1_stabilize") or "phase_1_stabilize"),
        "phase_transition_reason": str(getattr(best, "phase_transition_reason", "initial_plan") or "initial_plan"),
        "replanned_from_phase": str(getattr(best, "replanned_from_phase", "") or ""),
        "phases": phases,
        "checkpoints": checkpoints,
        "next_review_week": int(_safe_int(getattr(best, "next_review_week", 4), 4)),
    }
    checkpoint_map = {
        int(_safe_int(checkpoint.get("week", 0), 0)): checkpoint
        for checkpoint in checkpoints
        if isinstance(checkpoint, dict)
    }
    checkpoint_4w = checkpoint_map.get(4, {})
    checkpoint_12w = checkpoint_map.get(12, {})
    checkpoint_24w = checkpoint_map.get(24, {})
    approval_ready_4w = bool(_safe_int(checkpoint_4w.get("gate_pass_estimate", 0), 0))
    approval_ready_12w = bool(_safe_int(checkpoint_12w.get("gate_pass_estimate", 0), 0))
    approval_ready_24w = bool(_safe_int(checkpoint_24w.get("gate_pass_estimate", 0), 0))
    credit_readiness_stage = "not_ready_yet"
    if str(best.status) == "APPROVED":
        if approval_ready_4w:
            credit_readiness_stage = "week_4"
        elif approval_ready_12w:
            credit_readiness_stage = "week_12"
        elif approval_ready_24w:
            credit_readiness_stage = "week_24"
        else:
            credit_readiness_stage = "now"
    roadmap["summary"] = {
        "base_pd": float(base_pd),
        "target_pd_4w": _safe_float(checkpoint_4w.get("predicted_pd", base_pd), base_pd),
        "target_pd_12w": _safe_float(checkpoint_12w.get("predicted_pd", base_pd), base_pd),
        "target_pd_24w": _safe_float(checkpoint_24w.get("predicted_pd", base_pd), base_pd),
        "plan_execution_probability": (
            _safe_float(getattr(best, "plan_execution_probability", 0.0), 0.0)
            if getattr(best, "plan_execution_probability", None) is not None
            else None
        ),
        "approval_dependent_plan_probability": (
            _safe_float(getattr(best, "approval_dependent_plan_probability", 0.0), 0.0)
            if getattr(best, "approval_dependent_plan_probability", None) is not None
            else None
        ),
        "offer_acceptance_probability": (
            _safe_float(getattr(best, "offer_acceptance_probability", 0.0), 0.0)
            if getattr(best, "offer_acceptance_probability", None) is not None
            else None
        ),
        "combined_plan_realization_probability": (
            _safe_float(getattr(best, "combined_plan_realization_probability", 0.0), 0.0)
            if getattr(best, "combined_plan_realization_probability", None) is not None
            else None
        ),
        "trajectory_status": str(getattr(best, "trajectory_status", "on_track") or "on_track"),
        "decision_status": str(best.status),
        "approval_ready_now": bool(str(best.status) == "APPROVED" and approval_ready_4w),
        "approval_ready_4w": approval_ready_4w,
        "approval_ready_12w": approval_ready_12w,
        "approval_ready_24w": approval_ready_24w,
        "credit_readiness_stage": credit_readiness_stage,
        "mean_group_difficulty_score": (
            _safe_float(getattr(best, "mean_group_difficulty_score", 0.0), 0.0)
            if getattr(best, "mean_group_difficulty_score", None) is not None
            else None
        ),
        "peak_group_difficulty_score": (
            _safe_float(getattr(best, "peak_group_difficulty_score", 0.0), 0.0)
            if getattr(best, "peak_group_difficulty_score", None) is not None
            else None
        ),
        "dominant_difficulty_label": str(getattr(best, "dominant_difficulty_label", "") or ""),
        "follow_through_readiness_label": str(getattr(best, "follow_through_readiness_label", "") or ""),
    }
    roadmap["narrative"] = build_customer_roadmap_narrative(
        base_pd=base_pd,
        tau=tau,
        phases=phases,
        checkpoints=checkpoints,
        status=str(best.status),
        local_reason_bundle=local_reason_bundle or {},
        constraint_trace=list(getattr(best, "constraint_trace", [])),
        plan_execution_probability=getattr(best, "plan_execution_probability", None),
        approval_dependent_plan_probability=getattr(best, "approval_dependent_plan_probability", None),
        offer_acceptance_probability=getattr(best, "offer_acceptance_probability", None),
        combined_plan_realization_probability=getattr(best, "combined_plan_realization_probability", None),
        mean_group_difficulty_score=getattr(best, "mean_group_difficulty_score", None),
        peak_group_difficulty_score=getattr(best, "peak_group_difficulty_score", None),
        follow_through_readiness_label=getattr(best, "follow_through_readiness_label", None),
    ).model_dump(mode="json")
    return roadmap


def _plan_to_row(plan: PlanRecord) -> dict:
    timeline_steps: list[dict] = []
    phase_1_count = 0
    phase_2_count = 0
    phase_3_count = 0
    for action in sorted(
        list(plan.actions),
        key=lambda a: (
            _safe_int(getattr(a, "time_months", 0), 0),
            str(getattr(a, "feature_name", "")),
        ),
    ):
        m = max(1, _safe_int(getattr(action, "time_months", 1), 1))
        phase_id = _phase_id_for_month(m)
        if phase_id == "phase_1_stabilize":
            phase_1_count += 1
        elif phase_id == "phase_2_build":
            phase_2_count += 1
        else:
            phase_3_count += 1
        primary_numeric_target = getattr(action, "primary_numeric_target", None)
        offer_contract = getattr(action, "offer_contract", None)
        timeline_steps.append(
            {
                "phase_id": phase_id,
                "phase_title": _phase_title(phase_id),
                "time_months": int(m),
                "business_view": dict(getattr(action, "business_view").model_dump(mode="json")),
                "technical_view": dict(getattr(action, "technical_view").model_dump(mode="json")),
                "primary_numeric_target": (
                    primary_numeric_target.model_dump(mode="json")
                    if primary_numeric_target is not None
                    else None
                ),
                "estimated_cost_usd": _safe_float(getattr(action, "estimated_cost_usd", 0.0), 0.0),
                "requires_institutional_approval": int(
                    bool(getattr(action, "requires_institutional_approval", False))
                ),
                "institutional_approval_state": str(getattr(action, "institutional_approval_state", "") or ""),
                "approval_pending_semantic_only": int(
                    bool(getattr(action, "approval_pending_semantic_only", False))
                ),
                "offer_contract": (
                    offer_contract.model_dump(mode="json")
                    if offer_contract is not None
                    else None
                ),
                "offer_type": str(getattr(action, "offer_type", "") or ""),
                "offer_terms": dict(getattr(action, "offer_terms", {}) or {}),
                "offer_terms_complete": int(bool(getattr(action, "offer_terms_complete", False))),
                "requires_acceptance": int(bool(getattr(action, "requires_acceptance", False))),
                "offer_family": str(getattr(action, "offer_family", "") or ""),
                "offer_scoring_profile": str(getattr(action, "offer_scoring_profile", "") or ""),
                "term_generation_rule": str(getattr(action, "term_generation_rule", "") or ""),
                "offer_policy_arm": str(getattr(action, "offer_policy_arm", "") or ""),
                "plan_constraint_status": str(getattr(plan, "constraint_status", "valid") or "valid"),
                "action_status": str(getattr(action, "action_status", "") or ""),
                "action_status_reason": str(getattr(action, "action_status_reason", "") or ""),
                "constraint_family": str(getattr(action, "constraint_family", "") or ""),
                "constraint_reason_codes": list(getattr(action, "constraint_reason_codes", [])),
                "was_clipped": int(bool(getattr(action, "was_clipped", False))),
                "repair_applied": int(bool(getattr(action, "repair_applied", False))),
                "dependency_gate": int(bool(getattr(action, "dependency_gate", False))),
                "semantic_preserved": getattr(action, "semantic_preserved", None),
                "diagnostic_flags": list(getattr(action, "diagnostic_flags", [])),
                "difficulty_score": (
                    _safe_float(getattr(action, "difficulty_score", 0.0), 0.0)
                    if getattr(action, "difficulty_score", None) is not None
                    else None
                ),
                "action_execution_probability": (
                    _safe_float(getattr(action, "action_execution_probability", 0.0), 0.0)
                    if getattr(action, "action_execution_probability", None) is not None
                    else None
                ),
                "approval_dependent_probability": (
                    _safe_float(getattr(action, "approval_dependent_probability", 0.0), 0.0)
                    if getattr(action, "approval_dependent_probability", None) is not None
                    else None
                ),
                "action_group_execution_probability": (
                    _safe_float(getattr(action, "action_group_execution_probability", 0.0), 0.0)
                    if getattr(action, "action_group_execution_probability", None) is not None
                    else None
                ),
                "difficulty_label": str(getattr(action, "difficulty_label", "") or ""),
                "difficulty_drivers": dict(getattr(action, "difficulty_drivers", {}) or {}),
                "approval_friction": (
                    _safe_float(getattr(action, "approval_friction", 0.0), 0.0)
                    if getattr(action, "approval_friction", None) is not None
                    else None
                ),
            }
        )
    canonical_phases = list(getattr(plan, "phases", [])) or build_canonical_phases(
        plan.actions,
        predicted_pd=getattr(plan, "predicted_pd", None),
    )
    phases_json = json.dumps(
        [phase.model_dump(mode="json") for phase in canonical_phases],
        ensure_ascii=False,
    )
    checkpoints_json = json.dumps(
        [checkpoint.model_dump(mode="json") for checkpoint in list(getattr(plan, "trajectory_checkpoints", []))],
        ensure_ascii=False,
    )
    return {
        "plan_id": plan.plan_id,
        "horizon": plan.horizon_months,
        "strategy": plan.strategy,
        "predicted_pd": plan.predicted_pd,
        "reliability": plan.reliability,
        "ci_low": plan.ci_low,
        "ci_high": plan.ci_high,
        "risk_margin": plan.risk_margin,
        "robust_score": plan.robust_score,
        "robust_margin": plan.robust_margin,
        "robust_anchor_pd": plan.robust_anchor_pd,
        "robust_method": plan.robust_method,
        "robust_worst_risk_margin": plan.robust_worst_risk_margin,
        "causal_penalty": plan.causal_penalty,
        "score": plan.score,
        "cost": _plan_cost(plan),
        "action_count": len(plan.actions),
        "phase_1_action_count": int(phase_1_count),
        "phase_2_action_count": int(phase_2_count),
        "phase_3_action_count": int(phase_3_count),
        "proximity_l1": _plan_proximity_l1(plan),
        "timeline_steps_json": json.dumps(timeline_steps, ensure_ascii=False),
        "phases_json": phases_json,
        "trajectory_checkpoints_json": checkpoints_json,
        "constraint_status": str(getattr(plan, "constraint_status", "valid") or "valid"),
        "constraint_reason": str(getattr(plan, "constraint_reason", "") or ""),
        "constraint_trace_json": json.dumps(getattr(plan, "constraint_trace", []), ensure_ascii=False),
        "plan_execution_probability": (
            _safe_float(getattr(plan, "plan_execution_probability", 0.0), 0.0)
            if getattr(plan, "plan_execution_probability", None) is not None
            else None
        ),
        "approval_dependent_plan_probability": (
            _safe_float(getattr(plan, "approval_dependent_plan_probability", 0.0), 0.0)
            if getattr(plan, "approval_dependent_plan_probability", None) is not None
            else None
        ),
        "mean_action_execution_probability": (
            _safe_float(getattr(plan, "mean_action_execution_probability", 0.0), 0.0)
            if getattr(plan, "mean_action_execution_probability", None) is not None
            else None
        ),
        "mean_approval_dependent_probability": (
            _safe_float(getattr(plan, "mean_approval_dependent_probability", 0.0), 0.0)
            if getattr(plan, "mean_approval_dependent_probability", None) is not None
            else None
        ),
        "mean_group_difficulty_score": (
            _safe_float(getattr(plan, "mean_group_difficulty_score", 0.0), 0.0)
            if getattr(plan, "mean_group_difficulty_score", None) is not None
            else None
        ),
        "peak_group_difficulty_score": (
            _safe_float(getattr(plan, "peak_group_difficulty_score", 0.0), 0.0)
            if getattr(plan, "peak_group_difficulty_score", None) is not None
            else None
        ),
        "dominant_difficulty_label": str(getattr(plan, "dominant_difficulty_label", "") or ""),
        "follow_through_readiness_label": str(getattr(plan, "follow_through_readiness_label", "") or ""),
        "nominal_pd_improvement": _safe_float(getattr(plan, "nominal_pd_improvement", 0.0), 0.0),
        "expected_pd_improvement": _safe_float(getattr(plan, "expected_pd_improvement", 0.0), 0.0),
        "executable_action_count": int(getattr(plan, "executable_action_count", 0) or 0),
        "executable_action_group_count": int(getattr(plan, "executable_action_group_count", 0) or 0),
        "approval_pending_action_count": int(getattr(plan, "approval_pending_action_count", 0) or 0),
        "offer_plan": int(bool(getattr(plan, "offer_plan", False))),
        "rankable_offer_count": int(getattr(plan, "rankable_offer_count", 0) or 0),
        "offer_acceptance_probability": (
            _safe_float(getattr(plan, "offer_acceptance_probability", 0.0), 0.0)
            if getattr(plan, "offer_acceptance_probability", None) is not None
            else None
        ),
        "combined_plan_realization_probability": (
            _safe_float(getattr(plan, "combined_plan_realization_probability", 0.0), 0.0)
            if getattr(plan, "combined_plan_realization_probability", None) is not None
            else None
        ),
        "expected_recovery_proxy": _safe_float(getattr(plan, "expected_recovery_proxy", 0.0), 0.0),
        "approval_rate_proxy_delta": _safe_float(getattr(plan, "approval_rate_proxy_delta", 0.0), 0.0),
        "default_rate_90d_proxy_delta": _safe_float(getattr(plan, "default_rate_90d_proxy_delta", 0.0), 0.0),
        "avg_margin_90d_proxy_delta": _safe_float(getattr(plan, "avg_margin_90d_proxy_delta", 0.0), 0.0),
        "governance_safe_offer": int(bool(getattr(plan, "governance_safe_offer", False))),
        "dominant_offer_type": str(getattr(plan, "dominant_offer_type", "") or ""),
        "offer_policy_arm": str(getattr(plan, "offer_policy_arm", "") or ""),
        "offer_family": str(getattr(plan, "offer_family", "") or ""),
        "offer_scoring_profile": str(getattr(plan, "offer_scoring_profile", "") or ""),
        "term_generation_rule": str(getattr(plan, "term_generation_rule", "") or ""),
        "trajectory_status": str(getattr(plan, "trajectory_status", "on_track") or "on_track"),
        "current_phase": str(getattr(plan, "current_phase", "") or ""),
        "next_review_week": int(_safe_int(getattr(plan, "next_review_week", 4), 4)),
        "phase_transition_reason": str(getattr(plan, "phase_transition_reason", "") or ""),
        "replanned_from_phase": str(getattr(plan, "replanned_from_phase", "") or ""),
        "trajectory_policy_label": str(getattr(plan, "trajectory_policy_label", "") or ""),
        "trajectory_policy_score": (
            _safe_float(getattr(plan, "trajectory_policy_score", 0.0), 0.0)
            if getattr(plan, "trajectory_policy_score", None) is not None
            else None
        ),
        "status": plan.status,
        "status_reason": plan.status_reason,
    }


def _dice_plan_record(
    idx: int,
    customer_id: str,
    run_id: str,
    row: pd.Series,
    feature_cols: list[str],
    actions: list[dict],
    model,
    calibrator,
    tau: float,
    graph: dict | None,
    causal_weight: float = 0.3,
    feasibility_profile: dict | None = None,
    segment_context: dict | None = None,
) -> PlanRecord:
    plan_actions: list[PlanAction] = []

    for a in actions:
        feature = str(a["feature_name"])
        spec = get_action_spec(feature)
        action_month = max(1, int(spec.time_months))
        phase_id = _phase_id_for_month(action_month)
        action_meta = get_action_metadata(feature, action_month=action_month, action_phase=phase_id)
        current = float(a["current_value"])
        detail = apply_target_feasibility_with_details(
            feature_name=feature,
            current_value=current,
            target_value=float(a["target_value"]),
            horizon_months=6,
            profile=feasibility_profile,
            segment_context=segment_context,
            action_class=spec.action_class,
            action_context={str(k): row.get(k) for k in row.index},
        )
        target = float(detail["target_value"])
        delta = float(target - current)
        if str(detail["status"]) == "invalid":
            continue
        week_start = int(((action_month - 1) * 4) + 1)
        week_end = int(action_month * 4)
        offer_contract = build_offer_contract(
            action_meta,
            current_value=current,
            target_value=target,
            action_month=action_month,
            action_context={str(k): row.get(k) for k in row.index},
        )
        plan_actions.append(
            PlanAction(
                feature_name=feature,
                current_value=current,
                target_value=target,
                delta=delta,
                time_months=action_month,
                estimated_cost_usd=estimate_action_cost_usd(current, target, spec),
                phase_id=_phase_id_for_month(action_month),
                week_start=week_start,
                week_end=week_end,
                checkpoint_metric=f"{feature} -> {float(target):.6f}",
                action_key=str(action_meta.get("action_key") or ""),
                action_class=action_meta.get("action_class"),
                action_family=str(action_meta.get("action_family") or "") or None,
                action_title=str(action_meta.get("action_title") or ""),
                action_description=str(action_meta.get("action_description") or ""),
                action_group_id=str(action_meta.get("action_group_id") or ""),
                composite_action=bool(action_meta.get("composite_action", False)),
                requires_institutional_approval=bool(action_meta.get("requires_institutional_approval", False)),
                approval_pending_semantic_only=bool(action_meta.get("approval_pending_semantic_only", False)),
                offer_contract=offer_contract,
                prerequisite_tags=list(action_meta.get("prerequisite_tags", [])),
                conflict_tags=list(action_meta.get("conflict_tags", [])),
                action_status=str(detail["status"]),
                action_status_reason=detail.get("status_reason"),
                constraint_family=detail.get("constraint_family"),
                constraint_reason_codes=list(detail.get("reason_codes", [])),
                was_clipped=bool(detail.get("was_clipped", False)),
                semantic_preserved=detail.get("semantic_preserved"),
                diagnostic_flags=list(detail.get("reason_codes", [])),
            )
        )

    constraint_result = enforce_action_constraints(
        plan_actions,
        action_context={str(k): row.get(k) for k in row.index},
    )
    plan_actions = list(constraint_result.actions)
    x_prime = row.copy()
    for action in plan_actions:
        x_prime[str(action.feature_name)] = float(action.target_value)

    x_input = pd.DataFrame([x_prime[feature_cols].values], columns=feature_cols)
    pred_pd = float(predict_proba_pd(model, calibrator, x_input)[0])
    cost = float(sum(a.estimated_cost_usd for a in plan_actions))
    cpen = float(causal_penalty(actions, graph, penalty_weight=causal_weight)) if graph else 0.0
    score = float((max(0.0, tau - pred_pd) * 100.0) - (cost * 0.001) - cpen)

    base_input = pd.DataFrame([row[feature_cols].values], columns=feature_cols)
    base_pd = float(predict_proba_pd(model, calibrator, base_input)[0])
    plan = PlanRecord(
        plan_id=f"{run_id}_{customer_id}_dice_{idx}",
        customer_id=customer_id,
        run_id=run_id,
        horizon_months=6,
        strategy="balanced",
        actions=plan_actions,
        predicted_pd=pred_pd,
        causal_penalty=cpen,
        score=score,
        constraint_status=constraint_result.status,
        constraint_reason=constraint_result.reason,
        constraint_trace=list(constraint_result.trace),
        status="PENDING",
    )
    annotate_plan_execution_probability(
        plan,
        base_pd=base_pd,
        customer_context={str(k): row.get(k) for k in row.index},
        segment_context=segment_context,
    )
    attach_canonical_trajectory(
        plan,
        row=row,
        base_pd=base_pd,
        tau=tau,
        model=model,
        calibrator=calibrator,
        feature_cols=feature_cols,
    )
    annotate_offer_optimization(
        plan,
        customer_context={str(k): row.get(k) for k in row.index},
        segment_context=segment_context,
    )
    return plan


def _candidate_rank_tuple(plan: PlanRecord) -> tuple:
    return (
        plan.status != "APPROVED",
        -(float(plan.robust_score) if plan.robust_score is not None else float(plan.score or -1e9)),
        int(len(plan.actions)),
        float(sum(float(a.estimated_cost_usd) for a in plan.actions)),
        float(plan.predicted_pd or 1.0),
    )


def _prune_candidate_pool(plans: list[PlanRecord], max_size: int) -> list[PlanRecord]:
    if max_size <= 0 or len(plans) <= max_size:
        return plans
    return sorted(plans, key=_candidate_rank_tuple)[:max_size]


def main() -> None:
    args = parse_args()
    base_cfg = load_config(args.base_config)
    model_cfg = load_config(args.model_config)
    rec_cfg = load_config(args.recourse_config)
    c_cfg = load_config(args.causality_config)
    s_cfg = load_config(args.safety_config)
    m_cfg = load_config(args.macro_config)
    cfg = _merge_dict(
        _merge_dict(_merge_dict(_merge_dict(base_cfg, model_cfg), rec_cfg), _merge_dict(c_cfg, s_cfg)),
        {"macro": m_cfg},
    )

    run_ctx = create_run_context(cfg, base_artifact_dir="artifacts/runs")

    contract = load_feature_contract(base_cfg.get("features_config", "configs/features_48.yaml"))
    feature_cols = contract["features"]
    target_col = contract["target"]

    processed_root = Path(base_cfg.get("paths", {}).get("processed_data", "data/processed"))
    test_path = processed_root / "test.parquet"
    train_path = processed_root / "train.parquet"
    if not test_path.exists() or not train_path.exists():
        raise FileNotFoundError("Processed data missing. Run run_prepare_data first.")

    test_df = pd.read_parquet(test_path)
    train_df = pd.read_parquet(train_path)

    row_idx = max(0, min(args.row_index, len(test_df) - 1))
    row = test_df.iloc[row_idx]

    model, calibrator, manifest, _ = load_model_bundle(
        base_path=model_cfg.get("registry", {}).get("path", "artifacts/models"),
        model_version=str(args.model_version).strip() or None,
        manifest_path=str(args.model_manifest).strip() or None,
    )

    local_reason_bundle = compute_local_reason_bundle(
        model,
        row[feature_cols],
        top_k=int(rec_cfg.get("shap", {}).get("topk_features", 10)),
        perturbations=int(rec_cfg.get("shap", {}).get("stability_perturbations", 6)),
        noise_std=float(rec_cfg.get("shap", {}).get("stability_noise_std", 0.01)),
        random_state=int(rec_cfg.get("shap", {}).get("stability_seed", 42)),
        background_df=train_df[feature_cols].sample(
            n=min(len(train_df), int(rec_cfg.get("shap", {}).get("background_samples", 256))),
            random_state=int(rec_cfg.get("shap", {}).get("stability_seed", 42)),
        ),
    )
    reasons_path = run_ctx.tables_dir / "local_reasons.json"
    reasons_path.write_text(json.dumps(local_reason_bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    adverse_action_reasons = build_adverse_action_reasons(local_reason_bundle.get("reasons", []), max_items=4)
    adverse_out = run_ctx.tables_dir / "adverse_action_reasons.json"
    adverse_out.write_text(json.dumps({"reasons": adverse_action_reasons}, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.explain_only:
        conf = local_reason_bundle.get("meta", {}).get("explainability_confidence")
        logger.info("Explain-only mode complete. Reasons saved: %s confidence=%s", reasons_path, conf)
        return

    graph_out = Path(c_cfg.get("graph", {}).get("output_path", "artifacts/models/causal_graph.json"))
    if graph_out.exists():
        graph = load_graph(graph_out)
    else:
        graph = run_rex_adapter(
            train_df,
            feature_cols=feature_cols,
            min_edge_weight=float(c_cfg.get("graph", {}).get("min_edge_weight", 0.1)),
            algorithm=c_cfg.get("algorithm", "pc"),
            output_path=graph_out,
        )

    tau = float(model_cfg.get("decision", {}).get("tau_0", 0.35))
    horizons = [int(v) for v in rec_cfg.get("horizons", [3, 6, 12])]
    strategies = [str(v) for v in rec_cfg.get("strategies", ["conservative", "balanced", "aggressive"])]
    robust_cfg_base = rec_cfg.get("robust", {}) if isinstance(rec_cfg.get("robust", {}), dict) else {}
    dice_cfg_base = rec_cfg.get("dice", {}) if isinstance(rec_cfg.get("dice", {}), dict) else {}
    scenarios = m_cfg.get("shock_scenarios", []) if isinstance(m_cfg.get("shock_scenarios", []), list) else []
    threshold_shift = float(m_cfg.get("event_impact", {}).get("threshold_shift_per_msi_unit", 0.0))
    uncertainty_cfg = s_cfg.get("uncertainty", {}) if isinstance(s_cfg.get("uncertainty", {}), dict) else {}
    conformal_artifact_path = manifest.get("conformal_calibration_path")
    if conformal_artifact_path:
        uncertainty_cfg = dict(uncertainty_cfg)
        conformal_cfg = uncertainty_cfg.get("conformal", {}) if isinstance(uncertainty_cfg.get("conformal", {}), dict) else {}
        conformal_cfg = dict(conformal_cfg)
        if not str(conformal_cfg.get("calibration_artifact_path", "")).strip():
            conformal_cfg["calibration_artifact_path"] = str(conformal_artifact_path)
        uncertainty_cfg["conformal"] = conformal_cfg

        robust_cfg_base = dict(robust_cfg_base)
        gate_obj = robust_cfg_base.get("gate_objective", {}) if isinstance(robust_cfg_base.get("gate_objective", {}), dict) else {}
        gate_obj = dict(gate_obj)
        unc_cfg = gate_obj.get("uncertainty", {}) if isinstance(gate_obj.get("uncertainty", {}), dict) else {}
        unc_cfg = dict(unc_cfg)
        if not str(unc_cfg.get("calibration_artifact_path", "")).strip():
            unc_cfg["calibration_artifact_path"] = str(conformal_artifact_path)
        gate_obj["uncertainty"] = unc_cfg
        robust_cfg_base["gate_objective"] = gate_obj

    actionable = set(get_actionable_features())
    local_reasons = local_reason_bundle.get("reasons", [])
    candidate_features = [r for r in local_reasons if str(r.get("feature", "")) in actionable]

    base_pd = float(predict_proba_pd(model, calibrator, pd.DataFrame([row[feature_cols].values], columns=feature_cols))[0])
    topk_default = int(rec_cfg.get("shap", {}).get("topk_features", 10))
    segment_caps_cfg = rec_cfg.get("segment_caps", {}) if isinstance(rec_cfg.get("segment_caps", {}), dict) else {}
    q_cfg = segment_caps_cfg.get("income_quantiles", [0.25, 0.50, 0.75])
    q_list = list(q_cfg) if isinstance(q_cfg, list) else [0.25, 0.50, 0.75]
    income_edges = _compute_income_edges(test_df.get("annual_inc", pd.Series(dtype=float)), q_list)
    feasibility_cfg = rec_cfg.get("feasibility", {}) if isinstance(rec_cfg.get("feasibility", {}), dict) else {}
    feasibility_profile: dict | None = None
    if bool(feasibility_cfg.get("enabled", False)):
        profile_path = str(feasibility_cfg.get("profile_path", "")).strip()
        if profile_path:
            feasibility_profile = load_config(profile_path)
    feasibility_internal_profile = feasibility_profile if bool(feasibility_cfg.get("enforce_on_internal", True)) else None
    feasibility_dice_profile = feasibility_profile if bool(feasibility_cfg.get("enforce_on_dice", True)) else None
    search_profile, robust_cfg, dice_cfg = _effective_recourse_search(
        base_pd=base_pd,
        tau=tau,
        topk=topk_default,
        horizons=horizons,
        strategies=strategies,
        robust_cfg=robust_cfg_base,
        dice_cfg=dice_cfg_base,
        rec_cfg=rec_cfg,
    )
    segment_context = _build_segment_context(
        row=row,
        base_pd=base_pd,
        tau=tau,
        denied_mode=bool(search_profile.get("is_denied_target", False)),
        segment_caps_cfg=segment_caps_cfg,
        income_edges=income_edges,
    )
    search_cfg_patch = search_profile.get("search_cfg", {}) if isinstance(search_profile.get("search_cfg", {}), dict) else {}
    search_cfg_patch = dict(search_cfg_patch)
    search_cfg_patch["segment_context"] = segment_context
    search_profile["search_cfg"] = search_cfg_patch
    robust_objective = str(robust_cfg.get("objective", "cvar"))
    robust_cvar_quantile = float(robust_cfg.get("cvar_quantile", 0.9))
    min_reliability = robust_cfg.get("min_reliability")
    min_worst_margin = robust_cfg.get("min_worst_risk_margin")
    min_reliability_f = float(min_reliability) if min_reliability is not None else None
    min_worst_margin_f = float(min_worst_margin) if min_worst_margin is not None else None

    fairness_cfg = rec_cfg.get("fairness", {}) if isinstance(rec_cfg.get("fairness", {}), dict) else {}
    fairness_group_col = str(fairness_cfg.get("group_feature", "home_ownership"))
    fairness_penalty = 0.0
    if fairness_group_col in test_df.columns and fairness_group_col in row.index:
        sample_n = min(len(test_df), int(fairness_cfg.get("penalty_sample_n", 3000)))
        fairness_sample = test_df.sample(n=sample_n, random_state=int(fairness_cfg.get("penalty_seed", 42)))
        fairness_proba = pd.Series(
            predict_proba_pd(model, calibrator, fairness_sample[feature_cols]),
            index=fairness_sample.index,
            dtype=float,
        )
        fairness_scored = pd.DataFrame(
            {
                fairness_group_col: fairness_sample[fairness_group_col].astype(str).fillna("unknown"),
                "approve": (fairness_proba <= tau).astype(int),
            }
        )
        group_penalties = build_group_advantage_penalties(
            fairness_scored,
            group_col=fairness_group_col,
            approval_col="approve",
            tolerance=float(fairness_cfg.get("advantage_tolerance", 0.01)),
        )
        fairness_penalty = lookup_group_penalty(row[fairness_group_col], group_penalties)

    recourse_start_ts = time.perf_counter()
    plans = generate_nine_plans(
        customer_id=args.customer_id,
        run_id=run_ctx.run_id,
        row=row,
        model=model,
        calibrator=calibrator,
        feature_cols=feature_cols,
        graph=graph,
        tau=tau,
        horizons=search_profile["horizons"],
        strategies=search_profile["strategies"],
        candidate_features=candidate_features,
        topk=int(search_profile["topk"]),
        scenarios=scenarios,
        threshold_shift_per_msi_unit=threshold_shift,
        robust_cfg=robust_cfg,
        search_cfg=search_profile.get("search_cfg", {}),
        fairness_penalty=fairness_penalty,
        feasibility_profile=feasibility_internal_profile,
        segment_context=segment_context,
    )

    macro_snapshot = load_macro_snapshot_mock()
    msi = compute_macro_stress_index(macro_snapshot, m_cfg.get("stress_index_weights", {}))
    base_alpha = float(s_cfg.get("confidence", {}).get("base_alpha", 0.05))
    high_stress_alpha = float(s_cfg.get("confidence", {}).get("high_stress_alpha", 0.01))
    stress_threshold = float(m_cfg.get("stress_threshold", 0.7))
    alpha = dynamic_alpha(msi, base_alpha=base_alpha, high_stress_alpha=high_stress_alpha, threshold=stress_threshold)

    b = int(s_cfg.get("bootstrap", {}).get("B", 500))
    validated = [
        validate_plan(
            plan,
            tau=tau,
            alpha=alpha,
            bootstrap_b=b,
            scenarios=scenarios,
            threshold_shift_per_msi_unit=threshold_shift,
            robust_objective=robust_objective,
            robust_cvar_quantile=robust_cvar_quantile,
            min_reliability=min_reliability_f,
            min_worst_risk_margin=min_worst_margin_f,
            uncertainty_cfg=uncertainty_cfg,
            segment_context=segment_context,
        )
        for plan in plans
    ]

    for p in validated:
        save_plan(p)

    plans_df = pd.DataFrame([_plan_to_row(p) for p in validated])
    plans_csv = run_ctx.tables_dir / "plans.csv"
    plans_json = run_ctx.tables_dir / "plans.json"
    plans_df.to_csv(plans_csv, index=False)
    plans_json.write_text(plans_df.to_json(orient="records", indent=2), encoding="utf-8")

    search_cfg = search_profile.get("search_cfg", {}) if isinstance(search_profile.get("search_cfg", {}), dict) else {}
    internal_approved_count = int(sum(1 for p in validated if p.status == "APPROVED"))
    deny_mode = bool(search_profile.get("is_denied_target", False))
    time_budget_ms = int(search_cfg.get("time_budget_ms", 0))
    skip_dice_when_internal_approved = bool(search_cfg.get("skip_dice_when_internal_approved", False))
    skip_dice_for_non_denied = bool(search_cfg.get("skip_dice_for_non_denied", False))
    elapsed_so_far_ms = float((time.perf_counter() - recourse_start_ts) * 1000.0)
    remaining_budget_ms = int(max(0.0, float(time_budget_ms) - elapsed_so_far_ms)) if time_budget_ms > 0 else 0

    skip_dice_reason = ""
    if skip_dice_when_internal_approved and internal_approved_count > 0:
        skip_dice_reason = "internal_already_approved"
    if not skip_dice_reason and skip_dice_for_non_denied and not deny_mode:
        skip_dice_reason = "non_denied_profile"
    if not skip_dice_reason and time_budget_ms > 0 and elapsed_so_far_ms >= float(time_budget_ms):
        skip_dice_reason = "time_budget_exceeded"

    dice_records: list[PlanRecord] = []
    dice_backend = "skipped"
    dice_telemetry = {
        "method_requested": str(dice_cfg.get("method", "random")),
        "method_used": "skipped",
        "fallback_reason": skip_dice_reason or "skipped_by_policy",
        "attempted_method_count": 0,
    }
    if not skip_dice_reason:
        configured_timeout_ms = int(dice_cfg.get("timeout_ms", 0))
        dice_timeout_ms = configured_timeout_ms
        if dice_timeout_ms > 0 and remaining_budget_ms > 0:
            dice_timeout_ms = min(dice_timeout_ms, remaining_budget_ms)
        dice_action_sets, dice_backend, dice_telemetry = generate_dice_counterfactual_actions(
            row=row,
            feature_cols=feature_cols,
            actionable_features=sorted(actionable),
            model=model,
            calibrator=calibrator,
            train_df=train_df,
            target_col=target_col,
            total_cfs=int(dice_cfg.get("total_cfs", 3)),
            random_seed=int(dice_cfg.get("seed", 42)),
            dice_method=str(dice_cfg.get("method", "random")),
            max_actions=int(dice_cfg.get("max_actions", 4)),
            enable_method_fallback=bool(dice_cfg.get("enable_method_fallback", True)),
            timeout_ms=int(max(0, dice_timeout_ms)),
            stopping_threshold=float(tau),
        )
        for idx, actions in enumerate(dice_action_sets, start=1):
            p = _dice_plan_record(
                idx=idx,
                customer_id=args.customer_id,
                run_id=run_ctx.run_id,
                row=row,
                feature_cols=feature_cols,
                actions=actions,
                model=model,
                calibrator=calibrator,
                tau=tau,
                graph=graph,
                causal_weight=float(c_cfg.get("penalty_weight", 0.3)),
                feasibility_profile=feasibility_dice_profile,
                segment_context=segment_context,
            )
            p = validate_plan(
                p,
                tau=tau,
                alpha=alpha,
                bootstrap_b=b,
                scenarios=scenarios,
                threshold_shift_per_msi_unit=threshold_shift,
                robust_objective=robust_objective,
                robust_cvar_quantile=robust_cvar_quantile,
                min_reliability=min_reliability_f,
                min_worst_risk_margin=min_worst_margin_f,
                uncertainty_cfg=uncertainty_cfg,
                segment_context=segment_context,
            )
            dice_records.append(p)
            save_plan(p)

    dice_df = pd.DataFrame([_plan_to_row(p) for p in dice_records])
    dice_csv = run_ctx.tables_dir / "dice_plans.csv"
    dice_json = run_ctx.tables_dir / "dice_plans.json"
    dice_df.to_csv(dice_csv, index=False)
    dice_json.write_text(dice_df.to_json(orient="records", indent=2), encoding="utf-8")
    dice_tel_json = run_ctx.tables_dir / "dice_telemetry.json"
    dice_tel_json.write_text(json.dumps(dice_telemetry, indent=2, ensure_ascii=False), encoding="utf-8")

    candidate_pool = validated + dice_records
    candidate_pool_max_size = int(search_cfg.get("candidate_pool_max_size", 0))
    candidate_pool = _prune_candidate_pool(candidate_pool, candidate_pool_max_size)
    pool_df = pd.DataFrame(
        [
            {
                **_plan_to_row(p),
                "plan_source": ("dice" if "_dice_" in str(p.plan_id) else "internal"),
            }
            for p in candidate_pool
        ]
    )
    pool_csv = run_ctx.tables_dir / "candidate_pool.csv"
    pool_json = run_ctx.tables_dir / "candidate_pool.json"
    pool_df.to_csv(pool_csv, index=False)
    pool_json.write_text(pool_df.to_json(orient="records", indent=2), encoding="utf-8")

    best = choose_best_plan(
        candidate_pool,
        base_pd=base_pd,
        tau=tau,
        min_reliability=min_reliability_f,
        min_worst_risk_margin=min_worst_margin_f,
        fairness_penalty=fairness_penalty,
        denied_mode=bool(search_profile.get("is_denied_target", False)),
        segment_context=segment_context,
        denied_objective_cfg=robust_cfg.get("denied_objective", {}),
    )
    best_source = "dice" if "_dice_" in str(best.plan_id) else "internal"
    roadmap = _build_customer_roadmap(
        customer_id=args.customer_id,
        base_pd=base_pd,
        tau=tau,
        best=best,
        best_source=best_source,
        row=row,
        model=model,
        calibrator=calibrator,
        feature_cols=feature_cols,
        local_reason_bundle=local_reason_bundle,
    )
    roadmap_json = run_ctx.tables_dir / "customer_roadmap.json"
    roadmap_json.write_text(json.dumps(roadmap, indent=2, ensure_ascii=False), encoding="utf-8")
    roadmap_steps_rows: list[dict] = []
    for phase in roadmap.get("phases", []):
        phase_id = str(phase.get("phase_id", ""))
        phase_title = str(phase.get("phase_title", ""))
        for step in phase.get("steps", []):
            technical_view = step.get("technical_view", {})
            if not isinstance(technical_view, dict):
                technical_view = {}
            primary_numeric_target = step.get("primary_numeric_target", {})
            if not isinstance(primary_numeric_target, dict):
                primary_numeric_target = {}
            row_out = {
                "customer_id": str(args.customer_id),
                "best_plan_id": str(best.plan_id),
                "phase_id": phase_id,
                "phase_title": phase_title,
                "target_window_weeks": str(phase.get("target_window_weeks", "")),
                "action_key": str(step.get("action_key", "")),
                "action_class": str(step.get("action_class", "")),
                "action_title": str(step.get("action_title", "")),
                "action_group_id": str(step.get("action_group_id", "")),
                "composite_action": _safe_int(step.get("composite_action", 0), 0),
                "feature_name": str(technical_view.get("feature_name", step.get("feature_name", "")) or ""),
                "metric_key": str(primary_numeric_target.get("metric_key", "") or ""),
                "unit": str(primary_numeric_target.get("unit", "") or ""),
                "current_value": _safe_float(
                    primary_numeric_target.get("current_value", technical_view.get("current_value", step.get("current_value", 0.0))),
                    0.0,
                ),
                "target_value": _safe_float(
                    primary_numeric_target.get("target_value", technical_view.get("target_value", step.get("target_value", 0.0))),
                    0.0,
                ),
                "delta": _safe_float(
                    primary_numeric_target.get("delta_value", technical_view.get("delta", step.get("delta", 0.0))),
                    0.0,
                ),
                "time_months": _safe_int(step.get("time_months", 0), 0),
                "due_month": _safe_int(primary_numeric_target.get("due_month", step.get("time_months", 0)), 0),
                "direction": str(primary_numeric_target.get("direction", "") or ""),
                "generation_notes_json": json.dumps(
                    list(primary_numeric_target.get("generation_notes", [])),
                    ensure_ascii=False,
                ),
                "estimated_cost_usd": _safe_float(step.get("estimated_cost_usd", 0.0), 0.0),
                "requires_institutional_approval": _safe_int(step.get("requires_institutional_approval", 0), 0),
                "approval_pending_semantic_only": _safe_int(step.get("approval_pending_semantic_only", 0), 0),
                "action_status": str(step.get("action_status", "") or ""),
                "constraint_family": str(step.get("constraint_family", "") or ""),
                "constraint_reason_codes_json": json.dumps(
                    list(step.get("constraint_reason_codes", [])),
                    ensure_ascii=False,
                ),
                "was_clipped": _safe_int(step.get("was_clipped", 0), 0),
                "repair_applied": _safe_int(step.get("repair_applied", 0), 0),
                "dependency_gate": _safe_int(step.get("dependency_gate", 0), 0),
                "semantic_preserved": (
                    bool(step.get("semantic_preserved"))
                    if step.get("semantic_preserved", None) is not None
                    else None
                ),
            }
            roadmap_steps_rows.append(row_out)
    roadmap_steps_df = pd.DataFrame(roadmap_steps_rows)
    roadmap_steps_csv = run_ctx.tables_dir / "customer_roadmap_steps.csv"
    roadmap_steps_df.to_csv(roadmap_steps_csv, index=False)
    decision_log_record = _decision_log_record(
        run_id=run_ctx.run_id,
        customer_id=str(args.customer_id),
        plan=best,
    )
    decision_log_summary = build_decision_logging_summary([decision_log_record])
    decision_log_out = run_ctx.tables_dir / "decision_log_record.json"
    decision_log_summary_out = run_ctx.tables_dir / "decision_logging_summary.json"
    decision_log_out.write_text(json.dumps(decision_log_record, indent=2, ensure_ascii=False), encoding="utf-8")
    decision_log_summary_out.write_text(
        json.dumps(decision_log_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    cp_week4 = next((c for c in roadmap.get("checkpoints", []) if int(c.get("week", 0)) == 4), {})
    cp_week12 = next((c for c in roadmap.get("checkpoints", []) if int(c.get("week", 0)) == 12), {})
    cp_week24 = next((c for c in roadmap.get("checkpoints", []) if int(c.get("week", 0)) == 24), {})
    summary = {
        "model_version": manifest["model_version"],
        "customer_id": args.customer_id,
        "base_pd": base_pd,
        "denied_target_mode": bool(search_profile.get("is_denied_target", False)),
        "income_band": str(segment_context.get("income_band", "")),
        "risk_band": str(segment_context.get("risk_band", "")),
        "segment_caps_applied": bool(segment_context.get("segment_caps_applied", False)),
        "cap_multiplier_income": float(segment_context.get("cap_multiplier_income", 1.0)),
        "cap_multiplier_risk": float(segment_context.get("cap_multiplier_risk", 1.0)),
        "cap_multiplier_total": float(segment_context.get("cap_multiplier", 1.0)),
        "plan_count": len(validated),
        "approved_count": int(sum(1 for p in validated if p.status == "APPROVED")),
        "candidate_pool_count": len(candidate_pool),
        "candidate_pool_approved_count": int(sum(1 for p in candidate_pool if p.status == "APPROVED")),
        "best_plan_id": best.plan_id,
        "best_plan_source": best_source,
        "best_status": best.status,
        "trajectory_pd_4w": _safe_float(cp_week4.get("predicted_pd", base_pd), base_pd),
        "trajectory_pd_12w": _safe_float(cp_week12.get("predicted_pd", base_pd), base_pd),
        "trajectory_pd_24w": _safe_float(cp_week24.get("predicted_pd", base_pd), base_pd),
        "trajectory_gate_pass_4w": _safe_int(cp_week4.get("gate_pass_estimate", 0), 0),
        "trajectory_gate_pass_12w": _safe_int(cp_week12.get("gate_pass_estimate", 0), 0),
        "trajectory_gate_pass_24w": _safe_int(cp_week24.get("gate_pass_estimate", 0), 0),
        "trajectory_next_review_week": _safe_int(roadmap.get("next_review_week", 4), 4),
        "trajectory_phase_count": int(len(roadmap.get("phases", []))),
        "trajectory_step_count": int(sum(len(p.get("steps", [])) for p in roadmap.get("phases", []))),
        "mean_group_difficulty_score": (
            _safe_float(getattr(best, "mean_group_difficulty_score", 0.0), 0.0)
            if getattr(best, "mean_group_difficulty_score", None) is not None
            else None
        ),
        "peak_group_difficulty_score": (
            _safe_float(getattr(best, "peak_group_difficulty_score", 0.0), 0.0)
            if getattr(best, "peak_group_difficulty_score", None) is not None
            else None
        ),
        "dominant_difficulty_label": str(getattr(best, "dominant_difficulty_label", "") or ""),
        "follow_through_readiness_label": str(getattr(best, "follow_through_readiness_label", "") or ""),
        "macro_stress_index": msi,
        "alpha_used": alpha,
        "robust_objective": robust_objective,
        "robust_cvar_quantile": robust_cvar_quantile,
        "avg_reliability": float(sum(float(p.reliability or 0.0) for p in validated) / max(1, len(validated))),
        "avg_robust_score": float(sum(float(p.robust_score or 0.0) for p in validated) / max(1, len(validated))),
        "min_robust_margin": float(min(float(p.robust_margin or 0.0) for p in validated)),
        "local_explainability_confidence": float(local_reason_bundle.get("meta", {}).get("explainability_confidence", 0.0)),
        "local_shap_stability_score": float(local_reason_bundle.get("meta", {}).get("stability_score", 0.0)),
        "local_shap_baseline_drift_l1": float(local_reason_bundle.get("meta", {}).get("baseline_drift_l1", 0.0)),
        "adverse_action_reasons": adverse_action_reasons,
        "dice_backend": dice_backend,
        "dice_plan_count": len(dice_records),
        "dice_method_requested": dice_telemetry.get("method_requested"),
        "dice_method_used": dice_telemetry.get("method_used"),
        "dice_fallback_reason": dice_telemetry.get("fallback_reason"),
        "dice_changed_features": int(dice_telemetry.get("changed_feature_union_count", 0)),
        "dice_attempted_method_count": int(dice_telemetry.get("attempted_method_count", 0)),
        "dice_skipped_reason": str(dice_telemetry.get("fallback_reason") or ""),
        "search_time_budget_ms": int(time_budget_ms),
        "search_elapsed_ms": float((time.perf_counter() - recourse_start_ts) * 1000.0),
        "fairness_penalty": float(fairness_penalty),
        "decision_id": str(decision_log_record["decision_id"]),
        "selection_propensity": float(decision_log_record["selection_propensity"]),
        "decision_log_completeness": float(decision_log_summary.get("decision_log_completeness", 0.0)),
    }
    run_ctx.save_metrics(summary)

    logger.info(
        "Recourse run complete. plans=%s approved=%s denied_target=%s best_source=%s",
        summary["plan_count"],
        summary["approved_count"],
        summary["denied_target_mode"],
        summary["best_plan_source"],
    )
    logger.info("Plan outputs: %s %s", plans_csv, plans_json)
    logger.info("DiCE outputs: %s %s %s backend=%s", dice_csv, dice_json, dice_tel_json, dice_backend)
    logger.info("Candidate pool outputs: %s %s", pool_csv, pool_json)
    logger.info("Roadmap outputs: %s %s", roadmap_json, roadmap_steps_csv)
    logger.info("Decision logging outputs: %s %s", decision_log_out, decision_log_summary_out)
    logger.info("Adverse action reasons: %s", adverse_out)


if __name__ == "__main__":
    main()
