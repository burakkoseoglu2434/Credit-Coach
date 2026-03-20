import { DemoSectionCta } from "@/components/DemoSectionCta";
import { MetricTile } from "@/components/MetricTile";
import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import {
  proofInvestorSharedLanguage,
  proofPageNarrative,
} from "@/data/site-content";
import { useDemoItem } from "@/hooks/useDemoData";
import { useLanguage } from "@/i18n/language";
import type { ProductConfidenceSnapshot } from "@shared/demo-schema";

type ProofMetric =
  ProductConfidenceSnapshot["headline_metrics"]["product_ready_plan_coverage"];

function emptyMetric(higherIsBetter = true): ProofMetric {
  return {
    current: 0,
    baseline: 0,
    delta: 0,
    higher_is_better: higherIsBetter,
    improved: false,
  };
}

export function ProofPage() {
  const { lang, text } = useLanguage();
  const locale = lang === "tr" ? "tr-TR" : "en-US";
  const proof = useDemoItem<ProductConfidenceSnapshot>("product-confidence-snapshot");
  const snapshot = proof.data?.content;

  const formatPercent = (value: number, digits = 0) =>
    new Intl.NumberFormat(locale, {
      style: "percent",
      maximumFractionDigits: digits,
      minimumFractionDigits: digits,
    }).format(value);

  const formatPoints = (value: number, digits = 1) =>
    `${new Intl.NumberFormat(locale, {
      maximumFractionDigits: digits,
      minimumFractionDigits: digits,
    }).format(value * 100)} ${text({ tr: "puan", en: "pts" })}`;

  const metricDelta = (metric: ProofMetric) => {
    if (typeof metric.delta !== "number") {
      return undefined;
    }

    const sign = metric.delta >= 0 ? "+" : "-";
    return text({
      tr: `${text(proofInvestorSharedLanguage.benchmark.previousBenchmark)} ${sign}${formatPoints(
        Math.abs(metric.delta),
        1,
      )}`,
      en: `${text(proofInvestorSharedLanguage.benchmark.previousBenchmark)} ${sign}${formatPoints(
        Math.abs(metric.delta),
        1,
      )}`,
    });
  };

  const verdictKey = snapshot?.proof_verdict ?? "not_proven";
  const verdictCopy = proofPageNarrative.verdicts[verdictKey];

  const confidenceLabel = {
    strong: text({ tr: "Guclu kanit", en: "Strong evidence" }),
    moderate: text({ tr: "Orta duzey kanit", en: "Moderate evidence" }),
    weak: text({ tr: "Sinirli kanit", en: "Limited evidence" }),
  }[snapshot?.proof_confidence ?? "weak"];

  const comparisonStory = {
    credibility_improved: text({
      tr: "Baz portfoy gorunumune gore guven resmi belirgin bicimde guclendi.",
      en: "Compared with the baseline portfolio snapshot, the confidence picture strengthened clearly.",
    }),
    more_honest_but_narrower: text({
      tr: "Proof daha secici hale geldi, ama daha durust bir portfoy resmi sunuyor.",
      en: "The proof became more selective, but it now presents a more honest portfolio read.",
    }),
    mixed_change: text({
      tr: "Baz portfoy gorunumune gore kapsam ve gercekci etki guclendi; erken saglik baskisi ise gorunur kaldi.",
      en: "Compared with the baseline portfolio snapshot, coverage and realistic impact improved while early-health pressure remained visible.",
    }),
    credibility_weakened: text({
      tr: "Baz portfoy gorunumune gore alici guveni zayifladi ve daha dar bir okuma ortaya cikti.",
      en: "Compared with the baseline portfolio snapshot, buyer confidence weakened and the read became narrower.",
    }),
  }[snapshot?.phase17_delta.comparison_story ?? "mixed_change"];

  const demoFitLabel = {
    representative: text({ tr: "Geneli temsil ediyor", en: "Representative" }),
    optimistic: text({ tr: "Iyimser okuma", en: "Optimistic" }),
    narrow: text({ tr: "Dar ama inandirici", en: "Narrow but credible" }),
    misleading: text({ tr: "Yaniltici gorunum", en: "Misleading" }),
  }[snapshot?.demo_fit_annotation.demo_representativeness_verdict ?? "misleading"];

  const demoFitConfidence = {
    strong: text({ tr: "Guclu guven", en: "Strong confidence" }),
    moderate: text({ tr: "Orta duzey guven", en: "Moderate confidence" }),
    weak: text({ tr: "Sinirli guven", en: "Limited confidence" }),
  }[snapshot?.demo_fit_annotation.demo_fit_confidence ?? "weak"];

  const opeConfidence = {
    strong: text({ tr: "Guclu", en: "Strong" }),
    moderate: text({ tr: "Orta", en: "Moderate" }),
    weak: text({ tr: "Sinirli", en: "Limited" }),
  }[
    snapshot?.supporting_trust_layer.ope.ope_confidence === "strong" ||
    snapshot?.supporting_trust_layer.ope.ope_confidence === "moderate" ||
    snapshot?.supporting_trust_layer.ope.ope_confidence === "weak"
      ? snapshot.supporting_trust_layer.ope.ope_confidence
      : "weak"
  ];

  const opeStatus = {
    treatment_vs_control: text({
      tr: "Mevcut akisla karsilastirma",
      en: "Compared with the current flow",
    }),
  }[snapshot?.supporting_trust_layer.ope.comparison_status ?? "treatment_vs_control"];

  const productReadyMetric =
    snapshot?.headline_metrics.product_ready_plan_coverage ?? emptyMetric(true);
  const governanceMetric =
    snapshot?.headline_metrics.governance_safe_plan_coverage ?? emptyMetric(true);
  const executionMetric =
    snapshot?.headline_metrics.execution_aware_value ?? emptyMetric(true);
  const weak4wMetric =
    snapshot?.supporting_metrics.weak_4w_health_rate ?? emptyMetric(false);
  const delayedMetric = snapshot?.supporting_metrics.delayed_trajectory_rate ?? {
    current: 0,
    higher_is_better: false,
  };
  const longHorizonMetric = snapshot?.supporting_metrics.long_horizon_heavy_rate ?? {
    current: 0,
    higher_is_better: false,
  };
  const realityGapMetric =
    snapshot?.supporting_metrics.reality_gap_flag_rate ?? emptyMetric(false);

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Kanit", en: "Proof" })}
        title={text(proofPageNarrative.question)}
        supportingNote={text(verdictCopy.statement)}
        description={text(proofPageNarrative.description)}
        primaryCta={{ href: "/contact", label: text({ tr: "Demo Talep Et", en: "Request Demo" }) }}
        secondaryCta={{ href: "/demo", label: text({ tr: "Demoyu Gor", en: "See the Demo" }) }}
        tertiaryCta={{
          href: "/investor",
          label: text({ tr: "Yatirimci Ozetini Oku", en: "Review Investor Story" }),
        }}
        badges={[
          text(proofInvestorSharedLanguage.contextLabels.curated),
          text(proofInvestorSharedLanguage.contextLabels.simulation),
          text(proofInvestorSharedLanguage.contextLabels.benchmark),
        ]}
        variant="product"
        aside={
          <div className="panel-product p-6 lg:w-[430px]">
            <div className="surface-label">{text({ tr: "Alici karari", en: "Buyer verdict" })}</div>
            <div className="mt-3 font-display text-3xl font-semibold text-white">
              {text(verdictCopy.label)}
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-300">{text(verdictCopy.support)}</p>
            <div className="mt-5 inline-flex rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-arctic/80">
              {confidenceLabel}
            </div>
            <div className="mt-6 space-y-3">
              {proofPageNarrative.trustRail.map((item) => (
                <div
                  key={item.title.en}
                  className="rounded-[20px] border border-white/10 bg-white/[0.03] px-4 py-3"
                >
                  <div className="text-sm font-semibold text-white">{item.title[lang]}</div>
                  <div className="mt-1 text-sm leading-6 text-slate-300">
                    {text(item.description)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        }
      />

      <section className="shell py-16 sm:py-20">
        <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr] xl:items-start">
          <div className="panel-product p-6">
            <SectionHeading
              eyebrow={text(proofPageNarrative.sections.proofNow.eyebrow)}
              title={text(proofPageNarrative.sections.proofNow.title)}
              description={text(proofPageNarrative.sections.proofNow.description)}
            />
            <p className="mt-6 max-w-3xl text-sm leading-7 text-slate-300">
              {comparisonStory}
            </p>
          </div>

          <div className="panel-product p-6">
            <div className="surface-label">{text(proofInvestorSharedLanguage.benchmark.baselinePortfolioSnapshot)}</div>
            <div className="mt-3 font-display text-2xl font-semibold text-white">
              {text(proofInvestorSharedLanguage.benchmark.previousBenchmark)}
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-300">
              {text({
                tr: "Bu okuma tek bir demo hikayesine degil, onceki karsilastirma ile bugunku portfoy resmini ayni anda gormeye dayanir.",
                en: "This read does not depend on one curated story; it compares today's portfolio picture against the previous benchmark.",
              })}
            </p>
          </div>
        </div>

        <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          <MetricTile
            label={text({
              tr: "Alici yuzeyine tasinabilir plan payi",
              en: "Buyer-ready plan share",
            })}
            value={formatPercent(productReadyMetric.current)}
            change={metricDelta(productReadyMetric)}
            context={text(proofInvestorSharedLanguage.contextLabels.portfolio)}
            hint={text({
              tr: "Ek aciklama gerektirmeden urun yuzeyine tasinabilecek plan payi.",
              en: "Share of plans that can move into a buyer-facing product surface without extra cleanup.",
            })}
            variant="product"
          />
          <MetricTile
            label={text({
              tr: "Kontrollu kullanim icin uygun pay",
              en: "Share fit for controlled use",
            })}
            value={formatPercent(governanceMetric.current)}
            change={metricDelta(governanceMetric)}
            context={text(proofInvestorSharedLanguage.contextLabels.portfolio)}
            hint={text({
              tr: "Kuruma hazir guvencelerle uyumlu kalan plan payi.",
              en: "Share of plans that stay aligned with institution-ready safeguards.",
            })}
            variant="product"
          />
          <MetricTile
            label={text({
              tr: "Gercekci etki sinyali",
              en: "Realistic impact signal",
            })}
            value={formatPoints(executionMetric.current)}
            change={metricDelta(executionMetric)}
            context={text(proofInvestorSharedLanguage.contextLabels.benchmark)}
            hint={text({
              tr: "Kagit ustundeki uplift degil, gerceklesme ihtimali dikkate alindiktan sonraki etki.",
              en: "Expected impact after execution likelihood is considered, not just paper uplift.",
            })}
            variant="product"
          />
        </div>
      </section>

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-16 sm:py-20">
          <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr] xl:items-start">
            <div className="panel-product p-6">
              <SectionHeading
                eyebrow={text(proofPageNarrative.sections.watchlist.eyebrow)}
                title={text(proofPageNarrative.sections.watchlist.title)}
                description={text(proofPageNarrative.sections.watchlist.description)}
              />
            </div>

            <div className="panel-product p-6">
              <div className="surface-label">{text({ tr: "Temsil sinyali", en: "Representativeness" })}</div>
              <div className="mt-3 font-display text-2xl font-semibold text-white">{demoFitLabel}</div>
              <p className="mt-4 text-sm leading-7 text-slate-300">
                {text({
                  tr: "Demo hikayesi bugunku okuyusu destekliyor, ancak halen dar bir toparlanma segmenti uzerinden okunuyor.",
                  en: "The demo story supports this read, but it still reflects a narrow recovery segment rather than the entire book.",
                })}
              </p>
            </div>
          </div>

          <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            <MetricTile
              label={text({ tr: "Zayif ilk 4 hafta maruziyeti", en: "Weak first-4-week exposure" })}
              value={formatPercent(weak4wMetric.current)}
              change={metricDelta(weak4wMetric)}
              context={text(proofInvestorSharedLanguage.contextLabels.portfolio)}
              hint={text({
                tr: "Ilk 4 haftada yeterince guclu okunmayan plan payi halen yuksek.",
                en: "The share of plans that do not look strong enough in the first 4 weeks remains elevated.",
              })}
              variant="product"
            />
            <MetricTile
              label={text({ tr: "Orta vadeye kayan ilerleme", en: "Improvement pushed to later weeks" })}
              value={formatPercent(delayedMetric.current)}
              context={text(proofInvestorSharedLanguage.contextLabels.simulation)}
              hint={text({
                tr: "Ilerlemenin daha cok 4 hafta sonrasina yigilmasi gereken plan payi.",
                en: "Share of plans whose progress is pushed beyond the first 4 weeks.",
              })}
              variant="product"
            />
            <MetricTile
              label={text({ tr: "Gercek hayat baskisi", en: "Real-world pressure" })}
              value={formatPercent(realityGapMetric.current)}
              change={metricDelta(realityGapMetric)}
              context={text(proofInvestorSharedLanguage.contextLabels.benchmark)}
              hint={text({
                tr: "Teknik olarak guclu gorunup uygulamada sorgulanabilecek plan payi.",
                en: "Share of plans that can still look stronger in the model than in day-to-day execution.",
              })}
              variant="product"
            />
          </div>

          <details className="detail-panel mt-8 px-6 py-5 text-sm text-slate-300">
            <summary className="cursor-pointer list-none font-semibold text-white">
              {text({ tr: "Teknik detaylari goster", en: "Show technical details" })}
            </summary>
            <div className="mt-5 grid gap-5 lg:grid-cols-2">
              <div className="rounded-[24px] border border-white/10 bg-slate-950/35 p-5">
                <div className="surface-label">{text(proofPageNarrative.sections.technicalDetails.eyebrow)}</div>
                <div className="mt-4 grid gap-2">
                  <div className="flex items-center justify-between gap-4">
                    <span>{text({ tr: "Demo guven seviyesi", en: "Demo confidence" })}</span>
                    <span className="text-white">{demoFitConfidence}</span>
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <span>{text({ tr: "Demo segment payi", en: "Demo segment share" })}</span>
                    <span className="text-white">
                      {formatPercent(snapshot?.demo_fit_annotation.demo_case_segment_share ?? 0)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <span>{text({ tr: "Uzun vade agirlik", en: "Long-horizon load" })}</span>
                    <span className="text-white">{formatPercent(longHorizonMetric.current)}</span>
                  </div>
                </div>
              </div>

              <div className="rounded-[24px] border border-white/10 bg-slate-950/35 p-5">
                <div className="surface-label">{text({ tr: "Ogrenme detayi", en: "Learning detail" })}</div>
                <div className="mt-4 grid gap-2">
                  <div className="flex items-center justify-between gap-4">
                    <span>{text({ tr: "Politika karsilastirma guveni", en: "OPE confidence" })}</span>
                    <span className="text-white">{opeConfidence}</span>
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <span>{text({ tr: "Karsilastirma modu", en: "Comparison mode" })}</span>
                    <span className="text-white">{opeStatus}</span>
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <span>{text({ tr: "Tercih edilen politika", en: "Preferred policy" })}</span>
                    <span className="text-right text-white">
                      {snapshot?.supporting_trust_layer.ope.preferred_policy_arm ?? "-"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </details>
        </div>
      </section>

      <section className="shell py-16 sm:py-20">
        <SectionHeading
          eyebrow={text(proofPageNarrative.sections.learning.eyebrow)}
          title={text(proofPageNarrative.sections.learning.title)}
          description={text(proofPageNarrative.sections.learning.description)}
        />

        <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          <MetricTile
            label={text({ tr: "Karar kayit tamligi", en: "Decision log completeness" })}
            value={formatPercent(snapshot?.supporting_trust_layer.learning.decision_log_completeness ?? 0)}
            context={text(proofInvestorSharedLanguage.contextLabels.curated)}
            hint={text({
              tr: "Gelecekteki politika ogrenimi icin kayit disiplini guclu kaliyor.",
              en: "Record discipline remains strong enough to support future policy learning.",
            })}
            variant="product"
          />
          <MetricTile
            label={text({ tr: "Ogrenmeye hazir portfoy payi", en: "Learning-ready portfolio share" })}
            value={formatPercent(snapshot?.supporting_trust_layer.learning.learning_ready_share ?? 0)}
            context={text(proofInvestorSharedLanguage.contextLabels.benchmark)}
            hint={text({
              tr: "Gecikmeli sonuc okumasi icin yeterli kaydi olan portfoy payi.",
              en: "Share of the portfolio with enough data to support delayed outcome learning.",
            })}
            variant="product"
          />
          <MetricTile
            label={text({ tr: "90 gunluk sonuc kapsami", en: "90-day outcome coverage" })}
            value={formatPercent(snapshot?.supporting_trust_layer.learning.reward_90d_coverage ?? 0)}
            context={text(proofInvestorSharedLanguage.contextLabels.benchmark)}
            hint={text({
              tr: "Politika kalitesini zaman icinde ogrenmeye yetecek sonuc kapsami.",
              en: "Outcome coverage that helps the system learn which policies improve over time.",
            })}
            variant="product"
          />
        </div>

        <DemoSectionCta
          title={text({
            tr: "Bu proof'u kendi portfoyunuz uzerinden gormek ister misiniz?",
            en: "Would you like to see this proof on your portfolio?",
          })}
          description={text({
            tr: "Ayni okuyusu kurumunuzun segmentleri ve hedefleri uzerinden birlikte inceleyebiliriz.",
            en: "We can review the same decision read against your own segments and portfolio goals.",
          })}
          ctaLabel={text({ tr: "Demo Talep Et", en: "Request Demo" })}
        />
      </section>
    </div>
  );
}
