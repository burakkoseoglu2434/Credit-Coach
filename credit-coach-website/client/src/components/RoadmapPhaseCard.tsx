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

type MonthlyGuidanceItem = {
  month: number;
  title: string;
  detail: string;
};

function phaseMonths(phaseId: string) {
  if (phaseId === "phase_1_stabilize") {
    return [1];
  }
  if (phaseId === "phase_2_build") {
    return [2, 3];
  }
  return [4, 5, 6];
}

function buildPhaseGuidance(
  phaseId: string,
  lang: "tr" | "en",
): MonthlyGuidanceItem[] {
  if (phaseId === "phase_1_stabilize") {
    return [
      {
        month: 1,
        title:
          lang === "tr"
            ? "Nakit akisini dengede tut"
            : "Protect short-term cash flow",
        detail:
          lang === "tr"
            ? "Yeni gecikme yaratmadan minimum odemeleri zamaninda tamamla ve kart kullanimini yukari cekme."
            : "Keep payments current, avoid fresh delinquencies, and do not add new card pressure.",
      },
    ];
  }

  if (phaseId === "phase_2_build") {
    return [
      {
        month: 2,
        title:
          lang === "tr"
            ? "Temiz odeme duzenini baslat"
            : "Start a clean payment streak",
        detail:
          lang === "tr"
            ? "Tum odemeleri son gune birakmadan tamamla ve kredi davranisini istikrara al."
            : "Complete every payment on time and begin rebuilding a cleaner repayment pattern.",
      },
      {
        month: 3,
        title:
          lang === "tr"
            ? "Yeniden basvuru guvenini guclendir"
            : "Rebuild approval confidence",
        detail:
          lang === "tr"
            ? "Temiz odeme serisini koru, yeni bakiye baskisi yaratma ve yeniden degerlendirme icin dosyayi hazir tut."
            : "Maintain the payment streak, avoid new balance stress, and keep the file ready for reassessment.",
      },
    ];
  }

  return [
    {
      month: 4,
      title:
        lang === "tr"
          ? "Kazanilan istikrari koru"
          : "Protect the stability gained",
      detail:
        lang === "tr"
          ? "Son checkpoint sonrasi odeme disiplini bozulmadan devam etmeli."
          : "Keep the payment discipline intact after the positive review checkpoint.",
    },
    {
      month: 5,
      title:
        lang === "tr"
          ? "Yeni risk yaratma"
          : "Avoid introducing new risk",
      detail:
        lang === "tr"
          ? "Yeni kredi baskisi, limit kullanimi veya gecikme olusturacak adimlardan kacin."
          : "Avoid new borrowing pressure, utilization spikes, or late-payment behavior.",
    },
    {
      month: 6,
      title:
        lang === "tr"
          ? "Kalici uygunlugu guclendir"
          : "Lock in durable readiness",
      detail:
        lang === "tr"
          ? "Profilin guclu halini koruyarak bir sonraki karar penceresine hazir kal."
          : "Hold the stronger profile in place so the next decision window stays favorable.",
    },
  ];
}

function buildStepGuidance(
  phaseId: string,
  step: RoadmapStep,
  lang: "tr" | "en",
): MonthlyGuidanceItem[] {
  const months = phaseMonths(phaseId);

  const plans: Record<string, MonthlyGuidanceItem[]> = {
    improve_payment_consistency: [
      {
        month: months[0] ?? 1,
        title:
          lang === "tr"
            ? "Tum odemeleri zamaninda kapat"
            : "Keep every payment on time",
        detail:
          lang === "tr"
            ? "Minimum odemeleri geciktirmeden tamamla ve hesap hareketlerinde yeni bir zayiflik yaratma."
            : "Clear all minimum payments on time and avoid any new negative payment signal.",
      },
      {
        month: months[1] ?? months[0] ?? 1,
        title:
          lang === "tr"
            ? "Temiz seriyi surdur"
            : "Extend the clean streak",
        detail:
          lang === "tr"
            ? "Iki ay ust uste duzenli odeme davranisi gostererek kredi veren guvenini yeniden kur."
            : "Create a second month of steady payment behavior to rebuild lender confidence.",
      },
    ],
    refinance: [
      {
        month: months[0] ?? 1,
        title:
          lang === "tr"
            ? "Yeniden yapilandirma seceneklerini topla"
            : "Collect restructuring options",
        detail:
          lang === "tr"
            ? "Mevcut borc yapisini ve alternatif kosullari karsilastir; yalnizca aylik baskiyi gercekten azaltan secenekleri ayir."
            : "Compare the current debt burden with realistic restructuring options that truly lower monthly pressure.",
      },
      {
        month: months[1] ?? months[0] ?? 1,
        title:
          lang === "tr"
            ? "Daha guclu kosula gec"
            : "Move to the stronger structure",
        detail:
          lang === "tr"
            ? "Ilk sinyal guclu ise daha yonetilebilir taksit ve faiz kosuluna gecis yap."
            : "If the early signal holds, move into the structure with safer installment and rate pressure.",
      },
    ],
    debt_consolidation: [
      {
        month: months[0] ?? 1,
        title:
          lang === "tr"
            ? "Daginik borc baskisini cikar"
            : "Map the fragmented debt pressure",
        detail:
          lang === "tr"
            ? "Yuksek maliyetli donen borclari belirle ve hangilerinin once tasinacagini netlestir."
            : "Identify the highest-pressure revolving balances and decide which ones should move first.",
      },
      {
        month: months[1] ?? months[0] ?? 1,
        title:
          lang === "tr"
            ? "Borcu daha surdurulebilir yapiya tasi"
            : "Move debt into a more durable structure",
        detail:
          lang === "tr"
            ? "Uygun bakiyeleri daha istikrarli geri odeme duzenine alarak profil baskisini azalt."
            : "Shift eligible balances into a steadier repayment structure to reduce profile stress.",
      },
    ],
    credit_limit_adjustment: [
      {
        month: months[0] ?? 1,
        title:
          lang === "tr"
            ? "Limit rahatlama potansiyelini olc"
            : "Assess utilization relief potential",
        detail:
          lang === "tr"
            ? "Limit ayarlamasinin kullanim oranini anlamli sekilde rahatlatip rahatlatmayacagini netlestir."
            : "Confirm whether a limit adjustment would materially improve utilization headroom.",
      },
      {
        month: months[1] ?? months[0] ?? 1,
        title:
          lang === "tr"
            ? "Uygunsa kontrollu sekilde devreye al"
            : "Use it only if it helps materially",
        detail:
          lang === "tr"
            ? "Yalnizca gercek fayda yaratiyorsa kurum tarafli limit hamlesini uygulamaya al."
            : "Only activate the lender-side limit move if it clearly improves the customer profile.",
      },
    ],
  };

  return plans[step.action_key] ?? [
    {
      month: months[0] ?? 1,
      title:
        lang === "tr"
          ? "Ilk adimi uygula"
          : "Take the first move",
      detail:
        lang === "tr"
          ? "Bu adimi ilk uygun ay icinde hayata gecir ve etkisini ilk checkpoint'e tasiyacak sekilde takip et."
          : "Apply this move in the earliest suitable month and track it into the next checkpoint.",
    },
    {
      month: months[1] ?? months[0] ?? 1,
      title:
        lang === "tr"
          ? "Etkisini kalici hale getir"
          : "Turn the effect into a stable signal",
      detail:
        lang === "tr"
          ? "Ilk etkiyi bozmayacak sekilde davranisi surdur ve sonraki karar penceresine hazir kal."
          : "Sustain the first improvement so it remains visible in the next decision window.",
    },
  ];
}

export function RoadmapPhaseCard({ phase }: RoadmapPhaseCardProps) {
  const { text, lang } = useLanguage();
  const emptyPhaseGuidance = buildPhaseGuidance(phase.phase_id, lang);

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
            {formatPdPercent(phase.target_pd, lang)}
          </div>
          <div className="mt-1 text-sm text-slate-400">
            {formatWindowLabel(phase.target_window_weeks, lang)}
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-4">
        {phase.steps.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-white/10 bg-white/[0.03] p-4 text-sm leading-6 text-slate-300">
            {text({
              tr: "Bu fazda yeni bir aksiyon yerine profilin istikrarini korumak ve sonraki kontrol noktasina hazir kalmak onerilir.",
              en: "This phase focuses on preserving stability and staying ready for the next review checkpoint rather than adding a new action.",
            })}
            <div className="mt-4 grid gap-3">
              {emptyPhaseGuidance.map((item) => (
                <div
                  key={`${phase.phase_id}-guidance-${item.month}`}
                  className="rounded-2xl border border-white/10 bg-white/[0.04] p-3"
                >
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-arctic/70">
                    {text({ tr: "Ay", en: "Month" })} {item.month}
                  </div>
                  <div className="mt-1 font-medium text-white">{item.title}</div>
                  <div className="mt-1 text-sm text-slate-400">{item.detail}</div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
        {phase.steps.map((step) => (
          <div
            key={`${phase.phase_id}-${step.step_id ?? step.action_key}`}
            className="rounded-3xl border border-white/10 bg-white/4 p-4"
          >
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
              {step.narrative
                ? pickLocalizedText(step.narrative.action_summary, lang)
                : formatActionTitle(step.action_title, lang)}
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              {step.narrative
                ? pickLocalizedText(step.narrative.why_this_matters, lang)
                : formatActionDetail(step.detail, lang)}
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
              {step.narrative?.action_timing_hint ? (
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5">
                  {pickLocalizedText(step.narrative.action_timing_hint, lang)}
                </span>
              ) : null}
            </div>
            {step.narrative ? (
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-arctic/60">
                    {text({ tr: "Beklenen sonuc", en: "Expected outcome" })}
                  </div>
                  <div className="mt-2 text-sm leading-6 text-slate-300">
                    {pickLocalizedText(step.narrative.expected_outcome, lang)}
                  </div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-arctic/60">
                    {text({ tr: "Yapilirsa", en: "If completed" })}
                  </div>
                  <div className="mt-2 text-sm leading-6 text-slate-300">
                    {pickLocalizedText(step.narrative.what_happens_if_done, lang)}
                  </div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-arctic/60">
                    {text({ tr: "Yapilmazsa", en: "If skipped" })}
                  </div>
                  <div className="mt-2 text-sm leading-6 text-slate-300">
                    {pickLocalizedText(step.narrative.what_happens_if_not_done, lang)}
                  </div>
                </div>
              </div>
            ) : null}
            {step.narrative?.offer_narrative ? (
              <div className="mt-4 rounded-2xl border border-signal/20 bg-signal/5 p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-signal/80">
                  {text({ tr: "Teklif anlatimi", en: "Offer narrative" })}
                </div>
                <div className="mt-2 font-medium text-white">
                  {pickLocalizedText(step.narrative.offer_narrative.offer_explanation, lang)}
                </div>
                <div className="mt-2 text-sm leading-6 text-slate-300">
                  {pickLocalizedText(step.narrative.offer_narrative.why_offered, lang)}
                </div>
                {step.narrative.offer_narrative.offer_terms_summary ? (
                  <div className="mt-3 rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-slate-300">
                    {pickLocalizedText(step.narrative.offer_narrative.offer_terms_summary, lang)}
                  </div>
                ) : null}
              </div>
            ) : null}
            <div className="mt-4 rounded-2xl border border-white/10 bg-midnight/25 p-4">
              <div className="text-xs uppercase tracking-[0.18em] text-arctic/60">
                {text({ tr: "Ay ay plan", en: "Month-by-month plan" })}
              </div>
              <div className="mt-3 grid gap-3">
                {buildStepGuidance(phase.phase_id, step, lang).map((item) => (
                  <div
                    key={`${phase.phase_id}-${step.action_key}-month-${item.month}`}
                    className="rounded-2xl border border-white/10 bg-white/[0.03] p-3"
                  >
                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-arctic/70">
                      {text({ tr: "Ay", en: "Month" })} {item.month}
                    </div>
                    <div className="mt-1 font-medium text-white">{item.title}</div>
                    <div className="mt-1 text-sm text-slate-400">{item.detail}</div>
                  </div>
                ))}
              </div>
            </div>
            <details className="mt-4 rounded-2xl border border-white/10 bg-midnight/35 px-4 py-3 text-sm text-slate-300">
              <summary className="cursor-pointer list-none font-medium text-arctic">
                {text({ tr: "Teknik detaylar", en: "Technical details" })}
              </summary>
              <div className="mt-3 grid gap-2 text-sm text-slate-400">
                {step.narrative ? (
                  <>
                    <div>
                      {text({ tr: "Ham baslik", en: "Raw title" })}:{" "}
                      <span className="text-white">{formatActionTitle(step.action_title, lang)}</span>
                    </div>
                    <div>
                      {text({ tr: "Ham detay", en: "Raw detail" })}:{" "}
                      <span className="text-white">{formatActionDetail(step.detail, lang)}</span>
                    </div>
                  </>
                ) : null}
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
