import { useMemo, useState, type ReactNode } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm, type UseFormReturn } from "react-hook-form";

import { useLanguage } from "@/i18n/language";
import { postJson } from "@/lib/api";
import {
  contactRequestSchema,
  demoRequestSchema,
  investorRequestSchema,
  type ContactRequest,
  type DemoRequest,
  type InvestorRequest,
} from "@shared/content-schema";

type InquiryKind = "contact" | "demo" | "investor";

export function InquiryForm() {
  const [kind, setKind] = useState<InquiryKind>("demo");
  const { lang, text } = useLanguage();

  const tabs: { id: InquiryKind; label: string }[] = [
    { id: "contact", label: text({ tr: "Genel Iletisim", en: "General Contact" }) },
    { id: "demo", label: text({ tr: "Demo Talebi", en: "Request a Demo" }) },
    { id: "investor", label: text({ tr: "Yatirimci Girisi", en: "Investor Intro" }) },
  ];

  const endpoint = useMemo(() => {
    if (kind === "contact") return "/api/contact";
    if (kind === "investor") return "/api/investor-request";
    return "/api/demo-request";
  }, [kind]);

  const mutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      postJson<{ ok: boolean; message: string; storageMode: string }>(endpoint, payload),
  });

  const commonDefaults = {
    name: "",
    company: "",
    role: "",
    email: "",
    message: "",
  };

  const contactForm = useForm<ContactRequest>({
    resolver: zodResolver(contactRequestSchema),
    defaultValues: {
      ...commonDefaults,
      inquiryType: "contact",
    },
  });

  const demoForm = useForm<DemoRequest>({
    resolver: zodResolver(demoRequestSchema),
    defaultValues: {
      ...commonDefaults,
      inquiryType: "demo",
      useCase: "",
      teamSize: "",
    },
  });

  const investorForm = useForm<InvestorRequest>({
    resolver: zodResolver(investorRequestSchema),
    defaultValues: {
      ...commonDefaults,
      inquiryType: "investor",
      fundName: "",
      focusArea: "",
    },
  });

  const activeForm =
    kind === "contact"
      ? (contactForm as unknown as UseFormReturn<Record<string, any>>)
      : kind === "demo"
        ? (demoForm as unknown as UseFormReturn<Record<string, any>>)
        : (investorForm as unknown as UseFormReturn<Record<string, any>>);

  const onSubmit = activeForm.handleSubmit(async (values) => {
    await mutation.mutateAsync(values as Record<string, unknown>);
    activeForm.reset();
  });

  return (
    <div className="panel p-6 sm:p-8">
      <div className="flex flex-wrap gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setKind(tab.id)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition ${
              kind === tab.id
                ? "bg-white text-midnight"
                : "border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <form onSubmit={onSubmit} className="mt-6 grid gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={text({ tr: "Ad Soyad", en: "Name" })} error={errorText(activeForm.formState.errors.name, lang)}>
            <input
              {...activeForm.register("name")}
              className={inputClassName}
              placeholder={text({ tr: "Adinizi girin", en: "Enter your name" })}
            />
          </Field>
          <Field label={text({ tr: "Sirket", en: "Company" })} error={errorText(activeForm.formState.errors.company, lang)}>
            <input
              {...activeForm.register("company")}
              className={inputClassName}
              placeholder={text({ tr: "Sirket adini girin", en: "Enter company name" })}
            />
          </Field>
          <Field label={text({ tr: "Rol", en: "Role" })} error={errorText(activeForm.formState.errors.role, lang)}>
            <input
              {...activeForm.register("role")}
              className={inputClassName}
              placeholder={text({ tr: "Rolunuzu girin", en: "Enter your role" })}
            />
          </Field>
          <Field label={text({ tr: "E-posta", en: "Email" })} error={errorText(activeForm.formState.errors.email, lang)}>
            <input
              type="email"
              {...activeForm.register("email")}
              className={inputClassName}
              placeholder={text({ tr: "E-posta adresiniz", en: "Your email address" })}
            />
          </Field>
        </div>

        {kind === "demo" ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              label={text({ tr: "Ana kullanim alani", en: "Primary use case" })}
              error={errorText(demoForm.formState.errors.useCase, lang)}
            >
              <input
                {...demoForm.register("useCase")}
                className={inputClassName}
                placeholder={text({ tr: "Orn. denied basvuru geri kazanimi", en: "E.g. denied applicant recovery" })}
              />
            </Field>
            <Field
              label={text({ tr: "Takim buyuklugu", en: "Team size" })}
              error={errorText(demoForm.formState.errors.teamSize, lang)}
            >
              <select {...demoForm.register("teamSize")} className={inputClassName}>
                <option value="">{text({ tr: "Takim buyuklugu secin", en: "Select team size" })}</option>
                <option value="1-10">1-10</option>
                <option value="11-50">11-50</option>
                <option value="51-200">51-200</option>
                <option value="200+">200+</option>
              </select>
            </Field>
          </div>
        ) : null}

        {kind === "investor" ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              label={text({ tr: "Fon veya kurum", en: "Fund or firm" })}
              error={errorText(investorForm.formState.errors.fundName, lang)}
            >
              <input
                {...investorForm.register("fundName")}
                className={inputClassName}
                placeholder={text({ tr: "Fon veya kurum adini girin", en: "Enter fund or firm name" })}
              />
            </Field>
            <Field
              label={text({ tr: "Yatirim odagi", en: "Focus area" })}
              error={errorText(investorForm.formState.errors.focusArea, lang)}
            >
              <input
                {...investorForm.register("focusArea")}
                className={inputClassName}
                placeholder={text({ tr: "Orn. fintech, AI, infra", en: "E.g. fintech, AI, infra" })}
              />
            </Field>
          </div>
        ) : null}

        <Field label={text({ tr: "Mesaj", en: "Message" })} error={errorText(activeForm.formState.errors.message, lang)}>
          <textarea
            rows={5}
            {...activeForm.register("message")}
            className={inputClassName}
            placeholder={text({
              tr: "Kisaca neyi gormek istediginizi veya neyi cozmeye calistiginizi yazin",
              en: "Share what you want to see or the problem you are trying to solve",
            })}
          />
        </Field>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-slate-400">
            {text({
              tr: "Talepler website backend'ine kaydedilir; veritabani yoksa bellek fallback'i kullanilir.",
              en: "Requests are saved to the website backend and can fall back to memory if a database is not configured yet.",
            })}
          </p>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="rounded-full bg-gradient-to-r from-cobalt to-signal px-6 py-3 text-sm font-semibold text-midnight transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {mutation.isPending
              ? text({ tr: "Gonderiliyor...", en: "Sending..." })
              : text({ tr: "Talebi Gonder", en: "Send request" })}
          </button>
        </div>

        {mutation.isSuccess ? (
          <div className="rounded-2xl border border-signal/30 bg-signal/10 px-4 py-3 text-sm text-signal">
            {translateServerMessage(mutation.data.message, lang)}
          </div>
        ) : null}

        {mutation.isError ? (
          <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {translateServerMessage((mutation.error as Error).message, lang)}
          </div>
        ) : null}
      </form>
    </div>
  );
}

function errorText(error: unknown, lang: "tr" | "en"): string | undefined {
  if (
    typeof error === "object" &&
    error !== null &&
    "message" in error &&
    typeof (error as { message?: unknown }).message === "string"
  ) {
    return translateError((error as { message: string }).message, lang);
  }

  return undefined;
}

function translateError(message: string, lang: "tr" | "en") {
  if (lang === "en") return message;

  const translations: Record<string, string> = {
    "Please enter a name.": "Lutfen adinizi girin.",
    "Please enter a company name.": "Lutfen sirket adini girin.",
    "Please enter your role.": "Lutfen rolunuzu girin.",
    "Please enter a valid email.": "Lutfen gecerli bir e-posta girin.",
    "Please share a bit more context.": "Lutfen biraz daha baglam paylasin.",
    "Please describe the primary use case.": "Lutfen ana kullanim alanini yazin.",
    "Please select a team size.": "Lutfen takim buyuklugunu secin.",
    "Please enter a fund or firm name.": "Lutfen fon veya kurum adini girin.",
    "Please share your focus area.": "Lutfen yatirim odaginizi yazin.",
  };

  return translations[message] ?? message;
}

function translateServerMessage(message: string, lang: "tr" | "en") {
  if (lang === "en") return message;

  const translations: Record<string, string> = {
    "Contact request saved.": "Iletisim talebi kaydedildi.",
    "Demo request saved.": "Demo talebi kaydedildi.",
    "Investor inquiry saved.": "Yatirimci talebi kaydedildi.",
    "Validation failed.": "Dogrulama basarisiz oldu.",
    "Unexpected error.": "Beklenmeyen bir hata olustu.",
    "Request failed": "Istek basarisiz oldu.",
  };

  return translations[message] ?? message;
}

const inputClassName =
  "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-cobalt focus:bg-white/[0.07]";

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <label className="grid gap-2">
      <span className="text-sm font-medium text-slate-200">{label}</span>
      {children}
      {error ? <span className="text-xs text-red-300">{error}</span> : null}
    </label>
  );
}
