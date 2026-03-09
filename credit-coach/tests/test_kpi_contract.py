from __future__ import annotations

from argparse import Namespace

from credit_coach.ops.kpi_contract import (
    DEFAULT_KPI_THRESHOLDS,
    apply_kpi_thresholds_to_args,
    extract_kpi_thresholds,
    load_kpi_thresholds,
)


def test_load_kpi_thresholds_missing_file_falls_back_to_defaults(tmp_path):
    cfg = load_kpi_thresholds(tmp_path / "missing.yaml")
    assert cfg == DEFAULT_KPI_THRESHOLDS


def test_load_kpi_thresholds_merges_known_fields(tmp_path):
    path = tmp_path / "kpi_contract.yaml"
    path.write_text(
        "\n".join(
            [
                "thresholds:",
                "  min_denied_to_approved_lift: 0.08",
                "  min_denied_gate_pass_rate: 0.12",
                "  max_denied_reliability_violation_rate: 0.35",
                "  max_p95_latency_ms: 350",
                "  require_telemetry_enabled: true",
                "  unknown_key: 123",
            ]
        ),
        encoding="utf-8",
    )
    cfg = load_kpi_thresholds(path)
    assert float(cfg["min_denied_to_approved_lift"]) == 0.08
    assert float(cfg["min_denied_gate_pass_rate"]) == 0.12
    assert float(cfg["max_denied_reliability_violation_rate"]) == 0.35
    assert float(cfg["max_p95_latency_ms"]) == 350.0
    assert bool(cfg["require_telemetry_enabled"]) is True
    assert "unknown_key" not in cfg


def test_apply_and_extract_kpi_thresholds():
    args = Namespace(
        min_denied_to_approved_lift=None,
        min_denied_high_risk_lift=None,
        min_denied_gate_pass_rate=None,
        max_denied_reliability_violation_rate=None,
        max_approval_gap_delta=None,
        max_equalized_odds_gap_delta=None,
        max_p95_latency_ms=999.0,
        max_p99_latency_ms=None,
        max_error_rate=None,
        min_last_k_validity=None,
        min_last_k_safe_rate=None,
        min_last_k_avg_risk_margin=None,
        max_fairness_gap=None,
        max_high_stress_fairness_gap=None,
        max_recourse_success_gap=None,
        max_recourse_cost_gap=None,
        min_approval_rate=None,
        max_psi=None,
        min_avg_reliability=None,
        min_telemetry_success_rate=None,
        max_telemetry_ingest_lag_s=None,
        require_telemetry_enabled=None,
    )
    resolved_args = apply_kpi_thresholds_to_args(args, DEFAULT_KPI_THRESHOLDS)
    assert float(resolved_args.min_denied_to_approved_lift) == float(DEFAULT_KPI_THRESHOLDS["min_denied_to_approved_lift"])
    # explicit CLI value should stay untouched
    assert float(resolved_args.max_p95_latency_ms) == 999.0

    out = extract_kpi_thresholds(resolved_args)
    assert float(out["max_p95_latency_ms"]) == 999.0
    assert float(out["min_denied_gate_pass_rate"]) == float(DEFAULT_KPI_THRESHOLDS["min_denied_gate_pass_rate"])
    assert float(out["max_denied_reliability_violation_rate"]) == float(
        DEFAULT_KPI_THRESHOLDS["max_denied_reliability_violation_rate"]
    )
    assert bool(out["require_telemetry_enabled"]) is True
