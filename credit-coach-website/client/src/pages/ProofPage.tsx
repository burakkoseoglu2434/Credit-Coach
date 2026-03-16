import { ArtifactCard } from "@/components/ArtifactCard";
import { CapabilityCard } from "@/components/CapabilityCard";
import { MetricTile } from "@/components/MetricTile";
import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { proofCards, proofPillars } from "@/data/site-content";
import { useDemoItem } from "@/hooks/useDemoData";
import { useLanguage } from "@/i18n/language";

type GenericContent = Record<string, unknown>;

function readNumber(value: unknown) {
  return typeof value === "number" ? value : 0;
}

export function ProofPage() {
  const { lang, text } = useLanguage();
  const locale = lang === "tr" ? "tr-TR" : "en-US";

  const batch = useDemoItem<GenericContent>("portfolio-batch-summary");
  const offer = useDemoItem<GenericContent>("offer-optimization");
  const learning = useDemoItem<GenericContent>("outcome-ingestion");
  const ope = useDemoItem<GenericContent>("off-policy-evaluation");

  const batchContent = batch.data?.content ?? {};
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

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Kanit", en: "Proof" })}
        title={text({
          tr: "Bu platform ne olcuyor, nasil kontrol ediyor ve neden guven veriyor?",
          en: "What this platform measures, controls, and why teams can trust it.",
        })}
        supportingNote={text({
          tr: "Kurgulanmis kilometre tasi gorunumu",
          en: "Curated milestone snapshot",
        })}
        description={text({
          tr: "credit-coach'i siradan bir AI demosundan ayiran sey yalnizca onerileri degil; olcum, yayin disiplini ve ogrenme hazirligi ile birlikte gelmesi.",
          en: "What separates credit-coach from a generic AI demo is not only the recommendation layer, but the measurement, release discipline, and learning readiness behind it.",
        })}
        primaryCta={{ href: "/demo", label: text({ tr: "Demoyu Gor", en: "See the Demo" }) }}
        secondaryCta={{ href: "/contact", label: text({ tr: "Demo Talep Et", en: "Request a Demo" }) }}
        tertiaryCta={{ href: "/investor", label: text({ tr: "Yatirimci Ozetini Oku", en: "Review Investor Story" }) }}
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow={text({ tr: "Ne olcuyoruz", en: "What we measure" })}
          title={text({
            tr: "Urun degeri, teknik terimlerle degil is sonucuyla anlatilir.",
            en: "Product value is explained through business outcomes, not internal labels.",
          })}
          description={text({
            tr: "Bu ilk katman, bir finans kurumunun urunde gormek isteyecegi somut kabiliyetleri ozetler.",
            en: "This first layer summarizes the tangible capabilities that financial institutions expect to see in a production-facing product.",
          })}
        />
        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {proofCards.map((item) => (
            <ArtifactCard
              key={item.title.tr}
              name={text(item.title)}
              description={text(item.description)}
              icon={item.icon}
            />
          ))}
        </div>
        <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <MetricTile
            label={text({ tr: "Portfoy uplift", en: "Portfolio uplift" })}
            value={formatPercent(readNumber(batchContent.denied_to_approved_lift))}
            context={text({ tr: "Temsili offline", en: "Offline demo" })}
            hint={text({
              tr: "Temsili cohort uzerinde redden tekrar deger yaratmaya gecen alan.",
              en: "Illustrative cohort lift from denied cases into recovery-ready value.",
            })}
          />
          <MetricTile
            label={text({ tr: "Teklif guvenligi", en: "Offer safety" })}
            value={formatPercent(readNumber(offerMetrics.governance_safe_offer_rate))}
            context={text({ tr: "Yayina hazir", en: "Release-ready" })}
            hint={text({
              tr: "Kurumsal tekliflerin governance sinirinda kalabildigi pay.",
              en: "Share of institution-side offers that remain inside governance constraints.",
            })}
          />
          <MetricTile
            label={text({ tr: "Karar kayit tamligi", en: "Decision log completeness" })}
            value={formatPercent(readNumber(learningContent.decision_log_completeness))}
            context={text({ tr: "90 gun", en: "90 days" })}
            hint={text({
              tr: "Karar kalite kontrolunun sonradan da izlenebilmesini saglayan kapsama orani.",
              en: "Coverage that keeps decision quality auditable over time.",
            })}
          />
          <MetricTile
            label={text({ tr: "Ogrenme guveni", en: "Learning confidence" })}
            value={String(opeContent.ope_confidence ?? text({ tr: "Belirsiz", en: "Unclear" }))}
            context={text({ tr: "Politika incelemesi", en: "Policy review" })}
            hint={text({
              tr: "Politika karsilastirmalarinin ne kadar guvenli okunabilecegi.",
              en: "How confidently policy comparisons can already be interpreted.",
            })}
          />
        </div>
      </section>

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Neden guvenilir", en: "Why it is trustworthy" })}
            title={text({
              tr: "Kanit, tek bir ekran goruntusunden degil bir disiplin setinden gelir.",
              en: "Trust comes from a discipline set, not from a single screenshot.",
            })}
            description={text({
              tr: "Bu blok, olcum, inceleme ve yayina gecis mantiginin nasil birbirine baglandigini gosterir.",
              en: "This block shows how measurement, review, and rollout logic stay connected.",
            })}
          />
          <div className="mt-10 grid gap-5 lg:grid-cols-2 xl:grid-cols-4">
            {proofPillars.map((pillar) => (
              <CapabilityCard
                key={pillar.title.tr}
                eyebrow={text({ tr: "Guven katmani", en: "Trust layer" })}
                title={text(pillar.title)}
                description={text(pillar.description)}
                icon={pillar.icon}
              />
            ))}
          </div>
        </div>
      </section>

      <section className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Nasil yayina aliyoruz", en: "How we release" })}
            title={text({
              tr: "Yeni bir strateji, kontrolsuz sekilde yayina alinmaz.",
              en: "New strategies do not move to production without controls.",
            })}
            description={text({
              tr: "Bu ekran neden onemli? Cunku kurumsal urunlerde yalnizca iyi oneriler degil, guvenli yayina gecis davranisi da satin alinir.",
              en: "Why it matters: enterprise buyers are not only purchasing recommendations, but safe release behavior.",
            })}
          />
        <div className="mt-10 grid gap-5 lg:grid-cols-3">
          <CapabilityCard
            eyebrow={text({ tr: "1. Olcum", en: "1. Measurement" })}
            title={text({ tr: "Portfoy KPI ile baslar", en: "Starts with portfolio KPIs" })}
            description={text({
              tr: "Donusum, risk, teklif etkisi ve erken checkpoint sagligi ayni hikaye icinde okunur.",
              en: "Conversion, risk, offer impact, and early checkpoint health are read in the same story.",
            })}
            icon="portfolio"
            tone="blue"
          />
          <CapabilityCard
            eyebrow={text({ tr: "2. Review", en: "2. Review" })}
            title={text({ tr: "Karar yuzeyi aciklanabilir kalir", en: "Decision surfaces stay explainable" })}
            description={text({
              tr: "Adalet, tutarlilik ve izleme kontrolleri urun dilinin arkasinda saklanmaz; yayin kararinin onunde durur.",
              en: "Fairness, reliability, and telemetry controls stay visible and upstream of promotion decisions.",
            })}
            icon="governance"
            tone="green"
          />
          <CapabilityCard
            eyebrow={text({ tr: "3. Ogrenme", en: "3. Learning" })}
            title={text({ tr: "Her yayin gelecegi besler", en: "Every release feeds the future" })}
            description={text({
              tr: "Karar kaydi ve gecikmeli sonuc verisi, yalnizca raporlama degil bir sonraki politika secimi icin de sinyal uretir.",
              en: "Decision logging and delayed outcomes do more than reporting; they produce signal for future policy choices.",
            })}
            icon="learning"
            tone="amber"
          />
        </div>
      </section>

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Nasil ogreniyoruz", en: "How we learn" })}
            title={text({
              tr: "Gecikmeli sonuc geldikce sistem yeni politika kararlarini daha guvenle destekler.",
              en: "As delayed outcomes arrive, the system can support future policy choices with greater confidence.",
            })}
            description={text({
              tr: "Bu blok, bir AI ozelliginden bir karar altyapisina gecisin nerede gerceklestigini gosterir.",
              en: "This block shows where an AI feature becomes a decision infrastructure layer.",
            })}
          />
          <div className="mt-10 grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
            <div className="panel p-6">
              <div className="eyebrow">{text({ tr: "Kapsam gorunumu", en: "Coverage snapshot" })}</div>
              <div className="grid gap-4 md:grid-cols-2">
                <MetricTile
                  label={text({ tr: "Odul kapsami", en: "Reward coverage" })}
                  value={formatPercent(readNumber(learningContent.reward_90d_coverage))}
                  context={text({ tr: "90 gun", en: "90 days" })}
                />
                <MetricTile
                  label={text({ tr: "Default kapsami", en: "Default coverage" })}
                  value={formatPercent(readNumber(learningContent.default_90d_coverage))}
                  context={text({ tr: "90 gun", en: "90 days" })}
                />
                <MetricTile
                  label={text({ tr: "Margin kapsami", en: "Margin coverage" })}
                  value={formatPercent(readNumber(learningContent.margin_90d_coverage))}
                  context={text({ tr: "90 gun", en: "90 days" })}
                />
                <MetricTile
                  label={text({ tr: "Ogrenmeye hazir kayit", en: "Learning-ready records" })}
                  value={formatPercent(
                    readNumber(
                      (((learningContent.learning_readiness_status_distribution as GenericContent | undefined)
                        ?.learning_ready as GenericContent | undefined)?.share as number) ?? 0,
                    ),
                  )}
                  context={text({ tr: "Snapshot", en: "Snapshot" })}
                />
              </div>
            </div>
            <div className="panel p-6">
              <div className="eyebrow">{text({ tr: "Politika incelemesi", en: "Policy review" })}</div>
              <div className="font-display text-2xl font-semibold text-white">
                {text({
                  tr: "Ogrenme katmani rollout'u degil, gelecekteki secimleri bilgilendirir.",
                  en: "The learning layer informs future choices rather than overriding rollout controls.",
                })}
              </div>
              <p className="mt-4 text-sm leading-7 text-slate-300">
                {text({
                  tr: "Bu yuzey, yayin kararinin altina degil yanina oturur: hangi politika profilinin daha umut verici oldugunu soyler, ama karar guvencesi kontrollerinin yerine gecmez.",
                  en: "This surface sits beside release decisions rather than beneath them: it indicates which policy profile looks stronger, but never replaces governance controls.",
                })}
              </p>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <MetricTile
                  label={text({ tr: "Tercih edilen sinyal", en: "Preferred signal" })}
                  value={
                    opeContent.preferred_policy_signal
                      ? text({ tr: "Treatment destekli", en: "Treatment supported" })
                      : text({ tr: "Yetersiz kanit", en: "Insufficient evidence" })
                  }
                  context={String(opeContent.ope_confidence ?? "")}
                />
                <MetricTile
                  label={text({ tr: "Onay proxy farki", en: "Approval proxy delta" })}
                  value={formatPointChange(readNumber(offerMetrics.approval_rate_proxy_delta), 1)}
                  context={text({ tr: "Temsili", en: "Illustrative" })}
                />
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
