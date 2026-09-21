"""
Citation validator.

All citation objects are built from Qdrant retrieval metadata — never from LLM
output.  This module validates that the constructed citations are internally
consistent and free of invented identifiers.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.chat import SourceCitation

logger = logging.getLogger(__name__)


class CitationValidationError(Exception):
    """Raised when citation validation cannot produce a safe result."""


def build_citations_from_passages(
    passages: list[dict[str, Any]],
) -> list[SourceCitation]:
    """Convert raw Qdrant payload dicts into validated SourceCitation objects.

    Rules enforced:
    1. Empty or malformed payload records are skipped with a warning.
    2. Duplicate document_ids are deduplicated (first occurrence wins).
    3. chapter and verse must be positive integers.
    4. Returns an empty list if no passages pass validation.

    This function MUST NOT receive LLM-generated text as input.
    """
    seen_ids: set[str] = set()
    citations: list[SourceCitation] = []

    for passage in passages:
        doc_id = passage.get("document_id", "").strip()
        if not doc_id:
            logger.warning("Skipping passage with missing document_id.")
            continue

        if doc_id in seen_ids:
            logger.debug("Deduplicating citation for '%s'.", doc_id)
            continue

        chapter = passage.get("chapter")
        verse = passage.get("verse")
        score = passage.get("retrieval_score", 0.0)

        # Validate chapter and verse are positive integers.
        try:
            chapter_int = int(chapter)
            verse_int = int(verse)
        except (TypeError, ValueError):
            logger.warning(
                "Skipping '%s': chapter/verse are not valid integers (%s, %s).",
                doc_id,
                chapter,
                verse,
            )
            continue

        if chapter_int <= 0 or verse_int <= 0:
            logger.warning(
                "Skipping '%s': chapter (%d) or verse (%d) is not positive.",
                doc_id,
                chapter_int,
                verse_int,
            )
            continue

        seen_ids.add(doc_id)
        citations.append(
            SourceCitation(
                document_id=doc_id,
                scripture=passage.get("scripture", ""),
                chapter=chapter_int,
                verse=verse_int,
                translation=passage.get("translation", ""),
                translator=passage.get("translator", ""),
                edition=passage.get("edition", ""),
                source_reference=passage.get("source_reference", ""),
                retrieval_score=float(score),
            )
        )

    logger.debug("Built %d valid citation(s) from %d passage(s).", len(citations), len(passages))
    return citations


def validate_response_citations(
    grounded: bool,
    citations: list[SourceCitation],
    retrieved_ids: set[str],
) -> list[SourceCitation]:
    """Final consistency check before citations are returned in the API response.

    Rules:
    1. If grounded is True, there must be at least one citation.
    2. If grounded is False, no citations should be returned.
    3. Every citation's document_id must be in the retrieved_ids set.

    Args:
        grounded:      Whether the answer was grounded in retrieved passages.
        citations:     Citations produced by build_citations_from_passages().
        retrieved_ids: Set of document_ids that were actually retrieved from Qdrant.

    Returns:
        A filtered, validated list of SourceCitation objects.

    Raises:
        CitationValidationError: If grounded=True but no valid citations remain.
    """
    if not grounded:
        if citations:
            logger.warning(
                "Dropping %d citation(s) from an ungrounded response.",
                len(citations),
            )
        return []

    # Remove any citation whose ID was not actually retrieved.
    valid = [c for c in citations if c.document_id in retrieved_ids]
    invented = [c for c in citations if c.document_id not in retrieved_ids]

    if invented:
        logger.error(
            "Rejected %d citation(s) with IDs not present in retrieval results: %s",
            len(invented),
            [c.document_id for c in invented],
        )

    if grounded and not valid:
        raise CitationValidationError(
            "Response is marked grounded but no valid citations could be constructed "
            "from the retrieved passages."
        )

    return valid
