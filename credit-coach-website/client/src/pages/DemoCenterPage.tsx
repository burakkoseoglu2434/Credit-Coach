import { ComparisonBar } from "@/components/ComparisonBar";
import { MetricTile } from "@/components/MetricTile";
import { PageHero } from "@/components/PageHero";
import { RoadmapPhaseCard } from "@/components/RoadmapPhaseCard";
import { SchemaPreviewCard } from "@/components/SchemaPreviewCard";
import { SectionHeading } from "@/components/SectionHeading";
import { useDemoItem } from "@/hooks/useDemoData";
import { useLanguage } from "@/i18n/language";
import type { SingleCustomerDemo } from "@shared/demo-schema";

type GenericContent = Record<string, unknown>;

export function DemoCenterPage() {
  const { text } = useLanguage();
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
        eyebrow={text({ tr: "Demo Merkezi", en: "Demo Center" })}
        title={text({
          tr: "credit-coach'in gercekte ne urettigini dosya ve KPI uzerinden gorun.",
          en: "See what credit-coach actually produces through files and KPIs.",
        })}
        description={text({
          tr: "Bu sayfa en somut urun anlatimidir: tek musteri akisi, portfoy etkisi ve ogrenme sinyalleri ayni yerde gorunur.",
          en: "This is the clearest product walkthrough: customer flow, portfolio impact, and learning signals in one place.",
        })}
        badges={[
          text({ tr: "Tek musteri", en: "Single customer" }),
          text({ tr: "Portfoy KPI'lari", en: "Portfolio KPIs" }),
          text({ tr: "Offer optimizasyonu", en: "Offer optimization" }),
          text({ tr: "Learning loop", en: "Learning loop" }),
        ]}
        aside={
          <div className="grid gap-4 sm:grid-cols-2 lg:w-[480px] lg:grid-cols-2">
            <SchemaPreviewCard
              title={text({ tr: "Musteri Yol Haritasi", en: "Customer Roadmap" })}
              description={text({
                tr: "Her musteri icin bir sonraki en iyi adimi net ve uygulanabilir hale getirir.",
                en: "Makes the next best action clear and practical for each customer.",
              })}
            />
            <SchemaPreviewCard
              title={text({ tr: "Ogrenme Sinyalleri", en: "Learning Signals" })}
              description={text({
                tr: "Gercek sonuclarin gelecekteki karar kalitesine nasil donusecegini gosterir.",
                en: "Shows how real outcomes can improve future decision quality.",
              })}
              tone="green"
            />
          </div>
        }
      />

      <section className="shell py-20">
        <SectionHeading
          eyebrow={text({ tr: "Tek musteri", en: "Single customer" })}
          title={text({
            tr: "Reddedilen bir musteri, fazli ve kontrollu bir yol haritasina donusur.",
            en: "A denied applicant becomes a phased, governed roadmap.",
          })}
          description={text({
            tr: "Ayni plan icinde musteri aksiyonlari, checkpoint sagligi ve kurum teklifi birlikte gorunur.",
            en: "This view shows how customer actions, checkpoint health, and institution-side offers can live in the same plan.",
          })}
        />
        {roadmapContent ? (
          <div className="mt-10 grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
            <div className="panel p-6">
              <div className="text-xs uppercase tracking-[0.22em] text-arctic/55">
                {text({ tr: "Profil", en: "Profile" })}
              </div>
              <div className="mt-3 font-display text-3xl font-semibold text-white">
                {roadmapContent.customer.profile}
              </div>
              <div className="mt-5 grid gap-3 text-sm text-slate-300">
                <div>{text({ tr: "Musteri", en: "Customer" })}: <span className="text-white">{roadmapContent.customer.customer_id}</span></div>
                <div>{text({ tr: "Segment", en: "Segment" })}: <span className="text-white">{roadmapContent.customer.segment}</span></div>
                <div>{text({ tr: "Risk bandi", en: "Risk band" })}: <span className="text-white">{roadmapContent.customer.risk_band}</span></div>
                <div>{text({ tr: "Gelir bandi", en: "Income band" })}: <span className="text-white">{roadmapContent.customer.income_band}</span></div>
              </div>
              <div className="mt-6 grid gap-4">
                <MetricTile label={text({ tr: "Baslangic PD", en: "Base PD" })} value={roadmapContent.summary.base_pd.toFixed(2)} />
                <MetricTile
                  label={text({ tr: "Plan gerceklesme", en: "Plan execution" })}
                  value={`${Math.round(roadmapContent.summary.plan_execution_probability * 100)}%`}
                />
                <MetricTile
                  label={text({ tr: "Birlesik gerceklesme", en: "Combined realization" })}
                  value={`${Math.round(roadmapContent.summary.combined_plan_realization_probability * 100)}%`}
                />
                <MetricTile
                  label={text({ tr: "Trajectory durumu", en: "Trajectory status" })}
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
          eyebrow={text({ tr: "Portfoy gorunumu", en: "Portfolio view" })}
          title={text({
            tr: "Tek ornek degil, cohort seviyesinde ne oldugunu gorun.",
            en: "What happens across a cohort, not just in a single example.",
          })}
          description={text({
            tr: "Batch yuzeyi, motorun anekdot degil olculebilir hareket urettiginin en net kaniti.",
            en: "The batch surface is the clearest proof that the engine creates measurable movement rather than isolated anecdotes.",
          })}
        />
        <div className="mt-10 grid gap-5 lg:grid-cols-5">
          <MetricTile
            label={text({ tr: "Denied to approved lift", en: "Denied to approved lift" })}
            value={`${Math.round(((batchContent.denied_to_approved_lift as number) ?? 0) * 100)}%`}
          />
          <MetricTile
            label={text({ tr: "PD dususu", en: "PD reduction" })}
            value={`${Math.round(((batchContent.avg_pd_reduction as number) ?? 0) * 100)} bps`}
          />
          <MetricTile
            label={text({ tr: "4 hafta gecis", en: "4-week pass" })}
            value={`${Math.round(((batchContent.trajectory_gate_pass_rate_4w as number) ?? 0) * 100)}%`}
          />
          <MetricTile
            label={text({ tr: "12 hafta gecis", en: "12-week pass" })}
            value={`${Math.round(((batchContent.trajectory_gate_pass_rate_12w as number) ?? 0) * 100)}%`}
          />
          <MetricTile
            label={text({ tr: "24 hafta gecis", en: "24-week pass" })}
            value={`${Math.round(((batchContent.trajectory_gate_pass_rate_24w as number) ?? 0) * 100)}%`}
          />
        </div>
      </section>

      <section className="shell pb-20">
        <SectionHeading
          eyebrow={text({ tr: "Hizli kalite panosu", en: "Quality snapshot" })}
          title={text({
            tr: "Onerinin ne kadar gercekci ve saglikli oldugu burada okunur.",
            en: "This is where recommendation realism and health become visible.",
          })}
          description={text({
            tr: "Uzun teknik aciklama yerine oranlar ve dominant sinyaller one cikar.",
            en: "Instead of long technical text, show the dominant ratios and signals.",
          })}
        />
        <div className="grid gap-5 lg:grid-cols-3">
          <div className="panel p-6">
            <div className="eyebrow">{text({ tr: "Action realism", en: "Action realism" })}</div>
            <div className="mt-2 font-display text-2xl font-semibold text-white">
              {text({ tr: "Sembolik degil, uygulanabilir.", en: "Feasible, not symbolic." })}
            </div>
            <div className="mt-6 space-y-4">
              <ComparisonBar label={text({ tr: "Davranissal aksiyon", en: "Behavioral actions" })} value={Number(actionMetrics.action_type_behavioral_rate ?? 0)} />
              <ComparisonBar label={text({ tr: "Yapisal aksiyon", en: "Structural actions" })} value={Number(actionMetrics.action_type_structural_rate ?? 0)} />
              <ComparisonBar label={text({ tr: "Kurumsal aksiyon", en: "Institutional actions" })} value={Number(actionMetrics.action_type_institutional_rate ?? 0)} />
              <ComparisonBar label={text({ tr: "Infeasible plan rate", en: "Infeasible plan rate" })} value={Number(actionMetrics.infeasible_plan_rate ?? 0)} color="amber" />
            </div>
          </div>

          <div className="panel p-6">
            <div className="eyebrow">{text({ tr: "Behavior-aware", en: "Behavior-aware" })}</div>
            <div className="mt-2 font-display text-2xl font-semibold text-white">
              {text({ tr: "Motor gercekciligi siralamaya katar.", en: "The engine prices realism into ranking." })}
            </div>
            <div className="mt-6 space-y-4">
              <ComparisonBar label={text({ tr: "Gerceklesme olasiligi", en: "Execution probability" })} value={Number(behaviorMetrics.mean_plan_execution_probability ?? 0)} />
              <ComparisonBar label={text({ tr: "Kismi uygulama", en: "Partial execution" })} value={Number(behaviorMetrics.partial_execution_rate ?? 0)} color="green" />
              <ComparisonBar label={text({ tr: "Karisik uygulama", en: "Mixed execution" })} value={Number(behaviorMetrics.mixed_execution_rate ?? 0)} />
              <ComparisonBar label={text({ tr: "Basarisiz uygulama", en: "Failed execution" })} value={Number(behaviorMetrics.failed_execution_rate ?? 0)} color="amber" />
            </div>
          </div>

          <div className="panel p-6">
            <div className="eyebrow">{text({ tr: "Trajectory", en: "Trajectory" })}</div>
            <div className="mt-2 font-display text-2xl font-semibold text-white">
              {text({ tr: "Kisa vade sagligi birinci oncelik.", en: "Short-term health stays primary." })}
            </div>
            <div className="mt-6 space-y-4">
              <ComparisonBar label={text({ tr: "Yolunda", en: "On-track" })} value={Number(trajectoryMetrics.trajectory_on_track_rate ?? 0)} color="green" />
              <ComparisonBar label={text({ tr: "Replan gerekiyor", en: "Needs replan" })} value={Number(trajectoryMetrics.trajectory_needs_replan_rate ?? 0)} />
              <ComparisonBar label={text({ tr: "Degraded", en: "Degraded" })} value={Number(trajectoryMetrics.trajectory_degraded_rate ?? 0)} color="amber" />
              <div className="rounded-3xl border border-white/10 bg-white/4 p-4 text-sm text-slate-300">
                {text({ tr: "Baskin gecis nedeni", en: "Dominant transition reason" })}:{" "}
                <span className="font-medium text-white">
                  {String((trajectory.data?.content as GenericContent)?.dominant_transition_reason ?? text({ tr: "yok", en: "n/a" }))}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="shell pb-20">
        <SectionHeading
          eyebrow={text({ tr: "Ticari ve ogrenme katmani", en: "Commercial and learning layer" })}
          title={text({
            tr: "Offer kararlarini ve ogrenme hazirligini ayni yuzeyde gosteren blok.",
            en: "A single block for offer decisions and learning readiness.",
          })}
          description={text({
            tr: "Bu kisim, fintech urun havasini en iyi veren somut KPI seti.",
            en: "This is the clearest fintech-facing KPI surface in the demo.",
          })}
        />
        <div className="grid gap-5 lg:grid-cols-2">
          <div className="panel p-6">
            <div className="eyebrow">{text({ tr: "Offer optimizasyonu", en: "Offer optimization" })}</div>
            <div className="mt-2 font-display text-3xl font-semibold text-white">
              {text({
                tr: "Kurum teklifleri, recommendation yuzeyinin dogal parcasi olur.",
                en: "Institution-side offers become part of the recommendation surface.",
              })}
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <MetricTile
                label={text({ tr: "Offer plan rate", en: "Offer plan rate" })}
                value={`${Math.round(Number(offerMetrics.offer_plan_rate ?? 0) * 100)}%`}
              />
              <MetricTile
                label={text({ tr: "Rankable offer rate", en: "Rankable offer rate" })}
                value={`${Math.round(Number(offerMetrics.rankable_offer_rate ?? 0) * 100)}%`}
              />
              <MetricTile
                label={text({ tr: "Offer kabul", en: "Offer acceptance" })}
                value={`${Math.round(Number(offerMetrics.offer_acceptance_probability_mean ?? 0) * 100)}%`}
              />
              <MetricTile
                label={text({ tr: "Birlesik gerceklesme", en: "Combined realization" })}
                value={`${Math.round(Number(offerMetrics.combined_plan_realization_probability_mean ?? 0) * 100)}%`}
              />
            </div>
          </div>

          <div className="panel p-6">
            <div className="eyebrow">{text({ tr: "Learning loop", en: "Learning loop" })}</div>
            <div className="mt-2 font-display text-3xl font-semibold text-white">
              {text({
                tr: "Sistem, sonradan ogrenebilecegi kaniti toplamaya basliyor.",
                en: "The system is collecting evidence it can learn from later.",
              })}
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <MetricTile
                label={text({ tr: "Decision log tamligi", en: "Decision log completeness" })}
                value={`${Math.round(Number(learningContent.decision_log_completeness ?? 0) * 100)}%`}
              />
              <MetricTile
                label={text({ tr: "90 gun reward coverage", en: "Reward 90d coverage" })}
                value={`${Math.round(Number(learningContent.reward_90d_coverage ?? 0) * 100)}%`}
              />
              <MetricTile
                label={text({ tr: "OPE guveni", en: "OPE confidence" })}
                value={String(opeContent.ope_confidence ?? text({ tr: "yok", en: "n/a" }))}
              />
              <MetricTile
                label={text({ tr: "Tercih edilen policy sinyali", en: "Preferred policy signal" })}
                value={String((opeContent.preferred_policy_signal as GenericContent)?.signal ?? text({ tr: "yok", en: "n/a" }))}
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
