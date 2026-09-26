"""
Corpus normalization script — Phase 2.

Applies deterministic normalization to each record and outputs a new file.

Usage (PowerShell):
    python scripts\normalize_corpus.py --help
    python scripts\normalize_corpus.py `
        --input data\bhagavad_gita.raw.json `
        --output data\bhagavad_gita.normalized.json `
        --report-dir reports

Exit codes:
    0 — success
    1 — failure
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.corpus.loader import load_corpus_file
from app.corpus.normalizer import normalize_record
from app.corpus.errors import CorpusLoadError, NormalizationError


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize a VedaGPT corpus JSON file deterministically. (Phase 2)"
    )
    parser.add_argument("--input", required=True, type=Path,
                        help="Path to the raw JSON corpus file.")
    parser.add_argument("--output", required=True, type=Path,
                        help="Path for the normalized output JSON file.")
    parser.add_argument("--report-dir", type=Path, default=None,
                        help="Directory to write normalization report.")
    args = parser.parse_args()

    try:
        records = load_corpus_file(args.input)
    except CorpusLoadError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Normalizing {len(records)} record(s) from '{args.input}' ...")

    normalized = []
    failed = 0
    for i, rec in enumerate(records):
        try:
            normalized.append(normalize_record(rec))
        except NormalizationError as exc:
            print(f"  ERROR in record[{i}] id={rec.get('id')!r}: {exc}", file=sys.stderr)
            failed += 1

    if failed:
        print(f"  {failed} record(s) failed normalization — output not written.", file=sys.stderr)
        return 1

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=2, ensure_ascii=False)
    except OSError as exc:
        print(f"ERROR writing output: {exc}", file=sys.stderr)
        return 1

    print(f"\u2713  Normalized {len(normalized)} records -> '{args.output}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
