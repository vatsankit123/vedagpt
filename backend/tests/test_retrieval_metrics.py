"""Tests for retrieval evaluation metrics."""
from __future__ import annotations

from app.evaluation.metrics import (
    recall_at_k,
    reciprocal_rank,
    mean_reciprocal_rank,
    mean_recall_at_k,
    latency_stats,
    compute_per_category_metrics,
)


def test_recall_at_1_found():
    assert recall_at_k(["gita-2-47", "gita-3-1"], {"gita-2-47"}, 1) == 1.0


def test_recall_at_1_not_found():
    assert recall_at_k(["gita-3-1", "gita-4-2"], {"gita-2-47"}, 1) == 0.0


def test_recall_at_3_found_in_position_3():
    assert recall_at_k(["a", "b", "gita-2-47"], {"gita-2-47"}, 3) == 1.0


def test_recall_at_3_not_found():
    assert recall_at_k(["a", "b", "c"], {"gita-2-47"}, 3) == 0.0


def test_recall_at_5_partial_match():
    retrieved = ["a", "b", "c", "d", "gita-2-47"]
    assert recall_at_k(retrieved, {"gita-2-47"}, 5) == 1.0


def test_recall_at_10_not_found():
    assert recall_at_k(["a"] * 10, {"gita-2-47"}, 10) == 0.0


def test_recall_no_expected_is_full():
    assert recall_at_k(["anything"], set(), 1) == 1.0


def test_mrr_first_position():
    assert reciprocal_rank(["gita-2-47"], {"gita-2-47"}) == 1.0


def test_mrr_second_position():
    assert reciprocal_rank(["other", "gita-2-47"], {"gita-2-47"}) == pytest.approx(0.5)


def test_mrr_not_found():
    assert reciprocal_rank(["a", "b", "c"], {"gita-2-47"}) == 0.0


def test_mrr_empty_expected():
    assert reciprocal_rank(["a", "b"], set()) == 1.0


def test_mean_mrr():
    rr_vals = [1.0, 0.5, 0.0]
    assert mean_reciprocal_rank(rr_vals) == pytest.approx(0.5)


def test_mean_recall():
    assert mean_recall_at_k([1.0, 0.0, 1.0]) == pytest.approx(2/3)


def test_latency_stats_correct():
    stats = latency_stats([10.0, 20.0, 30.0, 40.0, 100.0])
    assert stats["mean"] == pytest.approx(40.0)
    assert stats["max"] == 100.0
    assert stats["p95"] >= 40.0


def test_latency_stats_empty():
    s = latency_stats([])
    assert s["mean"] == 0.0


def test_per_category_metrics_grouping():
    results = [
        {"category": "concept_retrieval", "recall@1": 1.0, "recall@3": 1.0,
         "recall@5": 1.0, "recall@10": 1.0, "reciprocal_rank": 1.0, "latency_ms": 10.0},
        {"category": "concept_retrieval", "recall@1": 0.0, "recall@3": 1.0,
         "recall@5": 1.0, "recall@10": 1.0, "reciprocal_rank": 0.5, "latency_ms": 20.0},
        {"category": "direct_verse_reference", "recall@1": 1.0, "recall@3": 1.0,
         "recall@5": 1.0, "recall@10": 1.0, "reciprocal_rank": 1.0, "latency_ms": 5.0},
    ]
    by_cat = compute_per_category_metrics(results)
    assert "concept_retrieval" in by_cat
    assert "direct_verse_reference" in by_cat
    assert by_cat["concept_retrieval"]["count"] == 2
    assert by_cat["concept_retrieval"]["recall@1"] == pytest.approx(0.5)


import pytest
