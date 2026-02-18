"""
services/ai_service.py — Gemini AI integration.

Change Resilience: This is the ONLY file that knows about the Gemini SDK.
To switch providers (e.g., OpenAI), replace this file's implementation
while keeping the same public interface: FeedbackAnalyzer.analyze(text).

Uses: google-genai (the new SDK, replacing deprecated google-generativeai)
"""

import json
import logging
import os

from google import genai
from google.genai import types
from dotenv import load_dotenv

from models import FeedbackItem

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — forces the LLM to return JSON matching FeedbackItem schema
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a customer feedback analyst. Your job is to read raw customer feedback and extract structured insights.

You MUST respond with ONLY a valid JSON array. No markdown, no explanation, no code fences — just the raw JSON array.

Each element in the array must be a JSON object with EXACTLY these fields:
- "category": one of "Bug", "Feature", or "Pain Point"
- "summary": a concise one-sentence summary of the feedback item (string)
- "sentiment_score": a float between 0.0 (very negative) and 1.0 (very positive)
- "original_text": the verbatim excerpt from the input that this item is based on (string)

Rules:
1. Split compound feedback into multiple items if needed.
2. Bugs are defects or broken functionality.
3. Features are requests for new or improved capabilities.
4. Pain Points are frustrations or usability issues that aren't clearly bugs or feature requests.
5. sentiment_score reflects the emotional tone of the original text, not your opinion of the issue.
6. If the input contains no actionable feedback, return an empty array: []

Example output:
[
  {
    "category": "Bug",
    "summary": "The login button does not respond on mobile devices.",
    "sentiment_score": 0.1,
    "original_text": "The login button is completely broken on my phone."
  }
]"""


class AIServiceError(Exception):
    """Raised when the AI service fails to produce a valid response."""
    pass


class FeedbackAnalyzer:
    """
    Analyzes raw feedback text using Gemini and returns validated FeedbackItem objects.

    Public interface:
        analyzer = FeedbackAnalyzer()
        items = analyzer.analyze("The app crashes on startup...")
    """

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise AIServiceError(
                "GEMINI_API_KEY environment variable is not set. "
                "Create a .env file based on .env.example."
            )
        self._client = genai.Client(api_key=api_key)
        self._model = "gemini-2.5-flash"
        logger.info("FeedbackAnalyzer initialized with model: %s", self._model)

    def analyze(self, text: str) -> list[FeedbackItem]:
        """
        Send feedback text to Gemini and return a list of validated FeedbackItem objects.

        Raises:
            AIServiceError: if the AI returns invalid JSON or an unexpected response.
        """
        logger.info("Sending %d characters of feedback to Gemini.", len(text))

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,  # Low temp for consistent, structured output
                ),
            )
            raw = response.text.strip()
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            raise AIServiceError(f"AI provider error: {exc}") from exc

        logger.debug("Raw AI response: %s", raw)

        # Strip accidental markdown code fences if the model adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("AI returned invalid JSON: %s", raw[:200])
            raise AIServiceError(f"AI returned invalid JSON: {exc}") from exc

        if not isinstance(data, list):
            logger.error("AI response is not a JSON array: %s", type(data))
            raise AIServiceError("AI response must be a JSON array.")

        items: list[FeedbackItem] = []
        for i, entry in enumerate(data):
            try:
                item = FeedbackItem(**entry)
                items.append(item)
            except Exception as exc:
                logger.warning("Skipping malformed item at index %d: %s — %s", i, entry, exc)
                # Skip malformed items rather than failing the whole request

        logger.info("Successfully parsed %d feedback items.", len(items))
        return items
