from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import joblib
import yaml

from credit_coach.utils.hashing import hash_file


def save_model_bundle(
    model,
    calibrator,
    metrics: dict,
    model_version: str,
    base_path: str | Path = "artifacts/models",
    extra_manifest_fields: dict | None = None,
) -> dict[str, str]:
    root = Path(base_path) / model_version
    root.mkdir(parents=True, exist_ok=True)

    model_path = root / "model.joblib"
    calibrator_path = root / "calibrator.joblib"
    metrics_path = root / "metrics.json"
    manifest_path = root / "manifest.json"

    joblib.dump(model, model_path)
    joblib.dump(calibrator, calibrator_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    manifest = {
        "model_version": model_version,
        "model_path": str(model_path),
        "calibrator_path": str(calibrator_path),
        "metrics_path": str(metrics_path),
    }
    if isinstance(extra_manifest_fields, dict):
        for k, v in extra_manifest_fields.items():
            manifest[str(k)] = v
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    latest = Path(base_path) / "latest.json"
    latest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def resolve_model_manifest(
    *,
    base_path: str | Path = "artifacts/models",
    model_version: str | None = None,
    manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    base_path = Path(base_path)
    requested_model_version = str(model_version or "").strip()
    requested_manifest_path = str(manifest_path or "").strip()

    if requested_manifest_path:
        resolved_manifest_path = Path(requested_manifest_path)
        if resolved_manifest_path.is_dir():
            resolved_manifest_path = resolved_manifest_path / "manifest.json"
        freeze_mode = "explicit_manifest"
    elif requested_model_version:
        resolved_manifest_path = base_path / requested_model_version / "manifest.json"
        freeze_mode = "explicit_model_version"
    else:
        resolved_manifest_path = base_path / "latest.json"
        freeze_mode = "implicit_latest"

    if not resolved_manifest_path.exists():
        raise FileNotFoundError(f"Model manifest not found: {resolved_manifest_path}")

    manifest = json.loads(resolved_manifest_path.read_text(encoding="utf-8"))
    resolved_model_version = str(manifest.get("model_version", "")).strip()
    if requested_model_version and resolved_model_version and resolved_model_version != requested_model_version:
        raise ValueError(
            f"Requested model_version '{requested_model_version}' does not match manifest model_version '{resolved_model_version}'"
        )
    for key in ("model_path", "calibrator_path", "metrics_path"):
        path = Path(str(manifest.get(key, "")).strip())
        if not path.exists():
            raise FileNotFoundError(f"Manifest field '{key}' points to missing file: {path}")

    resolved = dict(manifest)
    resolved["manifest_path"] = str(resolved_manifest_path)
    resolved["freeze_mode"] = freeze_mode
    resolved["requested_model_version"] = requested_model_version
    resolved["requested_model_manifest"] = requested_manifest_path
    resolved["acceptance_eligible"] = bool(freeze_mode != "implicit_latest")
    return resolved


def load_model_bundle(
    *,
    base_path: str | Path = "artifacts/models",
    model_version: str | None = None,
    manifest_path: str | Path | None = None,
):
    manifest = resolve_model_manifest(
        base_path=base_path,
        model_version=model_version,
        manifest_path=manifest_path,
    )

    model = joblib.load(manifest["model_path"])
    calibrator = joblib.load(manifest["calibrator_path"])
    metrics = json.loads(Path(manifest["metrics_path"]).read_text(encoding="utf-8"))
    return model, calibrator, manifest, metrics


def load_latest_model_bundle(base_path: str | Path = "artifacts/models"):
    return load_model_bundle(base_path=base_path)


def build_frozen_model_manifest(
    manifest: dict[str, Any],
    *,
    project_root: str | Path,
    resolved_by_runner: str,
    training_run_id: str | None = None,
) -> dict[str, Any]:
    project_root = Path(project_root)
    model_version = str(manifest.get("model_version", "")).strip()
    run_id = str(training_run_id or model_version).strip()
    config_hash = ""
    feature_schema_hash = ""

    if run_id:
        config_snapshot_path = project_root / "artifacts" / "runs" / run_id / "config_snapshot.yaml"
        if config_snapshot_path.exists():
            config_hash = hash_file(config_snapshot_path)
            try:
                cfg = yaml.safe_load(config_snapshot_path.read_text(encoding="utf-8")) or {}
            except Exception:
                cfg = {}
            features_config = str(cfg.get("features_config", "")).strip()
            if features_config:
                features_path = Path(features_config)
                if not features_path.is_absolute():
                    features_path = project_root / features_path
                if features_path.exists():
                    feature_schema_hash = hash_file(features_path)

    manifest_path = Path(str(manifest.get("manifest_path", "")).strip())
    artifact_hash = hash_file(manifest_path) if manifest_path.exists() else ""
    return {
        "model_version": model_version,
        "training_run_id": run_id,
        "manifest_path": str(manifest.get("manifest_path", "")),
        "freeze_mode": str(manifest.get("freeze_mode", "implicit_latest")),
        "requested_model_version": str(manifest.get("requested_model_version", "")),
        "requested_model_manifest": str(manifest.get("requested_model_manifest", "")),
        "config_hash": config_hash,
        "feature_schema_hash": feature_schema_hash,
        "artifact_hash": artifact_hash,
        "acceptance_eligible": bool(manifest.get("acceptance_eligible", False)),
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "resolved_by_runner": str(resolved_by_runner),
    }
