type ComparisonBarProps = {
  label: string;
  value: number;
  color?: "blue" | "green" | "amber";
  formatter?: (value: number) => string;
};

const colorMap = {
  blue: "from-cobalt to-arctic",
  green: "from-signal to-emerald-300",
  amber: "from-copper to-yellow-300",
};

export function ComparisonBar({
  label,
  value,
  color = "blue",
  formatter = (input) => `${Math.round(input * 100)}%`,
}: ComparisonBarProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-300">{label}</span>
        <span className="font-medium text-white">{formatter(value)}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/10">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${colorMap[color]}`}
          style={{ width: `${Math.max(6, Math.min(100, value * 100))}%` }}
        />
      </div>
    </div>
  );
}
