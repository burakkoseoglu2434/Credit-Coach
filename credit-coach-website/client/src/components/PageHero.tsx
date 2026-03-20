import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Link } from "wouter";

type PageHeroProps = {
  eyebrow: string;
  title: string;
  supportingNote?: string;
  disclaimer?: string;
  description: string;
  primaryCta?: { href: string; label: string };
  secondaryCta?: { href: string; label: string };
  tertiaryCta?: { href: string; label: string };
  badges?: string[];
  aside?: ReactNode;
  variant?: "default" | "product";
};

export function PageHero({
  eyebrow,
  title,
  supportingNote,
  disclaimer,
  description,
  primaryCta,
  secondaryCta,
  tertiaryCta,
  badges = [],
  aside,
  variant = "default",
}: PageHeroProps) {
  const isProduct = variant === "product";

  return (
    <section className={`relative overflow-hidden ${isProduct ? "border-b border-white/6" : "border-b border-white/10"}`}>
      <div className={`absolute inset-0 bg-hero-grid ${isProduct ? "opacity-60" : "opacity-100"}`} />
      <div className="shell relative py-20 sm:py-24 lg:py-28">
        <div className={`grid gap-10 ${aside ? "lg:grid-cols-[1.05fr_0.95fr] lg:items-center" : ""}`}>
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: "easeOut" }}
            className="max-w-4xl"
          >
            {disclaimer ? (
              <div className="surface-label border-white/14 bg-white/[0.08] text-mist">{disclaimer}</div>
            ) : null}
            <div className="eyebrow">{eyebrow}</div>
            <h1 className="headline max-w-4xl lg:max-w-3xl">{title}</h1>
            {supportingNote ? (
              <div
                className={`mt-5 max-w-2xl rounded-[24px] px-4 py-3 text-sm font-medium ${
                  isProduct
                    ? "border border-white/10 bg-white/[0.04] text-arctic/90"
                    : "border border-cobalt/20 bg-white/[0.05] text-arctic"
                }`}
              >
                {supportingNote}
              </div>
            ) : null}
            <p className="copy mt-6 max-w-3xl">{description}</p>

            <div className="mt-8 flex flex-wrap gap-3">
              {primaryCta ? (
                <Link
                  href={primaryCta.href}
                  className={
                    isProduct
                      ? "rounded-full bg-mist px-6 py-3 text-sm font-semibold text-ink transition hover:bg-white"
                      : "rounded-full bg-gradient-to-r from-cobalt to-signal px-6 py-3 text-sm font-semibold text-midnight shadow-glow transition hover:opacity-90"
                  }
                >
                  {primaryCta.label}
                </Link>
              ) : null}
              {secondaryCta ? (
                <Link
                  href={secondaryCta.href}
                  className={
                    isProduct
                      ? "rounded-full border border-white/12 bg-white/[0.03] px-6 py-3 text-sm font-medium text-white transition hover:bg-white/[0.08]"
                      : "rounded-full border border-white/15 px-6 py-3 text-sm font-medium text-white transition hover:bg-white/5"
                  }
                >
                  {secondaryCta.label}
                </Link>
              ) : null}
              {tertiaryCta ? (
                <Link
                  href={tertiaryCta.href}
                  className={`px-2 py-3 text-sm font-medium transition hover:text-white ${isProduct ? "text-arctic/90" : "text-arctic"}`}
                >
                  {tertiaryCta.label}
                </Link>
              ) : null}
            </div>

            {badges.length ? (
              <div className="mt-10 flex flex-wrap gap-3">
                {badges.map((badge) => (
                  <span
                    key={badge}
                    className={
                      isProduct
                        ? "surface-label border-white/12 bg-white/[0.04] text-arctic/85"
                        : "rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-arctic"
                    }
                  >
                    {badge}
                  </span>
                ))}
              </div>
            ) : null}
          </motion.div>

          {aside ? <div className="lg:justify-self-end">{aside}</div> : null}
        </div>
      </div>
    </section>
  );
}
