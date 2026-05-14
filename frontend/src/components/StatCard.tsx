import type { LucideIcon } from "lucide-react";

type StatCardProps = {
  label: string;
  value: string | number;
  detail?: string;
  icon: LucideIcon;
  accent?: "cyan" | "emerald" | "amber" | "rose";
};

const accentClasses = {
  cyan: "bg-cyan-50 text-cyan-700",
  emerald: "bg-emerald-50 text-emerald-700",
  amber: "bg-amber-50 text-amber-700",
  rose: "bg-rose-50 text-rose-700"
};

export function StatCard({ label, value, detail, icon: Icon, accent = "cyan" }: StatCardProps) {
  return (
    <section className="card-surface">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">{value}</p>
        </div>
        <div className={`rounded p-2 shadow-sm ${accentClasses[accent]}`}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      </div>
      {detail ? <p className="mt-4 text-sm text-slate-500">{detail}</p> : null}
    </section>
  );
}
