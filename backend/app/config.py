"""
VedaGPT configuration module.

All settings are loaded from environment variables (via .env file in development).
Validates required variables at import time so misconfiguration surfaces immediately.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = Field(default="VedaGPT API")
    app_env: Literal["development", "production", "test"] = Field(default="development")
    log_level: str = Field(default="INFO")

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Comma-separated allowed origins.  Empty string disables CORS middleware.
    # Do not use '*' in production.
    cors_allowed_origins: str = Field(default="http://localhost:3000,http://localhost:8000")

    # ── Google Gemini ─────────────────────────────────────────────────────────
    gemini_api_key: str = Field(default="")
    # Gemini model identifier — confirm the exact name in your Google AI Studio
    # account.  Do not hard-code an assumed "latest" alias.
    # Example: gemini-2.0-flash, gemini-1.5-pro
    gemini_model: str = Field(default="gemini-2.0-flash")

    # ── Embedding ─────────────────────────────────────────────────────────────
    # Supported providers: "sentence_transformers" | "openai" | "cohere"
    embedding_provider: str = Field(default="sentence_transformers")
    # For sentence_transformers the default is a compact multilingual model.
    # Change to a larger model once the environment can support it.
    embedding_model: str = Field(default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    # Vector dimension MUST match the embedding model output.
    embedding_dimension: int = Field(default=384)

    # ── Qdrant ────────────────────────────────────────────────────────────────
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str = Field(default="")
    qdrant_collection: str = Field(default="vedagpt_scriptures")

    # ── Retrieval ─────────────────────────────────────────────────────────────
    retrieval_top_k: int = Field(default=5)
    # Similarity threshold in [0, 1].  Results below this score are considered
    # insufficient evidence.  Requires evaluation and tuning against a real corpus.
    retrieval_score_threshold: float = Field(default=0.30)

    # ── Safety ────────────────────────────────────────────────────────────────
    # If true, the ingestion pipeline will accept DEMO_DATA_NOT_FOR_PRODUCTION records.
    allow_unverified_demo_data: bool = Field(default=False)
    max_question_length: int = Field(default=1000)

    # ── Derived / computed ────────────────────────────────────────────────────
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"LOG_LEVEL must be one of {valid}, got '{v}'")
        return upper

    @field_validator("retrieval_score_threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("RETRIEVAL_SCORE_THRESHOLD must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def warn_missing_api_key(self) -> "Settings":
        if self.app_env != "test" and not self.gemini_api_key:
            logger.warning(
                "GEMINI_API_KEY is not set.  "
                "The generation service will fail until it is provided."
            )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list, filtering empty strings."""
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    def log_safe_summary(self) -> dict:
        """Return a loggable config summary that never exposes secrets."""
        return {
            "app_name": self.app_name,
            "app_env": self.app_env,
            "gemini_model": self.gemini_model,
            "embedding_provider": self.embedding_provider,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dimension,
            "qdrant_url": self.qdrant_url,
            "qdrant_collection": self.qdrant_collection,
            "retrieval_top_k": self.retrieval_top_k,
            "retrieval_score_threshold": self.retrieval_score_threshold,
            "allow_unverified_demo_data": self.allow_unverified_demo_data,
            "gemini_api_key_set": bool(self.gemini_api_key),
            "qdrant_api_key_set": bool(self.qdrant_api_key),
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    settings = Settings()
    logging.basicConfig(level=settings.log_level)
    logger.info("VedaGPT config loaded: %s", settings.log_safe_summary())
    return settings
