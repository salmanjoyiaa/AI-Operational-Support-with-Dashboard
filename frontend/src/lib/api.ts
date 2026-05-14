import type {
  AnalyticsOverview,
  KnowledgeArticle,
  SettingsRead,
  TicketChannel,
  TicketDetail,
  TicketListResponse,
  TicketStatus
} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type CreateTicketPayload = {
  customer_name: string;
  email: string;
  message: string;
  channel: TicketChannel;
};

type CreateArticlePayload = {
  title: string;
  category: string;
  content: string;
  source_url?: string;
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers
    },
    ...options
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  getTickets(filters: Record<string, string> = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value && value !== "all") params.set(key, value);
    });
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return request<TicketListResponse>(`/api/tickets${suffix}`);
  },
  getTicket(id: string | number) {
    return request<TicketDetail>(`/api/tickets/${id}`);
  },
  createTicket(payload: CreateTicketPayload) {
    return request<TicketDetail>("/api/tickets", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  updateStatus(id: number, status: TicketStatus, notes?: string) {
    return request<TicketDetail>(`/api/tickets/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, human_review_notes: notes })
    });
  },
  recordHumanReview(id: number, action: string, notes?: string) {
    return request<TicketDetail>(`/api/tickets/${id}/human-review`, {
      method: "POST",
      body: JSON.stringify({ action, notes })
    });
  },
  retriage(id: number) {
    return request<TicketDetail>(`/api/tickets/${id}/retriage`, { method: "POST" });
  },
  getAnalytics() {
    return request<AnalyticsOverview>("/api/analytics/overview");
  },
  getArticles() {
    return request<KnowledgeArticle[]>("/api/knowledge-base/articles");
  },
  createArticle(payload: CreateArticlePayload) {
    return request<KnowledgeArticle>("/api/knowledge-base/articles", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  resetDemo() {
    return request<{ status: string }>("/api/demo/reset", { method: "POST" });
  },
  getSettings() {
    return request<SettingsRead>("/api/settings");
  }
};

export function formatDate(value: string | null): string {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}
