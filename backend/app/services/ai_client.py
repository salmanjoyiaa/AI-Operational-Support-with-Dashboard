from __future__ import annotations

import json
import re
from typing import Protocol

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings
from app.models import Ticket, TicketCategory, TicketPriority, TicketSentiment
from app.services.knowledge_base import KnowledgeBaseMatch


class AIProviderError(RuntimeError):
    """Raised when the configured AI provider cannot produce a valid response."""


class TicketAIAnalysis(BaseModel):
    category: TicketCategory
    sentiment: TicketSentiment
    priority: TicketPriority
    confidence: float = Field(ge=0.0, le=1.0)
    issue_pattern: str
    summary: str


class GeneratedReply(BaseModel):
    body: str
    citations: list[dict[str, str | int | float]]


class LLMClient(Protocol):
    def analyze_ticket(self, ticket: Ticket) -> TicketAIAnalysis:
        ...

    def generate_reply(
        self, ticket: Ticket, analysis: TicketAIAnalysis, matches: list[KnowledgeBaseMatch]
    ) -> GeneratedReply:
        ...


class HeuristicLLMClient:
    """Deterministic local provider for demos and offline development.

    Production Groq mode is explicit via AI_PROVIDER=groq and never silently falls
    back to this provider if remote inference fails.
    """

    CATEGORY_KEYWORDS = {
        TicketCategory.refund: ["refund", "cancel", "money back", "chargeback", "return"],
        TicketCategory.billing: ["invoice", "billing", "charged", "payment", "card", "subscription"],
        TicketCategory.technical: ["error", "bug", "crash", "broken", "login loop", "api", "webhook", "sync"],
        TicketCategory.account: ["password", "login", "account", "sso", "2fa", "access"],
        TicketCategory.sales: ["pricing", "quote", "enterprise", "demo", "plan", "upgrade"],
    }

    ANGRY_WORDS = ["angry", "furious", "unacceptable", "lawsuit", "legal", "chargeback", "terrible"]
    FRUSTRATED_WORDS = ["frustrated", "annoyed", "stuck", "again", "still", "not working", "blocked"]
    POSITIVE_WORDS = ["thanks", "great", "love", "helpful", "appreciate"]

    def analyze_ticket(self, ticket: Ticket) -> TicketAIAnalysis:
        text = ticket.message.lower()
        category = TicketCategory.other
        confidence = 0.64

        for candidate, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                category = candidate
                confidence = 0.86
                break

        if any(word in text for word in self.ANGRY_WORDS):
            sentiment = TicketSentiment.angry
        elif any(word in text for word in self.FRUSTRATED_WORDS):
            sentiment = TicketSentiment.frustrated
        elif any(word in text for word in self.POSITIVE_WORDS):
            sentiment = TicketSentiment.positive
        else:
            sentiment = TicketSentiment.neutral

        priority = TicketPriority.low
        if sentiment == TicketSentiment.angry or "legal" in text or "chargeback" in text:
            priority = TicketPriority.urgent
            confidence = max(confidence, 0.9)
        elif category in {TicketCategory.refund, TicketCategory.billing}:
            priority = TicketPriority.high
        elif sentiment == TicketSentiment.frustrated or category == TicketCategory.technical:
            priority = TicketPriority.medium

        pattern = self._issue_pattern(text, category)
        summary = self._summary(ticket.message)
        return TicketAIAnalysis(
            category=category,
            sentiment=sentiment,
            priority=priority,
            confidence=round(confidence, 2),
            issue_pattern=pattern,
            summary=summary,
        )

    def generate_reply(
        self, ticket: Ticket, analysis: TicketAIAnalysis, matches: list[KnowledgeBaseMatch]
    ) -> GeneratedReply:
        citation_lines = []
        citations: list[dict[str, str | int | float]] = []
        for match in matches[:3]:
            citation_lines.append(f"- {match.title}")
            citations.append(
                {
                    "article_id": match.article_id,
                    "title": match.title,
                    "relevance_score": round(match.relevance_score, 3),
                }
            )

        if analysis.sentiment == TicketSentiment.angry:
            opening = "I am sorry this has been such a frustrating experience."
        elif analysis.sentiment == TicketSentiment.positive:
            opening = "Thanks for reaching out and for the kind context."
        else:
            opening = "Thanks for reaching out."

        kb_context = "\n".join(citation_lines) if citation_lines else "- No confident source found"
        body = (
            f"Hi {ticket.customer_name},\n\n"
            f"{opening} I reviewed your note about {analysis.issue_pattern.lower()} and want to help get this resolved.\n\n"
            "Based on our support resources, the next best step is to verify the account details tied to "
            "this request and follow the documented workflow for the issue type. If this involves billing, "
            "refunds, or account security, a specialist should review it before any commitment is made.\n\n"
            "Relevant internal references:\n"
            f"{kb_context}\n\n"
            "I will keep this with our support team for human review before we send a final response."
        )
        return GeneratedReply(body=body, citations=citations)

    def _issue_pattern(self, text: str, category: TicketCategory) -> str:
        if "refund" in text or "money back" in text:
            return "Refund request"
        if "payment" in text or "charged" in text or "invoice" in text:
            return "Payment or invoice concern"
        if "login" in text or "password" in text or "sso" in text:
            return "Account access issue"
        if "webhook" in text or "api" in text or "sync" in text:
            return "Integration reliability issue"
        if category == TicketCategory.sales:
            return "Plan evaluation"
        return f"{category.value.title()} support request"

    def _summary(self, message: str) -> str:
        cleaned = re.sub(r"\s+", " ", message).strip()
        if len(cleaned) <= 180:
            return cleaned
        return cleaned[:177].rstrip() + "..."


class GroqLLMClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise AIProviderError("GROQ_API_KEY is required when AI_PROVIDER=groq.")
        self.settings = settings

    def analyze_ticket(self, ticket: Ticket) -> TicketAIAnalysis:
        prompt = {
            "task": "Classify a customer support ticket for a human-in-the-loop SaaS support workflow.",
            "allowed_categories": [item.value for item in TicketCategory],
            "allowed_sentiments": [item.value for item in TicketSentiment],
            "allowed_priorities": [item.value for item in TicketPriority],
            "ticket": {
                "customer_name": ticket.customer_name,
                "email": ticket.email,
                "channel": ticket.channel,
                "message": ticket.message,
            },
            "required_json_shape": {
                "category": "billing|refund|technical|account|sales|other",
                "sentiment": "angry|frustrated|neutral|positive",
                "priority": "low|medium|high|urgent",
                "confidence": "number between 0 and 1",
                "issue_pattern": "short label",
                "summary": "one sentence",
            },
        }
        data = self._chat_json(
            system="You are a precise support operations classifier. Return only valid JSON.",
            user=json.dumps(prompt),
        )
        try:
            return TicketAIAnalysis.model_validate(data)
        except ValidationError as exc:
            raise AIProviderError(f"Groq classification response failed validation: {exc}") from exc

    def generate_reply(
        self, ticket: Ticket, analysis: TicketAIAnalysis, matches: list[KnowledgeBaseMatch]
    ) -> GeneratedReply:
        articles = [
            {
                "article_id": match.article_id,
                "title": match.title,
                "category": match.category,
                "relevance_score": match.relevance_score,
                "excerpt": match.excerpt,
            }
            for match in matches[:3]
        ]
        prompt = {
            "task": "Draft a customer support reply for human review. Never claim it has been sent.",
            "ticket": {
                "customer_name": ticket.customer_name,
                "email": ticket.email,
                "channel": ticket.channel,
                "message": ticket.message,
            },
            "classification": analysis.model_dump(mode="json"),
            "knowledge_base_articles": articles,
            "required_json_shape": {
                "body": "polite customer-facing draft reply with no unsupported promises",
                "citations": [
                    {"article_id": "number", "title": "string", "relevance_score": "number"}
                ],
            },
        }
        data = self._chat_json(
            system=(
                "You draft support replies that must be reviewed by a human before sending. "
                "Return only valid JSON."
            ),
            user=json.dumps(prompt),
        )
        try:
            return GeneratedReply.model_validate(data)
        except ValidationError as exc:
            raise AIProviderError(f"Groq reply response failed validation: {exc}") from exc

    def _chat_json(self, system: str, user: str) -> dict:
        url = f"{self.settings.groq_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.groq_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.settings.groq_api_key}"}

        try:
            with httpx.Client(timeout=self.settings.groq_timeout_seconds) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AIProviderError(f"Groq API request failed: {exc}") from exc

        content = response.json()["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIProviderError("Groq API response was not valid JSON.") from exc


def build_ai_client(settings: Settings) -> LLMClient:
    if settings.ai_provider == "groq":
        return GroqLLMClient(settings)
    return HeuristicLLMClient()
