import { CapabilityCard } from "@/components/CapabilityCard";
import { MetricTile } from "@/components/MetricTile";
import { PageHero } from "@/components/PageHero";
import { SchemaPreviewCard } from "@/components/SchemaPreviewCard";
import { SectionHeading } from "@/components/SectionHeading";
import { VisualFlow } from "@/components/VisualFlow";
import {
  buyerPaths,
  homeProblemCards,
  processSteps,
  proofPillars,
  surfaceCards,
} from "@/data/site-content";
import { useDemoItem } from "@/hooks/useDemoData";
import { useLanguage } from "@/i18n/language";

export function HomePage() {
  const { text } = useLanguage();
  const batch = useDemoItem<Record<string, number>>("portfolio-batch-summary");
  const offer = useDemoItem<Record<string, unknown>>("offer-optimization");
  const learning = useDemoItem<Record<string, unknown>>("outcome-ingestion");

  const batchContent = batch.data?.content ?? {};
  const offerMetrics = (offer.data?.content as { canonical_metrics?: Record<string, number> })?.canonical_metrics ?? {};
  const learningContent = learning.data?.content ?? {};

  return (
    <div>
      <PageHero
        eyebrow={text({
          tr: "Finans kurumlari icin karar platformu",
          en: "Decision platform for financial institutions",
        })}
        title={text({
          tr: "Kredi karari redde geldigi yerde bitmemeli.",
          en: "Credit decisions should not end at deny.",
        })}
        supportingNote={text({
          tr: "AI destekli kredi mudahale ve teklif optimizasyon platformu.",
          en: "AI-powered intervention and offer optimization platform for lenders.",
        })}
        description={text({
          tr: "credit-coach, reddedilen veya sinirdaki basvurular icin uygulanabilir bir sonraki adimi, kurum tekliflerini ve olculebilir geri kazanimi ayni urun yuzeyinde bir araya getirir.",
          en: "credit-coach brings feasible next steps, institution-side offers, and measurable recovery into one product surface for denied or borderline applications.",
        })}
        primaryCta={{ href: "/contact", label: text({ tr: "Demo Talep Et", en: "Request a Demo" }) }}
        secondaryCta={{ href: "/demo", label: text({ tr: "Demoyu Gor", en: "See Demo" }) }}
        tertiaryCta={{ href: "/investor", label: text({ tr: "Yatirimci Ozetini Oku", en: "Read Investor Story" }) }}
        badges={[
          text({ tr: "Risk ekipleri", en: "Risk teams" }),
          text({ tr: "Tahsilat ekipleri", en: "Collections" }),
          text({ tr: "Karar guvencesi", en: "Governance" }),
          text({ tr: "Tek urun", en: "Single platform" }),
        ]}
        aside={
          <div className="grid gap-4 sm:grid-cols-2 lg:w-[470px] lg:grid-cols-1">
            <SchemaPreviewCard
              title={text({ tr: "Musteri aksiyon yol haritasi", en: "Customer action roadmap" })}
              description={text({
                tr: "Her musteri icin kisisel bir sonraki adimi, checkpoint mantigi ve kurum teklifini ayni yerde toplar.",
                en: "Brings the next best action, checkpoint logic, and institution-side offers into one view.",
              })}
              icon="roadmap"
            />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-2">
              <MetricTile
                label={text({ tr: "4 haftalik gecis", en: "4-week pass rate" })}
                value={`${Math.round(((batchContent.trajectory_gate_pass_rate_4w as number) ?? 0) * 100)}%`}
                context={text({ tr: "Demo gorunumu", en: "Demo snapshot" })}
              />
              <MetricTile
                label={text({ tr: "Ortalama teklif kabul", en: "Offer acceptance" })}
                value={`${Math.round(((offerMetrics.offer_acceptance_probability_mean as number) ?? 0) * 100)}%`}
                context={text({ tr: "Ornek portfoy", en: "Sample portfolio" })}
              />
            </div>
          </div>
        }
      />

      <section className="border-t border-white/5">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Problem", en: "Problem" })}
            title={text({
              tr: "Red kararindan sonra en degerli alan bos kaliyor.",
              en: "The most valuable window starts after the denial.",
            })}
            description={text({
              tr: "Bu urun, finans kurumlarinin red kararindan sonra kaybettigi musteri ve gelir alanina odaklanir.",
              en: "The product focuses on the customer and revenue value that financial institutions lose after a denial.",
            })}
          />
          <div className="mt-10 grid gap-5 lg:grid-cols-3">
            {homeProblemCards.map((card) => (
              <CapabilityCard
                key={card.title.tr}
                title={text(card.title)}
                description={text(card.description)}
                icon={card.icon}
              />
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Cozum", en: "Solution" })}
            title={text({
              tr: "Tek platform, cok modül, tek karar yuzeyi.",
              en: "One platform, many modules, one decision surface.",
            })}
            description={text({
              tr: "credit-coach, musteri aksiyonu, kurum teklifi ve yayin guvencesini ayni urunde birlestirir.",
              en: "credit-coach combines customer action planning, institution-side offers, and release controls in one platform.",
            })}
          />
          <div className="mt-10 grid gap-5 lg:grid-cols-3">
            {surfaceCards.map((card) => (
              <SchemaPreviewCard
                key={card.title.tr}
                title={text(card.title)}
                description={text(card.description)}
                icon={card.icon}
                tone={card.tone}
              />
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-white/5">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Nasil calisir", en: "How it works" })}
            title={text({
              tr: "Aciklamadan kontrollu aksiyona giden urun akisi.",
              en: "A product flow that moves from explanation to controlled action.",
            })}
            description={text({
              tr: "Bu akista once neden anlasilir, sonra uygulanabilir yol olusturulur, en son ogrenme sinyali uretilir.",
              en: "The product first explains why, then builds an actionable path, and finally creates learning signal.",
            })}
          />
          <div className="mt-10">
            <VisualFlow
              steps={processSteps.map((step) => ({
                title: text(step.title),
                body: text(step.body),
              }))}
            />
          </div>
        </div>
      </section>

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Kanit", en: "Proof" })}
            title={text({
              tr: "Urun gucu hem KPI hem release disiplini ile desteklenir.",
              en: "Product strength is backed by both KPI movement and release discipline.",
            })}
            description={text({
              tr: "Sadece iyi gorunen bir demo degil; olcum, guven, yayin disiplini ve ogrenme katmani birlikte anlatilir.",
              en: "This is more than a polished demo. Measurement, trust, release, and learning all stay visible.",
            })}
          />
          <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            <MetricTile
              label={text({ tr: "Denied to approved lift", en: "Denied to approved lift" })}
              value={`${Math.round(((batchContent.denied_to_approved_lift as number) ?? 0) * 100)}%`}
              context={text({ tr: "Temsili offline", en: "Offline demo" })}
              hint={text({ tr: "Ornek cohort icinde donusum artisini gosterir.", en: "Shows portfolio conversion lift in the representative cohort." })}
            />
            <MetricTile
              label={text({ tr: "Ortalama PD dususu", en: "Average PD reduction" })}
              value={`${Math.round(((batchContent.avg_pd_reduction as number) ?? 0) * 100)} bps`}
              context={text({ tr: "Temsili benchmark", en: "Representative benchmark" })}
              hint={text({ tr: "Donusum artarken risk kalitesinin korunup korunmadigini gosterir.", en: "Shows whether risk quality improves alongside conversion." })}
            />
            <MetricTile
              label={text({ tr: "Teklif kabul ortalamasi", en: "Offer acceptance" })}
              value={`${Math.round(((offerMetrics.offer_acceptance_probability_mean as number) ?? 0) * 100)}%`}
              context={text({ tr: "Kurgulanmis gorunum", en: "Curated snapshot" })}
              hint={text({ tr: "Kurum tekliflerinin urun akisi icinde ne kadar ise yaradigini gosterir.", en: "Shows how institution-side offers perform in the product flow." })}
            />
            <MetricTile
              label={text({ tr: "90 gun reward coverage", en: "Reward 90d coverage" })}
              value={`${Math.round(((learningContent.reward_90d_coverage as number) ?? 0) * 100)}%`}
              context={text({ tr: "Learning readiness", en: "Learning readiness" })}
              hint={text({ tr: "Sistemin zamanla ogrenmeye hazir veri toplayip toplamadigini gosterir.", en: "Shows whether the system is collecting learning-grade feedback." })}
            />
          </div>
          <div className="mt-10 grid gap-5 lg:grid-cols-4">
            {proofPillars.map((item) => (
              <CapabilityCard
                key={item.title.tr}
                title={text(item.title)}
                description={text(item.description)}
                icon={item.icon}
                tone="default"
              />
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-white/5">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Bir sonraki adim", en: "Next step" })}
            title={text({
              tr: "Hangi aciyla bakiyorsan ona gore giris yolu hazir.",
              en: "There is a clear next step for each type of visitor.",
            })}
            description={text({
              tr: "Kurum alicisi, yatirimci veya urun meraklisi olmaniza gore farkli ama net bir sonraki adim sunuyoruz.",
              en: "Whether you are a buyer, investor, or product explorer, the next step is explicit.",
            })}
          />
          <div className="mt-10 grid gap-5 lg:grid-cols-3">
            {buyerPaths.map((path) => (
              <CapabilityCard
                key={path.title.tr}
                title={text(path.title)}
                description={text(path.description)}
                icon={path.icon}
                tone="blue"
                cta={{ href: path.href, label: text(path.cta) }}
              />
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
