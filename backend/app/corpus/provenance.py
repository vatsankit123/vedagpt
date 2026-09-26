"""
Provenance and licensing validation.

VedaGPT cannot determine legal status automatically.
The project owner must supply and verify all legal information.
"""
from __future__ import annotations

from app.corpus.models import SourceManifest
from app.corpus.errors import LicenseValidationError, ProvenanceValidationError


def validate_manifest_for_production(manifest: SourceManifest) -> None:
    """Raise ProvenanceValidationError or LicenseValidationError if the manifest
    is not suitable for production ingestion.

    This function does NOT decide legal status — it checks that the project
    owner has supplied and verified the required fields.
    """
    errors = manifest.validate_for_production()
    if not errors:
        return

    # Separate license vs provenance issues.
    license_issues = [e for e in errors if any(
        kw in e for kw in ("license", "redistribution", "copyright")
    )]
    prov_issues = [e for e in errors if e not in license_issues]

    if license_issues:
        raise LicenseValidationError(
            "Source manifest has licensing issues that prevent production ingestion:\n"
            + "\n".join(f"  - {e}" for e in license_issues)
        )
    if prov_issues:
        raise ProvenanceValidationError(
            "Source manifest has provenance issues that prevent production ingestion:\n"
            + "\n".join(f"  - {e}" for e in prov_issues)
        )


def load_and_validate_manifest(manifest_path: str, production: bool = False) -> SourceManifest:
    """Load a SourceManifest from a JSON file and optionally validate for production."""
    import json
    from pathlib import Path
    from app.corpus.errors import SourceManifestError

    p = Path(manifest_path)
    if not p.exists():
        raise SourceManifestError(f"Source manifest file not found: {manifest_path!r}")
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise SourceManifestError(f"Failed to read source manifest: {exc}") from exc

    try:
        manifest = SourceManifest.model_validate(data)
    except Exception as exc:
        raise SourceManifestError(f"Source manifest schema error: {exc}") from exc

    if production:
        validate_manifest_for_production(manifest)

    return manifest


def load_corpus_profile(profile_path: str) -> "CorpusProfile":
    """Load a CorpusProfile from a JSON file."""
    import json
    from pathlib import Path
    from app.corpus.models import CorpusProfile
    from app.corpus.errors import CorpusLoadError

    p = Path(profile_path)
    if not p.exists():
        raise CorpusLoadError(f"Corpus profile file not found: {profile_path!r}")
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise CorpusLoadError(f"Failed to read corpus profile: {exc}") from exc

    try:
        return CorpusProfile.model_validate(data)
    except Exception as exc:
        raise CorpusLoadError(f"Corpus profile schema error: {exc}") from exc
