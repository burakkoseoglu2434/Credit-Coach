import { motion } from "framer-motion";
import { Link } from "wouter";

import { ArtifactCard } from "@/components/ArtifactCard";
import { MetricTile } from "@/components/MetricTile";
import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { modules } from "@/data/site-content";
import { useDemoItem } from "@/hooks/useDemoData";

export function HomePage() {
  const batch = useDemoItem<Record<string, number>>("portfolio-batch-summary");
  const offer = useDemoItem<Record<string, unknown>>("offer-optimization");
  const learning = useDemoItem<Record<string, unknown>>("outcome-ingestion");

  const batchContent = batch.data?.content ?? {};
  const offerMetrics = (offer.data?.content as { canonical_metrics?: Record<string, number> })?.canonical_metrics ?? {};
  const learningContent = learning.data?.content ?? {};

  return (
    <div>
      <PageHero
        eyebrow="Decision Intelligence for Lenders"
        title="Credit decisions should not end at deny."
        description="Kuantitive's credit-coach helps lenders turn denied applications into feasible action plans, institution-side offers, and measurable recovery opportunities without breaking governance."
        primaryCta={{ href: "/demo", label: "See Demo Center" }}
        secondaryCta={{ href: "/investor", label: "Read Investor Story" }}
        badges={[
          "Behavior-aware recourse",
          "Offer optimization",
          "Learning-loop ready",
          "Governance-first",
        ]}
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow="Outcome Layer"
          title="A fintech product wedge between deny and lost customer value."
          description="credit-coach does not stop at explanation. It turns a denied decision into guided next steps, institution-side offers, and measurable evidence for both operations and investors."
        />

        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <MetricTile
            label="Denied to approved lift"
            value={`${Math.round(((batchContent.denied_to_approved_lift as number) ?? 0) * 100)}%`}
            hint="The clearest top-line recourse KPI."
            change="portfolio"
          />
          <MetricTile
            label="Average PD reduction"
            value={`${Math.round(((batchContent.avg_pd_reduction as number) ?? 0) * 100)} bps`}
            hint="Shows that risk quality improves alongside conversion."
            change="risk"
          />
          <MetricTile
            label="Offer acceptance mean"
            value={`${Math.round(((offerMetrics.offer_acceptance_probability_mean as number) ?? 0) * 100)}%`}
            hint="Institution-side offer acceptance becomes part of the same decision surface."
            change="commercial"
          />
          <MetricTile
            label="Reward 90d coverage"
            value={`${Math.round(((learningContent.reward_90d_coverage as number) ?? 0) * 100)}%`}
            hint="The system is already collecting learning-grade evidence."
            change="learning"
          />
        </div>
      </section>

      <section className="shell pb-20">
        <div className="panel overflow-hidden">
          <div className="grid gap-8 px-6 py-8 lg:grid-cols-[1.1fr_0.9fr] lg:px-10 lg:py-12">
            <div>
              <div className="eyebrow">Who this is for</div>
              <h2 className="font-display text-3xl font-semibold text-white sm:text-4xl">
                Built for lenders, understood by investors.
              </h2>
              <p className="mt-5 max-w-2xl text-base leading-7 text-slate-300">
                The website is designed to speak to two audiences at once:
                lenders who want concrete product value and investors who want a
                credible path from technical engine to commercial product.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link href="/product" className="rounded-full border border-white/10 px-5 py-3 text-sm font-medium text-white hover:bg-white/5">
                  Explore Product
                </Link>
                <Link href="/modules" className="rounded-full border border-white/10 px-5 py-3 text-sm font-medium text-white hover:bg-white/5">
                  See Modules
                </Link>
              </div>
            </div>

            <div className="grid gap-4">
              <div className="rounded-[28px] border border-white/10 bg-white/5 p-6">
                <div className="text-xs uppercase tracking-[0.2em] text-arctic/60">Lender view</div>
                <div className="mt-3 font-display text-2xl font-semibold text-white">
                  Move from explainability to guided action.
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-400">
                  Show feasible actions, checkpoint health, offers, and governance-ready evidence in a single decision surface.
                </p>
              </div>
              <div className="rounded-[28px] border border-white/10 bg-white/5 p-6">
                <div className="text-xs uppercase tracking-[0.2em] text-arctic/60">Investor view</div>
                <div className="mt-3 font-display text-2xl font-semibold text-white">
                  More than a scoring model.
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-400">
                  credit-coach is becoming a lending optimization layer with recourse, offer logic, evidence contracts, and outcome-aware learning.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="shell pb-20">
        <SectionHeading
          eyebrow="Modules"
          title="Seven modules, one coherent decision surface."
          description="Each module strengthens the same core promise: feasible recommendations, measurable impact, and governance that stays visible."
        />
        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {modules.slice(0, 6).map((module, index) => (
            <motion.div
              key={module.title}
              initial={{ opacity: 0, y: 22 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ delay: index * 0.05, duration: 0.4 }}
              className="panel p-6"
            >
              <div className="text-xs uppercase tracking-[0.18em] text-arctic/55">Module {index + 1}</div>
              <div className="mt-3 font-display text-2xl font-semibold text-white">{module.title}</div>
              <p className="mt-4 text-sm leading-7 text-slate-400">{module.description}</p>
              <div className="mt-5 text-sm text-slate-300">
                <div><span className="text-slate-500">Outputs:</span> {module.output}</div>
                <div className="mt-1"><span className="text-slate-500">Artifact:</span> {module.artifact}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="shell pb-20">
        <SectionHeading
          eyebrow="Proof"
          title="Artifact-backed, not slogan-backed."
          description="The strongest signal in Credit Coach is that it can point to concrete outputs: customer roadmap artifacts, batch KPIs, offer optimization evidence, and acceptance reviews."
        />
        <div className="mt-10 grid gap-5 lg:grid-cols-4">
          <ArtifactCard
            name="customer_roadmap.json"
            description="Single-customer phased action plan with checkpoint logic and offer context."
            type="json"
          />
          <ArtifactCard
            name="batch_summary.json"
            description="Cohort-level uplift, PD reduction, and trajectory performance summary."
            type="json"
          />
          <ArtifactCard
            name="offer_optimization_summary.json"
            description="Commercial proxy and governance-safe offer evidence."
            type="json"
          />
          <ArtifactCard
            name="milestone_acceptance_review.md"
            description="Human-readable release and governance review derived from machine-readable acceptance data."
            type="markdown"
          />
        </div>
      </section>
    </div>
  );
}
