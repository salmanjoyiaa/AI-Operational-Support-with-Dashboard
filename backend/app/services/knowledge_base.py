from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import KnowledgeArticle

try:
    import chromadb
except ImportError:  # pragma: no cover - dependency is installed through requirements in normal use
    chromadb = None

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover - optional dependency for Gemini embeddings
    genai = None
    types = None


@dataclass(frozen=True)
class KnowledgeBaseMatch:
    article_id: int
    title: str
    category: str
    relevance_score: float
    excerpt: str


class EmbeddingBackend(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class HashingEmbeddingBackend:
    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(document) for document in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class GeminiEmbeddingBackend:
    def __init__(self, settings: Settings) -> None:
        if genai is None:
            raise RuntimeError(
                "Gemini embeddings require the google-genai package. Install backend requirements first."
            )
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required when embedding_provider=gemini.")
        self.model = settings.gemini_embedding_model
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text, task_type="retrieval_document") for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text, task_type="retrieval_query")

    def _embed(self, text: str, task_type: str) -> list[float]:
        try:
            response = self.client.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(task_type=task_type),
            )
        except Exception as exc:  # pragma: no cover - network and SDK failures are environment dependent
            raise RuntimeError(f"Gemini embedding request failed: {exc}") from exc

        embedding = self._extract_embedding(response)
        if not embedding:
            raise RuntimeError("Gemini embedding response did not include vector values.")
        return embedding

    @staticmethod
    def _extract_embedding(response: object) -> list[float]:
        embedding: object | None = None
        if isinstance(response, dict):
            embedding = response.get("embedding")
            if embedding is None:
                embeddings = response.get("embeddings")
                if isinstance(embeddings, list) and embeddings:
                    embedding = embeddings[0]
        else:
            embedding = getattr(response, "embedding", None)
            if embedding is None:
                embeddings = getattr(response, "embeddings", None)
                if isinstance(embeddings, list) and embeddings:
                    embedding = embeddings[0]
                elif embeddings is not None:
                    embedding = embeddings

        if embedding is None:
            raise RuntimeError("Gemini embedding response did not include embeddings.")

        values: object | None
        if isinstance(embedding, dict):
            values = embedding.get("values")
            if values is None:
                values = embedding.get("embedding")
        else:
            values = getattr(embedding, "values", None)
            if values is None:
                values = getattr(embedding, "embedding", None)
            if values is None:
                values = embedding

        return [float(value) for value in values]


class KnowledgeBaseService:
    def __init__(self, settings: Settings) -> None:
        if chromadb is None:
            raise RuntimeError("chromadb is required. Install backend requirements before running the API.")
        self.settings = settings
        Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.chroma_path)
        self.embedding_backend = self._build_embedding_backend(settings)
        self.collection_name = "knowledge_articles"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _build_embedding_backend(self, settings: Settings) -> EmbeddingBackend:
        if settings.embedding_provider == "hashing":
            return HashingEmbeddingBackend()
        if settings.embedding_provider == "gemini":
            return GeminiEmbeddingBackend(settings)
        if settings.gemini_api_key and genai is not None:
            return GeminiEmbeddingBackend(settings)
        return HashingEmbeddingBackend()

    def rebuild_index(self, db: Session) -> None:
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        documents: list[str] = []
        ids: list[str] = []
        metadatas: list[dict[str, str | int]] = []
        articles = list(
            db.scalars(select(KnowledgeArticle).where(KnowledgeArticle.is_active.is_(True)))
        )
        for article in articles:
            for index, chunk in enumerate(chunk_article(article.content)):
                documents.append(chunk)
                ids.append(f"article-{article.id}-chunk-{index}")
                metadatas.append(
                    {
                        "article_id": article.id,
                        "title": article.title,
                        "category": article.category,
                        "chunk_index": index,
                    }
                )
        if documents:
            embeddings = self.embedding_backend.embed_documents(documents)
            self.collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def search(self, db: Session, query: str, top_k: int = 3) -> list[KnowledgeBaseMatch]:
        if self.collection.count() == 0:
            self.rebuild_index(db)
        if self.collection.count() == 0:
            return []

        query_embedding = self.embedding_backend.embed_query(query)
        results = self.collection.query(query_embeddings=[query_embedding], n_results=top_k * 3)
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        deduped: dict[int, KnowledgeBaseMatch] = {}
        for document, metadata, distance in zip(documents, metadatas, distances, strict=False):
            article_id = int(metadata["article_id"])
            score = max(0.0, min(1.0, 1.0 - float(distance)))
            match = KnowledgeBaseMatch(
                article_id=article_id,
                title=str(metadata["title"]),
                category=str(metadata["category"]),
                relevance_score=score,
                excerpt=document,
            )
            existing = deduped.get(article_id)
            if existing is None or match.relevance_score > existing.relevance_score:
                deduped[article_id] = match

        return sorted(deduped.values(), key=lambda item: item.relevance_score, reverse=True)[:top_k]


def chunk_article(content: str, max_words: int = 130) -> list[str]:
    words = content.split()
    if len(words) <= max_words:
        return [content.strip()]
    chunks = []
    for start in range(0, len(words), max_words):
        chunk = " ".join(words[start : start + max_words]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks
