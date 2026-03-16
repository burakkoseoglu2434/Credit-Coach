type MetricTileProps = {
  label: string;
  value: string;
  hint?: string;
  change?: string;
  context?: string;
};

export function MetricTile({ label, value, hint, change, context }: MetricTileProps) {
  return (
    <div className="panel h-full p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="text-xs uppercase tracking-[0.18em] text-arctic/60">{label}</div>
        {context ? (
          <div className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-arctic/75">
            {context}
          </div>
        ) : null}
      </div>
      <div className="mt-3 font-display text-3xl font-semibold text-white">{value}</div>
      {change ? (
        <div className="mt-2 inline-flex rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-semibold text-arctic/80">
          {change}
        </div>
      ) : null}
      {hint ? <div className="mt-3 text-sm leading-6 text-slate-400">{hint}</div> : null}
    </div>
  );
}
