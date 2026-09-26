"""
Offline retrieval evaluation runner.

Does NOT call Gemini.  Evaluates retrieval quality only.

Flow:
  Load dataset -> validate -> embed query -> query Qdrant ->
  compare retrieved IDs with expected -> compute metrics -> report.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.evaluation.metrics import (
    recall_at_k,
    reciprocal_rank,
    mean_recall_at_k,
    mean_reciprocal_rank,
    latency_stats,
    compute_per_category_metrics,
    compute_per_difficulty_metrics,
)
from app.evaluation.models import EvaluationDataset, EvaluationQuestion
from app.corpus.errors import EvaluationDatasetError, EvaluationRunError

logger = logging.getLogger(__name__)

TOP_K_VALUES = [1, 3, 5, 10]


def load_evaluation_dataset(dataset_path: str) -> EvaluationDataset:
    """Load and validate an evaluation dataset JSON file."""
    p = Path(dataset_path)
    if not p.exists():
        raise EvaluationDatasetError(f"Dataset file not found: {dataset_path!r}")
    try:
        with p.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise EvaluationDatasetError(f"Failed to load dataset: {exc}") from exc

    if isinstance(raw, list):
        raw = {"questions": raw}

    try:
        ds = EvaluationDataset.model_validate(raw)
    except Exception as exc:
        raise EvaluationDatasetError(f"Dataset schema error: {exc}") from exc

    if not ds.questions:
        raise EvaluationDatasetError("Evaluation dataset contains no questions.")

    return ds


def run_evaluation(
    dataset: EvaluationDataset,
    embedder: Any,
    vector_store: Any,
    score_threshold: float = 0.0,
    candidate_k: int = 20,
    collection_name: str = "",
    embedding_model: str = "",
    embedding_provider: str = "",
    document_strategy: str = "",
    source_id: str = "",
    corpus_profile_id: str = "",
    environment: str = "development",
    using_mocks: bool = False,
    using_fixtures: bool = False,
) -> dict[str, Any]:
    """Run the offline retrieval evaluation.

    Returns a result dict suitable for JSON/Markdown report generation.
    Does NOT call Gemini.
    """
    run_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    question_results: list[dict[str, Any]] = []
    failed_cases: list[dict[str, Any]] = []
    forbidden_cases: list[dict[str, Any]] = []

    for q in dataset.questions:
        result = _evaluate_question(
            q=q,
            embedder=embedder,
            vector_store=vector_store,
            score_threshold=score_threshold,
            candidate_k=candidate_k,
        )
        question_results.append(result)

        if result.get("error"):
            failed_cases.append({"id": q.id, "error": result["error"]})

        if result.get("forbidden_retrieved"):
            forbidden_cases.append({
                "id": q.id,
                "forbidden_found": result["forbidden_retrieved"],
            })

    # ── Aggregate metrics ──────────────────────────────────────────────────────
    r1_vals = [r.get("recall@1", 0.0) for r in question_results]
    r3_vals = [r.get("recall@3", 0.0) for r in question_results]
    r5_vals = [r.get("recall@5", 0.0) for r in question_results]
    r10_vals = [r.get("recall@10", 0.0) for r in question_results]
    rr_vals = [r.get("reciprocal_rank", 0.0) for r in question_results]
    lat_vals = [r.get("latency_ms", 0.0) for r in question_results]

    # Refusal metrics.
    refusal_results = [r for r in question_results if r.get("must_refuse")]
    grounded_results = [r for r in question_results if not r.get("must_refuse")]

    n = len(question_results)
    false_grounded = sum(
        1 for r in refusal_results if not r.get("correctly_refused", False)
    )
    false_refusal = sum(
        1 for r in grounded_results
        if r.get("retrieval_count", 0) == 0 and r.get("expected_count", 0) > 0
    )

    overall = {
        "count": n,
        "recall@1": round(mean_recall_at_k(r1_vals), 4),
        "recall@3": round(mean_recall_at_k(r3_vals), 4),
        "recall@5": round(mean_recall_at_k(r5_vals), 4),
        "recall@10": round(mean_recall_at_k(r10_vals), 4),
        "mrr": round(mean_reciprocal_rank(rr_vals), 4),
        "false_grounded_count": false_grounded,
        "false_refusal_count": false_refusal,
        "failed_cases": len(failed_cases),
        "forbidden_cases": len(forbidden_cases),
    }

    label = "NON_PRODUCTION_FIXTURE_REPORT" if (using_mocks or using_fixtures) else "EVALUATION_REPORT"

    return {
        "fixture_label": label,
        "run_id": run_id,
        "timestamp": ts,
        "environment": environment,
        "collection_name": collection_name,
        "embedding_model": embedding_model,
        "embedding_provider": embedding_provider,
        "document_strategy": document_strategy,
        "source_id": source_id,
        "corpus_profile_id": corpus_profile_id,
        "score_threshold": score_threshold,
        "candidate_k": candidate_k,
        "top_k_values": TOP_K_VALUES,
        "using_mocks": using_mocks,
        "using_fixtures": using_fixtures,
        "overall": overall,
        "by_category": compute_per_category_metrics(question_results),
        "by_difficulty": compute_per_difficulty_metrics(question_results),
        "latency": latency_stats(lat_vals),
        "failed_cases": failed_cases,
        "forbidden_cases": forbidden_cases,
    }


def _evaluate_question(
    q: EvaluationQuestion,
    embedder: Any,
    vector_store: Any,
    score_threshold: float,
    candidate_k: int,
) -> dict[str, Any]:
    """Evaluate a single question. Returns a result dict."""
    t0 = time.perf_counter()

    expected = set(q.expected_document_ids or [])
    acceptable = set(q.acceptable_document_ids or [])
    all_relevant = expected | acceptable
    forbidden = set(q.forbidden_document_ids or [])

    retrieved_ids: list[str] = []
    error: str | None = None
    retrieval_count = 0

    try:
        if q.question.strip():
            vec = embedder.embed_query(q.question)
            hits = vector_store.search(
                query_vector=vec,
                top_k=candidate_k,
                score_threshold=score_threshold,
            )
            retrieved_ids = [h.get("document_id", "") for h in hits if h.get("document_id")]
            retrieval_count = len(retrieved_ids)
    except Exception as exc:
        error = str(exc)

    lat_ms = (time.perf_counter() - t0) * 1000.0

    # Correctly refused = must_refuse and retrieval returned nothing above threshold.
    correctly_refused = q.must_refuse and retrieval_count == 0

    forbidden_retrieved = [fid for fid in forbidden if fid in retrieved_ids]

    result = {
        "id": q.id,
        "category": q.category,
        "difficulty": q.difficulty,
        "must_refuse": q.must_refuse,
        "expected_count": len(expected),
        "retrieval_count": retrieval_count,
        "retrieved_ids": retrieved_ids[:10],  # truncate for reports.
        "correctly_refused": correctly_refused,
        "forbidden_retrieved": forbidden_retrieved,
        "latency_ms": round(lat_ms, 3),
        "error": error,
    }

    # Recall and MRR are computed only for grounded questions with expected IDs.
    if not q.must_refuse and all_relevant:
        for k in TOP_K_VALUES:
            result[f"recall@{k}"] = recall_at_k(retrieved_ids, all_relevant, k)
        result["reciprocal_rank"] = reciprocal_rank(retrieved_ids, all_relevant)
    else:
        for k in TOP_K_VALUES:
            result[f"recall@{k}"] = 1.0 if correctly_refused or not all_relevant else 0.0
        result["reciprocal_rank"] = 1.0 if correctly_refused or not all_relevant else 0.0

    return result
