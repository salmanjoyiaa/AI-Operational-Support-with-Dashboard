import { Inbox } from "lucide-react";

type EmptyStateProps = {
  title: string;
  message: string;
};

export function EmptyState({ title, message }: EmptyStateProps) {
  return (
    <div className="card-surface flex min-h-56 flex-col items-center justify-center px-6 py-10 text-center">
      <Inbox className="h-9 w-9 text-slate-400" aria-hidden="true" />
      <h3 className="mt-4 text-base font-semibold text-slate-900">{title}</h3>
      <p className="mt-2 max-w-md text-sm text-slate-500">{message}</p>
    </div>
  );
}
