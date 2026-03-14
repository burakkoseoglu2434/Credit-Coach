from __future__ import annotations

from typing import Any, Iterable

from credit_coach.evaluation.fairness import classify_primary_fairness_fail_reason
from credit_coach.ops.kpi_contract import (
    FAIRNESS_KPI_THRESHOLD_KEYS,
    LIFT_KPI_THRESHOLD_KEYS,
    RELIABILITY_KPI_THRESHOLD_KEYS,
    evaluate_kpi_checks,
    list_failed_kpi_checks,
)

PRIMARY_FAIRNESS_METRIC = "equalized_odds_gap_delta"
PRIMARY_FAIRNESS_THRESHOLD_KEY = "max_equalized_odds_gap_delta"
LIMITED_GO_CAP_MULTIPLIER = 1.5
DOMINANT_FAIL_SEGMENT_SHARE_THRESHOLD = 0.60
LIMITED_GO_MAX_TRAFFIC_PCT = 5

SUPPORTING_GUARDRAIL_THRESHOLDS: dict[str, str] = {
    "high_stress_fairness_gap_after": "max_high_stress_fairness_gap",
    "recourse_success_gap": "max_recourse_success_gap",
}

GO = "GO"
LIMITED_GO = "LIMITED_GO"
NO_GO = "NO_GO"


def _safe_float(payload: dict[str, Any] | None, key: str, default: float = 0.0) -> float:
    if not isinstance(payload, dict):
        return float(default)
    value = payload.get(key, default)
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(payload: dict[str, Any] | None, key: str, default: int = 0) -> int:
    if not isinstance(payload, dict):
        return int(default)
    value = payload.get(key, default)
    try:
        return int(value)
    except Exception:
        return int(default)


def _safe_bool(payload: dict[str, Any] | None, key: str, default: bool = False) -> bool:
    if not isinstance(payload, dict):
        return bool(default)
    return bool(payload.get(key, default))

def evaluate_fairness_seed_pass(
    metrics: dict[str, Any],
    thresholds: dict[str, float | bool],
) -> dict[str, Any]:
    primary_threshold = _safe_float(thresholds, PRIMARY_FAIRNESS_THRESHOLD_KEY, 0.01)
    primary_value = _safe_float(metrics, PRIMARY_FAIRNESS_METRIC)
    guardrail_checks = {
        metric: _safe_float(metrics, metric) <= _safe_float(thresholds, threshold_key, 0.0)
        for metric, threshold_key in SUPPORTING_GUARDRAIL_THRESHOLDS.items()
    }
    fairness_checks = {
        PRIMARY_FAIRNESS_METRIC: primary_value <= primary_threshold,
        **guardrail_checks,
    }
    failed_metrics = [metric for metric, passed in fairness_checks.items() if not passed]

    limited_go_guardrail_caps = {
        metric: _safe_float(metrics, metric)
        <= (_safe_float(thresholds, threshold_key, 0.0) * LIMITED_GO_CAP_MULTIPLIER)
        for metric, threshold_key in SUPPORTING_GUARDRAIL_THRESHOLDS.items()
    }

    return {
        "fairness_seed_pass": bool(all(fairness_checks.values())),
        "fairness_checks": fairness_checks,
        "primary_fairness_metric": PRIMARY_FAIRNESS_METRIC,
        "primary_fairness_threshold": float(primary_threshold),
        "primary_fairness_value": float(primary_value),
        "primary_fail_reason": classify_primary_fairness_fail_reason(metrics, thresholds),
        "failed_metrics": failed_metrics,
        "worst_fairness_gap": float(primary_value),
        "within_limited_go_cap": bool(primary_value <= (primary_threshold * LIMITED_GO_CAP_MULTIPLIER)),
        "supporting_guardrails_within_limited_cap": bool(all(limited_go_guardrail_caps.values())),
        "supporting_guardrail_caps": limited_go_guardrail_caps,
    }


def evaluate_seed_kpi_contract(
    summary: dict[str, Any],
    fair_metrics: dict[str, Any],
    thresholds: dict[str, float | bool],
) -> dict[str, Any]:
    denied_count = max(1, _safe_int(summary, "denied_count", 0))
    denied_gate_pass_rate = _safe_float(summary, "denied_with_gate_pass_plan", 0.0) / float(denied_count)

    contract_metrics = {
        "denied_to_approved_lift": _safe_float(summary, "denied_to_approved_lift"),
        "denied_high_risk_lift": _safe_float(summary, "denied_high_risk_lift"),
        "denied_gate_pass_rate": denied_gate_pass_rate,
        "denied_reliability_violation_rate": _safe_float(summary, "denied_reliability_violation_rate"),
        "latency_p95_ms": _safe_float(summary, "sync_latency_p95_ms", _safe_float(summary, "latency_p95_ms")),
        "latency_p99_ms": _safe_float(summary, "sync_latency_p99_ms", _safe_float(summary, "latency_p99_ms")),
        "error_rate": _safe_float(summary, "error_rate"),
        "trajectory_gate_pass_rate_4w": _safe_float(summary, "trajectory_gate_pass_rate_4w"),
        "trajectory_gate_pass_rate_12w": _safe_float(summary, "trajectory_gate_pass_rate_12w"),
        "trajectory_gate_pass_rate_24w": _safe_float(summary, "trajectory_gate_pass_rate_24w"),
        "trajectory_partial_progress_rate": _safe_float(summary, "trajectory_partial_progress_rate"),
        "trajectory_median_time_to_gate_pass_days": _safe_float(summary, "trajectory_median_time_to_gate_pass_days", 9_999.0),
    }
    normalized_fair_metrics = {
        "approval_gap_delta": _safe_float(fair_metrics, "approval_gap_delta"),
        PRIMARY_FAIRNESS_METRIC: _safe_float(
            fair_metrics,
            PRIMARY_FAIRNESS_METRIC,
            _safe_float(fair_metrics, "equalized_odds_gap_delta"),
        ),
        "high_stress_fairness_gap_after": _safe_float(
            fair_metrics,
            "high_stress_fairness_gap_after",
            _safe_float(fair_metrics, "high_stress_approval_gap_after"),
        ),
        "recourse_success_gap": _safe_float(fair_metrics, "recourse_success_gap"),
        "fairness_gap_after": _safe_float(
            fair_metrics,
            "fairness_gap_after",
            _safe_float(summary, "fairness_approval_gap_after"),
        ),
    }
    contract_metrics.update(normalized_fair_metrics)
    lift_evaluations = evaluate_kpi_checks(contract_metrics, thresholds, threshold_keys=LIFT_KPI_THRESHOLD_KEYS)
    reliability_evaluations = evaluate_kpi_checks(contract_metrics, thresholds, threshold_keys=RELIABILITY_KPI_THRESHOLD_KEYS)
    fairness_evaluations = evaluate_kpi_checks(contract_metrics, thresholds, threshold_keys=FAIRNESS_KPI_THRESHOLD_KEYS)
    lift_checks = {metric: bool(payload["pass"]) for metric, payload in lift_evaluations.items()}
    reliability_checks = {metric: bool(payload["pass"]) for metric, payload in reliability_evaluations.items()}
    fairness_snapshot = evaluate_fairness_seed_pass(normalized_fair_metrics, thresholds)
    fairness_checks = {
        "approval_gap_delta": bool(fairness_evaluations["approval_gap_delta"]["pass"]),
        PRIMARY_FAIRNESS_METRIC: bool(fairness_snapshot["fairness_checks"][PRIMARY_FAIRNESS_METRIC]),
        "fairness_gap_after": bool(fairness_evaluations["fairness_gap_after"]["pass"]),
        "high_stress_fairness_gap_after": bool(fairness_snapshot["fairness_checks"]["high_stress_fairness_gap_after"]),
        "recourse_success_gap": bool(fairness_snapshot["fairness_checks"]["recourse_success_gap"]),
    }
    checks = {**lift_checks, **reliability_checks, **fairness_checks}
    failed = (
        list_failed_kpi_checks(lift_evaluations)
        + list_failed_kpi_checks(reliability_evaluations)
        + [metric for metric, passed in fairness_checks.items() if not passed and metric not in {
            "approval_gap_delta",
            "fairness_gap_after",
        }]
    )
    if not fairness_checks["approval_gap_delta"]:
        failed.append("approval_gap_delta")
    if not fairness_checks["fairness_gap_after"]:
        failed.append("fairness_gap_after")

    return {
        "all_pass": bool(all(checks.values())),
        "failed_checks": ";".join(failed),
        "lift_pass": bool(all(lift_checks.values())),
        "reliability_pass": bool(all(reliability_checks.values())),
        "fairness_seed_pass": bool(fairness_snapshot["fairness_seed_pass"]),
        "primary_fairness_metric": str(fairness_snapshot["primary_fairness_metric"]),
        "primary_fail_reason": str(fairness_snapshot["primary_fail_reason"]),
        "worst_fairness_gap": float(fairness_snapshot["worst_fairness_gap"]),
        "approval_gap_delta": float(normalized_fair_metrics["approval_gap_delta"]),
        "equalized_odds_gap_delta": float(normalized_fair_metrics[PRIMARY_FAIRNESS_METRIC]),
        "fairness_gap_after": float(normalized_fair_metrics["fairness_gap_after"]),
        "high_stress_fairness_gap_after": float(normalized_fair_metrics["high_stress_fairness_gap_after"]),
        "recourse_success_gap": float(normalized_fair_metrics["recourse_success_gap"]),
        "supporting_guardrails_within_limited_cap": bool(
            fairness_snapshot["supporting_guardrails_within_limited_cap"]
        ),
    }


def compute_dominant_failure_localization(
    breakdown_rows: Iterable[dict[str, Any]] | None,
) -> dict[str, Any]:
    totals: dict[tuple[str, str], float] = {}
    total_weight = 0.0
    for row in breakdown_rows or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("breakdown_type", "")) not in {"segment_candidate_source", "seed_segment"}:
            continue
        segment_key = str(
            row.get("canonical_segment_key")
            or row.get("dominant_fail_segment_key")
            or row.get("segment_key")
            or ""
        ).strip()
        candidate_source = str(
            row.get("candidate_source")
            or row.get("dominant_fail_candidate_source")
            or row.get("best_source")
            or ""
        ).strip()
        weight = row.get("failure_weight", row.get("failure_severity_score", 0.0))
        try:
            weight_f = float(weight)
        except Exception:
            weight_f = 0.0
        if not segment_key or weight_f <= 0.0:
            continue
        total_weight += weight_f
        totals[(segment_key, candidate_source)] = totals.get((segment_key, candidate_source), 0.0) + weight_f

    if total_weight <= 0.0 or not totals:
        return {
            "dominant_fail_segment_key": "",
            "dominant_fail_candidate_source": "",
            "dominant_fail_segment_share": 0.0,
        }

    (segment_key, candidate_source), dominant_weight = max(
        totals.items(),
        key=lambda item: (item[1], item[0][0], item[0][1]),
    )
    return {
        "dominant_fail_segment_key": str(segment_key),
        "dominant_fail_candidate_source": str(candidate_source),
        "dominant_fail_segment_share": float(dominant_weight / total_weight),
    }


def aggregate_release_metrics(
    seed_rows: Iterable[dict[str, Any]],
    *,
    thresholds: dict[str, float | bool],
    breakdown_rows: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = [row for row in seed_rows if isinstance(row, dict)]
    localization = compute_dominant_failure_localization(breakdown_rows)
    fairness_seed_total = int(len(rows))
    fairness_seed_pass_count = int(sum(1 for row in rows if _safe_bool(row, "fairness_seed_pass")))
    worst_fairness_gap = max((_safe_float(row, "worst_fairness_gap") for row in rows), default=0.0)
    worst_high_stress_gap = max((_safe_float(row, "high_stress_fairness_gap_after") for row in rows), default=0.0)
    worst_recourse_success_gap = max((_safe_float(row, "recourse_success_gap") for row in rows), default=0.0)
    limited_go_guardrails_ok = (
        worst_high_stress_gap
        <= (_safe_float(thresholds, SUPPORTING_GUARDRAIL_THRESHOLDS["high_stress_fairness_gap_after"], 0.0) * LIMITED_GO_CAP_MULTIPLIER)
        and worst_recourse_success_gap
        <= (_safe_float(thresholds, SUPPORTING_GUARDRAIL_THRESHOLDS["recourse_success_gap"], 0.0) * LIMITED_GO_CAP_MULTIPLIER)
    )
    fail_reason_counts: dict[str, int] = {}
    for row in rows:
        reason = str(row.get("primary_fail_reason", "") or "").strip()
        if not reason:
            continue
        fail_reason_counts[reason] = fail_reason_counts.get(reason, 0) + 1
    dominant_fail_reason = ""
    if fail_reason_counts:
        dominant_fail_reason = max(
            fail_reason_counts.items(),
            key=lambda item: (item[1], item[0]),
        )[0]

    metrics = {
        "lift_pass": bool(rows) and all(_safe_bool(row, "lift_pass") for row in rows),
        "reliability_pass": bool(rows) and all(_safe_bool(row, "reliability_pass") for row in rows),
        "fairness_seed_pass_count": fairness_seed_pass_count,
        "fairness_seed_total": fairness_seed_total,
        "worst_fairness_gap": float(worst_fairness_gap),
        "worst_high_stress_fairness_gap_after": float(worst_high_stress_gap),
        "worst_recourse_success_gap": float(worst_recourse_success_gap),
        "supporting_guardrails_within_limited_cap": bool(limited_go_guardrails_ok),
        "dominant_fail_reason": dominant_fail_reason,
        **localization,
    }
    return metrics


def build_pilot_guardrails(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "pilot_eligible": True,
        "broad_rollout_allowed": False,
        "max_traffic_pct": LIMITED_GO_MAX_TRAFFIC_PCT,
        "fairness_monitoring_required": True,
        "rollback_guard_required": True,
        "targeted_alerting_required": True,
        "manual_approval_required": True,
        "remediation_artifacts_required": True,
        "dominant_fail_segment_key": str(metrics.get("dominant_fail_segment_key", "")),
        "dominant_fail_candidate_source": str(metrics.get("dominant_fail_candidate_source", "")),
    }


def build_rollback_conditions(
    metrics: dict[str, Any],
    thresholds: dict[str, float | bool],
) -> dict[str, Any]:
    primary_threshold = _safe_float(thresholds, PRIMARY_FAIRNESS_THRESHOLD_KEY, 0.01)
    return {
        "rollback_if": [
            "reliability_pass becomes false",
            f"{PRIMARY_FAIRNESS_METRIC} exceeds {primary_threshold * LIMITED_GO_CAP_MULTIPLIER:.6f}",
            "high_stress_fairness_gap_after exceeds hard cap",
            "recourse_success_gap exceeds hard cap",
            f"dominant_fail_segment_share drops below {DOMINANT_FAIL_SEGMENT_SHARE_THRESHOLD:.2f}",
            f"traffic exceeds {LIMITED_GO_MAX_TRAFFIC_PCT} percent",
        ],
        "dominant_fail_segment_key": str(metrics.get("dominant_fail_segment_key", "")),
        "dominant_fail_candidate_source": str(metrics.get("dominant_fail_candidate_source", "")),
    }


def evaluate_release_decision(
    metrics: dict[str, Any],
    thresholds: dict[str, float | bool],
) -> dict[str, Any]:
    fairness_seed_pass_count = _safe_int(metrics, "fairness_seed_pass_count")
    fairness_seed_total = _safe_int(metrics, "fairness_seed_total")
    dominant_fail_segment_share = _safe_float(metrics, "dominant_fail_segment_share")
    worst_fairness_gap = _safe_float(metrics, "worst_fairness_gap")
    primary_threshold = _safe_float(thresholds, PRIMARY_FAIRNESS_THRESHOLD_KEY, 0.01)
    supporting_guardrails_ok = _safe_bool(metrics, "supporting_guardrails_within_limited_cap", True)

    if not _safe_bool(metrics, "reliability_pass"):
        decision = NO_GO
        decision_reason = "reliability_fail"
    elif not _safe_bool(metrics, "lift_pass"):
        decision = NO_GO
        decision_reason = "lift_fail"
    elif fairness_seed_total > 0 and fairness_seed_pass_count == fairness_seed_total:
        decision = GO
        decision_reason = "fairness_stable"
    elif (
        fairness_seed_total > 0
        and fairness_seed_pass_count == (fairness_seed_total - 1)
        and dominant_fail_segment_share >= DOMINANT_FAIL_SEGMENT_SHARE_THRESHOLD
        and worst_fairness_gap <= (primary_threshold * LIMITED_GO_CAP_MULTIPLIER)
        and supporting_guardrails_ok
    ):
        decision = LIMITED_GO
        decision_reason = "localized_fairness_instability"
    else:
        decision = NO_GO
        decision_reason = "systemic_fairness_instability"

    payload = {
        "decision": decision,
        "decision_reason": decision_reason,
        "release_decision": decision,
        "smoke_pass": bool(decision == GO),
        "pilot_eligible": bool(decision == LIMITED_GO),
        "fairness_seed_pass_count": fairness_seed_pass_count,
        "fairness_seed_total": fairness_seed_total,
        "worst_fairness_gap": float(worst_fairness_gap),
        "dominant_fail_segment_key": str(metrics.get("dominant_fail_segment_key", "")),
        "dominant_fail_candidate_source": str(metrics.get("dominant_fail_candidate_source", "")),
        "dominant_fail_segment_share": float(dominant_fail_segment_share),
        "lift_pass": bool(metrics.get("lift_pass", False)),
        "reliability_pass": bool(metrics.get("reliability_pass", False)),
    }

    if decision == LIMITED_GO:
        payload.update(build_pilot_guardrails(metrics))
    else:
        payload.update(
            {
                "broad_rollout_allowed": bool(decision == GO),
                "max_traffic_pct": 100 if decision == GO else 0,
                "fairness_monitoring_required": bool(decision == LIMITED_GO),
                "rollback_guard_required": bool(decision == LIMITED_GO),
                "targeted_alerting_required": bool(decision == LIMITED_GO),
                "manual_approval_required": bool(decision == LIMITED_GO),
                "remediation_artifacts_required": bool(decision in {LIMITED_GO, NO_GO}),
            }
        )
    return payload
