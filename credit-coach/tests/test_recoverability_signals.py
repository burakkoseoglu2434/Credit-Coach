from __future__ import annotations

from credit_coach.evaluation import recoverability as recv


def test_resolve_recoverability_thresholds_uses_shipped_defaults() -> None:
    thresholds = recv.resolve_recoverability_thresholds()

    assert thresholds == {"near_upper": 0.1, "mid_upper": 0.25}


def test_gap_bucket_and_score_follow_absolute_phase_61_contract() -> None:
    near = recv.build_recoverability_signal(base_pd=0.40, tau=0.35)
    mid = recv.build_recoverability_signal(base_pd=0.55, tau=0.35)
    high = recv.build_recoverability_signal(base_pd=0.70, tau=0.35)

    assert near["approval_gap"] == 0.05
    assert near["normalized_gap"] == 0.2
    assert near["risk_band"] == "near"
    assert near["recoverability_bucket"] == "near_threshold"
    assert near["recoverability_score"] == 0.8

    assert mid["approval_gap"] == 0.2
    assert mid["risk_band"] == "mid"
    assert mid["recoverability_bucket"] == "mid_risk"
    assert mid["recoverability_score"] == 0.2

    assert high["approval_gap"] == 0.35
    assert high["normalized_gap"] == 1.0
    assert high["risk_band"] == "high"
    assert high["recoverability_bucket"] == "structural_limited"
    assert high["recoverability_score"] == 0.0


def test_threshold_reachability_uses_best_possible_improvement_only() -> None:
    signal = recv.build_recoverability_signal(
        base_pd=0.42,
        tau=0.35,
        has_valid_path_flag=True,
        has_rankable_path_flag=True,
        best_possible_pd_improvement=0.08,
    )

    assert signal["threshold_reach_possible"] is True
    assert signal["structural_blocker_flag"] == 0
    assert "HAS_VALID_PATH" in signal["recoverable_reason_codes"]
    assert "HAS_RANKABLE_PATH" in signal["recoverable_reason_codes"]
    assert "THRESHOLD_REACHABLE" in signal["recoverable_reason_codes"]


def test_hard_structural_blockers_are_separated_from_soft_blockers() -> None:
    signal = recv.build_recoverability_signal(
        base_pd=0.70,
        tau=0.35,
        has_valid_path_flag=False,
        has_rankable_path_flag=False,
        best_possible_pd_improvement=0.0,
        selection_outcome="no_valid_winner",
    )

    assert signal["hard_structural_blocker_flag"] == 1
    assert signal["soft_structural_blocker_flag"] == 0
    assert signal["structural_blocker_flag"] == 1
    assert signal["hard_structural_blockers"] == [
        "NO_VALID_WINNER",
        "NO_PATH",
        "HIGH_RISK_DISTANCE",
    ]
    assert "HARD_STRUCTURAL_BLOCK" in signal["recoverable_reason_codes"]
    assert "SOFT_STRUCTURAL_BLOCK" not in signal["recoverable_reason_codes"]


def test_soft_blockers_capture_time_offer_and_low_impact_without_hard_block() -> None:
    signal = recv.build_recoverability_signal(
        base_pd=0.41,
        tau=0.35,
        has_valid_path_flag=True,
        has_rankable_path_flag=True,
        best_possible_pd_improvement=0.02,
        expected_readiness="week_12",
        offer_maturity="provisional",
        offer_plan=True,
    )

    assert signal["threshold_reach_possible"] is False
    assert signal["hard_structural_blocker_flag"] == 0
    assert signal["soft_structural_blocker_flag"] == 1
    assert signal["soft_structural_blockers"] == [
        "BLOCKED_BY_TIME",
        "BLOCKED_BY_OFFER",
        "LOW_IMPACT",
    ]
    assert "SOFT_STRUCTURAL_BLOCK" in signal["recoverable_reason_codes"]


def test_non_denied_rows_do_not_get_fake_structural_interpretation() -> None:
    signal = recv.build_recoverability_signal(
        base_pd=0.30,
        tau=0.35,
        has_valid_path_flag=False,
        has_rankable_path_flag=False,
        selection_outcome="no_valid_winner",
    )

    assert signal["approval_gap"] == 0.0
    assert signal["threshold_reach_possible"] is True
    assert signal["hard_structural_blocker_flag"] == 0
    assert signal["soft_structural_blocker_flag"] == 0
    assert "STRUCTURAL_LIMIT" not in signal["recoverable_reason_codes"]


def test_best_possible_pd_improvement_uses_lowest_predicted_pd() -> None:
    improvement = recv.best_possible_pd_improvement_from_predictions(
        base_pd=0.48,
        predicted_pds=[0.44, 0.39, 0.41],
    )

    assert improvement == 0.09
