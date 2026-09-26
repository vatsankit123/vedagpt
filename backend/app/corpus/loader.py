"""
Corpus file loader.

Loads, parses, and does basic structural checks on a corpus JSON file.
Full semantic validation is done by validator.py.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.corpus.errors import CorpusLoadError

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


def load_corpus_file(corpus_path: str | Path) -> list[dict[str, Any]]:
    """Load and structurally validate a corpus JSON file.

    Args:
        corpus_path: Path to a UTF-8 JSON file containing a list of records.

    Returns:
        List of record dicts (not yet semantically validated).

    Raises:
        CorpusLoadError: On file-not-found, size-exceeded, JSON error, or wrong type.
    """
    p = Path(corpus_path)
    if not p.exists():
        raise CorpusLoadError(f"Corpus file not found: {corpus_path!r}")
    if p.stat().st_size > MAX_FILE_SIZE_BYTES:
        raise CorpusLoadError(
            f"Corpus file exceeds maximum allowed size "
            f"({MAX_FILE_SIZE_BYTES // (1024*1024)} MB): {corpus_path!r}"
        )

    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise CorpusLoadError(f"Invalid JSON in corpus file {corpus_path!r}: {exc}") from exc
    except OSError as exc:
        raise CorpusLoadError(f"Failed to read corpus file {corpus_path!r}: {exc}") from exc

    if not isinstance(data, list):
        raise CorpusLoadError(
            f"Corpus file must contain a JSON array of records, "
            f"got {type(data).__name__!r}."
        )

    return data
