from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.services.ai_client import AIProviderError
from app.services.triage import TriageService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=schemas.TicketDetail, status_code=201)
def create_ticket(
    payload: schemas.TicketCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> schemas.TicketDetail:
    ticket = crud.create_ticket(db, payload)
    try:
        ticket = TriageService(db, settings).process_ticket(ticket)
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return serialize_ticket_detail(db, ticket)


@router.get("", response_model=schemas.TicketListResponse)
def list_tickets(
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    sentiment: str | None = Query(default=None),
    escalated: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> schemas.TicketListResponse:
    tickets, total = crud.list_tickets(
        db,
        status=status,
        category=category,
        priority=priority,
        sentiment=sentiment,
        escalated=escalated,
    )
    return schemas.TicketListResponse(items=tickets, total=total)


@router.get("/{ticket_id}", response_model=schemas.TicketDetail)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> schemas.TicketDetail:
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return serialize_ticket_detail(db, ticket)


@router.post("/{ticket_id}/retriage", response_model=schemas.TicketDetail)
def retriage_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> schemas.TicketDetail:
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    try:
        ticket = TriageService(db, settings).process_ticket(ticket)
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return serialize_ticket_detail(db, ticket)


@router.patch("/{ticket_id}/status", response_model=schemas.TicketDetail)
def update_ticket_status(
    ticket_id: int,
    payload: schemas.TicketStatusUpdate,
    db: Session = Depends(get_db),
) -> schemas.TicketDetail:
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = payload.status.value
    if payload.human_review_notes:
        ticket.human_review_notes = payload.human_review_notes
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return serialize_ticket_detail(db, ticket)


@router.post("/{ticket_id}/human-review", response_model=schemas.TicketDetail)
def record_human_review(
    ticket_id: int,
    payload: schemas.HumanReviewAction,
    db: Session = Depends(get_db),
) -> schemas.TicketDetail:
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.human_review_notes = payload.notes
    if payload.action == "resolve":
        ticket.status = models.TicketStatus.resolved.value
    elif payload.action == "escalate":
        ticket.status = models.TicketStatus.waiting_human.value
        ticket.escalation_required = True
        reasons = list(ticket.escalation_reasons or [])
        if "Manually escalated during human review." not in reasons:
            reasons.append("Manually escalated during human review.")
        ticket.escalation_reasons = reasons
    elif payload.action == "request_changes":
        ticket.status = models.TicketStatus.waiting_human.value
    else:
        ticket.status = models.TicketStatus.triaged.value

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return serialize_ticket_detail(db, ticket)


def serialize_ticket_detail(db: Session, ticket: models.Ticket) -> schemas.TicketDetail:
    matches = list(
        db.scalars(
            select(models.TicketArticleMatch)
            .where(models.TicketArticleMatch.ticket_id == ticket.id)
            .order_by(models.TicketArticleMatch.relevance_score.desc())
        )
    )
    knowledge_matches = [
        schemas.KnowledgeMatchRead(
            article_id=match.article_id,
            title=match.article.title,
            category=match.article.category,
            relevance_score=round(match.relevance_score, 3),
            excerpt=match.excerpt,
        )
        for match in matches
        if match.article is not None
    ]
    return schemas.TicketDetail(
        id=ticket.id,
        customer_name=ticket.customer_name,
        email=ticket.email,
        message=ticket.message,
        channel=ticket.channel,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        status=ticket.status,
        category=ticket.category,
        sentiment=ticket.sentiment,
        priority=ticket.priority,
        ai_confidence=ticket.ai_confidence,
        ai_summary=ticket.ai_summary,
        issue_pattern=ticket.issue_pattern,
        escalation_required=ticket.escalation_required,
        escalation_reasons=ticket.escalation_reasons or [],
        suggested_reply=ticket.suggested_reply,
        source_citations=ticket.source_citations or [],
        human_review_notes=ticket.human_review_notes,
        knowledge_matches=knowledge_matches,
    )
