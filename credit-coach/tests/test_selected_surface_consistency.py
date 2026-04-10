from __future__ import annotations

from credit_coach.cli.run_recourse import _apply_recourse_gate_to_roadmap, _build_selected_surface_projection


def test_selected_surface_projection_keeps_technical_status_separate_from_consumer_decision() -> None:
    roadmap = {
        "customer_id": "cust-selected",
        "best_plan_id": "plan-1",
        "best_status": "REJECTED",
        "summary": {
            "decision_status": "CONDITIONAL",
            "best_plan_id": "plan-1",
            "best_action_count": 2,
            "selection_outcome": "selected_valid_winner",
            "selection_stage": "preferred_valid",
        },
        "narrative": {
            "steps": [
                {
                    "step_id": "step-1",
                    "action_key": "limit_credit_usage",
                    "primary_recommendation": {
                        "tr": "Kart kullanim oranini %63.2'den %45 altina indir.",
                        "en": "Reduce credit utilization from %63.2 to below %45.",
                    },
                    "institution_condition": {
                        "tr": "Profilin guclenmesi icin toplam limit tarafinda yaklasik 640 birim ek kapasite gerekiyor.",
                        "en": "The profile needs about 640 units of additional total credit capacity to strengthen.",
                    },
                }
            ]
        },
    }

    projected = _build_selected_surface_projection(roadmap)
    summary = projected["summary"]

    assert summary["selected_decision_status"] == "CONDITIONAL"
    assert summary["selected_plan_status_internal"] == "REJECTED"
    assert summary["selected_recommendation_text"] == "Reduce credit utilization from %63.2 to below %45."
    assert summary["selected_institution_condition"] == (
        "The profile needs about 640 units of additional total credit capacity to strengthen."
    )
    assert summary["selected_recommendation_source"] == "selected_plan"
    assert summary["selected_action_count"] == 2
    assert summary["selected_recommendation_projection_version"] == "v2.2_phase_47"


def test_selected_surface_projection_promotes_no_valid_winner_to_real_empty_state() -> None:
    roadmap = {
        "customer_id": "cust-empty",
        "best_plan_id": None,
        "best_status": "",
        "summary": {
            "decision_status": "REJECTED",
            "best_plan_id": None,
            "best_action_count": 0,
            "selection_outcome": "no_valid_winner",
            "selection_stage": "no_valid_winner",
        },
        "narrative": {"steps": []},
    }

    projected = _build_selected_surface_projection(roadmap)
    summary = projected["summary"]

    assert summary["selected_decision_status"] == "REJECTED"
    assert summary["selected_plan_status_internal"] is None
    assert summary["selected_recommendation_text"] is None
    assert summary["selected_institution_condition"] is None
    assert summary["selected_recommendation_source"] == "empty_state"
    assert summary["selected_action_count"] == 0
    assert summary["selected_recommendation_projection_version"] == "v2.2_phase_47"


def test_selected_surface_projection_reuses_empty_state_when_limited_mode_suppresses_promotion() -> None:
    roadmap = {
        "customer_id": "cust-gated",
        "best_plan_id": "plan-1",
        "base_pd": 0.42,
        "tau": 0.35,
        "summary": {
            "decision_status": "CONDITIONAL",
            "best_plan_id": "plan-1",
            "best_action_count": 1,
            "selection_outcome": "selected_valid_winner",
            "selection_stage": "preferred_valid",
            "recoverable_flag": False,
            "recoverability_bucket": "mid_risk",
            "movement_score": 88.0,
            "threshold_reach_probability": 0.77,
            "threshold_reach_priority_flag": 1,
            "movement_rank_reason_codes": ["THRESHOLD_REACH_PRIORITY"],
            "selected_path_movement_strength": "strong",
        },
        "narrative": {
            "executive_summary": {
                "recommended_path": {
                    "label": {"tr": "Kontrollu toparlanma yolu", "en": "Controlled recovery path"},
                    "description": {"tr": "dummy", "en": "dummy"},
                }
            },
            "steps": [
                {
                    "primary_recommendation": {
                        "en": "Reduce credit utilization from %63.2 to below %45.",
                    }
                }
            ]
        },
        "phases": [{"phase_id": "phase-1", "steps": [{"action_key": "limit_credit_usage"}]}],
        "checkpoints": [{"checkpoint_id": "checkpoint_week_4", "week": 4, "predicted_pd": 0.31, "gate_pass_estimate": 1}],
    }

    projected = _apply_recourse_gate_to_roadmap(roadmap)
    summary = projected["summary"]
    narrative = projected.get("narrative", {})

    assert summary["selection_outcome"] == "selected_valid_winner"
    assert summary["recourse_mode"] == "limited"
    assert summary["recommendation_mode"] == "informational"
    assert summary["narrative_type"] == "informational"
    assert summary["informational_subtype"] == "not_currently_actionable"
    assert summary["narrative_contract_version"] == "phase_66_v1"
    assert summary["selected_recommendation_text"] is None
    assert summary["selected_recommendation_source"] == "empty_state"
    assert summary["selected_action_count"] == 0
    assert summary["selected_recommendation_projection_version"] == "v2.2_phase_47"
    assert summary["movement_score"] == 0.0
    assert summary["threshold_reach_probability"] == 0.0
    assert summary["threshold_reach_priority_flag"] == 0
    assert summary["movement_rank_reason_codes"] == []
    assert summary["selected_path_movement_strength"] == ""
    assert isinstance(narrative, dict)
    assert narrative.get("steps", []) == []
    executive = dict(narrative.get("executive_summary", {}) or {})
    recommended = dict(executive.get("recommended_path", {}) or {})
    label = dict(recommended.get("label", {}) or {})
    assert label.get("en") == "Not actionable yet"
