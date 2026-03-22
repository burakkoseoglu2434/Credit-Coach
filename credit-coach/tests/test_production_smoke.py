from __future__ import annotations

from argparse import Namespace

import pandas as pd

from credit_coach.cli.run_production_smoke import (
    _kpi_snapshot_from_rows,
    _resolve_artifact_from_release_pack,
    build_smoke_gate_rows,
    build_smoke_release_summary,
)


def _args(**overrides) -> Namespace:
    base = {
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
        "min_trajectory_gate_pass_rate_4w": 0.03,
        "min_trajectory_gate_pass_rate_12w": 0.06,
        "min_trajectory_gate_pass_rate_24w": 0.09,
        "min_trajectory_partial_progress_rate": 0.20,
        "max_trajectory_median_time_to_gate_pass_days": 168.0,
        "min_approval_rate": 0.60,
        "max_psi": 0.25,
        "min_avg_reliability": 0.70,
        "min_telemetry_success_rate": 0.99,
        "max_telemetry_ingest_lag_s": 60.0,
        "require_telemetry_enabled": False,
    }
    base.update(overrides)
    return Namespace(**base)


def test_build_smoke_gate_rows_passes():
    batch_summary = {
        "denied_to_approved_lift": 0.08,
        "denied_high_risk_lift": 0.04,
        "denied_count": 100,
        "denied_with_gate_pass_plan": 10,
        "denied_reliability_violation_rate": 0.20,
        "latency_p95_ms": 420.0,
        "latency_p99_ms": 1800.0,
        "error_rate": 0.003,
        "trajectory_gate_pass_rate_4w": 0.05,
        "trajectory_gate_pass_rate_12w": 0.09,
        "trajectory_gate_pass_rate_24w": 0.13,
        "trajectory_partial_progress_rate": 0.35,
        "trajectory_median_time_to_gate_pass_days": 84.0,
    }
    batch_fairness_change = pd.DataFrame([{"approval_gap_delta": 0.005, "equalized_odds_gap_delta": 0.004}])
    benchmark = pd.DataFrame(
        [{"method": "our", "last_k_validity": 0.95, "last_k_safe_rate": 0.90, "last_k_avg_risk_margin": 0.15}]
    )
    monitoring = pd.DataFrame([{"approval_rate": 0.85, "max_psi": 0.08, "avg_reliability": 0.93}])
    fairness = pd.DataFrame([{"approval_gap": 0.06}])
    fairness_stress = pd.DataFrame([{"high_stress": 1, "approval_gap": 0.07}])
    telemetry = {
        "enabled": True,
        "status": "success",
        "exported": True,
        "telemetry_status": "success",
        "telemetry_failure_reason": "",
        "send_success_rate": 1.0,
        "ingest_lag_s_p95": 12.0,
    }

    rows = build_smoke_gate_rows(
        batch_summary=batch_summary,
        batch_fairness_change_df=batch_fairness_change,
        benchmark_df=benchmark,
        monitoring_df=monitoring,
        fairness_df=fairness,
        fairness_stress_df=fairness_stress,
        telemetry_payload=telemetry,
        telemetry_artifact_path="tables/telemetry_export.json",
        audit_ok=True,
        audit_issue_count=0,
        args=_args(),
    )
    out = pd.DataFrame(rows)
    assert len(out) == 8
    assert (out["status"] == "PASS").all()
    recourse_row = out[out["gate_id"] == "G0B_RECOURSE_FUNNEL"].iloc[0]
    assert recourse_row["status"] == "PASS"


def test_build_smoke_gate_rows_detects_failures():
    batch_summary = {
        "denied_to_approved_lift": 0.01,
        "denied_high_risk_lift": 0.0,
        "denied_count": 100,
        "denied_with_gate_pass_plan": 2,
        "denied_reliability_violation_rate": 0.95,
        "latency_p95_ms": 800.0,
        "latency_p99_ms": 3500.0,
        "error_rate": 0.02,
        "trajectory_gate_pass_rate_4w": 0.0,
        "trajectory_gate_pass_rate_12w": 0.01,
        "trajectory_gate_pass_rate_24w": 0.01,
        "trajectory_partial_progress_rate": 0.05,
        "trajectory_median_time_to_gate_pass_days": 365.0,
    }
    batch_fairness_change = pd.DataFrame([{"approval_gap_delta": 0.03, "equalized_odds_gap_delta": 0.02}])
    benchmark = pd.DataFrame(
        [{"method": "our", "last_k_validity": 0.65, "last_k_safe_rate": 0.40, "last_k_avg_risk_margin": -0.2}]
    )
    monitoring = pd.DataFrame([{"approval_rate": 0.50, "max_psi": 0.40, "avg_reliability": 0.40}])
    fairness = pd.DataFrame([{"approval_gap": 0.18}])
    fairness_stress = pd.DataFrame([{"high_stress": 1, "approval_gap": 0.22}])
    telemetry = {
        "enabled": False,
        "status": "disabled",
        "exported": False,
        "telemetry_status": "disabled",
        "telemetry_failure_reason": "disabled_exporter",
        "send_success_rate": 0.0,
        "ingest_lag_s_p95": 999.0,
    }

    rows = build_smoke_gate_rows(
        batch_summary=batch_summary,
        batch_fairness_change_df=batch_fairness_change,
        benchmark_df=benchmark,
        monitoring_df=monitoring,
        fairness_df=fairness,
        fairness_stress_df=fairness_stress,
        telemetry_payload=telemetry,
        telemetry_artifact_path="tables/telemetry_export.json",
        audit_ok=False,
        audit_issue_count=2,
        args=_args(require_telemetry_enabled=True),
    )
    out = pd.DataFrame(rows)
    assert len(out) == 8
    assert (out["status"] == "FAIL").all()
    recourse_row = out[out["gate_id"] == "G0B_RECOURSE_FUNNEL"].iloc[0]
    assert recourse_row["status"] == "FAIL"


def test_build_smoke_gate_rows_prefers_sync_latency_when_available():
    batch_summary = {
        "denied_to_approved_lift": 0.09,
        "denied_high_risk_lift": 0.04,
        "denied_count": 100,
        "denied_with_gate_pass_plan": 10,
        "denied_reliability_violation_rate": 0.30,
        "latency_p95_ms": 1200.0,
        "latency_p99_ms": 1800.0,
        "sync_latency_p95_ms": 420.0,
        "sync_latency_p99_ms": 700.0,
        "error_rate": 0.0,
        "trajectory_gate_pass_rate_4w": 0.05,
        "trajectory_gate_pass_rate_12w": 0.09,
        "trajectory_gate_pass_rate_24w": 0.12,
        "trajectory_partial_progress_rate": 0.30,
        "trajectory_median_time_to_gate_pass_days": 84.0,
    }
    batch_fairness_change = pd.DataFrame([{"approval_gap_delta": 0.0, "equalized_odds_gap_delta": 0.0}])
    benchmark = pd.DataFrame(
        [{"method": "our", "last_k_validity": 0.95, "last_k_safe_rate": 0.90, "last_k_avg_risk_margin": 0.15}]
    )
    monitoring = pd.DataFrame([{"approval_rate": 0.85, "max_psi": 0.08, "avg_reliability": 0.93}])
    fairness = pd.DataFrame([{"approval_gap": 0.06}])
    fairness_stress = pd.DataFrame([{"high_stress": 1, "approval_gap": 0.07}])
    telemetry = {
        "enabled": True,
        "status": "success",
        "exported": True,
        "telemetry_status": "success",
        "telemetry_failure_reason": "",
        "send_success_rate": 1.0,
        "ingest_lag_s_p95": 12.0,
    }

    rows = build_smoke_gate_rows(
        batch_summary=batch_summary,
        batch_fairness_change_df=batch_fairness_change,
        benchmark_df=benchmark,
        monitoring_df=monitoring,
        fairness_df=fairness,
        fairness_stress_df=fairness_stress,
        telemetry_payload=telemetry,
        telemetry_artifact_path="tables/telemetry_export.json",
        audit_ok=True,
        audit_issue_count=0,
        args=_args(),
    )
    out = pd.DataFrame(rows)
    g0 = out[out["gate_id"] == "G0_BATCH_RECOURSE_KPI"].iloc[0]
    assert g0["status"] == "PASS"
    assert "latency_mode" in g0["details_json"]


def test_build_smoke_release_summary_uses_fallback_single_seed_contract():
    batch_summary = {
        "denied_count": 100,
        "denied_with_gate_pass_plan": 10,
        "denied_to_approved_lift": 0.10,
        "denied_high_risk_lift": 0.04,
        "denied_reliability_violation_rate": 0.20,
        "sync_latency_p95_ms": 420.0,
        "sync_latency_p99_ms": 700.0,
        "error_rate": 0.0,
        "fairness_approval_gap_after": 0.06,
        "trajectory_gate_pass_rate_4w": 0.05,
        "trajectory_gate_pass_rate_12w": 0.09,
        "trajectory_gate_pass_rate_24w": 0.12,
        "trajectory_partial_progress_rate": 0.30,
        "trajectory_median_time_to_gate_pass_days": 84.0,
    }
    batch_fairness_change = pd.DataFrame(
        [{"approval_gap_delta": 0.0, "equalized_odds_gap_delta": 0.0, "high_stress_approval_gap_after": 0.07, "recourse_success_gap": 0.05}]
    )

    payload = build_smoke_release_summary(
        batch_summary=batch_summary,
        batch_fairness_change_df=batch_fairness_change,
        thresholds=_args().__dict__,
    )
    assert payload["release_decision"] == "GO"
    assert payload["smoke_pass"] is False
    assert payload["pilot_eligible"] is False
    assert payload["acceptance_eligible"] is False
    assert payload["evidence_level"] == "single_run_fallback"
    assert payload["broad_rollout_allowed"] is False
    assert payload["degraded_reason"] == "missing_repeated_seeded_evidence"
    assert payload["acceptance_status"] == "PILOT_ONLY"
    assert payload["telemetry_gate_status"] == "degraded"
    assert payload["telemetry_failure_reason"] == "missing_artifact"


def test_build_smoke_release_summary_respects_phase_scale_limited_go():
    payload = build_smoke_release_summary(
        batch_summary={},
        batch_fairness_change_df=pd.DataFrame(),
        thresholds=_args().__dict__,
        telemetry_payload={
            "enabled": False,
            "exported": False,
            "telemetry_status": "disabled",
            "telemetry_failure_reason": "disabled_exporter",
        },
        telemetry_artifact_path="",
        phase_scale_aggregate={
            "lift_pass": True,
            "reliability_pass": True,
            "fairness_seed_pass_count": 4,
            "fairness_seed_total": 5,
            "worst_fairness_gap": 0.012,
            "supporting_guardrails_within_limited_cap": True,
            "dominant_fail_segment_key": "mid|q1|stress",
            "dominant_fail_candidate_source": "internal",
            "dominant_fail_segment_share": 0.71,
        },
    )
    assert payload["release_decision"] == "LIMITED_GO"
    assert payload["smoke_pass"] is False
    assert payload["pilot_eligible"] is False
    assert payload["acceptance_eligible"] is True
    assert payload["evidence_level"] == "seeded_suite"
    assert payload["telemetry_gate_status"] == "degraded"
    assert payload["telemetry_failure_reason"] == "missing_artifact"


def test_build_smoke_release_summary_prefers_milestone_acceptance_summary() -> None:
    payload = build_smoke_release_summary(
        batch_summary={},
        batch_fairness_change_df=pd.DataFrame(),
        thresholds=_args().__dict__,
        telemetry_payload={
            "enabled": True,
            "exported": True,
            "telemetry_status": "success",
            "telemetry_failure_reason": "",
            "send_success_rate": 1.0,
            "ingest_lag_s_p95": 12.0,
        },
        telemetry_artifact_path="tables/telemetry_export.json",
        phase_scale_aggregate={
            "lift_pass": True,
            "reliability_pass": True,
            "fairness_seed_pass_count": 5,
            "fairness_seed_total": 5,
            "model_freeze_mode": "explicit_model_version",
        },
        milestone_acceptance_summary={
            "release_decision": "LIMITED_GO",
            "smoke_pass": False,
            "pilot_eligible": True,
            "broad_rollout_allowed": False,
            "evidence_level": "seeded_suite",
            "evidence_status": "complete",
            "acceptance_eligible": True,
            "lift_pass": True,
            "reliability_pass": True,
            "fairness_seed_pass_count": 4,
            "seed_count": 5,
            "primary_fairness_metric": "equalized_odds_gap_delta",
            "worst_primary_fairness_gap": 0.012,
            "dominant_fail_segment_key": "mid|q1|stress",
            "dominant_fail_candidate_source": "internal",
            "model_version": "model-123",
            "model_freeze_mode": "explicit_model_version",
            "candidate_quality_summary": {
                "candidate_quality_population": "denied",
                "candidate_quality_secondary_population": "high_risk_denied",
            },
            "high_risk_tuning_summary": {
                "primary_metric": "denied_high_risk_lift",
                "high_risk_profile_applied_rate": 0.07,
            },
            "impact_attribution_summary": {
                "baseline_label": "control_logistic_isotonic",
                "comparative_impact_confidence": "tentative",
            },
        },
    )
    assert payload["release_decision"] == "LIMITED_GO"
    assert payload["pilot_eligible"] is True
    assert payload["acceptance_eligible"] is True
    assert payload["model_version"] == "model-123"
    assert payload["telemetry_gate_status"] == "healthy"


def test_build_smoke_gate_rows_marks_missing_telemetry_artifact_when_required() -> None:
    rows = build_smoke_gate_rows(
        batch_summary={
            "denied_to_approved_lift": 0.08,
            "denied_high_risk_lift": 0.04,
            "denied_count": 100,
            "denied_with_gate_pass_plan": 10,
            "denied_reliability_violation_rate": 0.20,
            "latency_p95_ms": 420.0,
            "latency_p99_ms": 1800.0,
            "error_rate": 0.003,
            "trajectory_gate_pass_rate_4w": 0.05,
            "trajectory_gate_pass_rate_12w": 0.09,
            "trajectory_gate_pass_rate_24w": 0.13,
            "trajectory_partial_progress_rate": 0.35,
            "trajectory_median_time_to_gate_pass_days": 84.0,
        },
        batch_fairness_change_df=pd.DataFrame([{"approval_gap_delta": 0.005, "equalized_odds_gap_delta": 0.004}]),
        benchmark_df=pd.DataFrame(
            [{"method": "our", "last_k_validity": 0.95, "last_k_safe_rate": 0.90, "last_k_avg_risk_margin": 0.15}]
        ),
        monitoring_df=pd.DataFrame([{"approval_rate": 0.85, "max_psi": 0.08, "avg_reliability": 0.93}]),
        fairness_df=pd.DataFrame([{"approval_gap": 0.06}]),
        fairness_stress_df=pd.DataFrame([{"high_stress": 1, "approval_gap": 0.07}]),
        telemetry_payload={},
        telemetry_artifact_path="",
        audit_ok=True,
        audit_issue_count=0,
        args=_args(require_telemetry_enabled=True),
    )
    telemetry_row = pd.DataFrame(rows).query("gate_id == 'G4_MONITORING_TELEMETRY'").iloc[0]
    assert telemetry_row["status"] == "FAIL"
    assert "missing_artifact" in telemetry_row["details_json"]


def test_kpi_snapshot_from_rows_uses_shared_contract_snapshot() -> None:
    gate_rows = [
        {
            "gate_id": "G0_BATCH_RECOURSE_KPI",
            "status": "PASS",
            "failed_checks": "",
            "details_json": '{"denied_to_approved_lift": 0.08, "denied_high_risk_lift": 0.04, "approval_gap_delta": 0.005, "equalized_odds_gap_delta": 0.004, "latency_p95_ms": 420.0, "latency_p99_ms": 1800.0, "error_rate": 0.003}',
        },
        {
            "gate_id": "G0B_RECOURSE_FUNNEL",
            "status": "PASS",
            "failed_checks": "",
            "details_json": '{"denied_gate_pass_rate": 0.10, "denied_reliability_violation_rate": 0.20}',
        },
        {
            "gate_id": "G0C_TRAJECTORY",
            "status": "PASS",
            "failed_checks": "",
            "details_json": '{"trajectory_gate_pass_rate_4w": 0.05, "trajectory_gate_pass_rate_12w": 0.09, "trajectory_gate_pass_rate_24w": 0.13, "trajectory_partial_progress_rate": 0.35, "trajectory_median_time_to_gate_pass_days": 84.0}',
        },
        {
            "gate_id": "G1_MODEL_BACKTEST",
            "status": "PASS",
            "failed_checks": "",
            "details_json": '{"last_k_validity": 0.95, "last_k_safe_rate": 0.90, "last_k_avg_risk_margin": 0.15}',
        },
        {
            "gate_id": "G2_FAIRNESS",
            "status": "PASS",
            "failed_checks": "",
            "details_json": '{"fairness_gap": 0.06, "high_stress_fairness_gap": 0.07, "recourse_success_gap": 0.05, "recourse_cost_gap": 120.0}',
        },
        {
            "gate_id": "G3_ROBUSTNESS",
            "status": "PASS",
            "failed_checks": "",
            "details_json": '{"avg_reliability": 0.93}',
        },
        {
            "gate_id": "G4_MONITORING_TELEMETRY",
            "status": "PASS",
            "failed_checks": "",
            "details_json": '{"approval_rate": 0.85, "max_psi": 0.08, "telemetry_status": "success", "telemetry_gate_status": "healthy", "telemetry_failure_reason": "", "telemetry_success_rate": 0.995, "telemetry_ingest_lag_s": 12.0}',
        },
        {
            "gate_id": "G5_SECURITY_AUDIT",
            "status": "PASS",
            "failed_checks": "",
            "details_json": '{"audit_chain_ok": true}',
        },
    ]
    snapshot = _kpi_snapshot_from_rows(
        gate_rows=gate_rows,
        args=_args(),
        run_id="demo",
        overall_status="GO",
    )
    assert snapshot["run_id"] == "demo"
    assert snapshot["kpis"]["fairness_gap_after"]["pass"] is True
    assert snapshot["kpis"]["high_stress_fairness_gap_after"]["pass"] is True
    assert snapshot["kpis"]["trajectory_gate_pass_rate_24w"]["pass"] is True


def test_build_smoke_release_summary_blocks_go_when_telemetry_threshold_fails() -> None:
    payload = build_smoke_release_summary(
        batch_summary={},
        batch_fairness_change_df=pd.DataFrame(),
        thresholds=_args(require_telemetry_enabled=True).__dict__,
        telemetry_payload={
            "enabled": True,
            "exported": True,
            "telemetry_status": "success",
            "telemetry_failure_reason": "",
            "send_success_rate": 0.80,
            "ingest_lag_s_p95": 15.0,
        },
        telemetry_artifact_path="tables/telemetry_export.json",
        milestone_acceptance_summary={
            "release_decision": "GO",
            "smoke_pass": True,
            "pilot_eligible": False,
            "broad_rollout_allowed": True,
            "evidence_level": "seeded_suite",
            "evidence_status": "complete",
            "acceptance_eligible": True,
            "lift_pass": True,
            "reliability_pass": True,
            "fairness_seed_pass_count": 5,
            "seed_count": 5,
            "model_version": "model-123",
            "model_freeze_mode": "explicit_model_version",
        },
    )
    assert payload["release_decision"] == "GO"
    assert payload["smoke_pass"] is False
    assert payload["pilot_eligible"] is False
    assert payload["broad_rollout_allowed"] is False
    assert payload["telemetry_gate_status"] == "degraded"
    assert payload["telemetry_failure_reason"] == "success_rate_below_threshold"


def test_resolve_artifact_from_release_pack_uses_tables_relative_contract(tmp_path) -> None:
    run_dir = tmp_path / "run-001"
    tables_dir = run_dir / "tables"
    tables_dir.mkdir(parents=True)
    target = tables_dir / "milestone_acceptance_summary.json"
    target.write_text("{}", encoding="utf-8")
    pack_path = tables_dir / "release_evidence_pack.json"
    pack_path.write_text("{}", encoding="utf-8")

    resolved = _resolve_artifact_from_release_pack(
        pack_payload={
            "required_artifacts": {
                "milestone_acceptance_summary_json": "tables/milestone_acceptance_summary.json",
            }
        },
        pack_path=pack_path,
        artifact_key="milestone_acceptance_summary_json",
    )

    assert resolved == target
