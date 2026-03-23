from __future__ import annotations

from typing import Any, Mapping


DECISION_POLICY_VERSION = "v2.1_phase_40_5"

_VALID_EXTERNAL = {"APPROVED", "CONDITIONAL", "REJECTED"}
_VALID_INTERNAL = {"APPROVED", "CONDITIONAL", "REJECTED", "NEEDS_REVIEW"}
_VALID_OFFER_MATURITY = {"none", "inactive", "provisional", "active_rankable"}
_VALID_READINESS = {"now", "week_4", "week_12", "week_24", "not_ready", "unknown_review"}


def _safe_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return bool(default)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n", ""}:
        return False
    try:
        return bool(int(value))
    except Exception:
        return bool(default)


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(value)))


def _normalize_readiness(value: Any) -> str:
    normalized = _safe_text(value).lower()
    mapping = {
        "now": "now",
        "week_4": "week_4",
        "week4": "week_4",
        "week_12": "week_12",
        "week12": "week_12",
        "week_24": "week_24",
        "week24": "week_24",
        "not_ready": "not_ready",
        "not_ready_yet": "not_ready",
        "unknown_review": "unknown_review",
    }
    return mapping.get(normalized, "unknown_review")


def _readiness_week(readiness: str) -> int | None:
    return {
        "now": 0,
        "week_4": 4,
        "week_12": 12,
        "week_24": 24,
    }.get(readiness)


def _normalize_offer_maturity(summary: Mapping[str, Any]) -> str:
    if not _safe_bool(summary.get("offer_plan"), False):
        return "none"
    explicit = _safe_text(summary.get("offer_maturity")).lower()
    if explicit in _VALID_OFFER_MATURITY:
        return explicit
    if _safe_int(summary.get("approval_pending_action_count", 0), 0) > 0:
        return "provisional"
    if _safe_int(summary.get("rankable_offer_count", 0), 0) > 0:
        return "active_rankable"
    return "inactive"


def _build_driver(
    *,
    driver_key: str,
    current_value: float,
    target_value: float,
    unit: str,
    source_field: str,
    comparison: str,
) -> dict[str, Any]:
    return {
        "driver_key": str(driver_key),
        "current_value": float(current_value),
        "target_value": float(target_value),
        "unit": str(unit),
        "source_field": str(source_field),
        "comparison": str(comparison),
    }


def _driver_phrase(driver: Mapping[str, Any]) -> str:
    key = _safe_text(driver.get("driver_key"))
    current_value = _safe_text(driver.get("current_value"))
    target_value = _safe_text(driver.get("target_value"))
    if key and current_value and target_value:
        return f"{key} {current_value} -> {target_value}"
    return ""


def _conditional_subtype(*, data_issue: bool, offer_issue: bool, time_issue: bool) -> str:
    if data_issue:
        return "DATA_ISSUE"
    if offer_issue:
        return "OFFER_GATED"
    if time_issue:
        return "TIME_GATED"
    return "EXECUTION_GATED"


def _map_internal_to_external(internal_status: str) -> str:
    normalized = _safe_text(internal_status).upper()
    if normalized == "NEEDS_REVIEW":
        return "CONDITIONAL"
    if normalized in _VALID_EXTERNAL:
        return normalized
    return "CONDITIONAL"


def _build_rejected_drivers(
    *,
    rejection_type: str,
    best_action_count: int,
    expected_pd_improvement: float,
    realization_anchor: float,
) -> list[dict[str, Any]]:
    if rejection_type == "NO_PATH":
        return [
            _build_driver(
                driver_key="best_action_count",
                current_value=float(best_action_count),
                target_value=1.0,
                unit="count",
                source_field="best_action_count",
                comparison="gte",
            )
        ]
    if rejection_type == "LOW_IMPACT":
        return [
            _build_driver(
                driver_key="expected_pd_improvement",
                current_value=float(expected_pd_improvement),
                target_value=0.01,
                unit="probability_points",
                source_field="expected_pd_improvement",
                comparison="gte",
            )
        ]
    return [
        _build_driver(
            driver_key="realization_anchor",
            current_value=float(realization_anchor),
            target_value=0.20,
            unit="probability",
            source_field="realization_anchor",
            comparison="gte",
        )
    ]


def _build_conditional_drivers(
    *,
    conditional_type: str,
    decision_confidence: float,
    expected_pd_improvement: float,
    realization_anchor: float,
    expected_readiness: str,
    critical_field_null_count: int,
    parity_pass: int,
    parity_mismatch_count: int,
    rankable_offer_count: int,
) -> list[dict[str, Any]]:
    if conditional_type == "DATA_ISSUE":
        drivers: list[dict[str, Any]] = []
        if critical_field_null_count > 0:
            drivers.append(
                _build_driver(
                    driver_key="critical_field_null_count",
                    current_value=float(critical_field_null_count),
                    target_value=0.0,
                    unit="count",
                    source_field="critical_field_null_count",
                    comparison="eq",
                )
            )
        if parity_pass == 0 or parity_mismatch_count > 0:
            drivers.append(
                _build_driver(
                    driver_key="parity_mismatch_count",
                    current_value=float(max(1, parity_mismatch_count)),
                    target_value=0.0,
                    unit="count",
                    source_field="parity_mismatch_count",
                    comparison="eq",
                )
            )
        return drivers
    if conditional_type == "OFFER_GATED":
        return [
            _build_driver(
                driver_key="rankable_offer_count",
                current_value=float(rankable_offer_count),
                target_value=1.0,
                unit="count",
                source_field="rankable_offer_count",
                comparison="gte",
            ),
            _build_driver(
                driver_key="realization_anchor",
                current_value=float(realization_anchor),
                target_value=0.50,
                unit="probability",
                source_field="realization_anchor",
                comparison="gte",
            ),
        ]
    if conditional_type == "TIME_GATED":
        readiness_week = float(_readiness_week(expected_readiness) or 24)
        return [
            _build_driver(
                driver_key="expected_readiness_week",
                current_value=readiness_week,
                target_value=4.0,
                unit="weeks",
                source_field="expected_readiness",
                comparison="lte",
            ),
            _build_driver(
                driver_key="expected_pd_improvement",
                current_value=float(expected_pd_improvement),
                target_value=0.02,
                unit="probability_points",
                source_field="expected_pd_improvement",
                comparison="gte",
            ),
        ]
    return [
        _build_driver(
            driver_key="realization_anchor",
            current_value=float(realization_anchor),
            target_value=0.50,
            unit="probability",
            source_field="realization_anchor",
            comparison="gte",
        ),
        _build_driver(
            driver_key="decision_confidence",
            current_value=float(decision_confidence),
            target_value=0.60,
            unit="score",
            source_field="decision_confidence",
            comparison="gte",
        ),
    ]


def _validated_upgrade_condition(status: str, drivers: list[dict[str, Any]], fallback_text: str | None = None) -> str | None:
    if status != "CONDITIONAL":
        return None
    phrases = [phrase for phrase in (_driver_phrase(driver) for driver in drivers) if phrase]
    if phrases:
        return "; ".join(phrases[:2])
    fallback = _safe_text(fallback_text)
    if any(char.isdigit() for char in fallback):
        return fallback
    return None


def _reason_summary(*, external_status: str, rejection_type: str | None, conditional_type: str | None) -> str:
    if external_status == "APPROVED":
        return "The current plan meets the approval policy under the current evidence."
    if external_status == "REJECTED":
        if rejection_type == "NO_PATH":
            return "No actionable plan is available right now."
        if rejection_type == "LOW_IMPACT":
            return "The current plan would not improve risk enough yet."
        return "The current plan is not realistic enough to rely on."
    if conditional_type == "DATA_ISSUE":
        return "The plan looks directionally viable, but decision data needs controlled review."
    if conditional_type == "OFFER_GATED":
        return "The plan is viable, but institution-side support is not fully active yet."
    if conditional_type == "TIME_GATED":
        return "The plan is viable, but more time is needed before approval."
    return "The plan is viable, but execution confidence is not strong enough yet."


def build_customer_decision_payload(summary: Mapping[str, Any], *, debug_mode: bool = False) -> dict[str, Any]:
    source = dict(summary or {})

    best_action_count = int(_safe_int(source.get("best_action_count", 0), 0))
    zero_step_flag = int(bool(_safe_int(source.get("zero_step_flag", best_action_count == 0), 0)))
    best_plan_id = _safe_text(source.get("best_plan_id"))
    plan_contract_pass = int(
        bool(
            _safe_int(
                source.get("plan_contract_pass", 1 if best_plan_id else 0),
                1 if best_plan_id else 0,
            )
        )
    )
    best_constraint_status = _safe_text(source.get("best_constraint_status"), "valid").lower()

    raw_contract_pass = int(bool(_safe_int(source.get("raw_contract_pass", 0), 0)))
    parity_pass = int(bool(_safe_int(source.get("parity_pass", 1), 1)))
    parity_mismatch_count = int(_safe_int(source.get("parity_mismatch_count", 0), 0))
    critical_field_null_count = int(_safe_int(source.get("critical_field_null_count", 0), 0))
    data_issue_flag = int(bool(_safe_int(source.get("data_issue_flag", 0), 0)))

    plan_execution_probability = _safe_float(source.get("plan_execution_probability", 0.0), 0.0)
    combined_plan_realization_probability = _safe_float(
        source.get("combined_plan_realization_probability", 0.0),
        0.0,
    )
    approval_dependent_plan_probability = _safe_float(
        source.get("approval_dependent_plan_probability", plan_execution_probability),
        plan_execution_probability,
    )
    offer_acceptance_probability = _safe_float(source.get("offer_acceptance_probability", 0.0), 0.0)
    expected_pd_improvement = _safe_float(source.get("expected_pd_improvement", 0.0), 0.0)
    nominal_pd_improvement = _safe_float(source.get("nominal_pd_improvement", 0.0), 0.0)
    local_explainability_confidence = _safe_float(
        source.get("local_explainability_confidence", 0.50),
        0.50,
    )

    expected_readiness = _normalize_readiness(source.get("credit_readiness_stage"))
    checkpoint_status_4w = _safe_text(source.get("checkpoint_status_4w")).lower()
    approval_ready_4w = bool(
        _safe_bool(source.get("approval_ready_4w"), False)
        or checkpoint_status_4w == "pass"
    )
    offer_maturity = _normalize_offer_maturity(source)
    offer_plan = int(bool(_safe_bool(source.get("offer_plan"), False)))
    approval_pending_action_count = int(_safe_int(source.get("approval_pending_action_count", 0), 0))
    rankable_offer_count = int(_safe_int(source.get("rankable_offer_count", 0), 0))

    no_viable_plan = int(best_action_count == 0 or not best_plan_id or plan_contract_pass == 0)
    invalid_best_path = int(best_constraint_status == "invalid" or plan_contract_pass == 0)
    realization_anchor = (
        float(combined_plan_realization_probability)
        if float(combined_plan_realization_probability) > 0.0
        else float(plan_execution_probability)
    )
    strong_execution_flag = int(plan_execution_probability >= 0.50)
    data_issue = bool(
        data_issue_flag
        or raw_contract_pass == 0
        or parity_pass == 0
        or expected_readiness == "unknown_review"
    )

    readiness_component = {
        "now": 1.00,
        "week_4": 1.00,
        "week_12": 0.65,
        "week_24": 0.45,
        "not_ready": 0.20,
        "unknown_review": 0.10,
    }.get(expected_readiness, 0.10)
    impact_component = 0.0 if expected_pd_improvement <= 0 else min(1.0, expected_pd_improvement / 0.05)
    contract_component = 1.00 if raw_contract_pass == 1 and parity_pass == 1 and not data_issue else 0.35
    decision_confidence = round(
        0.35 * realization_anchor
        + 0.25 * readiness_component
        + 0.20 * impact_component
        + 0.10 * local_explainability_confidence
        + 0.10 * contract_component,
        4,
    )
    decision_confidence = _clamp(decision_confidence, 0.0, 1.0)

    reject_gate = bool(
        zero_step_flag == 1
        or no_viable_plan == 1
        or invalid_best_path == 1
        or best_constraint_status == "invalid"
        or expected_pd_improvement < 0.01
        or realization_anchor < 0.10
    )
    approve_gate = bool(
        not reject_gate
        and raw_contract_pass == 1
        and parity_pass == 1
        and not data_issue
        and decision_confidence >= 0.60
        and realization_anchor >= 0.50
        and expected_pd_improvement >= 0.02
        and expected_readiness in {"now", "week_4"}
        and (approval_ready_4w or strong_execution_flag == 1)
        and offer_maturity not in {"inactive", "provisional"}
    )

    offer_issue = offer_maturity in {"inactive", "provisional"}
    time_issue = expected_readiness in {"week_12", "week_24", "not_ready"} or not approval_ready_4w
    conditional_gate = bool(
        not reject_gate
        and not approve_gate
        and best_action_count > 0
        and raw_contract_pass == 1
        and parity_pass == 1
        and not data_issue
        and realization_anchor >= 0.20
        and expected_pd_improvement >= 0.01
        and decision_confidence >= 0.40
    )

    rejection_type: str | None = None
    conditional_type: str | None = None
    decision_reason_primary = ""

    if reject_gate:
        internal_status = "REJECTED"
        if zero_step_flag == 1 or no_viable_plan == 1 or invalid_best_path == 1:
            rejection_type = "NO_PATH"
            decision_reason_primary = "NO_PATH"
        elif expected_pd_improvement < 0.01:
            rejection_type = "LOW_IMPACT"
            decision_reason_primary = "LOW_IMPACT"
        else:
            rejection_type = "LOW_EXECUTION"
            decision_reason_primary = "LOW_EXECUTION"
    elif approve_gate:
        internal_status = "APPROVED"
    elif conditional_gate:
        internal_status = "CONDITIONAL"
        conditional_type = _conditional_subtype(
            data_issue=False,
            offer_issue=offer_issue,
            time_issue=time_issue,
        )
        decision_reason_primary = {
            "DATA_ISSUE": "DATA_ISSUE",
            "OFFER_GATED": "OFFER_BLOCK",
            "TIME_GATED": "TIME_BLOCK",
            "EXECUTION_GATED": "LOW_EXECUTION",
        }[conditional_type]
    else:
        internal_status = "NEEDS_REVIEW"
        conditional_type = _conditional_subtype(
            data_issue=data_issue,
            offer_issue=offer_issue,
            time_issue=time_issue,
        )
        decision_reason_primary = {
            "DATA_ISSUE": "DATA_ISSUE",
            "OFFER_GATED": "OFFER_BLOCK",
            "TIME_GATED": "TIME_BLOCK",
            "EXECUTION_GATED": "LOW_EXECUTION",
        }[conditional_type]

    if internal_status not in _VALID_INTERNAL:
        internal_status = "NEEDS_REVIEW"

    external_status = _map_internal_to_external(internal_status)
    if external_status not in _VALID_EXTERNAL:
        external_status = "CONDITIONAL"
    assert external_status != "NEEDS_REVIEW"

    output_expected_readiness = expected_readiness
    if internal_status == "NEEDS_REVIEW":
        output_expected_readiness = "unknown_review"
    elif external_status == "REJECTED":
        output_expected_readiness = "not_ready"

    if external_status == "REJECTED":
        drivers = _build_rejected_drivers(
            rejection_type=rejection_type or "LOW_EXECUTION",
            best_action_count=best_action_count,
            expected_pd_improvement=expected_pd_improvement,
            realization_anchor=realization_anchor,
        )
    elif external_status == "CONDITIONAL":
        drivers = _build_conditional_drivers(
            conditional_type=conditional_type or "EXECUTION_GATED",
            decision_confidence=decision_confidence,
            expected_pd_improvement=expected_pd_improvement,
            realization_anchor=realization_anchor,
            expected_readiness=output_expected_readiness,
            critical_field_null_count=critical_field_null_count,
            parity_pass=parity_pass,
            parity_mismatch_count=parity_mismatch_count,
            rankable_offer_count=rankable_offer_count,
        )
    else:
        drivers = []
    drivers = drivers[:3]

    data_issue_fallback_text: str | None = None
    if conditional_type == "DATA_ISSUE":
        if critical_field_null_count > 0:
            data_issue_fallback_text = f"critical_field_null_count {critical_field_null_count} -> 0"
        elif parity_mismatch_count > 0:
            data_issue_fallback_text = f"parity_mismatch_count {parity_mismatch_count} -> 0"

    decision_reason_summary = _reason_summary(
        external_status=external_status,
        rejection_type=rejection_type,
        conditional_type=conditional_type,
    )
    upgrade_condition = _validated_upgrade_condition(
        external_status,
        drivers,
        fallback_text=data_issue_fallback_text,
    )

    gate_trace: dict[str, Any] = {
        "reject": bool(reject_gate),
        "approve": bool(approve_gate),
        "conditional": bool(conditional_gate),
        "confidence": float(decision_confidence),
    }
    if debug_mode:
        gate_trace.update(
            {
                "no_viable_plan": bool(no_viable_plan),
                "invalid_best_path": bool(invalid_best_path),
                "data_issue": bool(data_issue),
                "offer_plan": bool(offer_plan),
                "offer_maturity": offer_maturity,
            }
        )

    payload = {
        "decision_status": external_status,
        "decision_status_internal": internal_status,
        "decision_confidence": float(decision_confidence),
        "expected_readiness": output_expected_readiness,
        "decision_reason_summary": decision_reason_summary,
        "decision_reason_primary": decision_reason_primary,
        "decision_reason_drivers": drivers,
        "rejection_type": rejection_type,
        "conditional_type": conditional_type,
        "upgrade_condition": upgrade_condition,
        "realization_anchor": float(realization_anchor),
        "strong_execution_flag": int(strong_execution_flag),
        "offer_maturity": offer_maturity,
        "decision_policy_version": DECISION_POLICY_VERSION,
        "decision_gate_trace": gate_trace,
    }
    return payload
