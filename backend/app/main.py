from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analytics, demo, knowledge_base, settings as settings_route, tickets
from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.services.demo_data import seed_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)
    init_db()
    if settings.seed_demo_data:
        with SessionLocal() as db:
            seed_database(db, settings)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Human-in-the-loop AI support operations platform.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router, prefix=settings.api_prefix)
app.include_router(knowledge_base.router, prefix=settings.api_prefix)
app.include_router(analytics.router, prefix=settings.api_prefix)
app.include_router(demo.router, prefix=settings.api_prefix)
app.include_router(settings_route.router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
