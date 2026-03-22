import type { ReactNode } from "react";
import { DemoSectionCta } from "@/components/DemoSectionCta";
import { MetricTile } from "@/components/MetricTile";
import { PageHero } from "@/components/PageHero";
import { RoadmapPhaseCard } from "@/components/RoadmapPhaseCard";
import { SectionHeading } from "@/components/SectionHeading";
import { useDemoItem } from "@/hooks/useDemoData";
import { useLanguage } from "@/i18n/language";
import {
  formatApprovalReady,
  formatCheckpointLabel,
  formatCheckpointNote,
  formatCreditReadinessStage,
  formatDecisionStatus,
  formatDemoProfile,
  formatDemoSegment,
  formatIncomeBand,
  formatOfferType,
  formatPdPercent,
  formatTrajectoryStatus,
  formatWindowLabel,
  pickLocalizedText,
} from "@/lib/demo-formatters";
import type { SingleCustomerDemo } from "@shared/demo-schema";

type GenericContent = Record<string, unknown>;

type BusinessSectionIntroProps = {
  bridge: string;
  eyebrow: string;
  title: string;
  summary: string;
  whyMatters: string;
};

type DetailRowProps = {
  label: string;
  value: ReactNode;
};

type LocalizedText = { tr: string; en: string };

type ExecutiveNarrativeCardProps = {
  eyebrow: string;
  value?: { label: LocalizedText; description: LocalizedText } | null;
};

type CheckpointStripCardProps = {
  label: string;
  week: number;
  summary: string;
  supporting: string;
  emphasis?: boolean;
};

type ReasonNarrativeCardProps = {
  title: string;
  description: string;
  hint: string;
  severity?: string | null;
};

function readNumber(value: unknown) {
  return typeof value === "number" ? value : 0;
}

function BusinessSectionIntro({
  bridge,
  eyebrow,
  title,
  summary,
  whyMatters,
}: BusinessSectionIntroProps) {
  const { text } = useLanguage();

  return (
    <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr] xl:items-start">
      <div>
        <p className="section-bridge">{bridge}</p>
        <div className="mt-3">
          <SectionHeading eyebrow={eyebrow} title={title} description={summary} />
        </div>
      </div>
      <div className="panel-product p-6">
        <div className="surface-label">{text({ tr: "Neden onemli", en: "Why this matters" })}</div>
        <p className="mt-4 text-sm leading-7 text-slate-300">{whyMatters}</p>
      </div>
    </div>
  );
}

function DetailRow({ label, value }: DetailRowProps) {
  return (
    <div>
      <span className="text-slate-500">{label}: </span>
      <span className="text-white">{value}</span>
    </div>
  );
}

function ExecutiveNarrativeCard({ eyebrow, value }: ExecutiveNarrativeCardProps) {
  const { lang, text } = useLanguage();
  const label = value ? pickLocalizedText(value.label, lang) : text({ tr: "Hazir degil", en: "Unavailable" });
  const description = value
    ? pickLocalizedText(value.description, lang)
    : text({
        tr: "Bu kart icin aciklama bu gorunumde hazir degil.",
        en: "The supporting explanation for this card is not available in this view.",
      });

  return (
    <div className="rounded-[24px] border border-white/10 bg-slate-950/45 p-5">
      <div className="surface-label">{eyebrow}</div>
      <div className="mt-3 font-medium text-white">{label}</div>
      <p className="mt-2 text-sm leading-7 text-slate-300">{description}</p>
    </div>
  );
}

function CheckpointStripCard({
  label,
  week,
  summary,
  supporting,
  emphasis = false,
}: CheckpointStripCardProps) {
  const { text } = useLanguage();

  return (
    <div
      className={[
        "rounded-[24px] border p-5",
        emphasis
          ? "border-arctic/30 bg-arctic/10 shadow-[0_0_0_1px_rgba(112,236,255,0.12)]"
          : "border-white/10 bg-slate-950/45",
      ].join(" ")}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="surface-label">{label}</div>
        <div className="surface-label">
          {text({ tr: "Hafta", en: "Week" })} {week}
        </div>
      </div>
      <div className="mt-3 font-medium text-white">{summary}</div>
      <p className="mt-2 text-sm leading-7 text-slate-300">{supporting}</p>
    </div>
  );
}

function ReasonNarrativeCard({
  title,
  description,
  hint,
  severity,
}: ReasonNarrativeCardProps) {
  const { text } = useLanguage();

  return (
    <div className="rounded-[24px] border border-white/10 bg-slate-950/45 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="surface-label">{text({ tr: "Plan nedeni", en: "Plan reason" })}</div>
        {severity ? <div className="surface-label">{severity}</div> : null}
      </div>
      <div className="mt-3 font-medium text-white">{title}</div>
      <p className="mt-2 text-sm leading-7 text-slate-300">{description}</p>
      <div className="mt-4 rounded-[18px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-300">
        {hint}
      </div>
    </div>
  );
}

export function DemoCenterPage() {
  const { lang, text } = useLanguage();
  const locale = lang === "tr" ? "tr-TR" : "en-US";

  const roadmap = useDemoItem<SingleCustomerDemo>("single-customer-roadmap");
  const batch = useDemoItem<GenericContent>("portfolio-batch-summary");
  const actionRealism = useDemoItem<GenericContent>("action-realism");
  const behaviorAware = useDemoItem<GenericContent>("behavior-aware");
  const trajectory = useDemoItem<GenericContent>("trajectory");
  const offer = useDemoItem<GenericContent>("offer-optimization");
  const learning = useDemoItem<GenericContent>("outcome-ingestion");
  const ope = useDemoItem<GenericContent>("off-policy-evaluation");

  const roadmapContent = roadmap.data?.content;
  const batchContent = batch.data?.content ?? {};
  const actionMetrics =
    ((actionRealism.data?.content as GenericContent)?.canonical_metrics as GenericContent) ?? {};
  const behaviorMetrics =
    ((behaviorAware.data?.content as GenericContent)?.canonical_metrics as GenericContent) ?? {};
  const trajectoryMetrics =
    ((trajectory.data?.content as GenericContent)?.canonical_metrics as GenericContent) ?? {};
  const offerMetrics =
    ((offer.data?.content as GenericContent)?.canonical_metrics as GenericContent) ?? {};
  const learningContent = learning.data?.content ?? {};
  const opeContent = ope.data?.content ?? {};

  const customer = roadmapContent?.customer;
  const summary = roadmapContent?.summary;
  const narrative = roadmapContent?.narrative;
  const executiveSummary = narrative?.executive_summary;
  const technicalReveal = narrative?.technical_reveal;
  const firstCheckpoint = roadmapContent?.checkpoints[0];
  const activePhases = roadmapContent?.phases.filter((phase) => phase.steps.length > 0) ?? [];
  const visibleSteps = activePhases.flatMap((phase) =>
    phase.steps.map((step) => ({
      phase,
      step,
    })),
  );
  const visibleReasons = narrative?.reasons ?? [];
  const offerBearingSteps = visibleSteps.filter(({ step }) =>
    Boolean(step.narrative?.offer_narrative || step.offer_type),
  );
  const isLiveDemo = Boolean(roadmapContent?.meta?.live);
  const hasOffer = Boolean(
    offerBearingSteps.length > 0,
  );
  const firstOfferType = offerBearingSteps.find(({ step }) => step.offer_type)?.step.offer_type;
  const improvement = summary ? summary.base_pd - summary.target_pd_24w : 0;
  const preferredPolicy = (opeContent.preferred_policy_signal as GenericContent | undefined) ?? {};
  const readiness =
    (learningContent.learning_readiness_status_distribution as GenericContent | undefined) ?? {};
  const learningReadyShare = readNumber(
    (readiness.learning_ready as GenericContent | undefined)?.share,
  );
  const partialLearningReadyShare = readNumber(
    (readiness.partial_learning_ready as GenericContent | undefined)?.share,
  );
  const descriptiveOnlyShare = readNumber(
    (readiness.descriptive_only as GenericContent | undefined)?.share,
  );

  const contextLabels = {
    curated: text({
      tr: "Kurgulanmis demo gorunumu",
      en: "Curated demo snapshot",
    }),
    simulation: text({
      tr: "Temsili simulasyon",
      en: "Representative simulation",
    }),
    benchmark: text({
      tr: "Offline kiyas",
      en: "Offline benchmark",
    }),
  };

  const formatPercent = (value: number, digits = 0) =>
    new Intl.NumberFormat(locale, {
      style: "percent",
      maximumFractionDigits: digits,
      minimumFractionDigits: digits,
    }).format(value);

  const formatPointChange = (value: number, digits = 0) =>
    `${new Intl.NumberFormat(locale, {
      maximumFractionDigits: digits,
      minimumFractionDigits: digits,
    }).format(value * 100)} ${text({ tr: "puan", en: "pts" })}`;

  const formatNumber = (value: number, digits = 0) =>
    new Intl.NumberFormat(locale, {
      maximumFractionDigits: digits,
      minimumFractionDigits: digits,
    }).format(value);

  const formatPolicySignal = (value: unknown) => {
    const signal = String(value ?? "");
    const labels: Record<string, { tr: string; en: string }> = {
      supports_treatment: {
        tr: "Yeni politika lehine sinyal",
        en: "Signal favors treatment",
      },
      supports_control: {
        tr: "Mevcut politika lehine sinyal",
        en: "Signal favors control",
      },
      mixed: {
        tr: "Karisik sinyal",
        en: "Mixed signal",
      },
      insufficient_evidence: {
        tr: "Kanit yetersiz",
        en: "Insufficient evidence",
      },
    };

    return (labels[signal] ?? { tr: signal, en: signal })[lang];
  };

  const formatBusinessOutcome = (
    value: "now" | "week_4" | "week_12" | "week_24" | "not_ready_yet" | undefined,
  ) => {
    const labels = {
      now: {
        tr: "Bugun krediye hazir",
        en: "Credit-ready now",
      },
      week_4: {
        tr: "4 haftada krediye hazir",
        en: "Credit-ready in 4 weeks",
      },
      week_12: {
        tr: "12 haftada krediye hazir",
        en: "Credit-ready in 12 weeks",
      },
      week_24: {
        tr: "24 haftada krediye hazir",
        en: "Credit-ready in 24 weeks",
      },
      not_ready_yet: {
        tr: "Ek guclenme gerekiyor",
        en: "Additional strengthening required",
      },
    };

    return labels[value ?? "not_ready_yet"][lang];
  };

  const customerStatus = !summary
    ? text({ tr: "Degerlendirme bekleniyor", en: "Awaiting evaluation" })
    : summary.trajectory_status === "on_track"
      ? text({ tr: "Kontrollu toparlanma", en: "Controlled recovery" })
      : summary.trajectory_status === "needs_replan"
        ? text({ tr: "Mudahale gerekiyor", en: "Needs intervention" })
        : summary.trajectory_status === "degraded"
          ? text({ tr: "Toparlanma zayifladi", en: "Recovery weakened" })
          : text({ tr: "Toparlanma yolu acildi", en: "Recovery path opened" });

  const expectedOutcome = formatBusinessOutcome(summary?.credit_readiness_stage);
  const riskTrend =
    improvement > 0.001
      ? text({ tr: "Azaliyor", en: "Decreasing" })
      : improvement < -0.001
        ? text({ tr: "Artiyor", en: "Increasing" })
        : text({ tr: "Yatay", en: "Stable" });

  const readinessHint =
    executiveSummary?.expected_result
      ? pickLocalizedText(executiveSummary.expected_result.description, lang)
      : summary?.credit_readiness_stage === "week_4"
        ? text({
            tr: "Ilk 4 haftalik disiplin kuruldugunda dosya hizla yeniden basvuru seviyesine yaklasiyor.",
            en: "Once the first 4 weeks of discipline land, the file moves quickly toward re-application readiness.",
          })
        : summary?.credit_readiness_stage === "week_12"
          ? text({
              tr: "Temiz orta vade davranisi korunursa dosyanin 12 hafta icinde krediye hazir olmasi bekleniyor.",
              en: "If the cleaner mid-term behavior holds, the file is expected to become credit-ready within 12 weeks.",
            })
          : summary?.credit_readiness_stage === "week_24"
            ? text({
                tr: "Bu gorunum daha uzun vadeli iyilesme gerektiriyor; hedef 24 haftalik pencerede kuruluyor.",
                en: "This view needs a longer improvement runway, with the target landing in the 24-week window.",
              })
            : text({
                tr: "Dosya gucleniyor ancak daha fazla istikrar gormeden yeniden basvuru onerilmiyor.",
                en: "The file is improving, but re-application is not recommended until more stability is visible.",
              });

  const riskTrendHint =
    improvement > 0.001
      ? text({
          tr: "Beklenen yol, risk baskisinin checkpoint'ler ilerledikce gerilemesini hedefliyor.",
          en: "The expected path is designed to reduce risk pressure as checkpoints progress.",
        })
      : improvement < -0.001
        ? text({
            tr: "Bu gorunum ilave baski isareti veriyor; teknik detaylar ve yeniden planlama sinyali gozden gecirilmeli.",
            en: "This view signals added pressure; the technical reveal and replan posture should be reviewed.",
          })
        : text({
            tr: "Risk gorunumu su an korunuyor; kalici iyilesme sonraki pencerelere bagli.",
            en: "The risk view is currently holding steady; durable improvement depends on later windows.",
          });

  const customerNarrativeHeadline = executiveSummary?.headline
    ? pickLocalizedText(executiveSummary.headline, lang)
    : text({
        tr: "Reddedilen dosya, cikmaz yerine yonetilen bir toparlanma akisina alinmis durumda.",
        en: "The declined file has been moved into a governed recovery flow instead of a dead end.",
      });

  const customerNarrativeSummary = executiveSummary?.summary_line
    ? pickLocalizedText(executiveSummary.summary_line, lang)
    : text({
        tr: "Varsayilan okumada once kurumun verecegi is karari gorulur; sayisal motor izleri ise yalnizca acildiginda gelir.",
      en: "The default read shows the business decision first; the underlying engine traces appear only when opened.",
      });
  const executiveCards = executiveSummary
    ? [
        {
          key: "risk_start",
          eyebrow: text({ tr: "Baslangic riski", en: "Starting risk" }),
          value: executiveSummary.risk_start,
        },
        {
          key: "recommended_path",
          eyebrow: text({ tr: "Onerilen yol", en: "Recommended path" }),
          value: executiveSummary.recommended_path,
        },
        {
          key: "checkpoint_4w_summary",
          eyebrow: text({ tr: "4 haftalik oncelik", en: "4-week priority" }),
          value: executiveSummary.checkpoint_4w_summary,
        },
        {
          key: "time_to_readiness",
          eyebrow: text({ tr: "Hazirlik takvimi", en: "Readiness timeline" }),
          value: executiveSummary.time_to_readiness,
        },
        {
          key: "decision_view",
          eyebrow: text({ tr: "Karar gorunumu", en: "Decision view" }),
          value: executiveSummary.decision_view,
        },
        {
          key: "follow_through_readiness",
          eyebrow: text({ tr: "Takip gercekligi", en: "Follow-through readiness" }),
          value: executiveSummary.follow_through_readiness ?? null,
        },
        {
          key: "offer_status",
          eyebrow: text({ tr: "Kurum destegi", en: "Institution support" }),
          value: executiveSummary.offer_status,
        },
        {
          key: "narrative_confidence",
          eyebrow: text({ tr: "Anlatim guveni", en: "Narrative confidence" }),
          value: executiveSummary.narrative_confidence,
        },
      ]
    : [];

  const portfolioStory =
    String(batchContent.batch_summary_story ?? "") ||
    text({
      tr: "Benzer dosyalarda toparlanma potansiyeli portfoy geneline yayilabiliyor.",
      en: "Across similar files, the recovery path can translate into broader portfolio movement.",
    });

  const offerStory = hasOffer && firstOfferType
    ? text({
        tr: `${formatOfferType(firstOfferType, lang)} bu portfoyde musteri davranisini tamamlayan yonetilen bir kurum hamlesi olarak konumlanir.`,
        en: `${formatOfferType(firstOfferType, lang)} appears as a governed institution-side move that complements customer behavior.`,
      })
    : text({
        tr: "Teklif katmani, yalnizca kurum tarafinda anlamli ve guvenli etki yarattiginda devreye girer.",
        en: "The offer layer appears only when it creates meaningful institution-side impact within governance limits.",
      });

  const learningStory =
    preferredPolicy?.why && String(preferredPolicy.why).trim()
      ? String(preferredPolicy.why)
      : text({
          tr: "Kararlar ve sonuclar biriktikce hangi politika kolunun guclendigini offline olarak okumak mumkun hale gelir.",
          en: "As decisions and outcomes accumulate, the team can read offline which policy arm is pulling ahead.",
        });

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Demo Merkezi", en: "Demo Center" })}
        title={text({
          tr: "Kurumsal ekipler icin toparlanma, portfoy etkisi ve teklif ogrenmesini is diliyle gorun.",
          en: "See recovery, portfolio impact, and offer learning in business language built for institutional teams.",
        })}
        supportingNote={text({
          tr: "Yonetici gorunumu varsayilan, teknik detay istege bagli.",
          en: "Executive view by default, technical detail on demand.",
        })}
        disclaimer={text({
          tr: "Temsili urun onizlemesi — gercek musteri verisi degildir",
          en: "Representative product preview — not real customer data",
        })}
        description={text({
          tr: "Bu sayfa, motor ciktisini degil is kararini one cikarir: once tekil musteri toparlanmasi, sonra portfoy etkisi, teklif performansi ve ogrenme guveni.",
          en: "This page puts the business decision ahead of the engine output: first the customer recovery path, then portfolio impact, offer performance, and learning confidence.",
        })}
        primaryCta={{ href: "/contact", label: text({ tr: "Demo Talep Et", en: "Request Demo" }) }}
        secondaryCta={{ href: "/proof", label: text({ tr: "Kanitlari Incele", en: "Review Proof" }) }}
        tertiaryCta={{ href: "/product", label: text({ tr: "Urunu Anla", en: "Understand the Product" }) }}
        badges={[
          contextLabels.curated,
          contextLabels.simulation,
          contextLabels.benchmark,
        ]}
        variant="product"
        aside={
          <div className="panel-product p-6 lg:w-[420px]">
            <div className="surface-label">{text({ tr: "Okuma sirasi", en: "Reading order" })}</div>
            <div className="mt-3 font-display text-2xl font-semibold text-white">
              {text({
                tr: "Yonetici ozeti once gelir. Kanit ve teknik iz acildiginda gorunur.",
                en: "The executive summary comes first. Evidence and technical trace appear when opened.",
              })}
            </div>
            <div className="mt-5 space-y-4 text-sm leading-7 text-slate-300">
              <div>
                <span className="text-white">
                  {text({ tr: "Musteri", en: "Customer" })}:
                </span>{" "}
                {text({
                  tr: "Reddedilen bir dosya nasil kontrollu toparlanmaya giriyor.",
                  en: "How a declined file moves into controlled recovery.",
                })}
              </div>
              <div>
                <span className="text-white">
                  {text({ tr: "Portfoy", en: "Portfolio" })}:
                </span>{" "}
                {text({
                  tr: "Bu yolun genelde nasil bir toplu hareket yarattigi.",
                  en: "What that journey translates into across a broader book.",
                })}
              </div>
              <div>
                <span className="text-white">
                  {text({ tr: "Teklif", en: "Offer" })}:
                </span>{" "}
                {text({
                  tr: "Kurum tekliflerinin ayni karar yuzeyinde nasil olculdugu.",
                  en: "How institution-side offers are measured inside the same decision surface.",
                })}
              </div>
              <div>
                <span className="text-white">
                  {text({ tr: "Ogrenme", en: "Learning" })}:
                </span>{" "}
                {text({
                  tr: "Hangi politikanin guclendigine dair offline guvenin nasil kuruldugu.",
                  en: "How offline confidence is built around which policy is winning.",
                })}
              </div>
            </div>
          </div>
        }
      />

      <section className="shell py-16 sm:py-20">
        <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr] xl:items-start">
          <div className="panel-product p-6">
            <div className="surface-label">{text({ tr: "Yonetici gorunumu", en: "Executive view" })}</div>
            <div className="mt-3 font-display text-3xl font-semibold text-white">
              {text({
                tr: "Bu demo, ekran yogunlugunu degil karar netligini one cikarir.",
                en: "This demo prioritizes decision clarity over screen density.",
              })}
            </div>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300">
              {text({
                tr: "Kurumsal alici ilk bakista tekil toparlanma gorunumunu, portfoye cevrilen etkiyi ve gelecekte ogrenmeye donecek kayit kalitesini gorur.",
                en: "At first glance, an institutional buyer sees the single-customer recovery view, the portfolio translation, and the record quality that feeds future learning.",
              })}
            </p>
          </div>

          <div className="panel-product p-6">
            <div className="surface-label">{text({ tr: "Bu sayfada ne var", en: "What is on this page" })}</div>
            <div className="mt-4 space-y-4 text-sm leading-7 text-slate-300">
              <div>
                <span className="text-white">{text({ tr: "1.", en: "1." })}</span>{" "}
                {text({
                  tr: "Bir musteri dosyasinda kontrollu toparlanma hikayesi.",
                  en: "A controlled recovery story for one customer file.",
                })}
              </div>
              <div>
                <span className="text-white">{text({ tr: "2.", en: "2." })}</span>{" "}
                {text({
                  tr: "Bu hikayenin portfoy seviyesinde neye donustugu.",
                  en: "What that story becomes at the portfolio level.",
                })}
              </div>
              <div>
                <span className="text-white">{text({ tr: "3.", en: "3." })}</span>{" "}
                {text({
                  tr: "Teklif katmaninin kabul ve etki tarafinda ne uretebildigi.",
                  en: "What the offer layer can produce on acceptance and impact.",
                })}
              </div>
              <div>
                <span className="text-white">{text({ tr: "4.", en: "4." })}</span>{" "}
                {text({
                  tr: "Ayni karar izinin gelecekte ogrenme icin ne kadar hazir oldugu.",
                  en: "How ready the same decision trace is for future learning.",
                })}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <MetricTile
            label={text({ tr: "Musteri gorunumu", en: "Customer outlook" })}
            value={expectedOutcome}
            hint={readinessHint}
            context={contextLabels.curated}
            variant="product"
          />
          <MetricTile
            label={text({ tr: "Portfoy hareketi", en: "Portfolio movement" })}
            value={formatPercent(readNumber(batchContent.denied_to_approved_lift))}
            hint={text({
              tr: "Temsili toplulukta yeniden onaylanabilir banda donen dosya payi.",
              en: "Share of the representative cohort that moves back into an approval-ready band.",
            })}
            context={contextLabels.simulation}
            variant="product"
          />
          <MetricTile
            label={text({ tr: "Ogrenme hazirligi", en: "Learning readiness" })}
            value={formatPercent(learningReadyShare)}
            hint={text({
              tr: "Karar ve sonuc birlikte geldigi icin gelecekte politika analizine hazir kayit payi.",
              en: "Share of records already complete enough for future policy analysis.",
            })}
            context={contextLabels.benchmark}
            variant="product"
          />
        </div>
      </section>

      <section className="border-t border-white/10 bg-white/[0.02]">
        <div className="shell py-20">
          <BusinessSectionIntro
            bridge={text({
              tr: "Is hikayesi bir musteri dosyasinin nasil kontrollu toparlanmaya girdigiyle basliyor:",
              en: "The business story starts with how one customer file moves into controlled recovery:",
            })}
            eyebrow={text({ tr: "Musteri", en: "Customer" })}
            title={text({
              tr: "Varsayilan gorunum, teknik surec yerine is sonucunu anlatir.",
              en: "The default view explains the business outcome instead of the technical process.",
            })}
            summary={text({
              tr: "Bu bolum, dosyanin bugunku durumunu, beklenen sonucu ve risk yonunu ilk okumada netlestirir.",
              en: "This section clarifies the current status, expected outcome, and risk direction on the first read.",
            })}
            whyMatters={text({
              tr: "Karar sonrasinda kuruma gereken sey yeni bir teknik rapor degil, kontrollu toparlanma dilidir.",
              en: "After a decision, the institution needs controlled recovery language rather than another technical report.",
            })}
          />

          {customer && summary ? (
            <>
              <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <MetricTile
                  label={text({ tr: "Durum", en: "Status" })}
                  value={customerStatus}
                  hint={text({
                    tr: "Dosya reddedilmis halde kalmiyor; yonetilen bir toparlanma yoluna alinmis durumda.",
                    en: "The file is not left as a dead-end decline; it has been moved into a managed recovery path.",
                  })}
                  context={contextLabels.curated}
                  variant="product"
                />
                <MetricTile
                  label={text({ tr: "Beklenen sonuc", en: "Expected outcome" })}
                  value={expectedOutcome}
                  hint={readinessHint}
                  context={contextLabels.curated}
                  variant="product"
                />
                <MetricTile
                  label={text({ tr: "Risk trendi", en: "Risk trend" })}
                  value={riskTrend}
                  hint={riskTrendHint}
                  context={contextLabels.curated}
                  variant="product"
                />
              </div>

              <div className="mt-8 grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
                <div className="panel-product p-6">
                  <div className="surface-label">{text({ tr: "Musteri anlatimi", en: "Customer narrative" })}</div>
                  <div className="mt-3 font-display text-2xl font-semibold text-white">
                    {customerNarrativeHeadline}
                  </div>
                  <p className="mt-4 text-sm leading-7 text-slate-300">
                    {customerNarrativeSummary}
                  </p>

                  <div className="mt-6 grid gap-4 md:grid-cols-2">
                    <div className="rounded-[24px] border border-white/10 bg-slate-950/45 p-5">
                      <div className="surface-label">{text({ tr: "Musteri baglami", en: "Customer context" })}</div>
                      <div className="mt-4 space-y-3 text-sm leading-6 text-slate-300">
                        <div>
                          {text({ tr: "Profil", en: "Profile" })}:{" "}
                          <span className="text-white">{formatDemoProfile(customer.profile, lang)}</span>
                        </div>
                        <div>
                          {text({ tr: "Segment", en: "Segment" })}:{" "}
                          <span className="text-white">{formatDemoSegment(customer.segment, lang)}</span>
                        </div>
                        <div>
                          {text({ tr: "Gelir gorunumu", en: "Income view" })}:{" "}
                          <span className="text-white">{formatIncomeBand(customer.income_band, lang)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="rounded-[24px] border border-white/10 bg-slate-950/45 p-5">
                      <div className="surface-label">
                        {text({ tr: "Bir sonraki karar penceresi", en: "Next decision window" })}
                      </div>
                      <div className="mt-4 font-medium text-white">{expectedOutcome}</div>
                      <p className="mt-2 text-sm leading-7 text-slate-300">
                        {firstCheckpoint
                          ? formatCheckpointNote(
                              firstCheckpoint.week,
                              firstCheckpoint.approval_ready,
                              firstCheckpoint.gate_pass_estimate,
                              lang,
                            )
                          : text({
                              tr: "Ilk checkpoint, dosyanin yeni baski yaratmadan ilerleyip ilerlemedigini kontrol eder.",
                              en: "The first checkpoint verifies whether the file is progressing without creating new pressure.",
                            })}
                      </p>
                      <div className="mt-4 text-sm leading-6 text-slate-300">
                        {hasOffer && firstOfferType
                          ? text({
                              tr: `Gerekirse ${formatOfferType(firstOfferType, lang)} ayni karar akisinin icine eklenebilir.`,
                              en: `If needed, ${formatOfferType(firstOfferType, lang)} can be inserted into the same decision flow.`,
                            })
                          : text({
                              tr: "Bu gorunumde teklif katmani zorunlu degil; once davranis istikrari bekleniyor.",
                              en: "An offer layer is not required in this view; behavior stability comes first.",
                            })}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="panel-product p-6">
                  <div className="surface-label">{text({ tr: "Yonetici kartlari", en: "Executive cards" })}</div>
                  <div className="mt-4 grid gap-4 md:grid-cols-2">
                    {executiveCards.map((card) => (
                      <ExecutiveNarrativeCard
                        key={card.key}
                        eyebrow={card.eyebrow}
                        value={card.value}
                      />
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-8">
                <p className="section-bridge">
                  {text({
                    tr: "Bu yolun erken sagligi once checkpoint'lerde okunur, sonra aksiyon kartlariyla uygulanir:",
                    en: "The early health of this path is read through checkpoints first, then carried through action cards:",
                  })}
                </p>
                <div className="mt-4 grid gap-4 xl:grid-cols-[1.2fr_1fr_1fr]">
                  {roadmapContent.checkpoints.map((checkpoint) => (
                    <CheckpointStripCard
                      key={checkpoint.week}
                      label={formatCheckpointLabel(checkpoint.checkpoint_label, lang)}
                      week={checkpoint.week}
                      summary={
                        checkpoint.narrative
                          ? pickLocalizedText(checkpoint.narrative.expected_state, lang)
                          : checkpoint.note
                      }
                      supporting={
                        checkpoint.narrative
                          ? pickLocalizedText(checkpoint.narrative.success_condition, lang)
                          : formatCheckpointNote(
                              checkpoint.week,
                              checkpoint.approval_ready,
                              checkpoint.gate_pass_estimate,
                              lang,
                            )
                      }
                      emphasis={checkpoint.week === 4}
                    />
                  ))}
                </div>
              </div>

              <div className="mt-8 grid gap-5">
                {activePhases.map((phase) => (
                  <RoadmapPhaseCard key={phase.phase_id} phase={phase} />
                ))}
              </div>

              {offerBearingSteps.length > 0 ? (
                <div className="mt-8 panel-product p-6">
                  <div className="surface-label">{text({ tr: "Kurum destegi", en: "Institution support" })}</div>
                  <div className="mt-3 font-display text-2xl font-semibold text-white">
                    {executiveSummary?.offer_status
                      ? pickLocalizedText(executiveSummary.offer_status.label, lang)
                      : text({
                          tr: "Bu planda kurum destegi ayni yolun destek katmani olarak konumlanir.",
                          en: "In this plan, institution support appears as a supporting layer inside the same path.",
                        })}
                  </div>
                  <p className="mt-4 text-sm leading-7 text-slate-300">
                    {executiveSummary?.offer_status
                      ? pickLocalizedText(executiveSummary.offer_status.description, lang)
                      : offerStory}
                  </p>
                  <div className="mt-6 grid gap-4 lg:grid-cols-2">
                    {offerBearingSteps.map(({ phase, step }) => (
                      <div
                        key={`${phase.phase_id}-${step.step_id ?? step.action_key}-offer`}
                        className="rounded-[24px] border border-signal/20 bg-signal/5 p-5"
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="surface-label border-signal/20 bg-signal/10 text-signal">
                            {formatWindowLabel(phase.target_window_weeks, lang)}
                          </span>
                          {step.offer_type ? (
                            <span className="surface-label border-signal/20 bg-signal/10 text-signal">
                              {formatOfferType(step.offer_type, lang)}
                            </span>
                          ) : null}
                        </div>
                        <div className="mt-3 font-medium text-white">
                          {step.narrative?.offer_narrative
                            ? pickLocalizedText(step.narrative.offer_narrative.offer_explanation, lang)
                            : text({
                                tr: "Bu adimla birlikte kurum tarafli destek degerlendirilebilir.",
                                en: "Institution-side support can be evaluated alongside this step.",
                              })}
                        </div>
                        <p className="mt-2 text-sm leading-7 text-slate-300">
                          {step.narrative?.offer_narrative
                            ? pickLocalizedText(step.narrative.offer_narrative.why_offered, lang)
                            : text({
                                tr: "Teklif destegi bu planin gerceklesmesini desteklemek icin eklenir.",
                                en: "Offer support is added to strengthen the realization of this plan.",
                              })}
                        </p>
                        {step.narrative?.offer_narrative?.offer_terms_summary ? (
                          <div className="mt-4 rounded-[18px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-300">
                            {pickLocalizedText(step.narrative.offer_narrative.offer_terms_summary, lang)}
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {visibleReasons.length > 0 ? (
                <div className="mt-8">
                  <p className="section-bridge">
                    {text({
                      tr: "Bu plan, rastgele degil dosyanin baskin nedenlerine gore kuruluyor:",
                      en: "This plan is built around the dominant reasons in the file rather than at random:",
                    })}
                  </p>
                  <div className="mt-4 grid gap-4 lg:grid-cols-3">
                    {visibleReasons.map((reason) => (
                      <ReasonNarrativeCard
                        key={reason.reason_code}
                        title={pickLocalizedText(reason.reason_title, lang)}
                        description={pickLocalizedText(reason.reason_description, lang)}
                        hint={pickLocalizedText(reason.remediation_hint, lang)}
                        severity={reason.reason_severity ?? undefined}
                      />
                    ))}
                  </div>
                </div>
              ) : null}

              <div className="mt-8">
                <DemoSectionCta
                  title={text({
                    tr: "Bu sistemi kendi portfoyunuzde gormek ister misiniz?",
                    en: "Would you like to see this system on your portfolio?",
                  })}
                  description={text({
                    tr: "Kendi segmentleriniz, teklif kurallariniz ve karar akisiniza gore ayni toparlanma yuzeyini birlikte kuralim.",
                    en: "We can map the same recovery surface to your own segments, offer rules, and decision workflow.",
                  })}
                  ctaLabel={text({ tr: "Demo Talep Et", en: "Request Demo" })}
                />
              </div>
            </>
          ) : null}
        </div>
      </section>

      <section className="shell py-20">
        <BusinessSectionIntro
          bridge={text({
            tr: "Bu tekil musteri yolculugu su portfoy etkisine donusur:",
            en: "This single-customer journey translates to the following portfolio impact:",
          })}
          eyebrow={text({ tr: "Portfoy", en: "Portfolio" })}
          title={text({
            tr: "Toparlanma hikayesi, tek dosyada kalmayip toplu hareket uretir.",
            en: "The recovery story does not stay in one file; it creates broader movement.",
          })}
          summary={text({
            tr: "Varsayilan okumada yalnizca toplu donusum, risk iyilesmesi ve erken checkpoint sagligi gorunur.",
            en: "The default read shows only the aggregate movement, risk improvement, and early checkpoint health.",
          })}
          whyMatters={text({
            tr: "Kurumsal alici icin esas soru, iyi gorunen tek bir dosya degil bunun portfoyde tekrar edilip edilemeyecegidir.",
            en: "For an institutional buyer, the real question is not one good-looking file but whether the effect repeats across the portfolio.",
          })}
        />

        <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <MetricTile
            label={text({ tr: "Toplam toparlanma hareketi", en: "Recovery lift" })}
            value={formatPercent(readNumber(batchContent.denied_to_approved_lift))}
            hint={text({
              tr: "Temsili toplulukta yeniden onaylanabilir banda giren dosya payi.",
              en: "Share of the representative cohort that moves back into an approval-ready band.",
            })}
            context={contextLabels.simulation}
            variant="product"
          />
          <MetricTile
            label={text({ tr: "Ortalama risk iyilesmesi", en: "Average risk improvement" })}
            value={formatPointChange(readNumber(batchContent.avg_pd_reduction), 1)}
            hint={text({
              tr: "Planlar uygulandiginda beklenen ortalama risk gerilemesi.",
              en: "Expected average risk reduction once plans are applied.",
            })}
            context={contextLabels.simulation}
            variant="product"
          />
          <MetricTile
            label={text({ tr: "Ilk 4 haftalik saglik", en: "First-4-weeks health" })}
            value={formatPercent(readNumber(batchContent.trajectory_gate_pass_rate_4w))}
            hint={text({
              tr: "Erken checkpoint'i kontrollu sekilde gecmesi beklenen planlarin payi.",
              en: "Share of plans expected to pass the early checkpoint in a controlled way.",
            })}
            context={contextLabels.simulation}
            variant="product"
          />
        </div>

        <div className="mt-8 grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="panel-product p-6">
            <div className="surface-label">{contextLabels.simulation}</div>
            <div className="mt-3 font-display text-2xl font-semibold text-white">
              {text({
                tr: "Portfoy anlatimi",
                en: "Portfolio narrative",
              })}
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-300">{portfolioStory}</p>
          </div>

          <div className="panel-product p-6">
            <div className="surface-label">{text({ tr: "Neyi gosterir", en: "What this shows" })}</div>
            <p className="mt-4 text-sm leading-7 text-slate-300">
              {text({
                tr: "Demo, yalnizca en iyi dosyalari degil erken checkpoint disiplinini koruyarak anlamli toparlanma uretebilen genis bir uygulama alanini gosterir.",
                en: "The demo shows a broader operating lane that can generate meaningful recovery without sacrificing early-checkpoint discipline.",
              })}
            </p>
          </div>
        </div>

        <DemoSectionCta
          title={text({
            tr: "Bu sistemi kendi portfoyunuzde gormek ister misiniz?",
            en: "Would you like to see this system on your portfolio?",
          })}
          description={text({
            tr: "Kendi red portfoyunuz icin hangi segmentlerde toplu toparlanma uretilebildigini birlikte haritalayabiliriz.",
            en: "We can map where the same portfolio movement appears across your own declined segments.",
          })}
          ctaLabel={text({ tr: "Demo Talep Et", en: "Request Demo" })}
        />
      </section>

      <section className="border-t border-white/10 bg-white/[0.02]">
        <div className="shell py-20">
          <BusinessSectionIntro
            bridge={text({
              tr: "Portfoy hareketi netlestiginde teklif stratejisi ayni karar yuzeyine baglanir:",
              en: "Once portfolio movement is clear, offer strategy connects into the same decision surface:",
            })}
            eyebrow={text({ tr: "Teklif", en: "Offer" })}
            title={text({
              tr: "Kurum teklifleri musteri toparlanmasindan ayri bir ekran degil ayni akisin parcasi olur.",
              en: "Institution-side offers become part of the same flow instead of a separate screen.",
            })}
            summary={text({
              tr: "Varsayilan okumada yalnizca kabul, birlesik gerceklesme ve beklenen etki gorunur.",
              en: "The default read shows only acceptance, combined realization, and expected impact.",
            })}
            whyMatters={text({
              tr: "Tekliflerin ticari degeri, ancak kurum yonetimi icinde ve musteri adimlariyla birlikte olculdugunde anlamlidir.",
              en: "Offers create real commercial value only when measured within governance and alongside customer actions.",
            })}
          />

          <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <MetricTile
              label={text({ tr: "Teklif kabul olasiligi", en: "Offer acceptance" })}
              value={formatPercent(readNumber(offerMetrics.offer_acceptance_probability_mean))}
              hint={text({
                tr: "Kurum teklifinin temsil gucu olan kabul olasiligi.",
                en: "Representative likelihood that the institution-side offer is accepted.",
              })}
              context={contextLabels.simulation}
              variant="product"
            />
            <MetricTile
              label={text({ tr: "Birlesik gerceklesme", en: "Combined realization" })}
              value={formatPercent(
                readNumber(offerMetrics.combined_plan_realization_probability_mean),
              )}
              hint={text({
                tr: "Musteri adimi ve teklif kabulunun birlikte gerceklesme olasiligi.",
                en: "Likelihood that the customer action and offer acceptance happen together.",
              })}
              context={contextLabels.simulation}
              variant="product"
            />
            <MetricTile
              label={text({ tr: "Beklenen etki", en: "Expected impact" })}
              value={formatPointChange(readNumber(offerMetrics.approval_rate_proxy_delta), 1)}
              hint={text({
                tr: "Temsili teklifte beklenen onay proxy hareketi.",
                en: "Expected approval-proxy movement for the representative offer layer.",
              })}
              context={contextLabels.simulation}
              variant="product"
            />
          </div>

          <div className="mt-8 grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
            <div className="panel-product p-6">
              <div className="surface-label">{contextLabels.simulation}</div>
              <div className="mt-3 font-display text-2xl font-semibold text-white">
                {text({ tr: "Teklif anlatimi", en: "Offer narrative" })}
              </div>
              <p className="mt-4 text-sm leading-7 text-slate-300">{offerStory}</p>
            </div>

            <div className="panel-product p-6">
              <div className="surface-label">{text({ tr: "Neyi gosterir", en: "What this shows" })}</div>
              <p className="mt-4 text-sm leading-7 text-slate-300">
                {text({
                  tr: "Kurum teklifleri yalnizca ticari olarak degil, kabul ve gerceklesme ile birlikte bakildiginda operasyonel olarak da degerlendirilir.",
                  en: "Institution-side offers are evaluated not only commercially, but operationally through acceptance and realization together.",
                })}
              </p>
            </div>
          </div>

          <DemoSectionCta
            title={text({
              tr: "Bu sistemi kendi portfoyunuzde gormek ister misiniz?",
              en: "Would you like to see this system on your portfolio?",
            })}
            description={text({
              tr: "Tekliflerinizin kabul, etki ve yonetim dengesini ayni karar yuzeyinde birlikte test edebiliriz.",
              en: "We can test the acceptance, impact, and governance balance of your own offers in the same decision surface.",
            })}
            ctaLabel={text({ tr: "Demo Talep Et", en: "Request Demo" })}
          />
        </div>
      </section>

      <section className="shell py-20">
        <BusinessSectionIntro
          bridge={text({
            tr: "Kararlar ve teklifler uygulandikca ayni sistem hangi politikanin guclendigini ogrenmeye baslar:",
            en: "As decisions and offers are applied, the same system starts learning which policy is pulling ahead:",
          })}
          eyebrow={text({ tr: "Ogrenme", en: "Learning" })}
          title={text({
            tr: "Iyi bir urun yalnizca bugunu yonetmez, yarin icin daha guvenli karar verir.",
            en: "A strong product does not only manage today; it makes tomorrow's decisions safer.",
          })}
          summary={text({
            tr: "Varsayilan okumada karar kayit kalitesi, sonuc kapsami ve ogrenmeye hazir kayit payi gorunur.",
            en: "The default read shows decision log quality, outcome coverage, and the share of learning-ready records.",
          })}
          whyMatters={text({
            tr: "Kurumsal guven, sonuc kayitlarinin gelecekte politika secimini besleyebildigi yerde derinlesir.",
            en: "Enterprise trust deepens when outcome records can feed future policy choices.",
          })}
        />

        <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <MetricTile
            label={text({ tr: "Karar kayit tamligi", en: "Decision log completeness" })}
            value={formatPercent(readNumber(learningContent.decision_log_completeness))}
            hint={text({
              tr: "Karar baglaminin daha sonra analize donebilme orani.",
              en: "How much of the decision context remains usable for later analysis.",
            })}
            context={contextLabels.benchmark}
            variant="product"
          />
          <MetricTile
            label={text({ tr: "Sonuc kapsami", en: "Outcome coverage" })}
            value={formatPercent(readNumber(learningContent.reward_90d_coverage))}
            hint={text({
              tr: "Birincil sonuc penceresinde geri donen kayit payi.",
              en: "Share of records that return within the primary outcome window.",
            })}
            context={contextLabels.benchmark}
            variant="product"
          />
          <MetricTile
            label={text({ tr: "Ogrenmeye hazir kayit", en: "Learning-ready records" })}
            value={formatPercent(learningReadyShare)}
            hint={text({
              tr: "Karar ve sonuc birlikte geldigi icin gelecekte politika degerlendirmesine hazir kayit payi.",
              en: "Share of records already complete enough for future policy evaluation.",
            })}
            context={contextLabels.benchmark}
            variant="product"
          />
        </div>

        <div className="mt-8 grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="panel-product p-6">
            <div className="surface-label">{contextLabels.benchmark}</div>
            <div className="mt-3 font-display text-2xl font-semibold text-white">
              {preferredPolicy?.signal
                ? formatPolicySignal(preferredPolicy.signal)
                : text({ tr: "Daha guclu sinyal bekleniyor", en: "Awaiting stronger signal" })}
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-300">{learningStory}</p>
          </div>

          <div className="panel-product p-6">
            <div className="surface-label">{text({ tr: "Neyi gosterir", en: "What this shows" })}</div>
            <p className="mt-4 text-sm leading-7 text-slate-300">
              {text({
                tr: "Bu katman, urunun yalnizca karar verdigini degil sonuclari toplayip gelecek politika secimini daha guvenli hale getirdigini gosterir.",
                en: "This layer shows that the product does not only decide; it also captures outcomes and makes the next policy choice safer.",
              })}
            </p>
          </div>
        </div>

        <DemoSectionCta
          title={text({
            tr: "Bu sistemi kendi portfoyunuzde gormek ister misiniz?",
            en: "Would you like to see this system on your portfolio?",
          })}
          description={text({
            tr: "Kendi karar loglariniz ve sonuc pencerelerinizle ne kadar hizli ogrenme hazirligi kurulabilecegini birlikte gosterebiliriz.",
            en: "We can show how quickly learning readiness can be established with your own decision logs and outcome windows.",
          })}
          ctaLabel={text({ tr: "Demo Talep Et", en: "Request Demo" })}
        />
      </section>

      <section className="border-t border-white/10 bg-slate-950/65">
        <div className="shell py-16">
          <details className="detail-panel px-6 py-5 text-sm text-slate-300">
            <summary className="cursor-pointer list-none font-semibold text-white">
              {text({ tr: "Analist gorunumu: teknik izi ac", en: "Analyst view: open the technical trace" })}
            </summary>

            <div className="mt-5 grid gap-5 xl:grid-cols-2">
              <div className="rounded-[24px] border border-white/10 bg-slate-950/35 p-5">
                <div className="surface-label">{text({ tr: "Musteri plan ozeti", en: "Customer plan summary" })}</div>
                <div className="mt-4 grid gap-2 text-sm text-slate-400">
                  <DetailRow
                    label={text({ tr: "Karar durumu", en: "Decision status" })}
                    value={formatDecisionStatus(summary?.decision_status ?? "", lang)}
                  />
                  <DetailRow
                    label={text({ tr: "Trajectory status", en: "Trajectory status" })}
                    value={formatTrajectoryStatus(summary?.trajectory_status ?? "", lang)}
                  />
                  <DetailRow
                    label={text({ tr: "Credit readiness", en: "Credit readiness" })}
                    value={formatCreditReadinessStage(summary?.credit_readiness_stage, lang)}
                  />
                  <DetailRow
                    label={text({ tr: "Baz PD", en: "Base PD" })}
                    value={formatPdPercent(summary?.base_pd ?? 0, lang)}
                  />
                  <DetailRow
                    label={text({ tr: "12 haftalik hedef PD", en: "12-week target PD" })}
                    value={formatPdPercent(summary?.target_pd_12w ?? 0, lang)}
                  />
                  <DetailRow
                    label={text({ tr: "Plan execution", en: "Plan execution" })}
                    value={formatPercent(summary?.plan_execution_probability ?? 0)}
                  />
                  <DetailRow
                    label={text({ tr: "Birlesik gerceklesme", en: "Combined realization" })}
                    value={formatPercent(summary?.combined_plan_realization_probability ?? 0)}
                  />
                  <DetailRow
                    label={text({ tr: "4 haftada hazirlik", en: "4-week approval readiness" })}
                    value={formatApprovalReady(Boolean(summary?.approval_ready_4w), lang)}
                  />
                </div>
              </div>

              <div className="rounded-[24px] border border-white/10 bg-slate-950/35 p-5">
                <div className="surface-label">{text({ tr: "Checkpoint izi", en: "Checkpoint trace" })}</div>
                <div className="mt-4 grid gap-3">
                  {roadmapContent?.checkpoints.map((checkpoint) => (
                    <div
                      key={`technical-checkpoint-${checkpoint.week}`}
                      className="rounded-[18px] border border-white/10 bg-white/[0.03] p-4"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="font-medium text-white">
                          {formatCheckpointLabel(checkpoint.checkpoint_label, lang)}
                        </div>
                        <div className="surface-label">
                          {text({ tr: "Hafta", en: "Week" })} {checkpoint.week}
                        </div>
                      </div>
                      <div className="mt-3 grid gap-2 text-sm text-slate-400">
                        <DetailRow
                          label={text({ tr: "Tahmini PD", en: "Predicted PD" })}
                          value={formatPdPercent(checkpoint.predicted_pd, lang)}
                        />
                        <DetailRow
                          label={text({ tr: "Gate gecis tahmini", en: "Gate pass estimate" })}
                          value={formatApprovalReady(checkpoint.gate_pass_estimate, lang)}
                        />
                        <DetailRow
                          label={text({ tr: "Approval ready", en: "Approval ready" })}
                          value={formatApprovalReady(Boolean(checkpoint.approval_ready), lang)}
                        />
                      </div>
                    </div>
                  )) ?? null}
                </div>
              </div>

              <div className="rounded-[24px] border border-white/10 bg-slate-950/35 p-5 xl:col-span-2">
                <div className="surface-label">{text({ tr: "Aksiyon izi", en: "Action trace" })}</div>
                <div className="mt-4 grid gap-4 lg:grid-cols-2">
                  {visibleSteps.length > 0 ? (
                    visibleSteps.map(({ phase, step }) => (
                      <div
                        key={`technical-step-${phase.phase_id}-${step.step_id ?? step.action_key}`}
                        className="rounded-[20px] border border-white/10 bg-white/[0.03] p-4"
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="surface-label">{formatWindowLabel(phase.target_window_weeks, lang)}</span>
                          <span className="surface-label">{step.action_key}</span>
                          {step.action_group_id ? (
                            <span className="surface-label">{step.action_group_id}</span>
                          ) : null}
                        </div>
                        <div className="mt-3 font-medium text-white">{step.action_title}</div>
                        <div className="mt-3 grid gap-2 text-sm text-slate-400">
                          <DetailRow
                            label={text({ tr: "Metric key", en: "Metric key" })}
                            value={String(step.primary_numeric_target?.metric_key ?? text({ tr: "yok", en: "n/a" }))}
                          />
                          <DetailRow
                            label={text({ tr: "Target", en: "Target" })}
                            value={
                              step.primary_numeric_target
                                ? `${formatNumber(step.primary_numeric_target.target_value, 1)} (${step.primary_numeric_target.unit})`
                                : text({ tr: "yok", en: "n/a" })
                            }
                          />
                          <DetailRow
                            label={text({ tr: "Due month", en: "Due month" })}
                            value={
                              step.primary_numeric_target
                                ? String(step.primary_numeric_target.due_month)
                                : text({ tr: "yok", en: "n/a" })
                            }
                          />
                          <DetailRow
                            label={text({ tr: "Difficulty", en: "Difficulty" })}
                            value={String(step.difficulty_label ?? text({ tr: "yok", en: "n/a" }))}
                          />
                          <DetailRow
                            label={text({ tr: "Action execution", en: "Action execution" })}
                            value={formatPercent(step.action_execution_probability ?? 0)}
                          />
                          <DetailRow
                            label={text({ tr: "Group execution", en: "Group execution" })}
                            value={formatPercent(step.action_group_execution_probability ?? 0)}
                          />
                          <DetailRow
                            label={text({ tr: "Approval-dependent", en: "Approval-dependent" })}
                            value={formatPercent(step.approval_dependent_probability ?? 0)}
                          />
                          <DetailRow
                            label={text({ tr: "Feature anchor", en: "Feature anchor" })}
                            value={String(step.technical_view?.feature_name ?? text({ tr: "yok", en: "n/a" }))}
                          />
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="rounded-[20px] border border-dashed border-white/10 bg-white/[0.02] p-4 text-slate-400">
                      {text({
                        tr: "Bu snapshot icinde action trace alanlari henuz mevcut degil.",
                        en: "Action trace fields are not present in this snapshot yet.",
                      })}
                    </div>
                  )}
                </div>
              </div>

              <div className="rounded-[24px] border border-white/10 bg-slate-950/35 p-5">
                <div className="surface-label">{text({ tr: "Narrative technical reveal", en: "Narrative technical reveal" })}</div>
                <div className="mt-4 grid gap-2 text-sm text-slate-400">
                  <DetailRow
                    label={text({ tr: "Feature changes", en: "Feature changes" })}
                    value={String(technicalReveal?.feature_changes.length ?? 0)}
                  />
                  <DetailRow
                    label={text({ tr: "Primary numeric targets", en: "Primary numeric targets" })}
                    value={String(technicalReveal?.primary_numeric_targets?.length ?? 0)}
                  />
                  <DetailRow
                    label={text({ tr: "Constraints applied", en: "Constraints applied" })}
                    value={String(technicalReveal?.constraints_applied.length ?? 0)}
                  />
                  <DetailRow
                    label={text({ tr: "Approval dependencies", en: "Approval dependencies" })}
                    value={String(technicalReveal?.approval_dependencies.length ?? 0)}
                  />
                  <DetailRow
                    label={text({ tr: "Diagnostic flags", en: "Diagnostic flags" })}
                    value={String(technicalReveal?.diagnostic_flags.length ?? 0)}
                  />
                  <DetailRow
                    label={text({ tr: "Narrative confidence", en: "Narrative confidence" })}
                    value={String(technicalReveal?.narrative_confidence_label ?? text({ tr: "yok", en: "n/a" }))}
                  />
                </div>
              </div>

              <div className="rounded-[24px] border border-white/10 bg-slate-950/35 p-5">
                <div className="surface-label">{text({ tr: "Portfoy metrikleri", en: "Portfolio metrics" })}</div>
                <div className="mt-4 grid gap-2 text-sm text-slate-400">
                  <DetailRow
                    label={text({ tr: "Oncesi onay orani", en: "Before approval rate" })}
                    value={formatPercent(readNumber(batchContent.before_approval_rate))}
                  />
                  <DetailRow
                    label={text({ tr: "Sonrasi onay orani", en: "After approval rate" })}
                    value={formatPercent(readNumber(batchContent.after_approval_rate))}
                  />
                  <DetailRow
                    label={text({ tr: "12 haftalik checkpoint sagligi", en: "12-week checkpoint health" })}
                    value={formatPercent(readNumber(batchContent.trajectory_gate_pass_rate_12w))}
                  />
                  <DetailRow
                    label={text({ tr: "24 haftalik checkpoint sagligi", en: "24-week checkpoint health" })}
                    value={formatPercent(readNumber(batchContent.trajectory_gate_pass_rate_24w))}
                  />
                  <DetailRow
                    label={text({ tr: "Kismi ilerleme orani", en: "Partial progress rate" })}
                    value={formatPercent(readNumber(batchContent.trajectory_partial_progress_rate))}
                  />
                  <DetailRow
                    label={text({ tr: "Yuksek risk erisimi", en: "High-risk reachability" })}
                    value={formatPercent(readNumber(batchContent.high_risk_reachability_rate))}
                  />
                </div>
              </div>

              <div className="rounded-[24px] border border-white/10 bg-slate-950/35 p-5">
                <div className="surface-label">{text({ tr: "Destekleyici sinyaller", en: "Supporting signals" })}</div>
                <div className="mt-4 grid gap-2 text-sm text-slate-400">
                  <DetailRow
                    label={text({ tr: "Davranissal adim orani", en: "Behavioral action rate" })}
                    value={formatPercent(readNumber(actionMetrics.action_type_behavioral_rate))}
                  />
                  <DetailRow
                    label={text({ tr: "Kismi uygulama olasiligi", en: "Partial execution likelihood" })}
                    value={formatPercent(readNumber(behaviorMetrics.partial_execution_rate))}
                  />
                  <DetailRow
                    label={text({ tr: "Yolunda kalan planlar", en: "Plans that stay on track" })}
                    value={formatPercent(readNumber(trajectoryMetrics.trajectory_on_track_rate))}
                  />
                  <DetailRow
                    label={text({ tr: "Uygulanamaz plan orani", en: "Infeasible plan rate" })}
                    value={formatPercent(readNumber(actionMetrics.infeasible_plan_rate))}
                  />
                </div>
              </div>

              <div className="rounded-[24px] border border-white/10 bg-slate-950/35 p-5">
                <div className="surface-label">{text({ tr: "Teklif metrikleri", en: "Offer metrics" })}</div>
                <div className="mt-4 grid gap-2 text-sm text-slate-400">
                  <DetailRow
                    label={text({ tr: "Teklif iceren planlar", en: "Plans with offers" })}
                    value={formatPercent(readNumber(offerMetrics.offer_plan_rate))}
                  />
                  <DetailRow
                    label={text({ tr: "Siralanabilir teklifler", en: "Rankable offers" })}
                    value={formatPercent(readNumber(offerMetrics.rankable_offer_rate))}
                  />
                  <DetailRow
                    label={text({ tr: "Guvenli teklif orani", en: "Governance-safe offer rate" })}
                    value={formatPercent(readNumber(offerMetrics.governance_safe_offer_rate))}
                  />
                  <DetailRow
                    label={text({ tr: "Baskin teklif tipi", en: "Dominant offer type" })}
                    value={formatOfferType(String(offerMetrics.dominant_offer_type ?? ""), lang)}
                  />
                  <DetailRow
                    label={text({ tr: "Recovery proxy", en: "Recovery proxy" })}
                    value={formatNumber(readNumber(offerMetrics.expected_recovery_proxy), 1)}
                  />
                  <DetailRow
                    label={text({ tr: "Onay proxy delta", en: "Approval proxy delta" })}
                    value={formatPointChange(readNumber(offerMetrics.approval_rate_proxy_delta), 1)}
                  />
                </div>
              </div>

              <div className="rounded-[24px] border border-white/10 bg-slate-950/35 p-5">
                <div className="surface-label">{text({ tr: "Ogrenme ve OPE", en: "Learning and OPE" })}</div>
                <div className="mt-4 grid gap-2 text-sm text-slate-400">
                  <DetailRow
                    label={text({ tr: "Odeme davranisi kapsami", en: "Payment behavior coverage" })}
                    value={formatPercent(readNumber(learningContent.has_payment_behavior_rate))}
                  />
                  <DetailRow
                    label={text({ tr: "Recovery sonucu kapsami", en: "Recovery outcome coverage" })}
                    value={formatPercent(readNumber(learningContent.has_recovery_outcome_rate))}
                  />
                  <DetailRow
                    label={text({ tr: "Teklif kabul kapsami", en: "Offer acceptance coverage" })}
                    value={formatPercent(readNumber(learningContent.has_offer_acceptance_rate))}
                  />
                  <DetailRow
                    label={text({ tr: "Aksiyon tamamlama kapsami", en: "Action completion coverage" })}
                    value={formatPercent(readNumber(learningContent.has_action_completion_rate))}
                  />
                  <DetailRow
                    label={text({ tr: "Karsilastirma durumu", en: "Comparison status" })}
                    value={String(opeContent.comparison_status ?? text({ tr: "yok", en: "n/a" }))}
                  />
                  <DetailRow
                    label={text({ tr: "OPE guveni", en: "OPE confidence" })}
                    value={String(opeContent.ope_confidence ?? text({ tr: "Belirsiz", en: "Unclear" }))}
                  />
                  <DetailRow
                    label={text({ tr: "Baskin politika kolu", en: "Preferred policy arm" })}
                    value={String(preferredPolicy?.policy_arm ?? text({ tr: "yok", en: "n/a" }))}
                  />
                  <DetailRow
                    label={text({ tr: "Betimsel kayitlar", en: "Descriptive-only records" })}
                    value={formatPercent(descriptiveOnlyShare)}
                  />
                  <DetailRow
                    label={text({ tr: "Kismi ogrenme hazirligi", en: "Partial learning ready" })}
                    value={formatPercent(partialLearningReadyShare)}
                  />
                </div>
              </div>
            </div>
          </details>
        </div>
      </section>
    </div>
  );
}
