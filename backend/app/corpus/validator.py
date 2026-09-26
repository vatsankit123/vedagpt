"""
Phase 2 corpus validator.

Provides two levels of validation:

1. record_errors(record, allow_demo, production)
   Returns (errors, warnings) for a single raw record dict.

2. validate_corpus_records(records, manifest, profile, allow_demo, production)
   Full corpus-level validation: individual records + cross-record checks.

This module replaces and extends the Phase 1 validate_corpus script logic.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.corpus.models import (
    CopyrightStatus,
    CorpusProfile,
    SourceManifest,
)

PRODUCTION_REJECTED_STATUSES = {"UNVERIFIED", "DEMO_DATA_NOT_FOR_PRODUCTION"}
VALID_COPYRIGHT_STATUSES = {
    "PUBLIC_DOMAIN", "CREATIVE_COMMONS", "LICENSED",
    "ALL_RIGHTS_RESERVED", "UNVERIFIED", "DEMO_DATA_NOT_FOR_PRODUCTION",
}
VALID_REVIEW_STATUSES = {"PENDING", "VERIFIED", "REJECTED"}
MAX_FIELD_LEN = 4096
MAX_TRANSLATION_LEN = 32768
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _has_control_chars(s: str) -> bool:
    for ch in s:
        code = ord(ch)
        if code < 32 and code not in (9, 10, 13):
            return True
    return False


def _has_replacement_char(s: str) -> bool:
    return "\uFFFD" in s


def record_errors(
    record: dict[str, Any],
    allow_demo: bool = False,
    production: bool = False,
) -> tuple[list[str], list[str]]:
    """Validate a single corpus record dict.

    Returns:
        errors:   Blocking problems — ingestion must be rejected.
        warnings: Non-blocking observations.
    """
    errors: list[str] = []
    warnings: list[str] = []
    ref = f"record '{record.get('id', '<unknown>')}'"

    # ── ID ──────────────────────────────────────────────────────────────────
    rid = str(record.get("id", "")).strip()
    if not rid:
        errors.append(f"{ref}: Missing or empty 'id'.")

    # ── Source ID ────────────────────────────────────────────────────────────
    if not str(record.get("source_id", "")).strip():
        errors.append(f"{ref}: Missing or empty 'source_id'.")

    # ── Scripture ─────────────────────────────────────────────────────────────
    if not str(record.get("scripture", "")).strip():
        errors.append(f"{ref}: Missing or empty 'scripture'.")

    # ── Chapter ───────────────────────────────────────────────────────────────
    chapter = record.get("chapter")
    chapter_ok = False
    if chapter is None:
        errors.append(f"{ref}: Missing 'chapter'.")
    else:
        try:
            chapter_int = int(chapter)
            if chapter_int <= 0:
                errors.append(f"{ref}: 'chapter' must be a positive integer, got {chapter_int}.")
            else:
                chapter_ok = True
                chapter = chapter_int
        except (TypeError, ValueError):
            errors.append(f"{ref}: 'chapter' is not a valid integer: {chapter!r}.")

    # ── Verse ─────────────────────────────────────────────────────────────────
    verse = record.get("verse")
    verse_ok = False
    if verse is None:
        errors.append(f"{ref}: Missing 'verse'.")
    else:
        try:
            verse_int = int(verse)
            if verse_int <= 0:
                errors.append(f"{ref}: 'verse' must be a positive integer, got {verse_int}.")
            else:
                verse_ok = True
                verse = verse_int
        except (TypeError, ValueError):
            errors.append(f"{ref}: 'verse' is not a valid integer: {verse!r}.")

    # ── Verse range ───────────────────────────────────────────────────────────
    verse_end = record.get("verse_end")
    if verse_end is not None:
        try:
            ve = int(verse_end)
            if verse_ok and ve < verse:
                errors.append(f"{ref}: 'verse_end' ({ve}) must be >= 'verse' ({verse}).")
        except (TypeError, ValueError):
            errors.append(f"{ref}: 'verse_end' is not a valid integer: {verse_end!r}.")

    # ── Translation ───────────────────────────────────────────────────────────
    translation = record.get("translation", "")
    if not isinstance(translation, str) or not translation.strip():
        errors.append(f"{ref}: 'translation' is empty or whitespace-only.")
    else:
        if len(translation) > MAX_TRANSLATION_LEN:
            warnings.append(f"{ref}: 'translation' is very long ({len(translation)} chars).")
        if _has_control_chars(translation):
            errors.append(f"{ref}: 'translation' contains invalid control characters.")
        if _has_replacement_char(translation):
            warnings.append(f"{ref}: 'translation' contains Unicode replacement character.")

    # ── Commentary not merged into translation ────────────────────────────────
    translation_str = str(record.get("translation", ""))
    commentary_str = str(record.get("commentary", ""))
    if commentary_str and commentary_str.strip() and translation_str.strip():
        # Warn if commentary looks merged (very long translation with no separate commentary)
        if len(translation_str) > 2000 and not commentary_str.strip():
            warnings.append(
                f"{ref}: Very long translation with no commentary — "
                "check that commentary is not merged into the translation field."
            )

    # ── Copyright status ──────────────────────────────────────────────────────
    cs = str(record.get("copyright_status", "")).strip()
    if not cs:
        errors.append(f"{ref}: 'copyright_status' is missing or empty.")
    elif cs not in VALID_COPYRIGHT_STATUSES:
        errors.append(f"{ref}: Unknown 'copyright_status': {cs!r}.")
    elif cs in PRODUCTION_REJECTED_STATUSES and not allow_demo:
        errors.append(
            f"{ref}: copyright_status={cs!r} is not allowed in production. "
            "Use --allow-demo (dev only) to override."
        )

    # ── Review status ─────────────────────────────────────────────────────────
    rs = str(record.get("review_status", "")).strip()
    if rs and rs not in VALID_REVIEW_STATUSES:
        errors.append(f"{ref}: Unknown 'review_status': {rs!r}.")

    # ── Production-only checks ────────────────────────────────────────────────
    if production:
        if not str(record.get("translator", "")).strip():
            errors.append(f"{ref}: 'translator' is required for production ingestion.")
        if not str(record.get("edition", "")).strip():
            errors.append(f"{ref}: 'edition' is required for production ingestion.")
        if not str(record.get("source_reference", "")).strip():
            errors.append(f"{ref}: 'source_reference' is required for production ingestion.")
        if not str(record.get("reviewed_by", "")).strip():
            errors.append(f"{ref}: 'reviewed_by' is required for production ingestion.")
        if not str(record.get("reviewed_date", "")).strip():
            errors.append(f"{ref}: 'reviewed_date' is required for production ingestion.")
        rdate = str(record.get("reviewed_date", "")).strip()
        if rdate and not _ISO_DATE_RE.match(rdate):
            errors.append(f"{ref}: 'reviewed_date' must be YYYY-MM-DD, got {rdate!r}.")
        rv = record.get("record_version")
        if rv is not None:
            try:
                if int(rv) < 1:
                    errors.append(f"{ref}: 'record_version' must be >= 1.")
            except (TypeError, ValueError):
                errors.append(f"{ref}: 'record_version' is not a valid integer.")
    else:
        # Warnings for non-production.
        if not str(record.get("translator", "")).strip():
            warnings.append(f"{ref}: 'translator' is missing. Attribution is encouraged.")
        if not str(record.get("edition", "")).strip():
            warnings.append(f"{ref}: 'edition' is missing. Attribution is encouraged.")

    # ── Field length guards ───────────────────────────────────────────────────
    for fname in ("id", "source_id", "scripture", "translator", "edition",
                  "source_reference", "language"):
        val = str(record.get(fname, ""))
        if len(val) > MAX_FIELD_LEN:
            errors.append(f"{ref}: Field {fname!r} exceeds maximum length ({MAX_FIELD_LEN} chars).")

    # ── Short translation warning ─────────────────────────────────────────────
    if isinstance(translation, str) and 0 < len(translation.strip()) < 10:
        warnings.append(f"{ref}: Translation is suspiciously short ({len(translation.strip())} chars).")

    return errors, warnings


def validate_corpus_records(
    records: list[dict[str, Any]],
    manifest: SourceManifest | None = None,
    profile: CorpusProfile | None = None,
    allow_demo: bool = False,
    production: bool = False,
) -> dict[str, Any]:
    """Full corpus validation: per-record + cross-record checks.

    Returns a summary dict with 'errors', 'warnings', 'stats', and 'chapter_map'.
    """
    all_errors: list[str] = []
    all_warnings: list[str] = []

    seen_ids: set[str] = set()
    seen_cv: dict[str, str] = {}  # "ch:v" → record id
    seen_hashes: dict[str, str] = {}  # hash → record id
    seen_translations: dict[str, str] = {}  # normalized translation → record id
    chapter_map: dict[int, list[int]] = {}  # chapter → [verse numbers]
    source_ids_seen: set[str] = set()

    for i, rec in enumerate(records):
        errs, warns = record_errors(rec, allow_demo=allow_demo, production=production)
        all_errors.extend(errs)
        all_warnings.extend(warns)

        rid = str(rec.get("id", "")).strip() or f"__unknown_{i}__"

        # ── Uniqueness checks ──────────────────────────────────────────────────
        if rid in seen_ids:
            all_errors.append(f"Duplicate record id: {rid!r}.")
        else:
            seen_ids.add(rid)

        try:
            ch = int(rec.get("chapter", 0))
            vs = int(rec.get("verse", 0))
            if ch > 0 and vs > 0:
                cv_key = f"{ch}:{vs}"
                if cv_key in seen_cv:
                    all_errors.append(
                        f"Duplicate chapter/verse {ch}:{vs} in record {rid!r} "
                        f"(first seen in {seen_cv[cv_key]!r})."
                    )
                else:
                    seen_cv[cv_key] = rid
                    chapter_map.setdefault(ch, []).append(vs)
        except (TypeError, ValueError):
            pass

        # ── Source ID consistency ──────────────────────────────────────────────
        sid = str(rec.get("source_id", "")).strip()
        if sid:
            source_ids_seen.add(sid)

        # ── Content hash duplicate detection ──────────────────────────────────
        content_hash = str(rec.get("content_hash", "")).strip()
        if content_hash:
            if content_hash in seen_hashes:
                all_warnings.append(
                    f"Duplicate content hash {content_hash[:16]}… in record {rid!r} "
                    f"(matches {seen_hashes[content_hash]!r})."
                )
            else:
                seen_hashes[content_hash] = rid

        # ── Duplicate translation detection ────────────────────────────────────
        trans = str(rec.get("translation", "")).strip().lower()
        if trans and len(trans) > 20:
            if trans in seen_translations:
                all_warnings.append(
                    f"Duplicate translation text in record {rid!r} "
                    f"(matches {seen_translations[trans]!r})."
                )
            else:
                seen_translations[trans] = rid

    # ── Corpus-level source checks ────────────────────────────────────────────
    if len(source_ids_seen) > 1:
        all_warnings.append(
            f"Multiple source IDs found in corpus: {sorted(source_ids_seen)}. "
            "Ensure all records belong to the same verified edition."
        )

    if manifest:
        for sid in source_ids_seen:
            if sid != manifest.source_id:
                all_errors.append(
                    f"Record source_id {sid!r} does not match manifest source_id "
                    f"{manifest.source_id!r}."
                )

    # ── Chapter completeness checks ───────────────────────────────────────────
    if profile:
        expected_chapters = set(range(1, profile.expected_chapters + 1))
        found_chapters = set(chapter_map.keys())
        missing = sorted(expected_chapters - found_chapters)
        extra = sorted(found_chapters - expected_chapters)
        if missing:
            all_warnings.append(f"Missing chapters: {missing}.")
        if extra:
            all_warnings.append(f"Unexpected chapters: {extra}.")

        # Verse-count validation (when profile has expected_verse_counts).
        for ch_str, expected_count in profile.expected_verse_counts.items():
            ch = int(ch_str)
            actual = len(chapter_map.get(ch, []))
            if actual != expected_count:
                all_warnings.append(
                    f"Chapter {ch}: expected {expected_count} verses, found {actual}. "
                    "Verify whether this is a numbering variant or data issue."
                )

    # ── Gap detection ──────────────────────────────────────────────────────────
    for ch, verses in sorted(chapter_map.items()):
        sorted_v = sorted(verses)
        for a, b in zip(sorted_v, sorted_v[1:]):
            if b - a > 1:
                all_warnings.append(
                    f"Chapter {ch}: suspicious verse number gap between {a} and {b}."
                )

    stats = {
        "total": len(records),
        "errors": len(all_errors),
        "warnings": len(all_warnings),
        "chapters_found": sorted(chapter_map.keys()),
        "source_ids": sorted(source_ids_seen),
        "duplicate_ids_detected": len(records) - len(seen_ids),
        "duplicate_hashes_detected": len(records) - len(seen_hashes),
    }

    return {
        "errors": all_errors,
        "warnings": all_warnings,
        "stats": stats,
        "chapter_map": {ch: sorted(vs) for ch, vs in chapter_map.items()},
    }
