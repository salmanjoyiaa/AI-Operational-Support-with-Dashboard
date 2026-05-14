import { AlertTriangle, CheckCircle2, RefreshCw, Send, UserCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Badge, toneForPriority, toneForSentiment, toneForStatus } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { api, formatDate } from "../lib/api";
import type { TicketDetail as TicketDetailType } from "../types/api";

export function TicketDetail() {
  const { id } = useParams();
  const [ticket, setTicket] = useState<TicketDetailType | null>(null);
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTicket = () => {
    if (!id) return;
    setLoading(true);
    api
      .getTicket(id)
      .then((response) => {
        setTicket(response);
        setNotes(response.human_review_notes ?? "");
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTicket();
  }, [id]);

  const runAction = (action: string) => {
    if (!ticket) return;
    setSaving(true);
    api
      .recordHumanReview(ticket.id, action, notes)
      .then(setTicket)
      .catch((err: Error) => setError(err.message))
      .finally(() => setSaving(false));
  };

  const retriage = () => {
    if (!ticket) return;
    setSaving(true);
    api
      .retriage(ticket.id)
      .then(setTicket)
      .catch((err: Error) => setError(err.message))
      .finally(() => setSaving(false));
  };

  if (loading) return <LoadingState label="Loading ticket" />;
  if (error) return <EmptyState title="Ticket unavailable" message={error} />;
  if (!ticket) return <EmptyState title="Ticket not found" message="The selected ticket could not be loaded." />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Link to="/tickets" className="text-sm font-semibold text-cyan-700 hover:text-cyan-900">
            Back to inbox
          </Link>
          <h1 className="mt-2 text-2xl font-semibold text-slate-950">{ticket.customer_name}</h1>
          <p className="mt-1 text-sm text-slate-500">
            {ticket.email} / {ticket.channel} / {formatDate(ticket.created_at)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge value={ticket.status} tone={toneForStatus(ticket.status)} />
          <Badge value={ticket.priority} tone={toneForPriority(ticket.priority)} />
          <Badge value={ticket.sentiment} tone={toneForSentiment(ticket.sentiment)} />
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
        <section className="space-y-6">
          <div className="rounded border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-base font-semibold text-slate-950">Customer message</h2>
            <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-slate-700">{ticket.message}</p>
          </div>

          <div className="rounded border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-base font-semibold text-slate-950">Suggested reply</h2>
              <span className="rounded bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700">
                Human review required
              </span>
            </div>
            <textarea
              className="mt-4 min-h-72 w-full rounded border border-slate-300 bg-slate-50 px-3 py-3 text-sm leading-6 text-slate-800"
              value={ticket.suggested_reply ?? ""}
              readOnly
            />
          </div>

          <div className="rounded border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-base font-semibold text-slate-950">Knowledge sources</h2>
            <div className="mt-4 grid gap-3">
              {ticket.knowledge_matches.map((match) => (
                <article key={match.article_id} className="rounded border border-slate-200 p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="font-semibold text-slate-950">{match.title}</h3>
                      <p className="mt-2 text-sm leading-6 text-slate-600">{match.excerpt}</p>
                    </div>
                    <span className="rounded bg-cyan-50 px-2 py-1 text-xs font-semibold text-cyan-700">
                      {Math.round(match.relevance_score * 100)}%
                    </span>
                  </div>
                </article>
              ))}
              {!ticket.knowledge_matches.length ? (
                <p className="text-sm text-slate-500">No relevant articles were attached.</p>
              ) : null}
            </div>
          </div>
        </section>

        <aside className="space-y-6">
          <div className="rounded border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-base font-semibold text-slate-950">AI triage</h2>
            <dl className="mt-4 space-y-4 text-sm">
              <div>
                <dt className="font-medium text-slate-500">Category</dt>
                <dd className="mt-1">
                  <Badge value={ticket.category} tone="purple" />
                </dd>
              </div>
              <div>
                <dt className="font-medium text-slate-500">Confidence</dt>
                <dd className="mt-1 text-slate-900">
                  {ticket.ai_confidence ? `${Math.round(ticket.ai_confidence * 100)}%` : "Not scored"}
                </dd>
              </div>
              <div>
                <dt className="font-medium text-slate-500">Issue pattern</dt>
                <dd className="mt-1 text-slate-900">{ticket.issue_pattern ?? "Unclassified"}</dd>
              </div>
              <div>
                <dt className="font-medium text-slate-500">Summary</dt>
                <dd className="mt-1 leading-6 text-slate-700">{ticket.ai_summary ?? "No summary"}</dd>
              </div>
            </dl>
          </div>

          <div className="rounded border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-600" aria-hidden="true" />
              <h2 className="text-base font-semibold text-slate-950">Escalation log</h2>
            </div>
            <div className="mt-4 space-y-2">
              {ticket.escalation_reasons.length ? (
                ticket.escalation_reasons.map((reason) => (
                  <p key={reason} className="rounded bg-amber-50 px-3 py-2 text-sm text-amber-800">
                    {reason}
                  </p>
                ))
              ) : (
                <p className="rounded bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                  No escalation rule was triggered.
                </p>
              )}
            </div>
          </div>

          <div className="rounded border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-base font-semibold text-slate-950">Review actions</h2>
            <textarea
              className="focus-ring mt-4 min-h-28 w-full rounded border border-slate-300 px-3 py-2 text-sm"
              placeholder="Internal review notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
            />
            <div className="mt-4 grid gap-2">
              <button
                className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-cyan-600 px-3 py-2 text-sm font-semibold text-white hover:bg-cyan-700 disabled:bg-slate-300"
                disabled={saving}
                onClick={() => runAction("approve_reply")}
                type="button"
              >
                <UserCheck className="h-4 w-4" aria-hidden="true" />
                Approve draft
              </button>
              <button
                className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-rose-600 px-3 py-2 text-sm font-semibold text-white hover:bg-rose-700 disabled:bg-slate-300"
                disabled={saving}
                onClick={() => runAction("escalate")}
                type="button"
              >
                <Send className="h-4 w-4" aria-hidden="true" />
                Escalate
              </button>
              <button
                className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:bg-slate-300"
                disabled={saving}
                onClick={() => runAction("resolve")}
                type="button"
              >
                <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                Mark resolved
              </button>
              <button
                className="focus-ring inline-flex items-center justify-center gap-2 rounded border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:text-slate-400"
                disabled={saving}
                onClick={retriage}
                type="button"
              >
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
                Re-run triage
              </button>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
