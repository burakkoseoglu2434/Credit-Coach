from __future__ import annotations


def reason_codes(
    progress_label: str,
    replan: bool,
    ci_high: float,
    tau: float,
    replan_reasons: list[str] | None = None,
) -> list[str]:
    reasons = []
    reasons.append(f"progress:{progress_label}")
    reasons.append(f"risk_bound:{ci_high:.4f}_tau:{tau:.4f}")
    reasons.append("action:replan" if replan else "action:continue")
    if replan and replan_reasons:
        reasons.extend([f"trigger:{r}" for r in replan_reasons[:2]])
    return reasons[:3]


_ADVERSE_ACTION_REASON_MAP = {
    "dti": "high_debt_to_income",
    "revol_util": "high_credit_utilization",
    "int_rate": "high_interest_obligation",
    "inq_last_6mths": "too_many_recent_credit_inquiries",
    "delinq_2yrs": "recent_delinquency_history",
    "open_acc": "high_open_credit_exposure",
    "annual_inc": "insufficient_verified_income",
    "tot_cur_bal": "high_total_outstanding_balance",
    "credit_history_len": "limited_credit_history_depth",
    "mths_since_last_delinq": "recent_delinquency_recency_risk",
}

_REASON_TEMPLATES: dict[str, dict[str, str]] = {
    "high_debt_to_income": {
        "title": "Debt-to-income ratio is high",
        "description": "Current debt burden relative to income is above policy tolerance.",
        "remediation_hint": "Reduce monthly debt obligations or increase verified income.",
    },
    "high_credit_utilization": {
        "title": "Credit utilization is high",
        "description": "A high share of revolving limits is currently in use.",
        "remediation_hint": "Lower revolving balances and keep utilization stable over time.",
    },
    "high_interest_obligation": {
        "title": "Interest burden is elevated",
        "description": "Current rate and debt structure imply high payment pressure.",
        "remediation_hint": "Refinance expensive balances or reduce high-rate obligations.",
    },
    "insufficient_verified_income": {
        "title": "Verified income is insufficient",
        "description": "Verified income level does not currently support requested risk level.",
        "remediation_hint": "Provide updated income verification or reduce requested amount.",
    },
}


def _normalize_reason_code(feature: str) -> str:
    f = str(feature).strip().lower()
    if f in _ADVERSE_ACTION_REASON_MAP:
        return _ADVERSE_ACTION_REASON_MAP[f]
    safe = "".join(ch if ch.isalnum() else "_" for ch in f).strip("_")
    return f"risk_factor_{safe}" if safe else "risk_factor_unknown"


def build_adverse_action_reasons(local_reasons: list[dict], max_items: int = 4) -> list[str]:
    """
    Converts local explanation contributions into regulator-friendly reason codes.

    Rules:
    - only risk-increasing drivers are considered
    - reasons are ordered by absolute contribution descending
    - duplicates are removed while preserving order
    """
    if not local_reasons:
        return []
    ranked = sorted(
        [
            r
            for r in local_reasons
            if str(r.get("direction", "")).strip().lower() == "increase_risk"
        ],
        key=lambda r: float(r.get("abs_contribution", 0.0)),
        reverse=True,
    )
    out: list[str] = []
    seen: set[str] = set()
    for r in ranked:
        code = _normalize_reason_code(str(r.get("feature", "")))
        if code in seen:
            continue
        seen.add(code)
        out.append(code)
        if len(out) >= max(1, int(max_items)):
            break
    return out


def validate_reason_specificity(reason_codes: list[str]) -> bool:
    if not reason_codes:
        return False
    generic_tokens = {"unknown", "other", "misc", "risk_factor_unknown"}
    for code in reason_codes:
        c = str(code).strip().lower()
        if not c:
            return False
        if c in generic_tokens:
            return False
        if c.endswith("_unknown"):
            return False
    return True


def build_adverse_action_payload(local_reasons: list[dict], max_items: int = 4) -> dict:
    principal = build_adverse_action_reasons(local_reasons, max_items=max_items)
    details: list[dict[str, str]] = []
    for code in principal:
        tpl = _REASON_TEMPLATES.get(code, {})
        details.append(
            {
                "code": code,
                "title": str(tpl.get("title", code.replace("_", " ").capitalize())),
                "description": str(
                    tpl.get(
                        "description",
                        "Risk profile requires additional improvement on this factor.",
                    )
                ),
                "remediation_hint": str(
                    tpl.get(
                        "remediation_hint",
                        "Follow recourse plan actions for this factor and re-apply.",
                    )
                ),
            }
        )
    notice_text = "; ".join([d["title"] for d in details]) if details else "No principal reasons generated."
    return {
        "principal_reasons": principal,
        "specificity_ok": bool(validate_reason_specificity(principal)),
        "reason_details": details,
        "notice_text": notice_text,
    }
