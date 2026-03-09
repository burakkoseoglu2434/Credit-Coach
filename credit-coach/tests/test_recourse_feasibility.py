from __future__ import annotations

from credit_coach.recourse.feasibility import apply_target_feasibility


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
