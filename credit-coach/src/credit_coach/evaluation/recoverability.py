from __future__ import annotations

from typing import Any, Iterable, Mapping


DEFAULT_NEAR_UPPER = 0.10
DEFAULT_MID_UPPER = 0.25
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
    reasons = _ordered_unique(
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
    return {
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
        "recoverable_reason_codes": reasons,
    }
