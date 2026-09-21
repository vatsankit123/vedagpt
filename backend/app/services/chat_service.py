"""
Chat service — orchestrates the full RAG pipeline.

Flow:
  validate input → normalize question → retrieve passages → assess evidence
  → generate explanation → validate citations → return structured response
"""

from __future__ import annotations

import logging

from app.rag.citation_validator import (
    CitationValidationError,
    build_citations_from_passages,
    validate_response_citations,
)
from app.rag.generator import GenerationError, GeneratorService
from app.rag.retriever import RetrieverService
from app.schemas.chat import ChatResponse, SourceCitation

logger = logging.getLogger(__name__)

_INSUFFICIENT_ANSWER = (
    "I could not find sufficient support for this question in the currently indexed sources."
)


class ChatService:
    """Coordinates retrieval, generation, and citation building for a single chat turn."""

    def __init__(
        self,
        retriever: RetrieverService,
        generator: GeneratorService,
    ) -> None:
        self._retriever = retriever
        self._generator = generator

    def answer(self, question: str, top_k: int = 5) -> ChatResponse:
        """Execute the full RAG pipeline and return a structured response.

        Args:
            question: Validated, non-blank question string.
            top_k:    Number of passages to retrieve.
        """
        # 1. Normalize question (strip outer whitespace; preserve inner).
        normalized = question.strip()

        # 2. Retrieve passages and assess evidence sufficiency.
        retrieval = self._retriever.retrieve(normalized, top_k=top_k)

        if not retrieval.is_sufficient:
            logger.info("Evidence insufficient: %s", retrieval.reason)
            return ChatResponse(
                answer=_INSUFFICIENT_ANSWER,
                grounded=False,
                sources=[],
                message="Insufficient evidence in the indexed corpus.",
            )

        # 3. Build citations directly from retrieved metadata BEFORE generation.
        #    This ensures citations can never be influenced by LLM output.
        retrieved_ids = {p.get("document_id", "") for p in retrieval.passages}
        raw_citations = build_citations_from_passages(retrieval.passages)

        if not raw_citations:
            logger.warning("Passages retrieved but all failed citation validation.")
            return ChatResponse(
                answer=_INSUFFICIENT_ANSWER,
                grounded=False,
                sources=[],
                message="Insufficient evidence in the indexed corpus.",
            )

        # 4. Generate explanation using Gemini (passes retrieved text, not raw IDs).
        try:
            answer_text, is_grounded = self._generator.generate(
                question=normalized,
                passages=retrieval.passages,
            )
        except GenerationError as exc:
            # Provider-level error (quota, auth, network).  The message is
            # safe to log internally but must not be forwarded to API users.
            logger.error("Generation failed (provider error): %s", exc)
            return ChatResponse(
                answer="The generation service is currently unavailable.  Please try again later.",
                grounded=False,
                sources=[],
                message="Generation service error.",
            )
        except Exception as exc:
            logger.error("Generation failed (unexpected): %s", exc)
            return ChatResponse(
                answer="The generation service is currently unavailable.  Please try again later.",
                grounded=False,
                sources=[],
                message="Generation service error.",
            )

        # 5. If the model signalled insufficient evidence despite retrieved passages,
        #    honour the model's decision and drop sources.
        if not is_grounded:
            return ChatResponse(
                answer=answer_text,
                grounded=False,
                sources=[],
                message="Insufficient evidence in the indexed corpus.",
            )

        # 6. Final citation validation — reject any invented IDs.
        try:
            valid_citations = validate_response_citations(
                grounded=True,
                citations=raw_citations,
                retrieved_ids=retrieved_ids,
            )
        except CitationValidationError as exc:
            logger.error("Citation validation failed: %s", exc)
            return ChatResponse(
                answer=_INSUFFICIENT_ANSWER,
                grounded=False,
                sources=[],
                message="Citation validation failed.  Please contact support.",
            )

        return ChatResponse(
            answer=answer_text,
            grounded=True,
            sources=valid_citations,
            message=None,
        )
