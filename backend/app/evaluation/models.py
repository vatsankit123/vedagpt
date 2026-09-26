"""
Phase 2 evaluation data models.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


EvalCategory = Literal[
    "direct_verse_reference",
    "exact_phrase",
    "concept_retrieval",
    "chapter_specific",
    "multi_verse_concept",
    "sanskrit_query",
    "transliteration_query",
    "paraphrase",
    "commentary_specific",
    "unsupported_modern_topic",
    "incorrect_verse_assumption",
    "prompt_injection",
    "ambiguous_philosophical",
    "cross_chapter_comparison",
    "adversarial_citation_request",
    "empty_query",
    "malformed_query",
    "very_long_query",
    "conflicting_verse_references",
]

Difficulty = Literal["easy", "medium", "hard"]
ReviewStatus = Literal["PENDING", "VERIFIED", "REJECTED"]


class EvaluationQuestion(BaseModel):
    """A single evaluation question with expected retrieval outcomes."""

    id: str = Field(..., description="Unique identifier, e.g. eval-001.")
    question: str = Field(default="")
    category: str = Field(default="")
    expected_document_ids: list[str] = Field(default_factory=list)
    acceptable_document_ids: list[str] = Field(default_factory=list)
    forbidden_document_ids: list[str] = Field(default_factory=list)
    must_refuse: bool = Field(default=False)
    explicit_reference: bool = Field(default=False)
    expected_chapter: Optional[int] = Field(default=None)
    expected_verse: Optional[int] = Field(default=None)
    language: str = Field(default="English")
    difficulty: str = Field(default="medium")
    notes: str = Field(default="")
    review_status: str = Field(default="PENDING")
    reviewed_by: str = Field(default="")
    reviewed_date: str = Field(default="")


class EvaluationDataset(BaseModel):
    """Container for a set of evaluation questions."""

    questions: list[EvaluationQuestion] = Field(default_factory=list)
    dataset_id: str = Field(default="")
    description: str = Field(default="")
    is_fixture: bool = Field(default=True)
    review_status: str = Field(default="PENDING")
