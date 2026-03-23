from __future__ import annotations

import json
from pathlib import Path

import pytest

from credit_coach.ops.decision_explanation_pack import (
    build_decision_explanation_pack,
    write_decision_explanation_pack,
)
from credit_coach.ops.operator_review import build_operator_review_packet


def _sample_roadmap() -> dict:
    return {
        "customer_id": "cust-explain",
        "best_plan_id": "plan-001",
        "summary": {
            "decision_id": "decision-cust-explain",
            "decision_policy_version": "v2.1_phase_40_5",
            "decision_status": "CONDITIONAL",
            "decision_status_internal": "NEEDS_REVIEW",
            "decision_reason_summary": "The file can improve, but utilization is still above the target range.",
            "decision_reason_primary": "TIME_BLOCK",
            "decision_reason_drivers": [
                {
                    "driver_key": "utilization",
                    "current_value": 82.0,
                    "target_value": 50.0,
                    "unit": "pct",
                    "source_field": "revol_util",
                    "comparison": "lte",
                }
            ],
            "expected_readiness": "week_12",
            "upgrade_condition": "Utilization 82% -> below 50%",
            "decision_confidence": 0.58,
            "conditional_type": "TIME_GATED",
            "offer_maturity": "none",
            "offer_plan": 0,
            "offer_acceptance_probability": 0.0,
        },
        "contract_health": {"raw_contract_pass": 1, "parity_pass": 1, "data_issue_flag": 0},
        "narrative": {
            "steps": [
                {
                    "step_id": "limit_credit_usage:phase_1",
                    "action_key": "limit_credit_usage",
                    "action_summary": {"tr": "Kart kullanimini azalt.", "en": "Reduce credit utilization."},
                    "what_happens_if_not_done": {"tr": "Hazirlik gecikir.", "en": "Readiness remains delayed."},
                }
            ]
        },
    }


def test_build_decision_explanation_pack_is_external_only_and_matches_operator_packet() -> None:
    roadmap = _sample_roadmap()
    operator_packet = build_operator_review_packet(roadmap)

    pack = build_decision_explanation_pack(
        roadmap,
        metrics_summary={"adverse_action_reasons": ["high_credit_utilization", "high_debt_to_income"]},
        operator_packet=operator_packet,
        qa_status="PASS",
        qa_stamp="artifact_qa:PASS",
    )

    assert pack.external_decision_only is True
    assert pack.decision_outcome == "CONDITIONAL"
    assert pack.decision_id == operator_packet.decision_id
    assert pack.policy_version == operator_packet.decision_policy_version
    assert pack.expected_readiness == "week_12"
    assert pack.upgrade_condition == "Utilization 82% -> below 50%"
    assert len(pack.structured_numeric_drivers) == 1
    assert pack.structured_numeric_drivers[0].driver_key == "utilization"
    assert [reason.reason_code for reason in pack.adverse_action_friendly_reasons] == [
        "high_credit_utilization",
        "high_debt_to_income",
    ]
    assert any("not a legal opinion" in item.lower() for item in pack.disclaimer)


def test_build_decision_explanation_pack_fails_on_operator_drift() -> None:
    roadmap = _sample_roadmap()
    operator_packet = build_operator_review_packet(roadmap).model_dump(mode="json")
    operator_packet["short_view"]["expected_readiness"] = "week_4"

    with pytest.raises(ValueError, match="expected readiness mismatch"):
        build_decision_explanation_pack(
            roadmap,
            metrics_summary={"adverse_action_reasons": ["high_credit_utilization"]},
            operator_packet=operator_packet,
        )


def test_write_decision_explanation_pack_emits_json_and_markdown(tmp_path: Path) -> None:
    pack = build_decision_explanation_pack(
        _sample_roadmap(),
        metrics_summary={"adverse_action_reasons": ["high_credit_utilization"]},
        qa_status="DEGRADED",
        qa_stamp="artifact_qa:DEGRADED",
    )

    written = write_decision_explanation_pack(pack, tmp_path / "explanations" / "cust-explain")

    assert written["decision_explanation_pack_json"].exists()
    assert written["decision_explanation_pack_md"].exists()
    payload = json.loads(written["decision_explanation_pack_json"].read_text(encoding="utf-8"))
    assert payload["decision_outcome"] == "CONDITIONAL"
    assert payload["external_decision_only"] is True
    assert payload["qa_status"] == "DEGRADED"
