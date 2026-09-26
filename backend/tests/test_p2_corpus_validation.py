"""Phase 2 corpus validation tests (supplements existing test_corpus_validation.py)."""
from __future__ import annotations

import pytest

from app.corpus.validator import validate_corpus_records, record_errors
from app.corpus.models import SourceManifest, CorpusProfile


def _demo_rec(id="gita-2-47", chapter=2, verse=47, override=None) -> dict:
    r = {
        "id": id,
        "source_id": "fixture-test-source-v1",
        "scripture": "Bhagavad Gita",
        "chapter": chapter,
        "verse": verse,
        "translation": "DEMO translation text",
        "translator": "Test Translator",
        "edition": "Test Edition",
        "source_reference": "https://example.com",
        "copyright_status": "DEMO_DATA_NOT_FOR_PRODUCTION",
        "review_status": "PENDING",
    }
    if override:
        r.update(override)
    return r


def test_valid_demo_record_passes_with_allow_demo():
    errs, warns = record_errors(_demo_rec(), allow_demo=True)
    assert errs == []


def test_duplicate_id_detected():
    r1 = _demo_rec("gita-2-47")
    r2 = _demo_rec("gita-2-47")
    result = validate_corpus_records([r1, r2], allow_demo=True)
    assert any("Duplicate record id" in e for e in result["errors"])


def test_duplicate_chapter_verse_detected():
    r1 = _demo_rec("gita-2-47", 2, 47)
    r2 = _demo_rec("gita-2-47b", 2, 47)
    result = validate_corpus_records([r1, r2], allow_demo=True)
    assert any("Duplicate chapter/verse" in e for e in result["errors"])


def test_missing_chapter_detected_in_profile():
    profile = CorpusProfile.model_validate({
        "profile_id": "test-profile",
        "scripture": "Bhagavad Gita",
        "source_id": "fixture-test-source-v1",
        "expected_chapters": 2,
    })
    # Only chapter 2 provided, profile expects chapters 1 and 2.
    records = [_demo_rec("gita-2-47", 2, 47)]
    result = validate_corpus_records(records, profile=profile, allow_demo=True)
    assert any("Missing chapters" in w for w in result["warnings"])


def test_inconsistent_source_detected():
    r1 = _demo_rec("gita-2-47", override={"source_id": "source-a"})
    r2 = _demo_rec("gita-2-48", 2, 48, override={"source_id": "source-b"})
    result = validate_corpus_records([r1, r2], allow_demo=True)
    assert any("Multiple source IDs" in w for w in result["warnings"])


def test_source_id_mismatch_with_manifest():
    manifest = SourceManifest.model_validate({
        "source_id": "the-real-source",
        "title": "Bhagavad Gita",
        "translator": "T",
        "edition": "E",
        "source_reference": "https://example.com",
        "copyright_status": "PUBLIC_DOMAIN",
        "license_name": "PD",
        "license_reference": "https://cc.org",
        "redistribution_permitted": True,
        "verification_status": "VERIFIED",
        "verified_by": "R",
        "verified_date": "2024-01-15",
    })
    r = _demo_rec("gita-2-47", override={"source_id": "wrong-source"})
    result = validate_corpus_records([r], manifest=manifest, allow_demo=True)
    assert any("does not match manifest" in e for e in result["errors"])


def test_duplicate_translation_flagged():
    r1 = _demo_rec("gita-2-47", override={"translation": "DEMO same translation text repeated here"})
    r2 = _demo_rec("gita-2-48", 2, 48, override={"translation": "DEMO same translation text repeated here"})
    result = validate_corpus_records([r1, r2], allow_demo=True)
    assert any("Duplicate translation" in w for w in result["warnings"])


def test_empty_translation_is_error():
    r = _demo_rec("gita-2-47", override={"translation": ""})
    errs, _ = record_errors(r, allow_demo=True)
    assert any("translation" in e.lower() for e in errs)


def test_unknown_copyright_status_is_error():
    r = _demo_rec("gita-2-47", override={"copyright_status": "UNKNOWN_STATUS"})
    errs, _ = record_errors(r, allow_demo=True)
    assert any("Unknown" in e for e in errs)


def test_production_requires_reviewer():
    r = _demo_rec("gita-2-47", override={
        "copyright_status": "PUBLIC_DOMAIN",
        "review_status": "VERIFIED",
        "reviewed_by": "",
        "reviewed_date": "2024-01-15",
    })
    errs, _ = record_errors(r, allow_demo=False, production=True)
    assert any("reviewed_by" in e for e in errs)


def test_gap_in_verse_numbering_warned():
    r1 = _demo_rec("gita-2-47", 2, 47)
    r2 = _demo_rec("gita-2-50", 2, 50)  # Gap from 47 to 50.
    result = validate_corpus_records([r1, r2], allow_demo=True)
    assert any("gap" in w.lower() for w in result["warnings"])


def test_stats_totals_correct():
    records = [_demo_rec(f"gita-2-{v}", 2, v) for v in range(47, 52)]
    result = validate_corpus_records(records, allow_demo=True)
    assert result["stats"]["total"] == 5
