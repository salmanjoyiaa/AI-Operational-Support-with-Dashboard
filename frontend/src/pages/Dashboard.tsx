import { AlertTriangle, Gauge, Inbox, Percent } from "lucide-react";
import { useEffect, useState } from "react";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { MiniBarChart } from "../components/MiniBarChart";
import { StatCard } from "../components/StatCard";
import { TicketTable } from "../components/TicketTable";
import { api } from "../lib/api";
import type { AnalyticsOverview, Ticket } from "../types/api";

export function Dashboard() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getAnalytics(), api.getTickets()])
      .then(([analyticsResponse, ticketResponse]) => {
        setAnalytics(analyticsResponse);
        setTickets(ticketResponse.items);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState label="Loading dashboard" />;
  if (error) return <EmptyState title="Dashboard unavailable" message={error} />;
  if (!analytics) return null;

  const highRiskTickets = tickets
    .filter((ticket) => ticket.escalation_required || ticket.priority === "urgent" || ticket.priority === "high")
    .slice(0, 5);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-950">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">Live support operations snapshot</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total tickets" value={analytics.total_tickets} icon={Inbox} detail="Seeded demo workload" />
        <StatCard label="Open tickets" value={analytics.open_tickets} icon={Gauge} accent="cyan" />
        <StatCard
          label="Escalation rate"
          value={`${Math.round(analytics.escalation_rate * 100)}%`}
          icon={AlertTriangle}
          accent="amber"
        />
        <StatCard
          label="Avg confidence"
          value={`${Math.round(analytics.average_ai_confidence * 100)}%`}
          icon={Percent}
          accent="emerald"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-950">High-risk queue</h2>
            <span className="text-sm text-slate-500">{highRiskTickets.length} tickets</span>
          </div>
          {highRiskTickets.length ? (
            <TicketTable tickets={highRiskTickets} />
          ) : (
            <EmptyState title="No high-risk tickets" message="Escalated and urgent tickets will appear here." />
          )}
        </section>

        <section className="rounded border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-slate-950">Ticket categories</h2>
          <div className="mt-5">
            <MiniBarChart data={analytics.tickets_by_category} />
          </div>
        </section>
      </div>
    </div>
  );
}
