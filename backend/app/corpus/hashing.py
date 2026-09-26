"""
Deterministic content hashing for corpus records.

Rules:
  - Uses SHA-256.
  - Only includes content-bearing fields (not volatile metadata).
  - Field order is fixed alphabetically to ensure stability across Python versions.
  - Empty optional fields are included as empty strings (not omitted) so the
    hash captures the absence of content explicitly.
  - Volatile fields excluded: ingestion timestamps, run IDs, Qdrant scores,
    processing time, normalization version, pipeline version.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


# Fixed ordered list of fields that contribute to the content hash.
_HASH_FIELDS = (
    "chapter",
    "commentary",
    "commentator",
    "edition",
    "sanskrit",
    "scripture",
    "source_id",
    "translation",
    "transliteration",
    "translator",
    "verse",
    "verse_end",
)


def compute_content_hash(record: dict[str, Any]) -> str:
    """Return a stable SHA-256 hex digest for a corpus record.

    The hash covers only content-bearing fields.  Volatile metadata
    (timestamps, run IDs, scores) is excluded to ensure stability.

    Args:
        record: A dict representation of a CorpusRecord (or raw dict).

    Returns:
        64-character lowercase hex string.
    """
    # Build a canonical dict with a fixed set of keys, converting None to "".
    canonical: dict[str, Any] = {}
    for field in _HASH_FIELDS:
        val = record.get(field)
        if val is None:
            canonical[field] = ""
        elif isinstance(val, int):
            canonical[field] = val  # Keep integers as integers.
        else:
            canonical[field] = str(val)

    # Use compact, sorted JSON for stability.
    serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def verify_content_hash(record: dict[str, Any], stored_hash: str) -> bool:
    """Return True if the stored hash matches the computed hash."""
    return compute_content_hash(record) == stored_hash
