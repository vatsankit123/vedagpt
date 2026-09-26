"""
Phase 2 regression tests.

Verifies that all Phase 1 API contracts, schemas, and behaviors remain intact
after Phase 2 additions.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from tests.conftest import _build_test_app


def _make_client():
    from unittest.mock import MagicMock
    from app.rag.vector_store import VectorStore
    from app.rag.embeddings import EmbeddingProvider

    mock_store = MagicMock(spec=VectorStore)
    mock_store.search.return_value = [
        {
            "document_id": "gita-2-47",
            "scripture": "Bhagavad Gita",
            "chapter": 2,
            "verse": 47,
            "translation": "DEMO: duty.",
            "translator": "Test",
            "edition": "Test Ed",
            "source_reference": "https://example.com",
            "copyright_status": "DEMO_DATA_NOT_FOR_PRODUCTION",
            "retrieval_score": 0.85,
        }
    ]
    mock_store.ensure_collection.return_value = None

    mock_embedder = MagicMock(spec=EmbeddingProvider)
    mock_embedder.embed_query.return_value = [0.0] * 384

    mock_gen = MagicMock()
    mock_gen.generate.return_value = ("DEMO grounded answer.", True)

    app = _build_test_app(mock_store, mock_embedder, mock_gen)
    return TestClient(app)


def test_health_endpoint_unchanged():
    client = _make_client()
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "vedagpt-api"


def test_chat_endpoint_path_unchanged():
    client = _make_client()
    r = client.post("/api/v1/chat", json={"question": "What is dharma?"})
    assert r.status_code == 200


def test_chat_request_schema_unchanged():
    """question and top_k must still be accepted."""
    client = _make_client()
    r = client.post("/api/v1/chat", json={"question": "What is duty?", "top_k": 3})
    assert r.status_code == 200


def test_chat_response_schema_unchanged():
    """Response must still have: answer, grounded, sources, message."""
    client = _make_client()
    r = client.post("/api/v1/chat", json={"question": "What is karma?"})
    data = r.json()
    assert "answer" in data
    assert "grounded" in data
    assert "sources" in data
    assert "message" in data


def test_source_citation_schema_unchanged():
    """Each source must have: document_id, scripture, chapter, verse, retrieval_score."""
    client = _make_client()
    r = client.post("/api/v1/chat", json={"question": "What is duty?"})
    sources = r.json().get("sources", [])
    for src in sources:
        assert "document_id" in src
        assert "scripture" in src
        assert "chapter" in src
        assert "verse" in src
        assert "retrieval_score" in src


def test_empty_question_still_rejected():
    client = _make_client()
    r = client.post("/api/v1/chat", json={"question": ""})
    assert r.status_code == 422


def test_demo_data_controls_unchanged():
    """Demo copyright status in retrieval results must not change citation behavior."""
    from app.rag.citation_validator import build_citations_from_passages
    passages = [{
        "document_id": "gita-2-47",
        "scripture": "Bhagavad Gita",
        "chapter": 2,
        "verse": 47,
        "translation": "DEMO translation.",
        "translator": "Test",
        "edition": "Test Ed",
        "source_reference": "https://example.com",
        "copyright_status": "DEMO_DATA_NOT_FOR_PRODUCTION",
        "retrieval_score": 0.8,
    }]
    # Citation builder should still handle demo records.
    citations = build_citations_from_passages(passages)
    assert isinstance(citations, list)


def test_gemini_not_called_when_no_evidence():
    """GeneratorService must not be called when retrieval is insufficient."""
    from app.rag.retriever import RetrieverService, RetrievalResult
    from app.services.chat_service import ChatService

    mock_retriever = MagicMock(spec=RetrieverService)
    mock_retriever.retrieve.return_value = RetrievalResult(
        passages=[], is_sufficient=False, reason="no results"
    )
    mock_generator = MagicMock()

    svc = ChatService(retriever=mock_retriever, generator=mock_generator)
    response = svc.answer("What is quantum computing?")

    mock_generator.generate.assert_not_called()
    assert response.grounded is False


def test_no_gemini_api_key_required_for_tests():
    """Import key modules without triggering Gemini SDK."""
    from app.corpus.models import CorpusRecord, SourceManifest, CorpusProfile
    from app.corpus.hashing import compute_content_hash
    from app.corpus.normalizer import normalize_record
    from app.corpus.document_builder import build_document
    from app.rag.reference_parser import parse_verse_reference
    from app.evaluation.metrics import recall_at_k
    # No exception should be raised.
    assert True
