"""
Shared pytest fixtures for VedaGPT tests.

All external services (Qdrant, Google Gemini, sentence-transformers) are
mocked so unit tests run without network access or paid API usage.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ── Force test environment before any app imports ─────────────────────────────
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key-not-real")
os.environ.setdefault("ALLOW_UNVERIFIED_DEMO_DATA", "true")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")


# ── Demo passage payloads (DEMO_DATA_NOT_FOR_PRODUCTION) ─────────────────────

DEMO_PASSAGE_1 = {
    "document_id": "gita-2-47",
    "scripture": "Bhagavad Gita",
    "chapter": 2,
    "verse": 47,
    "translation": "DEMO: You have a right to perform your prescribed duties...",
    "translator": "DEMO_TRANSLATOR",
    "edition": "DEMO_EDITION",
    "source_reference": "DEMO",
    "copyright_status": "DEMO_DATA_NOT_FOR_PRODUCTION",
    "retrieval_score": 0.88,
}

DEMO_PASSAGE_2 = {
    "document_id": "gita-3-5",
    "scripture": "Bhagavad Gita",
    "chapter": 3,
    "verse": 5,
    "translation": "DEMO: Everyone is forced to act helplessly...",
    "translator": "DEMO_TRANSLATOR",
    "edition": "DEMO_EDITION",
    "source_reference": "DEMO",
    "copyright_status": "DEMO_DATA_NOT_FOR_PRODUCTION",
    "retrieval_score": 0.72,
}


# ── Shared mock factories ─────────────────────────────────────────────────────

@pytest.fixture()
def mock_embedder():
    """Embedding provider that returns a fixed-size zero vector."""
    embedder = MagicMock()
    embedder.embed_query.return_value = [0.0] * 384
    embedder.embed_texts.return_value = [[0.0] * 384]
    embedder.dimension = 384
    return embedder


@pytest.fixture()
def mock_vector_store():
    """VectorStore that returns demo passages by default."""
    store = MagicMock()
    store.search.return_value = [DEMO_PASSAGE_1, DEMO_PASSAGE_2]
    store.ensure_collection.return_value = None
    store.upsert_records.return_value = None
    store.collection_info.return_value = {
        "collection": "vedagpt_scriptures",
        "vectors_count": 5,
        "status": "green",
    }
    return store


@pytest.fixture()
def mock_generator():
    """GeneratorService that returns a canned grounded answer."""
    generator = MagicMock()
    generator.generate.return_value = (
        "DEMO answer: According to the retrieved passage, one should act without attachment.",
        True,  # is_grounded
    )
    return generator


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear the lru_cache on get_settings before each test so env changes take effect."""
    from app.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _build_test_app(mock_vector_store, mock_embedder, mock_generator):
    """Build a minimal FastAPI app for testing without triggering the real lifespan."""
    from app.rag.retriever import RetrieverService
    from app.schemas.chat import ChatResponse, HealthResponse
    from app.services.chat_service import ChatService
    from app.api.chat import router as chat_router

    # Build services with mocks.
    retriever = RetrieverService(
        vector_store=mock_vector_store,
        embedding_provider=mock_embedder,
        score_threshold=0.30,
        default_top_k=5,
    )
    chat_service = ChatService(retriever=retriever, generator=mock_generator)

    # Create a bare FastAPI app — no lifespan (no real Qdrant or model loading).
    app = FastAPI(title="VedaGPT Test App")

    @app.get("/health", response_model=HealthResponse)
    async def health():
        return HealthResponse(status="ok", service="vedagpt-api")

    app.include_router(chat_router)

    # Inject mocked services into app state (chat router reads from request.app.state).
    app.state.chat_service = chat_service

    return app


@pytest.fixture()
def test_client(mock_vector_store, mock_embedder, mock_generator):
    """TestClient with all external dependencies mocked.

    Services are injected directly into app.state so no real network calls
    are made during unit tests.
    """
    app = _build_test_app(mock_vector_store, mock_embedder, mock_generator)
    with TestClient(app, raise_server_exceptions=True) as client:
        yield client
