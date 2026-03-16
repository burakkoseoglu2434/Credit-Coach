import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { modules } from "@/data/site-content";
import { useLanguage } from "@/i18n/language";

export function ModulesPage() {
  const { text } = useLanguage();

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Moduller", en: "Modules" })}
        title={text({
          tr: "Her modul karar yuzeyini biraz daha ticari ve kullanilabilir hale getirir.",
          en: "Each module makes the decision surface more commercially useful.",
        })}
        description={text({
          tr: "Bu sayfa daha kisa tutuldu: ne yapar, ne uretir, hangi artifact ile kanitlanir.",
          en: "This page is intentionally shorter: what it does, what it outputs, and which artifact proves it.",
        })}
        primaryCta={{ href: "/demo", label: text({ tr: "Ciktilari Gor", en: "See Module Outputs" }) }}
        secondaryCta={{ href: "/contact", label: text({ tr: "Pilot Konus", en: "Discuss a Pilot" }) }}
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow={text({ tr: "Modul haritasi", en: "Module map" })}
          title={text({
            tr: "Risk tespitinden ogrenmeye hazir policy evidence'e.",
            en: "From risk diagnosis to learning-ready policy evidence.",
          })}
          description={text({
            tr: "Her kart, kullanicinin hissettigi urun degerini tek cumlede anlatir.",
            en: "Each card explains the user-facing product value in one sentence.",
          })}
        />
        <div className="mt-10 grid gap-5 lg:grid-cols-2">
          {modules.map((module) => (
            <div key={module.artifact} className="panel p-7">
              <div className="text-xs uppercase tracking-[0.18em] text-arctic/55">
                {text({ tr: "Modul", en: "Module" })}
              </div>
              <div className="mt-3 font-display text-2xl font-semibold text-white">
                {text(module.title)}
              </div>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-400">
                {text(module.description)}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
