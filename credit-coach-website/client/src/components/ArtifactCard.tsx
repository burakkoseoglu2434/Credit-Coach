import { FeatureIcon, type FeatureIconName } from "./FeatureIcon";

type ArtifactCardProps = {
  name: string;
  description: string;
  icon?: FeatureIconName;
};

export function ArtifactCard({ name, description, icon = "proof" }: ArtifactCardProps) {
  return (
    <div className="panel p-5">
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-midnight/45 text-arctic">
          <FeatureIcon name={icon} />
        </div>
        <div>
          <div className="font-display text-lg font-semibold text-white">{name}</div>
          <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
        </div>
      </div>
    </div>
  );
}
