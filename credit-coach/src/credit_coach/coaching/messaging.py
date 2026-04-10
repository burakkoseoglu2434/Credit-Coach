from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from credit_coach.data.schema import (
    CustomerRoadmapNarrative,
    LocalizedText,
    NarrativeCard,
    OfferNarrative,
    RoadmapCheckpointNarrative,
    RoadmapExecutiveSummary,
    RoadmapReasonNarrative,
    RoadmapStepNarrative,
    RoadmapTechnicalReveal,
)


def reason_codes(
    progress_label: str,
    replan: bool,
    ci_high: float,
    tau: float,
    replan_reasons: list[str] | None = None,
) -> list[str]:
    reasons = []
    reasons.append(f"progress:{progress_label}")
    reasons.append(f"risk_bound:{ci_high:.4f}_tau:{tau:.4f}")
    reasons.append("action:replan" if replan else "action:continue")
    if replan and replan_reasons:
        reasons.extend([f"trigger:{r}" for r in replan_reasons[:2]])
    return reasons[:3]


_ADVERSE_ACTION_REASON_MAP = {
    "dti": "high_debt_to_income",
    "revol_util": "high_credit_utilization",
    "int_rate": "high_interest_obligation",
    "inq_last_6mths": "too_many_recent_credit_inquiries",
    "delinq_2yrs": "recent_delinquency_history",
    "open_acc": "high_open_credit_exposure",
    "annual_inc": "insufficient_verified_income",
    "tot_cur_bal": "high_total_outstanding_balance",
    "credit_history_len": "limited_credit_history_depth",
    "mths_since_last_delinq": "recent_delinquency_recency_risk",
}

_REASON_TEMPLATES: dict[str, dict[str, str]] = {
    "high_debt_to_income": {
        "title": "Debt-to-income ratio is high",
        "description": "Current debt burden relative to income is above policy tolerance.",
        "remediation_hint": "Reduce monthly debt obligations or increase verified income.",
        "tr_title": "Borc gelire gore yuksek",
        "tr_description": "Mevcut borc baskisi, gelir seviyesine gore politika toleransinin ustunde.",
        "tr_remediation_hint": "Aylik borc baskisini azaltin veya belgelenebilir geliri guclendirin.",
    },
    "high_credit_utilization": {
        "title": "Credit utilization is high",
        "description": "A high share of revolving limits is currently in use.",
        "remediation_hint": "Lower revolving balances and keep utilization stable over time.",
        "tr_title": "Kredi kullanim orani yuksek",
        "tr_description": "Donen limitlerin yuksek bir bolumu su anda kullanimda.",
        "tr_remediation_hint": "Donen borc bakiyelerini azaltin ve kullanim oranini istikrarli tutun.",
    },
    "high_interest_obligation": {
        "title": "Interest burden is elevated",
        "description": "Current rate and debt structure imply high payment pressure.",
        "remediation_hint": "Refinance expensive balances or reduce high-rate obligations.",
        "tr_title": "Faiz kaynakli odeme baskisi yuksek",
        "tr_description": "Mevcut faiz ve borc yapisi, yuksek aylik odeme baskisi yaratiyor.",
        "tr_remediation_hint": "Pahali borclari yeniden yapilandirin veya yuksek faizli yukumlulukleri azaltin.",
    },
    "insufficient_verified_income": {
        "title": "Verified income is insufficient",
        "description": "Verified income level does not currently support requested risk level.",
        "remediation_hint": "Provide updated income verification or reduce requested amount.",
        "tr_title": "Dogrulanmis gelir yetersiz",
        "tr_description": "Dogrulanmis gelir seviyesi, mevcut risk seviyesini desteklemiyor.",
        "tr_remediation_hint": "Guncel gelir dogrulamasini saglayin veya talep edilen tutari azaltin.",
    },
}

_ACTION_NARRATIVE_TEMPLATES: dict[str, dict[str, tuple[str, str]]] = {
    "adjust_requested_loan_amount": {
        "action_summary": (
            "Talep edilen kredi tutarini geri odeme kapasitesiyle uyumlu seviyeye cek.",
            "Adjust the requested loan amount to match current repayment capacity.",
        ),
        "why_this_matters": (
            "Daha dengeli bir talep seviyesi, dosyanin ilk kontrolde daha guvenli gorunmesini saglar.",
            "A more balanced request level helps the file look safer at the first review checkpoint.",
        ),
        "expected_outcome": (
            "Basvuru baskisi azalir ve erken onay hazirligi guclenir.",
            "Application pressure eases and early approval readiness improves.",
        ),
        "what_happens_if_done": (
            "Talep ile gelir kapasitesi daha iyi hizalanir ve karar gorunumu yumusar.",
            "Request size aligns better with affordability and the decision outlook softens.",
        ),
        "what_happens_if_not_done": (
            "Talep baskisi yuksek kalir ve dosya yeniden fazla agresif gorunebilir.",
            "The request stays stretched and the file may continue to look too aggressive.",
        ),
    },
    "refinance": {
        "action_summary": (
            "Borcu daha yonetilebilir bir geri odeme yapisina tasimayi hedefle.",
            "Move the debt into a more manageable repayment structure.",
        ),
        "why_this_matters": (
            "Daha saglikli vade ve faiz yapisi aylik odeme baskisini azaltir.",
            "A healthier term and rate structure reduces monthly payment pressure.",
        ),
        "expected_outcome": (
            "Odeme davranisini korumak daha kolay hale gelir ve profil dengelenir.",
            "It becomes easier to sustain repayment behavior and stabilize the profile.",
        ),
        "what_happens_if_done": (
            "Borclanin baskisi azalir ve orta vadeli onay hikayesi guclenir.",
            "Debt pressure falls and the mid-term approval story improves.",
        ),
        "what_happens_if_not_done": (
            "Yuksek odeme baskisi korunur ve sonraki checkpoint'lerde zayiflik devam edebilir.",
            "High payment pressure persists and later checkpoints may remain weak.",
        ),
    },
    "increase_regular_income": {
        "action_summary": (
            "Daha istikrarli ve belgelenebilir duzenli gelir olustur.",
            "Build more stable and documentable recurring income.",
        ),
        "why_this_matters": (
            "Gelir gucu, risk toleransini ve aylik odeme kapasitesini dogrudan etkiler.",
            "Income strength directly affects both risk tolerance and monthly repayment capacity.",
        ),
        "expected_outcome": (
            "Gelir tarafi guclendikce dosyanin desteklenebilirligi artar.",
            "As the income side strengthens, the file becomes easier to support.",
        ),
        "what_happens_if_done": (
            "Basvuru dosyasi daha dengeli gelir ve gelir kaynakli red baskisi azalir.",
            "The application looks more balanced and income-related rejection pressure declines.",
        ),
        "what_happens_if_not_done": (
            "Gelir tarafi zayif kalirsa iyilesme hikayesi eksik gorunmeye devam eder.",
            "If income stays weak, the improvement story remains incomplete.",
        ),
    },
    "verify_income_documentation": {
        "action_summary": (
            "Gelir belgelerini guncelleyip dogrulanabilir hale getir.",
            "Update income documents and make them fully verifiable.",
        ),
        "why_this_matters": (
            "Belgelenmis gelir, risk kararinda gorunen dosya kalitesini iyilestirir.",
            "Verified income improves the quality of the file seen by the risk decision.",
        ),
        "expected_outcome": (
            "Dosya daha temiz ve daha guvenilir gorunur.",
            "The file looks cleaner and more reliable.",
        ),
        "what_happens_if_done": (
            "Belirsizlik azalir ve gelir tarafli inceleme baskisi hafifler.",
            "Uncertainty drops and income-driven scrutiny softens.",
        ),
        "what_happens_if_not_done": (
            "Gelir tarafinda soru isaretleri devam eder ve dosya eksik kalir.",
            "Income-side uncertainty remains and the file continues to look incomplete.",
        ),
    },
    "reduce_spending": {
        "action_summary": (
            "Zorunlu olmayan harcamalari azaltip kisa vadeli nefes alani ac.",
            "Reduce non-essential spending to create short-term breathing room.",
        ),
        "why_this_matters": (
            "Daha dusuk harcama baskisi, ilk checkpoint'e kadar odeme davranisini korumayi kolaylastirir.",
            "Lower spending pressure makes it easier to protect repayment behavior through the first checkpoint.",
        ),
        "expected_outcome": (
            "Aylik nakit akisi dengelenir ve kisa vadeli risk baskisi hafifler.",
            "Monthly cash flow stabilizes and near-term risk pressure eases.",
        ),
        "what_happens_if_done": (
            "Ilk kontrol noktasina daha temiz bir davranis sinyali tasinabilir.",
            "A cleaner behavior signal can be carried into the first review point.",
        ),
        "what_happens_if_not_done": (
            "Aylik baski yuksek kalirsa ilk checkpoint zayif gelebilir.",
            "If monthly pressure stays high, the first checkpoint may remain weak.",
        ),
    },
    "debt_consolidation": {
        "action_summary": (
            "Daginik ve baskili borcu daha surdurulebilir bir yapiya tasi.",
            "Move fragmented high-pressure debt into a more sustainable structure.",
        ),
        "why_this_matters": (
            "Daha duzenli bir borc yapisi, hem kullanim hem de odeme sinyalini iyilestirir.",
            "A more structured debt shape improves both utilization and repayment signals.",
        ),
        "expected_outcome": (
            "Borclanma baskisi dagilir ve profil daha yonetilebilir hale gelir.",
            "Debt pressure becomes more manageable and the profile stabilizes.",
        ),
        "what_happens_if_done": (
            "Yuksek baskili bakiyeler daha kontrollu bir duzene girer.",
            "High-pressure balances move into a more controlled path.",
        ),
        "what_happens_if_not_done": (
            "Daginiq baski devam eder ve uzun vadeli iyilesme daha kirilgan olur.",
            "Fragmented pressure remains and longer-term improvement becomes more fragile.",
        ),
    },
    "limit_credit_usage": {
        "action_summary": (
            "Kart kullanimini sinirla ve yeni bakiye baskisi yaratma.",
            "Limit credit usage and avoid creating fresh balance pressure.",
        ),
        "why_this_matters": (
            "Daha dusuk kullanim orani erken checkpoint'te davranis ve risk gorunumunu destekler.",
            "Lower utilization supports both behavior and risk posture at the early checkpoint.",
        ),
        "expected_outcome": (
            "Donen borc baskisi hafifler ve profil daha kontrollu gorunur.",
            "Revolving balance pressure eases and the profile looks more controlled.",
        ),
        "what_happens_if_done": (
            "Kullanim orani rahatlar ve sonraki inceleme icin daha temiz sinyal olusur.",
            "Utilization improves and a cleaner signal appears for the next review.",
        ),
        "what_happens_if_not_done": (
            "Yeni bakiye baskisi, daha guclu bir hikaye kurulmasini zorlastirir.",
            "Fresh balance pressure makes it harder to build a stronger story.",
        ),
    },
    "improve_payment_consistency": {
        "action_summary": (
            "Odeme duzenini istikrarli hale getir ve temiz bir seri olustur.",
            "Make repayment behavior consistent and build a clean payment streak.",
        ),
        "why_this_matters": (
            "Duzenli odeme davranisi, kredi veren guvenini yeniden kurmanin en guclu sinyallerinden biridir.",
            "Consistent repayment is one of the strongest signals for rebuilding lender confidence.",
        ),
        "expected_outcome": (
            "Orta vadeli onay hazirligi guclenir ve profil daha guvenilir gorunur.",
            "Mid-term approval readiness improves and the profile looks more reliable.",
        ),
        "what_happens_if_done": (
            "Checkpoints boyunca daha guclu bir guven sinyali birikir.",
            "A stronger trust signal accumulates across checkpoints.",
        ),
        "what_happens_if_not_done": (
            "Odeme serisi kirik kalirsa toparlanma hikayesi zayif gorunur.",
            "If the payment streak stays broken, the recovery story remains weak.",
        ),
    },
    "credit_limit_adjustment": {
        "action_summary": (
            "Kullanim baskisini hafifletecek bir limit ayarlamasini degerlendir.",
            "Evaluate a limit adjustment that meaningfully relieves utilization pressure.",
        ),
        "why_this_matters": (
            "Dogru kullanildiginda limit rahatlamasi profilin kullanimi daha guvenli gosterebilir.",
            "When used correctly, limit relief can make utilization look safer.",
        ),
        "expected_outcome": (
            "Kullanim oraninda gorunen baski duserek dosya daha dengeli gorunur.",
            "Visible utilization pressure drops and the file looks more balanced.",
        ),
        "what_happens_if_done": (
            "Kullanim orani daha iyi desteklenirse kurum tarafli rahatlama saglanir.",
            "If utilization truly improves, the institution-side move creates visible relief.",
        ),
        "what_happens_if_not_done": (
            "Limit rahatlamasi olmadan kullanim baskisi daha uzun sure yuksek kalabilir.",
            "Without the relief move, utilization pressure may stay elevated longer.",
        ),
    },
    "settlement_discount": {
        "action_summary": (
            "Uygunsa odeme indirimi secenegiyle borc baskisini azalt.",
            "If eligible, use a settlement discount option to reduce debt pressure.",
        ),
        "why_this_matters": (
            "Uygun bir indirim, yuksek baskili borcu daha hizli kontrol altina alabilir.",
            "A well-structured discount can reduce high-pressure debt more quickly.",
        ),
        "expected_outcome": (
            "Borclanma baskisi duserek profilin toparlanma hizi artar.",
            "Debt pressure falls and the profile can recover faster.",
        ),
        "what_happens_if_done": (
            "Uygun kosullarda borc yukunun bir kismi temizlenir ve dosya rahatlar.",
            "Under the right terms, part of the debt burden clears and the file relaxes.",
        ),
        "what_happens_if_not_done": (
            "Yuksek baskili bakiye daha uzun sure profilin uzerinde kalir.",
            "The high-pressure balance remains on the profile for longer.",
        ),
    },
    "installment_plan": {
        "action_summary": (
            "Borcun bir kismini daha duzenli bir taksit planina tasi.",
            "Move part of the balance into a steadier installment structure.",
        ),
        "why_this_matters": (
            "Daha duzenli geri odeme yapisi, odeme davranisini korumayi kolaylastirir.",
            "A steadier repayment structure makes it easier to protect repayment behavior.",
        ),
        "expected_outcome": (
            "Aylik baski daha yonetilebilir hale gelir ve profil istikrar kazanir.",
            "Monthly pressure becomes more manageable and the profile stabilizes.",
        ),
        "what_happens_if_done": (
            "Kurumsal destekle daha surdurulebilir bir odeme hikayesi kurulur.",
            "Institution-side support creates a more sustainable repayment story.",
        ),
        "what_happens_if_not_done": (
            "Borc yapisi ayni baski ile kalir ve davranis iyilesmesi daha zor olur.",
            "The debt structure keeps the same pressure and behavior improvement becomes harder.",
        ),
    },
}

_PRIMARY_TARGET_METRIC_LABELS: dict[str, tuple[str, str]] = {
    "requested_loan_amount": ("talep edilen kredi tutari", "requested loan amount"),
    "monthly_payment_amount": ("aylik odeme tutari", "monthly payment amount"),
    "documented_income_amount": ("belgelenmis gelir", "documented income"),
    "income_verification_state": ("gelir dogrulama durumu", "income verification state"),
    "debt_to_income_pct": ("borc/gelir orani", "debt-to-income ratio"),
    "credit_utilization_pct": ("kredi kullanim orani", "credit utilization"),
    "credit_score_points": ("kredi skoru", "credit score"),
    "credit_limit_amount": ("kredi limiti", "credit limit"),
    "bankcard_limit_amount": ("banka karti limiti", "bankcard limit"),
    "total_high_credit_limit_amount": ("toplam yuksek kredi limiti", "total high credit limit"),
    "revolving_balance_amount": ("donen borc bakiyesi", "revolving balance"),
    "total_current_balance_amount": ("toplam aktif borc bakiyesi", "total current balance"),
    "non_mortgage_balance_amount": ("ipotek disi borc bakiyesi", "non-mortgage balance"),
    "interest_rate_pct": ("faiz orani", "interest rate"),
    "delinquent_balance_amount": ("gecikmeli borc bakiyesi", "delinquent balance"),
    "delinquent_accounts_count": ("gecikmeli hesap sayisi", "delinquent account count"),
    "recent_collections_count": ("yakin donem tahsilat kaydi", "recent collections count"),
}

_OFFER_NARRATIVE_TEMPLATES: dict[str, dict[str, tuple[str, str]]] = {
    "installment_terms": {
        "offer_explanation": (
            "Aylik odemeyi daha duzenli hale getiren taksitlendirme teklifi sunuluyor.",
            "An installment offer is being presented to make the monthly payment path more stable.",
        ),
        "why_offered": (
            "Bu teklif, odeme baskisini azaltip davranis istikrarini korumaya yardimci olur.",
            "This offer helps lower payment pressure while preserving repayment stability.",
        ),
        "if_accepted": (
            "Musteri daha duzenli bir geri odeme yapisina gecer ve profil daha hizli dengelenebilir.",
            "The customer moves into a steadier repayment structure and the profile may stabilize faster.",
        ),
        "if_not_accepted": (
            "Plan yalnizca musteri aksiyonlariyla ilerler ve iyilesme daha kirilgan kalabilir.",
            "The plan must rely on customer actions alone and the recovery path may stay more fragile.",
        ),
    },
    "discount_offer": {
        "offer_explanation": (
            "Uygun kosullarda borc baskisini azaltan odeme indirimi teklifi sunuluyor.",
            "A settlement-style discount offer is available to reduce debt pressure if terms fit.",
        ),
        "why_offered": (
            "Bu teklif, yuksek baskili bakiyeyi daha hizli kontrol altina almayi amaclar.",
            "This offer aims to bring a high-pressure balance under control faster.",
        ),
        "if_accepted": (
            "Borc yukunun bir kismi temizlenir ve toparlanma hikayesi hizlanabilir.",
            "Part of the debt burden clears and the recovery story can accelerate.",
        ),
        "if_not_accepted": (
            "Plan daha yavas ama daha davranis odakli bir yol olarak devam eder.",
            "The plan continues as a slower, more behavior-led path.",
        ),
    },
    "credit_limit_adjustment": {
        "offer_explanation": (
            "Kullanim oranini rahatlatabilecek bir limit ayarlama secenegi sunuluyor.",
            "A limit-adjustment option is available to relieve utilization pressure.",
        ),
        "why_offered": (
            "Teklif, profilin kullanim gorunumunu kontrollu sekilde iyilestirmeyi hedefler.",
            "The offer aims to improve the visible utilization profile in a controlled way.",
        ),
        "if_accepted": (
            "Kullanim baskisi daha hizli rahatlayabilir ve dosya daha dengeli gorunebilir.",
            "Utilization pressure can ease faster and the file may look more balanced.",
        ),
        "if_not_accepted": (
            "Musteri yine de davranis bazli iyilesme yoluyla ilerleyebilir.",
            "The customer can still progress through behavior-led improvement.",
        ),
    },
}

_PATH_RENDER_VERSION = "phase59_action_semantics_rendering_v1"
_PATH_TYPE_LABELS: dict[str, tuple[str, str]] = {
    "customer_only": ("yalniz musteri yolu", "customer-only path"),
    "institution_assisted": ("kurum destekli yol", "institution-assisted path"),
    "hybrid": ("hibrit yol", "hybrid path"),
}
_PATH_RENDER_GENERIC_PHRASES = {
    "improve profile",
    "take action",
    "follow the plan",
    "make progress",
    "recommended path",
    "improve outcome",
}


def _lt(tr: str, en: str) -> LocalizedText:
    return LocalizedText(tr=str(tr), en=str(en))


def _localized_pair(values: tuple[str, str]) -> LocalizedText:
    tr, en = values
    return _lt(tr, en)


def _combine_localized_texts(parts: Sequence[LocalizedText | None]) -> LocalizedText | None:
    tr_parts = [part.tr.strip() for part in parts if part is not None and str(part.tr or "").strip()]
    en_parts = [part.en.strip() for part in parts if part is not None and str(part.en or "").strip()]
    if not tr_parts and not en_parts:
        return None
    return _lt(" ".join(tr_parts), " ".join(en_parts))


def _prepend_localized_prefix(prefix: LocalizedText, text: LocalizedText | None) -> LocalizedText | None:
    if text is None:
        return None
    return _combine_localized_texts([prefix, text])


def _payload_from_model(value: Any) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="python")
        if isinstance(dumped, Mapping):
            return dumped
    return None


def _representative_action_payload(representative_plan: Any) -> Mapping[str, Any] | None:
    payload = _payload_from_model(representative_plan)
    if payload is None:
        return None
    actions = payload.get("actions", [])
    if isinstance(actions, Sequence):
        for action in actions:
            action_payload = _payload_from_model(action)
            if action_payload is not None and (
                str(action_payload.get("action_key", "") or "").strip()
                or str(action_payload.get("feature_name", "") or "").strip()
                or _primary_numeric_target(action_payload)
            ):
                return action_payload
    if (
        str(payload.get("action_key", "") or "").strip()
        or str(payload.get("feature_name", "") or "").strip()
        or _primary_numeric_target(payload)
    ):
        return payload
    return None


def _contains_generic_weak_language(text: LocalizedText | None) -> bool:
    if text is None:
        return False
    combined = f"{text.tr} {text.en}".strip().lower()
    if not combined:
        return True
    return any(phrase in combined for phrase in _PATH_RENDER_GENERIC_PHRASES)


def _card(label_tr: str, label_en: str, desc_tr: str, desc_en: str) -> NarrativeCard:
    return NarrativeCard(label=_lt(label_tr, label_en), description=_lt(desc_tr, desc_en))


def build_informational_executive_summary(
    *,
    base_pd: float,
    tau: float,
    checkpoints: Sequence[Mapping[str, Any]],
    status: str,
    informational_subtype: str,
    confidence_label: str = "moderate",
    expected_readiness: str | None = None,
    decision_reason_summary: str | None = None,
    conditional_type: str | None = None,
    upgrade_condition: str | None = None,
) -> RoadmapExecutiveSummary:
    readiness_stage, readiness_week = _resolve_business_readiness_stage(
        expected_readiness,
        base_pd=base_pd,
        checkpoints=checkpoints,
        tau=tau,
    )
    decision_view = _decision_view_card(
        status,
        readiness_stage,
        conditional_type=conditional_type,
        decision_reason_summary=decision_reason_summary,
        upgrade_condition=upgrade_condition,
    )
    time_to_readiness = _time_to_readiness_card(readiness_stage, readiness_week)
    checkpoint_4w_summary = _checkpoint_4w_card(checkpoints, tau)
    risk_start = _risk_card(base_pd, tau)

    subtype = str(informational_subtype or "").strip().lower()
    if subtype == "structural_limited":
        headline = _lt(
            "Bu gorunum bilgilendiricidir: su an guvenli bir aksiyon plani onerilmiyor.",
            "This is an informational view: no safe action plan is being promoted right now.",
        )
        recommended_path = _card(
            "Bilgilendirici gorunum",
            "Informational view",
            "Mevcut risk mesafesi ve kanit seti ile esige ulasan guvenli bir yol gosterilemiyor.",
            "With the current risk distance and evidence, a governed threshold-reaching path cannot be promoted.",
        )
        expected_result = _card(
            "Sinirli hareket alani",
            "Limited movement potential",
            "Bu dosyada oncelik, kosullar degistiginde yeniden degerlendirmedir.",
            "The right next step is to re-evaluate if underlying conditions change.",
        )
    else:
        headline = _lt(
            "Bu gorunum bilgilendiricidir: su an guvenli bir aksiyon plani onerilmiyor.",
            "This is an informational view: no safe action plan is being promoted right now.",
        )
        recommended_path = _card(
            "Henuz aksiyonel degil",
            "Not actionable yet",
            "Guvenli bir plan icin kritik bir kosul eksik (zaman penceresi, teklif uygunlugu veya etki).",
            "A key condition is missing for a safe plan (time window, offer eligibility, or impact evidence).",
        )
        expected_result = _card(
            "Kosullar olusunca yeniden bak",
            "Re-evaluate when conditions change",
            "Kosullar olusunca sistem tekrar aksiyonel yol arayabilir.",
            "When conditions change, the system can reassess whether an actionable route becomes viable.",
        )

    offer_status = _card(
        "Bu gorunumde teklif onerilmiyor",
        "No offer is promoted in this view",
        "Bu gorunum, teklif/kurum destegi uzerinden bir yol secmez.",
        "This view does not promote an offer/institution-assisted route.",
    )

    return RoadmapExecutiveSummary(
        headline=headline,
        summary_line=_lt(
            "Guvenli bir oneriyi one cikarmak icin yeterli kanit yok.",
            "There is not enough evidence to promote a safe recommendation.",
        ),
        risk_start=risk_start,
        recommended_path=recommended_path,
        offer_status=offer_status,
        checkpoint_4w_summary=checkpoint_4w_summary,
        expected_result=expected_result,
        follow_through_readiness=None,
        decision_view=decision_view,
        time_to_readiness=time_to_readiness,
        narrative_confidence=_card(
            confidence_label.replace("_", " ").capitalize(),
            confidence_label.replace("_", " ").capitalize(),
            _confidence_description(confidence_label).tr,
            _confidence_description(confidence_label).en,
        ),
    )


def apply_informational_posture_to_narrative(
    narrative: Mapping[str, Any] | None,
    *,
    base_pd: float,
    tau: float,
    checkpoints: Sequence[Mapping[str, Any]],
    decision_status: str,
    expected_readiness: str | None,
    decision_reason_summary: str | None,
    conditional_type: str | None,
    upgrade_condition: str | None,
    informational_subtype: str,
) -> dict[str, Any]:
    """
    Phase 66 post-processing: when the recourse gate forces informational posture,
    ensure the executive narrative cannot read as actionable.
    """

    raw = dict(narrative or {}) if isinstance(narrative, Mapping) else {}
    technical_reveal = raw.get("technical_reveal", {})
    confidence_label = (
        str(dict(technical_reveal or {}).get("narrative_confidence_label") or "").strip().lower()
        if isinstance(technical_reveal, Mapping)
        else ""
    ) or "moderate"
    raw["executive_summary"] = build_informational_executive_summary(
        base_pd=base_pd,
        tau=tau,
        checkpoints=checkpoints,
        status=decision_status,
        informational_subtype=informational_subtype,
        confidence_label=confidence_label,
        expected_readiness=expected_readiness,
        decision_reason_summary=decision_reason_summary,
        conditional_type=conditional_type,
        upgrade_condition=upgrade_condition,
    ).model_dump(mode="json")
    return raw


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _offer_contract_payload(action: Mapping[str, Any]) -> dict[str, Any]:
    contract = action.get("offer_contract")
    if isinstance(contract, Mapping):
        payload = dict(contract)
        terms = payload.get("offer_terms", {})
        payload["offer_terms"] = dict(terms or {}) if isinstance(terms, Mapping) else {}
        return payload
    offer_terms = action.get("offer_terms", {})
    return {
        "offer_type": str(action.get("offer_type", "") or "") or None,
        "offer_family": str(action.get("offer_family", "") or "") or None,
        "offer_terms": dict(offer_terms or {}) if isinstance(offer_terms, Mapping) else {},
        "offer_terms_complete": bool(action.get("offer_terms_complete", False)),
        "requires_acceptance": bool(action.get("requires_acceptance", False)),
        "requires_institutional_approval": bool(action.get("requires_institutional_approval", False)),
        "institutional_approval_state": str(action.get("institutional_approval_state", "") or "not_required"),
        "offer_policy_arm": str(action.get("offer_policy_arm", "") or "") or None,
        "offer_scoring_profile": str(action.get("offer_scoring_profile", "") or "") or None,
        "term_generation_rule": str(action.get("term_generation_rule", "") or "") or None,
    }


def _has_visible_offer(action: Mapping[str, Any]) -> bool:
    contract = _offer_contract_payload(action)
    return bool(str(contract.get("offer_type", "") or "").strip() or dict(contract.get("offer_terms", {}) or {}))


def _offer_state_note(action: Mapping[str, Any]) -> LocalizedText | None:
    contract = _offer_contract_payload(action)
    approval_state = str(contract.get("institutional_approval_state", "") or "").strip().lower()
    requires_approval = (
        bool(contract.get("requires_institutional_approval", False))
        or approval_state in {"pending", "unknown"}
        or bool(action.get("approval_pending_semantic_only", False))
        or bool(action.get("dependency_gate", False))
    )
    if requires_approval:
        return _lt("Kurum onayina bagli.", "Depends on institution approval.")
    if bool(contract.get("requires_acceptance", False)):
        return _lt("Musteri kabulune bagli.", "Depends on customer acceptance.")
    if _has_visible_offer(action):
        return _lt("Teklif aktif durumda.", "Offer is currently active.")
    return None


def _format_pct(value: float) -> str:
    return f"%{int(round(float(value) * 100))}"


def _format_scalar(value: float) -> str:
    numeric = float(value)
    if abs(numeric - round(numeric)) < 1e-9:
        return f"{int(round(numeric)):,}"
    return f"{numeric:,.1f}".rstrip("0").rstrip(".")


def _format_primary_target_value(value: float, unit: str, *, locale: str) -> str:
    if unit in {"probability", "probability_points", "score"}:
        return f"{float(value):.2f}".rstrip("0").rstrip(".")
    if unit == "weeks":
        display = _format_scalar(value)
        suffix = " hafta" if locale == "tr" else " weeks"
        return f"{display}{suffix}"
    if unit == "flag":
        if float(value) >= 0.5:
            return "tamam" if locale == "tr" else "pass"
        return "degil" if locale == "tr" else "fail"
    display = _format_scalar(value)
    if unit == "currency":
        suffix = " birim" if locale == "tr" else " units"
        return f"{display}{suffix}"
    if unit == "percentage_points":
        return f"%{display}"
    if unit == "score_points":
        suffix = " puan" if locale == "tr" else " points"
        return f"{display}{suffix}"
    if unit == "months":
        suffix = " ay" if locale == "tr" else " months"
        return f"{display}{suffix}"
    if unit == "count":
        suffix = " adet" if locale == "tr" else " items"
        return f"{display}{suffix}"
    if unit == "boolean_state":
        return "dogrulanmis" if locale == "tr" and value >= 0.5 else (
            "verified" if locale == "en" and value >= 0.5 else (
                "dogrulanmamis" if locale == "tr" else "unverified"
            )
        )
    return display


def _format_primary_target_delta(value: float, unit: str, *, locale: str) -> str:
    if unit in {"probability", "probability_points", "score"}:
        display = f"{abs(float(value)):.2f}".rstrip("0").rstrip(".")
        sign = "+" if float(value) >= 0.0 else "-"
        return f"{sign}{display}"
    display = _format_scalar(abs(value))
    sign = "+" if float(value) >= 0.0 else "-"
    if unit == "currency":
        suffix = " birim" if locale == "tr" else " units"
        return f"{sign}{display}{suffix}"
    if unit == "percentage_points":
        suffix = " puan" if locale == "tr" else " pts"
        return f"{sign}{display}{suffix}"
    if unit == "score_points":
        suffix = " puan" if locale == "tr" else " points"
        return f"{sign}{display}{suffix}"
    if unit == "months":
        suffix = " ay" if locale == "tr" else " months"
        return f"{sign}{display}{suffix}"
    if unit == "count":
        suffix = " adet" if locale == "tr" else " items"
        return f"{sign}{display}{suffix}"
    if unit == "boolean_state":
        suffix = " durum" if locale == "tr" else " state"
        return f"{sign}{display}{suffix}"
    return f"{sign}{display}"


def _primary_target_direction_verb(direction: str) -> tuple[str, str]:
    normalized = str(direction or "").strip().lower()
    if normalized == "increase":
        return ("yukselt", "increase")
    if normalized == "maintain":
        return ("koru", "maintain")
    return ("indir", "reduce")


_DECISION_DRIVER_LABELS: dict[str, tuple[str, str]] = {
    "best_action_count": ("uygulanabilir adim sayisi", "actionable step count"),
    "expected_pd_improvement": ("beklenen PD iyilesmesi", "expected PD improvement"),
    "realization_anchor": ("uygulama gucu", "execution strength"),
    "decision_confidence": ("karar guveni", "decision confidence"),
    "expected_readiness_week": ("hazirlik zamani", "readiness timing"),
    "critical_field_null_count": ("eksik karar verisi", "missing decision data"),
    "parity_pass": ("artifact tutarliligi", "artifact consistency"),
    "rankable_offer_count": ("aktif kurum teklifi", "active institution support"),
}


def build_operator_summary_line(decision_reason_summary: str | None) -> str:
    return str(decision_reason_summary or "").strip()


def build_operator_driver_line(driver: Mapping[str, Any]) -> LocalizedText:
    driver_key = str(driver.get("driver_key", "") or "").strip()
    label_tr, label_en = _DECISION_DRIVER_LABELS.get(
        driver_key,
        (driver_key.replace("_", " ").strip() or "engel", driver_key.replace("_", " ").strip() or "blocker"),
    )
    unit = str(driver.get("unit", "") or "").strip()
    comparison = str(driver.get("comparison", "") or "").strip().lower()
    current_value = _safe_float(driver.get("current_value", 0.0), 0.0)
    target_value = _safe_float(driver.get("target_value", 0.0), 0.0)
    if comparison == "gte":
        cmp_tr = f">= {_format_primary_target_value(target_value, unit, locale='tr')}"
        cmp_en = f">= {_format_primary_target_value(target_value, unit, locale='en')}"
    elif comparison == "lte":
        cmp_tr = f"<= {_format_primary_target_value(target_value, unit, locale='tr')}"
        cmp_en = f"<= {_format_primary_target_value(target_value, unit, locale='en')}"
    elif comparison == "eq":
        cmp_tr = f"= {_format_primary_target_value(target_value, unit, locale='tr')}"
        cmp_en = f"= {_format_primary_target_value(target_value, unit, locale='en')}"
    else:
        cmp_tr = _format_primary_target_value(target_value, unit, locale="tr")
        cmp_en = _format_primary_target_value(target_value, unit, locale="en")
    current_tr = _format_primary_target_value(current_value, unit, locale="tr")
    current_en = _format_primary_target_value(current_value, unit, locale="en")
    return _lt(
        f"{label_tr}: {current_tr} -> hedef {cmp_tr}",
        f"{label_en}: {current_en} -> target {cmp_en}",
    )


def build_operator_readiness_note(expected_readiness: str | None) -> LocalizedText:
    readiness = str(expected_readiness or "").strip().lower()
    if readiness == "now":
        return _lt(
            "Profil mevcut gorunumde yeniden basvuruya uygun duruyor.",
            "The profile already looks ready for re-application in the current view.",
        )
    if readiness == "week_4":
        return _lt(
            "Plan korunursa yaklasik 4 hafta icinde onaya daha yakin bir gorunum beklenir.",
            "If the plan holds, a more approval-ready view is expected within about 4 weeks.",
        )
    if readiness == "week_12":
        return _lt(
            "Plan korunursa yaklasik 12 hafta icinde onaya daha yakin bir gorunum beklenir.",
            "If the plan holds, a more approval-ready view is expected within about 12 weeks.",
        )
    if readiness == "week_24":
        return _lt(
            "Plan korunursa yaklasik 24 hafta icinde daha guclu bir karar gorunumu beklenir.",
            "If the plan holds, a stronger decision view is expected within about 24 weeks.",
        )
    if readiness == "unknown_review":
        return _lt(
            "Hazirlik zamani icin once karar verisinin kontrollu sekilde tamamlanmasi gerekiyor.",
            "Decision data still needs controlled review before readiness timing is reliable.",
        )
    return _lt(
        "Mevcut sinyaller henuz guvenilir bir onay hazirligi zamani vermiyor.",
        "Current signals do not yet support a reliable approval-readiness timeline.",
    )


def build_operator_offer_state(
    *,
    offer_maturity: str | None,
    offer_plan: bool | int | None = None,
    offer_acceptance_probability: float | None = None,
) -> LocalizedText:
    maturity = str(offer_maturity or "").strip().lower()
    has_offer = bool(offer_plan) or maturity not in {"", "none"} or _safe_float(offer_acceptance_probability, 0.0) > 0.0
    if maturity == "active_rankable":
        return _lt("Kurum teklifi aktif", "Institution offer is active")
    if maturity == "provisional":
        return _lt("Kurum teklifine bagli", "Depends on institution offer")
    if maturity == "inactive" and has_offer:
        return _lt("Musteri kabulune bagli", "Depends on customer acceptance")
    return _lt("Kurum teklifi yok", "No institution offer")


def build_operator_downside_risk(
    *,
    decision_status: str | None,
    conditional_type: str | None = None,
    rejection_type: str | None = None,
) -> LocalizedText:
    status = _normalize_business_decision_status(str(decision_status or "CONDITIONAL"))
    conditional = str(conditional_type or "").strip().upper()
    rejection = str(rejection_type or "").strip().upper()
    if status == "APPROVED":
        return _lt(
            "Aksiyon ritmi bozulursa mevcut onaya uygun gorunum zayiflayabilir.",
            "If follow-through slips, the current approval-ready view can soften.",
        )
    if status == "REJECTED":
        if rejection == "NO_PATH":
            return _lt(
                "Aksiyon alinmazsa mevcut karar icin savunulabilir bir yol olusmaz.",
                "Without action, there is no defendable path to a safer decision right now.",
            )
        if rejection == "LOW_IMPACT":
            return _lt(
                "Aksiyon alinmazsa mevcut iyilesme karari degistirecek kadar guclenmez.",
                "Without action, the current improvement stays too small to change the decision.",
            )
        return _lt(
            "Aksiyon alinmazsa mevcut planin gerceklesme gucu zayif kalir.",
            "Without action, the current plan remains too fragile to rely on.",
        )
    if conditional == "OFFER_GATED":
        return _lt(
            "Kurum destegi devreye girmezse yol yalniz musteri aksiyonlariyla daha yavas ilerler.",
            "If institution support does not activate, the path relies on customer action alone and may move more slowly.",
        )
    if conditional == "DATA_ISSUE":
        return _lt(
            "Karar verisi tamamlanmazsa hazirlik zamani belirsiz kalir.",
            "If decision data stays incomplete, readiness timing remains uncertain.",
        )
    if conditional == "TIME_GATED":
        return _lt(
            "Aksiyon alinmazsa onay hazirligi beklenen pencerenin disina kayabilir.",
            "If action is not taken, approval readiness can slip beyond the expected window.",
        )
    return _lt(
        "Aksiyon alinmazsa karar gorunumu daha yavas guclenir.",
        "Without action, the decision outlook will strengthen more slowly.",
    )


def _due_month_phrase(months: int, *, locale: str) -> str:
    bounded = max(1, int(months))
    if locale == "tr":
        if bounded == 1:
            return "bu ay icinde"
        return f"onumuzdeki {bounded} ay icinde"
    if bounded == 1:
        return "within this month"
    return f"within the next {bounded} months"


def _primary_numeric_target(action: Mapping[str, Any]) -> Mapping[str, Any]:
    target = action.get("primary_numeric_target", {})
    if isinstance(target, Mapping):
        return target
    return {}


def _has_primary_numeric_target(action: Mapping[str, Any]) -> bool:
    target = _primary_numeric_target(action)
    return bool(str(target.get("metric_key", "") or ""))


def _prefer_primary_target_step(existing: Mapping[str, Any], candidate: Mapping[str, Any]) -> bool:
    return _has_primary_numeric_target(candidate) and not _has_primary_numeric_target(existing)


def _append_localized_sentence(base: tuple[str, str], addition: LocalizedText | None) -> LocalizedText:
    if addition is None:
        return _localized_pair(base)
    tr, en = base
    return _lt(f"{tr} {addition.tr}".strip(), f"{en} {addition.en}".strip())


def _finite_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except Exception:
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _context_float(customer_context: Mapping[str, Any] | None, *keys: str) -> float | None:
    if not isinstance(customer_context, Mapping):
        return None
    for key in keys:
        if not key:
            continue
        numeric = _finite_float(customer_context.get(key))
        if numeric is not None:
            return numeric
    return None


def _small_monetary_delta(value: float | None) -> bool:
    if value is None:
        return True
    return abs(float(value)) < 500.0


def _utilization_ratio(value: float) -> float:
    numeric = float(value)
    return numeric / 100.0 if abs(numeric) > 1.0 else numeric


def _generic_exact_recommendation(target: Mapping[str, Any]) -> LocalizedText | None:
    metric_key = str(target.get("metric_key", "") or "")
    unit = str(target.get("unit", "") or "")
    current_value = _finite_float(target.get("current_value"))
    target_value = _finite_float(target.get("target_value"))
    if not metric_key or current_value is None or target_value is None:
        return None
    if metric_key == "credit_score_points" or unit in {"score_points", "score", "boolean_state"}:
        return None
    label_tr, label_en = _PRIMARY_TARGET_METRIC_LABELS.get(
        metric_key,
        (metric_key.replace("_", " ").strip() or "hedef metrik", metric_key.replace("_", " ").strip() or "target metric"),
    )
    current_tr = _format_primary_target_value(current_value, unit, locale="tr")
    current_en = _format_primary_target_value(current_value, unit, locale="en")
    target_tr = _format_primary_target_value(target_value, unit, locale="tr")
    target_en = _format_primary_target_value(target_value, unit, locale="en")
    direction = str(target.get("direction", "") or "decrease").strip().lower()
    if direction == "increase":
        return _lt(
            f"{label_tr} seviyesini {current_tr}'den {target_tr} seviyesine cikar.",
            f"Increase {label_en} from {current_en} to {target_en}.",
        )
    if direction == "maintain":
        return _lt(
            f"{label_tr} seviyesini {target_tr} civarinda koru.",
            f"Maintain {label_en} around {target_en}.",
        )
    return _lt(
        f"{label_tr} seviyesini {current_tr}'den {target_tr} seviyesine indir.",
        f"Reduce {label_en} from {current_en} to {target_en}.",
    )


def _utilization_paydown_amount(
    target: Mapping[str, Any],
    *,
    customer_context: Mapping[str, Any] | None,
) -> float | None:
    current_value = _finite_float(target.get("current_value"))
    target_value = _finite_float(target.get("target_value"))
    if current_value is None or target_value is None:
        return None
    current_ratio = _utilization_ratio(current_value)
    target_ratio = _utilization_ratio(target_value)
    if current_ratio <= 0.0 or target_ratio >= current_ratio:
        return None
    current_balance = _context_float(customer_context, "revol_bal")
    inferred_limit = None
    if current_balance is not None and current_ratio > 0.0:
        inferred_limit = current_balance / current_ratio
    if inferred_limit is None:
        inferred_limit = _context_float(customer_context, "total_rev_hi_lim", "total_bc_limit", "tot_hi_cred_lim")
    if inferred_limit is None or inferred_limit <= 0.0:
        return None
    if current_balance is None:
        current_balance = current_ratio * inferred_limit
    target_balance = target_ratio * inferred_limit
    paydown = max(0.0, current_balance - target_balance)
    return paydown if paydown > 0.0 else None


def _build_utilization_recommendation(
    target: Mapping[str, Any],
    *,
    customer_context: Mapping[str, Any] | None,
) -> LocalizedText | None:
    current_value = _finite_float(target.get("current_value"))
    target_value = _finite_float(target.get("target_value"))
    if current_value is None or target_value is None:
        return None
    current_tr = _format_primary_target_value(current_value, "percentage_points", locale="tr")
    current_en = _format_primary_target_value(current_value, "percentage_points", locale="en")
    target_tr = _format_primary_target_value(target_value, "percentage_points", locale="tr")
    target_en = _format_primary_target_value(target_value, "percentage_points", locale="en")
    paydown = _utilization_paydown_amount(target, customer_context=customer_context)
    if not _small_monetary_delta(paydown):
        paydown_tr = _format_primary_target_value(float(paydown), "currency", locale="tr")
        paydown_en = _format_primary_target_value(float(paydown), "currency", locale="en")
        return _lt(
            f"Kart kullanim oranini {current_tr}'den {target_tr} altina indir. Bu da yaklasik {paydown_tr} donen borc azaltimi demek.",
            f"Reduce credit utilization from {current_en} to below {target_en}. That implies about {paydown_en} of revolving-balance paydown.",
        )
    return _lt(
        f"Kart kullanim oranini {current_tr}'den {target_tr} altina indir.",
        f"Reduce credit utilization from {current_en} to below {target_en}.",
    )


def _build_installment_recommendation(target: Mapping[str, Any]) -> LocalizedText | None:
    current_value = _finite_float(target.get("current_value"))
    target_value = _finite_float(target.get("target_value"))
    if current_value is None or target_value is None:
        return None
    current_tr = _format_primary_target_value(current_value, "currency", locale="tr")
    current_en = _format_primary_target_value(current_value, "currency", locale="en")
    target_tr = _format_primary_target_value(target_value, "currency", locale="tr")
    target_en = _format_primary_target_value(target_value, "currency", locale="en")
    reduction = max(0.0, current_value - target_value)
    if not _small_monetary_delta(reduction):
        reduction_tr = _format_primary_target_value(reduction, "currency", locale="tr")
        reduction_en = _format_primary_target_value(reduction, "currency", locale="en")
        return _lt(
            f"Aylik taksit yukunu yaklasik {reduction_tr} azalt ve {current_tr}'den {target_tr} seviyesine cek.",
            f"Reduce the monthly payment burden by about {reduction_en} and move it from {current_en} to {target_en}.",
        )
    return _lt(
        f"Aylik taksit yukunu {current_tr}'den {target_tr} seviyesine cek.",
        f"Move the monthly payment burden from {current_en} to {target_en}.",
    )


def _build_loan_amount_recommendation(target: Mapping[str, Any]) -> LocalizedText | None:
    current_value = _finite_float(target.get("current_value"))
    target_value = _finite_float(target.get("target_value"))
    if current_value is None or target_value is None:
        return None
    current_tr = _format_primary_target_value(current_value, "currency", locale="tr")
    current_en = _format_primary_target_value(current_value, "currency", locale="en")
    target_tr = _format_primary_target_value(target_value, "currency", locale="tr")
    target_en = _format_primary_target_value(target_value, "currency", locale="en")
    reduction = max(0.0, current_value - target_value)
    if not _small_monetary_delta(reduction):
        reduction_tr = _format_primary_target_value(reduction, "currency", locale="tr")
        reduction_en = _format_primary_target_value(reduction, "currency", locale="en")
        return _lt(
            f"Talep edilen kredi tutarini yaklasik {reduction_tr} dusur ve {current_tr}'den {target_tr} seviyesine cek.",
            f"Reduce the requested loan amount by about {reduction_en} and move it from {current_en} to {target_en}.",
        )
    return _lt(
        f"Talep edilen kredi tutarini {current_tr}'den {target_tr} seviyesine cek.",
        f"Move the requested loan amount from {current_en} to {target_en}.",
    )


def _build_dti_recommendation(
    target: Mapping[str, Any],
    *,
    customer_context: Mapping[str, Any] | None,
) -> LocalizedText | None:
    current_value = _finite_float(target.get("current_value"))
    target_value = _finite_float(target.get("target_value"))
    if current_value is None or target_value is None:
        return None
    current_tr = _format_primary_target_value(current_value, "percentage_points", locale="tr")
    current_en = _format_primary_target_value(current_value, "percentage_points", locale="en")
    target_tr = _format_primary_target_value(target_value, "percentage_points", locale="tr")
    target_en = _format_primary_target_value(target_value, "percentage_points", locale="en")
    annual_inc = _context_float(customer_context, "annual_inc")
    monthly_relief = None
    if annual_inc is not None and annual_inc > 0.0:
        monthly_relief = max(0.0, ((current_value - target_value) / 100.0) * annual_inc / 12.0)
    if not _small_monetary_delta(monthly_relief):
        relief_tr = _format_primary_target_value(float(monthly_relief), "currency", locale="tr")
        relief_en = _format_primary_target_value(float(monthly_relief), "currency", locale="en")
        return _lt(
            f"Aylik borc/harcama baskisini yaklasik {relief_tr} azalt ve borc/gelir oranini {current_tr}'den {target_tr} seviyesine indir.",
            f"Reduce monthly debt pressure by about {relief_en} and move debt-to-income from {current_en} to {target_en}.",
        )
    return _lt(
        f"Borc/gelir oranini {current_tr}'den {target_tr} seviyesine indir.",
        f"Reduce debt-to-income from {current_en} to {target_en}.",
    )


def _build_limit_institution_condition(target: Mapping[str, Any]) -> LocalizedText | None:
    current_value = _finite_float(target.get("current_value"))
    target_value = _finite_float(target.get("target_value"))
    if current_value is None or target_value is None:
        return None
    current_tr = _format_primary_target_value(current_value, "currency", locale="tr")
    current_en = _format_primary_target_value(current_value, "currency", locale="en")
    target_tr = _format_primary_target_value(target_value, "currency", locale="tr")
    target_en = _format_primary_target_value(target_value, "currency", locale="en")
    increase = max(0.0, target_value - current_value)
    if not _small_monetary_delta(increase):
        increase_tr = _format_primary_target_value(increase, "currency", locale="tr")
        increase_en = _format_primary_target_value(increase, "currency", locale="en")
        return _lt(
            f"Profilin guclenmesi icin toplam limit tarafinda yaklasik {increase_tr} ek kapasite gerekiyor.",
            f"The profile needs about {increase_en} of additional total credit capacity to strengthen.",
        )
    return _lt(
        f"Profilin guclenmesi icin toplam limit tarafinda {current_tr}'den {target_tr} seviyesine cikmak gerekiyor.",
        f"The profile needs total credit capacity to move from {current_en} to {target_en} to strengthen.",
    )


def _build_step_recommendations(
    action: Mapping[str, Any],
    *,
    customer_context: Mapping[str, Any] | None,
) -> tuple[LocalizedText | None, LocalizedText | None]:
    target = _primary_numeric_target(action)
    metric_key = str(target.get("metric_key", "") or "")
    action_key = str(action.get("action_key", "") or "")
    primary_recommendation: LocalizedText | None = None
    institution_condition: LocalizedText | None = None

    if metric_key == "credit_utilization_pct":
        primary_recommendation = _build_utilization_recommendation(target, customer_context=customer_context)
    elif metric_key == "monthly_payment_amount":
        primary_recommendation = _build_installment_recommendation(target)
    elif metric_key == "requested_loan_amount":
        primary_recommendation = _build_loan_amount_recommendation(target)
    elif metric_key == "debt_to_income_pct":
        primary_recommendation = _build_dti_recommendation(target, customer_context=customer_context)
    elif metric_key in {"total_high_credit_limit_amount", "credit_limit_amount", "bankcard_limit_amount"} or action_key == "credit_limit_adjustment":
        institution_condition = _build_limit_institution_condition(target)
    else:
        primary_recommendation = _generic_exact_recommendation(target)

    if institution_condition is None:
        institution_condition = _offer_state_note(action)
    return primary_recommendation, institution_condition


def _primary_target_sentence(action: Mapping[str, Any]) -> LocalizedText | None:
    target = _primary_numeric_target(action)
    metric_key = str(target.get("metric_key", "") or "")
    if not metric_key:
        return None
    unit = str(target.get("unit", "") or "")
    current_value = target.get("current_value", None)
    target_value = _safe_float(target.get("target_value", 0.0), 0.0)
    delta_value = _safe_float(target.get("delta_value", 0.0), 0.0)
    due_month = _safe_int(target.get("due_month", action.get("time_months", 1)), 1)
    direction = str(target.get("direction", "") or "decrease")
    label_tr, label_en = _PRIMARY_TARGET_METRIC_LABELS.get(
        metric_key,
        (metric_key.replace("_", " "), metric_key.replace("_", " ")),
    )
    verb_tr, verb_en = _primary_target_direction_verb(direction)
    current_tr = (
        _format_primary_target_value(_safe_float(current_value, 0.0), unit, locale="tr")
        if current_value is not None
        else None
    )
    current_en = (
        _format_primary_target_value(_safe_float(current_value, 0.0), unit, locale="en")
        if current_value is not None
        else None
    )
    target_tr = _format_primary_target_value(target_value, unit, locale="tr")
    target_en = _format_primary_target_value(target_value, unit, locale="en")
    delta_tr = _format_primary_target_delta(delta_value, unit, locale="tr")
    delta_en = _format_primary_target_delta(delta_value, unit, locale="en")
    due_tr = _due_month_phrase(due_month, locale="tr")
    due_en = _due_month_phrase(due_month, locale="en")
    if unit == "boolean_state":
        return _lt(
            f"Hedef, {label_tr} durumunu {due_tr} {target_tr} hale getirmek ({delta_tr}).",
            f"The target is to move {label_en} to {target_en} {due_en} ({delta_en}).",
        )
    if current_tr and current_en:
        return _lt(
            f"Mevcut {label_tr} {current_tr} seviyesindeyken hedef, bunu {due_tr} {target_tr} seviyesine {verb_tr}mek ({delta_tr}).",
            f"With {label_en} currently at {current_en}, the target is to {verb_en} it to {target_en} {due_en} ({delta_en}).",
        )
    return _lt(
        f"Hedef, {label_tr} icin {due_tr} {target_tr} seviyesine {verb_tr}mek ({delta_tr}).",
        f"The target is to {verb_en} {label_en} to {target_en} {due_en} ({delta_en}).",
    )


def _timing_hint(time_months: int) -> LocalizedText:
    months = max(1, int(time_months))
    if months <= 1:
        return _lt("Hemen, bu ay icinde baslat.", "Start immediately, within this month.")
    if months <= 6:
        return _lt(f"Onumuzdeki {months} ay icinde tamamla.", f"Complete within the next {months} months.")
    return _lt(f"Bu adimi {months} ay icinde tamamla.", f"Complete this move within {months} months.")


def _feasibility_status_for_action(action: Mapping[str, Any]) -> str:
    action_status = str(action.get("action_status", "") or "").strip().lower()
    if action_status == "invalid":
        return "invalid"
    if action_status == "provisional" or bool(action.get("dependency_gate", False)):
        return "provisional"
    if action_status == "repaired":
        return "repaired"
    plan_constraint_status = str(action.get("plan_constraint_status", "") or "").strip().lower()
    if plan_constraint_status == "provisional" and (
        bool(action.get("requires_institutional_approval", False)) or bool(action.get("requires_acceptance", False))
    ):
        return "provisional"
    if plan_constraint_status == "repaired":
        return "repaired"
    return action_status or "valid"


def _feasibility_outcome_label(action: Mapping[str, Any]) -> LocalizedText | None:
    status = _feasibility_status_for_action(action)
    if status == "invalid":
        return None
    if status == "provisional":
        return _lt(
            "Dis bagimlilik nedeniyle kosullu",
            "Conditional because of an external dependency",
        )
    if status == "repaired":
        return _lt(
            "Yumusatilarak uygulanabilir",
            "Softened but usable",
        )
    return _lt(
        "Kontrollu bicimde uygulanabilir",
        "Usable as a controlled target",
    )


def _difficulty_label_text(action: Mapping[str, Any]) -> LocalizedText | None:
    label = str(action.get("difficulty_label", "") or "").strip().lower()
    if label == "high":
        return _lt("Yuksek zorluk", "High difficulty")
    if label == "moderate":
        return _lt("Orta zorluk", "Moderate difficulty")
    if label == "low":
        return _lt("Dusuk zorluk", "Low difficulty")
    return None


def _follow_through_note(action: Mapping[str, Any]) -> LocalizedText | None:
    difficulty_label = str(action.get("difficulty_label", "") or "").strip().lower()
    approval_friction = _safe_float(action.get("approval_friction", 0.0), 0.0)
    approval_probability = action.get("approval_dependent_probability", None)
    if approval_probability is not None and approval_friction >= 0.35:
        return _lt(
            "Dis onay akisindaki surtunme, bu adimin ne kadar hizli gerceklesecegini belirleyebilir.",
            "External approval friction can determine how quickly this step lands.",
        )
    if difficulty_label == "high":
        return _lt(
            "Bu adim beklenen etkiyi vermek icin duzenli takip ve davranis disiplini gerektirir.",
            "This step needs disciplined follow-through to deliver the expected effect.",
        )
    if difficulty_label == "moderate":
        return _lt(
            "Bu adim istikrarli takip gerektirir; duzen bozulursa etki zayiflayabilir.",
            "This step needs steady follow-through; impact can soften if momentum slips.",
        )
    if difficulty_label == "low":
        return _lt(
            "Bu adim gorece daha yonetilebilir gorunuyor, ancak temiz takip yine de onemli.",
            "This step looks relatively manageable, but clean follow-through still matters.",
        )
    return None


def _follow_through_readiness_card(
    readiness_label: str | None,
    *,
    plan_execution_probability: float | None,
    approval_dependent_plan_probability: float | None,
    peak_group_difficulty_score: float | None,
) -> NarrativeCard | None:
    label = str(readiness_label or "").strip().lower()
    if label not in {"low", "moderate", "high"}:
        return None
    effective_probability = _safe_float(plan_execution_probability, 0.0)
    if approval_dependent_plan_probability is not None:
        effective_probability = min(
            effective_probability,
            _safe_float(approval_dependent_plan_probability, effective_probability),
        )
    peak_difficulty = _safe_float(peak_group_difficulty_score, 0.0)
    if label == "high":
        return _card(
            "Takip hazirligi yuksek",
            "High follow-through readiness",
            (
                "Planin mevcut siralamasi uygulanabilir gorunuyor;"
                " erken takip hikayesi savunulabilir kalmaya devam ediyor."
            ),
            (
                "The current sequencing looks realistic to carry through;"
                " the early follow-through story remains defensible."
            ),
        )
    if label == "moderate":
        return _card(
            "Takip hazirligi orta",
            "Moderate follow-through readiness",
            (
                "Beklenen etkiyi almak icin istikrarli takip gerekir;"
                " ritim zayiflarsa planin etkisi yumusayabilir."
            ),
            (
                "Steady follow-through is needed to realize the expected impact;"
                " if momentum weakens, the uplift can soften."
            ),
        )
    return _card(
        "Takip hazirligi dusuk",
        "Low follow-through readiness",
        (
            "Plan hala anlamli olabilir, ancak takip zayiflarsa beklenen etki hizla dusur;"
            " bu nedenle daha kontrollu izleme gerekir."
        ),
        (
            "The plan may still matter, but expected impact falls quickly if follow-through weakens;"
            " it needs more controlled monitoring."
        ),
    )


def _normalized_constraints_applied(
    *,
    actions: Sequence[Mapping[str, Any]],
    constraint_trace: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()

    def _append(entry: dict[str, Any]) -> None:
        key = (
            str(entry.get("event_type", "") or ""),
            str(entry.get("action_group_id", "") or ""),
            str(entry.get("constraint_status", "") or ""),
            str(entry.get("constraint_family", "") or ""),
            str(entry.get("reason_code", "") or ""),
        )
        if key in seen:
            return
        seen.add(key)
        out.append(entry)

    for action in actions:
        action_status = str(action.get("action_status", "") or "").strip().lower()
        if action_status in {"", "valid", "invalid"} and not bool(action.get("was_clipped", False)):
            continue
        reason_codes = action.get("constraint_reason_codes", [])
        if not isinstance(reason_codes, list):
            reason_codes = []
        if not reason_codes:
            raw_reason = str(action.get("action_status_reason", "") or "")
            reason_codes = [code for code in raw_reason.split("|") if code]
        if not reason_codes:
            reason_codes = [""]
        for reason_code in reason_codes:
            _append(
                {
                    "event_type": "action_feasibility",
                    "step_id": str(action.get("step_id", "") or ""),
                    "action_key": str(action.get("action_key", "") or ""),
                    "action_group_id": str(action.get("action_group_id", "") or ""),
                    "feature_name": str(action.get("feature_name", action.get("technical_view", {}).get("feature_name", "")) or ""),
                    "time_months": _safe_int(action.get("time_months", 1), 1),
                    "constraint_status": action_status or "valid",
                    "constraint_family": str(action.get("constraint_family", "") or ""),
                    "reason_code": str(reason_code or ""),
                    "was_clipped": bool(action.get("was_clipped", False)),
                    "repair_applied": bool(action.get("repair_applied", False)),
                    "dependency_gate": bool(action.get("dependency_gate", False)),
                    "semantic_preserved": (
                        bool(action.get("semantic_preserved"))
                        if action.get("semantic_preserved", None) is not None
                        else action_status != "invalid"
                    ),
                }
            )

    for item in list(constraint_trace or []):
        if not isinstance(item, Mapping):
            continue
        _append(
            {
                "event_type": str(item.get("event_type", "") or ""),
                "step_id": str(item.get("step_id", "") or ""),
                "action_key": str(item.get("action_key", "") or ""),
                "action_group_id": str(item.get("action_group_id", "") or ""),
                "feature_name": str(item.get("feature_name", "") or ""),
                "time_months": _safe_int(item.get("time_months", 1), 1),
                "constraint_status": str(item.get("constraint_status", "") or ""),
                "constraint_family": str(item.get("constraint_family", "") or ""),
                "reason_code": str(item.get("reason_code", "") or ""),
                "was_clipped": bool(item.get("was_clipped", False)),
                "repair_applied": bool(item.get("repair_applied", False)),
                "dependency_gate": bool(item.get("dependency_gate", False)),
                "semantic_preserved": (
                    bool(item.get("semantic_preserved"))
                    if item.get("semantic_preserved", None) is not None
                    else None
                ),
            }
        )
    return out


def _severity_from_contribution(abs_contribution: float) -> str:
    value = abs(float(abs_contribution))
    if value >= 0.25:
        return "high"
    if value >= 0.10:
        return "moderate"
    return "low"


def narrative_confidence_label(score: float | None) -> str:
    value = _safe_float(score, 0.0)
    if value >= 0.8:
        return "high"
    if value >= 0.55:
        return "moderate"
    return "low"


def _confidence_description(label: str) -> LocalizedText:
    if label == "high":
        return _lt(
            "Anlatim, model sinyalleriyle guclu bicimde destekleniyor.",
            "The narrative is strongly supported by model signals.",
        )
    if label == "moderate":
        return _lt(
            "Anlatim destekleniyor ancak izlenmesi gereken belirsizlikler var.",
            "The narrative is supported, but some uncertainty still needs monitoring.",
        )
    return _lt(
        "Anlatim yon gosteriyor ancak daha dikkatli yorumlanmali.",
        "The narrative is directionally useful, but should be read with extra caution.",
    )


def _reason_localized_text(code: str, key: str, fallback_en: str, fallback_tr: str) -> LocalizedText:
    tpl = _REASON_TEMPLATES.get(code, {})
    if key == "title":
        return _lt(str(tpl.get("tr_title", fallback_tr)), str(tpl.get("title", fallback_en)))
    if key == "description":
        return _lt(str(tpl.get("tr_description", fallback_tr)), str(tpl.get("description", fallback_en)))
    return _lt(
        str(tpl.get("tr_remediation_hint", fallback_tr)),
        str(tpl.get("remediation_hint", fallback_en)),
    )


def build_reason_narratives(local_reasons: list[dict], max_items: int = 4) -> list[RoadmapReasonNarrative]:
    payload = build_adverse_action_payload(local_reasons, max_items=max_items)
    out: list[RoadmapReasonNarrative] = []
    for detail in payload.get("reason_details", []):
        code = str(detail.get("code", "") or "")
        out.append(
            RoadmapReasonNarrative(
                reason_code=code,
                reason_title=_reason_localized_text(
                    code,
                    "title",
                    str(detail.get("title", code.replace("_", " ").title())),
                    "Bu risk basligi onemli",
                ),
                reason_description=_reason_localized_text(
                    code,
                    "description",
                    str(detail.get("description", "Risk profile requires additional improvement on this factor.")),
                    "Bu risk faktoru ilave iyilesme gerektiriyor.",
                ),
                remediation_hint=_reason_localized_text(
                    code,
                    "remediation_hint",
                    str(detail.get("remediation_hint", "Follow the action plan and re-apply later.")),
                    "Aksiyon planini izleyin ve daha sonra yeniden basvurun.",
                ),
                reason_severity=_severity_from_contribution(
                    _safe_float(
                        next(
                            (
                                item.get("abs_contribution", 0.0)
                                for item in local_reasons
                                if _normalize_reason_code(str(item.get("feature", ""))) == code
                            ),
                            0.0,
                        ),
                        0.0,
                    )
                ),
            )
        )
    return out


def build_step_narrative(
    action: Mapping[str, Any],
    *,
    step_id: str,
    phase_id: str,
    customer_context: Mapping[str, Any] | None = None,
) -> RoadmapStepNarrative:
    business_view = action.get("business_view", {})
    if not isinstance(business_view, Mapping):
        business_view = {}
    action_key = str(business_view.get("action_key", action.get("action_key", "")) or "")
    action_group_id = str(business_view.get("action_group_id", action.get("action_group_id", "")) or "")
    action_class = str(business_view.get("action_class", action.get("action_class", "")) or "")
    template = _ACTION_NARRATIVE_TEMPLATES.get(action_key)
    action_title = str(
        business_view.get("action_title", action.get("action_title", "")) or action_key.replace("_", " ").strip()
    )
    if template is None:
        summary = (
            f"{action_title} adimini oncelikli pencere icinde tamamla.",
            f"Complete the {action_title.lower()} move within the suggested window.",
        )
        why = (
            "Bu adim, dosyanin daha guvenli ve daha uygulanabilir gorunmesine yardimci olur.",
            "This move helps the file look safer and more executable.",
        )
        expected = (
            "Bir sonraki checkpoint'te daha guclu bir sinyal beklenir.",
            "A stronger signal is expected at the next checkpoint.",
        )
        done = (
            "Aksiyon tamamlanirsa toparlanma hikayesi daha inandirici hale gelir.",
            "If the action lands, the recovery story becomes more credible.",
        )
        not_done = (
            "Aksiyon ertelenirse erken guclenme hikayesi zayif kalabilir.",
            "If the action slips, the early-improvement story may remain weak.",
        )
    else:
        summary = template["action_summary"]
        why = template["why_this_matters"]
        expected = template["expected_outcome"]
        done = template["what_happens_if_done"]
        not_done = template["what_happens_if_not_done"]
    primary_target_sentence = _primary_target_sentence(action)
    primary_recommendation, institution_condition = _build_step_recommendations(
        action,
        customer_context=customer_context,
    )
    offer_narrative = build_offer_narrative(action)
    return RoadmapStepNarrative(
        step_id=step_id,
        phase_id=phase_id,
        action_key=action_key or None,
        action_group_id=action_group_id or None,
        action_summary=_localized_pair(summary),
        primary_recommendation=primary_recommendation,
        institution_condition=institution_condition,
        why_this_matters=_localized_pair(why),
        expected_outcome=_append_localized_sentence(expected, primary_target_sentence),
        what_happens_if_done=_localized_pair(done),
        what_happens_if_not_done=_localized_pair(not_done),
        feasibility_outcome_label=_feasibility_outcome_label(action),
        difficulty_label=_difficulty_label_text(action),
        follow_through_note=_follow_through_note(action),
        action_timing_hint=_timing_hint(
            _safe_int(_primary_numeric_target(action).get("due_month", action.get("time_months", 1)), 1)
        ),
        offer_narrative=offer_narrative if action_class == "institutional" or offer_narrative else None,
    )


def build_recourse_path_render_payload(
    path: Any,
    representative_plan: Any | None = None,
    *,
    customer_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Render deterministic customer/operator summaries for a grouped recourse path.
    """

    path_payload = _payload_from_model(path) or {}
    path_type = str(path_payload.get("path_type", "") or "").strip().lower()
    path_id = str(path_payload.get("path_id", "") or "path_summary").strip()
    representative_action = _representative_action_payload(representative_plan)
    if representative_action is None:
        return {
            "customer_summary": None,
            "operator_summary": None,
            "render_version": _PATH_RENDER_VERSION,
        }

    step_narrative = build_step_narrative(
        representative_action,
        step_id=f"{path_id}:representative",
        phase_id=path_type or "path_summary",
        customer_context=customer_context,
    )
    path_label_tr, path_label_en = _PATH_TYPE_LABELS.get(path_type, ("path", "path"))
    path_label = _lt(path_label_tr, path_label_en)

    primary_recommendation = step_narrative.primary_recommendation
    target_sentence = step_narrative.expected_outcome
    institution_condition = step_narrative.institution_condition
    action_summary = step_narrative.action_summary
    if path_type == "customer_only":
        customer_summary = primary_recommendation or action_summary or target_sentence
        operator_summary = _combine_localized_texts([path_label, customer_summary, target_sentence])
    elif path_type == "institution_assisted":
        customer_summary = _prepend_localized_prefix(
            _lt("Onaylanirsa,", "If approved,"),
            primary_recommendation or institution_condition or target_sentence or action_summary,
        )
        operator_summary = _combine_localized_texts([path_label, customer_summary, institution_condition])
    else:
        core_summary = primary_recommendation or action_summary or target_sentence
        if core_summary is None:
            customer_summary = None
            operator_summary = None
        else:
            customer_summary = _combine_localized_texts(
                [
                    core_summary,
                    institution_condition
                    or _lt(
                        "Pair it with institution support so the path stays sustainable.",
                        "Pair it with institution support so the path stays sustainable.",
                    ),
                ]
            )
            operator_summary = _combine_localized_texts([path_label, customer_summary, institution_condition])

    if (
        customer_summary is None
        or operator_summary is None
        or _contains_generic_weak_language(customer_summary)
        or _contains_generic_weak_language(operator_summary)
    ):
        customer_summary = None
        operator_summary = None

    return {
        "customer_summary": customer_summary,
        "operator_summary": operator_summary,
        "render_version": _PATH_RENDER_VERSION,
    }


def _offer_terms_summary(offer_terms: Mapping[str, Any]) -> LocalizedText | None:
    if not offer_terms:
        return None
    parts_tr: list[str] = []
    parts_en: list[str] = []
    payment_delta = offer_terms.get("payment_delta_monthly")
    if payment_delta is not None:
        delta = _safe_float(payment_delta, 0.0)
        parts_tr.append(f"Aylik odemede {delta:.0f} birim degisim")
        parts_en.append(f"About {delta:.0f} monthly payment change")
    term_extension = offer_terms.get("term_extension_months")
    if term_extension:
        months = _safe_int(term_extension, 0)
        parts_tr.append(f"{months} ay vade uzatma")
        parts_en.append(f"{months} month extension")
    grace_weeks = offer_terms.get("grace_period_weeks")
    if grace_weeks:
        weeks = _safe_int(grace_weeks, 0)
        parts_tr.append(f"{weeks} hafta grace")
        parts_en.append(f"{weeks} week grace period")
    if not parts_tr:
        return None
    return _lt(", ".join(parts_tr), ", ".join(parts_en))


def build_offer_narrative(action: Mapping[str, Any]) -> OfferNarrative | None:
    contract = _offer_contract_payload(action)
    offer_type = str(contract.get("offer_type", "") or "")
    requires_approval = (
        bool(contract.get("requires_institutional_approval", False))
        or str(contract.get("institutional_approval_state", "") or "").strip().lower() in {"pending", "unknown"}
        or bool(action.get("approval_pending_semantic_only", False))
        or bool(action.get("dependency_gate", False))
    )
    requires_acceptance = bool(contract.get("requires_acceptance", False))
    if not _has_visible_offer(action) and (requires_approval or requires_acceptance):
        return None
    if not offer_type and not requires_approval and not requires_acceptance:
        return None
    template = _OFFER_NARRATIVE_TEMPLATES.get(
        offer_type,
        {
            "offer_explanation": (
                "Bu adim kurum tarafli bir teklif veya onay katmani tasiyor.",
                "This move carries an institution-side offer or approval layer.",
            ),
            "why_offered": (
                "Teklif, yalniz musteri davranisiyla saglanamayacak rahatlamayi desteklemek icin eklenir.",
                "The offer is included to support relief that customer action alone may not create.",
            ),
            "if_accepted": (
                "Teklif devreye girerse toparlanma yolu daha guclu desteklenir.",
                "If the offer lands, the recovery path gains stronger support.",
            ),
            "if_not_accepted": (
                "Teklif gelismezse plan daha davranis odakli kalir.",
                "If the offer does not land, the plan remains more behavior-led.",
            ),
        },
    )
    state_note = _offer_state_note(action)
    return OfferNarrative(
        offer_explanation=_append_localized_sentence(template["offer_explanation"], state_note),
        why_offered=_localized_pair(template["why_offered"]),
        if_accepted=_localized_pair(template["if_accepted"]),
        if_not_accepted=_localized_pair(template["if_not_accepted"]),
        offer_terms_summary=_offer_terms_summary(contract.get("offer_terms", {}) or {}),
    )


def build_checkpoint_narrative(checkpoint: Mapping[str, Any], tau: float) -> RoadmapCheckpointNarrative:
    week = _safe_int(checkpoint.get("week", 0), 0)
    checkpoint_id = str(checkpoint.get("checkpoint_id", f"week_{week}"))
    predicted_pd = _safe_float(checkpoint.get("predicted_pd", 1.0), 1.0)
    gate_pass = bool(_safe_int(checkpoint.get("gate_pass_estimate", 0), 0))
    checkpoint_status = str(checkpoint.get("status", "") or ("on_track" if gate_pass else "at_risk")).strip().lower()
    trajectory_jump_flag = bool(checkpoint.get("trajectory_jump_flag", False))
    non_monotonic_flag = bool(checkpoint.get("non_monotonic_flag", False))
    checkpoint_inconsistency_flag = bool(checkpoint.get("checkpoint_inconsistency_flag", False))
    ready = predicted_pd <= float(tau) and gate_pass

    if week == 4:
        if checkpoint_status == "missed":
            expected_state = (
                "Ilk checkpoint zayif gorunuyor; erken toparlanma sinyali henuz kurulmus degil.",
                "The first checkpoint looks weak; the early recovery signal has not formed yet.",
            )
            success = (
                "Bu noktadan sonra daha guclu destek veya yeniden planlama gerekir.",
                "From this point, the path likely needs stronger support or replanning.",
            )
            failure = (
                "Erken checkpoint kacirilirsa mevcut plan oldugu gibi savunulamaz.",
                "If the early checkpoint is missed, the current plan is no longer easy to defend as-is.",
            )
            review = (
                "Plani sikilastir, yeniden planla veya ek destek katmani ekle.",
                "Tighten the plan, replan it, or add another support layer.",
            )
        elif checkpoint_status == "at_risk":
            expected_state = (
                "Ilk 4 hafta sonunda profilin daha stabil ama halen dikkat gerektiren bir noktada olmasi beklenir.",
                "By week 4, the profile should look more stable, but still require caution.",
            )
            success = (
                "Yeni negatif sinyal uretmeden ilk checkpoint'e kadar denge korunur.",
                "Stability is preserved into the first checkpoint without creating new negative signals.",
            )
            failure = (
                "Bu sinyal zayif kalirsa planin sikilasmasi veya yeniden degerlendirilmesi gerekir.",
                "If this signal remains weak, the plan likely needs tightening or reassessment.",
            )
            review = (
                "Plani yeniden degerlendir veya destek katmani ekle.",
                "Reassess the plan or add another support layer.",
            )
        else:
            expected_state = (
                "Ilk 4 hafta sonunda profilin daha stabil gorunmesi beklenir.",
                "By week 4, the profile is expected to look more stable.",
            )
            success = (
                "Erken baski azalir ve ilk review kontrollu bir gecis sinyali verir.",
                "Early pressure eases and the first review signals a controlled pass.",
            )
            failure = (
                "Ilk sinyal gelmezse planin sikilasmasi veya yeniden degerlendirilmesi gerekir.",
                "If the early signal does not show up, the plan likely needs tightening or reassessment.",
            )
            review = (
                "Plani surdur ve orta vadeli guclenmeye gec.",
                "Continue the plan and move into the mid-term strengthening phase.",
            )
    elif week == 12:
        if checkpoint_status == "missed":
            expected_state = (
                "Orta vadeli guclenme beklenen seviyeye ulasmamis gorunuyor.",
                "The mid-term strengthening does not yet appear to be reaching the required level.",
            )
            success = (
                "Bu noktadan sonra daha agir mudahale veya kurumsal destek gerekebilir.",
                "From here, the path may require heavier intervention or institution-side support.",
            )
            failure = (
                "12 haftalik pencere de zayif kalirsa mevcut hikaye tek basina yeterli gorunmez.",
                "If the 12-week window stays weak, the current story no longer looks sufficient on its own.",
            )
            review = (
                "Daha guclu bir mudahale yoluna gec.",
                "Escalate into a stronger intervention path.",
            )
        else:
            expected_state = (
                "Orta vadede dosyanin yeniden basvuruya daha yakin gorunmesi beklenir.",
                "By the mid-term checkpoint, the file should look closer to re-application readiness.",
            )
            success = (
                "Profil kontrollu bicimde yeniden degerlendirme veya onay gorunumune yaklasir.",
                "The profile moves into a controlled reassessment or approval-ready posture.",
            )
            failure = (
                "Bu noktada ilerleme zayif kalirsa daha agir mudahale veya teklif destegi gerekebilir.",
                "If progress is still weak here, heavier intervention or offer support may be required.",
            )
            review = (
                "Guclu gorunum korunuyorsa iyilesmeyi kalicilastir."
                if gate_pass
                else "Daha guclu bir mudahale yoluna gec.",
                "If the signal is healthy, protect the gains and make them durable."
                if gate_pass
                else "Escalate into a stronger intervention path.",
            )
    else:
        if checkpoint_status == "missed" or trajectory_jump_flag or non_monotonic_flag:
            expected_state = (
                "Uzun vadeli iyilesme tutarsiz gorunuyor; kazanimlar kalicilasmakta zorlanabilir.",
                "The long-horizon improvement looks unstable; gains may be struggling to hold.",
            )
            success = (
                "Yol haritasi korunacaksa daha sik kontrol ve daha temiz sinyaller gerekir.",
                "If the roadmap is to hold, it needs tighter monitoring and cleaner signals.",
            )
            failure = (
                "Uzun vadeli kazanim kalicilasmiyorsa onceki iyilesme hikayesi kirilgan kalir.",
                "If the long-horizon gain does not hold, the earlier improvement story remains fragile.",
            )
            review = (
                "Plani yeniden degerlendir ve yeni risk olusumunu durdur.",
                "Reassess the plan and stop any new risk from forming.",
            )
        else:
            expected_state = (
                "Uzun vadede iyilesmenin kalici hale gelmesi beklenir.",
                "Over the long horizon, the improvement should become durable.",
            )
            success = (
                "Toparlanma hikayesi kirilmadan korunur ve profil daha guvenilir hale gelir.",
                "The recovery story holds together and the profile becomes more dependable.",
            )
            failure = (
                "Uzun vadeli kazanim kalicilasmiyorsa onceki iyilesme hikayesi kirilgan kalir.",
                "If the long-horizon gain does not hold, the earlier improvement story remains fragile.",
            )
            review = (
                "Mevcut duzeni koru ve yeni risk yaratma.",
                "Protect the current structure and avoid creating new risk.",
            )

    if checkpoint_inconsistency_flag:
        review = (
            "Checkpoint sinyalini tekrar incele; etiket ile metrikler ayni hikayeyi anlatmiyor.",
            "Review the checkpoint signal again; the label and metrics are not telling the same story.",
        )

    return RoadmapCheckpointNarrative(
        checkpoint_id=checkpoint_id,
        week=week,
        expected_state=_localized_pair(expected_state),
        success_condition=_localized_pair(success),
        failure_implication=_localized_pair(failure),
        review_action=_localized_pair(review),
    )


def _risk_card(base_pd: float, tau: float) -> NarrativeCard:
    margin = float(base_pd) - float(tau)
    if margin <= 0:
        return _card(
            "Esik altinda risk",
            "Below-threshold risk",
            "Profil su anda politika esiginin altinda ve karar gorunumu daha dengeli.",
            "The profile is already below threshold and the decision outlook is more balanced.",
        )
    if margin <= 0.07:
        return _card(
            "Sinira yakin risk",
            "Near-threshold risk",
            "Profil toparlanabilir ama hala yakindan izlenmeli.",
            "The profile is recoverable but still needs close monitoring.",
        )
    if margin <= 0.15:
        return _card(
            "Yuksek baskili risk",
            "Elevated risk pressure",
            "Basvuru baskisi belirgin; ilk iyilesme sinyali kritik onemde.",
            "Application pressure is clearly elevated; the first improvement signal matters.",
        )
    return _card(
        "Belirgin risk baskisi",
        "Material risk pressure",
        "Profilin yeniden guven kazanmasi icin daha guclu iyilesme gerekir.",
        "The profile needs stronger improvement before it can rebuild lender confidence.",
    )


def _offer_status_card(actions: Sequence[Mapping[str, Any]]) -> NarrativeCard:
    offer_actions = [a for a in actions if _has_visible_offer(a)]
    if not offer_actions:
        return _card(
            "Kurum teklifi yok",
            "No institution offer",
            "Bu yol, agirlikli olarak musteri aksiyonlariyla ilerliyor.",
            "This path relies primarily on customer action rather than an institution-side offer.",
        )
    if any(
        bool(_offer_contract_payload(a).get("requires_institutional_approval", False))
        or str(_offer_contract_payload(a).get("institutional_approval_state", "") or "").strip().lower() in {"pending", "unknown"}
        or bool(a.get("approval_pending_semantic_only", False))
        for a in offer_actions
    ):
        return _card(
            "Teklif kurum onayina bagli",
            "Offer depends on institution approval",
            "Teklif var ancak devreye girmesi icin kurum onayi gerekiyor.",
            "An offer exists, but it still depends on institution approval.",
        )
    if any(bool(_offer_contract_payload(a).get("requires_acceptance", False)) for a in offer_actions):
        return _card(
            "Musteri kabulune bagli teklif",
            "Offer requires customer acceptance",
            "Teklif acik ancak etkinin gorulmesi musteri kabulune bagli.",
            "The offer is available, but its impact depends on customer acceptance.",
        )
    offer_type = str(_offer_contract_payload(offer_actions[0]).get("offer_type", "") or "")
    if offer_type == "installment_terms":
        return _card(
            "Taksitlendirme destegi var",
            "Installment support included",
            "Kurumsal taksitlendirme, musteri aksiyonlarini destekliyor.",
            "An institution-side installment offer supports the customer actions.",
        )
    return _card(
        "Kurum teklifi dahil",
        "Institution offer included",
        "Plan, musteri aksiyonlarinin yanina kurumsal bir destek katmani ekliyor.",
        "The plan adds an institution-side support layer next to the customer actions.",
    )


def _readiness_stage(base_pd: float, checkpoints: Sequence[Mapping[str, Any]], tau: float) -> tuple[str, int | None]:
    if float(base_pd) <= float(tau):
        return ("now", 0)
    for checkpoint in checkpoints:
        week = _safe_int(checkpoint.get("week", 0), 0)
        if week <= 0:
            continue
        if _safe_float(checkpoint.get("predicted_pd", 1.0), 1.0) <= float(tau) and bool(
            _safe_int(checkpoint.get("gate_pass_estimate", 0), 0)
        ):
            return (f"week_{week}", week)
    return ("not_ready_yet", None)


def _normalize_business_decision_status(status: str) -> str:
    normalized = str(status or "").upper()
    if normalized == "APPROVED":
        return "APPROVED"
    if normalized == "REJECTED":
        return "REJECTED"
    return "CONDITIONAL"


def _resolve_business_readiness_stage(
    expected_readiness: str | None,
    *,
    base_pd: float,
    checkpoints: Sequence[Mapping[str, Any]],
    tau: float,
) -> tuple[str, int | None]:
    normalized = str(expected_readiness or "").strip().lower()
    if normalized == "now":
        return ("now", 0)
    if normalized in {"week_4", "week4"}:
        return ("week_4", 4)
    if normalized in {"week_12", "week12"}:
        return ("week_12", 12)
    if normalized in {"week_24", "week24"}:
        return ("week_24", 24)
    if normalized in {"not_ready", "unknown_review"}:
        return ("not_ready_yet", None)
    return _readiness_stage(base_pd, checkpoints, tau)


def _decision_summary_line(
    status: str,
    *,
    decision_reason_summary: str | None = None,
    conditional_type: str | None = None,
    rejection_type: str | None = None,
    upgrade_condition: str | None = None,
) -> LocalizedText:
    normalized = _normalize_business_decision_status(status)
    has_upgrade_condition = bool(str(upgrade_condition or "").strip())
    if normalized == "APPROVED":
        return _lt(
            "Plan, mevcut kanitlarla onay cizgisini karsiliyor.",
            str(decision_reason_summary or "The current plan meets the approval policy under the current evidence."),
        )
    if normalized == "REJECTED":
        if str(rejection_type or "").upper() == "NO_PATH":
            return _lt(
                "Su an icin uygulanabilir bir yol gorunmuyor.",
                str(decision_reason_summary or "No actionable plan is available right now."),
            )
        if str(rejection_type or "").upper() == "LOW_IMPACT":
            return _lt(
                "Mevcut plan riski yeterince iyilestirmiyor.",
                str(decision_reason_summary or "The current plan would not improve risk enough yet."),
            )
        return _lt(
            "Mevcut planin gerceklesme gucu henuz yeterli degil.",
            str(decision_reason_summary or "The current plan is not realistic enough to rely on."),
        )
    if str(conditional_type or "").upper() == "DATA_ISSUE":
        return _lt(
            "Plan yon olarak anlamli, ancak karar verisinin kontrollu bicimde tamamlanmasi gerekiyor.",
            str(decision_reason_summary or "The plan looks directionally viable, but decision data needs controlled review."),
        )
    if str(conditional_type or "").upper() == "OFFER_GATED":
        return _lt(
            "Plan anlamli, ancak kurum desteginin tamamen aktiflesmesi gerekiyor.",
            str(decision_reason_summary or "The plan is viable, but institution-side support is not fully active yet."),
        )
    if str(conditional_type or "").upper() == "TIME_GATED":
        return _lt(
            "Plan anlamli, ancak onay icin biraz daha zaman gerekiyor.",
            str(decision_reason_summary or "The plan is viable, but more time is needed before approval."),
        )
    if has_upgrade_condition:
        return _lt(
            "Plan anlamli, ancak belirli esikler tamamlanmadan onay gorunumu guclenmiyor.",
            str(decision_reason_summary or "The plan is viable, but specific thresholds still need to be met."),
        )
    return _lt(
        "Plan anlamli, ancak uygulama guveni henuz yeterince guclu degil.",
        str(decision_reason_summary or "The plan is viable, but execution confidence is not strong enough yet."),
    )


def _decision_view_card(
    status: str,
    readiness_stage: str,
    *,
    conditional_type: str | None = None,
    decision_reason_summary: str | None = None,
    upgrade_condition: str | None = None,
) -> NarrativeCard:
    normalized = _normalize_business_decision_status(status)
    if normalized == "APPROVED":
        return _card(
            "Onaya uygun gorunum",
            "Approval-ready view",
            "Mevcut sinyaller kontrollu bicimde onay gorunumunu destekliyor.",
            str(decision_reason_summary or "The current signals support an approval-ready view in a controlled way."),
        )
    if normalized == "REJECTED":
        return _card(
            "Henuz erken",
            "Not ready yet",
            "Mevcut sinyaller, daha fazla iyilesme olmadan olumlu karar icin yeterli degil.",
            str(decision_reason_summary or "Current signals are still not sufficient for a positive decision without more improvement."),
        )
    if str(conditional_type or "").upper() == "OFFER_GATED":
        return _card(
            "Kosullu gorunum",
            "Conditional view",
            "Plan anlamli, ancak kurum desteginin aktiflesmesi gerekiyor.",
            str(decision_reason_summary or "The plan is viable, but institution-side support still needs to activate."),
        )
    if str(conditional_type or "").upper() == "TIME_GATED" or readiness_stage in {"week_12", "week_24"}:
        return _card(
            "Kosullu gorunum",
            "Conditional view",
            "Plan anlamli, ancak onay gorunumu icin biraz daha zaman gerekiyor.",
            str(decision_reason_summary or "The plan is viable, but it still needs more time before it looks approval-ready."),
        )
    if str(conditional_type or "").upper() == "DATA_ISSUE":
        return _card(
            "Kosullu gorunum",
            "Conditional view",
            "Plan yon olarak anlamli, ancak karar verisinin kontrollu sekilde tamamlanmasi gerekiyor.",
            str(decision_reason_summary or "The plan looks viable, but the decision data still needs controlled review."),
        )
    if str(upgrade_condition or "").strip():
        return _card(
            "Kosullu gorunum",
            "Conditional view",
            "Plan anlamli, ancak belirli esikler tamamlanmadan onay gorunumu guclenmiyor.",
            str(decision_reason_summary or "The plan is viable, but specific thresholds still need to be met before approval."),
        )
    return _card(
        "Kosullu gorunum",
        "Conditional view",
        "Plan ilerliyor, ancak uygulama guveni henuz tam olarak guclenmedi.",
        str(decision_reason_summary or "The plan is progressing, but execution confidence is not strong enough yet."),
    )


def _time_to_readiness_card(readiness_stage: str, readiness_week: int | None) -> NarrativeCard:
    if readiness_stage == "now":
        return _card(
            "Simdi",
            "Now",
            "Profil mevcut gorunumde yeniden basvuruya uygun.",
            "The profile is already suitable for re-application in the current view.",
        )
    if readiness_week:
        return _card(
            f"{readiness_week} hafta",
            f"{readiness_week} weeks",
            "Plan tutarsa bu pencerede yeniden basvuru hazirligi beklenir.",
            "If the plan holds, re-application readiness is expected in this window.",
        )
    return _card(
        "Belirsiz",
        "Uncertain",
        "Mevcut sinyaller hazirlik zamanini netlestirmiyor; planin guclenmesi gerekiyor.",
        "Current signals do not yet pin down readiness timing; the plan still needs strengthening.",
    )


def _recommended_path_card(actions: Sequence[Mapping[str, Any]], offer_status: NarrativeCard) -> NarrativeCard:
    has_institutional = any(str(a.get("action_class", "") or "") == "institutional" for a in actions)
    if has_institutional:
        return _card(
            "Once dengele, sonra kurum destegiyle guclendir",
            "Stabilize first, then strengthen with institution support",
            "Plan, erken davranis dengesini kurup uygun noktada kurumsal destek ekliyor.",
            "The plan stabilizes behavior early and adds institution-side support at the right moment.",
        )
    if "No institution offer" in offer_status.label.en or "Kurum teklifi yok" in offer_status.label.tr:
        return _card(
            "Once dengele, sonra basvuru hazirligini kur",
            "Stabilize first, then rebuild application readiness",
            "Plan, erken baskiyi azaltip orta vadede daha guclu bir basvuru hikayesi kuruyor.",
            "The plan reduces early pressure and then builds a stronger mid-term application story.",
        )
    return _card(
        "Kontrollu toparlanma yolu",
        "Controlled recovery path",
        "Plan, kademeli ilerleme ile karari daha guvenli hale getiriyor.",
        "The plan makes the decision story safer through phased progress.",
    )


def _checkpoint_4w_card(checkpoints: Sequence[Mapping[str, Any]], tau: float) -> NarrativeCard:
    cp4 = next((cp for cp in checkpoints if _safe_int(cp.get("week", 0), 0) == 4), None)
    if cp4 is None:
        return _card(
            "4 haftalik checkpoint hazir degil",
            "4-week checkpoint unavailable",
            "Bu plan icin ilk review yorumu henuz olusmadi.",
            "The first review view is not yet available for this plan.",
        )
    ready = _safe_float(cp4.get("predicted_pd", 1.0), 1.0) <= float(tau) and bool(_safe_int(cp4.get("gate_pass_estimate", 0), 0))
    checkpoint_status = str(cp4.get("status", "") or ("on_track" if ready else "at_risk")).strip().lower()
    if ready:
        return _card(
            "Ilk 4 haftada olumlu gecis",
            "Positive first 4-week signal",
            "Erken checkpoint kontrollu bir guclenme sinyali veriyor.",
            "The early checkpoint shows a controlled strengthening signal.",
        )
    if checkpoint_status == "missed":
        return _card(
            "Ilk 4 hafta zayif gorunuyor",
            "The first 4 weeks look weak",
            "Erken checkpoint kaciyor; planin sikilasmasi veya yeniden kurulmasi gerekebilir.",
            "The early checkpoint is being missed; the plan may need tightening or a reset.",
        )
    return _card(
        "Ilk 4 hafta denge kurma asamasi",
        "First 4 weeks are a stabilization stage",
        "Erken pencerede amac tam onay degil, baskiyi azaltip hikayeyi duzeltmek.",
        "In the early window the goal is not full approval, but reducing pressure and repairing the story.",
    )


def _expected_result_card(base_pd: float, checkpoints: Sequence[Mapping[str, Any]], readiness_stage: str, readiness_week: int | None) -> NarrativeCard:
    latest_pd = float(base_pd)
    if checkpoints:
        latest_pd = min(_safe_float(cp.get("predicted_pd", latest_pd), latest_pd) for cp in checkpoints)
    if readiness_stage == "now":
        return _card(
            "Profil su anda yeniden basvuruya uygun",
            "The profile is approval-ready now",
            "Plan, mevcut gorunumu karar esiginin guvenli tarafinda tutabiliyor.",
            "The plan keeps the current view on the safe side of the decision threshold.",
        )
    if readiness_week is not None:
        return _card(
            f"{readiness_week} hafta icinde yeniden basvuruya hazirlik",
            f"Re-application readiness in {readiness_week} weeks",
            "Profilin bu pencere icinde daha savunulabilir ve daha kontrollu hale gelmesi bekleniyor.",
            "The profile is expected to become more defensible and controlled in this window.",
        )
    return _card(
        "Toparlaniyor ama henuz hazir degil",
        "Improving but not yet ready",
        "Risk gorunumu iyilesse de karar hikayesinin daha guclu hale gelmesi gerekiyor.",
        "The risk view improves, but the decision story still needs more strengthening.",
    )


def build_executive_summary(
    *,
    base_pd: float,
    tau: float,
    checkpoints: Sequence[Mapping[str, Any]],
    actions: Sequence[Mapping[str, Any]],
    status: str,
    confidence_label: str,
    plan_execution_probability: float | None = None,
    approval_dependent_plan_probability: float | None = None,
    follow_through_readiness_label: str | None = None,
    peak_group_difficulty_score: float | None = None,
    expected_readiness: str | None = None,
    decision_reason_summary: str | None = None,
    conditional_type: str | None = None,
    rejection_type: str | None = None,
    upgrade_condition: str | None = None,
) -> RoadmapExecutiveSummary:
    readiness_stage, readiness_week = _resolve_business_readiness_stage(
        expected_readiness,
        base_pd=base_pd,
        checkpoints=checkpoints,
        tau=tau,
    )
    offer_status = _offer_status_card(actions)
    decision_view = _decision_view_card(
        status,
        readiness_stage,
        conditional_type=conditional_type,
        decision_reason_summary=decision_reason_summary,
        upgrade_condition=upgrade_condition,
    )
    time_to_readiness = _time_to_readiness_card(readiness_stage, readiness_week)
    expected_result = _expected_result_card(base_pd, checkpoints, readiness_stage, readiness_week)
    return RoadmapExecutiveSummary(
        headline=_lt(
            "Musteri icin kontrollu ve kisisellestirilmis bir toparlanma yolu kuruldu.",
            "A controlled and personalized recovery path is now in place for the customer.",
        ),
        summary_line=_decision_summary_line(
            status,
            decision_reason_summary=decision_reason_summary,
            conditional_type=conditional_type,
            rejection_type=rejection_type,
            upgrade_condition=upgrade_condition,
        ),
        risk_start=_risk_card(base_pd, tau),
        recommended_path=_recommended_path_card(actions, offer_status),
        offer_status=offer_status,
        checkpoint_4w_summary=_checkpoint_4w_card(checkpoints, tau),
        expected_result=expected_result,
        follow_through_readiness=_follow_through_readiness_card(
            follow_through_readiness_label,
            plan_execution_probability=plan_execution_probability,
            approval_dependent_plan_probability=approval_dependent_plan_probability,
            peak_group_difficulty_score=peak_group_difficulty_score,
        ),
        decision_view=decision_view,
        time_to_readiness=time_to_readiness,
        narrative_confidence=_card(
            confidence_label.replace("_", " ").capitalize(),
            confidence_label.replace("_", " ").capitalize(),
            _confidence_description(confidence_label).tr,
            _confidence_description(confidence_label).en,
        ),
    )


def build_customer_roadmap_narrative(
    *,
    base_pd: float,
    tau: float,
    phases: Sequence[Mapping[str, Any]],
    checkpoints: Sequence[Mapping[str, Any]],
    status: str,
    local_reason_bundle: Mapping[str, Any] | None = None,
    constraint_trace: Sequence[Mapping[str, Any]] | None = None,
    plan_execution_probability: float | None = None,
    approval_dependent_plan_probability: float | None = None,
    offer_acceptance_probability: float | None = None,
    combined_plan_realization_probability: float | None = None,
    mean_group_difficulty_score: float | None = None,
    peak_group_difficulty_score: float | None = None,
    follow_through_readiness_label: str | None = None,
    decision_status_internal: str | None = None,
    decision_confidence: float | None = None,
    expected_readiness: str | None = None,
    decision_reason_summary: str | None = None,
    decision_reason_primary: str | None = None,
    rejection_type: str | None = None,
    conditional_type: str | None = None,
    upgrade_condition: str | None = None,
    decision_policy_version: str | None = None,
    decision_gate_trace: Mapping[str, Any] | None = None,
    offer_maturity: str | None = None,
    customer_context: Mapping[str, Any] | None = None,
) -> CustomerRoadmapNarrative:
    local_reason_bundle = local_reason_bundle or {}
    reason_rows = list(local_reason_bundle.get("reasons", [])) if isinstance(local_reason_bundle.get("reasons", []), list) else []
    meta = local_reason_bundle.get("meta", {}) if isinstance(local_reason_bundle.get("meta", {}), dict) else {}
    confidence_score = _safe_float(meta.get("explainability_confidence", 0.0), 0.0)
    confidence_label = narrative_confidence_label(confidence_score)

    step_narratives: list[RoadmapStepNarrative] = []
    raw_actions: list[Mapping[str, Any]] = []
    feature_changes: list[dict[str, Any]] = []
    primary_numeric_targets: list[dict[str, Any]] = []
    approval_dependencies: list[dict[str, Any]] = []
    diagnostic_flags: list[str] = []
    seen_approval_steps: set[str] = set()
    representative_steps: dict[str, tuple[str, Mapping[str, Any]]] = {}
    step_order: list[str] = []

    for phase in phases:
        phase_id = str(phase.get("phase_id", "") or "")
        for step in list(phase.get("steps", [])):
            if not isinstance(step, Mapping):
                continue
            business_view = step.get("business_view", {})
            if not isinstance(business_view, Mapping):
                business_view = {}
            technical_view = step.get("technical_view", {})
            if not isinstance(technical_view, Mapping):
                technical_view = {}
            raw_actions.append(step)
            step_id = str(step.get("step_id", "") or "")
            if step_id not in representative_steps:
                representative_steps[step_id] = (phase_id, step)
                step_order.append(step_id)
            elif _prefer_primary_target_step(representative_steps[step_id][1], step):
                representative_steps[step_id] = (phase_id, step)
            feature_changes.append(
                {
                    "step_id": step_id,
                    "phase_id": phase_id,
                    "feature_name": str(technical_view.get("feature_name", step.get("feature_name", "")) or ""),
                    "action_key": str(business_view.get("action_key", step.get("action_key", "")) or ""),
                    "action_title": str(business_view.get("action_title", step.get("action_title", "")) or ""),
                    "current_value": _safe_float(technical_view.get("current_value", step.get("current_value", 0.0)), 0.0),
                    "target_value": _safe_float(technical_view.get("target_value", step.get("target_value", 0.0)), 0.0),
                    "delta": _safe_float(technical_view.get("delta", step.get("delta", 0.0)), 0.0),
                    "time_months": _safe_int(technical_view.get("time_months", step.get("time_months", 0)), 0),
                }
            )
            primary_target = _primary_numeric_target(step)
            if primary_target:
                primary_numeric_targets.append(
                    {
                        "step_id": step_id,
                        "phase_id": phase_id,
                        "action_key": str(business_view.get("action_key", step.get("action_key", "")) or ""),
                        "action_title": str(business_view.get("action_title", step.get("action_title", "")) or ""),
                        "primary_numeric_target": dict(primary_target),
                    }
                )
            if (
                (
                    bool(_offer_contract_payload(step).get("requires_institutional_approval", False))
                    or bool(_offer_contract_payload(step).get("requires_acceptance", False))
                    or _has_visible_offer(step)
                )
                and step_id not in seen_approval_steps
            ):
                contract = _offer_contract_payload(step)
                approval_dependencies.append(
                    {
                        "step_id": step_id,
                        "action_key": str(business_view.get("action_key", step.get("action_key", "")) or ""),
                        "action_title": str(business_view.get("action_title", step.get("action_title", "")) or ""),
                        "institutional_approval_state": str(contract.get("institutional_approval_state", "") or ""),
                        "requires_institutional_approval": bool(contract.get("requires_institutional_approval", False)),
                        "requires_acceptance": bool(contract.get("requires_acceptance", False)),
                        "offer_type": str(contract.get("offer_type", "") or ""),
                        "offer_contract": contract if _has_visible_offer(step) else None,
                        "offer_policy_arm": contract.get("offer_policy_arm"),
                        "offer_scoring_profile": contract.get("offer_scoring_profile"),
                        "term_generation_rule": contract.get("term_generation_rule"),
                        "approval_dependent_probability": step.get("approval_dependent_probability"),
                    }
                )
                seen_approval_steps.add(step_id)
            for flag in list(step.get("diagnostic_flags", [])):
                flag_str = str(flag)
                if flag_str and flag_str not in diagnostic_flags:
                    diagnostic_flags.append(flag_str)

    for step_id in step_order:
        phase_id, representative_step = representative_steps[step_id]
        step_narratives.append(
            build_step_narrative(
                representative_step,
                step_id=step_id,
                phase_id=phase_id,
                customer_context=customer_context,
            )
        )

    sorted_checkpoints = sorted(
        [checkpoint for checkpoint in checkpoints if isinstance(checkpoint, Mapping)],
        key=lambda checkpoint: _safe_int(checkpoint.get("week", 0), 0),
    )
    checkpoint_narratives = [
        build_checkpoint_narrative(checkpoint, tau)
        for checkpoint in sorted_checkpoints
    ]
    reason_narratives = build_reason_narratives(reason_rows, max_items=3)
    technical_reason_narratives = build_reason_narratives(reason_rows, max_items=max(3, len(reason_rows)))
    explainability_reasons = [
        {
            "reason_code": reason.reason_code,
            "reason_title": reason.reason_title.model_dump(mode="json"),
            "reason_description": reason.reason_description.model_dump(mode="json"),
            "remediation_hint": reason.remediation_hint.model_dump(mode="json"),
            "reason_severity": reason.reason_severity,
            "abs_contribution": _safe_float(
                next(
                    (
                        item.get("abs_contribution", 0.0)
                        for item in reason_rows
                        if _normalize_reason_code(str(item.get("feature", ""))) == reason.reason_code
                    ),
                    0.0,
                ),
                0.0,
            ),
        }
        for reason in technical_reason_narratives
    ]
    executive_summary = build_executive_summary(
        base_pd=base_pd,
        tau=tau,
        checkpoints=checkpoints,
        actions=raw_actions,
        status=status,
        confidence_label=confidence_label,
        plan_execution_probability=plan_execution_probability,
        approval_dependent_plan_probability=approval_dependent_plan_probability,
        follow_through_readiness_label=follow_through_readiness_label,
        peak_group_difficulty_score=peak_group_difficulty_score,
        expected_readiness=expected_readiness,
        decision_reason_summary=decision_reason_summary,
        conditional_type=conditional_type,
        rejection_type=rejection_type,
        upgrade_condition=upgrade_condition,
    )
    execution_step_details = []
    for step_id in step_order:
        _, representative_step = representative_steps[step_id]
        execution_step_details.append(
            {
                "step_id": step_id,
                "difficulty_score": representative_step.get("difficulty_score"),
                "difficulty_label": representative_step.get("difficulty_label"),
                "action_execution_probability": representative_step.get("action_execution_probability"),
                "action_group_execution_probability": representative_step.get("action_group_execution_probability"),
                "approval_dependent_probability": representative_step.get("approval_dependent_probability"),
                "difficulty_drivers": dict(representative_step.get("difficulty_drivers", {}) or {}),
                "approval_friction": representative_step.get("approval_friction"),
            }
        )
    for checkpoint in sorted_checkpoints:
        for key in (
            "trajectory_jump_flag",
            "non_monotonic_flag",
            "checkpoint_inconsistency_flag",
        ):
            if bool(checkpoint.get(key, False)) and key not in diagnostic_flags:
                diagnostic_flags.append(key)
    return CustomerRoadmapNarrative(
        executive_summary=executive_summary,
        steps=step_narratives,
        checkpoints=checkpoint_narratives,
        reasons=reason_narratives,
        technical_reveal=RoadmapTechnicalReveal(
            feature_changes=feature_changes,
            primary_numeric_targets=primary_numeric_targets,
            explainability_reasons=explainability_reasons,
            constraints_applied=_normalized_constraints_applied(actions=raw_actions, constraint_trace=constraint_trace),
            approval_dependencies=approval_dependencies,
            diagnostic_flags=diagnostic_flags,
            execution_details={
                "plan_execution_probability": plan_execution_probability,
                "approval_dependent_plan_probability": approval_dependent_plan_probability,
                "offer_acceptance_probability": offer_acceptance_probability,
                "combined_plan_realization_probability": combined_plan_realization_probability,
                "mean_group_difficulty_score": mean_group_difficulty_score,
                "peak_group_difficulty_score": peak_group_difficulty_score,
                "follow_through_readiness_label": follow_through_readiness_label,
                "step_execution_details": execution_step_details,
            },
            decision_details={
                "decision_status": _normalize_business_decision_status(status),
                "decision_status_internal": str(decision_status_internal or ""),
                "decision_confidence": decision_confidence,
                "expected_readiness": expected_readiness,
                "decision_reason_summary": decision_reason_summary,
                "decision_reason_primary": decision_reason_primary,
                "rejection_type": rejection_type,
                "conditional_type": conditional_type,
                "upgrade_condition": upgrade_condition,
                "decision_policy_version": decision_policy_version,
                "decision_gate_trace": dict(decision_gate_trace or {}),
                "offer_maturity": offer_maturity,
            },
            confidence_inputs={
                "local_explainability_confidence": confidence_score,
                "local_shap_stability_score": _safe_float(meta.get("stability_score", 0.0), 0.0),
                "local_shap_baseline_drift_l1": _safe_float(meta.get("baseline_drift_l1", 0.0), 0.0),
                "plan_execution_probability": plan_execution_probability,
                "approval_dependent_plan_probability": approval_dependent_plan_probability,
                "offer_acceptance_probability": offer_acceptance_probability,
                "combined_plan_realization_probability": combined_plan_realization_probability,
            },
            narrative_confidence_label=confidence_label,
            narrative_confidence_score=confidence_score,
        ),
    )


def _normalize_reason_code(feature: str) -> str:
    f = str(feature).strip().lower()
    if f in _ADVERSE_ACTION_REASON_MAP:
        return _ADVERSE_ACTION_REASON_MAP[f]
    safe = "".join(ch if ch.isalnum() else "_" for ch in f).strip("_")
    return f"risk_factor_{safe}" if safe else "risk_factor_unknown"


def build_adverse_action_reasons(local_reasons: list[dict], max_items: int = 4) -> list[str]:
    """
    Converts local explanation contributions into regulator-friendly reason codes.

    Rules:
    - only risk-increasing drivers are considered
    - reasons are ordered by absolute contribution descending
    - duplicates are removed while preserving order
    """
    if not local_reasons:
        return []
    ranked = sorted(
        [
            r
            for r in local_reasons
            if str(r.get("direction", "")).strip().lower() == "increase_risk"
        ],
        key=lambda r: float(r.get("abs_contribution", 0.0)),
        reverse=True,
    )
    out: list[str] = []
    seen: set[str] = set()
    for r in ranked:
        code = _normalize_reason_code(str(r.get("feature", "")))
        if code in seen:
            continue
        seen.add(code)
        out.append(code)
        if len(out) >= max(1, int(max_items)):
            break
    return out


def validate_reason_specificity(reason_codes: list[str]) -> bool:
    if not reason_codes:
        return False
    generic_tokens = {"unknown", "other", "misc", "risk_factor_unknown"}
    for code in reason_codes:
        c = str(code).strip().lower()
        if not c:
            return False
        if c in generic_tokens:
            return False
        if c.endswith("_unknown"):
            return False
    return True


def build_adverse_action_payload(local_reasons: list[dict], max_items: int = 4) -> dict:
    principal = build_adverse_action_reasons(local_reasons, max_items=max_items)
    details: list[dict[str, str]] = []
    for code in principal:
        tpl = _REASON_TEMPLATES.get(code, {})
        details.append(
            {
                "code": code,
                "title": str(tpl.get("title", code.replace("_", " ").capitalize())),
                "description": str(
                    tpl.get(
                        "description",
                        "Risk profile requires additional improvement on this factor.",
                    )
                ),
                "remediation_hint": str(
                    tpl.get(
                        "remediation_hint",
                        "Follow recourse plan actions for this factor and re-apply.",
                    )
                ),
            }
        )
    notice_text = "; ".join([d["title"] for d in details]) if details else "No principal reasons generated."
    return {
        "principal_reasons": principal,
        "specificity_ok": bool(validate_reason_specificity(principal)),
        "reason_details": details,
        "notice_text": notice_text,
    }
