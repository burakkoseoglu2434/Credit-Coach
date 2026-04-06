from __future__ import annotations

import json
from types import SimpleNamespace

from credit_coach.cli.run_recourse import (
    _attach_recoverability_signal_to_roadmap,
    _sync_metrics_summary_with_roadmap_summary,
)
from credit_coach.evaluation import recoverability as recv


def _build_signal(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "base_pd": 0.41,
        "tau": 0.35,
        "has_valid_path_flag": True,
        "has_rankable_path_flag": True,
        "best_possible_pd_improvement": 0.08,
        "selection_outcome": "",
        "expected_readiness": "",
        "credit_readiness_stage": "",
        "offer_maturity": "",
        "offer_plan": False,
    }
    payload.update(overrides)
    return recv.build_recoverability_signal(**payload)


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
    assert near["recoverability_signal_reason_codes"] == [
        "LOW_APPROVAL_GAP",
        "NO_VALID_PATH",
        "THRESHOLD_NOT_REACHABLE",
        "NO_PATH",
        "HARD_STRUCTURAL_BLOCK",
    ]


def test_classifier_marks_near_threshold_rankable_reachable_case_recoverable() -> None:
    signal = _build_signal(base_pd=0.42, best_possible_pd_improvement=0.08)

    assert signal["recoverable_flag"] is True
    assert signal["recoverability_classifier_version"] == recv.RECOVERABILITY_CLASSIFIER_VERSION
    assert signal["threshold_reach_possible"] is True
    assert signal["structural_blocker_flag"] == 0
    assert signal["recoverable_reason_codes"] == [
        "WITHIN_RECOVERABLE_BAND",
        "HAS_VALID_PATH",
        "HAS_RANKABLE_PATH",
        "THRESHOLD_REACHABLE",
        "NO_ACTIVE_CLASSIFIER_BLOCKERS",
        "RECOVERABLE",
    ]
    assert signal["recoverability_signal_reason_codes"] == [
        "LOW_APPROVAL_GAP",
        "HAS_VALID_PATH",
        "HAS_RANKABLE_PATH",
        "THRESHOLD_REACHABLE",
    ]


def test_classifier_excludes_mid_risk_case_even_when_threshold_is_reachable() -> None:
    signal = _build_signal(
        base_pd=0.55,
        best_possible_pd_improvement=0.25,
    )

    assert signal["recoverability_bucket"] == "mid_risk"
    assert signal["threshold_reach_possible"] is True
    assert signal["recoverable_flag"] is False
    assert signal["recoverable_reason_codes"] == [
        "OUTSIDE_RECOVERABLE_BAND",
        "HAS_VALID_PATH",
        "HAS_RANKABLE_PATH",
        "THRESHOLD_REACHABLE",
        "NO_ACTIVE_CLASSIFIER_BLOCKERS",
        "NOT_RECOVERABLE",
    ]
    assert "MID_APPROVAL_GAP" in signal["recoverability_signal_reason_codes"]


def test_classifier_fails_closed_on_hard_blockers() -> None:
    signal = _build_signal(
        has_valid_path_flag=False,
        has_rankable_path_flag=False,
        selection_outcome="no_valid_winner",
        best_possible_pd_improvement=0.08,
    )

    assert signal["recoverable_flag"] is False
    assert signal["hard_structural_blocker_flag"] == 1
    assert signal["soft_structural_blocker_flag"] == 0
    assert signal["hard_structural_blockers"] == ["NO_VALID_WINNER", "NO_PATH"]
    assert signal["recoverable_reason_codes"] == [
        "WITHIN_RECOVERABLE_BAND",
        "NO_VALID_PATH",
        "NO_RANKABLE_PATH",
        "THRESHOLD_REACHABLE",
        "HARD_STRUCTURAL_BLOCK",
        "NO_VALID_WINNER",
        "NO_PATH",
        "NOT_RECOVERABLE",
    ]


def test_classifier_fails_closed_on_soft_blockers() -> None:
    signal = _build_signal(
        best_possible_pd_improvement=0.02,
        expected_readiness="week_12",
        offer_maturity="provisional",
        offer_plan=True,
    )

    assert signal["recoverable_flag"] is False
    assert signal["threshold_reach_possible"] is False
    assert signal["hard_structural_blocker_flag"] == 0
    assert signal["soft_structural_blocker_flag"] == 1
    assert signal["soft_structural_blockers"] == [
        "BLOCKED_BY_TIME",
        "BLOCKED_BY_OFFER",
        "LOW_IMPACT",
    ]
    assert signal["recoverable_reason_codes"] == [
        "WITHIN_RECOVERABLE_BAND",
        "HAS_VALID_PATH",
        "HAS_RANKABLE_PATH",
        "THRESHOLD_NOT_REACHABLE",
        "SOFT_STRUCTURAL_BLOCK",
        "BLOCKED_BY_TIME",
        "BLOCKED_BY_OFFER",
        "LOW_IMPACT",
        "NOT_RECOVERABLE",
    ]


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
    assert signal["recoverable_flag"] is False
    assert signal["hard_structural_blocker_flag"] == 0
    assert signal["soft_structural_blocker_flag"] == 0
    assert "STRUCTURAL_LIMIT" not in signal["recoverability_signal_reason_codes"]
    assert signal["recoverable_reason_codes"] == [
        "OUTSIDE_RECOVERABLE_BAND",
        "NO_VALID_PATH",
        "NO_RANKABLE_PATH",
        "THRESHOLD_REACHABLE",
        "NO_ACTIVE_CLASSIFIER_BLOCKERS",
        "NOT_RECOVERABLE",
    ]


def test_best_possible_pd_improvement_uses_lowest_predicted_pd() -> None:
    improvement = recv.best_possible_pd_improvement_from_predictions(
        base_pd=0.48,
        predicted_pds=[0.44, 0.39, 0.41],
    )

    assert improvement == 0.09


def test_classifier_decision_does_not_depend_on_recoverability_score() -> None:
    signal = _build_signal(base_pd=0.42, best_possible_pd_improvement=0.08)
    high_score = recv.build_recoverability_classifier({**signal, "recoverability_score": 0.99})
    low_score = recv.build_recoverability_classifier({**signal, "recoverability_score": 0.01})

    assert high_score == low_score == {
        "recoverable_flag": True,
        "recoverable_reason_codes": [
            "WITHIN_RECOVERABLE_BAND",
            "HAS_VALID_PATH",
            "HAS_RANKABLE_PATH",
            "THRESHOLD_REACHABLE",
            "NO_ACTIVE_CLASSIFIER_BLOCKERS",
            "RECOVERABLE",
        ],
        "recoverability_classifier_version": recv.RECOVERABILITY_CLASSIFIER_VERSION,
    }


def test_runtime_summary_and_metrics_sync_emit_shared_classifier_truth() -> None:
    roadmap = {
        "summary": {
            "selection_outcome": "selected_valid_winner",
            "expected_readiness": "week_4",
            "credit_readiness_stage": "week_4",
            "offer_maturity": "none",
            "offer_plan": 0,
        }
    }
    path_records = [SimpleNamespace(representative_plan_id="plan-1", rankable_flag=True)]
    plan_lookup = {"plan-1": SimpleNamespace(predicted_pd=0.34)}

    updated = _attach_recoverability_signal_to_roadmap(
        roadmap,
        base_pd=0.42,
        tau=0.35,
        segment_context={"recoverability_near_upper": 0.10, "recoverability_mid_upper": 0.25},
        path_records=path_records,
        plan_lookup=plan_lookup,
    )
    summary = updated["summary"]
    signal = recv.build_recoverability_signal(
        base_pd=0.42,
        tau=0.35,
        thresholds={"near_upper": 0.10, "mid_upper": 0.25},
        has_valid_path_flag=True,
        has_rankable_path_flag=True,
        best_possible_pd_improvement=0.08,
        selection_outcome="selected_valid_winner",
        expected_readiness="week_4",
        credit_readiness_stage="week_4",
        offer_maturity="none",
        offer_plan=False,
    )

    assert summary["recoverable_flag"] is True
    assert summary["recoverability_classifier_version"] == recv.RECOVERABILITY_CLASSIFIER_VERSION
    assert summary["recoverable_reason_codes"] == signal["recoverable_reason_codes"]
    assert json.loads(summary["recoverability_signal_reason_codes_json"]) == signal["recoverability_signal_reason_codes"]
    assert json.loads(summary["recoverable_reason_codes_json"]) == signal["recoverable_reason_codes"]

    metrics = _sync_metrics_summary_with_roadmap_summary({}, roadmap=updated)

    assert metrics["recoverable_flag"] == 1
    assert metrics["recoverability_classifier_version"] == recv.RECOVERABILITY_CLASSIFIER_VERSION
    assert metrics["recoverability_signal_reason_codes"] == signal["recoverability_signal_reason_codes"]
    assert metrics["recoverable_reason_codes"] == signal["recoverable_reason_codes"]
    assert json.loads(metrics["recoverability_signal_reason_codes_json"]) == signal["recoverability_signal_reason_codes"]
    assert json.loads(metrics["recoverable_reason_codes_json"]) == signal["recoverable_reason_codes"]
