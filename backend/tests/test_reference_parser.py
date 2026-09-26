"""Tests for the deterministic verse reference parser."""
from __future__ import annotations

import pytest

from app.rag.reference_parser import parse_verse_reference, is_explicit_reference
from app.corpus.errors import ReferenceParseError


def test_gita_dot_format():
    assert parse_verse_reference("Bhagavad Gita 2.47") == (2, 47)


def test_gita_colon_format():
    assert parse_verse_reference("Gita 2:47") == (2, 47)


def test_chapter_verse_spelled_out():
    assert parse_verse_reference("chapter 2 verse 47") == (2, 47)


def test_what_does_verse_say():
    result = parse_verse_reference("What does verse 2.47 say?")
    assert result == (2, 47)


def test_explain_gita():
    assert parse_verse_reference("Explain Bhagavad Gita 6.5") == (6, 5)


def test_no_reference_returns_none():
    assert parse_verse_reference("What is the meaning of life?") is None


def test_empty_string_returns_none():
    assert parse_verse_reference("") is None


def test_very_long_input_raises():
    with pytest.raises(ReferenceParseError):
        parse_verse_reference("a" * 1001)


def test_conflicting_references_raises():
    with pytest.raises(ReferenceParseError):
        parse_verse_reference("Gita 2.47 and also Gita 3.5")


def test_invalid_chapter_out_of_range_rejected():
    # Chapter 99 is out of range for Bhagavad Gita.
    result = parse_verse_reference("Gita 99.1")
    assert result is None


def test_is_explicit_reference_true():
    assert is_explicit_reference("Gita 2.47") is True


def test_is_explicit_reference_false():
    assert is_explicit_reference("What is karma?") is False


def test_is_explicit_reference_conflicting_still_true():
    # Conflicting references still count as explicit.
    assert is_explicit_reference("Gita 2.47 and Gita 3.5") is True


def test_similar_verse_not_substituted():
    # Parser returns exactly the requested reference, not a nearby one.
    result = parse_verse_reference("Gita 2.47")
    assert result == (2, 47)
    # A different query should not return (2, 47).
    assert parse_verse_reference("What is yoga?") is None
