from app.core.config import Settings
from app.models import TicketCategory, TicketPriority, TicketSentiment
from app.services.ai_client import TicketAIAnalysis
from app.services.escalation import EscalationService
from app.services.knowledge_base import KnowledgeBaseMatch


def make_analysis(**overrides) -> TicketAIAnalysis:
    data = {
        "category": TicketCategory.technical,
        "sentiment": TicketSentiment.neutral,
        "priority": TicketPriority.medium,
        "confidence": 0.9,
        "issue_pattern": "Webhook issue",
        "summary": "Webhook delivery delay.",
    }
    data.update(overrides)
    return TicketAIAnalysis(**data)


def test_escalates_angry_customer() -> None:
    service = EscalationService(Settings(ai_confidence_threshold=0.72, kb_min_relevance=0.42))
    decision = service.evaluate(
        make_analysis(sentiment=TicketSentiment.angry, priority=TicketPriority.urgent),
        "I am angry and this is unacceptable",
        [KnowledgeBaseMatch(1, "Webhook Delivery", "technical", 0.9, "Webhook help")],
    )

    assert decision.required is True
    assert any("angry" in reason.lower() for reason in decision.reasons)


def test_escalates_low_confidence_and_missing_kb() -> None:
    service = EscalationService(Settings(ai_confidence_threshold=0.72, kb_min_relevance=0.42))
    decision = service.evaluate(make_analysis(confidence=0.45), "Ambiguous issue", [])

    assert decision.required is True
    assert any("confidence" in reason.lower() for reason in decision.reasons)
    assert any("knowledge base" in reason.lower() for reason in decision.reasons)


def test_escalates_refund_request() -> None:
    service = EscalationService(Settings(ai_confidence_threshold=0.72, kb_min_relevance=0.42))
    decision = service.evaluate(
        make_analysis(category=TicketCategory.refund, priority=TicketPriority.high),
        "Please refund our last renewal",
        [KnowledgeBaseMatch(1, "Refund Review", "refund", 0.9, "Refund workflow")],
    )

    assert decision.required is True
    assert any("refund" in reason.lower() for reason in decision.reasons)
