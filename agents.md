# AI Guidance & Usage Log — BetterFeedback

This file documents how AI tools were used in this project, what constraints were applied,
how generated code was reviewed, and what risks were identified. It is a required submission artifact.

---

## 1. AI Tools Used

| Tool | Purpose |
|---|---|
| **Gemini 2.5 Flash** (runtime) | Categorizes customer feedback into structured JSON at request time |
| **Antigravity (AI coding assistant)** | Used during development to scaffold code, suggest structure, and generate boilerplate |

---

## 2. Constraints Applied to the Runtime AI (Gemini)

The system prompt in `backend/services/ai_service.py` enforces the following hard constraints:

```
- Respond with ONLY a valid JSON array. No markdown, no explanation, no code fences.
- Each element must have exactly four fields: category, summary, sentiment_score, original_text.
- category must be one of: "Bug", "Feature", "Pain Point" — no other values accepted.
- sentiment_score must be a float between 0.0 and 1.0.
- If no actionable feedback is found, return an empty array [].
```

**Why these constraints matter:** LLMs are non-deterministic. Without explicit output constraints,
the model may return prose, partial JSON, or invent new categories. The system prompt reduces
the output space to a predictable shape.

**Defense in depth:** Even with these constraints, the response is parsed and validated through
Pydantic (`FeedbackItem`) before any data reaches the frontend. Malformed items are skipped
individually with a warning log rather than crashing the request.

---

## 3. Constraints Applied to the Coding AI (Antigravity)

The following rules were applied when using AI to generate application code:

### Structural Rules
- `services/ai_service.py` must be the **only** file that imports the Gemini SDK.
  All other code interacts with `FeedbackAnalyzer` through its public interface only.
- All API responses must go through `AnalyzeResponse` (Pydantic). The API must never
  return a raw exception, a bare string, or an unvalidated dict.
- The app must use the **application factory pattern** (`create_app()`) so tests can
  inject configuration without touching global state.

### Simplicity Rules
- No ORMs with migrations at MVP scale — `db.create_all()` is sufficient.
- No async, no task queues, no caching layers unless explicitly required.
- No frontend state management libraries — React `useState` and `useCallback` only.

### What Was Reviewed After Generation
Every AI-generated file was reviewed for:
1. **Correctness of error handling** — does every failure path return a valid `AnalyzeResponse`?
2. **Correct use of Pydantic v2 API** — `model_validate`, `model_dump` (not v1's `parse_obj`, `dict`)
3. **Test isolation** — do tests share state through the database or global variables?
4. **SQL injection surface** — SQLAlchemy ORM used throughout; no raw SQL strings.

---

## 4. Known Risks & Weaknesses

| Risk | Severity | Mitigation |
|---|---|---|
| Gemini returns unexpected JSON structure | Medium | Pydantic validation + per-item skip on failure |
| Gemini rate limits / quota exhaustion | Medium | `AIServiceError` caught and returned as 502 with error field |
| SQLite not suitable for concurrent writes | Low (MVP) | Swap `DATABASE_URL` env var for Postgres in production |
| No authentication on `/api/analyze` | Low (MVP) | Anyone with the URL can call the API and consume quota |
| LLM hallucination on ambiguous feedback | Low | Prompt constraints reduce but don't eliminate this |
| Cold start latency on Render free tier (~30s) | Low | Hit `/api/health` first to wake the server |

---

## 5. How to Extend This System

### Adding a new feedback category (e.g., "Compliment")
1. Add `COMPLIMENT = "Compliment"` to `Category` enum in `models.py`
2. Update the system prompt in `ai_service.py` to include the new category
3. Add a new column in the React `Dashboard.jsx` `COLUMN_CONFIG` object
4. Add a test in `test_models.py` verifying the new category is accepted

**Impact radius:** 3 files. No database migration needed (category is stored as a string).

### Switching from Gemini to OpenAI
1. Replace `backend/services/ai_service.py` with an OpenAI implementation
2. Keep the same public interface: `FeedbackAnalyzer.analyze(text) -> list[FeedbackItem]`
3. All routes, tests, and models remain unchanged

**Impact radius:** 1 file.

### Adding user authentication
1. Add a `User` model to `database.py`
2. Add `user_id` foreign key to `AnalysisRun`
3. Add auth middleware to `app.py`
4. Frontend: add login flow before the upload screen

**Impact radius:** 2 backend files + frontend. No changes to AI service or Pydantic models.
