"""Pure decision function (ADR-004). No clock, randomness, network or file access in here."""

from __future__ import annotations

from credit_coach.contract import (
    HUMAN_REVIEW_COMPLETED,
    ConditionalType,
    DecisionInput,
    InnerStatus,
    InternalDecision,
    InvalidDecisionInput,
    OuterStatus,
    PublicDecision,
    PublicReasonCode,
    ReasonCode,
    RuleId,
    check_invariants,
)
from credit_coach.policy import Policy

_ORDER = {c: i for i, c in enumerate(ReasonCode)}
_PUBLIC = {c.value for c in PublicReasonCode}


def _codes(*codes: ReasonCode) -> tuple[ReasonCode, ...]:
    return tuple(sorted(set(codes), key=_ORDER.__getitem__))


def decide(girdi: DecisionInput, politika: Policy) -> InternalDecision:
    check_invariants(girdi)
    if girdi.politika_surumu != politika.surum:
        raise InvalidDecisionInput(
            f"policy version mismatch: input {girdi.politika_surumu!r} vs policy {politika.surum!r}"
        )
    lo, pt, hi, s = girdi.p_low, girdi.p_point, girdi.p_high, girdi.ham_skor
    thr, band = politika.onay_esigi, politika.band

    hard = politika.ret_esigi is not None and lo > politika.ret_esigi
    near = (lo - band <= thr) and (hi + band >= thr)
    weak = any(a <= s <= b for a, b in politika.zayif_destek_araliklari)
    weak_near = weak and abs(pt - thr) <= politika.zayif_destek_yakinlik_carpani * band

    fired: list[RuleId] = []
    if hard:
        fired.append(RuleId.R1_HARD_REJECT)
    if near:
        fired.append(RuleId.R2_THRESHOLD_BAND)
    if weak_near:
        fired.append(RuleId.R3_WEAK_SUPPORT_NEAR)

    cond_type: ConditionalType | None = None
    upgrade: str | None = None
    if hard:
        inner, outer = InnerStatus.REJECTED, OuterStatus.REJECTED
        codes = _codes(ReasonCode.HARD_REJECT_THRESHOLD)
    elif near or weak_near:
        inner, outer = InnerStatus.NEEDS_REVIEW, OuterStatus.CONDITIONAL
        cond_type, upgrade = ConditionalType.DATA_ISSUE, HUMAN_REVIEW_COMPLETED
        extra = []
        if near:
            extra.append(
                ReasonCode.INTERVAL_STRADDLES_THRESHOLD
                if lo <= thr <= hi
                else ReasonCode.WITHIN_BAND_OF_THRESHOLD
            )
        if weak_near:
            extra.append(ReasonCode.WEAK_SUPPORT_NEAR_THRESHOLD)
        codes = _codes(ReasonCode.REVIEW_REQUIRED, *extra)
    elif hi < thr:
        fired.append(RuleId.R4_APPROVE)
        inner, outer = InnerStatus.APPROVED, OuterStatus.APPROVED
        codes = _codes(ReasonCode.PD_BELOW_THRESHOLD)
    elif girdi.plan_available is True:
        fired.append(RuleId.R5_NOT_APPROVED_PLAN)
        inner, outer = InnerStatus.CONDITIONAL, OuterStatus.CONDITIONAL
        cond_type = ConditionalType.PLAN_BASED  # numeric upgrade_condition arrives in week 4
        codes = _codes(ReasonCode.PD_ABOVE_THRESHOLD, ReasonCode.PLAN_AVAILABLE)
    else:
        fired.append(RuleId.R6_NOT_APPROVED)
        inner, outer = InnerStatus.REJECTED, OuterStatus.REJECTED
        codes = _codes(
            ReasonCode.PD_ABOVE_THRESHOLD,
            *([ReasonCode.NO_PLAN_AVAILABLE] if girdi.plan_available is False else []),
        )

    return InternalDecision(
        dis_durum=outer,
        ic_durum=inner,
        gerekce_kodlari=codes,
        tetiklenen_kurallar=tuple(fired),
        conditional_type=cond_type,
        upgrade_condition=upgrade,
        politika_surumu=politika.surum,
    )


def to_public(d: InternalDecision) -> PublicDecision:
    return PublicDecision(
        dis_durum=d.dis_durum,
        gerekce_kodlari=tuple(
            PublicReasonCode(c.value) for c in d.gerekce_kodlari if c.value in _PUBLIC
        ),
        conditional_type=d.conditional_type,
        upgrade_condition=d.upgrade_condition,
        politika_surumu=d.politika_surumu,
    )
