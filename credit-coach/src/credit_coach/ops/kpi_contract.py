from __future__ import annotations

from argparse import Namespace
from datetime import datetime, timezone
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

THRESHOLD_KEYS: tuple[str, ...] = (
    "min_denied_to_approved_lift",
    "min_denied_high_risk_lift",
    "min_denied_gate_pass_rate",
    "max_denied_reliability_violation_rate",
    "max_approval_gap_delta",
    "max_equalized_odds_gap_delta",
    "max_p95_latency_ms",
    "max_p99_latency_ms",
    "max_error_rate",
    "min_last_k_validity",
    "min_last_k_safe_rate",
    "min_last_k_avg_risk_margin",
    "max_fairness_gap",
    "max_high_stress_fairness_gap",
    "max_recourse_success_gap",
    "max_recourse_cost_gap",
    "min_trajectory_gate_pass_rate_4w",
    "min_trajectory_gate_pass_rate_12w",
    "min_trajectory_gate_pass_rate_24w",
    "min_trajectory_partial_progress_rate",
    "max_trajectory_median_time_to_gate_pass_days",
    "min_approval_rate",
    "max_psi",
    "min_avg_reliability",
    "require_telemetry_enabled",
    "min_telemetry_success_rate",
    "max_telemetry_ingest_lag_s",
)

DEFAULT_KPI_THRESHOLDS: dict[str, float | bool] = {
    "min_denied_to_approved_lift": 0.05,
    "min_denied_high_risk_lift": 0.03,
    "min_denied_gate_pass_rate": 0.08,
    "max_denied_reliability_violation_rate": 0.40,
    "max_approval_gap_delta": 0.01,
    "max_equalized_odds_gap_delta": 0.01,
    "max_p95_latency_ms": 500.0,
    "max_p99_latency_ms": 2000.0,
    "max_error_rate": 0.005,
    "min_last_k_validity": 0.70,
    "min_last_k_safe_rate": 0.60,
    "min_last_k_avg_risk_margin": 0.0,
    "max_fairness_gap": 0.10,
    "max_high_stress_fairness_gap": 0.10,
    "max_recourse_success_gap": 0.10,
    "max_recourse_cost_gap": 500.0,
    "min_trajectory_gate_pass_rate_4w": 0.0,
    "min_trajectory_gate_pass_rate_12w": 0.0,
    "min_trajectory_gate_pass_rate_24w": 0.0,
    "min_trajectory_partial_progress_rate": 0.0,
    "max_trajectory_median_time_to_gate_pass_days": 365.0,
    "min_approval_rate": 0.60,
    "max_psi": 0.25,
    "min_avg_reliability": 0.70,
    "require_telemetry_enabled": True,
    "min_telemetry_success_rate": 0.99,
    "max_telemetry_ingest_lag_s": 60.0,
}

KPI_CHECK_SPECS: dict[str, dict[str, Any]] = {
    "min_denied_to_approved_lift": {
        "metric_key": "denied_to_approved_lift",
        "direction": "min",
        "aliases": (),
    },
    "min_denied_high_risk_lift": {
        "metric_key": "denied_high_risk_lift",
        "direction": "min",
        "aliases": (),
    },
    "min_denied_gate_pass_rate": {
        "metric_key": "denied_gate_pass_rate",
        "direction": "min",
        "aliases": (),
    },
    "max_denied_reliability_violation_rate": {
        "metric_key": "denied_reliability_violation_rate",
        "direction": "max",
        "aliases": (),
    },
    "max_approval_gap_delta": {
        "metric_key": "approval_gap_delta",
        "direction": "max",
        "aliases": (),
    },
    "max_equalized_odds_gap_delta": {
        "metric_key": "equalized_odds_gap_delta",
        "direction": "max",
        "aliases": (),
    },
    "max_p95_latency_ms": {
        "metric_key": "latency_p95_ms",
        "direction": "max",
        "aliases": ("sync_latency_p95_ms",),
    },
    "max_p99_latency_ms": {
        "metric_key": "latency_p99_ms",
        "direction": "max",
        "aliases": ("sync_latency_p99_ms",),
    },
    "max_error_rate": {
        "metric_key": "error_rate",
        "direction": "max",
        "aliases": (),
    },
    "min_last_k_validity": {
        "metric_key": "last_k_validity",
        "direction": "min",
        "aliases": (),
    },
    "min_last_k_safe_rate": {
        "metric_key": "last_k_safe_rate",
        "direction": "min",
        "aliases": (),
    },
    "min_last_k_avg_risk_margin": {
        "metric_key": "last_k_avg_risk_margin",
        "direction": "min",
        "aliases": (),
    },
    "max_fairness_gap": {
        "metric_key": "fairness_gap_after",
        "direction": "max",
        "aliases": ("fairness_gap", "fairness_approval_gap_after"),
    },
    "max_high_stress_fairness_gap": {
        "metric_key": "high_stress_fairness_gap_after",
        "direction": "max",
        "aliases": ("high_stress_fairness_gap", "high_stress_approval_gap_after"),
    },
    "max_recourse_success_gap": {
        "metric_key": "recourse_success_gap",
        "direction": "max",
        "aliases": (),
    },
    "max_recourse_cost_gap": {
        "metric_key": "recourse_cost_gap",
        "direction": "max",
        "aliases": (),
    },
    "min_trajectory_gate_pass_rate_4w": {
        "metric_key": "trajectory_gate_pass_rate_4w",
        "direction": "min",
        "aliases": (),
    },
    "min_trajectory_gate_pass_rate_12w": {
        "metric_key": "trajectory_gate_pass_rate_12w",
        "direction": "min",
        "aliases": (),
    },
    "min_trajectory_gate_pass_rate_24w": {
        "metric_key": "trajectory_gate_pass_rate_24w",
        "direction": "min",
        "aliases": (),
    },
    "min_trajectory_partial_progress_rate": {
        "metric_key": "trajectory_partial_progress_rate",
        "direction": "min",
        "aliases": (),
    },
    "max_trajectory_median_time_to_gate_pass_days": {
        "metric_key": "trajectory_median_time_to_gate_pass_days",
        "direction": "max",
        "aliases": (),
    },
    "min_approval_rate": {
        "metric_key": "approval_rate",
        "direction": "min",
        "aliases": (),
    },
    "max_psi": {
        "metric_key": "max_psi",
        "direction": "max",
        "aliases": (),
    },
    "min_avg_reliability": {
        "metric_key": "avg_reliability",
        "direction": "min",
        "aliases": (),
    },
    "min_telemetry_success_rate": {
        "metric_key": "telemetry_success_rate",
        "direction": "min",
        "aliases": (),
    },
    "max_telemetry_ingest_lag_s": {
        "metric_key": "telemetry_ingest_lag_s",
        "direction": "max",
        "aliases": (),
    },
}

ALL_KPI_THRESHOLD_KEYS: tuple[str, ...] = tuple(KPI_CHECK_SPECS.keys())
LIFT_KPI_THRESHOLD_KEYS: tuple[str, ...] = (
    "min_denied_to_approved_lift",
    "min_denied_high_risk_lift",
)
RELIABILITY_KPI_THRESHOLD_KEYS: tuple[str, ...] = (
    "min_denied_gate_pass_rate",
    "max_denied_reliability_violation_rate",
    "max_p95_latency_ms",
    "max_p99_latency_ms",
    "max_error_rate",
    "min_trajectory_gate_pass_rate_4w",
    "min_trajectory_gate_pass_rate_12w",
    "min_trajectory_gate_pass_rate_24w",
    "min_trajectory_partial_progress_rate",
    "max_trajectory_median_time_to_gate_pass_days",
)
FAIRNESS_KPI_THRESHOLD_KEYS: tuple[str, ...] = (
    "max_approval_gap_delta",
    "max_equalized_odds_gap_delta",
    "max_fairness_gap",
    "max_high_stress_fairness_gap",
    "max_recourse_success_gap",
)
SMOKE_ONLY_KPI_THRESHOLD_KEYS: tuple[str, ...] = (
    "min_last_k_validity",
    "min_last_k_safe_rate",
    "min_last_k_avg_risk_margin",
    "max_recourse_cost_gap",
    "min_approval_rate",
    "max_psi",
    "min_avg_reliability",
    "min_telemetry_success_rate",
    "max_telemetry_ingest_lag_s",
)

KPI_CONTRACT_VERSION = "phase9.v1"
ACCEPTED = "ACCEPTED"
PILOT_ONLY = "PILOT_ONLY"
REJECTED = "REJECTED"


def _coerce_value(key: str, value: Any) -> float | bool:
    if key == "require_telemetry_enabled":
        return bool(value)
    return float(value)


def _coerce_metric_value(value: Any) -> float | None:
    if value is None:
        return None
    try:
        value_f = float(value)
    except Exception:
        return None
    if math.isnan(value_f):
        return None
    return value_f


def _resolve_metric_value(metrics: Mapping[str, Any], threshold_key: str) -> tuple[float | None, str]:
    spec = KPI_CHECK_SPECS.get(threshold_key, {})
    metric_key = str(spec.get("metric_key", ""))
    aliases = tuple(spec.get("aliases", ()))
    for key in (metric_key, *aliases):
        if not key:
            continue
        value = _coerce_metric_value(metrics.get(key))
        if value is not None:
            return value, str(key)
    return None, ""


def load_kpi_thresholds(contract_path: str | Path | None) -> dict[str, float | bool]:
    thresholds = dict(DEFAULT_KPI_THRESHOLDS)
    if not contract_path:
        return thresholds
    path = Path(contract_path)
    if not path.exists():
        return thresholds
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = payload.get("thresholds", {}) if isinstance(payload, dict) else {}
    if not isinstance(raw, dict):
        return thresholds
    for key in THRESHOLD_KEYS:
        if key not in raw:
            continue
        try:
            thresholds[key] = _coerce_value(key, raw[key])
        except Exception:
            continue
    return thresholds


def apply_kpi_thresholds_to_args(
    args: Namespace,
    thresholds: dict[str, float | bool],
) -> Namespace:
    for key in THRESHOLD_KEYS:
        if not hasattr(args, key):
            continue
        current = getattr(args, key)
        if current is None:
            setattr(args, key, thresholds.get(key, DEFAULT_KPI_THRESHOLDS[key]))
    return args


def extract_kpi_thresholds(args: Namespace) -> dict[str, float | bool]:
    resolved: dict[str, float | bool] = {}
    for key in THRESHOLD_KEYS:
        value = getattr(args, key, DEFAULT_KPI_THRESHOLDS[key])
        try:
            resolved[key] = _coerce_value(key, value)
        except Exception:
            resolved[key] = DEFAULT_KPI_THRESHOLDS[key]
    return resolved


def evaluate_kpi_checks(
    metrics: Mapping[str, Any],
    thresholds: Mapping[str, float | bool],
    *,
    threshold_keys: Iterable[str] | None = None,
) -> dict[str, dict[str, Any]]:
    selected = tuple(threshold_keys or ALL_KPI_THRESHOLD_KEYS)
    evaluations: dict[str, dict[str, Any]] = {}
    for threshold_key in selected:
        if threshold_key not in KPI_CHECK_SPECS:
            continue
        spec = KPI_CHECK_SPECS[threshold_key]
        metric_key = str(spec["metric_key"])
        direction = str(spec["direction"])
        value, source_key = _resolve_metric_value(metrics, threshold_key)
        threshold_raw = thresholds.get(threshold_key, DEFAULT_KPI_THRESHOLDS.get(threshold_key))
        try:
            threshold = float(_coerce_value(threshold_key, threshold_raw))
        except Exception:
            threshold = None
        checked = value is not None and threshold is not None
        passed = False
        violation = None
        if checked:
            passed = bool(value >= threshold) if direction == "min" else bool(value <= threshold)
            if passed:
                violation = 0.0
            else:
                denom = max(abs(float(threshold)), 1e-9)
                if direction == "min":
                    violation = float((threshold - value) / denom)
                else:
                    violation = float((value - threshold) / denom)
        evaluations[metric_key] = {
            "metric_key": metric_key,
            "source_key": source_key or metric_key,
            "threshold_key": threshold_key,
            "direction": direction,
            "value": value,
            "threshold": threshold,
            "checked": bool(checked),
            "pass": bool(passed),
            "violation": violation,
        }
    return evaluations


def list_failed_kpi_checks(evaluations: Mapping[str, Mapping[str, Any]]) -> list[str]:
    failed: list[str] = []
    for metric_key, payload in evaluations.items():
        if not bool(payload.get("checked", False)):
            continue
        if bool(payload.get("pass", False)):
            continue
        failed.append(str(metric_key))
    return failed


def compute_kpi_violation_score(
    metrics: Mapping[str, Any],
    thresholds: Mapping[str, float | bool],
    *,
    threshold_keys: Iterable[str] | None = None,
) -> tuple[float, int]:
    evaluations = evaluate_kpi_checks(metrics, thresholds, threshold_keys=threshold_keys)
    violations = [
        float(payload["violation"])
        for payload in evaluations.values()
        if bool(payload.get("checked", False)) and payload.get("violation") not in (None, 0.0)
    ]
    return float(sum(violations)), int(len(violations))


def build_kpi_snapshot(
    metrics: Mapping[str, Any],
    thresholds: Mapping[str, float | bool],
    *,
    threshold_keys: Iterable[str] | None = None,
    run_id: str = "",
    overall_status: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    evaluations = evaluate_kpi_checks(metrics, thresholds, threshold_keys=threshold_keys)
    snapshot = {
        "run_id": str(run_id),
        "overall_status": str(overall_status),
        "kpis": {
            metric_key: {
                "value": payload.get("value"),
                "threshold": payload.get("threshold"),
                "direction": payload.get("direction"),
                "pass": bool(payload.get("pass", False)),
                "threshold_key": payload.get("threshold_key"),
                "source_key": payload.get("source_key"),
            }
            for metric_key, payload in evaluations.items()
        },
    }
    if isinstance(metadata, Mapping):
        for key, value in metadata.items():
            snapshot[str(key)] = value
    return snapshot


def map_release_decision_to_acceptance_status(release_decision: str) -> str:
    decision = str(release_decision or "").strip().upper()
    if decision == "GO":
        return ACCEPTED
    if decision == "LIMITED_GO":
        return PILOT_ONLY
    return REJECTED


def _normalize_supporting_artifacts(supporting_artifacts: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(supporting_artifacts, Mapping):
        return {}
    normalized: dict[str, Any] = {}
    for key in sorted(supporting_artifacts.keys(), key=str):
        value = supporting_artifacts[key]
        if isinstance(value, (str, int, float, bool)) or value is None:
            normalized[str(key)] = value
        elif isinstance(value, Mapping):
            normalized[str(key)] = {str(k): v for k, v in value.items()}
        else:
            normalized[str(key)] = str(value)
    return normalized


def build_kpi_contract_snapshot(
    *,
    runner_type: str,
    release_payload: Mapping[str, Any],
    aggregate_metrics: Mapping[str, Any] | None,
    evidence_level: str,
    acceptance_eligible: bool,
    supporting_artifacts: Mapping[str, Any] | None = None,
    model_version: str = "",
    model_freeze_mode: str = "",
    evidence_status: str = "",
    degraded_reason: str = "",
    missing_artifacts: Iterable[str] | None = None,
    fallback_source: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    aggregate = dict(aggregate_metrics or {})
    decision = str(release_payload.get("decision", release_payload.get("release_decision", "NO_GO")))
    smoke_pass = bool(release_payload.get("smoke_pass", decision == "GO"))
    pilot_eligible = bool(release_payload.get("pilot_eligible", decision == "LIMITED_GO"))
    broad_rollout_allowed = bool(release_payload.get("broad_rollout_allowed", decision == "GO"))
    missing = [str(item) for item in (missing_artifacts or []) if str(item).strip()]
    status = str(evidence_status or ("degraded" if (degraded_reason or missing or not acceptance_eligible) else "complete"))
    if not acceptance_eligible:
        broad_rollout_allowed = False

    snapshot = {
        "contract_version": KPI_CONTRACT_VERSION,
        "runner_type": str(runner_type),
        "evidence_level": str(evidence_level),
        "evidence_status": status,
        "acceptance_eligible": bool(acceptance_eligible),
        "release_decision": decision,
        "decision_reason": str(release_payload.get("decision_reason", "")),
        "smoke_pass": smoke_pass,
        "pilot_eligible": pilot_eligible,
        "broad_rollout_allowed": broad_rollout_allowed,
        "model_freeze_mode": str(model_freeze_mode or aggregate.get("model_freeze_mode", "")),
        "model_version": str(model_version or aggregate.get("model_version", "")),
        "lift_pass": bool(aggregate.get("lift_pass", False)),
        "reliability_pass": bool(aggregate.get("reliability_pass", False)),
        "fairness_seed_pass_count": int(aggregate.get("fairness_seed_pass_count", 0)),
        "fairness_seed_total": int(aggregate.get("fairness_seed_total", 0)),
        "primary_fairness_metric": str(
            aggregate.get("primary_fairness_metric", aggregate.get("dominant_fail_reason", "equalized_odds_gap_delta"))
            or "equalized_odds_gap_delta"
        ),
        "worst_primary_fairness_gap": float(aggregate.get("worst_fairness_gap", 0.0)),
        "dominant_fail_segment_key": str(aggregate.get("dominant_fail_segment_key", "")),
        "dominant_fail_candidate_source": str(aggregate.get("dominant_fail_candidate_source", "")),
        "supporting_artifacts": _normalize_supporting_artifacts(supporting_artifacts),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if degraded_reason:
        snapshot["degraded_reason"] = str(degraded_reason)
    if missing:
        snapshot["missing_artifacts"] = missing
    if fallback_source:
        snapshot["fallback_source"] = str(fallback_source)
    if isinstance(metadata, Mapping):
        for key, value in metadata.items():
            snapshot[str(key)] = value
    return snapshot


def build_milestone_acceptance_summary(
    *,
    phase: str,
    milestone: str,
    runner_type: str,
    release_payload: Mapping[str, Any],
    aggregate_metrics: Mapping[str, Any] | None,
    evidence_level: str,
    acceptance_eligible: bool,
    supporting_artifacts: Mapping[str, Any] | None = None,
    model_version: str = "",
    model_freeze_mode: str = "",
    evidence_status: str = "",
    degraded_reason: str = "",
    missing_artifacts: Iterable[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    aggregate = dict(aggregate_metrics or {})
    decision = str(release_payload.get("decision", release_payload.get("release_decision", "NO_GO")))
    broad_rollout_allowed = bool(release_payload.get("broad_rollout_allowed", decision == "GO"))
    if not acceptance_eligible:
        broad_rollout_allowed = False
    missing = [str(item) for item in (missing_artifacts or []) if str(item).strip()]
    status = str(evidence_status or ("degraded" if (degraded_reason or missing or not acceptance_eligible) else "complete"))

    summary = {
        "phase": str(phase),
        "milestone": str(milestone),
        "contract_version": KPI_CONTRACT_VERSION,
        "runner_type": str(runner_type),
        "evidence_level": str(evidence_level),
        "evidence_status": status,
        "acceptance_eligible": bool(acceptance_eligible),
        "acceptance_status": map_release_decision_to_acceptance_status(decision),
        "release_decision": decision,
        "smoke_pass": bool(release_payload.get("smoke_pass", decision == "GO")),
        "pilot_eligible": bool(release_payload.get("pilot_eligible", decision == "LIMITED_GO")),
        "broad_rollout_allowed": broad_rollout_allowed,
        "model_freeze_mode": str(model_freeze_mode or aggregate.get("model_freeze_mode", "")),
        "model_version": str(model_version or aggregate.get("model_version", "")),
        "seed_count": int(aggregate.get("seed_count", aggregate.get("fairness_seed_total", 0))),
        "fairness_seed_pass_count": int(aggregate.get("fairness_seed_pass_count", 0)),
        "lift_pass": bool(aggregate.get("lift_pass", False)),
        "reliability_pass": bool(aggregate.get("reliability_pass", False)),
        "primary_fairness_metric": str(
            aggregate.get("primary_fairness_metric", aggregate.get("dominant_fail_reason", "equalized_odds_gap_delta"))
            or "equalized_odds_gap_delta"
        ),
        "worst_primary_fairness_gap": float(aggregate.get("worst_fairness_gap", 0.0)),
        "dominant_fail_segment_key": str(aggregate.get("dominant_fail_segment_key", "")),
        "dominant_fail_candidate_source": str(aggregate.get("dominant_fail_candidate_source", "")),
        "supporting_artifacts": _normalize_supporting_artifacts(supporting_artifacts),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if degraded_reason:
        summary["degraded_reason"] = str(degraded_reason)
    if missing:
        summary["missing_artifacts"] = missing
    if isinstance(metadata, Mapping):
        for key, value in metadata.items():
            summary[str(key)] = value
    return summary


def render_milestone_acceptance_review(summary: Mapping[str, Any]) -> str:
    supporting_artifacts = summary.get("supporting_artifacts", {})
    if not isinstance(supporting_artifacts, Mapping):
        supporting_artifacts = {}

    lines = [
        "# Milestone Acceptance Review",
        "",
        "## Decision",
        "",
        f"- Acceptance status: {summary.get('acceptance_status', REJECTED)}",
        f"- Release decision: {summary.get('release_decision', 'NO_GO')}",
        f"- Acceptance eligible: {bool(summary.get('acceptance_eligible', False))}",
        f"- Broad rollout allowed: {bool(summary.get('broad_rollout_allowed', False))}",
        "",
        "## Reason Summary",
        "",
        f"- Evidence level: {summary.get('evidence_level', '')}",
        f"- Lift pass: {bool(summary.get('lift_pass', False))}",
        f"- Reliability pass: {bool(summary.get('reliability_pass', False))}",
        f"- Fairness seed pass count: {int(summary.get('fairness_seed_pass_count', 0))}/{int(summary.get('seed_count', 0))}",
        f"- Primary fairness metric: {summary.get('primary_fairness_metric', '')}",
        f"- Worst primary fairness gap: {float(summary.get('worst_primary_fairness_gap', 0.0)):.6f}",
    ]
    if summary.get("degraded_reason"):
        lines.append(f"- Degraded reason: {summary.get('degraded_reason', '')}")

    lines.extend(
        [
            "",
            "## Freeze / Provenance",
            "",
            f"- Phase: {summary.get('phase', '')}",
            f"- Milestone: {summary.get('milestone', '')}",
            f"- Runner type: {summary.get('runner_type', '')}",
            f"- Model version: {summary.get('model_version', '')}",
            f"- Freeze mode: {summary.get('model_freeze_mode', '')}",
            "",
            "## Dominant Failure Localization",
            "",
            f"- Dominant fail segment: {summary.get('dominant_fail_segment_key', '')}",
            f"- Dominant fail candidate source: {summary.get('dominant_fail_candidate_source', '')}",
        ]
    )
    if supporting_artifacts:
        lines.extend(["", "## Supporting Artifacts", ""])
        for key in sorted(supporting_artifacts.keys(), key=str):
            lines.append(f"- {key}: {supporting_artifacts[key]}")
    return "\n".join(lines) + "\n"
