from __future__ import annotations

import json

from credit_coach.cli.run_recourse import _apply_recourse_gate_to_roadmap


def _roadmap(
    *,
    selected_path_type: str,
    phases: list[dict],
    narrative_steps: list[dict],
    recourse_gate_config: dict,
    threshold_reach_probability: float = 0.30,
    approval_gap: float = 0.20,
    best_possible_pd_improvement: float = 0.05,
) -> dict:
    return {
        "recourse_gate_config": recourse_gate_config,
        "summary": {
            "recoverable_flag": False,
            "best_plan_id": "p1",
            "selection_outcome": "ok",
            "decision_status": "REJECTED",
            "selected_path_type": selected_path_type,
            "movement_score": 0.81,
            "threshold_reach_probability": threshold_reach_probability,
            "approval_gap": approval_gap,
            "best_possible_pd_improvement": best_possible_pd_improvement,
        },
        "narrative": {"steps": narrative_steps},
        "phases": phases,
    }


def test_assisted_full_routing_and_pruning_surfaces_exactly_one_allowlisted_step() -> None:
    roadmap = _roadmap(
        selected_path_type="customer_only",
        recourse_gate_config={
            "assisted_full": {
                "enabled": True,
                "threshold_prob_min": 0.20,
                "gap_closure_min": 1e9,
                "gap_divide_epsilon": 1e-6,
                "allowlisted_action_keys": [
                    "adjust_requested_loan_amount",
                    "limit_credit_usage",
                    "reduce_spending",
                ],
                "action_preference_order": [
                    "adjust_requested_loan_amount",
                    "limit_credit_usage",
                    "reduce_spending",
                ],
            }
        },
        phases=[
            {
                "phase_id": "phase_1",
                "steps": [
                    {"action_key": "reduce_spending", "requires_institutional_approval": 0, "requires_acceptance": 0},
                    {
                        "action_key": "adjust_requested_loan_amount",
                        "requires_institutional_approval": 0,
                        "requires_acceptance": 0,
                    },
                ],
            }
        ],
        narrative_steps=[
            {
                "action_key": "reduce_spending",
                "primary_recommendation": {"en": "Reduce spending", "tr": "Reduce spending"},
                "requires_institutional_approval": False,
                "requires_acceptance": False,
            },
            {
                "action_key": "adjust_requested_loan_amount",
                "primary_recommendation": {"en": "Lower requested amount", "tr": "Lower requested amount"},
                "requires_institutional_approval": False,
                "requires_acceptance": False,
            },
        ],
    )

    out = _apply_recourse_gate_to_roadmap(roadmap)
    summary = out.get("summary", {}) or {}

    assert summary.get("recourse_mode") == "assisted_full"
    assert summary.get("recommendation_mode") == "actionable"
    assert int(summary.get("assisted_full_flag", 0)) == 1
    assert summary.get("selected_recommendation_source") == "selected_plan"
    assert int(summary.get("selected_action_count", 0)) == 1

    assert len(out.get("phases", [])) == 1
    assert len(out["phases"][0].get("steps", [])) == 1
    assert out["phases"][0]["steps"][0].get("action_key") == "adjust_requested_loan_amount"

    assert len(out.get("narrative", {}).get("steps", [])) == 1
    assert out["narrative"]["steps"][0].get("action_key") == "adjust_requested_loan_amount"

    assert json.loads(summary.get("assisted_full_reason_codes_json", "[]")) == [
        "assisted_full:prob_ok:1",
        "assisted_full:gap_ok:0",
    ]
    assert json.loads(summary.get("assisted_full_thresholds_json", "{}")) == {
        "enabled": True,
        "threshold_prob_min": 0.2,
        "gap_closure_min": 1000000000.0,
        "gap_divide_epsilon": 1e-6,
    }


def test_assisted_full_falls_back_when_selected_path_is_not_customer_only() -> None:
    out = _apply_recourse_gate_to_roadmap(
        _roadmap(
            selected_path_type="hybrid",
            recourse_gate_config={
                "assisted_full": {
                    "enabled": True,
                    "threshold_prob_min": 0.20,
                    "gap_closure_min": 1e9,
                    "gap_divide_epsilon": 1e-6,
                }
            },
            phases=[
                {
                    "phase_id": "phase_1",
                    "steps": [
                        {
                            "action_key": "adjust_requested_loan_amount",
                            "requires_institutional_approval": 0,
                            "requires_acceptance": 0,
                        }
                    ],
                }
            ],
            narrative_steps=[
                {
                    "action_key": "adjust_requested_loan_amount",
                    "primary_recommendation": {"en": "Lower requested amount", "tr": "Lower requested amount"},
                    "requires_institutional_approval": False,
                    "requires_acceptance": False,
                }
            ],
        )
    )
    summary = out.get("summary", {}) or {}

    assert summary.get("recourse_mode") == "limited"
    assert int(summary.get("assisted_full_flag", 0)) == 0
    assert out.get("phases", []) == []
    assert out.get("narrative", {}).get("steps", []) == []

    assert json.loads(summary.get("assisted_full_reason_codes_json", "[]")) == [
        "assisted_full:prob_ok:1",
        "assisted_full:gap_ok:0",
        "assisted_full:fallback:path_type:hybrid",
    ]


def test_assisted_full_falls_back_when_no_allowlisted_step_is_available() -> None:
    out = _apply_recourse_gate_to_roadmap(
        _roadmap(
            selected_path_type="customer_only",
            recourse_gate_config={
                "assisted_full": {
                    "enabled": True,
                    "threshold_prob_min": 0.20,
                    "gap_closure_min": 1e9,
                    "gap_divide_epsilon": 1e-6,
                }
            },
            phases=[
                {
                    "phase_id": "phase_1",
                    "steps": [
                        {"action_key": "refinance", "requires_institutional_approval": 0, "requires_acceptance": 0}
                    ],
                }
            ],
            narrative_steps=[
                {
                    "action_key": "refinance",
                    "primary_recommendation": {"en": "Refinance", "tr": "Refinance"},
                    "requires_institutional_approval": False,
                    "requires_acceptance": False,
                }
            ],
        )
    )
    summary = out.get("summary", {}) or {}

    assert summary.get("recourse_mode") == "limited"
    assert int(summary.get("assisted_full_flag", 0)) == 0
    assert out.get("phases", []) == []
    assert out.get("narrative", {}).get("steps", []) == []

    assert json.loads(summary.get("assisted_full_reason_codes_json", "[]")) == [
        "assisted_full:prob_ok:1",
        "assisted_full:gap_ok:0",
        "assisted_full:fallback:no_allowlisted_step",
    ]


def test_assisted_full_not_eligible_remains_limited() -> None:
    out = _apply_recourse_gate_to_roadmap(
        _roadmap(
            selected_path_type="customer_only",
            recourse_gate_config={
                "assisted_full": {
                    "enabled": True,
                    "threshold_prob_min": 0.90,
                    "gap_closure_min": 100.0,
                    "gap_divide_epsilon": 1e-6,
                }
            },
            phases=[
                {
                    "phase_id": "phase_1",
                    "steps": [
                        {
                            "action_key": "adjust_requested_loan_amount",
                            "requires_institutional_approval": 0,
                            "requires_acceptance": 0,
                        }
                    ],
                }
            ],
            narrative_steps=[
                {
                    "action_key": "adjust_requested_loan_amount",
                    "primary_recommendation": {"en": "Lower requested amount", "tr": "Lower requested amount"},
                    "requires_institutional_approval": False,
                    "requires_acceptance": False,
                }
            ],
        )
    )
    summary = out.get("summary", {}) or {}

    assert summary.get("recourse_mode") == "limited"
    assert int(summary.get("assisted_full_flag", 0)) == 0
    assert out.get("phases", []) == []
    assert out.get("narrative", {}).get("steps", []) == []

    assert json.loads(summary.get("assisted_full_reason_codes_json", "[]")) == [
        "assisted_full:prob_ok:0",
        "assisted_full:gap_ok:0",
    ]
