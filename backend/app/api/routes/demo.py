from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.services.demo_data import seed_database

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/reset", response_model=dict[str, str])
def reset_demo_data(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    seed_database(db, settings, force=True)
    return {"status": "demo data reset"}
