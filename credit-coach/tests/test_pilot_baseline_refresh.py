from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from credit_coach.cli import run_pilot_baseline_refresh as refresh
from credit_coach.data.ingest import load_feature_contract
from credit_coach.ops.operator_review import build_operator_review_packet, write_operator_review_packet
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
                    "portfolio_focus": "pilot refresh",
                },
                "source": {
                    "data_path": str(source_path),
                    "data_format": "csv",
                    "source_export_name": "refresh_export",
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


def _arg_value(argv: list[str], name: str, default: str = "") -> str:
    if name not in argv:
        return default
    index = argv.index(name)
    if index + 1 >= len(argv):
        return default
    return str(argv[index + 1])


def _roadmap_for(customer_id: str, run_id: str) -> dict:
    return {
        "customer_id": customer_id,
        "best_plan_id": f"plan-{customer_id}",
        "summary": {
            "customer_id": customer_id,
            "decision_id": f"{run_id}_{customer_id}",
            "decision_policy_version": "v2.1_phase_40_5",
            "decision_status": "CONDITIONAL",
            "decision_status_internal": "NEEDS_REVIEW",
            "decision_reason_summary": "The file can improve, but utilization is still above target.",
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
            "decision_confidence": 0.58,
            "expected_readiness": "week_12",
            "upgrade_condition": "Utilization 82% -> below 50%",
            "conditional_type": "TIME_GATED",
            "offer_maturity": "none",
            "offer_plan": 0,
            "offer_acceptance_probability": 0.0,
        },
        "contract_health": {"raw_contract_pass": 1, "parity_pass": 1, "data_issue_flag": 0},
        "narrative": {
            "steps": [
                {
                    "step_id": f"limit_credit_usage:{customer_id}",
                    "action_key": "limit_credit_usage",
                    "action_summary": {"tr": "Kart kullanimini azalt.", "en": "Reduce credit utilization."},
                }
            ]
        },
    }


def _build_collection_run(tmp_path: Path, artifact_root: str, customer_ids: list[str], cohort_policy: str):
    run_ctx = create_run_context({"fake": "collection"}, base_artifact_dir=artifact_root)
    collection_root = run_ctx.tables_dir / "customer_artifact_collection"
    raw_root = collection_root / "raw"
    flat_root = collection_root / "flat"
    calibration_root = collection_root / "calibration"
    operator_root = collection_root / "operator_packets"
    raw_root.mkdir(parents=True, exist_ok=True)
    flat_root.mkdir(parents=True, exist_ok=True)
    calibration_root.mkdir(parents=True, exist_ok=True)
    operator_root.mkdir(parents=True, exist_ok=True)

    for index, customer_id in enumerate(customer_ids, start=1):
        folder = f"{index:04d}_{customer_id}"
        roadmap = _roadmap_for(customer_id, run_ctx.run_id)
        raw_dir = raw_root / folder
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "customer_roadmap.json").write_text(json.dumps(roadmap, indent=2), encoding="utf-8")
        (raw_dir / "metrics.json").write_text(
            json.dumps({"adverse_action_reasons": ["high_credit_utilization"]}, indent=2),
            encoding="utf-8",
        )
        packet = build_operator_review_packet(roadmap)
        write_operator_review_packet(packet, operator_root / folder)

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
        "calibration/policy_profile_catalog.json",
        "calibration/policy_recommendation_summary.json",
        "calibration/outcome_rule_comparison.csv",
        "calibration/outcome_rule_shift_matrix.csv",
        "calibration/outcome_rule_customer_effects.csv",
        "calibration/outcome_rule_profile_catalog.json",
        "calibration/outcome_rule_recommendation_summary.json",
        "calibration/policy_baseline_selection.json",
        "calibration/policy_candidate_disposition.csv",
        "calibration/movement_guardrail_summary.json",
        "calibration/movement_promotion_blockers.csv",
        "calibration/movement_bottleneck_breakdown.csv",
        "calibration/movement_ceiling_breakdown.csv",
        "calibration/movement_guardrail_review.md",
        "calibration/calibration_review.md",
        "operator_review_briefing.md",
    ]:
        path = collection_root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            path.write_text("{}", encoding="utf-8")
        else:
            path.write_text("ok\n", encoding="utf-8")

    manifest = {
        "collection_run_id": run_ctx.run_id,
        "selection_policy_name": cohort_policy,
        "selection_fill_behavior": "quota-first deterministic soft-fill",
        "selected_n_customers": len(customer_ids),
        "policy_version_evaluated": "v2.1_phase_40_5",
        "candidate_policy_versions_compared": [
            "analysis_mild_relax_v2_3a",
            "analysis_relaxed_v2_3a",
            "analysis_strict_control_v2_3a",
        ],
        "recommended_candidate_policy_version": "analysis_mild_relax_v2_3a",
        "recommended_candidate_status": "shortlisted",
        "recommended_candidate_reason": "Bounded yield uplift is positive while Phase 49 proxy guardrails remain within limits.",
        "candidate_outcome_rule_versions_compared": [
            "analysis_offer_support_v2_3b",
            "analysis_readiness_support_v2_3b",
            "analysis_offer_readiness_combo_v2_3b",
        ],
        "recommended_outcome_rule_profile_version": "analysis_offer_readiness_combo_v2_3b",
        "recommended_outcome_rule_status": "shortlisted",
        "recommended_outcome_rule_reason": "Offer/readiness-driven uplift is positive while Phase 50 guardrails remain within limits.",
        "preferred_demo_profile": "preferred_demo_baseline_v2_3",
        "fallback_demo_profile": "trust_first_baseline_v2_3",
        "policy_baseline_selection_reason": "Phase 52 keeps the shipped live baseline as the preferred runtime policy because shortlisted bounded candidates remain analysis-only and are not promoted in this milestone-close package.",
        "threshold_family_promotion_status": "shortlisted",
        "outcome_rule_family_promotion_status": "shortlisted",
        "next_milestone_focus": "expand_movement_levers",
        "dominant_movement_bottleneck": "structural_cohort_limited",
        "movement_guardrail_summary": "Neither threshold nor offer/readiness candidates created safe movement; this cohort appears structurally too far from near-term movement.",
        "promotion_blocker_summary": "No candidate family created promotable movement under the shipped trust and risk guardrails.",
        "funnel_summary": {
            "approved_share": 0.10,
            "conditional_share": 0.60,
            "rejected_share": 0.30,
            "approve_plus_conditional_share": 0.70,
            "internal_needs_review_share": 0.05,
        },
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
            "policy_profile_catalog_json": "tables/customer_artifact_collection/calibration/policy_profile_catalog.json",
            "policy_recommendation_summary_json": "tables/customer_artifact_collection/calibration/policy_recommendation_summary.json",
            "outcome_rule_comparison_csv": "tables/customer_artifact_collection/calibration/outcome_rule_comparison.csv",
            "outcome_rule_shift_matrix_csv": "tables/customer_artifact_collection/calibration/outcome_rule_shift_matrix.csv",
            "outcome_rule_customer_effects_csv": "tables/customer_artifact_collection/calibration/outcome_rule_customer_effects.csv",
            "outcome_rule_profile_catalog_json": "tables/customer_artifact_collection/calibration/outcome_rule_profile_catalog.json",
            "outcome_rule_recommendation_summary_json": "tables/customer_artifact_collection/calibration/outcome_rule_recommendation_summary.json",
            "policy_baseline_selection_json": "tables/customer_artifact_collection/calibration/policy_baseline_selection.json",
            "policy_candidate_disposition_csv": "tables/customer_artifact_collection/calibration/policy_candidate_disposition.csv",
            "movement_guardrail_summary_json": "tables/customer_artifact_collection/calibration/movement_guardrail_summary.json",
            "movement_promotion_blockers_csv": "tables/customer_artifact_collection/calibration/movement_promotion_blockers.csv",
            "movement_bottleneck_breakdown_csv": "tables/customer_artifact_collection/calibration/movement_bottleneck_breakdown.csv",
            "movement_ceiling_breakdown_csv": "tables/customer_artifact_collection/calibration/movement_ceiling_breakdown.csv",
            "movement_guardrail_review_md": "tables/customer_artifact_collection/calibration/movement_guardrail_review.md",
            "calibration_review_md": "tables/customer_artifact_collection/calibration/calibration_review.md",
        },
        "operator_files": {
            "operator_briefing_md": "tables/customer_artifact_collection/operator_review_briefing.md",
            "operator_packets_root": "tables/customer_artifact_collection/operator_packets",
        },
        "raw_root": "tables/customer_artifact_collection/raw",
    }
    (collection_root / "collection_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return run_ctx


def _fake_collection_main_factory(tmp_path: Path):
    def _fake_collection_main(argv: list[str] | None = None):
        argv = list(argv or [])
        input_data_path = Path(_arg_value(argv, "--input_data_path"))
        cohort_policy = _arg_value(argv, "--cohort_policy", "pilot_mixed")
        artifact_root = _arg_value(argv, "--artifact_root")
        df = pd.read_parquet(input_data_path)
        customer_ids = df["customer_id"].astype(str).tolist()
        return _build_collection_run(tmp_path, artifact_root, customer_ids, cohort_policy)

    return _fake_collection_main


def _fake_pilot_integration_main(argv: list[str] | None = None):
    argv = list(argv or [])
    artifact_root = _arg_value(argv, "--artifact_root")
    run_ctx = create_run_context({"fake": "pilot"}, base_artifact_dir=artifact_root)
    (run_ctx.tables_dir / "batch_summary.json").write_text(json.dumps({"model_version": "model-1"}, indent=2), encoding="utf-8")
    pd.DataFrame([{"approval_gap_delta": 0.0}]).to_csv(run_ctx.tables_dir / "batch_fairness_change.csv", index=False)
    (run_ctx.tables_dir / "release_evidence_pack.json").write_text(json.dumps({}, indent=2), encoding="utf-8")
    manifest = {
        "run_id": run_ctx.run_id,
        "policy_version_evaluated": _arg_value(argv, "--policy_version_evaluated"),
        "institution_profile_key": _arg_value(argv, "--institution_profile_key"),
        "overlay_provenance": {
            "institution_policy": json.loads(_arg_value(argv, "--institution_policy_overlay_json", "{}") or "{}"),
            "institution_offer": json.loads(_arg_value(argv, "--institution_offer_overlay_json", "{}") or "{}"),
            "pilot_profile": json.loads(_arg_value(argv, "--pilot_profile_overlay_json", "{}") or "{}"),
        },
        "resolved_runtime_config": json.loads(_arg_value(argv, "--resolved_runtime_config_json", "{}") or "{}"),
        "explanation_artifacts": {
            "decision_explanation_packs_root": _arg_value(argv, "--explanation_pack_root"),
        },
        "refresh_provenance": {
            "refresh_run_id": _arg_value(argv, "--refresh_run_id"),
        },
    }
    (run_ctx.tables_dir / "pilot_package_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return run_ctx


def _fake_smoke_main(argv: list[str] | None = None):
    argv = list(argv or [])
    artifact_root = _arg_value(argv, "--artifact_root")
    run_ctx = create_run_context({"fake": "smoke"}, base_artifact_dir=artifact_root)
    (run_ctx.tables_dir / "release_smoke_summary.json").write_text(
        json.dumps({"run_id": run_ctx.run_id, "release_decision": "LIMITED_GO"}, indent=2),
        encoding="utf-8",
    )
    return run_ctx


def _write_reference_run(tmp_path: Path, artifact_root: Path, *, run_id: str, profile_key: str, canonical: bool = True) -> None:
    reference_collection_root = tmp_path / f"{run_id}_collection" / "tables" / "customer_artifact_collection"
    reference_collection_root.mkdir(parents=True, exist_ok=True)
    (reference_collection_root / "collection_manifest.json").write_text(
        json.dumps(
            {
                "policy_version_evaluated": "v2.0_baseline",
                "funnel_summary": {
                    "approved_share": 0.05,
                    "conditional_share": 0.55,
                    "rejected_share": 0.40,
                    "approve_plus_conditional_share": 0.60,
                    "internal_needs_review_share": 0.08,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    manifest_dir = artifact_root / run_id / "tables"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "pilot_refresh_manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "institution_profile_key": profile_key,
                "artifact_qa_status": "PASS" if canonical else "FAIL",
                "portfolio_smoke_status": "LIMITED_GO" if canonical else "NO_GO",
                "collection_manifest_path": str(reference_collection_root / "collection_manifest.json"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_run_pilot_baseline_refresh_writes_dual_lane_summary_and_canonical_reference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "pilot_source.csv"
    pd.DataFrame([_source_row(customer_id="cust-101"), _source_row(customer_id="cust-102")]).to_csv(source_path, index=False)
    bundle_path = _write_bundle(tmp_path, source_path)
    policy_overlay = tmp_path / "institution_policy.yaml"
    policy_overlay.write_text("cadence_mode: weekly_during_pilot\n", encoding="utf-8")
    offer_overlay = tmp_path / "institution_offer.yaml"
    offer_overlay.write_text("enabled_offer_families:\n  - installment_plan\n", encoding="utf-8")
    pilot_profile = tmp_path / "pilot_profile.yaml"
    pilot_profile.write_text("profile_key: test_bank_profile\nselection_policy_name: pilot_mixed\n", encoding="utf-8")
    artifact_root = tmp_path / "refresh_runs"
    _write_reference_run(tmp_path, artifact_root, run_id="reference_run", profile_key="test_bank_profile", canonical=True)

    monkeypatch.setattr(refresh.run_customer_artifact_collection, "main", _fake_collection_main_factory(tmp_path))
    monkeypatch.setattr(refresh.run_pilot_integration, "main", _fake_pilot_integration_main)
    monkeypatch.setattr(refresh.run_production_smoke, "main", _fake_smoke_main)

    run_ctx = refresh.main(
        [
            "--pilot_bundle",
            str(bundle_path),
            "--institution_policy",
            str(policy_overlay),
            "--institution_offer",
            str(offer_overlay),
            "--pilot_profile",
            str(pilot_profile),
            "--artifact_root",
            str(artifact_root),
            "--n_customers",
            "2",
        ]
    )

    manifest = json.loads((run_ctx.tables_dir / "pilot_refresh_manifest.json").read_text(encoding="utf-8"))
    summary_md = (run_ctx.tables_dir / "pilot_refresh_summary.md").read_text(encoding="utf-8")
    qa_summary = json.loads((run_ctx.tables_dir / "artifact_qa_summary.json").read_text(encoding="utf-8"))

    assert manifest["artifact_qa_status"] == "PASS"
    assert manifest["portfolio_smoke_status"] == "LIMITED_GO"
    assert manifest["comparison_is_canonical"] is True
    assert manifest["reference_run_id"] == "reference_run"
    assert manifest["preferred_demo_profile"] == "preferred_demo_baseline_v2_3"
    assert manifest["fallback_demo_profile"] == "trust_first_baseline_v2_3"
    assert manifest["overlay_provenance"]["institution_policy"]["cadence_mode"] == "weekly_during_pilot"
    assert manifest["resolved_runtime_config"]["resolved"]["cohort_policy"] == "pilot_mixed"
    assert manifest["comparison_summary"]["recommended_candidate_policy_version"] == "analysis_mild_relax_v2_3a"
    assert manifest["comparison_summary"]["recommended_candidate_status"] == "shortlisted"
    assert manifest["comparison_summary"]["recommended_outcome_rule_profile_version"] == "analysis_offer_readiness_combo_v2_3b"
    assert manifest["comparison_summary"]["recommended_outcome_rule_status"] == "shortlisted"
    assert manifest["comparison_summary"]["preferred_demo_profile"] == "preferred_demo_baseline_v2_3"
    assert manifest["comparison_summary"]["fallback_demo_profile"] == "trust_first_baseline_v2_3"
    assert manifest["comparison_summary"]["dominant_movement_bottleneck"] == "structural_cohort_limited"
    assert (run_ctx.tables_dir / "policy_version_comparison.csv").exists()
    assert (run_ctx.tables_dir / "policy_version_comparison.md").exists()
    assert (run_ctx.tables_dir / "demo_policy_proof.md").exists()
    assert (run_ctx.tables_dir / "next_milestone_handoff.md").exists()
    assert manifest["output_artifacts"]["demo_policy_proof_md"] == "tables/demo_policy_proof.md"
    assert "Recommended candidate status: shortlisted" in summary_md
    assert "Preferred demo profile: preferred_demo_baseline_v2_3" in summary_md
    assert "Fallback demo profile: trust_first_baseline_v2_3" in summary_md
    assert "Recommended candidate policy: analysis_mild_relax_v2_3a" in summary_md
    assert "Recommended outcome-rule status: shortlisted" in summary_md
    assert "Recommended outcome-rule profile: analysis_offer_readiness_combo_v2_3b" in summary_md
    assert "Dominant movement bottleneck: structural_cohort_limited" in summary_md
    assert "Portfolio smoke status: LIMITED_GO" in summary_md
    assert "Artifact QA status: PASS" in summary_md
    assert qa_summary["artifact_qa_status"] == "PASS"


def test_run_pilot_baseline_refresh_uses_explicit_reference_as_non_canonical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "pilot_source.csv"
    pd.DataFrame([_source_row(customer_id="cust-201")]).to_csv(source_path, index=False)
    bundle_path = _write_bundle(tmp_path, source_path)
    pilot_profile = tmp_path / "pilot_profile.yaml"
    pilot_profile.write_text("profile_key: explicit_profile\nselection_policy_name: pilot_mixed\n", encoding="utf-8")
    artifact_root = tmp_path / "refresh_runs"
    _write_reference_run(tmp_path, artifact_root, run_id="explicit_ref", profile_key="other_profile", canonical=False)

    monkeypatch.setattr(refresh.run_customer_artifact_collection, "main", _fake_collection_main_factory(tmp_path))
    monkeypatch.setattr(refresh.run_pilot_integration, "main", _fake_pilot_integration_main)
    monkeypatch.setattr(refresh.run_production_smoke, "main", _fake_smoke_main)

    run_ctx = refresh.main(
        [
            "--pilot_bundle",
            str(bundle_path),
            "--pilot_profile",
            str(pilot_profile),
            "--artifact_root",
            str(artifact_root),
            "--reference_run_id",
            "explicit_ref",
            "--reference_label",
            "manual_baseline",
        ]
    )

    manifest = json.loads((run_ctx.tables_dir / "pilot_refresh_manifest.json").read_text(encoding="utf-8"))

    assert manifest["reference_run_id"] == "explicit_ref"
    assert manifest["reference_label"] == "manual_baseline"
    assert manifest["comparison_is_canonical"] is False
