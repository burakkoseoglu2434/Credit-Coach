from __future__ import annotations

from credit_coach.recourse.region_targets import get_target_pd


def test_target_pd_ordering_by_strategy():
    tau = 0.35
    conservative = get_target_pd("conservative", tau)
    balanced = get_target_pd("balanced", tau)
    aggressive = get_target_pd("aggressive", tau)

    assert aggressive <= balanced <= conservative


def test_target_pd_lower_bound():
    tau = 0.05
    assert get_target_pd("aggressive", tau) >= 0.01
