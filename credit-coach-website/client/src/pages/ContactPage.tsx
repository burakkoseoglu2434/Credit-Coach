import { InquiryForm } from "@/components/InquiryForm";
import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { SchemaPreviewCard } from "@/components/SchemaPreviewCard";
import { useLanguage } from "@/i18n/language";

export function ContactPage() {
  const { text } = useLanguage();

  return (
    <div>
      <PageHero
        eyebrow={text({ tr: "Iletisim", en: "Contact" })}
        title={text({
          tr: "Kuantitive ile credit-coach hakkinda konusun.",
          en: "Talk to Kuantitive about credit-coach.",
        })}
        description={text({
          tr: "Demo talebi, lender pilot gorusmesi veya yatirimci tanisimi icin bu sayfayi kullanin.",
          en: "Use this page to request a product walkthrough, discuss a lender pilot, or start an investor conversation.",
        })}
        aside={
          <SchemaPreviewCard
            title={text({ tr: "Hizli Baslangic", en: "Fast Start" })}
            description={text({
              tr: "Dogru ekip ile hizlica gorusme planlayip size uygun akisa gecebiliriz.",
              en: "We can quickly route you to the right conversation and next step.",
            })}
          />
        }
      />

      <section className="shell py-20">
        <div className="grid gap-8 lg:grid-cols-[0.85fr_1.15fr]">
          <div>
            <SectionHeading
              eyebrow={text({ tr: "Temasa gecin", en: "Get in touch" })}
              title={text({
                tr: "En hizli ilerleme yolu odakli bir gorusme.",
                en: "The fastest way to move this forward is a focused conversation.",
              })}
              description={text({
                tr: "Kurum kullanim senaryosu, canli demo ya da yatirimci gorusmesi; form hepsini ayri kaydeder.",
                en: "Tell us whether you are exploring a lender use case, a live demo, or an investor discussion. The backend captures all three.",
              })}
            />
            <div className="mt-8 grid gap-4">
              <div className="panel p-5">
                <div className="font-display text-xl font-semibold text-white">
                  {text({ tr: "Lender ekipleri icin", en: "For lenders" })}
                </div>
                <p className="mt-3 text-sm leading-7 text-slate-400">
                  {text({
                    tr: "Degerlendirme, geri kazanım, aksiyon planlama veya teklif optimizasyonu kullanimlarini konusmak icin en dogru giris.",
                    en: "Best when you want to discuss underwriting, recovery, recourse, or policy optimization use cases.",
                  })}
                </p>
              </div>
              <div className="panel p-5">
                <div className="font-display text-xl font-semibold text-white">
                  {text({ tr: "Yatirimcilar icin", en: "For investors" })}
                </div>
                <p className="mt-3 text-sm leading-7 text-slate-400">
                  {text({
                    tr: "Wedge'i, kanit katmanini ve urunlesme yolunu hizli gormek isteyenler icin uygun.",
                    en: "Best when you want to see the wedge, the proof surface, and the next productization path.",
                  })}
                </p>
              </div>
              <div className="rounded-[28px] border border-white/10 bg-gradient-to-br from-cobalt/10 to-ocean/5 p-5">
                <div className="text-xs uppercase tracking-[0.2em] text-arctic/65">
                  {text({ tr: "Hizli beklenti", en: "What to expect" })}
                </div>
                <div className="mt-4 grid gap-3 text-sm text-slate-300">
                  <div>{text({ tr: "1. Talep tipi kaydedilir", en: "1. Request type is captured" })}</div>
                  <div>{text({ tr: "2. Uygun akisa yonlendirilir", en: "2. Routed to the right workflow" })}</div>
                  <div>{text({ tr: "3. Demo veya gorusme planlanir", en: "3. Demo or conversation is scheduled" })}</div>
                </div>
              </div>
            </div>
          </div>

          <InquiryForm />
        </div>
      </section>
    </div>
  );
}
