"""
Unit tests for the Gemini GeneratorService provider.

All Gemini SDK calls are mocked — no network access or API key required.
Tests verify:
  - Successful grounded generation.
  - Insufficient-sentinel detection.
  - Empty / blocked response handling.
  - Provider error (quota, network) → GenerationError raised.
  - Missing API key → RuntimeError at construction.
  - SDK not installed → RuntimeError at construction.
  - API key is never exposed in raised exceptions or log output.
  - GeneratorService.generate() signature unchanged (returns tuple[str, bool]).
  - ChatService integration: GenerationError is caught and returns a safe response.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from app.rag.generator import (
    INSUFFICIENT_SENTINEL,
    GenerationError,
    GeneratorService,
    _build_context_block,
    _extract_text,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

DEMO_PASSAGES = [
    {
        "scripture": "Bhagavad Gita",
        "chapter": 2,
        "verse": 47,
        "translation": "DEMO: You have a right to perform your prescribed duties...",
        "commentary": "DEMO: nishkama karma verse.",
    }
]


def _make_gemini_response(text: str) -> MagicMock:
    """Build a MagicMock that mimics a Gemini GenerateContentResponse."""
    response = MagicMock()
    response.text = text
    return response


def _make_generator(
    api_key: str = "test-gemini-key", model: str = "gemini-2.0-flash"
) -> tuple[GeneratorService, MagicMock]:
    """Build a GeneratorService with the Gemini SDK fully mocked at import time.

    The mock modules are injected into sys.modules during __init__ so that
    `google.genai` and `google.genai.types` resolve to MagicMocks.
    After construction, the internal client is returned for per-test control.
    """
    mock_client = MagicMock()
    mock_genai_module = MagicMock()
    mock_genai_module.Client.return_value = mock_client
    mock_types_module = MagicMock()

    # Ensure the google namespace package is also mocked so the sub-imports work.
    google_mock = MagicMock()
    google_mock.genai = mock_genai_module

    with patch.dict(
        sys.modules,
        {
            "google": google_mock,
            "google.genai": mock_genai_module,
            "google.genai.types": mock_types_module,
        },
    ):
        service = GeneratorService(api_key=api_key, model=model)

    # Replace client after construction so tests control generate_content().
    service._client = mock_client
    return service, mock_client


# ── Construction ──────────────────────────────────────────────────────────────

def test_construction_fails_without_api_key():
    """GeneratorService must raise RuntimeError when api_key is empty."""
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        GeneratorService(api_key="", model="gemini-2.0-flash")


def test_construction_fails_if_sdk_not_installed():
    """RuntimeError must be raised when google-genai is not importable."""
    with patch.dict(sys.modules, {"google": None, "google.genai": None, "google.genai.types": None}):
        with pytest.raises((RuntimeError, ImportError)):
            GeneratorService(api_key="test-key", model="gemini-2.0-flash")


# ── Successful generation ─────────────────────────────────────────────────────

def test_generate_returns_grounded_answer():
    """A normal Gemini response should return (answer, True)."""
    service, mock_client = _make_generator()
    expected_answer = "According to the retrieved passage, one should act without attachment."
    mock_client.models.generate_content.return_value = _make_gemini_response(expected_answer)

    answer, is_grounded = service.generate("What is karma yoga?", DEMO_PASSAGES)

    assert answer == expected_answer
    assert is_grounded is True


def test_generate_passes_correct_model():
    """The model identifier from config must be passed to the SDK call."""
    service, mock_client = _make_generator(model="gemini-1.5-pro")
    mock_client.models.generate_content.return_value = _make_gemini_response("An answer.")

    service.generate("question", DEMO_PASSAGES)

    call_kwargs = mock_client.models.generate_content.call_args
    assert call_kwargs is not None
    # Model passed as positional or keyword arg.
    passed_model = (
        call_kwargs.kwargs.get("model")
        or (call_kwargs.args[0] if call_kwargs.args else None)
    )
    assert passed_model == "gemini-1.5-pro"


def test_generate_returns_tuple_str_bool():
    """Return type must always be tuple[str, bool] regardless of answer content."""
    service, mock_client = _make_generator()
    mock_client.models.generate_content.return_value = _make_gemini_response("Some answer.")

    result = service.generate("question", DEMO_PASSAGES)

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)
    assert isinstance(result[1], bool)


def test_generate_calls_client_generate_content():
    """generate() must call client.models.generate_content exactly once."""
    service, mock_client = _make_generator()
    mock_client.models.generate_content.return_value = _make_gemini_response("answer")

    service.generate("question", DEMO_PASSAGES)

    mock_client.models.generate_content.assert_called_once()


# ── Insufficient evidence sentinel ────────────────────────────────────────────

def test_generate_detects_insufficient_sentinel():
    """When the model returns the sentinel phrase, is_grounded must be False."""
    service, mock_client = _make_generator()
    mock_client.models.generate_content.return_value = _make_gemini_response(
        INSUFFICIENT_SENTINEL
    )

    answer, is_grounded = service.generate("Unrelated question", DEMO_PASSAGES)

    assert is_grounded is False
    assert INSUFFICIENT_SENTINEL in answer


def test_sentinel_substring_in_longer_response():
    """Sentinel contained in a longer response still marks it as ungrounded."""
    service, mock_client = _make_generator()
    mock_client.models.generate_content.return_value = _make_gemini_response(
        f"Unfortunately, {INSUFFICIENT_SENTINEL}"
    )

    _, is_grounded = service.generate("q", DEMO_PASSAGES)

    assert is_grounded is False


# ── Empty / blocked response ──────────────────────────────────────────────────

def test_empty_response_returns_insufficient():
    """An empty Gemini response must be treated as insufficient evidence."""
    service, mock_client = _make_generator()
    mock_client.models.generate_content.return_value = _make_gemini_response("")

    answer, is_grounded = service.generate("question", DEMO_PASSAGES)

    assert is_grounded is False
    assert answer == INSUFFICIENT_SENTINEL


def test_blocked_response_returns_insufficient():
    """A blocked response (response.text raises) must return insufficient."""
    service, mock_client = _make_generator()

    blocked_response = MagicMock()
    # Simulate a blocked response where .text raises ValueError.
    type(blocked_response).text = PropertyMock(side_effect=ValueError("blocked"))
    blocked_response.candidates = []
    mock_client.models.generate_content.return_value = blocked_response

    answer, is_grounded = service.generate("question", DEMO_PASSAGES)

    assert is_grounded is False


# ── Provider errors ────────────────────────────────────────────────────────────

def test_provider_network_error_raises_generation_error():
    """A network or quota error from the SDK must be wrapped in GenerationError."""
    service, mock_client = _make_generator()
    mock_client.models.generate_content.side_effect = ConnectionError("Network unreachable")

    with pytest.raises(GenerationError):
        service.generate("question", DEMO_PASSAGES)


def test_provider_auth_error_raises_generation_error():
    """An auth error must be wrapped in GenerationError."""
    service, mock_client = _make_generator()
    mock_client.models.generate_content.side_effect = PermissionError("invalid credentials")

    with pytest.raises(GenerationError):
        service.generate("question", DEMO_PASSAGES)


def test_provider_error_message_does_not_contain_api_key():
    """GenerationError must not expose the API key in its message."""
    service, mock_client = _make_generator(api_key="super-secret-key-12345")
    mock_client.models.generate_content.side_effect = RuntimeError("auth failed")

    with pytest.raises(GenerationError) as exc_info:
        service.generate("question", DEMO_PASSAGES)

    assert "super-secret-key-12345" not in str(exc_info.value)


# ── Context block builder ─────────────────────────────────────────────────────

def test_build_context_block_contains_passage_fields():
    """The XML context block must include scripture, chapter, verse, translation."""
    block = _build_context_block(DEMO_PASSAGES)
    assert "<sources>" in block
    assert "<scripture>Bhagavad Gita</scripture>" in block
    assert "<chapter>2</chapter>" in block
    assert "<verse>47</verse>" in block
    assert "DEMO: You have a right" in block


def test_build_context_block_includes_commentary_when_present():
    """Commentary field must appear in the XML block when non-empty."""
    block = _build_context_block(DEMO_PASSAGES)
    assert "<commentary>" in block


def test_build_context_block_omits_commentary_when_absent():
    """Commentary must be omitted when the field is empty."""
    passages_no_commentary = [{**DEMO_PASSAGES[0], "commentary": ""}]
    block = _build_context_block(passages_no_commentary)
    assert "<commentary>" not in block


def test_build_context_block_multiple_passages():
    """Multiple passages must each appear as a separate <source> element."""
    passages = [
        {**DEMO_PASSAGES[0], "verse": 47},
        {**DEMO_PASSAGES[0], "verse": 48},
    ]
    block = _build_context_block(passages)
    assert "index='1'" in block
    assert "index='2'" in block


# ── _extract_text helper ──────────────────────────────────────────────────────

def test_extract_text_returns_text_from_response():
    """_extract_text must return the response.text value when available."""
    resp = _make_gemini_response("Hello world")
    assert _extract_text(resp) == "Hello world"


def test_extract_text_returns_empty_on_exception():
    """_extract_text must return '' when response.text raises."""
    resp = MagicMock()
    type(resp).text = PropertyMock(side_effect=Exception("blocked"))
    resp.candidates = []
    assert _extract_text(resp) == ""


def test_extract_text_strips_whitespace():
    """_extract_text must strip leading and trailing whitespace."""
    resp = _make_gemini_response("  answer  ")
    assert _extract_text(resp) == "answer"


# ── ChatService integration ────────────────────────────────────────────────────

def test_chat_service_handles_generation_error_gracefully():
    """When GeneratorService raises GenerationError, ChatService returns grounded=False."""
    from app.rag.retriever import RetrieverService, RetrievalResult
    from app.services.chat_service import ChatService

    # Mock retriever that returns sufficient evidence.
    mock_retriever = MagicMock(spec=RetrieverService)
    mock_retriever.retrieve.return_value = RetrievalResult(
        passages=[
            {
                "document_id": "gita-2-47",
                "scripture": "Bhagavad Gita",
                "chapter": 2,
                "verse": 47,
                "translation": "DEMO translation",
                "translator": "DEMO",
                "edition": "DEMO",
                "source_reference": "DEMO",
                "retrieval_score": 0.85,
            }
        ],
        is_sufficient=True,
        reason="",
    )

    # Generator that always raises GenerationError.
    mock_generator = MagicMock()
    mock_generator.generate.side_effect = GenerationError("quota exceeded")

    chat_service = ChatService(retriever=mock_retriever, generator=mock_generator)
    response = chat_service.answer("What is dharma?")

    assert response.grounded is False
    assert response.sources == []
    assert response.message is not None
    # The GenerationError detail must not appear in the user-facing response.
    assert "quota exceeded" not in (response.answer or "")
    assert "quota exceeded" not in (response.message or "")


def test_gemini_not_called_when_evidence_insufficient():
    """GeneratorService must NOT be called when retrieval evidence is insufficient."""
    from app.rag.retriever import RetrieverService, RetrievalResult
    from app.services.chat_service import ChatService

    mock_retriever = MagicMock(spec=RetrieverService)
    mock_retriever.retrieve.return_value = RetrievalResult(
        passages=[],
        is_sufficient=False,
        reason="no passages above threshold",
    )

    mock_generator = MagicMock()
    chat_service = ChatService(retriever=mock_retriever, generator=mock_generator)
    response = chat_service.answer("What is AI?")

    mock_generator.generate.assert_not_called()
    assert response.grounded is False
