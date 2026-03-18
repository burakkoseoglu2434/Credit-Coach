import { CapabilityCard } from "@/components/CapabilityCard";
import { ComparisonBar } from "@/components/ComparisonBar";
import { MetricTile } from "@/components/MetricTile";
import { PageHero } from "@/components/PageHero";
import { RoadmapPhaseCard } from "@/components/RoadmapPhaseCard";
import { SectionHeading } from "@/components/SectionHeading";
import { demoOverviewCards } from "@/data/site-content";
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
  formatRiskBand,
  formatTrajectoryStatus,
  pickLocalizedText,
} from "@/lib/demo-formatters";
import type { SingleCustomerDemo } from "@shared/demo-schema";

type GenericContent = Record<string, unknown>;

function readNumber(value: unknown) {
  return typeof value === "number" ? value : 0;
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
        tr: "Kanıt yetersiz",
        en: "Insufficient evidence",
      },
    };

    return (labels[signal] ?? { tr: signal, en: signal })[lang];
  };

  const customer = roadmapContent?.customer;
  const summary = roadmapContent?.summary;
  const firstCheckpoint = roadmapContent?.checkpoints[0];
  const narrative = roadmapContent?.narrative;
  const executiveSummary = narrative?.executive_summary;
  const isLiveDemo = Boolean(roadmapContent?.meta?.live);
  const hasOffer = roadmapContent?.phases.some((phase) =>
    phase.steps.some((step) => step.offer_type),
  );
  const firstOfferType = roadmapContent?.phases
    .flatMap((phase) => phase.steps)
    .find((step) => step.offer_type)?.offer_type;
  const improvement = summary ? summary.base_pd - summary.target_pd_24w : 0;
  const preferredPolicy = (opeContent.preferred_policy_signal as GenericContent | undefined) ?? undefined;
  const readiness = (learningContent.learning_readiness_status_distribution as GenericContent | undefined) ?? {};
  const readinessHint =
    executiveSummary
      ? pickLocalizedText(executiveSummary.expected_result.description, lang)
      :
    summary?.decision_status === "NEEDS_REVIEW"
      ? text({
          tr: "Profil yeniden basvuru esigine yaklasmis olsa da son karar icin manuel review gerekiyor.",
          en: "The profile is moving toward re-application readiness, but the final decision still requires manual review.",
        })
      : summary?.credit_readiness_stage === "now"
      ? text({
          tr: "Musteri mevcut gorunumde yeniden basvuru efigine ulasmis durumda.",
          en: "The customer is already back at an approval-ready threshold in this view.",
        })
      : summary?.credit_readiness_stage === "week_4"
        ? text({
            tr: "Ilk 4 haftalik aksiyonlar tamamlanirsa yeniden basvuru zemini hizla olusuyor.",
            en: "If the first 4-week actions land, re-application readiness forms quickly.",
          })
        : summary?.credit_readiness_stage === "week_12"
          ? text({
              tr: "Yapisal adimlar tamamlandiginda orta vadede krediye hazirlik bekleniyor.",
              en: "Credit readiness is expected by the mid-term checkpoint once structural steps land.",
            })
          : summary?.credit_readiness_stage === "week_24"
            ? text({
                tr: "Krediye hazirlik uzun vadeli iyilesme ile geliyor; kisa vadede daha fazla destek gerekiyor.",
                en: "Readiness arrives through longer-horizon improvement, with more support needed early on.",
              })
            : text({
                tr: "Bu plan ilerleme sagliyor, ancak daha fazla guclenme olmadan krediye hazirlik olusmuyor.",
                en: "The plan creates progress, but more strengthening is still needed before approval readiness.",
              });

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Demo Merkezi", en: "Demo Center" })}
        title={text({
          tr: "Temsili urun akisini tek musteri, portfoy ve ogrenme yuzeyinde gorun.",
          en: "See the representative product flow across customer, portfolio, and learning surfaces.",
        })}
        supportingNote={
          isLiveDemo
            ? text({ tr: "Canli model calistirma", en: "Live model run" })
            : text({ tr: "Temsili urun onizlemesi", en: "Representative product preview" })
        }
        description={text({
          tr: "Bu demo, credit-coach'in kurumsal ekipler icin nasil deger urettigini ham motor ciktisi yerine karar diliyle gosterir.",
          en: "This demo shows how credit-coach creates value for institutional teams through decision language rather than raw engine output.",
        })}
        primaryCta={{ href: "/contact", label: text({ tr: "Demo Talep Et", en: "Request a Demo" }) }}
        secondaryCta={{ href: "/proof", label: text({ tr: "Kanitlari Incele", en: "Review Proof" }) }}
        tertiaryCta={{ href: "/product", label: text({ tr: "Urunu Anla", en: "Understand the Product" }) }}
        badges={[
          text({ tr: "Kurumsal karar yuzeyi", en: "Institutional decision surface" }),
          isLiveDemo
            ? text({ tr: "Ornek kullanici icin canli sonuc", en: "Live result for a sample user" })
            : text({ tr: "Temsili demo gorunumu", en: "Curated demo snapshot" }),
          text({ tr: "Is odakli anlatim", en: "Business-first storytelling" }),
        ]}
        aside={
          <div className="grid gap-4 lg:w-[520px] lg:grid-cols-2">
            {demoOverviewCards.map((card) => (
              <CapabilityCard
                key={card.title.tr}
                title={text(card.title)}
                description={text(card.description)}
                icon={card.icon}
                tone="default"
              />
            ))}
          </div>
        }
      />

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Demo ozeti", en: "Demo overview" })}
            title={text({
              tr: "Bu ekran neden onemli?",
              en: "Why this screen matters",
            })}
            description={text({
              tr: "Burada urunun yalnizca ne anlattigi degil, hangi is sorusunu cozdugu da netlesir: musteri aksiyonu, portfoy etkisi, teklif stratejisi ve ogrenme sinyali.",
              en: "This is where the product stops looking like a prototype and starts answering business questions around customer action, portfolio impact, offer strategy, and learning signal.",
            })}
          />
          <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {demoOverviewCards.map((card) => (
              <CapabilityCard
                key={`${card.title.tr}-overview`}
                eyebrow={text({ tr: "Neden onemli", en: "Why it matters" })}
                title={text(card.title)}
                description={text(card.description)}
                icon={card.icon}
              />
            ))}
          </div>
        </div>
      </section>

      <section className="shell py-20">
        <SectionHeading
          eyebrow={text({ tr: "Tek musteri", en: "Single customer" })}
          title={text({
            tr: "Bir red karari, yonlendirilmis bir toparlanma planina donusur.",
            en: "A declined case becomes a guided recovery path.",
          })}
          description={text({
            tr: "Bu ekran neden onemli? Cunku ekipler bir karar sonrasinda musteriye ne gosterilecegini, hangi teklifin dahil oldugunu ve ilk 4 haftada ne beklenmesi gerektigini burada gorur.",
            en: "Why it matters: teams can see what a customer-facing next step looks like, whether an offer is included, and what should happen in the first 4 weeks.",
          })}
        />
        {customer && summary ? (
          <>
            <div className="mt-10 grid gap-5 xl:grid-cols-[1.3fr_0.7fr]">
              <div className="panel p-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="eyebrow !mb-3">
                      {text({ tr: "Yonetici ozeti", en: "Executive summary" })}
                    </div>
                    <div className="font-display text-3xl font-semibold text-white">
                      {pickLocalizedText(
                        executiveSummary?.headline,
                        lang,
                        text({
                          tr: "Musteri, asamali bir toparlanma yoluna alinmis durumda.",
                          en: "The customer is now on a phased recovery path.",
                        }),
                      )}
                    </div>
                    {executiveSummary?.summary_line ? (
                      <div className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">
                        {pickLocalizedText(executiveSummary.summary_line, lang)}
                      </div>
                    ) : null}
                  </div>
                  <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-arctic/75">
                    {isLiveDemo
                      ? text({ tr: "Canli model sonucu", en: "Live model result" })
                      : text({ tr: "Kurgulanmis demo gorunumu", en: "Curated demo snapshot" })}
                  </div>
                </div>
                <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  <MetricTile
                    label={text({ tr: "Baslangic riski", en: "Starting risk" })}
                    value={
                      executiveSummary
                        ? pickLocalizedText(executiveSummary.risk_start.label, lang)
                        : formatRiskBand(customer.risk_band, lang)
                    }
                    hint={
                      executiveSummary
                        ? pickLocalizedText(executiveSummary.risk_start.description, lang)
                        : text({
                            tr: "Duzensiz ama toparlanabilir bir profil.",
                            en: "A pressured but recoverable profile.",
                          })
                    }
                  />
                  <MetricTile
                    label={text({ tr: "Karar gorunumu", en: "Decision outlook" })}
                    value={
                      executiveSummary
                        ? pickLocalizedText(executiveSummary.decision_view.label, lang)
                        : formatDecisionStatus(summary.decision_status, lang)
                    }
                    hint={
                      executiveSummary
                        ? pickLocalizedText(executiveSummary.decision_view.description, lang)
                        : summary.decision_status === "APPROVED"
                          ? text({
                              tr: "Model bu profili yeniden onaya uygun goruyor; yani karar dili toparlanma planindan onay gorunumune gecmis durumda.",
                              en: "The model now sees this profile as approval-ready, meaning the decision story has moved from recovery mode into an approval posture.",
                            })
                          : text({
                              tr: "Model, bu noktada otomatik karar yerine kontrollu bir karar gorunumu uretir.",
                              en: "At this stage, the model produces a controlled decision outlook rather than a blind automatic outcome.",
                            })
                    }
                  />
                  <MetricTile
                    label={text({ tr: "Teklif durumu", en: "Offer status" })}
                    value={
                      executiveSummary
                        ? pickLocalizedText(executiveSummary.offer_status.label, lang)
                        : hasOffer && firstOfferType
                          ? formatOfferType(firstOfferType, lang)
                          : text({ tr: "Teklif yok", en: "No offer included" })
                    }
                    hint={
                      executiveSummary
                        ? pickLocalizedText(executiveSummary.offer_status.description, lang)
                        : hasOffer && firstOfferType
                          ? text({
                              tr: "Kurum teklifi, musteri aksiyon planinin icinde yer aliyor.",
                              en: "The institution-side offer sits inside the customer plan.",
                            })
                          : text({
                              tr: "Bu yol haritasi kurum teklifi olmadan, musteri davranisini guclendirerek ilerliyor.",
                              en: "This path improves the outcome through customer action rather than an institution-side offer.",
                            })
                    }
                  />
                  <MetricTile
                    label={text({ tr: "4 haftalik checkpoint", en: "4-week checkpoint" })}
                    value={
                      executiveSummary
                        ? pickLocalizedText(executiveSummary.checkpoint_4w_summary.label, lang)
                        : firstCheckpoint?.gate_pass_estimate
                          ? text({ tr: "Olumlu gecis", en: "Positive checkpoint" })
                          : text({ tr: "Yakindan izleme", en: "Needs close follow-up" })
                    }
                    hint={
                      executiveSummary
                        ? pickLocalizedText(executiveSummary.checkpoint_4w_summary.description, lang)
                        : firstCheckpoint
                          ? formatCheckpointNote(
                              firstCheckpoint.week,
                              firstCheckpoint.approval_ready,
                              firstCheckpoint.gate_pass_estimate,
                              lang,
                            )
                          : undefined
                    }
                  />
                  <MetricTile
                    label={text({ tr: "Krediye hazirlik", en: "Credit readiness" })}
                    value={
                      executiveSummary
                        ? pickLocalizedText(executiveSummary.time_to_readiness.label, lang)
                        : formatCreditReadinessStage(summary.credit_readiness_stage, lang)
                    }
                    context={
                      isLiveDemo
                        ? text({ tr: "Canli sonuc", en: "Live result" })
                        : text({ tr: "Demo yorumu", en: "Demo interpretation" })
                    }
                    hint={
                      executiveSummary
                        ? pickLocalizedText(executiveSummary.time_to_readiness.description, lang)
                        : readinessHint
                    }
                  />
                  <MetricTile
                    label={text({ tr: "Beklenen ilerleme", en: "Expected progress" })}
                    value={
                      executiveSummary
                        ? pickLocalizedText(executiveSummary.expected_result.label, lang)
                        : `${formatPointChange(improvement, 0)} ${text({ tr: "iyilesme", en: "improvement" })}`
                    }
                    hint={
                      executiveSummary
                        ? pickLocalizedText(executiveSummary.expected_result.description, lang)
                        : `${formatPdPercent(summary.base_pd, lang)} -> ${formatPdPercent(summary.target_pd_24w, lang)} PD`
                    }
                  />
                </div>
              </div>

              <div className="grid gap-5">
                <div className="panel p-6">
                  <div className="eyebrow">{text({ tr: "Musteri baglami", en: "Customer context" })}</div>
                  <div className="font-display text-2xl font-semibold text-white">
                    {formatDemoProfile(customer.profile, lang)}
                  </div>
                  <div className="mt-5 space-y-3 text-sm text-slate-300">
                    <div>
                      {text({ tr: "Musteri tipi", en: "Customer type" })}:{" "}
                      <span className="text-white">{formatDemoSegment(customer.segment, lang)}</span>
                    </div>
                    <div>
                      {text({ tr: "Gelir profili", en: "Income profile" })}:{" "}
                      <span className="text-white">{formatIncomeBand(customer.income_band, lang)}</span>
                    </div>
                    <div>
                      {text({ tr: "Yol durumu", en: "Path status" })}:{" "}
                      <span className="text-white">{formatTrajectoryStatus(summary.trajectory_status, lang)}</span>
                    </div>
                    <div>
                      {text({ tr: "Karar gorunumu", en: "Decision outlook" })}:{" "}
                      <span className="text-white">{formatDecisionStatus(summary.decision_status, lang)}</span>
                    </div>
                    <div>
                      {text({ tr: "Kredi uygunlugu", en: "Credit eligibility" })}:{" "}
                      <span className="text-white">
                        {formatCreditReadinessStage(summary.credit_readiness_stage, lang)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="panel p-6">
                  <div className="eyebrow">{text({ tr: "Neden onemli", en: "Why it matters" })}</div>
                  <p className="text-sm leading-7 text-slate-300">
                    {executiveSummary?.recommended_path
                      ? pickLocalizedText(executiveSummary.recommended_path.description, lang)
                      : text({
                          tr: "Bu gorunum, karar sonrasi iletisim dilini netlestirir: musteriye hangi aksiyonlarin sirayla onerilecegi ve hangi kurum teklifinin ne zaman devreye girecegi acik olur.",
                          en: "This surface clarifies post-decision communication: what steps the customer should take, in what order, and when the institution-side offer should appear.",
                        })}
                  </p>
                </div>

                <details className="panel p-6 text-sm text-slate-300">
                  <summary className="cursor-pointer font-semibold text-white">
                    {text({ tr: "Teknik detaylari goster", en: "Show technical details" })}
                  </summary>
                  <div className="mt-4 grid gap-2">
                    <div>
                      {text({ tr: "Narrative confidence", en: "Narrative confidence" })}:{" "}
                      <span className="text-white">
                        {executiveSummary
                          ? pickLocalizedText(executiveSummary.narrative_confidence.label, lang)
                          : text({ tr: "n/a", en: "n/a" })}
                      </span>
                    </div>
                    <div>
                      {text({ tr: "Confidence summary", en: "Confidence summary" })}:{" "}
                      <span className="text-white">
                        {executiveSummary
                          ? pickLocalizedText(executiveSummary.narrative_confidence.description, lang)
                          : text({ tr: "n/a", en: "n/a" })}
                      </span>
                    </div>
                    <div>
                      {text({ tr: "Plan gerceklesme olasiligi", en: "Plan execution probability" })}:{" "}
                      <span className="text-white">{formatPercent(summary.plan_execution_probability, 0)}</span>
                    </div>
                    <div>
                      {text({ tr: "Kredi esigi yorumu", en: "Readiness stage" })}:{" "}
                      <span className="text-white">
                        {formatCreditReadinessStage(summary.credit_readiness_stage, lang)}
                      </span>
                    </div>
                    <div>
                      {text({ tr: "Karar gorunumu", en: "Decision outlook" })}:{" "}
                      <span className="text-white">{formatDecisionStatus(summary.decision_status, lang)}</span>
                    </div>
                    <div>
                      {text({ tr: "Birlesik gerceklesme olasiligi", en: "Combined realization probability" })}:{" "}
                      <span className="text-white">
                        {formatPercent(summary.combined_plan_realization_probability, 0)}
                      </span>
                    </div>
                    {narrative?.technical_reveal?.diagnostic_flags?.length ? (
                      <div>
                        {text({ tr: "Diagnostic flags", en: "Diagnostic flags" })}:{" "}
                        <span className="text-white">
                          {narrative.technical_reveal.diagnostic_flags.join(", ")}
                        </span>
                      </div>
                    ) : null}
                    {roadmapContent.meta?.run_id ? (
                      <div>
                        {text({ tr: "Canli run kimligi", en: "Live run id" })}:{" "}
                        <span className="text-white">{roadmapContent.meta.run_id}</span>
                      </div>
                    ) : null}
                  </div>
                </details>
              </div>
            </div>

            <div className="mt-10 grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
              <div className="grid gap-5">
                {roadmapContent.phases.map((phase) => (
                  <RoadmapPhaseCard key={phase.phase_id} phase={phase} />
                ))}
              </div>

              <div className="panel p-6">
                <div className="eyebrow">{text({ tr: "Checkpoint ozeti", en: "Checkpoint summary" })}</div>
                <div className="mt-2 font-display text-2xl font-semibold text-white">
                  {text({
                    tr: "Kisa vade sagligi, uzun vade vaadinden once gelir.",
                    en: "Short-term health comes before long-term upside.",
                  })}
                </div>
                <div className="mt-6 space-y-4">
                  {roadmapContent.checkpoints.map((checkpoint) => (
                    <div
                      key={checkpoint.week}
                      className="rounded-3xl border border-white/10 bg-white/[0.04] p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="font-semibold text-white">
                          {formatCheckpointLabel(checkpoint.checkpoint_label, lang)}
                        </div>
                        <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold text-arctic/75">
                          {text({ tr: "Hafta", en: "Week" })} {checkpoint.week}
                        </div>
                      </div>
                      <div className="mt-3 text-sm text-slate-300">
                        {checkpoint.narrative
                          ? pickLocalizedText(checkpoint.narrative.expected_state, lang)
                          : formatCheckpointNote(
                              checkpoint.week,
                              checkpoint.approval_ready,
                              checkpoint.gate_pass_estimate,
                              lang,
                            )}
                      </div>
                      {checkpoint.narrative ? (
                        <div className="mt-3 grid gap-2 text-sm text-slate-400">
                          <div>
                            <span className="text-slate-500">
                              {text({ tr: "Basari kosulu", en: "Success condition" })}:{" "}
                            </span>
                            <span className="text-slate-300">
                              {pickLocalizedText(checkpoint.narrative.success_condition, lang)}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500">
                              {text({ tr: "Aksi durumda", en: "If not" })}:{" "}
                            </span>
                            <span className="text-slate-300">
                              {pickLocalizedText(checkpoint.narrative.failure_implication, lang)}
                            </span>
                          </div>
                        </div>
                      ) : null}
                      <div className="mt-4 flex flex-wrap gap-2 text-xs text-arctic/80">
                        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                          {text({ tr: "Tahmini PD", en: "Predicted PD" })}:{" "}
                          {formatPdPercent(checkpoint.predicted_pd, lang)}
                        </span>
                        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                          {text({ tr: "Krediye uygunluk", en: "Credit eligibility" })}:{" "}
                          {formatApprovalReady(checkpoint.approval_ready, lang)}
                        </span>
                        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                          {checkpoint.gate_pass_estimate
                            ? text({ tr: "Kontrollu gecis bekleniyor", en: "Expected to pass review" })
                            : text({ tr: "Yeniden planlama riski", en: "Replan risk" })}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        ) : null}
      </section>

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Portfoy etkisi", en: "Portfolio impact" })}
            title={text({
              tr: "Bu urun tek bir musteri hikayesi degil, portfoy seviyesi hareket yaratir.",
              en: "This product creates movement across a portfolio, not just in a single case.",
            })}
            description={text({
              tr: "Bu ekran neden onemli? Cunku ekipler burada hangi stratejinin donusum, risk ve erken checkpoint sagligi uzerinde nasil etki yarattigini topluca gorur.",
              en: "Why it matters: teams can see how the strategy moves conversion, risk, and early checkpoint health across a broader population.",
            })}
          />
          <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-5">
            <MetricTile
              label={text({ tr: "Redden geri kazanima gecis", en: "Denied-to-approved lift" })}
              value={formatPercent(readNumber(batchContent.denied_to_approved_lift))}
              context={text({ tr: "Temsili offline", en: "Offline demo" })}
              hint={text({
                tr: "Reddedilen portfoy icinde yeniden onaylanabilir duruma gecen pay.",
                en: "Share of declined cases that move back into an approval-ready state.",
              })}
            />
            <MetricTile
              label={text({ tr: "Ortalama risk iyilesmesi", en: "Average risk improvement" })}
              value={formatPointChange(readNumber(batchContent.avg_pd_reduction), 1)}
              context={text({ tr: "Temsili benchmark", en: "Representative benchmark" })}
              hint={text({
                tr: "Plan sonrasinda beklenen ortalama PD hareketi.",
                en: "Expected average PD movement after recommendation.",
              })}
            />
            <MetricTile
              label={text({ tr: "4 haftalik saglik", en: "4-week health" })}
              value={formatPercent(readNumber(batchContent.trajectory_gate_pass_rate_4w))}
              context={text({ tr: "Erken kontrol", en: "Early control" })}
              hint={text({
                tr: "Ilk checkpoint'te kontrollu gecis beklenen planlarin payi.",
                en: "Share of plans expected to pass the first review checkpoint.",
              })}
            />
            <MetricTile
              label={text({ tr: "12 haftalik guclenme", en: "12-week confirmation" })}
              value={formatPercent(readNumber(batchContent.trajectory_gate_pass_rate_12w))}
              context={text({ tr: "Orta vade", en: "Mid-term" })}
              hint={text({
                tr: "Orta vadede guclenmesini surduren planlarin payi.",
                en: "Share of plans that remain healthy through the mid-term checkpoint.",
              })}
            />
            <MetricTile
              label={text({ tr: "Kismi ilerleme", en: "Partial progress" })}
              value={formatPercent(readNumber(batchContent.trajectory_partial_progress_rate))}
              context={text({ tr: "Gercekci uygulama", en: "Realistic execution" })}
              hint={text({
                tr: "Planin tamamini degil ama anlamli kismini hayata geciren musteri payi.",
                en: "Share of customers who make meaningful progress even without full completion.",
              })}
            />
          </div>

          <div className="mt-8 grid gap-5 lg:grid-cols-[1fr_1fr]">
            <div className="panel p-6">
              <div className="eyebrow">{text({ tr: "Portfoy hikayesi", en: "Portfolio story" })}</div>
              <div className="font-display text-2xl font-semibold text-white">
                {text({
                  tr: "Erken checkpoint disiplini korunurken toplu uplift saglanabiliyor.",
                  en: "Portfolio uplift can improve without sacrificing early checkpoint discipline.",
                })}
              </div>
              <p className="mt-4 text-sm leading-7 text-slate-300">
                {String(batchContent.batch_summary_story ?? "")}
              </p>
            </div>
            <div className="panel p-6">
              <div className="eyebrow">{text({ tr: "Oneri kalitesi", en: "Recommendation quality" })}</div>
              <div className="space-y-4">
                <ComparisonBar
                  label={text({ tr: "Musteri aksiyonlari", en: "Customer actions" })}
                  value={readNumber(actionMetrics.action_type_behavioral_rate)}
                  color="green"
                />
                <ComparisonBar
                  label={text({ tr: "Kismi uygulama ihtimali", en: "Partial execution likelihood" })}
                  value={readNumber(behaviorMetrics.partial_execution_rate)}
                />
                <ComparisonBar
                  label={text({ tr: "Yolunda kalan planlar", en: "Plans that stay on track" })}
                  value={readNumber(trajectoryMetrics.trajectory_on_track_rate)}
                  color="green"
                />
                <ComparisonBar
                  label={text({ tr: "Infeasible plan orani", en: "Infeasible plan rate" })}
                  value={readNumber(actionMetrics.infeasible_plan_rate)}
                  color="amber"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="shell py-20">
        <SectionHeading
          eyebrow={text({ tr: "Teklif optimizasyonu", en: "Offer optimization" })}
          title={text({
            tr: "Kurum teklifleri ayni karar yuzeyinde olculebilir hale gelir.",
            en: "Institution-side offers become measurable within the same decision surface.",
          })}
          description={text({
            tr: "Bu ekran neden onemli? Cunku ticari etkiyi musteri aksiyonlarindan koparmadan, ayni kontrol siniri icinde gormeyi saglar.",
            en: "Why it matters: teams can evaluate commercial impact without separating offers from customer actions or governance.",
          })}
        />
        <div className="mt-10 grid gap-5 xl:grid-cols-[1fr_0.9fr]">
          <div className="grid gap-5 md:grid-cols-2">
            <MetricTile
              label={text({ tr: "Teklif iceren planlar", en: "Plans with offers" })}
              value={formatPercent(readNumber(offerMetrics.offer_plan_rate))}
              context={text({ tr: "Temsili gorunum", en: "Representative snapshot" })}
              hint={text({
                tr: "Musteri aksiyonlarina kurum teklifi eklenen planlarin payi.",
                en: "Share of plans that include an institution-side offer.",
              })}
            />
            <MetricTile
              label={text({ tr: "Siralanabilir teklifler", en: "Rankable offers" })}
              value={formatPercent(readNumber(offerMetrics.rankable_offer_rate))}
              context={text({ tr: "Hazir teklif", en: "Ready to rank" })}
              hint={text({
                tr: "Sartlari net ve karar yuzeyine dogrudan girebilen teklifler.",
                en: "Offers with clear enough terms to enter the decision surface directly.",
              })}
            />
            <MetricTile
              label={text({ tr: "Teklif kabul olasiligi", en: "Offer acceptance" })}
              value={formatPercent(readNumber(offerMetrics.offer_acceptance_probability_mean))}
              context={text({ tr: "Ticari sinyal", en: "Commercial signal" })}
              hint={text({
                tr: "Musterinin kurumsal teklifi kabul etme ihtimali.",
                en: "Likelihood that the customer accepts the institution-side offer.",
              })}
            />
            <MetricTile
              label={text({ tr: "Birlesik gerceklesme", en: "Combined realization" })}
              value={formatPercent(
                readNumber(offerMetrics.combined_plan_realization_probability_mean),
              )}
              context={text({ tr: "Plan + teklif", en: "Plan + offer" })}
              hint={text({
                tr: "Musteri aksiyonu ile teklif kabulunun birlikte gerceklesme olasiligi.",
                en: "Combined likelihood of plan execution and offer acceptance.",
              })}
            />
          </div>

          <div className="panel p-6">
            <div className="eyebrow">{text({ tr: "Ticari etki", en: "Commercial impact" })}</div>
              <div className="font-display text-2xl font-semibold text-white">
                {text({
                  tr: "Ticari proxy iyilesirken karar guvencesi korunuyor.",
                  en: "Commercial proxy movement improves while governance stays intact.",
                })}
              </div>
            <div className="mt-6 space-y-4">
                <ComparisonBar
                  label={text({ tr: "Guvenli teklif orani", en: "Governance-safe offers" })}
                  value={readNumber(offerMetrics.governance_safe_offer_rate)}
                  color="green"
                />
              <div className="grid gap-4 sm:grid-cols-3">
                <MetricTile
                  label={text({ tr: "Onay proxy delta", en: "Approval proxy delta" })}
                  value={formatPointChange(readNumber(offerMetrics.approval_rate_proxy_delta), 1)}
                  context={text({ tr: "Temsili", en: "Illustrative" })}
                />
                <MetricTile
                  label={text({ tr: "Default proxy delta", en: "Default proxy delta" })}
                  value={formatPointChange(readNumber(offerMetrics.default_rate_90d_proxy_delta), 1)}
                  context={text({ tr: "Temsili", en: "Illustrative" })}
                />
                <MetricTile
                  label={text({ tr: "Margin proxy delta", en: "Margin proxy delta" })}
                  value={formatNumber(readNumber(offerMetrics.avg_margin_90d_proxy_delta), 1)}
                  context={text({ tr: "Temsili", en: "Illustrative" })}
                />
              </div>
              <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-4 text-sm text-slate-300">
                {text({ tr: "Baskin teklif tipi", en: "Dominant offer type" })}:{" "}
                <span className="font-semibold text-white">
                  {formatOfferType(String(offerMetrics.dominant_offer_type ?? ""), lang)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Ogrenme dongusu", en: "Learning loop" })}
            title={text({
              tr: "Karar kalitesi, sadece bugunu degil yarini da besler.",
              en: "Decision quality should improve tomorrow, not just today.",
            })}
            description={text({
              tr: "Bu ekran neden onemli? Cunku bir platformun kurumsal degeri, sonuclari kaydedip gelecek politika secimlerine geri besleyebilmesinden gelir.",
              en: "Why it matters: an enterprise platform earns trust when it can log outcomes and feed them back into future policy decisions.",
            })}
          />
          <div className="mt-10 grid gap-5 xl:grid-cols-[1fr_1fr]">
            <div className="panel p-6">
              <div className="eyebrow">{text({ tr: "Ogrenme hazirligi", en: "Learning readiness" })}</div>
              <div className="grid gap-4 md:grid-cols-2">
                <MetricTile
                  label={text({ tr: "Karar kayit tamligi", en: "Decision log completeness" })}
                  value={formatPercent(readNumber(learningContent.decision_log_completeness))}
                  context={text({ tr: "90 gun", en: "90 days" })}
                  hint={text({
                    tr: "Karar baglaminin daha sonra ogrenme icin ne kadar kullanilabilir oldugu.",
                    en: "How usable decision context remains for future learning.",
                  })}
                />
                <MetricTile
                  label={text({ tr: "Odul kapsami", en: "Reward coverage" })}
                  value={formatPercent(readNumber(learningContent.reward_90d_coverage))}
                  context={text({ tr: "90 gun", en: "90 days" })}
                  hint={text({
                    tr: "Gecikmeli sonuc verisinin ne kadarinin ana reward penceresinde toplandigi.",
                    en: "How much delayed outcome data is captured in the primary reward window.",
                  })}
                />
                <MetricTile
                  label={text({ tr: "Ogrenmeye hazir kayit", en: "Learning-ready records" })}
                  value={formatPercent(
                    readNumber(
                      ((readiness.learning_ready as GenericContent | undefined)?.share as number) ?? 0,
                    ),
                  )}
                  context={text({ tr: "Temsili gorunum", en: "Representative snapshot" })}
                  hint={text({
                    tr: "Karar ve sonuc birlikte geldigi icin gelecekte politika analizinde kullanilabilecek kayit payi.",
                    en: "Share of records already usable for future policy evaluation.",
                  })}
                />
                <MetricTile
                  label={text({ tr: "OPE guveni", en: "OPE confidence" })}
                  value={String(opeContent.ope_confidence ?? text({ tr: "Belirsiz", en: "Unclear" }))}
                  context={text({ tr: "Kontrollu ogrenme", en: "Controlled learning" })}
                  hint={text({
                    tr: "Politika karsilastirmasinin ne kadar guvenle yorumlanabilecegi.",
                    en: "How confidently the policy comparison can be interpreted.",
                  })}
                />
              </div>
            </div>

            <div className="panel p-6">
              <div className="eyebrow">{text({ tr: "Politika sinyali", en: "Policy signal" })}</div>
              <div className="font-display text-2xl font-semibold text-white">
                {preferredPolicy?.signal
                  ? formatPolicySignal(preferredPolicy.signal)
                  : text({ tr: "Yeterli sinyal bekleniyor", en: "Awaiting stronger signal" })}
              </div>
              <p className="mt-4 text-sm leading-7 text-slate-300">
                {preferredPolicy?.why
                  ? String(preferredPolicy.why)
                  : text({
                      tr: "Bu alanda yeterli kapsama olustugunda hangi politika profilinin daha guclu oldugu daha net okunur.",
                      en: "As coverage improves, this area shows which policy profile is pulling ahead.",
                    })}
              </p>
              <div className="mt-6 space-y-4">
                <ComparisonBar
                  label={text({ tr: "Yalnizca betimsel", en: "Descriptive only" })}
                  value={readNumber(
                    ((readiness.descriptive_only as GenericContent | undefined)?.share as number) ?? 0,
                  )}
                  color="amber"
                />
                <ComparisonBar
                  label={text({ tr: "Kismi ogrenme hazirligi", en: "Partial learning ready" })}
                  value={readNumber(
                    ((readiness.partial_learning_ready as GenericContent | undefined)?.share as number) ??
                      0,
                  )}
                />
                <ComparisonBar
                  label={text({ tr: "Tam ogrenme hazirligi", en: "Learning ready" })}
                  value={readNumber(
                    ((readiness.learning_ready as GenericContent | undefined)?.share as number) ?? 0,
                  )}
                  color="green"
                />
              </div>
              <details className="mt-6 rounded-3xl border border-white/10 bg-white/[0.04] p-4 text-sm text-slate-300">
                <summary className="cursor-pointer font-semibold text-white">
                  {text({ tr: "Ogrenme detaylari", en: "Learning details" })}
                </summary>
                <div className="mt-4 grid gap-2">
                  <div>
                    {text({ tr: "Politika profili", en: "Policy profile" })}:{" "}
                    <span className="text-white">
                      {String(preferredPolicy?.policy_arm ?? text({ tr: "yok", en: "n/a" }))}
                    </span>
                  </div>
                  <div>
                    {text({ tr: "Odeme davranisi kapsami", en: "Payment behavior coverage" })}:{" "}
                    <span className="text-white">
                      {formatPercent(readNumber(learningContent.has_payment_behavior_rate))}
                    </span>
                  </div>
                  <div>
                    {text({ tr: "Recovery sonucu kapsami", en: "Recovery outcome coverage" })}:{" "}
                    <span className="text-white">
                      {formatPercent(readNumber(learningContent.has_recovery_outcome_rate))}
                    </span>
                  </div>
                </div>
              </details>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
