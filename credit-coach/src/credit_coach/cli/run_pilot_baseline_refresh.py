from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any, Mapping, Sequence, Type

import pandas as pd
import yaml

from credit_coach.cli import (
    run_customer_artifact_collection,
    run_pilot_artifact_qa,
    run_pilot_integration,
    run_production_smoke,
)
from credit_coach.data.ingest import load_feature_contract
from credit_coach.ops.decision_explanation_pack import (
    DecisionExplanationPack,
    build_decision_explanation_pack,
    render_decision_explanation_pack_markdown,
    write_decision_explanation_pack,
)
from credit_coach.pilot import (
    InstitutionOfferOverlay,
    InstitutionPolicyOverlay,
    PilotInputBundle,
    PilotProfileOverlay,
    PilotRefreshManifest,
    load_pilot_bundle,
    normalize_pilot_dataframe,
)
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_pilot_baseline_refresh")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Phase 44 production pilot baseline refresh")
    parser.add_argument("--pilot_bundle", type=str, required=True)
    parser.add_argument("--base_config", type=str, default="configs/default.yaml")
    parser.add_argument("--model_config", type=str, default="configs/model.yaml")
    parser.add_argument("--recourse_config", type=str, default="configs/recourse.yaml")
    parser.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    parser.add_argument("--safety_config", type=str, default="configs/safety.yaml")
    parser.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    parser.add_argument("--kpi_contract", type=str, default="configs/kpi_contract.yaml")
    parser.add_argument("--institution_policy", type=str, default="")
    parser.add_argument("--institution_offer", type=str, default="")
    parser.add_argument("--pilot_profile", type=str, default="")
    parser.add_argument("--cadence_mode", type=str, default="")
    parser.add_argument("--cohort_policy", type=str, default="")
    parser.add_argument("--n_customers", type=int, default=0)
    parser.add_argument("--sample_seed", type=int, default=42)
    parser.add_argument("--n_workers", type=int, default=1)
    parser.add_argument("--artifact_root", type=str, default="artifacts/pilot_refresh_runs")
    parser.add_argument("--reference_run_id", type=str, default="")
    parser.add_argument("--reference_label", type=str, default="")
    parser.add_argument("--model_version", type=str, default="")
    parser.add_argument("--model_manifest", type=str, default="")
    return parser.parse_args(argv)


def _safe_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _resolve_repo_path(raw_path: str | Path) -> Path:
    project_root = Path(__file__).resolve().parents[3]
    path = Path(raw_path)
    if path.exists():
        return path
    candidate = project_root / path
    if candidate.exists():
        return candidate
    return path


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _load_yaml_overlay(path: Path | None, model_cls: Type[Any]) -> tuple[Any | None, dict[str, Any]]:
    if path is None:
        return None, {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Overlay payload must be a mapping: {path}")
    return model_cls.model_validate(payload), payload


def _profile_key(bundle: PilotInputBundle, pilot_profile: PilotProfileOverlay | None) -> str:
    raw = _safe_text(
        getattr(pilot_profile, "profile_key", ""),
        _safe_text(
            getattr(pilot_profile, "profile_name", ""),
            _safe_text(bundle.institution.institution_name, "institution"),
        ),
    )
    return re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_") or "institution"


def _resolved_runtime_config(
    *,
    args: argparse.Namespace,
    bundle: PilotInputBundle,
    institution_policy: InstitutionPolicyOverlay | None,
    institution_offer: InstitutionOfferOverlay | None,
    pilot_profile: PilotProfileOverlay | None,
    cadence_mode: str,
    cohort_policy: str,
    institution_profile_key: str,
) -> dict[str, Any]:
    return {
        "base_configs": {
            "base_config": str(_resolve_repo_path(args.base_config)),
            "model_config": str(_resolve_repo_path(args.model_config)),
            "recourse_config": str(_resolve_repo_path(args.recourse_config)),
            "causality_config": str(_resolve_repo_path(args.causality_config)),
            "safety_config": str(_resolve_repo_path(args.safety_config)),
            "macro_config": str(_resolve_repo_path(args.macro_config)),
            "kpi_contract": str(_resolve_repo_path(args.kpi_contract)),
        },
        "institution_policy": institution_policy.model_dump(mode="json") if institution_policy is not None else {},
        "institution_offer": institution_offer.model_dump(mode="json") if institution_offer is not None else {},
        "pilot_profile": pilot_profile.model_dump(mode="json") if pilot_profile is not None else {},
        "bundle_context": {
            "institution_name": bundle.institution.institution_name,
            "institution_type": bundle.institution.institution_type,
            "source_data_path": bundle.source.data_path,
        },
        "resolved": {
            "cadence_mode": cadence_mode,
            "cohort_policy": cohort_policy,
            "institution_profile_key": institution_profile_key,
            "n_customers": int(args.n_customers),
            "sample_seed": int(args.sample_seed),
            "n_workers": int(args.n_workers),
            "model_version": _safe_text(args.model_version),
            "model_manifest": _safe_text(args.model_manifest),
        },
        "precedence": [
            "base_configs",
            "institution_overlays",
            "pilot_bundle_context",
            "cli_overrides",
        ],
    }


def _overlay_provenance(
    *,
    institution_policy_path: Path | None,
    institution_offer_path: Path | None,
    pilot_profile_path: Path | None,
) -> dict[str, Any]:
    return {
        "institution_policy_path": str(institution_policy_path) if institution_policy_path is not None else "",
        "institution_offer_path": str(institution_offer_path) if institution_offer_path is not None else "",
        "pilot_profile_path": str(pilot_profile_path) if pilot_profile_path is not None else "",
    }


def _build_explanation_packs(
    *,
    collection_manifest_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    collection_manifest = _load_json(collection_manifest_path)
    artifact_root = collection_manifest_path.parents[2]
    raw_root = artifact_root / _safe_text(collection_manifest.get("raw_root"))
    operator_root = artifact_root / _safe_text(
        (
            collection_manifest.get("operator_files", {})
            if isinstance(collection_manifest.get("operator_files", {}), Mapping)
            else {}
        ).get("operator_packets_root")
    )

    pack_records: list[dict[str, Any]] = []
    for raw_dir in sorted(path for path in raw_root.iterdir() if path.is_dir()):
        roadmap_path = raw_dir / "customer_roadmap.json"
        metrics_path = raw_dir / "metrics.json"
        operator_packet_path = operator_root / raw_dir.name / "operator_packet.json"
        if not roadmap_path.exists():
            continue
        roadmap = _load_json(roadmap_path)
        metrics_summary = _load_json(metrics_path) if metrics_path.exists() else {}
        operator_packet = _load_json(operator_packet_path) if operator_packet_path.exists() else {}
        pack = build_decision_explanation_pack(
            roadmap,
            metrics_summary=metrics_summary,
            operator_packet=operator_packet or None,
            qa_status="PASS",
            qa_stamp="phase44_pre_qa",
        )
        pack_dir = output_root / raw_dir.name
        written = write_decision_explanation_pack(pack, pack_dir)
        pack_records.append(
            {
                "customer_id": _safe_text(pack.customer_id),
                "decision_id": _safe_text(pack.decision_id),
                "directory": raw_dir.name,
                "json_path": str(written["decision_explanation_pack_json"]),
            }
        )
    manifest = {
        "decision_explanation_packs_root": str(output_root),
        "decision_explanation_pack_count": len(pack_records),
        "packs": pack_records,
    }
    (output_root / "decision_explanation_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest


def _load_refresh_manifest(path: Path) -> dict[str, Any] | None:
    try:
        return _load_json(path)
    except Exception:
        return None


def _is_canonical_reference(manifest: Mapping[str, Any], institution_profile_key: str) -> bool:
    if _safe_text(manifest.get("institution_profile_key")) != institution_profile_key:
        return False
    if _safe_text(manifest.get("artifact_qa_status")) != "PASS":
        return False
    return _safe_text(manifest.get("portfolio_smoke_status")) not in {"", "NO_GO"}


def _find_reference_manifest(
    *,
    artifact_root: Path,
    institution_profile_key: str,
    current_run_id: str,
    explicit_reference_run_id: str,
) -> tuple[dict[str, Any] | None, bool]:
    manifests = sorted(artifact_root.glob("*/tables/pilot_refresh_manifest.json"))
    explicit_reference_run_id = _safe_text(explicit_reference_run_id)
    if explicit_reference_run_id:
        explicit_path = artifact_root / explicit_reference_run_id / "tables" / "pilot_refresh_manifest.json"
        if explicit_path.exists():
            return _load_json(explicit_path), False
        return None, False
    for path in reversed(manifests):
        manifest = _load_refresh_manifest(path)
        if not manifest:
            continue
        if _safe_text(manifest.get("run_id")) == current_run_id:
            continue
        if _is_canonical_reference(manifest, institution_profile_key):
            return manifest, True
    return None, False


def _metric_rows_from_funnel(funnel_summary: Mapping[str, Any]) -> list[tuple[str, float]]:
    rows: list[tuple[str, float]] = []
    for metric in (
        "approved_share",
        "conditional_share",
        "rejected_share",
        "approve_plus_conditional_share",
        "internal_needs_review_share",
    ):
        rows.append((metric, float(funnel_summary.get(metric, 0.0))))
    return rows


def _write_policy_comparison(
    *,
    current_collection_manifest: Mapping[str, Any],
    reference_refresh_manifest: Mapping[str, Any] | None,
    output_csv: Path,
    output_md: Path,
    reference_label: str,
) -> dict[str, Any]:
    current_funnel = (
        dict(current_collection_manifest.get("funnel_summary", {}))
        if isinstance(current_collection_manifest.get("funnel_summary", {}), Mapping)
        else {}
    )
    reference_collection_manifest: dict[str, Any] = {}
    if reference_refresh_manifest is not None:
        reference_path = Path(_safe_text(reference_refresh_manifest.get("collection_manifest_path")))
        if reference_path.exists():
            reference_collection_manifest = _load_json(reference_path)
    reference_funnel = (
        dict(reference_collection_manifest.get("funnel_summary", {}))
        if isinstance(reference_collection_manifest.get("funnel_summary", {}), Mapping)
        else {}
    )
    rows: list[dict[str, Any]] = []
    for metric, current_value in _metric_rows_from_funnel(current_funnel):
        reference_value = float(reference_funnel.get(metric, 0.0))
        rows.append(
            {
                "metric": metric,
                "current_value": float(current_value),
                "reference_value": float(reference_value),
                "delta_vs_reference": float(current_value - reference_value),
                "reference_label": reference_label,
            }
        )
    comparison_df = pd.DataFrame(rows)
    comparison_df.to_csv(output_csv, index=False)
    recommended_candidate_policy_version = _safe_text(current_collection_manifest.get("recommended_candidate_policy_version"))
    recommended_candidate_status = _safe_text(
        current_collection_manifest.get("recommended_candidate_status"),
        "no_safe_uplift",
    )
    recommended_candidate_reason = _safe_text(current_collection_manifest.get("recommended_candidate_reason"))
    candidate_policy_versions = list(current_collection_manifest.get("candidate_policy_versions_compared", []) or [])
    recommended_outcome_rule_profile_version = _safe_text(
        current_collection_manifest.get("recommended_outcome_rule_profile_version")
    )
    recommended_outcome_rule_status = _safe_text(
        current_collection_manifest.get("recommended_outcome_rule_status"),
        "no_safe_uplift",
    )
    recommended_outcome_rule_reason = _safe_text(current_collection_manifest.get("recommended_outcome_rule_reason"))
    candidate_outcome_rule_versions = list(current_collection_manifest.get("candidate_outcome_rule_versions_compared", []) or [])
    preferred_demo_profile = _safe_text(current_collection_manifest.get("preferred_demo_profile"))
    fallback_demo_profile = _safe_text(current_collection_manifest.get("fallback_demo_profile"))
    policy_baseline_selection_reason = _safe_text(current_collection_manifest.get("policy_baseline_selection_reason"))
    threshold_family_promotion_status = _safe_text(current_collection_manifest.get("threshold_family_promotion_status"))
    outcome_rule_family_promotion_status = _safe_text(current_collection_manifest.get("outcome_rule_family_promotion_status"))
    next_milestone_focus = _safe_text(current_collection_manifest.get("next_milestone_focus"))
    dominant_movement_bottleneck = _safe_text(current_collection_manifest.get("dominant_movement_bottleneck"))
    movement_guardrail_summary = _safe_text(current_collection_manifest.get("movement_guardrail_summary"))
    promotion_blocker_summary = _safe_text(current_collection_manifest.get("promotion_blocker_summary"))
    lines = [
        "# Policy Version Comparison",
        "",
        f"- Current policy version: {_safe_text(current_collection_manifest.get('policy_version_evaluated')) or 'n/a'}",
        f"- Reference label: {reference_label or 'none'}",
        f"- Candidate policies compared: {', '.join(str(item) for item in candidate_policy_versions) or 'n/a'}",
        f"- Recommended candidate status: {recommended_candidate_status or 'no_safe_uplift'}",
        f"- Recommended candidate policy: {recommended_candidate_policy_version or 'n/a'}",
        f"- Recommended candidate reason: {recommended_candidate_reason or 'n/a'}",
        f"- Candidate outcome rules compared: {', '.join(str(item) for item in candidate_outcome_rule_versions) or 'n/a'}",
        f"- Recommended outcome-rule status: {recommended_outcome_rule_status or 'no_safe_uplift'}",
        f"- Recommended outcome-rule profile: {recommended_outcome_rule_profile_version or 'n/a'}",
        f"- Recommended outcome-rule reason: {recommended_outcome_rule_reason or 'n/a'}",
        f"- Preferred demo profile: {preferred_demo_profile or 'n/a'}",
        f"- Fallback demo profile: {fallback_demo_profile or 'n/a'}",
        f"- Baseline selection reason: {policy_baseline_selection_reason or 'n/a'}",
        f"- Threshold family promotion status: {threshold_family_promotion_status or 'n/a'}",
        f"- Outcome-rule family promotion status: {outcome_rule_family_promotion_status or 'n/a'}",
        f"- Next milestone focus: {next_milestone_focus or 'n/a'}",
        f"- Dominant movement bottleneck: {dominant_movement_bottleneck or 'n/a'}",
        f"- Movement guardrail summary: {movement_guardrail_summary or 'n/a'}",
        f"- Promotion blocker summary: {promotion_blocker_summary or 'n/a'}",
        "",
        "## Funnel Deltas",
    ]
    if not comparison_df.empty:
        for row in comparison_df.to_dict(orient="records"):
            lines.append(
                f"- {row['metric']}: current={row['current_value']:.4f}, reference={row['reference_value']:.4f}, delta={row['delta_vs_reference']:.4f}"
            )
    else:
        lines.append("- n/a")
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "rows": len(comparison_df),
        "reference_label": reference_label,
        "reference_policy_version": _safe_text(reference_collection_manifest.get("policy_version_evaluated")),
        "candidate_policy_versions_compared": [str(item) for item in candidate_policy_versions],
        "recommended_candidate_policy_version": recommended_candidate_policy_version,
        "recommended_candidate_status": recommended_candidate_status or "no_safe_uplift",
        "recommended_candidate_reason": recommended_candidate_reason,
        "candidate_outcome_rule_versions_compared": [str(item) for item in candidate_outcome_rule_versions],
        "recommended_outcome_rule_profile_version": recommended_outcome_rule_profile_version,
        "recommended_outcome_rule_status": recommended_outcome_rule_status or "no_safe_uplift",
        "recommended_outcome_rule_reason": recommended_outcome_rule_reason,
        "preferred_demo_profile": preferred_demo_profile,
        "fallback_demo_profile": fallback_demo_profile,
        "policy_baseline_selection_reason": policy_baseline_selection_reason,
        "threshold_family_promotion_status": threshold_family_promotion_status,
        "outcome_rule_family_promotion_status": outcome_rule_family_promotion_status,
        "next_milestone_focus": next_milestone_focus,
        "dominant_movement_bottleneck": dominant_movement_bottleneck,
        "movement_guardrail_summary": movement_guardrail_summary,
        "promotion_blocker_summary": promotion_blocker_summary,
    }


def _render_demo_policy_proof(
    *,
    collection_manifest: Mapping[str, Any],
    artifact_qa_status: str,
    portfolio_smoke_status: str,
) -> str:
    recommended_candidate_status = _safe_text(collection_manifest.get("recommended_candidate_status"), "no_safe_uplift")
    recommended_outcome_rule_status = _safe_text(
        collection_manifest.get("recommended_outcome_rule_status"),
        "no_safe_uplift",
    )
    lines = [
        "# Demo Policy Proof",
        "",
        "## Preferred Profile",
        f"- Preferred demo profile: {_safe_text(collection_manifest.get('preferred_demo_profile')) or 'n/a'}",
        f"- Preferred runtime policy: {_safe_text(collection_manifest.get('policy_version_evaluated')) or 'n/a'}",
        f"- Selection reason: {_safe_text(collection_manifest.get('policy_baseline_selection_reason')) or 'n/a'}",
        "",
        "## Fallback Profile",
        f"- Fallback demo profile: {_safe_text(collection_manifest.get('fallback_demo_profile')) or 'n/a'}",
        f"- Fallback posture: same shipped runtime baseline, narrower trust-first communication mode",
        "",
        "## Candidate Non-Adoption",
        f"- Threshold family status: {_safe_text(collection_manifest.get('threshold_family_promotion_status')) or recommended_candidate_status or 'n/a'}",
        f"- Threshold recommendation status: {recommended_candidate_status or 'no_safe_uplift'}",
        f"- Threshold recommendation reason: {_safe_text(collection_manifest.get('recommended_candidate_reason')) or 'n/a'}",
        f"- Outcome-rule family status: {_safe_text(collection_manifest.get('outcome_rule_family_promotion_status')) or recommended_outcome_rule_status or 'n/a'}",
        f"- Outcome-rule recommendation status: {recommended_outcome_rule_status or 'no_safe_uplift'}",
        f"- Outcome-rule recommendation reason: {_safe_text(collection_manifest.get('recommended_outcome_rule_reason')) or 'n/a'}",
        f"- Dominant movement bottleneck: {_safe_text(collection_manifest.get('dominant_movement_bottleneck')) or 'n/a'}",
        f"- Movement guardrail summary: {_safe_text(collection_manifest.get('movement_guardrail_summary')) or 'n/a'}",
        f"- Promotion blocker summary: {_safe_text(collection_manifest.get('promotion_blocker_summary')) or 'n/a'}",
        "",
        "## Allowed Claims",
        "- The shipped trust baseline remains clean.",
        "- Bounded threshold and outcome-rule candidates were evaluated explicitly.",
        "- No bounded candidate was adopted into the runtime demo baseline in Phase 52.",
        "",
        "## Disallowed Claims",
        "- Do not claim that a new uplift policy has been promoted.",
        "- Do not claim that bounded threshold or outcome-rule changes safely improved production decisions.",
        "- Do not claim that the current cohort bottleneck is solved.",
        "",
        "## Current Package Health",
        f"- Artifact QA status: {artifact_qa_status or 'n/a'}",
        f"- Portfolio smoke status: {portfolio_smoke_status or 'n/a'}",
    ]
    return "\n".join(lines) + "\n"


def _render_next_milestone_handoff(collection_manifest: Mapping[str, Any]) -> str:
    lines = [
        "# Next Milestone Handoff",
        "",
        f"- Current preferred runtime baseline: {_safe_text(collection_manifest.get('policy_version_evaluated')) or 'n/a'}",
        f"- Dominant bottleneck: {_safe_text(collection_manifest.get('dominant_movement_bottleneck')) or 'n/a'}",
        f"- Current next-milestone focus: {_safe_text(collection_manifest.get('next_milestone_focus')) or 'n/a'}",
        "",
        "## Why Phase 52 Stops Here",
        f"- Threshold family promotion status: {_safe_text(collection_manifest.get('threshold_family_promotion_status')) or 'n/a'}",
        f"- Outcome-rule family promotion status: {_safe_text(collection_manifest.get('outcome_rule_family_promotion_status')) or 'n/a'}",
        f"- Baseline selection reason: {_safe_text(collection_manifest.get('policy_baseline_selection_reason')) or 'n/a'}",
        "",
        "## Guidance",
        "- Do not reopen the same bounded threshold ladder as a default next step.",
        "- Do not reopen the same bounded offer/readiness ladder as a default next step.",
        "- Use the next milestone to investigate broader movement leverage while preserving the shipped trust baseline.",
    ]
    return "\n".join(lines) + "\n"


def _apply_qa_to_explanation_packs(
    *,
    explanation_root: Path,
    qa_status: str,
    qa_stamp: str,
) -> None:
    for pack_path in sorted(explanation_root.rglob("decision_explanation_pack.json")):
        payload = _load_json(pack_path)
        payload["qa_status"] = _safe_text(qa_status, "PASS")
        payload["qa_stamp"] = _safe_text(qa_stamp)
        pack = DecisionExplanationPack.model_validate(payload)
        pack_path.write_text(pack.model_dump_json(indent=2), encoding="utf-8")
        md_path = pack_path.with_suffix(".md")
        if md_path.exists():
            md_path.write_text(render_decision_explanation_pack_markdown(pack), encoding="utf-8")


def _render_refresh_summary(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Pilot Baseline Refresh",
        "",
        f"- Cadence mode: {_safe_text(summary.get('cadence_mode'))}",
        f"- Institution profile key: {_safe_text(summary.get('institution_profile_key'))}",
        f"- Policy version: {_safe_text(summary.get('policy_version_evaluated')) or 'n/a'}",
        f"- Preferred demo profile: {_safe_text(summary.get('preferred_demo_profile')) or 'n/a'}",
        f"- Fallback demo profile: {_safe_text(summary.get('fallback_demo_profile')) or 'n/a'}",
        f"- Baseline selection reason: {_safe_text(summary.get('policy_baseline_selection_reason')) or 'n/a'}",
        f"- Recommended candidate status: {_safe_text(summary.get('recommended_candidate_status')) or 'no_safe_uplift'}",
        f"- Recommended candidate policy: {_safe_text(summary.get('recommended_candidate_policy_version')) or 'n/a'}",
        f"- Recommended outcome-rule status: {_safe_text(summary.get('recommended_outcome_rule_status')) or 'no_safe_uplift'}",
        f"- Recommended outcome-rule profile: {_safe_text(summary.get('recommended_outcome_rule_profile_version')) or 'n/a'}",
        f"- Threshold family promotion status: {_safe_text(summary.get('threshold_family_promotion_status')) or 'n/a'}",
        f"- Outcome-rule family promotion status: {_safe_text(summary.get('outcome_rule_family_promotion_status')) or 'n/a'}",
        f"- Next milestone focus: {_safe_text(summary.get('next_milestone_focus')) or 'n/a'}",
        f"- Dominant movement bottleneck: {_safe_text(summary.get('dominant_movement_bottleneck')) or 'n/a'}",
        f"- Movement guardrail summary: {_safe_text(summary.get('movement_guardrail_summary')) or 'n/a'}",
        f"- Promotion blocker summary: {_safe_text(summary.get('promotion_blocker_summary')) or 'n/a'}",
        f"- Portfolio smoke status: {_safe_text(summary.get('portfolio_smoke_status')) or 'n/a'}",
        f"- Artifact QA status: {_safe_text(summary.get('artifact_qa_status')) or 'n/a'}",
        f"- Comparison canonical: {'yes' if bool(summary.get('comparison_is_canonical')) else 'no'}",
        "",
        "## Referenced Runs",
        f"- Collection run: {_safe_text(summary.get('collection_run_id')) or 'n/a'}",
        f"- Pilot package run: {_safe_text(summary.get('pilot_package_run_id')) or 'n/a'}",
        f"- Smoke run: {_safe_text(summary.get('smoke_run_id')) or 'n/a'}",
        f"- Reference run: {_safe_text(summary.get('reference_run_id')) or 'n/a'}",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None):
    args = parse_args(argv)
    pilot_bundle_path = _resolve_repo_path(args.pilot_bundle)
    base_config_path = _resolve_repo_path(args.base_config)
    model_config_path = _resolve_repo_path(args.model_config)
    recourse_config_path = _resolve_repo_path(args.recourse_config)
    causality_config_path = _resolve_repo_path(args.causality_config)
    safety_config_path = _resolve_repo_path(args.safety_config)
    macro_config_path = _resolve_repo_path(args.macro_config)
    kpi_contract_path = _resolve_repo_path(args.kpi_contract)
    institution_policy_path = _resolve_repo_path(args.institution_policy) if _safe_text(args.institution_policy) else None
    institution_offer_path = _resolve_repo_path(args.institution_offer) if _safe_text(args.institution_offer) else None
    pilot_profile_path = _resolve_repo_path(args.pilot_profile) if _safe_text(args.pilot_profile) else None

    bundle = load_pilot_bundle(pilot_bundle_path)
    base_cfg = load_config(base_config_path)
    feature_contract = load_feature_contract(_resolve_repo_path(base_cfg.get("features_config", "configs/features_48.yaml")))
    required_features = list(feature_contract["features"])
    target_column_name = str(feature_contract["target"])

    institution_policy, institution_policy_raw = _load_yaml_overlay(institution_policy_path, InstitutionPolicyOverlay)
    institution_offer, institution_offer_raw = _load_yaml_overlay(institution_offer_path, InstitutionOfferOverlay)
    pilot_profile, pilot_profile_raw = _load_yaml_overlay(pilot_profile_path, PilotProfileOverlay)

    cadence_mode = _safe_text(
        args.cadence_mode,
        _safe_text(getattr(institution_policy, "cadence_mode", ""), "pre_pilot"),
    )
    cohort_policy = _safe_text(
        args.cohort_policy,
        _safe_text(getattr(pilot_profile, "selection_policy_name", ""), "pilot_mixed"),
    )
    institution_profile_key = _profile_key(bundle, pilot_profile)
    resolved_runtime_config = _resolved_runtime_config(
        args=args,
        bundle=bundle,
        institution_policy=institution_policy,
        institution_offer=institution_offer,
        pilot_profile=pilot_profile,
        cadence_mode=cadence_mode,
        cohort_policy=cohort_policy,
        institution_profile_key=institution_profile_key,
    )

    run_ctx = create_run_context(
        {
            "phase": "44-production-pilot-baseline",
            "pilot_bundle": str(pilot_bundle_path),
            "cadence_mode": cadence_mode,
            "cohort_policy": cohort_policy,
            "institution_profile_key": institution_profile_key,
            "resolved_runtime_config": resolved_runtime_config,
        },
        base_artifact_dir=args.artifact_root,
    )

    normalized_df, _ = normalize_pilot_dataframe(
        bundle,
        required_features=required_features,
        target_column_name=target_column_name,
    )
    normalized_input_path = run_ctx.tables_dir / "refresh_normalized_input.parquet"
    normalized_df.to_parquet(normalized_input_path, index=False)

    child_root = run_ctx.artifact_dir / "subruns"
    collection_ctx = run_customer_artifact_collection.main(
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
            "--input_data_path",
            str(normalized_input_path),
            "--input_data_format",
            "parquet",
            "--n_customers",
            str(int(args.n_customers) if int(args.n_customers) > 0 else int(len(normalized_df))),
            "--sample_seed",
            str(int(args.sample_seed)),
            "--n_workers",
            str(int(args.n_workers)),
            "--cohort_policy",
            cohort_policy,
            "--artifact_root",
            str(child_root / "collection"),
        ]
    )
    collection_manifest_path = collection_ctx.tables_dir / "customer_artifact_collection" / "collection_manifest.json"
    collection_manifest = _load_json(collection_manifest_path)

    explanation_root = run_ctx.tables_dir / "decision_explanation_packs"
    explanation_manifest = _build_explanation_packs(
        collection_manifest_path=collection_manifest_path,
        output_root=explanation_root,
    )

    pilot_ctx = run_pilot_integration.main(
        [
            "--pilot_bundle",
            str(pilot_bundle_path),
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
            "--kpi_contract",
            str(kpi_contract_path),
            "--n_customers",
            str(int(args.n_customers) if int(args.n_customers) > 0 else int(len(normalized_df))),
            "--sample_seed",
            str(int(args.sample_seed)),
            "--artifact_root",
            str(child_root / "pilot"),
            "--model_version",
            _safe_text(args.model_version),
            "--model_manifest",
            _safe_text(args.model_manifest),
            "--institution_policy_overlay_json",
            json.dumps(institution_policy_raw, ensure_ascii=False),
            "--institution_offer_overlay_json",
            json.dumps(institution_offer_raw, ensure_ascii=False),
            "--pilot_profile_overlay_json",
            json.dumps(pilot_profile_raw, ensure_ascii=False),
            "--resolved_runtime_config_json",
            json.dumps(resolved_runtime_config, ensure_ascii=False),
            "--institution_profile_key",
            institution_profile_key,
            "--policy_version_evaluated",
            _safe_text(collection_manifest.get("policy_version_evaluated")),
            "--explanation_pack_root",
            str(explanation_root),
            "--refresh_run_id",
            run_ctx.run_id,
        ]
    )
    pilot_manifest_path = pilot_ctx.tables_dir / "pilot_package_manifest.json"

    smoke_ctx = run_production_smoke.main(
        [
            "--kpi_contract",
            str(kpi_contract_path),
            "--batch_summary_json",
            str(pilot_ctx.tables_dir / "batch_summary.json"),
            "--batch_fairness_change_csv",
            str(pilot_ctx.tables_dir / "batch_fairness_change.csv"),
            "--release_evidence_pack_json",
            str(pilot_ctx.tables_dir / "release_evidence_pack.json"),
            "--artifact_root",
            str(child_root / "smoke"),
        ]
    )
    release_smoke_summary_path = smoke_ctx.tables_dir / "release_smoke_summary.json"
    release_smoke_summary = _load_json(release_smoke_summary_path)

    artifact_qa_summary = run_pilot_artifact_qa.evaluate_pilot_artifact_qa(
        collection_manifest_path=collection_manifest_path,
        pilot_package_manifest_path=pilot_manifest_path,
        explanation_root=explanation_root,
        expected_policy_version=_safe_text(collection_manifest.get("policy_version_evaluated")),
    )
    artifact_qa_summary_path = run_ctx.tables_dir / "artifact_qa_summary.json"
    artifact_qa_summary_path.write_text(
        json.dumps(artifact_qa_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _apply_qa_to_explanation_packs(
        explanation_root=explanation_root,
        qa_status=_safe_text(artifact_qa_summary.get("artifact_qa_status"), "PASS"),
        qa_stamp=f"artifact_qa:{_safe_text(artifact_qa_summary.get('artifact_qa_status'), 'PASS')}",
    )

    reference_manifest, comparison_is_canonical = _find_reference_manifest(
        artifact_root=Path(args.artifact_root),
        institution_profile_key=institution_profile_key,
        current_run_id=run_ctx.run_id,
        explicit_reference_run_id=_safe_text(args.reference_run_id),
    )
    comparison_csv = run_ctx.tables_dir / "policy_version_comparison.csv"
    comparison_md = run_ctx.tables_dir / "policy_version_comparison.md"
    comparison_summary = _write_policy_comparison(
        current_collection_manifest=collection_manifest,
        reference_refresh_manifest=reference_manifest,
        output_csv=comparison_csv,
        output_md=comparison_md,
        reference_label=_safe_text(args.reference_label, _safe_text((reference_manifest or {}).get("run_id"), "none")),
    )
    demo_policy_proof_path = run_ctx.tables_dir / "demo_policy_proof.md"
    next_milestone_handoff_path = run_ctx.tables_dir / "next_milestone_handoff.md"
    demo_policy_proof_path.write_text(
        _render_demo_policy_proof(
            collection_manifest=collection_manifest,
            artifact_qa_status=_safe_text(artifact_qa_summary.get("artifact_qa_status")),
            portfolio_smoke_status=_safe_text(release_smoke_summary.get("release_decision")),
        ),
        encoding="utf-8",
    )
    next_milestone_handoff_path.write_text(
        _render_next_milestone_handoff(collection_manifest),
        encoding="utf-8",
    )

    refresh_context = {
        "cadence_mode": cadence_mode,
        "institution_profile_key": institution_profile_key,
        "reference_run_id_requested": _safe_text(args.reference_run_id),
        "reference_label_requested": _safe_text(args.reference_label),
        "invoked_runners": [
            "run_customer_artifact_collection",
            "run_pilot_integration",
            "run_production_smoke",
            "run_pilot_artifact_qa",
        ],
    }
    (run_ctx.tables_dir / "refresh_context.json").write_text(
        json.dumps(refresh_context, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (run_ctx.tables_dir / "release_smoke_summary.json").write_text(
        json.dumps(release_smoke_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    manifest = PilotRefreshManifest(
        run_id=run_ctx.run_id,
        cadence_mode=cadence_mode,
        institution_profile_key=institution_profile_key,
        selection_policy_name=_safe_text(collection_manifest.get("selection_policy_name"), cohort_policy),
        selection_fill_behavior=_safe_text(collection_manifest.get("selection_fill_behavior")),
        policy_version_evaluated=_safe_text(collection_manifest.get("policy_version_evaluated")),
        collection_run_id=collection_ctx.run_id,
        collection_manifest_path=str(collection_manifest_path),
        pilot_package_run_id=pilot_ctx.run_id,
        pilot_package_manifest_path=str(pilot_manifest_path),
        smoke_run_id=smoke_ctx.run_id,
        smoke_summary_path=str(release_smoke_summary_path),
        artifact_qa_status=_safe_text(artifact_qa_summary.get("artifact_qa_status"), "FAIL"),
        portfolio_smoke_status=_safe_text(release_smoke_summary.get("release_decision")),
        preferred_demo_profile=_safe_text(collection_manifest.get("preferred_demo_profile")),
        fallback_demo_profile=_safe_text(collection_manifest.get("fallback_demo_profile")),
        policy_baseline_selection_reason=_safe_text(collection_manifest.get("policy_baseline_selection_reason")),
        next_milestone_focus=_safe_text(collection_manifest.get("next_milestone_focus")),
        reference_run_id=_safe_text((reference_manifest or {}).get("run_id")) or None,
        reference_label=_safe_text(args.reference_label, _safe_text((reference_manifest or {}).get("run_id"))) or None,
        comparison_is_canonical=bool(comparison_is_canonical),
        refresh_context=refresh_context,
        resolved_runtime_config=resolved_runtime_config,
        overlay_provenance={
            **_overlay_provenance(
                institution_policy_path=institution_policy_path,
                institution_offer_path=institution_offer_path,
                pilot_profile_path=pilot_profile_path,
            ),
            "institution_policy": institution_policy_raw,
            "institution_offer": institution_offer_raw,
            "pilot_profile": pilot_profile_raw,
        },
        comparison_summary=comparison_summary,
        output_artifacts={
            "pilot_refresh_summary_md": "tables/pilot_refresh_summary.md",
            "policy_version_comparison_csv": "tables/policy_version_comparison.csv",
            "policy_version_comparison_md": "tables/policy_version_comparison.md",
            "demo_policy_proof_md": "tables/demo_policy_proof.md",
            "next_milestone_handoff_md": "tables/next_milestone_handoff.md",
            "artifact_qa_summary_json": "tables/artifact_qa_summary.json",
            "release_smoke_summary_json": "tables/release_smoke_summary.json",
            "refresh_context_json": "tables/refresh_context.json",
            "decision_explanation_packs_root": str(explanation_root),
        },
    )
    manifest_path = run_ctx.tables_dir / "pilot_refresh_manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    summary_payload = {
        "cadence_mode": cadence_mode,
        "institution_profile_key": institution_profile_key,
        "policy_version_evaluated": _safe_text(collection_manifest.get("policy_version_evaluated")),
        "preferred_demo_profile": _safe_text(collection_manifest.get("preferred_demo_profile")),
        "fallback_demo_profile": _safe_text(collection_manifest.get("fallback_demo_profile")),
        "policy_baseline_selection_reason": _safe_text(collection_manifest.get("policy_baseline_selection_reason")),
        "recommended_candidate_policy_version": _safe_text(collection_manifest.get("recommended_candidate_policy_version")),
        "recommended_candidate_status": _safe_text(collection_manifest.get("recommended_candidate_status"), "no_safe_uplift"),
        "recommended_outcome_rule_profile_version": _safe_text(collection_manifest.get("recommended_outcome_rule_profile_version")),
        "recommended_outcome_rule_status": _safe_text(collection_manifest.get("recommended_outcome_rule_status"), "no_safe_uplift"),
        "threshold_family_promotion_status": _safe_text(collection_manifest.get("threshold_family_promotion_status")),
        "outcome_rule_family_promotion_status": _safe_text(collection_manifest.get("outcome_rule_family_promotion_status")),
        "next_milestone_focus": _safe_text(collection_manifest.get("next_milestone_focus")),
        "dominant_movement_bottleneck": _safe_text(collection_manifest.get("dominant_movement_bottleneck")),
        "movement_guardrail_summary": _safe_text(collection_manifest.get("movement_guardrail_summary")),
        "promotion_blocker_summary": _safe_text(collection_manifest.get("promotion_blocker_summary")),
        "portfolio_smoke_status": _safe_text(release_smoke_summary.get("release_decision")),
        "artifact_qa_status": _safe_text(artifact_qa_summary.get("artifact_qa_status")),
        "comparison_is_canonical": bool(comparison_is_canonical),
        "collection_run_id": collection_ctx.run_id,
        "pilot_package_run_id": pilot_ctx.run_id,
        "smoke_run_id": smoke_ctx.run_id,
        "reference_run_id": _safe_text((reference_manifest or {}).get("run_id")),
    }
    (run_ctx.tables_dir / "pilot_refresh_summary.md").write_text(
        _render_refresh_summary(summary_payload),
        encoding="utf-8",
    )
    run_ctx.save_metrics(summary_payload)
    logger.info(
        "Pilot baseline refresh complete. portfolio_smoke_status=%s artifact_qa_status=%s",
        summary_payload["portfolio_smoke_status"],
        summary_payload["artifact_qa_status"],
    )
    return run_ctx


if __name__ == "__main__":
    main()
