from __future__ import annotations

import numpy as np
import pandas as pd

from credit_coach.cli.run_recourse import _effective_recourse_search
from credit_coach.evaluation.fairness import build_group_advantage_penalties, lookup_group_penalty
from credit_coach.recourse.generator import PlanGenConfig, generate_plan_record
from credit_coach.safety.statistical import estimate_prediction_ci


class _DummyModel:
    def predict_proba(self, x):
        df = x if isinstance(x, pd.DataFrame) else pd.DataFrame(x)
        inc = pd.to_numeric(df.get("annual_inc", pd.Series([50_000.0] * len(df))), errors="coerce").fillna(50_000.0)
        util = pd.to_numeric(df.get("revol_util", pd.Series([50.0] * len(df))), errors="coerce").fillna(50.0)
        p = (0.75 - (inc / 250000.0) + (util / 500.0)).clip(0.05, 0.99).to_numpy()
        return np.column_stack([1.0 - p, p])


def test_effective_recourse_search_denied_target_profile():
    rec_cfg = {
        "adaptive_steps": {"enabled": True},
        "weekly_optimizer": {"enabled": True, "only_denied": True},
        "denied_target": {
            "enabled": True,
            "activation_margin": 0.0,
            "topk_multiplier": 2.0,
            "min_topk": 12,
            "horizons": [3, 12],
            "strategies": ["balanced", "aggressive"],
            "strict_min_reliability": 0.8,
            "strict_min_worst_risk_margin": -0.01,
            "dice_total_cfs_multiplier": 2.0,
            "dice_max_actions_multiplier": 1.5,
        },
    }
    search, robust, dice = _effective_recourse_search(
        base_pd=0.52,
        tau=0.35,
        topk=8,
        horizons=[3, 6, 12],
        strategies=["conservative", "balanced", "aggressive"],
        robust_cfg={"min_reliability": 0.7, "min_worst_risk_margin": -0.05},
        dice_cfg={"total_cfs": 3, "max_actions": 4},
        rec_cfg=rec_cfg,
    )
    assert search["is_denied_target"] is True
    assert search["search_cfg"]["denied_mode"] is True
    assert search["search_cfg"]["weekly_optimizer"]["enabled"] is True
    assert search["topk"] >= 12
    assert search["horizons"] == [3, 12]
    assert search["strategies"] == ["balanced", "aggressive"]
    assert robust["min_reliability"] >= 0.8
    assert robust["min_worst_risk_margin"] >= -0.01
    assert dice["total_cfs"] >= 6
    assert dice["max_actions"] >= 6


def test_effective_recourse_search_adaptive_only_denied():
    rec_cfg = {
        "adaptive_steps": {"enabled": True, "only_denied": True},
        "weekly_optimizer": {"enabled": True, "only_denied": True},
        "denied_target": {"enabled": True, "activation_margin": 0.0},
    }
    search_ok, _, _ = _effective_recourse_search(
        base_pd=0.20,
        tau=0.35,
        topk=8,
        horizons=[3, 6, 12],
        strategies=["conservative", "balanced", "aggressive"],
        robust_cfg={},
        dice_cfg={},
        rec_cfg=rec_cfg,
    )
    assert search_ok["is_denied_target"] is False
    assert search_ok["search_cfg"]["adaptive_steps"]["enabled"] is False
    assert search_ok["search_cfg"]["weekly_optimizer"]["enabled"] is False

    search_denied, _, _ = _effective_recourse_search(
        base_pd=0.50,
        tau=0.35,
        topk=8,
        horizons=[3, 6, 12],
        strategies=["conservative", "balanced", "aggressive"],
        robust_cfg={},
        dice_cfg={},
        rec_cfg=rec_cfg,
    )
    assert search_denied["is_denied_target"] is True
    assert search_denied["search_cfg"]["adaptive_steps"]["enabled"] is True
    assert search_denied["search_cfg"]["weekly_optimizer"]["enabled"] is True


def test_group_advantage_penalties():
    scored = pd.DataFrame(
        {
            "g": ["A", "A", "B", "B", "C", "C"],
            "approve": [1, 1, 1, 0, 0, 0],
        }
    )
    penalties = build_group_advantage_penalties(scored, group_col="g", approval_col="approve", tolerance=0.0)
    assert penalties["A"] > penalties["B"] > penalties["C"] - 1e-12
    assert lookup_group_penalty("A", penalties) > 0.0
    assert lookup_group_penalty("missing", penalties) == 0.0


def test_estimate_prediction_ci_conformal_and_hybrid_bounds():
    low_c, high_c = estimate_prediction_ci(
        0.4,
        alpha=0.05,
        method="conformal",
        conformal_residual_quantile=0.05,
        conformal_min_width=0.01,
    )
    low_b, high_b = estimate_prediction_ci(
        0.4,
        alpha=0.05,
        method="bootstrap",
        b=200,
        sigma=0.02,
    )
    assert 0.0 <= low_c <= high_c <= 1.0
    assert 0.0 <= low_b <= high_b <= 1.0
    assert (high_c - low_c) >= 0.02


def test_generate_plan_record_repairs_conflicting_action_bundle():
    row = pd.Series(
        {
            "annual_inc": 55_000.0,
            "dti": 22.0,
            "revol_bal": 12_000.0,
            "tot_coll_amt": 2_500.0,
        }
    )
    plan = generate_plan_record(
        customer_id="c1",
        run_id="r1",
        row=row,
        model=_DummyModel(),
        calibrator=None,
        feature_cols=list(row.index),
        horizon_months=6,
        strategy="balanced",
        graph=None,
        cfg=PlanGenConfig(tau=0.35),
        candidate_features=["revol_bal", "tot_coll_amt"],
        topk=2,
        robust_cfg={"enabled": False},
        search_cfg={"min_abs_action_delta": 1e-6},
    )
    assert plan.constraint_status == "repaired"
    assert plan.actions
    assert all(action.action_key != "settlement_discount" for action in plan.actions)
    assert any(str(entry.get("reason_code", "")).startswith("conflict_with:") for entry in plan.constraint_trace)


def test_generate_plan_record_marks_approval_required_action_provisional():
    row = pd.Series(
        {
            "annual_inc": 50_000.0,
            "dti": 21.0,
            "total_rev_hi_lim": 6_000.0,
        }
    )
    plan = generate_plan_record(
        customer_id="c2",
        run_id="r2",
        row=row,
        model=_DummyModel(),
        calibrator=None,
        feature_cols=list(row.index),
        horizon_months=6,
        strategy="balanced",
        graph=None,
        cfg=PlanGenConfig(tau=0.35),
        candidate_features=["total_rev_hi_lim"],
        topk=1,
        robust_cfg={"enabled": False},
        search_cfg={"min_abs_action_delta": 1e-6},
    )
    assert plan.constraint_status == "provisional"
    assert len(plan.actions) == 1
    assert plan.actions[0].action_status == "provisional"
    assert "requires_institutional_approval" in plan.actions[0].diagnostic_flags
    assert plan.actions[0].action_execution_probability is None
    assert float(plan.actions[0].approval_dependent_probability or 0.0) > 0.0


def test_generate_plan_record_emits_execution_probability_contract():
    row = pd.Series(
        {
            "annual_inc": 68_000.0,
            "dti": 31.0,
            "revol_bal": 11_000.0,
            "revol_util": 58.0,
        }
    )
    plan = generate_plan_record(
        customer_id="c3",
        run_id="r3",
        row=row,
        model=_DummyModel(),
        calibrator=None,
        feature_cols=list(row.index),
        horizon_months=6,
        strategy="balanced",
        graph=None,
        cfg=PlanGenConfig(tau=0.35),
        candidate_features=["dti", "revol_bal"],
        topk=2,
        robust_cfg={"enabled": False},
        search_cfg={"min_abs_action_delta": 1e-6},
        base_pd=0.52,
    )
    assert float(plan.plan_execution_probability or 0.0) > 0.0
    assert float(plan.mean_action_execution_probability or 0.0) > 0.0
    assert float(plan.nominal_pd_improvement or 0.0) >= 0.0
    assert float(plan.expected_pd_improvement or 0.0) >= 0.0
    assert int(plan.executable_action_count) >= 1
    assert int(plan.executable_action_group_count) >= 1
    assert all(action.action_group_execution_probability is not None for action in plan.actions)
    assert all(action.action_execution_probability is not None for action in plan.actions)
