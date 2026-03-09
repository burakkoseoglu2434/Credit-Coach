from __future__ import annotations

from credit_coach.coaching.messaging import (
    build_adverse_action_payload,
    build_adverse_action_reasons,
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
