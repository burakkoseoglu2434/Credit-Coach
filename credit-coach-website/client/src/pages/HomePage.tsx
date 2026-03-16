import { motion } from "framer-motion";

import { ArtifactCard } from "@/components/ArtifactCard";
import { MetricTile } from "@/components/MetricTile";
import { PageHero } from "@/components/PageHero";
import { SchemaPreviewCard } from "@/components/SchemaPreviewCard";
import { SectionHeading } from "@/components/SectionHeading";
import { modules, proofCards, surfaceCards } from "@/data/site-content";
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
          tr: "Lender Karar Istihbarati",
          en: "Decision Intelligence for Lenders",
        })}
        title={text({
          tr: "Kredi karari redde geldigi yerde bitmemeli.",
          en: "Credit decisions should not end at deny.",
        })}
        description={text({
          tr: "Kuantitive credit-coach; reddedilen basvurulari uygulanabilir aksiyon planlari, kurum teklifleri ve olculebilir toparlanma firsatlarina donusturur.",
          en: "Kuantitive's credit-coach turns denied applications into feasible action plans, institution-side offers, and measurable recovery opportunities.",
        })}
        primaryCta={{ href: "/demo", label: text({ tr: "Demo Merkezini Ac", en: "Open Demo Center" }) }}
        secondaryCta={{ href: "/investor", label: text({ tr: "Yatirimci Ozetini Oku", en: "Read Investor Story" }) }}
        badges={[
          text({ tr: "Davranis farkindalikli", en: "Behavior-aware recourse" }),
          text({ tr: "Offer optimizasyonu", en: "Offer optimization" }),
          text({ tr: "Learning-loop hazir", en: "Learning-loop ready" }),
          text({ tr: "Governance-first", en: "Governance-first" }),
        ]}
        aside={
          <div className="grid gap-4 sm:grid-cols-2 lg:w-[460px] lg:grid-cols-1">
            <div className="panel p-5">
              <div className="text-xs uppercase tracking-[0.2em] text-arctic/60">
                {text({ tr: "One cikan urun deneyimi", en: "Featured product experience" })}
              </div>
              <div className="mt-4 rounded-[24px] border border-white/10 bg-midnight/45 p-4">
                <div className="font-display text-2xl font-semibold text-white">
                  {text({ tr: "Musteri Aksiyon Yol Haritasi", en: "Customer Action Roadmap" })}
                </div>
                <p className="mt-3 text-sm leading-7 text-slate-300">
                  {text({
                    tr: "Her musteri icin kredi profilini zamanla guclendiren kisisel bir ilerleme plani.",
                    en: "A personalized roadmap that helps each customer improve over time.",
                  })}
                </p>
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-2">
              <MetricTile
                label={text({ tr: "4 hafta gate", en: "4-week gate" })}
                value={`${Math.round(((batchContent.trajectory_gate_pass_rate_4w as number) ?? 0) * 100)}%`}
              />
              <MetricTile
                label={text({ tr: "Offer kabul", en: "Offer acceptance" })}
                value={`${Math.round(((offerMetrics.offer_acceptance_probability_mean as number) ?? 0) * 100)}%`}
              />
            </div>
          </div>
        }
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow={text({ tr: "Sonuc Katmani", en: "Outcome Layer" })}
          title={text({
            tr: "Red ile kayip musteri arasina yerlesen urun katmani.",
            en: "A product layer between deny and lost customer value.",
          })}
          description={text({
            tr: "Bu sayfada once KPI'lari, sonra cikti semalarini, sonra da urun modullerini goruyorsun.",
            en: "This page starts with KPIs, then output schemas, then the module map.",
          })}
        />

        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <MetricTile
            label={text({ tr: "Denied to approved lift", en: "Denied to approved lift" })}
            value={`${Math.round(((batchContent.denied_to_approved_lift as number) ?? 0) * 100)}%`}
            hint={text({ tr: "Recourse motorunun ana donusum KPI'i.", en: "The clearest top-line recourse KPI." })}
            change={text({ tr: "portfoy", en: "portfolio" })}
          />
          <MetricTile
            label={text({ tr: "Ortalama PD dususu", en: "Average PD reduction" })}
            value={`${Math.round(((batchContent.avg_pd_reduction as number) ?? 0) * 100)} bps`}
            hint={text({ tr: "Donusum artarken risk kalitesi de iyilesiyor.", en: "Shows that risk quality improves alongside conversion." })}
            change={text({ tr: "risk", en: "risk" })}
          />
          <MetricTile
            label={text({ tr: "Ortalama offer kabul", en: "Offer acceptance mean" })}
            value={`${Math.round(((offerMetrics.offer_acceptance_probability_mean as number) ?? 0) * 100)}%`}
            hint={text({ tr: "Kurum teklifleri ayni karar yuzeyine giriyor.", en: "Institution-side offer acceptance becomes part of the same decision surface." })}
            change={text({ tr: "ticari", en: "commercial" })}
          />
          <MetricTile
            label={text({ tr: "90 gun reward coverage", en: "Reward 90d coverage" })}
            value={`${Math.round(((learningContent.reward_90d_coverage as number) ?? 0) * 100)}%`}
            hint={text({ tr: "Sistem ogrenmeye uygun veri toplamaya baslamis durumda.", en: "The system is already collecting learning-grade evidence." })}
            change={text({ tr: "ogrenme", en: "learning" })}
          />
        </div>
      </section>

      <section className="shell pb-20">
        <SectionHeading
          eyebrow={text({ tr: "Urun yuzeyleri", en: "Product surfaces" })}
          title={text({
            tr: "Teknik dosya adlari yerine kullanicinin gordugu urun degeri.",
            en: "Show product value instead of internal file names.",
          })}
          description={text({
            tr: "Bu blok, sistemin neden anlamli oldugunu bir bakista anlatir.",
            en: "This block explains why the product matters at a glance.",
          })}
        />
        <div className="mt-10 grid gap-5 lg:grid-cols-3">
          {surfaceCards.map((card) => (
            <SchemaPreviewCard
              key={card.title.tr}
              title={text(card.title)}
              description={text(card.description)}
              tone={card.tone}
            />
          ))}
        </div>
      </section>

      <section className="shell pb-20">
        <SectionHeading
          eyebrow={text({ tr: "Moduller", en: "Modules" })}
          title={text({
            tr: "Yedi modul, tek karar yuzeyi.",
            en: "Seven modules, one decision surface.",
          })}
          description={text({
            tr: "Her kart, teknik detaya bogmadan sundugu urun kabiliyetini anlatir.",
            en: "Each card describes a product capability without exposing internal implementation details.",
          })}
        />
        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {modules.slice(0, 6).map((module, index) => (
            <motion.div
              key={module.artifact}
              initial={{ opacity: 0, y: 22 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ delay: index * 0.05, duration: 0.4 }}
              className="panel p-6"
            >
              <div className="text-xs uppercase tracking-[0.18em] text-arctic/55">
                {text({ tr: "Modul", en: "Module" })} {index + 1}
              </div>
              <div className="mt-3 font-display text-2xl font-semibold text-white">
                {text(module.title)}
              </div>
              <p className="mt-4 text-sm leading-7 text-slate-400">{text(module.description)}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="shell pb-20">
        <SectionHeading
          eyebrow={text({ tr: "Kanit", en: "Proof" })}
          title={text({
            tr: "Slogan degil, urun seviyesi kanit.",
            en: "Product proof, not platform jargon.",
          })}
          description={text({
            tr: "Bu kartlar, sistemi teknik olmayan bir dilde anlatan en guclu ozet seti.",
            en: "These cards are the clearest non-technical summary of what the system delivers.",
          })}
        />
        <div className="mt-10 grid gap-5 lg:grid-cols-4">
          {proofCards.map((card) => (
            <ArtifactCard
              key={card.title.tr}
              name={text(card.title)}
              description={text(card.description)}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
