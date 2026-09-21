"""
Qdrant vector store management.

Handles collection creation, idempotent upsert, and search.
All Qdrant interaction is isolated to this module so it can be mocked in tests.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

logger = logging.getLogger(__name__)

# ── Payload field names (kept as constants to avoid magic strings) ─────────────
FIELD_DOCUMENT_ID = "document_id"
FIELD_SCRIPTURE = "scripture"
FIELD_CHAPTER = "chapter"
FIELD_VERSE = "verse"
FIELD_SANSKRIT = "sanskrit"
FIELD_TRANSLITERATION = "transliteration"
FIELD_TRANSLATION = "translation"
FIELD_COMMENTARY = "commentary"
FIELD_TRANSLATOR = "translator"
FIELD_EDITION = "edition"
FIELD_LANGUAGE = "language"
FIELD_SOURCE_REFERENCE = "source_reference"
FIELD_COPYRIGHT_STATUS = "copyright_status"


class VectorStore:
    """Thin wrapper around Qdrant for VedaGPT's scripture collection."""

    def __init__(
        self,
        url: str,
        collection_name: str,
        vector_size: int,
        api_key: str = "",
    ) -> None:
        self._collection = collection_name
        self._vector_size = vector_size

        connect_kwargs: dict[str, Any] = {"url": url}
        if api_key:
            connect_kwargs["api_key"] = api_key

        self._client = QdrantClient(**connect_kwargs)
        logger.info(
            "VectorStore connected to Qdrant at '%s', collection='%s'.",
            url,
            collection_name,
        )

    # ── Collection management ─────────────────────────────────────────────────

    def ensure_collection(self) -> None:
        """Create the collection if it does not exist (idempotent)."""
        existing = [c.name for c in self._client.get_collections().collections]
        if self._collection in existing:
            logger.info("Collection '%s' already exists; skipping creation.", self._collection)
            return

        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=qmodels.VectorParams(
                size=self._vector_size,
                distance=qmodels.Distance.COSINE,
            ),
        )
        logger.info(
            "Created Qdrant collection '%s' (dim=%d, distance=COSINE).",
            self._collection,
            self._vector_size,
        )

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def upsert_records(
        self,
        records: list[dict[str, Any]],
        vectors: list[list[float]],
    ) -> None:
        """Upsert scripture records into Qdrant.

        Ingestion is idempotent: each record's document_id is deterministically
        converted to a UUID-5 so re-running ingestion overwrites rather than
        duplicates.

        Args:
            records: List of payload dicts (one per verse).
            vectors: Corresponding embedding vectors.
        """
        if len(records) != len(vectors):
            raise ValueError(
                f"Records and vectors must have the same length "
                f"({len(records)} != {len(vectors)})."
            )

        points = []
        for record, vector in zip(records, vectors):
            doc_id = record[FIELD_DOCUMENT_ID]
            # Deterministic UUID from document_id prevents duplicate insertion.
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        FIELD_DOCUMENT_ID: doc_id,
                        FIELD_SCRIPTURE: record.get(FIELD_SCRIPTURE, ""),
                        FIELD_CHAPTER: record.get(FIELD_CHAPTER, 0),
                        FIELD_VERSE: record.get(FIELD_VERSE, 0),
                        FIELD_SANSKRIT: record.get(FIELD_SANSKRIT, ""),
                        FIELD_TRANSLITERATION: record.get(FIELD_TRANSLITERATION, ""),
                        FIELD_TRANSLATION: record.get(FIELD_TRANSLATION, ""),
                        FIELD_COMMENTARY: record.get(FIELD_COMMENTARY, ""),
                        FIELD_TRANSLATOR: record.get(FIELD_TRANSLATOR, ""),
                        FIELD_EDITION: record.get(FIELD_EDITION, ""),
                        FIELD_LANGUAGE: record.get(FIELD_LANGUAGE, "English"),
                        FIELD_SOURCE_REFERENCE: record.get(FIELD_SOURCE_REFERENCE, ""),
                        FIELD_COPYRIGHT_STATUS: record.get(FIELD_COPYRIGHT_STATUS, "UNVERIFIED"),
                    },
                )
            )

        self._client.upsert(collection_name=self._collection, points=points)
        logger.info("Upserted %d records into collection '%s'.", len(points), self._collection)

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        score_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Return the top-k most similar passages above the score threshold.

        Returns a list of dicts with keys: payload + retrieval_score.
        """
        results = self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True,
        )

        hits = []
        for r in results:
            payload = dict(r.payload or {})
            payload["retrieval_score"] = r.score
            hits.append(payload)

        logger.debug("Search returned %d hits (threshold=%.3f).", len(hits), score_threshold)
        return hits

    # ── Health / info ─────────────────────────────────────────────────────────

    def collection_info(self) -> dict[str, Any]:
        """Return basic collection information for health checks."""
        try:
            info = self._client.get_collection(self._collection)
            return {
                "collection": self._collection,
                "vectors_count": info.vectors_count,
                "status": str(info.status),
            }
        except Exception as exc:
            logger.warning("Could not fetch collection info: %s", exc)
            return {"collection": self._collection, "error": str(exc)}
