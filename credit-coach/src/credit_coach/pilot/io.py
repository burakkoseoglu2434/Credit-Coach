from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from credit_coach.pilot.contracts import PilotInputBundle, PilotResolvedMapping


def _load_structured_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Pilot bundle not found: {path}")
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload = json.loads(raw)
    else:
        payload = yaml.safe_load(raw)
    if not isinstance(payload, dict):
        raise ValueError("Pilot bundle payload must be a mapping")
    return payload


def load_pilot_bundle(path: str | Path) -> PilotInputBundle:
    bundle_path = Path(path)
    payload = _load_structured_payload(bundle_path)
    if "source" in payload and isinstance(payload["source"], dict):
        source = dict(payload["source"])
        if source.get("data_path"):
            source["data_path"] = str((bundle_path.parent / str(source["data_path"])).resolve())
        payload["source"] = source
    return PilotInputBundle.model_validate(payload)


def load_pilot_dataframe(bundle: PilotInputBundle) -> pd.DataFrame:
    source_path = Path(bundle.source.data_path)
    if bundle.source.data_format == "csv":
        return pd.read_csv(source_path)
    if bundle.source.data_format == "parquet":
        return pd.read_parquet(source_path)
    raise ValueError(f"Unsupported pilot source format: {bundle.source.data_format}")


def resolve_pilot_mapping(
    bundle: PilotInputBundle,
    *,
    source_columns: list[str],
    required_features: list[str],
) -> PilotResolvedMapping:
    available = set(source_columns)
    mapping = bundle.mapping

    for required_key, source_column in (
        ("customer_id_column", mapping.customer_id_column),
        ("target_column", mapping.target_column),
        ("group_feature_column", mapping.group_feature_column),
    ):
        if str(source_column).strip() not in available:
            raise ValueError(f"Pilot input missing mandatory mapped column for {required_key}: {source_column!r}")

    feature_mapping: dict[str, str] = {}
    identity_fallback_features: list[str] = []
    missing_required_features: list[str] = []
    explicit_feature_count = 0
    overrides = dict(mapping.feature_columns or {})
    for feature_name in required_features:
        source_column = str(overrides.get(feature_name, "")).strip()
        if source_column:
            explicit_feature_count += 1
        elif feature_name in available:
            source_column = feature_name
            identity_fallback_features.append(feature_name)
        else:
            missing_required_features.append(feature_name)
            continue
        if source_column not in available:
            missing_required_features.append(feature_name)
            continue
        feature_mapping[feature_name] = source_column

    if missing_required_features:
        raise ValueError(
            "Pilot input missing required feature mappings: " + ", ".join(sorted(missing_required_features))
        )

    return PilotResolvedMapping(
        customer_id_column=mapping.customer_id_column,
        target_column=mapping.target_column,
        group_feature_name=mapping.group_feature_name,
        group_feature_column=mapping.group_feature_column,
        feature_mapping=feature_mapping,
        explicit_feature_count=explicit_feature_count,
        identity_fallback_features=sorted(identity_fallback_features),
        missing_required_features=[],
    )


def normalize_pilot_dataframe(
    bundle: PilotInputBundle,
    *,
    required_features: list[str],
    target_column_name: str,
) -> tuple[pd.DataFrame, PilotResolvedMapping]:
    source_df = load_pilot_dataframe(bundle)
    resolved = resolve_pilot_mapping(
        bundle,
        source_columns=list(source_df.columns),
        required_features=required_features,
    )

    normalized = pd.DataFrame(index=source_df.index)
    normalized["customer_id"] = source_df[resolved.customer_id_column].astype(str)
    if normalized["customer_id"].str.strip().eq("").any():
        raise ValueError("Pilot input contains empty customer_id values")
    if normalized["customer_id"].duplicated().any():
        raise ValueError("Pilot input contains duplicate customer_id values")

    for feature_name, source_column in resolved.feature_mapping.items():
        normalized[feature_name] = source_df[source_column]
    normalized[target_column_name] = source_df[resolved.target_column]
    if normalized[target_column_name].isna().any():
        raise ValueError("Pilot input contains missing target values")

    if resolved.group_feature_name not in normalized.columns:
        normalized[resolved.group_feature_name] = source_df[resolved.group_feature_column]
    if normalized[resolved.group_feature_name].isna().any():
        raise ValueError("Pilot input contains missing group feature values")

    ordered_columns = ["customer_id", *required_features, target_column_name]
    if resolved.group_feature_name not in ordered_columns:
        ordered_columns.append(resolved.group_feature_name)
    normalized = normalized[ordered_columns].copy()
    if normalized.empty:
        raise ValueError("Pilot input contains zero rows after normalization")
    return normalized, resolved


def build_pilot_input_manifest(
    *,
    bundle: PilotInputBundle,
    resolved_mapping: PilotResolvedMapping,
    normalized_path: str | Path,
    normalized_row_count: int,
) -> dict[str, Any]:
    return {
        "contract_version": bundle.contract_version,
        "institution": bundle.institution.model_dump(mode="json"),
        "source": bundle.source.model_dump(mode="json"),
        "group_feature_name": resolved_mapping.group_feature_name,
        "normalized_input_path": str(normalized_path),
        "normalized_row_count": int(normalized_row_count),
        "mapping_provenance": {
            "customer_id_column": resolved_mapping.customer_id_column,
            "target_column": resolved_mapping.target_column,
            "group_feature_column": resolved_mapping.group_feature_column,
            "explicit_feature_count": int(resolved_mapping.explicit_feature_count),
            "identity_fallback_features": list(resolved_mapping.identity_fallback_features),
            "feature_mapping": dict(resolved_mapping.feature_mapping),
        },
    }
