import { Link } from "wouter";

import { FeatureIcon, type FeatureIconName } from "./FeatureIcon";

type CapabilityCardProps = {
  title: string;
  description: string;
  icon: FeatureIconName;
  eyebrow?: string;
  tone?: "default" | "blue" | "green" | "amber";
  cta?: {
    href: string;
    label: string;
  };
};

const toneClasses = {
  default: "border-white/10 bg-white/5",
  blue: "border-cobalt/20 bg-[linear-gradient(180deg,rgba(35,78,184,0.18),rgba(255,255,255,0.04))]",
  green: "border-signal/20 bg-[linear-gradient(180deg,rgba(41,214,175,0.14),rgba(255,255,255,0.04))]",
  amber: "border-copper/20 bg-[linear-gradient(180deg,rgba(221,167,92,0.14),rgba(255,255,255,0.04))]",
};

export function CapabilityCard({
  title,
  description,
  icon,
  eyebrow,
  tone = "default",
  cta,
}: CapabilityCardProps) {
  return (
    <div className={`panel h-full p-6 ${toneClasses[tone]}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-midnight/45 text-arctic">
          <FeatureIcon name={icon} />
        </div>
        {eyebrow ? (
          <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-arctic/70">
            {eyebrow}
          </div>
        ) : null}
      </div>
      <div className="mt-5 font-display text-2xl font-semibold text-white">{title}</div>
      <p className="mt-3 text-sm leading-7 text-slate-300">{description}</p>
      {cta ? (
        <Link
          href={cta.href}
          className="mt-5 inline-flex text-sm font-semibold text-arctic transition hover:text-white"
        >
          {cta.label}
        </Link>
      ) : null}
    </div>
  );
}
