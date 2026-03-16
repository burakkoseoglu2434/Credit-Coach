import { CapabilityCard } from "@/components/CapabilityCard";
import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { VisualFlow } from "@/components/VisualFlow";
import { modules, processSteps } from "@/data/site-content";
import { useLanguage } from "@/i18n/language";

export function ModulesPage() {
  const { text } = useLanguage();

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Nasil calisir", en: "How it works" })}
        title={text({
          tr: "Tek platform, cok modul, tek karar yuzeyi.",
          en: "One platform, many modules, one decision surface.",
        })}
        supportingNote={text({
          tr: "Bu sayfa modulleri teknik bileşen olarak degil, ürün akışının parçaları olarak anlatır.",
          en: "This page explains the modules as parts of a product flow, not just technical components.",
        })}
        description={text({
          tr: "credit-coach once karari aciklar, sonra uygulanabilir bir yol kurar, en son da bunu ogrenme sinyaliyle besler.",
          en: "credit-coach first explains the decision, then builds an actionable path, and finally closes the loop with learning signal.",
        })}
        primaryCta={{ href: "/contact", label: text({ tr: "Demo Talep Et", en: "Request a Demo" }) }}
        secondaryCta={{ href: "/demo", label: text({ tr: "Demoyu Gor", en: "See Demo" }) }}
      />

      <section className="border-t border-white/5">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Akis", en: "Flow" })}
            title={text({
              tr: "Bu ekran neden onemli?",
              en: "Why this matters",
            })}
            description={text({
              tr: "Cunku sistemin yalnizca ne yaptigini degil, kurum is akisi icinde hangi sirayla deger urettigini gosterir.",
              en: "Because it shows not just what the system does, but the order in which it creates value in a lender workflow.",
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
            eyebrow={text({ tr: "Platform katmanlari", en: "Platform layers" })}
            title={text({
              tr: "Moduller ana hikayenin yardimci katmanlari olarak konumlanir.",
              en: "Modules sit beneath the main product story as supporting layers.",
            })}
            description={text({
              tr: "Her modul farkli bir sorunu cozer ama hepsi ayni karar yuzeyini guclendirir.",
              en: "Each module solves a distinct problem, but all of them reinforce the same decision surface.",
            })}
          />
          <div className="mt-10 grid gap-5 lg:grid-cols-2">
            {modules.map((module) => (
              <CapabilityCard
                key={module.artifact}
                eyebrow={text({ tr: "Modul", en: "Module" })}
                title={text(module.title)}
                description={text(module.description)}
                icon={module.icon}
              />
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
