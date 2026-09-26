"""
Deterministic verse-reference parser.

Parses explicit scripture references from user input WITHOUT calling Gemini.

Supports:
  - "Bhagavad Gita 2.47"
  - "Gita 2:47"
  - "Gita chapter 2 verse 47"
  - "Chapter 2 verse 47"
  - "What does verse 2.47 say?"
  - "Explain Bhagavad Gita 6.5"

Rules:
  - Returns (chapter, verse) or None.
  - Rejects malformed, ambiguous, or conflicting references.
  - Never substitutes a similar verse for a missing exact reference.
  - Safe against maliciously long input.
  - No LLM dependency.
"""
from __future__ import annotations

import re
from typing import Optional

from app.corpus.errors import ReferenceParseError

MAX_INPUT_LEN = 1000

# Pattern matching common reference forms.
_PATTERNS = [
    # "2.47" or "2:47" with optional "chapter" / "verse" prefix
    re.compile(
        r"\b(?:chapter\s+)?(\d{1,3})[.:\s]+(?:verse\s+)?(\d{1,3})\b",
        re.IGNORECASE,
    ),
    # "chapter 2 verse 47" (loose spacing)
    re.compile(
        r"chapter\s+(\d{1,3})\s+verse\s+(\d{1,3})\b",
        re.IGNORECASE,
    ),
]

# Trigger keywords — require at least one to classify as an explicit reference.
_REFERENCE_TRIGGERS = re.compile(
    r"\b(gita|bhagavad|chapter|verse|\d+[.:]\d+)\b",
    re.IGNORECASE,
)


def parse_verse_reference(text: str) -> Optional[tuple[int, int]]:
    """Parse an explicit verse reference from user input.

    Args:
        text: Raw user question (already validated for max length by API layer).

    Returns:
        (chapter, verse) tuple if exactly one clear reference is found, else None.

    Raises:
        ReferenceParseError: For malformed, overlong, or conflicting input.
    """
    if not text:
        return None
    if len(text) > MAX_INPUT_LEN:
        raise ReferenceParseError(
            f"Input too long for reference parsing ({len(text)} chars; max {MAX_INPUT_LEN})."
        )

    # Quick bail if no reference triggers present.
    if not _REFERENCE_TRIGGERS.search(text):
        return None

    matches: list[tuple[int, int]] = []
    for pattern in _PATTERNS:
        for m in pattern.finditer(text):
            try:
                ch = int(m.group(1))
                vs = int(m.group(2))
            except (IndexError, ValueError):
                continue
            if 1 <= ch <= 18 and 1 <= vs <= 200:
                pair = (ch, vs)
                if pair not in matches:
                    matches.append(pair)

    if not matches:
        return None

    # Conflicting references — report and refuse to guess.
    unique = list(dict.fromkeys(matches))
    if len(unique) > 1:
        raise ReferenceParseError(
            f"Conflicting verse references found: {unique}. "
            "Clarify the specific chapter and verse."
        )

    return unique[0]


def is_explicit_reference(text: str) -> bool:
    """Return True if the text appears to contain an explicit verse reference."""
    try:
        result = parse_verse_reference(text)
        return result is not None
    except ReferenceParseError:
        return True  # Conflicting references still count as explicit.
