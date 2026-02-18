# BetterFeedback

> AI-powered customer feedback categorization — built with Flask, React, and Gemini.

Upload a block of raw customer feedback and get it instantly categorized into **Bugs**, **Feature Requests**, and **Pain Points**, each with a sentiment score and a concise summary. Every analysis is persisted to a database with a full history view.

---

## What It Does

Paste or upload customer feedback text → the system sends it to Gemini AI with a strict schema-enforcing prompt → the response is validated through Pydantic → structured cards appear in a three-column dashboard.

```
Input:  "The login button is broken. I wish there was dark mode. The app is painfully slow."

Output:
  Bug          → "Login button is non-functional."          sentiment: 0.10
  Feature      → "User requests a dark mode option."        sentiment: 0.65
  Pain Point   → "App performance is unacceptably slow."    sentiment: 0.20
```

---

## Stack

| Layer | Technology |
|---|---|
| Backend API | Python · Flask · Pydantic v2 |
| AI Integration | Gemini 2.5 Flash (`google-genai`) |
| Database | SQLAlchemy · SQLite (swap `DATABASE_URL` for Postgres) |
| Frontend | React 18 · Vite |
| Tests | Pytest (22 tests, ~0.14s, no API key needed) |

---

## Project Structure

```
betterfeedback/
├── backend/
│   ├── services/
│   │   └── ai_service.py     # Only file that imports the Gemini SDK
│   ├── tests/
│   │   ├── conftest.py       # MockAnalyzer + in-memory DB fixtures
│   │   ├── test_models.py    # Pydantic schema unit tests (8 tests)
│   │   └── test_api.py       # Route integration tests (14 tests)
│   ├── app.py                # Application factory + routes
│   ├── database.py           # SQLAlchemy ORM model
│   ├── models.py             # Pydantic schemas (single source of truth)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Dashboard.jsx # Three-column layout
│       │   └── FileUpload.jsx
│       └── App.jsx           # State machine: idle → ready → loading → success/error
├── agents.md                 # AI usage log and constraints (required artifact)
└── README.md
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- A [Gemini API key](https://aistudio.google.com/app/apikey) (free)

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Open .env and set: GEMINI_API_KEY=your_key_here
python app.py
# → http://localhost:5000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Tests

```bash
cd backend
python -m pytest tests/ -v
# 22 passed in ~0.14s — no API key or network required
```

---

## API Reference

### `GET /api/health`
```json
{ "status": "ok" }
```

### `POST /api/analyze`
Request:
```json
{ "text": "The export button crashes every time." }
```
Response — **always this exact shape**, never a bare error:
```json
{
  "items": [
    {
      "category": "Bug",
      "summary": "Export button causes a crash.",
      "sentiment_score": 0.08,
      "original_text": "The export button crashes every time."
    }
  ],
  "count": 1,
  "error": null
}
```

### `GET /api/history?limit=20`
Returns past analysis runs, most recent first.

---

## Key Technical Decisions

### 1. Pydantic as the contract layer
All data shapes — request bodies, AI responses, API responses — are defined once in `models.py`. The API is guaranteed to always return `{items, count, error}`. The frontend never needs to handle unexpected shapes.

### 2. Application factory for testability
`app.py` exports `create_app(config)` instead of a global `app`. Tests inject `SQLALCHEMY_DATABASE_URI: sqlite:///:memory:` to get a clean, isolated database per test — no patching or mocking of the DB layer required.

### 3. AI service as a swappable seam
`services/ai_service.py` is the only file that imports `google-genai`. It exposes one method: `analyze(text) -> list[FeedbackItem]`. Switching to OpenAI means replacing one file. Tests use `MockAnalyzer` — same interface, no network calls, deterministic output.

### 4. Defense in depth on AI output
The system prompt constrains Gemini to return a JSON array matching the schema exactly. Even so, the response is validated item-by-item through Pydantic. Malformed items are skipped with a warning log rather than failing the whole request.

### 5. SQLite with zero config, Postgres-ready
The DB URI comes from the `DATABASE_URL` environment variable (defaults to `sqlite:///betterfeedback.db`). No code changes needed to switch to Postgres in production.

---

## Known Weaknesses & Tradeoffs

| Weakness | Tradeoff Made |
|---|---|
| No authentication | Acceptable for an MVP demo; anyone with the URL can call the API |
| SQLite not suitable for concurrent writes | Zero-config for local dev; swap `DATABASE_URL` for Postgres to fix |
| LLM output is non-deterministic | System prompt + Pydantic validation reduce but don't eliminate bad output |
| No streaming | Simpler code; the full response arrives at once (~2–4s) |

---

## How to Extend

**Add a new feedback category (e.g., "Compliment")**
1. Add `COMPLIMENT = "Compliment"` to `Category` enum in `models.py`
2. Update the system prompt in `services/ai_service.py`
3. Add a column in `Dashboard.jsx`
4. Add a test in `test_models.py`
→ Impact: 3 files, no DB migration needed.

**Switch AI provider (e.g., OpenAI)**
1. Replace `services/ai_service.py` — keep the same `analyze(text) -> list[FeedbackItem]` interface
→ Impact: 1 file. Zero changes to routes, models, or tests.

**Add user authentication**
1. Add `User` model to `database.py`, `user_id` FK to `AnalysisRun`
2. Add auth middleware to `app.py`
3. Add login flow to frontend
→ Impact: 2 backend files + frontend. AI service and Pydantic models untouched.

---

## AI Usage

See [`agents.md`](./agents.md) for full documentation of:
- Constraints applied to the runtime AI (Gemini system prompt rules)
- Constraints applied to the coding AI (structural and simplicity rules)
- What was reviewed after code generation
- Known risks and mitigations
