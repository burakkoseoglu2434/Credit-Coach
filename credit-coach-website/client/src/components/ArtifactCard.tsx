type ArtifactCardProps = {
  name: string;
  description: string;
  type: string;
};

export function ArtifactCard({ name, description, type }: ArtifactCardProps) {
  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between gap-4">
        <div className="font-display text-lg font-semibold text-white">{name}</div>
        <div className="rounded-full border border-cobalt/30 bg-cobalt/10 px-2.5 py-1 text-[11px] uppercase tracking-[0.2em] text-arctic">
          {type}
        </div>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
    </div>
  );
}
