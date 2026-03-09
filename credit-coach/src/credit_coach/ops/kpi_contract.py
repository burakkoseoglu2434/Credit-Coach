from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

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


def _coerce_value(key: str, value: Any) -> float | bool:
    if key == "require_telemetry_enabled":
        return bool(value)
    return float(value)


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
