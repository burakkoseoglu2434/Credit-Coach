import type { Language } from "@/i18n/language";

export function formatDemoProfile(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    "Denied applicant, near-prime profile": {
      tr: "Reddedilmis, geri kazanimi mumkun profil",
      en: "Denied application with near-prime recovery potential",
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
  };

  return (labels[value] ?? { tr: value, en: value })[lang];
}

export function formatRiskBand(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    mid_high: {
      tr: "Orta-yuksek risk",
      en: "Mid-high risk",
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
      tr: "Basvuruya hazirligi guclendir",
      en: "Rebuild approval readiness",
    },
    phase_3_optimize: {
      tr: "Kalici iyilesmeyi guclendir",
      en: "Optimize for durable approval",
    },
  };

  return (labels[phaseId] ?? { tr: fallback, en: fallback })[lang];
}

export function formatWindowLabel(value: string, lang: Language) {
  const labels: Record<string, { tr: string; en: string }> = {
    "0-4 weeks": {
      tr: "0-4 hafta",
      en: "0-4 weeks",
    },
    "4-12 weeks": {
      tr: "4-12 hafta",
      en: "4-12 weeks",
    },
    "12-24 weeks": {
      tr: "12-24 hafta",
      en: "12-24 weeks",
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
      tr: "Kurum teklifi",
      en: "Institutional offer",
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
