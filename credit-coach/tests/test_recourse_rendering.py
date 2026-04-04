from __future__ import annotations

from credit_coach.coaching.messaging import build_recourse_path_render_payload


def test_customer_only_path_render_uses_metric_aware_summary() -> None:
    payload = build_recourse_path_render_payload(
        {"path_id": "path-1", "path_type": "customer_only"},
        {
            "actions": [
                {
                    "action_key": "limit_credit_usage",
                    "action_title": "Limit credit usage",
                    "business_view": {
                        "action_key": "limit_credit_usage",
                        "action_class": "behavioral",
                        "action_title": "Limit credit usage",
                        "action_group_id": "limit_credit_usage:phase_1",
                    },
                    "primary_numeric_target": {
                        "metric_key": "credit_utilization_pct",
                        "unit": "percentage_points",
                        "current_value": 63.2,
                        "target_value": 45.0,
                        "delta_value": -18.2,
                        "due_month": 3,
                        "direction": "decrease",
                    },
                }
            ]
        },
        customer_context={"revol_bal": 6320.0, "total_rev_hi_lim": 10000.0},
    )

    assert payload["render_version"] == "phase59_action_semantics_rendering_v1"
    assert payload["customer_summary"] is not None
    assert "Reduce credit utilization from %63.2 to below %45." in payload["customer_summary"].en
    assert "1,820 units" in payload["customer_summary"].en
    assert payload["operator_summary"] is not None
    assert payload["operator_summary"].en.startswith("customer-only path ")


def test_institution_assisted_path_render_stays_dependency_honest() -> None:
    payload = build_recourse_path_render_payload(
        {"path_id": "path-2", "path_type": "institution_assisted"},
        {
            "actions": [
                {
                    "action_key": "credit_limit_adjustment",
                    "action_title": "Request credit limit adjustment",
                    "business_view": {
                        "action_key": "credit_limit_adjustment",
                        "action_class": "institutional",
                        "action_title": "Request credit limit adjustment",
                        "action_group_id": "credit_limit_adjustment:phase_2",
                    },
                    "dependency_gate": True,
                    "primary_numeric_target": {
                        "metric_key": "total_high_credit_limit_amount",
                        "unit": "currency",
                        "current_value": 6000.0,
                        "target_value": 7500.0,
                        "delta_value": 1500.0,
                        "due_month": 3,
                        "direction": "increase",
                    },
                }
            ]
        },
    )

    assert payload["customer_summary"] is not None
    assert payload["customer_summary"].en.startswith("If approved,")
    assert "additional total credit capacity" in payload["customer_summary"].en
    assert payload["customer_summary"].tr.startswith("Onaylanirsa,")
    assert payload["operator_summary"] is not None
    assert payload["operator_summary"].en.startswith("institution-assisted path ")


def test_hybrid_path_render_names_customer_action_and_institution_dependency() -> None:
    payload = build_recourse_path_render_payload(
        {"path_id": "path-3", "path_type": "hybrid"},
        {
            "actions": [
                {
                    "action_key": "refinance",
                    "action_title": "Refinance or restructure debt",
                    "requires_institutional_approval": True,
                    "approval_pending_semantic_only": True,
                    "business_view": {
                        "action_key": "refinance",
                        "action_class": "structural",
                        "action_title": "Refinance or restructure debt",
                        "action_group_id": "refinance:phase_2",
                    },
                    "primary_numeric_target": {
                        "metric_key": "monthly_payment_amount",
                        "unit": "currency",
                        "current_value": 510.0,
                        "target_value": 450.0,
                        "delta_value": -60.0,
                        "due_month": 3,
                        "direction": "decrease",
                    },
                }
            ]
        },
    )

    assert payload["customer_summary"] is not None
    assert "monthly payment burden" in payload["customer_summary"].en
    assert "Depends on institution approval." in payload["customer_summary"].en
    assert payload["operator_summary"] is not None
    assert payload["operator_summary"].en.startswith("hybrid path ")


def test_path_render_suppresses_generic_summary_language() -> None:
    payload = build_recourse_path_render_payload(
        {"path_id": "path-4", "path_type": "customer_only"},
        {
            "actions": [
                {
                    "action_key": "custom_follow_up",
                    "action_title": "Take action",
                    "business_view": {
                        "action_key": "custom_follow_up",
                        "action_class": "behavioral",
                        "action_title": "Take action",
                        "action_group_id": "custom_follow_up:phase_1",
                    },
                }
            ]
        },
    )

    assert payload["customer_summary"] is None
    assert payload["operator_summary"] is None
    assert payload["render_version"] == "phase59_action_semantics_rendering_v1"
