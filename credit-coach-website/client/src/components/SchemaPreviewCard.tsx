import { FeatureIcon, type FeatureIconName } from "./FeatureIcon";

type SchemaPreviewCardProps = {
  title: string;
  description: string;
  icon?: FeatureIconName;
  tone?: "blue" | "green" | "amber";
};

const toneClasses = {
  blue: "from-cobalt/20 to-ocean/10 border-cobalt/20",
  green: "from-signal/15 to-emerald-400/5 border-signal/20",
  amber: "from-copper/15 to-yellow-300/5 border-copper/20",
};

export function SchemaPreviewCard({
  title,
  description,
  icon = "platform",
  tone = "blue",
}: SchemaPreviewCardProps) {
  return (
    <div
      className={`panel overflow-hidden border bg-gradient-to-br p-6 ${toneClasses[tone]}`}
    >
      <div className="flex items-start gap-4">
        <div className="mt-1 flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-midnight/40 text-arctic">
          <FeatureIcon name={icon} />
        </div>
        <div>
          <div className="font-display text-2xl font-semibold text-white">{title}</div>
          <p className="mt-3 max-w-md text-sm leading-7 text-slate-300">{description}</p>
        </div>
      </div>
      <div className="mt-6 grid gap-3">
        <div className="h-2 rounded-full bg-white/10" />
        <div className="h-2 w-4/5 rounded-full bg-white/10" />
        <div className="h-2 w-3/5 rounded-full bg-white/10" />
      </div>
    </div>
  );
}
