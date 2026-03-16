import { ComparisonBar } from "@/components/ComparisonBar";
import { MetricTile } from "@/components/MetricTile";
import { PageHero } from "@/components/PageHero";
import { RoadmapPhaseCard } from "@/components/RoadmapPhaseCard";
import { SectionHeading } from "@/components/SectionHeading";
import { useDemoItem } from "@/hooks/useDemoData";
import type { SingleCustomerDemo } from "@shared/demo-schema";

type GenericContent = Record<string, unknown>;

export function DemoCenterPage() {
  const roadmap = useDemoItem<SingleCustomerDemo>("single-customer-roadmap");
  const batch = useDemoItem<GenericContent>("portfolio-batch-summary");
  const actionRealism = useDemoItem<GenericContent>("action-realism");
  const behaviorAware = useDemoItem<GenericContent>("behavior-aware");
  const trajectory = useDemoItem<GenericContent>("trajectory");
  const offer = useDemoItem<GenericContent>("offer-optimization");
  const learning = useDemoItem<GenericContent>("outcome-ingestion");
  const ope = useDemoItem<GenericContent>("off-policy-evaluation");

  const roadmapContent = roadmap.data?.content;
  const batchContent = batch.data?.content ?? {};
  const actionMetrics = ((actionRealism.data?.content as GenericContent)?.canonical_metrics as GenericContent) ?? {};
  const behaviorMetrics = ((behaviorAware.data?.content as GenericContent)?.canonical_metrics as GenericContent) ?? {};
  const trajectoryMetrics = ((trajectory.data?.content as GenericContent)?.canonical_metrics as GenericContent) ?? {};
  const offerMetrics = ((offer.data?.content as GenericContent)?.canonical_metrics as GenericContent) ?? {};
  const learningContent = learning.data?.content ?? {};
  const opeContent = ope.data?.content ?? {};

  return (
    <div>
      <PageHero
        eyebrow="Demo Center"
        title="A proof-driven walkthrough of what credit-coach actually produces."
        description="This is the most important page in the site. It turns artifacts and KPIs into a lender-facing product story."
        badges={["Single customer", "Portfolio KPIs", "Offer optimization", "Learning loop"]}
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow="Single customer"
          title="A denied applicant becomes a phased, governed roadmap."
          description="This view shows how customer actions, checkpoint health, and institution-side offers can live in the same plan."
        />
        {roadmapContent ? (
          <div className="mt-10 grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
            <div className="panel p-6">
              <div className="text-xs uppercase tracking-[0.22em] text-arctic/55">Profile</div>
              <div className="mt-3 font-display text-3xl font-semibold text-white">
                {roadmapContent.customer.profile}
              </div>
              <div className="mt-5 grid gap-3 text-sm text-slate-300">
                <div>Customer: <span className="text-white">{roadmapContent.customer.customer_id}</span></div>
                <div>Segment: <span className="text-white">{roadmapContent.customer.segment}</span></div>
                <div>Risk band: <span className="text-white">{roadmapContent.customer.risk_band}</span></div>
                <div>Income band: <span className="text-white">{roadmapContent.customer.income_band}</span></div>
              </div>
              <div className="mt-6 grid gap-4">
                <MetricTile label="Base PD" value={roadmapContent.summary.base_pd.toFixed(2)} />
                <MetricTile
                  label="Plan execution"
                  value={`${Math.round(roadmapContent.summary.plan_execution_probability * 100)}%`}
                />
                <MetricTile
                  label="Combined realization"
                  value={`${Math.round(roadmapContent.summary.combined_plan_realization_probability * 100)}%`}
                />
                <MetricTile
                  label="Trajectory status"
                  value={String(roadmapContent.summary.trajectory_status)}
                />
              </div>
            </div>

            <div className="grid gap-5">
              {roadmapContent.phases.map((phase) => (
                <RoadmapPhaseCard key={phase.phase_id} phase={phase} />
              ))}
            </div>
          </div>
        ) : null}
      </section>

      <section className="shell pb-20">
        <SectionHeading
          eyebrow="Portfolio view"
          title="What happens across a cohort, not just in a single example."
          description="The batch surface is the clearest proof that the engine creates measurable movement rather than isolated anecdotes."
        />
        <div className="mt-10 grid gap-5 lg:grid-cols-5">
          <MetricTile
            label="Denied to approved lift"
            value={`${Math.round(((batchContent.denied_to_approved_lift as number) ?? 0) * 100)}%`}
          />
          <MetricTile
            label="PD reduction"
            value={`${Math.round(((batchContent.avg_pd_reduction as number) ?? 0) * 100)} bps`}
          />
          <MetricTile
            label="4-week pass"
            value={`${Math.round(((batchContent.trajectory_gate_pass_rate_4w as number) ?? 0) * 100)}%`}
          />
          <MetricTile
            label="12-week pass"
            value={`${Math.round(((batchContent.trajectory_gate_pass_rate_12w as number) ?? 0) * 100)}%`}
          />
          <MetricTile
            label="24-week pass"
            value={`${Math.round(((batchContent.trajectory_gate_pass_rate_24w as number) ?? 0) * 100)}%`}
          />
        </div>
      </section>

      <section className="shell pb-20">
        <div className="grid gap-5 lg:grid-cols-3">
          <div className="panel p-6">
            <div className="eyebrow">Action realism</div>
            <div className="mt-2 font-display text-2xl font-semibold text-white">Feasible, not symbolic.</div>
            <div className="mt-6 space-y-4">
              <ComparisonBar label="Behavioral actions" value={Number(actionMetrics.action_type_behavioral_rate ?? 0)} />
              <ComparisonBar label="Structural actions" value={Number(actionMetrics.action_type_structural_rate ?? 0)} />
              <ComparisonBar label="Institutional actions" value={Number(actionMetrics.action_type_institutional_rate ?? 0)} />
              <ComparisonBar label="Infeasible plan rate" value={Number(actionMetrics.infeasible_plan_rate ?? 0)} color="amber" />
            </div>
          </div>

          <div className="panel p-6">
            <div className="eyebrow">Behavior-aware</div>
            <div className="mt-2 font-display text-2xl font-semibold text-white">The engine prices realism into ranking.</div>
            <div className="mt-6 space-y-4">
              <ComparisonBar label="Execution probability" value={Number(behaviorMetrics.mean_plan_execution_probability ?? 0)} />
              <ComparisonBar label="Partial execution" value={Number(behaviorMetrics.partial_execution_rate ?? 0)} color="green" />
              <ComparisonBar label="Mixed execution" value={Number(behaviorMetrics.mixed_execution_rate ?? 0)} />
              <ComparisonBar label="Failed execution" value={Number(behaviorMetrics.failed_execution_rate ?? 0)} color="amber" />
            </div>
          </div>

          <div className="panel p-6">
            <div className="eyebrow">Trajectory</div>
            <div className="mt-2 font-display text-2xl font-semibold text-white">Short-term health stays primary.</div>
            <div className="mt-6 space-y-4">
              <ComparisonBar label="On-track" value={Number(trajectoryMetrics.trajectory_on_track_rate ?? 0)} color="green" />
              <ComparisonBar label="Needs replan" value={Number(trajectoryMetrics.trajectory_needs_replan_rate ?? 0)} />
              <ComparisonBar label="Degraded" value={Number(trajectoryMetrics.trajectory_degraded_rate ?? 0)} color="amber" />
              <div className="rounded-3xl border border-white/10 bg-white/4 p-4 text-sm text-slate-300">
                Dominant transition reason:{" "}
                <span className="font-medium text-white">
                  {String((trajectory.data?.content as GenericContent)?.dominant_transition_reason ?? "n/a")}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="shell pb-20">
        <div className="grid gap-5 lg:grid-cols-2">
          <div className="panel p-6">
            <div className="eyebrow">Offer optimization</div>
            <div className="mt-2 font-display text-3xl font-semibold text-white">
              Institution-side offers become part of the recommendation surface.
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <MetricTile
                label="Offer plan rate"
                value={`${Math.round(Number(offerMetrics.offer_plan_rate ?? 0) * 100)}%`}
              />
              <MetricTile
                label="Rankable offer rate"
                value={`${Math.round(Number(offerMetrics.rankable_offer_rate ?? 0) * 100)}%`}
              />
              <MetricTile
                label="Offer acceptance"
                value={`${Math.round(Number(offerMetrics.offer_acceptance_probability_mean ?? 0) * 100)}%`}
              />
              <MetricTile
                label="Combined realization"
                value={`${Math.round(Number(offerMetrics.combined_plan_realization_probability_mean ?? 0) * 100)}%`}
              />
            </div>
          </div>

          <div className="panel p-6">
            <div className="eyebrow">Learning loop</div>
            <div className="mt-2 font-display text-3xl font-semibold text-white">
              The system is collecting evidence it can learn from later.
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <MetricTile
                label="Decision log completeness"
                value={`${Math.round(Number(learningContent.decision_log_completeness ?? 0) * 100)}%`}
              />
              <MetricTile
                label="Reward 90d coverage"
                value={`${Math.round(Number(learningContent.reward_90d_coverage ?? 0) * 100)}%`}
              />
              <MetricTile
                label="OPE confidence"
                value={String(opeContent.ope_confidence ?? "n/a")}
              />
              <MetricTile
                label="Preferred policy signal"
                value={String((opeContent.preferred_policy_signal as GenericContent)?.signal ?? "n/a")}
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
