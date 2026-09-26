"""Tests for SourceManifest schema and production validation."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.corpus.models import SourceManifest


def _valid() -> dict:
    return {
        "source_id": "test-source-v1",
        "title": "Bhagavad Gita",
        "translator": "T. Translator",
        "edition": "2nd Edition",
        "source_reference": "https://example.com/gita",
        "copyright_status": "PUBLIC_DOMAIN",
        "license_name": "Public Domain",
        "license_reference": "https://creativecommons.org/publicdomain/zero/1.0/",
        "redistribution_permitted": True,
        "verification_status": "VERIFIED",
        "verified_by": "J. Reviewer",
        "verified_date": "2024-01-15",
    }


def test_valid_manifest_accepted():
    m = SourceManifest.model_validate(_valid())
    assert m.source_id == "test-source-v1"
    assert m.verification_status == "VERIFIED"


def test_empty_source_id_rejected():
    data = _valid()
    data["source_id"] = ""
    with pytest.raises(ValidationError):
        SourceManifest.model_validate(data)


def test_placeholder_source_id_rejected():
    data = _valid()
    data["source_id"] = "replace-with-verified-source-id"
    with pytest.raises(ValidationError):
        SourceManifest.model_validate(data)


def test_empty_title_rejected():
    data = _valid()
    data["title"] = ""
    with pytest.raises(ValidationError):
        SourceManifest.model_validate(data)


def test_missing_translator_fails_production():
    data = _valid()
    data["translator"] = ""
    m = SourceManifest.model_validate(data)
    errors = m.validate_for_production()
    assert any("translator" in e for e in errors)


def test_missing_edition_fails_production():
    data = _valid()
    data["edition"] = ""
    m = SourceManifest.model_validate(data)
    errors = m.validate_for_production()
    assert any("edition" in e for e in errors)


def test_missing_source_reference_fails_production():
    data = _valid()
    data["source_reference"] = ""
    m = SourceManifest.model_validate(data)
    errors = m.validate_for_production()
    assert any("source_reference" in e for e in errors)


def test_unverified_source_fails_production():
    data = _valid()
    data["verification_status"] = "PENDING"
    m = SourceManifest.model_validate(data)
    errors = m.validate_for_production()
    assert any("verification_status" in e or "VERIFIED" in e for e in errors)


def test_invalid_verification_date_rejected():
    data = _valid()
    data["verified_date"] = "15/01/2024"  # Wrong format.
    with pytest.raises(ValidationError):
        SourceManifest.model_validate(data)


def test_redistribution_false_fails_production():
    data = _valid()
    data["redistribution_permitted"] = False
    m = SourceManifest.model_validate(data)
    errors = m.validate_for_production()
    assert any("redistribution" in e for e in errors)


def test_missing_verified_by_fails_production():
    data = _valid()
    data["verified_by"] = ""
    m = SourceManifest.model_validate(data)
    errors = m.validate_for_production()
    assert any("verified_by" in e for e in errors)


def test_missing_verified_date_fails_production():
    data = _valid()
    data["verified_date"] = ""
    m = SourceManifest.model_validate(data)
    errors = m.validate_for_production()
    assert any("verified_date" in e for e in errors)


def test_fully_valid_manifest_passes_production():
    m = SourceManifest.model_validate(_valid())
    errors = m.validate_for_production()
    assert errors == []
