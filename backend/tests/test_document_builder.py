"""Tests for deterministic document construction strategies."""
from __future__ import annotations

import pytest

from app.corpus.document_builder import (
    build_document,
    build_translation_only,
    build_transliteration_and_translation,
    build_translation_and_commentary,
    build_context_window,
    VALID_STRATEGIES,
)
from app.corpus.errors import DocumentBuildError


def _rec(verse=47, trans="DEMO translation", commentary="", tlit="") -> dict:
    return {
        "id": f"gita-2-{verse}",
        "scripture": "Bhagavad Gita",
        "chapter": 2,
        "verse": verse,
        "translation": trans,
        "commentary": commentary,
        "transliteration": tlit,
    }


def test_translation_only_deterministic():
    r = _rec()
    out1 = build_translation_only(r)
    out2 = build_translation_only(r)
    assert out1 == out2


def test_translation_only_contains_header():
    out = build_translation_only(_rec())
    assert "Scripture: Bhagavad Gita" in out
    assert "Chapter: 2" in out
    assert "Verse: 47" in out


def test_translation_only_contains_translation():
    out = build_translation_only(_rec(trans="DEMO specific translation"))
    assert "DEMO specific translation" in out


def test_translation_only_empty_raises():
    with pytest.raises(DocumentBuildError):
        build_translation_only(_rec(trans=""))


def test_transliteration_and_translation_includes_tlit():
    r = _rec(tlit="karmany evadhikaras te")
    out = build_transliteration_and_translation(r)
    assert "karmany evadhikaras te" in out
    assert "Translation:" in out


def test_transliteration_and_translation_omits_empty_tlit():
    r = _rec(tlit="")
    out = build_transliteration_and_translation(r)
    assert "Transliteration:" not in out


def test_translation_and_commentary_includes_commentary():
    r = _rec(commentary="DEMO commentary here")
    out = build_translation_and_commentary(r)
    assert "Commentary: DEMO commentary here" in out


def test_translation_and_commentary_omits_empty_commentary():
    r = _rec(commentary="")
    out = build_translation_and_commentary(r)
    assert "Commentary:" not in out


def test_translation_distinguishable_from_commentary():
    r = _rec(trans="Translation text", commentary="Commentary text")
    out = build_translation_and_commentary(r)
    assert "Translation: Translation text" in out
    assert "Commentary: Commentary text" in out


def test_context_window_primary_verse_marked():
    all_records = [_rec(v) for v in range(46, 50)]
    out = build_context_window(_rec(47), all_records)
    assert "[PRIMARY]" in out
    assert "[CONTEXT]" in out


def test_context_window_first_verse_boundary():
    all_records = [_rec(v) for v in range(1, 5)]
    out = build_context_window(_rec(1, trans="DEMO first"), all_records)
    assert "[PRIMARY]" in out


def test_context_window_last_verse_boundary():
    all_records = [_rec(v) for v in range(1, 5)]
    out = build_context_window(_rec(4, trans="DEMO last"), all_records)
    assert "[PRIMARY]" in out


def test_licensing_not_embedded():
    r = {**_rec(), "license_name": "SECRET LICENSE", "license_reference": "https://secret.com"}
    out = build_translation_only(r)
    assert "SECRET LICENSE" not in out
    assert "secret.com" not in out


def test_unknown_strategy_raises():
    with pytest.raises(DocumentBuildError):
        build_document(_rec(), strategy="unknown_strategy")


def test_context_window_requires_all_records():
    with pytest.raises(DocumentBuildError):
        build_document(_rec(), strategy="context_window", all_records=None)


def test_all_strategies_deterministic():
    r = _rec(commentary="DEMO cmt", tlit="DEMO tlit")
    all_records = [r]
    for strategy in ("translation", "transliteration_and_translation", "translation_and_commentary"):
        out1 = build_document(r, strategy=strategy)
        out2 = build_document(r, strategy=strategy)
        assert out1 == out2, f"Strategy {strategy!r} is not deterministic"


def test_verse_range_in_header():
    r = _rec()
    r["verse_end"] = 49
    out = build_translation_only(r)
    assert "47-49" in out
