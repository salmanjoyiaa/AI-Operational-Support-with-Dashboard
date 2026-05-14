from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas import SettingsRead

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsRead)
def read_settings(settings: Settings = Depends(get_settings)) -> SettingsRead:
    return SettingsRead(
        app_name=settings.app_name,
        environment=settings.environment,
        ai_provider=settings.ai_provider,
        groq_model=settings.groq_model,
        embedding_provider=settings.embedding_provider,
        gemini_embedding_model=settings.gemini_embedding_model,
        ai_confidence_threshold=settings.ai_confidence_threshold,
        kb_min_relevance=settings.kb_min_relevance,
    )
