import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";

export type Language = "tr" | "en";

type LocalizedText = Record<Language, string>;

type LanguageContextValue = {
  lang: Language;
  setLang: (lang: Language) => void;
  text: (value: LocalizedText) => string;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: PropsWithChildren) {
  const [lang, setLang] = useState<Language>("tr");

  useEffect(() => {
    const stored = window.localStorage.getItem("credit-coach-lang");
    if (stored === "tr" || stored === "en") {
      setLang(stored);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("credit-coach-lang", lang);
    document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo<LanguageContextValue>(
    () => ({
      lang,
      setLang,
      text: (value) => value[lang],
    }),
    [lang],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used inside LanguageProvider");
  }

  return context;
}

export type { LocalizedText };
