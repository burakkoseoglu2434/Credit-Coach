from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from credit_coach.ops.operator_review import (
    build_collection_operator_briefing,
    build_operator_review_packet,
    render_collection_operator_briefing_markdown,
    render_operator_review_packet_markdown,
    write_operator_review_packet,
)


def _sample_roadmap() -> dict:
    return {
        "customer_id": "cust-operator",
        "best_plan_id": "plan-123",
        "summary": {
            "decision_id": "decision-cust-operator",
            "decision_policy_version": "v2.1_phase_40_5",
            "decision_status": "CONDITIONAL",
            "selected_decision_status": "CONDITIONAL",
            "decision_status_internal": "NEEDS_REVIEW",
            "selected_plan_status_internal": "REJECTED",
            "decision_reason_summary": "The plan is viable, but execution confidence is not strong enough yet.",
            "decision_reason_primary": "LOW_EXECUTION",
            "decision_reason_drivers": [
                {
                    "driver_key": "realization_anchor",
                    "current_value": 0.38,
                    "target_value": 0.50,
                    "unit": "probability",
                    "source_field": "realization_anchor",
                    "comparison": "gte",
                },
                {
                    "driver_key": "decision_confidence",
                    "current_value": 0.41,
                    "target_value": 0.60,
                    "unit": "score",
                    "source_field": "decision_confidence",
                    "comparison": "gte",
                },
            ],
            "decision_confidence": 0.41,
            "expected_readiness": "week_12",
            "upgrade_condition": "realization_anchor 0.38 -> 0.50; decision_confidence 0.41 -> 0.60",
            "conditional_type": "EXECUTION_GATED",
            "offer_maturity": "none",
            "offer_plan": 0,
            "offer_acceptance_probability": 0.0,
            "decision_gate_trace": {"reject": False, "approve": False, "conditional": True, "confidence": 0.41},
            "selection_outcome": "selected_valid_winner",
            "selection_stage": "preferred_valid",
            "selected_recommendation_text": "Reduce monthly debt pressure by about 600 units and move debt-to-income from %28 to %24.",
            "selected_recommendation_text_localized": {
                "tr": "Aylik borc/harcama baskisini yaklasik 600 birim azalt ve borc/gelir oranini %28'den %24 seviyesine indir.",
                "en": "Reduce monthly debt pressure by about 600 units and move debt-to-income from %28 to %24.",
            },
            "selected_institution_condition": "The profile needs about 1,500 units of additional total credit capacity to strengthen.",
            "selected_institution_condition_localized": {
                "tr": "Profilin guclenmesi icin toplam limit tarafinda yaklasik 1,500 birim ek kapasite gerekiyor.",
                "en": "The profile needs about 1,500 units of additional total credit capacity to strengthen.",
            },
            "selected_recommendation_source": "selected_plan",
            "selected_action_count": 2,
            "selected_recommendation_projection_version": "v2.2_phase_47",
        },
        "contract_health": {"raw_contract_pass": 1, "parity_pass": 1, "data_issue_flag": 0},
        "narrative": {
            "executive_summary": {
                "offer_status": {
                    "label": {"tr": "Kurum teklifi yok", "en": "No institution offer"},
                    "description": {"tr": "Yol musteride.", "en": "The path relies on customer action."},
                }
            },
            "steps": [
                {
                    "step_id": "reduce_spending:phase_1",
                    "action_key": "reduce_spending",
                    "primary_recommendation": {
                        "tr": "Aylik borc/harcama baskisini yaklasik 600 birim azalt ve borc/gelir oranini %28'den %24 seviyesine indir.",
                        "en": "Reduce monthly debt pressure by about 600 units and move debt-to-income from %28 to %24.",
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
                    "expected_outcome": {
                        "tr": "Nakit akisi dengelenir.",
                        "en": "Cash flow stabilizes.",
                    },
                },
                {
                    "step_id": "limit_credit_usage:phase_1",
                    "action_key": "limit_credit_usage",
                    "institution_condition": {
                        "tr": "Profilin guclenmesi icin toplam limit tarafinda yaklasik 1,500 birim ek kapasite gerekiyor.",
                        "en": "The profile needs about 1,500 units of additional total credit capacity to strengthen.",
                    },
                    "action_summary": {
                        "tr": "Kart kullanimini sinirla.",
                        "en": "Limit credit usage.",
                    },
                    "action_timing_hint": {
                        "tr": "Onumuzdeki 1 ay icinde tamamla.",
                        "en": "Complete within the next 1 months.",
                    },
                    "what_happens_if_not_done": {
                        "tr": "Kullanim baskisi yuksek kalir.",
                        "en": "Utilization pressure stays high.",
                    },
                    "expected_outcome": {
                        "tr": "Kullanim gorunumu iyilesir.",
                        "en": "Utilization improves.",
                    },
                },
            ],
        },
    }


def test_build_operator_review_packet_keeps_owned_summary_and_action_traces() -> None:
    packet = build_operator_review_packet(_sample_roadmap())

    assert packet.short_view.decision_status == "CONDITIONAL"
    assert (
        packet.short_view.decision_reason_summary
        == "The plan is viable, but execution confidence is not strong enough yet."
    )
    assert packet.short_view.expected_readiness == "week_12"
    assert packet.short_view.offer_state is not None
    assert packet.short_view.offer_state.en == "No institution offer"
    assert packet.short_view.technical_detail_available is True
    assert packet.decision_id == "decision-cust-operator"
    assert packet.decision_policy_version == "v2.1_phase_40_5"
    assert packet.technical_appendix.decision_status_internal == "NEEDS_REVIEW"
    assert packet.technical_appendix.selected_plan_status_internal == "REJECTED"
    assert packet.technical_appendix.selected_recommendation_source == "selected_plan"
    assert packet.technical_appendix.blocker_render_source == "driver"
    assert packet.technical_appendix.action_render_source == "selected_projection"
    assert packet.technical_appendix.readiness_render_mode == "conditional_time_gate"
    assert packet.technical_appendix.active_driver_count == 2
    assert len(packet.short_view.top_blockers) == 2
    assert len(packet.short_view.next_best_actions) == 2
    assert all(action.blocker_codes for action in packet.short_view.next_best_actions)
    assert packet.short_view.next_best_actions[0].action_summary.en.startswith("Reduce monthly debt pressure by about 600 units")
    assert packet.short_view.next_best_actions[1].institution_condition is not None
    assert "additional total credit capacity" in packet.short_view.next_best_actions[1].institution_condition.en
    assert "target" in packet.short_view.top_blockers[0].blocker_detail.en.lower()

    markdown = render_operator_review_packet_markdown(packet)
    assert "## 1-line Summary" in markdown
    assert "Institution condition:" in markdown
    assert "NEEDS_REVIEW" not in markdown.split("## Technical Appendix")[0]


def test_write_operator_review_packet_emits_json_and_markdown(tmp_path: Path) -> None:
    packet = build_operator_review_packet(_sample_roadmap())
    out = write_operator_review_packet(packet, tmp_path / "packet")

    assert out["operator_packet_json"].exists()
    assert out["operator_packet_md"].exists()
    payload = json.loads(out["operator_packet_json"].read_text(encoding="utf-8"))
    assert payload["decision_id"] == "decision-cust-operator"
    assert payload["short_view"]["decision_status"] == "CONDITIONAL"
    assert payload["technical_appendix"]["decision_status_internal"] == "NEEDS_REVIEW"


def test_build_operator_review_packet_surfaces_recommendation_sanity_badge() -> None:
    roadmap = _sample_roadmap()
    roadmap["summary"]["recommendation_sanity_flag"] = 1
    roadmap["summary"]["recommendation_warning_action_count"] = 1
    roadmap["summary"]["recommendation_validity_codes"] = ["economic_delta_large"]

    packet = build_operator_review_packet(roadmap)

    assert packet.short_view.recommendation_sanity_flag is True
    assert packet.short_view.recommendation_sanity_note is not None
    assert "manual-review note" in packet.short_view.recommendation_sanity_note.en.lower()
    assert packet.technical_appendix.recommendation_warning_action_count == 1
    assert packet.technical_appendix.recommendation_validity_codes == ["economic_delta_large"]


def test_build_operator_review_packet_renders_empty_state_for_no_valid_winner() -> None:
    roadmap = _sample_roadmap()
    roadmap["best_plan_id"] = None
    roadmap["summary"].update(
        {
            "decision_status": "REJECTED",
            "selected_decision_status": "REJECTED",
            "selected_plan_status_internal": None,
            "decision_reason_primary": "",
            "decision_reason_drivers": [],
            "selection_outcome": "no_valid_winner",
            "selection_stage": "no_valid_winner",
            "selected_recommendation_text": None,
            "selected_recommendation_text_localized": None,
            "selected_institution_condition": None,
            "selected_institution_condition_localized": None,
            "selected_recommendation_source": "empty_state",
            "selected_action_count": 0,
        }
    )

    packet = build_operator_review_packet(roadmap)

    assert packet.short_view.decision_status == "REJECTED"
    assert packet.short_view.next_best_actions == []
    assert packet.technical_appendix.selected_recommendation_source == "empty_state"
    assert packet.technical_appendix.blocker_render_source == "empty_state"
    assert packet.technical_appendix.action_render_source == "empty_state"
    assert packet.technical_appendix.readiness_render_mode == "empty_state_context"
    markdown = render_operator_review_packet_markdown(packet)
    assert "No valid recommendation path is currently available." in markdown


def test_build_collection_operator_briefing_prioritizes_upgrade_queue_and_health_note() -> None:
    metrics_df = pd.DataFrame(
        [
            {
                "customer_id": "cust-1",
                "decision_status": "CONDITIONAL",
                "expected_readiness": "week_4",
                "decision_confidence": 0.58,
                "conditional_type": "TIME_GATED",
                "offer_needed_flag": "offer_needed",
            },
            {
                "customer_id": "cust-2",
                "decision_status": "CONDITIONAL",
                "expected_readiness": "week_12",
                "decision_confidence": 0.55,
                "conditional_type": "OFFER_GATED",
                "offer_needed_flag": "offer_needed",
            },
            {
                "customer_id": "cust-3",
                "decision_status": "REJECTED",
                "expected_readiness": "not_ready",
                "decision_confidence": 0.22,
                "conditional_type": "",
                "offer_needed_flag": "no_offer_needed",
            },
        ]
    )
    packets = [
        {
            "short_view": {
                "top_blockers": [
                    {
                        "blocker_code": "driver:realization_anchor",
                        "blocker_title": {"en": "Execution strength is still weak", "tr": "Uygulama gucu zayif"},
                    }
                ]
            }
        },
        {
            "short_view": {
                "top_blockers": [
                    {
                        "blocker_code": "driver:rankable_offer_count",
                        "blocker_title": {"en": "Institution support is not active yet", "tr": "Kurum destegi aktif degil"},
                    }
                ]
            }
        },
    ]
    briefing = build_collection_operator_briefing(
        metrics_df=metrics_df,
        operator_packets=packets,
        funnel_summary={
            "approved_share": 0.0,
            "conditional_share": 0.6667,
            "rejected_share": 0.3333,
            "approve_plus_conditional_share": 0.6667,
            "internal_needs_review_share": 0.125,
        },
        readiness_summary={"distribution": {"week_4": {"count": 1}, "week_12": {"count": 1}, "not_ready": {"count": 1}}},
        segment_breakdown_df=pd.DataFrame(
            [
                {"segment_axis": "risk_band", "segment_value": "near", "count": 2, "approve_plus_conditional_share": 0.9},
                {"segment_axis": "offer_needed_flag", "segment_value": "offer_needed", "count": 2, "approve_plus_conditional_share": 0.7},
            ]
        ),
    )

    assert briefing["priority_queues"][0]["queue_key"] == "likely_to_upgrade_soon"
    assert briefing["priority_queues"][0]["count"] == 2
    assert briefing["dominant_blockers"][0]["count"] == 1
    assert "Internal needs-review share" in briefing["health_note"]
    markdown = render_collection_operator_briefing_markdown(briefing)
    assert "## Priority Queues" in markdown
    assert "Likely to upgrade soon" in markdown
