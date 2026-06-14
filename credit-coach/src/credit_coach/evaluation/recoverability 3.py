from __future__ import annotations

from typing import Any, Iterable, Mapping


DEFAULT_NEAR_UPPER = 0.10
DEFAULT_MID_UPPER = 0.25
RECOVERABILITY_CLASSIFIER_VERSION = "phase_62_v1"
RECOURSE_GATE_VERSION = "phase_63_v1"
NARRATIVE_CONTRACT_VERSION = "phase_66_v1"
HARD_STRUCTURAL_BLOCKERS: tuple[str, ...] = (
    "NO_VALID_WINNER",
    "NO_PATH",
    "HIGH_RISK_DISTANCE",
)
SOFT_STRUCTURAL_BLOCKERS: tuple[str, ...] = (
    "BLOCKED_BY_TIME",
    "BLOCKED_BY_OFFER",
    "LOW_IMPACT",
)
_LONG_HORIZON_READINESS = {
    "week_12",
    "week_24",
    "not_ready",
    "not_ready_yet",
    "unknown_review",
}
_OFFER_BLOCKING_MATURITY = {"inactive", "provisional"}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
    except Exception:
        pass
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _round_metric(value: Any, digits: int = 6) -> float:
    return round(_safe_float(value, 0.0), digits)


def _ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        text = _safe_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered


def resolve_recoverability_thresholds(config: Mapping[str, Any] | None = None) -> dict[str, float]:
    raw = dict(config or {})
    if isinstance(raw.get("risk_band_thresholds"), Mapping):
        raw = dict(raw.get("risk_band_thresholds", {}) or {})
    near_upper = max(0.01, _safe_float(raw.get("near_upper"), DEFAULT_NEAR_UPPER))
    mid_upper = max(near_upper, _safe_float(raw.get("mid_upper"), DEFAULT_MID_UPPER))
    return {
        "near_upper": _round_metric(near_upper),
        "mid_upper": _round_metric(mid_upper),
    }


def compute_approval_gap(*, base_pd: float, tau: float) -> float:
    return _round_metric(max(0.0, _safe_float(base_pd, 0.0) - _safe_float(tau, 0.0)))


def compute_normalized_gap(*, approval_gap: float, mid_upper: float = DEFAULT_MID_UPPER) -> float:
    denominator = max(0.000001, _safe_float(mid_upper, DEFAULT_MID_UPPER))
    return _round_metric(max(0.0, min(1.0, _safe_float(approval_gap, 0.0) / denominator)))


def recoverability_risk_band(*, approval_gap: float, near_upper: float = DEFAULT_NEAR_UPPER, mid_upper: float = DEFAULT_MID_UPPER) -> str:
    gap = _safe_float(approval_gap, 0.0)
    near = max(0.01, _safe_float(near_upper, DEFAULT_NEAR_UPPER))
    mid = max(near, _safe_float(mid_upper, DEFAULT_MID_UPPER))
    if gap <= near:
        return "near"
    if gap <= mid:
        return "mid"
    return "high"


def recoverability_bucket(*, approval_gap: float, near_upper: float = DEFAULT_NEAR_UPPER, mid_upper: float = DEFAULT_MID_UPPER) -> str:
    band = recoverability_risk_band(approval_gap=approval_gap, near_upper=near_upper, mid_upper=mid_upper)
    if band == "near":
        return "near_threshold"
    if band == "mid":
        return "mid_risk"
    return "structural_limited"


def recoverability_score(*, normalized_gap: float) -> float:
    return _round_metric(max(0.0, min(1.0, 1.0 - _safe_float(normalized_gap, 0.0))))


def best_possible_pd_improvement_from_predictions(*, base_pd: float, predicted_pds: Iterable[Any]) -> float:
    best_reachable_pd = _safe_float(base_pd, 0.0)
    found = False
    for value in predicted_pds:
        predicted_pd = _safe_float(value, base_pd)
        if not found or predicted_pd < best_reachable_pd:
            best_reachable_pd = predicted_pd
            found = True
    if not found:
        return 0.0
    return _round_metric(max(0.0, _safe_float(base_pd, 0.0) - best_reachable_pd))


def threshold_reach_possible(*, approval_gap: float, best_possible_pd_improvement: float) -> bool:
    gap = _safe_float(approval_gap, 0.0)
    if gap <= 0.0:
        return True
    return _safe_float(best_possible_pd_improvement, 0.0) >= gap


def build_recoverability_classifier(signal: Mapping[str, Any]) -> dict[str, Any]:
    approval_gap = _safe_float(signal.get("approval_gap"), 0.0)
    bucket = _safe_text(signal.get("recoverability_bucket"))
    has_valid_path = bool(int(_safe_float(signal.get("has_valid_path_flag"), 0)))
    has_rankable_path = bool(int(_safe_float(signal.get("has_rankable_path_flag"), 0)))
    threshold_reachable = bool(signal.get("threshold_reach_possible", False))
    hard_blockers = _ordered_unique(signal.get("hard_structural_blockers", []) or [])
    soft_blockers = _ordered_unique(signal.get("soft_structural_blockers", []) or [])
    hard_blocked = bool(_safe_float(signal.get("hard_structural_blocker_flag"), 0) or hard_blockers)
    soft_blocked = bool(_safe_float(signal.get("soft_structural_blocker_flag"), 0) or soft_blockers)
    within_recoverable_band = approval_gap > 0.0 and bucket == "near_threshold"
    no_active_blockers = not hard_blocked and not soft_blocked
    recoverable_flag = bool(
        within_recoverable_band
        and has_valid_path
        and has_rankable_path
        and threshold_reachable
        and no_active_blockers
    )
    reason_codes = _ordered_unique(
        [
            "WITHIN_RECOVERABLE_BAND" if within_recoverable_band else "OUTSIDE_RECOVERABLE_BAND",
            "HAS_VALID_PATH" if has_valid_path else "NO_VALID_PATH",
            "HAS_RANKABLE_PATH" if has_rankable_path else "NO_RANKABLE_PATH",
            "THRESHOLD_REACHABLE" if threshold_reachable else "THRESHOLD_NOT_REACHABLE",
            "HARD_STRUCTURAL_BLOCK" if hard_blocked else "",
            "SOFT_STRUCTURAL_BLOCK" if soft_blocked else "",
            "NO_ACTIVE_CLASSIFIER_BLOCKERS" if no_active_blockers else "",
            *hard_blockers,
            *soft_blockers,
            "RECOVERABLE" if recoverable_flag else "NOT_RECOVERABLE",
        ]
    )
    return {
        "recoverable_flag": recoverable_flag,
        "recoverable_reason_codes": reason_codes,
        "recoverability_classifier_version": RECOVERABILITY_CLASSIFIER_VERSION,
    }


def build_recourse_gate(signal: Mapping[str, Any]) -> dict[str, Any]:
    recoverable_flag = bool(signal.get("recoverable_flag", False))
    assisted_full_flag = bool(int(_safe_float(signal.get("assisted_full_flag"), 0)))
    assisted_full_mode = (not recoverable_flag) and assisted_full_flag
    return {
        "recourse_mode": "full" if recoverable_flag else ("assisted_full" if assisted_full_mode else "limited"),
        "recommendation_mode": "actionable" if (recoverable_flag or assisted_full_mode) else "informational",
        "recourse_gate_version": RECOURSE_GATE_VERSION,
        "recourse_gate_reason_codes": (
            ["RECOVERABLE_FULL_MODE"]
            if recoverable_flag
            else (["ASSISTED_FULL_MODE"] if assisted_full_mode else ["NOT_RECOVERABLE_LIMITED_MODE"])
        ),
    }


def build_narrative_posture(signal: Mapping[str, Any]) -> dict[str, Any]:
    """
    Phase 66 additive narrative contract:
    - narrative_type: actionable | informational (derived from shipped recourse gate truth)
    - informational_subtype: structural_limited | not_currently_actionable (required when informational)

    The mapping is deterministic and audit-safe; it must not invent actionability in limited mode.
    """

    recourse_mode = _safe_text(signal.get("recourse_mode")).lower()
    recommendation_mode = _safe_text(signal.get("recommendation_mode")).lower()
    recoverable_flag = bool(signal.get("recoverable_flag", False))
    narrative_type = (
        "actionable"
        if recommendation_mode == "actionable" or recourse_mode in {"full", "assisted_full"} or recoverable_flag
        else "informational"
    )

    informational_subtype = ""
    if narrative_type == "informational":
        bucket = _safe_text(signal.get("recoverability_bucket")).lower()
        hard_blocked = bool(_safe_float(signal.get("hard_structural_blocker_flag"), 0.0)) or bool(
            _ordered_unique(signal.get("hard_structural_blockers", []) or [])
        )
        if bucket == "structural_limited" or hard_blocked:
            informational_subtype = "structural_limited"
        else:
            # Includes `mid_risk` and soft-blocked cases.
            informational_subtype = "not_currently_actionable"

    return {
        "narrative_contract_version": NARRATIVE_CONTRACT_VERSION,
        "narrative_type": narrative_type,
        "informational_subtype": informational_subtype,
    }


def build_recoverability_signal(
    *,
    base_pd: float,
    tau: float,
    thresholds: Mapping[str, Any] | None = None,
    has_valid_path_flag: bool = False,
    has_rankable_path_flag: bool = False,
    best_possible_pd_improvement: float = 0.0,
    selection_outcome: str = "",
    expected_readiness: str = "",
    credit_readiness_stage: str = "",
    offer_maturity: str = "",
    offer_plan: bool | int = False,
) -> dict[str, Any]:
    resolved = resolve_recoverability_thresholds(thresholds)
    approval_gap = compute_approval_gap(base_pd=base_pd, tau=tau)
    normalized_gap = compute_normalized_gap(approval_gap=approval_gap, mid_upper=resolved["mid_upper"])
    needs_recourse = approval_gap > 0.0
    reach_possible = threshold_reach_possible(
        approval_gap=approval_gap,
        best_possible_pd_improvement=best_possible_pd_improvement,
    )
    readiness = _safe_text(expected_readiness or credit_readiness_stage).lower()
    offer_maturity_text = _safe_text(offer_maturity, "none").lower()
    selection = _safe_text(selection_outcome).lower()

    hard_codes: list[str] = []
    soft_codes: list[str] = []
    if needs_recourse and selection == "no_valid_winner":
        hard_codes.append("NO_VALID_WINNER")
    if needs_recourse and not bool(has_valid_path_flag):
        hard_codes.append("NO_PATH")
    if approval_gap > resolved["mid_upper"]:
        hard_codes.append("HIGH_RISK_DISTANCE")
    if needs_recourse and bool(has_valid_path_flag) and readiness in _LONG_HORIZON_READINESS:
        soft_codes.append("BLOCKED_BY_TIME")
    if needs_recourse and bool(has_valid_path_flag) and (bool(offer_plan) or offer_maturity_text in _OFFER_BLOCKING_MATURITY):
        soft_codes.append("BLOCKED_BY_OFFER")
    if needs_recourse and bool(has_valid_path_flag) and not reach_possible:
        soft_codes.append("LOW_IMPACT")

    gap_code = {
        "near": "LOW_APPROVAL_GAP",
        "mid": "MID_APPROVAL_GAP",
        "high": "HIGH_APPROVAL_GAP",
    }[
        recoverability_risk_band(
            approval_gap=approval_gap,
            near_upper=resolved["near_upper"],
            mid_upper=resolved["mid_upper"],
        )
    ]
    bucket = recoverability_bucket(
        approval_gap=approval_gap,
        near_upper=resolved["near_upper"],
        mid_upper=resolved["mid_upper"],
    )
    signal_reasons = _ordered_unique(
        [
            gap_code,
            "HAS_VALID_PATH" if bool(has_valid_path_flag) else "NO_VALID_PATH",
            "HAS_RANKABLE_PATH" if bool(has_rankable_path_flag) else "",
            "THRESHOLD_REACHABLE" if reach_possible else "THRESHOLD_NOT_REACHABLE",
            *hard_codes,
            *soft_codes,
            "HARD_STRUCTURAL_BLOCK" if hard_codes else "",
            "SOFT_STRUCTURAL_BLOCK" if soft_codes else "",
            "STRUCTURAL_LIMIT" if bucket == "structural_limited" else "",
        ]
    )
    signal = {
        "approval_gap": approval_gap,
        "normalized_gap": normalized_gap,
        "risk_band": recoverability_risk_band(
            approval_gap=approval_gap,
            near_upper=resolved["near_upper"],
            mid_upper=resolved["mid_upper"],
        ),
        "recoverability_bucket": bucket,
        "recoverability_score": recoverability_score(normalized_gap=normalized_gap),
        "has_valid_path_flag": int(bool(has_valid_path_flag)),
        "has_rankable_path_flag": int(bool(has_rankable_path_flag)),
        "threshold_reach_possible": bool(reach_possible),
        "hard_structural_blocker_flag": int(bool(hard_codes)),
        "soft_structural_blocker_flag": int(bool(soft_codes)),
        "structural_blocker_flag": int(bool(hard_codes or soft_codes)),
        "hard_structural_blockers": list(hard_codes),
        "soft_structural_blockers": list(soft_codes),
        "recoverability_signal_reason_codes": signal_reasons,
    }
    signal.update(build_recoverability_classifier(signal))
    signal.update(build_recourse_gate(signal))
    signal.update(build_narrative_posture(signal))
    return signal
