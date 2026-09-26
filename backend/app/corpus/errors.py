"""
Phase 2 corpus error types.

All errors are internal. API-facing errors must remain safe and generic.
"""
from __future__ import annotations

class CorpusLoadError(Exception):
    """Failed to load corpus file."""

class CorpusValidationError(Exception):
    """Corpus failed record-level or corpus-level validation."""

class SourceManifestError(Exception):
    """Source manifest is missing, invalid, or rejected."""

class ProvenanceValidationError(Exception):
    """Provenance metadata is invalid or incomplete."""

class LicenseValidationError(Exception):
    """License metadata is missing, invalid, or prohibits redistribution."""

class NormalizationError(Exception):
    """A record could not be deterministically normalized."""

class DocumentBuildError(Exception):
    """Failed to construct an embedding document from a record."""

class EmbeddingConfigurationError(Exception):
    """Embedding provider, model, or dimension is missing or inconsistent."""

class EmbeddingGenerationError(Exception):
    """Embedding generation failed for one or more records."""

class CollectionSchemaError(Exception):
    """Qdrant collection schema is incompatible with the current pipeline."""

class IngestionError(Exception):
    """Ingestion pipeline failed for one or more records."""

class ReferenceParseError(Exception):
    """Failed to parse an explicit verse reference from user input."""

class RetrievalError(Exception):
    """Retrieval pipeline encountered an unrecoverable error."""

class EvaluationDatasetError(Exception):
    """Evaluation dataset is missing, invalid, or incompatible."""

class EvaluationRunError(Exception):
    """Evaluation run failed."""

class ReportGenerationError(Exception):
    """Failed to write a validation or evaluation report."""
