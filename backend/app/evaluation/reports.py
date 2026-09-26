"""Evaluation report generation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.corpus.errors import ReportGenerationError


def _write(path: Path, content: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise ReportGenerationError(f"Failed to write report {path}: {exc}") from exc


def write_evaluation_reports(
    result: dict[str, Any],
    report_dir: str,
) -> tuple[Path, Path]:
    """Write JSON + Markdown evaluation reports. Returns (json_path, md_path)."""
    rdir = Path(report_dir)
    ts = result.get("timestamp", "")
    safe_ts = ts[:19].replace(":", "-").replace("T", "_") if ts else "run"
    json_path = rdir / f"retrieval_evaluation_{safe_ts}.json"
    md_path = rdir / f"retrieval_evaluation_{safe_ts}.md"

    _write(json_path, json.dumps(result, indent=2, ensure_ascii=False))

    label = result.get("fixture_label", "EVALUATION_REPORT")
    overall = result.get("overall", {})
    lat = result.get("latency", {})
    lines = [
        "# VedaGPT Retrieval Evaluation Report",
        "",
        f"> **{label}**",
        "",
        "## Configuration",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Run ID | `{result.get('run_id','')}` |",
        f"| Timestamp | {result.get('timestamp','')} |",
        f"| Environment | {result.get('environment','')} |",
        f"| Collection | `{result.get('collection_name','')}` |",
        f"| Embedding model | `{result.get('embedding_model','')}` |",
        f"| Document strategy | `{result.get('document_strategy','')}` |",
        f"| Using mocks | {result.get('using_mocks', False)} |",
        f"| Using fixtures | {result.get('using_fixtures', False)} |",
        "",
        "## Overall Metrics",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Questions | {overall.get('count', 0)} |",
        f"| Recall@1 | {overall.get('recall@1', 0):.4f} |",
        f"| Recall@3 | {overall.get('recall@3', 0):.4f} |",
        f"| Recall@5 | {overall.get('recall@5', 0):.4f} |",
        f"| Recall@10 | {overall.get('recall@10', 0):.4f} |",
        f"| MRR | {overall.get('mrr', 0):.4f} |",
        f"| False-grounded | {overall.get('false_grounded_count', 0)} |",
        f"| False-refusal | {overall.get('false_refusal_count', 0)} |",
        "",
        "## Latency",
        "",
        f"| Metric | Value (ms) |",
        f"|--------|-----------|",
        f"| Mean | {lat.get('mean', 0):.1f} |",
        f"| Median | {lat.get('median', 0):.1f} |",
        f"| P95 | {lat.get('p95', 0):.1f} |",
        f"| Max | {lat.get('max', 0):.1f} |",
        "",
    ]

    if result.get("by_category"):
        lines += ["## By Category", ""]
        lines += ["| Category | N | Recall@1 | Recall@5 | MRR |", "|----------|---|----------|----------|-----|"]
        for cat, m in result["by_category"].items():
            lines.append(
                f"| {cat} | {m.get('count',0)} | {m.get('recall@1',0):.3f} | "
                f"{m.get('recall@5',0):.3f} | {m.get('mrr',0):.3f} |"
            )
        lines.append("")

    if result.get("failed_cases"):
        lines += ["## Failed Cases", ""]
        for fc in result["failed_cases"][:20]:
            lines.append(f"- `{fc.get('id')}`: {fc.get('error','')}")
        lines.append("")

    _write(md_path, "\n".join(lines))
    return json_path, md_path
