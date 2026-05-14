from app.core.config import Settings
from app.models import KnowledgeArticle
from app.core.database import SessionLocal
from app.services.knowledge_base import KnowledgeBaseService


def test_knowledge_base_search_uses_embedding_backend() -> None:
    with SessionLocal() as db:
        article = KnowledgeArticle(
            title="Webhook Delivery Diagnostics",
            category="technical",
            content="Webhook delivery delays require endpoint health checks, retry inspection, and engineering escalation when events stop arriving.",
            source_url="kb://webhook",
        )
        db.add(article)
        db.commit()
        db.refresh(article)

        service = KnowledgeBaseService(Settings(seed_demo_data=False, embedding_provider="hashing"))
        service.rebuild_index(db)
        matches = service.search(db, "Webhook events are delayed again", top_k=1)

    assert matches
    assert matches[0].title == "Webhook Delivery Diagnostics"