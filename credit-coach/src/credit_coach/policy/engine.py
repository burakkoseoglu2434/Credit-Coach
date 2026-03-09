from __future__ import annotations

from credit_coach.coaching.messaging import build_adverse_action_payload


def apply_policy_rules(
    pd_score: float,
    tau: float,
    min_income_ok: bool = True,
    *,
    local_reasons: list[dict] | None = None,
) -> dict:
    approved = (pd_score <= tau) and min_income_ok
    payload = {"approved": approved, "reason": "policy_pass" if approved else "policy_reject"}
    if not approved:
        payload["adverse_action"] = build_adverse_action_payload(local_reasons or [], max_items=4)
    return payload
