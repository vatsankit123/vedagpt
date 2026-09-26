"""
Phase 2 corpus data models.

These Pydantic models are the authoritative schema for:
  - SourceManifest  (legal/provenance metadata for a text edition)
  - CorpusProfile   (structural expectations for a corpus dataset)
  - CorpusRecord    (a single verse record inside the corpus)

IMPORTANT: These models do NOT contain or generate scripture content.
All content must be supplied by the project owner.
"""
from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Allowed enumerated values ──────────────────────────────────────────────────

VerificationStatus = Literal["PENDING", "VERIFIED", "REJECTED"]
CopyrightStatus = Literal[
    "PUBLIC_DOMAIN",
    "CREATIVE_COMMONS",
    "LICENSED",
    "ALL_RIGHTS_RESERVED",
    "UNVERIFIED",
    "DEMO_DATA_NOT_FOR_PRODUCTION",
]
ReviewStatus = Literal["PENDING", "VERIFIED", "REJECTED"]

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_FIELD_LEN = 4096
MAX_TRANSLATION_LEN = 32768


def _validate_optional_date(v: str) -> str:
    """Allow empty string or ISO-8601 date YYYY-MM-DD."""
    if v and not _ISO_DATE_RE.match(v):
        raise ValueError(f"Date must be empty or YYYY-MM-DD, got: {v!r}")
    return v


def _no_control_chars(v: str) -> str:
    """Reject strings containing ASCII control characters (except newline/tab)."""
    for ch in v:
        code = ord(ch)
        if code < 32 and code not in (9, 10, 13):
            raise ValueError(f"Field contains invalid control character U+{code:04X}")
    if "\uFFFD" in v:
        raise ValueError("Field contains Unicode replacement character (U+FFFD)")
    return v


# ── Source Manifest ────────────────────────────────────────────────────────────

class SourceManifest(BaseModel):
    """Legal and provenance metadata for a single scripture edition.

    The project owner must complete and verify every mandatory field.
    VedaGPT cannot determine legal status automatically.
    """

    source_id: str = Field(..., description="Unique identifier for this edition.")
    title: str = Field(..., description="Full title of the scripture.")
    translator: str = Field(default="", description="Translator name(s).")
    editor: str = Field(default="", description="Editor name(s).")
    commentator: str = Field(default="", description="Commentator name(s).")
    edition: str = Field(default="", description="Edition description.")
    publisher: str = Field(default="", description="Publisher or institution.")
    publication_year: Optional[int] = Field(default=None)
    publication_country: str = Field(default="")
    language: str = Field(default="English")
    original_language: str = Field(default="Sanskrit")
    source_reference: str = Field(default="", description="URL, ISBN, DOI, or archive ref.")
    source_type: str = Field(default="", description="e.g. book, website, archive")
    accessed_date: str = Field(default="", description="ISO-8601 date if digital source.")
    copyright_status: CopyrightStatus = Field(default="UNVERIFIED")
    license_name: str = Field(default="", description="SPDX id or descriptive name.")
    license_reference: str = Field(default="", description="URL to license text.")
    redistribution_permitted: bool = Field(default=False)
    commercial_use_permitted: bool = Field(default=False)
    modification_permitted: bool = Field(default=False)
    attribution_required: bool = Field(default=False)
    required_attribution: str = Field(default="")
    verification_status: VerificationStatus = Field(default="PENDING")
    verified_by: str = Field(default="")
    verified_date: str = Field(default="")
    notes: str = Field(default="")

    @field_validator("source_id")
    @classmethod
    def source_id_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v or v.startswith("replace-with"):
            raise ValueError("source_id must be a meaningful non-placeholder value.")
        return v

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty.")
        return v.strip()

    @field_validator("accessed_date", "verified_date")
    @classmethod
    def validate_dates(cls, v: str) -> str:
        return _validate_optional_date(v)

    def validate_for_production(self) -> list[str]:
        """Return list of blocking errors for production ingestion."""
        errors: list[str] = []
        if not self.translator.strip():
            errors.append("translator is required for production.")
        if not self.edition.strip():
            errors.append("edition is required for production.")
        if not self.source_reference.strip():
            errors.append("source_reference is required for production.")
        if self.copyright_status == "UNVERIFIED":
            errors.append("copyright_status must not be UNVERIFIED for production.")
        if not self.license_name.strip():
            errors.append("license_name is required for production.")
        if not self.license_reference.strip():
            errors.append("license_reference is required for production.")
        if self.verification_status != "VERIFIED":
            errors.append(f"verification_status must be VERIFIED, got: {self.verification_status}")
        if not self.verified_by.strip():
            errors.append("verified_by is required for production.")
        if not self.verified_date.strip():
            errors.append("verified_date is required for production.")
        if not self.redistribution_permitted:
            errors.append("redistribution_permitted must be true for production ingestion.")
        return errors


# ── Corpus Profile ─────────────────────────────────────────────────────────────

class CorpusProfile(BaseModel):
    """Structural expectations for a corpus dataset.

    The project owner must review and supply verified chapter/verse counts.
    Do NOT populate expected_verse_counts without verified information.
    """

    profile_id: str = Field(..., description="Unique identifier for this profile.")
    scripture: str = Field(..., description="Name of the scripture.")
    source_id: str = Field(..., description="References a SourceManifest.source_id.")
    expected_chapters: int = Field(default=18, ge=1)
    expected_verse_counts: dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Map of chapter number (as string) to expected verse count. "
            "Leave empty until the project owner has verified counts per edition."
        ),
    )
    allow_numbering_variants: bool = Field(default=True)
    numbering_notes: str = Field(default="")
    profile_version: int = Field(default=1, ge=1)
    review_status: ReviewStatus = Field(default="PENDING")
    reviewed_by: str = Field(default="")
    reviewed_date: str = Field(default="")

    @field_validator("profile_id", "scripture", "source_id")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be empty.")
        return v.strip()

    @field_validator("reviewed_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        return _validate_optional_date(v)


# ── Corpus Record ──────────────────────────────────────────────────────────────

class CorpusRecord(BaseModel):
    """A single verse record in the corpus.

    Translation and commentary are kept separate.
    Do NOT merge commentary into the translation field.
    """

    id: str = Field(..., description="Stable unique identifier, e.g. gita-2-47.")
    source_id: str = Field(..., description="References a SourceManifest.source_id.")
    scripture: str = Field(..., description="Scripture name, e.g. Bhagavad Gita.")
    chapter: int = Field(..., ge=1)
    verse: int = Field(..., ge=1)
    verse_end: Optional[int] = Field(default=None, ge=1)
    sanskrit: str = Field(default="")
    transliteration: str = Field(default="")
    translation: str = Field(..., min_length=1)
    commentary: str = Field(default="")
    translator: str = Field(default="")
    commentator: str = Field(default="")
    edition: str = Field(default="")
    language: str = Field(default="English")
    source_reference: str = Field(default="")
    copyright_status: CopyrightStatus = Field(default="UNVERIFIED")
    license_name: str = Field(default="")
    license_reference: str = Field(default="")
    content_hash: str = Field(default="")
    record_version: int = Field(default=1, ge=1)
    review_status: ReviewStatus = Field(default="PENDING")
    reviewed_by: str = Field(default="")
    reviewed_date: str = Field(default="")
    notes: str = Field(default="")

    @field_validator("id", "source_id", "scripture")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be empty.")
        return v

    @field_validator("translation")
    @classmethod
    def translation_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("translation must not be blank.")
        return v

    @field_validator("reviewed_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        return _validate_optional_date(v)

    @model_validator(mode="after")
    def validate_verse_range(self) -> "CorpusRecord":
        if self.verse_end is not None and self.verse_end < self.verse:
            raise ValueError(
                f"verse_end ({self.verse_end}) must be >= verse ({self.verse})."
            )
        return self

    def is_demo(self) -> bool:
        return self.copyright_status == "DEMO_DATA_NOT_FOR_PRODUCTION"

    def is_production_ready(self) -> bool:
        return (
            self.copyright_status not in ("UNVERIFIED", "DEMO_DATA_NOT_FOR_PRODUCTION")
            and self.review_status == "VERIFIED"
            and bool(self.translator.strip())
            and bool(self.edition.strip())
            and bool(self.source_reference.strip())
        )

    def validate_for_production(self) -> list[str]:
        errors: list[str] = []
        if not self.translator.strip():
            errors.append(f"record {self.id!r}: translator required for production.")
        if not self.edition.strip():
            errors.append(f"record {self.id!r}: edition required for production.")
        if not self.source_reference.strip():
            errors.append(f"record {self.id!r}: source_reference required for production.")
        if self.copyright_status in ("UNVERIFIED", "DEMO_DATA_NOT_FOR_PRODUCTION"):
            errors.append(
                f"record {self.id!r}: copyright_status={self.copyright_status!r} "
                "not allowed in production."
            )
        if self.review_status != "VERIFIED":
            errors.append(
                f"record {self.id!r}: review_status must be VERIFIED, "
                f"got {self.review_status!r}."
            )
        if not self.reviewed_by.strip():
            errors.append(f"record {self.id!r}: reviewed_by required for production.")
        if not self.reviewed_date.strip():
            errors.append(f"record {self.id!r}: reviewed_date required for production.")
        return errors
