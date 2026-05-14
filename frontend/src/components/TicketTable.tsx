import { Link } from "react-router-dom";
import { Badge, toneForPriority, toneForSentiment, toneForStatus } from "./Badge";
import { formatDate } from "../lib/api";
import type { Ticket } from "../types/api";

type TicketTableProps = {
  tickets: Ticket[];
};

export function TicketTable({ tickets }: TicketTableProps) {
  return (
    <div className="overflow-hidden rounded border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">Customer</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">Category</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">Priority</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">Sentiment</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {tickets.map((ticket) => (
              <tr key={ticket.id} className="hover:bg-slate-50">
                <td className="min-w-72 px-4 py-4">
                  <Link to={`/tickets/${ticket.id}`} className="font-semibold text-slate-950 hover:text-cyan-700">
                    {ticket.customer_name}
                  </Link>
                  <p className="mt-1 max-w-xl truncate text-sm text-slate-500">{ticket.message}</p>
                </td>
                <td className="px-4 py-4">
                  <Badge value={ticket.category} tone="purple" />
                </td>
                <td className="px-4 py-4">
                  <Badge value={ticket.priority} tone={toneForPriority(ticket.priority)} />
                </td>
                <td className="px-4 py-4">
                  <Badge value={ticket.sentiment} tone={toneForSentiment(ticket.sentiment)} />
                </td>
                <td className="px-4 py-4">
                  <Badge value={ticket.status} tone={toneForStatus(ticket.status)} />
                </td>
                <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-500">
                  {formatDate(ticket.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
