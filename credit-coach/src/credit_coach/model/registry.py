from __future__ import annotations

import json
from pathlib import Path

import joblib


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


def load_latest_model_bundle(base_path: str | Path = "artifacts/models"):
    latest = Path(base_path) / "latest.json"
    if not latest.exists():
        raise FileNotFoundError("No latest model manifest found. Train a model first.")
    manifest = json.loads(latest.read_text(encoding="utf-8"))

    model = joblib.load(manifest["model_path"])
    calibrator = joblib.load(manifest["calibrator_path"])
    metrics = json.loads(Path(manifest["metrics_path"]).read_text(encoding="utf-8"))
    return model, calibrator, manifest, metrics
