type MetricTileProps = {
  label: string;
  value: string;
  hint?: string;
  change?: string;
  context?: string;
  variant?: "default" | "product";
  className?: string;
  valueClassName?: string;
};

export function MetricTile({
  label,
  value,
  hint,
  change,
  context,
  variant = "default",
  className,
  valueClassName,
}: MetricTileProps) {
  const isProduct = variant === "product";

  return (
    <div
      className={`${isProduct ? "panel-product" : "panel"} h-full p-5${className ? ` ${className}` : ""}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div
          className={
            isProduct
              ? "text-[11px] uppercase tracking-[0.16em] text-arctic/55"
              : "text-xs uppercase tracking-[0.18em] text-arctic/60"
          }
        >
          {label}
        </div>
        {context ? (
          <div
            className={
              isProduct
                ? "surface-label border-white/12 bg-white/[0.04] text-arctic/80"
                : "rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-arctic/75"
            }
          >
            {context}
          </div>
        ) : null}
      </div>
      <div
        className={`mt-3 font-display font-semibold text-white ${
          isProduct ? "text-[1.85rem] leading-tight sm:text-[2rem]" : "text-3xl"
        }${valueClassName ? ` ${valueClassName}` : ""}`}
      >
        {value}
      </div>
      {change ? (
        <div className="mt-2 inline-flex rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-semibold text-arctic/80">
          {change}
        </div>
      ) : null}
      {hint ? <div className="mt-3 text-sm leading-6 text-slate-400">{hint}</div> : null}
    </div>
  );
}
