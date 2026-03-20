import { DemoSectionCta } from "@/components/DemoSectionCta";
import { MetricTile } from "@/components/MetricTile";
import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import {
  investorPageNarrative,
  proofInvestorSharedLanguage,
} from "@/data/site-content";
import { useDemoItem } from "@/hooks/useDemoData";
import { useLanguage } from "@/i18n/language";

type GenericContent = Record<string, unknown>;

function readNumber(value: unknown) {
  return typeof value === "number" ? value : 0;
}

export function InvestorPage() {
  const { lang, text } = useLanguage();
  const locale = lang === "tr" ? "tr-TR" : "en-US";

  const batch = useDemoItem<GenericContent>("portfolio-batch-summary");
  const offer = useDemoItem<GenericContent>("offer-optimization");
  const learning = useDemoItem<GenericContent>("outcome-ingestion");

  const batchContent = batch.data?.content ?? {};
  const offerMetrics =
    ((offer.data?.content as GenericContent)?.canonical_metrics as GenericContent) ?? {};
  const learningContent = learning.data?.content ?? {};
  const learningReadiness =
    ((learningContent.learning_readiness_status_distribution as GenericContent)
      ?.learning_ready as GenericContent) ?? {};

  const formatPercent = (value: number, digits = 0) =>
    new Intl.NumberFormat(locale, {
      style: "percent",
      maximumFractionDigits: digits,
      minimumFractionDigits: digits,
    }).format(value);

  const formatNumber = (value: number, digits = 1) =>
    new Intl.NumberFormat(locale, {
      maximumFractionDigits: digits,
      minimumFractionDigits: digits,
    }).format(value);

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Yatirimci", en: "Investor" })}
        title={text(investorPageNarrative.hero.title)}
        supportingNote={text(investorPageNarrative.hero.supportingNote)}
        description={text(investorPageNarrative.hero.description)}
        primaryCta={{
          href: "/contact",
          label: text({ tr: "Yatirimci Gorusu Planla", en: "Schedule Investor Conversation" }),
        }}
        secondaryCta={{ href: "/demo", label: text({ tr: "Urunu Gor", en: "See the Product" }) }}
        tertiaryCta={{ href: "/proof", label: text({ tr: "Kanitlari Incele", en: "Review Proof" }) }}
        badges={[
          text(proofInvestorSharedLanguage.contextLabels.curated),
          text(proofInvestorSharedLanguage.contextLabels.simulation),
          text(proofInvestorSharedLanguage.contextLabels.benchmark),
        ]}
        variant="product"
        aside={
          <div className="panel-product p-6 lg:w-[430px]">
            <div className="surface-label">{text({ tr: "Okuma akisi", en: "Story order" })}</div>
            <div className="mt-3 font-display text-2xl font-semibold text-white">
              {text({
                tr: "Pazar problemi, giris noktasi, calistigina dair kanit ve ticari genisleme ayni akista okunur.",
                en: "Market pain, wedge, proof it works, and commercial expansion read in one flow.",
              })}
            </div>
            <div className="mt-6 space-y-3 text-sm leading-7 text-slate-300">
              <div>
                <span className="text-white">{text({ tr: "1.", en: "1." })}</span>{" "}
                {text({ tr: "Nerede deger kayboluyor?", en: "Where does value disappear?" })}
              </div>
              <div>
                <span className="text-white">{text({ tr: "2.", en: "2." })}</span>{" "}
                {text({ tr: "Bu urun neyi farkli cozer?", en: "What does this product solve differently?" })}
              </div>
              <div>
                <span className="text-white">{text({ tr: "3.", en: "3." })}</span>{" "}
                {text({ tr: "Bu neden tekrarlanabilir?", en: "Why is this repeatable?" })}
              </div>
              <div>
                <span className="text-white">{text({ tr: "4.", en: "4." })}</span>{" "}
                {text({ tr: "Bu nasil buyuyebilir?", en: "How can this grow?" })}
              </div>
            </div>
          </div>
        }
      />

      <section className="shell py-16 sm:py-20">
        <SectionHeading
          eyebrow={text(investorPageNarrative.sections.marketPain.eyebrow)}
          title={text(investorPageNarrative.sections.marketPain.title)}
          description={text(investorPageNarrative.sections.marketPain.description)}
        />

        <div className="mt-8 grid gap-5 lg:grid-cols-2">
          {investorPageNarrative.sections.marketPain.cards.map((item) => (
            <div key={item.title.en} className="panel-product p-6">
              <div className="font-display text-2xl font-semibold text-white">{item.title[lang]}</div>
              <p className="mt-4 text-sm leading-7 text-slate-300">{item.description[lang]}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-16 sm:py-20">
          <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr] xl:items-start">
            <div className="panel-product p-6">
              <SectionHeading
                eyebrow={text(investorPageNarrative.sections.wedge.eyebrow)}
                title={text(investorPageNarrative.sections.wedge.title)}
                description={text(investorPageNarrative.sections.wedge.description)}
              />
              <div className="mt-6 inline-flex rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-arctic/80">
                {text(proofInvestorSharedLanguage.positioning.decisionIntelligenceInfrastructure)}
              </div>
              <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300">
                {text({
                  tr: "Bu ifade baslik iddiasi degil, ikinci katman konumlama: once reddedilen musteri toparlanmasinda ise yarayan sistem, sonra kurum ici daha genis karar akislarina yayilan yeni bir katman.",
                  en: "This is a second-layer positioning claim, not the headline: a system that first works in declined-customer recovery, then spreads into broader decision workflows inside the institution.",
                })}
              </p>
            </div>

            <div className="grid gap-5 md:grid-cols-3 xl:grid-cols-1">
              {investorPageNarrative.sections.wedge.cards.map((item) => (
                <div key={item.title.en} className="panel-product p-6">
                  <div className="surface-label">{item.title[lang]}</div>
                  <p className="mt-4 text-sm leading-7 text-slate-300">{item.description[lang]}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="shell py-16 sm:py-20">
        <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr] xl:items-start">
          <div className="panel-product p-6">
            <SectionHeading
              eyebrow={text(investorPageNarrative.sections.proof.eyebrow)}
              title={text(investorPageNarrative.sections.proof.title)}
              description={text(investorPageNarrative.sections.proof.description)}
            />
            <p className="mt-6 text-sm leading-7 text-slate-300">
              {text(investorPageNarrative.sections.proof.narrative)}
            </p>
          </div>

          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            <MetricTile
              label={text({ tr: "Toparlanma acilan alan", en: "Recovery opening" })}
              value={formatPercent(readNumber(batchContent.denied_to_approved_lift))}
              context={text(proofInvestorSharedLanguage.contextLabels.simulation)}
              hint={text({
                tr: "Temsili portfoyde redden yonetilebilir toparlanmaya acilan alan.",
                en: "Illustrative room to move denied cases into managed recovery.",
              })}
              variant="product"
            />
            <MetricTile
              label={text({ tr: "Teklif yanit sinyali", en: "Offer response signal" })}
              value={formatPercent(readNumber(offerMetrics.offer_acceptance_probability_mean))}
              context={text(proofInvestorSharedLanguage.contextLabels.curated)}
              hint={text({
                tr: "Tekliflerin yan kanal degil, urunun merkezindeki karar yuzeyinin parcasi olabilecegini gosterir.",
                en: "Shows offers can live inside the main product surface, not as a side channel.",
              })}
              variant="product"
            />
            <MetricTile
              label={text({ tr: "Ogrenmeye hazir kayit", en: "Learning-ready records" })}
              value={formatPercent(readNumber(learningReadiness.share))}
              context={text(proofInvestorSharedLanguage.contextLabels.benchmark)}
              hint={text({
                tr: "Urunun yalnizca bugunu degil, gelecekteki politika kalitesini de ogrenebilecegini gosterir.",
                en: "Shows the product can learn not only about today, but about future policy quality as well.",
              })}
              variant="product"
            />
          </div>
        </div>

        <details className="detail-panel mt-8 px-6 py-5 text-sm text-slate-300">
          <summary className="cursor-pointer list-none font-semibold text-white">
            {text({ tr: "Teknik detaylari goster", en: "Show technical details" })}
          </summary>
          <div className="mt-5 grid gap-5 lg:grid-cols-3">
            <div className="rounded-[24px] border border-white/10 bg-slate-950/35 p-5">
              <div className="surface-label">{text({ tr: "Portfoy girdisi", en: "Portfolio input" })}</div>
              <div className="mt-4 grid gap-2">
                <div className="flex items-center justify-between gap-4">
                  <span>{text({ tr: "4 haftalik gecis", en: "4-week gate pass" })}</span>
                  <span className="text-white">
                    {formatPercent(readNumber(batchContent.trajectory_gate_pass_rate_4w))}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span>{text({ tr: "24 haftalik gecis", en: "24-week gate pass" })}</span>
                  <span className="text-white">
                    {formatPercent(readNumber(batchContent.trajectory_gate_pass_rate_24w))}
                  </span>
                </div>
              </div>
            </div>

            <div className="rounded-[24px] border border-white/10 bg-slate-950/35 p-5">
              <div className="surface-label">{text({ tr: "Teklif girdisi", en: "Offer input" })}</div>
              <div className="mt-4 grid gap-2">
                <div className="flex items-center justify-between gap-4">
                  <span>{text({ tr: "Guvenceli teklif payi", en: "Safeguarded offer share" })}</span>
                  <span className="text-white">
                    {formatPercent(readNumber(offerMetrics.governance_safe_offer_rate))}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span>{text({ tr: "Beklenen etki", en: "Expected impact" })}</span>
                  <span className="text-white">
                    {formatNumber(readNumber(offerMetrics.expected_recovery_proxy), 1)}
                  </span>
                </div>
              </div>
            </div>

            <div className="rounded-[24px] border border-white/10 bg-slate-950/35 p-5">
              <div className="surface-label">{text({ tr: "Ogrenme girdisi", en: "Learning input" })}</div>
              <div className="mt-4 grid gap-2">
                <div className="flex items-center justify-between gap-4">
                  <span>{text({ tr: "Karar kayit tamligi", en: "Decision log completeness" })}</span>
                  <span className="text-white">
                    {formatPercent(readNumber(learningContent.decision_log_completeness))}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span>{text({ tr: "90 gunluk sonuc kapsami", en: "90-day outcome coverage" })}</span>
                  <span className="text-white">
                    {formatPercent(readNumber(learningContent.reward_90d_coverage))}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </details>
      </section>

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-16 sm:py-20">
          <SectionHeading
            eyebrow={text(investorPageNarrative.sections.monetization.eyebrow)}
            title={text(investorPageNarrative.sections.monetization.title)}
            description={text(investorPageNarrative.sections.monetization.description)}
          />

          <div className="mt-8 grid gap-5 lg:grid-cols-3">
            {investorPageNarrative.sections.monetization.stages.map((stage) => (
              <div key={stage.title.en} className="panel-product p-6">
                <div className="surface-label">{stage.title[lang]}</div>
                <p className="mt-4 text-sm leading-7 text-slate-300">{stage.description[lang]}</p>
              </div>
            ))}
          </div>

          <div className="panel-product mt-8 p-6">
            <div className="surface-label">{text(proofInvestorSharedLanguage.positioning.pilotToPlatform)}</div>
            <div className="mt-3 font-display text-2xl font-semibold text-white">
              {text(proofInvestorSharedLanguage.positioning.decisionIntelligenceInfrastructure)}
            </div>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300">
              {text({
                tr: "Varsayilan ticari hareket, bir pilotu dogrudan genis fiyatlandirma anlatisina cevirmek degil; ayni kurum icinde daha fazla karar ekibine acilan ortak bir urun yuzeyi kurmaktir.",
                en: "The default commercial motion is not to jump from a pilot into a pricing story. It is to establish a shared product surface that opens to more decision teams inside the same institution.",
              })}
            </p>
          </div>
        </div>
      </section>

      <section className="shell py-16 sm:py-20">
        <div className="panel-product p-8 sm:p-10">
          <div className="surface-label">{text({ tr: "Sonuc", en: "Bottom line" })}</div>
          <div className="mt-3 max-w-4xl font-display text-3xl font-semibold text-white sm:text-4xl">
            {text(investorPageNarrative.bottomLine.title)}
          </div>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
            {text(investorPageNarrative.bottomLine.description)}
          </p>
        </div>

        <DemoSectionCta
          title={text({
            tr: "Bu sistemi kendi kurum yapiniz icinde tartismak ister misiniz?",
            en: "Would you like to discuss this system in the context of your institution?",
          })}
          description={text({
            tr: "Giris noktasi, kanit ve pilottan platforma genisleme yolunu kurum gerceginiz uzerinden acabiliriz.",
            en: "We can walk through the wedge, proof, and pilot-to-platform path against your institution's reality.",
          })}
          ctaLabel={text({ tr: "Gorusme Planla", en: "Schedule Conversation" })}
        />
      </section>
    </div>
  );
}
