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
    approval_pending_semantic_only: bool = Field(
        default=False,
        description="Feature effect'e henuz donusmeyen semantik placeholder institutional aksiyon mu",
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
    decision_status: str = Field(default="UNKNOWN", description="APPROVED | NEEDS_REVIEW | REJECTED | UNKNOWN")
    approved: bool = Field(default=False, description="Karar sonucu onaylandi mi")
    predicted_pd: float | None = Field(default=None, ge=0.0, le=1.0)
    observed_default_30d: int | None = Field(default=None, ge=0, le=1)
    observed_default_60d: int | None = Field(default=None, ge=0, le=1)
    observed_default_90d: int | None = Field(default=None, ge=0, le=1)
    observed_margin_90d: float | None = Field(default=None)
    observed_at: datetime = Field(default_factory=utc_now)
