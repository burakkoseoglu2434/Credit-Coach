import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { investorHighlights } from "@/data/site-content";

export function InvestorPage() {
  return (
    <div>
      <PageHero
        eyebrow="Investor"
        title="A lending optimization layer with a shipped technical core and open product surface."
        description="Kuantitive's opportunity is not to build another score. It is to productize the layer that comes after deny and before lost customer value."
        primaryCta={{ href: "/contact", label: "Request Investor Materials" }}
        secondaryCta={{ href: "/proof", label: "Review Product Proof" }}
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow="Why this matters"
          title="The wedge is commercially meaningful and technically differentiated."
          description="The best version of this company is not a model vendor. It is the operating layer that helps lenders recover denied or near-prime customer value under governance constraints."
        />
        <div className="mt-10 grid gap-5 lg:grid-cols-2">
          {investorHighlights.map((highlight) => (
            <div key={highlight} className="panel p-7 text-sm leading-7 text-slate-300">
              {highlight}
            </div>
          ))}
        </div>
      </section>

      <section className="shell pb-20">
        <div className="grid gap-5 lg:grid-cols-3">
          <div className="panel p-6">
            <div className="eyebrow">What is built</div>
            <div className="mt-3 font-display text-2xl font-semibold text-white">The engine is already real.</div>
            <p className="mt-4 text-sm leading-7 text-slate-400">
              Typed actions, execution-aware ranking, phased trajectories, offer optimization, and learning-loop evidence are already in place.
            </p>
          </div>
          <div className="panel p-6">
            <div className="eyebrow">What is missing</div>
            <div className="mt-3 font-display text-2xl font-semibold text-white">Product shell and commercial packaging.</div>
            <p className="mt-4 text-sm leading-7 text-slate-400">
              The remaining gap is not whether the recommendation core exists. It is whether the company wraps it in a strong operator-facing product and distribution story.
            </p>
          </div>
          <div className="panel p-6">
            <div className="eyebrow">Why now</div>
            <div className="mt-3 font-display text-2xl font-semibold text-white">Lenders need more than explainability.</div>
            <p className="mt-4 text-sm leading-7 text-slate-400">
              Credit teams increasingly need governed next-step systems that help them capture upside without breaking risk, fairness, or telemetry discipline.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
