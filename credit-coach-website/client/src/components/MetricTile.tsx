type MetricTileProps = {
  label: string;
  value: string;
  hint?: string;
  change?: string;
};

export function MetricTile({ label, value, hint, change }: MetricTileProps) {
  return (
    <div className="panel h-full p-5">
      <div className="text-xs uppercase tracking-[0.18em] text-arctic/60">{label}</div>
      <div className="mt-3 font-display text-3xl font-semibold text-white">{value}</div>
      {change ? (
        <div className="mt-2 inline-flex rounded-full bg-signal/10 px-2.5 py-1 text-xs font-semibold text-signal">
          {change}
        </div>
      ) : null}
      {hint ? <div className="mt-3 text-sm leading-6 text-slate-400">{hint}</div> : null}
    </div>
  );
}
