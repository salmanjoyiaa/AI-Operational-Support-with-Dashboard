type MiniBarChartProps = {
  data: Record<string, number>;
  maxItems?: number;
};

const colors = ["bg-cyan-500", "bg-emerald-500", "bg-amber-500", "bg-rose-500", "bg-violet-500"];

export function MiniBarChart({ data, maxItems = 6 }: MiniBarChartProps) {
  const items = Object.entries(data)
    .sort((a, b) => b[1] - a[1])
    .slice(0, maxItems);
  const max = Math.max(...items.map(([, value]) => value), 1);

  return (
    <div className="space-y-4">
      {items.map(([label, value], index) => (
        <div key={label}>
          <div className="mb-1 flex items-center justify-between gap-3 text-sm">
            <span className="font-medium capitalize text-slate-700">{label.replace("_", " ")}</span>
            <span className="text-slate-500">{value}</span>
          </div>
          <div className="h-2 overflow-hidden rounded bg-slate-100">
            <div
              className={`h-full rounded ${colors[index % colors.length]}`}
              style={{ width: `${Math.max((value / max) * 100, 8)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
