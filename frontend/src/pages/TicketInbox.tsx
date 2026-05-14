import { Plus, RefreshCw } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { TicketTable } from "../components/TicketTable";
import { api } from "../lib/api";
import type { Ticket, TicketChannel } from "../types/api";

const filterOptions = {
  status: ["all", "new", "triaged", "waiting_human", "resolved"],
  category: ["all", "billing", "refund", "technical", "account", "sales", "other"],
  priority: ["all", "low", "medium", "high", "urgent"],
  sentiment: ["all", "angry", "frustrated", "neutral", "positive"]
};

const initialForm = {
  customer_name: "",
  email: "",
  channel: "email" as TicketChannel,
  message: ""
};

export function TicketInbox() {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [filters, setFilters] = useState({ status: "all", category: "all", priority: "all", sentiment: "all" });
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTickets = () => {
    setLoading(true);
    api
      .getTickets(filters)
      .then((response) => setTickets(response.items))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTickets();
  }, [filters.status, filters.category, filters.priority, filters.sentiment]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    api
      .createTicket(form)
      .then((ticket) => {
        setForm(initialForm);
        navigate(`/tickets/${ticket.id}`);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setSubmitting(false));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-950">Ticket Inbox</h1>
          <p className="mt-1 text-sm text-slate-500">Triaged support tickets awaiting review</p>
        </div>
        <button
          className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
          onClick={loadTickets}
          type="button"
        >
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          Refresh
        </button>
      </div>

      <section className="rounded border border-slate-200 bg-white p-5 shadow-sm">
        <form className="grid gap-4 lg:grid-cols-[1fr_1fr_160px]" onSubmit={handleSubmit}>
          <input
            className="focus-ring rounded border border-slate-300 px-3 py-2 text-sm"
            placeholder="Customer name"
            value={form.customer_name}
            onChange={(event) => setForm({ ...form, customer_name: event.target.value })}
            required
          />
          <input
            className="focus-ring rounded border border-slate-300 px-3 py-2 text-sm"
            placeholder="Email"
            type="email"
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
            required
          />
          <select
            className="focus-ring rounded border border-slate-300 px-3 py-2 text-sm"
            value={form.channel}
            onChange={(event) => setForm({ ...form, channel: event.target.value as TicketChannel })}
          >
            {["email", "chat", "web", "phone", "social"].map((channel) => (
              <option key={channel} value={channel}>
                {channel}
              </option>
            ))}
          </select>
          <textarea
            className="focus-ring min-h-28 rounded border border-slate-300 px-3 py-2 text-sm lg:col-span-3"
            placeholder="Customer message"
            value={form.message}
            onChange={(event) => setForm({ ...form, message: event.target.value })}
            required
          />
          <div className="lg:col-span-3">
            <button
              className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-cyan-600 px-4 py-2 text-sm font-semibold text-white hover:bg-cyan-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              disabled={submitting}
              type="submit"
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              {submitting ? "Triaging" : "Create ticket"}
            </button>
          </div>
        </form>
        {error ? <p className="mt-3 text-sm font-medium text-rose-600">{error}</p> : null}
      </section>

      <section className="grid gap-3 rounded border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-4">
        {Object.entries(filterOptions).map(([key, values]) => (
          <label key={key} className="text-sm font-medium capitalize text-slate-600">
            {key}
            <select
              className="focus-ring mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
              value={filters[key as keyof typeof filters]}
              onChange={(event) => setFilters({ ...filters, [key]: event.target.value })}
            >
              {values.map((value) => (
                <option key={value} value={value}>
                  {value.replace("_", " ")}
                </option>
              ))}
            </select>
          </label>
        ))}
      </section>

      {loading ? (
        <LoadingState label="Loading tickets" />
      ) : tickets.length ? (
        <TicketTable tickets={tickets} />
      ) : (
        <EmptyState title="No tickets match" message="Adjust filters or create a new ticket." />
      )}
    </div>
  );
}
