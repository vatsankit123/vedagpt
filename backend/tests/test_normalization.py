"""Tests for deterministic corpus normalization."""
from __future__ import annotations

from app.corpus.normalizer import normalize_record, NORMALIZATION_VERSION


def _raw() -> dict:
    return {
        "id": "gita-2-47",
        "source_id": "test-src",
        "scripture": "Bhagavad Gita",
        "chapter": 2,
        "verse": 47,
        "translation": "  DEMO: duty text.  ",
        "commentary": "DEMO: commentary text.",
        "translator": "Test Translator",
        "edition": "Test Edition",
        "language": "English",
        "source_reference": "https://example.com",
        "copyright_status": "DEMO_DATA_NOT_FOR_PRODUCTION",
        "review_status": "PENDING",
        "reviewed_by": "",
        "reviewed_date": "",
        "record_version": 1,
    }


def test_normalization_is_deterministic():
    rec = _raw()
    r1 = normalize_record(rec)
    r2 = normalize_record(rec)
    assert r1 == r2


def test_whitespace_trimmed_in_translation():
    rec = _raw()
    rec["translation"] = "  hello world  "
    r = normalize_record(rec)
    assert r["translation"] == "hello world"


def test_crlf_normalized_to_lf():
    rec = _raw()
    rec["translation"] = "line1\r\nline2"
    r = normalize_record(rec)
    assert "\r" not in r["translation"]
    assert "line1\nline2" == r["translation"]


def test_original_id_preserved():
    r = normalize_record(_raw())
    assert r["id"] == "gita-2-47"


def test_original_source_id_preserved():
    r = normalize_record(_raw())
    assert r["source_id"] == "test-src"


def test_normalization_version_added():
    r = normalize_record(_raw())
    assert r["normalization_version"] == NORMALIZATION_VERSION


def test_content_hash_added():
    r = normalize_record(_raw())
    assert len(r["content_hash"]) == 64


def test_content_hash_is_deterministic():
    r1 = normalize_record(_raw())
    r2 = normalize_record(_raw())
    assert r1["content_hash"] == r2["content_hash"]


def test_translation_not_rewritten():
    rec = _raw()
    rec["translation"] = "DEMO: original translation."
    r = normalize_record(rec)
    assert "DEMO: original translation." in r["translation"]


def test_commentary_kept_separate():
    r = normalize_record(_raw())
    assert r["commentary"] == "DEMO: commentary text."
    assert "DEMO: commentary" not in r["translation"]


def test_chapter_parsed_as_integer():
    rec = _raw()
    rec["chapter"] = "2"
    r = normalize_record(rec)
    assert r["chapter"] == 2
    assert isinstance(r["chapter"], int)


def test_none_optional_field_becomes_empty_string():
    rec = _raw()
    rec["sanskrit"] = None
    r = normalize_record(rec)
    assert r["sanskrit"] == ""
