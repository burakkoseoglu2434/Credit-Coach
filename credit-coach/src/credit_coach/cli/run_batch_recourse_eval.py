from __future__ import annotations

import argparse
import json
import logging
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from credit_coach.causality.action_constraints import causal_penalty
from credit_coach.causality.graph_utils import load_graph
from credit_coach.coaching.loop import run_weekly_coaching_loop
from credit_coach.coaching.planner import choose_best_plan
from credit_coach.data.ingest import load_feature_contract
from credit_coach.data.schema import PlanAction, PlanRecord
from credit_coach.evaluation.fairness import (
    build_canonical_segment_key,
    compute_multi_segment_fairness,
    build_recourse_fairness_bundle,
    build_fairness_stress_matrix,
    build_group_advantage_penalties,
    compute_fairness_bundle,
    lookup_group_penalty,
)
from credit_coach.evaluation.portfolio_validation import build_portfolio_validation_artifacts
from credit_coach.macro.impact import dynamic_alpha
from credit_coach.macro.sources import load_macro_snapshot_mock
from credit_coach.macro.stress_index import compute_macro_stress_index
from credit_coach.model.predict import predict_proba_pd
from credit_coach.model.registry import build_frozen_model_manifest, load_model_bundle
from credit_coach.recourse.action_space import (
    estimate_action_cost_usd,
    get_action_metadata,
    get_action_spec,
    get_actionable_features,
)
from credit_coach.recourse.action_constraints import enforce_action_constraints
from credit_coach.recourse.dice_baseline import generate_dice_counterfactual_actions, generate_dice_like_baseline
from credit_coach.recourse.execution_probability import (
    annotate_plan_execution_probability,
    classify_execution_scenario,
)
from credit_coach.recourse.feasibility import apply_target_feasibility_with_details
from credit_coach.recourse.generator import PlanGenConfig, generate_nine_plans, generate_plan_record
from credit_coach.recourse.trajectory import (
    apply_plan_until_month,
    phase_id_for_month,
    phase_title,
    predict_plan_pd_at_month,
)
from credit_coach.safety.validator import validate_plan
from credit_coach.storage.repository import build_decision_logging_summary
from credit_coach.utils.hashing import hash_config, hash_file
from credit_coach.utils.run_context import create_run_context, load_config
from credit_coach.xai.shap_local import compute_local_topk_reasons

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_batch_recourse_eval")

_STATUS_PRIORITY = {
    "APPROVED": 0,
    "NEEDS_REVIEW": 1,
    "REJECTED": 2,
    "ERROR": 3,
}

_CANDIDATE_SOURCE_CATALOG: tuple[str, ...] = ("internal", "dice", "rule", "fallback")
_HIGH_RISK_ACTIVATION_FLOOR = 0.05


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch recourse evaluation for large customer cohorts")
    p.add_argument("--base_config", type=str, default="configs/default.yaml")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--recourse_config", type=str, default="configs/recourse.yaml")
    p.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    p.add_argument("--safety_config", type=str, default="configs/safety.yaml")
    p.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    p.add_argument("--n_customers", type=int, default=1000)
    p.add_argument("--sample_seed", type=int, default=42)
    p.add_argument("--group_feature", type=str, default="home_ownership")
    p.add_argument("--log_every", type=int, default=50)
    p.add_argument("--n_workers", type=int, default=1)
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


def _build_group_bucket(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series) and series.nunique(dropna=True) > 8:
        binned = pd.qcut(series, q=2, labels=["low", "high"], duplicates="drop")
        return binned.astype(str).fillna("unknown")
    return series.astype(str).fillna("unknown")


def _high_stress_gap(stress_df: pd.DataFrame, *, fallback: float) -> float:
    if stress_df.empty or "high_stress" not in stress_df.columns or "approval_gap" not in stress_df.columns:
        return float(fallback)
    hs = stress_df[stress_df["high_stress"] == 1]
    if hs.empty:
        return float(fallback)
    return float(hs["approval_gap"].max())


def _as_float_percentile(values: pd.Series, q: float) -> float:
    if values.empty:
        return 0.0
    return float(np.quantile(values.to_numpy(dtype=float), q))


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        if v is None:
            return int(default)
        if isinstance(v, float) and np.isnan(v):
            return int(default)
        return int(v)
    except Exception:
        return int(default)


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return float(default)
        if isinstance(v, float) and np.isnan(v):
            return float(default)
        return float(v)
    except Exception:
        return float(default)


def _safe_str(v: Any, default: str = "") -> str:
    if v is None:
        return default
    if isinstance(v, float) and np.isnan(v):
        return default
    return str(v)


def _split_reason_codes(value: Any) -> list[str]:
    raw = _safe_str(value, "")
    if not raw:
        return []
    return [piece.strip() for piece in raw.replace(",", "|").split("|") if piece.strip()]


def _build_decision_log_records(batch_df: pd.DataFrame, *, run_id: str) -> pd.DataFrame:
    if batch_df.empty:
        return pd.DataFrame(
            columns=[
                "decision_id",
                "run_id",
                "customer_id",
                "policy_arm",
                "policy_arm_profile",
                "candidate_set_id",
                "selected_plan_id",
                "selected_plan_status",
                "selected_offer_type",
                "selection_propensity",
                "propensity_source",
                "reason_codes",
                "recommended_plan_flag",
                "selected_plan_policy_label",
                "trajectory_status",
                "decision_status",
                "approved",
                "predicted_pd",
                "plan_execution_probability",
                "offer_acceptance_probability",
                "combined_plan_realization_probability",
            ]
        )

    records: list[dict[str, Any]] = []
    for row in batch_df.to_dict(orient="records"):
        customer_id = _safe_str(row.get("customer_id", ""))
        selected_plan_id = _safe_str(row.get("best_plan_id", ""))
        selected_offer_type = _safe_str(row.get("best_offer_type", ""))
        policy_arm = _safe_str(row.get("best_offer_policy_arm", "")) or "control"
        if policy_arm == "control":
            policy_arm_profile = {
                "offer_family": "control",
                "scoring_profile": "control",
                "term_generation_rule": "",
            }
        else:
            policy_arm_profile = {
                "offer_family": _safe_str(row.get("best_offer_family", "")),
                "scoring_profile": _safe_str(row.get("best_offer_scoring_profile", "")),
                "term_generation_rule": _safe_str(row.get("best_term_generation_rule", "")),
            }
        reason_codes = _split_reason_codes(row.get("best_status_reason", "")) or ["selected_best_plan"]
        records.append(
            {
                "decision_id": f"{run_id}_{customer_id}",
                "run_id": str(run_id),
                "customer_id": customer_id,
                "policy_arm": policy_arm,
                "policy_arm_profile": policy_arm_profile,
                "candidate_set_id": f"{run_id}:{customer_id}",
                "selected_plan_id": selected_plan_id,
                "selected_plan_status": _safe_str(row.get("best_status", "")),
                "selected_offer_type": selected_offer_type,
                "selection_propensity": 1.0,
                "propensity_source": "deterministic_fallback",
                "reason_codes": reason_codes,
                "recommended_plan_flag": bool(selected_plan_id),
                "selected_plan_policy_label": _safe_str(row.get("trajectory_policy_label", "")),
                "trajectory_status": _safe_str(row.get("trajectory_status", "")),
                "decision_status": _safe_str(row.get("best_status", "")),
                "approved": bool(_safe_str(row.get("best_status", "")) == "APPROVED"),
                "predicted_pd": _safe_float(row.get("best_candidate_pd", None), 0.0),
                "plan_execution_probability": _safe_float(row.get("best_plan_execution_probability", None), 0.0),
                "offer_acceptance_probability": (
                    _safe_float(row.get("best_offer_acceptance_probability", None), 0.0)
                    if int(_safe_int(row.get("best_offer_plan", 0), 0)) == 1
                    else None
                ),
                "combined_plan_realization_probability": (
                    _safe_float(row.get("best_combined_plan_realization_probability", None), 0.0)
                    if int(_safe_int(row.get("best_offer_plan", 0), 0)) == 1
                    else None
                ),
            }
        )
    return pd.DataFrame(records)


def _round_metric(value: Any, *, digits: int = 6) -> float:
    try:
        metric = float(value)
    except Exception:
        return 0.0
    if np.isnan(metric):
        return 0.0
    return round(metric, digits)


def _stress_band_from_row(row: pd.Series) -> str:
    dti = _safe_float(row.get("dti"), 0.0)
    revol_util = _safe_float(row.get("revol_util"), 0.0)
    annual_inc = max(_safe_float(row.get("annual_inc"), 0.0), 1.0)
    monthly_income = annual_inc / 12.0
    installment = _safe_float(row.get("installment"), 0.0)
    payment_burden = float(installment / monthly_income) if monthly_income > 0 else 0.0
    stress_score = 0
    if dti >= 25.0:
        stress_score += 1
    if revol_util >= 70.0:
        stress_score += 1
    if payment_burden >= 0.18:
        stress_score += 1
    if stress_score >= 2:
        return "high_stress"
    if stress_score == 1:
        return "elevated"
    return "base"


def _load_curated_demo_case(project_root: Path) -> dict[str, Any] | None:
    demo_path = project_root / "credit-coach-website" / "demo-data" / "single_customer_roadmap.json"
    if not demo_path.exists():
        return None
    try:
        payload = json.loads(demo_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _extract_model_importance_vector(model: Any, feature_cols: list[str]) -> np.ndarray | None:
    def _as_1d(arr_like: Any) -> np.ndarray | None:
        try:
            arr = np.asarray(arr_like, dtype=float).reshape(-1)
        except Exception:
            return None
        if arr.size != len(feature_cols):
            return None
        return arr

    direct_coef = _as_1d(getattr(model, "coef_", None))
    if direct_coef is not None:
        return direct_coef

    direct_importance = _as_1d(getattr(model, "feature_importances_", None))
    if direct_importance is not None:
        return direct_importance

    # sklearn Pipeline compatibility
    named_steps = getattr(model, "named_steps", None)
    if isinstance(named_steps, dict):
        for step in reversed(list(named_steps.values())):
            step_coef = _as_1d(getattr(step, "coef_", None))
            if step_coef is not None:
                return step_coef
            step_importance = _as_1d(getattr(step, "feature_importances_", None))
            if step_importance is not None:
                return step_importance

    steps = getattr(model, "steps", None)
    if isinstance(steps, list):
        for pair in reversed(steps):
            if not isinstance(pair, tuple) or len(pair) != 2:
                continue
            est = pair[1]
            step_coef = _as_1d(getattr(est, "coef_", None))
            if step_coef is not None:
                return step_coef
            step_importance = _as_1d(getattr(est, "feature_importances_", None))
            if step_importance is not None:
                return step_importance
    return None


def _pick_ordered_values(
    values: list[Any] | None,
    *,
    preferred: list[Any],
    keep: int,
) -> list[Any]:
    if not isinstance(values, list) or not values:
        return []
    keep = max(1, int(keep))
    out: list[Any] = []
    for p in preferred:
        if p in values and p not in out:
            out.append(p)
            if len(out) >= keep:
                return out
    for v in values:
        if v not in out:
            out.append(v)
            if len(out) >= keep:
                break
    return out


def _tune_internal_search_profile_for_budget(
    search_profile: dict[str, Any],
    *,
    time_budget_ms: int,
    denied_mode: bool,
    risk_band: str,
) -> dict[str, Any]:
    if int(time_budget_ms) <= 0:
        return dict(search_profile)

    sp = dict(search_profile)
    search_cfg = sp.get("search_cfg", {}) if isinstance(sp.get("search_cfg", {}), dict) else {}
    search_cfg = dict(search_cfg)

    topk = max(1, int(sp.get("topk", 4)))
    horizons = list(sp.get("horizons", [3, 6, 12])) if isinstance(sp.get("horizons", []), list) else [3, 6, 12]
    strategies = (
        list(sp.get("strategies", ["balanced"])) if isinstance(sp.get("strategies", []), list) else ["balanced"]
    )
    high_risk_denied = bool(denied_mode and str(risk_band).strip().lower() == "high")

    if int(time_budget_ms) <= 1200:
        max_topk = 10 if high_risk_denied else (8 if denied_mode else 6)
        sp["topk"] = min(topk, max_topk)
        if high_risk_denied:
            # Under tight budgets, one stronger plan outperforms many weak attempts.
            sp["horizons"] = _pick_ordered_values(horizons, preferred=[6, 12, 3], keep=1)
            sp["strategies"] = _pick_ordered_values(
                strategies, preferred=["aggressive", "balanced", "conservative"], keep=1
            )
        else:
            keep_h = 2 if denied_mode else 1
            sp["horizons"] = _pick_ordered_values(horizons, preferred=[6, 3, 12], keep=keep_h)
            keep_s = 2 if denied_mode else 1
            sp["strategies"] = _pick_ordered_values(
                strategies, preferred=["balanced", "aggressive", "conservative"], keep=keep_s
            )

        adaptive_cfg = (
            search_cfg.get("adaptive_steps", {})
            if isinstance(search_cfg.get("adaptive_steps", {}), dict)
            else {}
        )
        adaptive_cfg = dict(adaptive_cfg)
        if bool(adaptive_cfg.get("enabled", False)):
            attempt_cap = 3 if high_risk_denied else 2
            adaptive_cfg["max_attempts_per_feature"] = min(
                max(1, int(adaptive_cfg.get("max_attempts_per_feature", 3))),
                attempt_cap,
            )
            adaptive_cfg["max_multiplier"] = min(
                3.5 if high_risk_denied else 2.5,
                float(adaptive_cfg.get("max_multiplier", 4.0)),
            )
            adaptive_cfg["growth_factor"] = min(
                1.5 if high_risk_denied else 1.35,
                float(adaptive_cfg.get("growth_factor", 1.5)),
            )
            search_cfg["adaptive_steps"] = adaptive_cfg

        action_budget = (
            search_cfg.get("action_budget", {})
            if isinstance(search_cfg.get("action_budget", {}), dict)
            else {}
        )
        action_budget = dict(action_budget)
        if bool(action_budget.get("enabled", False)):
            max_actions_cap = 8 if high_risk_denied else (6 if denied_mode else 4)
            action_budget["max_actions"] = min(max_actions_cap, int(action_budget.get("max_actions", max_actions_cap)))
            search_cfg["action_budget"] = action_budget

    if int(time_budget_ms) <= 900:
        # Weekly optimizer + hard budget often triggers deadline abort on denied cohort.
        weekly_cfg = (
            search_cfg.get("weekly_optimizer", {})
            if isinstance(search_cfg.get("weekly_optimizer", {}), dict)
            else {}
        )
        weekly_cfg = dict(weekly_cfg)
        weekly_cfg["enabled"] = False
        search_cfg["weekly_optimizer"] = weekly_cfg

    if int(time_budget_ms) <= 650:
        sp["topk"] = min(int(sp.get("topk", 4)), 4 if denied_mode else 3)
        sp["horizons"] = _pick_ordered_values(sp.get("horizons", horizons), preferred=[6, 3, 12], keep=1)
        sp["strategies"] = _pick_ordered_values(
            sp.get("strategies", strategies), preferred=["balanced", "conservative", "aggressive"], keep=1
        )
        adaptive_cfg = (
            search_cfg.get("adaptive_steps", {})
            if isinstance(search_cfg.get("adaptive_steps", {}), dict)
            else {}
        )
        adaptive_cfg = dict(adaptive_cfg)
        adaptive_cfg["enabled"] = False
        search_cfg["adaptive_steps"] = adaptive_cfg

    # High-risk denied keep one extra candidate path when budget allows.
    if high_risk_denied and int(time_budget_ms) >= 800:
        sp["topk"] = max(int(sp.get("topk", 1)), 6)

    sp["search_cfg"] = search_cfg
    return sp


def _fast_internal_rescue_plan(
    *,
    customer_id: str,
    run_id: str,
    row: pd.Series,
    model,
    calibrator,
    feature_cols: list[str],
    graph: dict | None,
    tau: float,
    candidate_features: list[dict[str, Any]] | list[str],
    robust_cfg: dict[str, Any],
    fairness_penalty: float,
    scenarios: list[dict],
    threshold_shift_per_msi_unit: float,
    robust_objective: str,
    robust_cvar_quantile: float,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
    alpha: float,
    bootstrap_b: int,
    uncertainty_cfg: dict[str, Any],
    feasibility_profile: dict[str, Any] | None,
    segment_context: dict[str, Any] | None,
    denied_mode: bool,
) -> PlanRecord | None:
    risk_band = str((segment_context or {}).get("risk_band", "")).strip().lower()
    high_risk_denied = bool(denied_mode and risk_band == "high")
    horizons = [h for h in (6, 3, 12) if h in (3, 6, 12)]
    h = int(horizons[0])
    strat = "aggressive" if high_risk_denied else "balanced"
    topk = 6 if high_risk_denied else (4 if denied_mode else 3)

    rescue_search_cfg = {
        "denied_mode": bool(denied_mode),
        "min_abs_action_delta": 1e-6,
        "adaptive_steps": {
            "enabled": bool(high_risk_denied),
            "max_attempts_per_feature": 2,
            "max_multiplier": 3.0,
            "growth_factor": 1.4,
            "min_pd_improvement": 0.001,
        },
        "weekly_optimizer": {"enabled": False},
        "action_budget": {
            "enabled": True,
            "max_actions": 4 if high_risk_denied else (2 if denied_mode else 1),
        },
    }
    try:
        p = generate_plan_record(
            customer_id=customer_id,
            run_id=run_id,
            row=row,
            model=model,
            calibrator=calibrator,
            feature_cols=feature_cols,
            horizon_months=h,
            strategy=strat,
            graph=graph,
            cfg=PlanGenConfig(tau=tau),
            candidate_features=candidate_features,
            topk=topk,
            scenarios=scenarios,
            threshold_shift_per_msi_unit=threshold_shift_per_msi_unit,
            robust_cfg=robust_cfg,
            search_cfg=rescue_search_cfg,
            fairness_penalty=fairness_penalty,
            feasibility_profile=feasibility_profile,
            segment_context=segment_context,
            deadline_ts=None,
            runtime_diag=None,
        )
        p = validate_plan(
            p,
            tau=tau,
            alpha=alpha,
            bootstrap_b=bootstrap_b,
            scenarios=scenarios,
            threshold_shift_per_msi_unit=threshold_shift_per_msi_unit,
            robust_objective=robust_objective,
            robust_cvar_quantile=robust_cvar_quantile,
            min_reliability=min_reliability,
            min_worst_risk_margin=min_worst_risk_margin,
            uncertainty_cfg=uncertainty_cfg,
            segment_context=segment_context,
        )
        p.plan_id = f"{p.plan_id}_internal_rescue"
        return p
    except Exception:
        return None


def _status_priority(status: str | None) -> int:
    key = str(status or "").strip().upper()
    return int(_STATUS_PRIORITY.get(key, 4))


def _is_rejected_like(status: str | None) -> bool:
    return _status_priority(status) >= _STATUS_PRIORITY["REJECTED"]


def _prefer_non_rejected_candidates(plans: list[PlanRecord]) -> list[PlanRecord]:
    preferred = [p for p in plans if not _is_rejected_like(getattr(p, "status", ""))]
    return preferred if preferred else plans


def _align_gate_uncertainty_with_validator(
    robust_cfg: dict[str, Any],
    uncertainty_cfg: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(robust_cfg, dict):
        return {}
    if not isinstance(uncertainty_cfg, dict):
        return dict(robust_cfg)

    out = dict(robust_cfg)
    gate_obj = out.get("gate_objective", {}) if isinstance(out.get("gate_objective", {}), dict) else {}
    gate_obj = dict(gate_obj)
    gate_unc = gate_obj.get("uncertainty", {}) if isinstance(gate_obj.get("uncertainty", {}), dict) else {}
    conformal_cfg = uncertainty_cfg.get("conformal", {}) if isinstance(uncertainty_cfg.get("conformal", {}), dict) else {}

    aligned_unc = {
        "method": str(uncertainty_cfg.get("primary_method", gate_unc.get("method", "bootstrap"))),
        "bootstrap_b": int(gate_unc.get("bootstrap_b", 300)),
        "sigma": float(uncertainty_cfg.get("bootstrap_sigma", gate_unc.get("sigma", 0.03))),
        "conformal_residual_quantile": float(
            conformal_cfg.get("residual_quantile", gate_unc.get("conformal_residual_quantile", 0.06))
        ),
        "conformal_min_width": float(conformal_cfg.get("min_width", gate_unc.get("conformal_min_width", 0.005))),
        "calibration_artifact_path": str(
            gate_unc.get("calibration_artifact_path")
            or conformal_cfg.get("calibration_artifact_path")
            or ""
        ),
        "adaptive_by_score": bool(conformal_cfg.get("adaptive_by_score", gate_unc.get("adaptive_by_score", False))),
        "adaptive_mode": str(conformal_cfg.get("adaptive_mode", gate_unc.get("adaptive_mode", "cap"))),
        "adaptive_blend": float(conformal_cfg.get("adaptive_blend", gate_unc.get("adaptive_blend", 1.0))),
        "adaptive_gap_weight": float(
            conformal_cfg.get("adaptive_gap_weight", gate_unc.get("adaptive_gap_weight", 0.0))
        ),
        "max_width": (
            float(conformal_cfg.get("max_width"))
            if conformal_cfg.get("max_width") is not None
            else (float(gate_unc.get("max_width")) if gate_unc.get("max_width") is not None else None)
        ),
        "profiles": (
            dict(uncertainty_cfg.get("profiles", {}))
            if isinstance(uncertainty_cfg.get("profiles", {}), dict)
            else {}
        ),
        "reliability_gate_mode": str(
            uncertainty_cfg.get("reliability_gate_mode", gate_unc.get("reliability_gate_mode", "hard"))
        ),
        "reliability_soft_weight": float(
            uncertainty_cfg.get("reliability_soft_weight", gate_unc.get("reliability_soft_weight", 0.5))
        ),
        "reliability_soft_scale": float(
            uncertainty_cfg.get("reliability_soft_scale", gate_unc.get("reliability_soft_scale", 0.02))
        ),
        "reliability_profiles": (
            dict(uncertainty_cfg.get("reliability_profiles", {}))
            if isinstance(uncertainty_cfg.get("reliability_profiles", {}), dict)
            else {}
        ),
    }
    gate_obj["uncertainty"] = aligned_unc
    out["gate_objective"] = gate_obj
    return out


def _local_reason_candidates(
    *,
    model,
    row: pd.Series,
    feature_cols: list[str],
    actionable: list[str],
    topk: int,
    shap_cfg: dict[str, Any],
    prefer_fast: bool = False,
    background_df: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    actionable_set = set(actionable)
    topk = max(1, int(topk))
    x_row = row[feature_cols]
    values = x_row.astype(float).to_numpy(dtype=float)

    if bool(shap_cfg.get("batch_use_model_coef_proxy", True)):
        importance = _extract_model_importance_vector(model, feature_cols)
        if importance is not None:
            weighted: list[dict[str, Any]] = []
            for feat, imp, val in zip(feature_cols, importance, values):
                if feat not in actionable_set:
                    continue
                weighted.append(
                    {
                        "feature": str(feat),
                        "abs_contribution": float(abs(float(imp) * float(val))),
                    }
                )
            weighted.sort(key=lambda t: float(t.get("abs_contribution", 0.0)), reverse=True)
            if weighted:
                return weighted[:topk]

    if prefer_fast:
        fallback_weighted = [
            {
                "feature": str(feat),
                "abs_contribution": float(abs(float(val))),
            }
            for feat, val in zip(feature_cols, values)
            if feat in actionable_set
        ]
        fallback_weighted.sort(key=lambda t: float(t.get("abs_contribution", 0.0)), reverse=True)
        if fallback_weighted:
            return fallback_weighted[:topk]

    reasons: list[dict] = []
    try:
        reasons = compute_local_topk_reasons(
            model,
            x_row=x_row,
            top_k=max(topk, int(shap_cfg.get("topk_features", topk))),
            background_df=background_df,
        )
    except Exception:
        reasons = []

    weighted = []
    for r in reasons:
        feat = str(r.get("feature", "")).strip()
        if not feat or feat not in actionable_set:
            continue
        weighted.append(
            {
                "feature": feat,
                "abs_contribution": float(r.get("abs_contribution", abs(float(r.get("contribution", 0.0))))),
            }
        )
    weighted.sort(key=lambda t: float(t.get("abs_contribution", 0.0)), reverse=True)
    return weighted[:topk]


def _apply_phase1_feature_boost(
    *,
    candidate_features: list[dict[str, Any]] | list[str],
    rec_cfg: dict[str, Any],
    denied_mode: bool,
    risk_band: str,
    actionable: list[str],
) -> list[dict[str, Any]]:
    cfg = (
        rec_cfg.get("phase1_fast_track", {})
        if isinstance(rec_cfg.get("phase1_fast_track", {}), dict)
        else {}
    )
    if not bool(cfg.get("enabled", False)):
        return [
            {"feature": str(x), "abs_contribution": 0.0}
            if isinstance(x, str)
            else {"feature": str(x.get("feature", "")), "abs_contribution": float(x.get("abs_contribution", 0.0))}
            for x in candidate_features
        ]
    if bool(cfg.get("denied_only", True)) and not bool(denied_mode):
        return [
            {"feature": str(x), "abs_contribution": 0.0}
            if isinstance(x, str)
            else {"feature": str(x.get("feature", "")), "abs_contribution": float(x.get("abs_contribution", 0.0))}
            for x in candidate_features
        ]
    if bool(cfg.get("high_risk_only", True)) and str(risk_band).strip().lower() != "high":
        return [
            {"feature": str(x), "abs_contribution": 0.0}
            if isinstance(x, str)
            else {"feature": str(x.get("feature", "")), "abs_contribution": float(x.get("abs_contribution", 0.0))}
            for x in candidate_features
        ]

    prioritized_raw = cfg.get("prioritized_features", [])
    prioritized = [str(v).strip() for v in prioritized_raw if str(v).strip()] if isinstance(prioritized_raw, list) else []
    if not prioritized:
        return [
            {"feature": str(x), "abs_contribution": 0.0}
            if isinstance(x, str)
            else {"feature": str(x.get("feature", "")), "abs_contribution": float(x.get("abs_contribution", 0.0))}
            for x in candidate_features
        ]
    prioritized_set = set(prioritized)
    actionable_set = set(actionable)
    boost = max(1.0, float(cfg.get("feature_boost_multiplier", 1.35)))
    score_floor = max(0.0, float(cfg.get("min_score_floor", 1.0e-9)))
    append_missing = bool(cfg.get("append_missing_prioritized", True))
    max_append = max(0, int(cfg.get("max_append", 2)))

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in candidate_features:
        if isinstance(item, str):
            feat = str(item).strip()
            score = 0.0
        elif isinstance(item, dict):
            feat = str(item.get("feature", "")).strip()
            score = float(item.get("abs_contribution", item.get("weight", 0.0)) or 0.0)
        else:
            continue
        if not feat or feat in seen or feat not in actionable_set:
            continue
        seen.add(feat)
        if feat in prioritized_set:
            score = max(score_floor, score) * boost
        normalized.append({"feature": feat, "abs_contribution": float(score)})

    if append_missing and max_append > 0:
        appended = 0
        for feat in prioritized:
            if appended >= max_append:
                break
            if feat in seen or feat not in actionable_set:
                continue
            normalized.append({"feature": feat, "abs_contribution": float(score_floor * boost)})
            seen.add(feat)
            appended += 1

    normalized.sort(key=lambda t: float(t.get("abs_contribution", 0.0)), reverse=True)
    return normalized


def _normalize_risk_band_reservation(raw: Any) -> dict[str, float]:
    default = {"high": 0.5, "mid": 0.25, "near": 0.25}
    if not isinstance(raw, dict):
        return default
    out = {
        "high": max(0.0, float(raw.get("high", default["high"]))),
        "mid": max(0.0, float(raw.get("mid", default["mid"]))),
        "near": max(0.0, float(raw.get("near", default["near"]))),
    }
    s = float(out["high"] + out["mid"] + out["near"])
    if s <= 0.0:
        return default
    return {k: float(v / s) for k, v in out.items()}


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


def _risk_band_from_pd(base_pd: float, tau: float, segment_caps_cfg: dict[str, Any]) -> str:
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
    segment_caps_cfg: dict[str, Any],
    income_edges: tuple[float, float, float],
) -> dict[str, Any]:
    annual_inc = _safe_float(row.get("annual_inc"), 0.0)
    income_band = _income_band_from_value(annual_inc, income_edges)
    risk_band = _risk_band_from_pd(base_pd, tau, segment_caps_cfg)
    pd_distance_to_tau = max(0.0, float(base_pd) - float(tau))

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
        "denied_mode": bool(denied_mode),
        "segment_caps_applied": bool(can_apply and abs(m_total - 1.0) > 1e-12),
        "cap_multiplier_income": float(m_income),
        "cap_multiplier_risk": float(m_risk),
        "cap_multiplier": float(m_total),
        "cap_multiplier_min": float(min_mult),
        "cap_multiplier_max": float(max_mult),
        "feature_cap_multipliers": feature_mults,
        "pd_distance_to_tau": float(pd_distance_to_tau),
    }


def _plan_cost(plan: PlanRecord) -> float:
    return float(sum(float(a.estimated_cost_usd) for a in plan.actions))


def _plan_proximity_l1(plan: PlanRecord) -> float:
    return float(sum(abs(float(a.delta)) for a in plan.actions))


def _phase_id_for_month(month: int) -> str:
    return phase_id_for_month(month)


def _phase_title(phase_id: str) -> str:
    return phase_title(phase_id)


def _apply_plan_until_month(
    row: pd.Series,
    plan: PlanRecord,
    *,
    month: int,
) -> pd.Series:
    return apply_plan_until_month(row, plan, month=month)


def _predict_plan_pd_at_month(
    *,
    row: pd.Series,
    plan: PlanRecord,
    month: int,
    model: Any,
    calibrator: Any,
    feature_cols: list[str],
) -> float:
    return predict_plan_pd_at_month(
        row=row,
        plan=plan,
        month=month,
        model=model,
        calibrator=calibrator,
        feature_cols=feature_cols,
    )


def _scheduled_actions_by_week(plan: PlanRecord) -> dict[int, int]:
    scheduled: dict[int, int] = {}
    for action in list(plan.actions):
        week = max(
            1,
            _safe_int(
                getattr(action, "week_start", None),
                _safe_int(max(1, getattr(action, "time_months", 1)) * 4 - 3, 1),
            ),
        )
        scheduled[week] = int(scheduled.get(week, 0) + 1)
    return scheduled


def _plan_trajectory_metrics(
    *,
    row: pd.Series,
    plan: PlanRecord,
    base_pd: float,
    tau: float,
    model: Any,
    calibrator: Any,
    feature_cols: list[str],
    partial_progress_min_pd_delta: float = 0.05,
    random_state: int = 42,
    max_weekly_actions: int = 3,
    min_robust_margin: float | None = None,
) -> dict[str, Any]:
    action_count = max(0, int(len(plan.actions)))
    if action_count <= 0:
        return {
            "trajectory_pd_4w": float(base_pd),
            "trajectory_pd_12w": float(base_pd),
            "trajectory_pd_24w": float(base_pd),
            "trajectory_gate_pass_4w": 0,
            "trajectory_gate_pass_12w": 0,
            "trajectory_gate_pass_24w": 0,
            "trajectory_pd_delta_24w": 0.0,
            "trajectory_partial_progress": 0,
            "trajectory_time_to_gate_pass_days": np.nan,
            "trajectory_phase_1_action_count": 0,
            "trajectory_phase_2_action_count": 0,
            "trajectory_phase_3_action_count": 0,
            "trajectory_status": "degraded",
            "trajectory_current_phase": "phase_1_stabilize",
            "trajectory_next_review_week": 4,
            "trajectory_phase_transition_reason": "no_actions",
            "trajectory_replanned_from_phase": "",
            "trajectory_soft_regression_penalty": 0.0,
        }

    raw_plan_probability = getattr(plan, "plan_execution_probability", None)
    plan_execution_probability = (
        _safe_float(raw_plan_probability, 1.0) if raw_plan_probability is not None else 1.0
    )
    nominal_pd_improvement = max(
        0.0,
        _safe_float(
            getattr(plan, "nominal_pd_improvement", None),
            max(0.0, float(base_pd) - _safe_float(getattr(plan, "predicted_pd", base_pd), float(base_pd))),
        ),
    )
    loop_df = run_weekly_coaching_loop(
        base_pd=float(base_pd),
        tau=float(tau),
        weeks=24,
        macro_shock_week=0,
        plan_action_count=action_count,
        target_pd=_safe_float(getattr(plan, "predicted_pd", tau), float(tau)),
        action_dropout_prob=min(max(1.0 - float(plan_execution_probability), 0.02), 0.95),
        action_effect_per_step=max(0.002, nominal_pd_improvement / max(1, action_count)),
        max_weekly_actions=max(1, int(max_weekly_actions)),
        random_state=int(random_state),
        min_robust_margin=min_robust_margin,
        scheduled_actions_by_week=_scheduled_actions_by_week(plan),
        review_weeks=(4, 12, 24),
        financial_inertia=0.18,
    )

    def _checkpoint_row(week: int) -> pd.Series:
        match = loop_df[pd.to_numeric(loop_df["week"], errors="coerce").fillna(0).astype(int) == int(week)]
        if not match.empty:
            return match.iloc[-1]
        return loop_df.iloc[-1]

    cp_4w = _checkpoint_row(4)
    cp_12w = _checkpoint_row(12)
    cp_24w = _checkpoint_row(24)
    pd_4w = float(cp_4w.get("predicted_pd", base_pd))
    pd_12w = float(cp_12w.get("predicted_pd", base_pd))
    pd_24w = float(cp_24w.get("predicted_pd", base_pd))
    pass_4w = int(pd_4w <= float(tau))
    pass_12w = int(pd_12w <= float(tau))
    pass_24w = int(pd_24w <= float(tau))
    time_to_pass_days = np.nan
    if pass_4w == 1:
        time_to_pass_days = 28.0
    elif pass_12w == 1:
        time_to_pass_days = 84.0
    elif pass_24w == 1:
        time_to_pass_days = 168.0
    pd_delta_24w = float(max(0.0, float(base_pd) - float(pd_24w)))
    min_delta = max(0.0, float(partial_progress_min_pd_delta))
    partial_progress = int(pd_delta_24w >= min_delta)
    phase_1_count = 0
    phase_2_count = 0
    phase_3_count = 0
    for a in plan.actions:
        m = max(1, _safe_int(getattr(a, "time_months", 1), 1))
        pid = _phase_id_for_month(m)
        if pid == "phase_1_stabilize":
            phase_1_count += 1
        elif pid == "phase_2_build":
            phase_2_count += 1
        else:
            phase_3_count += 1
    regression_tolerance = 0.01
    soft_regression_penalty = max(0.0, pd_12w - (pd_4w + regression_tolerance)) + max(
        0.0,
        pd_24w - (pd_12w + regression_tolerance),
    )
    trajectory_status = str(cp_24w.get("trajectory_status", "on_track") or "on_track")
    current_phase = str(cp_24w.get("current_phase", "phase_3_optimize") or "phase_3_optimize")
    next_review_week = int(_safe_int(cp_24w.get("next_review_week", 24), 24))
    phase_transition_reason = str(cp_24w.get("phase_transition_reason", "") or "")
    replanned_from_phase = str(cp_24w.get("replanned_from_phase", "") or "")
    return {
        "trajectory_pd_4w": float(pd_4w),
        "trajectory_pd_12w": float(pd_12w),
        "trajectory_pd_24w": float(pd_24w),
        "trajectory_gate_pass_4w": int(pass_4w),
        "trajectory_gate_pass_12w": int(pass_12w),
        "trajectory_gate_pass_24w": int(pass_24w),
        "trajectory_pd_delta_24w": float(pd_delta_24w),
        "trajectory_partial_progress": int(partial_progress),
        "trajectory_time_to_gate_pass_days": float(time_to_pass_days) if not pd.isna(time_to_pass_days) else np.nan,
        "trajectory_phase_1_action_count": int(phase_1_count),
        "trajectory_phase_2_action_count": int(phase_2_count),
        "trajectory_phase_3_action_count": int(phase_3_count),
        "trajectory_status": trajectory_status,
        "trajectory_current_phase": current_phase,
        "trajectory_next_review_week": int(next_review_week),
        "trajectory_phase_transition_reason": phase_transition_reason,
        "trajectory_replanned_from_phase": replanned_from_phase,
        "trajectory_soft_regression_penalty": float(soft_regression_penalty),
    }


def _simulate_plan_execution_behavior(
    *,
    row: pd.Series,
    plan: PlanRecord,
    base_pd: float,
    tau: float,
    model: Any,
    calibrator: Any,
    feature_cols: list[str],
    random_state: int,
    partial_progress_min_pd_delta: float,
    max_weekly_actions: int = 3,
    min_robust_margin: float | None = None,
) -> dict[str, Any]:
    action_count = max(0, int(len(plan.actions)))
    plan_execution_probability = _safe_float(getattr(plan, "plan_execution_probability", 0.0), 0.0)
    nominal_pd_improvement = max(
        0.0,
        _safe_float(getattr(plan, "nominal_pd_improvement", 0.0), 0.0),
    )
    expected_pd_improvement = max(
        0.0,
        _safe_float(getattr(plan, "expected_pd_improvement", 0.0), 0.0),
    )
    if action_count <= 0:
        return {
            "execution_rate": 0.0,
            "execution_scenario": "failed_execution",
            "mixed_execution": 0,
            "failed_execution": 1,
            "partial_execution": 1,
            "expected_partial_progress": 0,
            "final_simulated_pd": float(base_pd),
            "missed_action": 0,
            "missed_actions_streak": 0,
            "trajectory_status": "degraded",
            "current_phase": "phase_1_stabilize",
            "next_review_week": 4,
            "phase_transition_reason": "no_actions",
            "replanned_from_phase": "",
        }

    weeks = max(4, min(24, int(getattr(plan, "horizon_months", 6) or 6) * 4))
    action_dropout_prob = _clamp(1.0 - float(plan_execution_probability), lo=0.02, hi=0.95)
    action_effect_per_step = max(0.002, nominal_pd_improvement / max(1, action_count))
    loop_df = run_weekly_coaching_loop(
        base_pd=float(base_pd),
        tau=float(tau),
        weeks=weeks,
        plan_action_count=action_count,
        target_pd=_safe_float(getattr(plan, "predicted_pd", tau), float(tau)),
        action_dropout_prob=action_dropout_prob,
        action_effect_per_step=action_effect_per_step,
        max_weekly_actions=max(1, int(max_weekly_actions)),
        random_state=int(random_state),
        min_robust_margin=min_robust_margin,
        scheduled_actions_by_week=_scheduled_actions_by_week(plan),
        review_weeks=(4, 12, 24),
        financial_inertia=0.18,
    )
    if loop_df.empty:
        return {
            "execution_rate": 0.0,
            "execution_scenario": "failed_execution",
            "mixed_execution": 0,
            "failed_execution": 1,
            "partial_execution": 1,
            "expected_partial_progress": 0,
            "final_simulated_pd": float(base_pd),
            "missed_action": 0,
            "missed_actions_streak": 0,
            "trajectory_status": "degraded",
            "current_phase": "phase_1_stabilize",
            "next_review_week": 4,
            "phase_transition_reason": "empty_simulation",
            "replanned_from_phase": "",
        }

    mean_execution_rate = float(pd.to_numeric(loop_df["execution_rate"], errors="coerce").fillna(0.0).mean())
    execution_scenario = classify_execution_scenario(mean_execution_rate)
    final_pd = float(pd.to_numeric(loop_df["predicted_pd"], errors="coerce").fillna(base_pd).iloc[-1])
    expected_partial_progress = int(max(0.0, float(base_pd) - final_pd) >= float(partial_progress_min_pd_delta))
    return {
        "execution_rate": float(mean_execution_rate),
        "execution_scenario": str(execution_scenario),
        "mixed_execution": int(execution_scenario == "mixed_execution"),
        "failed_execution": int(execution_scenario == "failed_execution"),
        "partial_execution": int(execution_scenario != "full_execution"),
        "expected_partial_progress": int(expected_partial_progress),
        "final_simulated_pd": float(final_pd),
        "missed_action": int(pd.to_numeric(loop_df["missed_action"], errors="coerce").fillna(0.0).iloc[-1]),
        "missed_actions_streak": int(
            pd.to_numeric(loop_df["missed_actions_streak"], errors="coerce").fillna(0.0).max()
        ),
        "trajectory_status": str(loop_df["trajectory_status"].iloc[-1]),
        "current_phase": str(loop_df["current_phase"].iloc[-1]),
        "next_review_week": int(pd.to_numeric(loop_df["next_review_week"], errors="coerce").fillna(24).iloc[-1]),
        "phase_transition_reason": str(loop_df["phase_transition_reason"].iloc[-1]),
        "replanned_from_phase": str(loop_df["replanned_from_phase"].iloc[-1]),
    }


def _build_behavior_aware_artifacts(batch_df: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    metric_fields = (
        "mean_plan_execution_probability",
        "nominal_pd_improvement",
        "expected_pd_improvement",
        "execution_weighted_gap_vs_nominal",
        "high_uplift_low_follow_through_rate",
        "partial_execution_rate",
        "failed_execution_rate",
        "mixed_execution_rate",
        "expected_partial_progress_rate",
    )
    empty_summary = {
        "canonical_population": "denied",
        "secondary_population": "high_risk_denied",
        "canonical_metrics": {field: 0.0 for field in metric_fields},
        "secondary_metrics": {field: 0.0 for field in metric_fields},
        "supporting_artifacts": {
            "execution_probability_breakdown_csv": "tables/execution_probability_breakdown.csv",
            "partial_execution_breakdown_csv": "tables/partial_execution_breakdown.csv",
        },
    }
    if batch_df.empty:
        return (
            empty_summary,
            pd.DataFrame(
                columns=[
                    "population",
                    "risk_band",
                    "best_source",
                    "count",
                    "mean_plan_execution_probability",
                    "nominal_pd_improvement",
                    "expected_pd_improvement",
                    "execution_weighted_gap_vs_nominal",
                    "high_uplift_low_follow_through_rate",
                ]
            ),
            pd.DataFrame(
                columns=[
                    "population",
                    "risk_band",
                    "execution_scenario",
                    "count",
                    "share",
                    "mean_execution_rate",
                    "expected_partial_progress_rate",
                    "max_missed_actions_streak",
                ]
            ),
        )

    denied_rows = batch_df[batch_df["denied_base"].astype(int) == 1].copy()
    high_risk_denied_rows = batch_df[
        (batch_df["denied_base"].astype(int) == 1)
        & (batch_df["risk_band"].astype(str).str.lower() == "high")
    ].copy()

    def _with_behavior_flags(frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return frame.copy()
        out = frame.copy()
        nominal = pd.to_numeric(out["best_nominal_pd_improvement"], errors="coerce").fillna(0.0)
        expected = pd.to_numeric(out["best_expected_pd_improvement"], errors="coerce").fillna(0.0)
        execution_probability = pd.to_numeric(out["best_plan_execution_probability"], errors="coerce").fillna(0.0)
        out["execution_weighted_gap_vs_nominal"] = (nominal - expected).clip(lower=0.0)
        out["high_uplift_low_follow_through"] = (
            (nominal >= 0.05)
            & ((execution_probability < 0.45) | (expected <= (0.50 * nominal)))
        ).astype(float)
        return out

    denied_rows = _with_behavior_flags(denied_rows)
    high_risk_denied_rows = _with_behavior_flags(high_risk_denied_rows)

    def _metrics(frame: pd.DataFrame) -> dict[str, float]:
        if frame.empty:
            return {field: 0.0 for field in metric_fields}
        return {
            "mean_plan_execution_probability": _round_metric(frame["best_plan_execution_probability"].astype(float).mean()),
            "nominal_pd_improvement": _round_metric(frame["best_nominal_pd_improvement"].astype(float).mean()),
            "expected_pd_improvement": _round_metric(frame["best_expected_pd_improvement"].astype(float).mean()),
            "execution_weighted_gap_vs_nominal": _round_metric(
                frame["execution_weighted_gap_vs_nominal"].astype(float).mean()
            ),
            "high_uplift_low_follow_through_rate": _round_metric(
                frame["high_uplift_low_follow_through"].astype(float).mean()
            ),
            "partial_execution_rate": _round_metric(frame["best_partial_execution"].astype(float).mean()),
            "failed_execution_rate": _round_metric(frame["best_failed_execution"].astype(float).mean()),
            "mixed_execution_rate": _round_metric(frame["best_mixed_execution"].astype(float).mean()),
            "expected_partial_progress_rate": _round_metric(frame["best_expected_partial_progress"].astype(float).mean()),
        }

    execution_probability_breakdown_rows: list[dict[str, Any]] = []
    partial_execution_breakdown_rows: list[dict[str, Any]] = []
    for population, frame in (("denied", denied_rows), ("high_risk_denied", high_risk_denied_rows)):
        if frame.empty:
            continue
        grouped = (
            frame.groupby(["risk_band", "best_source"], dropna=False)
            .agg(
                count=("customer_id", "size"),
                mean_plan_execution_probability=("best_plan_execution_probability", "mean"),
                nominal_pd_improvement=("best_nominal_pd_improvement", "mean"),
                expected_pd_improvement=("best_expected_pd_improvement", "mean"),
                execution_weighted_gap_vs_nominal=("execution_weighted_gap_vs_nominal", "mean"),
                high_uplift_low_follow_through_rate=("high_uplift_low_follow_through", "mean"),
            )
            .reset_index()
        )
        grouped["population"] = population
        execution_probability_breakdown_rows.extend(grouped.to_dict(orient="records"))

        scenario_rollup = (
            frame.groupby(["risk_band", "best_execution_scenario"], dropna=False)
            .agg(
                count=("customer_id", "size"),
                mean_execution_rate=("best_execution_rate", "mean"),
                expected_partial_progress_rate=("best_expected_partial_progress", "mean"),
                max_missed_actions_streak=("best_missed_actions_streak", "max"),
            )
            .reset_index()
            .rename(columns={"best_execution_scenario": "execution_scenario"})
        )
        total = max(1, int(frame.shape[0]))
        scenario_rollup["share"] = scenario_rollup["count"].astype(float) / float(total)
        scenario_rollup["population"] = population
        partial_execution_breakdown_rows.extend(scenario_rollup.to_dict(orient="records"))

    execution_probability_breakdown = (
        pd.DataFrame(execution_probability_breakdown_rows)
        if execution_probability_breakdown_rows
        else pd.DataFrame(
            columns=[
                "population",
                "risk_band",
                "best_source",
                "count",
                "mean_plan_execution_probability",
                "nominal_pd_improvement",
                "expected_pd_improvement",
                "execution_weighted_gap_vs_nominal",
                "high_uplift_low_follow_through_rate",
            ]
        )
    )
    partial_execution_breakdown = (
        pd.DataFrame(partial_execution_breakdown_rows)
        if partial_execution_breakdown_rows
        else pd.DataFrame(
            columns=[
                "population",
                "risk_band",
                "execution_scenario",
                "count",
                "share",
                "mean_execution_rate",
                "expected_partial_progress_rate",
                "max_missed_actions_streak",
            ]
        )
    )

    summary = {
        "canonical_population": "denied",
        "secondary_population": "high_risk_denied",
        "canonical_metrics": _metrics(denied_rows),
        "secondary_metrics": _metrics(high_risk_denied_rows),
        "primary_segment_lens": "risk_band",
        "primary_comparison": {
            "nominal_metric": "nominal_pd_improvement",
            "execution_aware_metric": "expected_pd_improvement",
            "gap_metric": "execution_weighted_gap_vs_nominal",
            "core_question": "how much of the plan is realistically executable",
            "risk_sentence": "high uplift but low follow-through",
        },
        "supporting_artifacts": {
            "execution_probability_breakdown_csv": "tables/execution_probability_breakdown.csv",
            "partial_execution_breakdown_csv": "tables/partial_execution_breakdown.csv",
        },
    }
    return summary, execution_probability_breakdown, partial_execution_breakdown


def _build_offer_optimization_artifacts(
    batch_df: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_fields = (
        "offer_plan_rate",
        "rankable_offer_rate",
        "offer_acceptance_probability_mean",
        "combined_plan_realization_probability_mean",
        "expected_recovery_proxy",
        "approval_rate_proxy_delta",
        "default_rate_90d_proxy_delta",
        "avg_margin_90d_proxy_delta",
        "governance_safe_offer_rate",
        "dominant_offer_type",
    )
    empty_summary = {
        "canonical_population": "denied",
        "canonical_metrics": {
            "offer_plan_rate": 0.0,
            "rankable_offer_rate": 0.0,
            "offer_acceptance_probability_mean": 0.0,
            "combined_plan_realization_probability_mean": 0.0,
            "expected_recovery_proxy": 0.0,
            "approval_rate_proxy_delta": 0.0,
            "default_rate_90d_proxy_delta": 0.0,
            "avg_margin_90d_proxy_delta": 0.0,
            "governance_safe_offer_rate": 0.0,
            "dominant_offer_type": "",
        },
        "supporting_artifacts": {
            "offer_type_breakdown_csv": "tables/offer_type_breakdown.csv",
            "offer_policy_arm_breakdown_csv": "tables/offer_policy_arm_breakdown.csv",
            "offer_acceptance_breakdown_csv": "tables/offer_acceptance_breakdown.csv",
            "offer_proxy_impact_breakdown_csv": "tables/offer_proxy_impact_breakdown.csv",
        },
    }
    if batch_df.empty:
        empty_type = pd.DataFrame(
            columns=["population", "risk_band", "offer_type", "count", "share", "mean_expected_recovery_proxy"]
        )
        empty_policy = pd.DataFrame(
            columns=[
                "population",
                "risk_band",
                "offer_policy_arm",
                "offer_family",
                "offer_scoring_profile",
                "term_generation_rule",
                "count",
                "share",
            ]
        )
        empty_acceptance = pd.DataFrame(
            columns=[
                "population",
                "risk_band",
                "income_band",
                "offer_type",
                "count",
                "mean_offer_acceptance_probability",
                "mean_combined_plan_realization_probability",
            ]
        )
        empty_proxy = pd.DataFrame(
            columns=[
                "population",
                "offer_type",
                "offer_policy_arm",
                "count",
                "approval_rate_proxy_delta",
                "default_rate_90d_proxy_delta",
                "avg_margin_90d_proxy_delta",
                "expected_recovery_proxy",
                "governance_safe_offer_rate",
            ]
        )
        return empty_summary, empty_type, empty_policy, empty_acceptance, empty_proxy

    denied_rows = batch_df[batch_df["denied_base"].astype(int) == 1].copy()

    if denied_rows.empty:
        empty_type = pd.DataFrame(
            columns=["population", "risk_band", "offer_type", "count", "share", "mean_expected_recovery_proxy"]
        )
        empty_policy = pd.DataFrame(
            columns=[
                "population",
                "risk_band",
                "offer_policy_arm",
                "offer_family",
                "offer_scoring_profile",
                "term_generation_rule",
                "count",
                "share",
            ]
        )
        empty_acceptance = pd.DataFrame(
            columns=[
                "population",
                "risk_band",
                "income_band",
                "offer_type",
                "count",
                "mean_offer_acceptance_probability",
                "mean_combined_plan_realization_probability",
            ]
        )
        empty_proxy = pd.DataFrame(
            columns=[
                "population",
                "offer_type",
                "offer_policy_arm",
                "count",
                "approval_rate_proxy_delta",
                "default_rate_90d_proxy_delta",
                "avg_margin_90d_proxy_delta",
                "expected_recovery_proxy",
                "governance_safe_offer_rate",
            ]
        )
        return empty_summary, empty_type, empty_policy, empty_acceptance, empty_proxy

    offer_rows = denied_rows[denied_rows["best_offer_plan"].astype(int) == 1].copy()
    rankable_rows = denied_rows[denied_rows["best_rankable_offer"].astype(int) == 1].copy()

    dominant_offer_type = ""
    if not offer_rows.empty:
        dominant = offer_rows["best_offer_type"].fillna("").astype(str)
        dominant = dominant[dominant != ""]
        if not dominant.empty:
            dominant_offer_type = str(dominant.value_counts().idxmax())

    summary = {
        "canonical_population": "denied",
        "canonical_metrics": {
            "offer_plan_rate": _round_metric(denied_rows["best_offer_plan"].astype(float).mean()),
            "rankable_offer_rate": _round_metric(denied_rows["best_rankable_offer"].astype(float).mean()),
            "offer_acceptance_probability_mean": _round_metric(
                rankable_rows["best_offer_acceptance_probability"].astype(float).mean() if not rankable_rows.empty else 0.0
            ),
            "combined_plan_realization_probability_mean": _round_metric(
                rankable_rows["best_combined_plan_realization_probability"].astype(float).mean()
                if not rankable_rows.empty
                else 0.0
            ),
            "expected_recovery_proxy": _round_metric(
                rankable_rows["best_expected_recovery_proxy"].astype(float).mean() if not rankable_rows.empty else 0.0
            ),
            "approval_rate_proxy_delta": _round_metric(
                rankable_rows["best_approval_rate_proxy_delta"].astype(float).mean() if not rankable_rows.empty else 0.0
            ),
            "default_rate_90d_proxy_delta": _round_metric(
                rankable_rows["best_default_rate_90d_proxy_delta"].astype(float).mean() if not rankable_rows.empty else 0.0
            ),
            "avg_margin_90d_proxy_delta": _round_metric(
                rankable_rows["best_avg_margin_90d_proxy_delta"].astype(float).mean() if not rankable_rows.empty else 0.0
            ),
            "governance_safe_offer_rate": _round_metric(
                rankable_rows["best_governance_safe_offer"].astype(float).mean() if not rankable_rows.empty else 0.0
            ),
            "dominant_offer_type": dominant_offer_type,
        },
        "supporting_artifacts": {
            "offer_type_breakdown_csv": "tables/offer_type_breakdown.csv",
            "offer_policy_arm_breakdown_csv": "tables/offer_policy_arm_breakdown.csv",
            "offer_acceptance_breakdown_csv": "tables/offer_acceptance_breakdown.csv",
            "offer_proxy_impact_breakdown_csv": "tables/offer_proxy_impact_breakdown.csv",
        },
    }

    if not offer_rows.empty:
        offer_type_breakdown = (
            offer_rows.groupby(["risk_band", "best_offer_type"], dropna=False)
            .agg(
                count=("customer_id", "size"),
                mean_expected_recovery_proxy=("best_expected_recovery_proxy", "mean"),
            )
            .reset_index()
            .rename(columns={"best_offer_type": "offer_type"})
        )
        offer_type_breakdown["share"] = offer_type_breakdown["count"].astype(float) / float(max(1, len(offer_rows)))
        offer_type_breakdown["population"] = "denied"
    else:
        offer_type_breakdown = pd.DataFrame(
            columns=["population", "risk_band", "offer_type", "count", "share", "mean_expected_recovery_proxy"]
        )

    if not offer_rows.empty:
        offer_policy_arm_breakdown = (
            offer_rows.groupby(
                ["risk_band", "best_offer_policy_arm", "best_offer_family", "best_offer_scoring_profile", "best_term_generation_rule"],
                dropna=False,
            )
            .agg(count=("customer_id", "size"))
            .reset_index()
            .rename(
                columns={
                    "best_offer_policy_arm": "offer_policy_arm",
                    "best_offer_family": "offer_family",
                    "best_offer_scoring_profile": "offer_scoring_profile",
                    "best_term_generation_rule": "term_generation_rule",
                }
            )
        )
        offer_policy_arm_breakdown["share"] = (
            offer_policy_arm_breakdown["count"].astype(float) / float(max(1, len(offer_rows)))
        )
        offer_policy_arm_breakdown["population"] = "denied"
    else:
        offer_policy_arm_breakdown = pd.DataFrame(
            columns=[
                "population",
                "risk_band",
                "offer_policy_arm",
                "offer_family",
                "offer_scoring_profile",
                "term_generation_rule",
                "count",
                "share",
            ]
        )

    if not rankable_rows.empty:
        offer_acceptance_breakdown = (
            rankable_rows.groupby(["risk_band", "income_band", "best_offer_type"], dropna=False)
            .agg(
                count=("customer_id", "size"),
                mean_offer_acceptance_probability=("best_offer_acceptance_probability", "mean"),
                mean_combined_plan_realization_probability=("best_combined_plan_realization_probability", "mean"),
            )
            .reset_index()
            .rename(columns={"best_offer_type": "offer_type"})
        )
        offer_acceptance_breakdown["population"] = "denied"
    else:
        offer_acceptance_breakdown = pd.DataFrame(
            columns=[
                "population",
                "risk_band",
                "income_band",
                "offer_type",
                "count",
                "mean_offer_acceptance_probability",
                "mean_combined_plan_realization_probability",
            ]
        )

    if not rankable_rows.empty:
        offer_proxy_impact_breakdown = (
            rankable_rows.groupby(["best_offer_type", "best_offer_policy_arm"], dropna=False)
            .agg(
                count=("customer_id", "size"),
                approval_rate_proxy_delta=("best_approval_rate_proxy_delta", "mean"),
                default_rate_90d_proxy_delta=("best_default_rate_90d_proxy_delta", "mean"),
                avg_margin_90d_proxy_delta=("best_avg_margin_90d_proxy_delta", "mean"),
                expected_recovery_proxy=("best_expected_recovery_proxy", "mean"),
                governance_safe_offer_rate=("best_governance_safe_offer", "mean"),
            )
            .reset_index()
            .rename(columns={"best_offer_type": "offer_type", "best_offer_policy_arm": "offer_policy_arm"})
        )
        offer_proxy_impact_breakdown["population"] = "denied"
    else:
        offer_proxy_impact_breakdown = pd.DataFrame(
            columns=[
                "population",
                "offer_type",
                "offer_policy_arm",
                "count",
                "approval_rate_proxy_delta",
                "default_rate_90d_proxy_delta",
                "avg_margin_90d_proxy_delta",
                "expected_recovery_proxy",
                "governance_safe_offer_rate",
            ]
        )

    return (
        summary,
        offer_type_breakdown,
        offer_policy_arm_breakdown,
        offer_acceptance_breakdown,
        offer_proxy_impact_breakdown,
    )


def _build_trajectory_artifacts(batch_df: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    metric_fields = (
        "trajectory_gate_pass_rate_4w",
        "trajectory_gate_pass_rate_12w",
        "trajectory_gate_pass_rate_24w",
        "trajectory_partial_progress_rate",
        "trajectory_median_time_to_gate_pass_days",
        "trajectory_soft_regression_penalty_mean",
        "trajectory_on_track_rate",
        "trajectory_needs_replan_rate",
        "trajectory_degraded_rate",
    )
    empty_summary = {
        "canonical_population": "denied",
        "secondary_population": "high_risk_denied",
        "primary_checkpoint_week": 4,
        "checkpoint_priority_order": [4, 12, 24],
        "canonical_metrics": {field: 0.0 for field in metric_fields},
        "secondary_metrics": {field: 0.0 for field in metric_fields},
        "dominant_transition_reason": "",
        "supporting_artifacts": {
            "trajectory_transition_breakdown_csv": "tables/trajectory_transition_breakdown.csv",
            "trajectory_policy_label_breakdown_csv": "tables/trajectory_policy_label_breakdown.csv",
            "trajectory_gate_by_risk_band_csv": "tables/trajectory_gate_by_risk_band.csv",
            "trajectory_gate_by_income_band_csv": "tables/trajectory_gate_by_income_band.csv",
            "trajectory_phase_action_mix_csv": "tables/trajectory_phase_action_mix.csv",
        },
    }
    if batch_df.empty:
        return (
            empty_summary,
            pd.DataFrame(
                columns=[
                    "population",
                    "risk_band",
                    "trajectory_status",
                    "current_phase",
                    "phase_transition_reason",
                    "count",
                    "share",
                    "mean_next_review_week",
                    "mean_soft_regression_penalty",
                ]
            ),
            pd.DataFrame(
                columns=[
                    "population",
                    "risk_band",
                    "trajectory_policy_label",
                    "count",
                    "share",
                    "mean_policy_score",
                ]
            ),
        )

    work = batch_df.copy()
    work["risk_band"] = work.get("risk_band", pd.Series(dtype=object)).fillna("").astype(str)
    work["trajectory_status"] = work.get("trajectory_status", pd.Series(dtype=object)).fillna("degraded").astype(str)
    work["current_phase"] = work.get("trajectory_current_phase", pd.Series(dtype=object)).fillna("").astype(str)
    work["phase_transition_reason"] = (
        work.get("trajectory_phase_transition_reason", pd.Series(dtype=object)).fillna("").astype(str)
    )
    work["trajectory_policy_label"] = (
        work.get("trajectory_policy_label", pd.Series(dtype=object)).fillna("").astype(str)
    )

    def _population_rows(frame: pd.DataFrame, population: str) -> pd.DataFrame:
        rows = frame.copy()
        rows["population"] = population
        return rows

    denied_rows = work[work.get("denied_base", pd.Series(dtype=float)).astype(int) == 1].copy()
    high_risk_denied_rows = denied_rows[denied_rows["risk_band"].str.lower() == "high"].copy()

    def _metrics(rows: pd.DataFrame) -> dict[str, float]:
        if rows.empty:
            return {field: 0.0 for field in metric_fields}
        return {
            "trajectory_gate_pass_rate_4w": _round_metric(rows["trajectory_gate_pass_4w"].astype(float).mean()),
            "trajectory_gate_pass_rate_12w": _round_metric(rows["trajectory_gate_pass_12w"].astype(float).mean()),
            "trajectory_gate_pass_rate_24w": _round_metric(rows["trajectory_gate_pass_24w"].astype(float).mean()),
            "trajectory_partial_progress_rate": _round_metric(rows["trajectory_partial_progress"].astype(float).mean()),
            "trajectory_median_time_to_gate_pass_days": _round_metric(
                pd.to_numeric(rows["trajectory_time_to_gate_pass_days"], errors="coerce").dropna().median()
            ),
            "trajectory_soft_regression_penalty_mean": _round_metric(
                pd.to_numeric(rows["trajectory_soft_regression_penalty"], errors="coerce").fillna(0.0).mean()
            ),
            "trajectory_on_track_rate": _round_metric((rows["trajectory_status"] == "on_track").astype(float).mean()),
            "trajectory_needs_replan_rate": _round_metric((rows["trajectory_status"] == "needs_replan").astype(float).mean()),
            "trajectory_degraded_rate": _round_metric((rows["trajectory_status"] == "degraded").astype(float).mean()),
        }

    transition_frames: list[pd.DataFrame] = []
    for population, rows in (
        ("denied", denied_rows),
        ("high_risk_denied", high_risk_denied_rows),
    ):
        if rows.empty:
            continue
        grouped = (
            _population_rows(rows, population)
            .groupby(
                ["population", "risk_band", "trajectory_status", "current_phase", "phase_transition_reason"],
                dropna=False,
            )
            .agg(
                count=("customer_id", "nunique"),
                mean_next_review_week=("trajectory_next_review_week", "mean"),
                mean_soft_regression_penalty=("trajectory_soft_regression_penalty", "mean"),
            )
            .reset_index()
        )
        grouped["share"] = grouped["count"] / max(1, int(len(rows)))
        transition_frames.append(grouped)
    transition_breakdown = (
        pd.concat(transition_frames, ignore_index=True)
        if transition_frames
        else pd.DataFrame(
            columns=[
                "population",
                "risk_band",
                "trajectory_status",
                "current_phase",
                "phase_transition_reason",
                "count",
                "mean_next_review_week",
                "mean_soft_regression_penalty",
                "share",
            ]
        )
    )

    policy_frames: list[pd.DataFrame] = []
    for population, rows in (
        ("denied", denied_rows),
        ("high_risk_denied", high_risk_denied_rows),
    ):
        if rows.empty:
            continue
        grouped = (
            _population_rows(rows, population)
            .groupby(["population", "risk_band", "trajectory_policy_label"], dropna=False)
            .agg(
                count=("customer_id", "nunique"),
                mean_policy_score=("trajectory_policy_score", "mean"),
            )
            .reset_index()
        )
        grouped["share"] = grouped["count"] / max(1, int(len(rows)))
        policy_frames.append(grouped)
    policy_breakdown = (
        pd.concat(policy_frames, ignore_index=True)
        if policy_frames
        else pd.DataFrame(
            columns=[
                "population",
                "risk_band",
                "trajectory_policy_label",
                "count",
                "mean_policy_score",
                "share",
            ]
        )
    )

    dominant_transition_reason = ""
    if not transition_breakdown.empty:
        dominant_transition_reason = str(
            transition_breakdown.sort_values(["count", "share"], ascending=[False, False]).iloc[0][
                "phase_transition_reason"
            ]
        )

    summary = {
        "canonical_population": "denied",
        "secondary_population": "high_risk_denied",
        "primary_checkpoint_week": 4,
        "checkpoint_priority_order": [4, 12, 24],
        "canonical_metrics": _metrics(denied_rows),
        "secondary_metrics": _metrics(high_risk_denied_rows),
        "dominant_transition_reason": dominant_transition_reason,
        "supporting_artifacts": {
            "trajectory_transition_breakdown_csv": "tables/trajectory_transition_breakdown.csv",
            "trajectory_policy_label_breakdown_csv": "tables/trajectory_policy_label_breakdown.csv",
            "trajectory_gate_by_risk_band_csv": "tables/trajectory_gate_by_risk_band.csv",
            "trajectory_gate_by_income_band_csv": "tables/trajectory_gate_by_income_band.csv",
            "trajectory_phase_action_mix_csv": "tables/trajectory_phase_action_mix.csv",
        },
    }
    return summary, transition_breakdown, policy_breakdown


def _plan_trajectory_steps(plan: PlanRecord) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for action in sorted(
        list(plan.actions),
        key=lambda a: (
            _safe_int(getattr(a, "time_months", 0), 0),
            _safe_str(getattr(a, "feature_name", "")),
        ),
    ):
        m = max(1, _safe_int(getattr(action, "time_months", 1), 1))
        phase_id = _phase_id_for_month(m)
        steps.append(
            {
                "phase_id": phase_id,
                "phase_title": _phase_title(phase_id),
                "time_months": int(m),
                "feature_name": _safe_str(getattr(action, "feature_name", "")),
                "current_value": _safe_float(getattr(action, "current_value", np.nan), np.nan),
                "target_value": _safe_float(getattr(action, "target_value", np.nan), np.nan),
                "delta": _safe_float(getattr(action, "delta", 0.0), 0.0),
                "estimated_cost_usd": _safe_float(getattr(action, "estimated_cost_usd", 0.0), 0.0),
            }
        )
    return steps


def _candidate_rank_tuple(plan: PlanRecord) -> tuple:
    return (
        _status_priority(getattr(plan, "status", "")),
        _plan_cost(plan),
        int(len(plan.actions)),
        float(plan.predicted_pd or 1.0),
        -(float(plan.robust_score) if plan.robust_score is not None else float(plan.score or -1e9)),
    )


def _plan_source(plan: PlanRecord) -> str:
    pid = str(plan.plan_id)
    if "_fallback_" in pid:
        return "fallback"
    if "_dice_" in pid:
        return "dice"
    if "_rule_" in pid:
        return "rule"
    return "internal"


def _plan_signature(plan: PlanRecord) -> tuple[str, ...]:
    feats = sorted({str(a.feature_name) for a in plan.actions})
    return tuple(feats)


def _jaccard_distance(a: tuple[str, ...], b: tuple[str, ...]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    union = len(sa | sb)
    if union <= 0:
        return 0.0
    return float(1.0 - (len(sa & sb) / union))


def _candidate_source_entropy(plans: list[PlanRecord]) -> float:
    if not plans:
        return 0.0
    counts: dict[str, int] = {}
    for p in plans:
        src = _plan_source(p)
        counts[src] = counts.get(src, 0) + 1
    total = float(len(plans))
    entropy = 0.0
    for c in counts.values():
        p = float(c) / total
        if p > 0:
            entropy -= p * math.log(p, 2.0)
    max_entropy = math.log(max(1, len(counts)), 2.0)
    if max_entropy <= 0:
        return 0.0
    return float(entropy / max_entropy)


def _candidate_pool_diversity_index(plans: list[PlanRecord]) -> float:
    if len(plans) <= 1:
        return 0.0
    sigs = [_plan_signature(p) for p in plans]
    distances: list[float] = []
    for i in range(len(sigs)):
        for j in range(i + 1, len(sigs)):
            distances.append(_jaccard_distance(sigs[i], sigs[j]))
    if not distances:
        return 0.0
    return float(np.mean(np.asarray(distances, dtype=float)))


def _plan_gate_margin(
    plan: PlanRecord,
    *,
    tau: float,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> float:
    ci_high = (
        float(plan.ci_high)
        if plan.ci_high is not None
        else float(plan.predicted_pd if plan.predicted_pd is not None else tau)
    )
    ci_margin = float(tau - ci_high)
    rel_margin = (
        float(plan.reliability) - float(min_reliability)
        if (min_reliability is not None and plan.reliability is not None)
        else 0.0
    )
    worst_margin = (
        float(plan.robust_worst_risk_margin) - float(min_worst_risk_margin)
        if (min_worst_risk_margin is not None and plan.robust_worst_risk_margin is not None)
        else 0.0
    )
    return float((0.6 * ci_margin) + (0.25 * rel_margin) + (0.15 * worst_margin))


def _plan_gate_violation_total(
    plan: PlanRecord,
    *,
    tau: float,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> float:
    ci_high = (
        float(plan.ci_high)
        if plan.ci_high is not None
        else float(plan.predicted_pd if plan.predicted_pd is not None else (tau + 1.0))
    )
    ci_v = max(0.0, float(ci_high) - float(tau))
    rel_v = 0.0
    if min_reliability is not None:
        rel_v = max(0.0, float(min_reliability) - float(plan.reliability if plan.reliability is not None else 0.0))
    worst_v = 0.0
    if min_worst_risk_margin is not None:
        worst_v = max(
            0.0,
            float(min_worst_risk_margin)
            - float(plan.robust_worst_risk_margin if plan.robust_worst_risk_margin is not None else -1.0),
        )
    return float(ci_v + rel_v + worst_v)


def _candidate_gate_sort_key(
    plan: PlanRecord,
    *,
    tau: float,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> tuple:
    return (
        _status_priority(getattr(plan, "status", "")),
        _plan_gate_violation_total(
            plan,
            tau=tau,
            min_reliability=min_reliability,
            min_worst_risk_margin=min_worst_risk_margin,
        ),
        _plan_cost(plan),
        int(len(plan.actions)),
        float(plan.predicted_pd if plan.predicted_pd is not None else 1.0),
        -(float(plan.robust_score) if plan.robust_score is not None else float(plan.score or -1e9)),
    )


def _stage1_filter_candidate_pool(
    plans: list[PlanRecord],
    *,
    max_size: int,
    tau: float,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
    multiplier: float = 2.0,
    per_source_cap: int = 0,
) -> list[PlanRecord]:
    if max_size <= 0 or len(plans) <= max_size:
        return plans
    stage1_size = int(max(max_size, round(float(max_size) * max(1.0, float(multiplier)))))
    stage1_size = min(stage1_size, len(plans))
    ranked = sorted(
        plans,
        key=lambda p: _candidate_gate_sort_key(
            p,
            tau=tau,
            min_reliability=min_reliability,
            min_worst_risk_margin=min_worst_risk_margin,
        ),
    )
    if per_source_cap <= 0:
        return ranked[:stage1_size]

    selected: list[PlanRecord] = []
    src_counts: dict[str, int] = {}
    for p in ranked:
        src = _plan_source(p)
        if src_counts.get(src, 0) >= int(per_source_cap):
            continue
        selected.append(p)
        src_counts[src] = src_counts.get(src, 0) + 1
        if len(selected) >= stage1_size:
            break
    if len(selected) < stage1_size:
        for p in ranked:
            if p in selected:
                continue
            selected.append(p)
            if len(selected) >= stage1_size:
                break
    return selected[:stage1_size]


def _prune_candidate_pool(
    plans: list[PlanRecord],
    max_size: int,
    novelty_weight: float = 0.0,
    *,
    tau: float = 0.35,
    min_reliability: float | None = None,
    min_worst_risk_margin: float | None = None,
) -> list[PlanRecord]:
    if max_size <= 0 or len(plans) <= max_size:
        return plans
    ranked = sorted(
        plans,
        key=lambda p: _candidate_gate_sort_key(
            p,
            tau=tau,
            min_reliability=min_reliability,
            min_worst_risk_margin=min_worst_risk_margin,
        ),
    )
    if novelty_weight <= 0.0:
        return ranked[:max_size]

    selected: list[PlanRecord] = [ranked[0]]
    remaining = ranked[1:]
    while len(selected) < max_size and remaining:
        best_idx = 0
        best_score = -1e18
        for idx, cand in enumerate(remaining):
            base_quality = -float(idx)
            cand_sig = _plan_signature(cand)
            novelty = 0.0
            if selected:
                novelty = float(
                    np.mean(
                        [
                            _jaccard_distance(cand_sig, _plan_signature(chosen))
                            for chosen in selected
                        ]
                    )
                )
            score = base_quality + (float(novelty_weight) * novelty)
            if score > best_score:
                best_score = score
                best_idx = idx
        selected.append(remaining.pop(best_idx))
    return selected


def _resolve_high_risk_profile_activation(
    *,
    search_profile: dict[str, Any],
    robust_cfg: dict[str, Any],
    dice_cfg: dict[str, Any],
    rec_cfg: dict[str, Any],
    segment_context: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    high_cfg = rec_cfg.get("high_risk_profile", {}) if isinstance(rec_cfg.get("high_risk_profile", {}), dict) else {}
    metadata: dict[str, Any] = {
        "enabled": bool(high_cfg.get("enabled", False)),
        "applied": False,
        "reason": "disabled",
        "denied_target_only": bool(high_cfg.get("denied_target_only", True)),
        "enforce_max_pd_delta": bool(high_cfg.get("enforce_max_pd_delta", False)),
        "max_pd_delta": _safe_float(high_cfg.get("max_pd_delta"), default=0.0)
        if high_cfg.get("max_pd_delta") is not None
        else None,
        "risk_band": str(segment_context.get("risk_band", "")),
        "pd_distance_to_tau": _safe_float(segment_context.get("pd_distance_to_tau"), default=0.0),
    }
    if not bool(high_cfg.get("enabled", False)):
        return search_profile, robust_cfg, dice_cfg, metadata
    if str(segment_context.get("risk_band", "")) != "high":
        metadata["reason"] = "not_high_risk"
        return search_profile, robust_cfg, dice_cfg, metadata
    max_pd_delta = high_cfg.get("max_pd_delta")
    enforce_max_pd_delta = bool(high_cfg.get("enforce_max_pd_delta", False))
    if enforce_max_pd_delta and max_pd_delta is not None:
        try:
            pd_delta = float(segment_context.get("pd_distance_to_tau", 0.0))
            if pd_delta > float(max_pd_delta):
                metadata["reason"] = "pd_delta_above_cap"
                return search_profile, robust_cfg, dice_cfg, metadata
        except Exception:
            pass
    denied_only = bool(high_cfg.get("denied_target_only", True))
    if denied_only and not bool(search_profile.get("is_denied_target", False)):
        metadata["reason"] = "not_denied_target"
        return search_profile, robust_cfg, dice_cfg, metadata

    sp = dict(search_profile)
    rc = dict(robust_cfg)
    dc = dict(dice_cfg)

    topk_multiplier = max(1.0, float(high_cfg.get("topk_multiplier", 1.0)))
    min_topk = int(high_cfg.get("min_topk", sp.get("topk", 1)))
    sp["topk"] = max(min_topk, int(round(float(sp.get("topk", 1)) * topk_multiplier)))

    hvals = high_cfg.get("horizons")
    if isinstance(hvals, list) and hvals:
        hs = [int(h) for h in hvals if int(h) in (3, 6, 12)]
        if hs:
            sp["horizons"] = hs

    svals = high_cfg.get("strategies")
    if isinstance(svals, list) and svals:
        ss = [str(s) for s in svals if str(s) in {"conservative", "balanced", "aggressive"}]
        if ss:
            sp["strategies"] = ss

    search_cfg = sp.get("search_cfg", {}) if isinstance(sp.get("search_cfg", {}), dict) else {}
    search_cfg = dict(search_cfg)
    action_budget = search_cfg.get("action_budget", {}) if isinstance(search_cfg.get("action_budget", {}), dict) else {}
    action_budget = dict(action_budget)
    if "max_actions" in high_cfg:
        action_budget["max_actions"] = int(high_cfg.get("max_actions", action_budget.get("max_actions", 4)))
    if action_budget:
        search_cfg["action_budget"] = action_budget

    weekly_cfg = search_cfg.get("weekly_optimizer", {}) if isinstance(search_cfg.get("weekly_optimizer", {}), dict) else {}
    weekly_cfg = dict(weekly_cfg)
    if bool(high_cfg.get("force_weekly_optimizer", True)):
        weekly_cfg["enabled"] = True
    if "weekly_weeks" in high_cfg:
        weekly_cfg["weeks"] = int(high_cfg.get("weekly_weeks", weekly_cfg.get("weeks", 8)))
    if "weekly_max_actions" in high_cfg:
        weekly_cfg["max_weekly_actions"] = int(high_cfg.get("weekly_max_actions", weekly_cfg.get("max_weekly_actions", 2)))
    search_cfg["weekly_optimizer"] = weekly_cfg

    target_pd_margin_extra = float(high_cfg.get("target_pd_margin_extra", 0.0))
    if target_pd_margin_extra > 0.0:
        current_extra = float(search_cfg.get("target_pd_margin_extra", 0.0))
        search_cfg["target_pd_margin_extra"] = max(current_extra, target_pd_margin_extra)
    sp["search_cfg"] = search_cfg

    if "min_reliability" in high_cfg:
        rc["min_reliability"] = float(high_cfg.get("min_reliability", rc.get("min_reliability", 0.7)))
    if "min_worst_risk_margin" in high_cfg:
        rc["min_worst_risk_margin"] = float(
            high_cfg.get("min_worst_risk_margin", rc.get("min_worst_risk_margin", -0.05))
        )

    if "dice_total_cfs_multiplier" in high_cfg:
        dc["total_cfs"] = int(
            max(
                1,
                round(
                    float(dc.get("total_cfs", 2))
                    * max(1.0, float(high_cfg.get("dice_total_cfs_multiplier", 1.0)))
                ),
            )
        )
    if "dice_max_actions_multiplier" in high_cfg:
        dc["max_actions"] = int(
            max(
                1,
                round(
                    float(dc.get("max_actions", 2))
                    * max(1.0, float(high_cfg.get("dice_max_actions_multiplier", 1.0)))
                ),
            )
        )
    metadata["applied"] = True
    metadata["reason"] = "applied"
    return sp, rc, dc, metadata


def _apply_high_risk_profile(
    *,
    search_profile: dict[str, Any],
    robust_cfg: dict[str, Any],
    dice_cfg: dict[str, Any],
    rec_cfg: dict[str, Any],
    segment_context: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], bool]:
    sp, rc, dc, metadata = _resolve_high_risk_profile_activation(
        search_profile=search_profile,
        robust_cfg=robust_cfg,
        dice_cfg=dice_cfg,
        rec_cfg=rec_cfg,
        segment_context=segment_context,
    )
    return sp, rc, dc, bool(metadata.get("applied", False))


def _root_cause_from_status_reasons(reasons: list[str] | str) -> str:
    if isinstance(reasons, str):
        text = str(reasons).lower().strip()
        if not text:
            return "unknown"
    else:
        if not reasons:
            return "unknown"
        text = " | ".join(str(r).lower() for r in reasons if r)
        if not text:
            return "unknown"
    if "fizibilite" in text or "feasible" in text:
        return "feasibility_gate"
    if "direction violation" in text:
        return "feasibility_gate"
    if "missing current/target" in text:
        return "feasibility_gate"
    if "not actionable" in text:
        return "feasibility_gate"
    if "pipeline_error" in text:
        return "pipeline_error"
    if "error" in text and "ci upper bound" not in text:
        return "pipeline_error"
    has_rel = "reliability" in text
    has_worst = "worst_risk_margin" in text
    has_ci = ("ci upper bound exceeds threshold" in text) or ("ci upper bound" in text)
    hit_count = int(has_rel) + int(has_worst) + int(has_ci)
    if hit_count > 1:
        return "multi_gate"
    if has_rel:
        return "reliability_gate"
    if has_worst:
        return "worst_margin_gate"
    if has_ci:
        return "ci_gate"
    return "multi_or_unknown"


def _top_action_realism_rejection_reason(events: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for event in events:
        if str(event.get("status", "")) != "rejected":
            continue
        codes = event.get("reason_codes", [])
        if not isinstance(codes, list) or not codes:
            codes = ["unknown"]
        for code in codes:
            key = str(code).strip() or "unknown"
            counts[key] = int(counts.get(key, 0) + 1)
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _top_constraint_reason(events: list[dict[str, Any]], *, event_type: str) -> str:
    counts: dict[str, int] = {}
    for event in events:
        if str(event.get("event_type", "")) != event_type:
            continue
        key = str(event.get("reason_code", "")).strip() or "unknown"
        counts[key] = int(counts.get(key, 0) + 1)
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _extract_reliability_thresholds_by_risk_band(
    *,
    uncertainty_cfg: dict[str, Any],
    default_min_reliability: float | None,
) -> dict[str, float | None]:
    out: dict[str, float | None] = {
        "default": float(default_min_reliability) if default_min_reliability is not None else None,
        "near": None,
        "mid": None,
        "high": None,
    }
    profiles = (
        uncertainty_cfg.get("reliability_profiles", {})
        if isinstance(uncertainty_cfg.get("reliability_profiles", {}), dict)
        else {}
    )
    if not isinstance(profiles, dict):
        return out
    default_override = profiles.get("default", {}) if isinstance(profiles.get("default", {}), dict) else {}
    if default_override.get("min_reliability") is not None:
        try:
            out["default"] = float(default_override.get("min_reliability"))
        except Exception:
            pass
    denied_override = profiles.get("denied", {}) if isinstance(profiles.get("denied", {}), dict) else {}
    denied_min = denied_override.get("min_reliability")

    for band in ("near", "mid", "high"):
        band_cfg = profiles.get(band, {}) if isinstance(profiles.get(band, {}), dict) else {}
        chosen = None
        if band_cfg.get("min_reliability") is not None:
            chosen = band_cfg.get("min_reliability")
        elif denied_min is not None:
            chosen = denied_min
        elif out["default"] is not None:
            chosen = out["default"]
        if chosen is not None:
            try:
                out[band] = float(chosen)
            except Exception:
                out[band] = out["default"]
    return out


def _apply_group_fairness_recourse_balance(
    *,
    robust_cfg: dict[str, Any],
    rec_cfg: dict[str, Any],
    fairness_penalty: float,
) -> dict[str, Any]:
    out = dict(robust_cfg)
    fairness_cfg = rec_cfg.get("fairness", {}) if isinstance(rec_cfg.get("fairness", {}), dict) else {}
    balance_cfg = (
        fairness_cfg.get("recourse_balance", {})
        if isinstance(fairness_cfg.get("recourse_balance", {}), dict)
        else {}
    )
    if not bool(balance_cfg.get("enabled", False)):
        return out

    threshold = max(0.0, float(balance_cfg.get("disadvantaged_penalty_threshold", 0.01)))
    is_disadvantaged = float(fairness_penalty) <= threshold
    if is_disadvantaged:
        rel_scale = max(0.0, float(balance_cfg.get("disadvantaged_min_reliability_scale", 0.85)))
        worst_shift = float(balance_cfg.get("disadvantaged_min_worst_margin_shift", -0.03))
    else:
        rel_scale = max(0.0, float(balance_cfg.get("advantaged_min_reliability_scale", 1.05)))
        worst_shift = float(balance_cfg.get("advantaged_min_worst_margin_shift", 0.01))

    min_rel = out.get("min_reliability")
    if min_rel is not None:
        out["min_reliability"] = max(0.0, min(1.0, float(min_rel) * rel_scale))
    min_worst = out.get("min_worst_risk_margin")
    if min_worst is not None:
        out["min_worst_risk_margin"] = float(min_worst) + worst_shift
    return out


def _apply_fairness_segment_cap_boost(
    *,
    segment_context: dict[str, Any],
    rec_cfg: dict[str, Any],
    fairness_penalty: float,
    denied_mode: bool,
) -> tuple[dict[str, Any], float, bool, float]:
    if not isinstance(segment_context, dict):
        return {}, 0.0, False, 1.0

    fairness_cfg = rec_cfg.get("fairness", {}) if isinstance(rec_cfg.get("fairness", {}), dict) else {}
    boost_cfg = (
        fairness_cfg.get("segment_cap_boost", {})
        if isinstance(fairness_cfg.get("segment_cap_boost", {}), dict)
        else {}
    )
    if not bool(boost_cfg.get("enabled", False)):
        return dict(segment_context), 0.0, False, 1.0
    if bool(boost_cfg.get("only_denied_target", True)) and not bool(denied_mode):
        return dict(segment_context), 0.0, False, 1.0
    if bool(boost_cfg.get("only_high_risk", True)) and str(segment_context.get("risk_band", "")).strip().lower() != "high":
        return dict(segment_context), 0.0, False, 1.0

    penalty = max(0.0, float(fairness_penalty))
    min_penalty = max(0.0, float(boost_cfg.get("min_penalty", 0.03)))
    if penalty < min_penalty:
        return dict(segment_context), 0.0, False, 1.0

    penalty_reference = max(min_penalty + 1e-6, float(boost_cfg.get("penalty_reference", max(min_penalty, 0.06))))
    intensity = min(1.0, max(0.0, (penalty - min_penalty) / max(1e-9, penalty_reference - min_penalty)))

    cap_boost_max = max(1.0, float(boost_cfg.get("cap_multiplier_boost_max", 1.15)))
    cap_boost = 1.0 + (cap_boost_max - 1.0) * intensity
    feature_boost_max = max(1.0, float(boost_cfg.get("feature_cap_multiplier_boost_max", 1.10)))
    feature_boost = 1.0 + (feature_boost_max - 1.0) * intensity
    target_pd_extra_max = max(0.0, float(boost_cfg.get("target_pd_margin_extra_max", 0.01)))
    target_pd_extra = float(target_pd_extra_max * intensity)

    out = dict(segment_context)
    old_cap = max(1e-9, float(out.get("cap_multiplier", 1.0)))
    cap_max = max(old_cap, float(out.get("cap_multiplier_max", old_cap)))
    new_cap = min(cap_max, old_cap * cap_boost)
    out["cap_multiplier"] = float(new_cap)
    out["segment_caps_applied"] = bool(abs(new_cap - 1.0) > 1e-12)

    feat_mults = (
        dict(out.get("feature_cap_multipliers", {}))
        if isinstance(out.get("feature_cap_multipliers", {}), dict)
        else {}
    )
    if feat_mults:
        out["feature_cap_multipliers"] = {
            str(k): float(max(0.0, float(v)) * feature_boost)
            for k, v in feat_mults.items()
        }

    return out, target_pd_extra, True, float(cap_boost)


def _build_denied_diagnostics(
    batch_df: pd.DataFrame,
    *,
    tau: float,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
    reliability_threshold_by_risk_band: dict[str, float | None] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, float]]:
    denied = batch_df[batch_df.get("denied_base", pd.Series(dtype=int)).astype(int) == 1].copy()
    if denied.empty:
        empty_gate = pd.DataFrame(columns=["gate", "count", "share"])
        empty_src = pd.DataFrame(columns=["source_bucket", "count", "share"])
        empty_income = pd.DataFrame(
            columns=["income_band", "denied_count", "denied_with_any_candidate", "denied_with_gate_pass_plan", "denied_to_approved_lift"]
        )
        empty_risk = pd.DataFrame(
            columns=["risk_band", "denied_count", "denied_with_any_candidate", "denied_with_gate_pass_plan", "denied_to_approved_lift"]
        )
        return (
            empty_gate,
            empty_src,
            empty_income,
            empty_risk,
            {
                "denied_reliability_violation_rate": 0.0,
                "denied_ci_violation_rate": 0.0,
                "denied_worst_margin_violation_rate": 0.0,
                "denied_internal_gate_pass_share": 0.0,
                "denied_dice_gate_pass_share": 0.0,
                "denied_rule_gate_pass_share": 0.0,
                "denied_internal_vs_dice_gate_pass_share": 0.0,
                "denied_nonrejected_best_rate": 0.0,
                "denied_nan_gate_fields_rate": 0.0,
                "denied_reliability_threshold_default": float(min_reliability) if min_reliability is not None else 0.0,
            },
        )
    if "income_band" not in denied.columns:
        denied["income_band"] = "unknown"
    if "risk_band" not in denied.columns:
        denied["risk_band"] = "unknown"

    denied_na = denied[denied.get("best_status", pd.Series(dtype=str)).astype(str) != "APPROVED"].copy()
    na_n = max(1, int(len(denied_na)))

    root = denied_na.get("denied_not_approved_root_cause", pd.Series([""] * len(denied_na))).astype(str).str.lower()
    ci_high = pd.to_numeric(denied_na.get("best_ci_high", pd.Series([np.nan] * len(denied_na))), errors="coerce")
    rel = pd.to_numeric(denied_na.get("best_reliability", pd.Series([np.nan] * len(denied_na))), errors="coerce")
    worst = pd.to_numeric(denied_na.get("best_worst_risk_margin", pd.Series([np.nan] * len(denied_na))), errors="coerce")
    nan_gate = ci_high.isna() | rel.isna() | worst.isna()

    ci_v = ci_high.isna() | (ci_high > float(tau)) | (root == "ci_gate")
    rel_v = rel.isna() | (root == "reliability_gate")
    if isinstance(reliability_threshold_by_risk_band, dict):
        risk_band_s = denied_na.get("risk_band", pd.Series([""] * len(denied_na))).astype(str).str.lower().str.strip()
        rel_thr_default = reliability_threshold_by_risk_band.get("default")
        rel_thr_series = risk_band_s.map(
            lambda b: reliability_threshold_by_risk_band.get(b, rel_thr_default)
        )
        rel_thr = pd.to_numeric(rel_thr_series, errors="coerce")
        rel_v = rel_v | (rel_thr.notna() & (rel < rel_thr))
    elif min_reliability is not None:
        rel_v = rel_v | (rel < float(min_reliability))
    worst_v = worst.isna() | (root == "worst_margin_gate")
    if min_worst_risk_margin is not None:
        worst_v = worst_v | (worst < float(min_worst_risk_margin))

    gate_counts = {
        "ci_gate": int(ci_v.sum()),
        "reliability_gate": int(rel_v.sum()),
        "worst_margin_gate": int(worst_v.sum()),
    }
    gate_breakdown = (
        pd.DataFrame([{"gate": k, "count": v, "share": float(v / na_n)} for k, v in gate_counts.items()])
        .sort_values(["count", "gate"], ascending=[False, True])
        .reset_index(drop=True)
    )

    internal_gate = denied.get("internal_gate_pass_any", pd.Series([0] * len(denied))).astype(int) == 1
    dice_gate = denied.get("dice_gate_pass_any", pd.Series([0] * len(denied))).astype(int) == 1
    rule_gate = denied.get("rule_gate_pass_any", pd.Series([0] * len(denied))).astype(int) == 1
    source_bucket = np.where(
        internal_gate & dice_gate,
        "both",
        np.where(internal_gate, "internal_only", np.where(dice_gate, "dice_only", "none")),
    )
    source_breakdown = (
        pd.Series(source_bucket)
        .value_counts(dropna=False)
        .rename_axis("source_bucket")
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )
    source_breakdown["share"] = (source_breakdown["count"] / max(1, int(len(denied)))).astype(float)

    income_lift = (
        denied.groupby("income_band", dropna=False)
        .agg(
            denied_count=("customer_id", "size"),
            denied_with_any_candidate=("had_any_candidate", "sum"),
            denied_with_gate_pass_plan=("gate_pass_any_candidate", "sum"),
        )
        .reset_index()
    )
    income_lift["denied_to_approved_lift"] = (
        income_lift["denied_with_gate_pass_plan"] / income_lift["denied_count"].clip(lower=1)
    ).astype(float)

    risk_lift = (
        denied.groupby("risk_band", dropna=False)
        .agg(
            denied_count=("customer_id", "size"),
            denied_with_any_candidate=("had_any_candidate", "sum"),
            denied_with_gate_pass_plan=("gate_pass_any_candidate", "sum"),
        )
        .reset_index()
    )
    risk_lift["denied_to_approved_lift"] = (
        risk_lift["denied_with_gate_pass_plan"] / risk_lift["denied_count"].clip(lower=1)
    ).astype(float)

    denied_n = max(1, int(len(denied)))
    internal_n = int(internal_gate.sum())
    dice_n = int(dice_gate.sum())
    rule_n = int(rule_gate.sum())
    denied_nonrejected = int(
        (~denied.get("best_status", pd.Series(dtype=str)).astype(str).str.upper().isin(["REJECTED", "ERROR"])).sum()
    )
    metrics = {
        "denied_reliability_violation_rate": float(rel_v.sum() / na_n),
        "denied_ci_violation_rate": float(ci_v.sum() / na_n),
        "denied_worst_margin_violation_rate": float(worst_v.sum() / na_n),
        "denied_internal_gate_pass_share": float(internal_n / denied_n),
        "denied_dice_gate_pass_share": float(dice_n / denied_n),
        "denied_rule_gate_pass_share": float(rule_n / denied_n),
        "denied_internal_vs_dice_gate_pass_share": float(internal_n / max(1, internal_n + dice_n)),
        "denied_nonrejected_best_rate": float(denied_nonrejected / denied_n),
        "denied_nan_gate_fields_rate": float(nan_gate.sum() / na_n),
        "denied_reliability_threshold_default": (
            float(reliability_threshold_by_risk_band.get("default"))
            if isinstance(reliability_threshold_by_risk_band, dict)
            and reliability_threshold_by_risk_band.get("default") is not None
            else (float(min_reliability) if min_reliability is not None else 0.0)
        ),
    }
    return gate_breakdown, source_breakdown, income_lift, risk_lift, metrics


def _candidate_quality_metrics_for_population(rows: pd.DataFrame) -> dict[str, float]:
    if rows.empty:
        return {
            "candidate_pool_diversity_index": 0.0,
            "candidate_source_entropy": 0.0,
            **{f"best_source_{source}_rate": 0.0 for source in _CANDIDATE_SOURCE_CATALOG},
        }
    best_source = rows.get("best_source", pd.Series([""] * len(rows))).astype(str).str.strip().str.lower()
    metrics = {
        "candidate_pool_diversity_index": _round_metric(
            pd.to_numeric(rows.get("candidate_pool_diversity_index", pd.Series([0.0] * len(rows))), errors="coerce")
            .fillna(0.0)
            .mean()
        ),
        "candidate_source_entropy": _round_metric(
            pd.to_numeric(rows.get("candidate_source_entropy", pd.Series([0.0] * len(rows))), errors="coerce")
            .fillna(0.0)
            .mean()
        ),
    }
    for source in _CANDIDATE_SOURCE_CATALOG:
        metrics[f"best_source_{source}_rate"] = _round_metric((best_source == source).mean())
    return metrics


def _build_candidate_quality_artifacts(batch_df: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    denied = batch_df[batch_df.get("denied_base", pd.Series(dtype=int)).astype(int) == 1].copy()
    denied_high_risk = denied[denied.get("risk_band", pd.Series(dtype=str)).astype(str).str.lower() == "high"].copy()

    canonical_metrics = _candidate_quality_metrics_for_population(denied)
    secondary_metrics = _candidate_quality_metrics_for_population(denied_high_risk)
    summary = {
        "canonical_population": "denied",
        "secondary_population": "high_risk_denied",
        "source_catalog": list(_CANDIDATE_SOURCE_CATALOG),
        "population_sizes": {
            "denied": int(len(denied)),
            "high_risk_denied": int(len(denied_high_risk)),
        },
        "canonical_metrics": canonical_metrics,
        "secondary_metrics": secondary_metrics,
    }

    breakdown_rows: list[dict[str, Any]] = []
    for population, rows in (("denied", denied), ("high_risk_denied", denied_high_risk)):
        best_source = rows.get("best_source", pd.Series([""] * len(rows))).astype(str).str.strip().str.lower()
        for source in _CANDIDATE_SOURCE_CATALOG:
            count = int((best_source == source).sum()) if not rows.empty else 0
            share = _round_metric((best_source == source).mean()) if not rows.empty else 0.0
            breakdown_rows.append(
                {
                    "population": population,
                    "candidate_source": source,
                    "count": count,
                    "share": share,
                    "population_size": int(len(rows)),
                }
            )
    breakdown_df = pd.DataFrame(breakdown_rows)
    return summary, breakdown_df


def _build_high_risk_profile_activation_summary(
    batch_df: pd.DataFrame,
    *,
    rec_cfg: dict[str, Any],
) -> dict[str, Any]:
    high_cfg = rec_cfg.get("high_risk_profile", {}) if isinstance(rec_cfg.get("high_risk_profile", {}), dict) else {}
    if batch_df.empty:
        return {
            "enabled": bool(high_cfg.get("enabled", False)),
            "denied_target_only": bool(high_cfg.get("denied_target_only", True)),
            "enforce_max_pd_delta": bool(high_cfg.get("enforce_max_pd_delta", False)),
            "max_pd_delta": _safe_float(high_cfg.get("max_pd_delta"), default=0.0)
            if high_cfg.get("max_pd_delta") is not None
            else None,
            "population_scope": "high_risk_denied",
            "minimum_meaningful_activation_rate": _HIGH_RISK_ACTIVATION_FLOOR,
            "eligible_population_size": 0,
            "applied_count": 0,
            "applied_rate": 0.0,
            "meaningful_activation": False,
            "reason_counts": {},
            "blocked_reason_counts": {},
        }

    eligible_mask = (
        batch_df.get("denied_base", pd.Series(dtype=int)).astype(int) == 1
    ) & (batch_df.get("risk_band", pd.Series(dtype=str)).astype(str).str.lower() == "high")
    applied_rate = _round_metric(batch_df.get("high_risk_profile_applied", pd.Series(dtype=int)).astype(int).mean())
    reason_series = batch_df.get("high_risk_profile_reason", pd.Series(dtype=str)).astype(str).replace("", "unknown")
    reason_counts = {str(key): int(value) for key, value in reason_series.value_counts(dropna=False).items()}
    blocked_reason_counts = {
        str(key): int(value)
        for key, value in reason_counts.items()
        if str(key) not in {"applied", ""}
    }
    return {
        "enabled": bool(high_cfg.get("enabled", False)),
        "denied_target_only": bool(high_cfg.get("denied_target_only", True)),
        "enforce_max_pd_delta": bool(high_cfg.get("enforce_max_pd_delta", False)),
        "max_pd_delta": _safe_float(high_cfg.get("max_pd_delta"), default=0.0)
        if high_cfg.get("max_pd_delta") is not None
        else None,
        "population_scope": "high_risk_denied",
        "minimum_meaningful_activation_rate": _HIGH_RISK_ACTIVATION_FLOOR,
        "eligible_population_size": int(eligible_mask.sum()),
        "applied_count": int(batch_df.get("high_risk_profile_applied", pd.Series(dtype=int)).astype(int).sum()),
        "applied_rate": applied_rate,
        "meaningful_activation": bool(applied_rate >= _HIGH_RISK_ACTIVATION_FLOOR),
        "reason_counts": reason_counts,
        "blocked_reason_counts": blocked_reason_counts,
    }


def _build_batch_high_risk_tuning_summary(
    *,
    summary: dict[str, Any],
    activation_summary: dict[str, Any],
) -> dict[str, Any]:
    diagnostic_reasons: list[str] = []
    if not bool(activation_summary.get("meaningful_activation", False)):
        diagnostic_reasons.append("activation_below_min_floor")
    evidence_status = "observed" if not diagnostic_reasons else "diagnostic_only"
    return {
        "primary_metric": "denied_high_risk_lift",
        "primary_metric_value": _round_metric(summary.get("denied_high_risk_lift", 0.0)),
        "high_risk_profile_applied_rate": _round_metric(summary.get("high_risk_profile_applied_rate", 0.0)),
        "activation_floor": _HIGH_RISK_ACTIVATION_FLOOR,
        "meaningful_activation": bool(activation_summary.get("meaningful_activation", False)),
        "supporting_metrics": {
            "high_risk_reachability_rate": _round_metric(summary.get("high_risk_reachability_rate", 0.0)),
            "trajectory_partial_progress_rate": _round_metric(summary.get("trajectory_partial_progress_rate", 0.0)),
        },
        "evidence_status": evidence_status,
        "diagnostic_reasons": diagnostic_reasons,
        "activation_summary": activation_summary,
    }


def _build_fairness_failure_breakdown(
    *,
    batch_df: pd.DataFrame,
    sampled_sorted: pd.DataFrame,
    base_proba: pd.Series,
    tau: float,
    group_feature: str,
    target_col: str,
) -> pd.DataFrame:
    if batch_df.empty or sampled_sorted.empty:
        return pd.DataFrame(
            columns=[
                "segment_key",
                "group_bucket",
                "risk_band",
                "income_band",
                "best_source",
                "n_rows",
                "denied_rows",
                "approval_rate_before",
                "approval_rate_after",
                "approval_rate_delta",
                "tpr_before",
                "tpr_after",
                "tpr_delta",
                "fpr_before",
                "fpr_after",
                "fpr_delta",
                "recourse_success_rate",
                "fairness_guard_demoted_rate",
                "failure_severity_score",
            ]
        )
    if group_feature not in sampled_sorted.columns or target_col not in sampled_sorted.columns:
        return pd.DataFrame(
            columns=[
                "segment_key",
                "group_bucket",
                "risk_band",
                "income_band",
                "best_source",
                "n_rows",
                "denied_rows",
                "approval_rate_before",
                "approval_rate_after",
                "approval_rate_delta",
                "tpr_before",
                "tpr_after",
                "tpr_delta",
                "fpr_before",
                "fpr_after",
                "fpr_delta",
                "recourse_success_rate",
                "fairness_guard_demoted_rate",
                "failure_severity_score",
            ]
        )

    df = pd.DataFrame(
        {
            "group_bucket": _build_group_bucket(sampled_sorted[group_feature]).astype(str).fillna("unknown").values,
            "risk_band": batch_df.get("risk_band", pd.Series(["unknown"] * len(batch_df))).astype(str).values,
            "income_band": batch_df.get("income_band", pd.Series(["unknown"] * len(batch_df))).astype(str).values,
            "best_source": batch_df.get("best_source", pd.Series(["unknown"] * len(batch_df))).astype(str).values,
            "y_true": pd.to_numeric(sampled_sorted[target_col], errors="coerce").fillna(0).astype(int).values,
            "denied_base": batch_df.get("denied_base", pd.Series([0] * len(batch_df))).astype(int).values,
            "gate_pass_any_candidate": batch_df.get("gate_pass_any_candidate", pd.Series([0] * len(batch_df))).astype(int).values,
            "fairness_guard_demoted": batch_df.get("fairness_guard_demoted", pd.Series([0] * len(batch_df))).astype(int).values,
            "before_pred_default": (base_proba.astype(float).to_numpy(dtype=float) > float(tau)).astype(int),
            "after_pred_default": (batch_df["best_pd"].astype(float).to_numpy(dtype=float) > float(tau)).astype(int),
        }
    )

    rows: list[dict[str, Any]] = []
    group_cols = ["group_bucket", "risk_band", "income_band", "best_source"]
    for keys, g in df.groupby(group_cols, dropna=False):
        y_true = g["y_true"].astype(int)
        before_pred = g["before_pred_default"].astype(int)
        after_pred = g["after_pred_default"].astype(int)
        before_approve = (before_pred == 0).astype(int)
        after_approve = (after_pred == 0).astype(int)
        pos_mask = y_true == 1
        neg_mask = y_true != 1

        tpr_before = float(before_pred[pos_mask].mean()) if bool(pos_mask.any()) else np.nan
        tpr_after = float(after_pred[pos_mask].mean()) if bool(pos_mask.any()) else np.nan
        fpr_before = float(before_pred[neg_mask].mean()) if bool(neg_mask.any()) else np.nan
        fpr_after = float(after_pred[neg_mask].mean()) if bool(neg_mask.any()) else np.nan
        approval_before = float(before_approve.mean()) if len(g) > 0 else 0.0
        approval_after = float(after_approve.mean()) if len(g) > 0 else 0.0
        recourse_success = (
            float(g.loc[g["denied_base"] == 1, "gate_pass_any_candidate"].mean())
            if int((g["denied_base"] == 1).sum()) > 0
            else 0.0
        )
        demoted_rate = float(g["fairness_guard_demoted"].mean()) if "fairness_guard_demoted" in g.columns else 0.0
        tpr_delta = float(tpr_after - tpr_before) if pd.notna(tpr_before) and pd.notna(tpr_after) else 0.0
        fpr_delta = float(fpr_after - fpr_before) if pd.notna(fpr_before) and pd.notna(fpr_after) else 0.0
        approval_delta = float(approval_after - approval_before)
        severity = float(abs(tpr_delta) + abs(fpr_delta) + abs(approval_delta))

        row = {
            "segment_key": "|".join([str(v) for v in keys]),
            "breakdown_type": "segment_candidate_source",
            "group_bucket": str(keys[0]),
            "risk_band": str(keys[1]),
            "income_band": str(keys[2]),
            "best_source": str(keys[3]),
            "candidate_source": str(keys[3]),
            "stress_band": "base",
            "canonical_segment_key": build_canonical_segment_key(
                risk_band=str(keys[1]),
                income_band=str(keys[2]),
                stress_band="base",
            ),
            "n_rows": int(len(g)),
            "denied_rows": int((g["denied_base"] == 1).sum()),
            "approval_rate_before": approval_before,
            "approval_rate_after": approval_after,
            "approval_rate_delta": approval_delta,
            "tpr_before": float(tpr_before) if pd.notna(tpr_before) else np.nan,
            "tpr_after": float(tpr_after) if pd.notna(tpr_after) else np.nan,
            "tpr_delta": tpr_delta,
            "fpr_before": float(fpr_before) if pd.notna(fpr_before) else np.nan,
            "fpr_after": float(fpr_after) if pd.notna(fpr_after) else np.nan,
            "fpr_delta": fpr_delta,
            "recourse_success_rate": recourse_success,
            "fairness_guard_demoted_rate": demoted_rate,
            "failure_severity_score": severity,
            "failure_weight": severity,
        }
        rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(
        ["failure_severity_score", "n_rows", "segment_key"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def _equalized_odds_gap_with_rates(
    *,
    y_true: pd.Series,
    y_pred_default: pd.Series,
    group_bucket: pd.Series,
) -> tuple[float, float, float, pd.Series, pd.Series]:
    pos = pd.DataFrame({"g": group_bucket, "y": y_true, "p": y_pred_default})
    pos = pos[pos["y"].astype(int) == 1]
    neg = pd.DataFrame({"g": group_bucket, "y": y_true, "p": y_pred_default})
    neg = neg[neg["y"].astype(int) != 1]
    tpr_rates = pos.groupby("g", dropna=False)["p"].mean() if not pos.empty else pd.Series(dtype=float)
    fpr_rates = neg.groupby("g", dropna=False)["p"].mean() if not neg.empty else pd.Series(dtype=float)
    tpr_gap = float(tpr_rates.max() - tpr_rates.min()) if not tpr_rates.empty else 0.0
    fpr_gap = float(fpr_rates.max() - fpr_rates.min()) if not fpr_rates.empty else 0.0
    eo_gap = float(max(tpr_gap, fpr_gap))
    return eo_gap, tpr_gap, fpr_gap, tpr_rates, fpr_rates


def _safe_rate_gap(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return float(series.max() - series.min())


def _apply_label_aware_fairness_guard(
    *,
    batch_df: pd.DataFrame,
    sampled_sorted: pd.DataFrame,
    group_feature: str,
    target_col: str,
    tau: float,
    rec_cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    fairness_cfg = rec_cfg.get("fairness", {}) if isinstance(rec_cfg.get("fairness", {}), dict) else {}
    guard_cfg = (
        fairness_cfg.get("postprocess_guard", {})
        if isinstance(fairness_cfg.get("postprocess_guard", {}), dict)
        else {}
    )
    enabled = bool(guard_cfg.get("enabled", False))
    out_metrics = {
        "fairness_guard_enabled": int(enabled),
        "fairness_guard_demotion_count": 0,
        "fairness_guard_iteration_count": 0,
        "fairness_guard_stop_reason": "disabled",
        "fairness_guard_initial_equalized_odds_gap_delta": 0.0,
        "fairness_guard_final_equalized_odds_gap_delta": 0.0,
        "fairness_guard_initial_approval_gap_after": 0.0,
        "fairness_guard_final_approval_gap_after": 0.0,
        "fairness_guard_initial_recourse_success_gap": 0.0,
        "fairness_guard_final_recourse_success_gap": 0.0,
    }
    if not enabled:
        return batch_df, out_metrics
    if batch_df.empty:
        out_metrics["fairness_guard_stop_reason"] = "empty_batch"
        return batch_df, out_metrics
    if group_feature not in sampled_sorted.columns or target_col not in sampled_sorted.columns:
        out_metrics["fairness_guard_stop_reason"] = "missing_group_or_target"
        return batch_df, out_metrics

    work = batch_df.copy()
    if "fairness_guard_demoted" not in work.columns:
        work["fairness_guard_demoted"] = 0
    if "fairness_guard_reason" not in work.columns:
        work["fairness_guard_reason"] = ""
    required_defaults: dict[str, Any] = {
        "best_status_reason": "",
        "best_status": "NEEDS_REVIEW",
        "gate_pass_any_candidate": 0,
        "approved_plan_count": 0,
        "best_pd": np.nan,
        "base_pd": np.nan,
        "pd_delta": 0.0,
        "risk_band": "unknown",
        "candidate_pd_delta": 0.0,
        "best_reliability": 0.0,
        "best_worst_risk_margin": 0.0,
        "best_cost_usd": 0.0,
        "denied_base": 0,
        "trajectory_pd_4w": np.nan,
        "trajectory_pd_12w": np.nan,
        "trajectory_pd_24w": np.nan,
        "trajectory_gate_pass_4w": 0,
        "trajectory_gate_pass_12w": 0,
        "trajectory_gate_pass_24w": 0,
        "trajectory_pd_delta_24w": 0.0,
        "trajectory_partial_progress": 0,
        "trajectory_time_to_gate_pass_days": np.nan,
        "trajectory_phase_1_action_count": 0,
        "trajectory_phase_2_action_count": 0,
        "trajectory_phase_3_action_count": 0,
    }
    for col_name, default_value in required_defaults.items():
        if col_name not in work.columns:
            work[col_name] = default_value
    work["best_pd"] = pd.to_numeric(work["best_pd"], errors="coerce")
    work["base_pd"] = pd.to_numeric(work["base_pd"], errors="coerce")
    work["best_pd"] = work["best_pd"].fillna(work["base_pd"]).fillna(float(tau))
    work["base_pd"] = work["base_pd"].fillna(work["best_pd"]).fillna(float(tau))

    group_bucket = _build_group_bucket(sampled_sorted[group_feature]).astype(str).fillna("unknown")
    y_true = pd.to_numeric(sampled_sorted[target_col], errors="coerce").fillna(0).astype(int)
    work["_fair_group"] = group_bucket.values
    work["_fair_y_true"] = y_true.values

    target_eo_delta = float(guard_cfg.get("target_equalized_odds_gap_delta", 0.01))
    target_approval_gap_after = float(guard_cfg.get("target_approval_gap_after", 0.10))
    target_recourse_success_gap = float(guard_cfg.get("target_recourse_success_gap", 0.10))
    min_denied_lift = float(guard_cfg.get("min_denied_to_approved_lift", 0.09))
    min_denied_high_risk_lift = float(guard_cfg.get("min_denied_high_risk_lift", 0.03))
    max_demotions = int(max(0, guard_cfg.get("max_demotions", 40)))
    max_iterations = int(max(1, guard_cfg.get("max_iterations", max(2, max_demotions * 2))))
    candidate_probe_limit = int(max(1, guard_cfg.get("candidate_probe_limit", 12)))
    min_violation_improvement = float(max(0.0, guard_cfg.get("min_violation_improvement", 1e-6)))

    priority_raw = guard_cfg.get("priority_order", ["recourse_success_gap", "approval_gap_after", "equalized_odds_gap_delta"])
    if not isinstance(priority_raw, list) or not priority_raw:
        priority = ["recourse_success_gap", "approval_gap_after", "equalized_odds_gap_delta"]
    else:
        priority = [str(x) for x in priority_raw if str(x).strip()]
        if not priority:
            priority = ["recourse_success_gap", "approval_gap_after", "equalized_odds_gap_delta"]

    before_pred = (work["base_pd"].astype(float) > float(tau)).astype(int)
    before_eo_gap, _, _, _, _ = _equalized_odds_gap_with_rates(
        y_true=work["_fair_y_true"].astype(int),
        y_pred_default=before_pred,
        group_bucket=work["_fair_group"].astype(str),
    )

    def _current_state(df: pd.DataFrame) -> dict[str, Any]:
        after_pred = (df["best_pd"].astype(float) > float(tau)).astype(int)
        after_approve = (after_pred == 0).astype(int)
        eo_gap, tpr_gap, fpr_gap, tpr_rates, fpr_rates = _equalized_odds_gap_with_rates(
            y_true=df["_fair_y_true"].astype(int),
            y_pred_default=after_pred,
            group_bucket=df["_fair_group"].astype(str),
        )
        approval_rates = pd.DataFrame(
            {"g": df["_fair_group"].astype(str), "a": after_approve}
        ).groupby("g", dropna=False)["a"].mean()
        denied_mask = df["denied_base"].astype(int) == 1
        denied_success_rates = (
            pd.DataFrame(
                {
                    "g": df.loc[denied_mask, "_fair_group"].astype(str),
                    "s": df.loc[denied_mask, "gate_pass_any_candidate"].astype(int),
                }
            ).groupby("g", dropna=False)["s"].mean()
            if int(denied_mask.sum()) > 0
            else pd.Series(dtype=float)
        )
        return {
            "eo_gap_after": float(eo_gap),
            "eo_delta": float(eo_gap - before_eo_gap),
            "tpr_gap_after": float(tpr_gap),
            "fpr_gap_after": float(fpr_gap),
            "tpr_rates": tpr_rates,
            "fpr_rates": fpr_rates,
            "approval_rates": approval_rates,
            "approval_gap_after": _safe_rate_gap(approval_rates),
            "denied_success_rates": denied_success_rates,
            "recourse_success_gap": _safe_rate_gap(denied_success_rates),
        }

    def _violation_score(state_in: dict[str, Any]) -> float:
        return float(
            max(0.0, float(state_in["eo_delta"]) - float(target_eo_delta))
            + max(0.0, float(state_in["approval_gap_after"]) - float(target_approval_gap_after))
            + max(0.0, float(state_in["recourse_success_gap"]) - float(target_recourse_success_gap))
        )

    state = _current_state(work)
    out_metrics["fairness_guard_initial_equalized_odds_gap_delta"] = float(state["eo_delta"])
    out_metrics["fairness_guard_initial_approval_gap_after"] = float(state["approval_gap_after"])
    out_metrics["fairness_guard_initial_recourse_success_gap"] = float(state["recourse_success_gap"])

    demotions = 0
    stop_reason = "targets_met"
    for i in range(max_iterations):
        state = _current_state(work)
        eo_bad = float(state["eo_delta"]) > float(target_eo_delta)
        approval_bad = float(state["approval_gap_after"]) > float(target_approval_gap_after)
        recourse_bad = float(state["recourse_success_gap"]) > float(target_recourse_success_gap)
        if not (eo_bad or approval_bad or recourse_bad):
            stop_reason = "targets_met"
            break
        if demotions >= max_demotions:
            stop_reason = "max_demotions_reached"
            break

        selected_group = None
        driver = ""
        for metric_name in priority:
            if metric_name == "recourse_success_gap" and recourse_bad and not state["denied_success_rates"].empty:
                selected_group = str(state["denied_success_rates"].idxmax())
                driver = "recourse_success_gap"
                break
            if metric_name == "approval_gap_after" and approval_bad and not state["approval_rates"].empty:
                selected_group = str(state["approval_rates"].idxmax())
                driver = "approval_gap_after"
                break
            if metric_name == "equalized_odds_gap_delta" and eo_bad:
                if float(state["tpr_gap_after"]) >= float(state["fpr_gap_after"]) and not state["tpr_rates"].empty:
                    selected_group = str(state["tpr_rates"].idxmin())
                    driver = "equalized_odds_gap_delta_tpr"
                    break
                if not state["fpr_rates"].empty:
                    selected_group = str(state["fpr_rates"].idxmin())
                    driver = "equalized_odds_gap_delta_fpr"
                    break
        if selected_group is None:
            stop_reason = "no_group_selected"
            break

        candidates_all = work[
            (work["denied_base"].astype(int) == 1)
            & (work["best_status"].astype(str).str.upper() == "APPROVED")
            & (work["_fair_group"].astype(str) == str(selected_group))
        ].copy()
        if candidates_all.empty:
            stop_reason = "no_candidates_in_selected_group"
            break
        candidates = candidates_all.sort_values(
            ["candidate_pd_delta", "best_reliability", "best_worst_risk_margin", "best_cost_usd", "batch_index"],
            ascending=[True, True, True, False, True],
        )
        denied_mask = work["denied_base"].astype(int) == 1
        denied_count = int(denied_mask.sum())
        denied_approved = int(work.loc[denied_mask, "gate_pass_any_candidate"].astype(int).sum())
        denied_high_mask = denied_mask & (work["risk_band"].astype(str).str.lower() == "high")
        denied_high_count = int(denied_high_mask.sum())
        denied_high_approved = int(work.loc[denied_high_mask, "gate_pass_any_candidate"].astype(int).sum())

        current_score = _violation_score(state)
        accepted = False
        floor_blocked = False
        for _, cand_row in candidates.head(candidate_probe_limit).iterrows():
            idx = int(cand_row["batch_index"])

            next_denied_lift = float((denied_approved - 1) / max(1, denied_count))
            drop_high = int(
                bool(work.loc[idx, "gate_pass_any_candidate"]) and str(work.loc[idx, "risk_band"]).lower() == "high"
            )
            next_high_lift = float((denied_high_approved - drop_high) / max(1, denied_high_count))
            if next_denied_lift < float(min_denied_lift) or next_high_lift < float(min_denied_high_risk_lift):
                floor_blocked = True
                continue

            backup = {
                "fairness_guard_demoted": int(work.loc[idx, "fairness_guard_demoted"]),
                "fairness_guard_reason": str(work.loc[idx, "fairness_guard_reason"] or ""),
                "best_status_reason": str(work.loc[idx, "best_status_reason"] or ""),
                "best_status": str(work.loc[idx, "best_status"] or ""),
                "gate_pass_any_candidate": int(work.loc[idx, "gate_pass_any_candidate"]),
                "approved_plan_count": int(work.loc[idx, "approved_plan_count"]),
                "best_pd": float(work.loc[idx, "best_pd"]),
                "pd_delta": float(work.loc[idx, "pd_delta"]),
                "trajectory_pd_4w": float(work.loc[idx, "trajectory_pd_4w"]),
                "trajectory_pd_12w": float(work.loc[idx, "trajectory_pd_12w"]),
                "trajectory_pd_24w": float(work.loc[idx, "trajectory_pd_24w"]),
                "trajectory_gate_pass_4w": int(work.loc[idx, "trajectory_gate_pass_4w"]),
                "trajectory_gate_pass_12w": int(work.loc[idx, "trajectory_gate_pass_12w"]),
                "trajectory_gate_pass_24w": int(work.loc[idx, "trajectory_gate_pass_24w"]),
                "trajectory_pd_delta_24w": float(work.loc[idx, "trajectory_pd_delta_24w"]),
                "trajectory_partial_progress": int(work.loc[idx, "trajectory_partial_progress"]),
                "trajectory_time_to_gate_pass_days": float(work.loc[idx, "trajectory_time_to_gate_pass_days"]),
                "trajectory_phase_1_action_count": int(work.loc[idx, "trajectory_phase_1_action_count"]),
                "trajectory_phase_2_action_count": int(work.loc[idx, "trajectory_phase_2_action_count"]),
                "trajectory_phase_3_action_count": int(work.loc[idx, "trajectory_phase_3_action_count"]),
            }
            work.loc[idx, "fairness_guard_demoted"] = 1
            work.loc[idx, "fairness_guard_reason"] = str(driver)
            prev_reason = str(work.loc[idx, "best_status_reason"] or "").strip()
            guard_note = f"fairness_guard:{driver}"
            work.loc[idx, "best_status_reason"] = f"{prev_reason} | {guard_note}" if prev_reason else guard_note
            work.loc[idx, "best_status"] = "NEEDS_REVIEW"
            work.loc[idx, "gate_pass_any_candidate"] = 0
            work.loc[idx, "approved_plan_count"] = 0
            work.loc[idx, "best_pd"] = float(work.loc[idx, "base_pd"])
            work.loc[idx, "pd_delta"] = 0.0
            work.loc[idx, "trajectory_pd_4w"] = float(work.loc[idx, "base_pd"])
            work.loc[idx, "trajectory_pd_12w"] = float(work.loc[idx, "base_pd"])
            work.loc[idx, "trajectory_pd_24w"] = float(work.loc[idx, "base_pd"])
            work.loc[idx, "trajectory_gate_pass_4w"] = 0
            work.loc[idx, "trajectory_gate_pass_12w"] = 0
            work.loc[idx, "trajectory_gate_pass_24w"] = 0
            work.loc[idx, "trajectory_pd_delta_24w"] = 0.0
            work.loc[idx, "trajectory_partial_progress"] = 0
            work.loc[idx, "trajectory_time_to_gate_pass_days"] = np.nan
            work.loc[idx, "trajectory_phase_1_action_count"] = 0
            work.loc[idx, "trajectory_phase_2_action_count"] = 0
            work.loc[idx, "trajectory_phase_3_action_count"] = 0

            projected = _current_state(work)
            projected_score = _violation_score(projected)
            if projected_score <= float(current_score - min_violation_improvement):
                state = projected
                demotions += 1
                out_metrics["fairness_guard_iteration_count"] = int(i + 1)
                accepted = True
                break

            work.loc[idx, "fairness_guard_demoted"] = backup["fairness_guard_demoted"]
            work.loc[idx, "fairness_guard_reason"] = backup["fairness_guard_reason"]
            work.loc[idx, "best_status_reason"] = backup["best_status_reason"]
            work.loc[idx, "best_status"] = backup["best_status"]
            work.loc[idx, "gate_pass_any_candidate"] = backup["gate_pass_any_candidate"]
            work.loc[idx, "approved_plan_count"] = backup["approved_plan_count"]
            work.loc[idx, "best_pd"] = backup["best_pd"]
            work.loc[idx, "pd_delta"] = backup["pd_delta"]
            work.loc[idx, "trajectory_pd_4w"] = backup["trajectory_pd_4w"]
            work.loc[idx, "trajectory_pd_12w"] = backup["trajectory_pd_12w"]
            work.loc[idx, "trajectory_pd_24w"] = backup["trajectory_pd_24w"]
            work.loc[idx, "trajectory_gate_pass_4w"] = backup["trajectory_gate_pass_4w"]
            work.loc[idx, "trajectory_gate_pass_12w"] = backup["trajectory_gate_pass_12w"]
            work.loc[idx, "trajectory_gate_pass_24w"] = backup["trajectory_gate_pass_24w"]
            work.loc[idx, "trajectory_pd_delta_24w"] = backup["trajectory_pd_delta_24w"]
            work.loc[idx, "trajectory_partial_progress"] = backup["trajectory_partial_progress"]
            work.loc[idx, "trajectory_time_to_gate_pass_days"] = backup["trajectory_time_to_gate_pass_days"]
            work.loc[idx, "trajectory_phase_1_action_count"] = backup["trajectory_phase_1_action_count"]
            work.loc[idx, "trajectory_phase_2_action_count"] = backup["trajectory_phase_2_action_count"]
            work.loc[idx, "trajectory_phase_3_action_count"] = backup["trajectory_phase_3_action_count"]

        if not accepted:
            stop_reason = "min_lift_floor_or_no_improving_candidate" if floor_blocked else "no_improving_candidate"
            break
    else:
        stop_reason = "max_iterations_reached"

    final_state = _current_state(work)
    out_metrics["fairness_guard_demotion_count"] = int(demotions)
    out_metrics["fairness_guard_stop_reason"] = str(stop_reason)
    out_metrics["fairness_guard_final_equalized_odds_gap_delta"] = float(final_state["eo_delta"])
    out_metrics["fairness_guard_final_approval_gap_after"] = float(final_state["approval_gap_after"])
    out_metrics["fairness_guard_final_recourse_success_gap"] = float(final_state["recourse_success_gap"])

    work = work.drop(columns=["_fair_group", "_fair_y_true"], errors="ignore")
    return work, out_metrics


def _is_denied_target(base_pd: float, tau: float, denied_cfg: dict) -> bool:
    if not bool(denied_cfg.get("enabled", False)):
        return False
    margin = float(denied_cfg.get("activation_margin", 0.0))
    return float(base_pd) > float(tau) + margin


def _apply_denied_distance_profile(
    *,
    base_pd: float,
    tau: float,
    denied_cfg: dict,
    effective: dict[str, Any],
    robust_eff: dict[str, Any],
) -> None:
    profiles = denied_cfg.get("distance_profiles", {}) if isinstance(denied_cfg.get("distance_profiles", {}), dict) else {}
    if not profiles:
        return
    pd_delta = max(0.0, float(base_pd) - float(tau))
    chosen: dict[str, Any] | None = None
    chosen_max = None
    for _, raw in profiles.items():
        if not isinstance(raw, dict):
            continue
        max_delta = raw.get("max_pd_delta")
        if max_delta is None:
            continue
        try:
            max_delta_f = float(max_delta)
        except Exception:
            continue
        if pd_delta <= max_delta_f:
            if chosen is None or chosen_max is None or max_delta_f < chosen_max:
                chosen = raw
                chosen_max = max_delta_f
    if chosen is None:
        return

    if "topk_multiplier" in chosen:
        try:
            topk_mult = max(1.0, float(chosen.get("topk_multiplier", 1.0)))
            effective["topk"] = max(1, int(round(float(effective.get("topk", 1)) * topk_mult)))
        except Exception:
            pass
    if "topk" in chosen:
        try:
            effective["topk"] = max(1, int(chosen.get("topk")))
        except Exception:
            pass
    if isinstance(chosen.get("horizons"), list) and chosen.get("horizons"):
        hs = [int(h) for h in chosen.get("horizons", []) if int(h) in (3, 6, 12)]
        if hs:
            effective["horizons"] = hs
    if isinstance(chosen.get("strategies"), list) and chosen.get("strategies"):
        ss = [str(s) for s in chosen.get("strategies", []) if str(s) in {"conservative", "balanced", "aggressive"}]
        if ss:
            effective["strategies"] = ss

    search_cfg = effective.get("search_cfg", {}) if isinstance(effective.get("search_cfg", {}), dict) else {}
    search_cfg = dict(search_cfg)
    if "enable_weekly_optimizer" in chosen:
        weekly_cfg = search_cfg.get("weekly_optimizer", {}) if isinstance(search_cfg.get("weekly_optimizer", {}), dict) else {}
        weekly_cfg = dict(weekly_cfg)
        weekly_cfg["enabled"] = bool(chosen.get("enable_weekly_optimizer", False))
        search_cfg["weekly_optimizer"] = weekly_cfg
    if "disable_adaptive_steps" in chosen:
        adaptive_cfg = search_cfg.get("adaptive_steps", {}) if isinstance(search_cfg.get("adaptive_steps", {}), dict) else {}
        adaptive_cfg = dict(adaptive_cfg)
        if bool(chosen.get("disable_adaptive_steps", False)):
            adaptive_cfg["enabled"] = False
        search_cfg["adaptive_steps"] = adaptive_cfg
    if "skip_dice" in chosen:
        search_cfg["force_skip_dice"] = bool(chosen.get("skip_dice", False))
    action_budget = search_cfg.get("action_budget", {}) if isinstance(search_cfg.get("action_budget", {}), dict) else {}
    action_budget = dict(action_budget)
    if "max_actions" in chosen:
        try:
            action_budget["max_actions"] = max(1, int(chosen.get("max_actions")))
        except Exception:
            pass
    if action_budget:
        search_cfg["action_budget"] = action_budget
    effective["search_cfg"] = search_cfg

    if "strict_min_reliability" in chosen:
        try:
            robust_eff["min_reliability"] = float(chosen.get("strict_min_reliability"))
        except Exception:
            pass
    if "strict_min_worst_risk_margin" in chosen:
        try:
            robust_eff["min_worst_risk_margin"] = float(chosen.get("strict_min_worst_risk_margin"))
        except Exception:
            pass


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
    allow_denied_target: bool = True,
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
            "min_abs_action_delta": float(rec_cfg.get("min_abs_action_delta", 1e-6)),
            "action_budget": {
                "enabled": action_budget_enabled,
                "max_actions": max_actions_regular,
            },
            "time_budget_ms": int(search_budget_cfg.get("per_customer_time_budget_ms", 0)),
            "candidate_pool_max_size": int(search_budget_cfg.get("candidate_pool_max_size", 0)),
            "skip_dice_when_internal_approved": bool(search_budget_cfg.get("skip_dice_when_internal_approved", False)),
            "skip_dice_for_non_denied": bool(search_budget_cfg.get("skip_dice_for_non_denied", False)),
            "force_skip_dice": False,
            "novelty_weight": float(search_budget_cfg.get("novelty_weight", 0.0)),
            "hard_time_budget_enforcement": bool(search_budget_cfg.get("hard_time_budget_enforcement", True)),
            "min_remaining_budget_for_dice_ms": int(search_budget_cfg.get("min_remaining_budget_for_dice_ms", 0)),
            "min_remaining_budget_for_rule_ms": int(search_budget_cfg.get("min_remaining_budget_for_rule_ms", 0)),
            "hard_max_dice_timeout_ms": int(search_budget_cfg.get("hard_max_dice_timeout_ms", 0)),
            "dice_only_high_risk_denied": bool(search_budget_cfg.get("dice_only_high_risk_denied", False)),
            "stage1_filter_multiplier": float(search_budget_cfg.get("stage1_filter_multiplier", 1.0)),
            "stage1_per_source_cap": int(search_budget_cfg.get("stage1_per_source_cap", 0)),
            "enable_deterministic_fallback": bool(search_budget_cfg.get("enable_deterministic_fallback", True)),
            "sync_fast_path_enabled": bool(search_budget_cfg.get("sync_fast_path_enabled", True)),
            "sync_time_budget_ms": int(search_budget_cfg.get("sync_time_budget_ms", 500)),
            "async_deep_path_enabled": bool(search_budget_cfg.get("async_deep_path_enabled", True)),
        },
    }
    regular_horizons = search_budget_cfg.get("regular_horizons")
    if isinstance(regular_horizons, list) and regular_horizons:
        filtered_h = [int(h) for h in regular_horizons if int(h) in (3, 6, 12)]
        if filtered_h:
            effective["horizons"] = filtered_h
    regular_strategies = search_budget_cfg.get("regular_strategies")
    if isinstance(regular_strategies, list) and regular_strategies:
        filtered_s = [str(s) for s in regular_strategies if str(s) in {"conservative", "balanced", "aggressive"}]
        if filtered_s:
            effective["strategies"] = filtered_s
    regular_topk = search_budget_cfg.get("regular_topk")
    if regular_topk is not None:
        try:
            effective["topk"] = max(1, int(regular_topk))
        except Exception:
            pass
    robust_eff = dict(robust_cfg or {})
    dice_eff = dict(dice_cfg or {})

    if (not allow_denied_target) or (not _is_denied_target(base_pd, tau, denied_cfg)):
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
        filtered_h = [int(h) for h in denied_horizons if int(h) in (3, 6, 12)]
        if filtered_h:
            effective["horizons"] = filtered_h

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
    _apply_denied_distance_profile(
        base_pd=base_pd,
        tau=tau,
        denied_cfg=denied_cfg,
        effective=effective,
        robust_eff=robust_eff,
    )
    return effective, robust_eff, dice_eff


def _dice_plan_record(
    *,
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
    feasibility_profile: dict[str, Any] | None = None,
    segment_context: dict[str, Any] | None = None,
    source_tag: str = "dice",
) -> PlanRecord:
    plan_actions: list[PlanAction] = []

    for a in actions:
        feature = str(a["feature_name"])
        spec = get_action_spec(feature)
        action_meta = get_action_metadata(feature, action_month=max(1, int(spec.time_months)))
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
        if str(detail["status"]) == "rejected":
            continue
        action_month = max(1, int(spec.time_months))
        week_start = int(((action_month - 1) * 4) + 1)
        week_end = int(action_month * 4)
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
                action_title=str(action_meta.get("action_title") or ""),
                action_group_id=str(action_meta.get("action_group_id") or ""),
                composite_action=bool(action_meta.get("composite_action", False)),
                requires_institutional_approval=bool(action_meta.get("requires_institutional_approval", False)),
                approval_pending_semantic_only=bool(action_meta.get("approval_pending_semantic_only", False)),
                prerequisite_tags=list(action_meta.get("prerequisite_tags", [])),
                conflict_tags=list(action_meta.get("conflict_tags", [])),
                action_status=str(detail["status"]),
                action_status_reason=detail.get("status_reason"),
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
        plan_id=f"{run_id}_{customer_id}_{source_tag}_{idx}",
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
    return annotate_plan_execution_probability(
        plan,
        base_pd=base_pd,
        customer_context={str(k): row.get(k) for k in row.index},
        segment_context=segment_context,
    )


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
        {"macro": m_cfg, "batch": {"n_customers": args.n_customers, "sample_seed": args.sample_seed, "group_feature": args.group_feature}},
    )
    run_ctx = create_run_context(cfg, base_artifact_dir="artifacts/runs")

    contract = load_feature_contract(base_cfg.get("features_config", "configs/features_48.yaml"))
    feature_cols = contract["features"]
    target_col = contract["target"]

    processed_root = Path(base_cfg.get("paths", {}).get("processed_data", "data/processed"))
    test_path = processed_root / "test.parquet"
    train_path = processed_root / "train.parquet"
    test_df = pd.read_parquet(test_path)
    train_df = pd.read_parquet(train_path)
    train_file_hash = hash_file(train_path)
    test_file_hash = hash_file(test_path)
    config_hash = hash_config(cfg)

    n = max(1, min(int(args.n_customers), len(test_df)))
    sampled = test_df.sample(n=n, random_state=int(args.sample_seed)).reset_index().rename(columns={"index": "source_row_index"})
    logger.info("Batch sample prepared: n=%s from test_rows=%s", n, len(test_df))

    model, calibrator, manifest, _ = load_model_bundle(
        base_path=model_cfg.get("registry", {}).get("path", "artifacts/models"),
        model_version=str(args.model_version).strip() or None,
        manifest_path=str(args.model_manifest).strip() or None,
    )
    tau = float(model_cfg.get("decision", {}).get("tau_0", 0.35))
    base_proba = pd.Series(predict_proba_pd(model, calibrator, sampled[feature_cols]), index=sampled.index, dtype=float)

    graph = None
    graph_out = Path(c_cfg.get("graph", {}).get("output_path", "artifacts/models/causal_graph.json"))
    if graph_out.exists():
        graph = load_graph(graph_out)
    else:
        logger.warning("Causal graph missing; causal penalty set to 0 in batch run. path=%s", graph_out)

    horizons = [int(v) for v in rec_cfg.get("horizons", [3, 6, 12])]
    strategies = [str(v) for v in rec_cfg.get("strategies", ["conservative", "balanced", "aggressive"])]
    robust_cfg_base = rec_cfg.get("robust", {}) if isinstance(rec_cfg.get("robust", {}), dict) else {}
    min_reliability_global = robust_cfg_base.get("min_reliability")
    min_worst_margin_global = robust_cfg_base.get("min_worst_risk_margin")
    min_reliability_global_f = float(min_reliability_global) if min_reliability_global is not None else None
    min_worst_margin_global_f = float(min_worst_margin_global) if min_worst_margin_global is not None else None
    robust_objective = str(robust_cfg_base.get("objective", "cvar"))
    robust_cvar_quantile = float(robust_cfg_base.get("cvar_quantile", 0.9))
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
    robust_cfg_base = _align_gate_uncertainty_with_validator(robust_cfg_base, uncertainty_cfg)

    macro_snapshot = load_macro_snapshot_mock()
    msi = compute_macro_stress_index(macro_snapshot, m_cfg.get("stress_index_weights", {}))
    base_alpha = float(s_cfg.get("confidence", {}).get("base_alpha", 0.05))
    high_stress_alpha = float(s_cfg.get("confidence", {}).get("high_stress_alpha", 0.01))
    stress_threshold = float(m_cfg.get("stress_threshold", 0.7))
    alpha = dynamic_alpha(msi, base_alpha=base_alpha, high_stress_alpha=high_stress_alpha, threshold=stress_threshold)
    bootstrap_b = int(s_cfg.get("bootstrap", {}).get("B", 500))

    dice_cfg_base = rec_cfg.get("dice", {}) if isinstance(rec_cfg.get("dice", {}), dict) else {}
    actionable = [f for f in sorted(get_actionable_features()) if f in feature_cols]
    topk_default = int(rec_cfg.get("shap", {}).get("topk_features", 10))
    shap_cfg = rec_cfg.get("shap", {}) if isinstance(rec_cfg.get("shap", {}), dict) else {}
    local_reason_background_df: pd.DataFrame | None = None
    batch_background_samples = int(shap_cfg.get("batch_background_samples", 0))
    if batch_background_samples > 0:
        local_reason_background_df = train_df[feature_cols].sample(
            n=min(len(train_df), batch_background_samples),
            random_state=int(shap_cfg.get("stability_seed", 42)),
        )
    segment_caps_cfg = rec_cfg.get("segment_caps", {}) if isinstance(rec_cfg.get("segment_caps", {}), dict) else {}
    q_cfg = segment_caps_cfg.get("income_quantiles", [0.25, 0.50, 0.75])
    q_list = list(q_cfg) if isinstance(q_cfg, list) else [0.25, 0.50, 0.75]
    income_edges = _compute_income_edges(sampled.get("annual_inc", pd.Series(dtype=float)), q_list)
    feasibility_cfg = rec_cfg.get("feasibility", {}) if isinstance(rec_cfg.get("feasibility", {}), dict) else {}
    feasibility_profile: dict[str, Any] | None = None
    if bool(feasibility_cfg.get("enabled", False)):
        profile_path = str(feasibility_cfg.get("profile_path", "")).strip()
        if profile_path:
            feasibility_profile = load_config(profile_path)
    feasibility_internal_profile = feasibility_profile if bool(feasibility_cfg.get("enforce_on_internal", True)) else None
    feasibility_dice_profile = feasibility_profile if bool(feasibility_cfg.get("enforce_on_dice", True)) else None
    fairness_cfg = rec_cfg.get("fairness", {}) if isinstance(rec_cfg.get("fairness", {}), dict) else {}
    fairness_group_col = str(fairness_cfg.get("group_feature", args.group_feature))
    group_penalties: dict[str, float] = {}
    if fairness_group_col in sampled.columns:
        fairness_scored = pd.DataFrame(
            {
                fairness_group_col: sampled[fairness_group_col].astype(str).fillna("unknown"),
                "approve": (base_proba <= tau).astype(int),
            }
        )
        group_penalties = build_group_advantage_penalties(
            fairness_scored,
            group_col=fairness_group_col,
            approval_col="approve",
            tolerance=float(fairness_cfg.get("advantage_tolerance", 0.01)),
        )
    denied_target_selection_penalty_weight = max(
        0.0, float(fairness_cfg.get("denied_target_selection_penalty_weight", 0.0))
    )
    denied_dice_selection_penalty_weight = max(
        0.0,
        float(
            fairness_cfg.get(
                "denied_dice_selection_penalty_weight",
                denied_target_selection_penalty_weight,
            )
        ),
    )
    denied_target_fair_share = float(
        fairness_cfg.get(
            "denied_target_fair_share",
            1.0 if denied_target_selection_penalty_weight > 0 else 0.0,
        )
    )
    denied_target_fair_share = min(1.0, max(0.0, denied_target_fair_share))
    denied_dice_fair_share = float(
        fairness_cfg.get(
            "denied_dice_fair_share",
            1.0 if denied_dice_selection_penalty_weight > 0 else 0.0,
        )
    )
    denied_dice_fair_share = min(1.0, max(0.0, denied_dice_fair_share))
    disadvantaged_target_pd_extra = max(0.0, float(fairness_cfg.get("disadvantaged_target_pd_extra", 0.0)))
    disadvantaged_penalty_threshold = max(0.0, float(fairness_cfg.get("disadvantaged_penalty_threshold", 0.0)))
    disadvantaged_extra_only_denied_target = bool(fairness_cfg.get("disadvantaged_target_pd_extra_only_denied_target", True))
    trajectory_cfg = rec_cfg.get("trajectory", {}) if isinstance(rec_cfg.get("trajectory", {}), dict) else {}
    trajectory_enabled = bool(trajectory_cfg.get("enabled", True))
    trajectory_partial_progress_min_pd_delta = max(
        0.0,
        float(trajectory_cfg.get("partial_progress_min_pd_delta", 0.05)),
    )

    search_budget_cfg = rec_cfg.get("search_budget", {}) if isinstance(rec_cfg.get("search_budget", {}), dict) else {}
    high_risk_bridge_cfg = (
        rec_cfg.get("high_risk_bridge_kpi", {})
        if isinstance(rec_cfg.get("high_risk_bridge_kpi", {}), dict)
        else {}
    )
    high_risk_bridge_enabled = bool(high_risk_bridge_cfg.get("enabled", True))
    high_risk_bridge_target_pd_delta_to_tau = max(
        0.0, float(high_risk_bridge_cfg.get("target_pd_delta_to_tau", 0.20))
    )
    high_risk_bridge_min_pd_reduction = max(
        0.0, float(high_risk_bridge_cfg.get("min_pd_reduction", 0.08))
    )
    denied_target_max_customers_cfg = int(search_budget_cfg.get("denied_target_max_customers", 0))
    denied_target_dynamic_max_enabled = bool(search_budget_cfg.get("denied_target_dynamic_max_enabled", True))
    denied_target_dynamic_max_cap = int(search_budget_cfg.get("denied_target_dynamic_max_cap", 300))
    denied_target_segment_reservation_enabled = bool(search_budget_cfg.get("denied_target_segment_reservation_enabled", True))
    denied_target_risk_band_reservation = _normalize_risk_band_reservation(
        search_budget_cfg.get(
            "denied_target_risk_band_reservation",
            {"high": 0.50, "mid": 0.25, "near": 0.25},
        )
    )
    denied_target_max_customers = denied_target_max_customers_cfg
    denied_dice_max_customers = int(search_budget_cfg.get("denied_dice_max_customers", 0))
    denied_target_eligible_batch_indices: set[int] = set()
    denied_dice_eligible_batch_indices: set[int] = set()
    if denied_target_max_customers > 0 or denied_dice_max_customers > 0:
        denied_mask_pre = (base_proba > tau)
        denied_candidates = sampled.loc[denied_mask_pre].copy()
        denied_candidates["base_pd"] = base_proba[denied_mask_pre].astype(float).values
        denied_candidates["pd_distance_to_tau"] = (base_proba[denied_mask_pre] - tau).abs().values
        denied_candidates["risk_band"] = denied_candidates["base_pd"].map(
            lambda v: _risk_band_from_pd(float(v), tau, segment_caps_cfg)
        )
        denied_candidates["group_penalty"] = 0.0
        if group_penalties and fairness_group_col in denied_candidates.columns:
            denied_candidates["group_penalty"] = (
                denied_candidates[fairness_group_col]
                .astype(str)
                .fillna("unknown")
                .map(lambda g: lookup_group_penalty(g, group_penalties))
                .astype(float)
            )
        denied_candidates["target_priority_score"] = denied_candidates["pd_distance_to_tau"] * (
            1.0 + (denied_target_selection_penalty_weight * denied_candidates["group_penalty"])
        )
        denied_candidates["dice_priority_score"] = denied_candidates["pd_distance_to_tau"] * (
            1.0 + (denied_dice_selection_penalty_weight * denied_candidates["group_penalty"])
        )

        if denied_target_dynamic_max_enabled and denied_target_max_customers_cfg > 0:
            denied_target_max_customers = min(
                int(len(denied_candidates)),
                max(1, int(denied_target_dynamic_max_cap)),
            )

        base_ranked = denied_candidates.sort_values(
            ["pd_distance_to_tau", "source_row_index"], ascending=[True, True]
        )
        denied_target_ranked = denied_candidates.sort_values(
            ["target_priority_score", "pd_distance_to_tau", "source_row_index"],
            ascending=[True, True, True],
        )
        denied_dice_ranked = denied_candidates.sort_values(
            ["dice_priority_score", "pd_distance_to_tau", "source_row_index"],
            ascending=[True, True, True],
        )

        def _select_mixed_quota(
            *,
            fair_ranked_df: pd.DataFrame,
            perf_ranked_df: pd.DataFrame,
            max_customers: int,
            fair_share: float,
        ) -> list[int]:
            if max_customers <= 0:
                return []
            if fair_share <= 0.0:
                return [int(i) for i in perf_ranked_df.index[:max_customers].tolist()]
            if fair_share >= 1.0:
                return [int(i) for i in fair_ranked_df.index[:max_customers].tolist()]

            fair_quota = min(max_customers, int(round(float(max_customers) * float(fair_share))))
            selected: list[int] = []
            selected_set: set[int] = set()

            for idx in fair_ranked_df.index.tolist():
                if len(selected) >= fair_quota:
                    break
                idx_i = int(idx)
                if idx_i in selected_set:
                    continue
                selected.append(idx_i)
                selected_set.add(idx_i)

            for idx in perf_ranked_df.index.tolist():
                if len(selected) >= max_customers:
                    break
                idx_i = int(idx)
                if idx_i in selected_set:
                    continue
                selected.append(idx_i)
                selected_set.add(idx_i)
            return selected

        def _select_segment_reserved_quota(
            *,
            fair_ranked_df: pd.DataFrame,
            perf_ranked_df: pd.DataFrame,
            max_customers: int,
            fair_share: float,
            reservation: dict[str, float],
        ) -> set[int]:
            if max_customers <= 0:
                return set()
            if not denied_target_segment_reservation_enabled:
                return set(
                    _select_mixed_quota(
                        fair_ranked_df=fair_ranked_df,
                        perf_ranked_df=perf_ranked_df,
                        max_customers=max_customers,
                        fair_share=fair_share,
                    )
                )
            selected: list[int] = []
            selected_set: set[int] = set()
            for band in ("high", "mid", "near"):
                quota = int(round(float(max_customers) * float(reservation.get(band, 0.0))))
                if quota <= 0:
                    continue
                fair_band = fair_ranked_df[fair_ranked_df["risk_band"] == band]
                perf_band = perf_ranked_df[perf_ranked_df["risk_band"] == band]
                if fair_band.empty and perf_band.empty:
                    continue
                band_selected = _select_mixed_quota(
                    fair_ranked_df=fair_band,
                    perf_ranked_df=perf_band,
                    max_customers=min(quota, int(max(1, len(perf_band)))),
                    fair_share=fair_share,
                )
                for idx_i in band_selected:
                    if idx_i in selected_set:
                        continue
                    selected.append(idx_i)
                    selected_set.add(idx_i)
                    if len(selected) >= max_customers:
                        return set(selected[:max_customers])

            if len(selected) < max_customers:
                global_selected = _select_mixed_quota(
                    fair_ranked_df=fair_ranked_df,
                    perf_ranked_df=perf_ranked_df,
                    max_customers=max_customers,
                    fair_share=fair_share,
                )
                for idx_i in global_selected:
                    if idx_i in selected_set:
                        continue
                    selected.append(idx_i)
                    selected_set.add(idx_i)
                    if len(selected) >= max_customers:
                        break
            return set(selected[:max_customers])

        if denied_target_max_customers > 0:
            denied_target_eligible_batch_indices = _select_segment_reserved_quota(
                fair_ranked_df=denied_target_ranked,
                perf_ranked_df=base_ranked,
                max_customers=denied_target_max_customers,
                fair_share=denied_target_fair_share,
                reservation=denied_target_risk_band_reservation,
            )
        if denied_dice_max_customers > 0:
            denied_dice_eligible_batch_indices = set(
                _select_mixed_quota(
                    fair_ranked_df=denied_dice_ranked,
                    perf_ranked_df=base_ranked,
                    max_customers=denied_dice_max_customers,
                    fair_share=denied_dice_fair_share,
                )
            )

    rows: list[dict] = []
    t0_all = time.perf_counter()

    def _process_one(i: int, row: pd.Series, base_pd_i: float) -> dict:
        t0 = time.perf_counter()
        out = {
            "batch_index": int(i),
            "source_row_index": int(row["source_row_index"]),
            "customer_id": f"batch_{int(i)}",
            "base_pd": base_pd_i,
            "denied_base": int(base_pd_i > tau),
            "denied_target_mode": 0,
            "high_risk_profile_applied": 0,
            "high_risk_profile_reason": "",
            "income_band": "",
            "risk_band": "",
            "stress_band": "base",
            "segment_caps_applied": 0,
            "cap_multiplier_income": 1.0,
            "cap_multiplier_risk": 1.0,
            "cap_multiplier_total": 1.0,
            "fairness_penalty": 0.0,
            "fairness_group": "",
            "fairness_cap_boost_applied": 0,
            "fairness_cap_boost_factor": 1.0,
            "best_pd": base_pd_i,
            "best_candidate_pd": base_pd_i,
            "candidate_pd_delta": 0.0,
            "pd_delta": 0.0,
            "high_risk_bridge_hit": 0,
            "best_status": "ERROR",
            "best_status_reason": "",
            "best_constraint_status": "invalid",
            "best_source": "",
            "best_plan_id": "",
            "best_horizon_months": 0,
            "best_strategy": "",
            "best_action_count": 0,
            "best_cost_usd": 0.0,
            "best_proximity_l1": 0.0,
            "best_robust_score": 0.0,
            "best_plan_execution_probability": 0.0,
            "best_mean_action_execution_probability": 0.0,
            "best_nominal_pd_improvement": 0.0,
            "best_expected_pd_improvement": 0.0,
            "best_offer_plan": 0,
            "best_rankable_offer": 0,
            "best_rankable_offer_count": 0,
            "best_offer_type": "",
            "best_offer_policy_arm": "",
            "best_offer_family": "",
            "best_offer_scoring_profile": "",
            "best_term_generation_rule": "",
            "best_offer_acceptance_probability": 0.0,
            "best_combined_plan_realization_probability": 0.0,
            "best_expected_recovery_proxy": 0.0,
            "best_approval_rate_proxy_delta": 0.0,
            "best_default_rate_90d_proxy_delta": 0.0,
            "best_avg_margin_90d_proxy_delta": 0.0,
            "best_governance_safe_offer": 0,
            "best_execution_scenario": "failed_execution",
            "best_execution_rate": 0.0,
            "best_partial_execution": 1,
            "best_mixed_execution": 0,
            "best_failed_execution": 1,
            "best_expected_partial_progress": 0,
            "best_missed_action": 0,
            "best_missed_actions_streak": 0,
            "best_timeline_steps_json": "[]",
            "best_phases_json": "[]",
            "best_trajectory_checkpoints_json": "[]",
            "best_ci_high": np.nan,
            "best_reliability": np.nan,
            "best_worst_risk_margin": np.nan,
            "trajectory_pd_4w": base_pd_i,
            "trajectory_pd_12w": base_pd_i,
            "trajectory_pd_24w": base_pd_i,
            "trajectory_gate_pass_4w": 0,
            "trajectory_gate_pass_12w": 0,
            "trajectory_gate_pass_24w": 0,
            "trajectory_pd_delta_24w": 0.0,
            "trajectory_partial_progress": 0,
            "trajectory_time_to_gate_pass_days": np.nan,
            "trajectory_phase_1_action_count": 0,
            "trajectory_phase_2_action_count": 0,
            "trajectory_phase_3_action_count": 0,
            "trajectory_status": "degraded",
            "trajectory_current_phase": "phase_1_stabilize",
            "trajectory_next_review_week": 4,
            "trajectory_phase_transition_reason": "no_plan_selected",
            "trajectory_replanned_from_phase": "",
            "trajectory_soft_regression_penalty": 0.0,
            "trajectory_policy_label": "",
            "trajectory_policy_score": 0.0,
            "denied_not_approved_root_cause": "",
            "approved_plan_count": 0,
            "internal_plan_count": 0,
            "internal_approved_plan_count": 0,
            "internal_gate_pass_any": 0,
            "dice_plan_count": 0,
            "dice_approved_plan_count": 0,
            "dice_gate_pass_any": 0,
            "rule_plan_count": 0,
            "rule_approved_plan_count": 0,
            "rule_gate_pass_any": 0,
            "candidate_pool_count": 0,
            "candidate_pool_approved_count": 0,
            "candidate_pool_diversity_index": 0.0,
            "candidate_source_entropy": 0.0,
            "action_realism_events_json": "[]",
            "action_realism_valid_action_count": 0,
            "action_realism_clipped_action_count": 0,
            "action_realism_rejected_action_count": 0,
            "action_realism_infeasible_plan_count": 0,
            "action_realism_top_rejection_reason": "",
            "action_constraint_events_json": "[]",
            "action_constraint_repair_applied_count": 0,
            "action_constraint_approval_pending_action_count": 0,
            "action_constraint_invalid_combination_count": 0,
            "action_constraint_top_reason": "",
            "had_any_candidate": 0,
            "gate_pass_any_candidate": 0,
            "dice_backend": "",
            "dice_success": 0,
            "dice_fallback_reason": "",
            "dice_attempted_method_count": 0,
            "fast_reason_mode": 0,
            "search_profile_budget_tuned": 0,
            "internal_rescue_used": 0,
            "search_time_budget_ms": 0,
            "search_elapsed_before_dice_ms": 0.0,
            "sync_elapsed_ms": 0.0,
            "async_deep_path_used": 0,
            "budget_overshoot": 0,
            "budget_overshoot_ms": 0.0,
            "deadline_abort": 0,
            "fallback_triggered": 0,
            "fallback_reason": "",
            "error_type": "",
            "error_message": "",
            "elapsed_ms": 0.0,
        }
        try:
            allow_denied_target = True
            if denied_target_max_customers > 0 and base_pd_i > tau and int(i) not in denied_target_eligible_batch_indices:
                allow_denied_target = False
            search_profile, robust_cfg, dice_cfg = _effective_recourse_search(
                base_pd=base_pd_i,
                tau=tau,
                topk=topk_default,
                horizons=horizons,
                strategies=strategies,
                robust_cfg=robust_cfg_base,
                dice_cfg=dice_cfg_base,
                rec_cfg=rec_cfg,
                allow_denied_target=allow_denied_target,
            )
            out["denied_target_mode"] = int(bool(search_profile.get("is_denied_target", False)))
            segment_context = _build_segment_context(
                row=row,
                base_pd=base_pd_i,
                tau=tau,
                denied_mode=bool(search_profile.get("is_denied_target", False)),
                segment_caps_cfg=segment_caps_cfg,
                income_edges=income_edges,
            )
            out["income_band"] = str(segment_context.get("income_band", ""))
            out["risk_band"] = str(segment_context.get("risk_band", ""))
            out["stress_band"] = _stress_band_from_row(row)
            out["segment_caps_applied"] = int(bool(segment_context.get("segment_caps_applied", False)))
            out["cap_multiplier_income"] = float(segment_context.get("cap_multiplier_income", 1.0))
            out["cap_multiplier_risk"] = float(segment_context.get("cap_multiplier_risk", 1.0))
            out["cap_multiplier_total"] = float(segment_context.get("cap_multiplier", 1.0))
            search_cfg_patch = search_profile.get("search_cfg", {}) if isinstance(search_profile.get("search_cfg", {}), dict) else {}
            search_cfg_patch = dict(search_cfg_patch)
            phase1_fast_cfg = (
                rec_cfg.get("phase1_fast_track", {})
                if isinstance(rec_cfg.get("phase1_fast_track", {}), dict)
                else {}
            )
            if phase1_fast_cfg:
                search_cfg_patch["phase1_fast_track"] = dict(phase1_fast_cfg)
            fairness_group_value = row.get(fairness_group_col) if fairness_group_col in row.index else None
            out["fairness_group"] = _safe_str(fairness_group_value, "")
            fairness_penalty = lookup_group_penalty(fairness_group_value, group_penalties) if fairness_group_col in row.index else 0.0
            segment_context, fairness_target_pd_extra, fairness_cap_boost_applied, fairness_cap_boost_factor = _apply_fairness_segment_cap_boost(
                segment_context=segment_context,
                rec_cfg=rec_cfg,
                fairness_penalty=float(fairness_penalty),
                denied_mode=bool(search_profile.get("is_denied_target", False)),
            )
            out["fairness_cap_boost_applied"] = int(fairness_cap_boost_applied)
            out["fairness_cap_boost_factor"] = float(fairness_cap_boost_factor)
            out["cap_multiplier_total"] = float(segment_context.get("cap_multiplier", out["cap_multiplier_total"]))
            if disadvantaged_target_pd_extra > 0.0:
                in_scope = bool(search_profile.get("is_denied_target", False)) if disadvantaged_extra_only_denied_target else True
                if in_scope and float(fairness_penalty) <= disadvantaged_penalty_threshold:
                    current_extra = float(search_cfg_patch.get("target_pd_margin_extra", 0.0))
                    search_cfg_patch["target_pd_margin_extra"] = max(current_extra, disadvantaged_target_pd_extra)
            if fairness_target_pd_extra > 0.0:
                current_extra = float(search_cfg_patch.get("target_pd_margin_extra", 0.0))
                search_cfg_patch["target_pd_margin_extra"] = max(current_extra, float(fairness_target_pd_extra))
            search_cfg_patch["segment_context"] = segment_context
            search_profile["search_cfg"] = search_cfg_patch

            out["fairness_penalty"] = float(fairness_penalty)

            search_profile, robust_cfg, dice_cfg, high_risk_profile_meta = _resolve_high_risk_profile_activation(
                search_profile=search_profile,
                robust_cfg=robust_cfg,
                dice_cfg=dice_cfg,
                rec_cfg=rec_cfg,
                segment_context=segment_context,
            )
            robust_cfg = _apply_group_fairness_recourse_balance(
                robust_cfg=robust_cfg,
                rec_cfg=rec_cfg,
                fairness_penalty=float(fairness_penalty),
            )
            min_reliability = robust_cfg.get("min_reliability")
            min_worst_margin = robust_cfg.get("min_worst_risk_margin")
            min_reliability_f = float(min_reliability) if min_reliability is not None else None
            min_worst_margin_f = float(min_worst_margin) if min_worst_margin is not None else None
            out["high_risk_profile_applied"] = int(bool(high_risk_profile_meta.get("applied", False)))
            out["high_risk_profile_reason"] = str(high_risk_profile_meta.get("reason", ""))
            deny_mode = bool(search_profile.get("is_denied_target", False))
            high_risk_denied = bool(deny_mode and str(segment_context.get("risk_band", "")).strip().lower() == "high")
            pre_tune = search_profile
            pre_tune_search_cfg = (
                search_profile.get("search_cfg", {}) if isinstance(search_profile.get("search_cfg", {}), dict) else {}
            )
            time_budget_hint_ms = int(pre_tune_search_cfg.get("time_budget_ms", 0))
            search_profile = _tune_internal_search_profile_for_budget(
                search_profile,
                time_budget_ms=time_budget_hint_ms,
                denied_mode=deny_mode,
                risk_band=str(segment_context.get("risk_band", "")),
            )
            out["search_profile_budget_tuned"] = int(search_profile != pre_tune)
            prefer_fast_reasons = bool(high_risk_denied or (time_budget_hint_ms > 0 and time_budget_hint_ms <= 1200))
            out["fast_reason_mode"] = int(prefer_fast_reasons)
            local_candidate_features = _local_reason_candidates(
                model=model,
                row=row,
                feature_cols=feature_cols,
                actionable=actionable,
                topk=max(int(search_profile["topk"]), topk_default),
                shap_cfg=shap_cfg,
                prefer_fast=prefer_fast_reasons,
                background_df=local_reason_background_df,
            )
            if not local_candidate_features:
                local_candidate_features = list(actionable)
            local_candidate_features = _apply_phase1_feature_boost(
                candidate_features=local_candidate_features,
                rec_cfg=rec_cfg,
                denied_mode=deny_mode,
                risk_band=str(segment_context.get("risk_band", "")),
                actionable=actionable,
            )

            search_cfg = search_profile.get("search_cfg", {}) if isinstance(search_profile.get("search_cfg", {}), dict) else {}
            time_budget_ms = int(search_cfg.get("time_budget_ms", 0))
            hard_budget_enforced = bool(search_cfg.get("hard_time_budget_enforcement", True))
            sync_fast_path_enabled = bool(search_cfg.get("sync_fast_path_enabled", True))
            sync_time_budget_ms = int(search_cfg.get("sync_time_budget_ms", 500))
            async_deep_path_enabled = bool(search_cfg.get("async_deep_path_enabled", True))
            out["search_time_budget_ms"] = int(time_budget_ms)
            deadline_ts = (
                (t0 + (float(time_budget_ms) / 1000.0))
                if (time_budget_ms > 0 and hard_budget_enforced)
                else None
            )
            runtime_diag: dict[str, Any] = {}

            plans = generate_nine_plans(
                customer_id=out["customer_id"],
                run_id=run_ctx.run_id,
                row=row,
                model=model,
                calibrator=calibrator,
                feature_cols=feature_cols,
                graph=graph,
                tau=tau,
                horizons=search_profile["horizons"],
                strategies=search_profile["strategies"],
                candidate_features=local_candidate_features,
                topk=int(search_profile["topk"]),
                scenarios=scenarios,
                threshold_shift_per_msi_unit=threshold_shift,
                robust_cfg=robust_cfg,
                search_cfg=search_profile.get("search_cfg", {}),
                fairness_penalty=fairness_penalty,
                feasibility_profile=feasibility_internal_profile,
                segment_context=segment_context,
                base_pd=base_pd_i,
                deadline_ts=deadline_ts,
                runtime_diag=runtime_diag,
            )
            action_realism_events = list(runtime_diag.get("action_realism_events", []))
            out["action_realism_events_json"] = json.dumps(action_realism_events, ensure_ascii=False)
            out["action_realism_valid_action_count"] = int(runtime_diag.get("action_realism_valid_action_count", 0))
            out["action_realism_clipped_action_count"] = int(runtime_diag.get("action_realism_clipped_action_count", 0))
            out["action_realism_rejected_action_count"] = int(runtime_diag.get("action_realism_rejected_action_count", 0))
            out["action_realism_infeasible_plan_count"] = int(runtime_diag.get("action_realism_infeasible_plan_count", 0))
            out["action_realism_top_rejection_reason"] = _top_action_realism_rejection_reason(action_realism_events)
            action_constraint_events = list(runtime_diag.get("action_constraint_events", []))
            out["action_constraint_events_json"] = json.dumps(action_constraint_events, ensure_ascii=False)
            out["action_constraint_repair_applied_count"] = int(
                runtime_diag.get("action_constraint_repair_applied_count", 0)
            )
            out["action_constraint_approval_pending_action_count"] = int(
                runtime_diag.get("action_constraint_approval_pending_action_count", 0)
            )
            out["action_constraint_invalid_combination_count"] = int(
                runtime_diag.get("action_constraint_invalid_combination_count", 0)
            )
            out["action_constraint_top_reason"] = _top_constraint_reason(
                action_constraint_events,
                event_type="repair_dropped",
            )
            validated: list[PlanRecord] = []
            for p in plans:
                if deadline_ts is not None and time.perf_counter() >= float(deadline_ts):
                    runtime_diag["deadline_aborted"] = True
                    break
                validated.append(
                    validate_plan(
                        p,
                        tau=tau,
                        alpha=alpha,
                        bootstrap_b=bootstrap_b,
                        scenarios=scenarios,
                        threshold_shift_per_msi_unit=threshold_shift,
                        robust_objective=robust_objective,
                        robust_cvar_quantile=robust_cvar_quantile,
                        min_reliability=min_reliability_f,
                        min_worst_risk_margin=min_worst_margin_f,
                        uncertainty_cfg=uncertainty_cfg,
                        segment_context=segment_context,
                        )
                    )
            has_non_rejected_internal = any(
                not _is_rejected_like(getattr(p, "status", ""))
                for p in validated
            )
            if deny_mode and (not validated or (bool(runtime_diag.get("deadline_aborted", False)) and not has_non_rejected_internal)):
                rescue_plan = _fast_internal_rescue_plan(
                    customer_id=out["customer_id"],
                    run_id=run_ctx.run_id,
                    row=row,
                    model=model,
                    calibrator=calibrator,
                    feature_cols=feature_cols,
                    graph=graph,
                    tau=tau,
                    candidate_features=local_candidate_features,
                    robust_cfg=robust_cfg,
                    fairness_penalty=fairness_penalty,
                    scenarios=scenarios,
                    threshold_shift_per_msi_unit=threshold_shift,
                    robust_objective=robust_objective,
                    robust_cvar_quantile=robust_cvar_quantile,
                    min_reliability=min_reliability_f,
                    min_worst_risk_margin=min_worst_margin_f,
                    alpha=alpha,
                    bootstrap_b=bootstrap_b,
                    uncertainty_cfg=uncertainty_cfg,
                    feasibility_profile=feasibility_internal_profile,
                    segment_context=segment_context,
                    denied_mode=deny_mode,
                )
                if rescue_plan is not None:
                    validated.append(rescue_plan)
                    out["internal_rescue_used"] = 1
            out["deadline_abort"] = int(bool(runtime_diag.get("deadline_aborted", False)))
            out["internal_plan_count"] = int(len(validated))
            out["internal_approved_plan_count"] = int(sum(1 for p in validated if p.status == "APPROVED"))
            out["internal_gate_pass_any"] = int(out["internal_approved_plan_count"] > 0)
            elapsed_before_dice_ms = float((time.perf_counter() - t0) * 1000.0)
            out["search_elapsed_before_dice_ms"] = elapsed_before_dice_ms
            if sync_fast_path_enabled and sync_time_budget_ms > 0:
                out["sync_elapsed_ms"] = float(min(elapsed_before_dice_ms, float(sync_time_budget_ms)))
                out["async_deep_path_used"] = int(
                    bool(deny_mode) and bool(async_deep_path_enabled) and (elapsed_before_dice_ms > float(sync_time_budget_ms))
                )
            else:
                out["sync_elapsed_ms"] = float(elapsed_before_dice_ms)
                out["async_deep_path_used"] = 0
            budget_overshoot_ms = (
                float(max(0.0, elapsed_before_dice_ms - float(time_budget_ms)))
                if time_budget_ms > 0
                else 0.0
            )
            out["budget_overshoot_ms"] = budget_overshoot_ms
            out["budget_overshoot"] = int(budget_overshoot_ms > 0.0)
            remaining_budget_ms = int(max(0.0, float(time_budget_ms) - elapsed_before_dice_ms)) if time_budget_ms > 0 else 0
            min_remaining_budget_for_dice_ms = int(search_cfg.get("min_remaining_budget_for_dice_ms", 0))
            min_remaining_budget_for_rule_ms = int(search_cfg.get("min_remaining_budget_for_rule_ms", 0))
            hard_max_dice_timeout_ms = int(search_cfg.get("hard_max_dice_timeout_ms", 0))
            skip_dice_when_internal_approved = bool(search_cfg.get("skip_dice_when_internal_approved", False))
            skip_dice_for_non_denied = bool(search_cfg.get("skip_dice_for_non_denied", False))
            force_skip_dice = bool(search_cfg.get("force_skip_dice", False))
            dice_only_high_risk_denied = bool(search_cfg.get("dice_only_high_risk_denied", False))
            denied_dice_quota_enabled = denied_dice_max_customers > 0

            skip_dice_reason = ""
            if force_skip_dice:
                skip_dice_reason = "forced_skip_dice"
            if not skip_dice_reason and denied_dice_quota_enabled and deny_mode and int(i) not in denied_dice_eligible_batch_indices:
                skip_dice_reason = "denied_dice_quota"
            if not skip_dice_reason and skip_dice_when_internal_approved and out["internal_approved_plan_count"] > 0:
                skip_dice_reason = "internal_already_approved"
            if not skip_dice_reason and skip_dice_for_non_denied and not deny_mode:
                skip_dice_reason = "non_denied_profile"
            if (
                not skip_dice_reason
                and dice_only_high_risk_denied
                and (not deny_mode or str(segment_context.get("risk_band", "")) != "high")
            ):
                skip_dice_reason = "dice_high_risk_denied_only"
            if (
                not skip_dice_reason
                and time_budget_ms > 0
                and min_remaining_budget_for_dice_ms > 0
                and remaining_budget_ms < int(min_remaining_budget_for_dice_ms)
            ):
                skip_dice_reason = "time_budget_insufficient_for_dice"
            if (
                not skip_dice_reason
                and time_budget_ms > 0
                and hard_budget_enforced
                and elapsed_before_dice_ms >= float(time_budget_ms)
            ):
                skip_dice_reason = "time_budget_exceeded"

            dice_records: list[PlanRecord] = []
            dice_backend = "skipped"
            dice_tel = {
                "fallback_reason": skip_dice_reason or "skipped_by_policy",
                "attempted_method_count": 0,
            }
            if not skip_dice_reason:
                configured_timeout_ms = int(dice_cfg.get("timeout_ms", 0))
                dice_timeout_ms = configured_timeout_ms
                if time_budget_ms > 0 and hard_budget_enforced:
                    if remaining_budget_ms > 0:
                        if dice_timeout_ms > 0:
                            dice_timeout_ms = min(dice_timeout_ms, remaining_budget_ms)
                        else:
                            # Hard budget mode: enforce timeout even if dice.timeout_ms is unset.
                            dice_timeout_ms = remaining_budget_ms
                    if hard_max_dice_timeout_ms > 0:
                        if dice_timeout_ms > 0:
                            dice_timeout_ms = min(dice_timeout_ms, int(hard_max_dice_timeout_ms))
                        else:
                            dice_timeout_ms = int(hard_max_dice_timeout_ms)
                elif dice_timeout_ms > 0 and remaining_budget_ms > 0:
                    dice_timeout_ms = min(dice_timeout_ms, remaining_budget_ms)
                dice_action_sets, dice_backend, dice_tel = generate_dice_counterfactual_actions(
                    row=row,
                    feature_cols=feature_cols,
                    actionable_features=actionable,
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
                        customer_id=out["customer_id"],
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
                        source_tag="dice",
                    )
                    p = validate_plan(
                        p,
                        tau=tau,
                        alpha=alpha,
                        bootstrap_b=bootstrap_b,
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

            out["dice_plan_count"] = int(len(dice_records))
            out["dice_approved_plan_count"] = int(sum(1 for p in dice_records if p.status == "APPROVED"))
            out["dice_gate_pass_any"] = int(out["dice_approved_plan_count"] > 0)
            rule_records: list[PlanRecord] = []
            out["rule_skipped_reason"] = ""
            rule_cfg = rec_cfg.get("rule_generator", {}) if isinstance(rec_cfg.get("rule_generator", {}), dict) else {}
            elapsed_before_rule_ms = float((time.perf_counter() - t0) * 1000.0)
            remaining_budget_for_rule_ms = (
                int(max(0.0, float(time_budget_ms) - elapsed_before_rule_ms))
                if time_budget_ms > 0
                else 0
            )
            rule_skipped_reason = ""
            rule_only_last_resort = bool(rule_cfg.get("only_last_resort", True))
            if rule_only_last_resort and any(
                not _is_rejected_like(getattr(p, "status", ""))
                for p in (validated + dice_records)
            ):
                rule_skipped_reason = "nonrejected_candidates_available"
            if (
                not rule_skipped_reason
                and time_budget_ms > 0
                and min_remaining_budget_for_rule_ms > 0
                and remaining_budget_for_rule_ms < int(min_remaining_budget_for_rule_ms)
            ):
                rule_skipped_reason = "time_budget_insufficient_for_rule"
            if (
                not rule_skipped_reason
                and time_budget_ms > 0
                and hard_budget_enforced
                and elapsed_before_rule_ms >= float(time_budget_ms)
            ):
                rule_skipped_reason = "time_budget_exceeded"
            if bool(rule_cfg.get("enabled", True)) and not rule_skipped_reason:
                rule_action_sets: list[list[dict[str, Any]]] = []
                base_rule_actions = generate_dice_like_baseline(
                    row=row,
                    feature_cols=feature_cols,
                    actionable_features=actionable,
                    max_actions=int(rule_cfg.get("max_actions", 2)),
                )
                if base_rule_actions:
                    rule_action_sets.append(base_rule_actions)
                for ridx, actions in enumerate(rule_action_sets, start=1):
                    rp = _dice_plan_record(
                        idx=ridx,
                        customer_id=out["customer_id"],
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
                        source_tag="rule",
                    )
                    rp = validate_plan(
                        rp,
                        tau=tau,
                        alpha=alpha,
                        bootstrap_b=bootstrap_b,
                        scenarios=scenarios,
                        threshold_shift_per_msi_unit=threshold_shift,
                        robust_objective=robust_objective,
                        robust_cvar_quantile=robust_cvar_quantile,
                        min_reliability=min_reliability_f,
                        min_worst_risk_margin=min_worst_margin_f,
                        uncertainty_cfg=uncertainty_cfg,
                        segment_context=segment_context,
                        )
                    rule_records.append(rp)
            else:
                out["rule_skipped_reason"] = rule_skipped_reason
            out["rule_plan_count"] = int(len(rule_records))
            out["rule_approved_plan_count"] = int(sum(1 for p in rule_records if p.status == "APPROVED"))
            out["rule_gate_pass_any"] = int(out["rule_approved_plan_count"] > 0)

            candidate_pool = validated + dice_records + rule_records
            candidate_pool_max_size = int(search_cfg.get("candidate_pool_max_size", 0))
            stage1_filter_multiplier = max(1.0, float(search_cfg.get("stage1_filter_multiplier", 1.0)))
            stage1_per_source_cap = int(search_cfg.get("stage1_per_source_cap", 0))
            if candidate_pool_max_size > 0:
                candidate_pool = _stage1_filter_candidate_pool(
                    candidate_pool,
                    max_size=candidate_pool_max_size,
                    tau=tau,
                    min_reliability=min_reliability_f,
                    min_worst_risk_margin=min_worst_margin_f,
                    multiplier=stage1_filter_multiplier,
                    per_source_cap=stage1_per_source_cap,
                )
            candidate_pool = _prune_candidate_pool(
                candidate_pool,
                candidate_pool_max_size,
                novelty_weight=max(0.0, float(search_cfg.get("novelty_weight", 0.0))),
                tau=tau,
                min_reliability=min_reliability_f,
                min_worst_risk_margin=min_worst_margin_f,
            )
            out["candidate_pool_count"] = int(len(candidate_pool))
            out["candidate_pool_approved_count"] = int(sum(1 for p in candidate_pool if p.status == "APPROVED"))
            out["candidate_pool_diversity_index"] = _candidate_pool_diversity_index(candidate_pool)
            out["candidate_source_entropy"] = _candidate_source_entropy(candidate_pool)
            elapsed_after_pool_ms = float((time.perf_counter() - t0) * 1000.0)
            fallback_enabled = bool(search_cfg.get("enable_deterministic_fallback", True))
            time_budget_exceeded = bool(time_budget_ms > 0 and elapsed_after_pool_ms >= float(time_budget_ms))
            if time_budget_exceeded and validated:
                hard_cap_keep = 3 if high_risk_denied else 1
                # Hard-cap fallback: avoid relying on slower external generators.
                candidate_pool = sorted(
                    validated,
                    key=lambda p: _candidate_gate_sort_key(
                        p,
                        tau=tau,
                        min_reliability=min_reliability_f,
                        min_worst_risk_margin=min_worst_margin_f,
                    ),
                )[: max(1, min(hard_cap_keep, len(validated)))]
                out["candidate_pool_count"] = int(len(candidate_pool))
                out["candidate_pool_approved_count"] = int(sum(1 for p in candidate_pool if p.status == "APPROVED"))
                out["candidate_pool_diversity_index"] = _candidate_pool_diversity_index(candidate_pool)
                out["candidate_source_entropy"] = _candidate_source_entropy(candidate_pool)
                out["fallback_triggered"] = 1
                out["fallback_reason"] = "budget_hard_cap_internal_only"
            if (not candidate_pool) and fallback_enabled:
                fallback_actions = generate_dice_like_baseline(
                    row=row,
                    feature_cols=feature_cols,
                    actionable_features=actionable,
                    max_actions=1,
                )
                if fallback_actions:
                    fp = _dice_plan_record(
                        idx=1,
                        customer_id=out["customer_id"],
                        run_id=run_ctx.run_id,
                        row=row,
                        feature_cols=feature_cols,
                        actions=fallback_actions,
                        model=model,
                        calibrator=calibrator,
                        tau=tau,
                        graph=graph,
                        causal_weight=float(c_cfg.get("penalty_weight", 0.3)),
                        feasibility_profile=feasibility_dice_profile,
                        segment_context=segment_context,
                        source_tag="fallback",
                    )
                    fp = validate_plan(
                        fp,
                        tau=tau,
                        alpha=alpha,
                        bootstrap_b=bootstrap_b,
                        scenarios=scenarios,
                        threshold_shift_per_msi_unit=threshold_shift,
                        robust_objective=robust_objective,
                        robust_cvar_quantile=robust_cvar_quantile,
                        min_reliability=min_reliability_f,
                        min_worst_risk_margin=min_worst_margin_f,
                        uncertainty_cfg=uncertainty_cfg,
                        segment_context=segment_context,
                    )
                    candidate_pool = [fp]
                    out["candidate_pool_count"] = 1
                    out["candidate_pool_approved_count"] = int(fp.status == "APPROVED")
                    out["candidate_pool_diversity_index"] = 0.0
                    out["candidate_source_entropy"] = 0.0
                    out["fallback_triggered"] = 1
                    out["fallback_reason"] = "time_budget_exceeded" if time_budget_exceeded else "empty_candidate_pool"
            out["approved_plan_count"] = int(out["candidate_pool_approved_count"])
            out["had_any_candidate"] = int(out["candidate_pool_count"] > 0)
            out["gate_pass_any_candidate"] = int(out["candidate_pool_approved_count"] > 0)
            candidate_pool_for_best = _prefer_non_rejected_candidates(candidate_pool)

            best = choose_best_plan(
                candidate_pool_for_best,
                base_pd=base_pd_i,
                tau=tau,
                min_reliability=min_reliability_f,
                min_worst_risk_margin=min_worst_margin_f,
                fairness_penalty=fairness_penalty,
                denied_mode=bool(search_profile.get("is_denied_target", False)),
                segment_context=segment_context,
                denied_objective_cfg=robust_cfg.get("denied_objective", {}),
            )
            out["best_status"] = str(best.status)
            out["best_status_reason"] = str(best.status_reason or "")
            out["best_constraint_status"] = str(getattr(best, "constraint_status", "valid") or "valid")
            out["best_source"] = _plan_source(best)
            out["best_plan_id"] = str(best.plan_id)
            out["best_horizon_months"] = int(best.horizon_months)
            out["best_strategy"] = str(best.strategy)
            out["best_action_count"] = int(len(best.actions))
            out["best_cost_usd"] = _plan_cost(best)
            out["best_proximity_l1"] = _plan_proximity_l1(best)
            out["best_robust_score"] = float(best.robust_score if best.robust_score is not None else (best.score or 0.0))
            out["best_plan_execution_probability"] = _safe_float(
                getattr(best, "plan_execution_probability", 0.0),
                0.0,
            )
            out["best_mean_action_execution_probability"] = _safe_float(
                getattr(best, "mean_action_execution_probability", 0.0),
                0.0,
            )
            out["best_nominal_pd_improvement"] = _safe_float(
                getattr(best, "nominal_pd_improvement", 0.0),
                0.0,
            )
            out["best_expected_pd_improvement"] = _safe_float(
                getattr(best, "expected_pd_improvement", 0.0),
                0.0,
            )
            out["best_offer_plan"] = int(bool(getattr(best, "offer_plan", False)))
            out["best_rankable_offer_count"] = int(getattr(best, "rankable_offer_count", 0) or 0)
            out["best_rankable_offer"] = int(int(out["best_rankable_offer_count"]) > 0)
            out["best_offer_type"] = _safe_str(getattr(best, "dominant_offer_type", ""))
            out["best_offer_policy_arm"] = _safe_str(getattr(best, "offer_policy_arm", ""))
            out["best_offer_family"] = _safe_str(getattr(best, "offer_family", ""))
            out["best_offer_scoring_profile"] = _safe_str(getattr(best, "offer_scoring_profile", ""))
            out["best_term_generation_rule"] = _safe_str(getattr(best, "term_generation_rule", ""))
            out["best_offer_acceptance_probability"] = _safe_float(
                getattr(best, "offer_acceptance_probability", 0.0),
                0.0,
            )
            out["best_combined_plan_realization_probability"] = _safe_float(
                getattr(best, "combined_plan_realization_probability", 0.0),
                0.0,
            )
            out["best_expected_recovery_proxy"] = _safe_float(
                getattr(best, "expected_recovery_proxy", 0.0),
                0.0,
            )
            out["best_approval_rate_proxy_delta"] = _safe_float(
                getattr(best, "approval_rate_proxy_delta", 0.0),
                0.0,
            )
            out["best_default_rate_90d_proxy_delta"] = _safe_float(
                getattr(best, "default_rate_90d_proxy_delta", 0.0),
                0.0,
            )
            out["best_avg_margin_90d_proxy_delta"] = _safe_float(
                getattr(best, "avg_margin_90d_proxy_delta", 0.0),
                0.0,
            )
            out["best_governance_safe_offer"] = int(bool(getattr(best, "governance_safe_offer", False)))
            out["best_ci_high"] = float(best.ci_high) if best.ci_high is not None else np.nan
            out["best_reliability"] = float(best.reliability) if best.reliability is not None else np.nan
            out["best_worst_risk_margin"] = (
                float(best.robust_worst_risk_margin) if best.robust_worst_risk_margin is not None else np.nan
            )
            best_pd = float(best.predicted_pd if best.predicted_pd is not None else base_pd_i)
            out["best_candidate_pd"] = best_pd
            out["candidate_pd_delta"] = float(base_pd_i - best_pd)
            out["best_pd"] = best_pd if best.status == "APPROVED" else base_pd_i
            out["pd_delta"] = float(base_pd_i - out["best_pd"])
            out["best_timeline_steps_json"] = json.dumps(
                _plan_trajectory_steps(best),
                ensure_ascii=False,
            )
            out["best_phases_json"] = json.dumps(
                [phase.model_dump(mode="json") for phase in list(getattr(best, "phases", []))],
                ensure_ascii=False,
            )
            out["best_trajectory_checkpoints_json"] = json.dumps(
                [checkpoint.model_dump(mode="json") for checkpoint in list(getattr(best, "trajectory_checkpoints", []))],
                ensure_ascii=False,
            )
            out["trajectory_policy_label"] = str(getattr(best, "trajectory_policy_label", "") or "")
            out["trajectory_policy_score"] = _safe_float(getattr(best, "trajectory_policy_score", 0.0), 0.0)
            behavior_metrics = _simulate_plan_execution_behavior(
                row=row,
                plan=best,
                base_pd=base_pd_i,
                tau=tau,
                model=model,
                calibrator=calibrator,
                feature_cols=feature_cols,
                random_state=int(args.sample_seed) + int(i),
                partial_progress_min_pd_delta=trajectory_partial_progress_min_pd_delta,
                max_weekly_actions=int(
                    (
                        search_profile.get("search_cfg", {})
                        if isinstance(search_profile.get("search_cfg", {}), dict)
                        else {}
                    ).get("weekly_optimizer", {})
                    .get("max_weekly_actions", 3)
                    if isinstance(
                        (
                            search_profile.get("search_cfg", {})
                            if isinstance(search_profile.get("search_cfg", {}), dict)
                            else {}
                        ).get("weekly_optimizer", {}),
                        dict,
                    )
                    else 3
                ),
                min_robust_margin=min_worst_margin_f,
            )
            out["best_execution_scenario"] = str(behavior_metrics["execution_scenario"])
            out["best_execution_rate"] = float(behavior_metrics["execution_rate"])
            out["best_partial_execution"] = int(behavior_metrics["partial_execution"])
            out["best_mixed_execution"] = int(behavior_metrics["mixed_execution"])
            out["best_failed_execution"] = int(behavior_metrics["failed_execution"])
            out["best_expected_partial_progress"] = int(behavior_metrics["expected_partial_progress"])
            out["best_missed_action"] = int(behavior_metrics["missed_action"])
            out["best_missed_actions_streak"] = int(behavior_metrics["missed_actions_streak"])
            out["trajectory_status"] = str(behavior_metrics["trajectory_status"])
            out["trajectory_current_phase"] = str(behavior_metrics["current_phase"])
            out["trajectory_next_review_week"] = int(behavior_metrics["next_review_week"])
            out["trajectory_phase_transition_reason"] = str(behavior_metrics["phase_transition_reason"])
            out["trajectory_replanned_from_phase"] = str(behavior_metrics["replanned_from_phase"])
            if trajectory_enabled:
                out.update(
                    _plan_trajectory_metrics(
                        row=row,
                        plan=best,
                        base_pd=base_pd_i,
                        tau=tau,
                        model=model,
                        calibrator=calibrator,
                        feature_cols=feature_cols,
                        partial_progress_min_pd_delta=trajectory_partial_progress_min_pd_delta,
                        random_state=int(args.sample_seed) + int(i),
                        max_weekly_actions=int(
                            (
                                search_profile.get("search_cfg", {})
                                if isinstance(search_profile.get("search_cfg", {}), dict)
                                else {}
                            ).get("weekly_optimizer", {})
                            .get("max_weekly_actions", 3)
                            if isinstance(
                                (
                                    search_profile.get("search_cfg", {})
                                    if isinstance(search_profile.get("search_cfg", {}), dict)
                                    else {}
                                ).get("weekly_optimizer", {}),
                                dict,
                            )
                            else 3
                        ),
                        min_robust_margin=min_worst_margin_f,
                    )
                )
            out["high_risk_bridge_hit"] = int(
                int(out["denied_base"]) == 1
                and str(out.get("risk_band", "")).lower() == "high"
                and (
                    out["best_status"] == "APPROVED"
                    or (
                        high_risk_bridge_enabled
                        and (out["candidate_pd_delta"] >= high_risk_bridge_min_pd_reduction)
                        and (out["best_candidate_pd"] <= float(tau) + high_risk_bridge_target_pd_delta_to_tau)
                    )
                )
            )

            out["dice_backend"] = str(dice_backend)
            out["dice_success"] = int(dice_backend == "dice")
            out["dice_fallback_reason"] = str(dice_tel.get("fallback_reason") or "")
            out["dice_attempted_method_count"] = int(dice_tel.get("attempted_method_count", 0))
            if int(out["denied_base"]) == 1 and out["best_status"] != "APPROVED":
                out["denied_not_approved_root_cause"] = _root_cause_from_status_reasons(str(best.status_reason or ""))
        except Exception as exc:
            out["error_type"] = exc.__class__.__name__
            out["error_message"] = str(exc)
            out["best_status"] = "ERROR"
            out["best_status_reason"] = str(exc)
            out["best_pd"] = base_pd_i
            out["best_candidate_pd"] = base_pd_i
            out["candidate_pd_delta"] = 0.0
            out["pd_delta"] = 0.0
            out["high_risk_bridge_hit"] = 0
            if int(out["denied_base"]) == 1:
                out["denied_not_approved_root_cause"] = "pipeline_error"
        out["elapsed_ms"] = float((time.perf_counter() - t0) * 1000.0)
        return out

    n_workers = max(1, int(args.n_workers))
    if n_workers <= 1:
        for i, row in sampled.iterrows():
            out = _process_one(int(i), row, float(base_proba.iloc[i]))
            rows.append(out)
            if (i + 1) % max(1, int(args.log_every)) == 0 or (i + 1) == n:
                logger.info("Processed %s/%s rows", i + 1, n)
    else:
        logger.info("Parallel processing enabled. workers=%s", n_workers)
        completed = 0
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = {
                ex.submit(_process_one, int(i), row.copy(deep=True), float(base_proba.iloc[i])): int(i)
                for i, row in sampled.iterrows()
            }
            for fut in as_completed(futures):
                rows.append(fut.result())
                completed += 1
                if completed % max(1, int(args.log_every)) == 0 or completed == n:
                    logger.info("Processed %s/%s rows", completed, n)

    elapsed_s = float(time.perf_counter() - t0_all)
    batch_df = pd.DataFrame(rows).sort_values("batch_index").reset_index(drop=True)
    sampled_sorted = sampled.sort_index().reset_index(drop=True)
    batch_df, fairness_guard_metrics = _apply_label_aware_fairness_guard(
        batch_df=batch_df,
        sampled_sorted=sampled_sorted,
        group_feature=args.group_feature,
        target_col=target_col,
        tau=tau,
        rec_cfg=rec_cfg,
    )
    batch_out = run_ctx.tables_dir / "batch_recourse_results.csv"
    batch_df.to_csv(batch_out, index=False)

    best_mix = (
        batch_df.groupby(["best_source", "best_horizon_months", "best_strategy"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )
    best_mix["share"] = (best_mix["count"] / max(1, int(len(batch_df)))).astype(float)
    best_mix_out = run_ctx.tables_dir / "best_plan_distribution.csv"
    best_mix.to_csv(best_mix_out, index=False)

    approved_only = batch_df[batch_df["best_status"] == "APPROVED"]
    best_mix_approved = (
        approved_only.groupby(["best_source", "best_horizon_months", "best_strategy"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )
    best_mix_approved["share"] = (best_mix_approved["count"] / max(1, int(len(approved_only)))).astype(float)
    best_mix_approved_out = run_ctx.tables_dir / "best_plan_distribution_approved.csv"
    best_mix_approved.to_csv(best_mix_approved_out, index=False)

    denied_only = batch_df[batch_df["denied_base"].astype(int) == 1]
    best_mix_denied = (
        denied_only.groupby(["best_source", "best_horizon_months", "best_strategy"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )
    best_mix_denied["share"] = (best_mix_denied["count"] / max(1, int(len(denied_only)))).astype(float)
    best_mix_denied_out = run_ctx.tables_dir / "best_plan_distribution_denied.csv"
    best_mix_denied.to_csv(best_mix_denied_out, index=False)

    action_dist = (
        batch_df["best_action_count"]
        .value_counts(dropna=False)
        .rename_axis("best_action_count")
        .reset_index(name="count")
        .sort_values("best_action_count")
        .reset_index(drop=True)
    )
    action_dist["share"] = (action_dist["count"] / max(1, int(len(batch_df)))).astype(float)
    action_dist_out = run_ctx.tables_dir / "recourse_action_count_distribution.csv"
    action_dist.to_csv(action_dist_out, index=False)
    timeline_step_rows: list[dict[str, Any]] = []
    for raw_steps in batch_df["best_timeline_steps_json"].astype(str).tolist():
        if not raw_steps or raw_steps == "[]":
            continue
        try:
            parsed = json.loads(raw_steps)
        except Exception:
            continue
        if not isinstance(parsed, list):
            continue
        for step in parsed:
            if not isinstance(step, dict):
                continue
            timeline_step_rows.append(
                {
                    "phase_id": _safe_str(step.get("phase_id", ""), ""),
                    "phase_title": _safe_str(step.get("phase_title", ""), ""),
                    "feature_name": _safe_str(step.get("feature_name", ""), ""),
                }
            )
    if timeline_step_rows:
        top_steps_by_phase = (
            pd.DataFrame(timeline_step_rows)
            .groupby(["phase_id", "phase_title", "feature_name"], dropna=False)
            .size()
            .reset_index(name="count")
            .sort_values(["phase_id", "count", "feature_name"], ascending=[True, False, True])
            .reset_index(drop=True)
        )
        top_steps_by_phase["share"] = (
            top_steps_by_phase["count"].astype(float) / max(1, float(top_steps_by_phase["count"].sum()))
        )
    else:
        top_steps_by_phase = pd.DataFrame(
            columns=["phase_id", "phase_title", "feature_name", "count", "share"]
        )
    top_steps_by_phase_out = run_ctx.tables_dir / "top_recommended_steps_by_phase.csv"
    top_steps_by_phase.to_csv(top_steps_by_phase_out, index=False)

    cost_series = batch_df["best_cost_usd"].astype(float)
    cost_percentiles = pd.DataFrame(
        [
            {
                "cost_p50": _as_float_percentile(cost_series, 0.50),
                "cost_p90": _as_float_percentile(cost_series, 0.90),
                "cost_p95": _as_float_percentile(cost_series, 0.95),
                "cost_p99": _as_float_percentile(cost_series, 0.99),
                "cost_mean": float(cost_series.mean()) if not cost_series.empty else 0.0,
            }
        ]
    )
    cost_percentiles_out = run_ctx.tables_dir / "recourse_cost_percentiles.csv"
    cost_percentiles.to_csv(cost_percentiles_out, index=False)

    denied_root_causes = (
        batch_df[
            (batch_df["denied_base"].astype(int) == 1)
            & (batch_df["best_status"] != "APPROVED")
            & (batch_df["denied_not_approved_root_cause"] != "")
        ]["denied_not_approved_root_cause"]
        .value_counts(dropna=False)
        .rename_axis("root_cause")
        .reset_index(name="count")
    )
    denied_root_causes["share"] = (
        denied_root_causes["count"] / max(1, int(((batch_df["denied_base"].astype(int) == 1) & (batch_df["best_status"] != "APPROVED")).sum()))
    ).astype(float)
    denied_root_causes_out = run_ctx.tables_dir / "denied_not_approved_root_causes.csv"
    denied_root_causes.to_csv(denied_root_causes_out, index=False)

    action_realism_event_rows: list[dict[str, Any]] = []
    for _, batch_row in batch_df[["batch_index", "denied_base", "risk_band", "action_realism_events_json"]].iterrows():
        raw_events = batch_row.get("action_realism_events_json", "[]")
        try:
            events = json.loads(raw_events) if isinstance(raw_events, str) else []
        except Exception:
            events = []
        if not isinstance(events, list):
            continue
        for event in events:
            if not isinstance(event, dict):
                continue
            codes = event.get("reason_codes", [])
            codes = codes if isinstance(codes, list) and codes else [""]
            for code in codes:
                action_realism_event_rows.append(
                    {
                        "batch_index": int(batch_row.get("batch_index", 0)),
                        "denied_base": int(batch_row.get("denied_base", 0)),
                        "risk_band": _safe_str(batch_row.get("risk_band", "")),
                        "action_key": _safe_str(event.get("action_key", "")),
                        "action_class": _safe_str(event.get("action_class", "")),
                        "feature_name": _safe_str(event.get("feature_name", "")),
                        "action_group_id": _safe_str(event.get("action_group_id", "")),
                        "composite_action": _safe_int(event.get("composite_action", 0)),
                        "status": _safe_str(event.get("status", "")),
                        "reason_code": _safe_str(code, ""),
                        "time_months": _safe_int(event.get("time_months", 0)),
                        "requested_delta": _safe_float(event.get("requested_delta", 0.0)),
                        "resolved_delta": _safe_float(event.get("resolved_delta", 0.0)),
                        "semantic_ratio": _safe_float(event.get("semantic_ratio", 1.0)),
                    }
                )
    if action_realism_event_rows:
        action_realism_events_df = pd.DataFrame(action_realism_event_rows)
        feasibility_rejection_breakdown = (
            action_realism_events_df[action_realism_events_df["status"].isin(["clipped", "rejected"])]
            .groupby(["status", "reason_code", "action_class", "action_key"], dropna=False)
            .size()
            .reset_index(name="count")
            .sort_values(["status", "count", "reason_code"], ascending=[True, False, True])
            .reset_index(drop=True)
        )
    else:
        action_realism_events_df = pd.DataFrame(
            columns=[
                "batch_index",
                "denied_base",
                "risk_band",
                "action_key",
                "action_class",
                "feature_name",
                "action_group_id",
                "composite_action",
                "status",
                "reason_code",
                "time_months",
                "requested_delta",
                "resolved_delta",
                "semantic_ratio",
            ]
        )
        feasibility_rejection_breakdown = pd.DataFrame(
            columns=["status", "reason_code", "action_class", "action_key", "count"]
        )
    feasibility_rejection_breakdown_out = run_ctx.tables_dir / "feasibility_rejection_breakdown.csv"
    feasibility_rejection_breakdown.to_csv(feasibility_rejection_breakdown_out, index=False)

    action_type_breakdown = (
        action_realism_events_df.groupby(["action_class", "action_key", "status"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "action_class", "action_key"], ascending=[False, True, True])
        .reset_index(drop=True)
        if not action_realism_events_df.empty
        else pd.DataFrame(columns=["action_class", "action_key", "status", "count"])
    )
    action_type_breakdown_out = run_ctx.tables_dir / "action_type_breakdown.csv"
    action_type_breakdown.to_csv(action_type_breakdown_out, index=False)

    action_constraint_event_rows: list[dict[str, Any]] = []
    for _, batch_row in batch_df[["batch_index", "denied_base", "risk_band", "action_constraint_events_json"]].iterrows():
        raw_events = batch_row.get("action_constraint_events_json", "[]")
        try:
            events = json.loads(raw_events) if isinstance(raw_events, str) else []
        except Exception:
            events = []
        if not isinstance(events, list):
            continue
        for event in events:
            if not isinstance(event, dict):
                continue
            action_constraint_event_rows.append(
                {
                    "batch_index": int(batch_row.get("batch_index", 0)),
                    "denied_base": int(batch_row.get("denied_base", 0)),
                    "risk_band": _safe_str(batch_row.get("risk_band", "")),
                    "event_type": _safe_str(event.get("event_type", "")),
                    "action_key": _safe_str(event.get("action_key", "")),
                    "action_class": _safe_str(event.get("action_class", "")),
                    "action_group_id": _safe_str(event.get("action_group_id", "")),
                    "feature_name": _safe_str(event.get("feature_name", "")),
                    "reason_code": _safe_str(event.get("reason_code", "")),
                    "related_action_key": _safe_str(event.get("related_action_key", "")),
                    "related_group_id": _safe_str(event.get("related_group_id", "")),
                    "time_months": _safe_int(event.get("time_months", 0)),
                }
            )
    action_constraint_events_df = (
        pd.DataFrame(action_constraint_event_rows)
        if action_constraint_event_rows
        else pd.DataFrame(
            columns=[
                "batch_index",
                "denied_base",
                "risk_band",
                "event_type",
                "action_key",
                "action_class",
                "action_group_id",
                "feature_name",
                "reason_code",
                "related_action_key",
                "related_group_id",
                "time_months",
            ]
        )
    )
    constraint_repair_breakdown = (
        action_constraint_events_df[action_constraint_events_df["event_type"] == "repair_dropped"]
        .groupby(["reason_code", "action_class", "action_key"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "reason_code"], ascending=[False, True])
        .reset_index(drop=True)
        if not action_constraint_events_df.empty
        else pd.DataFrame(columns=["reason_code", "action_class", "action_key", "count"])
    )
    constraint_repair_breakdown_out = run_ctx.tables_dir / "constraint_repair_breakdown.csv"
    constraint_repair_breakdown.to_csv(constraint_repair_breakdown_out, index=False)

    approval_pending_breakdown = (
        action_constraint_events_df[action_constraint_events_df["event_type"] == "approval_pending"]
        .groupby(["reason_code", "action_class", "action_key"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "reason_code"], ascending=[False, True])
        .reset_index(drop=True)
        if not action_constraint_events_df.empty
        else pd.DataFrame(columns=["reason_code", "action_class", "action_key", "count"])
    )
    approval_pending_breakdown_out = run_ctx.tables_dir / "approval_pending_breakdown.csv"
    approval_pending_breakdown.to_csv(approval_pending_breakdown_out, index=False)

    total_action_realism_events = float(max(1, len(action_realism_events_df)))
    action_type_behavioral_rate = (
        float((action_realism_events_df["action_class"] == "behavioral").mean())
        if not action_realism_events_df.empty
        else 0.0
    )
    action_type_structural_rate = (
        float((action_realism_events_df["action_class"] == "structural").mean())
        if not action_realism_events_df.empty
        else 0.0
    )
    action_type_institutional_rate = (
        float((action_realism_events_df["action_class"] == "institutional").mean())
        if not action_realism_events_df.empty
        else 0.0
    )
    composite_action_rate = (
        float(action_realism_events_df["composite_action"].astype(float).mean())
        if not action_realism_events_df.empty
        else 0.0
    )
    repair_applied_rate = float((batch_df["action_constraint_repair_applied_count"].astype(int) > 0).mean())
    approval_pending_action_rate = float(
        batch_df["action_constraint_approval_pending_action_count"].astype(float).sum() / total_action_realism_events
    )
    invalid_combination_rate = float((batch_df["action_constraint_invalid_combination_count"].astype(int) > 0).mean())

    top_plan = best_mix.iloc[0] if not best_mix.empty else pd.Series(dtype=object)
    top_plan_approved = best_mix_approved.iloc[0] if not best_mix_approved.empty else pd.Series(dtype=object)
    top_plan_denied = best_mix_denied.iloc[0] if not best_mix_denied.empty else pd.Series(dtype=object)
    top_step = top_steps_by_phase.iloc[0] if not top_steps_by_phase.empty else pd.Series(dtype=object)

    denied_mask = batch_df["denied_base"].astype(int) == 1
    denied_count = int(denied_mask.sum())
    denied_with_any_candidate = int(((batch_df["had_any_candidate"].astype(int) == 1) & denied_mask).sum())
    denied_with_gate_pass_plan = int(((batch_df["gate_pass_any_candidate"].astype(int) == 1) & denied_mask).sum())
    denied_to_approved_lift = float(denied_with_gate_pass_plan / denied_count) if denied_count > 0 else 0.0
    funnel_df = pd.DataFrame(
        [
            {
                "n_customers": int(n),
                "denied_count": denied_count,
                "denied_with_any_candidate": denied_with_any_candidate,
                "denied_with_gate_pass_plan": denied_with_gate_pass_plan,
                "denied_to_approved_lift": denied_to_approved_lift,
            }
        ]
    )
    funnel_out = run_ctx.tables_dir / "recourse_funnel_summary.csv"
    funnel_df.to_csv(funnel_out, index=False)
    denied_segment_funnel = (
        batch_df[batch_df["denied_base"].astype(int) == 1]
        .groupby(["income_band", "risk_band"], dropna=False)
        .agg(
            denied_count=("customer_id", "size"),
            denied_with_any_candidate=("had_any_candidate", "sum"),
            denied_with_gate_pass_plan=("gate_pass_any_candidate", "sum"),
            high_risk_bridge_count=("high_risk_bridge_hit", "sum"),
            avg_candidate_pd_delta=("candidate_pd_delta", "mean"),
            avg_cap_multiplier=("cap_multiplier_total", "mean"),
        )
        .reset_index()
    )
    denied_segment_funnel["denied_to_approved_lift"] = (
        denied_segment_funnel["denied_with_gate_pass_plan"] / denied_segment_funnel["denied_count"].clip(lower=1)
    ).astype(float)
    denied_segment_funnel["high_risk_bridge_rate"] = (
        denied_segment_funnel["high_risk_bridge_count"] / denied_segment_funnel["denied_count"].clip(lower=1)
    ).astype(float)
    denied_high_risk = denied_segment_funnel[denied_segment_funnel["risk_band"] == "high"]
    denied_high_risk_count = int(denied_high_risk["denied_count"].sum()) if not denied_high_risk.empty else 0
    denied_high_risk_lift = (
        float(denied_high_risk["denied_with_gate_pass_plan"].sum()) / max(1, denied_high_risk_count)
        if denied_high_risk_count > 0
        else 0.0
    )
    denied_high_risk_mask = (
        (batch_df["denied_base"].astype(int) == 1) & (batch_df["risk_band"].astype(str).str.lower() == "high")
    )
    denied_high_risk_rows = batch_df[denied_high_risk_mask].copy()
    denied_high_risk_bridge_count = int(denied_high_risk_rows["high_risk_bridge_hit"].astype(int).sum()) if not denied_high_risk_rows.empty else 0
    denied_high_risk_bridge_rate = float(denied_high_risk_bridge_count / max(1, denied_high_risk_count)) if denied_high_risk_count > 0 else 0.0
    denied_high_risk_any_pd_reduction_count = (
        int((denied_high_risk_rows["candidate_pd_delta"].astype(float) > 0.0).sum())
        if not denied_high_risk_rows.empty
        else 0
    )
    denied_high_risk_any_pd_reduction_rate = (
        float(denied_high_risk_any_pd_reduction_count / max(1, denied_high_risk_count))
        if denied_high_risk_count > 0
        else 0.0
    )
    denied_high_risk_targeted_count = (
        int(denied_high_risk_rows["denied_target_mode"].astype(int).sum()) if not denied_high_risk_rows.empty else 0
    )
    denied_high_risk_targeted_rate = (
        float(denied_high_risk_targeted_count / max(1, denied_high_risk_count))
        if denied_high_risk_count > 0
        else 0.0
    )
    denied_high_risk_nonrejected_best_rate = (
        float(
            (
                ~denied_high_risk_rows["best_status"].astype(str).str.upper().isin(["REJECTED", "ERROR"])
            ).mean()
        )
        if not denied_high_risk_rows.empty
        else 0.0
    )
    denied_high_risk_avg_candidate_pd_reduction = (
        float(denied_high_risk_rows["candidate_pd_delta"].astype(float).mean()) if not denied_high_risk_rows.empty else 0.0
    )
    denied_high_risk_p95_candidate_pd_reduction = (
        _as_float_percentile(denied_high_risk_rows["candidate_pd_delta"].astype(float), 0.95)
        if not denied_high_risk_rows.empty
        else 0.0
    )
    high_risk_reachability_rate = (
        float((denied_high_risk_rows["best_candidate_pd"].astype(float) <= float(tau)).mean())
        if not denied_high_risk_rows.empty
        else 0.0
    )
    denied_rows = batch_df[denied_mask].copy()
    trajectory_gate_pass_rate_4w = (
        float(denied_rows["trajectory_gate_pass_4w"].astype(float).mean()) if not denied_rows.empty else 0.0
    )
    trajectory_gate_pass_rate_12w = (
        float(denied_rows["trajectory_gate_pass_12w"].astype(float).mean()) if not denied_rows.empty else 0.0
    )
    trajectory_gate_pass_rate_24w = (
        float(denied_rows["trajectory_gate_pass_24w"].astype(float).mean()) if not denied_rows.empty else 0.0
    )
    trajectory_partial_progress_rate = (
        float(denied_rows["trajectory_partial_progress"].astype(float).mean()) if not denied_rows.empty else 0.0
    )
    trajectory_pass_days = (
        denied_rows.loc[
            denied_rows["trajectory_gate_pass_24w"].astype(int) == 1,
            "trajectory_time_to_gate_pass_days",
        ]
        .astype(float)
        .dropna()
        if not denied_rows.empty
        else pd.Series(dtype=float)
    )
    trajectory_median_time_to_gate_pass_days = (
        float(np.median(trajectory_pass_days.to_numpy(dtype=float)))
        if not trajectory_pass_days.empty
        else 0.0
    )
    trajectory_by_risk = (
        denied_rows.groupby("risk_band", dropna=False)
        .agg(
            denied_count=("customer_id", "size"),
            gate_pass_rate_4w=("trajectory_gate_pass_4w", "mean"),
            gate_pass_rate_12w=("trajectory_gate_pass_12w", "mean"),
            gate_pass_rate_24w=("trajectory_gate_pass_24w", "mean"),
            partial_progress_rate=("trajectory_partial_progress", "mean"),
            median_pd_delta_24w=("trajectory_pd_delta_24w", "median"),
        )
        .reset_index()
        if not denied_rows.empty
        else pd.DataFrame(
            columns=[
                "risk_band",
                "denied_count",
                "gate_pass_rate_4w",
                "gate_pass_rate_12w",
                "gate_pass_rate_24w",
                "partial_progress_rate",
                "median_pd_delta_24w",
            ]
        )
    )
    trajectory_by_risk_out = run_ctx.tables_dir / "trajectory_gate_by_risk_band.csv"
    trajectory_by_risk.to_csv(trajectory_by_risk_out, index=False)
    trajectory_by_income = (
        denied_rows.groupby("income_band", dropna=False)
        .agg(
            denied_count=("customer_id", "size"),
            gate_pass_rate_4w=("trajectory_gate_pass_4w", "mean"),
            gate_pass_rate_12w=("trajectory_gate_pass_12w", "mean"),
            gate_pass_rate_24w=("trajectory_gate_pass_24w", "mean"),
            partial_progress_rate=("trajectory_partial_progress", "mean"),
            median_pd_delta_24w=("trajectory_pd_delta_24w", "median"),
        )
        .reset_index()
        if not denied_rows.empty
        else pd.DataFrame(
            columns=[
                "income_band",
                "denied_count",
                "gate_pass_rate_4w",
                "gate_pass_rate_12w",
                "gate_pass_rate_24w",
                "partial_progress_rate",
                "median_pd_delta_24w",
            ]
        )
    )
    trajectory_by_income_out = run_ctx.tables_dir / "trajectory_gate_by_income_band.csv"
    trajectory_by_income.to_csv(trajectory_by_income_out, index=False)
    trajectory_phase_mix = (
        pd.DataFrame(
            [
                {
                    "phase_1_action_count_p50": _as_float_percentile(
                        denied_rows["trajectory_phase_1_action_count"].astype(float), 0.50
                    ),
                    "phase_2_action_count_p50": _as_float_percentile(
                        denied_rows["trajectory_phase_2_action_count"].astype(float), 0.50
                    ),
                    "phase_3_action_count_p50": _as_float_percentile(
                        denied_rows["trajectory_phase_3_action_count"].astype(float), 0.50
                    ),
                    "phase_1_action_count_p95": _as_float_percentile(
                        denied_rows["trajectory_phase_1_action_count"].astype(float), 0.95
                    ),
                    "phase_2_action_count_p95": _as_float_percentile(
                        denied_rows["trajectory_phase_2_action_count"].astype(float), 0.95
                    ),
                    "phase_3_action_count_p95": _as_float_percentile(
                        denied_rows["trajectory_phase_3_action_count"].astype(float), 0.95
                    ),
                }
            ]
        )
        if not denied_rows.empty
        else pd.DataFrame(
            [
                {
                    "phase_1_action_count_p50": 0.0,
                    "phase_2_action_count_p50": 0.0,
                    "phase_3_action_count_p50": 0.0,
                    "phase_1_action_count_p95": 0.0,
                    "phase_2_action_count_p95": 0.0,
                    "phase_3_action_count_p95": 0.0,
                }
            ]
        )
    )
    trajectory_phase_mix_out = run_ctx.tables_dir / "trajectory_phase_action_mix.csv"
    trajectory_phase_mix.to_csv(trajectory_phase_mix_out, index=False)
    denied_segment_funnel_out = run_ctx.tables_dir / "denied_lift_by_income_risk.csv"
    denied_segment_funnel.to_csv(denied_segment_funnel_out, index=False)
    high_risk_bridge_diag = batch_df[
        (batch_df["denied_base"].astype(int) == 1) & (batch_df["risk_band"].astype(str) == "high")
    ][
        [
            "customer_id",
            "base_pd",
            "best_candidate_pd",
            "candidate_pd_delta",
            "best_status",
            "best_ci_high",
            "best_reliability",
            "best_worst_risk_margin",
            "high_risk_bridge_hit",
            "denied_not_approved_root_cause",
            "best_source",
            "best_action_count",
            "best_cost_usd",
            "trajectory_gate_pass_4w",
            "trajectory_gate_pass_12w",
            "trajectory_gate_pass_24w",
            "trajectory_pd_delta_24w",
            "trajectory_phase_1_action_count",
            "trajectory_phase_2_action_count",
            "trajectory_phase_3_action_count",
        ]
    ].copy()
    high_risk_bridge_diag_out = run_ctx.tables_dir / "high_risk_bridge_diagnostics.csv"
    high_risk_bridge_diag.to_csv(high_risk_bridge_diag_out, index=False)

    reliability_threshold_by_risk_band = _extract_reliability_thresholds_by_risk_band(
        uncertainty_cfg=uncertainty_cfg,
        default_min_reliability=min_reliability_global_f,
    )
    denied_gate_breakdown, denied_source_breakdown, denied_income_lift, denied_risk_lift, denied_diag_metrics = (
        _build_denied_diagnostics(
            batch_df,
            tau=tau,
            min_reliability=min_reliability_global_f,
            min_worst_risk_margin=min_worst_margin_global_f,
            reliability_threshold_by_risk_band=reliability_threshold_by_risk_band,
        )
    )
    denied_gate_breakdown_out = run_ctx.tables_dir / "denied_gate_violation_breakdown.csv"
    denied_gate_breakdown.to_csv(denied_gate_breakdown_out, index=False)
    denied_source_breakdown_out = run_ctx.tables_dir / "denied_candidate_source_breakdown.csv"
    denied_source_breakdown.to_csv(denied_source_breakdown_out, index=False)
    denied_income_lift_out = run_ctx.tables_dir / "denied_lift_by_income_band.csv"
    denied_income_lift.to_csv(denied_income_lift_out, index=False)
    denied_risk_lift_out = run_ctx.tables_dir / "denied_lift_by_risk_band.csv"
    denied_risk_lift.to_csv(denied_risk_lift_out, index=False)

    backend_counts = (
        batch_df["dice_backend"]
        .replace("", "missing")
        .value_counts(dropna=False)
        .rename_axis("dice_backend")
        .reset_index(name="count")
    )
    backend_out = run_ctx.tables_dir / "dice_backend_distribution.csv"
    backend_counts.to_csv(backend_out, index=False)

    fallback_counts = (
        batch_df["dice_fallback_reason"]
        .replace("", "none")
        .value_counts(dropna=False)
        .rename_axis("dice_fallback_reason")
        .reset_index(name="count")
    )
    fallback_out = run_ctx.tables_dir / "dice_fallback_distribution.csv"
    fallback_counts.to_csv(fallback_out, index=False)

    candidate_quality_summary, candidate_source_breakdown = _build_candidate_quality_artifacts(batch_df)
    candidate_quality_summary_out = run_ctx.tables_dir / "candidate_quality_summary.json"
    candidate_quality_summary_out.write_text(
        json.dumps(candidate_quality_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    candidate_source_breakdown_out = run_ctx.tables_dir / "candidate_source_breakdown.csv"
    candidate_source_breakdown.to_csv(candidate_source_breakdown_out, index=False)
    behavior_aware_summary, execution_probability_breakdown, partial_execution_breakdown = _build_behavior_aware_artifacts(
        batch_df
    )
    behavior_aware_summary_out = run_ctx.tables_dir / "behavior_aware_summary.json"
    behavior_aware_summary_out.write_text(
        json.dumps(behavior_aware_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    execution_probability_breakdown_out = run_ctx.tables_dir / "execution_probability_breakdown.csv"
    execution_probability_breakdown.to_csv(execution_probability_breakdown_out, index=False)
    partial_execution_breakdown_out = run_ctx.tables_dir / "partial_execution_breakdown.csv"
    partial_execution_breakdown.to_csv(partial_execution_breakdown_out, index=False)
    (
        offer_optimization_summary,
        offer_type_breakdown,
        offer_policy_arm_breakdown,
        offer_acceptance_breakdown,
        offer_proxy_impact_breakdown,
    ) = _build_offer_optimization_artifacts(batch_df)
    offer_optimization_summary_out = run_ctx.tables_dir / "offer_optimization_summary.json"
    offer_optimization_summary_out.write_text(
        json.dumps(offer_optimization_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    offer_type_breakdown_out = run_ctx.tables_dir / "offer_type_breakdown.csv"
    offer_type_breakdown.to_csv(offer_type_breakdown_out, index=False)
    offer_policy_arm_breakdown_out = run_ctx.tables_dir / "offer_policy_arm_breakdown.csv"
    offer_policy_arm_breakdown.to_csv(offer_policy_arm_breakdown_out, index=False)
    offer_acceptance_breakdown_out = run_ctx.tables_dir / "offer_acceptance_breakdown.csv"
    offer_acceptance_breakdown.to_csv(offer_acceptance_breakdown_out, index=False)
    offer_proxy_impact_breakdown_out = run_ctx.tables_dir / "offer_proxy_impact_breakdown.csv"
    offer_proxy_impact_breakdown.to_csv(offer_proxy_impact_breakdown_out, index=False)
    trajectory_summary, trajectory_transition_breakdown, trajectory_policy_label_breakdown = _build_trajectory_artifacts(
        batch_df
    )
    trajectory_summary_out = run_ctx.tables_dir / "trajectory_summary.json"
    trajectory_summary_out.write_text(
        json.dumps(trajectory_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    trajectory_transition_breakdown_out = run_ctx.tables_dir / "trajectory_transition_breakdown.csv"
    trajectory_transition_breakdown.to_csv(trajectory_transition_breakdown_out, index=False)
    trajectory_policy_label_breakdown_out = run_ctx.tables_dir / "trajectory_policy_label_breakdown.csv"
    trajectory_policy_label_breakdown.to_csv(trajectory_policy_label_breakdown_out, index=False)
    portfolio_validation_artifacts = build_portfolio_validation_artifacts(
        batch_df,
        tau=float(tau),
        reliability_threshold_by_risk_band=reliability_threshold_by_risk_band,
        demo_case=_load_curated_demo_case(Path(__file__).resolve().parents[3]),
    )
    portfolio_validation_summary = portfolio_validation_artifacts["summary"]
    portfolio_validation_summary_out = run_ctx.tables_dir / "portfolio_validation_summary.json"
    portfolio_validation_summary_out.write_text(
        json.dumps(portfolio_validation_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    portfolio_coverage_breakdown_out = run_ctx.tables_dir / "portfolio_coverage_breakdown.csv"
    portfolio_validation_artifacts["coverage_breakdown"].to_csv(portfolio_coverage_breakdown_out, index=False)
    portfolio_coverage_drop_breakdown_out = run_ctx.tables_dir / "portfolio_coverage_drop_breakdown.csv"
    portfolio_validation_artifacts["coverage_drop_breakdown"].to_csv(portfolio_coverage_drop_breakdown_out, index=False)
    portfolio_reality_gap_breakdown_out = run_ctx.tables_dir / "portfolio_reality_gap_breakdown.csv"
    portfolio_validation_artifacts["reality_gap_breakdown"].to_csv(portfolio_reality_gap_breakdown_out, index=False)
    portfolio_segment_breakdown_out = run_ctx.tables_dir / "portfolio_segment_breakdown.csv"
    portfolio_validation_artifacts["segment_breakdown"].to_csv(portfolio_segment_breakdown_out, index=False)
    portfolio_offer_diagnostics_out = run_ctx.tables_dir / "portfolio_offer_diagnostics.csv"
    portfolio_validation_artifacts["offer_diagnostics"].to_csv(portfolio_offer_diagnostics_out, index=False)
    portfolio_behavior_comparison_out = run_ctx.tables_dir / "portfolio_behavior_comparison.csv"
    portfolio_validation_artifacts["behavior_comparison"].to_csv(portfolio_behavior_comparison_out, index=False)
    portfolio_trajectory_class_breakdown_out = run_ctx.tables_dir / "portfolio_trajectory_class_breakdown.csv"
    portfolio_validation_artifacts["trajectory_class_breakdown"].to_csv(
        portfolio_trajectory_class_breakdown_out, index=False
    )
    demo_representativeness_summary_out = run_ctx.tables_dir / "demo_representativeness_summary.json"
    demo_representativeness_summary_out.write_text(
        json.dumps(portfolio_validation_artifacts["demo_representativeness"], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    portfolio_validation_review_out = run_ctx.tables_dir / "portfolio_validation_review.md"
    portfolio_validation_review_out.write_text(
        portfolio_validation_artifacts["review_markdown"],
        encoding="utf-8",
    )
    decision_log_records = _build_decision_log_records(batch_df, run_id=run_ctx.run_id)
    decision_log_records_csv = decision_log_records.copy(deep=True)
    if not decision_log_records_csv.empty:
        decision_log_records_csv["policy_arm_profile"] = decision_log_records_csv["policy_arm_profile"].map(
            lambda value: json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else "{}"
        )
        decision_log_records_csv["reason_codes"] = decision_log_records_csv["reason_codes"].map(
            lambda value: json.dumps(value, ensure_ascii=False) if isinstance(value, list) else "[]"
        )
    decision_log_records_out = run_ctx.tables_dir / "decision_log_records.csv"
    decision_log_records_csv.to_csv(decision_log_records_out, index=False)
    decision_logging_summary = build_decision_logging_summary(decision_log_records)
    decision_logging_summary_out = run_ctx.tables_dir / "decision_logging_summary.json"
    decision_logging_summary_out.write_text(
        json.dumps(decision_logging_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    err_df = batch_df[batch_df["error_type"] != ""]
    err_counts = (
        err_df["error_type"].value_counts(dropna=False).rename_axis("error_type").reset_index(name="count")
        if not err_df.empty
        else pd.DataFrame(columns=["error_type", "count"])
    )
    err_out = run_ctx.tables_dir / "batch_error_breakdown.csv"
    err_counts.to_csv(err_out, index=False)

    latency_p95 = _as_float_percentile(batch_df["elapsed_ms"], 0.95)
    latency_p99 = _as_float_percentile(batch_df["elapsed_ms"], 0.99)
    sync_latency_p95 = _as_float_percentile(batch_df["sync_elapsed_ms"].astype(float), 0.95)
    sync_latency_p99 = _as_float_percentile(batch_df["sync_elapsed_ms"].astype(float), 0.99)
    latency_outliers = batch_df[
        (batch_df["elapsed_ms"] > max(1000.0, latency_p99))
        | (batch_df["error_type"] != "")
    ].copy()
    latency_outliers["is_gt_1s"] = (latency_outliers["elapsed_ms"] > 1000.0).astype(int)
    latency_outliers["is_gt_5s"] = (latency_outliers["elapsed_ms"] > 5000.0).astype(int)
    latency_out = run_ctx.tables_dir / "latency_outliers.csv"
    latency_outliers.to_csv(latency_out, index=False)

    scored_base = sampled_sorted[[args.group_feature, target_col]].copy()
    scored_base = scored_base.rename(columns={target_col: "y_true"})
    scored_base["group_bucket"] = _build_group_bucket(scored_base[args.group_feature])
    post_proba_s = pd.Series(batch_df["best_pd"].to_numpy(dtype=float), index=sampled_sorted.index, dtype=float)

    before_scored = scored_base[["group_bucket", "y_true"]].copy()
    before_scored["approve"] = (base_proba <= tau).astype(int)
    before_scored["pred_default"] = (base_proba > tau).astype(int)
    before_bundle = compute_fairness_bundle(before_scored, group_col="group_bucket", approval_col="approve", y_true_col="y_true", y_pred_col="pred_default")

    after_scored = scored_base[["group_bucket", "y_true"]].copy()
    after_scored["approve"] = (post_proba_s <= tau).astype(int)
    after_scored["pred_default"] = (post_proba_s > tau).astype(int)
    after_bundle = compute_fairness_bundle(after_scored, group_col="group_bucket", approval_col="approve", y_true_col="y_true", y_pred_col="pred_default")

    fairness_segment_sets_raw = fairness_cfg.get("segment_sets")
    fairness_segment_sets: list[list[str]] = []
    if isinstance(fairness_segment_sets_raw, list):
        for entry in fairness_segment_sets_raw:
            if isinstance(entry, str):
                fairness_segment_sets.append([entry])
            elif isinstance(entry, list):
                fairness_segment_sets.append([str(c) for c in entry if str(c).strip()])
    if not fairness_segment_sets:
        fairness_segment_sets = [
            ["home_ownership"],
            ["income_band"],
            ["risk_band"],
            ["income_band", "risk_band"],
            ["home_ownership", "risk_band"],
        ]
    min_segment_n = int(max(1, fairness_cfg.get("min_segment_n", 30)))
    segment_context_df = pd.DataFrame(
        {
            "income_band": batch_df["income_band"].astype(str).values,
            "risk_band": batch_df["risk_band"].astype(str).values,
        },
        index=sampled_sorted.index,
    )
    for col in ("home_ownership", "age_band"):
        if col in sampled_sorted.columns:
            segment_context_df[col] = sampled_sorted[col].astype(str).values
    before_multi = pd.DataFrame(
        {
            "y_true": before_scored["y_true"].astype(int).values,
            "approve": before_scored["approve"].astype(int).values,
            "pred_default": before_scored["pred_default"].astype(int).values,
        }
    )
    after_multi = pd.DataFrame(
        {
            "y_true": after_scored["y_true"].astype(int).values,
            "approve": after_scored["approve"].astype(int).values,
            "pred_default": after_scored["pred_default"].astype(int).values,
        }
    )
    for c in segment_context_df.columns:
        before_multi[c] = segment_context_df[c].values
        after_multi[c] = segment_context_df[c].values
    before_multi_eval = compute_multi_segment_fairness(
        before_multi,
        segment_sets=fairness_segment_sets,
        min_segment_n=min_segment_n,
    ).rename(
        columns={
            "approval_gap": "approval_gap_before",
            "equalized_odds_gap": "equalized_odds_gap_before",
            "adverse_impact_ratio": "adverse_impact_ratio_before",
            "segment_coverage_rate": "segment_coverage_rate_before",
            "reportable_group_count": "reportable_group_count_before",
            "total_group_count": "total_group_count_before",
        }
    )
    after_multi_eval = compute_multi_segment_fairness(
        after_multi,
        segment_sets=fairness_segment_sets,
        min_segment_n=min_segment_n,
    ).rename(
        columns={
            "approval_gap": "approval_gap_after",
            "equalized_odds_gap": "equalized_odds_gap_after",
            "adverse_impact_ratio": "adverse_impact_ratio_after",
            "segment_coverage_rate": "segment_coverage_rate_after",
            "reportable_group_count": "reportable_group_count_after",
            "total_group_count": "total_group_count_after",
        }
    )
    fairness_multi_compare = before_multi_eval.merge(
        after_multi_eval,
        on=["segment_id", "group_cols"],
        how="outer",
    )
    for col in (
        "approval_gap_before",
        "approval_gap_after",
        "equalized_odds_gap_before",
        "equalized_odds_gap_after",
    ):
        if col not in fairness_multi_compare.columns:
            fairness_multi_compare[col] = 0.0
    fairness_multi_compare["approval_gap_delta"] = (
        fairness_multi_compare["approval_gap_after"].astype(float)
        - fairness_multi_compare["approval_gap_before"].astype(float)
    )
    fairness_multi_compare["equalized_odds_gap_delta"] = (
        fairness_multi_compare["equalized_odds_gap_after"].astype(float)
        - fairness_multi_compare["equalized_odds_gap_before"].astype(float)
    )
    fairness_multi_out = run_ctx.tables_dir / "batch_fairness_multi_segment.csv"
    fairness_multi_compare.to_csv(fairness_multi_out, index=False)

    recourse_scored = pd.DataFrame(
        {
            "group_bucket": scored_base["group_bucket"].astype(str).values,
            "denied_base": batch_df["denied_base"].astype(int).values,
            "gate_pass_any_candidate": batch_df["gate_pass_any_candidate"].astype(int).values,
            "best_cost_usd": batch_df["best_cost_usd"].astype(float).values,
            "best_horizon_months": batch_df["best_horizon_months"].astype(int).values,
        }
    )
    recourse_fairness_bundle = build_recourse_fairness_bundle(
        recourse_scored,
        group_col="group_bucket",
        denied_col="denied_base",
        success_col="gate_pass_any_candidate",
        cost_col="best_cost_usd",
        horizon_col="best_horizon_months",
    )
    recourse_fairness_group = (
        recourse_scored[recourse_scored["denied_base"] == 1]
        .groupby("group_bucket", dropna=False)
        .agg(
            denied_count=("denied_base", "size"),
            recourse_success_rate=("gate_pass_any_candidate", "mean"),
            avg_best_cost_usd=("best_cost_usd", "mean"),
            avg_best_horizon_months=("best_horizon_months", "mean"),
        )
        .reset_index()
    )
    recourse_fairness_group_out = run_ctx.tables_dir / "batch_recourse_fairness.csv"
    recourse_fairness_group.to_csv(recourse_fairness_group_out, index=False)

    high_stress_sev = float(m_cfg.get("fairness", {}).get("high_stress_severity", 0.6))
    before_stress = build_fairness_stress_matrix(
        scored_base=scored_base[["group_bucket", "y_true"]],
        proba=base_proba,
        tau=tau,
        scenarios=scenarios,
        threshold_shift_per_msi_unit=threshold_shift,
        group_col="group_bucket",
        high_stress_severity=high_stress_sev,
    )
    after_stress = build_fairness_stress_matrix(
        scored_base=scored_base[["group_bucket", "y_true"]],
        proba=post_proba_s,
        tau=tau,
        scenarios=scenarios,
        threshold_shift_per_msi_unit=threshold_shift,
        group_col="group_bucket",
        high_stress_severity=high_stress_sev,
    )

    hs_before = _high_stress_gap(before_stress, fallback=float(before_bundle.get("approval_gap", 0.0)))
    hs_after = _high_stress_gap(after_stress, fallback=float(after_bundle.get("approval_gap", 0.0)))
    fairness_change = pd.DataFrame(
        [
            {
                "n_customers": n,
                "group_feature": args.group_feature,
                "approval_gap_before": float(before_bundle.get("approval_gap", 0.0)),
                "approval_gap_after": float(after_bundle.get("approval_gap", 0.0)),
                "approval_gap_delta": float(after_bundle.get("approval_gap", 0.0) - before_bundle.get("approval_gap", 0.0)),
                "equalized_odds_gap_before": float(before_bundle.get("equalized_odds_gap", 0.0)),
                "equalized_odds_gap_after": float(after_bundle.get("equalized_odds_gap", 0.0)),
                "equalized_odds_gap_delta": float(after_bundle.get("equalized_odds_gap", 0.0) - before_bundle.get("equalized_odds_gap", 0.0)),
                "high_stress_approval_gap_before": hs_before,
                "high_stress_approval_gap_after": hs_after,
                "high_stress_approval_gap_delta": float(hs_after - hs_before),
                "recourse_success_gap": float(recourse_fairness_bundle.get("recourse_success_gap", 0.0)),
                "recourse_cost_gap": float(recourse_fairness_bundle.get("recourse_cost_gap", 0.0)),
                "recourse_horizon_gap": float(recourse_fairness_bundle.get("recourse_horizon_gap", 0.0)),
            }
        ]
    )
    fairness_out = run_ctx.tables_dir / "batch_fairness_change.csv"
    fairness_change.to_csv(fairness_out, index=False)

    stress_compare = before_stress.merge(after_stress, on="scenario", suffixes=("_before", "_after"))
    stress_compare["approval_gap_delta"] = stress_compare["approval_gap_after"] - stress_compare["approval_gap_before"]
    stress_compare["equalized_odds_gap_delta"] = stress_compare["equalized_odds_gap_after"] - stress_compare["equalized_odds_gap_before"]
    stress_out = run_ctx.tables_dir / "batch_fairness_stress_compare.csv"
    stress_compare.to_csv(stress_out, index=False)
    fairness_failure_breakdown = _build_fairness_failure_breakdown(
        batch_df=batch_df,
        sampled_sorted=sampled_sorted,
        base_proba=base_proba,
        tau=tau,
        group_feature=args.group_feature,
        target_col=target_col,
    )
    fairness_failure_breakdown_out = run_ctx.tables_dir / "fairness_failure_breakdown.csv"
    fairness_failure_breakdown.to_csv(fairness_failure_breakdown_out, index=False)
    fairness_worst_segment = (
        fairness_failure_breakdown.iloc[0]
        if not fairness_failure_breakdown.empty
        else pd.Series(dtype=object)
    )

    summary = {
        "model_version": manifest.get("model_version"),
        "model_freeze_mode": manifest.get("freeze_mode", "implicit_latest"),
        "model_manifest_path": manifest.get("manifest_path", ""),
        "config_hash": config_hash,
        "train_data_hash": train_file_hash,
        "test_data_hash": test_file_hash,
        "n_customers": int(n),
        "processed_rows": int(len(batch_df)),
        "top_plan_source": _safe_str(top_plan.get("best_source", "")),
        "top_plan_horizon_months": _safe_int(top_plan.get("best_horizon_months", 0)),
        "top_plan_strategy": _safe_str(top_plan.get("best_strategy", "")),
        "top_plan_count": _safe_int(top_plan.get("count", 0)),
        "top_plan_share": _safe_float(top_plan.get("share", 0.0)),
        "top_plan_approved_source": _safe_str(top_plan_approved.get("best_source", "")),
        "top_plan_approved_horizon_months": _safe_int(top_plan_approved.get("best_horizon_months", 0)),
        "top_plan_approved_strategy": _safe_str(top_plan_approved.get("best_strategy", "")),
        "top_plan_approved_count": _safe_int(top_plan_approved.get("count", 0)),
        "top_plan_approved_share": _safe_float(top_plan_approved.get("share", 0.0)),
        "top_plan_denied_source": _safe_str(top_plan_denied.get("best_source", "")),
        "top_plan_denied_horizon_months": _safe_int(top_plan_denied.get("best_horizon_months", 0)),
        "top_plan_denied_strategy": _safe_str(top_plan_denied.get("best_strategy", "")),
        "top_plan_denied_count": _safe_int(top_plan_denied.get("count", 0)),
        "top_plan_denied_share": _safe_float(top_plan_denied.get("share", 0.0)),
        "top_recommended_step_phase_id": _safe_str(top_step.get("phase_id", "")),
        "top_recommended_step_phase_title": _safe_str(top_step.get("phase_title", "")),
        "top_recommended_step_feature": _safe_str(top_step.get("feature_name", "")),
        "top_recommended_step_count": _safe_int(top_step.get("count", 0)),
        "top_recommended_step_share": _safe_float(top_step.get("share", 0.0)),
        "error_count": int((batch_df["error_type"] != "").sum()),
        "error_rate": float((batch_df["error_type"] != "").mean()),
        "denied_count": denied_count,
        "denied_with_any_candidate": denied_with_any_candidate,
        "denied_with_gate_pass_plan": denied_with_gate_pass_plan,
        "denied_to_approved_lift": denied_to_approved_lift,
        "denied_high_risk_count": denied_high_risk_count,
        "denied_high_risk_lift": denied_high_risk_lift,
        "denied_high_risk_bridge_count": denied_high_risk_bridge_count,
        "denied_high_risk_bridge_rate": denied_high_risk_bridge_rate,
        "denied_high_risk_any_pd_reduction_count": denied_high_risk_any_pd_reduction_count,
        "denied_high_risk_any_pd_reduction_rate": denied_high_risk_any_pd_reduction_rate,
        "denied_high_risk_targeted_count": denied_high_risk_targeted_count,
        "denied_high_risk_targeted_rate": denied_high_risk_targeted_rate,
        "denied_high_risk_nonrejected_best_rate": denied_high_risk_nonrejected_best_rate,
        "high_risk_targeted_rate": denied_high_risk_targeted_rate,
        "high_risk_nonrejected_best_rate": denied_high_risk_nonrejected_best_rate,
        "denied_high_risk_avg_candidate_pd_reduction": denied_high_risk_avg_candidate_pd_reduction,
        "denied_high_risk_p95_candidate_pd_reduction": denied_high_risk_p95_candidate_pd_reduction,
        "high_risk_reachability_rate": high_risk_reachability_rate,
        "trajectory_enabled": int(trajectory_enabled),
        "trajectory_partial_progress_min_pd_delta": float(trajectory_partial_progress_min_pd_delta),
        "trajectory_gate_pass_rate_4w": float(trajectory_gate_pass_rate_4w),
        "trajectory_gate_pass_rate_12w": float(trajectory_gate_pass_rate_12w),
        "trajectory_gate_pass_rate_24w": float(trajectory_gate_pass_rate_24w),
        "trajectory_partial_progress_rate": float(trajectory_partial_progress_rate),
        "trajectory_median_time_to_gate_pass_days": float(trajectory_median_time_to_gate_pass_days),
        "trajectory_soft_regression_penalty_mean": float(
            trajectory_summary["canonical_metrics"]["trajectory_soft_regression_penalty_mean"]
        ),
        "trajectory_on_track_rate": float(trajectory_summary["canonical_metrics"]["trajectory_on_track_rate"]),
        "trajectory_needs_replan_rate": float(trajectory_summary["canonical_metrics"]["trajectory_needs_replan_rate"]),
        "trajectory_degraded_rate": float(trajectory_summary["canonical_metrics"]["trajectory_degraded_rate"]),
        "trajectory_dominant_transition_reason": str(trajectory_summary["dominant_transition_reason"]),
        "high_risk_denied_trajectory_gate_pass_rate_4w": float(
            trajectory_summary["secondary_metrics"]["trajectory_gate_pass_rate_4w"]
        ),
        "high_risk_denied_trajectory_gate_pass_rate_12w": float(
            trajectory_summary["secondary_metrics"]["trajectory_gate_pass_rate_12w"]
        ),
        "high_risk_denied_trajectory_gate_pass_rate_24w": float(
            trajectory_summary["secondary_metrics"]["trajectory_gate_pass_rate_24w"]
        ),
        "high_risk_denied_trajectory_partial_progress_rate": float(
            trajectory_summary["secondary_metrics"]["trajectory_partial_progress_rate"]
        ),
        "high_risk_denied_trajectory_median_time_to_gate_pass_days": float(
            trajectory_summary["secondary_metrics"]["trajectory_median_time_to_gate_pass_days"]
        ),
        "high_risk_denied_trajectory_soft_regression_penalty_mean": float(
            trajectory_summary["secondary_metrics"]["trajectory_soft_regression_penalty_mean"]
        ),
        "high_risk_denied_trajectory_on_track_rate": float(
            trajectory_summary["secondary_metrics"]["trajectory_on_track_rate"]
        ),
        "high_risk_denied_trajectory_needs_replan_rate": float(
            trajectory_summary["secondary_metrics"]["trajectory_needs_replan_rate"]
        ),
        "high_risk_denied_trajectory_degraded_rate": float(
            trajectory_summary["secondary_metrics"]["trajectory_degraded_rate"]
        ),
        "trajectory_phase_1_action_count_p50": float(trajectory_phase_mix.iloc[0]["phase_1_action_count_p50"]),
        "trajectory_phase_2_action_count_p50": float(trajectory_phase_mix.iloc[0]["phase_2_action_count_p50"]),
        "trajectory_phase_3_action_count_p50": float(trajectory_phase_mix.iloc[0]["phase_3_action_count_p50"]),
        "trajectory_phase_1_action_count_p95": float(trajectory_phase_mix.iloc[0]["phase_1_action_count_p95"]),
        "trajectory_phase_2_action_count_p95": float(trajectory_phase_mix.iloc[0]["phase_2_action_count_p95"]),
        "trajectory_phase_3_action_count_p95": float(trajectory_phase_mix.iloc[0]["phase_3_action_count_p95"]),
        "trajectory_stabilize_first_rate": float(
            (batch_df["trajectory_policy_label"].astype(str) == "stabilize_first").mean()
        ),
        "trajectory_balanced_progress_rate": float(
            (batch_df["trajectory_policy_label"].astype(str) == "balanced_progress").mean()
        ),
        "trajectory_long_horizon_heavy_rate": float(
            (batch_df["trajectory_policy_label"].astype(str) == "long_horizon_heavy").mean()
        ),
        "denied_reliability_violation_rate": float(denied_diag_metrics.get("denied_reliability_violation_rate", 0.0)),
        "denied_ci_violation_rate": float(denied_diag_metrics.get("denied_ci_violation_rate", 0.0)),
        "denied_worst_margin_violation_rate": float(denied_diag_metrics.get("denied_worst_margin_violation_rate", 0.0)),
        "denied_reliability_threshold_default": float(
            denied_diag_metrics.get(
                "denied_reliability_threshold_default",
                min_reliability_global_f if min_reliability_global_f is not None else 0.0,
            )
        ),
        "denied_internal_gate_pass_share": float(denied_diag_metrics.get("denied_internal_gate_pass_share", 0.0)),
        "denied_dice_gate_pass_share": float(denied_diag_metrics.get("denied_dice_gate_pass_share", 0.0)),
        "denied_rule_gate_pass_share": float(denied_diag_metrics.get("denied_rule_gate_pass_share", 0.0)),
        "denied_internal_vs_dice_gate_pass_share": float(
            denied_diag_metrics.get("denied_internal_vs_dice_gate_pass_share", 0.0)
        ),
        "denied_nonrejected_best_rate": float(denied_diag_metrics.get("denied_nonrejected_best_rate", 0.0)),
        "denied_nan_gate_fields_rate": float(denied_diag_metrics.get("denied_nan_gate_fields_rate", 0.0)),
        "segment_caps_applied_rate": float(batch_df["segment_caps_applied"].astype(int).mean()),
        "segment_cap_multiplier_avg": float(batch_df["cap_multiplier_total"].astype(float).mean()),
        "our_best_approved_rate": float((batch_df["best_status"] == "APPROVED").mean()),
        "before_approval_rate": float((base_proba <= tau).mean()),
        "after_approval_rate": float((post_proba_s <= tau).mean()),
        "approval_rate_lift": float((post_proba_s <= tau).mean() - (base_proba <= tau).mean()),
        "avg_pd_reduction": float((base_proba - post_proba_s).mean()),
        "dice_success_rate": float(batch_df["dice_success"].mean()),
        "dice_backend_dice_count": int((batch_df["dice_backend"] == "dice").sum()),
        "best_source_dice_rate": float((batch_df["best_source"] == "dice").mean()),
        "best_source_rule_rate": float((batch_df["best_source"] == "rule").mean()),
        "best_source_fallback_rate": float((batch_df["best_source"] == "fallback").mean()),
        "best_source_internal_rate": float((batch_df["best_source"] == "internal").mean()),
        "candidate_pool_diversity_index": float(batch_df["candidate_pool_diversity_index"].astype(float).mean()),
        "candidate_source_entropy": float(batch_df["candidate_source_entropy"].astype(float).mean()),
        "action_type_behavioral_rate": float(action_type_behavioral_rate),
        "action_type_structural_rate": float(action_type_structural_rate),
        "action_type_institutional_rate": float(action_type_institutional_rate),
        "composite_action_rate": float(composite_action_rate),
        "action_realism_valid_action_count": int(batch_df["action_realism_valid_action_count"].astype(int).sum()),
        "action_realism_clipped_action_count": int(batch_df["action_realism_clipped_action_count"].astype(int).sum()),
        "action_realism_rejected_action_count": int(batch_df["action_realism_rejected_action_count"].astype(int).sum()),
        "action_realism_infeasible_plan_count": int(batch_df["action_realism_infeasible_plan_count"].astype(int).sum()),
        "action_realism_clipped_action_rate": float(
            batch_df["action_realism_clipped_action_count"].astype(float).sum()
            / max(
                1.0,
                batch_df["action_realism_valid_action_count"].astype(float).sum()
                + batch_df["action_realism_clipped_action_count"].astype(float).sum()
                + batch_df["action_realism_rejected_action_count"].astype(float).sum()
            )
        ),
        "action_realism_rejected_action_rate": float(
            batch_df["action_realism_rejected_action_count"].astype(float).sum()
            / max(
                1.0,
                batch_df["action_realism_valid_action_count"].astype(float).sum()
                + batch_df["action_realism_clipped_action_count"].astype(float).sum()
                + batch_df["action_realism_rejected_action_count"].astype(float).sum()
            )
        ),
        "infeasible_plan_rate": float(batch_df["action_realism_infeasible_plan_count"].astype(int).mean()),
        "repair_applied_rate": float(repair_applied_rate),
        "approval_pending_action_rate": float(approval_pending_action_rate),
        "invalid_combination_rate": float(invalid_combination_rate),
        "candidate_quality_population": str(candidate_quality_summary["canonical_population"]),
        "candidate_quality_secondary_population": str(candidate_quality_summary["secondary_population"]),
        "denied_candidate_pool_diversity_index": float(
            candidate_quality_summary["canonical_metrics"]["candidate_pool_diversity_index"]
        ),
        "denied_candidate_source_entropy": float(candidate_quality_summary["canonical_metrics"]["candidate_source_entropy"]),
        "denied_best_source_internal_rate": float(candidate_quality_summary["canonical_metrics"]["best_source_internal_rate"]),
        "denied_best_source_dice_rate": float(candidate_quality_summary["canonical_metrics"]["best_source_dice_rate"]),
        "denied_best_source_rule_rate": float(candidate_quality_summary["canonical_metrics"]["best_source_rule_rate"]),
        "denied_best_source_fallback_rate": float(candidate_quality_summary["canonical_metrics"]["best_source_fallback_rate"]),
        "high_risk_denied_candidate_pool_diversity_index": float(
            candidate_quality_summary["secondary_metrics"]["candidate_pool_diversity_index"]
        ),
        "high_risk_denied_candidate_source_entropy": float(
            candidate_quality_summary["secondary_metrics"]["candidate_source_entropy"]
        ),
        "high_risk_denied_best_source_internal_rate": float(
            candidate_quality_summary["secondary_metrics"]["best_source_internal_rate"]
        ),
        "high_risk_denied_best_source_dice_rate": float(
            candidate_quality_summary["secondary_metrics"]["best_source_dice_rate"]
        ),
        "high_risk_denied_best_source_rule_rate": float(
            candidate_quality_summary["secondary_metrics"]["best_source_rule_rate"]
        ),
        "high_risk_denied_best_source_fallback_rate": float(
            candidate_quality_summary["secondary_metrics"]["best_source_fallback_rate"]
        ),
        "mean_plan_execution_probability": float(
            behavior_aware_summary["canonical_metrics"]["mean_plan_execution_probability"]
        ),
        "expected_pd_improvement": float(
            behavior_aware_summary["canonical_metrics"]["expected_pd_improvement"]
        ),
        "partial_execution_rate": float(
            behavior_aware_summary["canonical_metrics"]["partial_execution_rate"]
        ),
        "failed_execution_rate": float(
            behavior_aware_summary["canonical_metrics"]["failed_execution_rate"]
        ),
        "mixed_execution_rate": float(
            behavior_aware_summary["canonical_metrics"]["mixed_execution_rate"]
        ),
        "expected_partial_progress_rate": float(
            behavior_aware_summary["canonical_metrics"]["expected_partial_progress_rate"]
        ),
        "high_risk_denied_mean_plan_execution_probability": float(
            behavior_aware_summary["secondary_metrics"]["mean_plan_execution_probability"]
        ),
        "high_risk_denied_expected_pd_improvement": float(
            behavior_aware_summary["secondary_metrics"]["expected_pd_improvement"]
        ),
        "high_risk_denied_partial_execution_rate": float(
            behavior_aware_summary["secondary_metrics"]["partial_execution_rate"]
        ),
        "high_risk_denied_failed_execution_rate": float(
            behavior_aware_summary["secondary_metrics"]["failed_execution_rate"]
        ),
        "high_risk_denied_mixed_execution_rate": float(
            behavior_aware_summary["secondary_metrics"]["mixed_execution_rate"]
        ),
        "high_risk_denied_expected_partial_progress_rate": float(
            behavior_aware_summary["secondary_metrics"]["expected_partial_progress_rate"]
        ),
        "offer_plan_rate": float(offer_optimization_summary["canonical_metrics"]["offer_plan_rate"]),
        "rankable_offer_rate": float(offer_optimization_summary["canonical_metrics"]["rankable_offer_rate"]),
        "offer_acceptance_probability_mean": float(
            offer_optimization_summary["canonical_metrics"]["offer_acceptance_probability_mean"]
        ),
        "combined_plan_realization_probability_mean": float(
            offer_optimization_summary["canonical_metrics"]["combined_plan_realization_probability_mean"]
        ),
        "expected_recovery_proxy": float(offer_optimization_summary["canonical_metrics"]["expected_recovery_proxy"]),
        "approval_rate_proxy_delta": float(
            offer_optimization_summary["canonical_metrics"]["approval_rate_proxy_delta"]
        ),
        "default_rate_90d_proxy_delta": float(
            offer_optimization_summary["canonical_metrics"]["default_rate_90d_proxy_delta"]
        ),
        "avg_margin_90d_proxy_delta": float(
            offer_optimization_summary["canonical_metrics"]["avg_margin_90d_proxy_delta"]
        ),
        "governance_safe_offer_rate": float(
            offer_optimization_summary["canonical_metrics"]["governance_safe_offer_rate"]
        ),
        "dominant_offer_type": str(offer_optimization_summary["canonical_metrics"]["dominant_offer_type"]),
        "high_risk_profile_applied_rate": float(batch_df["high_risk_profile_applied"].astype(int).mean()),
        "fairness_cap_boost_applied_rate": float(batch_df["fairness_cap_boost_applied"].astype(int).mean()),
        "fairness_cap_boost_factor_avg": float(batch_df["fairness_cap_boost_factor"].astype(float).mean()),
        "fairness_guard_enabled": int(fairness_guard_metrics.get("fairness_guard_enabled", 0)),
        "fairness_guard_demotion_count": int(fairness_guard_metrics.get("fairness_guard_demotion_count", 0)),
        "fairness_guard_iteration_count": int(fairness_guard_metrics.get("fairness_guard_iteration_count", 0)),
        "fairness_guard_stop_reason": str(fairness_guard_metrics.get("fairness_guard_stop_reason", "")),
        "fairness_guard_initial_equalized_odds_gap_delta": float(
            fairness_guard_metrics.get("fairness_guard_initial_equalized_odds_gap_delta", 0.0)
        ),
        "fairness_guard_final_equalized_odds_gap_delta": float(
            fairness_guard_metrics.get("fairness_guard_final_equalized_odds_gap_delta", 0.0)
        ),
        "fairness_guard_initial_approval_gap_after": float(
            fairness_guard_metrics.get("fairness_guard_initial_approval_gap_after", 0.0)
        ),
        "fairness_guard_final_approval_gap_after": float(
            fairness_guard_metrics.get("fairness_guard_final_approval_gap_after", 0.0)
        ),
        "fairness_guard_initial_recourse_success_gap": float(
            fairness_guard_metrics.get("fairness_guard_initial_recourse_success_gap", 0.0)
        ),
        "fairness_guard_final_recourse_success_gap": float(
            fairness_guard_metrics.get("fairness_guard_final_recourse_success_gap", 0.0)
        ),
        "fast_reason_mode_rate": float(batch_df["fast_reason_mode"].astype(int).mean()),
        "search_profile_budget_tuned_rate": float(batch_df["search_profile_budget_tuned"].astype(int).mean()),
        "internal_rescue_used_count": int(batch_df["internal_rescue_used"].astype(int).sum()),
        "internal_rescue_used_rate": float(batch_df["internal_rescue_used"].astype(int).mean()),
        "timeout_or_fallback_rate": float(
            (
                (batch_df["fallback_triggered"].astype(int) == 1)
                | (batch_df["dice_fallback_reason"].astype(str) == "time_budget_exceeded")
            ).mean()
        ),
        "budget_overshoot_count": int(batch_df["budget_overshoot"].astype(int).sum()),
        "budget_overshoot_rate": float(batch_df["budget_overshoot"].astype(int).mean()),
        "budget_overshoot_ms_p95": _as_float_percentile(batch_df["budget_overshoot_ms"].astype(float), 0.95),
        "deadline_abort_count": int(batch_df["deadline_abort"].astype(int).sum()),
        "deadline_abort_rate": float(batch_df["deadline_abort"].astype(int).mean()),
        "best_action_count_p50": _as_float_percentile(batch_df["best_action_count"].astype(float), 0.50),
        "best_action_count_p95": _as_float_percentile(batch_df["best_action_count"].astype(float), 0.95),
        "best_cost_p50": _as_float_percentile(batch_df["best_cost_usd"].astype(float), 0.50),
        "best_cost_p95": _as_float_percentile(batch_df["best_cost_usd"].astype(float), 0.95),
        "latency_avg_ms": float(batch_df["elapsed_ms"].mean()),
        "latency_p50_ms": _as_float_percentile(batch_df["elapsed_ms"], 0.50),
        "latency_p95_ms": latency_p95,
        "latency_p99_ms": latency_p99,
        "sync_latency_avg_ms": float(batch_df["sync_elapsed_ms"].astype(float).mean()),
        "sync_latency_p50_ms": _as_float_percentile(batch_df["sync_elapsed_ms"].astype(float), 0.50),
        "sync_latency_p95_ms": sync_latency_p95,
        "sync_latency_p99_ms": sync_latency_p99,
        "async_deep_path_used_rate": float(batch_df["async_deep_path_used"].astype(int).mean()),
        "latency_bucket_le_500_count": int((batch_df["elapsed_ms"] <= 500.0).sum()),
        "latency_bucket_le_1000_count": int((batch_df["elapsed_ms"] <= 1000.0).sum()),
        "latency_bucket_le_2000_count": int((batch_df["elapsed_ms"] <= 2000.0).sum()),
        "latency_bucket_gt_2000_count": int((batch_df["elapsed_ms"] > 2000.0).sum()),
        "latency_outlier_count": int(len(latency_outliers)),
        "elapsed_total_s": elapsed_s,
        "fairness_approval_gap_before": float(before_bundle.get("approval_gap", 0.0)),
        "fairness_approval_gap_after": float(after_bundle.get("approval_gap", 0.0)),
        "fairness_equalized_odds_gap_before": float(before_bundle.get("equalized_odds_gap", 0.0)),
        "fairness_equalized_odds_gap_after": float(after_bundle.get("equalized_odds_gap", 0.0)),
        "fairness_multi_max_approval_gap_after": (
            float(fairness_multi_compare["approval_gap_after"].astype(float).max())
            if not fairness_multi_compare.empty
            else 0.0
        ),
        "fairness_multi_max_approval_gap_delta": (
            float(fairness_multi_compare["approval_gap_delta"].astype(float).max())
            if not fairness_multi_compare.empty
            else 0.0
        ),
        "fairness_multi_max_equalized_odds_gap_after": (
            float(fairness_multi_compare["equalized_odds_gap_after"].astype(float).max())
            if not fairness_multi_compare.empty
            else 0.0
        ),
        "fairness_multi_max_equalized_odds_gap_delta": (
            float(fairness_multi_compare["equalized_odds_gap_delta"].astype(float).max())
            if not fairness_multi_compare.empty
            else 0.0
        ),
        "fairness_failure_worst_segment_key": _safe_str(fairness_worst_segment.get("segment_key", "")),
        "fairness_failure_worst_segment_size": _safe_int(fairness_worst_segment.get("n_rows", 0)),
        "fairness_failure_worst_segment_score": _safe_float(
            fairness_worst_segment.get("failure_severity_score", 0.0)
        ),
        "fairness_segment_coverage_rate": (
            float(fairness_multi_compare["segment_coverage_rate_after"].astype(float).min())
            if ("segment_coverage_rate_after" in fairness_multi_compare.columns and not fairness_multi_compare.empty)
            else 0.0
        ),
        "recourse_success_gap": float(recourse_fairness_bundle.get("recourse_success_gap", 0.0)),
        "recourse_cost_gap": float(recourse_fairness_bundle.get("recourse_cost_gap", 0.0)),
        "recourse_horizon_gap": float(recourse_fairness_bundle.get("recourse_horizon_gap", 0.0)),
        "high_stress_approval_gap_before": float(hs_before),
        "high_stress_approval_gap_after": float(hs_after),
        "alpha_used": alpha,
        "macro_stress_index": float(msi),
    }
    if not denied_root_causes.empty:
        summary["denied_not_approved_top_root_cause"] = _safe_str(denied_root_causes.iloc[0].get("root_cause", ""))
        summary["denied_not_approved_top_root_cause_share"] = _safe_float(denied_root_causes.iloc[0].get("share", 0.0))
    else:
        summary["denied_not_approved_top_root_cause"] = ""
        summary["denied_not_approved_top_root_cause_share"] = 0.0
    if not feasibility_rejection_breakdown.empty:
        summary["action_realism_top_rejection_reason"] = _safe_str(
            feasibility_rejection_breakdown.iloc[0].get("reason_code", "")
        )
        summary["action_realism_top_rejection_reason_count"] = _safe_int(
            feasibility_rejection_breakdown.iloc[0].get("count", 0)
        )
    else:
        summary["action_realism_top_rejection_reason"] = ""
        summary["action_realism_top_rejection_reason_count"] = 0
    if not constraint_repair_breakdown.empty:
        summary["action_realism_top_constraint_reason"] = _safe_str(
            constraint_repair_breakdown.iloc[0].get("reason_code", "")
        )
        summary["action_realism_top_constraint_reason_count"] = _safe_int(
            constraint_repair_breakdown.iloc[0].get("count", 0)
        )
    else:
        summary["action_realism_top_constraint_reason"] = ""
        summary["action_realism_top_constraint_reason_count"] = 0
    run_ctx.save_metrics(summary)

    action_realism_summary = {
        "canonical_population": "denied",
        "action_type_behavioral_rate": float(action_type_behavioral_rate),
        "action_type_structural_rate": float(action_type_structural_rate),
        "action_type_institutional_rate": float(action_type_institutional_rate),
        "composite_action_rate": float(composite_action_rate),
        "clipped_action_rate": float(summary["action_realism_clipped_action_rate"]),
        "rejected_action_rate": float(summary["action_realism_rejected_action_rate"]),
        "repair_applied_rate": float(repair_applied_rate),
        "approval_pending_action_rate": float(approval_pending_action_rate),
        "invalid_combination_rate": float(invalid_combination_rate),
        "infeasible_plan_rate": float(summary["infeasible_plan_rate"]),
        "dominant_rejection_reason": str(summary["action_realism_top_rejection_reason"]),
        "supporting_artifacts": {
            "action_type_breakdown_csv": "tables/action_type_breakdown.csv",
            "feasibility_rejection_breakdown_csv": "tables/feasibility_rejection_breakdown.csv",
            "constraint_repair_breakdown_csv": "tables/constraint_repair_breakdown.csv",
            "approval_pending_breakdown_csv": "tables/approval_pending_breakdown.csv",
        },
    }
    action_realism_summary_out = run_ctx.tables_dir / "action_realism_summary.json"
    action_realism_summary_out.write_text(
        json.dumps(action_realism_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    summary["decision_log_total"] = int(decision_logging_summary.get("total_decisions", 0))
    summary["complete_decision_logs"] = int(decision_logging_summary.get("complete_decision_logs", 0))
    summary["decision_log_completeness"] = float(decision_logging_summary.get("decision_log_completeness", 0.0))
    summary["selection_propensity_coverage"] = float(
        decision_logging_summary.get("selection_propensity_coverage", 0.0)
    )
    summary["candidate_set_coverage"] = float(decision_logging_summary.get("candidate_set_coverage", 0.0))
    summary["reason_code_coverage"] = float(decision_logging_summary.get("reason_code_coverage", 0.0))

    summary_json = run_ctx.tables_dir / "batch_summary.json"
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    high_risk_profile_activation = _build_high_risk_profile_activation_summary(batch_df, rec_cfg=rec_cfg)
    high_risk_tuning_summary = _build_batch_high_risk_tuning_summary(
        summary=summary,
        activation_summary=high_risk_profile_activation,
    )
    high_risk_tuning_summary_out = run_ctx.tables_dir / "high_risk_tuning_summary.json"
    high_risk_tuning_summary_out.write_text(
        json.dumps(high_risk_tuning_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    frozen_manifest_payload = build_frozen_model_manifest(
        manifest,
        project_root=Path(__file__).resolve().parents[3],
        resolved_by_runner="run_batch_recourse_eval",
    )
    manifest_payload = {
        "run_id": run_ctx.run_id,
        "model_version": manifest.get("model_version"),
        "model_manifest_path": manifest.get("manifest_path", ""),
        "model_freeze_mode": manifest.get("freeze_mode", "implicit_latest"),
        "requested_model_version": str(args.model_version).strip(),
        "requested_model_manifest": str(args.model_manifest).strip(),
        "acceptance_eligible": bool(manifest.get("acceptance_eligible", False)),
        "frozen_model_manifest": frozen_manifest_payload,
        "config_hash": config_hash,
        "data": {
            "train_path": str(train_path),
            "train_hash": train_file_hash,
            "test_path": str(test_path),
            "test_hash": test_file_hash,
        },
        "sample": {
            "n_customers": int(n),
            "sample_seed": int(args.sample_seed),
        },
        "high_risk_profile": {
            **high_risk_profile_activation,
            "summary_path": "tables/high_risk_tuning_summary.json",
        },
    }
    run_manifest_out = run_ctx.tables_dir / "batch_run_manifest.json"
    run_manifest_out.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Batch recourse evaluation completed. n=%s elapsed=%.2fs", n, elapsed_s)
    logger.info("Outputs: %s", run_ctx.tables_dir)


if __name__ == "__main__":
    main()
