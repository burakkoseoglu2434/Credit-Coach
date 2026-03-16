import { Link } from "wouter";
import { useLanguage } from "@/i18n/language";
import { BrandLogo } from "./BrandLogo";

export function Footer() {
  const { text } = useLanguage();

  return (
    <footer className="border-t border-white/10 bg-midnight/70">
      <div className="shell flex flex-col gap-8 py-12 lg:flex-row lg:justify-between">
        <div className="max-w-xl">
          <div className="flex items-center gap-4">
            <div className="w-[78px] shrink-0 rounded-2xl border border-white/10 bg-white px-3 py-2 shadow-glow">
              <BrandLogo />
            </div>
            <div>
              <div className="font-display text-2xl font-semibold text-white">Kuantitive</div>
              <div className="text-sm text-arctic/70">credit-coach</div>
            </div>
          </div>
          <p className="mt-3 max-w-lg text-sm leading-7 text-slate-400">
            {text({
              tr: "credit-coach, finans kurumlari icin uygulanabilir aksiyon planlarini, kurum tekliflerini, karar guvencesini ve ogrenme hazirligini ayni urun yuzeyinde birlestiren karar katmanidir.",
              en: "credit-coach is a decision-intelligence layer for lenders: feasible recourse plans, institution-side offers, governance evidence, and learning-loop readiness in one surface.",
            })}
          </p>
        </div>

        <div className="grid gap-3 text-sm text-slate-400">
          <Link href="/product" className="hover:text-white">
            {text({ tr: "Urun", en: "Product" })}
          </Link>
          <Link href="/modules" className="hover:text-white">
            {text({ tr: "Nasil Calisir", en: "How It Works" })}
          </Link>
          <Link href="/demo" className="hover:text-white">
            {text({ tr: "Demo Merkezi", en: "Demo Center" })}
          </Link>
          <Link href="/investor" className="hover:text-white">
            {text({ tr: "Yatirimci", en: "Investor" })}
          </Link>
        </div>
      </div>
    </footer>
  );
}
