from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from credit_coach.utils.time import utc_now

PILOT_INPUT_CONTRACT_VERSION = "phase39.input.v1"
PILOT_PACKAGE_CONTRACT_VERSION = "phase39.package.v1"


class PilotInstitutionContext(BaseModel):
    institution_name: str = Field(..., description="Institution name for operator-facing pilot package context")
    institution_type: str = Field(..., description="Institution type such as bank, lender, fintech, or servicer")
    portfolio_focus: str | None = Field(default=None, description="Short portfolio focus description")
    data_readiness: str | None = Field(default=None, description="Declared data readiness posture")
    operator_owner: str | None = Field(default=None, description="Named operator owner for the pilot lane")
    notes: list[str] = Field(default_factory=list, description="Optional institution notes")


class PilotBundleSource(BaseModel):
    data_path: str = Field(..., description="Path to the institution-style exported dataset")
    data_format: Literal["csv", "parquet"] = Field(default="csv", description="Supported pilot input file format")
    source_export_name: str | None = Field(default=None, description="Human label for the source export")
    exported_at: datetime | None = Field(default=None, description="Optional export timestamp")


class PilotMappingContract(BaseModel):
    customer_id_column: str = Field(..., description="Source column used as the stable pilot customer identifier")
    target_column: str = Field(..., description="Source target/label column used for validation-time truth")
    group_feature_name: str = Field(
        default="home_ownership",
        description="Canonical fairness group feature expected by the planning core",
    )
    group_feature_column: str = Field(..., description="Source column mapped into the canonical group feature")
    feature_columns: dict[str, str] = Field(
        default_factory=dict,
        description="Explicit canonical feature -> source column mapping overrides",
    )


class PilotInputBundle(BaseModel):
    contract_version: str = Field(default=PILOT_INPUT_CONTRACT_VERSION, description="Canonical pilot input contract version")
    institution: PilotInstitutionContext
    source: PilotBundleSource
    mapping: PilotMappingContract
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional bundle metadata")

    @field_validator("contract_version")
    @classmethod
    def validate_contract_version(cls, value: str) -> str:
        if str(value).strip() != PILOT_INPUT_CONTRACT_VERSION:
            raise ValueError(
                f"Unsupported pilot input contract_version={value!r}; expected {PILOT_INPUT_CONTRACT_VERSION!r}"
            )
        return value


class PilotResolvedMapping(BaseModel):
    customer_id_column: str
    target_column: str
    group_feature_name: str
    group_feature_column: str
    feature_mapping: dict[str, str]
    explicit_feature_count: int = Field(default=0, ge=0)
    identity_fallback_features: list[str] = Field(default_factory=list)
    missing_required_features: list[str] = Field(default_factory=list)


class PilotPackageManifest(BaseModel):
    contract_version: str = Field(
        default=PILOT_PACKAGE_CONTRACT_VERSION,
        description="Canonical pilot package manifest contract version",
    )
    run_id: str
    generated_at: datetime = Field(default_factory=utc_now)
    institution: PilotInstitutionContext
    input_contract_version: str = Field(default=PILOT_INPUT_CONTRACT_VERSION)
    source_data_path: str
    normalized_input_path: str
    normalized_row_count: int = Field(..., ge=1)
    group_feature_name: str
    batch_run_id: str
    batch_artifact_dir: str
    release_decision: str
    acceptance_status: str
    pilot_eligible: bool
    broad_rollout_allowed: bool
    required_artifacts: dict[str, str] = Field(default_factory=dict)
    optional_artifacts: dict[str, str] = Field(default_factory=dict)
    mapping_provenance: dict[str, Any] = Field(default_factory=dict)

    @field_validator("contract_version")
    @classmethod
    def validate_package_contract_version(cls, value: str) -> str:
        if str(value).strip() != PILOT_PACKAGE_CONTRACT_VERSION:
            raise ValueError(
                f"Unsupported pilot package contract_version={value!r}; expected {PILOT_PACKAGE_CONTRACT_VERSION!r}"
            )
        return value
