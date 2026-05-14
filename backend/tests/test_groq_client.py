import json

import pytest

from app.core.config import Settings
from app.models import Ticket, TicketCategory, TicketPriority, TicketSentiment
from app.services import ai_client
from app.services.ai_client import AIProviderError, GroqLLMClient


def test_groq_requires_api_key() -> None:
    with pytest.raises(AIProviderError):
        GroqLLMClient(Settings(ai_provider="groq", groq_api_key=None))


def test_groq_classification_parses_valid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_payload = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "category": "technical",
                                    "sentiment": "frustrated",
                                    "priority": "medium",
                                    "confidence": 0.88,
                                    "issue_pattern": "Webhook delivery delay",
                                    "summary": "Customer reports delayed webhook delivery.",
                                }
                            )
                        }
                    }
                ]
            }

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, url: str, headers: dict, json: dict) -> FakeResponse:
            captured_payload["url"] = url
            captured_payload["headers"] = headers
            captured_payload["json"] = json
            return FakeResponse()

    monkeypatch.setattr(ai_client.httpx, "Client", FakeClient)

    client = GroqLLMClient(Settings(ai_provider="groq", groq_api_key="test-key"))
    analysis = client.analyze_ticket(
        Ticket(
            customer_name="Dev",
            email="dev@example.com",
            channel="email",
            message="Webhook events are delayed again.",
        )
    )

    assert captured_payload["headers"]["Authorization"] == "Bearer test-key"
    assert captured_payload["json"]["response_format"] == {"type": "json_object"}
    assert analysis.category == TicketCategory.technical
    assert analysis.sentiment == TicketSentiment.frustrated
    assert analysis.priority == TicketPriority.medium
