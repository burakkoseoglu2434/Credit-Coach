"""
storage/models.py
=================
SQLAlchemy ORM tabloları — ürün state veritabanının şeması.

Neden var?
----------
AGENT GUIDE kural #4: LendingClub eğitim verisi dosyada kalır;
ürün durumu (müşteri snapshot'ları, planlar, model runs, audit)
bu tablolarda saklanır.

Tablolar
--------
CustomerSnapshotORM  → x_t: müşteri feature vektörü + risk skoru
MacroSnapshotORM     → z_t: makro ekonomik durum + MSI
PlanRecordORM        → recourse planı (aksiyonlar JSON olarak saklanır)
ModelRunORM          → model training/prediction audit kaydı
AuditEventORM        → zincirli audit event kaydı (event_hash / prev_hash)
"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from credit_coach.storage.db import Base
from credit_coach.utils.time import utc_now_naive


# ------------------------------------------------------------------ #
# CustomerSnapshotORM
# ------------------------------------------------------------------ #
class CustomerSnapshotORM(Base):
    """
    Müşterinin belirli bir andaki 48-feature vektörü ve risk skoru.

    features_json sütunu: {"loan_amnt": 15000, "dti": 28.0, ...}
    şeklinde JSON string olarak saklanır (SQLite JSON desteği sınırlı).
    """

    __tablename__ = "customer_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    features_json: Mapped[str] = mapped_column(Text, nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)

    # İlişki: bu snapshot için üretilmiş planlar
    plans: Mapped[list["PlanRecordORM"]] = relationship(
        "PlanRecordORM",
        back_populates="snapshot",
        cascade="all, delete-orphan",
    )

    @property
    def features(self) -> dict:
        """features_json'u Python dict'e dönüştürür."""
        return json.loads(self.features_json)

    @features.setter
    def features(self, value: dict) -> None:
        self.features_json = json.dumps(value, ensure_ascii=False)

    def __repr__(self) -> str:
        return (
            f"<CustomerSnapshot id={self.id} customer={self.customer_id} "
            f"date={self.snapshot_date:%Y-%m-%d} risk={self.risk_score:.3f}>"
        )


# ------------------------------------------------------------------ #
# MacroSnapshotORM
# ------------------------------------------------------------------ #
class MacroSnapshotORM(Base):
    """
    Belirli bir tarihteki makro ekonomik durum.

    z_t olarak başvurulan bu kayıt; risk threshold tau_t ve
    alpha(z_t) hesaplamalarında kullanılır.
    """

    __tablename__ = "macro_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    interest_rate: Mapped[float] = mapped_column(Float, nullable=False)
    unemployment_rate: Mapped[float] = mapped_column(Float, nullable=False)
    gdp_growth: Mapped[float] = mapped_column(Float, nullable=False)
    inflation_rate: Mapped[float] = mapped_column(Float, nullable=False)
    credit_spread: Mapped[float] = mapped_column(Float, nullable=False)
    macro_stress_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="mock")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)

    def __repr__(self) -> str:
        return (
            f"<MacroSnapshot date={self.snapshot_date:%Y-%m-%d} "
            f"MSI={self.macro_stress_index}>"
        )


# ------------------------------------------------------------------ #
# PlanRecordORM
# ------------------------------------------------------------------ #
class PlanRecordORM(Base):
    """
    Bir müşteri için üretilmiş recourse planı.

    actions_json sütunu: [{"feature_name": "dti", "target_value": 22, ...}, ...]
    şeklinde JSON string olarak saklanır.

    snapshot_id ile CustomerSnapshotORM'a bağlıdır (foreign key).
    """

    __tablename__ = "plan_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    snapshot_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("customer_snapshots.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)

    horizon_months: Mapped[int] = mapped_column(Integer, nullable=False)
    strategy: Mapped[str] = mapped_column(String(20), nullable=False)
    actions_json: Mapped[str] = mapped_column(Text, default="[]")

    # Risk metrikleri
    predicted_pd: Mapped[float | None] = mapped_column(Float, nullable=True)
    ci_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    ci_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    alpha_used: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    reliability: Mapped[float | None] = mapped_column(Float, nullable=True)
    causal_penalty: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # İlişki
    snapshot: Mapped["CustomerSnapshotORM | None"] = relationship(
        "CustomerSnapshotORM", back_populates="plans"
    )

    @property
    def actions(self) -> list[dict]:
        return json.loads(self.actions_json)

    @actions.setter
    def actions(self, value: list[dict]) -> None:
        self.actions_json = json.dumps(value, ensure_ascii=False)

    def __repr__(self) -> str:
        return (
            f"<PlanRecord plan_id={self.plan_id} customer={self.customer_id} "
            f"h={self.horizon_months}m strategy={self.strategy} status={self.status}>"
        )


# ------------------------------------------------------------------ #
# ModelRunORM
# ------------------------------------------------------------------ #
class ModelRunORM(Base):
    """
    Bir model training / prediction / recourse çalışmasının audit kaydı.

    Bu tablo "model inventory" görevi görür (SR 11-7 ruhu).
    Hangi versiyonun hangi metrikle, hangi config ile train edildiği
    buradan sorgulanır.
    """

    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    run_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, default="{}")
    tau_used: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_champion: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def metrics(self) -> dict:
        return json.loads(self.metrics_json)

    @metrics.setter
    def metrics(self, value: dict) -> None:
        self.metrics_json = json.dumps(value, ensure_ascii=False)

    def __repr__(self) -> str:
        return (
            f"<ModelRun run_id={self.run_id} type={self.run_type} "
            f"version={self.model_version} champion={self.is_champion}>"
        )


# ------------------------------------------------------------------ #
# DecisionOutcomeORM
# ------------------------------------------------------------------ #
class DecisionOutcomeORM(Base):
    """
    Decision seviyesinde gecikmeli outcome kaydi (30/60/90 gun).

    Bu tablo offline recourse KPI ile gercek portfoy sonucunu baglar.
    """

    __tablename__ = "decision_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    run_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    policy_arm: Mapped[str] = mapped_column(String(40), nullable=False, default="control", index=True)
    decision_status: Mapped[str] = mapped_column(String(20), nullable=False, default="UNKNOWN")
    approved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    predicted_pd: Mapped[float | None] = mapped_column(Float, nullable=True)
    observed_default_30d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observed_default_60d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observed_default_90d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observed_margin_90d: Mapped[float | None] = mapped_column(Float, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, index=True)

    def __repr__(self) -> str:
        return (
            f"<DecisionOutcome decision_id={self.decision_id} arm={self.policy_arm} "
            f"approved={self.approved}>"
        )


# ------------------------------------------------------------------ #
# DecisionOutcomeContextORM
# ------------------------------------------------------------------ #
class DecisionOutcomeContextORM(Base):
    """
    Additive companion table for richer decision logging and delayed learning fields.

    The main `decision_outcomes` table stays thin and backward-compatible.
    This table carries the compact learning ledger plus richer delayed outcome context
    without requiring destructive schema changes on the core outcome table.
    """

    __tablename__ = "decision_outcome_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    run_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    candidate_set_id: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    policy_arm_profile_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    selected_plan_id: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    selected_plan_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    selected_offer_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    selection_propensity: Mapped[float | None] = mapped_column(Float, nullable=True)
    propensity_source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reason_codes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    recommended_plan_flag: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    selected_plan_policy_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    trajectory_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    plan_execution_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    offer_acceptance_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    combined_plan_realization_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    action_completed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    offer_accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    observed_payment_ratio_90d: Mapped[float | None] = mapped_column(Float, nullable=True)
    observed_recovery_amount_90d: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive, index=True)

    @property
    def policy_arm_profile(self) -> dict:
        return json.loads(self.policy_arm_profile_json or "{}")

    @policy_arm_profile.setter
    def policy_arm_profile(self, value: dict) -> None:
        self.policy_arm_profile_json = json.dumps(value or {}, ensure_ascii=False)

    @property
    def reason_codes(self) -> list[str]:
        return json.loads(self.reason_codes_json or "[]")

    @reason_codes.setter
    def reason_codes(self, value: list[str]) -> None:
        self.reason_codes_json = json.dumps(value or [], ensure_ascii=False)

    def __repr__(self) -> str:
        return (
            f"<DecisionOutcomeContext decision_id={self.decision_id} "
            f"plan={self.selected_plan_id} propensity={self.selection_propensity}>"
        )


# ------------------------------------------------------------------ #
# DecisionOutcomeRealizationContextORM
# ------------------------------------------------------------------ #
class DecisionOutcomeRealizationContextORM(Base):
    """
    Additive companion table for selected-path realization context.

    Keep v2.5 selected-path and targeting truth available to delayed-outcome
    analysis without mutating the older compact context table in place.
    """

    __tablename__ = "decision_outcome_realization_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    run_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    selected_plan_id: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    selected_path_id: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    selected_path_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    selected_path_movement_strength: Mapped[str | None] = mapped_column(String(40), nullable=True)
    recourse_mode: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    recoverable_flag: Mapped[bool | None] = mapped_column(Boolean, nullable=True, index=True)
    movement_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_reach_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, onupdate=utc_now_naive, index=True)

    def __repr__(self) -> str:
        return (
            f"<DecisionOutcomeRealizationContext decision_id={self.decision_id} "
            f"path={self.selected_path_id} mode={self.recourse_mode}>"
        )


# ------------------------------------------------------------------ #
# AuditEventORM
# ------------------------------------------------------------------ #
class AuditEventORM(Base):
    """
    Zincirlenmis audit event kaydi.

    Her event icin:
    - prev_hash: bir onceki event hash'i (genesis icin None)
    - event_hash: (prev_hash + canonical payload) SHA-256
    """

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, index=True)

    @property
    def payload(self) -> dict:
        return json.loads(self.payload_json)

    @payload.setter
    def payload(self, value: dict) -> None:
        self.payload_json = json.dumps(value, ensure_ascii=False)

    def __repr__(self) -> str:
        return (
            f"<AuditEvent id={self.id} type={self.event_type} "
            f"run_id={self.run_id} hash={self.event_hash[:10]}>"
        )
