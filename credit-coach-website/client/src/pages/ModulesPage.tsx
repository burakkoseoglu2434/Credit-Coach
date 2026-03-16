import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { modules } from "@/data/site-content";

export function ModulesPage() {
  return (
    <div>
      <PageHero
        eyebrow="Modules"
        title="Each module makes the decision surface more commercially useful."
        description="The product is modular enough to explain, but integrated enough to feel like one system."
        primaryCta={{ href: "/demo", label: "See Module Outputs" }}
        secondaryCta={{ href: "/contact", label: "Discuss a Pilot" }}
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow="Module map"
          title="From risk diagnosis to learning-ready policy evidence."
          description="This stack is what turns credit-coach from a research engine into a productizable fintech system."
        />
        <div className="mt-10 grid gap-5 lg:grid-cols-2">
          {modules.map((module) => (
            <div key={module.title} className="panel p-7">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="font-display text-2xl font-semibold text-white">
                    {module.title}
                  </div>
                  <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-400">
                    {module.description}
                  </p>
                </div>
                <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.2em] text-arctic/70">
                  {module.artifact}
                </div>
              </div>
              <div className="mt-6 rounded-3xl border border-white/10 bg-white/4 p-4">
                <div className="text-xs uppercase tracking-[0.2em] text-arctic/55">What it outputs</div>
                <div className="mt-2 text-sm leading-6 text-slate-300">{module.output}</div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
