from __future__ import annotations

import pandas as pd

from credit_coach.cli.run_recourse import _effective_recourse_search
from credit_coach.evaluation.fairness import build_group_advantage_penalties, lookup_group_penalty
from credit_coach.safety.statistical import estimate_prediction_ci


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
