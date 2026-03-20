import type { Language } from "@/i18n/language";

export function pickLocalizedText(
  value: { tr: string; en: string } | undefined,
  lang: Language,
  fallback = "",
) {
  if (!value) {
    return fallback;
  }

  return lang === "tr" ? value.tr : value.en;
}

export function formatDemoProfile(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    "Denied applicant, near-prime profile": {
      tr: "Reddedilmis, geri kazanimi mumkun profil",
      en: "Denied application with near-prime recovery potential",
    },
    declined_recovery_candidate: {
      tr: "Reddedilmis ama toparlanabilir musteri profili",
      en: "Declined customer with a recoverable profile",
    },
  };

  return (labels[value] ?? { tr: value, en: value })[lang];
}

export function formatDemoSegment(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    "Denied / recovery candidate": {
      tr: "Geri kazanima uygun basvuru",
      en: "Recovery-ready denied application",
    },
    recovery_candidate: {
      tr: "Geri kazanima uygun basvuru",
      en: "Recovery-ready declined application",
    },
  };

  return (labels[value] ?? { tr: value, en: value })[lang];
}

export function formatRiskBand(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    mid_high: {
      tr: "Orta-yuksek risk",
      en: "Mid-high risk",
    },
    near: {
      tr: "Sinira yakin risk",
      en: "Near-threshold risk",
    },
    mid: {
      tr: "Orta risk",
      en: "Mid risk",
    },
    high: {
      tr: "Yuksek risk",
      en: "High risk",
    },
  };

  return (labels[value] ?? { tr: value, en: value })[lang];
}

export function formatIncomeBand(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    stable_income: {
      tr: "Duzenli gelir",
      en: "Stable income",
    },
    q1: {
      tr: "Alt gelir bandi",
      en: "Lower income band",
    },
    q2: {
      tr: "Alt-orta gelir bandi",
      en: "Lower-mid income band",
    },
    q3: {
      tr: "Ust-orta gelir bandi",
      en: "Upper-mid income band",
    },
    q4: {
      tr: "Yuksek gelir bandi",
      en: "Higher income band",
    },
  };

  return (labels[value] ?? { tr: value, en: value })[lang];
}

export function formatTrajectoryStatus(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    on_track: {
      tr: "Yolunda",
      en: "On track",
    },
    needs_replan: {
      tr: "Yeniden planlama gerekiyor",
      en: "Needs replan",
    },
    degraded: {
      tr: "Zayifladi",
      en: "Degraded",
    },
    initial_plan: {
      tr: "Ilk yol haritasi olustu",
      en: "Initial plan created",
    },
  };

  return (labels[value] ?? { tr: value, en: value })[lang];
}

export function formatPhaseTitle(phaseId: string, fallback: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    phase_1_stabilize: {
      tr: "Ilk 4 haftada nakit akisini dengele",
      en: "Stabilize cash flow in the first 4 weeks",
    },
    phase_2_build: {
      tr: "4-12. haftalarda basvuru hazirligini guclendir",
      en: "Strengthen approval readiness in weeks 4-12",
    },
    phase_3_optimize: {
      tr: "12-24. haftalarda iyilesmeyi kalici hale getir",
      en: "Make the improvement durable in weeks 12-24",
    },
  };

  return (labels[phaseId] ?? { tr: fallback, en: fallback })[lang];
}

export function formatWindowLabel(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    "0-4 weeks": {
      tr: "Ilk 4 hafta",
      en: "First 4 weeks",
    },
    "4-12 weeks": {
      tr: "4-12. haftalar",
      en: "Weeks 4-12",
    },
    "12-24 weeks": {
      tr: "12-24. haftalar",
      en: "Weeks 12-24",
    },
    "1-4": {
      tr: "Ilk 4 hafta",
      en: "First 4 weeks",
    },
    "5-12": {
      tr: "4-12. haftalar",
      en: "Weeks 4-12",
    },
    "13-24": {
      tr: "12-24. haftalar",
      en: "Weeks 12-24",
    },
  };

  return (labels[value] ?? { tr: value, en: value })[lang];
}

export function formatActionClass(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    behavioral: {
      tr: "Musteri aksiyonu",
      en: "Customer action",
    },
    structural: {
      tr: "Yapisal adim",
      en: "Structural move",
    },
    institutional: {
      tr: "Kurum adimi",
      en: "Institution-side move",
    },
  };

  return (labels[value] ?? { tr: value, en: value })[lang];
}

export function formatOfferType(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    installment_terms: {
      tr: "Taksitlendirme teklifi",
      en: "Installment offer",
    },
    discount_offer: {
      tr: "Indirimli odeme teklifi",
      en: "Settlement discount offer",
    },
    credit_limit_adjustment: {
      tr: "Limit ayarlama teklifi",
      en: "Credit limit adjustment",
    },
  };

  return (labels[value] ?? { tr: value, en: value })[lang];
}

export function formatActionTitle(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    "Reduce monthly discretionary spending": {
      tr: "Aylik serbest harcamayi azalt",
      en: "Reduce monthly discretionary spending",
    },
    "Set up automatic payments": {
      tr: "Otomatik odeme duzeni kur",
      en: "Set up automatic payments",
    },
    "Move revolving balance to lower-pressure structure": {
      tr: "Donen borcu daha yonetilebilir yapiya tasi",
      en: "Move revolving balance to a lower-pressure structure",
    },
    "Accept institution-side installment plan": {
      tr: "Kurumun taksitlendirme teklifini degerlendir",
      en: "Accept the institution-side installment plan",
    },
    "Increase recurring payment amount": {
      tr: "Duzenli odeme tutarini artir",
      en: "Increase recurring payment amount",
    },
    "Refinance after stable checkpoint": {
      tr: "Stabil checkpoint sonrasi refinansman dene",
      en: "Refinance after a stable checkpoint",
    },
    "Adjust requested loan amount": {
      tr: "Talep edilen kredi tutarini yeniden ayarla",
      en: "Adjust requested loan amount",
    },
    "Refinance or restructure debt": {
      tr: "Borcu yeniden yapilandir veya refinanse et",
      en: "Refinance or restructure debt",
    },
    "Increase regular income": {
      tr: "Duzenli geliri guclendir",
      en: "Increase regular income",
    },
    "Verify income documentation": {
      tr: "Gelir belgelerini dogrula",
      en: "Verify income documentation",
    },
    "Reduce spending pressure": {
      tr: "Harcamayi baskisini azalt",
      en: "Reduce spending pressure",
    },
    "Consolidate revolving debt": {
      tr: "Donen borcu konsolide et",
      en: "Consolidate revolving debt",
    },
    "Limit credit usage": {
      tr: "Kredi kullanimini sinirla",
      en: "Limit credit usage",
    },
    "Improve payment consistency": {
      tr: "Odeme duzenini istikrarli hale getir",
      en: "Improve payment consistency",
    },
    "Request or negotiate credit limit adjustment": {
      tr: "Limit ayarlama secenegini degerlendir",
      en: "Request or negotiate credit limit adjustment",
    },
    "Negotiate settlement discount": {
      tr: "Odeme indirimi secenegini degerlendir",
      en: "Negotiate settlement discount",
    },
    "Enter an installment plan": {
      tr: "Taksitli geri odeme planina gec",
      en: "Enter an installment plan",
    },
  };

  return (labels[value] ?? { tr: value, en: value })[lang];
}

export function formatActionDetail(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    "Lower discretionary spend by roughly $220 per month for 8 weeks.": {
      tr: "Ilk 8 hafta boyunca aylik serbest harcamayi yaklasik 220 dolar azalt.",
      en: "Lower discretionary spend by roughly $220 per month for 8 weeks.",
    },
    "Enroll active obligations into autopay to improve repayment consistency.": {
      tr: "Odeme duzenini guclendirmek icin aktif borclari otomatik odemeye bagla.",
      en: "Enroll active obligations into autopay to improve repayment consistency.",
    },
    "Shift high-interest revolving debt into a controlled balance-transfer path.": {
      tr: "Yuksek faizli donen borcu daha kontrollu bir denge transferi yapisina tasi.",
      en: "Shift high-interest revolving debt into a controlled balance-transfer path.",
    },
    "Convert part of revolving exposure into a structured installment offer.": {
      tr: "Donen borcun bir kismini duzenli bir taksit teklifine cevir.",
      en: "Convert part of revolving exposure into a structured installment offer.",
    },
    "Increase monthly repayment cadence once phase 1 stability is established.": {
      tr: "Ilk fazdaki denge kurulduktan sonra aylik odeme duzenini guclendir.",
      en: "Increase monthly repayment cadence once phase 1 stability is established.",
    },
    "Pursue refinancing only if phase 2 targets are met and income remains stable.": {
      tr: "Refinansman yalnizca ikinci faz hedefleri tutarsa ve gelir istikrarli kalirsa dusunulsun.",
      en: "Pursue refinancing only if phase 2 targets are met and income remains stable.",
    },
    "Reduce the requested amount to a level that matches current affordability and improves approval readiness.": {
      tr: "Talep edilen tutari mevcut geri odeme kapasitesiyle uyumlu seviyeye cekerek onay hazirligini guclendir.",
      en: "Reduce the requested amount to a level that matches current affordability and improves approval readiness.",
    },
    "Pursue refinancing only after the earlier checkpoints are stable enough to support a stronger application.": {
      tr: "Refinansmani ancak ilk checkpoint'ler guclu ise daha saglam bir basvuru icin dusun.",
      en: "Pursue refinancing only after the earlier checkpoints are stable enough to support a stronger application.",
    },
    "Strengthen recurring income through stable and documentable sources before the next review window.": {
      tr: "Bir sonraki inceleme doneminden once duzenli ve belgelenebilir gelir kaynaklarini guclendir.",
      en: "Strengthen recurring income through stable and documentable sources before the next review window.",
    },
    "Complete income verification so the lender sees a cleaner and more dependable file.": {
      tr: "Kredi veren kurumun daha temiz ve guvenilir bir dosya gormesi icin gelir dogrulamasini tamamla.",
      en: "Complete income verification so the lender sees a cleaner and more dependable file.",
    },
    "Lower non-essential monthly spending to create short-term affordability and repayment headroom.": {
      tr: "Kisa vadeli odeme kapasitesini rahatlatmak icin zorunlu olmayan aylik harcamalari dusur.",
      en: "Lower non-essential monthly spending to create short-term affordability and repayment headroom.",
    },
    "Move high-pressure revolving balances into a more structured path that is easier to sustain.": {
      tr: "Baskisi yuksek donen borclari daha yonetilebilir ve surdurulebilir bir yapiya tasi.",
      en: "Move high-pressure revolving balances into a more structured path that is easier to sustain.",
    },
    "Reduce card usage and avoid adding new balance pressure while the profile is stabilizing.": {
      tr: "Profil dengelenirken kart kullanimini azalt ve yeni bakiye baskisi yaratma.",
      en: "Reduce card usage and avoid adding new balance pressure while the profile is stabilizing.",
    },
    "Maintain consistent on-time payments to rebuild lender confidence over the next checkpoints.": {
      tr: "Onumuzdeki checkpoint'lerde kredi veren guvenini geri kazanmak icin odemeleri istikrarli surdur.",
      en: "Maintain consistent on-time payments to rebuild lender confidence over the next checkpoints.",
    },
    "Use a lender-managed limit adjustment only where it meaningfully improves utilization headroom.": {
      tr: "Limit ayarlamasini yalnizca kullanim oraninda anlamli rahatlama sagliyorsa devreye al.",
      en: "Use a lender-managed limit adjustment only where it meaningfully improves utilization headroom.",
    },
    "Consider a negotiated settlement only when the institution confirms eligible terms and customer fit.": {
      tr: "Odeme indirimi secenegini yalnizca kurum uygun kosullari dogrularsa degerlendir.",
      en: "Consider a negotiated settlement only when the institution confirms eligible terms and customer fit.",
    },
    "Convert eligible balances into a structured installment path to make repayment behavior more stable.": {
      tr: "Geri odeme davranisini daha istikrarli hale getirmek icin uygun bakiyeleri taksitli yapiya cevir.",
      en: "Convert eligible balances into a structured installment path to make repayment behavior more stable.",
    },
    "Follow this step within the suggested window to improve credit readiness safely.": {
      tr: "Krediye hazirligi guvenli sekilde artirmak icin bu adimi onerilen zaman araliginda uygula.",
      en: "Follow this step within the suggested window to improve credit readiness safely.",
    },
  };

  return (labels[value] ?? { tr: value, en: value })[lang];
}

export function formatCheckpointLabel(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    "Early stabilization": {
      tr: "Erken dengeleme",
      en: "Early stabilization",
    },
    "Approval readiness": {
      tr: "Basvuru hazirligi",
      en: "Approval readiness",
    },
    "Durable optimization": {
      tr: "Kalici iyilesme",
      en: "Durable optimization",
    },
  };

  return (labels[value] ?? { tr: value, en: value })[lang];
}

export function formatCreditReadinessStage(
  value: "now" | "week_4" | "week_12" | "week_24" | "not_ready_yet" | undefined,
  lang: Language,
) {
  const labels = {
    now: {
      tr: "Su anda krediye hazir",
      en: "Credit-ready now",
    },
    week_4: {
      tr: "4 hafta sonunda krediye hazir",
      en: "Credit-ready by week 4",
    },
    week_12: {
      tr: "12 hafta sonunda krediye hazir",
      en: "Credit-ready by week 12",
    },
    week_24: {
      tr: "24 hafta sonunda krediye hazir",
      en: "Credit-ready by week 24",
    },
    not_ready_yet: {
      tr: "Henuz krediye hazir degil",
      en: "Not credit-ready yet",
    },
  };

  return labels[value ?? "not_ready_yet"][lang];
}

export function formatApprovalReady(value: boolean | undefined, lang: Language) {
  if (value) {
    return lang === "tr" ? "Evet" : "Yes";
  }

  return lang === "tr" ? "Hayir" : "No";
}

export function formatPdPercent(
  value: number | undefined,
  lang: Language,
  options?: { compact?: boolean },
) {
  const numericValue = typeof value === "number" && Number.isFinite(value) ? value : 0;
  if (numericValue <= 0) {
    return options?.compact ? "<1%" : lang === "tr" ? "%1'in altinda" : "Below 1%";
  }

  const locale = lang === "tr" ? "tr-TR" : "en-US";
  return new Intl.NumberFormat(locale, {
    style: "percent",
    maximumFractionDigits: numericValue < 0.1 ? 1 : 0,
    minimumFractionDigits: 0,
  }).format(numericValue);
}

export function formatDecisionStatus(value: string | undefined, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    APPROVED: {
      tr: "Onaya uygun",
      en: "Approval-ready",
    },
    NEEDS_REVIEW: {
      tr: "Manuel review gerekli",
      en: "Manual review required",
    },
    REJECTED: {
      tr: "Henuz uygun degil",
      en: "Not ready yet",
    },
    PENDING: {
      tr: "Degerlendiriliyor",
      en: "Pending review",
    },
  };

  return (labels[value ?? "NEEDS_REVIEW"] ?? { tr: value ?? "", en: value ?? "" })[lang];
}

export function formatCheckpointNote(
  week: number,
  approvalReady: boolean | undefined,
  gatePassEstimate: boolean,
  lang: Language,
) {
  if (week <= 4) {
    return approvalReady
      ? (lang === "tr"
          ? "Ilk checkpoint sonunda musteri yeniden basvuruya yaklasmis gorunuyor."
          : "By the first checkpoint, the customer is already moving close to approval readiness.")
      : (lang === "tr"
          ? "Ilk checkpoint denge kurmaya odaklanir; yapisal adimlar sonrasinda guclenme beklenir."
          : "The first checkpoint focuses on stabilization, with stronger gains expected after structural moves.");
  }

  if (week <= 12) {
    return approvalReady
      ? (lang === "tr"
          ? "Orta vadede musteri krediye daha yakin hale geliyor ve yeniden degerlendirme zemini olusuyor."
          : "By the mid-term checkpoint, the customer is moving into a more approval-ready state.")
      : (lang === "tr"
          ? "Orta vadede ilerleme var, ancak yeniden basvuru icin ek guclenme gerekiyor."
          : "There is visible progress by mid-term, but more strengthening is still needed before re-application.");
  }

  if (gatePassEstimate || approvalReady) {
    return lang === "tr"
      ? "Uzun vadede iyilesme kalicilasmis gorunuyor ve profil daha guvenli hale geliyor."
      : "The long-horizon outlook looks durable, with the profile moving into a safer state.";
  }

  return lang === "tr"
    ? "Uzun vadede ilerleme var, ancak profil hala kontrollu takip gerektiriyor."
    : "There is long-term progress, but the profile still needs controlled follow-up.";
}
