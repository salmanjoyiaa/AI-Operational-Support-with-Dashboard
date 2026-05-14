import { useEffect, useState } from "react";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { MiniBarChart } from "../components/MiniBarChart";
import { api } from "../lib/api";
import type { AnalyticsOverview } from "../types/api";

export function Analytics() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getAnalytics()
      .then(setAnalytics)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState label="Loading analytics" />;
  if (error) return <EmptyState title="Analytics unavailable" message={error} />;
  if (!analytics) return null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-950">Analytics</h1>
        <p className="mt-1 text-sm text-slate-500">Operational metrics and issue trends</p>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <section className="rounded border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-slate-950">Priority distribution</h2>
          <div className="mt-5">
            <MiniBarChart data={analytics.priority_distribution} />
          </div>
        </section>
        <section className="rounded border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-slate-950">Sentiment distribution</h2>
          <div className="mt-5">
            <MiniBarChart data={analytics.sentiment_distribution} />
          </div>
        </section>
        <section className="rounded border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-slate-950">Category volume</h2>
          <div className="mt-5">
            <MiniBarChart data={analytics.tickets_by_category} />
          </div>
        </section>
      </div>

      <section className="rounded border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-base font-semibold text-slate-950">Frequent issue patterns</h2>
          <span className="text-sm text-slate-500">{analytics.issue_patterns.length} patterns</span>
        </div>
        <div className="mt-5 grid gap-3">
          {analytics.issue_patterns.map((item) => (
            <div key={item.pattern} className="flex items-center justify-between rounded border border-slate-200 px-4 py-3">
              <span className="font-medium text-slate-800">{item.pattern}</span>
              <span className="rounded bg-slate-100 px-2 py-1 text-sm font-semibold text-slate-700">
                {item.count}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
