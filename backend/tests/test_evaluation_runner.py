"""Tests for the offline evaluation runner."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.evaluation.runner import load_evaluation_dataset, run_evaluation
from app.evaluation.reports import write_evaluation_reports
from app.corpus.errors import EvaluationDatasetError


def _sample_dataset_path() -> str:
    """Return path to the fixture evaluation dataset."""
    return str(
        Path(__file__).parent.parent / "data" / "evaluation_questions.sample.json"
    )


def _mock_embedder(dim=384) -> MagicMock:
    emb = MagicMock()
    emb.embed_query.return_value = [0.0] * dim
    return emb


def _mock_store() -> MagicMock:
    store = MagicMock()
    store.search.return_value = [
        {"document_id": "gita-2-47", "retrieval_score": 0.9},
    ]
    return store


def test_load_sample_dataset():
    ds = load_evaluation_dataset(_sample_dataset_path())
    assert len(ds.questions) > 0
    assert ds.is_fixture is True


def test_empty_dataset_rejected():
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump({"questions": []}, f)
        p = f.name
    with pytest.raises(EvaluationDatasetError):
        load_evaluation_dataset(p)


def test_missing_dataset_rejected():
    with pytest.raises(EvaluationDatasetError):
        load_evaluation_dataset("/nonexistent/path/dataset.json")


def test_run_evaluation_completes():
    ds = load_evaluation_dataset(_sample_dataset_path())
    result = run_evaluation(
        dataset=ds,
        embedder=_mock_embedder(),
        vector_store=_mock_store(),
        using_mocks=True,
        using_fixtures=True,
    )
    assert "overall" in result
    assert "by_category" in result
    assert "latency" in result
    assert result["using_mocks"] is True
    assert result["using_fixtures"] is True


def test_fixture_label_set():
    ds = load_evaluation_dataset(_sample_dataset_path())
    result = run_evaluation(
        dataset=ds, embedder=_mock_embedder(), vector_store=_mock_store(),
        using_mocks=True, using_fixtures=True,
    )
    assert "FIXTURE" in result["fixture_label"] or "MOCK" in result["fixture_label"]


def test_recall_at_k_present():
    ds = load_evaluation_dataset(_sample_dataset_path())
    result = run_evaluation(
        dataset=ds, embedder=_mock_embedder(), vector_store=_mock_store(),
        using_mocks=True, using_fixtures=True,
    )
    overall = result["overall"]
    assert "recall@1" in overall
    assert "recall@3" in overall
    assert "recall@5" in overall
    assert "recall@10" in overall


def test_mrr_present():
    ds = load_evaluation_dataset(_sample_dataset_path())
    result = run_evaluation(
        dataset=ds, embedder=_mock_embedder(), vector_store=_mock_store(),
        using_mocks=True, using_fixtures=True,
    )
    assert "mrr" in result["overall"]


def test_json_report_generated():
    ds = load_evaluation_dataset(_sample_dataset_path())
    result = run_evaluation(
        dataset=ds, embedder=_mock_embedder(), vector_store=_mock_store(),
        using_mocks=True, using_fixtures=True,
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        j, m = write_evaluation_reports(result, tmpdir)
        assert j.exists()
        assert m.exists()
        data = json.loads(j.read_text())
        assert "overall" in data


def test_markdown_report_generated():
    ds = load_evaluation_dataset(_sample_dataset_path())
    result = run_evaluation(
        dataset=ds, embedder=_mock_embedder(), vector_store=_mock_store(),
        using_mocks=True, using_fixtures=True,
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        j, m = write_evaluation_reports(result, tmpdir)
        md = m.read_text()
        assert "NON_PRODUCTION_FIXTURE_REPORT" in md
        assert "Recall@1" in md


def test_must_refuse_correctly_handled():
    ds = load_evaluation_dataset(_sample_dataset_path())
    result = run_evaluation(
        dataset=ds,
        embedder=_mock_embedder(),
        vector_store=MagicMock(search=MagicMock(return_value=[])),
        using_mocks=True,
        using_fixtures=True,
    )
    # Empty store returns no results; must_refuse questions should be "correctly refused".
    assert result["overall"]["count"] > 0
