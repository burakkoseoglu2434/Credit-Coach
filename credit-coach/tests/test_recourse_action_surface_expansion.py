from __future__ import annotations

import json

from credit_coach.cli.run_recourse import _apply_recourse_gate_to_roadmap


def _roadmap(
    *,
    recourse_mode: str = "full",
    paths: list[dict],
) -> dict:
    return {
        "recourse_gate_config": {},
        "summary": {
            "recoverable_flag": True,
            "selection_outcome": "ok",
            "best_plan_id": "p1",
            "decision_status": "CONDITIONAL",
            "assisted_full_flag": 0,
            "recourse_mode": recourse_mode,
        },
        "paths": paths,
        "narrative": {
            "steps": [
                {
                    "action_key": paths[0]["action_keys"][0] if paths and paths[0].get("action_keys") else "fallback",
                    "primary_recommendation": paths[0]["customer_summary"] if paths and "customer_summary" in paths[0] else {"en": "fallback", "tr": "fallback"},
                }
            ]
        }
    }


def test_full_mode_surfaces_secondary_action_from_distinct_family_path() -> None:
    roadmap = _roadmap(
        paths=[
            {
                "path_rank": 1,
                "action_keys": ["adjust_requested_loan_amount"],
                "rankable_flag": True,
                "selected_path_flag": True,
                "path_type": "customer_only",
                "path_id": "p1",
                "customer_summary": {"en": "Lower requested amount", "tr": "Lower requested amount"},
            },
            {
                "path_rank": 2,
                "action_keys": ["debt_consolidation"],
                "action_owners": ["hybrid"],
                "rankable_flag": True,
                "selected_path_flag": False,
                "path_type": "hybrid",
                "path_id": "p2",
                "customer_summary": {"en": "Debt consolidation", "tr": "Debt consolidation"},
            },
        ]
    )

    out = _apply_recourse_gate_to_roadmap(roadmap)
    summary = out.get("summary", {}) or {}

    assert summary.get("selected_secondary_action_present") == 1
    assert summary.get("selected_secondary_action_key") == "debt_consolidation"
    assert summary.get("selected_secondary_action_family") == "debt_restructuring"
    assert summary.get("selected_action_count") == 2
    assert summary.get("selected_recommendation_text") == "Lower requested amount"
    assert summary.get("best_plan_id") == "p1"


def test_full_mode_single_path_surfaces_one_action() -> None:
    roadmap = _roadmap(
        paths=[
            {
                "path_rank": 1,
                "action_keys": ["adjust_requested_loan_amount"],
                "rankable_flag": True,
                "selected_path_flag": True,
                "path_type": "customer_only",
                "path_id": "p1",
                "customer_summary": {"en": "Lower requested amount", "tr": "Lower requested amount"},
            }
        ]
    )

    out = _apply_recourse_gate_to_roadmap(roadmap)
    summary = out.get("summary", {}) or {}

    assert summary.get("selected_secondary_action_present") == 0
    assert summary.get("selected_action_count") == 1
    assert summary.get("selected_recommendation_text") == "Lower requested amount"
    assert summary.get("best_plan_id") == "p1"


def test_full_mode_same_family_alternative_surfaces_one_action() -> None:
    roadmap = _roadmap(
        paths=[
            {
                "path_rank": 1,
                "action_keys": ["refinance"],
                "rankable_flag": True,
                "selected_path_flag": True,
                "path_type": "hybrid",
                "path_id": "p1",
                "customer_summary": {"en": "Refinance", "tr": "Refinance"},
            },
            {
                "path_rank": 2,
                "action_keys": ["debt_consolidation"],
                "rankable_flag": True,
                "selected_path_flag": False,
                "path_type": "hybrid",
                "path_id": "p2",
                "customer_summary": {"en": "Debt consolidation", "tr": "Debt consolidation"},
            },
        ]
    )

    out = _apply_recourse_gate_to_roadmap(roadmap)
    summary = out.get("summary", {}) or {}

    assert summary.get("selected_secondary_action_present") == 0
    assert summary.get("selected_action_count") == 1


def test_full_mode_excludes_institutional_secondary() -> None:
    roadmap = _roadmap(
        paths=[
            {
                "path_rank": 1,
                "action_keys": ["adjust_requested_loan_amount"],
                "rankable_flag": True,
                "selected_path_flag": True,
                "path_type": "customer_only",
                "path_id": "p1",
                "customer_summary": {"en": "Lower requested amount", "tr": "Lower requested amount"},
            },
            {
                "path_rank": 2,
                "action_keys": ["credit_limit_adjustment"],
                "action_owners": ["institution"],
                "rankable_flag": True,
                "selected_path_flag": False,
                "path_type": "institution_assisted",
                "path_id": "p2",
                "customer_summary": {"en": "Credit limit", "tr": "Credit limit"},
            },
            {
                "path_rank": 3,
                "action_keys": ["debt_consolidation"],
                "action_owners": ["hybrid"],
                "rankable_flag": True,
                "selected_path_flag": False,
                "path_type": "hybrid",
                "path_id": "p3",
                "customer_summary": {"en": "Debt consolidation", "tr": "Debt consolidation"},
            },
        ]
    )

    out = _apply_recourse_gate_to_roadmap(roadmap)
    summary = out.get("summary", {}) or {}

    assert summary.get("selected_secondary_action_present") == 1
    assert summary.get("selected_secondary_action_key") == "debt_consolidation"
    assert summary.get("selected_secondary_action_family") == "debt_restructuring"
    assert summary.get("selected_action_count") == 2


def test_full_mode_secondary_narrative_matches_path_summary() -> None:
    roadmap = _roadmap(
        paths=[
            {
                "path_rank": 1,
                "action_keys": ["adjust_requested_loan_amount"],
                "rankable_flag": True,
                "selected_path_flag": True,
                "path_type": "customer_only",
                "path_id": "p1",
                "customer_summary": {"en": "Lower requested amount", "tr": "Lower requested amount"},
            },
            {
                "path_rank": 2,
                "action_keys": ["debt_consolidation"],
                "action_owners": ["hybrid"],
                "rankable_flag": True,
                "selected_path_flag": False,
                "path_type": "hybrid",
                "path_id": "p2",
                "customer_summary": {"en": "Secondary narrative exactly", "tr": "Secondary narrative exactly tr"},
            },
        ]
    )

    out = _apply_recourse_gate_to_roadmap(roadmap)
    summary = out.get("summary", {}) or {}

    assert summary.get("selected_secondary_recommendation_text") == "Secondary narrative exactly"


def test_full_mode_missing_paths_key_surfaces_one_action() -> None:
    roadmap = _roadmap(paths=[])
    del roadmap["paths"]

    out = _apply_recourse_gate_to_roadmap(roadmap)
    summary = out.get("summary", {}) or {}

    assert summary.get("selected_secondary_action_present") == 0
    assert summary.get("selected_action_count") == 1

def test_full_mode_action_count_two_does_not_trip_drift_guard() -> None:
    roadmap = _roadmap(
        paths=[
            {
                "path_rank": 1,
                "action_keys": ["adjust_requested_loan_amount"],
                "rankable_flag": True,
                "selected_path_flag": True,
                "path_type": "customer_only",
                "path_id": "p1",
                "customer_summary": {"en": "Lower requested amount", "tr": "Lower requested amount"},
            },
            {
                "path_rank": 2,
                "action_keys": ["debt_consolidation"],
                "action_owners": ["hybrid"],
                "rankable_flag": True,
                "selected_path_flag": False,
                "path_type": "hybrid",
                "path_id": "p2",
                "customer_summary": {"en": "Debt consolidation", "tr": "Debt consolidation"},
            },
        ]
    )

    out = _apply_recourse_gate_to_roadmap(roadmap)
    summary = out.get("summary", {}) or {}

    assert summary.get("selected_action_count") == 2
    assert summary.get("selected_recommendation_source") == "selected_plan"
    assert summary.get("best_plan_id") == "p1"
