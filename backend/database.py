"""
database.py — SQLAlchemy setup and ORM models.

Design decisions:
- SQLite for zero-config local dev; swap DATABASE_URL env var for Postgres in production.
- Stores every analysis run: the raw input text, the structured results as JSON,
  and a timestamp. This gives the system an audit trail and enables history queries.
- Kept intentionally thin — no migrations framework needed at MVP scale.
  If the schema changes, drop and recreate (acceptable for a small internal tool).
"""

import json
import os
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class AnalysisRun(db.Model):
    """
    Persists one complete analysis request + its results.

    Invariants enforced at the DB level:
    - input_text is never null or empty (checked before insert in app.py)
    - result_json is always valid JSON (serialized from validated Pydantic models)
    - created_at is always UTC (set automatically on insert)
    """

    __tablename__ = "analysis_runs"

    id = db.Column(db.Integer, primary_key=True)
    input_text = db.Column(db.Text, nullable=False)
    result_json = db.Column(db.Text, nullable=False)   # JSON array of FeedbackItem dicts
    item_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        """Safe serialization — never exposes raw DB internals."""
        return {
            "id": self.id,
            "input_preview": self.input_text[:120] + ("…" if len(self.input_text) > 120 else ""),
            "item_count": self.item_count,
            "items": json.loads(self.result_json),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def create(cls, input_text: str, items: list[dict]) -> "AnalysisRun":
        """Factory — ensures result_json is always valid JSON."""
        return cls(
            input_text=input_text,
            result_json=json.dumps(items),
            item_count=len(items),
        )
