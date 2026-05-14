type BadgeProps = {
  value?: string | null;
  tone?: "neutral" | "blue" | "green" | "amber" | "red" | "purple";
};

const toneClasses: Record<NonNullable<BadgeProps["tone"]>, string> = {
  neutral: "bg-slate-100 text-slate-700 border-slate-200",
  blue: "bg-cyan-50 text-cyan-700 border-cyan-200",
  green: "bg-emerald-50 text-emerald-700 border-emerald-200",
  amber: "bg-amber-50 text-amber-800 border-amber-200",
  red: "bg-rose-50 text-rose-700 border-rose-200",
  purple: "bg-violet-50 text-violet-700 border-violet-200"
};

export function Badge({ value, tone = "neutral" }: BadgeProps) {
  if (!value) return <span className="text-sm text-slate-400">Unclassified</span>;
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-1 text-xs font-semibold capitalize ${toneClasses[tone]} shadow-sm`}
    >
      {value.replace("_", " ")}
    </span>
  );
}

export function toneForPriority(priority?: string | null): BadgeProps["tone"] {
  if (priority === "urgent") return "red";
  if (priority === "high") return "amber";
  if (priority === "medium") return "blue";
  return "green";
}

export function toneForSentiment(sentiment?: string | null): BadgeProps["tone"] {
  if (sentiment === "angry") return "red";
  if (sentiment === "frustrated") return "amber";
  if (sentiment === "positive") return "green";
  return "neutral";
}

export function toneForStatus(status?: string | null): BadgeProps["tone"] {
  if (status === "resolved") return "green";
  if (status === "waiting_human") return "amber";
  if (status === "triaged") return "blue";
  return "neutral";
}
