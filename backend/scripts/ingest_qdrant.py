"""
Qdrant ingestion script -- Phase 2.

Improvements over Phase 1:
  - Stable point ID generation (deterministic UUID from record ID).
  - Idempotent: new records added, changed records updated, unchanged skipped.
  - Dry-run mode: validates and plans without writing anything or loading models.
  - Source manifest and corpus profile validation.
  - JSON + Markdown ingestion report.
  - Configurable document construction strategy.

Usage::

    # Dry run (no model download needed):
    python scripts/ingest_qdrant.py --corpus data/bhagavad_gita.verified.json --dry-run

    # Actual ingestion:
    python scripts/ingest_qdrant.py --corpus data/bhagavad_gita.verified.json
        --manifest data/source_manifest.verified.json

Exit codes:
    0 -- success (or dry-run completed)
    1 -- failure
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid as _uuid
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.corpus.loader import load_corpus_file
from app.corpus.validator import validate_corpus_records, PRODUCTION_REJECTED_STATUSES
from app.corpus.document_builder import build_document, VALID_STRATEGIES
from app.corpus.hashing import compute_content_hash
from app.corpus.normalizer import normalize_record
from app.corpus.reports import generate_ingestion_reports
from app.corpus.errors import (
    CorpusLoadError,
    SourceManifestError,
    LicenseValidationError,
    ProvenanceValidationError,
    DocumentBuildError,
)


def _stable_point_id(record_id: str) -> str:
    """Generate a deterministic UUID from a record ID string."""
    return str(_uuid.uuid5(_uuid.NAMESPACE_DNS, f"vedagpt.{record_id}"))


def _fetch_existing_hashes(store, collection: str) -> dict[str, str]:
    """Fetch document_id -> content_hash from Qdrant for idempotency check."""
    try:
        client = store._client
        offset = None
        existing: dict[str, str] = {}
        while True:
            result, offset = client.scroll(
                collection_name=collection,
                limit=256,
                offset=offset,
                with_payload=["document_id", "content_hash"],
                with_vectors=False,
            )
            for point in result:
                if point.payload:
                    did = point.payload.get("document_id", "")
                    ch = point.payload.get("content_hash", "")
                    if did:
                        existing[did] = ch
            if offset is None:
                break
        return existing
    except Exception:
        return {}


def ingest(
    corpus_path: Path,
    manifest_path: Path | None,
    profile_path: Path | None,
    allow_demo: bool,
    dry_run: bool,
    batch_size: int,
    document_strategy: str,
    report_dir: Path | None,
    recreate: bool,
) -> int:
    settings = get_settings()
    run_id = str(_uuid.uuid4())
    t_start = time.time()
    timestamp = datetime.now(timezone.utc).isoformat()
    collection = settings.qdrant_collection

    print(f"[{run_id[:8]}] Ingestion run  dry_run={dry_run}  strategy={document_strategy}")

    # -- Load corpus -------------------------------------------------------
    try:
        records = load_corpus_file(corpus_path)
    except CorpusLoadError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"  Loaded {len(records)} records from '{corpus_path}'")

    # -- Load manifest (optional) -----------------------------------------
    manifest = None
    if manifest_path:
        try:
            from app.corpus.provenance import load_and_validate_manifest
            manifest = load_and_validate_manifest(
                str(manifest_path),
                production=not allow_demo,
            )
            print(f"  Manifest: source_id={manifest.source_id!r}  "
                  f"status={manifest.verification_status}")
        except (SourceManifestError, LicenseValidationError, ProvenanceValidationError) as exc:
            print(f"ERROR in manifest: {exc}", file=sys.stderr)
            if not allow_demo:
                return 1

    # -- Load profile (optional) ------------------------------------------
    profile = None
    if profile_path:
        try:
            from app.corpus.provenance import load_corpus_profile
            profile = load_corpus_profile(str(profile_path))
            print(f"  Profile: {profile.profile_id!r}")
        except Exception as exc:
            print(f"  WARNING: Could not load profile: {exc}")

    # -- Validate ---------------------------------------------------------
    print("  Validating records ...")
    result = validate_corpus_records(
        records=records,
        manifest=manifest,
        profile=profile,
        allow_demo=allow_demo,
        production=not allow_demo,
    )
    for w in result["warnings"]:
        print(f"  WARN: {w}")
    if result["errors"]:
        for e in result["errors"]:
            print(f"  ERR: {e}", file=sys.stderr)
        print("Ingestion aborted: corpus validation failed.", file=sys.stderr)
        return 1

    # -- Normalize --------------------------------------------------------
    normalized: list[dict] = []
    for rec in records:
        try:
            normalized.append(normalize_record(rec))
        except Exception as exc:
            print(f"  ERR: Normalization failed for {rec.get('id')!r}: {exc}",
                  file=sys.stderr)

    # -- Filter demo/unverified records -----------------------------------
    if not allow_demo:
        before = len(normalized)
        normalized = [r for r in normalized
                      if r.get("copyright_status", "") not in PRODUCTION_REJECTED_STATUSES]
        dropped = before - len(normalized)
        if dropped:
            print(f"  WARN: Dropped {dropped} demo/unverified records.")

    if not normalized:
        print("No valid records to ingest after filtering.", file=sys.stderr)
        return 1

    # -- DRY-RUN early exit (no model download, no Qdrant connection) ------
    if dry_run:
        total = len(records)
        plan_count = len(normalized)
        duration = round(time.time() - t_start, 2)
        print(f"  DRY-RUN: {plan_count} records would be ingested "
              f"({total - plan_count} filtered).")
        summary = {
            "run_id": run_id,
            "timestamp": timestamp,
            "collection": collection,
            "dry_run": True,
            "allow_demo": allow_demo,
            "document_strategy": document_strategy,
            "embedding_model": settings.embedding_model,
            "source_id": manifest.source_id if manifest else "",
            "added": plan_count,
            "updated": 0,
            "unchanged": 0,
            "rejected": total - plan_count,
            "failed": 0,
            "total": total,
            "duration_seconds": duration,
            "note": "DRY-RUN: no data was written, no model was loaded.",
        }
        if report_dir:
            try:
                j, m = generate_ingestion_reports(summary, str(report_dir))
                print(f"  Report: {j}")
            except Exception as exc:
                print(f"  WARNING: Could not write report: {exc}")
        print(f"DRY-RUN complete ({duration}s). No data written.")
        return 0

    # -- Initialise embedding provider (live run only) --------------------
    print(f"  Initialising embedding provider '{settings.embedding_provider}' ...")
    try:
        from app.rag.embeddings import get_embedding_provider
        embedder = get_embedding_provider(
            provider=settings.embedding_provider,
            model_name=settings.embedding_model,
            dimension=settings.embedding_dimension,
        )
    except Exception as exc:
        print(f"ERROR initialising embedder: {exc}", file=sys.stderr)
        return 1

    # -- Connect to Qdrant ------------------------------------------------
    print(f"  Connecting to Qdrant: collection='{collection}' ...")
    try:
        from app.rag.vector_store import VectorStore
        store = VectorStore(
            url=settings.qdrant_url,
            collection_name=collection,
            vector_size=settings.embedding_dimension,
            api_key=settings.qdrant_api_key,
        )
        if recreate:
            print("  WARNING: --recreate flag set. Deleting existing collection ...")
            try:
                store._client.delete_collection(collection)
            except Exception:
                pass
        store.ensure_collection()
    except Exception as exc:
        print(f"ERROR connecting to Qdrant: {exc}", file=sys.stderr)
        return 1

    # -- Fetch existing hashes for idempotency ----------------------------
    existing_hashes = _fetch_existing_hashes(store, collection)
    print(f"  Found {len(existing_hashes)} existing records in collection.")

    # -- Batch ingestion --------------------------------------------------
    total = len(records)
    added = updated = unchanged = failed = rejected = 0
    pipeline_version = "phase2-v1"

    for start in range(0, len(normalized), batch_size):
        batch = normalized[start:start + batch_size]
        to_upsert_records = []
        to_upsert_texts = []

        for rec in batch:
            rec_id = str(rec.get("id", ""))
            new_hash = compute_content_hash(rec)
            rec["content_hash"] = new_hash

            if rec_id in existing_hashes:
                if existing_hashes[rec_id] == new_hash:
                    unchanged += 1
                    continue
                else:
                    updated += 1
            else:
                added += 1

            try:
                doc_text = build_document(
                    record=rec,
                    strategy=document_strategy,
                    all_records=normalized,
                )
            except DocumentBuildError as exc:
                print(f"  ERR: Document build failed for {rec_id!r}: {exc}",
                      file=sys.stderr)
                failed += 1
                continue

            rec["schema_version"] = 2
            rec["pipeline_version"] = pipeline_version
            rec["embedding_model"] = settings.embedding_model
            rec["embedding_provider"] = settings.embedding_provider
            rec["embedding_dimension"] = settings.embedding_dimension
            rec["document_strategy"] = document_strategy
            rec["is_demo"] = (
                rec.get("copyright_status") == "DEMO_DATA_NOT_FOR_PRODUCTION"
            )
            to_upsert_records.append(rec)
            to_upsert_texts.append(doc_text)

        if not to_upsert_records:
            continue

        try:
            vectors = embedder.embed_texts(to_upsert_texts)
            store.upsert_records(to_upsert_records, vectors)
            b_num = start // batch_size + 1
            print(f"  Batch {b_num}: +{added} added, ~{updated} updated, "
                  f"={unchanged} unchanged so far.")
        except Exception as exc:
            print(f"  ERR: Batch starting {start} failed: {exc}", file=sys.stderr)
            failed += len(to_upsert_records)
            added -= len(to_upsert_records)

    duration = round(time.time() - t_start, 2)
    print(
        f"\nIngestion complete in {duration}s: "
        f"added={added}, updated={updated}, unchanged={unchanged}, "
        f"rejected={rejected}, failed={failed}, total={total}"
    )

    summary = {
        "run_id": run_id,
        "timestamp": timestamp,
        "collection": collection,
        "dry_run": False,
        "allow_demo": allow_demo,
        "document_strategy": document_strategy,
        "embedding_model": settings.embedding_model,
        "source_id": manifest.source_id if manifest else "",
        "added": added,
        "updated": updated,
        "unchanged": unchanged,
        "rejected": rejected,
        "failed": failed,
        "total": total,
        "duration_seconds": duration,
    }

    if report_dir:
        try:
            j, m = generate_ingestion_reports(summary, str(report_dir))
            print(f"  Report: {j}")
        except Exception as exc:
            print(f"  WARNING: Could not write report: {exc}")

    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest a verified VedaGPT corpus into Qdrant. (Phase 2)"
    )
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--profile", type=Path, default=None)
    parser.add_argument("--allow-demo", action="store_true", default=False)
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Validate and plan without writing or loading models.")
    parser.add_argument("--recreate", action="store_true", default=False,
                        help="Delete and recreate collection. DESTRUCTIVE.")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--strategy", default="translation",
                        choices=sorted(VALID_STRATEGIES),
                        help="Document construction strategy.")
    parser.add_argument("--report-dir", type=Path, default=None)
    args = parser.parse_args()

    return ingest(
        corpus_path=args.corpus,
        manifest_path=args.manifest,
        profile_path=args.profile,
        allow_demo=args.allow_demo,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        document_strategy=args.strategy,
        report_dir=args.report_dir,
        recreate=args.recreate,
    )


if __name__ == "__main__":
    sys.exit(main())
