from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Literal

from credit_coach.data.schema import PlanRecord
from credit_coach.recourse.recommendation_validity import (
    filter_invalid_numeric_plans,
    recommendation_warning_penalty,
)
from credit_coach.recourse.trajectory import (
    TRAJECTORY_JUMP_THRESHOLD,
    TRAJECTORY_MINOR_DRIFT_TOLERANCE,
    summarize_trajectory_consistency,
)

_STATUS_PRIORITY = {
    "APPROVED": 0,
    "NEEDS_REVIEW": 1,
    "REJECTED": 2,
    "ERROR": 3,
}
_CONSTRAINT_PRIORITY = {
    "valid": 0,
    "repaired": 1,
    "provisional": 2,
    "invalid": 3,
}
CANDIDATE_SOURCE_CATALOG: tuple[str, ...] = ("internal", "dice", "rule", "fallback")
_SOURCE_TIE_PRIORITY = {source: idx for idx, source in enumerate(CANDIDATE_SOURCE_CATALOG)}
_CONTENDER_BUCKET_PRIORITY = {
    "ACTIONABLE": 0,
    "APPROVAL_SHELL_ONLY": 1,
    "EMPTY": 2,
}
_VALID_OFFER_MATURITY = {"none", "inactive", "provisional", "active_rankable"}
SelectionOutcome = Literal["selected_valid_winner", "no_valid_winner"]
SelectionStage = Literal[
    "preferred_valid",
    "widened_constraint_valid",
    "widened_non_rejected_valid",
    "widened_any_valid",
    "no_valid_winner",
]


@dataclass(frozen=True)
class BestPlanSelectionResult:
    best_plan: PlanRecord | None
    selection_outcome: SelectionOutcome
    selection_stage: SelectionStage
    invalid_candidates_removed_count: int = 0
    preferred_pool_invalid_exhausted: bool = False
    no_valid_candidate_available: bool = False
    selected_from_widened_valid_pool: bool = False

    def require_best_plan(self) -> PlanRecord:
        if self.best_plan is None:
            raise AttributeError("Selection result has no best_plan")
        return self.best_plan

    def __getattr__(self, name: str) -> Any:
        return getattr(self.require_best_plan(), name)


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)


def _safe_int(v, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


def canonical_plan_source(plan: PlanRecord) -> str:
    explicit = str(getattr(plan, "plan_source", "") or "").strip().lower()
    if explicit in CANDIDATE_SOURCE_CATALOG:
        return explicit
    pid = str(getattr(plan, "plan_id", "") or "")
    if "_fallback_" in pid:
        return "fallback"
    if "_dice_" in pid:
        return "dice"
    if "_rule_" in pid:
        return "rule"
    return "internal"


def _normalized_offer_maturity(plan: PlanRecord) -> str:
    explicit = str(getattr(plan, "offer_maturity", "") or "").strip().lower()
    if explicit in _VALID_OFFER_MATURITY:
        return explicit
    if not bool(getattr(plan, "offer_plan", False)):
        return "none"
    if _safe_int(getattr(plan, "approval_pending_action_count", 0), 0) > 0:
        return "provisional"
    if _safe_int(getattr(plan, "rankable_offer_count", 0), 0) > 0:
        return "active_rankable"
    return "inactive"


def _action_has_business_semantics(action: Any) -> bool:
    return any(
        str(getattr(action, field, "") or "").strip()
        for field in ("action_key", "action_title", "action_family", "action_class")
    )


def _approval_shell_only(plan: PlanRecord) -> bool:
    actions = list(getattr(plan, "actions", []) or [])
    if not actions:
        return False
    executable_count = _safe_int(getattr(plan, "executable_action_count", 0), 0)
    if executable_count > 0:
        return False
    approval_pending_count = _safe_int(getattr(plan, "approval_pending_action_count", 0), 0)
    if approval_pending_count >= len(actions):
        return True
    approval_only_flags = [
        bool(getattr(action, "approval_pending_semantic_only", False))
        or str(getattr(action, "institutional_approval_state", "") or "").strip().lower() == "pending"
        for action in actions
    ]
    return bool(approval_only_flags) and all(approval_only_flags)


def classify_plan_contender(plan: PlanRecord) -> tuple[str, str | None]:
    actions = list(getattr(plan, "actions", []) or [])
    if not actions:
        return "EMPTY", "ZERO_ACTION"
    if _approval_shell_only(plan):
        return "APPROVAL_SHELL_ONLY", None
    visible_actions = [
        action
        for action in actions
        if _action_has_business_semantics(action)
        and str(getattr(action, "action_status", "") or "").strip().lower() != "invalid"
    ]
    if visible_actions:
        return "ACTIONABLE", None
    if str(getattr(plan, "constraint_status", "valid") or "valid").strip().lower() == "invalid":
        return "EMPTY", "SEMANTIC_EMPTY"
    return "EMPTY", "SEMANTIC_EMPTY"


def annotate_plan_planner_quality(plan: PlanRecord) -> PlanRecord:
    plan.plan_source = canonical_plan_source(plan)
    contender_bucket, empty_reason = classify_plan_contender(plan)
    plan.contender_bucket = contender_bucket
    plan.empty_candidate_reason = empty_reason
    plan.approval_shell_only_flag = contender_bucket == "APPROVAL_SHELL_ONLY"
    plan.offer_maturity = _normalized_offer_maturity(plan)
    return plan


def filter_empty_contenders(plans: list[PlanRecord]) -> tuple[list[PlanRecord], list[PlanRecord]]:
    annotated = [annotate_plan_planner_quality(plan) for plan in plans]
    kept = [plan for plan in annotated if str(getattr(plan, "contender_bucket", "") or "").upper() != "EMPTY"]
    removed = [plan for plan in annotated if str(getattr(plan, "contender_bucket", "") or "").upper() == "EMPTY"]
    return kept, removed


def candidate_source_counts(plans: list[PlanRecord]) -> dict[str, int]:
    counts = {source: 0 for source in CANDIDATE_SOURCE_CATALOG}
    for plan in plans:
        counts[canonical_plan_source(plan)] += 1
    return counts


def candidate_source_presence_flags(plans: list[PlanRecord]) -> dict[str, int]:
    counts = candidate_source_counts(plans)
    return {source: int(counts.get(source, 0) > 0) for source in CANDIDATE_SOURCE_CATALOG}


def contender_bucket_counts(plans: list[PlanRecord]) -> dict[str, int]:
    counts = {"ACTIONABLE": 0, "APPROVAL_SHELL_ONLY": 0, "EMPTY": 0}
    for plan in plans:
        annotate_plan_planner_quality(plan)
        bucket = str(getattr(plan, "contender_bucket", "") or "").strip().upper()
        if bucket in counts:
            counts[bucket] += 1
    return counts


def _plan_signature(plan: PlanRecord) -> tuple[str, ...]:
    feats = sorted({str(getattr(action, "feature_name", "") or "") for action in list(getattr(plan, "actions", []) or [])})
    return tuple(feature for feature in feats if feature)


def _jaccard_distance(a: tuple[str, ...], b: tuple[str, ...]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    union = len(sa | sb)
    if union <= 0:
        return 0.0
    return float(1.0 - (len(sa & sb) / union))


def candidate_pool_diversity_index(plans: list[PlanRecord]) -> float:
    if len(plans) <= 1:
        return 0.0
    sigs = [_plan_signature(plan) for plan in plans]
    distances: list[float] = []
    for i in range(len(sigs)):
        for j in range(i + 1, len(sigs)):
            distances.append(_jaccard_distance(sigs[i], sigs[j]))
    if not distances:
        return 0.0
    return float(sum(distances) / float(len(distances)))


def candidate_source_entropy(plans: list[PlanRecord]) -> float:
    if not plans:
        return 0.0
    counts = candidate_source_counts(plans)
    total = float(len(plans))
    nonzero = [count for count in counts.values() if count > 0]
    if not nonzero:
        return 0.0
    entropy = 0.0
    for count in nonzero:
        probability = float(count) / total
        if probability > 0.0:
            entropy -= probability * math.log(probability, 2.0)
    max_entropy = math.log(max(1, len(nonzero)), 2.0)
    if max_entropy <= 0.0:
        return 0.0
    return float(entropy / max_entropy)


def execution_aware_value(plan: PlanRecord, *, base_pd: float | None = None, tau: float | None = None) -> float:
    explicit = getattr(plan, "expected_recovery_proxy", None)
    if explicit is not None:
        return max(0.0, _safe_float(explicit, 0.0))
    return _expected_pd_improvement(plan, base_pd=base_pd, tau=tau)


def _plan_cost(plan: PlanRecord) -> float:
    total = 0.0
    for action in plan.actions:
        total += _safe_float(getattr(action, "estimated_cost_usd", 0.0), 0.0)
    return float(total)


def _plan_execution_probability(plan: PlanRecord) -> float:
    execution_probability = getattr(plan, "plan_execution_probability", None)
    if execution_probability is None:
        return 0.0
    return max(0.0, min(1.0, _safe_float(execution_probability, 0.0)))


def _nominal_pd_improvement(plan: PlanRecord, *, base_pd: float | None, tau: float | None) -> float:
    explicit = getattr(plan, "nominal_pd_improvement", None)
    if explicit is not None:
        return max(0.0, _safe_float(explicit, 0.0))
    predicted_pd = getattr(plan, "predicted_pd", None)
    if predicted_pd is None:
        return 0.0
    if base_pd is not None:
        return max(0.0, float(base_pd) - float(predicted_pd))
    if tau is not None:
        return max(0.0, float(tau) - float(predicted_pd))
    return 0.0


def _expected_pd_improvement(plan: PlanRecord, *, base_pd: float | None, tau: float | None) -> float:
    explicit = getattr(plan, "expected_pd_improvement", None)
    if explicit is not None:
        return max(0.0, _safe_float(explicit, 0.0))
    return float(_plan_execution_probability(plan) * _nominal_pd_improvement(plan, base_pd=base_pd, tau=tau))


def _expected_recovery_proxy(plan: PlanRecord) -> float:
    explicit = getattr(plan, "expected_recovery_proxy", None)
    if explicit is None:
        return 0.0
    return _safe_float(explicit, 0.0)


def _approval_dependent_plan_probability(plan: PlanRecord) -> float:
    probability = getattr(plan, "approval_dependent_plan_probability", None)
    if probability is None:
        return 0.0
    return max(0.0, min(1.0, _safe_float(probability, 0.0)))


def _mean_group_difficulty_score(plan: PlanRecord) -> float:
    difficulty = getattr(plan, "mean_group_difficulty_score", None)
    if difficulty is None:
        return 0.0
    return max(0.0, min(1.0, _safe_float(difficulty, 0.0)))


def _peak_group_difficulty_score(plan: PlanRecord) -> float:
    difficulty = getattr(plan, "peak_group_difficulty_score", None)
    if difficulty is None:
        return _mean_group_difficulty_score(plan)
    return max(0.0, min(1.0, _safe_float(difficulty, 0.0)))


def _follow_through_readiness_label(plan: PlanRecord) -> str:
    return str(getattr(plan, "follow_through_readiness_label", "") or "").strip().lower()


def _execution_gap(plan: PlanRecord, *, base_pd: float | None, tau: float | None) -> float:
    nominal = _nominal_pd_improvement(plan, base_pd=base_pd, tau=tau)
    expected = _expected_pd_improvement(plan, base_pd=base_pd, tau=tau)
    return max(0.0, nominal - expected)


def _execution_rank_penalty(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    segment_context: dict[str, Any] | None = None,
    high_risk: bool = False,
) -> float:
    execution_probability = _plan_execution_probability(plan)
    approval_probability = _approval_dependent_plan_probability(plan)
    nominal = _nominal_pd_improvement(plan, base_pd=base_pd, tau=tau)
    expected = _expected_pd_improvement(plan, base_pd=base_pd, tau=tau)
    gap = max(0.0, nominal - expected)
    risk_band = str((segment_context or {}).get("risk_band", "")).strip().lower()
    consistency = _trajectory_consistency(plan)
    mean_group_difficulty = _mean_group_difficulty_score(plan)
    peak_group_difficulty = _peak_group_difficulty_score(plan)
    follow_through_readiness = _follow_through_readiness_label(plan)
    action_group_count = max(
        _safe_int(getattr(plan, "executable_action_group_count", 0), 0),
        len(list(getattr(plan, "actions", []))),
    )

    penalty = 0.0
    penalty += max(0.0, 0.65 - execution_probability) * 120.0
    penalty += gap * 140.0
    penalty += max(0.0, peak_group_difficulty - 0.55) * 28.0
    penalty += max(0.0, mean_group_difficulty - 0.45) * 14.0
    penalty += max(0.0, float(action_group_count - 2)) * 4.5

    if nominal >= 0.05 and execution_probability < 0.45:
        penalty += 10.0
    if nominal >= 0.08 and expected <= (0.50 * nominal):
        penalty += 12.0
    if follow_through_readiness == "low":
        penalty += 12.0
    elif follow_through_readiness == "moderate":
        penalty += 3.0
    if bool(consistency["weak_early_health"]):
        penalty += 16.0
    if str(consistency["primary_checkpoint_status"]) == "missed":
        penalty += 10.0
    if bool(consistency["trajectory_jump_flag"]):
        penalty += 14.0
    if bool(consistency["non_monotonic_flag"]):
        penalty += 9.0
    if bool(consistency["checkpoint_inconsistency_flag"]):
        penalty += 10.0

    approval_pending_count = _safe_int(getattr(plan, "approval_pending_action_count", 0), 0)
    if approval_pending_count > 0:
        penalty += 12.0 + (6.0 * float(approval_pending_count))
        penalty += max(0.0, 0.55 - approval_probability) * 40.0

    constraint_status = str(getattr(plan, "constraint_status", "valid") or "valid").strip().lower()
    if constraint_status == "provisional":
        penalty += 28.0
    elif constraint_status == "repaired":
        penalty += 4.0

    if high_risk or risk_band == "high":
        penalty *= 1.20
    return float(penalty)


def _execution_defensibility_score(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    segment_context: dict[str, Any] | None = None,
    high_risk: bool = False,
) -> float:
    expected = _expected_pd_improvement(plan, base_pd=base_pd, tau=tau)
    execution_probability = _plan_execution_probability(plan)
    approval_probability = _approval_dependent_plan_probability(plan)
    penalty = _execution_rank_penalty(
        plan,
        base_pd=base_pd,
        tau=tau,
        segment_context=segment_context,
        high_risk=high_risk,
    )
    score = (expected * 100.0) + (execution_probability * 20.0) + (approval_probability * 5.0) - penalty
    return float(score)


def _phase_action_shares(plan: PlanRecord) -> tuple[float, float, float]:
    actions = list(plan.actions)
    if not actions:
        return 0.0, 0.0, 0.0
    total = float(len(actions))
    phase1 = sum(1 for action in actions if _safe_int(getattr(action, "time_months", 1), 1) <= 1)
    phase2 = sum(1 for action in actions if _safe_int(getattr(action, "time_months", 1), 1) <= 3)
    return float(phase1 / total), float(phase2 / total), 1.0


def _trajectory_checkpoint_pds(plan: PlanRecord, *, base_pd: float | None, tau: float | None) -> tuple[float, float, float]:
    checkpoint_map: dict[int, float] = {}
    for checkpoint in list(getattr(plan, "trajectory_checkpoints", [])):
        week = _safe_int(getattr(checkpoint, "week", 0), 0)
        predicted_pd = getattr(checkpoint, "predicted_pd", None)
        if week > 0 and predicted_pd is not None:
            checkpoint_map[int(week)] = _safe_float(predicted_pd, 1.0)
    if checkpoint_map:
        pd4 = checkpoint_map.get(4, checkpoint_map.get(12, checkpoint_map.get(24, _safe_float(base_pd, 1.0))))
        pd12 = checkpoint_map.get(12, checkpoint_map.get(24, pd4))
        pd24 = checkpoint_map.get(24, checkpoint_map.get(12, pd12))
        return float(pd4), float(pd12), float(pd24)

    starting_pd = _safe_float(base_pd, _safe_float(tau, 1.0))
    final_pd = _safe_float(getattr(plan, "predicted_pd", None), starting_pd)
    total_improvement = max(0.0, starting_pd - final_pd)
    phase1_share, phase2_share, _ = _phase_action_shares(plan)
    pd4 = starting_pd - (total_improvement * max(0.15, phase1_share))
    pd12 = starting_pd - (total_improvement * max(0.45, phase2_share))
    pd24 = final_pd
    return float(pd4), float(pd12), float(pd24)


def _trajectory_consistency(plan: PlanRecord) -> dict[str, Any]:
    checkpoints = list(getattr(plan, "trajectory_checkpoints", []))
    if not checkpoints:
        return {
            "primary_checkpoint_status": "at_risk",
            "confirmation_checkpoint_status": "at_risk",
            "stability_checkpoint_status": "at_risk",
            "weak_early_health": False,
            "trajectory_jump_flag": False,
            "non_monotonic_flag": False,
            "checkpoint_inconsistency_flag": False,
        }
    return summarize_trajectory_consistency(checkpoints)


def _phase_aware_priority_score(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    segment_context: dict[str, Any] | None = None,
) -> float:
    pd4, pd12, pd24 = _trajectory_checkpoint_pds(plan, base_pd=base_pd, tau=tau)
    consistency = _trajectory_consistency(plan)
    starting_pd = _safe_float(base_pd, max(pd4, pd12, pd24))
    early_improvement = max(0.0, starting_pd - pd4)
    mid_improvement = max(0.0, starting_pd - pd12)
    long_improvement = max(0.0, starting_pd - pd24)
    pass4 = 1.0 if tau is not None and pd4 <= float(tau) else 0.0
    pass12 = 1.0 if tau is not None and pd12 <= float(tau) else 0.0
    pass24 = 1.0 if tau is not None and pd24 <= float(tau) else 0.0
    regression_tolerance = TRAJECTORY_MINOR_DRIFT_TOLERANCE
    regression_penalty = max(0.0, pd12 - (pd4 + regression_tolerance)) + max(0.0, pd24 - (pd12 + regression_tolerance))
    phase1_share, phase2_share, _ = _phase_action_shares(plan)
    primary_checkpoint_status = str(consistency["primary_checkpoint_status"])
    weak_early_health = bool(consistency["weak_early_health"])
    early_health_ok = bool(
        primary_checkpoint_status == "on_track"
        or (pass4 > 0.0)
        or early_improvement >= max(TRAJECTORY_JUMP_THRESHOLD, 0.35 * max(long_improvement, 0.01))
    )
    risk_band = str((segment_context or {}).get("risk_band", "")).strip().lower()
    if risk_band == "high":
        weights = (0.70, 0.20, 0.10)
    else:
        weights = (0.55, 0.30, 0.15)
    long_bonus_multiplier = 1.0 if early_health_ok else 0.15
    score = (
        (weights[0] * ((early_improvement * 100.0) + (8.0 * pass4) + (5.0 * phase1_share)))
        + (weights[1] * ((mid_improvement * 100.0) + (5.0 * pass12) + (3.0 * phase2_share)))
        + (weights[2] * long_bonus_multiplier * ((long_improvement * 100.0) + (4.0 * pass24)))
        - (35.0 * regression_penalty)
    )
    if weak_early_health:
        score -= 8.0
    if primary_checkpoint_status == "missed":
        score -= 6.0
    if bool(consistency["trajectory_jump_flag"]):
        score -= 12.0
    if bool(consistency["non_monotonic_flag"]):
        score -= 8.0
    if bool(consistency["checkpoint_inconsistency_flag"]):
        score -= 10.0
    return float(score)


def _contender_bucket_priority(plan: PlanRecord) -> int:
    annotate_plan_planner_quality(plan)
    bucket = str(getattr(plan, "contender_bucket", "") or "").strip().upper()
    return int(_CONTENDER_BUCKET_PRIORITY.get(bucket, 3))


def _offer_maturity_penalty(plan: PlanRecord) -> int:
    maturity = _normalized_offer_maturity(plan)
    if maturity in {"none", "active_rankable"}:
        return 0
    if maturity == "provisional":
        return 1
    return 2


def _recommendation_warning_penalty(plan: PlanRecord) -> float:
    combined = float(recommendation_warning_penalty(plan)) + float(
        getattr(plan, "dice_semantic_warning_penalty", 0.0) or 0.0
    )
    return float(min(30.0, combined))


def _source_tie_rank(plan: PlanRecord) -> int:
    return int(_SOURCE_TIE_PRIORITY.get(canonical_plan_source(plan), len(_SOURCE_TIE_PRIORITY)))


def _near_tie_signature(
    plan: PlanRecord,
    *,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> tuple[int, int, int, float]:
    return (
        _constraint_priority(plan),
        _status_priority(plan.status),
        _contender_bucket_priority(plan),
        _gate_pass_score(
            plan,
            tau=tau,
            min_reliability=min_reliability,
            min_worst_risk_margin=min_worst_risk_margin,
        ),
    )


def _is_near_tie(
    leader: PlanRecord,
    challenger: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> bool:
    if _near_tie_signature(
        leader,
        tau=tau,
        min_reliability=min_reliability,
        min_worst_risk_margin=min_worst_risk_margin,
    ) != _near_tie_signature(
        challenger,
        tau=tau,
        min_reliability=min_reliability,
        min_worst_risk_margin=min_worst_risk_margin,
    ):
        return False
    if abs(_expected_pd_improvement(leader, base_pd=base_pd, tau=tau) - _expected_pd_improvement(challenger, base_pd=base_pd, tau=tau)) > 0.01:
        return False
    if abs(_plan_execution_probability(leader) - _plan_execution_probability(challenger)) > 0.08:
        return False
    if abs(_plan_cost(leader) - _plan_cost(challenger)) > 150.0:
        return False
    if abs(_safe_float(getattr(leader, "predicted_pd", 1.0), 1.0) - _safe_float(getattr(challenger, "predicted_pd", 1.0), 1.0)) > 0.02:
        return False
    return True


def _select_with_source_tiebreak(
    ranked: list[PlanRecord],
    *,
    base_pd: float | None,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> PlanRecord:
    leader = ranked[0]
    tie_group = [leader]
    for challenger in ranked[1:]:
        if not _is_near_tie(
            leader,
            challenger,
            base_pd=base_pd,
            tau=tau,
            min_reliability=min_reliability,
            min_worst_risk_margin=min_worst_risk_margin,
        ):
            break
        tie_group.append(challenger)
    if len(tie_group) == 1:
        return leader
    if len({canonical_plan_source(plan) for plan in tie_group}) == 1:
        return leader
    return sorted(
        tie_group,
        key=lambda plan: (
            _recommendation_warning_penalty(plan),
            _source_tie_rank(plan),
            _offer_maturity_penalty(plan),
            _plan_cost(plan),
            int(len(list(getattr(plan, "actions", []) or []))),
            float(getattr(plan, "predicted_pd", 1.0) or 1.0),
        ),
    )[0]


def _trajectory_policy_label(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    segment_context: dict[str, Any] | None = None,
) -> str:
    pd4, pd12, pd24 = _trajectory_checkpoint_pds(plan, base_pd=base_pd, tau=tau)
    consistency = _trajectory_consistency(plan)
    starting_pd = _safe_float(base_pd, max(pd4, pd12, pd24))
    early_improvement = max(0.0, starting_pd - pd4)
    long_improvement = max(0.0, starting_pd - pd24)
    phase1_share, _, _ = _phase_action_shares(plan)
    early_gate_ok = bool(tau is not None and pd4 <= float(tau))
    execution_probability = _plan_execution_probability(plan)
    weak_early_health = bool(consistency["weak_early_health"])
    early_health_ok = bool(
        str(consistency["primary_checkpoint_status"]) == "on_track"
        or early_gate_ok
        or early_improvement >= max(TRAJECTORY_JUMP_THRESHOLD, 0.35 * max(long_improvement, 0.01))
    )
    if weak_early_health and (
        long_improvement > max(0.05, early_improvement + 0.02)
        or execution_probability < 0.55
        or bool(consistency["trajectory_jump_flag"])
        or bool(consistency["non_monotonic_flag"])
    ):
        label = "long_horizon_heavy"
    elif early_health_ok and phase1_share >= 0.5:
        label = "stabilize_first"
    elif early_gate_ok:
        label = "stabilize_first"
    else:
        label = "balanced_progress"

    if label == "stabilize_first" and execution_probability < 0.45:
        label = "balanced_progress"
    if label != "long_horizon_heavy" and (
        bool(consistency["checkpoint_inconsistency_flag"])
        or (execution_probability < 0.35 and weak_early_health)
    ):
        label = "long_horizon_heavy"
    return label


def _annotate_trajectory_policy(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    segment_context: dict[str, Any] | None = None,
) -> None:
    plan.trajectory_policy_score = _phase_aware_priority_score(
        plan,
        base_pd=base_pd,
        tau=tau,
        segment_context=segment_context,
    )
    plan.trajectory_policy_label = _trajectory_policy_label(
        plan,
        base_pd=base_pd,
        tau=tau,
        segment_context=segment_context,
    )


def _short_term_action_signal(plan: PlanRecord, short_term_cfg: dict | None) -> float:
    short_term_cfg = short_term_cfg or {}
    if not bool(short_term_cfg.get("enabled", False)):
        return 0.0
    actions = list(plan.actions)
    if not actions:
        return 0.0
    phase1_cutoff_month = max(1, int(_safe_float(short_term_cfg.get("phase1_cutoff_month", 1), 1)))
    phase2_cutoff_month = max(phase1_cutoff_month, int(_safe_float(short_term_cfg.get("phase2_cutoff_month", 3), 3)))
    phase1_share_weight = max(0.0, _safe_float(short_term_cfg.get("phase1_share_weight", 1.0), 1.0))
    phase2_share_weight = max(0.0, _safe_float(short_term_cfg.get("phase2_share_weight", 0.35), 0.35))
    min_phase1_actions = max(0, int(_safe_float(short_term_cfg.get("min_phase1_actions", 1), 1)))

    action_months = [max(1, int(_safe_float(getattr(a, "time_months", 1), 1))) for a in actions]
    total = float(max(1, len(action_months)))
    phase1_count = int(sum(1 for m in action_months if m <= phase1_cutoff_month))
    phase2_count = int(sum(1 for m in action_months if m <= phase2_cutoff_month))
    phase1_share = float(phase1_count / total)
    phase2_share = float(phase2_count / total)

    scarcity_penalty = 0.0
    if phase1_count < int(min_phase1_actions):
        scarcity_penalty = float(min_phase1_actions - phase1_count)
    return float((phase1_share_weight * phase1_share) + (phase2_share_weight * phase2_share) - scarcity_penalty)


def _status_priority(status: str | None) -> int:
    key = str(status or "").strip().upper()
    return int(_STATUS_PRIORITY.get(key, 4))


def _prefer_non_rejected(plans: list[PlanRecord]) -> list[PlanRecord]:
    preferred = [p for p in plans if _status_priority(getattr(p, "status", "")) <= _STATUS_PRIORITY["NEEDS_REVIEW"]]
    return preferred if preferred else plans


def _constraint_priority(plan: PlanRecord) -> int:
    key = str(getattr(plan, "constraint_status", "valid") or "valid").strip().lower()
    return int(_CONSTRAINT_PRIORITY.get(key, 4))


def _prefer_constraint_eligible(plans: list[PlanRecord]) -> list[PlanRecord]:
    preferred = [p for p in plans if _constraint_priority(p) <= _CONSTRAINT_PRIORITY["repaired"]]
    return preferred if preferred else plans


def _ci_high_with_fallback(plan: PlanRecord, tau: float | None) -> float:
    if plan.ci_high is not None:
        return float(plan.ci_high)
    if plan.predicted_pd is not None:
        return float(plan.predicted_pd)
    if tau is not None:
        return float(tau) + 1.0
    return 1.0


def _reliability_with_fallback(plan: PlanRecord) -> float:
    if plan.reliability is not None:
        return float(plan.reliability)
    return 0.0


def _worst_margin_with_fallback(plan: PlanRecord) -> float:
    if plan.robust_worst_risk_margin is not None:
        return float(plan.robust_worst_risk_margin)
    return -1.0


def _gate_pass_score(
    plan: PlanRecord,
    *,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> float:
    consistency = _trajectory_consistency(plan)
    ci_margin = 0.0
    if tau is not None and plan.ci_high is not None:
        ci_margin = float(tau) - float(plan.ci_high)

    rel_margin = 0.0
    if min_reliability is not None and plan.reliability is not None:
        rel_margin = float(plan.reliability) - float(min_reliability)

    worst_margin = 0.0
    if min_worst_risk_margin is not None and plan.robust_worst_risk_margin is not None:
        worst_margin = float(plan.robust_worst_risk_margin) - float(min_worst_risk_margin)

    score = float((0.6 * ci_margin) + (0.25 * rel_margin) + (0.15 * worst_margin))
    if bool(consistency["weak_early_health"]):
        score -= 0.30
    if bool(consistency["trajectory_jump_flag"]):
        score -= 0.15
    if bool(consistency["checkpoint_inconsistency_flag"]):
        score -= 0.10
    return score


def _gate_violations(
    plan: PlanRecord,
    *,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> tuple[float, float, float]:
    ci_violation = 0.0
    if tau is not None:
        ci_violation = max(0.0, _ci_high_with_fallback(plan, tau) - float(tau))

    rel_violation = 0.0
    if min_reliability is not None:
        rel_violation = max(0.0, float(min_reliability) - _reliability_with_fallback(plan))

    worst_violation = 0.0
    if min_worst_risk_margin is not None:
        worst_violation = max(0.0, float(min_worst_risk_margin) - _worst_margin_with_fallback(plan))
    return float(ci_violation), float(rel_violation), float(worst_violation)


def _gate_margins(
    plan: PlanRecord,
    *,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> tuple[float, float, float]:
    ci_margin = 0.0
    if tau is not None:
        ci_margin = float(tau) - _ci_high_with_fallback(plan, tau)

    rel_margin = 0.0
    if min_reliability is not None:
        rel_margin = _reliability_with_fallback(plan) - float(min_reliability)

    worst_margin = 0.0
    if min_worst_risk_margin is not None:
        worst_margin = _worst_margin_with_fallback(plan) - float(min_worst_risk_margin)
    return float(ci_margin), float(rel_margin), float(worst_margin)


def _gate_total_violation(
    plan: PlanRecord,
    *,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
) -> float:
    ci_v, rel_v, worst_v = _gate_violations(
        plan,
        tau=tau,
        min_reliability=min_reliability,
        min_worst_risk_margin=min_worst_risk_margin,
    )
    return float(ci_v + rel_v + worst_v)


def _normalize_denied_weights(raw: dict | None) -> dict[str, float]:
    raw = raw or {}
    defaults = {
        "ci": 0.45,
        "reliability": 0.30,
        "worst_margin": 0.20,
        "cost": 0.03,
        "sparsity": 0.02,
        "nominal_margin": 0.20,
        "reliability_margin_bonus": 0.20,
        "worst_margin_bonus": 0.10,
        "short_term": 0.15,
    }
    return {k: max(0.0, _safe_float(raw.get(k, v), v)) for k, v in defaults.items()}


def _normalize_high_risk_weights(raw: dict | None) -> dict[str, float]:
    raw = raw or {}
    defaults = {
        "pd_improvement": 0.55,
        "gate_pass": 0.20,
        "residual_pd": 0.25,
        "ci": 0.35,
        "reliability": 0.20,
        "worst_margin": 0.20,
        "cost": 0.03,
        "sparsity": 0.02,
        "short_term": 0.20,
    }
    return {k: max(0.0, _safe_float(raw.get(k, v), v)) for k, v in defaults.items()}


def _denied_priority_score(
    plan: PlanRecord,
    *,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
    denied_objective_cfg: dict | None,
) -> float:
    denied_objective_cfg = denied_objective_cfg or {}
    weights = _normalize_denied_weights(denied_objective_cfg.get("weights", {}))
    short_term_signal = _short_term_action_signal(
        plan,
        denied_objective_cfg.get("short_term", {})
        if isinstance(denied_objective_cfg.get("short_term", {}), dict)
        else {},
    )
    squared = bool(denied_objective_cfg.get("squared_violation", True))
    exponent = 2 if squared else 1
    penalty_scale = max(0.0, _safe_float(denied_objective_cfg.get("penalty_scale", 140.0), 140.0))

    ci_v, rel_v, worst_v = _gate_violations(
        plan,
        tau=tau,
        min_reliability=min_reliability,
        min_worst_risk_margin=min_worst_risk_margin,
    )
    loss = (
        (weights["ci"] * (ci_v**exponent))
        + (weights["reliability"] * (rel_v**exponent))
        + (weights["worst_margin"] * (worst_v**exponent))
        + (weights["cost"] * _plan_cost(plan) * 0.001)
        + (weights["sparsity"] * float(len(plan.actions)))
    )
    nominal_margin = 0.0
    if tau is not None and plan.predicted_pd is not None:
        nominal_margin = max(0.0, float(tau) - float(plan.predicted_pd))
    bonus = weights["nominal_margin"] * nominal_margin
    rel_margin = 0.0
    if min_reliability is not None and plan.reliability is not None:
        rel_margin = max(0.0, float(plan.reliability) - float(min_reliability))
    worst_margin = 0.0
    if min_worst_risk_margin is not None and plan.robust_worst_risk_margin is not None:
        worst_margin = max(0.0, float(plan.robust_worst_risk_margin) - float(min_worst_risk_margin))
    bonus += (weights["reliability_margin_bonus"] * rel_margin) + (weights["worst_margin_bonus"] * worst_margin)
    bonus += weights["short_term"] * short_term_signal
    pass_bonus = 10.0 if plan.status == "APPROVED" else 0.0
    return float(pass_bonus + (bonus * 100.0) - (loss * penalty_scale))


def _high_risk_priority_score(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
    high_risk_objective_cfg: dict | None,
) -> float:
    high_risk_objective_cfg = high_risk_objective_cfg or {}
    weights = _normalize_high_risk_weights(high_risk_objective_cfg.get("weights", {}))
    short_term_signal = _short_term_action_signal(
        plan,
        high_risk_objective_cfg.get("short_term", {})
        if isinstance(high_risk_objective_cfg.get("short_term", {}), dict)
        else {},
    )
    penalty_scale = max(0.0, _safe_float(high_risk_objective_cfg.get("penalty_scale", 80.0), 80.0))
    hard_gate = bool(high_risk_objective_cfg.get("hard_gate", True))
    hard_violation_penalty = max(0.0, _safe_float(high_risk_objective_cfg.get("hard_violation_penalty", 120.0), 120.0))

    pd_improvement = 0.0
    if base_pd is not None and plan.predicted_pd is not None:
        pd_improvement = max(0.0, float(base_pd) - float(plan.predicted_pd))

    residual_pd = 0.0
    if tau is not None and plan.predicted_pd is not None:
        residual_pd = max(0.0, float(plan.predicted_pd) - float(tau))

    ci_margin = 0.0
    rel_margin = 0.0
    worst_margin = 0.0
    ci_v = 0.0
    rel_v = 0.0
    worst_v = 0.0

    if tau is not None:
        ci_h = _ci_high_with_fallback(plan, tau)
        ci_margin = float(tau) - ci_h
        ci_v = max(0.0, ci_h - float(tau))
    if min_reliability is not None:
        rel = _reliability_with_fallback(plan)
        rel_margin = rel - float(min_reliability)
        rel_v = max(0.0, float(min_reliability) - rel)
    if min_worst_risk_margin is not None:
        worst = _worst_margin_with_fallback(plan)
        worst_margin = worst - float(min_worst_risk_margin)
        worst_v = max(0.0, float(min_worst_risk_margin) - worst)

    gate_pass = float((0.6 * ci_margin) + (0.25 * rel_margin) + (0.15 * worst_margin))
    violation = (
        (weights["ci"] * ci_v)
        + (weights["reliability"] * rel_v)
        + (weights["worst_margin"] * worst_v)
    )
    cost_pen = (weights["cost"] * _plan_cost(plan) * 0.001) + (weights["sparsity"] * float(len(plan.actions)))

    score = (
        (weights["pd_improvement"] * pd_improvement * 100.0)
        + (weights["gate_pass"] * gate_pass * 100.0)
        + (weights["short_term"] * short_term_signal * 100.0)
        - (weights["residual_pd"] * residual_pd * 100.0)
        - (penalty_scale * violation)
        - cost_pen
    )
    if hard_gate and (ci_v > 0.0 or rel_v > 0.0 or worst_v > 0.0):
        score -= float(hard_violation_penalty * (1.0 + ci_v + rel_v + worst_v))
    elif hard_gate:
        score += float(hard_violation_penalty * 0.05)
    if plan.status == "APPROVED":
        score += 20.0
    return float(score)


def _denied_sort_key(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
    denied_objective_cfg: dict[str, Any] | None,
    fairness_penalty: float = 0.0,
) -> tuple:
    fairness_cfg = (
        denied_objective_cfg.get("fairness_balance", {})
        if isinstance((denied_objective_cfg or {}).get("fairness_balance", {}), dict)
        else {}
    )
    fairness_enabled = bool(fairness_cfg.get("enabled", False))
    fairness_penalty_threshold = max(0.0, _safe_float(fairness_cfg.get("penalty_threshold", 0.01), 0.01))
    advantaged_cost_scale = max(0.0, _safe_float(fairness_cfg.get("advantaged_cost_scale", 0.50), 0.50))
    disadvantaged_gate_bonus = max(0.0, _safe_float(fairness_cfg.get("disadvantaged_gate_bonus", 0.20), 0.20))
    ci_margin, rel_margin, worst_margin = _gate_margins(
        plan,
        tau=tau,
        min_reliability=min_reliability,
        min_worst_risk_margin=min_worst_risk_margin,
    )
    base_priority = _denied_priority_score(
        plan,
        tau=tau,
        min_reliability=min_reliability,
        min_worst_risk_margin=min_worst_risk_margin,
        denied_objective_cfg=denied_objective_cfg,
    )
    if fairness_enabled:
        if float(fairness_penalty) > fairness_penalty_threshold:
            base_priority -= float(fairness_penalty) * advantaged_cost_scale * (_plan_cost(plan) * 0.01)
        else:
            base_priority += disadvantaged_gate_bonus * max(
                0.0,
                _gate_pass_score(
                    plan,
                    tau=tau,
                    min_reliability=min_reliability,
                    min_worst_risk_margin=min_worst_risk_margin,
                ),
            ) * 10.0
    return (
        _constraint_priority(plan),
        _status_priority(plan.status),
        _contender_bucket_priority(plan),
        _recommendation_warning_penalty(plan),
        _gate_total_violation(
            plan,
            tau=tau,
            min_reliability=min_reliability,
            min_worst_risk_margin=min_worst_risk_margin,
        ),
        -ci_margin,
        -rel_margin,
        -worst_margin,
        _execution_rank_penalty(
            plan,
            base_pd=base_pd,
            tau=tau,
            high_risk=False,
        ),
        -_execution_defensibility_score(
            plan,
            base_pd=base_pd,
            tau=tau,
            high_risk=False,
        ),
        -_safe_float(getattr(plan, "trajectory_policy_score", 0.0), 0.0),
        -_expected_pd_improvement(plan, base_pd=base_pd, tau=tau),
        -_plan_execution_probability(plan),
        -_expected_recovery_proxy(plan),
        _offer_maturity_penalty(plan),
        int(len(plan.actions)),
        _plan_cost(plan),
        plan.predicted_pd or 1.0,
        -float(base_priority),
    )


def _high_risk_sort_key(
    plan: PlanRecord,
    *,
    base_pd: float | None,
    tau: float | None,
    min_reliability: float | None,
    min_worst_risk_margin: float | None,
    high_risk_objective_cfg: dict[str, Any] | None,
    fairness_penalty: float = 0.0,
    denied_objective_cfg: dict[str, Any] | None = None,
) -> tuple:
    fairness_cfg = (
        denied_objective_cfg.get("fairness_balance", {})
        if isinstance((denied_objective_cfg or {}).get("fairness_balance", {}), dict)
        else {}
    )
    fairness_enabled = bool(fairness_cfg.get("enabled", False))
    fairness_penalty_threshold = max(0.0, _safe_float(fairness_cfg.get("penalty_threshold", 0.01), 0.01))
    advantaged_cost_scale = max(0.0, _safe_float(fairness_cfg.get("advantaged_cost_scale", 0.50), 0.50))
    disadvantaged_gate_bonus = max(0.0, _safe_float(fairness_cfg.get("disadvantaged_gate_bonus", 0.20), 0.20))

    high_violation = 0.0
    if tau is not None:
        high_violation += max(0.0, _ci_high_with_fallback(plan, tau) - float(tau))
    if min_reliability is not None:
        high_violation += max(0.0, float(min_reliability) - _reliability_with_fallback(plan))
    if min_worst_risk_margin is not None:
        high_violation += max(0.0, float(min_worst_risk_margin) - _worst_margin_with_fallback(plan))
    base_priority = _high_risk_priority_score(
        plan,
        base_pd=base_pd,
        tau=tau,
        min_reliability=min_reliability,
        min_worst_risk_margin=min_worst_risk_margin,
        high_risk_objective_cfg=high_risk_objective_cfg,
    )
    if fairness_enabled:
        if float(fairness_penalty) > fairness_penalty_threshold:
            base_priority -= float(fairness_penalty) * advantaged_cost_scale * (_plan_cost(plan) * 0.01)
        else:
            base_priority += disadvantaged_gate_bonus * max(
                0.0,
                _gate_pass_score(
                    plan,
                    tau=tau,
                    min_reliability=min_reliability,
                    min_worst_risk_margin=min_worst_risk_margin,
                ),
            ) * 10.0
    return (
        _constraint_priority(plan),
        _status_priority(plan.status),
        _contender_bucket_priority(plan),
        _recommendation_warning_penalty(plan),
        float(high_violation),
        _execution_rank_penalty(
            plan,
            base_pd=base_pd,
            tau=tau,
            segment_context={"risk_band": "high"},
            high_risk=True,
        ),
        -_execution_defensibility_score(
            plan,
            base_pd=base_pd,
            tau=tau,
            segment_context={"risk_band": "high"},
            high_risk=True,
        ),
        -_safe_float(getattr(plan, "trajectory_policy_score", 0.0), 0.0),
        -_expected_pd_improvement(plan, base_pd=base_pd, tau=tau),
        -_plan_execution_probability(plan),
        -_expected_recovery_proxy(plan),
        _offer_maturity_penalty(plan),
        -float(base_priority),
        int(len(plan.actions)),
        _plan_cost(plan),
        plan.predicted_pd or 1.0,
    )


def choose_best_plan(
    plans: list[PlanRecord],
    *,
    base_pd: float | None = None,
    tau: float | None = None,
    min_reliability: float | None = None,
    min_worst_risk_margin: float | None = None,
    fairness_penalty: float = 0.0,
    denied_mode: bool = False,
    segment_context: dict[str, Any] | None = None,
    denied_objective_cfg: dict[str, Any] | None = None,
) -> BestPlanSelectionResult:
    if not plans:
        raise ValueError("No plans provided")
    for plan in plans:
        annotate_plan_planner_quality(plan)
        _annotate_trajectory_policy(
            plan,
            base_pd=base_pd,
            tau=tau,
            segment_context=segment_context,
        )
    all_valid_candidates, removed_invalid_candidates = filter_invalid_numeric_plans(plans)
    invalid_candidates_removed_count = int(len(removed_invalid_candidates))
    preferred_candidates = _prefer_non_rejected(_prefer_constraint_eligible(plans))
    preferred_valid_candidates, removed_preferred_invalid_candidates = filter_invalid_numeric_plans(preferred_candidates)
    preferred_pool_invalid_exhausted = bool(
        preferred_candidates and removed_preferred_invalid_candidates and not preferred_valid_candidates
    )

    def _rank_best_candidate(candidates: list[PlanRecord]) -> PlanRecord:
        denied_enabled = bool((denied_objective_cfg or {}).get("enabled", False))
        high_risk_cfg = (
            (denied_objective_cfg or {}).get("high_risk_objective", {})
            if isinstance((denied_objective_cfg or {}).get("high_risk_objective", {}), dict)
            else {}
        )
        high_risk_enabled = bool(high_risk_cfg.get("enabled", False))
        risk_band = str((segment_context or {}).get("risk_band", "")).strip().lower()
        is_denied_base = bool(base_pd is not None and tau is not None and float(base_pd) > float(tau))
        if denied_enabled and high_risk_enabled and risk_band == "high" and is_denied_base:
            ranked = sorted(
                candidates,
                key=lambda p: _high_risk_sort_key(
                    p,
                    base_pd=base_pd,
                    tau=tau,
                    min_reliability=min_reliability,
                    min_worst_risk_margin=min_worst_risk_margin,
                    high_risk_objective_cfg=high_risk_cfg,
                    fairness_penalty=float(fairness_penalty),
                    denied_objective_cfg=denied_objective_cfg,
                ),
            )
            return _select_with_source_tiebreak(
                ranked,
                base_pd=base_pd,
                tau=tau,
                min_reliability=min_reliability,
                min_worst_risk_margin=min_worst_risk_margin,
            )

        if denied_mode and denied_enabled:
            ranked = sorted(
                candidates,
                key=lambda p: _denied_sort_key(
                    p,
                    base_pd=base_pd,
                    tau=tau,
                    min_reliability=min_reliability,
                    min_worst_risk_margin=min_worst_risk_margin,
                    denied_objective_cfg=denied_objective_cfg,
                    fairness_penalty=float(fairness_penalty),
                ),
            )
            return _select_with_source_tiebreak(
                ranked,
                base_pd=base_pd,
                tau=tau,
                min_reliability=min_reliability,
                min_worst_risk_margin=min_worst_risk_margin,
            )

        ranked = sorted(
            candidates,
            key=lambda p: (
                _constraint_priority(p),
                _status_priority(p.status),
                _contender_bucket_priority(p),
                _recommendation_warning_penalty(p),
                -_gate_pass_score(
                    p,
                    tau=tau,
                    min_reliability=min_reliability,
                    min_worst_risk_margin=min_worst_risk_margin,
                ),
                _execution_rank_penalty(
                    p,
                    base_pd=base_pd,
                    tau=tau,
                    segment_context=segment_context,
                    high_risk=False,
                ),
                -_execution_defensibility_score(
                    p,
                    base_pd=base_pd,
                    tau=tau,
                    segment_context=segment_context,
                    high_risk=False,
                ),
                -_safe_float(getattr(p, "trajectory_policy_score", 0.0), 0.0),
                -_expected_pd_improvement(p, base_pd=base_pd, tau=tau),
                -_plan_execution_probability(p),
                -_expected_recovery_proxy(p),
                _offer_maturity_penalty(p),
                int(len(p.actions)),
                _plan_cost(p),
                p.predicted_pd or 1.0,
                -(p.robust_score if p.robust_score is not None else (p.score or -1e9)),
            ),
        )
        return _select_with_source_tiebreak(
            ranked,
            base_pd=base_pd,
            tau=tau,
            min_reliability=min_reliability,
            min_worst_risk_margin=min_worst_risk_margin,
        )

    stage_candidates: list[tuple[SelectionStage, list[PlanRecord]]] = [
        ("preferred_valid", preferred_valid_candidates),
        ("widened_constraint_valid", filter_invalid_numeric_plans(_prefer_constraint_eligible(plans))[0]),
        ("widened_non_rejected_valid", filter_invalid_numeric_plans(_prefer_non_rejected(plans))[0]),
        ("widened_any_valid", all_valid_candidates),
    ]
    for selection_stage, raw_candidates in stage_candidates:
        if not raw_candidates:
            continue
        filtered_candidates, _removed_empty_candidates = filter_empty_contenders(raw_candidates)
        ranking_candidates = filtered_candidates if filtered_candidates else raw_candidates
        if not ranking_candidates:
            continue
        return BestPlanSelectionResult(
            best_plan=_rank_best_candidate(ranking_candidates),
            selection_outcome="selected_valid_winner",
            selection_stage=selection_stage,
            invalid_candidates_removed_count=invalid_candidates_removed_count,
            preferred_pool_invalid_exhausted=preferred_pool_invalid_exhausted,
            no_valid_candidate_available=False,
            selected_from_widened_valid_pool=selection_stage != "preferred_valid",
        )

    return BestPlanSelectionResult(
        best_plan=None,
        selection_outcome="no_valid_winner",
        selection_stage="no_valid_winner",
        invalid_candidates_removed_count=invalid_candidates_removed_count,
        preferred_pool_invalid_exhausted=preferred_pool_invalid_exhausted,
        no_valid_candidate_available=True,
        selected_from_widened_valid_pool=False,
    )
