from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Mapping, Sequence

from credit_coach.utils.run_context import create_run_context

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_pilot_artifact_qa")

QA_STATUS_PASS = "PASS"
QA_STATUS_DEGRADED = "DEGRADED"
QA_STATUS_FAIL = "FAIL"
EXTERNAL_DECISION_STATES = {"APPROVED", "CONDITIONAL", "REJECTED"}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate pilot artifact integrity and trust packaging")
    parser.add_argument("--collection_manifest_json", type=str, required=True)
    parser.add_argument("--pilot_package_manifest_json", type=str, default="")
    parser.add_argument("--explanation_root", type=str, default="")
    parser.add_argument("--expected_policy_version", type=str, default="")
    parser.add_argument("--artifact_root", type=str, default="artifacts/pilot_artifact_qa_runs")
    return parser.parse_args(argv)


def _safe_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _artifact_root_from_collection_manifest(collection_manifest_path: Path) -> Path:
    return collection_manifest_path.parents[2]


def _resolve_relpath(base_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return base_dir / path


def _json_files_under(root: Path, filename: str) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob(filename) if path.is_file())


def _leaks_internal_state(payload: Mapping[str, Any]) -> bool:
    status = _safe_text(payload.get("decision_outcome") or payload.get("decision_status"))
    if status == "NEEDS_REVIEW":
        return True
    if status and status not in EXTERNAL_DECISION_STATES:
        return True
    short_view = payload.get("short_view", {})
    if isinstance(short_view, Mapping):
        short_status = _safe_text(short_view.get("decision_status"))
        if short_status == "NEEDS_REVIEW":
            return True
    if payload.get("external_decision_only") is False:
        return True
    return False


def _collect_required_paths(collection_manifest: Mapping[str, Any]) -> list[str]:
    required: list[str] = []
    for block_key in ("flat_files", "calibration_files", "operator_files"):
        block = collection_manifest.get(block_key, {})
        if not isinstance(block, Mapping):
            continue
        required.extend([_safe_text(path) for path in block.values() if _safe_text(path)])
    return required


def evaluate_pilot_artifact_qa(
    *,
    collection_manifest_path: Path,
    pilot_package_manifest_path: Path | None = None,
    explanation_root: Path | None = None,
    expected_policy_version: str = "",
) -> dict[str, Any]:
    collection_manifest = _load_json(collection_manifest_path)
    artifact_root = _artifact_root_from_collection_manifest(collection_manifest_path)
    fail_findings: list[str] = []
    degraded_findings: list[str] = []

    selected_count = int(collection_manifest.get("selected_count", collection_manifest.get("selected_n_customers", 0)))
    contract_health = (
        dict(collection_manifest.get("contract_health", {}))
        if isinstance(collection_manifest.get("contract_health", {}), Mapping)
        else {}
    )

    required_paths = _collect_required_paths(collection_manifest)
    missing_required_paths = [
        raw_path
        for raw_path in required_paths
        if raw_path and not _resolve_relpath(artifact_root, raw_path).exists()
    ]
    if missing_required_paths:
        fail_findings.append("missing_required_artifacts")

    if _safe_float(contract_health.get("critical_field_null_rate"), 0.0) > 0.0:
        fail_findings.append("critical_field_null_rate_nonzero")
    if int(_safe_float(contract_health.get("raw_flat_mismatch_count"), 0.0)) > 0:
        fail_findings.append("raw_flat_mismatch_detected")

    operator_root_value = _safe_text(
        (
            collection_manifest.get("operator_files", {})
            if isinstance(collection_manifest.get("operator_files", {}), Mapping)
            else {}
        ).get("operator_packets_root")
    )
    operator_root = _resolve_relpath(artifact_root, operator_root_value) if operator_root_value else None
    operator_packet_paths = _json_files_under(operator_root, "operator_packet.json") if operator_root is not None else []
    if selected_count > 0 and len(operator_packet_paths) != selected_count:
        fail_findings.append("operator_packet_coverage_incomplete")
    for packet_path in operator_packet_paths:
        packet_payload = _load_json(packet_path)
        if _leaks_internal_state(packet_payload):
            fail_findings.append("operator_packet_internal_state_leak")
            break

    collection_policy_version = _safe_text(
        collection_manifest.get("decision_policy_version"),
        _safe_text(collection_manifest.get("policy_version_evaluated")),
    )
    if expected_policy_version and collection_policy_version and collection_policy_version != expected_policy_version:
        fail_findings.append("collection_policy_version_mismatch")

    explanation_pack_paths: list[Path] = []
    if explanation_root is None:
        degraded_findings.append("missing_explanation_root")
    else:
        explanation_pack_paths = _json_files_under(explanation_root, "decision_explanation_pack.json")
        if selected_count > 0 and len(explanation_pack_paths) != selected_count:
            fail_findings.append("explanation_pack_coverage_incomplete")
        for pack_path in explanation_pack_paths:
            pack_payload = _load_json(pack_path)
            if _leaks_internal_state(pack_payload):
                fail_findings.append("decision_explanation_internal_state_leak")
                break
            if not _safe_text(pack_payload.get("policy_version")):
                fail_findings.append("decision_explanation_missing_policy_version")
                break

    pilot_manifest_payload: dict[str, Any] = {}
    if pilot_package_manifest_path is None:
        degraded_findings.append("missing_pilot_package_manifest")
    else:
        pilot_manifest_payload = _load_json(pilot_package_manifest_path)
        if expected_policy_version and _safe_text(pilot_manifest_payload.get("policy_version_evaluated")) not in {"", expected_policy_version}:
            fail_findings.append("pilot_package_policy_version_mismatch")
        if explanation_root is not None:
            explanation_artifacts = pilot_manifest_payload.get("explanation_artifacts", {})
            if isinstance(explanation_artifacts, Mapping):
                explanation_root_ref = _safe_text(explanation_artifacts.get("decision_explanation_packs_root"))
                if explanation_root_ref and not Path(explanation_root_ref).exists():
                    degraded_findings.append("pilot_manifest_explanation_root_missing")

    status = QA_STATUS_PASS
    if fail_findings:
        status = QA_STATUS_FAIL
    elif degraded_findings:
        status = QA_STATUS_DEGRADED

    return {
        "artifact_qa_status": status,
        "collection_manifest_path": str(collection_manifest_path),
        "pilot_package_manifest_path": str(pilot_package_manifest_path) if pilot_package_manifest_path is not None else "",
        "explanation_root": str(explanation_root) if explanation_root is not None else "",
        "expected_policy_version": expected_policy_version,
        "selected_count": selected_count,
        "operator_packet_count": len(operator_packet_paths),
        "decision_explanation_pack_count": len(explanation_pack_paths),
        "missing_required_paths": missing_required_paths,
        "fail_findings": fail_findings,
        "degraded_findings": degraded_findings,
        "contract_health": contract_health,
        "collection_policy_version": collection_policy_version,
        "pilot_package_policy_version": _safe_text(pilot_manifest_payload.get("policy_version_evaluated")),
    }


def _render_summary_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Pilot Artifact QA",
        "",
        f"- Status: {_safe_text(summary.get('artifact_qa_status'), QA_STATUS_FAIL)}",
        f"- Selected customers: {int(summary.get('selected_count', 0))}",
        f"- Operator packets: {int(summary.get('operator_packet_count', 0))}",
        f"- Decision explanation packs: {int(summary.get('decision_explanation_pack_count', 0))}",
        "",
        "## Fail Findings",
    ]
    fail_findings = list(summary.get("fail_findings", []))
    if fail_findings:
        for item in fail_findings:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Degraded Findings"])
    degraded_findings = list(summary.get("degraded_findings", []))
    if degraded_findings:
        for item in degraded_findings:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None):
    args = parse_args(argv)
    collection_manifest_path = Path(args.collection_manifest_json)
    pilot_package_manifest_path = Path(args.pilot_package_manifest_json) if _safe_text(args.pilot_package_manifest_json) else None
    explanation_root = Path(args.explanation_root) if _safe_text(args.explanation_root) else None
    summary = evaluate_pilot_artifact_qa(
        collection_manifest_path=collection_manifest_path,
        pilot_package_manifest_path=pilot_package_manifest_path,
        explanation_root=explanation_root,
        expected_policy_version=_safe_text(args.expected_policy_version),
    )
    run_ctx = create_run_context(
        {
            "phase": "44-pilot-artifact-qa",
            "collection_manifest_json": str(collection_manifest_path),
            "pilot_package_manifest_json": str(pilot_package_manifest_path) if pilot_package_manifest_path is not None else "",
            "explanation_root": str(explanation_root) if explanation_root is not None else "",
            "expected_policy_version": _safe_text(args.expected_policy_version),
            "artifact_qa_status": summary["artifact_qa_status"],
        },
        base_artifact_dir=args.artifact_root,
    )
    (run_ctx.tables_dir / "artifact_qa_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (run_ctx.tables_dir / "artifact_qa_summary.md").write_text(
        _render_summary_markdown(summary),
        encoding="utf-8",
    )
    run_ctx.save_metrics({"artifact_qa_status": summary["artifact_qa_status"]})
    logger.info("Pilot artifact QA complete. status=%s", summary["artifact_qa_status"])
    return run_ctx


if __name__ == "__main__":
    main()
