from __future__ import annotations

from credit_coach.decision.ownership import DECISION_POLICY_VERSION, build_customer_decision_payload


def test_decision_payload_rejects_zero_step_as_no_path() -> None:
    payload = build_customer_decision_payload(
        {
            "best_plan_id": "",
            "best_action_count": 0,
            "zero_step_flag": 1,
            "plan_contract_pass": 0,
            "raw_contract_pass": 1,
            "parity_pass": 1,
            "data_issue_flag": 0,
            "plan_execution_probability": 0.70,
            "combined_plan_realization_probability": 0.70,
            "expected_pd_improvement": 0.04,
            "credit_readiness_stage": "week_4",
            "approval_ready_4w": 1,
        }
    )

    assert payload["decision_status"] == "REJECTED"
    assert payload["decision_status_internal"] == "REJECTED"
    assert payload["rejection_type"] == "NO_PATH"
    assert payload["decision_reason_primary"] == "NO_PATH"
    assert payload["decision_policy_version"] == DECISION_POLICY_VERSION


def test_decision_payload_approves_when_all_gates_pass() -> None:
    payload = build_customer_decision_payload(
        {
            "best_plan_id": "plan-1",
            "best_action_count": 2,
            "zero_step_flag": 0,
            "plan_contract_pass": 1,
            "best_constraint_status": "valid",
            "raw_contract_pass": 1,
            "parity_pass": 1,
            "data_issue_flag": 0,
            "plan_execution_probability": 0.66,
            "combined_plan_realization_probability": 0.66,
            "approval_dependent_plan_probability": 0.66,
            "offer_acceptance_probability": 0.0,
            "expected_pd_improvement": 0.03,
            "nominal_pd_improvement": 0.05,
            "local_explainability_confidence": 0.80,
            "credit_readiness_stage": "week_4",
            "approval_ready_4w": 1,
            "offer_plan": 0,
            "rankable_offer_count": 0,
            "approval_pending_action_count": 0,
        }
    )

    assert payload["decision_status"] == "APPROVED"
    assert payload["decision_status_internal"] == "APPROVED"
    assert payload["conditional_type"] is None
    assert payload["rejection_type"] is None
    assert payload["decision_confidence"] >= 0.60
    assert payload["strong_execution_flag"] == 1


def test_decision_payload_data_issue_stays_internal_review_and_external_conditional() -> None:
    payload = build_customer_decision_payload(
        {
            "best_plan_id": "plan-2",
            "best_action_count": 2,
            "zero_step_flag": 0,
            "plan_contract_pass": 1,
            "best_constraint_status": "valid",
            "raw_contract_pass": 0,
            "parity_pass": 1,
            "data_issue_flag": 1,
            "critical_field_null_count": 1,
            "plan_execution_probability": 0.72,
            "combined_plan_realization_probability": 0.72,
            "expected_pd_improvement": 0.04,
            "nominal_pd_improvement": 0.05,
            "local_explainability_confidence": 0.90,
            "credit_readiness_stage": "week_4",
            "approval_ready_4w": 1,
            "offer_plan": 0,
        }
    )

    assert payload["decision_status_internal"] == "NEEDS_REVIEW"
    assert payload["decision_status"] == "CONDITIONAL"
    assert payload["conditional_type"] == "DATA_ISSUE"
    assert payload["decision_reason_primary"] == "DATA_ISSUE"
    assert payload["upgrade_condition"] is not None


def test_decision_payload_week_12_is_time_gated_not_approved() -> None:
    payload = build_customer_decision_payload(
        {
            "best_plan_id": "plan-3",
            "best_action_count": 2,
            "zero_step_flag": 0,
            "plan_contract_pass": 1,
            "best_constraint_status": "valid",
            "raw_contract_pass": 1,
            "parity_pass": 1,
            "data_issue_flag": 0,
            "plan_execution_probability": 0.68,
            "combined_plan_realization_probability": 0.68,
            "expected_pd_improvement": 0.03,
            "nominal_pd_improvement": 0.05,
            "local_explainability_confidence": 0.82,
            "credit_readiness_stage": "week_12",
            "approval_ready_4w": 0,
            "offer_plan": 0,
        }
    )

    assert payload["decision_status"] == "CONDITIONAL"
    assert payload["decision_status_internal"] == "CONDITIONAL"
    assert payload["conditional_type"] == "TIME_GATED"
    assert payload["expected_readiness"] == "week_12"


def test_decision_payload_provisional_offer_cannot_approve() -> None:
    payload = build_customer_decision_payload(
        {
            "best_plan_id": "plan-4",
            "best_action_count": 2,
            "zero_step_flag": 0,
            "plan_contract_pass": 1,
            "best_constraint_status": "valid",
            "raw_contract_pass": 1,
            "parity_pass": 1,
            "data_issue_flag": 0,
            "plan_execution_probability": 0.74,
            "combined_plan_realization_probability": 0.74,
            "expected_pd_improvement": 0.04,
            "nominal_pd_improvement": 0.05,
            "local_explainability_confidence": 0.90,
            "credit_readiness_stage": "week_4",
            "approval_ready_4w": 1,
            "offer_plan": 1,
            "approval_pending_action_count": 1,
            "rankable_offer_count": 0,
        }
    )

    assert payload["offer_maturity"] == "provisional"
    assert payload["decision_status"] == "CONDITIONAL"
    assert payload["conditional_type"] == "OFFER_GATED"
    assert payload["decision_status_internal"] == "CONDITIONAL"
