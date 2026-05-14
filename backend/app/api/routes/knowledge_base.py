from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.services.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


@router.get("/articles", response_model=list[schemas.KnowledgeArticleRead])
def list_articles(db: Session = Depends(get_db)) -> list[models.KnowledgeArticle]:
    return crud.list_articles(db)


@router.post("/articles", response_model=schemas.KnowledgeArticleRead, status_code=201)
def create_article(
    payload: schemas.KnowledgeArticleCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> models.KnowledgeArticle:
    article = crud.create_article(db, payload)
    KnowledgeBaseService(settings).rebuild_index(db)
    return article


@router.get("/articles/{article_id}", response_model=schemas.KnowledgeArticleRead)
def get_article(article_id: int, db: Session = Depends(get_db)) -> models.KnowledgeArticle:
    article = db.get(models.KnowledgeArticle, article_id)
    if article is None or not article.is_active:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/reindex", response_model=dict[str, str])
def rebuild_index(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    KnowledgeBaseService(settings).rebuild_index(db)
    return {"status": "reindexed"}
