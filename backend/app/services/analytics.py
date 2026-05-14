from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Ticket, TicketStatus
from app.schemas import AnalyticsOverview


def build_analytics(db: Session) -> AnalyticsOverview:
    tickets = list(db.scalars(select(Ticket)))
    total = len(tickets)
    open_tickets = sum(1 for ticket in tickets if ticket.status != TicketStatus.resolved.value)
    escalated = sum(1 for ticket in tickets if ticket.escalation_required)
    confidence_values = [ticket.ai_confidence for ticket in tickets if ticket.ai_confidence is not None]

    return AnalyticsOverview(
        total_tickets=total,
        open_tickets=open_tickets,
        escalation_rate=round(escalated / total, 3) if total else 0.0,
        average_ai_confidence=round(sum(confidence_values) / len(confidence_values), 3)
        if confidence_values
        else 0.0,
        tickets_by_category=_counts(db, Ticket.category),
        priority_distribution=_counts(db, Ticket.priority),
        sentiment_distribution=_counts(db, Ticket.sentiment),
        issue_patterns=[
            {"pattern": pattern, "count": count}
            for pattern, count in Counter(ticket.issue_pattern for ticket in tickets if ticket.issue_pattern)
            .most_common(8)
        ],
    )


def _counts(db: Session, column) -> dict[str, int]:
    rows = db.execute(select(column, func.count(Ticket.id)).group_by(column)).all()
    return {str(key or "unclassified"): int(value) for key, value in rows}
