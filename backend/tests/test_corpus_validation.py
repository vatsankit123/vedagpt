"""
Tests for the corpus validation logic in scripts/validate_corpus.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow importing scripts from backend/scripts/.
# __file__ is backend/tests/test_corpus_validation.py
# parents[0] = backend/tests/
# parents[1] = backend/    ← scripts/ lives here
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_corpus import validate_corpus


def _make_record(**overrides) -> dict:
    """Return a minimal valid verse record, optionally overriding fields."""
    base = {
        "id": "gita-1-1",
        "scripture": "Bhagavad Gita",
        "chapter": 1,
        "verse": 1,
        "translation": "A valid translation for testing.",
        "copyright_status": "VERIFIED",
        "translator": "Test Translator",
        "edition": "Test Edition",
    }
    base.update(overrides)
    return base


# ── Passing validations ────────────────────────────────────────────────────────

def test_valid_records_pass():
    """A valid record should produce no errors."""
    records = [_make_record()]
    errors, warnings = validate_corpus(records, allow_demo=False)
    assert errors == []


def test_demo_data_allowed_with_flag():
    """DEMO_DATA_NOT_FOR_PRODUCTION is accepted when allow_demo=True."""
    records = [_make_record(copyright_status="DEMO_DATA_NOT_FOR_PRODUCTION")]
    errors, warnings = validate_corpus(records, allow_demo=True)
    # No error for the copyright status when demo mode is on.
    assert not any("copyright_status" in e for e in errors)


# ── Duplicate ID ──────────────────────────────────────────────────────────────

def test_duplicate_id_is_an_error():
    """Duplicate IDs must produce an error."""
    records = [_make_record(), _make_record()]  # Both have id="gita-1-1"
    errors, _ = validate_corpus(records)
    assert any("Duplicate id" in e for e in errors)


# ── Missing translation ────────────────────────────────────────────────────────

def test_missing_translation_is_an_error():
    """A blank translation must produce an error."""
    records = [_make_record(translation="")]
    errors, _ = validate_corpus(records)
    assert any("translation" in e.lower() for e in errors)


def test_whitespace_only_translation_is_an_error():
    """A whitespace-only translation must produce an error."""
    records = [_make_record(translation="   ")]
    errors, _ = validate_corpus(records)
    assert any("translation" in e.lower() for e in errors)


# ── chapter / verse validation ────────────────────────────────────────────────

def test_zero_chapter_is_an_error():
    records = [_make_record(chapter=0)]
    errors, _ = validate_corpus(records)
    assert any("chapter" in e.lower() for e in errors)


def test_negative_verse_is_an_error():
    records = [_make_record(verse=-1)]
    errors, _ = validate_corpus(records)
    assert any("verse" in e.lower() for e in errors)


def test_non_integer_chapter_is_an_error():
    records = [_make_record(chapter="two")]
    errors, _ = validate_corpus(records)
    assert any("chapter" in e.lower() for e in errors)


# ── Duplicate chapter/verse combination ──────────────────────────────────────

def test_duplicate_chapter_verse_is_an_error():
    """Two records with the same chapter+verse (but different IDs) must error."""
    r1 = _make_record(id="gita-1-1a", chapter=1, verse=1)
    r2 = _make_record(id="gita-1-1b", chapter=1, verse=1)
    errors, _ = validate_corpus([r1, r2])
    assert any("Duplicate chapter/verse" in e for e in errors)


# ── Copyright status ──────────────────────────────────────────────────────────

def test_unverified_status_rejected_in_production():
    """UNVERIFIED copyright_status must produce an error in production mode."""
    records = [_make_record(copyright_status="UNVERIFIED")]
    errors, _ = validate_corpus(records, allow_demo=False)
    assert any("copyright_status" in e for e in errors)


def test_demo_status_rejected_in_production():
    """DEMO_DATA_NOT_FOR_PRODUCTION copyright_status must error in production mode."""
    records = [_make_record(copyright_status="DEMO_DATA_NOT_FOR_PRODUCTION")]
    errors, _ = validate_corpus(records, allow_demo=False)
    assert any("copyright_status" in e for e in errors)


# ── Missing required fields ───────────────────────────────────────────────────

def test_missing_scripture_is_an_error():
    r = _make_record()
    del r["scripture"]
    errors, _ = validate_corpus([r])
    assert any("scripture" in e for e in errors)


def test_missing_id_is_an_error():
    r = _make_record()
    del r["id"]
    errors, _ = validate_corpus([r])
    assert any("id" in e.lower() for e in errors)


# ── Warnings ─────────────────────────────────────────────────────────────────

def test_missing_translator_is_a_warning():
    """Missing translator should produce a warning, not an error."""
    records = [_make_record(translator="")]
    errors, warnings = validate_corpus(records)
    assert errors == []
    assert any("translator" in w.lower() for w in warnings)
