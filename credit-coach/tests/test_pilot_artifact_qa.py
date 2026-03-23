from __future__ import annotations

import json
from pathlib import Path

from credit_coach.cli.run_pilot_artifact_qa import (
    QA_STATUS_DEGRADED,
    QA_STATUS_FAIL,
    QA_STATUS_PASS,
    evaluate_pilot_artifact_qa,
)
from credit_coach.ops.decision_explanation_pack import build_decision_explanation_pack, write_decision_explanation_pack
from credit_coach.ops.operator_review import build_operator_review_packet, write_operator_review_packet


def _sample_roadmap() -> dict:
    return {
        "customer_id": "cust-qa",
        "best_plan_id": "plan-qa",
        "summary": {
            "decision_id": "decision-cust-qa",
            "decision_policy_version": "v2.1_phase_40_5",
            "decision_status": "CONDITIONAL",
            "decision_status_internal": "NEEDS_REVIEW",
            "decision_reason_summary": "The file is improving, but utilization is still above target.",
            "decision_reason_primary": "TIME_BLOCK",
            "decision_reason_drivers": [
                {
                    "driver_key": "utilization",
                    "current_value": 82.0,
                    "target_value": 50.0,
                    "unit": "pct",
                    "source_field": "revol_util",
                    "comparison": "lte",
                }
            ],
            "expected_readiness": "week_12",
            "upgrade_condition": "Utilization 82% -> below 50%",
            "decision_confidence": 0.58,
        },
        "contract_health": {"raw_contract_pass": 1, "parity_pass": 1, "data_issue_flag": 0},
        "narrative": {
            "steps": [
                {
                    "step_id": "limit_credit_usage:phase_1",
                    "action_key": "limit_credit_usage",
                    "action_summary": {"tr": "Kart kullanimini azalt.", "en": "Reduce credit utilization."},
                }
            ]
        },
    }


def _build_collection_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    artifact_dir = tmp_path / "runs" / "refresh_collection_run"
    collection_root = artifact_dir / "tables" / "customer_artifact_collection"
    (collection_root / "flat").mkdir(parents=True, exist_ok=True)
    (collection_root / "calibration").mkdir(parents=True, exist_ok=True)
    (collection_root / "operator_packets" / "0001_cust-qa").mkdir(parents=True, exist_ok=True)
    (collection_root / "raw" / "0001_cust-qa").mkdir(parents=True, exist_ok=True)

    for relpath in [
        "flat/customer_metrics.csv",
        "flat/customer_plans.csv",
        "flat/customer_roadmap_steps.csv",
        "flat/customer_selection.csv",
        "calibration/funnel_summary.json",
        "calibration/readiness_distribution.csv",
        "calibration/status_by_readiness.csv",
        "calibration/policy_comparison.csv",
        "calibration/decision_shift_matrix.csv",
        "calibration/segment_breakdown.csv",
        "calibration/calibration_review.md",
        "operator_review_briefing.md",
    ]:
        path = collection_root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            path.write_text("{}", encoding="utf-8")
        else:
            path.write_text("ok\n", encoding="utf-8")

    roadmap = _sample_roadmap()
    operator_packet = build_operator_review_packet(roadmap)
    write_operator_review_packet(operator_packet, collection_root / "operator_packets" / "0001_cust-qa")

    explanation_root = tmp_path / "decision_explanations"
    explanation_pack = build_decision_explanation_pack(
        roadmap,
        metrics_summary={"adverse_action_reasons": ["high_credit_utilization"]},
        operator_packet=operator_packet,
    )
    write_decision_explanation_pack(explanation_pack, explanation_root / "0001_cust-qa")

    pilot_manifest_path = tmp_path / "pilot_package_manifest.json"
    pilot_manifest_path.write_text(
        json.dumps(
            {
                "policy_version_evaluated": "v2.1_phase_40_5",
                "explanation_artifacts": {
                    "decision_explanation_packs_root": str(explanation_root),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    manifest = {
        "selected_n_customers": 1,
        "policy_version_evaluated": "v2.1_phase_40_5",
        "contract_health": {
            "critical_field_null_rate": 0.0,
            "raw_flat_mismatch_count": 0,
        },
        "flat_files": {
            "customer_metrics_csv": "tables/customer_artifact_collection/flat/customer_metrics.csv",
            "customer_plans_csv": "tables/customer_artifact_collection/flat/customer_plans.csv",
            "customer_roadmap_steps_csv": "tables/customer_artifact_collection/flat/customer_roadmap_steps.csv",
            "customer_selection_csv": "tables/customer_artifact_collection/flat/customer_selection.csv",
        },
        "calibration_files": {
            "funnel_summary_json": "tables/customer_artifact_collection/calibration/funnel_summary.json",
            "readiness_distribution_csv": "tables/customer_artifact_collection/calibration/readiness_distribution.csv",
            "status_by_readiness_csv": "tables/customer_artifact_collection/calibration/status_by_readiness.csv",
            "policy_comparison_csv": "tables/customer_artifact_collection/calibration/policy_comparison.csv",
            "decision_shift_matrix_csv": "tables/customer_artifact_collection/calibration/decision_shift_matrix.csv",
            "segment_breakdown_csv": "tables/customer_artifact_collection/calibration/segment_breakdown.csv",
            "calibration_review_md": "tables/customer_artifact_collection/calibration/calibration_review.md",
        },
        "operator_files": {
            "operator_briefing_md": "tables/customer_artifact_collection/operator_review_briefing.md",
            "operator_packets_root": "tables/customer_artifact_collection/operator_packets",
        },
        "raw_root": "tables/customer_artifact_collection/raw",
    }
    manifest_path = collection_root / "collection_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path, pilot_manifest_path, explanation_root


def test_evaluate_pilot_artifact_qa_passes_for_complete_package(tmp_path: Path) -> None:
    manifest_path, pilot_manifest_path, explanation_root = _build_collection_fixture(tmp_path)

    summary = evaluate_pilot_artifact_qa(
        collection_manifest_path=manifest_path,
        pilot_package_manifest_path=pilot_manifest_path,
        explanation_root=explanation_root,
        expected_policy_version="v2.1_phase_40_5",
    )

    assert summary["artifact_qa_status"] == QA_STATUS_PASS
    assert summary["operator_packet_count"] == 1
    assert summary["decision_explanation_pack_count"] == 1


def test_evaluate_pilot_artifact_qa_degrades_when_optional_inputs_are_missing(tmp_path: Path) -> None:
    manifest_path, _, _ = _build_collection_fixture(tmp_path)

    summary = evaluate_pilot_artifact_qa(
        collection_manifest_path=manifest_path,
        pilot_package_manifest_path=None,
        explanation_root=None,
        expected_policy_version="v2.1_phase_40_5",
    )

    assert summary["artifact_qa_status"] == QA_STATUS_DEGRADED
    assert "missing_explanation_root" in summary["degraded_findings"]
    assert "missing_pilot_package_manifest" in summary["degraded_findings"]


def test_evaluate_pilot_artifact_qa_fails_on_internal_state_leak(tmp_path: Path) -> None:
    manifest_path, pilot_manifest_path, explanation_root = _build_collection_fixture(tmp_path)
    packet_path = (
        manifest_path.parent / "operator_packets" / "0001_cust-qa" / "operator_packet.json"
    )
    payload = json.loads(packet_path.read_text(encoding="utf-8"))
    payload["short_view"]["decision_status"] = "NEEDS_REVIEW"
    packet_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary = evaluate_pilot_artifact_qa(
        collection_manifest_path=manifest_path,
        pilot_package_manifest_path=pilot_manifest_path,
        explanation_root=explanation_root,
        expected_policy_version="v2.1_phase_40_5",
    )

    assert summary["artifact_qa_status"] == QA_STATUS_FAIL
    assert "operator_packet_internal_state_leak" in summary["fail_findings"]
