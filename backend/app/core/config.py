from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Support Ops Platform"
    environment: str = "development"
    api_prefix: str = "/api"

    database_url: str = "sqlite:///./data/support_ops.db"
    chroma_path: str = "./data/chroma"

    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    ai_provider: Literal["heuristic", "groq"] = "heuristic"
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout_seconds: float = 30.0

    embedding_provider: Literal["auto", "hashing", "gemini"] = "auto"
    gemini_api_key: str | None = None
    gemini_embedding_model: str = "models/text-embedding-004"

    ai_confidence_threshold: float = 0.72
    kb_min_relevance: float = 0.42
    seed_demo_data: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def data_dir(self) -> Path:
        database_path = self.database_url.replace("sqlite:///", "")
        if database_path.startswith(":memory:"):
            return Path(".")
        return Path(database_path).parent


@lru_cache
def get_settings() -> Settings:
    return Settings()
