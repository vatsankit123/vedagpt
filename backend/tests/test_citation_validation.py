"""
Tests for citation building and validation.
"""

from __future__ import annotations

import pytest

from app.rag.citation_validator import (
    CitationValidationError,
    build_citations_from_passages,
    validate_response_citations,
)

DEMO_PASSAGE = {
    "document_id": "gita-2-47",
    "scripture": "Bhagavad Gita",
    "chapter": 2,
    "verse": 47,
    "translation": "DEMO translation.",
    "translator": "DEMO_TRANSLATOR",
    "edition": "DEMO_EDITION",
    "source_reference": "DEMO",
    "retrieval_score": 0.85,
}


# ── build_citations_from_passages ─────────────────────────────────────────────

def test_builds_citation_from_valid_passage():
    citations = build_citations_from_passages([DEMO_PASSAGE])
    assert len(citations) == 1
    c = citations[0]
    assert c.document_id == "gita-2-47"
    assert c.chapter == 2
    assert c.verse == 47
    assert c.retrieval_score == pytest.approx(0.85)


def test_deduplicates_same_document_id():
    """Two passages with the same document_id should produce only one citation."""
    passages = [DEMO_PASSAGE, {**DEMO_PASSAGE, "retrieval_score": 0.70}]
    citations = build_citations_from_passages(passages)
    assert len(citations) == 1


def test_skips_missing_document_id():
    """Passage without document_id must be skipped silently (warning only)."""
    bad = {**DEMO_PASSAGE, "document_id": ""}
    citations = build_citations_from_passages([bad])
    assert citations == []


def test_skips_non_positive_chapter():
    """Chapter=0 must be rejected."""
    bad = {**DEMO_PASSAGE, "chapter": 0}
    citations = build_citations_from_passages([bad])
    assert citations == []


def test_skips_non_positive_verse():
    """Verse=-1 must be rejected."""
    bad = {**DEMO_PASSAGE, "verse": -1}
    citations = build_citations_from_passages([bad])
    assert citations == []


def test_skips_non_integer_chapter():
    """Non-integer chapter must be rejected."""
    bad = {**DEMO_PASSAGE, "chapter": "two"}
    citations = build_citations_from_passages([bad])
    assert citations == []


def test_empty_passages_returns_empty_list():
    citations = build_citations_from_passages([])
    assert citations == []


# ── validate_response_citations ───────────────────────────────────────────────

def test_valid_grounded_citations_pass():
    citations = build_citations_from_passages([DEMO_PASSAGE])
    retrieved_ids = {"gita-2-47"}
    valid = validate_response_citations(True, citations, retrieved_ids)
    assert len(valid) == 1
    assert valid[0].document_id == "gita-2-47"


def test_invented_citation_id_is_rejected():
    """A citation whose document_id was NOT in retrieval results must be rejected."""
    citations = build_citations_from_passages([DEMO_PASSAGE])
    # Pretend nothing was actually retrieved.
    retrieved_ids: set[str] = set()
    # grounded=True but no valid citations remain → CitationValidationError
    with pytest.raises(CitationValidationError):
        validate_response_citations(True, citations, retrieved_ids)


def test_ungrounded_response_returns_no_citations():
    """When grounded=False, all citations must be dropped."""
    citations = build_citations_from_passages([DEMO_PASSAGE])
    result = validate_response_citations(False, citations, {"gita-2-47"})
    assert result == []


def test_grounded_response_must_have_at_least_one_citation():
    """grounded=True with zero citations must raise CitationValidationError."""
    with pytest.raises(CitationValidationError):
        validate_response_citations(True, [], {"gita-2-47"})


def test_multiple_citations_deduplicated_by_build_step():
    """build_citations step already deduplicates; validate step must not re-add."""
    passages = [DEMO_PASSAGE, {**DEMO_PASSAGE, "retrieval_score": 0.6}]
    citations = build_citations_from_passages(passages)
    assert len(citations) == 1
    valid = validate_response_citations(True, citations, {"gita-2-47"})
    assert len(valid) == 1
