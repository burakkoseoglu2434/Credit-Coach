from __future__ import annotations

from credit_coach.coaching.messaging import (
    build_adverse_action_payload,
    build_adverse_action_reasons,
    build_checkpoint_narrative,
    build_customer_roadmap_narrative,
    validate_reason_specificity,
)


def test_build_adverse_action_reasons_orders_and_filters():
    reasons = [
        {"feature": "annual_inc", "direction": "decrease_risk", "abs_contribution": 0.12},
        {"feature": "dti", "direction": "increase_risk", "abs_contribution": 0.31},
        {"feature": "revol_util", "direction": "increase_risk", "abs_contribution": 0.22},
    ]
    out = build_adverse_action_reasons(reasons, max_items=3)
    assert out == ["high_debt_to_income", "high_credit_utilization"]


def test_build_adverse_action_reasons_deduplicates():
    reasons = [
        {"feature": "dti", "direction": "increase_risk", "abs_contribution": 0.31},
        {"feature": "dti", "direction": "increase_risk", "abs_contribution": 0.11},
        {"feature": "unknown-feature", "direction": "increase_risk", "abs_contribution": 0.09},
    ]
    out = build_adverse_action_reasons(reasons, max_items=5)
    assert out[0] == "high_debt_to_income"
    assert out[1] == "risk_factor_unknown_feature"
    assert len(out) == 2


def test_build_adverse_action_payload_contains_templates():
    reasons = [
        {"feature": "dti", "direction": "increase_risk", "abs_contribution": 0.31},
        {"feature": "revol_util", "direction": "increase_risk", "abs_contribution": 0.22},
    ]
    payload = build_adverse_action_payload(reasons, max_items=2)
    assert len(payload["principal_reasons"]) == 2
    assert payload["specificity_ok"] is True
    assert len(payload["reason_details"]) == 2
    assert "Debt-to-income ratio is high" in payload["notice_text"]


def test_validate_reason_specificity_flags_generic_codes():
    assert validate_reason_specificity(["high_debt_to_income"]) is True
    assert validate_reason_specificity(["risk_factor_unknown"]) is False


def test_build_customer_roadmap_narrative_is_deterministic():
    phases = [
        {
            "phase_id": "phase_1_stabilize",
            "steps": [
                {
                    "step_id": "reduce_spending:phase_1_stabilize",
                    "action_key": "reduce_spending",
                    "action_class": "behavioral",
                    "action_title": "Reduce spending pressure",
                    "time_months": 1,
                    "action_group_id": "reduce_spending:phase_1_stabilize",
                    "business_view": {
                        "action_key": "reduce_spending",
                        "action_family": "cashflow_management",
                        "action_class": "behavioral",
                        "action_title": "Reduce spending pressure",
                        "action_description": "Reduce ongoing spending to improve debt-to-income behavior.",
                        "action_group_id": "reduce_spending:phase_1_stabilize",
                    },
                    "technical_view": {
                        "feature_name": "dti",
                        "current_value": 28.0,
                        "target_value": 24.0,
                        "delta": -4.0,
                        "time_months": 1,
                        "phase_id": "phase_1_stabilize",
                    },
                    "primary_numeric_target": {
                        "metric_key": "debt_to_income_pct",
                        "unit": "percentage_points",
                        "current_value": 28.0,
                        "target_value": 24.0,
                        "delta_value": -4.0,
                        "due_month": 2,
                        "direction": "decrease",
                        "generation_notes": ["semantic_sanity_only"],
                        "raw_generation_basis": {"source_feature_name": "dti"},
                    },
                    "diagnostic_flags": ["light_burden"],
                }
            ],
        }
    ]
    checkpoints = [
        {
            "checkpoint_id": "checkpoint_week_4",
            "week": 4,
            "predicted_pd": 0.31,
            "gate_pass_estimate": 1,
        },
        {
            "checkpoint_id": "checkpoint_week_12",
            "week": 12,
            "predicted_pd": 0.28,
            "gate_pass_estimate": 1,
        },
    ]
    local_reason_bundle = {
        "reasons": [
            {"feature": "dti", "direction": "increase_risk", "abs_contribution": 0.31},
            {"feature": "revol_util", "direction": "increase_risk", "abs_contribution": 0.22},
        ],
        "meta": {
            "explainability_confidence": 0.83,
            "stability_score": 0.91,
            "baseline_drift_l1": 0.07,
        },
    }

    left = build_customer_roadmap_narrative(
        base_pd=0.42,
        tau=0.35,
        phases=phases,
        checkpoints=checkpoints,
        status="NEEDS_REVIEW",
        local_reason_bundle=local_reason_bundle,
        constraint_trace=[{"reason_code": "clip:income_cap"}],
        plan_execution_probability=0.72,
    )
    right = build_customer_roadmap_narrative(
        base_pd=0.42,
        tau=0.35,
        phases=phases,
        checkpoints=checkpoints,
        status="NEEDS_REVIEW",
        local_reason_bundle=local_reason_bundle,
        constraint_trace=[{"reason_code": "clip:income_cap"}],
        plan_execution_probability=0.72,
    )

    assert left.model_dump(mode="json") == right.model_dump(mode="json")
    assert left.executive_summary.decision_view.label.en == "Needs reassessment"
    assert left.executive_summary.time_to_readiness.label.en == "4 weeks"
    assert left.steps[0].action_summary.en.startswith("Reduce non-essential spending")
    assert "debt-to-income ratio" in left.steps[0].expected_outcome.en
    assert "%24" in left.steps[0].expected_outcome.en
    assert "-4 pts" in left.steps[0].expected_outcome.en
    assert left.steps[0].action_timing_hint.en == "Complete within the next 3 months."
    assert left.checkpoints[0].success_condition.en
    assert left.reasons[0].reason_title.en == "Debt-to-income ratio is high"
    assert left.technical_reveal.narrative_confidence_label == "high"


def test_build_customer_roadmap_narrative_separates_offer_and_checkpoint_layers():
    narrative = build_customer_roadmap_narrative(
        base_pd=0.51,
        tau=0.35,
        phases=[
            {
                "phase_id": "phase_2_build",
                "steps": [
                    {
                        "step_id": "installment_plan:phase_2_build",
                        "action_key": "installment_plan",
                        "action_class": "institutional",
                        "action_title": "Enter an installment plan",
                        "time_months": 3,
                        "business_view": {
                            "action_key": "installment_plan",
                            "action_family": "hardship_relief",
                            "action_class": "institutional",
                            "action_title": "Enter an installment plan",
                            "action_description": "Restructure delinquent balances into an approved installment plan.",
                            "action_group_id": "installment_plan:phase_2_build",
                        },
                        "technical_view": {
                            "feature_name": "delinq_amnt",
                            "current_value": 2400.0,
                            "target_value": 1200.0,
                            "delta": -1200.0,
                            "time_months": 3,
                            "phase_id": "phase_2_build",
                        },
                        "offer_type": "installment_terms",
                        "offer_terms": {
                            "payment_delta_monthly": -120.0,
                            "term_extension_months": 6,
                            "grace_period_weeks": 2,
                        },
                        "requires_acceptance": True,
                        "requires_institutional_approval": False,
                    }
                ],
            }
        ],
        checkpoints=[
            {
                "checkpoint_id": "checkpoint_week_12",
                "week": 12,
                "predicted_pd": 0.34,
                "gate_pass_estimate": 1,
            }
        ],
        status="NEEDS_REVIEW",
        local_reason_bundle={"reasons": [], "meta": {"explainability_confidence": 0.6}},
        plan_execution_probability=0.61,
        offer_acceptance_probability=0.49,
        combined_plan_realization_probability=0.2989,
    )

    step = narrative.steps[0]
    checkpoint = narrative.checkpoints[0]
    assert step.offer_narrative is not None
    assert "installment" in step.offer_narrative.offer_explanation.en.lower()
    assert step.offer_narrative.offer_terms_summary is not None
    assert checkpoint.expected_state.en.startswith("By the mid-term checkpoint")
    assert checkpoint.review_action is not None
    assert narrative.technical_reveal.approval_dependencies[0]["requires_acceptance"] is True
    assert narrative.technical_reveal.confidence_inputs["offer_acceptance_probability"] == 0.49


def test_build_customer_roadmap_narrative_groups_same_action_step_in_default_view():
    narrative = build_customer_roadmap_narrative(
        base_pd=0.48,
        tau=0.35,
        phases=[
            {
                "phase_id": "phase_2_build",
                "steps": [
                    {
                        "step_id": "refinance:phase_2_build",
                        "action_key": "refinance",
                        "action_class": "structural",
                        "action_title": "Refinance or restructure debt",
                        "action_group_id": "refinance:phase_2_build",
                        "business_view": {
                            "action_key": "refinance",
                            "action_family": "debt_restructuring",
                            "action_class": "structural",
                            "action_title": "Refinance or restructure debt",
                            "action_description": "Use refinancing to improve rate and installment affordability.",
                            "action_group_id": "refinance:phase_2_build",
                        },
                        "technical_view": {
                            "feature_name": "int_rate",
                            "current_value": 21.0,
                            "target_value": 18.5,
                            "delta": -2.5,
                            "time_months": 3,
                            "phase_id": "phase_2_build",
                        },
                    },
                    {
                        "step_id": "refinance:phase_2_build",
                        "action_key": "refinance",
                        "action_class": "structural",
                        "action_title": "Refinance or restructure debt",
                        "action_group_id": "refinance:phase_2_build",
                        "business_view": {
                            "action_key": "refinance",
                            "action_family": "debt_restructuring",
                            "action_class": "structural",
                            "action_title": "Refinance or restructure debt",
                            "action_description": "Use refinancing to improve rate and installment affordability.",
                            "action_group_id": "refinance:phase_2_build",
                        },
                        "technical_view": {
                            "feature_name": "installment",
                            "current_value": 510.0,
                            "target_value": 450.0,
                            "delta": -60.0,
                            "time_months": 3,
                            "phase_id": "phase_2_build",
                        },
                        "primary_numeric_target": {
                            "metric_key": "monthly_payment_amount",
                            "unit": "currency",
                            "current_value": 510.0,
                            "target_value": 450.0,
                            "delta_value": -60.0,
                            "due_month": 3,
                            "direction": "decrease",
                            "generation_notes": ["semantic_sanity_only"],
                            "raw_generation_basis": {"source_feature_name": "installment"},
                        },
                    },
                ],
            }
        ],
        checkpoints=[
            {
                "checkpoint_id": "checkpoint_week_12",
                "week": 12,
                "predicted_pd": 0.34,
                "gate_pass_estimate": 1,
            }
        ],
        status="NEEDS_REVIEW",
        local_reason_bundle={"reasons": [], "meta": {"explainability_confidence": 0.72}},
    )

    assert len(narrative.steps) == 1
    assert narrative.steps[0].step_id == "refinance:phase_2_build"
    assert "monthly payment amount" in narrative.steps[0].expected_outcome.en
    assert "450 units" in narrative.steps[0].expected_outcome.en
    assert len(narrative.technical_reveal.feature_changes) == 2


def test_build_checkpoint_narrative_reflects_missed_status_and_inconsistency():
    narrative = build_checkpoint_narrative(
        {
            "checkpoint_id": "checkpoint_week_24",
            "week": 24,
            "predicted_pd": 0.44,
            "gate_pass_estimate": 0,
            "status": "missed",
            "trajectory_jump_flag": 1,
            "checkpoint_inconsistency_flag": 1,
        },
        tau=0.35,
    )

    assert "kalicilasmakta zorlanabilir" in narrative.expected_state.tr
    assert narrative.review_action.en.startswith("Review the checkpoint signal again")
