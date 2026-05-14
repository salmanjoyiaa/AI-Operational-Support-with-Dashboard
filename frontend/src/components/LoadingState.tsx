export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="card-surface grid min-h-56 place-items-center">
      <div className="flex items-center gap-3 text-sm font-medium text-slate-500">
        <span className="h-3 w-3 animate-pulse rounded-full bg-cyan-500" />
        {label}
      </div>
    </div>
  );
}
