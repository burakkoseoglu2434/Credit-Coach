from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from credit_coach.cli import run_pilot_integration
from credit_coach.data.ingest import load_feature_contract
from credit_coach.pilot.io import load_pilot_bundle, normalize_pilot_dataframe
from credit_coach.utils.run_context import create_run_context


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FEATURE_CONTRACT = load_feature_contract(PROJECT_ROOT / "configs/features_48.yaml")
FEATURES = list(FEATURE_CONTRACT["features"])
TARGET = str(FEATURE_CONTRACT["target"])


def _source_row(*, customer_id: str = "cust-001") -> dict[str, object]:
    row: dict[str, object] = {}
    for index, feature in enumerate(FEATURES, start=1):
        if feature in {
            "grade",
            "sub_grade",
            "purpose",
            "application_type",
            "emp_title",
            "emp_length",
            "home_ownership",
            "verification_status",
            "addr_state",
            "zip_code",
            "earliest_cr_line",
            "issue_d",
            "initial_list_status",
            "debt_settlement_flag",
            "disbursement_method",
            "term",
        }:
            row[feature] = "A"
        else:
            row[feature] = float(index)
    row["customer_key"] = customer_id
    row["outcome_label"] = 0
    row["home_owner_group"] = "RENT"
    row["home_ownership"] = "RENT"
    return row


def _write_bundle(tmp_path: Path, source_path: Path) -> Path:
    bundle_path = tmp_path / "pilot_bundle.json"
    bundle_path.write_text(
        json.dumps(
            {
                "contract_version": "phase39.input.v1",
                "institution": {
                    "institution_name": "Test Bank",
                    "institution_type": "bank",
                    "portfolio_focus": "denied recovery",
                    "data_readiness": "sample-export",
                },
                "source": {
                    "data_path": str(source_path),
                    "data_format": "csv",
                    "source_export_name": "pilot_export",
                },
                "mapping": {
                    "customer_id_column": "customer_key",
                    "target_column": "outcome_label",
                    "group_feature_name": "home_ownership",
                    "group_feature_column": "home_owner_group",
                    "feature_columns": {},
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return bundle_path


def test_normalize_pilot_dataframe_uses_identity_fallback_and_preserves_group_feature(tmp_path: Path) -> None:
    source_path = tmp_path / "pilot_source.csv"
    pd.DataFrame([_source_row(customer_id="cust-101")]).to_csv(source_path, index=False)
    bundle = load_pilot_bundle(_write_bundle(tmp_path, source_path))

    normalized, resolved = normalize_pilot_dataframe(
        bundle,
        required_features=FEATURES,
        target_column_name=TARGET,
    )

    assert normalized.loc[0, "customer_id"] == "cust-101"
    assert normalized.loc[0, TARGET] == 0
    assert normalized.loc[0, "home_ownership"] == "RENT"
    assert resolved.explicit_feature_count == 0
    assert "loan_amnt" in resolved.identity_fallback_features


def test_normalize_pilot_dataframe_fails_closed_on_missing_required_feature(tmp_path: Path) -> None:
    row = _source_row()
    row.pop("loan_amnt")
    source_path = tmp_path / "pilot_source.csv"
    pd.DataFrame([row]).to_csv(source_path, index=False)
    bundle = load_pilot_bundle(_write_bundle(tmp_path, source_path))

    with pytest.raises(ValueError, match="missing required feature mappings"):
        normalize_pilot_dataframe(
            bundle,
            required_features=FEATURES,
            target_column_name=TARGET,
        )


def test_run_pilot_integration_emits_pilot_package_and_reuses_batch_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "pilot_source.csv"
    pd.DataFrame([_source_row(customer_id="cust-201"), _source_row(customer_id="cust-202")]).to_csv(
        source_path,
        index=False,
    )
    bundle_path = _write_bundle(tmp_path, source_path)
    captured: dict[str, object] = {}

    def _fake_batch_main(argv: list[str] | None = None):
        captured["argv"] = list(argv or [])
        batch_ctx = create_run_context({"fake": "batch"}, base_artifact_dir=tmp_path / "engine_runs")
        (batch_ctx.tables_dir / "batch_summary.json").write_text(
            json.dumps(
                {
                    "model_version": "model-001",
                    "model_freeze_mode": "explicit_model_version",
                    "denied_count": 100,
                    "denied_with_gate_pass_plan": 12,
                    "denied_to_approved_lift": 0.11,
                    "denied_high_risk_lift": 0.05,
                    "denied_reliability_violation_rate": 0.10,
                    "sync_latency_p95_ms": 120.0,
                    "sync_latency_p99_ms": 220.0,
                    "error_rate": 0.0,
                    "fairness_approval_gap_after": 0.04,
                    "trajectory_gate_pass_rate_4w": 0.08,
                    "trajectory_gate_pass_rate_12w": 0.12,
                    "trajectory_gate_pass_rate_24w": 0.20,
                    "trajectory_partial_progress_rate": 0.35,
                    "trajectory_median_time_to_gate_pass_days": 56.0,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        pd.DataFrame(
            [
                {
                    "approval_gap_delta": 0.0,
                    "equalized_odds_gap_delta": 0.0,
                    "high_stress_approval_gap_after": 0.04,
                    "recourse_success_gap": 0.03,
                }
            ]
        ).to_csv(batch_ctx.tables_dir / "batch_fairness_change.csv", index=False)
        pd.DataFrame([{"customer_id": "cust-201"}]).to_csv(
            batch_ctx.tables_dir / "batch_recourse_results.csv",
            index=False,
        )
        (batch_ctx.tables_dir / "batch_run_manifest.json").write_text(
            json.dumps({"run_id": batch_ctx.run_id}, indent=2),
            encoding="utf-8",
        )
        (batch_ctx.tables_dir / "portfolio_validation_summary.json").write_text(
            json.dumps(
                {
                    "canonical_metrics": {
                        "realism_clean_plan_rate": 0.7,
                        "false_optimism_exposure": 0.1,
                        "unstable_target_range_exposure": 0.05,
                        "narrow_distribution_exposure": 0.02,
                    },
                    "product_proof": {
                        "proof_verdict": "working",
                        "proof_confidence": "moderate",
                        "headline_metrics": {"product_ready_plan_coverage": 0.65},
                        "supporting_metrics": {"weak_4w_health_rate": 0.2},
                        "phase17_delta": {},
                        "demo_fit_annotation": {},
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (batch_ctx.tables_dir / "portfolio_validation_review.md").write_text(
            "# Pilot Portfolio Review\n",
            encoding="utf-8",
        )
        pd.DataFrame([{"slice_type": "all", "count": 2}]).to_csv(
            batch_ctx.tables_dir / "portfolio_calibration_validation_breakdown.csv",
            index=False,
        )
        (batch_ctx.tables_dir / "decision_logging_summary.json").write_text(
            json.dumps({"decision_log_completeness": 0.95}, indent=2),
            encoding="utf-8",
        )
        return batch_ctx

    monkeypatch.setattr(run_pilot_integration.run_batch_recourse_eval, "main", _fake_batch_main)

    pilot_ctx = run_pilot_integration.main(
        [
            "--pilot_bundle",
            str(bundle_path),
            "--artifact_root",
            str(tmp_path / "pilot_runs"),
        ]
    )

    argv = captured["argv"]
    assert isinstance(argv, list)
    assert "--input_data_path" in argv
    assert "--group_feature" in argv
    assert "home_ownership" in argv

    manifest = json.loads((pilot_ctx.tables_dir / "pilot_package_manifest.json").read_text(encoding="utf-8"))
    acceptance = json.loads((pilot_ctx.tables_dir / "milestone_acceptance_summary.json").read_text(encoding="utf-8"))
    release_pack = json.loads((pilot_ctx.tables_dir / "release_evidence_pack.json").read_text(encoding="utf-8"))

    assert manifest["acceptance_status"] == "PILOT_ONLY"
    assert manifest["pilot_eligible"] is True
    assert manifest["broad_rollout_allowed"] is False
    assert acceptance["acceptance_status"] == "PILOT_ONLY"
    assert release_pack["acceptance_status"] == "PILOT_ONLY"
    assert (pilot_ctx.tables_dir / "product_confidence_snapshot.json").exists()
    assert (pilot_ctx.tables_dir / "pilot_guardrails.json").exists()
    assert (pilot_ctx.tables_dir / "pilot_input_manifest.json").exists()
