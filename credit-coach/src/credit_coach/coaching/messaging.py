from __future__ import annotations

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


def _lt(tr: str, en: str) -> LocalizedText:
    return LocalizedText(tr=str(tr), en=str(en))


def _localized_pair(values: tuple[str, str]) -> LocalizedText:
    tr, en = values
    return _lt(tr, en)


def _card(label_tr: str, label_en: str, desc_tr: str, desc_en: str) -> NarrativeCard:
    return NarrativeCard(label=_lt(label_tr, label_en), description=_lt(desc_tr, desc_en))


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


def _format_pct(value: float) -> str:
    return f"%{int(round(float(value) * 100))}"


def _format_scalar(value: float) -> str:
    numeric = float(value)
    if abs(numeric - round(numeric)) < 1e-9:
        return f"{int(round(numeric)):,}"
    return f"{numeric:,.1f}".rstrip("0").rstrip(".")


def _format_primary_target_value(value: float, unit: str, *, locale: str) -> str:
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


def _primary_target_sentence(action: Mapping[str, Any]) -> LocalizedText | None:
    target = _primary_numeric_target(action)
    metric_key = str(target.get("metric_key", "") or "")
    if not metric_key:
        return None
    unit = str(target.get("unit", "") or "")
    target_value = _safe_float(target.get("target_value", 0.0), 0.0)
    delta_value = _safe_float(target.get("delta_value", 0.0), 0.0)
    direction = str(target.get("direction", "") or "decrease")
    label_tr, label_en = _PRIMARY_TARGET_METRIC_LABELS.get(
        metric_key,
        (metric_key.replace("_", " "), metric_key.replace("_", " ")),
    )
    verb_tr, verb_en = _primary_target_direction_verb(direction)
    target_tr = _format_primary_target_value(target_value, unit, locale="tr")
    target_en = _format_primary_target_value(target_value, unit, locale="en")
    delta_tr = _format_primary_target_delta(delta_value, unit, locale="tr")
    delta_en = _format_primary_target_delta(delta_value, unit, locale="en")
    if unit == "boolean_state":
        return _lt(
            f"Hedef: {label_tr} durumunu {target_tr} seviyesine getir ({delta_tr}).",
            f"Target: move {label_en} to {target_en} ({delta_en}).",
        )
    return _lt(
        f"Hedef: {label_tr} icin {target_tr} seviyesine {verb_tr} ({delta_tr}).",
        f"Target: {verb_en} {label_en} to {target_en} ({delta_en}).",
    )


def _timing_hint(time_months: int) -> LocalizedText:
    months = max(1, int(time_months))
    if months <= 1:
        return _lt("Hemen, bu ay icinde baslat.", "Start immediately, within this month.")
    if months <= 3:
        return _lt("Onumuzdeki 3 ay icinde tamamla.", "Complete within the next 3 months.")
    return _lt("Bu adimi orta vadeli pencere icinde tamamla.", "Complete this move within the mid-term window.")


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


def build_step_narrative(action: Mapping[str, Any], *, step_id: str, phase_id: str) -> RoadmapStepNarrative:
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
    offer_narrative = build_offer_narrative(action)
    return RoadmapStepNarrative(
        step_id=step_id,
        phase_id=phase_id,
        action_key=action_key or None,
        action_group_id=action_group_id or None,
        action_summary=_localized_pair(summary),
        why_this_matters=_localized_pair(why),
        expected_outcome=_append_localized_sentence(expected, primary_target_sentence),
        what_happens_if_done=_localized_pair(done),
        what_happens_if_not_done=_localized_pair(not_done),
        action_timing_hint=_timing_hint(
            _safe_int(_primary_numeric_target(action).get("due_month", action.get("time_months", 1)), 1)
        ),
        offer_narrative=offer_narrative if action_class == "institutional" or offer_narrative else None,
    )


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
    offer_type = str(action.get("offer_type", "") or "")
    requires_approval = bool(action.get("requires_institutional_approval", False))
    requires_acceptance = bool(action.get("requires_acceptance", False))
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
    return OfferNarrative(
        offer_explanation=_localized_pair(template["offer_explanation"]),
        why_offered=_localized_pair(template["why_offered"]),
        if_accepted=_localized_pair(template["if_accepted"]),
        if_not_accepted=_localized_pair(template["if_not_accepted"]),
        offer_terms_summary=_offer_terms_summary(action.get("offer_terms", {}) or {}),
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
            "Profil su anda politika esiginin altinda gorunuyor.",
            "The profile is already below the policy threshold.",
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
    offer_actions = [a for a in actions if str(a.get("offer_type", "") or "").strip()]
    if not offer_actions:
        return _card(
            "Kurum teklifi yok",
            "No institution offer",
            "Bu yol, agirlikli olarak musteri aksiyonlariyla ilerliyor.",
            "This path relies primarily on customer action rather than an institution-side offer.",
        )
    if any(bool(a.get("requires_institutional_approval", False)) for a in offer_actions):
        return _card(
            "Teklif kurum onayina bagli",
            "Offer depends on institution approval",
            "Teklif var ancak devreye girmesi icin kurum onayi gerekiyor.",
            "An offer exists, but it still depends on institution approval.",
        )
    if any(bool(a.get("requires_acceptance", False)) for a in offer_actions):
        return _card(
            "Musteri kabulune bagli teklif",
            "Offer requires customer acceptance",
            "Teklif acik ancak etkinin gorulmesi musteri kabulune bagli.",
            "The offer is available, but its impact depends on customer acceptance.",
        )
    offer_type = str(offer_actions[0].get("offer_type", "") or "")
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


def _decision_view_card(status: str, readiness_stage: str) -> NarrativeCard:
    normalized = str(status or "").upper()
    if normalized == "APPROVED":
        return _card(
            "Onaya uygun gorunum",
            "Approval-ready view",
            "Model bu profili yeniden onaya uygun buluyor.",
            "The model sees this profile as approval-ready again.",
        )
    if normalized == "NEEDS_REVIEW" and readiness_stage != "not_ready_yet":
        return _card(
            "Yeniden degerlendirme gerekir",
            "Needs reassessment",
            "Profil gucleniyor ancak son karar kontrollu inceleme ile verilmeli.",
            "The profile is strengthening, but the final decision should still be controlled and reviewed.",
        )
    if normalized == "REJECTED":
        return _card(
            "Henuz erken",
            "Not ready yet",
            "Mevcut sinyaller, daha fazla iyilesme olmadan olumlu karar icin yeterli degil.",
            "Current signals are still not sufficient for a positive decision without more improvement.",
        )
    return _card(
        "Toparlaniyor",
        "Recovering",
        "Plan ilerliyor ancak daha fazla guclenme gerekiyor.",
        "The plan is progressing, but more strengthening is still needed.",
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
            f"Risk gorunumu {_format_pct(base_pd)} seviyesinden politika esiginin altinda kalabiliyor.",
            f"The risk view can stay below threshold after starting from {_format_pct(base_pd)}.",
        )
    if readiness_week is not None:
        return _card(
            f"{readiness_week} hafta icinde yeniden basvuruya hazirlik",
            f"Re-application readiness in {readiness_week} weeks",
            f"Profilin {_format_pct(base_pd)} seviyesinden {_format_pct(latest_pd)} seviyesine iyilesmesi bekleniyor.",
            f"The profile is expected to improve from {_format_pct(base_pd)} to about {_format_pct(latest_pd)}.",
        )
    return _card(
        "Toparlaniyor ama henuz hazir degil",
        "Improving but not yet ready",
        f"Risk gorunumu {_format_pct(base_pd)} seviyesinden iyilesse de karar hikayesi icin daha fazla guclenme gerekiyor.",
        f"The risk view improves from {_format_pct(base_pd)}, but more strengthening is still needed for a credible decision story.",
    )


def build_executive_summary(
    *,
    base_pd: float,
    tau: float,
    checkpoints: Sequence[Mapping[str, Any]],
    actions: Sequence[Mapping[str, Any]],
    status: str,
    confidence_label: str,
) -> RoadmapExecutiveSummary:
    readiness_stage, readiness_week = _readiness_stage(base_pd, checkpoints, tau)
    offer_status = _offer_status_card(actions)
    decision_view = _decision_view_card(status, readiness_stage)
    time_to_readiness = _time_to_readiness_card(readiness_stage, readiness_week)
    expected_result = _expected_result_card(base_pd, checkpoints, readiness_stage, readiness_week)
    return RoadmapExecutiveSummary(
        headline=_lt(
            "Musteri kontrollu bir toparlanma yoluna alinmis durumda.",
            "The customer is now on a controlled recovery path.",
        ),
        summary_line=_lt(
            "Bu plan, ham motor ciktisini sirali aksiyonlara ve karar anlatimina cevirir.",
            "This plan turns raw engine output into sequenced actions and a decision-ready story.",
        ),
        risk_start=_risk_card(base_pd, tau),
        recommended_path=_recommended_path_card(actions, offer_status),
        offer_status=offer_status,
        checkpoint_4w_summary=_checkpoint_4w_card(checkpoints, tau),
        expected_result=expected_result,
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
    offer_acceptance_probability: float | None = None,
    combined_plan_realization_probability: float | None = None,
) -> CustomerRoadmapNarrative:
    local_reason_bundle = local_reason_bundle or {}
    reason_rows = list(local_reason_bundle.get("reasons", [])) if isinstance(local_reason_bundle.get("reasons", []), list) else []
    meta = local_reason_bundle.get("meta", {}) if isinstance(local_reason_bundle.get("meta", {}), dict) else {}
    confidence_score = _safe_float(meta.get("explainability_confidence", 0.0), 0.0)
    confidence_label = narrative_confidence_label(confidence_score)

    step_narratives: list[RoadmapStepNarrative] = []
    raw_actions: list[Mapping[str, Any]] = []
    feature_changes: list[dict[str, Any]] = []
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
            if (
                (bool(step.get("requires_institutional_approval", False)) or bool(step.get("requires_acceptance", False)))
                and step_id not in seen_approval_steps
            ):
                approval_dependencies.append(
                    {
                        "step_id": step_id,
                        "action_key": str(business_view.get("action_key", step.get("action_key", "")) or ""),
                        "action_title": str(business_view.get("action_title", step.get("action_title", "")) or ""),
                        "institutional_approval_state": str(step.get("institutional_approval_state", "") or ""),
                        "requires_institutional_approval": bool(step.get("requires_institutional_approval", False)),
                        "requires_acceptance": bool(step.get("requires_acceptance", False)),
                        "offer_type": str(step.get("offer_type", "") or ""),
                    }
                )
                seen_approval_steps.add(step_id)
            for flag in list(step.get("diagnostic_flags", [])):
                flag_str = str(flag)
                if flag_str and flag_str not in diagnostic_flags:
                    diagnostic_flags.append(flag_str)

    for step_id in step_order:
        phase_id, representative_step = representative_steps[step_id]
        step_narratives.append(build_step_narrative(representative_step, step_id=step_id, phase_id=phase_id))

    checkpoint_narratives = [
        build_checkpoint_narrative(checkpoint, tau)
        for checkpoint in checkpoints
        if isinstance(checkpoint, Mapping)
    ]
    reason_narratives = build_reason_narratives(reason_rows, max_items=4)
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
        for reason in reason_narratives
    ]
    executive_summary = build_executive_summary(
        base_pd=base_pd,
        tau=tau,
        checkpoints=checkpoints,
        actions=raw_actions,
        status=status,
        confidence_label=confidence_label,
    )
    for checkpoint in checkpoints:
        if not isinstance(checkpoint, Mapping):
            continue
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
            explainability_reasons=explainability_reasons,
            constraints_applied=[dict(item) for item in list(constraint_trace or [])],
            approval_dependencies=approval_dependencies,
            diagnostic_flags=diagnostic_flags,
            confidence_inputs={
                "local_explainability_confidence": confidence_score,
                "local_shap_stability_score": _safe_float(meta.get("stability_score", 0.0), 0.0),
                "local_shap_baseline_drift_l1": _safe_float(meta.get("baseline_drift_l1", 0.0), 0.0),
                "plan_execution_probability": plan_execution_probability,
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
