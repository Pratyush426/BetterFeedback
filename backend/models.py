"""
models.py — Pydantic schemas for BetterFeedback.
These are the single source of truth for data shapes across the entire app.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Category(str, Enum):
    BUG = "Bug"
    FEATURE = "Feature"
    PAIN_POINT = "Pain Point"


class FeedbackItem(BaseModel):
    """A single categorized feedback entry returned by the AI."""

    category: Category
    summary: str = Field(..., min_length=1, description="A concise one-sentence summary.")
    sentiment_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Sentiment from 0 (very negative) to 1 (very positive).",
    )
    original_text: str = Field(..., min_length=1, description="The verbatim source text.")

    @field_validator("sentiment_score")
    @classmethod
    def round_sentiment(cls, v: float) -> float:
        return round(v, 2)


class AnalyzeRequest(BaseModel):
    """Incoming request body for POST /api/analyze."""

    text: str = Field(..., min_length=1, description="Raw customer feedback text to analyze.")


class AnalyzeResponse(BaseModel):
    """Outgoing response body — always well-formed, never malformed."""

    items: list[FeedbackItem] = Field(default_factory=list)
    count: int = Field(default=0)
    error: Optional[str] = Field(default=None)

    @classmethod
    def from_items(cls, items: list[FeedbackItem]) -> "AnalyzeResponse":
        return cls(items=items, count=len(items))

    @classmethod
    def from_error(cls, message: str) -> "AnalyzeResponse":
        return cls(items=[], count=0, error=message)
