"""
Deterministic corpus normalization.

Allowed operations:
  - Unicode NFC normalization of text fields.
  - Consistent line endings (CRLF → LF).
  - Strip accidental leading/trailing whitespace.
  - Collapse clearly accidental repeated internal whitespace (only in
    metadata identifier fields, NOT in translations or commentaries).
  - Standardize None → "" for optional string fields.
  - Parse integer fields safely.
  - Compute stable content hashes.

NOT allowed:
  - Rewriting translations.
  - Correcting Sanskrit automatically.
  - Paraphrasing commentary.
  - Translating content automatically.
  - Removing meaningful punctuation.
  - Merging or splitting verses.
  - Modifying scripture wording silently.
"""
from __future__ import annotations

import unicodedata
from typing import Any

from app.corpus.hashing import compute_content_hash
from app.corpus.errors import NormalizationError

NORMALIZATION_VERSION = 1

# Text content fields: normalize Unicode + line endings + trim ONLY.
_TEXT_FIELDS = {"translation", "commentary", "sanskrit", "transliteration", "notes"}

# Identifier / short metadata fields: additionally collapse internal whitespace.
_META_FIELDS = {
    "id", "source_id", "scripture", "translator", "commentator",
    "edition", "language", "source_reference", "copyright_status",
    "license_name", "license_reference", "review_status",
    "reviewed_by", "reviewed_date",
}


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _normalize_text_field(value: Any) -> str:
    """Normalize a long text field: Unicode NFC + CRLF→LF + strip."""
    if value is None:
        return ""
    s = str(value)
    s = _nfc(s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.strip()
    return s


def _normalize_meta_field(value: Any) -> str:
    """Normalize a short metadata field: text normalization + collapse spaces."""
    s = _normalize_text_field(value)
    # Collapse runs of whitespace to a single space (for identifiers only).
    import re
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def _safe_int(value: Any, field_name: str) -> int:
    """Parse an integer field safely."""
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise NormalizationError(
            f"Cannot parse integer from field {field_name!r}: {value!r}"
        ) from exc


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Apply deterministic normalization to a single record dict.

    Returns a new dict — the original is not mutated.

    Every normalized record preserves:
      - Original record ID
      - Source ID
      - Record version
      - Normalization version (added)
      - Content hash (recomputed after normalization)
    """
    out: dict[str, Any] = {}

    # Text fields.
    for field in _TEXT_FIELDS:
        out[field] = _normalize_text_field(record.get(field))

    # Metadata fields.
    for field in _META_FIELDS:
        out[field] = _normalize_meta_field(record.get(field))

    # Integer fields.
    for int_field in ("chapter", "verse", "record_version"):
        out[int_field] = _safe_int(record[int_field], int_field)

    # Optional integer.
    ve = record.get("verse_end")
    out["verse_end"] = _safe_int(ve, "verse_end") if ve is not None else None

    # Provenance / version tracking.
    out["record_version"] = out.get("record_version") or 1
    out["normalization_version"] = NORMALIZATION_VERSION

    # Recompute content hash on the normalized record.
    out["content_hash"] = compute_content_hash(out)

    return out
