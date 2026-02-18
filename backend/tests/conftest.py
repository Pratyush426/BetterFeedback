"""
tests/conftest.py — Shared pytest fixtures.

Key design: every test gets a fresh in-memory SQLite database and a mock
AI analyzer. This means tests never hit the real Gemini API, never share
state between runs, and execute in milliseconds.
"""

import pytest

from app import create_app
from database import db as _db
from models import Category, FeedbackItem


class MockAnalyzer:
    """
    A deterministic stand-in for FeedbackAnalyzer.
    Returns a fixed list of items so tests are predictable and fast.
    Demonstrates the change-resilience seam: the route doesn't care
    which analyzer it gets, as long as it has an analyze(text) method.
    """

    def analyze(self, text: str) -> list[FeedbackItem]:
        return [
            FeedbackItem(
                category=Category.BUG,
                summary="Login button is broken.",
                sentiment_score=0.1,
                original_text="The login button is broken.",
            ),
            FeedbackItem(
                category=Category.FEATURE,
                summary="User wants dark mode.",
                sentiment_score=0.6,
                original_text="I wish there was dark mode.",
            ),
        ]


class ErrorAnalyzer:
    """Simulates an AI service failure — used to test error handling."""

    def analyze(self, text: str) -> list[FeedbackItem]:
        from services.ai_service import AIServiceError
        raise AIServiceError("Simulated AI failure")


@pytest.fixture
def app():
    """Create a fresh app with an in-memory DB for each test."""
    flask_app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client with the mock analyzer injected."""
    app._analyzer = MockAnalyzer()
    return app.test_client()


@pytest.fixture
def error_client(app):
    """Flask test client that simulates AI failures."""
    app._analyzer = ErrorAnalyzer()
    return app.test_client()
