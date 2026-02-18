"""
app.py — Flask application entry point for BetterFeedback.

Routes:
    GET  /api/health   — Liveness check
    POST /api/analyze  — Analyze raw feedback text with AI, persist result
    GET  /api/history  — Return past analysis runs (most recent first)
"""

import logging
import os
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS
from pydantic import ValidationError

from database import AnalysisRun, db
from models import AnalyzeRequest, AnalyzeResponse
from services.ai_service import AIServiceError, FeedbackAnalyzer

# ---------------------------------------------------------------------------
# Logging — structured, timestamped, goes to stdout for easy log aggregation
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def create_app(config: dict | None = None) -> Flask:
    """
    Application factory — makes the app testable by accepting config overrides.
    Tests pass {'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'}
    to get a clean, isolated database per test run.
    """
    app = Flask(__name__)

    # Defaults — override via environment or config dict
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///betterfeedback.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if config:
        app.config.update(config)

    # In production, set ALLOWED_ORIGINS=https://your-app.vercel.app
    _origins = os.environ.get("ALLOWED_ORIGINS", "*")
    CORS(app, resources={r"/api/*": {"origins": _origins}})

    db.init_app(app)

    with app.app_context():
        db.create_all()
        logger.info("Database ready: %s", app.config["SQLALCHEMY_DATABASE_URI"])

    # Initialize the AI service once at startup (validates API key early)
    # Skip in testing mode — tests inject a mock via the route directly
    if not app.config.get("TESTING"):
        try:
            app._analyzer = FeedbackAnalyzer()
            logger.info("AI service ready.")
        except AIServiceError as e:
            logger.critical("Failed to initialize AI service: %s", e)
            sys.exit(1)

    # ── Routes ──────────────────────────────────────────────────────────────

    @app.get("/api/health")
    def health():
        """Quick liveness check."""
        return jsonify({"status": "ok"}), 200

    @app.post("/api/analyze")
    def analyze():
        """
        Analyze raw customer feedback text and persist the result.

        Request body (JSON):  { "text": "..." }
        Response body (JSON): { "items": [...], "count": N, "error": null }

        The response is ALWAYS a valid AnalyzeResponse — never a bare error string.
        """
        logger.info("POST /api/analyze — received request")

        # 1. Validate request body
        try:
            body = AnalyzeRequest.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            logger.warning("Request validation failed: %s", exc)
            response = AnalyzeResponse.from_error(
                "Invalid request: 'text' field is required and must be non-empty."
            )
            return jsonify(response.model_dump()), 400

        # 2. Call AI service
        analyzer = getattr(app, "_analyzer", None) or request.environ.get("_test_analyzer")
        try:
            items = analyzer.analyze(body.text)
        except AIServiceError as exc:
            logger.error("AI service error: %s", exc)
            response = AnalyzeResponse.from_error(str(exc))
            return jsonify(response.model_dump()), 502

        # 3. Persist to database
        try:
            run = AnalysisRun.create(
                input_text=body.text,
                items=[item.model_dump() for item in items],
            )
            db.session.add(run)
            db.session.commit()
            logger.info("Persisted analysis run id=%d with %d items.", run.id, run.item_count)
        except Exception as exc:
            logger.error("Failed to persist analysis run: %s", exc)
            db.session.rollback()
            # Non-fatal — still return results to the user

        # 4. Return validated response
        response = AnalyzeResponse.from_items(items)
        logger.info("Returning %d items to client.", response.count)
        return jsonify(response.model_dump()), 200

    @app.get("/api/history")
    def history():
        """
        Return past analysis runs, most recent first.
        Query param: ?limit=N (default 20, max 100)
        """
        limit = min(int(request.args.get("limit", 20)), 100)
        runs = (
            AnalysisRun.query.order_by(AnalysisRun.created_at.desc()).limit(limit).all()
        )
        logger.info("GET /api/history — returning %d runs.", len(runs))
        return jsonify([run.to_dict() for run in runs]), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    logger.info("Starting BetterFeedback API on http://localhost:5000")
    app.run(debug=True, port=5000)
