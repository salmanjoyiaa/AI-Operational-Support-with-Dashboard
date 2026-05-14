from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.models import TicketCategory, TicketPriority, TicketSentiment
from app.services.ai_client import TicketAIAnalysis
from app.services.knowledge_base import KnowledgeBaseMatch


@dataclass(frozen=True)
class EscalationDecision:
    required: bool
    reasons: list[str]


class EscalationService:
    RISK_TERMS = ["legal", "lawsuit", "chargeback", "payment", "fraud", "security", "breach"]

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def evaluate(
        self, analysis: TicketAIAnalysis, message: str, matches: list[KnowledgeBaseMatch]
    ) -> EscalationDecision:
        reasons: list[str] = []
        text = message.lower()

        if analysis.sentiment == TicketSentiment.angry:
            reasons.append("Customer sentiment is angry.")
        if analysis.category == TicketCategory.refund:
            reasons.append("Ticket involves a refund request.")
        if analysis.category == TicketCategory.billing or any(term in text for term in self.RISK_TERMS):
            reasons.append("Ticket involves billing, legal, payment, fraud, or security risk.")
        if analysis.priority == TicketPriority.urgent:
            reasons.append("Ticket priority is urgent.")
        if analysis.confidence < self.settings.ai_confidence_threshold:
            reasons.append(
                f"AI confidence {analysis.confidence:.2f} is below threshold "
                f"{self.settings.ai_confidence_threshold:.2f}."
            )
        if not matches or all(match.relevance_score < self.settings.kb_min_relevance for match in matches):
            reasons.append("No sufficiently relevant knowledge base article was found.")

        return EscalationDecision(required=bool(reasons), reasons=reasons)
