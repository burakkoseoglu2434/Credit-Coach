from __future__ import annotations

from credit_coach.recourse.feasibility import apply_target_feasibility, apply_target_feasibility_with_details


def test_apply_target_feasibility_caps_relative_and_absolute():
    profile = {
        "enabled": True,
        "defaults": {"max_relative_change": 0.5},
        "features": {
            "annual_inc": {
                "max_abs_increase_per_month": 2000.0,
                "max_abs_increase": 10000.0,
            }
        },
    }
    # Requested jump: 50k -> 200k (delta +150k)
    target = apply_target_feasibility(
        feature_name="annual_inc",
        current_value=50000.0,
        target_value=200000.0,
        horizon_months=6,
        profile=profile,
    )
    # Relative cap would allow +25k, abs cap allows +10k, monthly cap allows +12k.
    assert target == 60000.0


def test_apply_target_feasibility_freeze_rule():
    profile = {
        "enabled": True,
        "features": {
            "last_fico_range_low": {
                "freeze_if_current_below": 300.0,
                "max_abs_increase": 40.0,
            }
        },
    }
    target = apply_target_feasibility(
        feature_name="last_fico_range_low",
        current_value=0.0,
        target_value=500.0,
        horizon_months=6,
        profile=profile,
    )
    assert target == 0.0


def test_apply_target_feasibility_round_and_bounds():
    profile = {
        "enabled": True,
        "features": {
            "verification_status": {
                "round_to_int": True,
                "min_target": 0.0,
                "max_target": 2.0,
                "max_abs_increase": 1.0,
            }
        },
    }
    target = apply_target_feasibility(
        feature_name="verification_status",
        current_value=1.0,
        target_value=2.7,
        horizon_months=3,
        profile=profile,
    )
    assert target == 2.0


def test_apply_target_feasibility_segment_multiplier_relaxes_caps():
    profile = {
        "enabled": True,
        "features": {
            "dti": {
                "max_abs_decrease": 2.0,
            }
        },
    }
    no_segment = apply_target_feasibility(
        feature_name="dti",
        current_value=30.0,
        target_value=24.0,
        horizon_months=3,
        profile=profile,
    )
    with_segment = apply_target_feasibility(
        feature_name="dti",
        current_value=30.0,
        target_value=24.0,
        horizon_months=3,
        profile=profile,
        segment_context={
            "segment_caps_applied": True,
            "cap_multiplier": 1.5,
            "cap_multiplier_min": 1.0,
            "cap_multiplier_max": 2.0,
        },
    )
    # Without segment multiplier: max decrease 2 => 28.
    assert no_segment == 28.0
    # With multiplier 1.5: max decrease 3 => 27.
    assert with_segment == 27.0


def test_apply_target_feasibility_income_growth_cap():
    profile = {
        "enabled": True,
        "features": {
            "annual_inc": {
                "income_growth_cap": 0.30,
            }
        },
    }
    target = apply_target_feasibility(
        feature_name="annual_inc",
        current_value=50_000.0,
        target_value=90_000.0,
        horizon_months=6,
        profile=profile,
    )
    assert target == 65_000.0


def test_apply_target_feasibility_utilization_drop_ratio():
    profile = {
        "enabled": True,
        "features": {
            "revol_util": {
                "max_utilization_drop_ratio": 0.50,
            }
        },
    }
    target = apply_target_feasibility(
        feature_name="revol_util",
        current_value=80.0,
        target_value=10.0,
        horizon_months=1,
        profile=profile,
    )
    assert target == 40.0


def test_apply_target_feasibility_financial_capacity_ratio():
    profile = {
        "enabled": True,
        "features": {
            "revol_bal": {
                "financial_capacity_ratio": 0.25,
            }
        },
    }
    target = apply_target_feasibility_with_details(
        feature_name="revol_bal",
        current_value=12_000.0,
        target_value=4_000.0,
        horizon_months=1,
        profile=profile,
        action_class="structural",
        action_context={"annual_inc": 48_000.0},
    )
    assert target["target_value"] == 11_000.0
    assert target["status"] == "rejected"
    assert "financial_capacity_ratio" in target["reason_codes"]


def test_apply_target_feasibility_rejects_structural_semantic_loss():
    profile = {
        "enabled": True,
        "features": {
            "int_rate": {
                "max_abs_decrease": 1.0,
                "min_structural_semantic_ratio": 0.50,
            }
        },
    }
    detail = apply_target_feasibility_with_details(
        feature_name="int_rate",
        current_value=20.0,
        target_value=10.0,
        horizon_months=6,
        profile=profile,
        action_class="structural",
    )
    assert detail["target_value"] == 19.0
    assert detail["status"] == "rejected"
    assert "semantic_loss_after_clip" in detail["reason_codes"]
