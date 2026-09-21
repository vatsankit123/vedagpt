"""
Tests for RetrieverService — evidence sufficiency and metadata preservation.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.rag.retriever import RetrieverService


def _make_mock_store(hits: list[dict]) -> MagicMock:
    store = MagicMock()
    store.search.return_value = hits
    return store


def _make_mock_embedder() -> MagicMock:
    embedder = MagicMock()
    embedder.embed_query.return_value = [0.0] * 384
    return embedder


DEMO_PASSAGE = {
    "document_id": "gita-2-47",
    "scripture": "Bhagavad Gita",
    "chapter": 2,
    "verse": 47,
    "translation": "DEMO translation",
    "translator": "DEMO_TRANSLATOR",
    "edition": "DEMO_EDITION",
    "retrieval_score": 0.85,
}


# ── Sufficient evidence ───────────────────────────────────────────────────────

def test_retrieval_returns_sufficient_when_above_threshold():
    """Results above threshold → is_sufficient=True."""
    store = _make_mock_store([DEMO_PASSAGE])
    embedder = _make_mock_embedder()
    retriever = RetrieverService(store, embedder, score_threshold=0.30)

    result = retriever.retrieve("What is karma yoga?")

    assert result.is_sufficient is True
    assert len(result.passages) == 1


def test_retrieval_preserves_metadata():
    """Retrieved passages must include all payload fields."""
    store = _make_mock_store([DEMO_PASSAGE])
    embedder = _make_mock_embedder()
    retriever = RetrieverService(store, embedder, score_threshold=0.30)

    result = retriever.retrieve("Duty without attachment")

    passage = result.passages[0]
    assert passage["document_id"] == "gita-2-47"
    assert passage["chapter"] == 2
    assert passage["verse"] == 47
    assert passage["retrieval_score"] == 0.85


# ── Insufficient evidence ─────────────────────────────────────────────────────

def test_no_hits_returns_insufficient():
    """Zero Qdrant results → is_sufficient=False."""
    store = _make_mock_store([])
    embedder = _make_mock_embedder()
    retriever = RetrieverService(store, embedder, score_threshold=0.30)

    result = retriever.retrieve("Some question")

    assert result.is_sufficient is False
    assert result.passages == []


def test_below_threshold_returns_insufficient():
    """All results below threshold → is_sufficient=False."""
    low_score_passage = {**DEMO_PASSAGE, "retrieval_score": 0.10}
    store = _make_mock_store([low_score_passage])
    embedder = _make_mock_embedder()
    retriever = RetrieverService(store, embedder, score_threshold=0.30)

    result = retriever.retrieve("Some question")

    assert result.is_sufficient is False
    assert result.passages == []


def test_mixed_scores_returns_only_above_threshold():
    """Only passages at or above threshold should be returned."""
    high = {**DEMO_PASSAGE, "document_id": "gita-2-47", "retrieval_score": 0.80}
    low = {**DEMO_PASSAGE, "document_id": "gita-3-5", "retrieval_score": 0.10}
    store = _make_mock_store([high, low])
    embedder = _make_mock_embedder()
    retriever = RetrieverService(store, embedder, score_threshold=0.30)

    result = retriever.retrieve("Karma")

    assert result.is_sufficient is True
    assert len(result.passages) == 1
    assert result.passages[0]["document_id"] == "gita-2-47"


def test_top_k_is_respected():
    """Retriever must not return more passages than top_k."""
    passages = [
        {**DEMO_PASSAGE, "document_id": f"gita-{i}-1", "retrieval_score": 0.9}
        for i in range(1, 6)  # 5 passages
    ]
    store = _make_mock_store(passages)
    embedder = _make_mock_embedder()
    retriever = RetrieverService(store, embedder, score_threshold=0.30)

    result = retriever.retrieve("question", top_k=3)

    assert len(result.passages) <= 3
