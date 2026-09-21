"""
Retrieval service.

Embeds the user query and fetches relevant scripture passages from Qdrant.
Evidence sufficiency is assessed here before the generation layer is called.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.rag.embeddings import EmbeddingProvider
from app.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Container returned by the retriever."""

    passages: list[dict[str, Any]] = field(default_factory=list)
    is_sufficient: bool = False
    reason: str = ""


class RetrieverService:
    """Retrieves scripture passages from Qdrant for a given query.

    Evidence sufficiency rules (transparent and configurable):
    1. Zero retrieved results → insufficient.
    2. All results below `score_threshold` → insufficient.

    NOTE: The score_threshold is a first approximation and requires evaluation
    against a real, verified corpus.  It is NOT an accuracy or confidence metric.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        score_threshold: float,
        default_top_k: int = 5,
    ) -> None:
        self._store = vector_store
        self._embedder = embedding_provider
        self._threshold = score_threshold
        self._default_top_k = default_top_k

    def retrieve(self, question: str, top_k: int | None = None) -> RetrievalResult:
        """Embed the question and retrieve the top-k passages.

        Args:
            question: The user's question (already validated by the API layer).
            top_k:    Number of passages to request; falls back to default_top_k.
        """
        k = top_k if top_k is not None else self._default_top_k
        k = max(1, min(k, 20))  # Hard bounds regardless of caller.

        logger.debug("Retrieving top-%d passages (threshold=%.3f).", k, self._threshold)

        query_vector = self._embedder.embed_query(question)

        # Retrieve more than requested and filter locally so we can detect
        # when all candidates are below threshold without re-querying.
        raw_hits = self._store.search(
            query_vector=query_vector,
            top_k=k,
            score_threshold=0.0,  # Get all hits; filter below.
        )

        if not raw_hits:
            logger.info("No passages found for the query.")
            return RetrievalResult(
                passages=[],
                is_sufficient=False,
                reason="No passages found in the indexed corpus.",
            )

        # Filter by threshold.
        above_threshold = [h for h in raw_hits if h.get("retrieval_score", 0.0) >= self._threshold]

        if not above_threshold:
            best = max(raw_hits, key=lambda h: h.get("retrieval_score", 0.0))
            logger.info(
                "Best retrieval score %.3f is below threshold %.3f; marking insufficient.",
                best.get("retrieval_score", 0.0),
                self._threshold,
            )
            return RetrievalResult(
                passages=[],
                is_sufficient=False,
                reason=(
                    f"Retrieved passages did not meet the relevance threshold "
                    f"({self._threshold:.2f}).  Best score: "
                    f"{best.get('retrieval_score', 0.0):.3f}."
                ),
            )

        # Limit to requested k after threshold filtering.
        selected = above_threshold[:k]
        logger.info(
            "Returning %d passage(s) above threshold (threshold=%.3f).",
            len(selected),
            self._threshold,
        )
        return RetrievalResult(
            passages=selected,
            is_sufficient=True,
            reason="",
        )
