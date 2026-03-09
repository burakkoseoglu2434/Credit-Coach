from __future__ import annotations

from credit_coach.policy.engine import apply_policy_rules


def test_apply_policy_rules_returns_adverse_action_payload_when_rejected():
    local_reasons = [
        {"feature": "dti", "direction": "increase_risk", "abs_contribution": 0.42},
        {"feature": "revol_util", "direction": "increase_risk", "abs_contribution": 0.31},
    ]
    out = apply_policy_rules(0.55, tau=0.35, min_income_ok=False, local_reasons=local_reasons)
    assert out["approved"] is False
    assert out["reason"] == "policy_reject"
    assert "adverse_action" in out
    assert out["adverse_action"]["specificity_ok"] is True


def test_apply_policy_rules_approved_has_no_adverse_action():
    out = apply_policy_rules(0.20, tau=0.35, min_income_ok=True)
    assert out["approved"] is True
    assert out["reason"] == "policy_pass"
    assert "adverse_action" not in out
