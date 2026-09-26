"""Tests for deterministic content hashing."""
from __future__ import annotations

from app.corpus.hashing import compute_content_hash, verify_content_hash


def _rec() -> dict:
    return {
        "id": "gita-2-47",
        "source_id": "test-src",
        "scripture": "Bhagavad Gita",
        "chapter": 2,
        "verse": 47,
        "verse_end": None,
        "translation": "DEMO translation",
        "commentary": "",
        "translator": "Test Translator",
        "edition": "Test Edition",
        "sanskrit": "",
        "transliteration": "",
        "commentator": "",
    }


def test_hash_is_64_chars():
    h = compute_content_hash(_rec())
    assert len(h) == 64


def test_hash_is_hex():
    h = compute_content_hash(_rec())
    assert all(c in "0123456789abcdef" for c in h)


def test_hash_is_deterministic():
    r = _rec()
    assert compute_content_hash(r) == compute_content_hash(r)


def test_different_translation_different_hash():
    r1 = _rec()
    r2 = {**_rec(), "translation": "DEMO different translation"}
    assert compute_content_hash(r1) != compute_content_hash(r2)


def test_volatile_fields_excluded_from_hash():
    """Adding ingestion timestamp or run ID must not change the hash."""
    r1 = _rec()
    r2 = {**_rec(), "ingestion_timestamp": "2024-01-01T00:00:00Z", "run_id": "abc123"}
    assert compute_content_hash(r1) == compute_content_hash(r2)


def test_verify_content_hash_passes():
    r = _rec()
    h = compute_content_hash(r)
    assert verify_content_hash(r, h) is True


def test_verify_content_hash_fails_after_change():
    r = _rec()
    h = compute_content_hash(r)
    r["translation"] = "Changed translation"
    assert verify_content_hash(r, h) is False


def test_hash_chapter_integer_vs_string_same():
    r1 = _rec()
    r2 = {**_rec(), "chapter": 2}  # integer
    # Both should produce same hash since normalizer coerces to int.
    assert compute_content_hash(r1) == compute_content_hash(r2)


def test_none_verse_end_included():
    r1 = _rec()
    r2 = {**_rec(), "verse_end": None}
    assert compute_content_hash(r1) == compute_content_hash(r2)


def test_verse_end_changes_hash():
    r1 = _rec()
    r2 = {**_rec(), "verse_end": 49}
    assert compute_content_hash(r1) != compute_content_hash(r2)
