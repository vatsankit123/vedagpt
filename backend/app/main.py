"""
VedaGPT FastAPI application entry point.

Startup sequence:
  1. Load and validate configuration.
  2. Initialise the embedding provider (may download model weights).
  3. Connect to Qdrant and ensure the collection exists.
  4. Initialise ChatService and attach to app.state.
  5. Register routers.

Lifespan context manager is used so that resources are cleaned up on shutdown.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.config import get_settings
from app.rag.embeddings import get_embedding_provider
from app.rag.generator import GeneratorService
from app.rag.retriever import RetrieverService
from app.rag.vector_store import VectorStore
from app.schemas.chat import HealthResponse
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise services on startup and release them on shutdown."""
    settings = get_settings()

    # ── Embedding provider ────────────────────────────────────────────────────
    logger.info("Initialising embedding provider '%s' …", settings.embedding_provider)
    try:
        embedder = get_embedding_provider(
            provider=settings.embedding_provider,
            model_name=settings.embedding_model,
            dimension=settings.embedding_dimension,
        )
    except Exception as exc:
        logger.critical("Failed to initialise embedding provider: %s", exc)
        raise

    # ── Qdrant ────────────────────────────────────────────────────────────────
    logger.info("Connecting to Qdrant at '%s' …", settings.qdrant_url)
    try:
        vector_store = VectorStore(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            vector_size=settings.embedding_dimension,
            api_key=settings.qdrant_api_key,
        )
        vector_store.ensure_collection()
    except Exception as exc:
        logger.critical("Failed to connect to Qdrant: %s", exc)
        raise

    # ── Retriever ─────────────────────────────────────────────────────────────
    retriever = RetrieverService(
        vector_store=vector_store,
        embedding_provider=embedder,
        score_threshold=settings.retrieval_score_threshold,
        default_top_k=settings.retrieval_top_k,
    )

    # ── Generator (Gemini) ────────────────────────────────────────────
    if settings.gemini_api_key:
        generator: GeneratorService | None = GeneratorService(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )
    else:
        logger.warning(
            "GEMINI_API_KEY is not set.  "
            "The /api/v1/chat endpoint will return 503 for generation requests."
        )
        generator = None

    # ── Attach services to app state ──────────────────────────────────────────
    if generator is not None:
        app.state.chat_service = ChatService(retriever=retriever, generator=generator)
    else:
        app.state.chat_service = None

    app.state.vector_store = vector_store
    app.state.embedder = embedder

    logger.info("VedaGPT API is ready.")
    yield

    logger.info("VedaGPT API shutting down.")


def create_app() -> FastAPI:
    """Application factory — used by uvicorn and tests."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "VedaGPT Phase 1: Educational scripture Q&A with grounded, traceable citations.\n\n"
            "**Disclaimer**: Responses may contain errors and should be verified against "
            "the cited edition and, where appropriate, qualified scholars.  "
            "This system does not represent every philosophical or religious tradition."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    origins = settings.cors_origins_list
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )

    # ── Health endpoint ───────────────────────────────────────────────────────
    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["health"],
        summary="Health check",
    )
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", service="vedagpt-api")

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(chat_router)

    return app


app = create_app()
