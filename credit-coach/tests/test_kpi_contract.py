from __future__ import annotations

from argparse import Namespace

from credit_coach.ops.kpi_contract import (
    DEFAULT_KPI_THRESHOLDS,
    apply_kpi_thresholds_to_args,
    extract_kpi_thresholds,
    load_kpi_thresholds,
    render_milestone_acceptance_review,
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


def test_render_milestone_acceptance_review_includes_learning_loop_summary() -> None:
    review = render_milestone_acceptance_review(
        {
            "acceptance_status": "ACCEPTED",
            "release_decision": "GO",
            "evidence_level": "seeded_suite",
            "acceptance_eligible": True,
            "broad_rollout_allowed": True,
            "phase": "phase-16",
            "milestone": "v1.2",
            "model_version": "model-001",
            "model_freeze_mode": "explicit_model_version",
            "telemetry_gate_status": "healthy",
            "telemetry_failure_reason": "",
            "telemetry_success_rate": 1.0,
            "telemetry_ingest_lag_s": 5.0,
            "pilot_eligible": False,
            "release_pack_summary": {
                "pack_status": "complete",
                "pack_acceptance_eligible": True,
                "required_artifacts": {},
                "optional_artifacts": {},
                "missing_artifacts": [],
            },
            "outcome_feedback_summary": {
                "comparison_status": "treatment_vs_control",
                "outcome_feedback_confidence": "strong",
                "best_proxy_improving_arm": {"policy_arm": "treatment"},
                "worst_proxy_regressing_arm": {"policy_arm": "control"},
                "approval_rate_delta": 0.02,
                "default_rate_90d_delta": -0.01,
                "avg_margin_90d_delta": 10.0,
            },
            "learning_loop_summary": {
                "decision_log_completeness": 0.9,
                "learning_readiness_status_distribution": {
                    "descriptive_only": {"count": 2, "share": 0.1},
                    "partial_learning_ready": {"count": 4, "share": 0.2},
                    "learning_ready": {"count": 14, "share": 0.7},
                },
                "reward_90d_coverage": 0.7,
                "ope_confidence": "strong",
                "comparison_status": "treatment_vs_control",
                "preferred_policy_signal": {"policy_arm": "treatment", "signal": "supports_treatment"},
                "preferred_policy_metric_labels": {
                    "approval_rate": "supports_treatment",
                    "default_rate_90d": "supports_treatment",
                    "avg_margin_90d": "mixed",
                },
            },
        }
    )

    assert "Learning Loop Summary" in review
    assert "Decision log completeness: 0.900000" in review
    assert "approval_rate OPE label: supports_treatment" in review
