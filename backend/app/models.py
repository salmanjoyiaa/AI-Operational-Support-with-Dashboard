from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TicketStatus(str, Enum):
    new = "new"
    triaged = "triaged"
    waiting_human = "waiting_human"
    resolved = "resolved"


class TicketCategory(str, Enum):
    billing = "billing"
    refund = "refund"
    technical = "technical"
    account = "account"
    sales = "sales"
    other = "other"


class TicketSentiment(str, Enum):
    angry = "angry"
    frustrated = "frustrated"
    neutral = "neutral"
    positive = "positive"


class TicketPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class TicketChannel(str, Enum):
    email = "email"
    chat = "chat"
    web = "web"
    phone = "phone"
    social = "social"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), default=TicketChannel.email.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    status: Mapped[str] = mapped_column(String(32), default=TicketStatus.new.value, nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    priority: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    issue_pattern: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)

    suggested_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_citations: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    escalation_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    escalation_reasons: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    human_review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    article_matches: Mapped[list["TicketArticleMatch"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", lazy="selectin"
    )


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    ticket_matches: Mapped[list["TicketArticleMatch"]] = relationship(back_populates="article")


class TicketArticleMatch(Base):
    __tablename__ = "ticket_article_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("knowledge_articles.id"), index=True)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="article_matches")
    article: Mapped[KnowledgeArticle] = relationship(back_populates="ticket_matches")
