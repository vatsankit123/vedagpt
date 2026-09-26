"""
Deterministic embedding document construction strategies.

Strategy A: TRANSLATION_ONLY
Strategy B: TRANSLITERATION_AND_TRANSLATION
Strategy C: TRANSLATION_AND_COMMENTARY
Strategy D: CONTEXT_WINDOW

Requirements:
  - Every strategy is deterministic (same input → same output).
  - Empty optional fields are cleanly omitted.
  - Licensing text is never embedded.
  - Operational metadata is never embedded.
  - Translation remains distinguishable from commentary.
"""
from __future__ import annotations

from typing import Any, Literal

from app.corpus.errors import DocumentBuildError

DocumentStrategy = Literal[
    "translation",
    "transliteration_and_translation",
    "translation_and_commentary",
    "context_window",
]

VALID_STRATEGIES: set[str] = {
    "translation",
    "transliteration_and_translation",
    "translation_and_commentary",
    "context_window",
}


def _record_header(record: dict[str, Any]) -> str:
    scripture = str(record.get("scripture", "")).strip()
    chapter = record.get("chapter", "")
    verse = record.get("verse", "")
    ve = record.get("verse_end")
    verse_str = f"{verse}" if not ve else f"{verse}-{ve}"
    return f"Scripture: {scripture}\nChapter: {chapter}\nVerse: {verse_str}"


def build_translation_only(record: dict[str, Any]) -> str:
    """Strategy A: Header + translation only."""
    translation = str(record.get("translation", "")).strip()
    if not translation:
        raise DocumentBuildError(
            f"Cannot build translation-only document for record {record.get('id')!r}: "
            "translation is empty."
        )
    return f"{_record_header(record)}\nTranslation: {translation}"


def build_transliteration_and_translation(record: dict[str, Any]) -> str:
    """Strategy B: Header + optional transliteration + translation."""
    translation = str(record.get("translation", "")).strip()
    if not translation:
        raise DocumentBuildError(
            f"Cannot build document for record {record.get('id')!r}: translation is empty."
        )
    parts = [_record_header(record)]
    tlit = str(record.get("transliteration", "")).strip()
    if tlit:
        parts.append(f"Transliteration: {tlit}")
    parts.append(f"Translation: {translation}")
    return "\n".join(parts)


def build_translation_and_commentary(record: dict[str, Any]) -> str:
    """Strategy C: Header + translation + optional commentary."""
    translation = str(record.get("translation", "")).strip()
    if not translation:
        raise DocumentBuildError(
            f"Cannot build document for record {record.get('id')!r}: translation is empty."
        )
    parts = [_record_header(record), f"Translation: {translation}"]
    commentary = str(record.get("commentary", "")).strip()
    if commentary:
        parts.append(f"Commentary: {commentary}")
    return "\n".join(parts)


def build_context_window(
    record: dict[str, Any],
    all_records: list[dict[str, Any]],
    window_size: int = 1,
) -> str:
    """Strategy D: Surrounding context + current verse as primary citation.

    The current verse is always the primary citation record.
    Context boundaries for first and last verses are handled safely.
    """
    translation = str(record.get("translation", "")).strip()
    if not translation:
        raise DocumentBuildError(
            f"Cannot build context document for record {record.get('id')!r}: "
            "translation is empty."
        )

    # Find records in the same chapter, sorted by verse.
    ch = record.get("chapter")
    vs = record.get("verse")
    same_ch = sorted(
        [r for r in all_records if r.get("chapter") == ch],
        key=lambda r: r.get("verse", 0),
    )
    current_idx = next(
        (i for i, r in enumerate(same_ch) if r.get("verse") == vs), None
    )

    parts: list[str] = []

    if current_idx is not None:
        start = max(0, current_idx - window_size)
        end = min(len(same_ch), current_idx + window_size + 1)
        for idx in range(start, end):
            ctx = same_ch[idx]
            ctx_vs = ctx.get("verse", "?")
            ctx_trans = str(ctx.get("translation", "")).strip()
            if idx == current_idx:
                parts.append(f"[PRIMARY] Verse {ctx_vs}: {ctx_trans}")
            elif ctx_trans:
                parts.append(f"[CONTEXT] Verse {ctx_vs}: {ctx_trans}")
    else:
        # Fallback: just the primary record.
        parts.append(f"[PRIMARY] Verse {vs}: {translation}")

    header = _record_header(record)
    return f"{header}\n" + "\n".join(parts)


def build_document(
    record: dict[str, Any],
    strategy: DocumentStrategy,
    all_records: list[dict[str, Any]] | None = None,
    context_window_size: int = 1,
) -> str:
    """Dispatch to the correct strategy.

    Args:
        record:              The verse record dict.
        strategy:            One of the VALID_STRATEGIES.
        all_records:         Required only for context_window strategy.
        context_window_size: Number of verses before/after for context window.

    Returns:
        Deterministic string to be embedded.

    Raises:
        DocumentBuildError: If the strategy is unknown or required fields are missing.
    """
    if strategy not in VALID_STRATEGIES:
        raise DocumentBuildError(
            f"Unknown document strategy: {strategy!r}. "
            f"Valid strategies: {sorted(VALID_STRATEGIES)}"
        )

    if strategy == "translation":
        return build_translation_only(record)
    elif strategy == "transliteration_and_translation":
        return build_transliteration_and_translation(record)
    elif strategy == "translation_and_commentary":
        return build_translation_and_commentary(record)
    elif strategy == "context_window":
        if all_records is None:
            raise DocumentBuildError(
                "context_window strategy requires all_records to be provided."
            )
        return build_context_window(record, all_records, context_window_size)
    # Should not reach here.
    raise DocumentBuildError(f"Unhandled strategy: {strategy!r}")
