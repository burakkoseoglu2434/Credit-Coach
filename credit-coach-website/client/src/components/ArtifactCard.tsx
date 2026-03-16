type ArtifactCardProps = {
  name: string;
  description: string;
};

export function ArtifactCard({ name, description }: ArtifactCardProps) {
  return (
    <div className="panel p-5">
      <div className="font-display text-lg font-semibold text-white">{name}</div>
      <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
    </div>
  );
}
