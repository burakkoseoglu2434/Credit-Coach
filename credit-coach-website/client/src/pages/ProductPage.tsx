import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { processSteps } from "@/data/site-content";

export function ProductPage() {
  return (
    <div>
      <PageHero
        eyebrow="Product"
        title="A lender-facing decision layer that starts after deny."
        description="credit-coach is not just another risk model. It sits between decline and lost customer value, turning denied decisions into guided actions, institution-side offers, and measurable learning signals."
        primaryCta={{ href: "/demo", label: "Open Demo Center" }}
        secondaryCta={{ href: "/modules", label: "See Modules" }}
        badges={["Recourse", "Offer logic", "Governance", "Learning loop"]}
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow="How it works"
          title="A product flow designed for lenders, risk teams, and operating teams."
          description="The goal is simple: move beyond explanation into controlled action."
        />
        <div className="mt-10 grid gap-5 lg:grid-cols-5">
          {processSteps.map((step, index) => (
            <div key={step.title} className="panel p-6">
              <div className="text-xs uppercase tracking-[0.22em] text-arctic/55">
                Step {index + 1}
              </div>
              <div className="mt-3 font-display text-2xl font-semibold text-white">
                {step.title}
              </div>
              <p className="mt-4 text-sm leading-7 text-slate-400">{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="shell pb-20">
        <div className="grid gap-5 lg:grid-cols-2">
          <div className="panel p-8">
            <div className="eyebrow">What lenders get</div>
            <ul className="grid gap-4 text-slate-300">
              <li>A single surface for customer actions and institution-side offers</li>
              <li>Recommendation realism instead of pure theoretical optimization</li>
              <li>Trajectory checkpoints and replan visibility</li>
              <li>Commercial proxy evidence for policy experiments</li>
            </ul>
          </div>
          <div className="panel p-8">
            <div className="eyebrow">What governance gets</div>
            <ul className="grid gap-4 text-slate-300">
              <li>Fairness, reliability, and telemetry stay upstream of release decisions</li>
              <li>Canonical machine-readable acceptance artifacts</li>
              <li>Outcome feedback and OPE as supporting evidence, not hidden logic</li>
              <li>Explicit traceability from recommendation to review pack</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
