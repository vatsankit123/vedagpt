"""
Retrieval evaluation script — Phase 2.

Does NOT call Gemini. Evaluates retrieval quality offline.

Usage (PowerShell):
    python scripts\evaluate_retrieval.py --help
    python scripts\evaluate_retrieval.py `
        --dataset data\evaluation_questions.verified.json `
        --report-dir reports

Exit codes:
    0 — evaluation completed (reports generated)
    1 — failure
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.evaluation.runner import load_evaluation_dataset, run_evaluation
from app.evaluation.reports import write_evaluation_reports
from app.corpus.errors import EvaluationDatasetError


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline retrieval evaluation for VedaGPT. (Phase 2, no Gemini required)"
    )
    parser.add_argument("--dataset", required=True, type=Path,
                        help="Path to evaluation questions JSON file.")
    parser.add_argument("--report-dir", type=Path, default=Path("reports"),
                        help="Directory for output reports.")
    parser.add_argument("--threshold", type=float, default=None,
                        help="Score threshold override.")
    parser.add_argument("--candidate-k", type=int, default=20,
                        help="Number of candidates to retrieve per query.")
    parser.add_argument("--strategy", default="translation",
                        help="Document strategy label for report.")
    parser.add_argument("--use-mock-embedder", action="store_true", default=False,
                        help="Use deterministic mock embedder (no model download required).")
    args = parser.parse_args()

    settings = get_settings()

    # ── Load dataset ───────────────────────────────────────────────────────────
    try:
        dataset = load_evaluation_dataset(str(args.dataset))
    except EvaluationDatasetError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    is_fixture = dataset.is_fixture
    using_mocks = args.use_mock_embedder
    print(f"Loaded {len(dataset.questions)} evaluation question(s).")
    print(f"  fixture={is_fixture}  use_mock_embedder={using_mocks}")

    # ── Embedder ────────────────────────────────────────────────────────────────
    if using_mocks:
        # Deterministic mock: all-zeros vector.
        class _MockEmbedder:
            def embed_query(self, text: str):
                return [0.0] * settings.embedding_dimension
        embedder = _MockEmbedder()
        print("  Using deterministic mock embedder (zero vectors).")
    else:
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

    # ── Qdrant ─────────────────────────────────────────────────────────────────
    try:
        from app.rag.vector_store import VectorStore
        store = VectorStore(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            vector_size=settings.embedding_dimension,
            api_key=settings.qdrant_api_key,
        )
    except Exception as exc:
        print(f"ERROR connecting to Qdrant: {exc}", file=sys.stderr)
        return 1

    threshold = args.threshold if args.threshold is not None else settings.retrieval_score_threshold

    # ── Run evaluation ─────────────────────────────────────────────────────────
    result = run_evaluation(
        dataset=dataset,
        embedder=embedder,
        vector_store=store,
        score_threshold=threshold,
        candidate_k=args.candidate_k,
        collection_name=settings.qdrant_collection,
        embedding_model=settings.embedding_model,
        embedding_provider=settings.embedding_provider,
        document_strategy=args.strategy,
        environment=settings.app_env,
        using_mocks=using_mocks,
        using_fixtures=is_fixture,
    )

    # ── Reports ────────────────────────────────────────────────────────────────
    try:
        j, m = write_evaluation_reports(result, str(args.report_dir))
        print(f"\nEvaluation complete.")
        print(f"  JSON: {j}")
        print(f"  Markdown: {m}")
        label = result.get("fixture_label", "")
        if "FIXTURE" in label or "MOCK" in label:
            print("  *** This is a NON_PRODUCTION_FIXTURE_REPORT ***")
            print("  *** Metrics do not reflect real retrieval quality. ***")
    except Exception as exc:
        print(f"ERROR writing reports: {exc}", file=sys.stderr)
        return 1

    overall = result.get("overall", {})
    print(f"\n  Recall@1={overall.get('recall@1',0):.4f}  Recall@5={overall.get('recall@5',0):.4f}  MRR={overall.get('mrr',0):.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
