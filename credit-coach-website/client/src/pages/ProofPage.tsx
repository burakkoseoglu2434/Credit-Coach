import { ArtifactCard } from "@/components/ArtifactCard";
import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { proofCards } from "@/data/site-content";
import { useLanguage } from "@/i18n/language";

export function ProofPage() {
  const { text } = useLanguage();

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Kanit", en: "Proof" })}
        title={text({
          tr: "Urunle ilgili her buyuk iddia bir artifact'e baglanabiliyor.",
          en: "Every major product claim can be tied back to an artifact.",
        })}
        description={text({
          tr: "Bu yuzey, generic AI demosu ile evidence-driven fintech urun arasindaki farki gosteriyor.",
          en: "This is where credit-coach separates itself from a generic AI demo.",
        })}
        primaryCta={{ href: "/demo", label: text({ tr: "Demo Merkezini Ac", en: "Open the Demo Center" }) }}
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow={text({ tr: "Evidence aileleri", en: "Evidence families" })}
          title={text({
            tr: "Urunun degeri teknik etiketlerle degil, kullaniciya sagladigi sonuc ile anlatilmali.",
            en: "The product should be explained through outcomes, not internal labels.",
          })}
          description={text({
            tr: "Bu kartlar, kredi ekiplerinin ve yatirimcilarin en hizli anlayacagi urun kabiliyetlerini ozetler.",
            en: "These cards summarize the product capabilities that business users and investors understand fastest.",
          })}
        />
        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {proofCards.map((item) => (
            <ArtifactCard
              key={item.title.tr}
              name={text(item.title)}
              description={text(item.description)}
            />
          ))}
        </div>
      </section>

      <section className="shell pb-20">
        <div className="grid gap-5 lg:grid-cols-3">
          <div className="panel p-6">
            <div className="eyebrow">{text({ tr: "Recommendation quality", en: "Recommendation quality" })}</div>
            <p className="mt-4 text-sm leading-7 text-slate-300">
              {text({
                tr: "Candidate diversity, action realism, behavior-aware ranking ve trajectory health birlikte bakildiginda motorun teorik olmadigi gorulur.",
                en: "Candidate diversity, action realism, behavior-aware ranking, and trajectory health show that the engine is not just theoretical.",
              })}
            </p>
          </div>
          <div className="panel p-6">
            <div className="eyebrow">{text({ tr: "Ticari katman", en: "Commercial layer" })}</div>
            <p className="mt-4 text-sm leading-7 text-slate-300">
              {text({
                tr: "Offer optimization, kurum aksiyonunu ayni governed karar yuzeyine sokar ve proxy etkisini dogrudan olcer.",
                en: "Offer optimization adds institution-side action into the same governed decision surface and measures proxy impact directly.",
              })}
            </p>
          </div>
          <div className="panel p-6">
            <div className="eyebrow">{text({ tr: "Governance ve ogrenme", en: "Governance and learning" })}</div>
            <p className="mt-4 text-sm leading-7 text-slate-300">
              {text({
                tr: "Acceptance artifact'leri, telemetry gate'leri, decision logging ve OPE sinyalleri sistemi ogrenmeye giderken durust tutar.",
                en: "Acceptance artifacts, telemetry gates, decision logging, and OPE signals keep the system honest as it moves toward learning-capable behavior.",
              })}
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
