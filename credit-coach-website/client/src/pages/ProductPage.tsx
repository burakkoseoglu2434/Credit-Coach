import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { VisualFlow } from "@/components/VisualFlow";
import { processSteps } from "@/data/site-content";
import { useLanguage } from "@/i18n/language";

export function ProductPage() {
  const { text } = useLanguage();

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Urun", en: "Product" })}
        title={text({
          tr: "credit-coach, red kararindan sonra baslayan lender urun katmanidir.",
          en: "credit-coach is a lender-facing layer that starts after deny.",
        })}
        description={text({
          tr: "Scoring modelinin ustune oturur; yonlendirilmis aksiyon, kurum teklifi ve ogrenme sinyali uretir.",
          en: "It sits on top of the risk model and generates guided actions, institution-side offers, and learning signals.",
        })}
        primaryCta={{ href: "/demo", label: text({ tr: "Demo Merkezi", en: "Open Demo Center" }) }}
        secondaryCta={{ href: "/modules", label: text({ tr: "Modulleri Gor", en: "See Modules" }) }}
        badges={[
          text({ tr: "Recourse", en: "Recourse" }),
          text({ tr: "Offer mantigi", en: "Offer logic" }),
          text({ tr: "Governance", en: "Governance" }),
          text({ tr: "Learning loop", en: "Learning loop" }),
        ]}
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow={text({ tr: "Nasil calisir", en: "How it works" })}
          title={text({
            tr: "Aciklamadan kontrollu aksiyona gecen urun akisi.",
            en: "A product flow that moves from explanation to controlled action.",
          })}
          description={text({
            tr: "Asagidaki akis, urunun en kisa teknik olmayan ozetidir.",
            en: "This is the shortest non-technical explanation of the product.",
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
      </section>

      <section className="shell pb-20">
        <div className="grid gap-5 lg:grid-cols-2">
          <div className="panel p-8">
            <div className="eyebrow">{text({ tr: "Lender ne alir", en: "What lenders get" })}</div>
            <ul className="grid gap-4 text-slate-300">
              <li>{text({ tr: "Musteri aksiyonu ve kurum teklifini tek yuzeyde gorur", en: "A single surface for customer actions and institution-side offers" })}</li>
              <li>{text({ tr: "Saf teorik optimizasyon yerine gercekcilik sinyali alir", en: "Recommendation realism instead of pure theoretical optimization" })}</li>
              <li>{text({ tr: "Checkpoint ve replan gorunurlugu kazanir", en: "Trajectory checkpoints and replan visibility" })}</li>
              <li>{text({ tr: "Policy denemeleri icin ticari proxy evidence alir", en: "Commercial proxy evidence for policy experiments" })}</li>
            </ul>
          </div>
          <div className="panel p-8">
            <div className="eyebrow">{text({ tr: "Governance ne alir", en: "What governance gets" })}</div>
            <ul className="grid gap-4 text-slate-300">
              <li>{text({ tr: "Fairness, reliability ve telemetry release'in onunde kalir", en: "Fairness, reliability, and telemetry stay upstream of release decisions" })}</li>
              <li>{text({ tr: "Makine-okunur canonical acceptance artifact'leri alir", en: "Canonical machine-readable acceptance artifacts" })}</li>
              <li>{text({ tr: "Outcome feedback ve OPE acik supporting evidence olur", en: "Outcome feedback and OPE become supporting evidence, not hidden logic" })}</li>
              <li>{text({ tr: "Oneriden review pack'e kadar izlenebilirlik korunur", en: "Explicit traceability from recommendation to review pack" })}</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
