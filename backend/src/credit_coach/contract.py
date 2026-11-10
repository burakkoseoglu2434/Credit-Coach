"""Decision contract (ADR-004): input, internal/public outputs, reason codes, rule ids."""

from __future__ import annotations

import math
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, StrictBool, ValidationError, create_model

from credit_coach.features import TYPES, allowed_features, load_manifest

HUMAN_REVIEW_COMPLETED = "HUMAN_REVIEW_COMPLETED"


class InvalidDecisionInput(ValueError):
    """Missing or invalid decision input. Never turned into a silent decision."""


class OuterStatus(StrEnum):
    APPROVED = "APPROVED"
    CONDITIONAL = "CONDITIONAL"
    REJECTED = "REJECTED"


class InnerStatus(StrEnum):
    APPROVED = "APPROVED"
    CONDITIONAL = "CONDITIONAL"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ReasonCode(StrEnum):
    """Closed list; declaration order is the canonical sort order."""

    PD_BELOW_THRESHOLD = "PD_BELOW_THRESHOLD"
    PD_ABOVE_THRESHOLD = "PD_ABOVE_THRESHOLD"
    PLAN_AVAILABLE = "PLAN_AVAILABLE"
    NO_PLAN_AVAILABLE = "NO_PLAN_AVAILABLE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    HARD_REJECT_THRESHOLD = "HARD_REJECT_THRESHOLD"
    INTERVAL_STRADDLES_THRESHOLD = "INTERVAL_STRADDLES_THRESHOLD"
    WITHIN_BAND_OF_THRESHOLD = "WITHIN_BAND_OF_THRESHOLD"
    WEAK_SUPPORT_NEAR_THRESHOLD = "WEAK_SUPPORT_NEAR_THRESHOLD"


class PublicReasonCode(StrEnum):
    PD_BELOW_THRESHOLD = "PD_BELOW_THRESHOLD"
    PD_ABOVE_THRESHOLD = "PD_ABOVE_THRESHOLD"
    PLAN_AVAILABLE = "PLAN_AVAILABLE"
    NO_PLAN_AVAILABLE = "NO_PLAN_AVAILABLE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    HARD_REJECT_THRESHOLD = "HARD_REJECT_THRESHOLD"


class RuleId(StrEnum):
    R1_HARD_REJECT = "R1_HARD_REJECT"
    R2_THRESHOLD_BAND = "R2_THRESHOLD_BAND"
    R3_WEAK_SUPPORT_NEAR = "R3_WEAK_SUPPORT_NEAR"
    R4_APPROVE = "R4_APPROVE"
    R5_NOT_APPROVED_PLAN = "R5_NOT_APPROVED_PLAN"
    R6_NOT_APPROVED = "R6_NOT_APPROVED"


class ConditionalType(StrEnum):
    DATA_ISSUE = "DATA_ISSUE"  # human review pending; process condition, no numeric upgrade
    PLAN_BASED = "PLAN_BASED"  # week 4: numeric upgrade_condition required


def _basvuru_model() -> type[BaseModel]:
    cols = {c.ad: c for c in load_manifest()}
    fields = {}
    for name in allowed_features():
        t = TYPES[cols[name].tip]
        fields[name] = (t | None, Field(allow_inf_nan=False)) if t is float else (t | None, Field())
    return create_model(
        "Basvuru", __config__=ConfigDict(extra="forbid", frozen=True, strict=True), **fields
    )


Basvuru = _basvuru_model()

_P = {"strict": True, "allow_inf_nan": False, "ge": 0.0, "le": 1.0}


class DecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    basvuru: Basvuru
    p_low: float = Field(**_P)
    p_point: float = Field(**_P)
    p_high: float = Field(**_P)
    ham_skor: float = Field(**_P)
    politika_surumu: str = Field(strict=True, min_length=1)
    plan_available: StrictBool | None = None


class InternalDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dis_durum: OuterStatus
    ic_durum: InnerStatus
    gerekce_kodlari: tuple[ReasonCode, ...]
    tetiklenen_kurallar: tuple[RuleId, ...]
    conditional_type: ConditionalType | None = None
    upgrade_condition: str | None = None
    politika_surumu: str


class PublicDecision(BaseModel):
    """What leaves the system: no NEEDS_REVIEW, no internal reason codes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dis_durum: OuterStatus
    gerekce_kodlari: tuple[PublicReasonCode, ...]
    conditional_type: ConditionalType | None = None
    upgrade_condition: str | None = None
    politika_surumu: str


def parse_input(data: dict) -> DecisionInput:
    """Validate raw data; any problem is an explicit InvalidDecisionInput."""
    try:
        girdi = DecisionInput.model_validate(data)
    except ValidationError as e:
        raise InvalidDecisionInput(str(e)) from e
    check_invariants(girdi)
    return girdi


def check_invariants(g: DecisionInput) -> None:
    vals = (g.p_low, g.p_point, g.p_high, g.ham_skor)
    if not all(isinstance(v, float) and math.isfinite(v) for v in vals):
        raise InvalidDecisionInput("probabilities must be finite floats")
    if not 0.0 <= g.p_low <= g.p_point <= g.p_high <= 1.0:
        raise InvalidDecisionInput("require 0 <= p_low <= p_point <= p_high <= 1")
    if not 0.0 <= g.ham_skor <= 1.0:
        raise InvalidDecisionInput("ham_skor must be in [0, 1]")
