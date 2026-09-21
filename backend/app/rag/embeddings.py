"""
Embedding provider abstraction.

Supports:
  - sentence_transformers  (default; runs locally, no API key required)
  - openai                 (requires OPENAI_API_KEY env var)
  - cohere                 (requires COHERE_API_KEY env var)

To add a new provider: subclass EmbeddingProvider and register it in
get_embedding_provider().
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Sequence

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract interface for all embedding providers."""

    @abstractmethod
    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Return a list of embedding vectors, one per input text."""

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string. Convenience wrapper."""
        return self.embed_texts([text])[0]

    @property
    @abstractmethod
    def dimension(self) -> int:
        """The output vector dimension for this provider/model combination."""


# ── Sentence Transformers (local) ─────────────────────────────────────────────


class SentenceTransformerProvider(EmbeddingProvider):
    """Uses a locally downloaded sentence-transformers model.

    Default model: paraphrase-multilingual-MiniLM-L12-v2 (dim=384, ~480 MB).
    This model supports 50+ languages including English and Sanskrit transliteration.

    For higher quality, switch to BAAI/bge-m3 (dim=1024) but ensure the host
    has sufficient RAM/disk.
    """

    def __init__(self, model_name: str, dimension: int) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed.  "
                "Run: pip install sentence-transformers"
            ) from exc

        logger.info("Loading SentenceTransformer model '%s' …", model_name)
        self._model = SentenceTransformer(model_name)
        self._dimension = dimension
        logger.info("SentenceTransformer model loaded (dim=%d).", dimension)

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self._model.encode(list(texts), convert_to_numpy=True)
        return [v.tolist() for v in vectors]

    @property
    def dimension(self) -> int:
        return self._dimension


# ── OpenAI ────────────────────────────────────────────────────────────────────


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Uses the OpenAI embeddings API.

    Requires OPENAI_API_KEY in the environment.
    Default model: text-embedding-3-small (dim=1536).
    """

    def __init__(self, model_name: str = "text-embedding-3-small", dimension: int = 1536) -> None:
        try:
            import openai  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "openai package is not installed.  Run: pip install openai"
            ) from exc
        import os

        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is not set."
            )
        self._client = openai.OpenAI(api_key=api_key)
        self._model_name = model_name
        self._dimension = dimension

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        response = self._client.embeddings.create(input=list(texts), model=self._model_name)
        return [item.embedding for item in response.data]

    @property
    def dimension(self) -> int:
        return self._dimension


# ── Cohere ────────────────────────────────────────────────────────────────────


class CohereEmbeddingProvider(EmbeddingProvider):
    """Uses the Cohere embeddings API.

    Requires COHERE_API_KEY in the environment.
    Default model: embed-multilingual-v3.0 (dim=1024).
    """

    def __init__(self, model_name: str = "embed-multilingual-v3.0", dimension: int = 1024) -> None:
        try:
            import cohere  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "cohere package is not installed.  Run: pip install cohere"
            ) from exc
        import os

        api_key = os.environ.get("COHERE_API_KEY", "")
        if not api_key:
            raise RuntimeError("COHERE_API_KEY environment variable is not set.")
        self._client = cohere.Client(api_key)
        self._model_name = model_name
        self._dimension = dimension

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        response = self._client.embed(
            texts=list(texts),
            model=self._model_name,
            input_type="search_document",
        )
        return list(response.embeddings)

    @property
    def dimension(self) -> int:
        return self._dimension


# ── Factory ───────────────────────────────────────────────────────────────────


def get_embedding_provider(
    provider: str,
    model_name: str,
    dimension: int,
) -> EmbeddingProvider:
    """Return the configured embedding provider instance.

    Args:
        provider:   One of "sentence_transformers", "openai", "cohere".
        model_name: Model identifier understood by the selected provider.
        dimension:  Expected output vector dimension (must match collection config).
    """
    provider_lower = provider.lower().strip()
    if provider_lower == "sentence_transformers":
        return SentenceTransformerProvider(model_name, dimension)
    if provider_lower == "openai":
        return OpenAIEmbeddingProvider(model_name, dimension)
    if provider_lower == "cohere":
        return CohereEmbeddingProvider(model_name, dimension)
    raise ValueError(
        f"Unknown EMBEDDING_PROVIDER '{provider}'.  "
        "Supported values: sentence_transformers, openai, cohere."
    )
