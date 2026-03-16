import { Link, useLocation } from "wouter";

import { navLinks } from "@/data/site-content";

export function MainNav() {
  const [location] = useLocation();

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-midnight/75 backdrop-blur-xl">
      <div className="shell flex flex-col gap-4 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-gradient-to-br from-cobalt to-ocean shadow-glow">
              <span className="font-display text-lg font-bold text-white">K</span>
            </div>
            <div>
              <div className="text-xs uppercase tracking-[0.22em] text-arctic/70">Kuantitive</div>
              <div className="font-display text-lg font-semibold text-white">credit-coach</div>
            </div>
          </Link>
        </div>

        <nav className="flex flex-wrap items-center gap-2 lg:justify-center">
          {navLinks.map((link) => {
            const active = location === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-full px-4 py-2 text-sm font-medium transition-all ${
                  active
                    ? "bg-white/10 text-white"
                    : "text-slate-300 hover:bg-white/5 hover:text-white"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href="/demo"
            className="rounded-full border border-white/10 px-4 py-2 text-sm font-medium text-white transition hover:border-cobalt/50 hover:bg-white/5"
          >
            See Demo
          </Link>
          <Link
            href="/contact"
            className="rounded-full bg-gradient-to-r from-cobalt to-signal px-4 py-2 text-sm font-semibold text-midnight transition hover:opacity-90"
          >
            Request a Demo
          </Link>
        </div>
      </div>
    </header>
  );
}
