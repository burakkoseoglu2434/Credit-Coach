from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from credit_coach.utils.time import utc_now

PILOT_INPUT_CONTRACT_VERSION = "phase39.input.v1"
PILOT_PACKAGE_CONTRACT_VERSION = "phase39.package.v1"
PILOT_REFRESH_CONTRACT_VERSION = "phase44.refresh.v1"
DECISION_EXPLANATION_PACK_CONTRACT_VERSION = "phase44.explanation.v1"
PilotCadenceMode = Literal["pre_pilot", "weekly_during_pilot", "pre_readout"]
PilotArtifactQAStatus = Literal["PASS", "DEGRADED", "FAIL"]
PilotExternalDecision = Literal["APPROVED", "CONDITIONAL", "REJECTED"]
PilotExpectedReadiness = Literal["now", "week_4", "week_12", "week_24", "not_ready", "unknown_review"]


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


class InstitutionPolicyOverlay(BaseModel):
    """
    Thin institution-specific policy overlay.
    """

    overlay_name: str | None = Field(default=None, description="Human-readable overlay label")
    cadence_mode: PilotCadenceMode | None = Field(default=None, description="Preferred pilot refresh cadence")
    allowed_cohort_policies: list[str] = Field(
        default_factory=list,
        description="Allowed collection cohort policies for this institution profile",
    )
    wording_guardrails: list[str] = Field(
        default_factory=list,
        description="Institution-safe wording constraints for proof and explanation surfaces",
    )
    usage_constraints: dict[str, Any] = Field(
        default_factory=dict,
        description="Extra institution usage posture flags",
    )

    model_config = {"extra": "allow"}


class InstitutionOfferOverlay(BaseModel):
    """
    Thin institution-specific offer overlay.
    """

    overlay_name: str | None = Field(default=None, description="Human-readable overlay label")
    enabled_offer_families: list[str] = Field(
        default_factory=list,
        description="Offer families enabled for this institution profile",
    )
    maturity_defaults: dict[str, str] = Field(
        default_factory=dict,
        description="Offer family -> default maturity mapping",
    )
    approval_dependency_flags: dict[str, bool] = Field(
        default_factory=dict,
        description="Offer family -> approval dependency flag mapping",
    )
    institution_action_availability: dict[str, bool] = Field(
        default_factory=dict,
        description="Institution-side action availability flags",
    )

    model_config = {"extra": "allow"}


class PilotProfileOverlay(BaseModel):
    """
    Optional pilot-profile overlay for refresh posture and reference-run grouping.
    """

    profile_name: str | None = Field(default=None, description="Stable institution pilot profile name")
    profile_key: str | None = Field(default=None, description="Stable key used for refresh comparison grouping")
    selection_policy_name: str | None = Field(default=None, description="Preferred collection cohort policy")
    selection_fill_behavior: str | None = Field(default=None, description="Preferred collection fill behavior")
    notes: list[str] = Field(default_factory=list, description="Optional operator notes")

    model_config = {"extra": "allow"}


class DecisionExplanationDriver(BaseModel):
    """
    External-safe numeric driver row for explanation packs.
    """

    driver_key: str = Field(..., description="Stable driver key")
    current_value: float = Field(..., description="Current numeric value")
    target_value: float = Field(..., description="Target numeric value")
    unit: str = Field(default="", description="Business-safe unit label")
    source_field: str | None = Field(default=None, description="Canonical source field name")
    comparison: str | None = Field(default=None, description="Comparison operator")


class DecisionExplanationReason(BaseModel):
    """
    Standardized institution-facing reason item.
    """

    reason_code: str = Field(..., description="Stable institution-facing reason code")
    title: str = Field(..., description="Short reason title")
    description: str = Field(..., description="Short reason description")
    remediation_hint: str | None = Field(default=None, description="Short institution-safe remediation hint")


class DecisionExplanationPack(BaseModel):
    """
    Institution-facing, audit-friendly explanation artifact.
    """

    contract_version: str = Field(
        default=DECISION_EXPLANATION_PACK_CONTRACT_VERSION,
        description="Canonical explanation-pack contract version",
    )
    decision_id: str = Field(..., description="Stable decision snapshot id")
    customer_id: str = Field(..., description="Stable customer identifier")
    decision_outcome: PilotExternalDecision = Field(..., description="External-only decision outcome")
    external_decision_only: bool = Field(default=True, description="Leak guard: external decision vocabulary only")
    one_line_decision_reason: str = Field(..., description="Owned one-line external decision reason")
    structured_numeric_drivers: list[DecisionExplanationDriver] = Field(
        default_factory=list,
        description="Institution-safe numeric drivers",
    )
    recommended_customer_action: str | None = Field(
        default=None,
        description="Owned customer-facing action recommendation derived from the roadmap narrative",
    )
    institution_condition: str | None = Field(
        default=None,
        description="Institution-side condition or dependency kept separate from customer action",
    )
    driver_methodology_note: str = Field(
        default="Drivers are derived from the owned decision payload and exposed only as institution-safe numeric summaries.",
        description="Short methodology note for the driver list",
    )
    upgrade_condition: str | None = Field(default=None, description="What would move the decision upward")
    expected_readiness: PilotExpectedReadiness = Field(..., description="Owned readiness expectation")
    adverse_action_friendly_reasons: list[DecisionExplanationReason] = Field(
        default_factory=list,
        description="Standardized institution-facing reason rows",
    )
    policy_version: str = Field(..., description="Owned decision-policy version")
    policy_effective_at: datetime | None = Field(default=None, description="Optional policy effective timestamp")
    artifact_generated_at: datetime = Field(default_factory=utc_now, description="Artifact generation timestamp")
    qa_status: PilotArtifactQAStatus = Field(default="PASS", description="Latest QA posture for this explanation pack")
    qa_stamp: str = Field(default="", description="Compact QA stamp string")
    human_review_required: bool = Field(default=False, description="Whether a human review flag should accompany this artifact")
    disclaimer: list[str] = Field(
        default_factory=lambda: [
            "This artifact is institution-facing explanatory support.",
            "It is not a legal opinion.",
            "It is not compliance automation.",
            "It does not replace institution review.",
        ],
        description="Boundary statements for external-safe usage",
    )

    @field_validator("contract_version")
    @classmethod
    def validate_explanation_contract_version(cls, value: str) -> str:
        if str(value).strip() != DECISION_EXPLANATION_PACK_CONTRACT_VERSION:
            raise ValueError(
                "Unsupported decision explanation contract_version="
                f"{value!r}; expected {DECISION_EXPLANATION_PACK_CONTRACT_VERSION!r}"
            )
        return value


class PilotRefreshManifest(BaseModel):
    """
    Phase 44 pilot refresh manifest over existing truth-owner runners.
    """

    contract_version: str = Field(
        default=PILOT_REFRESH_CONTRACT_VERSION,
        description="Canonical pilot refresh manifest contract version",
    )
    run_id: str
    generated_at: datetime = Field(default_factory=utc_now)
    cadence_mode: PilotCadenceMode
    institution_profile_key: str = Field(..., description="Stable grouping key for reference-run comparison")
    selection_policy_name: str = Field(default="", description="Collection selection policy used in this refresh")
    selection_fill_behavior: str = Field(default="", description="Selection fill behavior used in this refresh")
    policy_version_evaluated: str = Field(default="", description="Decision policy version evaluated by this refresh")
    collection_run_id: str = Field(default="", description="Collection run id used by this refresh")
    collection_manifest_path: str = Field(default="", description="Path to the collection manifest used by this refresh")
    pilot_package_run_id: str = Field(default="", description="Pilot package run id used by this refresh")
    pilot_package_manifest_path: str = Field(default="", description="Path to the pilot package manifest")
    smoke_run_id: str = Field(default="", description="Portfolio smoke run id used by this refresh")
    smoke_summary_path: str = Field(default="", description="Path to the release-smoke summary JSON")
    artifact_qa_status: PilotArtifactQAStatus = Field(..., description="Artifact QA status for the refresh package")
    portfolio_smoke_status: str = Field(default="", description="Portfolio smoke release decision/status")
    reference_run_id: str | None = Field(default=None, description="Canonical or explicit reference run id")
    reference_label: str | None = Field(default=None, description="Human label for the chosen reference run")
    comparison_is_canonical: bool = Field(
        default=False,
        description="Whether comparison is against the canonical previous approved baseline",
    )
    refresh_context: dict[str, Any] = Field(default_factory=dict, description="Refresh invocation context snapshot")
    resolved_runtime_config: dict[str, Any] = Field(default_factory=dict, description="Resolved runtime config after overlay precedence")
    overlay_provenance: dict[str, Any] = Field(default_factory=dict, description="Overlay source provenance")
    comparison_summary: dict[str, Any] = Field(default_factory=dict, description="Policy comparison summary slice")
    output_artifacts: dict[str, str] = Field(default_factory=dict, description="Refresh-output relative artifact paths")

    @field_validator("contract_version")
    @classmethod
    def validate_refresh_contract_version(cls, value: str) -> str:
        if str(value).strip() != PILOT_REFRESH_CONTRACT_VERSION:
            raise ValueError(
                f"Unsupported pilot refresh contract_version={value!r}; expected {PILOT_REFRESH_CONTRACT_VERSION!r}"
            )
        return value


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
    overlay_provenance: dict[str, Any] = Field(default_factory=dict)
    refresh_provenance: dict[str, Any] = Field(default_factory=dict)
    resolved_runtime_config: dict[str, Any] = Field(default_factory=dict)
    institution_profile_key: str = Field(default="", description="Stable grouping key for pilot refresh comparison")
    policy_version_evaluated: str = Field(default="", description="Decision policy version evaluated by the upstream refresh")
    explanation_artifacts: dict[str, str] = Field(default_factory=dict)

    @field_validator("contract_version")
    @classmethod
    def validate_package_contract_version(cls, value: str) -> str:
        if str(value).strip() != PILOT_PACKAGE_CONTRACT_VERSION:
            raise ValueError(
                f"Unsupported pilot package contract_version={value!r}; expected {PILOT_PACKAGE_CONTRACT_VERSION!r}"
            )
        return value
