export type TicketStatus = "new" | "triaged" | "waiting_human" | "resolved";
export type TicketCategory = "billing" | "refund" | "technical" | "account" | "sales" | "other";
export type TicketSentiment = "angry" | "frustrated" | "neutral" | "positive";
export type TicketPriority = "low" | "medium" | "high" | "urgent";
export type TicketChannel = "email" | "chat" | "web" | "phone" | "social";

export type Ticket = {
  id: number;
  customer_name: string;
  email: string;
  message: string;
  channel: TicketChannel | string;
  created_at: string | null;
  updated_at: string | null;
  status: TicketStatus | string;
  category: TicketCategory | string | null;
  sentiment: TicketSentiment | string | null;
  priority: TicketPriority | string | null;
  ai_confidence: number | null;
  ai_summary: string | null;
  issue_pattern: string | null;
  escalation_required: boolean;
  escalation_reasons: string[];
};

export type KnowledgeMatch = {
  article_id: number;
  title: string;
  category: string;
  relevance_score: number;
  excerpt: string;
};

export type TicketDetail = Ticket & {
  suggested_reply: string | null;
  source_citations: Array<Record<string, string | number>>;
  human_review_notes: string | null;
  knowledge_matches: KnowledgeMatch[];
};

export type TicketListResponse = {
  items: Ticket[];
  total: number;
};

export type AnalyticsOverview = {
  total_tickets: number;
  open_tickets: number;
  escalation_rate: number;
  average_ai_confidence: number;
  tickets_by_category: Record<string, number>;
  priority_distribution: Record<string, number>;
  sentiment_distribution: Record<string, number>;
  issue_patterns: Array<{ pattern: string; count: number }>;
};

export type KnowledgeArticle = {
  id: number;
  title: string;
  category: string;
  content: string;
  source_url: string | null;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type SettingsRead = {
  app_name: string;
  environment: string;
  ai_provider: string;
  groq_model: string;
  ai_confidence_threshold: number;
  kb_min_relevance: number;
  human_in_the_loop_enforced: boolean;
};
