import { CapabilityCard } from "@/components/CapabilityCard";
import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { processSteps } from "@/data/site-content";
import { useLanguage } from "@/i18n/language";

export function ProductPage() {
  const { text } = useLanguage();

  const productPillars = [
    {
      title: text({ tr: "Aksiyon ve teklif ayni yerde", en: "Actions and offers in one place" }),
      description: text({
        tr: "Musteri aksiyonlari ile kurum teklifleri ayni karar yuzeyinde birlikte degerlendirilir.",
        en: "Customer actions and institution-side offers are evaluated in one decision surface.",
      }),
      icon: "platform" as const,
    },
    {
      title: text({ tr: "Karar guvencesi one cikmaya devam eder", en: "Governance stays upstream" }),
      description: text({
        tr: "Adalet, tutarlilik ve izleme kontrolleri urun deneyiminin arkasinda degil onunde yer alir.",
        en: "Fairness, reliability, and telemetry stay upstream of the product experience.",
      }),
      icon: "governance" as const,
    },
    {
      title: text({ tr: "Ogrenmeye hazir", en: "Built to learn" }),
      description: text({
        tr: "Karar kayitlari ve gecikmeli sonuclar gelecekteki politika secimleri icin sinyal uretir.",
        en: "Decision logs and delayed outcomes generate signal for future policy choices.",
      }),
      icon: "learning" as const,
    },
  ];

  const buyerOutcomes = [
    {
      title: text({ tr: "Risk ekipleri", en: "Risk teams" }),
      description: text({
        tr: "Neden reddedildigini ve guvenli toparlanma yolunun nerede basladigini daha acik gorur.",
        en: "See why a case was denied and where safe recovery can begin.",
      }),
      icon: "decision" as const,
    },
    {
      title: text({ tr: "Tahsilat ekipleri", en: "Collections teams" }),
      description: text({
        tr: "Musteri adimlarini ve kurum tekliflerini ayni akista yonetebilir.",
        en: "Can manage customer actions and institution-side offers in the same workflow.",
      }),
      icon: "offer" as const,
    },
    {
      title: text({ tr: "Yonetim", en: "Leadership" }),
      description: text({
        tr: "Donusum, risk kalitesi ve ogrenme hazirligini tek urun hikayesi icinde takip eder.",
        en: "Tracks conversion, risk quality, and learning readiness in one product story.",
      }),
      icon: "portfolio" as const,
    },
  ];

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Urun", en: "Product" })}
        title={text({
          tr: "credit-coach, finans kurumlari icin karar sonrasi mudahale katmanidir.",
          en: "credit-coach is the post-decision intervention layer for financial institutions.",
        })}
        supportingNote={text({
          tr: "Tek urunde aksiyon plani, teklif stratejisi ve yayin guvencesi.",
          en: "Action planning, offer strategy, and release discipline in one platform.",
        })}
        description={text({
          tr: "Bu urun, skorlama modelinin yerine gecmez; red veya sinirda kalan musteri icin sonraki en iyi adimi urunlestirir.",
          en: "The product does not replace scoring. It productizes the next best step for denied or borderline customers.",
        })}
        primaryCta={{ href: "/contact", label: text({ tr: "Demo Talep Et", en: "Request a Demo" }) }}
        secondaryCta={{ href: "/demo", label: text({ tr: "Demoyu Gor", en: "See Demo" }) }}
        tertiaryCta={{ href: "/proof", label: text({ tr: "Kanitlari Incele", en: "Review Proof" }) }}
        badges={[
          text({ tr: "Kurumsal yazilim", en: "B2B platform" }),
          text({ tr: "Risk ve geri kazanım", en: "Risk + recovery" }),
          text({ tr: "Teklif stratejisi", en: "Offer strategy" }),
        ]}
      />

      <section className="border-t border-white/5">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Ne saglar", en: "What it delivers" })}
            title={text({
              tr: "Teknik cekirdegi urun deneyimine ceviren uc ana katman.",
              en: "Three layers that turn the technical core into a product experience.",
            })}
            description={text({
              tr: "Bu sayfa sistemi modul olarak degil, kurumun kullanacagi urun katmani olarak anlatir.",
              en: "This page describes the system as a product layer, not just a set of modules.",
            })}
          />
          <div className="mt-10 grid gap-5 lg:grid-cols-3">
            {productPillars.map((item, index) => (
              <CapabilityCard
                key={item.title}
                title={item.title}
                description={item.description}
                icon={item.icon}
                tone={index === 0 ? "blue" : index === 1 ? "default" : "green"}
              />
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-white/5 bg-white/[0.02]">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Tek platform", en: "Single platform" })}
            title={text({
              tr: "Cok modul olsa da deneyim tek karar yuzeyinde kalir.",
              en: "Even with many modules, the experience stays in one decision surface.",
            })}
            description={text({
              tr: "Moduller birbirinden bagimsiz degil; ayni karar akisini guclendiren tamamlayici katmanlar.",
              en: "The modules are not separate tools. They reinforce the same decision flow.",
            })}
          />
          <div className="mt-10 grid gap-5 lg:grid-cols-5">
            {processSteps.map((step, index) => (
              <CapabilityCard
                key={step.title.tr}
                eyebrow={`${index + 1}`}
                title={text(step.title)}
                description={text(step.body)}
                icon="process"
              />
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-white/5">
        <div className="shell py-20">
          <SectionHeading
            eyebrow={text({ tr: "Kime hitap eder", en: "Who it serves" })}
            title={text({
              tr: "Ayni urun, kurum icinde farkli rollere farkli deger sunar.",
              en: "The same product creates different value for different teams.",
            })}
            description={text({
              tr: "Bu nedenle site son kullanici uygulamasi gibi degil, kurum icinde kullanilan bir urun olarak konumlanir.",
              en: "That is why the site positions the product as an institutional workflow layer, not a consumer app.",
            })}
          />
          <div className="mt-10 grid gap-5 lg:grid-cols-3">
            {buyerOutcomes.map((item) => (
              <CapabilityCard
                key={item.title}
                title={item.title}
                description={item.description}
                icon={item.icon}
              />
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
