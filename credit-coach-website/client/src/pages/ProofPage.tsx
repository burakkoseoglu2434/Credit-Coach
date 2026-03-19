import { MetricTile } from "@/components/MetricTile";
import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { useDemoItem } from "@/hooks/useDemoData";
import { useLanguage } from "@/i18n/language";
import type { ProductConfidenceSnapshot } from "@shared/demo-schema";

type ProofMetric = ProductConfidenceSnapshot["headline_metrics"]["product_ready_plan_coverage"];

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
      tr: `Phase 17'ye gore ${sign}${formatPoints(Math.abs(metric.delta), 1)}`,
      en: `vs Phase 17 ${sign}${formatPoints(Math.abs(metric.delta), 1)}`,
    });
  };

  const verdictLabel = {
    working: text({ tr: "Calisiyor", en: "Working" }),
    promising: text({ tr: "Umut veriyor", en: "Promising" }),
    mixed: text({ tr: "Karisik", en: "Mixed" }),
    not_proven: text({ tr: "Henuz kanitli degil", en: "Not proven yet" }),
  }[snapshot?.proof_verdict ?? "not_proven"];

  const confidenceLabel = {
    strong: text({ tr: "Guclu kanit", en: "Strong evidence" }),
    moderate: text({ tr: "Orta duzey kanit", en: "Moderate evidence" }),
    weak: text({ tr: "Sinirli kanit", en: "Limited evidence" }),
  }[snapshot?.proof_confidence ?? "weak"];

  const comparisonStory = {
    credibility_improved: text({
      tr: "Phase 17'ye gore urun guveni guclendi.",
      en: "Product credibility improved versus Phase 17.",
    }),
    more_honest_but_narrower: text({
      tr: "Kanit daha dar ama daha durust hale geldi.",
      en: "The proof became narrower, but more honest.",
    }),
    mixed_change: text({
      tr: "Ilerleme var, ancak tum trust sinyalleri ayni anda guclenmedi.",
      en: "There is progress, but not every trust signal improved together.",
    }),
    credibility_weakened: text({
      tr: "Phase 17'ye gore proof gucu zayifladi.",
      en: "Proof strength weakened versus Phase 17.",
    }),
  }[snapshot?.phase17_delta.comparison_story ?? "mixed_change"];

  const verdictSummary = {
    working: text({
      tr: "Kapsam, guvenlik ve uygulanabilir deger ayni anda guclu gorunuyor.",
      en: "Coverage, safety, and execution-aware value all look strong together.",
    }),
    promising: text({
      tr: "Motor guclu sinyal veriyor; ancak erken saglik ve trust sinyalleri halen yakindan izlenmeli.",
      en: "The engine is showing strong signal, but early-health and trust indicators still need close monitoring.",
    }),
    mixed: text({
      tr: "Bazi alanlarda ilerleme var, ancak buyer-facing proof henuz tamamen temiz degil.",
      en: "There is progress in some areas, but the buyer-facing proof is not yet fully clean.",
    }),
    not_proven: text({
      tr: "Urun hikayesi icin yeterli guven sinyali henuz birikmedi.",
      en: "There is not yet enough trust signal to support a product proof story.",
    }),
  }[snapshot?.proof_verdict ?? "not_proven"];

  const demoFitLabel = {
    representative: text({ tr: "Temsili", en: "Representative" }),
    optimistic: text({ tr: "Iyimser", en: "Optimistic" }),
    narrow: text({ tr: "Dar segment", en: "Narrow segment" }),
    misleading: text({ tr: "Yaniltici", en: "Misleading" }),
  }[snapshot?.demo_fit_annotation.demo_representativeness_verdict ?? "misleading"];

  const productReadyMetric = snapshot?.headline_metrics.product_ready_plan_coverage ?? emptyMetric(true);
  const governanceMetric = snapshot?.headline_metrics.governance_safe_plan_coverage ?? emptyMetric(true);
  const executionMetric = snapshot?.headline_metrics.execution_aware_value ?? emptyMetric(true);
  const weak4wMetric = snapshot?.supporting_metrics.weak_4w_health_rate ?? emptyMetric(false);
  const delayedMetric = snapshot?.supporting_metrics.delayed_trajectory_rate ?? {
    current: 0,
    higher_is_better: false,
  };
  const longHorizonMetric = snapshot?.supporting_metrics.long_horizon_heavy_rate ?? {
    current: 0,
    higher_is_better: false,
  };
  const realityGapMetric = snapshot?.supporting_metrics.reality_gap_flag_rate ?? emptyMetric(false);

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Kanit", en: "Proof" })}
        title={text({
          tr: "Bu sistem gercekten calisiyor mu?",
          en: "Is this system actually working?",
        })}
        supportingNote={confidenceLabel}
        description={text({
          tr: "Bu sayfa ham proof artifact'lerini birlestirmez. Engine'in urettigi tek curated proof snapshot'i render ederek coverage, safety ve execution-aware degeri ayni hiyerarside gosterir.",
          en: "This page does not stitch together raw proof artifacts. It renders one engine-owned curated proof snapshot so coverage, safety, and execution-aware value stay in the same hierarchy.",
        })}
        primaryCta={{ href: "/demo-center", label: text({ tr: "Demoyu Gor", en: "See the Demo" }) }}
        secondaryCta={{ href: "/contact", label: text({ tr: "Demo Talep Et", en: "Request a Demo" }) }}
        tertiaryCta={{ href: "/investor", label: text({ tr: "Yatirimci Ozetini Oku", en: "Review Investor Story" }) }}
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow={text({ tr: "Proof verdict", en: "Proof verdict" })}
          title={verdictLabel}
          description={verdictSummary}
        />
        <div className="mt-10 grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
          <div className="panel p-6">
            <div className="eyebrow">{text({ tr: "Yonetici ozeti", en: "Executive summary" })}</div>
            <div className="mt-3 font-display text-3xl font-semibold text-white">{verdictLabel}</div>
            <div className="mt-3 inline-flex rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-arctic/80">
              {confidenceLabel}
            </div>
            <p className="mt-5 text-sm leading-7 text-slate-300">{comparisonStory}</p>
            <p className="mt-4 text-sm leading-7 text-slate-400">
              {snapshot?.phase17_delta.summary ?? ""}
            </p>
          </div>
          <div className="grid gap-5 md:grid-cols-3">
            <MetricTile
              label={text({ tr: "Urunlesebilir plan kapsami", en: "Product-ready coverage" })}
              value={formatPercent(productReadyMetric.current)}
              change={metricDelta(productReadyMetric)}
              context={text({ tr: "Headline", en: "Headline" })}
              hint={text({
                tr: "Kullanici yuzeyine ek temizlik olmadan tasinabilecek plan payi.",
                en: "Share of plans that can move to a user-facing surface without extra cleanup.",
              })}
            />
            <MetricTile
              label={text({ tr: "Governance-safe kapsami", en: "Governance-safe coverage" })}
              value={formatPercent(governanceMetric.current)}
              change={metricDelta(governanceMetric)}
              context={text({ tr: "Guvenlik", en: "Safety" })}
              hint={text({
                tr: "Adalet, tutarlilik ve trajectory guvencesiyle uyumlu plan payi.",
                en: "Share of plans that stay aligned with fairness, reliability, and trajectory guardrails.",
              })}
            />
            <MetricTile
              label={text({ tr: "Execution-aware deger", en: "Execution-aware value" })}
              value={formatPoints(executionMetric.current)}
              change={metricDelta(executionMetric)}
              context={text({ tr: "Gercekci etki", en: "Realistic value" })}
              hint={text({
                tr: "Nominal uplift degil, gerceklesme olasiligi hesaba katildiktan sonraki beklenen deger.",
                en: "Expected value after execution likelihood is applied, not just nominal uplift.",
              })}
            />
          </div>
        </div>
      </section>

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Destekleyici trust sinyalleri", en: "Supporting trust signals" })}
            title={text({
              tr: "Erken saglik ve demo fit, headline proof'un altinda ama gorunur kalir.",
              en: "Early health and demo fit stay visible beneath the headline proof.",
            })}
            description={text({
              tr: "Bu sinyaller headline verdict'i degistirmez, ama onun ne kadar savunulabilir oldugunu gosterir.",
              en: "These signals do not replace the headline verdict, but they show how defensible it is.",
            })}
          />
          <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            <MetricTile
              label={text({ tr: "Zayif 4 hafta maruziyeti", en: "Weak 4-week exposure" })}
              value={formatPercent(weak4wMetric.current)}
              change={metricDelta(weak4wMetric)}
              context={text({ tr: "Erken saglik", en: "Early health" })}
              hint={text({
                tr: "Planin ilk 4 haftada guclu okunamadigi alanlar halen ne kadar buyuk.",
                en: "How much of the portfolio still fails to look strong in the first 4 weeks.",
              })}
            />
            <MetricTile
              label={text({ tr: "Gecikmeli trajectory maruziyeti", en: "Delayed trajectory exposure" })}
              value={formatPercent(delayedMetric.current)}
              context={text({ tr: "12w / 24w", en: "12w / 24w" })}
              hint={text({
                tr: "Iyilesmenin daha cok orta ve uzun vadeye yigilmasi gereken plan payi.",
                en: "Share of plans whose improvement is pushed into the medium or long horizon.",
              })}
            />
            <MetricTile
              label={text({ tr: "Long-horizon yuk", en: "Long-horizon load" })}
              value={formatPercent(longHorizonMetric.current)}
              context={text({ tr: "Destekleyici", en: "Supporting" })}
              hint={text({
                tr: "Kisa vadede zayif, daha cok gec fazlara dayanan yol haritasi payi.",
                en: "Share of plans that depend more heavily on later phases than near-term stability.",
              })}
            />
            <MetricTile
              label={text({ tr: "Reality-gap baskisi", en: "Reality-gap pressure" })}
              value={formatPercent(realityGapMetric.current)}
              change={metricDelta(realityGapMetric)}
              context={text({ tr: "Audit-first", en: "Audit-first" })}
              hint={text({
                tr: "Motorun teknik olarak guclu gorundugu ama insan dunyasinda sorgulanabilecek plan payi.",
                en: "Share of plans that may look technically strong but remain questionable in human-world terms.",
              })}
            />
          </div>
          <div className="mt-10 grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
            <div className="panel p-6">
              <div className="eyebrow">{text({ tr: "Demo fit", en: "Demo fit" })}</div>
              <div className="mt-3 font-display text-2xl font-semibold text-white">{demoFitLabel}</div>
              <p className="mt-4 text-sm leading-7 text-slate-300">
                {text({
                  tr: "Proof sayfasi curated hikayeyi saklamaz; demo'nun portfoy gercegini ne kadar temsil ettigini acikca soyler.",
                  en: "The proof page does not hide behind a curated story; it states how representative the demo is of portfolio truth.",
                })}
              </p>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <MetricTile
                  label={text({ tr: "Segment payi", en: "Segment share" })}
                  value={formatPercent(snapshot?.demo_fit_annotation.demo_case_segment_share ?? 0)}
                  context={snapshot?.demo_fit_annotation.demo_fit_confidence ?? ""}
                />
                <MetricTile
                  label={text({ tr: "Product-ready uyumu", en: "Product-ready alignment" })}
                  value={
                    snapshot?.demo_fit_annotation.product_ready_alignment
                      ? text({ tr: "Uyumlu", en: "Aligned" })
                      : text({ tr: "Uyumsuz", en: "Misaligned" })
                  }
                  context={text({ tr: "Trust annotation", en: "Trust annotation" })}
                />
              </div>
            </div>
            <div className="panel p-6">
              <div className="eyebrow">{text({ tr: "Phase 17 karsilastirmasi", en: "Phase 17 comparison" })}</div>
              <div className="mt-3 font-display text-2xl font-semibold text-white">{comparisonStory}</div>
              <p className="mt-4 text-sm leading-7 text-slate-300">
                {text({
                  tr: "Bu fazin amaci yalnizca yeni bir snapshot gostermek degil; hardening sonrasi urun guveninin gercekten artip artmadigini gostermekti.",
                  en: "The point of this phase is not just to show a new snapshot, but to show whether product credibility truly improved after hardening.",
                })}
              </p>
              <p className="mt-4 text-sm leading-7 text-slate-400">
                {snapshot?.phase17_delta.summary ?? ""}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="shell py-20">
        <SectionHeading
          eyebrow={text({ tr: "Ikinci katman trust", en: "Secondary trust layer" })}
          title={text({
            tr: "Ogrenme ve OPE sinyalleri proof'u destekler, headline'in yerine gecmez.",
            en: "Learning and OPE signals support the proof, but they do not replace the headline answer.",
          })}
          description={text({
            tr: "Bu katman rollout kararindan ayridir; amaci daha cok gelecekteki politika secimlerinin ne kadar guvenle okunabilecegini gostermektir.",
            en: "This layer stays separate from rollout decisions and mainly shows how confidently future policy choices can be read.",
          })}
        />
        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <MetricTile
            label={text({ tr: "Karar kayit tamligi", en: "Decision log completeness" })}
            value={formatPercent(snapshot?.supporting_trust_layer.learning.decision_log_completeness ?? 0)}
            context={text({ tr: "Learning", en: "Learning" })}
          />
          <MetricTile
            label={text({ tr: "Ogrenmeye hazir kayit", en: "Learning-ready records" })}
            value={formatPercent(snapshot?.supporting_trust_layer.learning.learning_ready_share ?? 0)}
            context={text({ tr: "90 gun", en: "90 days" })}
          />
          <MetricTile
            label={text({ tr: "Reward kapsami", en: "Reward coverage" })}
            value={formatPercent(snapshot?.supporting_trust_layer.learning.reward_90d_coverage ?? 0)}
            context={text({ tr: "90 gun", en: "90 days" })}
          />
          <MetricTile
            label={text({ tr: "OPE guveni", en: "OPE confidence" })}
            value={String(snapshot?.supporting_trust_layer.ope.ope_confidence ?? text({ tr: "Belirsiz", en: "Unknown" }))}
            context={String(snapshot?.supporting_trust_layer.ope.comparison_status ?? "")}
            hint={
              snapshot?.supporting_trust_layer.ope.preferred_policy_arm
                ? text({
                    tr: `One cikan politika: ${snapshot.supporting_trust_layer.ope.preferred_policy_arm}`,
                    en: `Preferred policy: ${snapshot.supporting_trust_layer.ope.preferred_policy_arm}`,
                  })
                : undefined
            }
          />
        </div>
      </section>
    </div>
  );
}
