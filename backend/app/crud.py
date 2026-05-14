from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app import models, schemas


def create_ticket(db: Session, payload: schemas.TicketCreate) -> models.Ticket:
    ticket = models.Ticket(**payload.model_dump(mode="json"))
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_ticket(db: Session, ticket_id: int) -> models.Ticket | None:
    return db.get(models.Ticket, ticket_id)


def list_tickets(
    db: Session,
    status: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    sentiment: str | None = None,
    escalated: bool | None = None,
) -> tuple[list[models.Ticket], int]:
    query: Select[tuple[models.Ticket]] = select(models.Ticket)
    count_query = select(func.count(models.Ticket.id))

    filters = []
    if status:
        filters.append(models.Ticket.status == status)
    if category:
        filters.append(models.Ticket.category == category)
    if priority:
        filters.append(models.Ticket.priority == priority)
    if sentiment:
        filters.append(models.Ticket.sentiment == sentiment)
    if escalated is not None:
        filters.append(models.Ticket.escalation_required.is_(escalated))

    for condition in filters:
        query = query.where(condition)
        count_query = count_query.where(condition)

    query = query.order_by(models.Ticket.created_at.desc(), models.Ticket.id.desc())
    return list(db.scalars(query)), int(db.scalar(count_query) or 0)


def create_article(db: Session, payload: schemas.KnowledgeArticleCreate) -> models.KnowledgeArticle:
    article = models.KnowledgeArticle(**payload.model_dump(mode="json"))
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def list_articles(db: Session) -> list[models.KnowledgeArticle]:
    return list(
        db.scalars(
            select(models.KnowledgeArticle)
            .where(models.KnowledgeArticle.is_active.is_(True))
            .order_by(models.KnowledgeArticle.category, models.KnowledgeArticle.title)
        )
    )
