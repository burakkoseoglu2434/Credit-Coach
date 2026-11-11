"""Pydantic schemas: single source of truth for the API contract (TS types come from OpenAPI)."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from credit_coach.contract import Basvuru, ConditionalType, OuterStatus, PublicReasonCode
from credit_coach.recourse import PlanGereksiz, PlanVar, PlanYok


class HealthResponse(BaseModel):
    status: str
    version: str


Plan = Annotated[PlanVar | PlanYok | PlanGereksiz, Field(discriminator="durum")]


class ScoreRequest(BaseModel):
    """One application. `basvuru_tarihi` is explicit: it enters the model (credit history in
    months) and the service never reads the clock, so the same request gives the same answer."""

    model_config = ConfigDict(extra="forbid")

    basvuru: Basvuru
    basvuru_tarihi: date


class Skor3(BaseModel):
    model_config = ConfigDict(frozen=True)

    p_low: float
    p_point: float
    p_high: float


class SatirKarari(BaseModel):
    """Decision, support check and recourse result for one record."""

    model_config = ConfigDict(frozen=True)

    dis_durum: OuterStatus
    gerekce_kodlari: list[PublicReasonCode]
    conditional_type: ConditionalType | None = None
    upgrade_condition: str | None = None
    destek_ihlalleri: list[str]
    skor: Skor3 | None  # None when the record is outside the training support (not scored)
    plan: Plan


class Surumler(BaseModel):
    model_config = ConfigDict(frozen=True)

    politika_surumu: str
    politika_sha256: str
    katalog_surumu: str
    katalog_sha256: str
    bundle_sha256: str
    support_sha256: str


class Notlar(BaseModel):
    model_config = ConfigDict(frozen=True)

    etiket: str
    varsayim_notu: str
    plan_notu: str
    plan_yok_notu: str
    karar_notu: str
    dayaniklilik_notu: str
    kanit_notu: str


class GuvenlikPayi(BaseModel):
    """Safety margin delta used for plan validity (plan after-risk must end this far below the
    threshold). An assumption derived by the ADR-007 rule from monthly calibration drift."""

    model_config = ConfigDict(frozen=True)

    deger: float
    etiket: Literal["varsayım"] = "varsayım"
    kaynak: Literal["ADR-007"] = "ADR-007"


class ScoreResponse(BaseModel):
    karar: SatirKarari
    surumler: Surumler
    guvenlik_payi: GuvenlikPayi
    notlar: Notlar


class SatirSonucu(BaseModel):
    satir_no: int  # 1-based data row number
    kayit_id: str | None = None
    karar: SatirKarari


class KovaSatiri(BaseModel):
    kova: str  # p_point - threshold bucket (not approved, in support)
    n: int
    gecerli_plan_orani: float | None


class PortfoyOzeti(BaseModel):
    n: int
    dis_durum_dagilimi: dict[str, int]
    plan_durumu_dagilimi: dict[str, int]
    destek_disi: int
    plan_arayan: int  # in support and not approved
    gecerli_plan_orani: float | None  # plans found / plan_arayan
    yol_orani: dict[str, float | None]  # per path type, share of plan_arayan
    kovalar: list[KovaSatiri]
    # resilience labels of records that have a plan: strongest path per record, and per path type
    dayaniklilik_dagilimi: dict[str, int]
    yol_dayaniklilik: dict[str, dict[str, int]]


class BatchResponse(BaseModel):
    satirlar: list[SatirSonucu]
    ozet: PortfoyOzeti
    surumler: Surumler
    guvenlik_payi: GuvenlikPayi
    notlar: Notlar
