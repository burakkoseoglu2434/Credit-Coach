import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { investorHighlights } from "@/data/site-content";
import { useLanguage } from "@/i18n/language";

export function InvestorPage() {
  const { text } = useLanguage();

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Yatirimci", en: "Investor" })}
        title={text({
          tr: "Ship edilmis teknik cekirdegi olan, urunlesmeye acik bir lending optimization katmani.",
          en: "A lending optimization layer with a shipped core and open product surface.",
        })}
        description={text({
          tr: "Kuantitive'in firsati bir skor daha yapmak degil; deny sonrasindaki karar katmanini urunlestirmek.",
          en: "Kuantitive's opportunity is not to build another score, but to productize the layer that comes after deny.",
        })}
        primaryCta={{ href: "/contact", label: text({ tr: "Yatirimci Materyali Iste", en: "Request Investor Materials" }) }}
        secondaryCta={{ href: "/proof", label: text({ tr: "Urun Kanitlarini Incele", en: "Review Product Proof" }) }}
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow={text({ tr: "Neden onemli", en: "Why this matters" })}
          title={text({
            tr: "Wedge hem ticari olarak anlamli hem de teknik olarak ayrisiyor.",
            en: "The wedge is commercially meaningful and technically differentiated.",
          })}
          description={text({
            tr: "Bu sirketin en iyi versiyonu model vendor degil; lender ekiplerine governance siniri icinde yeni deger acan operating layer.",
            en: "The best version of this company is an operating layer that helps lenders recover customer value under governance constraints.",
          })}
        />
        <div className="mt-10 grid gap-5 lg:grid-cols-2">
          {investorHighlights.map((highlight) => (
            <div key={highlight.tr} className="panel p-7 text-sm leading-7 text-slate-300">
              {text(highlight)}
            </div>
          ))}
        </div>
      </section>

      <section className="shell pb-20">
        <div className="grid gap-5 lg:grid-cols-3">
          <div className="panel p-6">
            <div className="eyebrow">{text({ tr: "Neler hazir", en: "What is built" })}</div>
            <div className="mt-3 font-display text-2xl font-semibold text-white">
              {text({ tr: "Motor gercek ve calisiyor.", en: "The engine is already real." })}
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-400">
              {text({
                tr: "Typed actions, execution-aware ranking, phased trajectories, offer optimization ve learning-loop evidence zaten yerinde.",
                en: "Typed actions, execution-aware ranking, phased trajectories, offer optimization, and learning-loop evidence are already in place.",
              })}
            </p>
          </div>
          <div className="panel p-6">
            <div className="eyebrow">{text({ tr: "Neler eksik", en: "What is missing" })}</div>
            <div className="mt-3 font-display text-2xl font-semibold text-white">
              {text({ tr: "Product shell ve ticari paketleme.", en: "Product shell and commercial packaging." })}
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-400">
              {text({
                tr: "Kalan bosluk recommendation core'un varligi degil; bunu guclu operator urunu ve dagitim hikayesine baglamak.",
                en: "The remaining gap is not whether the recommendation core exists. It is whether the company wraps it in a strong operator-facing product and distribution story.",
              })}
            </p>
          </div>
          <div className="panel p-6">
            <div className="eyebrow">{text({ tr: "Neden simdi", en: "Why now" })}</div>
            <div className="mt-3 font-display text-2xl font-semibold text-white">
              {text({ tr: "Lender ekipleri sadece explainability istemiyor.", en: "Lenders need more than explainability." })}
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-400">
              {text({
                tr: "Kredi ekipleri, risk, fairness ve telemetry disiplinini bozmadan upside yakalayan bir sonraki adim sistemlerine ihtiyac duyuyor.",
                en: "Credit teams increasingly need governed next-step systems that help them capture upside without breaking risk, fairness, or telemetry discipline.",
              })}
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
