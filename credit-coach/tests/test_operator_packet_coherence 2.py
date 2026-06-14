from __future__ import annotations

from credit_coach.ops.operator_review import build_operator_review_packet, render_operator_review_packet_markdown


def _base_roadmap() -> dict:
    return {
        "customer_id": "cust-packet",
        "best_plan_id": "plan-1",
        "summary": {
            "decision_id": "decision-cust-packet",
            "decision_policy_version": "v2.2_phase_47",
            "decision_status": "CONDITIONAL",
            "selected_decision_status": "CONDITIONAL",
            "decision_status_internal": "CONDITIONAL",
            "selected_plan_status_internal": "CONDITIONAL",
            "decision_reason_summary": "Execution strength is not strong enough yet.",
            "decision_reason_primary": "LOW_EXECUTION",
            "decision_reason_drivers": [
                {
                    "driver_key": "realization_anchor",
                    "current_value": 0.38,
                    "target_value": 0.50,
                    "unit": "probability",
                    "source_field": "realization_anchor",
                    "comparison": "gte",
                }
            ],
            "decision_confidence": 0.41,
            "expected_readiness": "week_12",
            "upgrade_condition": "realization_anchor 0.38 -> 0.50",
            "conditional_type": "EXECUTION_GATED",
            "offer_maturity": "none",
            "offer_plan": 0,
            "offer_acceptance_probability": 0.0,
            "selected_recommendation_text": "Reduce monthly debt pressure by about 600 units.",
            "selected_recommendation_text_localized": {
                "tr": "Aylik borc baskisini yaklasik 600 birim azalt.",
                "en": "Reduce monthly debt pressure by about 600 units.",
            },
            "selected_institution_condition": "",
            "selected_institution_condition_localized": None,
            "selected_recommendation_source": "selected_plan",
            "selected_action_count": 2,
            "selected_recommendation_projection_version": "v2.2_phase_47",
            "selection_outcome": "selected_valid_winner",
            "selection_stage": "preferred_valid",
            "movement_score": 0.81,
            "threshold_reach_probability": 0.69,
            "threshold_reach_priority_flag": 1,
            "movement_rank_reason_codes": [
                "THRESHOLD_REACH_PRIORITY",
                "REALISTIC_MOVEMENT_ADVANTAGE",
            ],
            "selected_path_movement_strength": "moderate",
            "recourse_mode": "full",
            "recommendation_mode": "actionable",
            "recoverable_flag": True,
            "narrative_type": "actionable",
            "informational_subtype": "",
            "narrative_contract_version": "phase_66_v1",
            "approval_gap": 0.05,
            "recoverability_bucket": "near_threshold",
        },
        "contract_health": {"raw_contract_pass": 1, "parity_pass": 1},
        "narrative": {
            "steps": [
                {
                    "step_id": "reduce_spending:phase_1",
                    "action_key": "reduce_spending",
                    "primary_recommendation": {
                        "tr": "Aylik borc baskisini yaklasik 600 birim azalt.",
                        "en": "Reduce monthly debt pressure by about 600 units.",
                    },
                    "action_summary": {
                        "tr": "Harcama baskisini azalt.",
                        "en": "Reduce spending pressure.",
                    },
                    "action_timing_hint": {
                        "tr": "Onumuzdeki 1 ay icinde tamamla.",
                        "en": "Complete within the next 1 months.",
                    },
                    "what_happens_if_not_done": {
                        "tr": "Aylik baski yuksek kalir.",
                        "en": "Monthly pressure stays elevated.",
                    },
                }
            ]
        },
    }


def test_conditional_packet_keeps_selected_projection_and_driver_blocker() -> None:
    packet = build_operator_review_packet(_base_roadmap())

    assert packet.short_view.decision_status == "CONDITIONAL"
    assert packet.short_view.recourse_mode == "full"
    assert packet.short_view.recommendation_mode == "actionable"
    assert packet.short_view.recoverable_flag is True
    assert packet.short_view.narrative_type == "actionable"
    assert packet.short_view.narrative_contract_version == "phase_66_v1"
    assert len(packet.short_view.top_blockers) == 1
    assert len(packet.short_view.next_best_actions) == 1
    assert packet.technical_appendix.blocker_render_source == "driver"
    assert packet.technical_appendix.action_render_source == "selected_projection"
    assert packet.technical_appendix.readiness_render_mode == "conditional_time_gate"
    assert packet.short_view.next_best_actions[0].blocker_codes == ["driver:realization_anchor"]
    assert packet.short_view.upgrade_condition == "realization_anchor 0.38 -> 0.50"


def test_approved_packet_suppresses_blockers_actions_and_upgrade() -> None:
    roadmap = _base_roadmap()
    roadmap["summary"].update(
        {
            "decision_status": "APPROVED",
            "selected_decision_status": "APPROVED",
            "decision_status_internal": "APPROVED",
            "selected_plan_status_internal": "APPROVED",
            "decision_reason_primary": "LOW_EXECUTION",
            "decision_reason_drivers": [],
            "expected_readiness": "now",
            "recommendation_sanity_flag": 1,
        }
    )

    packet = build_operator_review_packet(roadmap)

    assert packet.short_view.decision_status == "APPROVED"
    assert packet.short_view.top_blockers == []
    assert packet.short_view.next_best_actions == []
    assert packet.short_view.upgrade_condition is None
    assert packet.short_view.recommendation_sanity_flag is True
    assert packet.technical_appendix.blocker_render_source == "suppressed"
    assert packet.technical_appendix.action_render_source == "suppressed"
    assert packet.technical_appendix.readiness_render_mode == "approved_info"
    assert packet.technical_appendix.fallback_blocker_suppressed is True
    assert "approved_fallback_blocker_suppressed" in packet.technical_appendix.packet_coherence_codes


def test_rejected_packet_without_selected_recommendation_suppresses_actions() -> None:
    roadmap = _base_roadmap()
    roadmap["summary"].update(
        {
            "decision_status": "REJECTED",
            "selected_decision_status": "REJECTED",
            "decision_status_internal": "REJECTED",
            "selected_plan_status_internal": "REJECTED",
            "rejection_type": "LOW_EXECUTION",
            "expected_readiness": "not_ready",
            "selected_recommendation_text": None,
            "selected_recommendation_text_localized": None,
            "selected_recommendation_source": "suppressed",
            "selected_action_count": 0,
        }
    )

    packet = build_operator_review_packet(roadmap)

    assert packet.short_view.decision_status == "REJECTED"
    assert len(packet.short_view.top_blockers) == 1
    assert packet.short_view.next_best_actions == []
    assert packet.technical_appendix.action_render_source == "suppressed"
    assert packet.technical_appendix.readiness_render_mode == "rejected_not_ready"
    assert "rejected_actions_suppressed" in packet.technical_appendix.packet_coherence_codes


def test_empty_state_packet_renders_explicit_message_without_actions() -> None:
    roadmap = _base_roadmap()
    roadmap["best_plan_id"] = None
    roadmap["summary"].update(
        {
            "decision_status": "REJECTED",
            "selected_decision_status": "REJECTED",
            "decision_status_internal": "REJECTED",
            "selected_plan_status_internal": None,
            "decision_reason_primary": "",
            "decision_reason_drivers": [],
            "selection_outcome": "no_valid_winner",
            "selection_stage": "no_valid_winner",
            "recourse_mode": "limited",
            "recommendation_mode": "informational",
            "recoverable_flag": False,
            "narrative_type": "informational",
            "informational_subtype": "not_currently_actionable",
            "narrative_contract_version": "phase_66_v1",
            "approval_gap": 0.12,
            "recoverability_bucket": "mid_risk",
            "selected_recommendation_text": None,
            "selected_recommendation_text_localized": None,
            "selected_recommendation_source": "empty_state",
            "selected_action_count": 0,
        }
    )

    packet = build_operator_review_packet(roadmap)
    markdown = render_operator_review_packet_markdown(packet)

    assert packet.short_view.next_best_actions == []
    assert len(packet.short_view.top_blockers) == 1
    assert packet.technical_appendix.blocker_render_source == "empty_state"
    assert packet.technical_appendix.action_render_source == "empty_state"
    assert packet.technical_appendix.readiness_render_mode == "empty_state_context"
    assert packet.technical_appendix.approval_gap == 0.12
    assert packet.technical_appendix.recoverability_bucket == "mid_risk"
    assert "empty_state_blocker_rendered" in packet.technical_appendix.packet_coherence_codes
    assert "No valid recommendation path is currently available." in markdown
