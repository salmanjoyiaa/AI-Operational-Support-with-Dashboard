from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import KnowledgeArticle, Ticket, TicketArticleMatch, TicketCategory, TicketPriority, TicketSentiment
from app.services.ai_client import HeuristicLLMClient, TicketAIAnalysis
from app.services.escalation import EscalationService
from app.services.knowledge_base import KnowledgeBaseService


DEMO_ARTICLES = [
    {
        "title": "Refund Review Workflow",
        "category": "refund",
        "source_url": "kb://refund-review-workflow",
        "content": (
            "Refund requests must be reviewed by a human support specialist before any commitment is made. "
            "Validate the customer identity, subscription status, payment date, and product usage window. "
            "If the customer mentions a chargeback, legal action, or an incorrect payment, escalate the ticket "
            "to the billing queue and include transaction context. Approved refunds are processed through the "
            "payments dashboard and confirmed only after the refund status is visible."
        ),
    },
    {
        "title": "Failed Payment and Invoice Troubleshooting",
        "category": "billing",
        "source_url": "kb://failed-payment-invoice",
        "content": (
            "When a customer reports failed payments, duplicate charges, missing invoices, or expired cards, "
            "verify the billing email and subscription workspace. Ask the customer to confirm the last four "
            "digits of the card through a secure form, never over plain email. Duplicate-charge concerns should "
            "be escalated to billing operations with the invoice ID and payment timestamp."
        ),
    },
    {
        "title": "Login and SSO Recovery",
        "category": "account",
        "source_url": "kb://login-sso-recovery",
        "content": (
            "For login issues, ask the customer to try password reset, confirm whether SSO is enabled, and verify "
            "that their email belongs to the expected workspace. If two-factor authentication recovery is needed, "
            "route to the account security queue. Do not disable security controls without manager approval."
        ),
    },
    {
        "title": "Webhook Delivery Diagnostics",
        "category": "technical",
        "source_url": "kb://webhook-delivery",
        "content": (
            "For webhook delivery delays, check endpoint health, retry policy, event volume, and recent incident "
            "logs. Customers should provide the event ID, endpoint URL, and approximate timestamp. If multiple "
            "workspaces are affected or data delivery is blocked, raise priority to high and notify engineering."
        ),
    },
    {
        "title": "API Rate Limit Guidance",
        "category": "technical",
        "source_url": "kb://api-rate-limits",
        "content": (
            "API rate limit questions should be answered with the customer's current plan limits, recommended "
            "backoff behavior, and upgrade options. Technical teams should avoid promising custom limits without "
            "sales engineering approval. Persistent 429 responses with normal traffic should be investigated."
        ),
    },
    {
        "title": "Enterprise Plan Qualification",
        "category": "sales",
        "source_url": "kb://enterprise-plan",
        "content": (
            "Enterprise inquiries should capture team size, required integrations, compliance needs, target launch "
            "date, and budget owner. Offer a tailored demo and route qualified opportunities to sales. Do not quote "
            "custom pricing in support replies unless an approved pricing package is attached."
        ),
    },
]


DEMO_TICKETS = [
    {
        "customer_name": "Alicia Morgan",
        "email": "alicia.morgan@example.com",
        "message": "I was charged twice this month and I am furious. If this is not fixed today I will start a chargeback.",
        "channel": "email",
        "category": TicketCategory.billing,
        "sentiment": TicketSentiment.angry,
        "priority": TicketPriority.urgent,
        "confidence": 0.93,
        "issue_pattern": "Duplicate charge risk",
        "summary": "Customer reports duplicate monthly charge and threatens a chargeback.",
    },
    {
        "customer_name": "Dev Patel",
        "email": "dev.patel@example.com",
        "message": "Our webhook events have been delayed for two hours and our operations team is blocked. Can someone help?",
        "channel": "chat",
        "category": TicketCategory.technical,
        "sentiment": TicketSentiment.frustrated,
        "priority": TicketPriority.medium,
        "confidence": 0.86,
        "issue_pattern": "Integration reliability issue",
        "summary": "Customer reports delayed webhook events blocking operations.",
    },
    {
        "customer_name": "Mina Chen",
        "email": "mina.chen@example.com",
        "message": "I need a refund for last week's renewal because our team cancelled before the renewal date.",
        "channel": "web",
        "category": TicketCategory.refund,
        "sentiment": TicketSentiment.neutral,
        "priority": TicketPriority.high,
        "confidence": 0.88,
        "issue_pattern": "Refund request",
        "summary": "Customer requests refund for a renewal they believe should not have happened.",
    },
    {
        "customer_name": "Jordan Ellis",
        "email": "jordan.ellis@example.com",
        "message": "We are evaluating your enterprise plan for 80 agents and need SSO, audit logs, and procurement details.",
        "channel": "email",
        "category": TicketCategory.sales,
        "sentiment": TicketSentiment.positive,
        "priority": TicketPriority.low,
        "confidence": 0.84,
        "issue_pattern": "Enterprise plan evaluation",
        "summary": "Customer is evaluating enterprise plan requirements.",
    },
    {
        "customer_name": "Sam Rivera",
        "email": "sam.rivera@example.com",
        "message": "Password reset emails are not arriving and I cannot access the account before a client call.",
        "channel": "phone",
        "category": TicketCategory.account,
        "sentiment": TicketSentiment.frustrated,
        "priority": TicketPriority.medium,
        "confidence": 0.82,
        "issue_pattern": "Account access issue",
        "summary": "Customer cannot receive password reset emails before a client call.",
    },
    {
        "customer_name": "Priya Shah",
        "email": "priya.shah@example.com",
        "message": "The API is returning 429 errors even though our traffic is normal. This started after yesterday's deployment.",
        "channel": "email",
        "category": TicketCategory.technical,
        "sentiment": TicketSentiment.frustrated,
        "priority": TicketPriority.medium,
        "confidence": 0.85,
        "issue_pattern": "API rate limit anomaly",
        "summary": "Customer reports unexpected API rate limit errors after deployment.",
    },
]


def seed_database(db: Session, settings: Settings, force: bool = False) -> None:
    if force:
        db.execute(delete(TicketArticleMatch))
        db.execute(delete(Ticket))
        db.execute(delete(KnowledgeArticle))
        db.commit()

    has_articles = db.scalar(select(KnowledgeArticle.id).limit(1)) is not None
    if not has_articles:
        for article in DEMO_ARTICLES:
            db.add(KnowledgeArticle(**article))
        db.commit()

    kb_service = KnowledgeBaseService(settings)
    kb_service.rebuild_index(db)

    has_tickets = db.scalar(select(Ticket.id).limit(1)) is not None
    if has_tickets:
        return

    local_ai = HeuristicLLMClient()
    escalation_service = EscalationService(settings)
    for item in DEMO_TICKETS:
        ticket = Ticket(
            customer_name=item["customer_name"],
            email=item["email"],
            message=item["message"],
            channel=item["channel"],
            category=item["category"].value,
            sentiment=item["sentiment"].value,
            priority=item["priority"].value,
            ai_confidence=item["confidence"],
            ai_summary=item["summary"],
            issue_pattern=item["issue_pattern"],
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        matches = kb_service.search(db, ticket.message, top_k=3)
        analysis = TicketAIAnalysis(
            category=item["category"],
            sentiment=item["sentiment"],
            priority=item["priority"],
            confidence=item["confidence"],
            issue_pattern=item["issue_pattern"],
            summary=item["summary"],
        )
        decision = escalation_service.evaluate(analysis, ticket.message, matches)
        reply = local_ai.generate_reply(ticket, analysis, matches)
        ticket.suggested_reply = reply.body
        ticket.source_citations = reply.citations
        ticket.escalation_required = decision.required
        ticket.escalation_reasons = decision.reasons
        ticket.status = "waiting_human" if decision.required else "triaged"
        for match in matches:
            db.add(
                TicketArticleMatch(
                    ticket_id=ticket.id,
                    article_id=match.article_id,
                    relevance_score=match.relevance_score,
                    excerpt=match.excerpt,
                )
            )
        db.add(ticket)
        db.commit()
