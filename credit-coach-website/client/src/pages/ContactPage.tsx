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
          tr: "Demo talebi, kontrollu pilot gorusmesi veya yatirimci tanisimi icin bu sayfayi kullanin.",
          en: "Use this page to request a product walkthrough, discuss a controlled pilot, or start an investor conversation.",
        })}
        aside={
          <SchemaPreviewCard
            title={text({ tr: "Hizli Baslangic", en: "Fast Start" })}
            description={text({
              tr: "Dogru demo track'i ve sonraki adimi secmek icin kurumsal baglaminizi hizlica toplariz.",
              en: "We collect enough institution context to route you to the right demo track and next step quickly.",
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
                tr: "Kurum kullanim senaryosu, demo track'i, pilot zamani ve veri hazirligi; form bunlari ayri kaydeder.",
                en: "Share the institution use case, demo track, pilot timeline, and data readiness. The form records them separately for follow-up.",
              })}
            />
            <div className="mt-8 grid gap-4">
              <div className="panel p-5">
                <div className="font-display text-xl font-semibold text-white">
                  {text({ tr: "Lender ekipleri icin", en: "For lenders" })}
                </div>
                <p className="mt-3 text-sm leading-7 text-slate-400">
                  {text({
                    tr: "Degerlendirme, geri kazanım, aksiyon planlama veya teklif optimizasyonu kullanimlarini kendi portfoyunuz baglaminda konusmak icin en dogru giris.",
                    en: "Best when you want to discuss underwriting, recovery, recourse, or policy optimization in the context of your own portfolio.",
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
                  {text({ tr: "Sonraki adim", en: "Next step" })}
                </div>
                <div className="mt-4 grid gap-3 text-sm text-slate-300">
                  <div>{text({ tr: "1. Kurum ve portfoy baglami kaydedilir", en: "1. Institution and portfolio context are captured" })}</div>
                  <div>{text({ tr: "2. Uygun demo track'i secilir", en: "2. The right demo track is selected" })}</div>
                  <div>{text({ tr: "3. Pilot veya gorusme akisi netlestirilir", en: "3. The pilot or follow-up path is clarified" })}</div>
                </div>
              </div>
              <div className="panel p-5">
                <div className="font-display text-xl font-semibold text-white">
                  {text({ tr: "Pilot baseline notu", en: "Pilot baseline note" })}
                </div>
                <p className="mt-3 text-sm leading-7 text-slate-400">
                  {text({
                    tr: "Ciddi pilot handoff icin database-backed persistence ve net operator sahipligi gerekir. Bu sayfa o giris bilgisini toplar; tam ops baseline bir sonraki katmandadir.",
                    en: "A serious pilot handoff needs database-backed persistence and clear operator ownership. This page captures the entry context; the full ops baseline lives in the next layer.",
                  })}
                </p>
              </div>
            </div>
          </div>

          <InquiryForm />
        </div>
      </section>
    </div>
  );
}
