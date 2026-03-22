import { useLanguage } from "@/i18n/language";
import {
  formatActionClass,
  formatActionTitle,
  formatOfferType,
  formatWindowLabel,
  pickLocalizedText,
} from "@/lib/demo-formatters";
import type { SingleCustomerDemo } from "@shared/demo-schema";

type RoadmapPhase = SingleCustomerDemo["phases"][number];
type RoadmapStep = RoadmapPhase["steps"][number];

type RoadmapPhaseCardProps = {
  phase: RoadmapPhase;
};

function localizedOrNull(
  value: { tr: string; en: string } | null | undefined,
  lang: "tr" | "en",
) {
  if (!value) {
    return null;
  }
  return pickLocalizedText(value, lang);
}

function missingFieldText(lang: "tr" | "en", kind: "outcome" | "timing" | "details") {
  const labels = {
    outcome: {
      tr: "Bu adim icin sayisal sonuc detayi bu gorunumde hazir degil.",
      en: "The numeric outcome detail for this step is not available in this view.",
    },
    timing: {
      tr: "Zamanlama detayi bu gorunumde hazir degil.",
      en: "Timing detail is not available in this view.",
    },
    details: {
      tr: "Bu adim icin ek anlatim detayi su anda kullanilabilir degil.",
      en: "Additional narrative detail for this step is not currently available.",
    },
  } as const;

  return labels[kind][lang];
}

function ActionCard({
  phase,
  step,
}: {
  phase: RoadmapPhase;
  step: RoadmapStep;
}) {
  const { lang, text } = useLanguage();
  const narrative = step.narrative;

  const actionSummary =
    localizedOrNull(narrative?.action_summary, lang) ??
    formatActionTitle(step.action_title, lang);
  const expectedOutcome =
    localizedOrNull(narrative?.expected_outcome, lang) ?? missingFieldText(lang, "outcome");
  const timingHint =
    localizedOrNull(narrative?.action_timing_hint, lang) ?? missingFieldText(lang, "timing");
  const whyThisMatters =
    localizedOrNull(narrative?.why_this_matters, lang) ?? missingFieldText(lang, "details");
  const ifDone =
    localizedOrNull(narrative?.what_happens_if_done, lang) ?? missingFieldText(lang, "details");
  const ifNotDone =
    localizedOrNull(narrative?.what_happens_if_not_done, lang) ?? missingFieldText(lang, "details");
  const feasibilityLabel = localizedOrNull(narrative?.feasibility_outcome_label, lang);
  const difficultyLabel = localizedOrNull(narrative?.difficulty_label, lang);
  const followThroughNote = localizedOrNull(narrative?.follow_through_note, lang);
  const offerExplanation = localizedOrNull(narrative?.offer_narrative?.offer_explanation, lang);

  return (
    <article className="rounded-[24px] border border-white/10 bg-white/[0.03] p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          <span className="surface-label">
            {formatWindowLabel(phase.target_window_weeks, lang)}
          </span>
          <span className="surface-label">{formatActionClass(step.action_class, lang)}</span>
          {feasibilityLabel ? <span className="surface-label">{feasibilityLabel}</span> : null}
          {difficultyLabel ? <span className="surface-label">{difficultyLabel}</span> : null}
        </div>
        <div className="surface-label">
          {text({ tr: "Faz", en: "Phase" })} {phase.phase_id.replace("phase_", "").replace(/_/g, " ")}
        </div>
      </div>

      <div className="mt-4 font-medium text-white">{actionSummary}</div>

      <div className="mt-4 grid gap-3 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[20px] border border-white/10 bg-slate-950/40 p-4">
          <div className="text-[11px] uppercase tracking-[0.16em] text-arctic/60">
            {text({ tr: "Beklenen sonuc", en: "Expected outcome" })}
          </div>
          <div className="mt-2 text-sm leading-6 text-slate-300">{expectedOutcome}</div>
        </div>
        <div className="rounded-[20px] border border-white/10 bg-slate-950/40 p-4">
          <div className="text-[11px] uppercase tracking-[0.16em] text-arctic/60">
            {text({ tr: "Ne zamana kadar", en: "By when" })}
          </div>
          <div className="mt-2 text-sm leading-6 text-slate-300">{timingHint}</div>
        </div>
      </div>

      {followThroughNote ? (
        <div className="mt-4 rounded-[18px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-300">
          {followThroughNote}
        </div>
      ) : null}

      {offerExplanation || step.offer_type ? (
        <div className="mt-4 rounded-[18px] border border-signal/20 bg-signal/5 px-4 py-3 text-sm text-slate-300">
          <div className="flex flex-wrap items-center gap-2">
            <span className="surface-label border-signal/20 bg-signal/10 text-signal">
              {text({ tr: "Kurum destegi", en: "Institution support" })}
            </span>
            {step.offer_type ? (
              <span className="surface-label border-signal/20 bg-signal/10 text-signal">
                {formatOfferType(step.offer_type, lang)}
              </span>
            ) : null}
          </div>
          <div className="mt-2">
            {offerExplanation ??
              text({
                tr: "Bu adimla birlikte kurum destegi ayni yolun icinde degerlendirilebilir.",
                en: "Institution support can be evaluated alongside this step inside the same path.",
              })}
          </div>
        </div>
      ) : null}

      <details className="mt-4 rounded-[18px] border border-white/10 bg-slate-950/30 px-4 py-3 text-sm text-slate-300">
        <summary className="cursor-pointer list-none font-semibold text-white">
          {text({ tr: "Bu adimin neden onemli oldugunu gor", en: "See why this step matters" })}
        </summary>
        <div className="mt-4 grid gap-3">
          <div>
            <div className="surface-label">{text({ tr: "Neden onemli", en: "Why this matters" })}</div>
            <p className="mt-2 leading-7 text-slate-300">{whyThisMatters}</p>
          </div>
          <div className="grid gap-3 lg:grid-cols-2">
            <div className="rounded-[16px] border border-white/10 bg-white/[0.03] p-4">
              <div className="surface-label">{text({ tr: "Yapilirsa", en: "If done" })}</div>
              <p className="mt-2 leading-7 text-slate-300">{ifDone}</p>
            </div>
            <div className="rounded-[16px] border border-white/10 bg-white/[0.03] p-4">
              <div className="surface-label">{text({ tr: "Atlanirsa", en: "If skipped" })}</div>
              <p className="mt-2 leading-7 text-slate-300">{ifNotDone}</p>
            </div>
          </div>
        </div>
      </details>
    </article>
  );
}

export function RoadmapPhaseCard({ phase }: RoadmapPhaseCardProps) {
  const { lang } = useLanguage();

  if (phase.steps.length === 0) {
    return null;
  }

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <span className="surface-label">{formatWindowLabel(phase.target_window_weeks, lang)}</span>
        <div className="text-sm font-medium text-white">{phase.phase_title}</div>
      </div>
      <div className="grid gap-4">
        {phase.steps.map((step) => (
          <ActionCard key={`${phase.phase_id}-${step.step_id ?? step.action_key}`} phase={phase} step={step} />
        ))}
      </div>
    </section>
  );
}
