"""
tests/test_models.py — Unit tests for Pydantic schemas.

These tests verify that the data layer enforces its own invariants
independently of the API or AI service. If these pass, the schema
is correct regardless of what the AI returns.
"""

import pytest
from pydantic import ValidationError

from models import AnalyzeRequest, AnalyzeResponse, Category, FeedbackItem


class TestFeedbackItem:
    def test_valid_item(self):
        item = FeedbackItem(
            category=Category.BUG,
            summary="Login is broken.",
            sentiment_score=0.1,
            original_text="Login is broken.",
        )
        assert item.category == Category.BUG
        assert item.sentiment_score == 0.1

    def test_sentiment_score_is_rounded(self):
        item = FeedbackItem(
            category=Category.FEATURE,
            summary="Wants dark mode.",
            sentiment_score=0.66666,
            original_text="I want dark mode.",
        )
        assert item.sentiment_score == 0.67

    def test_sentiment_score_below_zero_is_rejected(self):
        with pytest.raises(ValidationError):
            FeedbackItem(
                category=Category.BUG,
                summary="x",
                sentiment_score=-0.1,
                original_text="x",
            )

    def test_sentiment_score_above_one_is_rejected(self):
        with pytest.raises(ValidationError):
            FeedbackItem(
                category=Category.BUG,
                summary="x",
                sentiment_score=1.1,
                original_text="x",
            )

    def test_empty_summary_is_rejected(self):
        with pytest.raises(ValidationError):
            FeedbackItem(
                category=Category.BUG,
                summary="",
                sentiment_score=0.5,
                original_text="x",
            )

    def test_invalid_category_is_rejected(self):
        with pytest.raises(ValidationError):
            FeedbackItem(
                category="Complaint",   # not a valid Category
                summary="x",
                sentiment_score=0.5,
                original_text="x",
            )


class TestAnalyzeRequest:
    def test_empty_text_is_rejected(self):
        with pytest.raises(ValidationError):
            AnalyzeRequest(text="")

    def test_valid_text_is_accepted(self):
        req = AnalyzeRequest(text="The app crashes.")
        assert req.text == "The app crashes."


class TestAnalyzeResponse:
    def test_from_items_sets_count(self):
        items = [
            FeedbackItem(
                category=Category.BUG,
                summary="x",
                sentiment_score=0.1,
                original_text="x",
            )
        ]
        resp = AnalyzeResponse.from_items(items)
        assert resp.count == 1
        assert resp.error is None

    def test_from_error_has_empty_items(self):
        resp = AnalyzeResponse.from_error("Something went wrong")
        assert resp.items == []
        assert resp.count == 0
        assert resp.error == "Something went wrong"
