from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Ticket, TicketArticleMatch, TicketStatus
from app.services.ai_client import TicketAIAnalysis, build_ai_client
from app.services.escalation import EscalationService
from app.services.knowledge_base import KnowledgeBaseMatch, KnowledgeBaseService


class TriageService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.ai_client = build_ai_client(settings)
        self.kb_service = KnowledgeBaseService(settings)
        self.escalation_service = EscalationService(settings)

    def process_ticket(self, ticket: Ticket) -> Ticket:
        analysis = self.ai_client.analyze_ticket(ticket)
        matches = self.kb_service.search(self.db, ticket.message, top_k=3)
        return self.apply_analysis(ticket, analysis, matches)

    def apply_analysis(
        self, ticket: Ticket, analysis: TicketAIAnalysis, matches: list[KnowledgeBaseMatch]
    ) -> Ticket:
        escalation = self.escalation_service.evaluate(analysis, ticket.message, matches)
        reply = self.ai_client.generate_reply(ticket, analysis, matches)

        ticket.category = analysis.category.value
        ticket.sentiment = analysis.sentiment.value
        ticket.priority = analysis.priority.value
        ticket.ai_confidence = analysis.confidence
        ticket.ai_summary = analysis.summary
        ticket.issue_pattern = analysis.issue_pattern
        ticket.suggested_reply = reply.body
        ticket.source_citations = reply.citations
        ticket.escalation_required = escalation.required
        ticket.escalation_reasons = escalation.reasons
        ticket.status = TicketStatus.waiting_human.value if escalation.required else TicketStatus.triaged.value

        self.db.execute(delete(TicketArticleMatch).where(TicketArticleMatch.ticket_id == ticket.id))
        for match in matches:
            self.db.add(
                TicketArticleMatch(
                    ticket_id=ticket.id,
                    article_id=match.article_id,
                    relevance_score=match.relevance_score,
                    excerpt=match.excerpt,
                )
            )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket
