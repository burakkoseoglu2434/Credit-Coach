from __future__ import annotations

from credit_coach.cli.run_batch_recourse_eval import (
    _apply_phase1_feature_boost,
    _apply_fairness_segment_cap_boost,
    _apply_high_risk_profile,
    _build_fairness_failure_breakdown,
    _candidate_pool_diversity_index,
    _candidate_source_entropy,
    _extract_model_importance_vector,
    _effective_recourse_search,
    _prune_candidate_pool,
    _stage1_filter_candidate_pool,
    _tune_internal_search_profile_for_budget,
)
import pandas as pd
from credit_coach.data.schema import PlanAction, PlanRecord


def _plan(plan_id: str, *, feat: str, pd: float, score: float) -> PlanRecord:
    return PlanRecord(
        plan_id=plan_id,
        customer_id="c1",
        run_id="r1",
        horizon_months=6,
        strategy="balanced",
        actions=[
            PlanAction(
                feature_name=feat,
                current_value=10.0,
                target_value=9.0,
                delta=-1.0,
                time_months=3,
                estimated_cost_usd=50.0,
            )
        ],
        predicted_pd=pd,
        score=score,
        robust_score=score,
        status="NEEDS_REVIEW",
    )


def _plan_with_source(plan_id: str, *, feat: str, source: str, pd: float, score: float) -> PlanRecord:
    if source == "dice":
        pid = f"{plan_id}_dice_1"
    elif source == "rule":
        pid = f"{plan_id}_rule_1"
    else:
        pid = plan_id
    return _plan(pid, feat=feat, pd=pd, score=score)


def test_apply_high_risk_profile_overrides_denied_search():
    search_profile = {
        "is_denied_target": True,
        "topk": 10,
        "horizons": [3, 6, 12],
        "strategies": ["conservative", "balanced", "aggressive"],
        "search_cfg": {"action_budget": {"enabled": True, "max_actions": 4}, "weekly_optimizer": {"enabled": False}},
    }
    robust_cfg = {"min_reliability": 0.70, "min_worst_risk_margin": -0.05}
    dice_cfg = {"total_cfs": 2, "max_actions": 2}
    rec_cfg = {
        "high_risk_profile": {
            "enabled": True,
            "denied_target_only": True,
            "topk_multiplier": 1.5,
            "min_topk": 14,
            "horizons": [6, 12],
            "strategies": ["balanced", "aggressive"],
            "force_weekly_optimizer": True,
            "weekly_weeks": 10,
            "weekly_max_actions": 3,
            "max_actions": 8,
            "min_reliability": 0.74,
            "min_worst_risk_margin": -0.03,
            "dice_total_cfs_multiplier": 2.0,
            "dice_max_actions_multiplier": 1.5,
        }
    }
    segment_context = {"risk_band": "high"}
    sp, rc, dc, applied = _apply_high_risk_profile(
        search_profile=search_profile,
        robust_cfg=robust_cfg,
        dice_cfg=dice_cfg,
        rec_cfg=rec_cfg,
        segment_context=segment_context,
    )
    assert applied is True
    assert sp["topk"] >= 14
    assert sp["horizons"] == [6, 12]
    assert sp["strategies"] == ["balanced", "aggressive"]
    assert sp["search_cfg"]["weekly_optimizer"]["enabled"] is True
    assert sp["search_cfg"]["action_budget"]["max_actions"] == 8
    assert rc["min_reliability"] == 0.74
    assert rc["min_worst_risk_margin"] == -0.03
    assert dc["total_cfs"] >= 4
    assert dc["max_actions"] >= 3


def test_apply_high_risk_profile_skips_when_pd_delta_above_cap():
    search_profile = {
        "is_denied_target": True,
        "topk": 10,
        "horizons": [3, 6],
        "strategies": ["balanced"],
        "search_cfg": {"action_budget": {"enabled": True, "max_actions": 4}, "weekly_optimizer": {"enabled": False}},
    }
    robust_cfg = {"min_reliability": 0.70, "min_worst_risk_margin": -0.05}
    dice_cfg = {"total_cfs": 2, "max_actions": 2}
    rec_cfg = {
        "high_risk_profile": {
            "enabled": True,
            "denied_target_only": True,
            "max_pd_delta": 0.05,
            "enforce_max_pd_delta": True,
            "topk_multiplier": 1.5,
        }
    }
    segment_context = {"risk_band": "high", "pd_distance_to_tau": 0.20}
    sp, rc, dc, applied = _apply_high_risk_profile(
        search_profile=search_profile,
        robust_cfg=robust_cfg,
        dice_cfg=dice_cfg,
        rec_cfg=rec_cfg,
        segment_context=segment_context,
    )
    assert applied is False
    assert sp["topk"] == 10
    assert rc["min_reliability"] == 0.70
    assert dc["total_cfs"] == 2


def test_prune_candidate_pool_with_novelty_increases_diversity():
    plans = [
        _plan("p_internal_1", feat="dti", pd=0.32, score=10.0),
        _plan("p_internal_2", feat="dti", pd=0.33, score=9.0),
        _plan("p_dice_1_dice_1", feat="revol_util", pd=0.34, score=8.0),
        _plan("p_rule_1_rule_1", feat="annual_inc", pd=0.35, score=7.0),
    ]
    plain = _prune_candidate_pool(plans, max_size=3, novelty_weight=0.0)
    diverse = _prune_candidate_pool(plans, max_size=3, novelty_weight=1.0)
    assert len(plain) == 3
    assert len(diverse) == 3
    assert _candidate_pool_diversity_index(diverse) >= _candidate_pool_diversity_index(plain)
    assert _candidate_source_entropy(diverse) >= 0.0


def test_stage1_filter_candidate_pool_applies_source_cap():
    plans = [
        _plan_with_source("p_internal_1", feat="dti", source="internal", pd=0.31, score=10.0),
        _plan_with_source("p_internal_2", feat="annual_inc", source="internal", pd=0.32, score=9.0),
        _plan_with_source("p_internal_3", feat="revol_util", source="internal", pd=0.33, score=8.0),
        _plan_with_source("p_dice_1", feat="dti", source="dice", pd=0.34, score=7.0),
        _plan_with_source("p_dice_2", feat="annual_inc", source="dice", pd=0.35, score=6.0),
        _plan_with_source("p_rule_1", feat="revol_util", source="rule", pd=0.36, score=5.0),
    ]
    stage1 = _stage1_filter_candidate_pool(
        plans,
        max_size=2,
        tau=0.35,
        min_reliability=0.70,
        min_worst_risk_margin=-0.05,
        multiplier=2.0,
        per_source_cap=1,
    )
    assert len(stage1) == 4
    assert sum(1 for p in stage1 if "_dice_" in p.plan_id) <= 1
    assert sum(1 for p in stage1 if "_rule_" in p.plan_id) <= 1
    assert sum(1 for p in stage1 if "_dice_" not in p.plan_id and "_rule_" not in p.plan_id) <= 2


def test_effective_recourse_search_propagates_latency_controls():
    rec_cfg = {
        "search_budget": {
            "per_customer_time_budget_ms": 2000,
            "candidate_pool_max_size": 12,
            "novelty_weight": 0.3,
            "skip_dice_when_internal_approved": True,
            "skip_dice_for_non_denied": True,
            "hard_time_budget_enforcement": True,
            "min_remaining_budget_for_dice_ms": 350,
            "min_remaining_budget_for_rule_ms": 120,
            "hard_max_dice_timeout_ms": 900,
            "dice_only_high_risk_denied": True,
            "stage1_filter_multiplier": 2.0,
            "stage1_per_source_cap": 6,
            "regular_horizons": [3, 6],
            "regular_strategies": ["conservative"],
            "regular_topk": 6,
            "enable_deterministic_fallback": True,
        }
    }
    profile, _, _ = _effective_recourse_search(
        base_pd=0.30,
        tau=0.35,
        topk=10,
        horizons=[3, 6, 12],
        strategies=["conservative", "balanced"],
        robust_cfg={},
        dice_cfg={},
        rec_cfg=rec_cfg,
        allow_denied_target=True,
    )
    search_cfg = profile["search_cfg"]
    assert search_cfg["hard_time_budget_enforcement"] is True
    assert search_cfg["min_remaining_budget_for_dice_ms"] == 350
    assert search_cfg["min_remaining_budget_for_rule_ms"] == 120
    assert search_cfg["hard_max_dice_timeout_ms"] == 900
    assert search_cfg["dice_only_high_risk_denied"] is True
    assert search_cfg["stage1_filter_multiplier"] == 2.0
    assert search_cfg["stage1_per_source_cap"] == 6
    assert search_cfg["enable_deterministic_fallback"] is True
    assert profile["horizons"] == [3, 6]
    assert profile["strategies"] == ["conservative"]
    assert profile["topk"] == 6


def test_effective_recourse_search_applies_distance_profile_for_far_denied():
    rec_cfg = {
        "denied_target": {
            "enabled": True,
            "activation_margin": 0.0,
            "horizons": [3, 6],
            "strategies": ["balanced", "aggressive"],
            "max_actions": 8,
            "strict_min_reliability": 0.40,
            "strict_min_worst_risk_margin": -0.12,
            "distance_profiles": {
                "far": {
                    "max_pd_delta": 1.0,
                    "horizons": [3],
                    "strategies": ["conservative"],
                    "topk": 6,
                    "max_actions": 4,
                    "enable_weekly_optimizer": False,
                    "disable_adaptive_steps": True,
                    "skip_dice": True,
                }
            },
        },
        "adaptive_steps": {"enabled": True, "only_denied": True},
        "weekly_optimizer": {"enabled": True, "only_denied": True},
        "search_budget": {},
        "action_budget": {"enabled": True, "max_actions_regular": 4, "max_actions_denied": 8},
    }
    profile, robust_cfg, _ = _effective_recourse_search(
        base_pd=0.80,
        tau=0.35,
        topk=10,
        horizons=[3, 6, 12],
        strategies=["conservative", "balanced"],
        robust_cfg={"min_reliability": 0.45, "min_worst_risk_margin": -0.12},
        dice_cfg={},
        rec_cfg=rec_cfg,
        allow_denied_target=True,
    )
    assert profile["is_denied_target"] is True
    assert profile["horizons"] == [3]
    assert profile["strategies"] == ["conservative"]
    assert profile["topk"] == 6
    assert profile["search_cfg"]["force_skip_dice"] is True


def test_apply_phase1_feature_boost_prioritizes_configured_fast_features():
    boosted = _apply_phase1_feature_boost(
        candidate_features=[
            {"feature": "annual_inc", "abs_contribution": 0.2},
            {"feature": "dti", "abs_contribution": 2.0},
            {"feature": "revol_util", "abs_contribution": 1.0},
        ],
        rec_cfg={
            "phase1_fast_track": {
                "enabled": True,
                "denied_only": True,
                "high_risk_only": True,
                "prioritized_features": ["dti", "revol_util"],
                "feature_boost_multiplier": 10.0,
                "append_missing_prioritized": False,
            }
        },
        denied_mode=True,
        risk_band="high",
        actionable=["annual_inc", "dti", "revol_util"],
    )
    assert boosted[0]["feature"] == "dti"
    assert boosted[1]["feature"] == "revol_util"


def test_apply_phase1_feature_boost_appends_missing_prioritized_features():
    boosted = _apply_phase1_feature_boost(
        candidate_features=[{"feature": "annual_inc", "abs_contribution": 3.0}],
        rec_cfg={
            "phase1_fast_track": {
                "enabled": True,
                "denied_only": True,
                "high_risk_only": True,
                "prioritized_features": ["dti", "revol_util"],
                "append_missing_prioritized": True,
                "max_append": 1,
            }
        },
        denied_mode=True,
        risk_band="high",
        actionable=["annual_inc", "dti", "revol_util"],
    )
    feats = [str(x["feature"]) for x in boosted]
    assert "annual_inc" in feats
    assert "dti" in feats or "revol_util" in feats


def test_build_fairness_failure_breakdown_outputs_expected_columns():
    batch_df = pd.DataFrame(
        {
            "risk_band": ["high", "high", "mid", "mid"],
            "income_band": ["q1", "q1", "q2", "q2"],
            "best_source": ["internal", "dice", "internal", "rule"],
            "best_pd": [0.40, 0.30, 0.36, 0.31],
            "denied_base": [1, 1, 1, 0],
            "gate_pass_any_candidate": [0, 1, 0, 1],
            "fairness_guard_demoted": [1, 0, 0, 0],
        }
    )
    sampled_sorted = pd.DataFrame(
        {
            "home_ownership": ["RENT", "MORTGAGE", "RENT", "OWN"],
            "is_default": [1, 0, 1, 0],
        }
    )
    base_proba = pd.Series([0.45, 0.32, 0.38, 0.29], dtype=float)
    out = _build_fairness_failure_breakdown(
        batch_df=batch_df,
        sampled_sorted=sampled_sorted,
        base_proba=base_proba,
        tau=0.35,
        group_feature="home_ownership",
        target_col="is_default",
    )
    assert not out.empty
    assert "segment_key" in out.columns
    assert "failure_severity_score" in out.columns


def test_apply_fairness_segment_cap_boost_for_high_penalty_high_risk_denied():
    rec_cfg = {
        "fairness": {
            "segment_cap_boost": {
                "enabled": True,
                "only_denied_target": True,
                "only_high_risk": True,
                "min_penalty": 0.03,
                "penalty_reference": 0.07,
                "cap_multiplier_boost_max": 1.30,
                "feature_cap_multiplier_boost_max": 1.15,
                "target_pd_margin_extra_max": 0.02,
            }
        }
    }
    segment_context = {
        "risk_band": "high",
        "cap_multiplier": 2.0,
        "cap_multiplier_max": 2.8,
        "segment_caps_applied": True,
        "feature_cap_multipliers": {"dti": 1.0},
    }
    out, pd_extra, applied, cap_boost_factor = _apply_fairness_segment_cap_boost(
        segment_context=segment_context,
        rec_cfg=rec_cfg,
        fairness_penalty=0.063,
        denied_mode=True,
    )
    assert applied is True
    assert cap_boost_factor > 1.0
    assert out["cap_multiplier"] > 2.0
    assert out["cap_multiplier"] <= 2.8
    assert out["feature_cap_multipliers"]["dti"] > 1.0
    assert pd_extra > 0.0


def test_apply_fairness_segment_cap_boost_skips_when_not_high_risk():
    rec_cfg = {
        "fairness": {
            "segment_cap_boost": {
                "enabled": True,
                "only_denied_target": True,
                "only_high_risk": True,
                "min_penalty": 0.03,
                "cap_multiplier_boost_max": 1.30,
            }
        }
    }
    segment_context = {
        "risk_band": "mid",
        "cap_multiplier": 1.5,
        "cap_multiplier_max": 2.8,
        "segment_caps_applied": True,
    }
    out, pd_extra, applied, cap_boost_factor = _apply_fairness_segment_cap_boost(
        segment_context=segment_context,
        rec_cfg=rec_cfg,
        fairness_penalty=0.08,
        denied_mode=True,
    )
    assert applied is False
    assert out["cap_multiplier"] == 1.5
    assert pd_extra == 0.0
    assert cap_boost_factor == 1.0


def test_tune_internal_search_profile_for_budget_reduces_search_space():
    profile = {
        "is_denied_target": True,
        "topk": 12,
        "horizons": [3, 6, 12],
        "strategies": ["conservative", "balanced", "aggressive"],
        "search_cfg": {
            "time_budget_ms": 900,
            "adaptive_steps": {"enabled": True, "max_attempts_per_feature": 4, "growth_factor": 1.8},
            "weekly_optimizer": {"enabled": True},
            "action_budget": {"enabled": True, "max_actions": 10},
        },
    }
    tuned = _tune_internal_search_profile_for_budget(
        profile,
        time_budget_ms=900,
        denied_mode=True,
        risk_band="high",
    )
    assert tuned["topk"] <= 10
    assert len(tuned["horizons"]) <= 2
    assert len(tuned["strategies"]) <= 2
    assert tuned["search_cfg"]["weekly_optimizer"]["enabled"] is False
    assert tuned["search_cfg"]["adaptive_steps"]["max_attempts_per_feature"] <= 3
    assert tuned["search_cfg"]["action_budget"]["max_actions"] <= 8


def test_tune_internal_search_profile_for_very_low_budget_disables_adaptive():
    profile = {
        "is_denied_target": False,
        "topk": 8,
        "horizons": [3, 6, 12],
        "strategies": ["balanced", "aggressive"],
        "search_cfg": {
            "time_budget_ms": 500,
            "adaptive_steps": {"enabled": True},
            "weekly_optimizer": {"enabled": True},
        },
    }
    tuned = _tune_internal_search_profile_for_budget(
        profile,
        time_budget_ms=500,
        denied_mode=False,
        risk_band="near",
    )
    assert tuned["topk"] <= 3
    assert len(tuned["horizons"]) == 1
    assert len(tuned["strategies"]) == 1
    assert tuned["search_cfg"]["adaptive_steps"]["enabled"] is False


def test_extract_model_importance_vector_reads_pipeline_steps():
    class _Estimator:
        coef_ = [[1.0, -0.5, 0.2]]

    class _Pipeline:
        named_steps = {"prep": object(), "model": _Estimator()}

    vec = _extract_model_importance_vector(_Pipeline(), ["f1", "f2", "f3"])
    assert vec is not None
    assert vec.tolist() == [1.0, -0.5, 0.2]
