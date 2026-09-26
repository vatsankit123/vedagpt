"""Tests for CorpusRecord schema."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.corpus.models import CorpusRecord


def _valid() -> dict:
    return {
        "id": "gita-2-47",
        "source_id": "test-source-v1",
        "scripture": "Bhagavad Gita",
        "chapter": 2,
        "verse": 47,
        "translation": "DEMO: You have a right to perform your prescribed duties.",
        "translator": "T. Translator",
        "edition": "2nd Edition",
        "source_reference": "https://example.com/gita/2/47",
        "copyright_status": "DEMO_DATA_NOT_FOR_PRODUCTION",
        "record_version": 1,
        "review_status": "PENDING",
    }


def test_valid_record_accepted():
    r = CorpusRecord.model_validate(_valid())
    assert r.id == "gita-2-47"
    assert r.chapter == 2
    assert r.verse == 47


def test_missing_id_rejected():
    data = _valid()
    del data["id"]
    with pytest.raises(ValidationError):
        CorpusRecord.model_validate(data)


def test_empty_id_rejected():
    data = _valid()
    data["id"] = ""
    with pytest.raises(ValidationError):
        CorpusRecord.model_validate(data)


def test_missing_source_id_rejected():
    data = _valid()
    data["source_id"] = ""
    with pytest.raises(ValidationError):
        CorpusRecord.model_validate(data)


def test_invalid_chapter_rejected():
    data = _valid()
    data["chapter"] = 0
    with pytest.raises(ValidationError):
        CorpusRecord.model_validate(data)


def test_negative_chapter_rejected():
    data = _valid()
    data["chapter"] = -1
    with pytest.raises(ValidationError):
        CorpusRecord.model_validate(data)


def test_invalid_verse_rejected():
    data = _valid()
    data["verse"] = 0
    with pytest.raises(ValidationError):
        CorpusRecord.model_validate(data)


def test_invalid_verse_range_rejected():
    data = _valid()
    data["verse"] = 47
    data["verse_end"] = 46  # end < start
    with pytest.raises(ValidationError):
        CorpusRecord.model_validate(data)


def test_valid_verse_range_accepted():
    data = _valid()
    data["verse_end"] = 49
    r = CorpusRecord.model_validate(data)
    assert r.verse_end == 49


def test_missing_translation_rejected():
    data = _valid()
    data["translation"] = ""
    with pytest.raises(ValidationError):
        CorpusRecord.model_validate(data)


def test_whitespace_translation_rejected():
    data = _valid()
    data["translation"] = "   "
    with pytest.raises(ValidationError):
        CorpusRecord.model_validate(data)


def test_invalid_review_status_rejected():
    data = _valid()
    data["review_status"] = "APPROVED"  # Not a valid status.
    with pytest.raises(ValidationError):
        CorpusRecord.model_validate(data)


def test_demo_record_is_demo():
    r = CorpusRecord.model_validate(_valid())
    assert r.is_demo() is True


def test_production_ready_false_for_demo():
    r = CorpusRecord.model_validate(_valid())
    assert r.is_production_ready() is False


def test_invalid_reviewed_date_format_rejected():
    data = _valid()
    data["reviewed_date"] = "01-15-2024"
    with pytest.raises(ValidationError):
        CorpusRecord.model_validate(data)


def test_valid_reviewed_date_accepted():
    data = _valid()
    data["reviewed_date"] = "2024-01-15"
    r = CorpusRecord.model_validate(data)
    assert r.reviewed_date == "2024-01-15"
