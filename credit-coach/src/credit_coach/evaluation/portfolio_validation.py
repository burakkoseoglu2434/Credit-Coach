from __future__ import annotations

import json
from collections import Counter
from typing import Any, Mapping, Sequence

import pandas as pd


_CANONICAL_COVERAGE_FIELDS: tuple[str, ...] = (
    "raw_plan_coverage",
    "valid_plan_coverage",
    "governance_safe_plan_coverage",
    "product_ready_plan_coverage",
    "no_plan_rate",
)

_CANONICAL_REALITY_GAP_FLAGS: tuple[str, ...] = (
    "unrealistic_pd_drop_flag",
    "engine_native_action_flag",
    "trivial_or_degenerate_plan_flag",
    "narrative_gap_flag",
    "offer_state_ambiguity_flag",
    "checkpoint_consistency_flag",
    "execution_mismatch_flag",
)

_CRITICAL_REALITY_GAP_FLAGS: frozenset[str] = frozenset(
    {
        "unrealistic_pd_drop_flag",
        "engine_native_action_flag",
        "trivial_or_degenerate_plan_flag",
        "narrative_gap_flag",
        "offer_state_ambiguity_flag",
        "checkpoint_consistency_flag",
    }
)

_TRAJECTORY_CLASS_ORDER: tuple[str, ...] = (
    "early_healthy",
    "delayed_only",
    "unstable",
    "long_horizon_heavy",
    "replan_prone",
)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return int(default)
        if pd.isna(value):
            return int(default)
    except Exception:
        pass
    try:
        return int(value)
    except Exception:
        return int(default)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        if pd.isna(value):
            return float(default)
    except Exception:
        pass
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    text = str(value).strip()
    return text or default


def _round_metric(value: Any, *, digits: int = 6) -> float:
    metric = _safe_float(value, 0.0)
    return round(metric, digits)


def _column_or_default(
    frame: pd.DataFrame,
    column: str,
    *,
    default: Any,
) -> pd.Series:
    if column in frame.columns:
        return frame[column]
    return pd.Series(default, index=frame.index)


def _load_json_list(raw_value: Any) -> list[dict[str, Any]]:
    if isinstance(raw_value, list):
        return [item for item in raw_value if isinstance(item, dict)]
    if not isinstance(raw_value, str) or not raw_value.strip():
        return []
    try:
        payload = json.loads(raw_value)
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _best_steps(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    phases = _load_json_list(row.get("best_phases_json", "[]"))
    phase_steps: list[dict[str, Any]] = []
    for phase in phases:
        steps = phase.get("steps", [])
        if isinstance(steps, list):
            phase_steps.extend(step for step in steps if isinstance(step, dict))
    if phase_steps:
        return phase_steps
    return _load_json_list(row.get("best_timeline_steps_json", "[]"))


def _best_checkpoints(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    checkpoints = _load_json_list(row.get("best_trajectory_checkpoints_json", "[]"))
    if checkpoints:
        return checkpoints
    return [
        {
            "week": 4,
            "predicted_pd": _safe_float(row.get("trajectory_pd_4w"), _safe_float(row.get("base_pd"), 0.0)),
            "gate_pass_estimate": _safe_int(row.get("trajectory_gate_pass_4w"), 0),
        },
        {
            "week": 12,
            "predicted_pd": _safe_float(row.get("trajectory_pd_12w"), _safe_float(row.get("base_pd"), 0.0)),
            "gate_pass_estimate": _safe_int(row.get("trajectory_gate_pass_12w"), 0),
        },
        {
            "week": 24,
            "predicted_pd": _safe_float(row.get("trajectory_pd_24w"), _safe_float(row.get("base_pd"), 0.0)),
            "gate_pass_estimate": _safe_int(row.get("trajectory_gate_pass_24w"), 0),
        },
    ]


def _has_meaningful_action(steps: Sequence[Mapping[str, Any]], row: Mapping[str, Any]) -> bool:
    if any(
        _safe_str(step.get("action_key")) or _safe_str(step.get("action_title")) or _safe_str(step.get("action_class"))
        for step in steps
    ):
        return True
    return _safe_int(row.get("best_action_count"), 0) > 0


def _is_engine_native_action(steps: Sequence[Mapping[str, Any]], row: Mapping[str, Any]) -> bool:
    if not steps:
        return _safe_int(row.get("best_action_count"), 0) > 0
    for step in steps:
        if _safe_str(step.get("action_key")) or _safe_str(step.get("action_title")):
            return False
    return True


def _offer_state(row: Mapping[str, Any], steps: Sequence[Mapping[str, Any]]) -> tuple[str, bool]:
    offer_steps = [
        step
        for step in steps
        if _safe_str(step.get("offer_type"))
        or _safe_str(step.get("action_class")) == "institutional"
        or bool(step.get("requires_institutional_approval"))
        or bool(step.get("requires_acceptance"))
    ]
    if not offer_steps and _safe_int(row.get("best_offer_plan"), 0) == 0:
        return "no_offer", False
    if not offer_steps and _safe_int(row.get("best_offer_plan"), 0) == 1:
        if _safe_str(row.get("best_offer_type")):
            if _safe_int(row.get("best_rankable_offer"), 0) == 1:
                return "offer", False
            return "requires_approval", False
        return "unknown", True

    requires_approval = any(
        bool(step.get("requires_institutional_approval"))
        or _safe_str(step.get("institutional_approval_state")) in {"pending", "unknown"}
        or bool(step.get("approval_pending_semantic_only"))
        for step in offer_steps
    )
    requires_acceptance = any(bool(step.get("requires_acceptance")) for step in offer_steps)
    has_offer_type = any(_safe_str(step.get("offer_type")) for step in offer_steps) or bool(_safe_str(row.get("best_offer_type")))
    terms_complete = any(bool(step.get("offer_terms_complete")) for step in offer_steps) or _safe_int(
        row.get("best_rankable_offer"), 0
    ) == 1

    if not has_offer_type:
        return "unknown", True
    if requires_approval:
        return "requires_approval", False
    if requires_acceptance:
        return "requires_acceptance", False
    if _safe_int(row.get("best_offer_plan"), 0) == 1 and not terms_complete and _safe_int(row.get("best_rankable_offer"), 0) == 0:
        return "unknown", True
    return "offer", False


def _has_checkpoint_narrative(checkpoints: Sequence[Mapping[str, Any]]) -> bool:
    checkpoint_weeks = {_safe_int(checkpoint.get("week"), 0) for checkpoint in checkpoints}
    return 4 in checkpoint_weeks and 12 in checkpoint_weeks


def _checkpoint_consistency_flag(row: Mapping[str, Any], checkpoints: Sequence[Mapping[str, Any]]) -> bool:
    pd_4w = _safe_float(row.get("trajectory_pd_4w"), _safe_float(row.get("base_pd"), 0.0))
    pd_12w = _safe_float(row.get("trajectory_pd_12w"), _safe_float(row.get("base_pd"), 0.0))
    pd_24w = _safe_float(row.get("trajectory_pd_24w"), _safe_float(row.get("base_pd"), 0.0))
    pass_4w = _safe_int(row.get("trajectory_gate_pass_4w"), 0)
    pass_12w = _safe_int(row.get("trajectory_gate_pass_12w"), 0)
    pass_24w = _safe_int(row.get("trajectory_gate_pass_24w"), 0)
    soft_regression_penalty = _safe_float(row.get("trajectory_soft_regression_penalty"), 0.0)
    if soft_regression_penalty > 0.02:
        return True
    if pass_4w > pass_12w or pass_12w > pass_24w:
        return True
    if pd_12w > pd_4w + 0.02 or pd_24w > pd_12w + 0.02:
        return True
    if not _has_checkpoint_narrative(checkpoints):
        return True
    return False


def _degenerate_plan_flag(row: Mapping[str, Any], steps: Sequence[Mapping[str, Any]]) -> bool:
    action_count = _safe_int(row.get("best_action_count"), 0)
    if action_count <= 0 and not steps and _safe_int(row.get("best_offer_plan"), 0) == 0:
        return True
    if action_count <= 0 and _safe_int(row.get("best_rankable_offer"), 0) == 0:
        return True
    nominal_improvement = _safe_float(row.get("best_nominal_pd_improvement"), 0.0)
    expected_improvement = _safe_float(row.get("best_expected_pd_improvement"), 0.0)
    return nominal_improvement <= 1e-6 and expected_improvement <= 1e-6 and _safe_int(row.get("best_rankable_offer"), 0) == 0


def _reality_gap_flags(
    row: Mapping[str, Any],
    *,
    steps: Sequence[Mapping[str, Any]],
    checkpoints: Sequence[Mapping[str, Any]],
    offer_state: str,
    offer_state_ambiguous: bool,
) -> dict[str, int]:
    base_pd = _safe_float(row.get("base_pd"), 0.0)
    nominal_improvement = _safe_float(row.get("best_nominal_pd_improvement"), 0.0)
    expected_improvement = _safe_float(row.get("best_expected_pd_improvement"), 0.0)
    plan_execution_probability = _safe_float(row.get("best_plan_execution_probability"), 0.0)
    combined_realization = _safe_float(
        row.get("best_combined_plan_realization_probability"),
        plan_execution_probability,
    )
    action_count = max(0, _safe_int(row.get("best_action_count"), 0))
    feature_count = len(
        {
            _safe_str(step.get("feature_name"))
            for step in steps
            if _safe_str(step.get("feature_name"))
        }
    )
    early_progress = max(0.0, base_pd - _safe_float(row.get("trajectory_pd_4w"), base_pd))
    low_burden = action_count <= 1 or feature_count <= 1 or _safe_float(row.get("best_cost_usd"), 0.0) <= 25.0
    large_improvement = nominal_improvement >= 0.15 or expected_improvement >= 0.10
    checkpoint_support_weak = early_progress < min(0.02, max(0.01, nominal_improvement * 0.30))
    local_global_gap = feature_count <= 1 and nominal_improvement >= 0.12
    degenerate_flag = _degenerate_plan_flag(row, steps)
    engine_native = _is_engine_native_action(steps, row)
    narrative_gap = not _has_checkpoint_narrative(checkpoints)
    checkpoint_consistency = _checkpoint_consistency_flag(row, checkpoints)
    execution_mismatch = (
        nominal_improvement >= 0.05
        and (
            plan_execution_probability < 0.45
            or (_safe_int(row.get("best_offer_plan"), 0) == 1 and combined_realization < 0.25)
        )
    )

    return {
        "unrealistic_pd_drop_flag": int(large_improvement and low_burden and (checkpoint_support_weak or local_global_gap)),
        "engine_native_action_flag": int(engine_native),
        "trivial_or_degenerate_plan_flag": int(degenerate_flag),
        "narrative_gap_flag": int(narrative_gap),
        "offer_state_ambiguity_flag": int(offer_state_ambiguous or offer_state == "unknown"),
        "checkpoint_consistency_flag": int(checkpoint_consistency),
        "execution_mismatch_flag": int(execution_mismatch),
    }


def _critical_reality_gap_count(flags: Mapping[str, int]) -> int:
    return int(sum(int(flags.get(flag, 0)) for flag in _CRITICAL_REALITY_GAP_FLAGS))


def _flag_severity(flags: Mapping[str, int]) -> str:
    total_flags = int(sum(int(value) for value in flags.values()))
    critical_count = _critical_reality_gap_count(flags)
    if total_flags <= 0:
        return "none"
    if critical_count >= 2 or total_flags >= 4:
        return "severe"
    if critical_count >= 1 or total_flags >= 2:
        return "moderate"
    return "mild"


def _reliability_threshold(
    reliability_threshold_by_risk_band: Mapping[str, float] | None,
    risk_band: str,
) -> float:
    if not reliability_threshold_by_risk_band:
        return 0.0
    key = _safe_str(risk_band, "default").lower()
    if key in reliability_threshold_by_risk_band:
        return _safe_float(reliability_threshold_by_risk_band[key], 0.0)
    return _safe_float(reliability_threshold_by_risk_band.get("default"), 0.0)


def _trajectory_class(row: Mapping[str, Any]) -> str:
    status = _safe_str(row.get("trajectory_status"), "degraded")
    policy_label = _safe_str(row.get("trajectory_policy_label"))
    gate_4w = _safe_int(row.get("trajectory_gate_pass_4w"), 0)
    gate_12w = _safe_int(row.get("trajectory_gate_pass_12w"), 0)
    gate_24w = _safe_int(row.get("trajectory_gate_pass_24w"), 0)
    soft_regression_penalty = _safe_float(row.get("trajectory_soft_regression_penalty"), 0.0)
    transition_reason = _safe_str(row.get("trajectory_phase_transition_reason")).lower()

    if status == "needs_replan" or "replan" in transition_reason:
        return "replan_prone"
    if soft_regression_penalty > 0.02:
        return "unstable"
    if gate_4w == 1:
        return "early_healthy"
    if policy_label == "long_horizon_heavy" or (gate_4w == 0 and gate_12w == 0 and gate_24w == 1):
        return "long_horizon_heavy"
    if gate_4w == 0 and (gate_12w == 1 or gate_24w == 1):
        return "delayed_only"
    if status == "degraded":
        return "replan_prone"
    return "long_horizon_heavy"


def _recoverability_segment(row: Mapping[str, Any]) -> str:
    valid_plan = bool(row.get("_valid_plan", False))
    plan_execution_probability = _safe_float(row.get("best_plan_execution_probability"), 0.0)
    gate_4w = _safe_int(row.get("trajectory_gate_pass_4w"), 0)
    gate_12w = _safe_int(row.get("trajectory_gate_pass_12w"), 0)
    gate_24w = _safe_int(row.get("trajectory_gate_pass_24w"), 0)
    best_status = _safe_str(row.get("best_status"))

    if valid_plan and best_status == "APPROVED" and gate_4w == 1 and plan_execution_probability >= 0.55:
        return "approved_like"
    if valid_plan and (gate_12w == 1 or gate_24w == 1 or _safe_float(row.get("best_expected_pd_improvement"), 0.0) >= 0.05):
        return "recoverable"
    return "hard_to_recover"


def _offer_needed_segment(row: Mapping[str, Any]) -> str:
    return "offer_needed" if _safe_int(row.get("best_offer_plan"), 0) == 1 else "no_offer_needed"


def _segment_axes(work: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "risk_band": work["risk_band"].astype(str),
        "income_band": work["income_band"].astype(str),
        "stress_band": work["stress_band"].astype(str),
        "recoverability_segment": work["recoverability_segment"].astype(str),
        "offer_needed_segment": work["offer_needed_segment"].astype(str),
    }


def _coverage_reason_rows(work: pd.DataFrame, *, transition: str) -> pd.DataFrame:
    columns = ["population", "transition", "reason", "count", "share_of_source"]
    if work.empty:
        return pd.DataFrame(columns=columns)
    reason_counts = work["drop_reason"].fillna("").astype(str).value_counts()
    rows = []
    for reason, count in reason_counts.items():
        if not reason:
            continue
        rows.append(
            {
                "population": "full_evaluation_population",
                "transition": transition,
                "reason": reason,
                "count": int(count),
                "share_of_source": _round_metric(float(count) / max(1, len(work))),
            }
        )
    return pd.DataFrame(rows, columns=columns)


def _segment_breakdown(work: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "population",
        "segment_axis",
        "segment_value",
        "count",
        "share",
        "raw_plan_coverage",
        "valid_plan_coverage",
        "governance_safe_plan_coverage",
        "product_ready_plan_coverage",
        "reality_gap_flag_rate",
        "offer_plan_rate",
        "rankable_offer_rate",
        "governance_safe_offer_rate",
        "mean_plan_execution_probability",
        "mean_nominal_pd_improvement",
        "execution_weighted_expected_improvement",
        "early_healthy_rate",
        "delayed_only_rate",
        "long_horizon_heavy_rate",
        "replan_prone_rate",
    ]
    if work.empty:
        return pd.DataFrame(columns=columns)

    rows: list[dict[str, Any]] = []
    total = max(1, len(work))
    for axis_name, values in _segment_axes(work).items():
        for segment_value, frame in work.groupby(values, dropna=False):
            segment_value_str = _safe_str(segment_value, "unknown")
            rows.append(
                {
                    "population": "full_evaluation_population",
                    "segment_axis": axis_name,
                    "segment_value": segment_value_str,
                    "count": int(len(frame)),
                    "share": _round_metric(float(len(frame)) / float(total)),
                    "raw_plan_coverage": _round_metric(frame["_raw_plan"].astype(float).mean()),
                    "valid_plan_coverage": _round_metric(frame["_valid_plan"].astype(float).mean()),
                    "governance_safe_plan_coverage": _round_metric(frame["_governance_safe_plan"].astype(float).mean()),
                    "product_ready_plan_coverage": _round_metric(frame["_product_ready_plan"].astype(float).mean()),
                    "reality_gap_flag_rate": _round_metric(frame["_has_reality_gap"].astype(float).mean()),
                    "offer_plan_rate": _round_metric(frame["best_offer_plan"].astype(float).mean()),
                    "rankable_offer_rate": _round_metric(frame["best_rankable_offer"].astype(float).mean()),
                    "governance_safe_offer_rate": _round_metric(frame["best_governance_safe_offer"].astype(float).mean()),
                    "mean_plan_execution_probability": _round_metric(
                        pd.to_numeric(frame["best_plan_execution_probability"], errors="coerce").fillna(0.0).mean()
                    ),
                    "mean_nominal_pd_improvement": _round_metric(
                        pd.to_numeric(frame["best_nominal_pd_improvement"], errors="coerce").fillna(0.0).mean()
                    ),
                    "execution_weighted_expected_improvement": _round_metric(
                        pd.to_numeric(frame["best_expected_pd_improvement"], errors="coerce").fillna(0.0).mean()
                    ),
                    "early_healthy_rate": _round_metric((frame["trajectory_class"] == "early_healthy").astype(float).mean()),
                    "delayed_only_rate": _round_metric((frame["trajectory_class"] == "delayed_only").astype(float).mean()),
                    "long_horizon_heavy_rate": _round_metric(
                        (frame["trajectory_class"] == "long_horizon_heavy").astype(float).mean()
                    ),
                    "replan_prone_rate": _round_metric((frame["trajectory_class"] == "replan_prone").astype(float).mean()),
                }
            )
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["segment_axis", "product_ready_plan_coverage", "count", "segment_value"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)


def _select_segment_label(row: pd.Series) -> str:
    return f"{_safe_str(row.get('segment_axis'))}:{_safe_str(row.get('segment_value'))}"


def _top_segment_rows(segment_breakdown: pd.DataFrame, *, ascending: bool, top_n: int = 2) -> list[dict[str, Any]]:
    if segment_breakdown.empty:
        return []
    filtered = segment_breakdown[segment_breakdown["count"].astype(int) >= 5].copy()
    if filtered.empty:
        filtered = segment_breakdown.copy()
    sorted_rows = filtered.sort_values(
        ["product_ready_plan_coverage", "governance_safe_plan_coverage", "count"],
        ascending=[ascending, ascending, False],
    ).head(top_n)
    results: list[dict[str, Any]] = []
    for _, row in sorted_rows.iterrows():
        results.append(
            {
                "segment_axis": _safe_str(row.get("segment_axis")),
                "segment_value": _safe_str(row.get("segment_value")),
                "segment_label": _select_segment_label(row),
                "product_ready_plan_coverage": _safe_float(row.get("product_ready_plan_coverage")),
                "governance_safe_plan_coverage": _safe_float(row.get("governance_safe_plan_coverage")),
                "count": _safe_int(row.get("count")),
            }
        )
    return results


def _segment_extreme(segment_breakdown: pd.DataFrame, *, metric: str, highest: bool) -> dict[str, Any]:
    if segment_breakdown.empty or metric not in segment_breakdown.columns:
        return {}
    filtered = segment_breakdown[segment_breakdown["count"].astype(int) >= 5].copy()
    if filtered.empty:
        filtered = segment_breakdown.copy()
    ordered = filtered.sort_values([metric, "count"], ascending=[not highest, False]).head(1)
    if ordered.empty:
        return {}
    row = ordered.iloc[0]
    return {
        "segment_axis": _safe_str(row.get("segment_axis")),
        "segment_value": _safe_str(row.get("segment_value")),
        "segment_label": _select_segment_label(row),
        metric: _safe_float(row.get(metric)),
        "count": _safe_int(row.get("count")),
    }


def _build_demo_representativeness(
    work: pd.DataFrame,
    *,
    demo_case: Mapping[str, Any] | None,
) -> dict[str, Any]:
    empty = {
        "demo_representativeness_verdict": "misleading",
        "demo_fit_confidence": "weak",
        "demo_case_segment": "",
        "segment_size": 0,
        "demo_case_segment_share": 0.0,
        "segment_product_ready_rate": 0.0,
        "segment_offer_dependency": 0.0,
        "cohort_vs_demo_delta": {
            "plan_execution_probability": 0.0,
            "early_checkpoint_health_rate": 0.0,
            "product_ready_rate": 0.0,
        },
        "product_ready_alignment": False,
        "segment_product_ready_alignment_score": 0.0,
        "narrative": "demo is not representative of portfolio behavior",
    }
    if work.empty or not isinstance(demo_case, Mapping):
        return empty

    customer = demo_case.get("customer", {}) if isinstance(demo_case.get("customer", {}), Mapping) else {}
    summary = demo_case.get("summary", {}) if isinstance(demo_case.get("summary", {}), Mapping) else {}
    checkpoints = demo_case.get("checkpoints", []) if isinstance(demo_case.get("checkpoints", []), list) else []

    demo_risk_band = _safe_str(customer.get("risk_band"), "unknown")
    demo_income_band = _safe_str(customer.get("income_band"), "unknown")
    demo_stress_band = _safe_str(customer.get("stress_band"), "base")
    demo_offer_needed = "offer_needed" if _safe_float(summary.get("offer_acceptance_probability"), 0.0) > 0 else "no_offer_needed"
    demo_recoverability = "hard_to_recover"
    if bool(summary.get("approval_ready_4w")) or (
        _safe_str(summary.get("decision_status")) == "APPROVED" and _safe_str(summary.get("credit_readiness_stage")) in {"now", "week_4"}
    ):
        demo_recoverability = "approved_like"
    elif bool(summary.get("approval_ready_12w")) or bool(summary.get("approval_ready_24w")):
        demo_recoverability = "recoverable"

    anchor_mask = (
        (work["risk_band"].astype(str) == demo_risk_band)
        & (work["income_band"].astype(str) == demo_income_band)
        & (work["stress_band"].astype(str) == demo_stress_band)
        & (work["recoverability_segment"].astype(str) == demo_recoverability)
    )
    segment_frame = work[anchor_mask].copy()
    segment_size = int(len(segment_frame))
    segment_share = float(segment_size / max(1, len(work)))
    segment_product_ready_rate = float(segment_frame["_product_ready_plan"].astype(float).mean()) if not segment_frame.empty else 0.0
    segment_offer_dependency = float(
        (segment_frame["offer_needed_segment"].astype(str) == "offer_needed").astype(float).mean()
    ) if not segment_frame.empty else 0.0

    cohort_execution_probability = float(pd.to_numeric(work["best_plan_execution_probability"], errors="coerce").fillna(0.0).mean())
    cohort_early_health = float((work["trajectory_class"] == "early_healthy").astype(float).mean())
    cohort_product_ready = float(work["_product_ready_plan"].astype(float).mean())

    demo_execution_probability = _safe_float(summary.get("plan_execution_probability"), 0.0)
    demo_early_health = 1.0 if any(
        _safe_int(checkpoint.get("week"), 0) == 4 and bool(checkpoint.get("approval_ready"))
        for checkpoint in checkpoints
        if isinstance(checkpoint, Mapping)
    ) else float(bool(summary.get("approval_ready_4w")))
    demo_product_ready = bool(_safe_str(summary.get("decision_status")) == "APPROVED" and bool(demo_case.get("phases")))

    delta = {
        "plan_execution_probability": _round_metric(demo_execution_probability - cohort_execution_probability),
        "early_checkpoint_health_rate": _round_metric(float(demo_early_health) - cohort_early_health),
        "product_ready_rate": _round_metric(float(demo_product_ready) - cohort_product_ready),
    }
    alignment_score = 1.0 - min(1.0, abs(float(demo_product_ready) - segment_product_ready_rate))
    product_ready_alignment = alignment_score >= 0.75
    largest_gap = max(abs(float(value)) for value in delta.values())

    confidence = "weak"
    if segment_size >= 100:
        confidence = "strong"
    elif segment_size >= 30:
        confidence = "moderate"

    verdict = "representative"
    if not product_ready_alignment:
        verdict = "misleading"
    elif segment_share <= 0.20:
        verdict = "narrow"
    elif largest_gap > 0.25:
        verdict = "misleading"
    elif largest_gap > 0.10:
        verdict = "optimistic"

    narrative = {
        "representative": "demo aligns with cohort",
        "optimistic": "demo overstates portfolio reality",
        "narrow": "demo reflects a narrow segment",
        "misleading": "demo is not representative of portfolio behavior",
    }[verdict]

    return {
        "demo_representativeness_verdict": verdict,
        "demo_fit_confidence": confidence,
        "demo_case_segment": (
            f"risk_band={demo_risk_band}|income_band={demo_income_band}|stress_band={demo_stress_band}|"
            f"recoverability_segment={demo_recoverability}"
        ),
        "segment_size": segment_size,
        "demo_case_segment_share": _round_metric(segment_share),
        "segment_product_ready_rate": _round_metric(segment_product_ready_rate),
        "segment_offer_dependency": _round_metric(segment_offer_dependency),
        "cohort_vs_demo_delta": delta,
        "product_ready_alignment": bool(product_ready_alignment),
        "segment_product_ready_alignment_score": _round_metric(alignment_score),
        "narrative": narrative,
    }


def _render_portfolio_validation_review(summary: Mapping[str, Any]) -> str:
    strongest_segments = summary.get("strongest_segments", [])
    weakest_segments = summary.get("weakest_segments", [])
    demo_fit = summary.get("demo_representativeness", {})
    coverage = summary.get("canonical_metrics", {})
    reality_gap = summary.get("reality_gap_summary", {})
    segment_story = summary.get("segment_story", {})
    lines = [
        "# Portfolio Validation Review",
        "",
        "## Coverage Funnel",
        (
            f"- Raw -> Valid -> Governance-safe -> Product-ready: "
            f"{_safe_float(coverage.get('raw_plan_coverage')):.1%} -> "
            f"{_safe_float(coverage.get('valid_plan_coverage')):.1%} -> "
            f"{_safe_float(coverage.get('governance_safe_plan_coverage')):.1%} -> "
            f"{_safe_float(coverage.get('product_ready_plan_coverage')):.1%}"
        ),
        f"- No plan rate: {_safe_float(coverage.get('no_plan_rate')):.1%}",
        "",
        "## Reality Gap",
        f"- Flag rate: {_safe_float(reality_gap.get('reality_gap_flag_rate')):.1%}",
        f"- Dominant reason: {_safe_str(reality_gap.get('dominant_reality_gap_reason'), 'none')}",
        (
            f"- Product-ready drop due to reality gap: "
            f"{_safe_float(reality_gap.get('product_ready_drop_due_to_reality_gap')):.1%}"
        ),
        "",
        "## Segment Story",
        f"- Where engine works: {_safe_str(segment_story.get('where_engine_works'), 'n/a')}",
        f"- Where engine struggles: {_safe_str(segment_story.get('where_engine_struggles'), 'n/a')}",
        f"- Where offer is required: {_safe_str(segment_story.get('where_offer_is_required'), 'n/a')}",
        f"- Where narrative breaks: {_safe_str(segment_story.get('where_narrative_breaks'), 'n/a')}",
        "",
        "## Strongest Segments",
    ]
    if strongest_segments:
        for segment in strongest_segments:
            lines.append(
                f"- {segment['segment_label']}: product-ready {_safe_float(segment.get('product_ready_plan_coverage')):.1%}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Weakest Segments"])
    if weakest_segments:
        for segment in weakest_segments:
            lines.append(
                f"- {segment['segment_label']}: product-ready {_safe_float(segment.get('product_ready_plan_coverage')):.1%}"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Demo Fit",
            f"- Verdict: {_safe_str(demo_fit.get('demo_representativeness_verdict'), 'misleading')}",
            f"- Confidence: {_safe_str(demo_fit.get('demo_fit_confidence'), 'weak')}",
            f"- Segment share: {_safe_float(demo_fit.get('demo_case_segment_share')):.1%}",
            f"- Product-ready alignment: {'yes' if bool(demo_fit.get('product_ready_alignment')) else 'no'}",
            f"- Narrative: {_safe_str(demo_fit.get('narrative'), 'demo is not representative of portfolio behavior')}",
        ]
    )
    return "\n".join(lines) + "\n"


def _dominant_reality_gap_reason(work: pd.DataFrame) -> str:
    if work.empty:
        return ""
    focus = work[work["_governance_safe_plan"].astype(int) == 1].copy()
    if focus.empty:
        focus = work[work["_valid_plan"].astype(int) == 1].copy()
    if focus.empty:
        focus = work.copy()
    reality_gap_counts = {
        flag: int(focus[flag].astype(int).sum())
        for flag in _CANONICAL_REALITY_GAP_FLAGS
        if flag in focus.columns
    }
    if not reality_gap_counts:
        return ""
    dominant_reason, dominant_count = max(reality_gap_counts.items(), key=lambda item: (item[1], item[0]))
    if dominant_count <= 0:
        return ""
    return dominant_reason


def build_portfolio_validation_artifacts(
    batch_df: pd.DataFrame,
    *,
    tau: float,
    reliability_threshold_by_risk_band: Mapping[str, float] | None = None,
    demo_case: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    supporting_artifacts = {
        "portfolio_validation_summary_json": "tables/portfolio_validation_summary.json",
        "portfolio_coverage_breakdown_csv": "tables/portfolio_coverage_breakdown.csv",
        "portfolio_coverage_drop_breakdown_csv": "tables/portfolio_coverage_drop_breakdown.csv",
        "portfolio_reality_gap_breakdown_csv": "tables/portfolio_reality_gap_breakdown.csv",
        "portfolio_segment_breakdown_csv": "tables/portfolio_segment_breakdown.csv",
        "portfolio_offer_diagnostics_csv": "tables/portfolio_offer_diagnostics.csv",
        "portfolio_behavior_comparison_csv": "tables/portfolio_behavior_comparison.csv",
        "portfolio_trajectory_class_breakdown_csv": "tables/portfolio_trajectory_class_breakdown.csv",
        "demo_representativeness_summary_json": "tables/demo_representativeness_summary.json",
        "portfolio_validation_review_md": "tables/portfolio_validation_review.md",
    }
    if batch_df is None or batch_df.empty:
        empty_summary = {
            "canonical_population": "full_evaluation_population",
            "secondary_population": "denied",
            "population_sizes": {
                "full_evaluation_population": 0,
                "denied": 0,
                "high_risk_denied": 0,
            },
            "canonical_metrics": {field: 0.0 for field in _CANONICAL_COVERAGE_FIELDS},
            "secondary_metrics": {field: 0.0 for field in _CANONICAL_COVERAGE_FIELDS},
            "reality_gap_summary": {
                "reality_gap_flag_rate": 0.0,
                "dominant_reality_gap_reason": "",
                "product_ready_drop_due_to_reality_gap": 0.0,
                "multi_flag_exposure": 0.0,
                "severity_split": {"mild": 0.0, "moderate": 0.0, "severe": 0.0},
            },
            "strongest_segments": [],
            "weakest_segments": [],
            "segment_story": {
                "where_engine_works": "",
                "where_engine_struggles": "",
                "where_offer_is_required": "",
                "where_narrative_breaks": "",
            },
            "demo_representativeness": _build_demo_representativeness(pd.DataFrame(), demo_case=demo_case),
            "supporting_artifacts": supporting_artifacts,
        }
        return {
            "summary": empty_summary,
            "coverage_breakdown": pd.DataFrame(columns=["population", "funnel_stage", "count", "share"]),
            "coverage_drop_breakdown": pd.DataFrame(
                columns=["population", "transition", "reason", "count", "share_of_source"]
            ),
            "reality_gap_breakdown": pd.DataFrame(
                columns=["population", "flag", "count", "share", "severity", "severity_share", "breakdown_type"]
            ),
            "segment_breakdown": pd.DataFrame(),
            "offer_diagnostics": pd.DataFrame(),
            "behavior_comparison": pd.DataFrame(),
            "trajectory_class_breakdown": pd.DataFrame(),
            "demo_representativeness": empty_summary["demo_representativeness"],
            "review_markdown": _render_portfolio_validation_review(empty_summary),
        }

    work = batch_df.copy(deep=True)
    work["risk_band"] = _column_or_default(work, "risk_band", default="unknown").fillna("unknown").astype(str)
    work["income_band"] = _column_or_default(work, "income_band", default="unknown").fillna("unknown").astype(str)
    work["stress_band"] = _column_or_default(work, "stress_band", default="base").fillna("base").astype(str)
    work["fairness_guard_demoted"] = pd.to_numeric(
        _column_or_default(work, "fairness_guard_demoted", default=0),
        errors="coerce",
    ).fillna(0).astype(int)

    row_records: list[dict[str, Any]] = []
    for row in work.to_dict(orient="records"):
        steps = _best_steps(row)
        checkpoints = _best_checkpoints(row)
        raw_plan = _safe_int(row.get("had_any_candidate"), 0) == 1 and bool(_safe_str(row.get("best_plan_id")))
        degenerate_flag = _degenerate_plan_flag(row, steps)
        best_status = _safe_str(row.get("best_status"), "ERROR").upper()
        constraint_status = _safe_str(row.get("best_constraint_status"), "invalid").lower()
        non_rejected = raw_plan and best_status not in {"REJECTED", "ERROR"}
        feasible_or_repaired = constraint_status in {"valid", "repaired"}
        rankable = raw_plan and bool(_safe_str(row.get("best_plan_id"))) and _safe_int(row.get("candidate_pool_count"), 0) > 0
        provisional_only = constraint_status == "provisional"
        valid_plan = bool(non_rejected and feasible_or_repaired and rankable and not provisional_only and not degenerate_flag)

        risk_band = _safe_str(row.get("risk_band"), "default")
        reliability_threshold = _reliability_threshold(reliability_threshold_by_risk_band, risk_band)
        reliability_issue = (
            _safe_float(row.get("best_ci_high"), tau + 1.0) > float(tau)
            or _safe_float(row.get("best_reliability"), -1.0) < float(reliability_threshold)
            or _safe_float(row.get("best_worst_risk_margin"), -1.0) < 0.0
        )
        trajectory_class = _trajectory_class(row)
        trajectory_instability = trajectory_class in {"unstable", "replan_prone"} or _safe_str(row.get("trajectory_status")) == "degraded"
        governance_safe = bool(valid_plan and _safe_int(row.get("fairness_guard_demoted"), 0) == 0 and not reliability_issue and not trajectory_instability)

        offer_state, offer_state_ambiguous = _offer_state(row, steps)
        flags = _reality_gap_flags(
            row,
            steps=steps,
            checkpoints=checkpoints,
            offer_state=offer_state,
            offer_state_ambiguous=offer_state_ambiguous,
        )
        critical_gap = any(flag in _CRITICAL_REALITY_GAP_FLAGS and int(value) == 1 for flag, value in flags.items())
        product_ready = bool(
            governance_safe
            and _has_meaningful_action(steps, row)
            and not critical_gap
            and offer_state != "unknown"
            and not _is_engine_native_action(steps, row)
            and _has_checkpoint_narrative(checkpoints)
        )

        row_records.append(
            {
                **row,
                "offer_state": offer_state,
                "trajectory_class": trajectory_class,
                "recoverability_segment": _recoverability_segment({**row, "_valid_plan": valid_plan}),
                "offer_needed_segment": _offer_needed_segment(row),
                "_raw_plan": int(raw_plan),
                "_valid_plan": int(valid_plan),
                "_governance_safe_plan": int(governance_safe),
                "_product_ready_plan": int(product_ready),
                "_has_reality_gap": int(any(int(value) == 1 for value in flags.values())),
                "_reality_gap_severity": _flag_severity(flags),
                **flags,
            }
        )

    work = pd.DataFrame(row_records)

    work["drop_reason_raw_to_valid"] = ""
    raw_not_valid = work[(work["_raw_plan"] == 1) & (work["_valid_plan"] == 0)].copy()
    if not raw_not_valid.empty:
        raw_not_valid.loc[:, "drop_reason"] = raw_not_valid.apply(
            lambda row: (
                "rejected"
                if _safe_str(row.get("best_status"), "ERROR").upper() in {"REJECTED", "ERROR"}
                or _safe_str(row.get("best_constraint_status"), "").lower() == "provisional"
                else "infeasible"
                if _safe_str(row.get("best_constraint_status"), "").lower() not in {"valid", "repaired"}
                else "degenerate"
            ),
            axis=1,
        )
    valid_not_governance = work[(work["_valid_plan"] == 1) & (work["_governance_safe_plan"] == 0)].copy()
    if not valid_not_governance.empty:
        valid_not_governance.loc[:, "drop_reason"] = valid_not_governance.apply(
            lambda row: (
                "fairness"
                if _safe_int(row.get("fairness_guard_demoted"), 0) == 1
                else "reliability"
                if (
                    _safe_float(row.get("best_ci_high"), tau + 1.0) > float(tau)
                    or _safe_float(row.get("best_worst_risk_margin"), -1.0) < 0.0
                    or _safe_float(
                        row.get("best_reliability"),
                        -1.0,
                    )
                    < _reliability_threshold(reliability_threshold_by_risk_band, _safe_str(row.get("risk_band"), "default"))
                )
                else "trajectory_instability"
            ),
            axis=1,
        )
    governance_not_product = work[(work["_governance_safe_plan"] == 1) & (work["_product_ready_plan"] == 0)].copy()
    if not governance_not_product.empty:
        governance_not_product.loc[:, "drop_reason"] = governance_not_product.apply(
            lambda row: (
                "action_not_interpretable"
                if _safe_int(row.get("engine_native_action_flag"), 0) == 1
                else "narrative_missing"
                if _safe_int(row.get("narrative_gap_flag"), 0) == 1
                else "offer_unclear"
                if _safe_int(row.get("offer_state_ambiguity_flag"), 0) == 1
                else "reality_gap_flags"
            ),
            axis=1,
        )
    if "drop_reason" not in governance_not_product.columns:
        governance_not_product = governance_not_product.assign(
            drop_reason=pd.Series("", index=governance_not_product.index, dtype="object")
        )

    total = max(1, len(work))
    denied_rows = work[work["denied_base"].astype(int) == 1].copy()
    high_risk_denied_rows = denied_rows[denied_rows["risk_band"].astype(str).str.lower() == "high"].copy()

    def _coverage_metrics(frame: pd.DataFrame) -> dict[str, float]:
        if frame.empty:
            return {field: 0.0 for field in _CANONICAL_COVERAGE_FIELDS}
        raw = float(frame["_raw_plan"].astype(float).mean())
        valid = float(frame["_valid_plan"].astype(float).mean())
        governance = float(frame["_governance_safe_plan"].astype(float).mean())
        product_ready = float(frame["_product_ready_plan"].astype(float).mean())
        return {
            "raw_plan_coverage": _round_metric(raw),
            "valid_plan_coverage": _round_metric(valid),
            "governance_safe_plan_coverage": _round_metric(governance),
            "product_ready_plan_coverage": _round_metric(product_ready),
            "no_plan_rate": _round_metric(1.0 - raw),
        }

    coverage_breakdown = pd.DataFrame(
        [
            {
                "population": "full_evaluation_population",
                "funnel_stage": "raw",
                "count": int(work["_raw_plan"].sum()),
                "share": _round_metric(float(work["_raw_plan"].mean())),
            },
            {
                "population": "full_evaluation_population",
                "funnel_stage": "valid",
                "count": int(work["_valid_plan"].sum()),
                "share": _round_metric(float(work["_valid_plan"].mean())),
            },
            {
                "population": "full_evaluation_population",
                "funnel_stage": "governance_safe",
                "count": int(work["_governance_safe_plan"].sum()),
                "share": _round_metric(float(work["_governance_safe_plan"].mean())),
            },
            {
                "population": "full_evaluation_population",
                "funnel_stage": "product_ready",
                "count": int(work["_product_ready_plan"].sum()),
                "share": _round_metric(float(work["_product_ready_plan"].mean())),
            },
        ]
    )
    coverage_drop_frames = [
        _coverage_reason_rows(raw_not_valid, transition="raw_to_valid"),
        _coverage_reason_rows(valid_not_governance, transition="valid_to_governance_safe"),
        _coverage_reason_rows(governance_not_product, transition="governance_safe_to_product_ready"),
    ]
    non_empty_drop_frames = [frame for frame in coverage_drop_frames if not frame.empty]
    if non_empty_drop_frames:
        coverage_drop_breakdown = pd.concat(non_empty_drop_frames, ignore_index=True, sort=False)
    else:
        coverage_drop_breakdown = pd.DataFrame(
            columns=["population", "transition", "reason", "count", "share_of_source"]
        )

    flag_rows: list[dict[str, Any]] = []
    for flag in _CANONICAL_REALITY_GAP_FLAGS:
        count = int(work[flag].astype(int).sum())
        flag_rows.append(
            {
                "population": "full_evaluation_population",
                "flag": flag,
                "count": count,
                "share": _round_metric(float(count) / float(total)),
                "severity": "",
                "severity_share": 0.0,
                "breakdown_type": "flag_distribution",
            }
        )
    for severity in ("mild", "moderate", "severe"):
        count = int((work["_reality_gap_severity"] == severity).sum())
        flag_rows.append(
            {
                "population": "full_evaluation_population",
                "flag": "",
                "count": count,
                "share": _round_metric(float(count) / float(total)),
                "severity": severity,
                "severity_share": _round_metric(float(count) / float(total)),
                "breakdown_type": "severity_split",
            }
        )
    reality_gap_breakdown = pd.DataFrame(flag_rows)

    segment_breakdown = _segment_breakdown(work)

    offer_diagnostics = pd.DataFrame(
        [
            {
                "population": "full_evaluation_population",
                "offer_needed_segment": offer_needed,
                "count": int(len(frame)),
                "share": _round_metric(float(len(frame)) / float(total)),
                "offer_plan_rate": _round_metric(frame["best_offer_plan"].astype(float).mean()),
                "rankable_offer_rate": _round_metric(frame["best_rankable_offer"].astype(float).mean()),
                "governance_safe_offer_rate": _round_metric(frame["best_governance_safe_offer"].astype(float).mean()),
                "offer_acceptance_probability_mean": _round_metric(
                    pd.to_numeric(frame["best_offer_acceptance_probability"], errors="coerce").fillna(0.0).mean()
                ),
                "combined_realization_rate": _round_metric(
                    pd.to_numeric(frame["best_combined_plan_realization_probability"], errors="coerce").fillna(0.0).mean()
                ),
                "dominant_offer_type": (
                    frame["best_offer_type"].fillna("").astype(str).replace("", pd.NA).dropna().value_counts().idxmax()
                    if not frame["best_offer_type"].fillna("").astype(str).replace("", pd.NA).dropna().empty
                    else ""
                ),
            }
            for offer_needed, frame in work.groupby("offer_needed_segment", dropna=False)
        ]
    )

    behavior_rows = []
    overall_nominal = _round_metric(pd.to_numeric(work["best_nominal_pd_improvement"], errors="coerce").fillna(0.0).mean())
    overall_expected = _round_metric(pd.to_numeric(work["best_expected_pd_improvement"], errors="coerce").fillna(0.0).mean())
    behavior_rows.append(
        {
            "population": "full_evaluation_population",
            "slice_type": "overall",
            "slice_value": "all",
            "count": int(len(work)),
            "mean_plan_execution_probability": _round_metric(
                pd.to_numeric(work["best_plan_execution_probability"], errors="coerce").fillna(0.0).mean()
            ),
            "nominal_pd_improvement": overall_nominal,
            "execution_weighted_expected_improvement": overall_expected,
            "execution_weighted_gap_vs_nominal": _round_metric(overall_nominal - overall_expected),
            "mixed_execution_exposure": _round_metric(work["best_mixed_execution"].astype(float).mean()),
            "failed_execution_exposure": _round_metric(work["best_failed_execution"].astype(float).mean()),
        }
    )
    for risk_band, frame in work.groupby("risk_band", dropna=False):
        nominal = _round_metric(pd.to_numeric(frame["best_nominal_pd_improvement"], errors="coerce").fillna(0.0).mean())
        expected = _round_metric(pd.to_numeric(frame["best_expected_pd_improvement"], errors="coerce").fillna(0.0).mean())
        behavior_rows.append(
            {
                "population": "full_evaluation_population",
                "slice_type": "risk_band",
                "slice_value": _safe_str(risk_band),
                "count": int(len(frame)),
                "mean_plan_execution_probability": _round_metric(
                    pd.to_numeric(frame["best_plan_execution_probability"], errors="coerce").fillna(0.0).mean()
                ),
                "nominal_pd_improvement": nominal,
                "execution_weighted_expected_improvement": expected,
                "execution_weighted_gap_vs_nominal": _round_metric(nominal - expected),
                "mixed_execution_exposure": _round_metric(frame["best_mixed_execution"].astype(float).mean()),
                "failed_execution_exposure": _round_metric(frame["best_failed_execution"].astype(float).mean()),
            }
        )
    behavior_comparison = pd.DataFrame(behavior_rows)

    trajectory_class_breakdown = pd.DataFrame(
        [
            {
                "population": "full_evaluation_population",
                "trajectory_class": trajectory_class,
                "count": int(len(frame)),
                "share": _round_metric(float(len(frame)) / float(total)),
                "gate_pass_rate_4w": _round_metric(frame["trajectory_gate_pass_4w"].astype(float).mean()),
                "gate_pass_rate_12w": _round_metric(frame["trajectory_gate_pass_12w"].astype(float).mean()),
                "gate_pass_rate_24w": _round_metric(frame["trajectory_gate_pass_24w"].astype(float).mean()),
                "product_ready_plan_coverage": _round_metric(frame["_product_ready_plan"].astype(float).mean()),
            }
            for trajectory_class, frame in work.groupby("trajectory_class", dropna=False)
        ]
    )
    trajectory_class_breakdown["trajectory_class"] = pd.Categorical(
        trajectory_class_breakdown["trajectory_class"],
        categories=list(_TRAJECTORY_CLASS_ORDER),
        ordered=True,
    )
    trajectory_class_breakdown = trajectory_class_breakdown.sort_values("trajectory_class").reset_index(drop=True)
    trajectory_class_breakdown["trajectory_class"] = trajectory_class_breakdown["trajectory_class"].astype(str)

    dominant_reality_gap_reason = _dominant_reality_gap_reason(work)

    highest_reality_gap_segment = _segment_extreme(segment_breakdown, metric="reality_gap_flag_rate", highest=True)
    highest_product_ready_drop_segment = _segment_extreme(
        segment_breakdown.assign(
            product_ready_drop=(1.0 - segment_breakdown["product_ready_plan_coverage"].astype(float))
        ),
        metric="product_ready_drop",
        highest=True,
    )
    highest_offer_needed_segment = _segment_extreme(segment_breakdown, metric="offer_plan_rate", highest=True)
    lowest_product_ready_segment = _segment_extreme(segment_breakdown, metric="product_ready_plan_coverage", highest=False)

    canonical_metrics = {
        **_coverage_metrics(work),
        "infeasible_plan_rate": _round_metric((work["action_realism_infeasible_plan_count"].astype(int) > 0).astype(float).mean()),
        "repaired_plan_rate": _round_metric((work["best_constraint_status"].astype(str).str.lower() == "repaired").astype(float).mean()),
        "provisional_plan_rate": _round_metric((work["best_constraint_status"].astype(str).str.lower() == "provisional").astype(float).mean()),
        "reality_gap_flag_rate": _round_metric(work["_has_reality_gap"].astype(float).mean()),
        "unrealistic_pd_drop_rate": _round_metric(work["unrealistic_pd_drop_flag"].astype(float).mean()),
        "execution_mismatch_flag_rate": _round_metric(work["execution_mismatch_flag"].astype(float).mean()),
        "mean_plan_execution_probability": _round_metric(
            pd.to_numeric(work["best_plan_execution_probability"], errors="coerce").fillna(0.0).mean()
        ),
        "mean_nominal_pd_improvement": _round_metric(
            pd.to_numeric(work["best_nominal_pd_improvement"], errors="coerce").fillna(0.0).mean()
        ),
        "execution_weighted_expected_improvement": _round_metric(
            pd.to_numeric(work["best_expected_pd_improvement"], errors="coerce").fillna(0.0).mean()
        ),
        "execution_weighted_gap_vs_nominal": _round_metric(
            pd.to_numeric(work["best_nominal_pd_improvement"], errors="coerce").fillna(0.0).mean()
            - pd.to_numeric(work["best_expected_pd_improvement"], errors="coerce").fillna(0.0).mean()
        ),
        "offer_plan_rate": _round_metric(work["best_offer_plan"].astype(float).mean()),
        "rankable_offer_rate": _round_metric(work["best_rankable_offer"].astype(float).mean()),
        "governance_safe_offer_rate": _round_metric(work["best_governance_safe_offer"].astype(float).mean()),
        "combined_realization_rate": _round_metric(
            pd.to_numeric(work["best_combined_plan_realization_probability"], errors="coerce").fillna(0.0).mean()
        ),
        "early_checkpoint_health_rate": _round_metric((work["trajectory_class"] == "early_healthy").astype(float).mean()),
        "delayed_only_rate": _round_metric((work["trajectory_class"] == "delayed_only").astype(float).mean()),
        "long_horizon_heavy_rate": _round_metric((work["trajectory_class"] == "long_horizon_heavy").astype(float).mean()),
        "replan_risk_rate": _round_metric((work["trajectory_class"] == "replan_prone").astype(float).mean()),
        "product_ready_drop_due_to_reality_gap": _round_metric(
            float(
                (
                    (governance_not_product["drop_reason"].astype(str) == "reality_gap_flags").sum()
                    / max(1, len(governance_not_product))
                )
            )
        ),
    }
    secondary_metrics = _coverage_metrics(denied_rows)

    strongest_segments = _top_segment_rows(segment_breakdown, ascending=False, top_n=2)
    weakest_segments = _top_segment_rows(segment_breakdown, ascending=True, top_n=2)
    demo_representativeness = _build_demo_representativeness(work, demo_case=demo_case)

    summary = {
        "canonical_population": "full_evaluation_population",
        "secondary_population": "denied",
        "population_sizes": {
            "full_evaluation_population": int(len(work)),
            "denied": int(len(denied_rows)),
            "high_risk_denied": int(len(high_risk_denied_rows)),
        },
        "canonical_metrics": canonical_metrics,
        "secondary_metrics": secondary_metrics,
        "reality_gap_summary": {
            "reality_gap_flag_rate": canonical_metrics["reality_gap_flag_rate"],
            "dominant_reality_gap_reason": dominant_reality_gap_reason,
            "product_ready_drop_due_to_reality_gap": canonical_metrics["product_ready_drop_due_to_reality_gap"],
            "multi_flag_exposure": _round_metric(
                (
                    work[list(_CANONICAL_REALITY_GAP_FLAGS)].astype(int).sum(axis=1) >= 2
                ).astype(float).mean()
            ),
            "severity_split": {
                "mild": _round_metric((work["_reality_gap_severity"] == "mild").astype(float).mean()),
                "moderate": _round_metric((work["_reality_gap_severity"] == "moderate").astype(float).mean()),
                "severe": _round_metric((work["_reality_gap_severity"] == "severe").astype(float).mean()),
            },
            "highest_reality_gap_segment": highest_reality_gap_segment,
            "highest_product_ready_drop_segment": highest_product_ready_drop_segment,
        },
        "strongest_segments": strongest_segments,
        "weakest_segments": weakest_segments,
        "highest_offer_needed_segment": highest_offer_needed_segment,
        "lowest_product_ready_segment": lowest_product_ready_segment,
        "segment_story": {
            "where_engine_works": strongest_segments[0]["segment_label"] if strongest_segments else "",
            "where_engine_struggles": weakest_segments[0]["segment_label"] if weakest_segments else "",
            "where_offer_is_required": _safe_str(highest_offer_needed_segment.get("segment_label", "")),
            "where_narrative_breaks": _safe_str(highest_reality_gap_segment.get("segment_label", "")),
        },
        "demo_representativeness": demo_representativeness,
        "supporting_artifacts": supporting_artifacts,
    }
    review_markdown = _render_portfolio_validation_review(summary)

    return {
        "summary": summary,
        "coverage_breakdown": coverage_breakdown,
        "coverage_drop_breakdown": coverage_drop_breakdown,
        "reality_gap_breakdown": reality_gap_breakdown,
        "segment_breakdown": segment_breakdown,
        "offer_diagnostics": offer_diagnostics,
        "behavior_comparison": behavior_comparison,
        "trajectory_class_breakdown": trajectory_class_breakdown,
        "demo_representativeness": demo_representativeness,
        "review_markdown": review_markdown,
    }


def aggregate_portfolio_validation_summaries(seed_summaries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    supporting_artifacts = {
        "portfolio_validation_summary_json": "tables/portfolio_validation_summary.json",
        "portfolio_coverage_breakdown_csv": "tables/portfolio_coverage_breakdown.csv",
        "portfolio_coverage_drop_breakdown_csv": "tables/portfolio_coverage_drop_breakdown.csv",
        "portfolio_reality_gap_breakdown_csv": "tables/portfolio_reality_gap_breakdown.csv",
        "portfolio_segment_breakdown_csv": "tables/portfolio_segment_breakdown.csv",
        "portfolio_offer_diagnostics_csv": "tables/portfolio_offer_diagnostics.csv",
        "portfolio_behavior_comparison_csv": "tables/portfolio_behavior_comparison.csv",
        "portfolio_trajectory_class_breakdown_csv": "tables/portfolio_trajectory_class_breakdown.csv",
        "demo_representativeness_summary_json": "tables/demo_representativeness_summary.json",
        "portfolio_validation_review_md": "tables/portfolio_validation_review.md",
    }
    if not seed_summaries:
        return {
            "canonical_population": "full_evaluation_population",
            "secondary_population": "denied",
            "seed_count": 0,
            "population_sizes": {
                "full_evaluation_population": 0,
                "denied": 0,
                "high_risk_denied": 0,
            },
            "canonical_metrics": {},
            "secondary_metrics": {},
            "reality_gap_summary": {},
            "strongest_segments": [],
            "weakest_segments": [],
            "highest_offer_needed_segment": {},
            "lowest_product_ready_segment": {},
            "segment_story": {
                "where_engine_works": "",
                "where_engine_struggles": "",
                "where_offer_is_required": "",
                "where_narrative_breaks": "",
            },
            "demo_representativeness": {
                "demo_representativeness_verdict": "misleading",
                "demo_fit_confidence": "weak",
            },
            "supporting_artifacts": supporting_artifacts,
        }

    def _mean_metric(path: Sequence[str]) -> float:
        values = []
        for summary in seed_summaries:
            current: Any = summary
            for key in path:
                current = current.get(key, {}) if isinstance(current, Mapping) else {}
            if isinstance(current, (int, float)):
                values.append(float(current))
        return _round_metric(sum(values) / max(1, len(values)))

    def _mode_string(path: Sequence[str]) -> str:
        values: list[str] = []
        for summary in seed_summaries:
            current: Any = summary
            for key in path:
                current = current.get(key, {}) if isinstance(current, Mapping) else {}
            text = _safe_str(current)
            if text:
                values.append(text)
        if not values:
            return ""
        return Counter(values).most_common(1)[0][0]

    canonical_metric_keys = sorted(
        {
            str(key)
            for summary in seed_summaries
            for key in (
                summary.get("canonical_metrics", {}).keys()
                if isinstance(summary.get("canonical_metrics", {}), Mapping)
                else []
            )
        }
    )
    secondary_metric_keys = sorted(
        {
            str(key)
            for summary in seed_summaries
            for key in (
                summary.get("secondary_metrics", {}).keys()
                if isinstance(summary.get("secondary_metrics", {}), Mapping)
                else []
            )
        }
    )

    strongest_segments = []
    weakest_segments = []
    for key in ("strongest_segments", "weakest_segments"):
        collected = []
        for summary in seed_summaries:
            entries = summary.get(key, [])
            if isinstance(entries, list):
                collected.extend(entry for entry in entries if isinstance(entry, Mapping))
        if key == "strongest_segments":
            strongest_segments = collected[:2]
        else:
            weakest_segments = collected[:2]

    demo_fit = {
        "demo_representativeness_verdict": _mode_string(["demo_representativeness", "demo_representativeness_verdict"]),
        "demo_fit_confidence": _mode_string(["demo_representativeness", "demo_fit_confidence"]),
        "demo_case_segment": _mode_string(["demo_representativeness", "demo_case_segment"]),
        "segment_size": int(
            round(
                sum(
                    _safe_float(summary.get("demo_representativeness", {}).get("segment_size"), 0.0)
                    for summary in seed_summaries
                )
                / max(1, len(seed_summaries))
            )
        ),
        "demo_case_segment_share": _mean_metric(["demo_representativeness", "demo_case_segment_share"]),
        "segment_product_ready_rate": _mean_metric(["demo_representativeness", "segment_product_ready_rate"]),
        "segment_offer_dependency": _mean_metric(["demo_representativeness", "segment_offer_dependency"]),
        "product_ready_alignment": bool(
            round(
                sum(
                    1.0 if bool(summary.get("demo_representativeness", {}).get("product_ready_alignment")) else 0.0
                    for summary in seed_summaries
                )
                / max(1, len(seed_summaries))
            )
        ),
        "cohort_vs_demo_delta": {
            "plan_execution_probability": _mean_metric(
                ["demo_representativeness", "cohort_vs_demo_delta", "plan_execution_probability"]
            ),
            "early_checkpoint_health_rate": _mean_metric(
                ["demo_representativeness", "cohort_vs_demo_delta", "early_checkpoint_health_rate"]
            ),
            "product_ready_rate": _mean_metric(
                ["demo_representativeness", "cohort_vs_demo_delta", "product_ready_rate"]
            ),
        },
        "narrative": _mode_string(["demo_representativeness", "narrative"]),
    }

    summary = {
        "canonical_population": "full_evaluation_population",
        "secondary_population": "denied",
        "seed_count": int(len(seed_summaries)),
        "population_sizes": {
            "full_evaluation_population": int(
                round(
                    sum(_safe_float(summary.get("population_sizes", {}).get("full_evaluation_population"), 0.0) for summary in seed_summaries)
                    / max(1, len(seed_summaries))
                )
            ),
            "denied": int(
                round(
                    sum(_safe_float(summary.get("population_sizes", {}).get("denied"), 0.0) for summary in seed_summaries)
                    / max(1, len(seed_summaries))
                )
            ),
            "high_risk_denied": int(
                round(
                    sum(_safe_float(summary.get("population_sizes", {}).get("high_risk_denied"), 0.0) for summary in seed_summaries)
                    / max(1, len(seed_summaries))
                )
            ),
        },
        "canonical_metrics": {key: _mean_metric(["canonical_metrics", key]) for key in canonical_metric_keys},
        "secondary_metrics": {key: _mean_metric(["secondary_metrics", key]) for key in secondary_metric_keys},
        "reality_gap_summary": {
            "reality_gap_flag_rate": _mean_metric(["reality_gap_summary", "reality_gap_flag_rate"]),
            "dominant_reality_gap_reason": _mode_string(["reality_gap_summary", "dominant_reality_gap_reason"]),
            "product_ready_drop_due_to_reality_gap": _mean_metric(
                ["reality_gap_summary", "product_ready_drop_due_to_reality_gap"]
            ),
            "multi_flag_exposure": _mean_metric(["reality_gap_summary", "multi_flag_exposure"]),
            "severity_split": {
                "mild": _mean_metric(["reality_gap_summary", "severity_split", "mild"]),
                "moderate": _mean_metric(["reality_gap_summary", "severity_split", "moderate"]),
                "severe": _mean_metric(["reality_gap_summary", "severity_split", "severe"]),
            },
            "highest_reality_gap_segment": next(
                (
                    summary.get("reality_gap_summary", {}).get("highest_reality_gap_segment", {})
                    for summary in seed_summaries
                    if isinstance(summary.get("reality_gap_summary", {}).get("highest_reality_gap_segment", {}), Mapping)
                ),
                {},
            ),
            "highest_product_ready_drop_segment": next(
                (
                    summary.get("reality_gap_summary", {}).get("highest_product_ready_drop_segment", {})
                    for summary in seed_summaries
                    if isinstance(summary.get("reality_gap_summary", {}).get("highest_product_ready_drop_segment", {}), Mapping)
                ),
                {},
            ),
        },
        "strongest_segments": strongest_segments,
        "weakest_segments": weakest_segments,
        "highest_offer_needed_segment": next(
            (
                summary.get("highest_offer_needed_segment", {})
                for summary in seed_summaries
                if isinstance(summary.get("highest_offer_needed_segment", {}), Mapping)
            ),
            {},
        ),
        "lowest_product_ready_segment": next(
            (
                summary.get("lowest_product_ready_segment", {})
                for summary in seed_summaries
                if isinstance(summary.get("lowest_product_ready_segment", {}), Mapping)
            ),
            {},
        ),
        "segment_story": {
            "where_engine_works": _mode_string(["segment_story", "where_engine_works"]),
            "where_engine_struggles": _mode_string(["segment_story", "where_engine_struggles"]),
            "where_offer_is_required": _mode_string(["segment_story", "where_offer_is_required"]),
            "where_narrative_breaks": _mode_string(["segment_story", "where_narrative_breaks"]),
        },
        "demo_representativeness": demo_fit,
        "supporting_artifacts": supporting_artifacts,
    }
    return summary


def aggregate_portfolio_breakdown(
    seed_breakdowns: Sequence[pd.DataFrame],
    *,
    group_columns: Sequence[str],
    value_columns: Mapping[str, str],
    breakdown_type_seed: str,
    breakdown_type_rollup: str,
) -> pd.DataFrame:
    columns = ["seed", *group_columns, *value_columns.keys(), "breakdown_type"]
    if not seed_breakdowns:
        return pd.DataFrame(columns=columns)
    frames: list[pd.DataFrame] = []
    for breakdown_df in seed_breakdowns:
        if breakdown_df.empty or "seed" not in breakdown_df.columns:
            continue
        working = breakdown_df.copy()
        working["breakdown_type"] = breakdown_type_seed
        frames.append(working)
    if not frames:
        return pd.DataFrame(columns=columns)
    combined = pd.concat(frames, ignore_index=True, sort=False)
    agg_spec = dict(value_columns)
    rollup = combined.groupby(list(group_columns), dropna=False).agg(agg_spec).reset_index()
    rollup["seed"] = -1
    rollup["breakdown_type"] = breakdown_type_rollup
    return pd.concat([combined, rollup], ignore_index=True, sort=False)


def render_portfolio_validation_review(summary: Mapping[str, Any]) -> str:
    return _render_portfolio_validation_review(summary)
