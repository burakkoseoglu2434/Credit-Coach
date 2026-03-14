from __future__ import annotations

from argparse import Namespace
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
