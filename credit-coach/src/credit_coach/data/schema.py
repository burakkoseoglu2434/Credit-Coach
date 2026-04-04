"""
data/schema.py
==============
Pydantic v2 şemaları — proje genelinde veri kontratlarını tanımlar.

Neden var?
----------
- Type safety: Yanlış tipte veri pipeline'a girerse Pydantic hemen hata fırlatır.
- Self-documenting: Her field'ın ne anlama geldiği açıklamada yazıyor.
- Separation of concerns: DB tabloları (SQLAlchemy ORM) ile network/uygulama
  şemaları (Pydantic) ayrıdır — ikisi birbirinin içine geçmez.

Şemalar
-------
CustomerSnapshot   → x_t: müşterinin o andaki 48-feature vektörü + meta
MacroSnapshot      → z_t: makro ekonomik durum
PlanRecord         → recourse planı (aksiyonlar + skorlar + status)
ModelRunRecord     → bir model training/prediction çalışmasının kaydı
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from credit_coach.utils.time import utc_now


ActionClass = Literal["behavioral", "structural", "institutional"]
PlanSource = Literal["internal", "dice", "rule", "fallback"]
PathType = Literal["customer_only", "institution_assisted", "hybrid"]
PlanContenderBucket = Literal["ACTIONABLE", "APPROVAL_SHELL_ONLY", "EMPTY"]
PlanEmptyReason = Literal["ZERO_ACTION", "SEMANTIC_EMPTY"]
ConstraintFamily = Literal["capacity", "policy", "dependency", "interaction", "semantic", "documentation"]
ActionConstraintStatus = Literal["valid", "clipped", "repaired", "provisional", "invalid"]
PlanConstraintStatus = Literal["valid", "repaired", "provisional", "invalid"]
DifficultyLabel = Literal["low", "moderate", "high"]
ReadinessLabel = Literal["low", "moderate", "high"]
InstitutionalApprovalState = Literal["not_required", "approved", "pending", "unknown"]
RoadmapDecisionStatus = Literal["APPROVED", "CONDITIONAL", "REJECTED"]
RoadmapDecisionStatusInternal = Literal["APPROVED", "CONDITIONAL", "REJECTED", "NEEDS_REVIEW"]
DecisionExpectedReadiness = Literal["now", "week_4", "week_12", "week_24", "not_ready", "unknown_review"]
DecisionReasonPrimary = Literal["NO_PATH", "LOW_IMPACT", "LOW_EXECUTION", "OFFER_BLOCK", "TIME_BLOCK", "DATA_ISSUE"]
DecisionRejectionType = Literal["NO_PATH", "LOW_IMPACT", "LOW_EXECUTION"]
DecisionConditionalType = Literal["EXECUTION_GATED", "TIME_GATED", "OFFER_GATED", "DATA_ISSUE"]
OfferMaturity = Literal["none", "inactive", "provisional", "active_rankable"]
OfferFeasibility = Literal["not_applicable", "inactive", "provisional", "active_rankable"]
RecommendationValidityStatus = Literal["valid", "warning", "invalid"]
DiceBackendClass = Literal["native", "heuristic_fallback", "skipped"]
TrajectoryCheckpointStatus = Literal["on_track", "at_risk", "missed", "unknown"]
ContractDataIssueCode = Literal[
    "missing_required_field",
    "checkpoint_status_missing",
    "parity_mismatch",
    "zero_step_no_path",
]


# ------------------------------------------------------------------ #
# CustomerSnapshot — x_t
# ------------------------------------------------------------------ #
class CustomerSnapshot(BaseModel):
    """
    Müşterinin belirli bir zaman anındaki özellik vektörü.

    x_t olarak gösterilir. 48 feature + kimlik ve zaman meta verisi içerir.
    Bu nesne hem DB'ye kaydedilir hem de model predict input'u olarak kullanılır.
    """

    customer_id: str = Field(..., description="Müşteri benzersiz ID'si")
    snapshot_date: datetime = Field(
        default_factory=utc_now,
        description="Snapshot alınma zamanı (UTC)",
    )
    features: dict[str, float | int | None] = Field(
        ...,
        description="48 feature ismi → değer eşleşmesi. Eksik değerler None olabilir.",
    )
    risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="f(x_t, z_t) — model tarafından hesaplanan PD skoru",
    )
    source: str = Field(
        default="manual",
        description="Verinin kaynağı: 'lendingclub' | 'api' | 'manual' | 'demo'",
    )

    model_config = {"json_schema_extra": {"example": {
        "customer_id": "cust_001",
        "snapshot_date": "2026-03-05T10:00:00",
        "features": {"loan_amnt": 15000, "int_rate": 13.5, "dti": 28.0},
        "risk_score": 0.42,
        "source": "lendingclub",
    }}}


# ------------------------------------------------------------------ #
# MacroSnapshot — z_t
# ------------------------------------------------------------------ #
class MacroSnapshot(BaseModel):
    """
    Belirli bir tarihteki makro ekonomik durum.

    z_t olarak gösterilir. Risk modeli kararı ve alpha değeri bu
    snapshot'a göre koşullanır: f(x, z_t) ve alpha(z_t).
    """

    snapshot_date: datetime = Field(
        default_factory=utc_now,
        description="Makro snapshot tarihi",
    )
    interest_rate: float = Field(..., description="Merkez bankası faiz oranı (%)")
    unemployment_rate: float = Field(..., description="İşsizlik oranı (%)")
    gdp_growth: float = Field(..., description="GSYİH büyüme oranı (%)")
    inflation_rate: float = Field(..., description="Enflasyon oranı (%)")
    credit_spread: float = Field(..., description="Kredi spread endeksi")
    macro_stress_index: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="MSI — compute edilince doldurulur",
    )
    source: str = Field(default="mock", description="'mock' | 'csv' | 'api'")


# ------------------------------------------------------------------ #
# PlanAction views — semantic vs technical
# ------------------------------------------------------------------ #
class ActionBusinessView(BaseModel):
    """
    Product-facing semantic action identity.
    """

    action_key: str | None = Field(default=None, description="Semantic action key")
    action_family: str | None = Field(default=None, description="Canonical action family")
    action_class: ActionClass | None = Field(
        default=None,
        description="Top-level action class",
    )
    action_title: str | None = Field(default=None, description="Catalog-driven action title")
    action_description: str | None = Field(default=None, description="Catalog-driven short description")
    action_group_id: str | None = Field(default=None, description="Deterministic grouped action kimligi")


class ActionTechnicalView(BaseModel):
    """
    Engine-facing low-level effect traceability layer.
    """

    feature_name: str = Field(..., description="Effect anchor feature name")
    current_value: float | None = Field(default=None, description="Current raw feature value")
    target_value: float = Field(..., description="Target raw feature value")
    delta: float = Field(..., description="Raw feature delta")
    time_months: int = Field(..., ge=1, description="Action horizon in months")
    phase_id: str | None = Field(default=None, description="Canonical phase id")
    week_start: int | None = Field(default=None, ge=1, description="Action start week")
    week_end: int | None = Field(default=None, ge=1, description="Action end week")
    checkpoint_metric: str | None = Field(default=None, description="Technical checkpoint metric")


class PrimaryNumericTarget(BaseModel):
    """
    Business-readable primary numeric target contract for one semantic action.
    """

    metric_key: str = Field(..., description="Business-friendly deterministic numeric metric key")
    unit: Literal[
        "currency",
        "percentage_points",
        "ratio",
        "score_points",
        "months",
        "boolean_state",
        "count",
    ] = Field(..., description="Canonical unit family")
    current_value: float | None = Field(default=None, description="Current business-readable target value")
    target_value: float = Field(..., description="Recommended absolute target value")
    delta_value: float = Field(..., description="Signed target delta")
    due_month: int = Field(..., ge=1, description="Canonical due month for reaching the target")
    direction: Literal["decrease", "increase"] = Field(..., description="Target movement direction")
    generation_notes: list[str] = Field(
        default_factory=list,
        description="Non-verdict generation notes for later feasibility handling",
    )
    raw_generation_basis: dict[str, Any] = Field(
        default_factory=dict,
        description="Lightweight generation provenance carried into feasibility",
    )


class OfferTerms(BaseModel):
    """
    Semi-typed canonical offer term contract with a narrow extension map.
    """

    payment_delta_monthly: float | None = Field(default=None, description="Aylik odeme degisimi")
    discount_amount: float | None = Field(default=None, description="Mutlak indirim tutari")
    discount_pct: float | None = Field(default=None, description="Oransal indirim")
    term_extension_months: int | None = Field(default=None, ge=0, description="Vade uzatma ayi")
    interest_rate_delta: float | None = Field(default=None, description="Faiz orani farki")
    grace_period_weeks: int | None = Field(default=None, ge=0, description="Grace period haftasi")
    extensions: dict[str, Any] = Field(
        default_factory=dict,
        description="Canonical alanlar disindaki kucuk extension map",
    )

    @model_validator(mode="before")
    @classmethod
    def capture_extensions(cls, value: Any) -> Any:
        if isinstance(value, OfferTerms):
            return value
        if not isinstance(value, dict):
            return value
        data = dict(value)
        known_keys = {
            "payment_delta_monthly",
            "discount_amount",
            "discount_pct",
            "term_extension_months",
            "interest_rate_delta",
            "grace_period_weeks",
            "extensions",
        }
        extensions = dict(data.get("extensions", {}) or {})
        for key in list(data.keys()):
            if key not in known_keys:
                extensions[key] = data.pop(key)
        data["extensions"] = extensions
        return data

    def to_legacy_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key in (
            "payment_delta_monthly",
            "discount_amount",
            "discount_pct",
            "term_extension_months",
            "interest_rate_delta",
            "grace_period_weeks",
        ):
            value = getattr(self, key)
            if value is not None:
                out[key] = value
        out.update(dict(self.extensions or {}))
        return out


class OfferContract(BaseModel):
    """
    Canonical institution-side offer layer attached to a semantic action.
    """

    offer_type: str | None = Field(default=None, description="Canonical offer type")
    offer_family: str | None = Field(default=None, description="Canonical offer family")
    offer_terms: OfferTerms = Field(default_factory=OfferTerms, description="Semi-typed offer terms")
    offer_terms_complete: bool = Field(default=False, description="Offer term seti ordinary ranking icin complete mi")
    requires_acceptance: bool = Field(default=False, description="Offer musteri kabulune bagli mi")
    requires_institutional_approval: bool = Field(default=False, description="Offer kurum onayina bagli mi")
    institutional_approval_state: InstitutionalApprovalState | None = Field(
        default="not_required",
        description="Institution-side approval durumu",
    )
    offer_policy_arm: str | None = Field(default=None, description="Canonical offer policy arm")
    offer_scoring_profile: str | None = Field(default=None, description="Canonical offer scoring profile")
    term_generation_rule: str | None = Field(default=None, description="Canonical term generation rule")

    def is_present(self) -> bool:
        return bool(
            self.offer_type
            or self.requires_acceptance
            or self.requires_institutional_approval
            or self.institutional_approval_state not in {None, "", "not_required"}
            or bool(self.offer_terms.to_legacy_dict())
        )


def _offer_required_flag_from_contract(contract: OfferContract | None, action: "PlanAction") -> bool:
    if contract is not None and contract.is_present():
        return True
    return bool(
        action.requires_institutional_approval
        or action.requires_acceptance
        or action.approval_pending_semantic_only
        or action.offer_type
        or action.offer_family
        or action.offer_policy_arm
    )


def _offer_feasibility_from_contract(contract: OfferContract | None, action: "PlanAction") -> OfferFeasibility:
    if not _offer_required_flag_from_contract(contract, action):
        return "not_applicable"

    approval_state = str(
        getattr(contract, "institutional_approval_state", None)
        if contract is not None
        else getattr(action, "institutional_approval_state", None)
        or "unknown"
    ).strip().lower()
    offer_terms_complete = bool(
        getattr(contract, "offer_terms_complete", False)
        if contract is not None
        else getattr(action, "offer_terms_complete", False)
    )
    if approval_state in {"approved", "not_required"} and offer_terms_complete:
        return "active_rankable"
    if (
        approval_state in {"pending", "unknown"}
        or action.approval_pending_semantic_only
        or action.dependency_gate
        or str(action.action_status or "").strip().lower() == "provisional"
    ):
        return "provisional"
    return "inactive"


# ------------------------------------------------------------------ #
# PlanAction — tek bir aksiyon
# ------------------------------------------------------------------ #
class PlanAction(BaseModel):
    """
    Recourse planındaki tek bir aksiyon öğesi.

    Örnek: "dti'yi 28'den 22'ye düşür — 3 ay içinde."
    """

    feature_name: str = Field(..., description="Değiştirilecek özellik adı")
    current_value: float | None = Field(None, description="Şu anki değer")
    target_value: float = Field(..., description="Hedef değer")
    delta: float = Field(..., description="target_value - current_value")
    time_months: int = Field(..., ge=1, description="Bu aksiyonu tamamlamak için öngörülen ay")
    estimated_cost_usd: float = Field(default=0.0, ge=0.0, description="Tahmini finansal maliyet")
    phase_id: str | None = Field(
        default=None,
        description="Opsiyonel faz etiketi (örn: phase_1_stabilize | phase_2_build | phase_3_optimize)",
    )
    week_start: int | None = Field(default=None, ge=1, description="Aksiyonun başlama haftası (opsiyonel)")
    week_end: int | None = Field(default=None, ge=1, description="Aksiyonun bitiş haftası (opsiyonel)")
    expected_pd_delta: float | None = Field(
        default=None,
        description="Bu aksiyonun beklenen PD iyileştirme katkısı (opsiyonel)",
    )
    checkpoint_metric: str | None = Field(
        default=None,
        description="Aksiyon için izlenecek checkpoint metriği (opsiyonel, örn: dti<=30)",
    )
    action_key: str | None = Field(
        default=None,
        description="Kullaniciya gorunen gercek dunya aksiyon anahtari (orn: reduce_spending)",
    )
    action_class: ActionClass | None = Field(
        default=None,
        description="Aksiyon sinifi: behavioral | structural | institutional",
    )
    action_family: str | None = Field(
        default=None,
        description="Canonical ikinci katman aksiyon ailesi",
    )
    action_title: str | None = Field(default=None, description="Aksiyonun okunabilir basligi")
    action_description: str | None = Field(
        default=None,
        description="Catalog-driven kisa aksiyon aciklamasi",
    )
    action_group_id: str | None = Field(
        default=None,
        description="Composite aksiyonlari ayni grup altinda toplamak icin stabil grup kimligi",
    )
    business_view: ActionBusinessView | None = Field(
        default=None,
        description="Schema-level product-facing semantic action view",
    )
    technical_view: ActionTechnicalView | None = Field(
        default=None,
        description="Schema-level technical effect traceability view",
    )
    primary_numeric_target: PrimaryNumericTarget | None = Field(
        default=None,
        description="Business-readable canonical primary numeric target",
    )
    recommendation_validity_status: RecommendationValidityStatus | None = Field(
        default=None,
        description="Canonical numeric recommendation validity status",
    )
    recommendation_validity_codes: list[str] = Field(
        default_factory=list,
        description="Reason codes behind numeric recommendation validity",
    )
    recommendation_sanity_flag: bool = Field(
        default=False,
        description="Whether the numeric recommendation requires manual review",
    )
    recommendation_warning_penalty: float = Field(
        default=0.0,
        ge=0.0,
        description="Planner-side warning penalty contributed by this action",
    )
    composite_action: bool = Field(
        default=False,
        description="Bu aksiyon daha genis bir composite aksiyonun parcasi mi",
    )
    requires_institutional_approval: bool = Field(
        default=False,
        description="Aksiyonun uygulanmasi kurum onayi gerektiriyor mu",
    )
    institutional_approval_state: Literal["not_required", "approved", "pending", "unknown"] | None = Field(
        default=None,
        description="Institutional aksiyonlar icin onay durumu",
    )
    approval_pending_semantic_only: bool = Field(
        default=False,
        description="Feature effect'e henuz donusmeyen semantik placeholder institutional aksiyon mu",
    )
    offer_contract: OfferContract | None = Field(
        default=None,
        description="Canonical nested institution-side offer contract",
    )
    offer_type: str | None = Field(
        default=None,
        description="Institutional aksiyon icin offer alt-tipi (ornek: discount_offer)",
    )
    offer_terms: dict[str, Any] = Field(
        default_factory=dict,
        description="Offer-bearing institutional aksiyonlar icin structured terms katmani",
    )
    offer_terms_complete: bool = Field(
        default=False,
        description="Offer term seti ordinary winner scoring icin yeterince complete mi",
    )
    requires_acceptance: bool = Field(
        default=False,
        description="Offer veya kurumsal aksiyon ayrica musteri kabulune bagli mi",
    )
    offer_family: str | None = Field(
        default=None,
        description="Offer family veya policy-level aile sinifi",
    )
    offer_scoring_profile: str | None = Field(
        default=None,
        description="Offer kabul / recovery scoring profil etiketi",
    )
    term_generation_rule: str | None = Field(
        default=None,
        description="Offer termlerinin hangi kural paketiyle uretildigi",
    )
    offer_policy_arm: str | None = Field(
        default=None,
        description="Offer optimizer icinde bu aksiyonun bagli oldugu policy arm",
    )
    offer_required_flag: bool = Field(
        default=False,
        description="Aksiyonun semantik olarak institution-side offer veya approval truth gerektirip gerektirmedigi",
    )
    offer_feasibility: OfferFeasibility | None = Field(
        default=None,
        description="Offer/approval truth'unun deterministic feasibility etiketi",
    )
    prerequisite_tags: list[str] = Field(
        default_factory=list,
        description="Bu aksiyonun bagli oldugu prerequisite etiketleri",
    )
    conflict_tags: list[str] = Field(
        default_factory=list,
        description="Bu aksiyonun ayni planda conflict yaratabilecegi etiketler",
    )
    action_status: ActionConstraintStatus | None = Field(
        default="valid",
        description="Action realism veya constraint islemlerinden sonraki durum",
    )
    action_status_reason: str | None = Field(
        default=None,
        description="Aksiyon statusu icin reason code veya aciklama",
    )
    constraint_family: ConstraintFamily | None = Field(
        default=None,
        description="Dominant canonical feasibility or constraint family",
    )
    constraint_reason_codes: list[str] = Field(
        default_factory=list,
        description="Granular canonical reason codes carried with the action-level constraint truth",
    )
    was_clipped: bool = Field(
        default=False,
        description="Numeric target feasibility aksiyonu clip etti mi",
    )
    repair_applied: bool = Field(
        default=False,
        description="Aksiyon semantigi korunarak repair uygulanmis mi",
    )
    dependency_gate: bool = Field(
        default=False,
        description="Aksiyon dis bagimlilik nedeniyle kosullu mu",
    )
    semantic_preserved: bool | None = Field(
        default=None,
        description="Constraint sonrasi aksiyonun business semantics'i korundu mu",
    )
    diagnostic_flags: list[str] = Field(
        default_factory=list,
        description="Aksiyonla ilgili ek diagnostic flag'ler",
    )
    action_execution_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Aksiyonun gercekte uygulanma olasiligi",
    )
    approval_dependent_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Kurumsal onaya bagli aksiyonlar icin ayri olasilik sinyali",
    )
    action_group_execution_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Composite aksiyon grubu seviyesinde toplanmis uygulanma olasiligi",
    )
    difficulty_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Aksiyonun gercekte uygulanma zorlugu",
    )
    difficulty_label: DifficultyLabel | None = Field(
        default=None,
        description="Business-safe aksiyon zorluk etiketi",
    )
    difficulty_drivers: dict[str, float] = Field(
        default_factory=dict,
        description="Aksiyon zorlugunu suren canonical driver seti",
    )
    approval_friction: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Onay bagimli aksiyonlar icin ayri approval-friction sinyali",
    )

    @model_validator(mode="after")
    def populate_action_views(self) -> "PlanAction":
        if self.action_key:
            try:
                from credit_coach.recourse.action_space import get_action_template, get_numeric_target_metadata

                template = get_action_template(str(self.action_key))
                if self.action_class is None:
                    self.action_class = template.action_class
                if self.action_family is None:
                    self.action_family = template.action_family
                if self.action_title is None:
                    self.action_title = template.title
                if self.action_description is None:
                    self.action_description = template.description
            except Exception:
                pass

        if self.business_view is None:
            self.business_view = ActionBusinessView(
                action_key=self.action_key,
                action_family=self.action_family,
                action_class=self.action_class,
                action_title=self.action_title,
                action_description=self.action_description,
                action_group_id=self.action_group_id,
            )
        if self.technical_view is None:
            self.technical_view = ActionTechnicalView(
                feature_name=self.feature_name,
                current_value=self.current_value,
                target_value=self.target_value,
                delta=self.delta,
                time_months=self.time_months,
                phase_id=self.phase_id,
                week_start=self.week_start,
                week_end=self.week_end,
                checkpoint_metric=self.checkpoint_metric,
            )
        if self.primary_numeric_target is None and self.action_key:
            try:
                numeric_meta = get_numeric_target_metadata(
                    self.feature_name,
                    action_month=self.time_months,
                )
                if bool(numeric_meta.get("is_primary_target")):
                    direction = str(numeric_meta.get("direction") or "")
                    if direction in {"increase", "decrease"}:
                        self.primary_numeric_target = PrimaryNumericTarget(
                            metric_key=str(numeric_meta.get("metric_key") or ""),
                            unit=str(numeric_meta.get("unit") or ""),
                            current_value=self.current_value,
                            target_value=self.target_value,
                            delta_value=self.delta,
                            due_month=int(numeric_meta.get("due_month") or self.time_months),
                            direction=direction,
                            generation_notes=["auto_populated_fallback"],
                            raw_generation_basis={
                                "source_feature_name": self.feature_name,
                                "rule_source": str(numeric_meta.get("rule_source") or "unknown"),
                            },
                        )
            except Exception:
                pass
        if self.offer_contract is None:
            raw_terms = dict(self.offer_terms or {}) if isinstance(self.offer_terms, dict) else {}
            candidate = OfferContract(
                offer_type=self.offer_type,
                offer_family=self.offer_family,
                offer_terms=raw_terms,
                offer_terms_complete=bool(self.offer_terms_complete),
                requires_acceptance=bool(self.requires_acceptance),
                requires_institutional_approval=bool(self.requires_institutional_approval),
                institutional_approval_state=self.institutional_approval_state,
                offer_policy_arm=self.offer_policy_arm,
                offer_scoring_profile=self.offer_scoring_profile,
                term_generation_rule=self.term_generation_rule,
            )
            if candidate.is_present():
                self.offer_contract = candidate
        elif not isinstance(self.offer_contract, OfferContract):
            self.offer_contract = OfferContract.model_validate(self.offer_contract)

        if self.offer_contract is not None:
            contract = self.offer_contract
            if self.offer_type is None:
                self.offer_type = contract.offer_type
            if not self.offer_terms:
                self.offer_terms = contract.offer_terms.to_legacy_dict()
            if not self.offer_terms_complete:
                self.offer_terms_complete = bool(contract.offer_terms_complete)
            if not self.requires_acceptance:
                self.requires_acceptance = bool(contract.requires_acceptance)
            if self.offer_family is None:
                self.offer_family = contract.offer_family
            if self.offer_scoring_profile is None:
                self.offer_scoring_profile = contract.offer_scoring_profile
            if self.term_generation_rule is None:
                self.term_generation_rule = contract.term_generation_rule
            if self.offer_policy_arm is None:
                self.offer_policy_arm = contract.offer_policy_arm
            if self.institutional_approval_state is None:
                self.institutional_approval_state = contract.institutional_approval_state
            if not self.requires_institutional_approval:
                self.requires_institutional_approval = bool(contract.requires_institutional_approval)
        self.offer_required_flag = _offer_required_flag_from_contract(self.offer_contract, self)
        self.offer_feasibility = _offer_feasibility_from_contract(self.offer_contract, self)
        return self


class TrajectoryPhase(BaseModel):
    """
    Recourse planinin canonical cok-fazli trajectory bucket'i.
    """

    phase_id: Literal["phase_1_stabilize", "phase_2_build", "phase_3_optimize"] = Field(
        ...,
        description="Canonical faz kimligi",
    )
    phase_title: str = Field(..., description="Insan-okunur faz basligi")
    target_window_weeks: str = Field(..., description="Canonical hafta penceresi")
    target_window_months: list[int] = Field(default_factory=list, description="Canonical ay penceresi")
    review_week: int = Field(..., ge=1, description="Bu faz icin canonical review haftasi")
    target_pd: float | None = Field(default=None, ge=0.0, le=1.0, description="Faz bazli hedef PD")
    gate_pass_target: bool = Field(default=False, description="Faz sonunda gate-pass bekleniyor mu")
    steps: list[PlanAction] = Field(default_factory=list, description="Bu faza ait canonical step listesi")


class TrajectoryCheckpoint(BaseModel):
    """
    Canonical trajectory checkpoint kaydi.
    """

    week: Literal[4, 12, 24] = Field(..., description="Checkpoint haftasi")
    month: Literal[1, 3, 6] = Field(..., description="Checkpoint ay eslesmesi")
    phase_id: Literal["phase_1_stabilize", "phase_2_build", "phase_3_optimize"] = Field(
        ...,
        description="Checkpoint'in bagli oldugu canonical faz",
    )
    checkpoint_type: Literal["primary", "confirmation", "stability"] = Field(
        ...,
        description="Canonical checkpoint tipi",
    )
    checkpoint_label: str | None = Field(default=None, description="Kisa checkpoint etiketi")
    predicted_pd: float | None = Field(default=None, ge=0.0, le=1.0, description="Checkpoint PD tahmini")
    pd_delta_vs_base: float | None = Field(default=None, description="Base PD'ye gore iyilesme")
    gate_pass_estimate: int = Field(default=0, ge=0, le=1, description="Checkpoint gate-pass tahmini")
    checkpoint_priority: Literal[1, 2, 3] = Field(
        default=1,
        description="4w > 12w > 24w oncelik sirasi",
    )
    status: TrajectoryCheckpointStatus = Field(
        default="at_risk",
        description="Checkpoint-local durum etiketi",
    )
    trajectory_jump_flag: bool = Field(
        default=False,
        description="Bir onceki checkpoint'e gore anlamli kotulesme jump'i var mi",
    )
    non_monotonic_flag: bool = Field(
        default=False,
        description="Yumusak monotonicity beklentisi ihlal edildi mi",
    )
    checkpoint_inconsistency_flag: bool = Field(
        default=False,
        description="Checkpoint label/status ile numeric truth uyusmuyor mu",
    )

    @model_validator(mode="after")
    def validate_canonical_checkpoint_contract(self) -> "TrajectoryCheckpoint":
        contract = {
            4: ("phase_1_stabilize", 1, "primary"),
            12: ("phase_2_build", 3, "confirmation"),
            24: ("phase_3_optimize", 6, "stability"),
        }
        expected_phase, expected_month, expected_type = contract[int(self.week)]
        if str(self.phase_id) != expected_phase:
            raise ValueError(f"week={self.week} icin phase_id {expected_phase} olmalidir")
        if int(self.month) != expected_month:
            raise ValueError(f"week={self.week} icin month {expected_month} olmalidir")
        if str(self.checkpoint_type) != expected_type:
            raise ValueError(f"week={self.week} icin checkpoint_type {expected_type} olmalidir")
        expected_priority = {4: 1, 12: 2, 24: 3}[int(self.week)]
        if int(self.checkpoint_priority) != expected_priority:
            raise ValueError(f"week={self.week} icin checkpoint_priority {expected_priority} olmalidir")
        return self


class LocalReason(BaseModel):
    """
    Local explanation reason kaydi (SHAP/fallback).
    """

    feature: str = Field(..., description="Aciklama verilen feature")
    value: float = Field(..., description="Feature degeri")
    contribution: float = Field(..., description="Imzali katki degeri")
    abs_contribution: float = Field(..., ge=0.0, description="Mutlak katki")
    direction: Literal["increase_risk", "decrease_risk"] = Field(
        ..., description="Risk yonu"
    )


class ExplainabilityMeta(BaseModel):
    """
    Aciklama stabilite/guven metrikleri.
    """

    method: str = Field(..., description="shap veya fallback")
    stability_score: float = Field(..., ge=0.0, le=1.0, description="Perturbasyon bazli stabilite")
    baseline_drift_l1: float = Field(..., ge=0.0, description="Katki drift metriği")
    explainability_confidence: float = Field(..., ge=0.0, le=1.0, description="Birlesik guven skoru")
    perturbation_count: int = Field(..., ge=0, description="Kullanilan perturbasyon sayisi")


class LocalizedText(BaseModel):
    """
    Deterministic TR/EN text pair for product-facing narrative output.
    """

    tr: str = Field(..., description="Turkce metin")
    en: str = Field(..., description="English text")


class NarrativeCard(BaseModel):
    """
    Kisa label + supporting description pattern'i.
    """

    label: LocalizedText = Field(..., description="Kisa gorunen deger veya baslik")
    description: LocalizedText = Field(..., description="Destekleyici aciklama")


class OfferNarrative(BaseModel):
    """
    Offer-bearing adimlar icin ayri anlatim katmani.
    """

    offer_explanation: LocalizedText = Field(..., description="Teklifin ne oldugunu aciklar")
    why_offered: LocalizedText = Field(..., description="Neden bu teklifin secildigini aciklar")
    if_accepted: LocalizedText = Field(..., description="Kabul edilirse beklenen durum")
    if_not_accepted: LocalizedText = Field(..., description="Kabul edilmezse beklenen durum")
    offer_terms_summary: LocalizedText | None = Field(
        default=None,
        description="Opsiyonel kisa teklif kosul ozeti",
    )


class RoadmapStepNarrative(BaseModel):
    """
    Tek bir step icin product-facing narrative kaydi.
    """

    step_id: str = Field(..., description="Raw step ile narrative step arasindaki stabil bag")
    phase_id: str = Field(..., description="Bagli canonical faz")
    action_key: str | None = Field(default=None, description="Bagli aksiyon anahtari")
    action_group_id: str | None = Field(default=None, description="Composite action group kimligi")
    action_summary: LocalizedText = Field(..., description="Musteriye veya analiste gorunen kisa ozet")
    primary_recommendation: LocalizedText | None = Field(
        default=None,
        description="Sayisal ve customer-action odakli birincil onerme metni",
    )
    institution_condition: LocalizedText | None = Field(
        default=None,
        description="Kurum veya offer tarafli kosulun ayri callout metni",
    )
    why_this_matters: LocalizedText = Field(..., description="Adimin neden onemli oldugunu aciklar")
    expected_outcome: LocalizedText = Field(..., description="Beklenen sonucu ozetler")
    what_happens_if_done: LocalizedText = Field(..., description="Adim yapilirsa beklenen durum")
    what_happens_if_not_done: LocalizedText = Field(..., description="Adim yapilmazsa beklenen durum")
    feasibility_outcome_label: LocalizedText | None = Field(
        default=None,
        description="Business-safe feasibility outcome etiketi",
    )
    difficulty_label: LocalizedText | None = Field(
        default=None,
        description="Business-safe aksiyon zorluk etiketi",
    )
    follow_through_note: LocalizedText | None = Field(
        default=None,
        description="Kisa ve non-jargon takip notu",
    )
    action_timing_hint: LocalizedText | None = Field(
        default=None,
        description="Opsiyonel zamanlama ipucu",
    )
    offer_narrative: OfferNarrative | None = Field(
        default=None,
        description="Offer-bearing adimlar icin ayri narrative katmani",
    )


class RoadmapCheckpointNarrative(BaseModel):
    """
    Checkpoint seviyesinde product-facing beklenti ve review semantigi.
    """

    checkpoint_id: str = Field(..., description="Raw checkpoint ile narrative checkpoint arasindaki stabil bag")
    week: int = Field(..., ge=1, description="Checkpoint haftasi")
    expected_state: LocalizedText = Field(..., description="Bu noktada beklenen durum")
    success_condition: LocalizedText = Field(..., description="Success kosulu")
    failure_implication: LocalizedText = Field(..., description="Failure durumunda anlam")
    review_action: LocalizedText | None = Field(
        default=None,
        description="Opsiyonel sonraki review aksiyonu",
    )


class RoadmapReasonNarrative(BaseModel):
    """
    Principal risk reason'lar icin product-facing sentence layer.
    """

    reason_code: str = Field(..., description="Stabil internal reason code")
    reason_title: LocalizedText = Field(..., description="Kisa reason basligi")
    reason_description: LocalizedText = Field(..., description="Reason aciklamasi")
    remediation_hint: LocalizedText = Field(..., description="Iyilestirme ipucu")
    reason_severity: Literal["low", "moderate", "high"] | None = Field(
        default=None,
        description="Opsiyonel severity etiketi",
    )


class RoadmapTechnicalReveal(BaseModel):
    """
    Varsayilan gorunum arkasinda acilan teknik izlenebilirlik katmani.
    """

    feature_changes: list[dict[str, Any]] = Field(default_factory=list, description="Step-level feature degisim kayitlari")
    primary_numeric_targets: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Step-level primary numeric target truth set",
    )
    explainability_reasons: list[dict[str, Any]] = Field(default_factory=list, description="Reason ve katkilar")
    constraints_applied: list[dict[str, Any]] = Field(default_factory=list, description="Constraint ve repair trace kayitlari")
    approval_dependencies: list[dict[str, Any]] = Field(default_factory=list, description="Onay veya kabul bagimliliklari")
    diagnostic_flags: list[str] = Field(default_factory=list, description="Plan veya aksiyon diagnostic flag'leri")
    execution_details: dict[str, Any] = Field(
        default_factory=dict,
        description="Difficulty ve execution truth'unun technical-density ozet katmani",
    )
    confidence_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Narrative confidence etiketine giren ham sinyaller",
    )
    decision_details: dict[str, Any] = Field(
        default_factory=dict,
        description="Business-facing narrative'in dayandigi final decision payload",
    )
    narrative_confidence_label: Literal["high", "moderate", "low"] | None = Field(
        default=None,
        description="UI default gorunumunde kullanilabilecek confidence etiketi",
    )
    narrative_confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Opsiyonel ham narrative confidence skoru",
    )


class RoadmapExecutiveSummary(BaseModel):
    """
    Tek musteri yuzeyleri icin hizli okunabilir executive summary contract'i.
    """

    headline: LocalizedText | None = Field(default=None, description="Opsiyonel headline")
    summary_line: LocalizedText | None = Field(default=None, description="Opsiyonel supporting line")
    risk_start: NarrativeCard = Field(..., description="Baslangic riskinin business-facing yorumu")
    recommended_path: NarrativeCard = Field(..., description="Onerilen yolun kisa tarifi")
    offer_status: NarrativeCard = Field(..., description="Teklif durumunun business-facing yorumu")
    checkpoint_4w_summary: NarrativeCard = Field(..., description="4 haftalik checkpoint ozeti")
    expected_result: NarrativeCard = Field(..., description="Beklenen sonuc")
    follow_through_readiness: NarrativeCard | None = Field(
        default=None,
        description="Planin business-safe follow-through readiness karti",
    )
    decision_view: NarrativeCard = Field(..., description="Karar gorunumunun business-facing etiketi")
    time_to_readiness: NarrativeCard = Field(..., description="Hazirlik zaman cizgisi")
    narrative_confidence: NarrativeCard = Field(..., description="Narrative confidence ozet karti")


class CustomerRoadmapNarrative(BaseModel):
    """
    Raw roadmap truth'un yaninda tasinan translated narrative layer.
    """

    executive_summary: RoadmapExecutiveSummary = Field(..., description="Varsayilan gorunum ozet katmani")
    steps: list[RoadmapStepNarrative] = Field(default_factory=list, description="Step-level narrative kayitlari")
    checkpoints: list[RoadmapCheckpointNarrative] = Field(
        default_factory=list,
        description="Checkpoint-level narrative kayitlari",
    )
    reasons: list[RoadmapReasonNarrative] = Field(default_factory=list, description="Principal reason sentence layer")
    technical_reveal: RoadmapTechnicalReveal = Field(
        default_factory=RoadmapTechnicalReveal,
        description="Istege bagli teknik reveal katmani",
    )


class OperatorPacketBlocker(BaseModel):
    """
    Operator short-view blocker item.
    """

    blocker_code: str = Field(..., description="Stable blocker code for aggregation and tracing")
    blocker_title: LocalizedText = Field(..., description="Short blocker title")
    blocker_detail: LocalizedText = Field(..., description="Business-readable blocker detail")
    driver_key: str | None = Field(default=None, description="Related decision driver key when available")


class OperatorPacketAction(BaseModel):
    """
    Operator short-view recommended action row.
    """

    step_id: str = Field(..., description="Stable link to the roadmap step")
    action_key: str | None = Field(default=None, description="Linked semantic action key")
    action_summary: LocalizedText = Field(..., description="Business-readable action summary")
    institution_condition: LocalizedText | None = Field(
        default=None,
        description="Separate institution-side condition callout when relevant",
    )
    timing_hint: LocalizedText | None = Field(default=None, description="Optional timing hint")
    blocker_codes: list[str] = Field(
        default_factory=list,
        description="Blockers that this action is intended to address",
    )


class OperatorPacketShortView(BaseModel):
    """
    Fast operator-facing customer review surface.
    """

    decision_status: RoadmapDecisionStatus = Field(..., description="Business-visible decision state")
    decision_reason_summary: str = Field(..., description="Owned one-line decision summary")
    decision_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional low-prominence decision confidence score",
    )
    top_blockers: list[OperatorPacketBlocker] = Field(
        default_factory=list,
        description="Top blockers keeping the customer from a better state today",
    )
    next_best_actions: list[OperatorPacketAction] = Field(
        default_factory=list,
        description="Concrete next actions traced back to blockers",
    )
    expected_readiness: DecisionExpectedReadiness = Field(..., description="Owned readiness label")
    expected_readiness_note: LocalizedText | None = Field(
        default=None,
        description="Business-readable interpretation of the readiness label",
    )
    recommendation_sanity_flag: bool = Field(
        default=False,
        description="Whether the selected numeric recommendation carries a manual-review note",
    )
    recommendation_sanity_note: LocalizedText | None = Field(
        default=None,
        description="Low-prominence manual-review note for numeric recommendations",
    )
    outcome_rule_note: LocalizedText | None = Field(
        default=None,
        description="Analysis-only offer/readiness outcome-rule note kept separate from selected truth",
    )
    upgrade_condition: str | None = Field(
        default=None,
        description="What would move the decision upward",
    )
    offer_state: LocalizedText | None = Field(
        default=None,
        description="Business-safe institution-offer state",
    )
    downside_risk: LocalizedText | None = Field(
        default=None,
        description="Soft but honest downside-risk note",
    )
    technical_detail_available: bool = Field(
        default=False,
        description="Whether a technical appendix is available for this packet",
    )


class OperatorPacketTechnicalAppendix(BaseModel):
    """
    Same-artifact technical appendix for operator traceability.
    """

    decision_status_internal: RoadmapDecisionStatusInternal = Field(
        ...,
        description="Internal decision state kept out of default short view",
    )
    decision_reason_primary: DecisionReasonPrimary | None = Field(
        default=None,
        description="Primary structured decision reason code",
    )
    rejection_type: DecisionRejectionType | None = Field(
        default=None,
        description="Rejection subtype when relevant",
    )
    conditional_type: DecisionConditionalType | None = Field(
        default=None,
        description="Conditional subtype when relevant",
    )
    decision_reason_drivers: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Owned numeric drivers behind the current decision",
    )
    recommendation_validity_codes: list[str] = Field(
        default_factory=list,
        description="Selected-plan numeric recommendation validity codes",
    )
    recommendation_warning_action_count: int = Field(
        default=0,
        ge=0,
        description="Number of selected-plan actions carrying numeric warning status",
    )
    contract_health: dict[str, Any] = Field(
        default_factory=dict,
        description="Derived contract-health slice relevant for operator debugging",
    )
    decision_gate_trace: dict[str, Any] = Field(
        default_factory=dict,
        description="Compact gate trace for debugging and analyst review",
    )
    selection_outcome: str | None = Field(
        default=None,
        description="Selected-surface outcome trace for winner-vs-empty-state rendering",
    )
    selection_stage: str | None = Field(
        default=None,
        description="Selected-surface stage trace for integrity debugging",
    )
    selected_plan_status_internal: RoadmapDecisionStatusInternal | None = Field(
        default=None,
        description="Technical selected-plan status kept separate from consumer decision status",
    )
    selected_recommendation_source: str | None = Field(
        default=None,
        description="Projection owner source for the selected recommendation surface",
    )
    selected_recommendation_projection_version: str | None = Field(
        default=None,
        description="Projection version used to derive selected recommendation text",
    )
    selected_action_count: int = Field(
        default=0,
        ge=0,
        description="Selected-plan action count carried into the consumer-safe overlay",
    )
    selected_outcome_rule_applied: bool = Field(
        default=False,
        description="Whether an analysis-only outcome rule would move this case under the recommended profile",
    )
    selected_outcome_rule_profile_version: str | None = Field(
        default=None,
        description="Recommended analysis-only outcome-rule profile version when applicable",
    )
    selected_outcome_rule_source: str | None = Field(
        default=None,
        description="Offer/readiness rule source behind the analysis-only movement note",
    )
    selected_outcome_rule_transition: str | None = Field(
        default=None,
        description="One-step movement trace for the analysis-only outcome rule",
    )
    active_driver_count: int = Field(
        default=0,
        ge=0,
        description="Rendered packet icin aktif structured driver sayisi",
    )
    blocker_render_source: str | None = Field(
        default=None,
        description="Blocker rendering source: driver | primary_reason | empty_state | suppressed",
    )
    action_render_source: str | None = Field(
        default=None,
        description="Action rendering source: selected_projection | empty_state | suppressed",
    )
    readiness_render_mode: str | None = Field(
        default=None,
        description="Readiness note rendering mode for packet coherence debugging",
    )
    fallback_blocker_suppressed: bool = Field(
        default=False,
        description="Whether a fallback blocker candidate was intentionally suppressed",
    )
    packet_coherence_codes: list[str] = Field(
        default_factory=list,
        description="Additive packet coherence diagnostics",
    )


class OperatorReviewPacket(BaseModel):
    """
    Derived per-customer operator review artifact.
    """

    packet_version: str = Field(default="v2.1_phase_43", description="Operator packet contract version")
    decision_id: str = Field(..., description="Owned decision snapshot id")
    decision_policy_version: str = Field(..., description="Owned decision-policy version")
    customer_id: str = Field(..., description="Customer id carried into the packet")
    best_plan_id: str | None = Field(default=None, description="Best-plan link for traceability")
    short_view: OperatorPacketShortView = Field(..., description="Fast operator-facing review layer")
    technical_appendix: OperatorPacketTechnicalAppendix = Field(
        ...,
        description="Technical appendix that stays within the same artifact",
    )


# ------------------------------------------------------------------ #
# PlanRecord — recourse planı
# ------------------------------------------------------------------ #
class PlanRecord(BaseModel):
    """
    Tek bir recourse planını temsil eder.

    Her müşteri için 3 horizon × 3 strateji = 9 plan üretilir.
    Bu şema her planın tam içeriğini, skorunu ve güvenlik durumunu tutar.

    Alan açıklamaları
    -----------------
    horizon_months  : Planın süresi (3, 6 veya 12 ay)
    strategy        : Plan stratejisi (conservative / balanced / aggressive)
    actions         : Sıralı aksiyon listesi
    predicted_pd    : Aksiyonlar sonrası tahmini PD: f(x', z_t)
    ci_low/ci_high  : Bootstrap CI bandı (feasibility dışı güvensizlik)
    alpha_used      : Hesaplamada kullanılan alpha (normal: 0.05, stres: 0.01)
    risk_margin     : tau - ci_high (pozitif → güvenli)
    reliability     : Şok senaryolarında geçme oranı [0,1]
    causal_penalty  : CausalPenalty(A; G) — nedensel tutarsızlık cezası
    score           : Nihai plan skoru (formül: Bölüm 5.3)
    status          : APPROVED | NEEDS_REVIEW | REJECTED
    """

    plan_id: str = Field(..., description="Benzersiz plan ID")
    customer_id: str = Field(..., description="Müşteri ID")
    run_id: str = Field(..., description="Bu planı üreten run_id")
    created_at: datetime = Field(default_factory=utc_now)

    horizon_months: Literal[3, 6, 12] = Field(..., description="Planlama ufku (ay)")
    strategy: Literal["conservative", "balanced", "aggressive"] = Field(
        ..., description="Recourse stratejisi"
    )
    actions: list[PlanAction] = Field(default_factory=list, description="Aksiyon listesi")
    phases: list[TrajectoryPhase] = Field(
        default_factory=list,
        description="Canonical cok-fazli trajectory katmani; actions[] compatibility icin korunur",
    )
    trajectory_checkpoints: list[TrajectoryCheckpoint] = Field(
        default_factory=list,
        description="Canonical 4w/12w/24w trajectory checkpoint listesi",
    )
    plan_source: PlanSource | None = Field(
        default=None,
        description="Canonical planner/source provenance lane",
    )
    path_id: str | None = Field(
        default=None,
        description="Deterministic grouped-path identifier for this plan",
    )
    path_type: PathType | None = Field(
        default=None,
        description="Deterministic grouped-path type derived from canonical ownership semantics",
    )
    path_signature: str | None = Field(
        default=None,
        description="Stable grouped-path signature for duplicate-resistant identity",
    )
    path_rankable_flag: bool = Field(
        default=False,
        description="Whether the plan belongs to a rankable actionable grouped path",
    )
    path_representative_flag: bool = Field(
        default=False,
        description="Whether the plan is the representative of its grouped path",
    )
    path_rank: int | None = Field(
        default=None,
        ge=1,
        description="Global rank of the grouped path among rankable representatives",
    )
    contender_bucket: PlanContenderBucket | None = Field(
        default=None,
        description="Planner-quality contender bucket classification",
    )
    empty_candidate_reason: PlanEmptyReason | None = Field(
        default=None,
        description="Diagnostic reason when a contender is filtered as empty",
    )
    approval_shell_only_flag: bool = Field(
        default=False,
        description="Plan sadece approval-dependent shell olarak mi tasiniyor",
    )
    offer_maturity: OfferMaturity | None = Field(
        default=None,
        description="Planner-level offer maturity truth for candidate quality",
    )
    recommendation_validity_status: RecommendationValidityStatus | None = Field(
        default=None,
        description="Canonical plan-level numeric recommendation validity status",
    )
    recommendation_invalid_action_count: int = Field(
        default=0,
        ge=0,
        description="Count of actions with hard-invalid numeric recommendation status",
    )
    recommendation_warning_action_count: int = Field(
        default=0,
        ge=0,
        description="Count of actions with numeric warning status",
    )
    recommendation_validity_codes: list[str] = Field(
        default_factory=list,
        description="Union of numeric recommendation validity codes across actions",
    )
    recommendation_sanity_flag: bool = Field(
        default=False,
        description="Whether the selected numeric recommendation should surface a manual-review note",
    )
    recommendation_warning_penalty: float = Field(
        default=0.0,
        ge=0.0,
        description="Total warning penalty derived from numeric recommendation validity",
    )
    rule_annotation_complete: bool = Field(
        default=False,
        description="Rule-lane typed-action annotation completeness gate",
    )
    rule_semantic_quality_status: RecommendationValidityStatus | None = Field(
        default=None,
        description="Lane-specific institution/rule semantic contender-worthiness status",
    )
    rule_semantic_quality_codes: list[str] = Field(
        default_factory=list,
        description="Lane-specific institution/rule semantic quality and completeness codes",
    )
    rule_contender_eligible: bool = Field(
        default=False,
        description="Whether the rule candidate may enter planner contention",
    )
    rule_semantic_warning_penalty: float = Field(
        default=0.0,
        ge=0.0,
        description="Bounded additive planner penalty for institution/rule semantic warnings",
    )
    rule_quality_gate_version: str | None = Field(
        default=None,
        description="Version string for the institution/rule quality gate contract",
    )
    dice_backend_class: DiceBackendClass | None = Field(
        default=None,
        description="DICE backend provenance class: native | heuristic_fallback | skipped",
    )
    dice_annotation_complete: bool = Field(
        default=False,
        description="DICE typed-action annotation completeness gate",
    )
    dice_semantic_quality_status: RecommendationValidityStatus | None = Field(
        default=None,
        description="Lane-specific DICE semantic contender-worthiness status",
    )
    dice_semantic_quality_codes: list[str] = Field(
        default_factory=list,
        description="Lane-specific DICE semantic quality and completeness codes",
    )
    dice_contender_eligible: bool = Field(
        default=False,
        description="Whether the DICE candidate may enter planner contention",
    )
    dice_semantic_warning_penalty: float = Field(
        default=0.0,
        ge=0.0,
        description="Bounded additive planner penalty for DICE semantic warnings",
    )
    dice_quality_gate_version: str | None = Field(
        default=None,
        description="Version string for the DICE quality gate contract",
    )

    # Risk metrikleri
    predicted_pd: float | None = Field(None, ge=0.0, le=1.0, description="f(x', z_t)")
    ci_low: float | None = Field(None, description="Bootstrap CI alt band")
    ci_high: float | None = Field(None, description="Bootstrap CI üst band")
    alpha_used: float | None = Field(None, description="Güven seviyesi alpha")
    risk_margin: float | None = Field(
        None, description="tau - ci_high; pozitif = güvenli"
    )
    reliability: float | None = Field(
        None, ge=0.0, le=1.0, description="Şok senaryosu geçme oranı"
    )
    robust_score: float | None = Field(None, description="Robust objective ile hesaplanan plan skoru")
    robust_margin: float | None = Field(None, description="Robust anchor margin: tau - robust_anchor_pd")
    robust_anchor_pd: float | None = Field(None, ge=0.0, le=1.0, description="Worst/CVaR stres PD")
    robust_method: str | None = Field(None, description="Robust objective metodu: worst_case | cvar")
    robust_worst_risk_margin: float | None = Field(None, description="Stres senaryolarinda en dusuk margin")
    causal_penalty: float | None = Field(None, ge=0.0, description="Nedensel ceza puanı")
    score: float | None = Field(None, description="Nihai plan skoru")
    constraint_status: PlanConstraintStatus = Field(
        default="valid",
        description="Action dependency/conflict katmanindan gelen plan-level durum",
    )
    constraint_reason: str | None = Field(
        default=None,
        description="Action constraint katmaninin reason-coded ozet gerekcesi",
    )
    constraint_trace: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Repair, conflict ve approval-pending trace olaylari",
    )
    plan_execution_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Plan seviyesinde toplanmis gerceklesme olasiligi",
    )
    approval_dependent_plan_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Approval-dependent veya provisional branch'ler icin ayri plan-level gerceklesme olasiligi",
    )
    mean_action_execution_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Executable aksiyonlar icin ortalama aksiyon uygulanma olasiligi",
    )
    mean_approval_dependent_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Approval-dependent aksiyonlar icin ortalama onay/gerceklesme olasiligi",
    )
    mean_group_difficulty_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Grouped action truth sonrasi ortalama plan zorluk skoru",
    )
    peak_group_difficulty_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Plan icindeki en zor grouped action skorunun ozeti",
    )
    dominant_difficulty_label: DifficultyLabel | None = Field(
        default=None,
        description="Plan icindeki baskin zorluk etiketi",
    )
    follow_through_readiness_label: ReadinessLabel | None = Field(
        default=None,
        description="Planin default business gorunumu icin follow-through readiness etiketi",
    )
    nominal_pd_improvement: float | None = Field(
        default=None,
        description="Davranis modeli olmadan planin nominal PD iyilesmesi",
    )
    expected_pd_improvement: float | None = Field(
        default=None,
        description="Plan execution probability ile agirliklandirilmis beklenen PD iyilesmesi",
    )
    executable_action_count: int = Field(
        default=0,
        ge=0,
        description="Normal executable aksiyon sayisi",
    )
    executable_action_group_count: int = Field(
        default=0,
        ge=0,
        description="Composite aggregation sonrasi executable action group sayisi",
    )
    approval_pending_action_count: int = Field(
        default=0,
        ge=0,
        description="Ordinary winner scoring disinda kalan approval-dependent aksiyon sayisi",
    )
    offer_plan: bool = Field(
        default=False,
        description="Plan en az bir offer-bearing institutional aksiyon tasiyor mu",
    )
    rankable_offer_count: int = Field(
        default=0,
        ge=0,
        description="Ordinary ranking'e girebilen explicit offer branch sayisi",
    )
    offer_acceptance_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Rankable offer-bearing plan icin kurum teklifinin kabul edilme olasiligi",
    )
    combined_plan_realization_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="plan_execution_probability ile offer_acceptance_probability'nin bileşik gerceklesme olasiligi",
    )
    expected_recovery_proxy: float | None = Field(
        default=None,
        description="Offer optimization ranking icin governance-safe expected recovery proxy skoru",
    )
    approval_rate_proxy_delta: float | None = Field(
        default=None,
        description="Offer policy icin approval-rate proxy delta tahmini",
    )
    default_rate_90d_proxy_delta: float | None = Field(
        default=None,
        description="Offer policy icin 90d default-rate proxy delta tahmini",
    )
    avg_margin_90d_proxy_delta: float | None = Field(
        default=None,
        description="Offer policy icin 90d average margin proxy delta tahmini",
    )
    governance_safe_offer: bool = Field(
        default=False,
        description="Offer-bearing plan governance ve trajectory stack'i icinde safe gorunuyor mu",
    )
    dominant_offer_type: str | None = Field(
        default=None,
        description="Plan icindeki baskin offer tipi",
    )
    offer_policy_arm: str | None = Field(
        default=None,
        description="Plan seviyesinde baskin offer policy arm",
    )
    offer_family: str | None = Field(
        default=None,
        description="Plan seviyesinde baskin offer family",
    )
    offer_scoring_profile: str | None = Field(
        default=None,
        description="Plan seviyesinde baskin offer scoring profile",
    )
    term_generation_rule: str | None = Field(
        default=None,
        description="Plan seviyesinde baskin offer term generation rule",
    )
    trajectory_status: Literal["on_track", "needs_replan", "degraded"] = Field(
        default="on_track",
        description="Hybrid trajectory transition durumu",
    )
    current_phase: str | None = Field(
        default=None,
        description="Trajectory'nin su anki canonical fazi",
    )
    next_review_week: int | None = Field(
        default=None,
        ge=1,
        description="Bir sonraki canonical trajectory review haftasi",
    )
    phase_transition_reason: str | None = Field(
        default=None,
        description="Son phase transition veya review sonucunun reason code'u",
    )
    replanned_from_phase: str | None = Field(
        default=None,
        description="Varsa trajectory'nin replan edildigi onceki faz",
    )
    trajectory_policy_label: Literal["stabilize_first", "balanced_progress", "long_horizon_heavy"] | None = Field(
        default=None,
        description="Phase-aware optimizer tarafindan verilen policy label",
    )
    trajectory_policy_score: float | None = Field(
        default=None,
        description="Phase-aware optimizer tarafindan hesaplanan trajectory skoru",
    )

    status: Literal["APPROVED", "NEEDS_REVIEW", "REJECTED", "PENDING"] = Field(
        default="PENDING", description="Güvenlik kapısı sonucu"
    )
    status_reason: str | None = Field(None, description="Status gerekçesi")

    @field_validator("horizon_months")
    @classmethod
    def validate_horizon(cls, v: int) -> int:
        if v not in (3, 6, 12):
            raise ValueError(f"horizon_months {v} geçersiz — yalnızca 3, 6, 12 kabul edilir.")
        return v


class RecoursePathRecord(BaseModel):
    """
    Deterministic grouped-path record built on top of already-validated plan objects.
    """

    path_id: str = Field(..., description="Deterministic grouped-path identifier")
    customer_id: str = Field(..., description="Customer identifier")
    path_type: PathType = Field(..., description="Canonical grouped-path type")
    path_signature: str = Field(..., description="Stable grouped-path signature")
    rankable_flag: bool = Field(
        default=False,
        description="Whether the path contains at least one actionable contender",
    )
    path_rank: int | None = Field(
        default=None,
        ge=1,
        description="Global rank among rankable path representatives",
    )
    representative_plan_id: str | None = Field(
        default=None,
        description="Representative plan selected for this path",
    )
    representative_plan_source: PlanSource | None = Field(
        default=None,
        description="Source lane of the representative plan",
    )
    representative_contender_bucket: PlanContenderBucket | None = Field(
        default=None,
        description="Planner-quality contender bucket of the representative plan",
    )
    member_plan_ids: list[str] = Field(
        default_factory=list,
        description="Plan ids grouped into this path",
    )
    member_plan_count: int = Field(
        default=0,
        ge=0,
        description="Count of plans grouped into this path",
    )
    member_source_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Per-source counts among grouped plan members",
    )
    action_keys: list[str] = Field(
        default_factory=list,
        description="Normalized canonical action keys defining the path thesis",
    )
    action_owners: list[str] = Field(
        default_factory=list,
        description="Normalized action-owner mix defining the path thesis",
    )
    action_categories: list[str] = Field(
        default_factory=list,
        description="Normalized action-category mix defining the path thesis",
    )
    primary_metric_keys: list[str] = Field(
        default_factory=list,
        description="Primary numeric target metric keys defining the path thesis",
    )
    offer_plan: bool = Field(
        default=False,
        description="Whether the grouped path depends on institution-side offer semantics",
    )
    offer_maturity: OfferMaturity | None = Field(
        default=None,
        description="Dominant offer maturity truth for the grouped path",
    )
    selected_path_flag: bool = Field(
        default=False,
        description="Whether this path contains the selected winner plan",
    )
    customer_summary: LocalizedText | None = Field(
        default=None,
        description="Localized customer-facing path summary rendered from representative-plan truth",
    )
    operator_summary: LocalizedText | None = Field(
        default=None,
        description="Localized operator-facing path summary rendered from representative-plan truth",
    )
    render_version: str | None = Field(
        default=None,
        description="Optional render-version traceability tag for the path summary contract",
    )


# ------------------------------------------------------------------ #
# ModelRunRecord — model çalışma kaydı
# ------------------------------------------------------------------ #
class ModelRunRecord(BaseModel):
    """
    Bir model training veya prediction çalışmasının audit kaydı.

    Hangi model versiyonu hangi metriklerle train edildi?
    Hangi tarihte hangi threshold kullanıldı?
    Bu sorular audit sırasında bu kayıttan cevaplanır.
    """

    run_id: str = Field(..., description="RunContext.run_id ile eşleşir")
    model_version: str = Field(..., description="Örn: 'v1.0.0' veya run_id")
    run_type: Literal["train", "evaluate", "predict", "recourse", "retrain"] = Field(
        ..., description="Bu çalışmanın türü"
    )
    created_at: datetime = Field(default_factory=utc_now)
    config_hash: str = Field(..., description="Kullanılan config'in SHA-256 hash'i")
    metrics: dict[str, Any] = Field(default_factory=dict, description="AUC, F1, ECE vb.")
    tau_used: float | None = Field(None, description="Bu çalışmada kullanılan karar eşiği")
    notes: str | None = Field(None, description="Opsiyonel açıklama")


class DecisionOutcomeRecord(BaseModel):
    """
    Decision seviyesinde gecikmeli outcome kaydi.
    """

    decision_id: str = Field(..., description="Tekil karar kimligi")
    run_id: str = Field(..., description="Kararin uretildigi run")
    customer_id: str = Field(..., description="Musteri kimligi")
    policy_arm: str = Field(default="control", description="control | treatment")
    policy_arm_profile: dict[str, str] = Field(
        default_factory=dict,
        description="Policy arm'in offer family / scoring profile / term rule ozet profili",
    )
    candidate_set_id: str = Field(default="", description="Secim yapilan candidate set kimligi")
    selected_plan_id: str = Field(default="", description="Winner veya secilen plan kimligi")
    selected_plan_status: str = Field(default="", description="Winner plan durumu")
    selected_offer_type: str | None = Field(default=None, description="Secilen offer tipi varsa")
    selection_propensity: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Secilen policy / plan arm'inin propensity degeri",
    )
    propensity_source: str = Field(
        default="deterministic_fallback",
        description="Propensity'nin kaynagi: randomized | heuristic | deterministic_fallback",
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Karari ve secilen plani aciklayan compact reason code listesi",
    )
    recommended_plan_flag: bool = Field(default=False, description="Karar icin loggable bir recommendation secildi mi")
    selected_plan_policy_label: str | None = Field(
        default=None,
        description="Trajectory policy label gibi kisa plan etiketi",
    )
    trajectory_status: str | None = Field(
        default=None,
        description="Planin trajectory durumu: on_track | needs_replan | degraded",
    )
    decision_status: str = Field(default="UNKNOWN", description="APPROVED | NEEDS_REVIEW | REJECTED | UNKNOWN")
    approved: bool = Field(default=False, description="Karar sonucu onaylandi mi")
    predicted_pd: float | None = Field(default=None, ge=0.0, le=1.0)
    plan_execution_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    approval_dependent_plan_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    offer_acceptance_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    combined_plan_realization_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    action_completed: bool | None = Field(default=None, description="Aksiyonlar gercekte tamamlandi mi")
    offer_accepted: bool | None = Field(default=None, description="Institutional offer kabul edildi mi")
    observed_payment_ratio_90d: float | None = Field(
        default=None,
        ge=0.0,
        description="90 gun icinde beklenen odemenin gerceklesen orani",
    )
    observed_recovery_amount_90d: float | None = Field(
        default=None,
        description="90 gun icindeki gerceklesen recovery tutari",
    )
    observed_default_30d: int | None = Field(default=None, ge=0, le=1)
    observed_default_60d: int | None = Field(default=None, ge=0, le=1)
    observed_default_90d: int | None = Field(default=None, ge=0, le=1)
    observed_margin_90d: float | None = Field(default=None)
    observed_at: datetime = Field(default_factory=utc_now)
