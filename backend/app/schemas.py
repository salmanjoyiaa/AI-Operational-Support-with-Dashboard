from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import TicketCategory, TicketChannel, TicketPriority, TicketSentiment, TicketStatus


class TicketCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    message: str = Field(min_length=10)
    channel: TicketChannel = TicketChannel.email


class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    human_review_notes: str | None = None


class HumanReviewAction(BaseModel):
    action: Literal["approve_reply", "request_changes", "escalate", "resolve"]
    notes: str | None = None


class KnowledgeArticleCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    category: TicketCategory
    content: str = Field(min_length=30)
    source_url: str | None = None


class KnowledgeArticleRead(BaseModel):
    id: int
    title: str
    category: str
    content: str
    source_url: str | None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class KnowledgeMatchRead(BaseModel):
    article_id: int
    title: str
    category: str
    relevance_score: float
    excerpt: str


class TicketRead(BaseModel):
    id: int
    customer_name: str
    email: str
    message: str
    channel: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status: str
    category: str | None
    sentiment: str | None
    priority: str | None
    ai_confidence: float | None
    ai_summary: str | None
    issue_pattern: str | None
    escalation_required: bool
    escalation_reasons: list[str]

    model_config = ConfigDict(from_attributes=True)


class TicketDetail(TicketRead):
    suggested_reply: str | None
    source_citations: list[dict]
    human_review_notes: str | None
    knowledge_matches: list[KnowledgeMatchRead]


class TicketListResponse(BaseModel):
    items: list[TicketRead]
    total: int


class AnalyticsOverview(BaseModel):
    total_tickets: int
    open_tickets: int
    escalation_rate: float
    average_ai_confidence: float
    tickets_by_category: dict[str, int]
    priority_distribution: dict[str, int]
    sentiment_distribution: dict[str, int]
    issue_patterns: list[dict[str, int | str]]


class SettingsRead(BaseModel):
    app_name: str
    environment: str
    ai_provider: str
    groq_model: str
    embedding_provider: str
    gemini_embedding_model: str
    ai_confidence_threshold: float
    kb_min_relevance: float
    human_in_the_loop_enforced: bool = True
