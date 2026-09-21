"""
Qdrant ingestion script.

Reads a validated JSON corpus file and upserts records into Qdrant.

Usage:
    # From the backend/ directory:
    python scripts/ingest_qdrant.py --corpus data/bhagavad_gita.sample.json --allow-demo
    python scripts/ingest_qdrant.py --corpus data/bhagavad_gita.real.json

Requirements:
    - Qdrant must be running (docker-compose up -d).
    - .env must be present with correct configuration.
    - Corpus must already pass validate_corpus.py checks.

Exit codes:
    0 — ingestion succeeded
    1 — ingestion failed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from the backend/ directory directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.rag.embeddings import get_embedding_provider
from app.rag.vector_store import VectorStore
from scripts.validate_corpus import PRODUCTION_REJECTED_STATUSES, validate_corpus


def _build_embed_text(record: dict) -> str:
    """Construct the text that will be embedded for a verse record.

    Deterministic and reproducible — same record always produces the same
    embedding input.  Does NOT include licensing notes or credentials.
    """
    parts = [
        f"Scripture: {record.get('scripture', '')}",
        f"Chapter: {record.get('chapter', '')}",
        f"Verse: {record.get('verse', '')}",
        f"Translation: {record.get('translation', '')}",
    ]
    commentary = record.get("commentary", "")
    if commentary:
        parts.append(f"Commentary: {commentary}")
    return "\n".join(parts)


def ingest(corpus_path: Path, allow_demo: bool, batch_size: int = 32) -> int:
    settings = get_settings()

    # ── Load corpus ───────────────────────────────────────────────────────────
    print(f"Loading corpus from '{corpus_path}' …")
    try:
        with corpus_path.open("r", encoding="utf-8") as f:
            records = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR reading corpus: {exc}", file=sys.stderr)
        return 1

    if not isinstance(records, list):
        print("ERROR: Corpus must be a JSON array.", file=sys.stderr)
        return 1

    # ── Validate corpus ───────────────────────────────────────────────────────
    print(f"Validating {len(records)} records …")
    errors, warnings = validate_corpus(records, allow_demo=allow_demo)
    if warnings:
        for w in warnings:
            print(f"  ⚠  {w}")
    if errors:
        for e in errors:
            print(f"  ✗  {e}", file=sys.stderr)
        print("\nIngestion aborted: corpus validation failed.", file=sys.stderr)
        return 1

    # ── Filter production-rejected records ────────────────────────────────────
    if not allow_demo and not settings.allow_unverified_demo_data:
        before = len(records)
        records = [
            r for r in records
            if r.get("copyright_status", "") not in PRODUCTION_REJECTED_STATUSES
        ]
        dropped = before - len(records)
        if dropped:
            print(
                f"  ⚠  Dropped {dropped} record(s) with unverified copyright status "
                "(set ALLOW_UNVERIFIED_DEMO_DATA=true to include demo data)."
            )

    if not records:
        print("No records to ingest after filtering.  Exiting.", file=sys.stderr)
        return 1

    # ── Initialise embedding provider ─────────────────────────────────────────
    print(f"Initialising embedding provider '{settings.embedding_provider}' …")
    try:
        embedder = get_embedding_provider(
            provider=settings.embedding_provider,
            model_name=settings.embedding_model,
            dimension=settings.embedding_dimension,
        )
    except Exception as exc:
        print(f"ERROR initialising embedder: {exc}", file=sys.stderr)
        return 1

    # ── Connect to Qdrant ─────────────────────────────────────────────────────
    print(f"Connecting to Qdrant at '{settings.qdrant_url}' …")
    try:
        store = VectorStore(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            vector_size=settings.embedding_dimension,
            api_key=settings.qdrant_api_key,
        )
        store.ensure_collection()
    except Exception as exc:
        print(f"ERROR connecting to Qdrant: {exc}", file=sys.stderr)
        return 1

    # ── Batch ingestion ───────────────────────────────────────────────────────
    total = len(records)
    ingested = 0
    failed = 0

    for start in range(0, total, batch_size):
        batch = records[start : start + batch_size]
        try:
            texts = [_build_embed_text(r) for r in batch]
            vectors = embedder.embed_texts(texts)
            store.upsert_records(batch, vectors)
            ingested += len(batch)
            print(
                f"  Ingested batch {start // batch_size + 1}: "
                f"{ingested}/{total} records."
            )
        except Exception as exc:
            failed += len(batch)
            print(
                f"  ERROR in batch starting at index {start}: {exc}",
                file=sys.stderr,
            )

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\nIngestion complete: {ingested} succeeded, {failed} failed (total={total}).")
    if failed:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest a validated VedaGPT corpus into Qdrant."
    )
    parser.add_argument(
        "--corpus",
        required=True,
        type=Path,
        help="Path to the validated JSON corpus file.",
    )
    parser.add_argument(
        "--allow-demo",
        action="store_true",
        default=False,
        help="Allow DEMO_DATA_NOT_FOR_PRODUCTION records (development only).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Number of records per embedding batch (default: 32).",
    )
    args = parser.parse_args()
    return ingest(args.corpus, args.allow_demo, args.batch_size)


if __name__ == "__main__":
    sys.exit(main())
