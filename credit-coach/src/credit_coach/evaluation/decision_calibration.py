from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import pandas as pd

from credit_coach.decision.ownership import DECISION_POLICY_VERSION


READINESS_ORDER: tuple[str, ...] = ("now", "week_4", "week_12", "week_24", "not_ready", "unknown_review")
EXTERNAL_STATUS_ORDER: tuple[str, ...] = ("APPROVED", "CONDITIONAL", "REJECTED")
INTERNAL_STATUS_ORDER: tuple[str, ...] = ("APPROVED", "CONDITIONAL", "REJECTED", "NEEDS_REVIEW")
PILOT_MIX_BUCKET_ORDER: tuple[str, ...] = (
    "approved_like",
    "near_threshold",
    "denied_mid_pressure",
    "denied_high_pressure",
)
PILOT_MIX_WEIGHTS: Mapping[str, int] = {
    "approved_like": 20,
    "near_threshold": 30,
    "denied_mid_pressure": 25,
    "denied_high_pressure": 25,
}
DEFAULT_CANDIDATE_POLICIES: tuple[Mapping[str, Any], ...] = (
    {
        "policy_version": "analysis_mild_relax_v2_3a",
        "profile_role": "candidate",
        "promotion_target": True,
        "approved_realization_min": 0.49,
        "approved_improvement_min": 0.019,
        "approved_confidence_min": 0.58,
        "conditional_realization_min": 0.19,
        "conditional_improvement_min": 0.009,
        "conditional_confidence_min": 0.35,
    },
    {
        "policy_version": "analysis_relaxed_v2_3a",
        "profile_role": "candidate",
        "promotion_target": True,
        "approved_realization_min": 0.48,
        "approved_improvement_min": 0.018,
        "approved_confidence_min": 0.55,
        "conditional_realization_min": 0.18,
        "conditional_improvement_min": 0.008,
        "conditional_confidence_min": 0.30,
    },
    {
        "policy_version": "analysis_strict_control_v2_3a",
        "profile_role": "control",
        "promotion_target": False,
        "approved_realization_min": 0.55,
        "approved_improvement_min": 0.025,
        "approved_confidence_min": 0.68,
        "conditional_realization_min": 0.22,
        "conditional_improvement_min": 0.012,
        "conditional_confidence_min": 0.45,
    },
)
POLICY_PROFILE_CATALOG_VERSION = "v2.3_phase_49"
SHORTLIST_MAX_FALSE_POSITIVE_PROXY_DELTA = 0.01
SHORTLIST_MAX_INTERNAL_REVIEW_DELTA = 0.02
SHORTLIST_MIN_APPROVE_PLUS_CONDITIONAL_DELTA = 0.000001
FALSE_POSITIVE_PROXY_WEIGHTS: Mapping[str, float] = {
    "low_realization_rate": 0.40,
    "weak_readiness_alignment_rate": 0.30,
    "internal_review_pressure_rate": 0.30,
}


@dataclass(frozen=True)
class CohortSelectionResult:
    selected: pd.DataFrame
    metadata: dict[str, Any]


def baseline_policy_profile(*, policy_version: str = DECISION_POLICY_VERSION) -> dict[str, Any]:
    return {
        "policy_version": str(policy_version or DECISION_POLICY_VERSION),
        "profile_role": "baseline",
        "analysis_only": 0,
        "promotion_target": False,
        "approved_realization_min": 0.50,
        "approved_improvement_min": 0.02,
        "approved_confidence_min": 0.60,
        "conditional_realization_min": 0.20,
        "conditional_improvement_min": 0.01,
        "conditional_confidence_min": 0.40,
    }


def _normalize_candidate_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    normalized = {
        "policy_version": _safe_str(policy.get("policy_version"), "analysis_candidate"),
        "profile_role": _safe_str(policy.get("profile_role"), "candidate"),
        "analysis_only": int(_safe_int(policy.get("analysis_only", 1), 1)),
        "promotion_target": bool(policy.get("promotion_target", True)),
        "approved_realization_min": _round_metric(policy.get("approved_realization_min"), 6),
        "approved_improvement_min": _round_metric(policy.get("approved_improvement_min"), 6),
        "approved_confidence_min": _round_metric(policy.get("approved_confidence_min"), 6),
        "conditional_realization_min": _round_metric(policy.get("conditional_realization_min"), 6),
        "conditional_improvement_min": _round_metric(policy.get("conditional_improvement_min"), 6),
        "conditional_confidence_min": _round_metric(policy.get("conditional_confidence_min"), 6),
    }
    return normalized


def build_policy_profile_catalog(
    *,
    policy_version_evaluated: str,
    candidate_policies: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    candidates = [_normalize_candidate_policy(policy) for policy in (candidate_policies or DEFAULT_CANDIDATE_POLICIES)]
    baseline = baseline_policy_profile(policy_version=_safe_str(policy_version_evaluated, DECISION_POLICY_VERSION))
    return {
        "catalog_version": POLICY_PROFILE_CATALOG_VERSION,
        "policy_version_evaluated": baseline["policy_version"],
        "profiles": [baseline, *candidates],
    }


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


def _round_metric(value: Any, digits: int = 6) -> float:
    return round(_safe_float(value, 0.0), digits)


def _normalize_decision_status(value: Any) -> str:
    normalized = _safe_str(value).upper()
    return normalized if normalized in EXTERNAL_STATUS_ORDER else "CONDITIONAL"


def _normalize_internal_status(value: Any) -> str:
    normalized = _safe_str(value).upper()
    return normalized if normalized in INTERNAL_STATUS_ORDER else "NEEDS_REVIEW"


def _normalize_readiness(value: Any) -> str:
    normalized = _safe_str(value).lower()
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


def _decision_confidence_band(value: Any) -> str:
    score = _safe_float(value, 0.0)
    if score < 0.40:
        return "low"
    if score < 0.60:
        return "moderate"
    return "high"


def _offer_needed_flag(row: Mapping[str, Any]) -> str:
    if _safe_int(row.get("offer_plan", 0), 0) == 1:
        return "offer_needed"
    if _safe_str(row.get("offer_maturity")).lower() not in {"", "none"}:
        return "offer_needed"
    if _safe_float(row.get("offer_acceptance_probability"), 0.0) > 0.0:
        return "offer_needed"
    return "no_offer_needed"


def _pilot_bucket(base_pd: float, tau: float, *, near_upper: float, mid_upper: float) -> str:
    distance = float(base_pd) - float(tau)
    if distance < -float(near_upper):
        return "approved_like"
    if distance <= float(near_upper):
        return "near_threshold"
    if distance <= float(mid_upper):
        return "denied_mid_pressure"
    return "denied_high_pressure"


def _allocate_quotas(total: int, weights: Mapping[str, int]) -> dict[str, int]:
    requested = max(0, int(total))
    if requested == 0:
        return {str(key): 0 for key in weights}
    total_weight = max(1, int(sum(max(0, int(weight)) for weight in weights.values())))
    floors: dict[str, int] = {}
    remainders: list[tuple[float, str]] = []
    assigned = 0
    for key, weight in weights.items():
        ratio = float(max(0, int(weight))) / float(total_weight)
        exact = ratio * requested
        floor_value = int(exact)
        floors[str(key)] = floor_value
        assigned += floor_value
        remainders.append((exact - floor_value, str(key)))
    for _, key in sorted(remainders, key=lambda item: (-item[0], item[1]))[: max(0, requested - assigned)]:
        floors[key] += 1
    return floors


def _sample(frame: pd.DataFrame, n: int, *, seed: int) -> pd.DataFrame:
    if frame.empty or n <= 0:
        return frame.iloc[0:0].copy()
    keep = min(int(n), len(frame))
    return frame.sample(n=keep, random_state=int(seed)).copy()


def _take_remaining(frame: pd.DataFrame, *, selected_positions: set[int], n: int, seed: int) -> pd.DataFrame:
    remaining = frame.loc[~frame["_frame_position"].astype(int).isin(selected_positions)].copy()
    return _sample(remaining, n, seed=seed)


def _select_by_quotas(
    frame: pd.DataFrame,
    *,
    bucket_column: str,
    quota_map: Mapping[str, int],
    seed: int,
) -> tuple[pd.DataFrame, dict[str, int]]:
    chosen: list[pd.DataFrame] = []
    selected_positions: set[int] = set()
    fill_counts: dict[str, int] = {str(bucket): 0 for bucket in quota_map}
    for offset, bucket in enumerate(quota_map):
        bucket_frame = frame.loc[frame[bucket_column].astype(str) == str(bucket)].copy()
        sampled = _sample(bucket_frame, int(quota_map[bucket]), seed=seed + offset)
        if sampled.empty:
            continue
        selected_positions.update(sampled["_frame_position"].astype(int).tolist())
        fill_counts[str(bucket)] = len(sampled)
        chosen.append(sampled)
    selected = pd.concat(chosen, ignore_index=True) if chosen else frame.iloc[0:0].copy()
    remaining = max(0, int(sum(quota_map.values())) - len(selected))
    if remaining > 0:
        fill = _take_remaining(frame, selected_positions=selected_positions, n=remaining, seed=seed + 97)
        if not fill.empty:
            fill = fill.copy()
            fill["selection_reason"] = fill.get("selection_reason", pd.Series(index=fill.index, dtype=object)).fillna("").astype(str)
            fill.loc[:, "selection_reason"] = fill["selection_reason"].replace("", "soft_fill")
            selected = pd.concat([selected, fill], ignore_index=True)
    return selected.reset_index(drop=True), fill_counts


def build_selection_work_frame(
    *,
    input_df: pd.DataFrame,
    base_pd: pd.Series,
    tau: float,
    risk_band_fn,
    segment_caps_cfg: Mapping[str, Any],
    customer_id_getter,
) -> pd.DataFrame:
    work = input_df.copy()
    if "source_row_index" not in work.columns:
        work = work.reset_index().rename(columns={"index": "source_row_index"})
    else:
        work = work.reset_index(drop=True)
    work["_frame_position"] = range(len(work))
    work["base_pd"] = base_pd.reset_index(drop=True).astype(float).values
    work["pd_distance_to_tau"] = work["base_pd"].astype(float) - float(tau)
    work["denied_base"] = work["base_pd"].astype(float) > float(tau)
    work["risk_band"] = work["base_pd"].map(lambda value: risk_band_fn(float(value), float(tau), dict(segment_caps_cfg)))
    risk_cfg = (
        dict(segment_caps_cfg.get("risk_band_thresholds", {}))
        if isinstance(segment_caps_cfg.get("risk_band_thresholds", {}), Mapping)
        else {}
    )
    near_upper = max(0.01, float(risk_cfg.get("near_upper", 0.10)))
    mid_upper = max(float(near_upper), float(risk_cfg.get("mid_upper", 0.25)))
    work["pilot_bucket"] = work["base_pd"].map(
        lambda value: _pilot_bucket(float(value), float(tau), near_upper=near_upper, mid_upper=mid_upper)
    )
    work["customer_id"] = [customer_id_getter(row, fallback=f"customer_{int(row['source_row_index'])}") for _, row in work.iterrows()]
    return work


def select_initial_cohort(
    *,
    work: pd.DataFrame,
    requested_n: int,
    sample_seed: int,
    cohort_policy: str,
) -> CohortSelectionResult:
    requested = max(1, int(requested_n))
    seed = int(sample_seed)
    policy = str(cohort_policy)
    metadata: dict[str, Any] = {
        "selection_policy_name": policy,
        "requested_n_customers": requested,
    }

    if policy == "denied_only":
        selected = _sample(work.loc[work["denied_base"].astype(bool)].copy(), requested, seed=seed)
        selected["selection_reason"] = "denied_only"
        selected["cohort_bucket"] = "denied_only"
        metadata.update(
            {
                "selection_fill_behavior": "seeded_sampling",
                "cohort_purpose": "Denied-only review for hard-case inspection.",
                "cohort_definition": {"policy": "denied_only"},
            }
        )
    elif policy == "random_mixed":
        selected = _sample(work, requested, seed=seed)
        selected["selection_reason"] = "random_mixed"
        selected["cohort_bucket"] = "random_mixed"
        metadata.update(
            {
                "selection_fill_behavior": "seeded_sampling",
                "cohort_purpose": "Random mixed inspection across the available queue.",
                "cohort_definition": {"policy": "random_mixed"},
            }
        )
    elif policy == "union_denied_near":
        universe = work.loc[
            work["denied_base"].astype(bool) | (work["risk_band"].astype(str).str.lower() == "near")
        ].copy()
        selected = _sample(universe, requested, seed=seed)
        selected["selection_reason"] = selected["denied_base"].map(lambda denied: "denied_union" if bool(denied) else "near_union")
        selected["cohort_bucket"] = selected["selection_reason"]
        metadata.update(
            {
                "selection_fill_behavior": "seeded_sampling",
                "cohort_purpose": "Union of denied and near-threshold customers for transitional inspection.",
                "cohort_definition": {"policy": "union_denied_near"},
            }
        )
    elif policy == "pilot_mixed":
        quotas = _allocate_quotas(requested, PILOT_MIX_WEIGHTS)
        chosen: list[pd.DataFrame] = []
        selected_positions: set[int] = set()
        fill_counts: dict[str, int] = {}
        for offset, bucket in enumerate(PILOT_MIX_BUCKET_ORDER):
            bucket_frame = work.loc[work["pilot_bucket"].astype(str) == bucket].copy()
            sampled = _sample(bucket_frame, quotas[bucket], seed=seed + offset)
            if sampled.empty:
                fill_counts[bucket] = 0
                continue
            sampled["selection_reason"] = bucket
            sampled["cohort_bucket"] = bucket
            fill_counts[bucket] = len(sampled)
            selected_positions.update(sampled["_frame_position"].astype(int).tolist())
            chosen.append(sampled)
        selected = pd.concat(chosen, ignore_index=True) if chosen else work.iloc[0:0].copy()
        remaining = max(0, requested - len(selected))
        if remaining > 0:
            fill = _take_remaining(work, selected_positions=selected_positions, n=remaining, seed=seed + 97)
            if not fill.empty:
                fill["selection_reason"] = "soft_fill"
                fill["cohort_bucket"] = fill["pilot_bucket"].astype(str)
                selected = pd.concat([selected, fill], ignore_index=True)
        metadata.update(
            {
                "selection_fill_behavior": "quota_first_deterministic_soft_fill",
                "cohort_purpose": "Pilot-ready mixed cohort for real funnel measurement.",
                "cohort_definition": {
                    "policy": "pilot_mixed",
                    "bucket_weights": dict(PILOT_MIX_WEIGHTS),
                    "bucket_order": list(PILOT_MIX_BUCKET_ORDER),
                },
                "quota_fill_counts": fill_counts,
            }
        )
    elif policy == "risk_band_balanced":
        risk_weights = {"near": 1, "mid": 1, "high": 1}
        quotas = _allocate_quotas(requested, risk_weights)
        selected, fill_counts = _select_by_quotas(work, bucket_column="risk_band", quota_map=quotas, seed=seed)
        if not selected.empty:
            selected["selection_reason"] = selected.get("selection_reason", selected["risk_band"]).replace("", pd.NA).fillna(selected["risk_band"])
            selected["cohort_bucket"] = selected["risk_band"].astype(str)
        metadata.update(
            {
                "selection_fill_behavior": "quota_first_deterministic_soft_fill",
                "cohort_purpose": "Balanced risk-band cohort for decision comparisons without one band dominating.",
                "cohort_definition": {
                    "policy": "risk_band_balanced",
                    "bucket_weights": risk_weights,
                },
                "quota_fill_counts": fill_counts,
            }
        )
    elif policy == "ops_queue_replay":
        selected = work.sort_values(["_frame_position", "source_row_index"]).head(requested).copy().reset_index(drop=True)
        selected["selection_reason"] = "queue_replay"
        selected["cohort_bucket"] = "queue_replay"
        metadata.update(
            {
                "selection_fill_behavior": "order_preserving_replay",
                "cohort_purpose": "Replay the operator queue in its natural order for realism-first review.",
                "cohort_definition": {"policy": "ops_queue_replay"},
            }
        )
    elif policy == "offer_needed_balanced":
        broad_n = min(len(work), max(requested, requested * 2))
        pilot_result = select_initial_cohort(
            work=work,
            requested_n=broad_n,
            sample_seed=seed,
            cohort_policy="pilot_mixed",
        )
        selected = pilot_result.selected.copy()
        metadata.update(
            {
                "selection_fill_behavior": "two_pass_deterministic_rebalance",
                "cohort_purpose": "Pilot-like cohort rebalanced after execution into offer-needed vs no-offer-needed groups.",
                "cohort_definition": {
                    "policy": "offer_needed_balanced",
                    "pass_1_policy": "pilot_mixed",
                    "pass_1_requested_n": int(broad_n),
                    "rebalance_target": {"offer_needed": 1, "no_offer_needed": 1},
                },
                "requires_post_rebalance": True,
            }
        )
    else:
        denied = _sample(work.loc[work["denied_base"].astype(bool)].copy(), requested, seed=seed)
        denied["selection_reason"] = "denied"
        denied["cohort_bucket"] = "denied"
        selected_positions = set(denied["_frame_position"].astype(int).tolist())
        remaining = max(0, requested - len(denied))
        if remaining > 0:
            near_candidates = work.loc[
                (~work["_frame_position"].astype(int).isin(selected_positions))
                & (work["risk_band"].astype(str).str.lower() == "near")
            ].copy()
            near_fill = _sample(near_candidates, remaining, seed=seed + 1)
            near_fill["selection_reason"] = "near_fill"
            near_fill["cohort_bucket"] = "near_threshold"
            selected = pd.concat([denied, near_fill], ignore_index=True)
        else:
            selected = denied.reset_index(drop=True)
        metadata.update(
            {
                "selection_fill_behavior": "quota_first_deterministic_soft_fill",
                "cohort_purpose": "Stress-test only denied-first cohort with near-threshold backfill.",
                "cohort_definition": {
                    "policy": "denied_first_near",
                    "stress_test_only": True,
                },
            }
        )

    selected = selected.reset_index(drop=True)
    selected["cohort_policy"] = policy
    selected["selection_policy_name"] = str(metadata.get("selection_policy_name", policy))
    selected["selection_fill_behavior"] = str(metadata.get("selection_fill_behavior", "seeded_sampling"))
    selected["batch_index"] = range(len(selected))
    return CohortSelectionResult(selected=selected, metadata=metadata)


def rebalance_offer_needed_selection(
    *,
    selection_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    requested_n: int,
    sample_seed: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if selection_df.empty:
        return selection_df.copy(), {"offer_needed_rebalance_applied": False}
    work = selection_df.merge(
        metrics_df[["source_row_index", "customer_id", "offer_needed_flag"]].drop_duplicates(),
        on=["source_row_index", "customer_id"],
        how="left",
    )
    work["offer_needed_flag"] = work["offer_needed_flag"].fillna("no_offer_needed").astype(str)
    requested = max(1, int(requested_n))
    quotas = _allocate_quotas(requested, {"offer_needed": 1, "no_offer_needed": 1})
    chosen: list[pd.DataFrame] = []
    selected_positions: set[int] = set()
    counts: dict[str, int] = {"offer_needed": 0, "no_offer_needed": 0}
    for offset, flag in enumerate(("offer_needed", "no_offer_needed")):
        flag_frame = work.loc[work["offer_needed_flag"].astype(str) == flag].copy()
        sampled = _sample(flag_frame, quotas[flag], seed=int(sample_seed) + offset)
        if sampled.empty:
            continue
        counts[flag] = len(sampled)
        selected_positions.update(sampled["_frame_position"].astype(int).tolist())
        chosen.append(sampled)
    selected = pd.concat(chosen, ignore_index=True) if chosen else work.iloc[0:0].copy()
    remaining = max(0, requested - len(selected))
    if remaining > 0:
        fill = _take_remaining(work, selected_positions=selected_positions, n=remaining, seed=int(sample_seed) + 211)
        if not fill.empty:
            chosen_fill = fill.copy()
            chosen_fill["selection_reason"] = chosen_fill["offer_needed_flag"].map(
                lambda value: f"{value}_soft_fill"
            )
            selected = pd.concat([selected, chosen_fill], ignore_index=True)
    selected = selected.reset_index(drop=True)
    selected["cohort_bucket"] = selected["offer_needed_flag"].astype(str)
    selected["selection_policy_name"] = "offer_needed_balanced"
    selected["selection_fill_behavior"] = "two_pass_deterministic_rebalance"
    selected["batch_index"] = range(len(selected))
    metadata = {
        "offer_needed_rebalance_applied": True,
        "offer_needed_counts": counts,
        "offer_needed_balance": selected["offer_needed_flag"].astype(str).value_counts().sort_index().to_dict(),
    }
    return selected, metadata


def prepare_metrics_for_calibration(metrics_df: pd.DataFrame) -> pd.DataFrame:
    work = metrics_df.copy()
    if work.empty:
        for column in (
            "decision_status",
            "decision_status_internal",
            "expected_readiness",
            "decision_confidence_band",
            "offer_needed_flag",
            "conditional_type",
            "risk_band",
        ):
            if column not in work.columns:
                work[column] = pd.Series(dtype=object)
        return work
    work["decision_status"] = work.get("decision_status", pd.Series(dtype=object)).map(_normalize_decision_status)
    work["decision_status_internal"] = work.get("decision_status_internal", pd.Series(dtype=object)).map(_normalize_internal_status)
    work["expected_readiness"] = work.get("expected_readiness", pd.Series(dtype=object)).map(_normalize_readiness)
    work["decision_confidence"] = pd.to_numeric(work.get("decision_confidence", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    work["decision_confidence_band"] = work["decision_confidence"].map(_decision_confidence_band)
    work["offer_needed_flag"] = work.apply(lambda row: _offer_needed_flag(row.to_dict()), axis=1)
    work["conditional_type"] = work.get("conditional_type", pd.Series(dtype=object)).fillna("").astype(str)
    work["risk_band"] = work.get("risk_band", pd.Series(dtype=object)).fillna("unknown").astype(str)
    work["realization_anchor"] = pd.to_numeric(work.get("realization_anchor", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    work["expected_pd_improvement"] = pd.to_numeric(
        work.get("expected_pd_improvement", pd.Series(dtype=float)),
        errors="coerce",
    ).fillna(0.0)
    work["parity_pass"] = pd.to_numeric(work.get("parity_pass", pd.Series(dtype=float)), errors="coerce").fillna(1.0).astype(int)
    work["raw_contract_pass"] = pd.to_numeric(work.get("raw_contract_pass", pd.Series(dtype=float)), errors="coerce").fillna(1.0).astype(int)
    work["zero_step_flag"] = pd.to_numeric(work.get("zero_step_flag", pd.Series(dtype=float)), errors="coerce").fillna(0.0).astype(int)
    work["best_action_count"] = pd.to_numeric(work.get("best_action_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).astype(int)
    work["strong_execution_flag"] = pd.to_numeric(
        work.get("strong_execution_flag", pd.Series(dtype=float)),
        errors="coerce",
    ).fillna(0.0).astype(int)
    work["approval_ready_4w"] = pd.to_numeric(
        work.get("approval_ready_4w", pd.Series(dtype=float)),
        errors="coerce",
    ).fillna(0.0).astype(int)
    work["offer_maturity"] = work.get("offer_maturity", pd.Series(dtype=object)).fillna("none").astype(str)
    work["best_constraint_status"] = work.get("best_constraint_status", pd.Series(dtype=object)).fillna("valid").astype(str)
    work["plan_contract_pass"] = pd.to_numeric(
        work.get("plan_contract_pass", pd.Series(dtype=float)),
        errors="coerce",
    ).fillna(0.0).astype(int)
    work["decision_policy_version"] = work.get("decision_policy_version", pd.Series(dtype=object)).fillna("").astype(str)
    return work


def build_funnel_summary(metrics_df: pd.DataFrame) -> dict[str, Any]:
    work = prepare_metrics_for_calibration(metrics_df)
    total = max(1, len(work))
    approved_share = float((work["decision_status"] == "APPROVED").mean())
    conditional_share = float((work["decision_status"] == "CONDITIONAL").mean())
    rejected_share = float((work["decision_status"] == "REJECTED").mean())
    internal_needs_review_share = float((work["decision_status_internal"] == "NEEDS_REVIEW").mean())
    conditional_to_approved_potential = float(
        (
            (work["decision_status"] == "CONDITIONAL")
            & (work["expected_readiness"] == "week_4")
        ).mean()
    )
    return {
        "selected_n_customers": int(len(work)),
        "approved_share": _round_metric(approved_share),
        "conditional_share": _round_metric(conditional_share),
        "rejected_share": _round_metric(rejected_share),
        "internal_needs_review_share": _round_metric(internal_needs_review_share),
        "approve_plus_conditional_share": _round_metric(approved_share + conditional_share),
        "conditional_to_approved_potential": _round_metric(conditional_to_approved_potential),
        "decision_counts": {
            status: int((work["decision_status"] == status).sum()) for status in EXTERNAL_STATUS_ORDER
        },
        "internal_decision_counts": {
            status: int((work["decision_status_internal"] == status).sum()) for status in INTERNAL_STATUS_ORDER
        },
        "population": int(total),
    }


def build_readiness_distribution(metrics_df: pd.DataFrame) -> pd.DataFrame:
    work = prepare_metrics_for_calibration(metrics_df)
    total = max(1, len(work))
    rows: list[dict[str, Any]] = []
    counts = work["expected_readiness"].value_counts()
    for readiness in READINESS_ORDER:
        count = int(counts.get(readiness, 0))
        rows.append(
            {
                "expected_readiness": readiness,
                "count": count,
                "share": _round_metric(count / total if total else 0.0),
            }
        )
    return pd.DataFrame(rows)


def build_status_by_readiness(metrics_df: pd.DataFrame) -> pd.DataFrame:
    work = prepare_metrics_for_calibration(metrics_df)
    rows: list[dict[str, Any]] = []
    for readiness in READINESS_ORDER:
        readiness_frame = work.loc[work["expected_readiness"] == readiness].copy()
        denom = max(1, len(readiness_frame))
        for status in EXTERNAL_STATUS_ORDER:
            count = int((readiness_frame["decision_status"] == status).sum())
            rows.append(
                {
                    "expected_readiness": readiness,
                    "decision_status": status,
                    "count": count,
                    "share_given_readiness": _round_metric(count / denom if len(readiness_frame) else 0.0),
                }
            )
    return pd.DataFrame(rows)


def summarize_readiness(metrics_df: pd.DataFrame) -> dict[str, Any]:
    distribution = build_readiness_distribution(metrics_df)
    return {
        "distribution": {
            row["expected_readiness"]: {
                "count": int(row["count"]),
                "share": _round_metric(row["share"]),
            }
            for row in distribution.to_dict(orient="records")
        }
    }


def _candidate_policy_row(row: Mapping[str, Any], policy: Mapping[str, Any]) -> tuple[str, str]:
    best_plan_id = _safe_str(row.get("best_plan_id"))
    best_action_count = _safe_int(row.get("best_action_count", 0), 0)
    zero_step = _safe_int(row.get("zero_step_flag", 0), 0) == 1
    raw_contract_pass = _safe_int(row.get("raw_contract_pass", 1), 1) == 1
    parity_pass = _safe_int(row.get("parity_pass", 1), 1) == 1
    expected_pd_improvement = _safe_float(row.get("expected_pd_improvement"), 0.0)
    realization_anchor = _safe_float(row.get("realization_anchor"), 0.0)
    confidence = _safe_float(row.get("decision_confidence"), 0.0)
    readiness = _normalize_readiness(row.get("expected_readiness"))
    offer_maturity = _safe_str(row.get("offer_maturity"), "none").lower()
    approval_ready_4w = _safe_int(row.get("approval_ready_4w", 0), 0) == 1
    best_constraint_status = _safe_str(row.get("best_constraint_status"), "valid").lower()
    plan_contract_pass = _safe_int(row.get("plan_contract_pass", 0), 0) == 1
    no_viable_plan = bool(best_action_count == 0 or not best_plan_id or not plan_contract_pass)
    invalid_best_path = bool(best_constraint_status == "invalid" or not plan_contract_pass)
    data_issue = _safe_int(row.get("data_issue_flag", 0), 0) == 1 or not raw_contract_pass or not parity_pass
    strong_execution = _safe_int(row.get("strong_execution_flag", 0), 0) == 1

    reject_gate = bool(
        zero_step
        or no_viable_plan
        or invalid_best_path
        or best_constraint_status == "invalid"
        or expected_pd_improvement < 0.01
        or realization_anchor < 0.10
    )
    approve_gate = bool(
        not reject_gate
        and raw_contract_pass
        and parity_pass
        and not data_issue
        and readiness in {"now", "week_4"}
        and realization_anchor >= _safe_float(policy.get("approved_realization_min"), 0.50)
        and expected_pd_improvement >= _safe_float(policy.get("approved_improvement_min"), 0.02)
        and confidence >= _safe_float(policy.get("approved_confidence_min"), 0.60)
        and (approval_ready_4w or strong_execution)
        and offer_maturity not in {"inactive", "provisional"}
    )
    conditional_gate = bool(
        not reject_gate
        and not approve_gate
        and best_action_count > 0
        and raw_contract_pass
        and parity_pass
        and not data_issue
        and expected_pd_improvement >= _safe_float(policy.get("conditional_improvement_min"), 0.01)
        and realization_anchor >= _safe_float(policy.get("conditional_realization_min"), 0.20)
        and confidence >= _safe_float(policy.get("conditional_confidence_min"), 0.40)
    )
    if reject_gate:
        internal = "REJECTED"
    elif approve_gate:
        internal = "APPROVED"
    elif conditional_gate:
        internal = "CONDITIONAL"
    else:
        internal = "NEEDS_REVIEW"
    external = "CONDITIONAL" if internal == "NEEDS_REVIEW" else internal
    return external, internal


def _false_positive_proxy_components(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {
            "low_realization_rate": 0.0,
            "weak_readiness_alignment_rate": 0.0,
            "internal_review_pressure_rate": 0.0,
            "false_positive_proxy": 0.0,
        }
    visible_mask = frame["candidate_decision_status"].isin(["APPROVED", "CONDITIONAL"])
    visible = frame.loc[visible_mask].copy()
    low_realization_rate = float((visible["realization_anchor"] < 0.30).mean()) if not visible.empty else 0.0
    approved = frame.loc[frame["candidate_decision_status"] == "APPROVED"].copy()
    weak_readiness_alignment_rate = (
        float((~approved["expected_readiness"].isin(["now", "week_4"])).mean()) if not approved.empty else 0.0
    )
    internal_review_pressure_rate = float(
        (
            frame["candidate_decision_status"].eq("CONDITIONAL")
            | frame["candidate_decision_status_internal"].eq("NEEDS_REVIEW")
        ).mean()
    )
    proxy = sum(
        FALSE_POSITIVE_PROXY_WEIGHTS[name] * value
        for name, value in {
            "low_realization_rate": low_realization_rate,
            "weak_readiness_alignment_rate": weak_readiness_alignment_rate,
            "internal_review_pressure_rate": internal_review_pressure_rate,
        }.items()
    )
    return {
        "low_realization_rate": _round_metric(low_realization_rate),
        "weak_readiness_alignment_rate": _round_metric(weak_readiness_alignment_rate),
        "internal_review_pressure_rate": _round_metric(internal_review_pressure_rate),
        "false_positive_proxy": _round_metric(proxy),
    }


def _policy_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    total = max(1, len(frame))
    approved_share = float((frame["candidate_decision_status"] == "APPROVED").mean())
    conditional_share = float((frame["candidate_decision_status"] == "CONDITIONAL").mean())
    rejected_share = float((frame["candidate_decision_status"] == "REJECTED").mean())
    internal_needs_review_share = float((frame["candidate_decision_status_internal"] == "NEEDS_REVIEW").mean())
    readiness_distribution = {
        readiness: {
            "count": int((frame["expected_readiness"] == readiness).sum()),
            "share": _round_metric((frame["expected_readiness"] == readiness).mean()),
        }
        for readiness in READINESS_ORDER
    }
    proxy = _false_positive_proxy_components(frame)
    return {
        "approved_share": _round_metric(approved_share),
        "conditional_share": _round_metric(conditional_share),
        "rejected_share": _round_metric(rejected_share),
        "internal_needs_review_share": _round_metric(internal_needs_review_share),
        "approve_plus_conditional_share": _round_metric(approved_share + conditional_share),
        "readiness_distribution": readiness_distribution,
        "north_star_pass": bool(
            approved_share + conditional_share >= 0.30
            and approved_share >= 0.10
            and internal_needs_review_share < 0.20
        ),
        "population": int(total),
        **proxy,
    }


def _segment_breakdown(
    frame: pd.DataFrame,
    *,
    policy_version: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    segment_axes = (
        "risk_band",
        "expected_readiness",
        "conditional_type",
        "offer_needed_flag",
        "decision_confidence_band",
    )
    for axis in segment_axes:
        if axis not in frame.columns:
            continue
        for value, segment_frame in frame.groupby(axis, dropna=False):
            metrics = _policy_metrics(segment_frame)
            rows.append(
                {
                    "policy_version": policy_version,
                    "segment_axis": axis,
                    "segment_value": _safe_str(value, "unknown"),
                    "count": int(len(segment_frame)),
                    "approved_share": metrics["approved_share"],
                    "conditional_share": metrics["conditional_share"],
                    "rejected_share": metrics["rejected_share"],
                    "internal_needs_review_share": metrics["internal_needs_review_share"],
                    "approve_plus_conditional_share": metrics["approve_plus_conditional_share"],
                    "false_positive_proxy": metrics["false_positive_proxy"],
                }
            )
    return pd.DataFrame(rows)


def _candidate_recommendation_status(row: Mapping[str, Any]) -> tuple[str, str]:
    profile_role = _safe_str(row.get("profile_role"), "candidate")
    policy_version = _safe_str(row.get("policy_version"), "analysis_candidate")
    uplift_delta = _safe_float(row.get("approve_plus_conditional_share_delta"), 0.0)
    false_positive_delta = _safe_float(row.get("false_positive_proxy_delta"), 0.0)
    internal_review_delta = _safe_float(row.get("internal_needs_review_share_delta"), 0.0)

    if profile_role == "control":
        return "blocked", f"{policy_version} is a control profile and not a promotion target."
    if uplift_delta < SHORTLIST_MIN_APPROVE_PLUS_CONDITIONAL_DELTA:
        return "blocked", "No bounded APPROVED + CONDITIONAL uplift over the shipped baseline."
    if false_positive_delta > SHORTLIST_MAX_FALSE_POSITIVE_PROXY_DELTA:
        return "blocked", "False-positive proxy regression exceeds the Phase 49 guardrail."
    if internal_review_delta > SHORTLIST_MAX_INTERNAL_REVIEW_DELTA:
        return "blocked", "Internal review pressure regression exceeds the Phase 49 guardrail."
    return "shortlisted", "Bounded yield uplift is positive while Phase 49 proxy guardrails remain within limits."


def recommend_candidate_policy(policy_comparison_df: pd.DataFrame) -> dict[str, Any]:
    if policy_comparison_df.empty:
        return {
            "recommended_candidate_policy_version": "",
            "recommended_candidate_status": "no_safe_uplift",
            "recommended_candidate_reason": "No candidate policies were evaluated.",
            "shortlisted_candidate_versions": [],
            "blocked_candidate_versions": [],
        }

    work = policy_comparison_df.copy()
    if "analysis_only" not in work.columns:
        work["analysis_only"] = 0
    if "profile_role" not in work.columns:
        work["profile_role"] = "candidate"
    if "promotion_target" not in work.columns:
        work["promotion_target"] = work["profile_role"].astype(str) != "control"

    candidate_rows = work.loc[work["analysis_only"].astype(int) == 1].copy()
    if candidate_rows.empty:
        return {
            "recommended_candidate_policy_version": "",
            "recommended_candidate_status": "no_safe_uplift",
            "recommended_candidate_reason": "No analysis-only candidate policies were available.",
            "shortlisted_candidate_versions": [],
            "blocked_candidate_versions": [],
        }

    statuses = candidate_rows.apply(
        lambda row: _candidate_recommendation_status(row.to_dict()),
        axis=1,
    )
    candidate_rows["recommendation_status"] = [pair[0] for pair in statuses]
    candidate_rows["recommendation_reason"] = [pair[1] for pair in statuses]

    shortlisted = candidate_rows.loc[candidate_rows["recommendation_status"].astype(str) == "shortlisted"].copy()
    blocked_versions = candidate_rows.loc[
        candidate_rows["recommendation_status"].astype(str) == "blocked",
        "policy_version",
    ].astype(str).tolist()
    if shortlisted.empty:
        best_blocked = candidate_rows.sort_values(
            [
                "approve_plus_conditional_share_delta",
                "false_positive_proxy_delta",
                "internal_needs_review_share_delta",
                "policy_version",
            ],
            ascending=[False, True, True, True],
        ).head(1)
        reason = (
            _safe_str(best_blocked.iloc[0].get("recommendation_reason"))
            if not best_blocked.empty
            else "No candidate satisfied the bounded Phase 49 uplift guardrails."
        )
        return {
            "recommended_candidate_policy_version": "",
            "recommended_candidate_status": "no_safe_uplift",
            "recommended_candidate_reason": reason,
            "shortlisted_candidate_versions": [],
            "blocked_candidate_versions": blocked_versions,
        }

    shortlisted = shortlisted.sort_values(
        [
            "approve_plus_conditional_share_delta",
            "approved_share_delta",
            "false_positive_proxy_delta",
            "internal_needs_review_share_delta",
            "policy_version",
        ],
        ascending=[False, False, True, True, True],
    )
    best = shortlisted.iloc[0]
    return {
        "recommended_candidate_policy_version": _safe_str(best.get("policy_version")),
        "recommended_candidate_status": "shortlisted",
        "recommended_candidate_reason": _safe_str(best.get("recommendation_reason")),
        "shortlisted_candidate_versions": shortlisted["policy_version"].astype(str).tolist(),
        "blocked_candidate_versions": blocked_versions,
    }


def build_policy_comparison(
    metrics_df: pd.DataFrame,
    *,
    policy_version_evaluated: str,
    candidate_policies: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    work = prepare_metrics_for_calibration(metrics_df)
    policy_catalog = build_policy_profile_catalog(
        policy_version_evaluated=policy_version_evaluated,
        candidate_policies=candidate_policies,
    )
    baseline = work.copy()
    baseline["candidate_decision_status"] = baseline["decision_status"]
    baseline["candidate_decision_status_internal"] = baseline["decision_status_internal"]
    baseline["policy_version"] = str(policy_version_evaluated)
    baseline["profile_role"] = "baseline"
    baseline["promotion_target"] = False
    baseline_metrics = _policy_metrics(baseline)
    comparison_rows = [
        {
            "policy_version": str(policy_version_evaluated),
            "analysis_only": 0,
            "comparison_type": "baseline",
            "profile_role": "baseline",
            "promotion_target": False,
            **baseline_metrics,
            "approved_share_delta": 0.0,
            "conditional_share_delta": 0.0,
            "rejected_share_delta": 0.0,
            "internal_needs_review_share_delta": 0.0,
            "approve_plus_conditional_share_delta": 0.0,
            "false_positive_proxy_delta": 0.0,
            "recommendation_status": "baseline",
            "recommendation_reason": "Shipped live decision policy baseline.",
        }
    ]
    shift_rows: list[dict[str, Any]] = []
    segment_frames = [_segment_breakdown(baseline, policy_version=str(policy_version_evaluated))]
    candidates = list(policy_catalog.get("profiles", [])[1:])
    for policy in candidates:
        policy_version = _safe_str(policy.get("policy_version"), "analysis_candidate")
        candidate = work.copy()
        candidate_pairs = candidate.apply(lambda row: _candidate_policy_row(row.to_dict(), policy), axis=1)
        candidate["candidate_decision_status"] = [pair[0] for pair in candidate_pairs]
        candidate["candidate_decision_status_internal"] = [pair[1] for pair in candidate_pairs]
        candidate["policy_version"] = policy_version
        candidate["profile_role"] = _safe_str(policy.get("profile_role"), "candidate")
        candidate["promotion_target"] = bool(policy.get("promotion_target", True))
        metrics = _policy_metrics(candidate)
        comparison_rows.append(
            {
                "policy_version": policy_version,
                "analysis_only": 1,
                "comparison_type": "candidate",
                "profile_role": _safe_str(policy.get("profile_role"), "candidate"),
                "promotion_target": bool(policy.get("promotion_target", True)),
                **metrics,
                "approved_share_delta": _round_metric(metrics["approved_share"] - baseline_metrics["approved_share"]),
                "conditional_share_delta": _round_metric(metrics["conditional_share"] - baseline_metrics["conditional_share"]),
                "rejected_share_delta": _round_metric(metrics["rejected_share"] - baseline_metrics["rejected_share"]),
                "internal_needs_review_share_delta": _round_metric(
                    metrics["internal_needs_review_share"] - baseline_metrics["internal_needs_review_share"]
                ),
                "approve_plus_conditional_share_delta": _round_metric(
                    metrics["approve_plus_conditional_share"] - baseline_metrics["approve_plus_conditional_share"]
                ),
                "false_positive_proxy_delta": _round_metric(
                    metrics["false_positive_proxy"] - baseline_metrics["false_positive_proxy"]
                ),
                "recommendation_status": "",
                "recommendation_reason": "",
            }
        )
        shifts = (
            candidate.assign(baseline_status=baseline["candidate_decision_status"].values)
            .groupby(["baseline_status", "candidate_decision_status"], dropna=False)
            .size()
            .reset_index(name="count")
        )
        total = max(1, len(candidate))
        for row in shifts.to_dict(orient="records"):
            shift_rows.append(
                {
                    "policy_version": policy_version,
                    "from_status": _safe_str(row.get("baseline_status")),
                    "to_status": _safe_str(row.get("candidate_decision_status")),
                    "count": int(row.get("count", 0)),
                    "share": _round_metric(_safe_float(row.get("count"), 0.0) / total),
                }
            )
        segment_frames.append(_segment_breakdown(candidate, policy_version=policy_version))
    comparison_df = pd.DataFrame(comparison_rows)
    recommendation_summary = recommend_candidate_policy(comparison_df)
    if not comparison_df.empty and "analysis_only" in comparison_df.columns:
        candidate_mask = comparison_df["analysis_only"].astype(int) == 1
        status_pairs = comparison_df.loc[candidate_mask].apply(
            lambda row: _candidate_recommendation_status(row.to_dict()),
            axis=1,
        )
        comparison_df.loc[candidate_mask, "recommendation_status"] = [pair[0] for pair in status_pairs]
        comparison_df.loc[candidate_mask, "recommendation_reason"] = [pair[1] for pair in status_pairs]
    shift_df = pd.DataFrame(shift_rows)
    segment_df = pd.concat(segment_frames, ignore_index=True) if segment_frames else pd.DataFrame()
    summary = {
        "policy_version_evaluated": str(policy_version_evaluated),
        "candidate_policy_versions_compared": [str(row["policy_version"]) for row in comparison_rows if int(row["analysis_only"]) == 1],
        "baseline_policy_metrics": comparison_rows[0],
        "north_star_pass": bool(comparison_rows[0]["north_star_pass"]),
        "policy_profile_catalog_version": POLICY_PROFILE_CATALOG_VERSION,
        **recommendation_summary,
    }
    return {
        "policy_profile_catalog": policy_catalog,
        "policy_comparison": comparison_df,
        "decision_shift_matrix": shift_df,
        "segment_breakdown": segment_df,
        "calibration_summary": summary,
        "policy_recommendation_summary": recommendation_summary,
    }


def build_calibration_review_markdown(
    *,
    selection_policy_name: str,
    cohort_purpose: str,
    funnel_summary: Mapping[str, Any],
    readiness_summary: Mapping[str, Any],
    policy_comparison_df: pd.DataFrame,
    recommendation_summary: Mapping[str, Any] | None = None,
) -> str:
    baseline_row = (
        policy_comparison_df.loc[policy_comparison_df["comparison_type"].astype(str) == "baseline"].head(1).to_dict(orient="records")
    )
    candidate_rows = policy_comparison_df.loc[policy_comparison_df["analysis_only"].astype(int) == 1].to_dict(orient="records")
    baseline = baseline_row[0] if baseline_row else {}
    lines = [
        "# Calibration Review",
        "",
        f"- Selection policy: {selection_policy_name}",
        f"- Cohort purpose: {cohort_purpose}",
        "- Guardrail: candidate policies are analysis-only and never replace shipped customer decision truth.",
        "",
        "## Baseline Funnel",
        f"- Approved share: {_round_metric(baseline.get('approved_share', 0.0)):.4f}",
        f"- Conditional share: {_round_metric(baseline.get('conditional_share', 0.0)):.4f}",
        f"- Rejected share: {_round_metric(baseline.get('rejected_share', 0.0)):.4f}",
        f"- Internal needs-review share: {_round_metric(baseline.get('internal_needs_review_share', 0.0)):.4f}",
        f"- Approve + conditional share: {_round_metric(funnel_summary.get('approve_plus_conditional_share', 0.0)):.4f}",
        f"- False-positive proxy: {_round_metric(baseline.get('false_positive_proxy', 0.0)):.4f}",
        f"- North-star pass: {bool(baseline.get('north_star_pass', False))}",
        "",
        "## Readiness",
    ]
    readiness_distribution = dict(readiness_summary.get("distribution", {}))
    for readiness in READINESS_ORDER:
        payload = dict(readiness_distribution.get(readiness, {}))
        lines.append(
            f"- {readiness}: count={int(payload.get('count', 0))}, share={_round_metric(payload.get('share', 0.0)):.4f}"
        )
    lines.extend(["", "## Candidate Policies"])
    if not candidate_rows:
        lines.append("- No candidate policies evaluated.")
    else:
        for row in candidate_rows:
            lines.append(
                f"- {row.get('policy_version', 'candidate')}: "
                f"approved_delta={_round_metric(row.get('approved_share_delta', 0.0)):.4f}, "
                f"approve_plus_conditional_delta={_round_metric(row.get('approve_plus_conditional_share_delta', 0.0)):.4f}, "
                f"false_positive_proxy_delta={_round_metric(row.get('false_positive_proxy_delta', 0.0)):.4f}, "
                f"north_star_pass={bool(row.get('north_star_pass', False))}, "
                f"status={_safe_str(row.get('recommendation_status'), 'blocked')}"
            )
    if recommendation_summary:
        lines.extend(
            [
                "",
                "## Recommendation",
                f"- Status: {_safe_str(recommendation_summary.get('recommended_candidate_status'), 'no_safe_uplift')}",
                f"- Recommended candidate: {_safe_str(recommendation_summary.get('recommended_candidate_policy_version'), 'n/a') or 'n/a'}",
                f"- Reason: {_safe_str(recommendation_summary.get('recommended_candidate_reason'), 'n/a') or 'n/a'}",
            ]
        )
    return "\n".join(lines) + "\n"
