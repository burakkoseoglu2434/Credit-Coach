import { useMemo, useState, type ReactNode } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm, type UseFormReturn } from "react-hook-form";

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

const tabs: { id: InquiryKind; label: string }[] = [
  { id: "contact", label: "General Contact" },
  { id: "demo", label: "Request a Demo" },
  { id: "investor", label: "Investor Intro" },
];

export function InquiryForm() {
  const [kind, setKind] = useState<InquiryKind>("demo");

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
      ? (contactForm as UseFormReturn<Record<string, any>>)
      : kind === "demo"
        ? (demoForm as UseFormReturn<Record<string, any>>)
        : (investorForm as UseFormReturn<Record<string, any>>);

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
          <Field label="Name" error={activeForm.formState.errors.name?.message}>
            <input {...activeForm.register("name")} className={inputClassName} />
          </Field>
          <Field label="Company" error={activeForm.formState.errors.company?.message}>
            <input {...activeForm.register("company")} className={inputClassName} />
          </Field>
          <Field label="Role" error={activeForm.formState.errors.role?.message}>
            <input {...activeForm.register("role")} className={inputClassName} />
          </Field>
          <Field label="Email" error={activeForm.formState.errors.email?.message}>
            <input type="email" {...activeForm.register("email")} className={inputClassName} />
          </Field>
        </div>

        {kind === "demo" ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Primary use case" error={demoForm.formState.errors.useCase?.message}>
              <input {...demoForm.register("useCase")} className={inputClassName} />
            </Field>
            <Field label="Team size" error={demoForm.formState.errors.teamSize?.message}>
              <select {...demoForm.register("teamSize")} className={inputClassName}>
                <option value="">Select team size</option>
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
            <Field label="Fund or firm" error={investorForm.formState.errors.fundName?.message}>
              <input {...investorForm.register("fundName")} className={inputClassName} />
            </Field>
            <Field label="Focus area" error={investorForm.formState.errors.focusArea?.message}>
              <input {...investorForm.register("focusArea")} className={inputClassName} />
            </Field>
          </div>
        ) : null}

        <Field label="Message" error={activeForm.formState.errors.message?.message}>
          <textarea rows={5} {...activeForm.register("message")} className={inputClassName} />
        </Field>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-slate-400">
            Requests are saved to the website backend and can fall back to memory if a database is not configured yet.
          </p>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="rounded-full bg-gradient-to-r from-cobalt to-signal px-6 py-3 text-sm font-semibold text-midnight transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {mutation.isPending ? "Sending..." : "Send request"}
          </button>
        </div>

        {mutation.isSuccess ? (
          <div className="rounded-2xl border border-signal/30 bg-signal/10 px-4 py-3 text-sm text-signal">
            {mutation.data.message}
          </div>
        ) : null}

        {mutation.isError ? (
          <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {(mutation.error as Error).message}
          </div>
        ) : null}
      </form>
    </div>
  );
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
