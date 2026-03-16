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
HELPED = "helped"
HARMED = "harmed"
MIXED = "mixed"
NO_MATERIAL_CHANGE = "no_material_change"
STRONG = "strong"
TENTATIVE = "tentative"

PRIMARY_COMPARATIVE_IMPACT_AXES: dict[str, dict[str, Any]] = {
    "denied_to_approved_lift": {"higher_is_better": True},
    "denied_high_risk_lift": {"higher_is_better": True},
    "equalized_odds_gap_delta": {"higher_is_better": False},
    "denied_reliability_violation_rate": {"higher_is_better": False},
}
SUPPORTING_COMPARATIVE_IMPACT_AXES: dict[str, dict[str, Any]] = {
    "high_risk_reachability_rate": {"higher_is_better": True},
    "trajectory_partial_progress_rate": {"higher_is_better": True},
    "candidate_source_entropy": {"higher_is_better": True},
}


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


def _round_metric(value: Any, *, digits: int = 6) -> float:
    metric = _coerce_metric_value(value)
    if metric is None:
        return 0.0
    return round(float(metric), digits)


def _impact_label_from_delta(delta: float, *, higher_is_better: bool) -> str:
    if abs(delta) <= 1e-9:
        return NO_MATERIAL_CHANGE
    if higher_is_better:
        return HELPED if delta > 0.0 else HARMED
    return HELPED if delta < 0.0 else HARMED


def _overall_impact_assessment(labels: Iterable[str]) -> str:
    normalized = [str(label) for label in labels if str(label)]
    helped = any(label == HELPED for label in normalized)
    harmed = any(label == HARMED for label in normalized)
    if helped and harmed:
        return MIXED
    if helped:
        return HELPED
    if harmed:
        return HARMED
    return NO_MATERIAL_CHANGE


def build_comparative_impact_summary(
    *,
    subject_label: str,
    baseline_label: str,
    subject_metrics: Mapping[str, Any],
    baseline_metrics: Mapping[str, Any] | None,
    evidence_level: str,
    evidence_status: str,
    seed_count: int,
    metric_direction_consistency: Mapping[str, bool] | None = None,
    source_mix_deltas: Mapping[str, Any] | None = None,
    baseline_type: str = "control_variant",
    diagnostic_reason: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    consistency = {
        str(key): bool(value)
        for key, value in (metric_direction_consistency or {}).items()
    }
    normalized_source_mix = {
        str(key): _round_metric(value)
        for key, value in (source_mix_deltas or {}).items()
    }
    payload: dict[str, Any] = {
        "comparison_type": "comparative_evidence",
        "baseline_type": str(baseline_type),
        "baseline_label": str(baseline_label),
        "subject_label": str(subject_label),
        "evidence_level": str(evidence_level),
        "evidence_status": str(evidence_status or "degraded"),
        "seed_count": int(seed_count),
        "source_mix_deltas": normalized_source_mix,
        "primary_axes": {},
        "supporting_axes": {},
    }
    if isinstance(metadata, Mapping):
        for key, value in metadata.items():
            payload[str(key)] = value

    if not isinstance(baseline_metrics, Mapping):
        payload["comparative_impact_confidence"] = TENTATIVE
        payload["overall_assessment"] = NO_MATERIAL_CHANGE
        payload["diagnostic_only"] = True
        payload["diagnostic_reason"] = str(diagnostic_reason or "baseline_unavailable")
        return payload

    def _axis_payload(
        metric_key: str,
        spec: Mapping[str, Any],
    ) -> dict[str, Any]:
        baseline_value = _coerce_metric_value(baseline_metrics.get(metric_key))
        subject_value = _coerce_metric_value(subject_metrics.get(metric_key))
        if baseline_value is None or subject_value is None:
            return {
                "label": NO_MATERIAL_CHANGE,
                "baseline_value": 0.0 if baseline_value is None else _round_metric(baseline_value),
                "subject_value": 0.0 if subject_value is None else _round_metric(subject_value),
                "delta": 0.0,
                "directionally_consistent": bool(consistency.get(metric_key, False)),
            }
        delta = _round_metric(subject_value - baseline_value)
        return {
            "label": _impact_label_from_delta(delta, higher_is_better=bool(spec.get("higher_is_better", True))),
            "baseline_value": _round_metric(baseline_value),
            "subject_value": _round_metric(subject_value),
            "delta": delta,
            "directionally_consistent": bool(consistency.get(metric_key, True)),
        }

    primary_axes = {
        metric_key: _axis_payload(metric_key, spec)
        for metric_key, spec in PRIMARY_COMPARATIVE_IMPACT_AXES.items()
    }
    supporting_axes = {
        metric_key: _axis_payload(metric_key, spec)
        for metric_key, spec in SUPPORTING_COMPARATIVE_IMPACT_AXES.items()
    }
    payload["primary_axes"] = primary_axes
    payload["supporting_axes"] = supporting_axes
    payload["overall_assessment"] = _overall_impact_assessment(
        axis_payload["label"] for axis_payload in primary_axes.values()
    )

    consistency_values = [
        bool(consistency.get(metric_key, True))
        for metric_key in (*PRIMARY_COMPARATIVE_IMPACT_AXES.keys(), *SUPPORTING_COMPARATIVE_IMPACT_AXES.keys())
        if metric_key in consistency
    ]
    strong_confidence = bool(
        str(evidence_status or "").lower() == "complete"
        and int(seed_count) > 1
        and all(consistency_values or [True])
    )
    payload["comparative_impact_confidence"] = STRONG if strong_confidence else TENTATIVE
    payload["diagnostic_only"] = not strong_confidence
    if diagnostic_reason:
        payload["diagnostic_reason"] = str(diagnostic_reason)
    return payload


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


def _resolve_telemetry_metadata(
    *,
    release_payload: Mapping[str, Any],
    aggregate: Mapping[str, Any],
) -> dict[str, Any]:
    telemetry_status = str(release_payload.get("telemetry_status", aggregate.get("telemetry_status", "")))
    telemetry_gate_status = str(release_payload.get("telemetry_gate_status", aggregate.get("telemetry_gate_status", "")))
    telemetry_failure_reason = str(
        release_payload.get("telemetry_failure_reason", aggregate.get("telemetry_failure_reason", ""))
    )
    telemetry_artifact_path = str(
        release_payload.get("telemetry_artifact_path", aggregate.get("telemetry_artifact_path", ""))
    )
    return {
        "telemetry_status": telemetry_status,
        "telemetry_gate_status": telemetry_gate_status,
        "telemetry_failure_reason": telemetry_failure_reason,
        "telemetry_success_rate": float(release_payload.get("telemetry_success_rate", aggregate.get("telemetry_success_rate", 0.0))),
        "telemetry_ingest_lag_s": float(
            release_payload.get("telemetry_ingest_lag_s", aggregate.get("telemetry_ingest_lag_s", 0.0))
        ),
        "telemetry_required_for_broad_rollout": bool(
            release_payload.get(
                "telemetry_required_for_broad_rollout",
                aggregate.get("telemetry_required_for_broad_rollout", False),
            )
        ),
        "telemetry_required_for_pilot": bool(
            release_payload.get("telemetry_required_for_pilot", aggregate.get("telemetry_required_for_pilot", False))
        ),
        "telemetry_artifact_path": telemetry_artifact_path,
    }


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
    snapshot.update(_resolve_telemetry_metadata(release_payload=release_payload, aggregate=aggregate))
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
    summary.update(_resolve_telemetry_metadata(release_payload=release_payload, aggregate=aggregate))
    if degraded_reason:
        summary["degraded_reason"] = str(degraded_reason)
    if missing:
        summary["missing_artifacts"] = missing
    if isinstance(metadata, Mapping):
        for key, value in metadata.items():
            summary[str(key)] = value
    return summary


def build_release_evidence_pack(
    *,
    runner_type: str,
    release_decision: str,
    acceptance_status: str = "",
    evidence_level: str = "",
    evidence_status: str = "",
    acceptance_eligible: bool = False,
    phase: str = "",
    milestone: str = "",
    required_artifacts: Mapping[str, Any] | None = None,
    optional_artifacts: Mapping[str, Any] | None = None,
    existing_artifacts: Iterable[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    required = _normalize_supporting_artifacts(required_artifacts)
    optional = _normalize_supporting_artifacts(optional_artifacts)
    existing = {str(item) for item in (existing_artifacts or []) if str(item).strip()}
    missing = [
        str(path)
        for path in required.values()
        if isinstance(path, str) and str(path).strip() and str(path) not in existing
    ]
    pack_status = "complete" if not missing else "degraded"
    pack = {
        "contract_version": KPI_CONTRACT_VERSION,
        "runner_type": str(runner_type),
        "phase": str(phase),
        "milestone": str(milestone),
        "release_decision": str(release_decision or "NO_GO"),
        "acceptance_status": str(acceptance_status or map_release_decision_to_acceptance_status(release_decision)),
        "evidence_level": str(evidence_level),
        "evidence_status": str(evidence_status or ("complete" if acceptance_eligible else "degraded")),
        "pack_status": pack_status,
        "pack_acceptance_eligible": bool(acceptance_eligible) and pack_status == "complete",
        "pack_root": "tables",
        "required_artifacts": required,
        "optional_artifacts": optional,
        "missing_artifacts": missing,
        "pack_generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if isinstance(metadata, Mapping):
        for key, value in metadata.items():
            pack[str(key)] = value
    return pack


def render_milestone_acceptance_review(summary: Mapping[str, Any]) -> str:
    supporting_artifacts = summary.get("supporting_artifacts", {})
    if not isinstance(supporting_artifacts, Mapping):
        supporting_artifacts = {}
    release_pack_summary = summary.get("release_pack_summary", {})
    if not isinstance(release_pack_summary, Mapping):
        release_pack_summary = {}
    outcome_feedback = summary.get("outcome_feedback_summary", {})
    if not isinstance(outcome_feedback, Mapping):
        outcome_feedback = {}
    behavior_aware = summary.get("behavior_aware_summary", {})
    if not isinstance(behavior_aware, Mapping):
        behavior_aware = {}
    offer_optimization = summary.get("offer_optimization_summary", {})
    if not isinstance(offer_optimization, Mapping):
        offer_optimization = {}
    offer_metrics = offer_optimization.get("canonical_metrics", offer_optimization)
    if not isinstance(offer_metrics, Mapping):
        offer_metrics = {}
    trajectory = summary.get("trajectory_summary", {})
    if not isinstance(trajectory, Mapping):
        trajectory = {}
    trajectory_metrics = trajectory.get("canonical_metrics", trajectory)
    if not isinstance(trajectory_metrics, Mapping):
        trajectory_metrics = {}

    def _safe_float(value: Any) -> float:
        try:
            return float(value)
        except Exception:
            return 0.0

    telemetry_gate_status = str(summary.get("telemetry_gate_status", ""))
    pack_status = str(release_pack_summary.get("pack_status", "complete"))
    outcome_comparison_status = str(outcome_feedback.get("comparison_status", "not_available"))
    evidence_status = "complete"
    if (
        str(summary.get("evidence_status", "complete")) != "complete"
        or telemetry_gate_status == "degraded"
        or pack_status != "complete"
        or outcome_comparison_status == "baseline_missing"
    ):
        evidence_status = "degraded"

    evidence_reason = ""
    if telemetry_gate_status == "degraded":
        evidence_reason = "telemetry_degraded"
    elif list(release_pack_summary.get("missing_artifacts", [])):
        evidence_reason = "missing_artifacts"
    elif outcome_comparison_status == "baseline_missing":
        evidence_reason = "baseline_missing"
    elif str(summary.get("degraded_reason", "")).strip():
        evidence_reason = str(summary.get("degraded_reason", "")).strip()

    best_arm = outcome_feedback.get("best_proxy_improving_arm", {})
    if not isinstance(best_arm, Mapping):
        best_arm = {}
    worst_arm = outcome_feedback.get("worst_proxy_regressing_arm", {})
    if not isinstance(worst_arm, Mapping):
        worst_arm = {}

    lines = [
        "# Milestone Acceptance Review",
        "",
        f"Evidence Status: {evidence_status}" + (f" ({evidence_reason})" if evidence_reason else ""),
        "",
        "## Decision",
        "",
        f"- Acceptance status: {summary.get('acceptance_status', REJECTED)}",
        f"- Release decision: {summary.get('release_decision', 'NO_GO')}",
        f"- Evidence level: {summary.get('evidence_level', '')}",
        f"- Acceptance eligible: {bool(summary.get('acceptance_eligible', False))}",
        f"- Broad rollout allowed: {bool(summary.get('broad_rollout_allowed', False))}",
        f"- Phase: {summary.get('phase', '')}",
        f"- Milestone: {summary.get('milestone', '')}",
        f"- Model version: {summary.get('model_version', '')}",
        f"- Freeze mode: {summary.get('model_freeze_mode', '')}",
        "",
        "## Telemetry Readiness",
        "",
        f"- Telemetry gate status: {telemetry_gate_status or 'unknown'}",
        f"- Telemetry failure reason: {summary.get('telemetry_failure_reason', '') or 'none'}",
        f"- Telemetry success rate: {_safe_float(summary.get('telemetry_success_rate', 0.0)):.6f}",
        f"- Telemetry ingest lag (s): {_safe_float(summary.get('telemetry_ingest_lag_s', 0.0)):.6f}",
        f"- Broad rollout allowed: {bool(summary.get('broad_rollout_allowed', False))}",
        f"- Pilot eligible: {bool(summary.get('pilot_eligible', False))}",
        "",
        "## Release Pack Completeness",
        "",
        f"- Pack status: {pack_status or 'complete'}",
        f"- Pack acceptance eligible: {bool(release_pack_summary.get('pack_acceptance_eligible', False))}",
        f"- Required artifacts: {len(release_pack_summary.get('required_artifacts', {}))}",
        f"- Optional artifacts: {len(release_pack_summary.get('optional_artifacts', {}))}",
        f"- Missing artifacts: {', '.join(release_pack_summary.get('missing_artifacts', [])) or 'none'}",
        "",
        "## Outcome Feedback Summary",
        "",
        f"- Comparison status: {outcome_comparison_status}",
        f"- Outcome feedback confidence: {outcome_feedback.get('outcome_feedback_confidence', TENTATIVE)}",
        f"- Best proxy-improving arm: {best_arm.get('policy_arm', '') or 'none'}",
        f"- Worst proxy-regressing arm: {worst_arm.get('policy_arm', '') or 'none'}",
        f"- approval_rate delta: {_safe_float(outcome_feedback.get('approval_rate_delta', 0.0)):.6f}",
        f"- default_rate_90d delta: {_safe_float(outcome_feedback.get('default_rate_90d_delta', 0.0)):.6f}",
        f"- avg_margin_90d delta: {_safe_float(outcome_feedback.get('avg_margin_90d_delta', 0.0)):.6f}",
        "",
        "## Offer Optimization Summary",
        "",
        f"- Offer plan rate: {_safe_float(offer_metrics.get('offer_plan_rate', 0.0)):.6f}",
        f"- Rankable offer rate: {_safe_float(offer_metrics.get('rankable_offer_rate', 0.0)):.6f}",
        f"- Mean offer acceptance probability: {_safe_float(offer_metrics.get('offer_acceptance_probability_mean', 0.0)):.6f}",
        f"- Mean combined realization probability: {_safe_float(offer_metrics.get('combined_plan_realization_probability_mean', 0.0)):.6f}",
        f"- Expected recovery proxy: {_safe_float(offer_metrics.get('expected_recovery_proxy', 0.0)):.6f}",
        f"- approval_rate proxy delta: {_safe_float(offer_metrics.get('approval_rate_proxy_delta', 0.0)):.6f}",
        f"- default_rate_90d proxy delta: {_safe_float(offer_metrics.get('default_rate_90d_proxy_delta', 0.0)):.6f}",
        f"- avg_margin_90d proxy delta: {_safe_float(offer_metrics.get('avg_margin_90d_proxy_delta', 0.0)):.6f}",
        f"- Governance-safe offer rate: {_safe_float(offer_metrics.get('governance_safe_offer_rate', 0.0)):.6f}",
        f"- Dominant offer type: {offer_metrics.get('dominant_offer_type', '') or 'none'}",
        "",
        "## Behavior-Aware Summary",
        "",
        f"- Mean plan execution probability: {_safe_float(behavior_aware.get('mean_plan_execution_probability', 0.0)):.6f}",
        f"- Expected PD improvement: {_safe_float(behavior_aware.get('expected_pd_improvement', 0.0)):.6f}",
        f"- Mixed execution rate: {_safe_float(behavior_aware.get('mixed_execution_rate', 0.0)):.6f}",
        f"- Failed execution rate: {_safe_float(behavior_aware.get('failed_execution_rate', 0.0)):.6f}",
        f"- Expected partial progress rate: {_safe_float(behavior_aware.get('expected_partial_progress_rate', 0.0)):.6f}",
        "",
        "## Trajectory Summary",
        "",
        f"- Primary checkpoint week: {int(_safe_float(trajectory.get('primary_checkpoint_week', 4.0)))}",
        f"- trajectory_gate_pass_rate_4w: {_safe_float(trajectory_metrics.get('trajectory_gate_pass_rate_4w', 0.0)):.6f}",
        f"- trajectory_gate_pass_rate_12w: {_safe_float(trajectory_metrics.get('trajectory_gate_pass_rate_12w', 0.0)):.6f}",
        f"- trajectory_gate_pass_rate_24w: {_safe_float(trajectory_metrics.get('trajectory_gate_pass_rate_24w', 0.0)):.6f}",
        f"- trajectory_partial_progress_rate: {_safe_float(trajectory_metrics.get('trajectory_partial_progress_rate', 0.0)):.6f}",
        f"- trajectory_soft_regression_penalty_mean: {_safe_float(trajectory_metrics.get('trajectory_soft_regression_penalty_mean', 0.0)):.6f}",
        f"- trajectory_on_track_rate: {_safe_float(trajectory_metrics.get('trajectory_on_track_rate', 0.0)):.6f}",
        f"- trajectory_needs_replan_rate: {_safe_float(trajectory_metrics.get('trajectory_needs_replan_rate', 0.0)):.6f}",
        f"- trajectory_degraded_rate: {_safe_float(trajectory_metrics.get('trajectory_degraded_rate', 0.0)):.6f}",
        f"- dominant_transition_reason: {trajectory.get('dominant_transition_reason', '') or 'none'}",
    ]
    if supporting_artifacts:
        lines.extend(["", "## Supporting Artifacts", ""])
        for key in sorted(supporting_artifacts.keys(), key=str):
            lines.append(f"- {key}: {supporting_artifacts[key]}")
    return "\n".join(lines) + "\n"
