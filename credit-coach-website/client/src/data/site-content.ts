import type { LocalizedText } from "@/i18n/language";

export const modules = [
  {
    title: {
      tr: "Karar Icgorusu",
      en: "Decision Insight",
    },
    description: {
      tr: "Musterinin neden reddedildigini ve guvenli toparlanmanin nereden baslayabilecegini aciklar.",
      en: "Clarifies why a customer was declined and where safe recovery can begin.",
    },
    artifact: "batch_summary.json",
  },
  {
    title: {
      tr: "Musteri Aksiyon Plani",
      en: "Customer Action Planning",
    },
    description: {
      tr: "Her musteri icin uygulanabilir ve asamali bir sonraki adim plani olusturur.",
      en: "Builds a practical next-step plan for each customer.",
    },
    artifact: "customer_roadmap.json",
  },
  {
    title: {
      tr: "Akilli Onceliklendirme",
      en: "Smart Prioritization",
    },
    description: {
      tr: "Musterilerin gercekte uygulama ihtimali daha yuksek olan adimlari one cikarir.",
      en: "Prioritizes the actions customers are most likely to complete.",
    },
    artifact: "behavior_aware_summary.json",
  },
  {
    title: {
      tr: "Asamali Ilerleme",
      en: "Guided Progress",
    },
    description: {
      tr: "Tek seferlik tavsiye yerine checkpoint'lerle ilerleyen yonlendirilmis bir yol sunar.",
      en: "Turns one-time recommendations into a guided journey with checkpoints.",
    },
    artifact: "trajectory_summary.json",
  },
  {
    title: {
      tr: "Teklif Stratejisi",
      en: "Offer Strategy",
    },
    description: {
      tr: "Kurum tekliflerini geri kazanimi artiracak sekilde karar surecine dahil eder.",
      en: "Brings institution-side offers into the decision flow to improve recovery.",
    },
    artifact: "offer_optimization_summary.json",
  },
  {
    title: {
      tr: "Ogrenme Sinyalleri",
      en: "Learning Signals",
    },
    description: {
      tr: "Gercek sonuclari gelecekteki karar kalitesini artiracak sinyallere donusturur.",
      en: "Turns real outcomes into signals that improve future decisions.",
    },
    artifact: "off_policy_evaluation.json",
  },
  {
    title: {
      tr: "Karar Guvencesi",
      en: "Decision Governance",
    },
    description: {
      tr: "Her onerinin aciklanabilir, izlenebilir ve kontrollu kalmasini saglar.",
      en: "Keeps every recommendation reviewable, traceable, and controlled.",
    },
    artifact: "milestone_acceptance_summary.json",
  },
];

export const surfaceCards = [
  {
    title: {
      tr: "Musteri Aksiyon Yol Haritasi",
      en: "Customer Action Roadmap",
    },
    description: {
      tr: "Her musteri icin kredi profilini zamanla guclendiren kisisel bir ilerleme plani sunar.",
      en: "A personalized roadmap that helps each customer improve over time.",
    },
    tone: "blue" as const,
  },
  {
    title: {
      tr: "Portfoy Icgoruleri",
      en: "Portfolio Insights",
    },
    description: {
      tr: "Hangi stratejilerin donusumu artirirken risk kalitesini korudugunu gosterir.",
      en: "Shows which strategies improve conversion while protecting risk quality.",
    },
    tone: "green" as const,
  },
  {
    title: {
      tr: "Teklif Optimizasyonu",
      en: "Offer Optimization",
    },
    description: {
      tr: "Kurum tekliflerinin kabul ve geri kazanima etkisini acikca gorunur kilar.",
      en: "Makes the impact of institution-side offers on acceptance and recovery visible.",
    },
    tone: "amber" as const,
  },
];

export const proofCards = [
  {
    title: {
      tr: "Musteri Aksiyon Yol Haritasi",
      en: "Customer Action Roadmap",
    },
    description: {
      tr: "Her musteri icin bir sonraki en iyi adimi net ve uygulanabilir hale getirir.",
      en: "Makes the next best action clear and practical for each customer.",
    },
  },
  {
    title: {
      tr: "Portfoy Icgoruleri",
      en: "Portfolio Insights",
    },
    description: {
      tr: "Portfoy genelinde hangi yaklasimlarin ise yaradigini yonetime acikca gosterir.",
      en: "Shows leadership which approaches are working across the portfolio.",
    },
  },
  {
    title: {
      tr: "Teklif Optimizasyonu",
      en: "Offer Optimization",
    },
    description: {
      tr: "Kurum tekliflerinin gelir, kabul ve geri kazanima etkisini olculebilir kilar.",
      en: "Measures how institution-side offers affect revenue, acceptance, and recovery.",
    },
  },
  {
    title: {
      tr: "Karar Guvencesi",
      en: "Decision Governance",
    },
    description: {
      tr: "Kararlari aciklanabilir, denetlenebilir ve guvenle yayina alinabilir halde tutar.",
      en: "Keeps decisions explainable, reviewable, and ready for safe rollout.",
    },
  },
];

export const navLinks: Array<{ href: string; label: LocalizedText }> = [
  { href: "/product", label: { tr: "Urun", en: "Product" } },
  { href: "/modules", label: { tr: "Moduller", en: "Modules" } },
  { href: "/demo", label: { tr: "Demo Merkezi", en: "Demo Center" } },
  { href: "/proof", label: { tr: "Kanit", en: "Proof" } },
  { href: "/investor", label: { tr: "Yatirimci", en: "Investor" } },
  { href: "/contact", label: { tr: "Iletisim", en: "Contact" } },
];

export const processSteps = [
  {
    title: {
      tr: "Red nedenini cikar",
      en: "Diagnose the decline",
    },
    body: {
      tr: "Her reddedilen basvuruyu ayni gormez; risk, neden ve segment baglamiyla baslar.",
      en: "Starts with risk, explanation, and segment context instead of treating every denied customer the same.",
    },
  },
  {
    title: {
      tr: "Uygulanabilir adim uret",
      en: "Generate feasible next steps",
    },
    body: {
      tr: "Davranissal, yapisal ve kurumsal aksiyonlari fazlara yayarak uretir.",
      en: "Produces behavioral, structural, and institutional actions that can be sequenced over time.",
    },
  },
  {
    title: {
      tr: "Governance filtresinden gecir",
      en: "Filter through governance",
    },
    body: {
      tr: "Fairness, reliability, telemetry ve operasyonel kontroller kararlarin onunde kalir.",
      en: "Fairness, reliability, telemetry, and operational controls stay upstream of recommendation or promotion.",
    },
  },
  {
    title: {
      tr: "Ticari yolu optimize et",
      en: "Optimize the commercial path",
    },
    body: {
      tr: "Kurum teklifleri, governance'i bozmadan ayni plana eklenebilir.",
      en: "Institution-side offers can join customer actions when they improve recovery proxies safely.",
    },
  },
  {
    title: {
      tr: "Sonuclardan ogren",
      en: "Learn from outcomes",
    },
    body: {
      tr: "Karar log'lari, gecikmeli sonuclar ve OPE ile policy iyilestirmesi kanita dayanir.",
      en: "Decision logs, delayed outcomes, and off-policy evaluation close the loop for evidence-based policy improvement.",
    },
  },
];

export const investorHighlights = [
  {
    tr: "Bu yalnizca bir scoring modeli degil; deny sonrasina yerlesen bir karar-istihbarati katmani.",
    en: "This is not just a scoring model. It is a decision-intelligence layer that sits after deny.",
  },
  {
    tr: "En guclu wedge, governance sinirlari icinde denied veya near-prime musteri geri kazanimi.",
    en: "The strongest wedge is lender recovery of denied or near-prime customers under governance constraints.",
  },
  {
    tr: "Teknik cekirdek zaten var: recommendation quality, behavior-aware ranking, trajectories, offers ve learning evidence ship edildi.",
    en: "The technical core already exists: recommendation quality, behavior-aware ranking, trajectories, offers, and learning evidence are shipped.",
  },
  {
    tr: "Ticari bosluk productization, operator surface ve GTM paketlemesinde. Bu da website ve product shell'i kritik kiliyor.",
    en: "The commercial gap is productization, operator surfaces, and go-to-market packaging.",
  },
];
