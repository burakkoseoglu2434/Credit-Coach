import { useLanguage } from "@/i18n/language";
import {
  formatActionClass,
  formatActionDetail,
  formatActionTitle,
  formatOfferType,
  formatPdPercent,
  formatPhaseTitle,
  formatWindowLabel,
  pickLocalizedText,
} from "@/lib/demo-formatters";

type RoadmapStep = {
  step_id?: string;
  action_key: string;
  action_class: string;
  action_title: string;
  detail: string;
  time_months: number;
  estimated_cost_usd: number;
  plan_execution_probability?: number;
  offer_type?: string;
  narrative?: {
    step_id?: string;
    phase_id?: string;
    action_key?: string | null;
    action_group_id?: string | null;
    action_summary: { tr: string; en: string };
    why_this_matters: { tr: string; en: string };
    expected_outcome: { tr: string; en: string };
    what_happens_if_done: { tr: string; en: string };
    what_happens_if_not_done: { tr: string; en: string };
    action_timing_hint?: { tr: string; en: string };
    offer_narrative?: {
      offer_explanation: { tr: string; en: string };
      why_offered: { tr: string; en: string };
      if_accepted: { tr: string; en: string };
      if_not_accepted: { tr: string; en: string };
      offer_terms_summary?: { tr: string; en: string };
    } | null;
  };
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

function phaseNarrative(
  phaseId: string,
  lang: "tr" | "en",
): {
  summary: string;
  why: string;
  focus: string;
  focusHint: string;
} {
  const content: Record<
    string,
    {
      summary: { tr: string; en: string };
      why: { tr: string; en: string };
      focus: { tr: string; en: string };
      focusHint: { tr: string; en: string };
    }
  > = {
    phase_1_stabilize: {
      summary: {
        tr: "Bu pencere, yeni baski yaratmadan odeme davranisini istikrara almak icin kullanilir.",
        en: "This window is used to stabilize repayment behavior without creating new pressure.",
      },
      why: {
        tr: "Kurumsal ekip once dususu durdurmak ister; daha guclu teklifler ve yeniden basvuru adimlari bunun uzerine kurulur.",
        en: "Institutional teams first want to stop further deterioration; stronger offers and re-application steps build on that base.",
      },
      focus: {
        tr: "Faz odagi",
        en: "Phase focus",
      },
      focusHint: {
        tr: "Ilk 4 haftada amac yeni risk yaratmamak ve dosyayi kontrollu toparlanmaya almak.",
        en: "In the first 4 weeks, the goal is to avoid new risk and move the file into controlled recovery.",
      },
    },
    phase_2_build: {
      summary: {
        tr: "Bu pencere, ilk istikrari krediye hazir bir dosya gorunumune cevirmeye odaklanir.",
        en: "This window turns early stability into a cleaner approval-ready file.",
      },
      why: {
        tr: "Burada kazanilan duzen, hem yeniden degerlendirme hem de kurum tekliflerinin zamanlamasi icin ana sinyali uretir.",
        en: "The consistency earned here becomes the main signal for reassessment and for timing institution-side offers.",
      },
      focus: {
        tr: "Faz odagi",
        en: "Phase focus",
      },
      focusHint: {
        tr: "4-12. haftalarda hedef, guveni geri getirecek temiz bir odeme ve davranis paterni olusturmak.",
        en: "Across weeks 4-12, the target is to build a clean repayment pattern that restores confidence.",
      },
    },
    phase_3_optimize: {
      summary: {
        tr: "Bu pencere, elde edilen iyilesmeyi kalici hale getirip sonraki karar pencerelerini korur.",
        en: "This window makes the improvement durable and protects later decision windows.",
      },
      why: {
        tr: "Kisa vadeli toparlanma kalici hale gelmezse guven hizla geri kaybolur; bu faz kaliciligi guclendirir.",
        en: "If short-term recovery does not hold, confidence erodes quickly; this phase protects durability.",
      },
      focus: {
        tr: "Faz odagi",
        en: "Phase focus",
      },
      focusHint: {
        tr: "12-24. haftalarda onceki kazanimlari bozmayacak sekilde profilin guclu hali korunur.",
        en: "Across weeks 12-24, the stronger profile is protected so earlier gains are not lost.",
      },
    },
  };

  const selected = content[phaseId];

  if (!selected) {
    return {
      summary: lang === "tr" ? "Bu pencere kontrollu ilerleme uretir." : "This window is designed to create controlled progress.",
      why:
        lang === "tr"
          ? "Kurumsal ekipler bir sonraki karar penceresini daha guvenli hale getirmek ister."
          : "Institutional teams want to make the next decision window safer.",
      focus: lang === "tr" ? "Faz odagi" : "Phase focus",
      focusHint:
        lang === "tr"
          ? "Bu faz, mevcut iyilesmeyi koruyarak sonraki checkpoint'e hazir kalmayi hedefler."
          : "This phase protects the current improvement and keeps the file ready for the next checkpoint.",
    };
  }

  return {
    summary: selected.summary[lang],
    why: selected.why[lang],
    focus: selected.focus[lang],
    focusHint: selected.focusHint[lang],
  };
}

function fallbackExpectedOutcome(phaseId: string, lang: "tr" | "en") {
  const labels: Record<string, { tr: string; en: string }> = {
    phase_1_stabilize: {
      tr: "Yeni gecikme yaratmadan dosya sakinlesir.",
      en: "The file steadies without adding new delinquency pressure.",
    },
    phase_2_build: {
      tr: "Profil yeniden degerlendirmeye daha yakin hale gelir.",
      en: "The profile moves closer to reassessment readiness.",
    },
    phase_3_optimize: {
      tr: "Ilerlemenin kalici hale gelme olasiligi artar.",
      en: "The improvement becomes more likely to hold.",
    },
  };

  return (labels[phaseId] ?? { tr: "Beklenen iyilesme korunur.", en: "Expected improvement is preserved." })[lang];
}

function fallbackTimingHint(phaseId: string, lang: "tr" | "en") {
  const labels: Record<string, { tr: string; en: string }> = {
    phase_1_stabilize: {
      tr: "Bu adimlar ilk 4 haftada disiplin olusturacak sekilde uygulanmali.",
      en: "These actions should land within the first 4 weeks to create early discipline.",
    },
    phase_2_build: {
      tr: "Bu pencere boyunca temiz sinyal kesintisiz korunmali.",
      en: "The cleaner signal should stay uninterrupted through this window.",
    },
    phase_3_optimize: {
      tr: "Bu faz, onceki ilerlemeyi koruyacak sekilde daha istikrarli bir ritim ister.",
      en: "This phase requires a steadier rhythm that protects the earlier progress.",
    },
  };

  return (labels[phaseId] ?? { tr: "Bu pencere icinde planli sekilde ilerleyin.", en: "Advance in a planned way within this window." })[lang];
}

export function RoadmapPhaseCard({ phase }: RoadmapPhaseCardProps) {
  const { text, lang } = useLanguage();
  const narrative = phaseNarrative(phase.phase_id, lang);

  return (
    <div className="panel-product p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-3xl">
          <div className="surface-label">{formatWindowLabel(phase.target_window_weeks, lang)}</div>
          <div className="mt-3 font-display text-2xl font-semibold text-white">
            {formatPhaseTitle(phase.phase_id, phase.phase_title, lang)}
          </div>
          <p className="mt-3 text-sm leading-7 text-slate-300">{narrative.summary}</p>
        </div>
        <div className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-arctic/75">
          {text({ tr: "Faz bazli yol haritasi", en: "Phase-based roadmap" })}
        </div>
      </div>

      <div className="mt-6 rounded-[24px] border border-white/10 bg-white/[0.03] p-5">
        <div className="surface-label">{text({ tr: "Neden onemli", en: "Why this matters" })}</div>
        <p className="mt-3 text-sm leading-7 text-slate-300">{narrative.why}</p>
      </div>

      <div className="mt-6 grid gap-4">
        {phase.steps.length === 0 ? (
          <div className="rounded-[24px] border border-dashed border-white/10 bg-white/[0.03] p-5">
            <div className="surface-label">{narrative.focus}</div>
            <div className="mt-3 font-medium text-white">
              {text({
                tr: "Bu pencerede yeni bir urun adimindan cok mevcut ilerleme korunur.",
                en: "This window is about protecting the progress already earned rather than adding a new product move.",
              })}
            </div>
            <p className="mt-2 text-sm leading-7 text-slate-300">{narrative.focusHint}</p>
          </div>
        ) : null}

        {phase.steps.map((step) => (
          <div
            key={`${phase.phase_id}-${step.step_id ?? step.action_key}`}
            className="rounded-[24px] border border-white/10 bg-white/[0.03] p-5"
          >
            <div className="flex flex-wrap gap-2">
              <span className="surface-label">{formatActionClass(step.action_class, lang)}</span>
              {step.offer_type ? (
                <span className="surface-label border-signal/20 bg-signal/10 text-signal">
                  {formatOfferType(step.offer_type, lang)}
                </span>
              ) : null}
            </div>

            <div className="mt-4 font-medium text-white">
              {step.narrative
                ? pickLocalizedText(step.narrative.action_summary, lang)
                : formatActionTitle(step.action_title, lang)}
            </div>
            <p className="mt-2 text-sm leading-7 text-slate-300">
              {step.narrative
                ? pickLocalizedText(step.narrative.why_this_matters, lang)
                : formatActionDetail(step.detail, lang)}
            </p>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="rounded-[20px] border border-white/10 bg-slate-950/40 p-4">
                <div className="text-[11px] uppercase tracking-[0.16em] text-arctic/60">
                  {text({ tr: "Beklenen sonuc", en: "Expected outcome" })}
                </div>
                <div className="mt-2 text-sm leading-6 text-slate-300">
                  {step.narrative
                    ? pickLocalizedText(step.narrative.expected_outcome, lang)
                    : fallbackExpectedOutcome(phase.phase_id, lang)}
                </div>
              </div>
              <div className="rounded-[20px] border border-white/10 bg-slate-950/40 p-4">
                <div className="text-[11px] uppercase tracking-[0.16em] text-arctic/60">
                  {text({ tr: "Yonetim ritmi", en: "Execution rhythm" })}
                </div>
                <div className="mt-2 text-sm leading-6 text-slate-300">
                  {step.narrative?.action_timing_hint
                    ? pickLocalizedText(step.narrative.action_timing_hint, lang)
                    : fallbackTimingHint(phase.phase_id, lang)}
                </div>
              </div>
            </div>

            {step.narrative?.offer_narrative ? (
              <div className="mt-4 rounded-[20px] border border-signal/20 bg-signal/5 p-4">
                <div className="surface-label border-signal/20 bg-signal/10 text-signal">
                  {text({ tr: "Teklif anlatimi", en: "Offer narrative" })}
                </div>
                <div className="mt-3 font-medium text-white">
                  {pickLocalizedText(step.narrative.offer_narrative.offer_explanation, lang)}
                </div>
                <p className="mt-2 text-sm leading-7 text-slate-300">
                  {pickLocalizedText(step.narrative.offer_narrative.why_offered, lang)}
                </p>
                {step.narrative.offer_narrative.offer_terms_summary ? (
                  <div className="mt-3 rounded-[18px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-300">
                    {pickLocalizedText(step.narrative.offer_narrative.offer_terms_summary, lang)}
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        ))}
      </div>

      <details className="detail-panel mt-6 px-5 py-4 text-sm text-slate-300">
        <summary className="cursor-pointer list-none font-semibold text-white">
          {text({ tr: "Teknik detaylari goster", en: "Show technical details" })}
        </summary>
        <div className="mt-4 grid gap-4">
          <div className="rounded-[20px] border border-white/10 bg-slate-950/35 p-4">
            <div className="surface-label">{text({ tr: "Faz detayi", en: "Phase detail" })}</div>
            <div className="mt-3 grid gap-2 text-sm text-slate-400">
              <div>
                {text({ tr: "Ham faz basligi", en: "Raw phase title" })}:{" "}
                <span className="text-white">{phase.phase_title}</span>
              </div>
              <div>
                {text({ tr: "Hedef pencere", en: "Target window" })}:{" "}
                <span className="text-white">{phase.target_window_weeks}</span>
              </div>
              <div>
                {text({ tr: "Hedef PD", en: "Target PD" })}:{" "}
                <span className="text-white">{formatPdPercent(phase.target_pd, lang)}</span>
              </div>
            </div>
          </div>

          {phase.steps.map((step) => (
            <div
              key={`${phase.phase_id}-${step.step_id ?? step.action_key}-technical`}
              className="rounded-[20px] border border-white/10 bg-slate-950/35 p-4"
            >
              <div className="surface-label">{text({ tr: "Adim detayi", en: "Step detail" })}</div>
              <div className="mt-3 grid gap-2 text-sm text-slate-400">
                <div>
                  {text({ tr: "Ham baslik", en: "Raw title" })}:{" "}
                  <span className="text-white">{formatActionTitle(step.action_title, lang)}</span>
                </div>
                <div>
                  {text({ tr: "Ham detay", en: "Raw detail" })}:{" "}
                  <span className="text-white">{formatActionDetail(step.detail, lang)}</span>
                </div>
                <div>
                  {text({ tr: "Action key", en: "Action key" })}:{" "}
                  <span className="text-white">{step.action_key}</span>
                </div>
                <div>
                  {text({ tr: "Ham sinif", en: "Raw class" })}:{" "}
                  <span className="text-white">{step.action_class}</span>
                </div>
                <div>
                  {text({ tr: "Sure", en: "Duration" })}:{" "}
                  <span className="text-white">
                    {step.time_months} {text({ tr: "ay", en: "months" })}
                  </span>
                </div>
                <div>
                  {text({ tr: "Tahmini maliyet", en: "Estimated cost" })}:{" "}
                  <span className="text-white">${step.estimated_cost_usd}</span>
                </div>
                <div>
                  {text({ tr: "Plan gerceklesme olasiligi", en: "Plan execution probability" })}:{" "}
                  <span className="text-white">
                    {step.plan_execution_probability !== undefined
                      ? `${Math.round(step.plan_execution_probability * 100)}%`
                      : text({ tr: "yok", en: "n/a" })}
                  </span>
                </div>
                {step.offer_type ? (
                  <div>
                    {text({ tr: "Teklif tipi", en: "Offer type" })}:{" "}
                    <span className="text-white">{formatOfferType(step.offer_type, lang)}</span>
                  </div>
                ) : null}
                {step.narrative ? (
                  <>
                    <div>
                      {text({ tr: "Tamamlanirsa", en: "If completed" })}:{" "}
                      <span className="text-white">
                        {pickLocalizedText(step.narrative.what_happens_if_done, lang)}
                      </span>
                    </div>
                    <div>
                      {text({ tr: "Atlanirsa", en: "If skipped" })}:{" "}
                      <span className="text-white">
                        {pickLocalizedText(step.narrative.what_happens_if_not_done, lang)}
                      </span>
                    </div>
                  </>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}
