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
    icon: "decision" as const,
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
    icon: "roadmap" as const,
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
    icon: "platform" as const,
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
    icon: "process" as const,
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
    icon: "offer" as const,
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
    icon: "learning" as const,
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
    icon: "governance" as const,
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
    icon: "roadmap" as const,
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
    icon: "portfolio" as const,
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
    icon: "offer" as const,
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
    icon: "roadmap" as const,
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
    icon: "portfolio" as const,
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
    icon: "offer" as const,
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
    icon: "governance" as const,
  },
];

export const navLinks: Array<{ href: string; label: LocalizedText }> = [
  { href: "/product", label: { tr: "Urun", en: "Product" } },
  { href: "/modules", label: { tr: "Nasil Calisir", en: "How It Works" } },
  { href: "/demo", label: { tr: "Demo Merkezi", en: "Demo Center" } },
  { href: "/proof", label: { tr: "Kanit", en: "Proof" } },
  { href: "/investor", label: { tr: "Yatirimci", en: "Investor" } },
  { href: "/contact", label: { tr: "Iletisim", en: "Contact" } },
];

export const homeProblemCards = [
  {
    title: {
      tr: "Red sonrasinda deger kayboluyor",
      en: "Value disappears after deny",
    },
    description: {
      tr: "Bugun bircok finans kurumu red kararindan sonra musteriye anlamli bir sonraki adim sunamiyor.",
      en: "Many lenders still have no meaningful next step once an application is denied.",
    },
    icon: "decision" as const,
  },
  {
    title: {
      tr: "Aksiyon ve teklif ayrik kaliyor",
      en: "Actions and offers stay disconnected",
    },
    description: {
      tr: "Musteri aksiyonlari ile kurum teklifleri ayni karar yuzeyinde birlikte optimize edilmiyor.",
      en: "Customer actions and institution-side offers are rarely optimized in one decision surface.",
    },
    icon: "offer" as const,
  },
  {
    title: {
      tr: "Karar guvencesi zayiflarsa yayina gecis zorlasiyor",
      en: "Governance slows rollout",
    },
    description: {
      tr: "Adalet, tutarlilik ve yayin kontrolleri zayif oldugunda yeni stratejiler hayata gecemiyor.",
      en: "New strategies stall when fairness, reliability, and release controls are weak.",
    },
    icon: "governance" as const,
  },
];

export const buyerPaths = [
  {
    title: {
      tr: "Kurum ekipleri icin",
      en: "For lenders",
    },
    description: {
      tr: "Demo talep edin ve bu urunun risk, tahsilat veya geri kazanım surecine nasil oturacagini gorun.",
      en: "Request a demo to see how the platform fits underwriting, collections, or recovery workflows.",
    },
    cta: {
      tr: "Demo Talep Et",
      en: "Request a Demo",
    },
    href: "/contact",
    icon: "contact" as const,
  },
  {
    title: {
      tr: "Urunu gormek isteyenler icin",
      en: "For product explorers",
    },
    description: {
      tr: "Tek musteri, portfoy KPI ve ogrenme sinyallerini ornek bir demo akisi icinde inceleyin.",
      en: "Explore customer journeys, portfolio KPIs, and learning signals in a curated product demo.",
    },
    cta: {
      tr: "Demo Merkezine Git",
      en: "Open Demo Center",
    },
    href: "/demo",
    icon: "demo" as const,
  },
  {
    title: {
      tr: "Yatirimcilar icin",
      en: "For investors",
    },
    description: {
      tr: "Wedge'i, farklilasmayi ve urunlesme yolunu daha kisa bir yatirim hikayesi uzerinden gorun.",
      en: "See the wedge, differentiation, and productization path in an investor-focused narrative.",
    },
    cta: {
      tr: "Yatirimci Ozetini Incele",
      en: "Review Investor Story",
    },
    href: "/investor",
    icon: "market" as const,
  },
];

export const proofPillars = [
  {
    title: {
      tr: "Ne olcuyoruz",
      en: "What we measure",
    },
    description: {
      tr: "Dönüşüm, risk kalitesi, teklif etkisi ve öğrenme hazırlığı aynı ürün yüzeyinde izlenir.",
      en: "Conversion, risk quality, offer impact, and learning readiness are measured in one surface.",
    },
    icon: "portfolio" as const,
  },
  {
    title: {
      tr: "Neden guvenilir",
      en: "Why it is trustworthy",
    },
    description: {
      tr: "Oneriler tek ornekle degil, portfoy seviyesi KPI'lar ve kontrollu demo gorunumleriyle anlatilir.",
      en: "Claims are grounded in portfolio-level KPIs and controlled demo snapshots, not anecdotes.",
    },
    icon: "proof" as const,
  },
  {
    title: {
      tr: "Nasil release ediyoruz",
      en: "How we release",
    },
    description: {
      tr: "Adalet, tutarlilik ve izleme kontrolleri urun kararlarinin onunde kalir.",
      en: "Fairness, reliability, and telemetry controls stay upstream of release decisions.",
    },
    icon: "governance" as const,
  },
  {
    title: {
      tr: "Nasil ogreniyoruz",
      en: "How we learn",
    },
    description: {
      tr: "Karar kayıtları ve gecikmeli sonuçlar gelecekteki politika iyileştirmeleri için sinyal üretir.",
      en: "Decision logs and delayed outcomes create the signal needed for future policy improvement.",
    },
    icon: "learning" as const,
  },
];

export const investorNarrative = [
  {
    title: {
      tr: "Neden simdi",
      en: "Why now",
    },
    description: {
      tr: "Finans kurumlari sadece karar aciklamasi degil, red sonrasinda guvenli bir sonraki adimi da yonetmek istiyor.",
      en: "Financial institutions need governed next-step systems, not just more explainability.",
    },
    icon: "market" as const,
  },
  {
    title: {
      tr: "Ilk wedge",
      en: "Initial wedge",
    },
    description: {
      tr: "En guclu giris noktasi, reddedilmis veya sinira yakin musteri geri kazanimi ve teklif optimizasyonu.",
      en: "The strongest wedge is recovery and offer optimization for denied or near-prime applicants.",
    },
    icon: "offer" as const,
  },
  {
    title: {
      tr: "Neden farkli",
      en: "Why different",
    },
    description: {
      tr: "Bu yalnizca skor degil; aksiyon, teklif, kontrol ve ogrenme katmanini ayni urunde toplar.",
      en: "This is not just a score. It combines actions, offers, governance, and learning in one platform.",
    },
    icon: "platform" as const,
  },
  {
    title: {
      tr: "Nasil para kazanir",
      en: "How it makes money",
    },
    description: {
      tr: "Kurumsal yazilim ve pilot projeler uzerinden baslayan, kurum ici sureclere giren bir karar altyapisi olarak konumlanir.",
      en: "It fits as B2B software that starts with pilots and expands into institutional decision workflows.",
    },
    icon: "portfolio" as const,
  },
  {
    title: {
      tr: "Urunlesme acigi",
      en: "Productization gap",
    },
    description: {
      tr: "Teknik cekirdek mevcut; asil bosluk kullanim yuzeyi, paketleme ve dagitim hikayesinde.",
      en: "The technical core is real; the remaining work is operator experience, packaging, and distribution.",
    },
    icon: "proof" as const,
  },
];

export const demoOverviewCards = [
  {
    title: {
      tr: "Tek musteri gorunumu",
      en: "Single customer view",
    },
    description: {
      tr: "Bir red kararinin kademeli aksiyon plani ve kurum teklifiyle nasil yeniden yorumlandigini gosterir.",
      en: "Shows how a denied case becomes a phased action plan with institution-side offers.",
    },
    icon: "roadmap" as const,
  },
  {
    title: {
      tr: "Portfoy etkisi",
      en: "Portfolio impact",
    },
    description: {
      tr: "Tek bir ornek yerine toplu performansin nasil degistigini netlestirir.",
      en: "Clarifies how performance moves across a cohort rather than in a single anecdote.",
    },
    icon: "portfolio" as const,
  },
  {
    title: {
      tr: "Teklif stratejisi",
      en: "Offer strategy",
    },
    description: {
      tr: "Kurum tekliflerinin kabul ve geri kazanima etkisini urun seviyesi bir blokta gosterir.",
      en: "Shows how institution-side offers affect acceptance and recovery in one product block.",
    },
    icon: "offer" as const,
  },
  {
    title: {
      tr: "Ogrenme sinyali",
      en: "Learning signal",
    },
    description: {
      tr: "Gercek sonuclarin gelecekteki politika secimlerine nasil geri beslendigini aciklar.",
      en: "Explains how real outcomes feed back into future policy decisions.",
    },
    icon: "learning" as const,
  },
];

export const processSteps = [
  {
    title: {
      tr: "Karari acikla",
      en: "Diagnose the decline",
    },
    body: {
      tr: "Her reddedilen basvuruyu ayni gormez; risk, neden ve musteri baglamiyla baslar.",
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
      tr: "Kontrol filtresinden gecir",
      en: "Filter through governance",
    },
    body: {
      tr: "Adalet, tutarlilik, izleme ve operasyonel kontroller kararlarin onunde kalir.",
      en: "Fairness, reliability, telemetry, and operational controls stay upstream of recommendation or promotion.",
    },
  },
  {
    title: {
      tr: "Ticari yolu optimize et",
      en: "Optimize the commercial path",
    },
    body: {
      tr: "Kurum teklifleri, kontrol disiplinini bozmadan ayni plana eklenebilir.",
      en: "Institution-side offers can join customer actions when they improve recovery proxies safely.",
    },
  },
  {
    title: {
      tr: "Sonuclardan ogren",
      en: "Learn from outcomes",
    },
    body: {
      tr: "Karar kayitlari, gecikmeli sonuclar ve OPE ile politika iyilestirmesi kanita dayanir.",
      en: "Decision logs, delayed outcomes, and off-policy evaluation close the loop for evidence-based policy improvement.",
    },
  },
];

export const investorHighlights = [
  {
    tr: "Bu yalnizca bir skor modeli degil; red sonrasina yerlesen bir karar istihbarati katmani.",
    en: "This is not just a scoring model. It is a decision-intelligence layer that sits after deny.",
  },
  {
    tr: "En guclu giris, karar guvencesi sinirlari icinde reddedilmis veya sinira yakin musteri geri kazanimi.",
    en: "The strongest wedge is lender recovery of denied or near-prime customers under governance constraints.",
  },
  {
    tr: "Teknik cekirdek zaten var: onerinin kalitesi, davranis farkindalikli siralama, yol haritasi, teklifler ve ogrenme kaniti kurulmus durumda.",
    en: "The technical core already exists: recommendation quality, behavior-aware ranking, trajectories, offers, and learning evidence are shipped.",
  },
  {
    tr: "Ticari bosluk urunlestirme, kullanim yuzeyi ve pazara cikis paketlemesinde. Bu da website ve urun kabugunu kritik kiliyor.",
    en: "The commercial gap is productization, operator surfaces, and go-to-market packaging.",
  },
];
