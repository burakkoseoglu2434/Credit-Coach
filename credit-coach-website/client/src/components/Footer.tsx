import { Link } from "wouter";

export function Footer() {
  return (
    <footer className="border-t border-white/10 bg-midnight/70">
      <div className="shell flex flex-col gap-8 py-12 lg:flex-row lg:justify-between">
        <div className="max-w-xl">
          <div className="font-display text-2xl font-semibold text-white">Kuantitive</div>
          <p className="mt-3 max-w-lg text-sm leading-7 text-slate-400">
            credit-coach is a decision-intelligence layer for lenders: feasible
            recourse plans, institution-side offers, governance evidence, and
            learning-loop readiness in one product surface.
          </p>
        </div>

        <div className="grid gap-3 text-sm text-slate-400">
          <Link href="/product" className="hover:text-white">
            Product
          </Link>
          <Link href="/modules" className="hover:text-white">
            Modules
          </Link>
          <Link href="/demo" className="hover:text-white">
            Demo Center
          </Link>
          <Link href="/investor" className="hover:text-white">
            Investor
          </Link>
        </div>
      </div>
    </footer>
  );
}
