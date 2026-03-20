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
      tr: "Ilk giris noktasi",
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

export const proofInvestorSharedLanguage = {
  contextLabels: {
    curated: {
      tr: "Derlenmis demo gorunumu",
      en: "Curated demo snapshot",
    },
    simulation: {
      tr: "Temsili simulasyon",
      en: "Representative simulation",
    },
    benchmark: {
      tr: "Cevrimdisi karsilastirma",
      en: "Offline benchmark",
    },
    portfolio: {
      tr: "Derlenmis portfoy gorunumu",
      en: "Curated portfolio snapshot",
    },
  },
  trust: {
    safeToPilot: {
      tr: "Pilot icin guvenli baslangic",
      en: "Safe to pilot",
    },
    controlledRollout: {
      tr: "Kontrollu yayina alim",
      en: "Controlled rollout",
    },
    institutionReadySafeguards: {
      tr: "Kuruma hazir guvenceler",
      en: "Institution-ready safeguards",
    },
  },
  benchmark: {
    baselinePortfolioSnapshot: {
      tr: "Baz portfoy gorunumu",
      en: "Baseline portfolio snapshot",
    },
    previousBenchmark: {
      tr: "Onceki karsilastirma",
      en: "Previous benchmark",
    },
  },
  positioning: {
    decisionIntelligenceInfrastructure: {
      tr: "Karar istihbarati altyapisi",
      en: "Decision intelligence infrastructure",
    },
    pilotToPlatform: {
      tr: "Pilottan platforma",
      en: "Pilot to platform",
    },
  },
};

export const proofPageNarrative = {
  question: {
    tr: "Bu sistem gercekten portfoyumde ise yarar mi?",
    en: "Will this system actually work on my portfolio?",
  },
  description: {
    tr: "Karar diliyle okundugunda bu kanit, portfoy etkisini, kontrollu kullanim disiplinini ve izlenecek riskleri tek yonetici okumasinda toplar.",
    en: "Read in business language, this proof brings portfolio impact, rollout discipline, and watch items into one executive decision read.",
  },
  verdicts: {
    working: {
      label: {
        tr: "Calisiyor",
        en: "Working",
      },
      statement: {
        tr: "Bu sistem kontrollu bir kullanim icinde gercek portfoy etkisi yaratmaya hazir gorunuyor.",
        en: "This system looks ready to create real portfolio impact inside a controlled rollout.",
      },
      support: {
        tr: "Kapsam, guvence ve gercekci etki ayni anda yeterince guclu.",
        en: "Coverage, safeguards, and realistic impact are all strong enough together.",
      },
    },
    promising: {
      label: {
        tr: "Umut veriyor",
        en: "Promising",
      },
      statement: {
        tr: "Sistem pilot icin guvenli bir baslangic sinyali veriyor, ancak yakindan izlenmesi gereken alanlar var.",
        en: "The system looks safe to pilot, with a few areas that still need close monitoring.",
      },
      support: {
        tr: "Portfoy sinyali guclendi; erken saglik ve temsil kapsamasi halen dikkat istiyor.",
        en: "The portfolio signal improved, while early health and representativeness still need attention.",
      },
    },
    mixed: {
      label: {
        tr: "Karisik",
        en: "Mixed",
      },
      statement: {
        tr: "Deger sinyali var, ancak bugun icin alici guvenini temiz bicimde tasimiyor.",
        en: "There is value signal here, but it is not yet carrying clean buyer confidence.",
      },
      support: {
        tr: "Pilot karari icin once daha tutarli bir guven tablosu gerekiyor.",
        en: "A pilot decision still needs a more consistent trust picture first.",
      },
    },
    not_proven: {
      label: {
        tr: "Henuz kanitli degil",
        en: "Not proven",
      },
      statement: {
        tr: "Bu sistem henuz alici guveniyle savunulacak kadar net kanit biriktirmedi.",
        en: "This system has not yet built enough proof to support buyer confidence.",
      },
      support: {
        tr: "Hikaye var, ancak portfoy seviyesi karar icin kanit daha fazla olgunlasmali.",
        en: "The story exists, but the evidence still needs to mature for a portfolio decision.",
      },
    },
  },
  trustRail: [
    {
      title: {
        tr: "Pilot icin guvenli baslangic",
        en: "Safe to pilot",
      },
      description: {
        tr: "Giriste genis yayina alim yerine sinirli kapsam ve net gozden gecirme adimlari onerir.",
        en: "Recommends a contained starting scope instead of a broad rollout.",
      },
    },
    {
      title: {
        tr: "Kontrollu yayina alim",
        en: "Controlled rollout",
      },
      description: {
        tr: "Ekip, portfoy dilimini kontrollu genisleterek performansi takip edebilir.",
        en: "Teams can expand through explicit portfolio slices and review gates.",
      },
    },
    {
      title: {
        tr: "Kuruma hazir guvenceler",
        en: "Institution-ready safeguards",
      },
      description: {
        tr: "Adalet, guvenilirlik ve izleme disiplini teknik katmanda korunuyor.",
        en: "Fairness, reliability, and telemetry discipline remain available underneath.",
      },
    },
  ],
  sections: {
    proofNow: {
      eyebrow: {
        tr: "Karar ozet",
        en: "Decision read",
      },
      title: {
        tr: "Neden guven artiyor",
        en: "Why confidence is improving",
      },
      description: {
        tr: "Ilk cevap, portfoyde neyin daha kullanilabilir, daha kontrollu ve daha anlamli hale geldigini gosterir.",
        en: "The first answer shows what is becoming more usable, more controlled, and more meaningful on the portfolio.",
      },
    },
    watchlist: {
      eyebrow: {
        tr: "Yakindan izlenecekler",
        en: "What still needs watching",
      },
      title: {
        tr: "Pilot oncesi gizlenmeyen izleme listesi",
        en: "The watchlist we would not hide before a pilot",
      },
      description: {
        tr: "Guven yalnizca iyi sinyalleri degil, halen baski yaratan alanlari da acikca gostermeyi gerektirir.",
        en: "Trust comes from showing the pressure points as clearly as the positives.",
      },
    },
    learning: {
      eyebrow: {
        tr: "Ikinci katman kanit",
        en: "Second-layer evidence",
      },
      title: {
        tr: "Ogrenme disiplini gelecekteki politika kalitesini destekliyor",
        en: "Learning discipline supports future policy quality",
      },
      description: {
        tr: "Bu katman bugunku portfoy kararini destekler ve yarin daha iyi politika secimine zemin hazirlar.",
        en: "This layer supports today's portfolio decision and creates the base for future policy improvement.",
      },
    },
    technicalDetails: {
      eyebrow: {
        tr: "Teknik detay",
        en: "Technical detail",
      },
      title: {
        tr: "Alt seviyedeki kanit girdileri",
        en: "Underlying proof inputs",
      },
      description: {
        tr: "Ham cikti isimleri yerine, hangi karsilastirma ve sinyal ailesinin bu karari destekledigini gosteren detay katmani.",
        en: "A lower-detail view of the benchmark and signal families behind this decision read.",
      },
    },
  },
};

export const investorPageNarrative = {
  hero: {
    title: {
      tr: "Red sonrasinda kaybolan degeri geri alan urun katmani.",
      en: "The product layer that recovers value after the credit decision.",
    },
    supportingNote: {
      tr: "Giris noktasi net: reddedilen veya sinira yakin musteri toparlanmasi.",
      en: "The entry wedge is clear: recovery for denied and near-threshold customers.",
    },
    description: {
      tr: "Hedef once tek bir aci noktayi net bicimde cozmektir, sonra ayni kurum icinde daha fazla ekibe yayilan bir karar istihbarati altyapisina donusmektir.",
      en: "The goal is to solve one painful workflow first, then grow into decision intelligence infrastructure across more teams in the same institution.",
    },
  },
  sections: {
    marketPain: {
      eyebrow: {
        tr: "Pazar problemi",
        en: "Market pain",
      },
      title: {
        tr: "Kredi karari sonrasinda deger ve yonlendirme ayni anda kayboluyor.",
        en: "After the credit decision, both value and guidance tend to disappear.",
      },
      description: {
        tr: "Kurumlar hayir dedikten sonra ne yapacaklarini bilen sistemlere degil, sadece neden hayir dediklerini gosteren araclara sahip.",
        en: "Institutions often own tools that explain a decline, but not systems that manage what should happen next.",
      },
      cards: [
        {
          title: {
            tr: "Gelir ve musteri iliskisi kopuyor",
            en: "Value drops out of the funnel",
          },
          description: {
            tr: "Reddedilen veya sinira gelen dosyalar genelde tamamen kaybediliyor, halbuki bir kismi yonetilebilir toparlanma icinde kalabilir.",
            en: "Denied and near-threshold files are often lost entirely, even when part of that book could move into managed recovery.",
          },
        },
        {
          title: {
            tr: "Ekipler ortak bir sonraki adim yuzeyine sahip degil",
            en: "Teams lack one next-step surface",
          },
          description: {
            tr: "Risk, recovery ve teklif ekipleri ayni musteri icin farkli araclarda hareket ediyor.",
            en: "Risk, recovery, and offer teams often act in different tools against the same customer file.",
          },
        },
      ],
    },
    wedge: {
      eyebrow: {
        tr: "Urun giris noktasi",
        en: "Product wedge",
      },
      title: {
        tr: "Ilk adim, olculebilir aci ve net sahiplik olan yerde basliyor.",
        en: "The first step starts where pain is measurable and ownership is clear.",
      },
      description: {
        tr: "Ilk giris noktasi, reddedilen veya sinira yakin musteri toparlanmasi. Yeni yaklasim ise aksiyon, teklif ve takip noktalarini tek yonetilen yuzeyde toplamak.",
        en: "The first wedge is denied and near-threshold recovery. The new approach is to manage actions, offers, and follow-up checkpoints in one surface.",
      },
      cards: [
        {
          title: {
            tr: "Baslangic giris noktasi",
            en: "Starting wedge",
          },
          description: {
            tr: "Kuruma somut ROI gosterebilen, operasyonel sahipligi net bir kullanim alani.",
            en: "A use case with clear ownership and a direct path to showing ROI.",
          },
        },
        {
          title: {
            tr: "Yeni yaklasim",
            en: "New approach",
          },
          description: {
            tr: "Skorun yanina ikinci bir rapor koymak degil, karar sonrasini yoneten yeni bir katman kurmak.",
            en: "Not another report next to the score, but a new layer that manages what happens after the decision.",
          },
        },
        {
          title: {
            tr: "Neden genisleyebilir",
            en: "Why it can expand",
          },
          description: {
            tr: "Ayni mantik once ayni kurum icinde daha fazla ekibe, sonra komsu kullanim alanlarina tasinabilir.",
            en: "The same logic can spread to more teams inside one institution before it expands into adjacent use cases.",
          },
        },
      ],
    },
    proof: {
      eyebrow: {
        tr: "Neden calisabilir",
        en: "Proof it works",
      },
      title: {
        tr: "Kanit, bunun yalnizca fikir degil urunlesebilir bir sistem oldugunu gosteriyor.",
        en: "The proof suggests this is not just an idea, but a system that can become software.",
      },
      description: {
        tr: "Portfoy etkisi, teklif yaniti ve ogrenme disiplini birlikte okundugunda, kurum ici tekrar eden bir urun davranisi gorunuyor.",
        en: "Read together, portfolio impact, offer response, and learning discipline look like repeatable product behavior inside an institution.",
      },
      narrative: {
        tr: "Bu kanitin anlattigi sey yalnizca calisiyor olmasi degil; ayni kurum icinde tekrar tekrar uygulanabilecek bir kullanim kalibi olmasi.",
        en: "The proof matters not only because it works, but because it resembles a usage pattern that can be deployed again and again inside one institution.",
      },
    },
    monetization: {
      eyebrow: {
        tr: "Ticari model",
        en: "Monetization",
      },
      title: {
        tr: "Ticari yol dar bir girisle baslar, kullanim derinligiyle genisler.",
        en: "The commercial path starts narrow and expands through product depth.",
      },
      description: {
        tr: "Varsayilan ticari okuma pilottan platforma gider. Ilk genisleme ayni kurum icinde daha fazla ekip ve karar akisina yayilmaktir; daha genis kullanim alani ikinci asamadir.",
        en: "The default commercial read is pilot to platform. Expansion starts with more teams and workflows inside one institution, with broader use cases as a later step.",
      },
      stages: [
        {
          title: {
            tr: "Pilot girisi",
            en: "Pilot entry",
          },
          description: {
            tr: "Sinirli bir portfoy veya ekipte hizli deger gosteren kontrollu kullanim.",
            en: "A controlled deployment in one portfolio slice or team that can show value quickly.",
          },
        },
        {
          title: {
            tr: "Platform derinligi",
            en: "Platform depth",
          },
          description: {
            tr: "Ayni kurum icinde risk, recovery ve teklif ekiplerine yayilan ortak yuzey.",
            en: "A shared surface that spreads across risk, recovery, and offer teams inside the same institution.",
          },
        },
        {
          title: {
            tr: "Genisleme opsiyonu",
            en: "Expansion option",
          },
          description: {
            tr: "Temel urun oturduktan sonra komsu karar kullanim alanlarina gecis.",
            en: "Adjacent decision workflows once the core product is established.",
          },
        },
      ],
    },
  },
  bottomLine: {
    title: {
      tr: "Firsat, tek bir modeli satmak degil; karar sonrasinin kurumsal yazilimini sahiplenmek.",
      en: "The opportunity is not to sell one model, but to own the institutional software layer after the decision.",
    },
    description: {
      tr: "Bugun gorulen kanit, yarin ayni kurum icinde daha fazla ekip tarafindan kullanilabilecek bir karar istihbarati altyapisina isaret ediyor.",
      en: "The proof visible today points toward decision intelligence infrastructure that more teams inside the same institution can use tomorrow.",
    },
  },
};

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
