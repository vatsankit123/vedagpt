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
