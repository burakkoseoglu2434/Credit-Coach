import { useLanguage } from "@/i18n/language";
import {
  formatActionClass,
  formatActionDetail,
  formatActionTitle,
  formatOfferType,
  formatPhaseTitle,
  formatWindowLabel,
} from "@/lib/demo-formatters";

type RoadmapStep = {
  action_key: string;
  action_class: string;
  action_title: string;
  detail: string;
  time_months: number;
  estimated_cost_usd: number;
  plan_execution_probability?: number;
  offer_type?: string;
};

type RoadmapPhaseCardProps = {
  phase: {
    phase_id: string;
    phase_title: string;
    target_window_weeks: string;
    target_pd: number;
    steps: RoadmapStep[];
  };
};

export function RoadmapPhaseCard({ phase }: RoadmapPhaseCardProps) {
  const { text, lang } = useLanguage();

  return (
    <div className="panel p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mt-2 font-display text-2xl font-semibold text-white">
            {formatPhaseTitle(phase.phase_id, phase.phase_title, lang)}
          </div>
          <div className="mt-2 text-sm text-slate-400">
            {formatWindowLabel(phase.target_window_weeks, lang)}
          </div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-right">
          <div className="text-xs uppercase tracking-[0.18em] text-arctic/55">
            {text({ tr: "Hedef PD", en: "Target PD" })}
          </div>
          <div className="mt-1 font-display text-2xl font-semibold text-white">
            {phase.target_pd.toFixed(2)}
          </div>
          <div className="mt-1 text-sm text-slate-400">
            {formatWindowLabel(phase.target_window_weeks, lang)}
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-4">
        {phase.steps.map((step) => (
          <div key={`${phase.phase_id}-${step.action_key}`} className="rounded-3xl border border-white/10 bg-white/4 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-cobalt/15 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-arctic">
                {formatActionClass(step.action_class, lang)}
              </span>
              {step.offer_type ? (
                <span className="rounded-full bg-signal/10 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-signal">
                  {formatOfferType(step.offer_type, lang)}
                </span>
              ) : null}
            </div>
            <div className="mt-3 font-medium text-white">
              {formatActionTitle(step.action_title, lang)}
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              {formatActionDetail(step.detail, lang)}
            </p>
            <div className="mt-4 flex flex-wrap gap-3 text-sm text-slate-300">
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5">
                {text({ tr: "Zaman", en: "Timeline" })}: {step.time_months} {text({ tr: "ay", en: "months" })}
              </span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5">
                {text({ tr: "Gerceklesme", en: "Execution" })}:{" "}
                {step.plan_execution_probability !== undefined
                  ? `${Math.round(step.plan_execution_probability * 100)}%`
                  : text({ tr: "yok", en: "n/a" })}
              </span>
            </div>
            <details className="mt-4 rounded-2xl border border-white/10 bg-midnight/35 px-4 py-3 text-sm text-slate-300">
              <summary className="cursor-pointer list-none font-medium text-arctic">
                {text({ tr: "Teknik detaylar", en: "Technical details" })}
              </summary>
              <div className="mt-3 grid gap-2 text-sm text-slate-400">
                <div>
                  {text({ tr: "Action key", en: "Action key" })}:{" "}
                  <span className="text-white">{step.action_key}</span>
                </div>
                <div>
                  {text({ tr: "Ham sinif", en: "Raw class" })}:{" "}
                  <span className="text-white">{step.action_class}</span>
                </div>
                <div>
                  {text({ tr: "Tahmini maliyet", en: "Estimated cost" })}:{" "}
                  <span className="text-white">${step.estimated_cost_usd}</span>
                </div>
              </div>
            </details>
          </div>
        ))}
      </div>
    </div>
  );
}
