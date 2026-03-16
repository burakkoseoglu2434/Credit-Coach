import { CapabilityCard } from "@/components/CapabilityCard";
import { MetricTile } from "@/components/MetricTile";
import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { investorNarrative } from "@/data/site-content";
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

  const formatPercent = (value: number, digits = 0) =>
    new Intl.NumberFormat(locale, {
      style: "percent",
      maximumFractionDigits: digits,
      minimumFractionDigits: digits,
    }).format(value);

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Yatirimci", en: "Investor" })}
        title={text({
          tr: "Kredi kararindan sonra acilan yeni yazilim katmani.",
          en: "A new software layer that opens after the credit decision.",
        })}
        supportingNote={text({
          tr: "Kuantitive, red sonrasi mudahale ve teklif optimizasyonunu urunlestiriyor.",
          en: "Kuantitive is productizing post-decline intervention and offer optimization.",
        })}
        description={text({
          tr: "Bu yalnizca baska bir skor urunu degil. credit-coach, finans kurumlarinin red sonrasinda kaybettigi musteri ve gelir alanini yeniden yoneten bir karar urunu olma iddiasinda.",
          en: "This is not another scoring product. credit-coach aims to become the decision platform financial institutions use to recover value after a decline.",
        })}
        primaryCta={{ href: "/contact", label: text({ tr: "Yatirimci Gorusu Planla", en: "Schedule an Investor Conversation" }) }}
        secondaryCta={{ href: "/demo", label: text({ tr: "Urunu Gor", en: "See the Product" }) }}
        tertiaryCta={{ href: "/proof", label: text({ tr: "Kanitlari Incele", en: "Review Proof" }) }}
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow={text({ tr: "Yatirim hikayesi", en: "Investor narrative" })}
          title={text({
            tr: "Neden simdi, nereden giriyor ve neden ayrisiyor?",
            en: "Why now, where it enters, and why it differs.",
          })}
          description={text({
            tr: "Bu ilk blok, pazara cikis mantigini teknik detaylarin icinde kaybetmeden ozetler.",
            en: "This first block summarizes the go-to-market logic without hiding it inside technical detail.",
          })}
        />
        <div className="mt-10 grid gap-5 lg:grid-cols-2 xl:grid-cols-5">
          {investorNarrative.map((item) => (
            <CapabilityCard
              key={item.title.tr}
              eyebrow={text({ tr: "Yatirim tezi", en: "Investment thesis" })}
              title={text(item.title)}
              description={text(item.description)}
              icon={item.icon}
            />
          ))}
        </div>
      </section>

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Neden simdi", en: "Why now" })}
            title={text({
              tr: "Finans kurumlari sadece karar aciklamasi degil, sonraki en iyi adimi satin almak istiyor.",
              en: "Financial institutions need more than explainability; they need the next best action layer.",
            })}
            description={text({
              tr: "Red karari artik surecin sonu degil. Kurumlar, geri kazanimi artirirken karar guvencesini koruyan yeni bir yazilim katmanina ihtiyac duyuyor.",
              en: "A decline is no longer the end of the process. Institutions need a new software layer that improves recovery without breaking governance boundaries.",
            })}
          />
          <div className="mt-10 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="panel p-7">
              <div className="eyebrow">{text({ tr: "Ilk wedge", en: "Initial wedge" })}</div>
              <div className="font-display text-3xl font-semibold text-white">
                {text({
                  tr: "Reddedilmis veya sinira yakin musteri geri kazanimi.",
                  en: "Recovery for denied or near-threshold applicants.",
                })}
              </div>
              <p className="mt-4 text-sm leading-7 text-slate-300">
                {text({
                  tr: "Ilk giris noktasi, hem acik aci hissedilen hem de olculebilir bir alan: kaybedilen basvurulari, uygulanabilir aksiyonlar ve kurum teklifleriyle tekrar deger ureten bir yuzeye cevirmek.",
                  en: "The initial wedge is an area where pain is obvious and outcomes are measurable: turning lost applications into a surface that can create value again through feasible actions and institution-side offers.",
                })}
              </p>
            </div>
            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-1">
              <MetricTile
                label={text({ tr: "Temsili uplift", en: "Illustrative uplift" })}
                value={formatPercent(readNumber(batchContent.denied_to_approved_lift))}
                context={text({ tr: "Temsili offline", en: "Offline demo" })}
                hint={text({
                  tr: "Temsili portfoyde redden geri kazanima acilan alan.",
                  en: "Illustrative portfolio lift from decline into recovery-ready value.",
                })}
              />
              <MetricTile
                label={text({ tr: "Teklif kabul sinyali", en: "Offer acceptance signal" })}
                value={formatPercent(readNumber(offerMetrics.offer_acceptance_probability_mean))}
                context={text({ tr: "Temsili gorunum", en: "Representative snapshot" })}
                hint={text({
                  tr: "Kurum tekliflerinin ticari bir yan kanal degil, ana karar yuzeyinin parcasi olabilecegini gosterir.",
                  en: "Shows institution-side offers can act as part of the main decision surface rather than a side channel.",
                })}
              />
            </div>
          </div>
        </div>
      </section>

      <section className="shell py-20">
        <SectionHeading
          eyebrow={text({ tr: "Nasil para kazanir", en: "How it makes money" })}
          title={text({
            tr: "B2B yazilim olarak baslar, kurumsal is akisi icinde genisler.",
            en: "Starts as B2B software and expands inside institutional workflows.",
          })}
            description={text({
              tr: "Urun mantigi, once net bir pilot sorununu cozmeye sonra ayni urunu daha fazla karar noktasina tasimaya dayanir.",
              en: "The commercial model starts by solving a clear pilot problem and then extending the same platform into more decision points.",
            })}
        />
        <div className="mt-10 grid gap-5 lg:grid-cols-3">
          <CapabilityCard
            eyebrow={text({ tr: "Asama 1", en: "Phase 1" })}
            title={text({ tr: "Pilot ve proof of value", en: "Pilot and proof of value" })}
            description={text({
              tr: "Risk veya recovery ekibiyle sinirli kapsamda baslar; musteri geri kazanimi ve teklif stratejisi uzerinden somut ROI olcer.",
              en: "Starts with a limited scope pilot for risk or recovery teams and measures ROI through customer recovery and offer strategy.",
            })}
            icon="demo"
            tone="blue"
          />
          <CapabilityCard
            eyebrow={text({ tr: "Asama 2", en: "Phase 2" })}
            title={text({ tr: "Yillik platform gelirine gecis", en: "Expansion into platform revenue" })}
            description={text({
              tr: "Demo katmanindan kullanim urunune gecisle birlikte kurum ici karar ekiplerine daha genis lisans modeline tasinir.",
              en: "As the product moves from demo layer to operator-facing software, it expands into a wider institutional licensing model.",
            })}
            icon="platform"
            tone="green"
          />
          <CapabilityCard
            eyebrow={text({ tr: "Asama 3", en: "Phase 3" })}
            title={text({ tr: "Karar altyapisi etkisi", en: "Decision infrastructure leverage" })}
            description={text({
              tr: "Ayni karar motoru, risk, teklif, geri kazanım ve politika ogrenimi yuzeylerinde tekrar kullanilan bir altyapi katmanina donusur.",
              en: "The same decision engine becomes infrastructure reused across risk, offers, recovery, and policy learning surfaces.",
            })}
            icon="process"
            tone="amber"
          />
        </div>
      </section>

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Bugun ne var", en: "What exists today" })}
            title={text({
              tr: "Teknik cekirdek hazir; asil is urunlestirme ve dagitimda.",
              en: "The technical core is built; the remaining work is productization and distribution.",
            })}
            description={text({
              tr: "Bu ayrim onemli: ortada bir fikir degil, kurulmus bir karar cekirdegi var. Yatirim ihtiyaci bunun kullanim urunune ve ticari paketlemeye donusmesinde.",
              en: "This distinction matters: the company already has a shipped decision core. The funding need is to turn it into an operator-facing product and commercial package.",
            })}
          />
          <div className="mt-10 grid gap-5 lg:grid-cols-3">
            <div className="panel p-6">
              <div className="eyebrow">{text({ tr: "Hazir olan", en: "Already built" })}</div>
              <div className="font-display text-2xl font-semibold text-white">
                {text({ tr: "Karar motoru gercek.", en: "The decision core is real." })}
              </div>
              <p className="mt-4 text-sm leading-7 text-slate-300">
                {text({
                  tr: "Aksiyon planlama, davranis farkindalikli siralama, asamali yol haritasi, teklif optimizasyonu ve ogrenme sinyalleri bugun ayni urun hikayesi icinde calisiyor.",
                  en: "Recourse planning, behavior-aware ranking, phased trajectories, offer optimization, and learning signals already work inside one platform story today.",
                })}
              </p>
            </div>
            <div className="panel p-6">
              <div className="eyebrow">{text({ tr: "Eksik olan", en: "What is missing" })}</div>
              <div className="font-display text-2xl font-semibold text-white">
                {text({ tr: "Operator yuzeyi ve paketleme.", en: "Operator surface and packaging." })}
              </div>
              <p className="mt-4 text-sm leading-7 text-slate-300">
                {text({
                  tr: "Asil bosluk model kalitesi degil; kurumsal kullanicinin satin alabilecegi arayuz, pazara cikis paketleme ve dagitim kasidir.",
                  en: "The gap is not model quality. It is the buyer-ready interface, go-to-market packaging, and distribution muscle.",
                })}
              </p>
            </div>
            <div className="panel p-6">
              <div className="eyebrow">{text({ tr: "Ogrenme hazirligi", en: "Learning readiness" })}</div>
              <div className="font-display text-2xl font-semibold text-white">
                {formatPercent(readNumber(learningContent.decision_log_completeness))}
              </div>
              <p className="mt-4 text-sm leading-7 text-slate-300">
                {text({
                  tr: "Karar kayit disiplini ve gecikmeli sonuc kapsami, urunun gelecekte politika ogrenimi tarafina da acilabilecegini gosteriyor.",
                  en: "Decision logging discipline and delayed outcome coverage show the product can eventually open into policy learning as well.",
                })}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="shell py-20">
        <div className="panel overflow-hidden border-cobalt/20 bg-[linear-gradient(135deg,rgba(35,78,184,0.22),rgba(255,255,255,0.04))] p-8 sm:p-10">
          <div className="max-w-3xl">
            <div className="eyebrow">{text({ tr: "Son soz", en: "Bottom line" })}</div>
            <div className="font-display text-3xl font-semibold text-white sm:text-4xl">
              {text({
                tr: "Bu sirketin firsati baska bir skor satmak degil; karar sonrasindaki ticari ve operasyonel katmani sahiplenmek.",
                en: "The opportunity is not to sell another score, but to own the commercial and operational layer that comes after the decision.",
              })}
            </div>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-200/85 sm:text-base">
              {text({
                tr: "Teknik cekirdek var, urun hikayesi netlesiyor ve finans kurumlari icin anlamli bir wedge aciliyor. Simdi ihtiyac, bunu enterprise hazir bir yazilim urunune cevirmek.",
                en: "The technical core exists, the product story is sharpening, and the wedge is meaningful for financial institutions. The next step is turning it into enterprise-ready software.",
              })}
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
