import { Link } from "wouter";
import { useLanguage } from "@/i18n/language";

type DemoSectionCtaProps = {
  title: string;
  description: string;
  ctaLabel: string;
  href?: string;
  eyebrow?: string;
};

export function DemoSectionCta({
  title,
  description,
  ctaLabel,
  href = "/contact",
  eyebrow,
}: DemoSectionCtaProps) {
  const { text } = useLanguage();

  return (
    <div className="panel-product mt-8 flex flex-col gap-5 p-6 sm:flex-row sm:items-center sm:justify-between">
      <div className="max-w-2xl">
        <div className="surface-label">
          {eyebrow ?? text({ tr: "Demo talebi", en: "Request demo" })}
        </div>
        <div className="mt-3 font-display text-2xl font-semibold text-white">{title}</div>
        <p className="mt-3 text-sm leading-7 text-slate-300">{description}</p>
      </div>
      <Link
        href={href}
        className="inline-flex items-center justify-center rounded-full bg-mist px-6 py-3 text-sm font-semibold text-ink transition hover:bg-white"
      >
        {ctaLabel}
      </Link>
    </div>
  );
}
