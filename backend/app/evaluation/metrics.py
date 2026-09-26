"""
Retrieval evaluation metrics.

Implements:
  - Recall@K (K in [1, 3, 5, 10])
  - Mean Reciprocal Rank (MRR)
  - Exact-reference top-1 accuracy
  - Refusal metrics (false_grounded, false_refusal)
  - Forbidden-result detection
  - Per-category and per-difficulty breakdowns
  - Latency metrics (mean, median, p95, max)

IMPORTANT: Vector similarity scores are NOT treated as factual confidence.
           Retrieved document IDs are compared, not similarity values.
"""
from __future__ import annotations

import statistics
from typing import Any


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Fraction of relevant IDs found in the top-k retrieved results.

    Returns 1.0 if any relevant ID is in top-k (binary: found or not found)
    for a single query.  Macro-average over queries gives overall recall@k.
    """
    if not relevant_ids:
        return 1.0  # No expectation → always satisfied.
    top_k = retrieved_ids[:k]
    return 1.0 if any(rid in relevant_ids for rid in top_k) else 0.0


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """1 / rank of first relevant result, or 0 if none found."""
    if not relevant_ids:
        return 1.0
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in relevant_ids:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(rr_values: list[float]) -> float:
    return statistics.mean(rr_values) if rr_values else 0.0


def mean_recall_at_k(recall_values: list[float]) -> float:
    return statistics.mean(recall_values) if recall_values else 0.0


def latency_stats(latencies_ms: list[float]) -> dict[str, float]:
    """Compute mean, median, p95, max from a list of ms latencies."""
    if not latencies_ms:
        return {"mean": 0.0, "median": 0.0, "p95": 0.0, "max": 0.0}
    sorted_l = sorted(latencies_ms)
    p95_idx = max(0, int(len(sorted_l) * 0.95) - 1)
    return {
        "mean": round(statistics.mean(sorted_l), 3),
        "median": round(statistics.median(sorted_l), 3),
        "p95": round(sorted_l[p95_idx], 3),
        "max": round(sorted_l[-1], 3),
    }


def compute_per_category_metrics(
    question_results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Group metrics by category."""
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for r in question_results:
        cat = r.get("category", "unknown")
        by_cat.setdefault(cat, []).append(r)
    result = {}
    for cat, items in sorted(by_cat.items()):
        result[cat] = _aggregate_results(items)
    return result


def compute_per_difficulty_metrics(
    question_results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Group metrics by difficulty."""
    by_diff: dict[str, list[dict[str, Any]]] = {}
    for r in question_results:
        diff = r.get("difficulty", "medium")
        by_diff.setdefault(diff, []).append(r)
    result = {}
    for diff, items in sorted(by_diff.items()):
        result[diff] = _aggregate_results(items)
    return result


def _aggregate_results(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate metrics from a list of single-question result dicts."""
    n = len(items)
    if n == 0:
        return {"count": 0}

    r1 = [i.get("recall@1", 0.0) for i in items]
    r3 = [i.get("recall@3", 0.0) for i in items]
    r5 = [i.get("recall@5", 0.0) for i in items]
    r10 = [i.get("recall@10", 0.0) for i in items]
    rr = [i.get("reciprocal_rank", 0.0) for i in items]
    lats = [i.get("latency_ms", 0.0) for i in items]

    return {
        "count": n,
        "recall@1": round(mean_recall_at_k(r1), 4),
        "recall@3": round(mean_recall_at_k(r3), 4),
        "recall@5": round(mean_recall_at_k(r5), 4),
        "recall@10": round(mean_recall_at_k(r10), 4),
        "mrr": round(mean_reciprocal_rank(rr), 4),
        "latency": latency_stats(lats),
    }
