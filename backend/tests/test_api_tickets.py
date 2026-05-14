def test_create_ticket_runs_triage_and_keeps_human_review_gate(client) -> None:
    article_response = client.post(
        "/api/knowledge-base/articles",
        json={
            "title": "Webhook Delivery Diagnostics",
            "category": "technical",
            "content": "Webhook delivery issues require event IDs, endpoint health checks, retries, and engineering escalation when delivery is blocked.",
            "source_url": "kb://webhook",
        },
    )
    assert article_response.status_code == 201

    response = client.post(
        "/api/tickets",
        json={
            "customer_name": "Riley Stone",
            "email": "riley@example.com",
            "message": "Webhook events are delayed and our operations team is blocked again.",
            "channel": "email",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "technical"
    assert data["suggested_reply"]
    assert data["status"] in {"triaged", "waiting_human"}
    assert "human review" in data["suggested_reply"].lower()
    assert data["knowledge_matches"]


def test_human_review_can_resolve_ticket(client) -> None:
    client.post(
        "/api/knowledge-base/articles",
        json={
            "title": "Refund Review Workflow",
            "category": "refund",
            "content": "Refunds require human review, identity verification, and billing operations approval before customer commitments.",
            "source_url": "kb://refund",
        },
    )
    create_response = client.post(
        "/api/tickets",
        json={
            "customer_name": "Morgan Lee",
            "email": "morgan@example.com",
            "message": "Please refund the last renewal because we cancelled before the renewal date.",
            "channel": "web",
        },
    )
    ticket_id = create_response.json()["id"]

    review_response = client.post(
        f"/api/tickets/{ticket_id}/human-review",
        json={"action": "resolve", "notes": "Refund reviewed by billing."},
    )

    assert review_response.status_code == 200
    assert review_response.json()["status"] == "resolved"
    assert review_response.json()["human_review_notes"] == "Refund reviewed by billing."
