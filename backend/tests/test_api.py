"""
tests/test_api.py — Integration tests for Flask routes.

These tests verify the full request/response cycle using a mock AI service.
The mock means: no API key needed, no network calls, deterministic results.
Every test gets a fresh in-memory database (see conftest.py).
"""

import json


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.get_json() == {"status": "ok"}


class TestAnalyzeEndpoint:
    def test_valid_request_returns_200(self, client):
        res = client.post(
            "/api/analyze",
            json={"text": "The login button is broken."},
        )
        assert res.status_code == 200

    def test_response_shape_is_always_valid(self, client):
        """The API must NEVER return a shape the frontend can't handle."""
        res = client.post("/api/analyze", json={"text": "Some feedback."})
        data = res.get_json()
        assert "items" in data
        assert "count" in data
        assert "error" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["count"], int)

    def test_items_match_mock_analyzer_output(self, client):
        res = client.post("/api/analyze", json={"text": "Some feedback."})
        data = res.get_json()
        assert data["count"] == 2
        categories = [i["category"] for i in data["items"]]
        assert "Bug" in categories
        assert "Feature" in categories

    def test_empty_text_returns_400(self, client):
        res = client.post("/api/analyze", json={"text": ""})
        assert res.status_code == 400
        data = res.get_json()
        assert data["error"] is not None
        assert data["items"] == []

    def test_missing_text_field_returns_400(self, client):
        res = client.post("/api/analyze", json={})
        assert res.status_code == 400

    def test_ai_failure_returns_502_with_error_field(self, error_client):
        """Even on AI failure, the response shape must be valid."""
        res = error_client.post("/api/analyze", json={"text": "Some feedback."})
        assert res.status_code == 502
        data = res.get_json()
        assert data["error"] is not None
        assert data["items"] == []

    def test_successful_analysis_is_persisted(self, client, app):
        """Every successful analysis must be saved to the database."""
        from database import AnalysisRun
        client.post("/api/analyze", json={"text": "The login button is broken."})
        with app.app_context():
            runs = AnalysisRun.query.all()
            assert len(runs) == 1
            assert runs[0].item_count == 2


class TestHistoryEndpoint:
    def test_history_is_empty_initially(self, client):
        res = client.get("/api/history")
        assert res.status_code == 200
        assert res.get_json() == []

    def test_history_contains_run_after_analysis(self, client):
        client.post("/api/analyze", json={"text": "Some feedback."})
        res = client.get("/api/history")
        data = res.get_json()
        assert len(data) == 1
        assert data[0]["item_count"] == 2
        assert "created_at" in data[0]
        assert "input_preview" in data[0]

    def test_history_is_ordered_most_recent_first(self, client):
        client.post("/api/analyze", json={"text": "First feedback."})
        client.post("/api/analyze", json={"text": "Second feedback."})
        res = client.get("/api/history")
        data = res.get_json()
        assert len(data) == 2
        # Most recent first — second run should be at index 0
        assert "Second" in data[0]["input_preview"]

    def test_history_limit_param_is_respected(self, client):
        for i in range(5):
            client.post("/api/analyze", json={"text": f"Feedback {i}."})
        res = client.get("/api/history?limit=3")
        assert len(res.get_json()) == 3
