"""
Corpus validation script.

Validates a Bhagavad Gita JSON corpus file against the VedaGPT schema
before ingestion.  Prints a structured report of all errors and warnings.

Usage:
    python scripts/validate_corpus.py --corpus data/bhagavad_gita.sample.json
    python scripts/validate_corpus.py --corpus data/bhagavad_gita.sample.json --allow-demo

Exit codes:
    0 — validation passed (errors=0)
    1 — validation failed (one or more errors)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# ── Constants ──────────────────────────────────────────────────────────────────

REQUIRED_FIELDS = {"id", "scripture", "chapter", "verse", "translation", "copyright_status"}
PRODUCTION_REJECTED_STATUSES = {"UNVERIFIED", "DEMO_DATA_NOT_FOR_PRODUCTION"}


# ── Validation logic ───────────────────────────────────────────────────────────


def validate_corpus(
    records: list[dict[str, Any]],
    allow_demo: bool = False,
) -> tuple[list[str], list[str]]:
    """Validate a list of corpus records.

    Returns:
        errors:   List of error messages (block ingestion if non-empty).
        warnings: List of warning messages (non-blocking).
    """
    errors: list[str] = []
    warnings: list[str] = []

    seen_ids: set[str] = set()
    seen_chapter_verse: dict[str, str] = {}  # (chapter, verse) → id

    for i, record in enumerate(records):
        idx = f"record[{i}]"

        # ── ID presence and uniqueness ────────────────────────────────────────
        record_id = record.get("id", "").strip()
        if not record_id:
            errors.append(f"{idx}: Missing or empty 'id' field.")
            record_id = f"__unknown_{i}__"
        elif record_id in seen_ids:
            errors.append(f"{idx}: Duplicate id '{record_id}'.")
        else:
            seen_ids.add(record_id)

        ref = f"record '{record_id}'"

        # ── Required fields ───────────────────────────────────────────────────
        for field in REQUIRED_FIELDS - {"id"}:
            if field not in record or record[field] is None:
                errors.append(f"{ref}: Missing required field '{field}'.")

        # ── chapter and verse types ───────────────────────────────────────────
        chapter = record.get("chapter")
        verse = record.get("verse")

        chapter_ok = False
        verse_ok = False

        if chapter is None:
            pass  # Already reported above as missing required field.
        else:
            try:
                chapter = int(chapter)
                if chapter <= 0:
                    errors.append(f"{ref}: 'chapter' must be a positive integer, got {chapter}.")
                else:
                    chapter_ok = True
            except (TypeError, ValueError):
                errors.append(f"{ref}: 'chapter' is not a valid integer: {chapter!r}.")

        if verse is None:
            pass
        else:
            try:
                verse = int(verse)
                if verse <= 0:
                    errors.append(f"{ref}: 'verse' must be a positive integer, got {verse}.")
                else:
                    verse_ok = True
            except (TypeError, ValueError):
                errors.append(f"{ref}: 'verse' is not a valid integer: {verse!r}.")

        # ── Duplicate chapter/verse combinations ──────────────────────────────
        if chapter_ok and verse_ok:
            cv_key = f"{chapter}:{verse}"
            if cv_key in seen_chapter_verse:
                errors.append(
                    f"{ref}: Duplicate chapter/verse combination "
                    f"{chapter}:{verse} (first seen in '{seen_chapter_verse[cv_key]}')."
                )
            else:
                seen_chapter_verse[cv_key] = record_id

        # ── Translation presence ──────────────────────────────────────────────
        translation = record.get("translation", "")
        if isinstance(translation, str) and not translation.strip():
            errors.append(f"{ref}: 'translation' is empty or whitespace only.")

        # ── Copyright status ──────────────────────────────────────────────────
        copyright_status = record.get("copyright_status", "")
        if not copyright_status:
            errors.append(f"{ref}: 'copyright_status' is missing or empty.")
        elif copyright_status in PRODUCTION_REJECTED_STATUSES and not allow_demo:
            errors.append(
                f"{ref}: copyright_status='{copyright_status}' is not allowed "
                "in production ingestion.  "
                "Set ALLOW_UNVERIFIED_DEMO_DATA=true (dev only) to override."
            )

        # ── Translator warning (encouraged but not required) ──────────────────
        if not record.get("translator", "").strip():
            warnings.append(f"{ref}: 'translator' is missing.  Attribution is encouraged.")

        # ── Edition warning ────────────────────────────────────────────────────
        if not record.get("edition", "").strip():
            warnings.append(f"{ref}: 'edition' is missing.  Attribution is encouraged.")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a VedaGPT corpus JSON file before ingestion."
    )
    parser.add_argument(
        "--corpus",
        required=True,
        type=Path,
        help="Path to the JSON corpus file (list of verse records).",
    )
    parser.add_argument(
        "--allow-demo",
        action="store_true",
        default=False,
        help="Allow DEMO_DATA_NOT_FOR_PRODUCTION records (development only).",
    )
    args = parser.parse_args()

    corpus_path: Path = args.corpus
    if not corpus_path.exists():
        print(f"ERROR: File not found: {corpus_path}", file=sys.stderr)
        return 1

    try:
        with corpus_path.open("r", encoding="utf-8") as f:
            records = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON in '{corpus_path}': {exc}", file=sys.stderr)
        return 1

    if not isinstance(records, list):
        print("ERROR: Corpus file must contain a JSON array of records.", file=sys.stderr)
        return 1

    print(f"\nValidating {len(records)} record(s) from '{corpus_path}' …")
    print(f"Mode: {'DEMO (unverified records allowed)' if args.allow_demo else 'PRODUCTION'}\n")

    errors, warnings = validate_corpus(records, allow_demo=args.allow_demo)

    if warnings:
        print(f"⚠  Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"   {w}")
        print()

    if errors:
        print(f"✗  Errors ({len(errors)}) — corpus FAILED validation:")
        for e in errors:
            print(f"   {e}")
        print()
        return 1

    print(f"✓  Corpus validation PASSED ({len(records)} records, {len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
