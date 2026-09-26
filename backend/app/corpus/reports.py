"""
Validation and ingestion report generation.

Generates:
  - JSON machine-readable reports
  - Markdown human-readable reports

Reports are written to a configurable reports/ directory.
Large timestamped reports must not be committed automatically.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.corpus.errors import ReportGenerationError

_SAFE_PATH_RE_PARTS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")


def _safe_filename(name: str) -> str:
    return "".join(c if c in _SAFE_PATH_RE_PARTS else "_" for c in name)


def _write_report(path: Path, content: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise ReportGenerationError(f"Failed to write report to {path}: {exc}") from exc


def generate_validation_reports(
    validation_result: dict[str, Any],
    corpus_path: str,
    manifest_path: str,
    profile_path: str,
    report_dir: str,
    environment: str = "development",
    allow_demo: bool = False,
) -> tuple[Path, Path]:
    """Write JSON + Markdown validation reports.

    Returns:
        (json_path, md_path)

    IMPORTANT: Reports from fixture/demo data must be clearly labelled.
    """
    run_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()
    rdir = Path(report_dir)

    safe_ts = ts[:19].replace(":", "-").replace("T", "_")
    json_path = rdir / f"corpus_validation_{safe_ts}.json"
    md_path = rdir / f"corpus_validation_{safe_ts}.md"

    stats = validation_result.get("stats", {})
    errors = validation_result.get("errors", [])
    warnings = validation_result.get("warnings", [])
    chapter_map = validation_result.get("chapter_map", {})

    is_fixture = allow_demo
    fixture_label = "NON_PRODUCTION_FIXTURE_REPORT" if is_fixture else "PRODUCTION_REPORT"

    # ── JSON report ────────────────────────────────────────────────────────────
    report_data = {
        "report_type": "corpus_validation",
        "fixture_label": fixture_label,
        "run_id": run_id,
        "timestamp": ts,
        "environment": environment,
        "corpus_path": corpus_path,
        "manifest_path": manifest_path,
        "profile_path": profile_path,
        "schema_version": 2,
        "statistics": stats,
        "errors": errors,
        "warnings": warnings,
        "chapter_distribution": {
            str(ch): vs for ch, vs in sorted(chapter_map.items())
        },
        "passed": len(errors) == 0,
        "using_demo_data": allow_demo,
    }
    _write_report(json_path, json.dumps(report_data, indent=2, ensure_ascii=False))

    # ── Markdown report ────────────────────────────────────────────────────────
    status = "✓ PASSED" if not errors else "✗ FAILED"
    lines = [
        f"# VedaGPT Corpus Validation Report",
        f"",
        f"> **{fixture_label}**",
        f"",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Run ID | `{run_id}` |",
        f"| Timestamp | {ts} |",
        f"| Environment | {environment} |",
        f"| Corpus | `{corpus_path}` |",
        f"| Status | **{status}** |",
        f"| Total records | {stats.get('total', 0)} |",
        f"| Errors | {len(errors)} |",
        f"| Warnings | {len(warnings)} |",
        f"",
    ]

    if errors:
        lines += ["## Errors", ""]
        for e in errors[:50]:
            lines.append(f"- {e}")
        if len(errors) > 50:
            lines.append(f"- ... and {len(errors)-50} more errors.")
        lines.append("")

    if warnings:
        lines += ["## Warnings", ""]
        for w in warnings[:50]:
            lines.append(f"- {w}")
        if len(warnings) > 50:
            lines.append(f"- ... and {len(warnings)-50} more warnings.")
        lines.append("")

    if chapter_map:
        lines += ["## Chapter Distribution", "", "| Chapter | Verse Count |", "|---------|-------------|"]
        for ch in sorted(chapter_map.keys()):
            lines.append(f"| {ch} | {len(chapter_map[ch])} |")
        lines.append("")

    _write_report(md_path, "\n".join(lines))
    return json_path, md_path


def generate_ingestion_reports(
    summary: dict[str, Any],
    report_dir: str,
) -> tuple[Path, Path]:
    """Write JSON + Markdown ingestion reports."""
    run_id = summary.get("run_id", str(uuid.uuid4()))
    ts = summary.get("timestamp", datetime.now(timezone.utc).isoformat())
    rdir = Path(report_dir)
    safe_ts = ts[:19].replace(":", "-").replace("T", "_")
    json_path = rdir / f"ingestion_{safe_ts}.json"
    md_path = rdir / f"ingestion_{safe_ts}.md"

    is_fixture = summary.get("allow_demo", False)
    fixture_label = "NON_PRODUCTION_FIXTURE_REPORT" if is_fixture else "PRODUCTION_REPORT"

    _write_report(json_path, json.dumps(
        {**summary, "fixture_label": fixture_label},
        indent=2, ensure_ascii=False
    ))

    lines = [
        "# VedaGPT Ingestion Report",
        "",
        f"> **{fixture_label}**",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Run ID | `{run_id}` |",
        f"| Timestamp | {ts} |",
        f"| Collection | `{summary.get('collection', '')}` |",
        f"| Dry Run | {summary.get('dry_run', False)} |",
        f"| Added | {summary.get('added', 0)} |",
        f"| Updated | {summary.get('updated', 0)} |",
        f"| Unchanged | {summary.get('unchanged', 0)} |",
        f"| Rejected | {summary.get('rejected', 0)} |",
        f"| Failed | {summary.get('failed', 0)} |",
        f"| Total | {summary.get('total', 0)} |",
        "",
    ]
    _write_report(md_path, "\n".join(lines))
    return json_path, md_path
