from app.models import Ticket, TicketCategory, TicketPriority, TicketSentiment
from app.services.ai_client import HeuristicLLMClient


def test_heuristic_triage_detects_refund_risk() -> None:
    ticket = Ticket(
        customer_name="Ava",
        email="ava@example.com",
        channel="email",
        message="I need a refund immediately because I was charged after cancellation.",
    )

    analysis = HeuristicLLMClient().analyze_ticket(ticket)

    assert analysis.category == TicketCategory.refund
    assert analysis.priority == TicketPriority.high
    assert analysis.confidence >= 0.8
    assert "Refund" in analysis.issue_pattern


def test_heuristic_triage_detects_angry_chargeback() -> None:
    ticket = Ticket(
        customer_name="Kai",
        email="kai@example.com",
        channel="chat",
        message="This is unacceptable and I will start a chargeback today.",
    )

    analysis = HeuristicLLMClient().analyze_ticket(ticket)

    assert analysis.sentiment == TicketSentiment.angry
    assert analysis.priority == TicketPriority.urgent
