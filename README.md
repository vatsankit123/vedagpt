# VedaGPT — Phase 1

> **Educational Disclaimer**: VedaGPT is an educational AI system that generates explanations
> from selected indexed sources. Responses may contain errors and should be verified against the
> cited edition and, where appropriate, qualified scholars. The system does not represent every
> philosophical or religious tradition. It does not provide professional medical, legal, or
> financial conclusions based on scripture.

---

## 1. Project Purpose

VedaGPT is a Retrieval-Augmented Generation (RAG) application that answers questions about
indexed Indian scripture passages and provides precise, traceable citations. Every citation is
built directly from the metadata stored in the vector database — the LLM is never asked to
generate or invent chapter or verse references.

Phase 1 is a deliberately minimal, reliable proof of concept using one verified Bhagavad Gita
edition.

---

## 2. Phase 1 Scope

### Included
- FastAPI backend with `/health` and `/api/v1/chat` endpoints
- Pydantic v2 request/response schemas with input validation
- Structured Bhagavad Gita JSON corpus ingestion
- Qdrant vector store (local via Docker Compose)
- Pluggable embedding provider (sentence-transformers, OpenAI, Cohere)
- Evidence sufficiency checking before calling the LLM
- Anthropic Claude generation with strict grounding prompt
- Citation building from Qdrant metadata (never from LLM output)
- Citation validation (rejects invented IDs, deduplicates, validates chapter/verse)
- Corpus validation script with detailed error reporting
- Automated unit tests (all external services mocked)
- Docker Compose for local Qdrant
- Evaluation question dataset

<<<<<<< HEAD
### Excluded (Phase 2+)
- React / React Native frontend
- User authentication and JWT
- PostgreSQL chat history
- Multi-agent orchestration (LangGraph)
- Knowledge graph
- Fine-tuning
- Voice features
- Payments / subscriptions
- Complete Vedic corpus
- Production cloud deployment

---

## 3. Architecture Overview

```
User → POST /api/v1/chat
         │
         ▼
    Input validation (Pydantic, length check)
         │
         ▼
    Embed question (EmbeddingProvider)
         │
         ▼
    Search Qdrant (VectorStore.search)
         │
         ▼
    Evidence sufficiency check (RetrieverService)
         │
     ┌───┴──────────────┐
     │ Insufficient      │ Sufficient
     ▼                   ▼
  Return                Build citations from metadata
  grounded=false        (CitationValidator — before generation)
                         │
                         ▼
                    Generate with Claude (GeneratorService)
                    [Grounding prompt + XML-delimited passages]
                         │
                         ▼
                    Validate citations (CitationValidator)
                         │
                         ▼
                    Return ChatResponse
```

---

## 4. Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Python | 3.11 | |
| Docker | 24.x | For local Qdrant |
| Docker Compose | v2 | Bundled with Docker Desktop |
| Anthropic API key | — | From console.anthropic.com |

---

## 5. Environment Setup

```powershell
# PowerShell
cd backend
Copy-Item .env.example .env
# Edit .env and fill in ANTHROPIC_API_KEY and other required values
notepad .env
```

```bash
# POSIX shell
cd backend
cp .env.example .env
# Edit .env and fill in ANTHROPIC_API_KEY
nano .env
```

---

## 6. Installing Dependencies

```powershell
# PowerShell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# POSIX shell
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **Embedding model download**: The default sentence-transformers model
> (`paraphrase-multilingual-MiniLM-L12-v2`, ~480 MB) is downloaded automatically
> on first use. Ensure you have sufficient disk space and a network connection.

---

## 7. Starting Qdrant

```bash
# From the repository root
docker-compose up -d

# Verify Qdrant is healthy
curl http://localhost:6333/healthz

# View logs
docker-compose logs -f qdrant

# Stop (preserves data)
docker-compose stop

# Reset — deletes ALL stored vectors
docker-compose down -v
```

---

## 8. Corpus Format

Each verse record in the JSON corpus must conform to this schema:

```json
{
  "id": "gita-2-47",
  "scripture": "Bhagavad Gita",
  "chapter": 2,
  "verse": 47,
  "sanskrit": "",
  "transliteration": "",
  "translation": "...",
  "commentary": "",
  "translator": "Translator Name",
  "edition": "Edition Name",
  "language": "English",
  "source_reference": "Full bibliographic reference",
  "copyright_status": "VERIFIED",
  "license_notes": ""
}
```

Valid values for `copyright_status`:

| Value | Meaning |
|-------|---------|
| `VERIFIED` | License confirmed by project owner — safe for production |
| `UNVERIFIED` | License not yet confirmed — blocked in production |
| `DEMO_DATA_NOT_FOR_PRODUCTION` | Synthetic test fixture — blocked in production |

---

## 9. Corpus Licensing Warning

⚠️ **Do not ingest any text unless its copyright status has been verified by the project owner.**

The ingestion pipeline will reject records marked `UNVERIFIED` or
`DEMO_DATA_NOT_FOR_PRODUCTION` unless `ALLOW_UNVERIFIED_DEMO_DATA=true` is set in `.env`
(for local development only).

Recommended sources for legally usable Bhagavad Gita translations:
- Translations published before 1928 (US public domain — verify jurisdiction separately)
- Open-access translations with an explicit Creative Commons or equivalent license
- Translations where the project owner holds a license or permission from the publisher

Do not assume any particular edition is public domain without verification.

---

## 10. Validating the Corpus

```powershell
# PowerShell — production mode (DEMO records rejected)
python scripts/validate_corpus.py --corpus data/bhagavad_gita.sample.json

# With demo records allowed (development only)
python scripts/validate_corpus.py --corpus data/bhagavad_gita.sample.json --allow-demo
```

```bash
# POSIX shell
python scripts/validate_corpus.py --corpus data/bhagavad_gita.sample.json
python scripts/validate_corpus.py --corpus data/bhagavad_gita.sample.json --allow-demo
```

The script reports all errors and warnings and exits with code 1 if validation fails.

---

## 11. Running Ingestion

> Qdrant must be running before ingestion. Run validation first.

```powershell
# PowerShell — ingest demo fixture (development only)
python scripts/ingest_qdrant.py --corpus data/bhagavad_gita.sample.json --allow-demo

# Ingest a verified production corpus
python scripts/ingest_qdrant.py --corpus data/bhagavad_gita.real.json
```

```bash
# POSIX shell
python scripts/ingest_qdrant.py --corpus data/bhagavad_gita.sample.json --allow-demo
python scripts/ingest_qdrant.py --corpus data/bhagavad_gita.real.json
```

Ingestion is **idempotent** — re-running will upsert (overwrite) existing records without
creating duplicates.

---

## 12. Starting the FastAPI Server

```powershell
# PowerShell — from the backend/ directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# POSIX shell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 13. Example API Requests

### Health check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok", "service": "vedagpt-api"}
```

### Ask a question

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the Bhagavad Gita teach about attachment to results?", "top_k": 5}'
```

```powershell
# PowerShell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/chat" `
  -ContentType "application/json" `
  -Body '{"question": "What does the Bhagavad Gita teach about attachment to results?", "top_k": 5}'
```

Expected grounded response shape:
```json
{
  "answer": "A grounded explanation based on retrieved passages.",
  "grounded": true,
  "sources": [
    {
      "document_id": "gita-2-47",
      "scripture": "Bhagavad Gita",
      "chapter": 2,
      "verse": 47,
      "translation": "Retrieved translation text.",
      "translator": "Translator name",
      "edition": "Edition name",
      "source_reference": "Bibliographic reference",
      "retrieval_score": 0.89
    }
  ],
  "message": null
}
```

Expected insufficient-evidence response:
```json
{
  "answer": "I could not find sufficient support for this question in the currently indexed sources.",
  "grounded": false,
  "sources": [],
  "message": "Insufficient evidence in the indexed corpus."
}
```

---

## 14. Running Tests

```powershell
# PowerShell — from backend/ directory
pytest -v
```

```bash
# POSIX shell
pytest -v
```

Tests run without any network calls, Qdrant, or Anthropic API key.
All external services are mocked in `tests/conftest.py`.

To run a specific test file:

```bash
pytest tests/test_corpus_validation.py -v
pytest tests/test_citation_validation.py -v
pytest tests/test_chat_api.py -v
```

---

## 15. Running Evaluation

```bash
# View the evaluation dataset
cat data/evaluation_questions.json
```

The evaluation dataset (`data/evaluation_questions.json`) contains 10 questions across 6
categories. Automated evaluation against a live API is a Phase 2 task. To manually evaluate:

1. Start the server and ingest a verified corpus.
2. For each question in the dataset, send a request to `/api/v1/chat`.
3. For `must_refuse: true` questions, verify `grounded: false`.
4. For other questions, verify `grounded: true` and that `sources` contains
   the expected document IDs (once a verified corpus is available).

---

## 16. Troubleshooting Common Errors

### `Connection refused` on Qdrant

Qdrant is not running. Start it with `docker-compose up -d`.

### `ANTHROPIC_API_KEY is not set`

Add your API key to `backend/.env`. The `/health` endpoint works without it;
`/api/v1/chat` requires it.

### `sentence-transformers model download fails`

Check network connectivity and disk space (~480 MB for the default model).
Alternatively, set `EMBEDDING_PROVIDER=openai` or `cohere` and configure the
corresponding API key.

### `Collection ... does not exist`

Run `python scripts/ingest_qdrant.py --corpus data/... --allow-demo` to create
the collection and ingest data.

### `copyright_status ... not allowed in production`

Your corpus has `UNVERIFIED` or `DEMO_DATA_NOT_FOR_PRODUCTION` records.
Either fix the records or set `ALLOW_UNVERIFIED_DEMO_DATA=true` in `.env`
for local development only.

### Validation error on `top_k`

`top_k` must be between 1 and 20. The default is 5.

---

## 17. Known Limitations

1. **No verified corpus supplied** — The sample fixture (`bhagavad_gita.sample.json`)
   contains synthetic placeholder translations labelled `DEMO_DATA_NOT_FOR_PRODUCTION`.
   No authentic scripture text is present until you supply a legally verified corpus.

2. **Score threshold requires tuning** — The default `RETRIEVAL_SCORE_THRESHOLD=0.30`
   is a starting point. It must be evaluated and tuned against a real corpus.
   Cosine similarity is not equivalent to factual confidence.

3. **Single-turn only** — No conversation history is maintained (Phase 2 feature).

4. **English queries only validated** — The embedding model supports multilingual input,
   but retrieval quality for non-English queries has not been evaluated.

5. **No frontend** — The API is designed to be called by a frontend (Phase 2) or
   directly via curl/Postman.

---

## 18. Phase 1 → Phase 2 Boundary

Phase 1 ends when:
- A verified corpus is ingested and retrieval quality is validated.
- All unit tests pass.
- The `GET /health` and `POST /api/v1/chat` endpoints work end-to-end.

**Phase 2 will add** (not implemented here):
- React or React Native frontend
- User authentication (JWT)
- PostgreSQL-backed conversation history
- Additional scripture sources
- Multi-agent orchestration
- Voice features
- Production deployment

Do not implement any Phase 2 features in this codebase until Phase 1 is accepted.
=======
Do not upload API keys, `.env` files, copyrighted scripture datasets, or private credentials to this repository.
<<<<<<< HEAD
=======


phase 3 prompt 

You are working on VedaGPT, a source-grounded educational RAG application for understanding selected Indian scriptures.

CURRENT PROJECT STATUS

The following work is already complete:

1. Phase 1 FastAPI backend.
2. Qdrant vector database integration.
3. Configurable embedding provider.
4. Google Gemini generation provider.
5. Evidence-sufficiency validation.
6. Programmatic scripture citations.
7. Citation validation.
8. Phase 2 source-manifest and corpus-profile schemas.
9. Corpus validation and deterministic normalization.
10. Provenance and licensing validation.
11. Stable content hashing.
12. Idempotent Qdrant ingestion.
13. Exact verse-reference parsing.
14. Offline retrieval evaluation.
15. Recall@K and Mean Reciprocal Rank metrics.
16. JSON and Markdown evaluation reports.
17. Application-level Qdrant integration testing.
18. All Phase 1 and Phase 2 tests are passing.
19. Phase 2 changes have been pushed to GitHub.

Your task is to implement PHASE 3 ONLY.

PHASE 3 TITLE

Production-Quality React Web Frontend and FastAPI Integration

PRIMARY OBJECTIVE

Build a polished, responsive, accessible VedaGPT web application that connects to the existing FastAPI backend and provides a ChatGPT-style scripture-learning experience.

The frontend must:

1. Allow users to ask scripture-related questions.
2. Display grounded answers clearly.
3. Display structured scripture citations from the backend.
4. Allow users to inspect source details.
5. Clearly distinguish grounded and ungrounded responses.
6. Clearly identify demonstration data.
7. Handle API failures safely.
8. Work well on desktop, tablet, and mobile browsers.
9. Preserve the existing backend API contract.
10. Avoid implementing Phase 4 features.

PHASE 3 BOUNDARY

Implement:

- React frontend
- TypeScript
- Vite
- Responsive application layout
- VedaGPT branding
- Chat interface
- Question composer
- Answer rendering
- Source citation cards
- Source details drawer or modal
- Suggested questions
- Grounded-response state
- Ungrounded-response state
- Loading state
- Retry state
- Empty state
- API error state
- Backend-unavailable state
- Demo-data warning
- Light and dark theme
- Accessibility
- Typed API client
- Environment-based backend URL
- Frontend tests
- Frontend documentation
- Backend CORS validation
- Development integration with FastAPI
- Production build validation
- Safe Markdown rendering if required
- Request cancellation
- Duplicate-submission protection
- Basic client-side conversation state
- Optional local conversation persistence if implemented safely

Do not implement:

- User registration
- User authentication
- JWT login
- OAuth
- PostgreSQL chat history
- Server-side conversation storage
- Cross-device synchronization
- Payments
- Subscriptions
- Premium plans
- React Native
- Android application
- iOS application
- Voice input
- Text-to-speech
- Multi-agent systems
- LangGraph agents
- Knowledge graphs
- Fine-tuning
- New scripture ingestion
- Cloud deployment
- Google Play publishing
- Apple App Store publishing
- Admin dashboard
- User analytics
- Production monitoring
- Phase 4 features

CRITICAL WORKSPACE REQUIREMENT

Before making any changes, run:

Get-Location
git status
git branch --show-current
git log -5 --oneline
python --version
node --version
npm --version

The expected repository is:

C:\Users\vatsa\Downloads\vedagpt-git

Do not work inside the old vedagpt-main ZIP folder.

If the correct Git repository is not open, stop and report the current location.

GIT REQUIREMENTS

Before starting implementation:

1. Confirm the working tree is clean.
2. Confirm Phase 2 is pushed to origin/main.
3. Confirm the current branch.

If currently on main, create and switch to:

phase-3-web-frontend

Use:

git checkout -b phase-3-web-frontend

Do not force-push.

Do not rewrite Git history.

Do not use git reset --hard.

Do not use git clean -fd.

Do not delete Phase 1 or Phase 2 code.

Do not modify files outside the repository.

Do not automatically merge Phase 3 into main.

Do not push unless explicitly requested by the project owner.

EXISTING BACKEND CONTRACT

Inspect the real backend implementation before creating frontend types.

Do not assume the exact response shape without reading:

- backend/app/schemas/chat.py
- backend/app/api/chat.py
- backend/app/services/chat_service.py
- backend/app/main.py
- backend/app/config.py

Preserve:

GET /health

POST /api/v1/chat

The frontend must use the existing request and response contract exactly.

Do not modify backend schemas merely to make frontend implementation easier.

If backward-compatible optional fields are truly required, clearly explain the need and add regression tests before modifying the backend.

BACKEND RESPONSE HANDLING

The frontend must support at least these logical response states:

1. Grounded response with one or more sources.
2. Grounded response with several sources.
3. Ungrounded or insufficient-evidence response.
4. Malformed or incomplete backend response.
5. Backend validation error.
6. Backend internal error.
7. Network error.
8. Request timeout.
9. Request cancellation.
10. Backend unavailable.
11. Empty answer.
12. Empty source list.
13. Quota or provider failure represented safely by the backend.

Never display raw stack traces, API keys, environment values, provider errors, or internal exception text.

TECHNOLOGY STACK

Use this stack unless the existing repository already contains a compatible frontend framework:

- React
- TypeScript
- Vite
- React Router
- TanStack Query
- Tailwind CSS
- Vitest
- React Testing Library
- user-event
- MSW or an equivalent request-mocking approach
- Zod for runtime response validation if appropriate
- Lucide React for icons if needed

Use npm unless an existing lockfile establishes another package manager.

Do not mix npm, pnpm, and Yarn lockfiles.

Pin compatible package versions through package.json and commit the lockfile.

Do not use a large UI framework unless justified.

Keep the application maintainable and lightweight.

FRONTEND LOCATION

Create the frontend under:

frontend/

Recommended structure:

frontend/
  src/
    app/
      App.tsx
      router.tsx
      providers.tsx

    api/
      client.ts
      chatApi.ts
      healthApi.ts
      schemas.ts
      types.ts
      errors.ts

    components/
      layout/
        AppHeader.tsx
        AppShell.tsx
        MobileNavigation.tsx

      chat/
        ChatPanel.tsx
        ChatMessage.tsx
        UserMessage.tsx
        AssistantMessage.tsx
        ChatComposer.tsx
        ChatEmptyState.tsx
        ChatLoadingState.tsx
        ChatErrorState.tsx
        SuggestedQuestions.tsx
        GroundingBadge.tsx

      sources/
        SourceCard.tsx
        SourceList.tsx
        SourceDetailsDrawer.tsx
        SourceMetadata.tsx

      common/
        Button.tsx
        IconButton.tsx
        Alert.tsx
        Spinner.tsx
        Skeleton.tsx
        ThemeToggle.tsx
        ErrorBoundary.tsx

    features/
      chat/
        chatTypes.ts
        chatState.ts
        useChat.ts
        useChatRequest.ts

      theme/
        ThemeProvider.tsx
        useTheme.ts

    pages/
      ChatPage.tsx
      AboutPage.tsx
      SourcesPage.tsx
      NotFoundPage.tsx

    config/
      env.ts

    lib/
      cn.ts
      format.ts
      storage.ts
      accessibility.ts

    styles/
      index.css

    test/
      setup.ts
      handlers.ts
      server.ts
      fixtures.ts

    main.tsx

  public/
    favicon.svg

  .env.example
  index.html
  package.json
  package-lock.json
  tailwind.config
  tsconfig.json
  vite.config.ts
  vitest.config.ts
  README.md

Adapt this structure if a simpler equivalent is more appropriate.

Do not create empty files or unnecessary abstractions.

DESIGN DIRECTION

Create a calm, trustworthy, educational visual identity.

The visual style should be:

- Clean
- Modern
- Respectful
- Calm
- Minimal
- Warm
- Readable
- Mobile-first
- Professional

Suggested design direction:

- Warm neutral background
- Deep saffron or amber accent used sparingly
- Rich indigo or dark blue for primary actions
- Neutral text colors with strong contrast
- Soft card borders
- Subtle shadows
- Rounded corners
- Generous spacing
- Clear typography hierarchy

Do not overuse religious symbols.

Do not imitate sacred manuscript artwork in a way that reduces readability.

Do not present the AI as a divine authority.

Do not display language implying that answers are unquestionably correct.

APPLICATION LAYOUT

Desktop layout may contain:

1. Application header.
2. Main chat area.
3. Optional source-details drawer.
4. Footer or informational notice.

Mobile layout should contain:

1. Compact header.
2. Full-width message list.
3. Sticky composer near the bottom.
4. Source drawer that works on narrow screens.
5. Touch-friendly controls.
6. No horizontal overflow.

The experience should work from approximately 320 pixels wide upward.

HEADER

Include:

- VedaGPT name
- Short subtitle such as "Source-grounded scripture learning"
- Theme toggle
- About link
- Backend connection indicator if appropriate
- Demo-mode indicator when using demonstration data

Do not show sensitive backend details.

DEMO-DATA WARNING

The project does not yet contain a fully approved production scripture corpus.

Display a clear, non-alarming notice:

"VedaGPT is currently running with demonstration or limited test data. Responses and citations are for technical evaluation and should not be treated as authoritative scripture references."

Requirements:

1. Display prominently in development or demo mode.
2. Do not allow the warning to be permanently hidden if the backend is using demo data.
3. Keep the warning accessible.
4. Do not describe demo sources as verified.
5. Make the warning configurable using a frontend environment value.
6. Default to showing the warning when configuration is uncertain.

Suggested environment variable:

VITE_DEMO_MODE=true

CHAT EXPERIENCE

Implement a ChatGPT-style chat interface.

The empty state should include:

- Welcome heading
- Short explanation of VedaGPT
- Demo-data notice
- Suggested questions
- Explanation that answers include retrieved sources
- Clear question input

Suggested questions must be clearly identified as examples.

Do not include questions that imply unsupported corpus coverage.

Example suggestions may include:

- What does the indexed text say about performing duty?
- What does the indexed text say about controlling the mind?
- Explain a verse by chapter and verse number.
- Which indexed passages discuss attachment to outcomes?

Do not hard-code expected scripture answers.

CHAT COMPOSER

Requirements:

1. Multiline input.
2. Send button.
3. Enter submits.
4. Shift+Enter adds a new line.
5. Disable send for blank input.
6. Trim accidental whitespace.
7. Client-side maximum length consistent with backend limits.
8. Character counter near the maximum.
9. Prevent duplicate submission while a request is active.
10. Support cancellation.
11. Preserve the draft after a failed request.
12. Clear the draft only when submission is accepted.
13. Accessible label.
14. Keyboard-focus indicators.
15. Mobile-friendly touch target.
16. Do not include voice input in Phase 3.

CHAT MESSAGE MODEL

Keep client-side messages separate from backend responses.

Suggested logical model:

- Message ID
- Role
- Content
- Creation time
- Request status
- Grounded state
- Sources
- Safe error state
- Original question
- Retry metadata

Do not store API keys or internal errors in message state.

USER MESSAGE

Display:

- User question
- Clear role distinction
- Creation time only if useful
- Accessible semantic structure

Do not allow HTML execution.

ASSISTANT MESSAGE

Display:

- Answer content
- Grounding status
- Sources
- Safe error state
- Retry button when appropriate
- Copy-answer button if implemented
- Clear distinction between quoted source material and AI explanation

Do not visually present generated explanation as direct scripture quotation.

If Markdown rendering is used:

1. Sanitize output.
2. Disable raw HTML.
3. Do not execute scripts.
4. Prevent unsafe links.
5. Style headings, lists, emphasis, and code safely.
6. Do not assume backend text is trusted HTML.

GROUNDED RESPONSE STATE

When grounded is true:

- Display a visible "Grounded in indexed sources" badge.
- Display at least one source card.
- Allow opening source details.
- Do not create source metadata on the frontend.
- Use only source objects returned by the backend.
- Do not infer a missing translator, edition, chapter, or verse.

UNGROUNDED RESPONSE STATE

When grounded is false:

- Display a neutral informational state.
- Use the backend message where safe.
- Explain that sufficient support was not found in the indexed sources.
- Do not show fabricated citations.
- Do not display a success-style grounding badge.
- Offer a suggestion to rephrase the question.
- Do not automatically send a broader question.

SOURCE CARDS

Each citation card should display fields only when returned by the backend.

Possible fields:

- Scripture
- Chapter
- Verse
- Verse range
- Translation
- Translator
- Edition
- Source reference
- Retrieval score, only if appropriate for development mode

Requirements:

1. Never invent missing metadata.
2. Do not convert retrieval score to confidence percentage.
3. Do not describe the score as truth probability.
4. Avoid displaying internal document IDs prominently to normal users.
5. Permit document IDs in a development-details section if useful.
6. Make each source card keyboard accessible.
7. Allow opening the source-details drawer.

SOURCE DETAILS DRAWER

Display all safe source metadata returned by the backend.

Possible sections:

- Reference
- Sanskrit text
- Transliteration
- Translation
- Commentary
- Translator
- Commentator
- Edition
- Source reference
- License
- Review status
- Technical metadata in development mode only

Requirements:

1. Work on desktop and mobile.
2. Trap focus while open.
3. Close with Escape.
4. Return focus to the triggering element.
5. Provide an accessible name.
6. Prevent background interaction while open.
7. Do not display fields that were not returned.
8. Do not expose secrets or internal paths.
9. Clearly label translation and commentary separately.
10. Clearly label demo content.

API CLIENT

Create a typed API client.

Environment configuration:

VITE_API_BASE_URL=http://localhost:8000

Requirements:

1. Validate the environment value.
2. Avoid hard-coded production URLs.
3. Normalize trailing slashes.
4. Add a reasonable timeout.
5. Support AbortController request cancellation.
6. Parse JSON safely.
7. Validate responses at runtime where practical.
8. Convert backend errors into safe frontend error types.
9. Do not expose raw response bodies to users.
10. Do not log sensitive data.
11. Do not retry validation errors.
12. Use limited retries only for appropriate transient network failures.
13. Prevent retry storms.
14. Keep API logic separate from presentation components.

If TanStack Query is used:

- Configure conservative retry behavior.
- Do not retry HTTP 400 or 422 automatically.
- Do not retry indefinitely.
- Preserve mutation cancellation behavior.
- Keep query and mutation keys organized.

HEALTH CHECK

Use:

GET /health

Display a small backend status indicator:

- Connected
- Checking
- Unavailable

Requirements:

1. Do not block the whole UI permanently if health check fails.
2. Show a safe message.
3. Allow manual retry.
4. Avoid polling too frequently.
5. Do not show sensitive service metadata.

ERROR HANDLING

Create safe user-facing errors for:

- Network failure
- Timeout
- Backend unavailable
- Validation error
- Request cancelled
- Provider temporarily unavailable
- Unknown server error
- Malformed response

Examples:

"VedaGPT could not reach the backend. Please check that the local API is running."

"The request took too long. Please try again."

"The indexed sources could not support this question."

Do not display:

- Stack traces
- Python exception messages
- API keys
- Environment variables
- Gemini provider details
- Qdrant connection strings
- Absolute local paths

ERROR BOUNDARY

Add a React error boundary.

Requirements:

- Provide a calm fallback state.
- Allow reloading the page.
- Do not display internal stack traces in production mode.
- Log only safe development information.
- Keep the header or recovery action available where possible.

CLIENT-SIDE CONVERSATION STATE

Phase 3 may maintain conversation state in memory.

Optional local persistence may use localStorage only if implemented safely.

If using localStorage:

1. Store only user questions, generated answers, safe source metadata, and UI preferences.
2. Do not store secrets.
3. Do not store internal errors.
4. Add a clear "Clear conversation" action.
5. Version the storage format.
6. Handle malformed stored data safely.
7. Set a reasonable maximum history size.
8. Do not imply server-side synchronization.
9. Document that history remains on the current browser.
10. Provide an option to disable persistence.

Do not implement server-side chat history in Phase 3.

THEME

Implement light and dark themes.

Requirements:

1. Respect system preference initially.
2. Allow manual switching.
3. Persist theme preference locally.
4. Maintain accessible contrast.
5. Avoid flashes of incorrect theme during initialization.
6. Do not rely only on color to convey grounding or errors.

ROUTING

Recommended routes:

/                Chat page
/about           About VedaGPT
/sources         Indexed-source information, if useful
/*               Not-found page

Do not add login or account routes.

ABOUT PAGE

Explain:

- What VedaGPT is
- How retrieval grounding works at a high level
- That answers are AI-generated
- That citations should be verified
- Which corpus is currently indexed
- Whether demo mode is enabled
- That different traditions may interpret scripture differently
- That VedaGPT is educational and not a divine authority
- That it does not provide professional medical, legal, or financial advice

Do not expose system prompts or internal implementation secrets.

ACCESSIBILITY

Target WCAG-friendly behavior.

Requirements:

1. Semantic HTML.
2. Keyboard navigation.
3. Visible focus indicators.
4. Accessible form labels.
5. Appropriate ARIA only where needed.
6. Dynamic response announcements through an aria-live region.
7. Accessible loading indicators.
8. Source drawer focus management.
9. Sufficient contrast.
10. Touch targets of reasonable size.
11. Do not convey state by color alone.
12. Reduced-motion preference support.
13. Screen-reader-friendly grounded state.
14. Screen-reader-friendly error state.
15. Page titles for routes.

Avoid unnecessary ARIA when native semantics are sufficient.

RESPONSIVE DESIGN

Test these target widths:

- 320 pixels
- 375 pixels
- 768 pixels
- 1024 pixels
- 1440 pixels

Ensure:

- No horizontal scrolling.
- Composer remains usable.
- Source drawer fits the screen.
- Cards do not overflow.
- Long source references wrap safely.
- Long Sanskrit or transliteration strings do not break layout.
- Buttons remain reachable.
- The chat remains readable at increased browser zoom.

FRONTEND SECURITY

Implement:

- No raw HTML execution
- Safe Markdown rendering
- Safe external links
- rel="noopener noreferrer" where appropriate
- No API keys in frontend variables
- No Gemini key in VITE variables
- No Qdrant credentials in the frontend
- No backend secrets in source code
- No use of dangerouslySetInnerHTML unless fully justified and sanitized
- Runtime response validation where practical
- Safe localStorage parsing
- Safe URL construction
- Client-side length validation
- Request cancellation
- Dependency-audit review

Important:

Any VITE environment variable is visible to the browser.

Never place these in frontend environment files:

- GEMINI_API_KEY
- QDRANT_API_KEY
- Database credentials
- Private tokens
- Service-account credentials

CORS

Inspect the FastAPI CORS configuration.

For local development, allow only configured frontend origins such as:

http://localhost:5173

Do not use unrestricted production CORS.

Use an environment value such as:

CORS_ORIGINS=http://localhost:5173

If backend changes are required:

1. Keep them minimal.
2. Preserve API behavior.
3. Add backend tests.
4. Keep production defaults restrictive.
5. Do not use allow_origins=["*"] with credentials.

ENVIRONMENT FILES

Create:

frontend/.env.example

Suggested values:

VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=VedaGPT
VITE_DEMO_MODE=true
VITE_ENABLE_LOCAL_HISTORY=true

Do not create or commit frontend/.env containing secrets.

Update .gitignore appropriately.

TESTING REQUIREMENTS

Create comprehensive frontend tests.

API CLIENT TESTS

Test:

- Correct endpoint construction
- Request body serialization
- Successful grounded response
- Successful ungrounded response
- HTTP 400 handling
- HTTP 422 handling
- HTTP 500 handling
- Network failure
- Timeout
- Cancellation
- Malformed response
- Empty response
- No secret leakage

CHAT COMPOSER TESTS

Test:

- Blank input disabled
- Whitespace-only input disabled
- Enter submits
- Shift+Enter creates newline
- Maximum length enforced
- Duplicate submission prevented
- Draft retained on failure
- Input cleared after accepted submission
- Cancel action works
- Accessible label exists

CHAT PAGE TESTS

Test:

- Empty state
- Suggested questions
- Loading state
- Grounded answer
- Ungrounded answer
- Citation cards
- Source drawer
- Retry behavior
- Backend unavailable
- Demo warning
- Clear conversation
- Responsive layout classes where practical

SOURCE TESTS

Test:

- Source metadata displayed only when present
- Missing metadata not invented
- Translation and commentary separate
- Drawer opens
- Drawer closes with Escape
- Focus returns to trigger
- Duplicate sources handled appropriately
- Retrieval score is not shown as confidence
- Demo source labelled

THEME TESTS

Test:

- System theme respected
- Manual theme switch
- Theme persisted
- Invalid stored theme handled safely

ACCESSIBILITY TESTS

Test:

- Input label
- Buttons have accessible names
- Dynamic answers announced
- Error state announced
- Drawer has accessible name
- Loading state announced
- Keyboard operation
- Focus management
- No major automated accessibility violations if an accessibility testing library is used

ROUTING TESTS

Test:

- Chat route
- About route
- Sources route if implemented
- Not-found route

REGRESSION TESTS

Verify:

- Backend endpoint remains POST /api/v1/chat
- Backend health endpoint remains GET /health
- Existing backend tests pass
- No Gemini calls required by frontend tests
- No Qdrant instance required by frontend unit tests
- Demo-data safeguards remain unchanged
- No Phase 4 feature added

MOCKING

Use MSW or an equivalent request mock.

Create fixtures for:

1. Grounded answer with one source.
2. Grounded answer with several sources.
3. Ungrounded answer.
4. Backend validation error.
5. Provider unavailable.
6. Network failure.
7. Malformed response.
8. Slow response.
9. Demo source.
10. Source with optional fields missing.

Do not use live Gemini or live Qdrant for frontend unit tests.

INTEGRATION VERIFICATION

After unit tests pass, run a local integration check.

Backend:

- FastAPI running on localhost:8000
- GET /health working
- POST /api/v1/chat reachable

Frontend:

- Vite running on localhost:5173
- API base URL configured
- CORS working
- Error handling working

Do not require a successful live Gemini answer if credits are unavailable.

If Gemini is unavailable, verify integration using:

- A backend development stub if one already exists
- Mock Service Worker
- A safe test endpoint only if it does not alter the public API
- A stored mocked response

Do not add a development backdoor that can be enabled accidentally in production.

BUILD REQUIREMENTS

Run:

npm install
npm run lint
npm run typecheck
npm run test
npm run build

Add scripts if missing:

- dev
- build
- preview
- test
- test:watch
- lint
- typecheck

The production build must complete without errors.

Do not ignore TypeScript errors during the build.

Do not disable strict TypeScript merely to make the build pass.

QUALITY REQUIREMENTS

Use:

- Strict TypeScript
- Small focused components
- Clear prop types
- Reusable presentation components
- Separation of API and UI logic
- No massive single-file chat component
- No unnecessary global state library
- No any types unless justified
- No console logging of sensitive data
- No dead code
- No placeholder production text
- No unexplained TODO comments
- No duplicated API types across unrelated files
- No brittle CSS selectors
- No hard-coded backend URLs in components

PERFORMANCE

Implement reasonable performance practices:

- Avoid unnecessary re-renders.
- Use stable list keys.
- Avoid loading heavy dependencies unnecessarily.
- Lazy-load secondary routes if appropriate.
- Keep the initial bundle reasonable.
- Avoid expensive Markdown parsing when no content is present.
- Limit locally persisted chat size.
- Cancel stale requests.
- Do not make repeated health checks on every render.

Do not prematurely optimize at the expense of correctness.

DOCUMENTATION

Create or update:

frontend/README.md

Document:

1. Phase 3 purpose.
2. Technology stack.
3. Installation.
4. Environment configuration.
5. Starting the backend.
6. Starting the frontend.
7. Running tests.
8. Running type checks.
9. Running lint.
10. Creating a production build.
11. API integration.
12. CORS configuration.
13. Demo mode.
14. Local conversation history.
15. Accessibility features.
16. Known limitations.
17. Troubleshooting.
18. Phase 4 boundary.

Update the root README with:

- Frontend folder
- Development commands
- Backend plus frontend startup order
- Demo-data warning
- Phase 3 status

Do not delete existing Phase 1 or Phase 2 documentation.

README commands must work on Windows PowerShell.

GITIGNORE

Ensure Git ignores:

frontend/.env
frontend/.env.local
frontend/dist
frontend/coverage
frontend/node_modules
*.log

Preserve:

frontend/.env.example
package-lock.json

Do not commit node_modules.

DO NOT MODIFY UNRELATED BACKEND CODE

Backend modifications are allowed only for:

- Restricted configurable CORS
- Clearly necessary backward-compatible API support
- Additional regression tests
- Development integration documentation

Do not rewrite the RAG pipeline.

Do not rewrite ingestion.

Do not change Qdrant collection behavior.

Do not change corpus schemas.

Do not change citation logic.

Do not change evaluation metrics.

Do not add a second backend.

Do not call Gemini directly from the browser.

IMPLEMENTATION WORKFLOW

STEP 1: VERIFY WORKSPACE

Run:

Get-Location
git status
git branch --show-current
git log -5 --oneline
python --version
node --version
npm --version

Confirm the correct Git repository.

STEP 2: CHECKPOINT

Confirm Phase 2 is pushed.

If a phase-2-complete tag does not exist, report that fact.

Do not create or push a tag without explicit approval unless this prompt is interpreted as sufficient approval for a local tag only.

Create the Phase 3 branch if it does not already exist:

phase-3-web-frontend

STEP 3: BASELINE BACKEND TESTS

Run existing backend tests before modifying backend configuration.

Report:

- Collected
- Passed
- Failed
- Skipped
- Warnings
- Duration

Do not proceed with unrelated backend failures.

STEP 4: INSPECT BACKEND API

Read the actual FastAPI request and response schemas.

Document the exact API contract that the frontend will consume.

STEP 5: IMPACT ANALYSIS

Report:

- Files to create
- Files to modify
- Files intentionally unchanged
- Backend API contract
- CORS impact
- Security considerations
- Accessibility plan
- Testing plan
- Missing inputs
- Known demo-data limitation

Proceed directly after the impact analysis.

Do not stop for confirmation unless there is a destructive or genuinely blocking issue.

STEP 6: FRONTEND INITIALIZATION

Initialize React, TypeScript, and Vite in the frontend directory.

Do not overwrite backend files.

Install only necessary dependencies.

Commit the package lockfile.

STEP 7: IMPLEMENTATION

Implement the full Phase 3 frontend.

Create actual application files.

Do not provide only a plan or pseudocode.

STEP 8: TESTING

Run:

- Frontend unit tests
- Frontend component tests
- Frontend accessibility tests
- TypeScript validation
- Lint
- Production build
- Existing backend tests

Fix all Phase 3 regressions.

STEP 9: LOCAL INTEGRATION

Where possible:

- Start FastAPI
- Start Vite
- Verify the health endpoint
- Verify CORS
- Verify chat request behavior
- Verify grounded response rendering using safe mocked data if Gemini is unavailable
- Verify network-error behavior
- Verify mobile-friendly layout

Do not claim live Gemini integration passed if it was not performed.

STEP 10: FINAL REPORT

Return:

1. Workspace used.
2. Git branch used.
3. Baseline backend test results.
4. Exact backend API contract used.
5. Implementation summary.
6. Files created.
7. Files modified.
8. Files intentionally unchanged.
9. Dependencies added.
10. Commands executed.
11. Frontend test results.
12. Accessibility test results.
13. Type-check result.
14. Lint result.
15. Build result.
16. Backend regression-test result.
17. Local integration result.
18. Skipped checks and reasons.
19. Security review.
20. Demo-data limitation.
21. Known limitations.
22. Exact commands for the project owner.
23. Phase 3 acceptance checklist.
24. Confirmation that Phase 4 was not started.

Do not claim success for checks that were skipped.

PHASE 3 ACCEPTANCE CRITERIA

Phase 3 is complete only when:

- Correct vedagpt-git workspace used
- Phase 3 branch used
- Existing backend tests pass
- React and TypeScript frontend created
- Vite development server works
- Production build succeeds
- Strict TypeScript passes
- Lint passes
- Frontend tests pass
- API client is typed
- API responses are safely validated
- GET /health integration exists
- POST /api/v1/chat integration exists
- Grounded responses render correctly
- Ungrounded responses render correctly
- Citation cards use only backend metadata
- Source drawer works
- Translation and commentary remain separate
- Missing metadata is not invented
- Demo-data warning is visible
- Loading state works
- Retry state works
- Network error state works
- Timeout state works
- Request cancellation works
- Duplicate submission is prevented
- Chat composer is keyboard accessible
- Theme switch works
- Mobile layout works
- Desktop layout works
- No horizontal overflow at target widths
- No frontend secrets exist
- Gemini is not called directly from the browser
- Qdrant is not called directly from the browser
- CORS configuration is restrictive and configurable
- node_modules is not tracked
- frontend/.env is not tracked
- frontend/.env.example is committed
- Root and frontend documentation are updated
- Existing backend API contract remains compatible
- No Phase 4 functionality was implemented

KNOWN PROJECT LIMITATION

The production scripture corpus is not yet available.

The frontend must operate in demo or limited-data mode.

It must clearly display the demo-data warning.

Do not describe VedaGPT as production-ready.

Do not represent demo scripture records as authoritative.

START NOW

Begin by verifying the workspace, Git state, Phase 3 branch, Node.js version, npm version, and existing backend test baseline.

Then inspect the real FastAPI schemas and provide the Phase 3 impact analysis.

Proceed directly with implementation after the impact analysis.

Build the Phase 3 React frontend completely.

Run all frontend and backend regression tests.

Fix all Phase 3 failures.

Do not call Gemini directly from the frontend.

Do not invent scripture data.

Do not implement Phase 4.