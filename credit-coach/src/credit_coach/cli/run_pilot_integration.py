from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from credit_coach.cli import run_batch_recourse_eval
from credit_coach.data.ingest import load_feature_contract
from credit_coach.evaluation.portfolio_validation import build_product_confidence_snapshot
from credit_coach.ops.kpi_contract import (
    build_kpi_contract_snapshot,
    build_milestone_acceptance_summary,
    build_release_evidence_pack,
    derive_acceptance_status,
    load_kpi_thresholds,
)
from credit_coach.ops.release_decision import (
    aggregate_release_metrics,
    build_pilot_guardrails,
    build_pilot_package_release_payload,
    build_rollback_conditions,
    evaluate_seed_kpi_contract,
)
from credit_coach.pilot import (
    PilotPackageManifest,
    build_pilot_input_manifest,
    load_pilot_bundle,
    normalize_pilot_dataframe,
)
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_pilot_integration")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run validated pilot integration against institution-style export data")
    parser.add_argument("--pilot_bundle", type=str, required=True)
    parser.add_argument("--base_config", type=str, default="configs/default.yaml")
    parser.add_argument("--model_config", type=str, default="configs/model.yaml")
    parser.add_argument("--recourse_config", type=str, default="configs/recourse.yaml")
    parser.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    parser.add_argument("--safety_config", type=str, default="configs/safety.yaml")
    parser.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    parser.add_argument("--kpi_contract", type=str, default="configs/kpi_contract.yaml")
    parser.add_argument("--group_feature", type=str, default="")
    parser.add_argument("--n_customers", type=int, default=0)
    parser.add_argument("--sample_seed", type=int, default=42)
    parser.add_argument("--artifact_root", type=str, default="artifacts/pilot_runs")
    parser.add_argument("--model_version", type=str, default="")
    parser.add_argument("--model_manifest", type=str, default="")
    return parser.parse_args(argv)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _resolve_repo_path(raw_path: str | Path) -> Path:
    project_root = Path(__file__).resolve().parents[3]
    path = Path(raw_path)
    if path.exists():
        return path
    candidate = project_root / path
    if candidate.exists():
        return candidate
    return path


def _read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _copy_artifact(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return str(destination.relative_to(destination.parent.parent))


def _build_pilot_calibration_summary(portfolio_validation_summary: dict[str, Any]) -> dict[str, Any]:
    canonical_metrics = (
        portfolio_validation_summary.get("canonical_metrics", {})
        if isinstance(portfolio_validation_summary.get("canonical_metrics", {}), dict)
        else {}
    )
    return {
        "realism_clean_plan_rate": float(canonical_metrics.get("realism_clean_plan_rate", 0.0)),
        "false_optimism_exposure": float(canonical_metrics.get("false_optimism_exposure", 0.0)),
        "unstable_target_range_exposure": float(canonical_metrics.get("unstable_target_range_exposure", 0.0)),
        "narrow_distribution_exposure": float(canonical_metrics.get("narrow_distribution_exposure", 0.0)),
    }


def main(argv: Sequence[str] | None = None):
    args = parse_args(argv)
    bundle = load_pilot_bundle(_resolve_repo_path(args.pilot_bundle))
    base_config_path = _resolve_repo_path(args.base_config)
    model_config_path = _resolve_repo_path(args.model_config)
    recourse_config_path = _resolve_repo_path(args.recourse_config)
    causality_config_path = _resolve_repo_path(args.causality_config)
    safety_config_path = _resolve_repo_path(args.safety_config)
    macro_config_path = _resolve_repo_path(args.macro_config)
    kpi_contract_path = _resolve_repo_path(args.kpi_contract)
    base_cfg = load_config(base_config_path)
    feature_contract = load_feature_contract(_resolve_repo_path(base_cfg.get("features_config", "configs/features_48.yaml")))
    required_features = list(feature_contract["features"])
    target_column_name = str(feature_contract["target"])

    normalized_df, resolved_mapping = normalize_pilot_dataframe(
        bundle,
        required_features=required_features,
        target_column_name=target_column_name,
    )
    n_customers = int(args.n_customers) if int(args.n_customers) > 0 else int(len(normalized_df))

    run_ctx = create_run_context(
        {
            "phase": "39-pilot-integration",
            "pilot_bundle": str(_resolve_repo_path(args.pilot_bundle).resolve()),
            "institution": bundle.institution.model_dump(mode="json"),
            "source": bundle.source.model_dump(mode="json"),
            "group_feature": str(args.group_feature).strip() or resolved_mapping.group_feature_name,
            "n_customers": n_customers,
            "sample_seed": int(args.sample_seed),
            "configs": {
                "base_config": str(base_config_path),
                "model_config": str(model_config_path),
                "recourse_config": str(recourse_config_path),
                "causality_config": str(causality_config_path),
                "safety_config": str(safety_config_path),
                "macro_config": str(macro_config_path),
                "kpi_contract": str(kpi_contract_path),
            },
        },
        base_artifact_dir=args.artifact_root,
    )
    normalized_input_path = run_ctx.tables_dir / "pilot_normalized_input.parquet"
    normalized_df.to_parquet(normalized_input_path, index=False)

    pilot_input_manifest = build_pilot_input_manifest(
        bundle=bundle,
        resolved_mapping=resolved_mapping,
        normalized_path=normalized_input_path,
        normalized_row_count=len(normalized_df),
    )
    (run_ctx.tables_dir / "pilot_input_manifest.json").write_text(
        json.dumps(pilot_input_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    group_feature = str(args.group_feature).strip() or resolved_mapping.group_feature_name
    batch_run_ctx = run_batch_recourse_eval.main(
        [
            "--base_config",
            str(base_config_path),
            "--model_config",
            str(model_config_path),
            "--recourse_config",
            str(recourse_config_path),
            "--causality_config",
            str(causality_config_path),
            "--safety_config",
            str(safety_config_path),
            "--macro_config",
            str(macro_config_path),
            "--n_customers",
            str(n_customers),
            "--sample_seed",
            str(int(args.sample_seed)),
            "--group_feature",
            group_feature,
            "--input_data_path",
            str(normalized_input_path),
            "--input_data_format",
            "parquet",
            "--model_version",
            str(args.model_version).strip(),
            "--model_manifest",
            str(args.model_manifest).strip(),
        ]
    )
    if batch_run_ctx is None:
        raise RuntimeError("run_batch_recourse_eval did not return a run context")

    batch_tables_dir = batch_run_ctx.tables_dir
    mirrored_required = {
        "batch_summary_json": "batch_summary.json",
        "batch_fairness_change_csv": "batch_fairness_change.csv",
        "batch_run_manifest_json": "batch_run_manifest.json",
        "batch_recourse_results_csv": "batch_recourse_results.csv",
        "portfolio_validation_summary_json": "portfolio_validation_summary.json",
        "portfolio_validation_review_md": "portfolio_validation_review.md",
        "portfolio_calibration_validation_breakdown_csv": "portfolio_calibration_validation_breakdown.csv",
        "decision_logging_summary_json": "decision_logging_summary.json",
    }
    mirrored_optional = {
        "portfolio_numeric_impact_breakdown_csv": "portfolio_numeric_impact_breakdown.csv",
        "portfolio_segment_breakdown_csv": "portfolio_segment_breakdown.csv",
        "portfolio_offer_diagnostics_csv": "portfolio_offer_diagnostics.csv",
        "demo_representativeness_summary_json": "demo_representativeness_summary.json",
    }
    required_artifacts: dict[str, str] = {}
    for artifact_key, file_name in mirrored_required.items():
        source = batch_tables_dir / file_name
        if not source.exists():
            raise FileNotFoundError(f"Missing required batch artifact for pilot package: {source}")
        destination = run_ctx.tables_dir / file_name
        _copy_artifact(source, destination)
        required_artifacts[artifact_key] = f"tables/{file_name}"

    optional_artifacts: dict[str, str] = {}
    for artifact_key, file_name in mirrored_optional.items():
        source = batch_tables_dir / file_name
        if not source.exists():
            continue
        destination = run_ctx.tables_dir / file_name
        _copy_artifact(source, destination)
        optional_artifacts[artifact_key] = f"tables/{file_name}"

    batch_summary = _load_json(run_ctx.tables_dir / "batch_summary.json")
    portfolio_validation_summary = _load_json(run_ctx.tables_dir / "portfolio_validation_summary.json")
    decision_logging_summary = _load_json(run_ctx.tables_dir / "decision_logging_summary.json")
    fairness_change_df = _read_csv_if_exists(run_ctx.tables_dir / "batch_fairness_change.csv")
    thresholds = load_kpi_thresholds(kpi_contract_path)
    fair_row = fairness_change_df.iloc[0].to_dict() if not fairness_change_df.empty else {}
    seed_snapshot = evaluate_seed_kpi_contract(batch_summary, fair_row, thresholds)
    aggregate_metrics = {
        "seed_count": 1,
        "model_version": str(batch_summary.get("model_version", "")),
        "model_freeze_mode": str(batch_summary.get("model_freeze_mode", "")),
        **aggregate_release_metrics([seed_snapshot], thresholds=thresholds),
    }
    release_payload = build_pilot_package_release_payload(aggregate_metrics, thresholds)
    if release_payload.get("pilot_eligible", False):
        pilot_guardrails = build_pilot_guardrails(aggregate_metrics)
    else:
        pilot_guardrails = {
            "pilot_eligible": False,
            "broad_rollout_allowed": False,
            "max_traffic_pct": 0,
            "fairness_monitoring_required": False,
            "rollback_guard_required": False,
            "targeted_alerting_required": False,
            "manual_approval_required": False,
            "remediation_artifacts_required": True,
            "dominant_fail_segment_key": str(aggregate_metrics.get("dominant_fail_segment_key", "")),
            "dominant_fail_candidate_source": str(aggregate_metrics.get("dominant_fail_candidate_source", "")),
        }
    (run_ctx.tables_dir / "pilot_guardrails.json").write_text(
        json.dumps(pilot_guardrails, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    rollback_conditions = build_rollback_conditions(aggregate_metrics, thresholds)
    (run_ctx.tables_dir / "rollback_conditions.json").write_text(
        json.dumps(rollback_conditions, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    product_confidence_snapshot = build_product_confidence_snapshot(
        portfolio_validation_summary,
        decision_logging_summary=decision_logging_summary,
    )
    (run_ctx.tables_dir / "product_confidence_snapshot.json").write_text(
        json.dumps(product_confidence_snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    pilot_calibration_summary = _build_pilot_calibration_summary(portfolio_validation_summary)
    (run_ctx.tables_dir / "pilot_calibration_summary.json").write_text(
        json.dumps(pilot_calibration_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    acceptance_eligible = False
    evidence_level = "single_pilot_run"
    evidence_status = "degraded"
    degraded_reason = "single_pilot_package_evidence_only"
    acceptance_status = derive_acceptance_status(
        str(release_payload["decision"]),
        acceptance_eligible=acceptance_eligible,
        broad_rollout_allowed=bool(release_payload.get("broad_rollout_allowed", False)),
    )
    supporting_artifacts = {
        **required_artifacts,
        **optional_artifacts,
        "pilot_input_manifest_json": "tables/pilot_input_manifest.json",
        "pilot_guardrails_json": "tables/pilot_guardrails.json",
        "rollback_conditions_json": "tables/rollback_conditions.json",
        "product_confidence_snapshot_json": "tables/product_confidence_snapshot.json",
        "pilot_calibration_summary_json": "tables/pilot_calibration_summary.json",
    }
    kpi_contract_snapshot = build_kpi_contract_snapshot(
        runner_type="pilot",
        release_payload=release_payload,
        aggregate_metrics=aggregate_metrics,
        evidence_level=evidence_level,
        acceptance_eligible=acceptance_eligible,
        supporting_artifacts=supporting_artifacts,
        model_version=str(aggregate_metrics.get("model_version", "")),
        model_freeze_mode=str(aggregate_metrics.get("model_freeze_mode", "")),
        evidence_status=evidence_status,
        degraded_reason=degraded_reason,
        metadata={
            "pilot_guardrails": pilot_guardrails,
            "product_confidence_snapshot": product_confidence_snapshot,
            "pilot_calibration_summary": pilot_calibration_summary,
            "batch_run_id": str(batch_run_ctx.run_id),
        },
    )
    (run_ctx.tables_dir / "kpi_contract_snapshot.json").write_text(
        json.dumps(kpi_contract_snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    milestone_acceptance_summary = build_milestone_acceptance_summary(
        phase="39",
        milestone="v2.0",
        runner_type="pilot",
        release_payload=release_payload,
        aggregate_metrics=aggregate_metrics,
        evidence_level=evidence_level,
        acceptance_eligible=acceptance_eligible,
        supporting_artifacts=supporting_artifacts,
        model_version=str(aggregate_metrics.get("model_version", "")),
        model_freeze_mode=str(aggregate_metrics.get("model_freeze_mode", "")),
        evidence_status=evidence_status,
        degraded_reason=degraded_reason,
        metadata={
            "product_confidence_snapshot": product_confidence_snapshot,
            "pilot_guardrails": pilot_guardrails,
            "pilot_calibration_summary": pilot_calibration_summary,
            "batch_run_id": str(batch_run_ctx.run_id),
        },
    )
    milestone_acceptance_summary["acceptance_status"] = acceptance_status
    (run_ctx.tables_dir / "milestone_acceptance_summary.json").write_text(
        json.dumps(milestone_acceptance_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    release_evidence_pack = build_release_evidence_pack(
        runner_type="pilot",
        phase="39",
        milestone="v2.0",
        release_decision=str(release_payload["decision"]),
        acceptance_status=acceptance_status,
        evidence_level=evidence_level,
        evidence_status=evidence_status,
        acceptance_eligible=acceptance_eligible,
        required_artifacts={
            "pilot_input_manifest_json": "tables/pilot_input_manifest.json",
            "batch_summary_json": "tables/batch_summary.json",
            "portfolio_validation_summary_json": "tables/portfolio_validation_summary.json",
            "portfolio_validation_review_md": "tables/portfolio_validation_review.md",
            "product_confidence_snapshot_json": "tables/product_confidence_snapshot.json",
            "pilot_guardrails_json": "tables/pilot_guardrails.json",
            "kpi_contract_snapshot_json": "tables/kpi_contract_snapshot.json",
            "milestone_acceptance_summary_json": "tables/milestone_acceptance_summary.json",
        },
        optional_artifacts={
            **optional_artifacts,
            "portfolio_calibration_validation_breakdown_csv": "tables/portfolio_calibration_validation_breakdown.csv",
            "rollback_conditions_json": "tables/rollback_conditions.json",
            "pilot_calibration_summary_json": "tables/pilot_calibration_summary.json",
        },
        existing_artifacts=[
            f"tables/{path.name}"
            for path in run_ctx.tables_dir.iterdir()
            if path.is_file()
        ],
        metadata={
            "batch_run_id": str(batch_run_ctx.run_id),
            "institution_name": bundle.institution.institution_name,
            "group_feature_name": group_feature,
        },
    )
    (run_ctx.tables_dir / "release_evidence_pack.json").write_text(
        json.dumps(release_evidence_pack, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    manifest = PilotPackageManifest(
        run_id=str(run_ctx.run_id),
        institution=bundle.institution,
        source_data_path=str(bundle.source.data_path),
        normalized_input_path=str(normalized_input_path),
        normalized_row_count=int(len(normalized_df)),
        group_feature_name=group_feature,
        batch_run_id=str(batch_run_ctx.run_id),
        batch_artifact_dir=str(batch_run_ctx.artifact_dir),
        release_decision=str(release_payload["decision"]),
        acceptance_status=acceptance_status,
        pilot_eligible=bool(release_payload.get("pilot_eligible", False)),
        broad_rollout_allowed=bool(release_payload.get("broad_rollout_allowed", False)),
        required_artifacts={
            **required_artifacts,
            "pilot_input_manifest_json": "tables/pilot_input_manifest.json",
            "pilot_guardrails_json": "tables/pilot_guardrails.json",
            "product_confidence_snapshot_json": "tables/product_confidence_snapshot.json",
            "kpi_contract_snapshot_json": "tables/kpi_contract_snapshot.json",
            "milestone_acceptance_summary_json": "tables/milestone_acceptance_summary.json",
            "release_evidence_pack_json": "tables/release_evidence_pack.json",
        },
        optional_artifacts={
            **optional_artifacts,
            "rollback_conditions_json": "tables/rollback_conditions.json",
            "pilot_calibration_summary_json": "tables/pilot_calibration_summary.json",
        },
        mapping_provenance=pilot_input_manifest["mapping_provenance"],
    )
    (run_ctx.tables_dir / "pilot_package_manifest.json").write_text(
        manifest.model_dump_json(indent=2),
        encoding="utf-8",
    )
    logger.info("Pilot integration package completed: %s", run_ctx.tables_dir)
    return run_ctx


if __name__ == "__main__":
    main()
