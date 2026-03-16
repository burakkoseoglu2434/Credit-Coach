import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Link } from "wouter";

type PageHeroProps = {
  eyebrow: string;
  title: string;
  description: string;
  primaryCta?: { href: string; label: string };
  secondaryCta?: { href: string; label: string };
  badges?: string[];
  aside?: ReactNode;
};

export function PageHero({
  eyebrow,
  title,
  description,
  primaryCta,
  secondaryCta,
  badges = [],
  aside,
}: PageHeroProps) {
  return (
    <section className="relative overflow-hidden border-b border-white/10">
      <div className="absolute inset-0 bg-hero-grid opacity-100" />
      <div className="shell relative py-20 sm:py-24 lg:py-28">
        <div className={`grid gap-10 ${aside ? "lg:grid-cols-[1.05fr_0.95fr] lg:items-center" : ""}`}>
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: "easeOut" }}
            className="max-w-4xl"
          >
            <div className="eyebrow">{eyebrow}</div>
            <h1 className="headline max-w-4xl lg:max-w-3xl">{title}</h1>
            <p className="copy mt-6 max-w-3xl">{description}</p>

            <div className="mt-8 flex flex-wrap gap-3">
              {primaryCta ? (
                <Link
                  href={primaryCta.href}
                  className="rounded-full bg-gradient-to-r from-cobalt to-signal px-6 py-3 text-sm font-semibold text-midnight shadow-glow transition hover:opacity-90"
                >
                  {primaryCta.label}
                </Link>
              ) : null}
              {secondaryCta ? (
                <Link
                  href={secondaryCta.href}
                  className="rounded-full border border-white/15 px-6 py-3 text-sm font-medium text-white transition hover:bg-white/5"
                >
                  {secondaryCta.label}
                </Link>
              ) : null}
            </div>

            {badges.length ? (
              <div className="mt-10 flex flex-wrap gap-3">
                {badges.map((badge) => (
                  <span
                    key={badge}
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-arctic"
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
