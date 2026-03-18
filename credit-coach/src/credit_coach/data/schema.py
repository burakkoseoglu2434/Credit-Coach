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

from pydantic import BaseModel, Field, field_validator

from credit_coach.utils.time import utc_now


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
    action_class: Literal["behavioral", "structural", "institutional"] | None = Field(
        default=None,
        description="Aksiyon sinifi: behavioral | structural | institutional",
    )
    action_title: str | None = Field(default=None, description="Aksiyonun okunabilir basligi")
    action_group_id: str | None = Field(
        default=None,
        description="Composite aksiyonlari ayni grup altinda toplamak icin stabil grup kimligi",
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
    prerequisite_tags: list[str] = Field(
        default_factory=list,
        description="Bu aksiyonun bagli oldugu prerequisite etiketleri",
    )
    conflict_tags: list[str] = Field(
        default_factory=list,
        description="Bu aksiyonun ayni planda conflict yaratabilecegi etiketler",
    )
    action_status: Literal["valid", "clipped", "provisional", "invalid", "repair_dropped"] | None = Field(
        default="valid",
        description="Action realism veya constraint islemlerinden sonraki durum",
    )
    action_status_reason: str | None = Field(
        default=None,
        description="Aksiyon statusu icin reason code veya aciklama",
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

    week: int = Field(..., ge=1, description="Checkpoint haftasi")
    month: int = Field(..., ge=1, description="Checkpoint ay eslesmesi")
    phase_id: Literal["phase_1_stabilize", "phase_2_build", "phase_3_optimize"] = Field(
        ...,
        description="Checkpoint'in bagli oldugu canonical faz",
    )
    checkpoint_label: str | None = Field(default=None, description="Kisa checkpoint etiketi")
    predicted_pd: float | None = Field(default=None, ge=0.0, le=1.0, description="Checkpoint PD tahmini")
    pd_delta_vs_base: float | None = Field(default=None, description="Base PD'ye gore iyilesme")
    gate_pass_estimate: int = Field(default=0, ge=0, le=1, description="Checkpoint gate-pass tahmini")
    checkpoint_priority: int = Field(default=0, ge=0, description="4w > 12w > 24w oncelik sirasi")


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
    why_this_matters: LocalizedText = Field(..., description="Adimin neden onemli oldugunu aciklar")
    expected_outcome: LocalizedText = Field(..., description="Beklenen sonucu ozetler")
    what_happens_if_done: LocalizedText = Field(..., description="Adim yapilirsa beklenen durum")
    what_happens_if_not_done: LocalizedText = Field(..., description="Adim yapilmazsa beklenen durum")
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
    explainability_reasons: list[dict[str, Any]] = Field(default_factory=list, description="Reason ve katkilar")
    constraints_applied: list[dict[str, Any]] = Field(default_factory=list, description="Constraint ve repair trace kayitlari")
    approval_dependencies: list[dict[str, Any]] = Field(default_factory=list, description="Onay veya kabul bagimliliklari")
    diagnostic_flags: list[str] = Field(default_factory=list, description="Plan veya aksiyon diagnostic flag'leri")
    confidence_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Narrative confidence etiketine giren ham sinyaller",
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
    constraint_status: Literal["valid", "repaired", "provisional", "invalid"] = Field(
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
    mean_action_execution_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Executable aksiyonlar icin ortalama aksiyon uygulanma olasiligi",
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
