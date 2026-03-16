import { ArtifactCard } from "@/components/ArtifactCard";
import { PageHero } from "@/components/PageHero";
import { SectionHeading } from "@/components/SectionHeading";
import { useDemoIndex } from "@/hooks/useDemoData";

export function ProofPage() {
  const demoIndex = useDemoIndex();

  return (
    <div>
      <PageHero
        eyebrow="Proof"
        title="Every major claim in the product can be tied back to an artifact."
        description="This is where credit-coach separates itself from a generic AI demo. The system ships with evidence contracts, not just copy."
        primaryCta={{ href: "/demo", label: "Open the Demo Center" }}
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow="Evidence families"
          title="Canonical outputs across recommendation quality, offers, learning, and governance."
          description="The same artifact-first model powers the engine, the review workflow, and now the website proof layer."
        />
        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {demoIndex.data?.items.map((item) => (
            <ArtifactCard
              key={item.slug}
              name={item.title}
              description={item.summary}
              type={item.type}
            />
          ))}
        </div>
      </section>

      <section className="shell pb-20">
        <div className="grid gap-5 lg:grid-cols-3">
          <div className="panel p-6">
            <div className="eyebrow">Recommendation quality</div>
            <p className="mt-4 text-sm leading-7 text-slate-300">
              Candidate diversity, action realism, behavior-aware ranking, and trajectory health prove that the engine is not just theoretical.
            </p>
          </div>
          <div className="panel p-6">
            <div className="eyebrow">Commercial layer</div>
            <p className="mt-4 text-sm leading-7 text-slate-300">
              Offer optimization adds institution-side action into the same governed decision surface and measures proxy impact directly.
            </p>
          </div>
          <div className="panel p-6">
            <div className="eyebrow">Governance and learning</div>
            <p className="mt-4 text-sm leading-7 text-slate-300">
              Acceptance artifacts, telemetry gates, decision logging, and OPE signals keep the system honest as it moves toward learning-capable behavior.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
