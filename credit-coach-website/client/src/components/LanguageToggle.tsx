import { useLanguage } from "@/i18n/language";

export function LanguageToggle() {
  const { lang, setLang } = useLanguage();

  return (
    <div className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 p-1">
      <button
        type="button"
        onClick={() => setLang("tr")}
        className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
          lang === "tr" ? "bg-white text-midnight" : "text-slate-300 hover:text-white"
        }`}
      >
        TR
      </button>
      <button
        type="button"
        onClick={() => setLang("en")}
        className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
          lang === "en" ? "bg-white text-midnight" : "text-slate-300 hover:text-white"
        }`}
      >
        EN
      </button>
    </div>
  );
}
