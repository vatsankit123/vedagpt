"""
Collection inspection script — Phase 2.

Displays safe metadata for a Qdrant document by ID.
Does NOT expose API keys, credentials, or sensitive paths.

Usage (PowerShell):
    python scripts\inspect_collection.py --document-id gita-2-47
    python scripts\inspect_collection.py --help
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.rag.vector_store import VectorStore

SAFE_FIELDS = (
    "document_id", "source_id", "scripture", "chapter", "verse",
    "translator", "edition", "source_reference", "copyright_status",
    "license_name", "review_status", "content_hash",
    "pipeline_version", "embedding_model", "document_strategy",
    "language", "record_version", "normalization_version",
    "schema_version", "is_demo",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a Qdrant document by ID. (Phase 2)"
    )
    parser.add_argument("--document-id", required=True,
                        help="Document ID, e.g. gita-2-47.")
    parser.add_argument("--show-translation", action="store_true", default=False,
                        help="Also display the stored translation text.")
    args = parser.parse_args()

    doc_id = args.document_id.strip()
    if not doc_id or len(doc_id) > 256:
        print("ERROR: Invalid document ID.", file=sys.stderr)
        return 1

    settings = get_settings()
    try:
        store = VectorStore(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            vector_size=settings.embedding_dimension,
            api_key=settings.qdrant_api_key,
        )
    except Exception as exc:
        print(f"ERROR connecting to Qdrant: {exc}", file=sys.stderr)
        return 1

    try:
        hits = store.search(
            query_vector=[0.0] * settings.embedding_dimension,
            top_k=1,
            score_threshold=0.0,
        )
        # The zero-vector search is a fallback; use filter instead if available.
        # Try scroll with filter by document_id.
        client = store._client
        results, _ = client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter={
                "must": [{"key": "document_id", "match": {"value": doc_id}}]
            },
            limit=1,
            with_payload=True,
            with_vectors=False,
        )
    except Exception as exc:
        print(f"ERROR querying Qdrant: {exc}", file=sys.stderr)
        return 1

    if not results:
        print(f"Document '{doc_id}' not found in collection '{settings.qdrant_collection}'.")
        return 1

    payload = results[0].payload or {}
    print(f"\nDocument: {doc_id}")
    print(f"Collection: {settings.qdrant_collection}")
    print("-" * 50)
    for field in SAFE_FIELDS:
        val = payload.get(field, "")
        if val not in (None, "", False):
            print(f"  {field}: {val}")

    if args.show_translation:
        trans = payload.get("translation", "")
        if trans:
            print(f"\n  translation: {trans[:500]}{'...' if len(trans) > 500 else ''}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
