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


Migration prompt :

The current VedaGPT Phase 1 Anthropic implementation is complete and all 46 tests pass.

Perform a strictly scoped migration from Anthropic Claude to Google Gemini.

This is not Phase 2. Do not add any new product features.

Requirements:

1. Replace the Anthropic generation provider with a Google Gemini generation provider.
2. Use the official Google Gen AI Python SDK.
3. Preserve the existing generic LLM provider abstraction.
4. The chat service must not directly import Gemini SDK classes.
5. Replace ANTHROPIC_API_KEY with GEMINI_API_KEY.
6. Replace ANTHROPIC_MODEL with GEMINI_MODEL.
7. Read the model identifier from environment configuration.
8. Do not hard-code an assumed latest Gemini model name.
9. Remove the Anthropic dependency if it is no longer used.
10. Add the Google Gen AI SDK dependency.
11. Keep the embedding provider separate from Gemini.
12. Do not change the FastAPI endpoint paths, request schemas, response schemas, or API contracts.
13. Do not change the Qdrant collection schema.
14. Do not change corpus ingestion, retrieval, evidence sufficiency, or citation validation behavior.
15. Citations must continue to come only from retrieved Qdrant metadata.
16. Do not call Gemini when retrieval evidence is insufficient.
17. Handle invalid credentials, quota errors, timeouts, blocked responses, empty responses, and provider failures safely.
18. Do not expose Gemini errors, API keys, stack traces, or internal configuration to API users.
19. Mock Gemini API calls in unit tests.
20. Preserve all 46 existing tests and add Gemini-specific provider tests.
21. Update .env.example, requirements.txt, README.md, and relevant tests.
22. Do not modify or remove the demo-data safety controls.
23. Do not add frontend, React Native, authentication, agents, LangGraph, knowledge graphs, payments, voice, or deployment features.

Workflow:

1. Inspect the current repository.
2. Provide a concise file-level impact analysis.
3. Proceed directly with the migration without waiting for confirmation.
4. Make the smallest possible provider-layer changes.
5. Run the complete test suite.
6. Fix every test failure caused by the migration.
7. Report the actual number of passed, failed, and skipped tests.
8. List every file created, modified, or deleted.
9. Confirm that the API contract and RAG behavior remain unchanged.
10. Confirm that no Phase 2 features were implemented.

Do not stop after the impact analysis.

The migration is complete only when all original tests and the new Gemini provider tests pass.
>>>>>>> 27c8903 (Add Gemini migration instructions)








New prompt :


You are working on VedaGPT, a source-grounded educational RAG application for understanding selected Indian scriptures.

CURRENT PROJECT STATUS

The following work has already been completed:

1. Phase 1 FastAPI backend.
2. Qdrant vector database integration.
3. Configurable embedding provider.
4. Evidence-sufficiency checking.
5. Structured citation generation.
6. Citation validation.
7. Corpus validation foundation.
8. Demo Bhagavad Gita fixtures.
9. Docker Compose configuration.
10. Automated tests.
11. Anthropic was replaced with Google Gemini.
12. Gemini remains behind a provider abstraction.
13. The existing test suite reportedly contains 68 passing tests.
14. Changes are stored in the Git-connected repository.

The current implementation is only a technical foundation.

The project does not yet contain a complete, verified, legally usable Bhagavad Gita corpus.

Your task is to implement PHASE 2 ONLY.

PHASE 2 TITLE

Verified Corpus Preparation, Production Ingestion, Retrieval Quality, and Offline Evaluation

IMPORTANT WORKSPACE RULE

Before making any change, verify the current workspace.

Run:

Get-Location
git status
git log -3 --oneline
python --version

The expected project directory is the Git-connected repository named:

vedagpt-git

Do not work in the older downloaded ZIP folder named vedagpt-main.

If the current workspace is not the Git-connected vedagpt-git repository, stop and report the exact current path.

Do not modify files in another workspace.

PRIMARY PHASE 2 GOAL

Build a production-quality corpus, ingestion, retrieval, provenance, and evaluation pipeline for one Bhagavad Gita edition.

Phase 2 must allow the project to:

1. Accept a complete Bhagavad Gita dataset supplied by the project owner.
2. Validate every record and its source metadata.
3. Reject unverified or unlicensed content during production ingestion.
4. Normalize corpus records deterministically without changing their meaning.
5. generate stable content hashes.
6. Build deterministic embedding documents.
7. Ingest records into Qdrant idempotently.
8. Retrieve exact verse references reliably.
9. Retrieve relevant verses for conceptual questions.
10. Apply safe metadata filtering.
11. Evaluate retrieval quality without calling Gemini.
12. Generate JSON and Markdown evaluation reports.
13. Preserve all existing Phase 1 behavior and tests.
14. Keep citations traceable to source metadata.
15. Remain ready for a later frontend phase without implementing it now.

PHASE 2 BOUNDARY

Implement:

- Corpus schema
- Source manifest
- Corpus profile
- Corpus validation
- Provenance validation
- Licensing checks
- Deterministic normalization
- Content hashes
- Document construction strategies
- Qdrant ingestion improvements
- Idempotent ingestion
- Dry-run ingestion
- Versioned collections
- Metadata filters
- Exact verse-reference parsing
- Dense retrieval evaluation
- Optional hybrid retrieval only if justified
- Offline retrieval evaluation
- Evaluation metrics
- Evaluation reports
- Phase 2 tests
- Documentation

Do not implement:

- React frontend
- React Native
- Android application
- iOS application
- Authentication
- Authorization
- User accounts
- Chat history
- Bookmarks
- Payments
- Subscriptions
- Voice features
- Multi-agent architecture
- LangGraph agents
- Knowledge graphs
- Fine-tuning
- All four Vedas
- Upanishads
- Puranas
- Ramayana
- Mahabharata
- Cloud deployment
- App Store publishing
- Google Play publishing
- Phase 3 features

NON-NEGOTIABLE RULES

1. Implement Phase 2 only.
2. Preserve all existing Phase 1 API contracts.
3. Preserve every currently passing test.
4. Add meaningful Phase 2 tests.
5. Do not require live Gemini access.
6. Do not make live Gemini API calls during unit tests.
7. Do not make Gemini a dependency for corpus validation.
8. Do not make Gemini a dependency for ingestion.
9. Do not make Gemini a dependency for retrieval evaluation.
10. Do not invent scripture content.
11. Do not download scripture text automatically.
12. Do not scrape scripture websites.
13. Do not generate translations using an LLM.
14. Do not generate Sanskrit verses using an LLM.
15. Do not generate commentaries using an LLM.
16. Do not invent translators, editions, publishers, licenses, or source references.
17. Do not treat demo data as verified content.
18. Do not change DEMO_DATA_NOT_FOR_PRODUCTION into VERIFIED.
19. Do not silently skip invalid corpus records.
20. Do not weaken current production-ingestion safeguards.
21. Do not hard-code one universal verse count without a source profile.
22. Do not treat vector similarity as factual confidence.
23. Do not let Gemini create citation metadata.
24. Keep citations derived from retrieved Qdrant metadata.
25. Do not log secrets.
26. Do not commit .env files.
27. Do not commit API keys.
28. Do not commit a virtual environment.
29. Do not delete an existing Qdrant collection automatically.
30. Do not perform destructive Git operations.
31. Do not use git reset --hard.
32. Do not use git push --force.
33. Do not claim a test passed unless it was actually executed.
34. Do not claim production readiness only because unit tests pass.
35. Do not proceed to Phase 3.

EXISTING BEHAVIOR THAT MUST REMAIN COMPATIBLE

Preserve:

GET /health

POST /api/v1/chat

Preserve the existing:

- Chat request schema
- Chat response schema
- Source response schema
- Unsupported-question response
- Evidence-sufficiency behavior
- Citation-validator behavior
- Embedding-provider abstraction
- Gemini-provider abstraction
- Qdrant abstraction
- Demo-data rejection behavior
- Environment-based configuration
- Safe API errors

Do not break existing clients.

PHASE 2 ARCHITECTURE

Implement or extend the project to support this flow:

Raw user-supplied corpus
    ->
Source manifest validation
    ->
Corpus profile validation
    ->
Typed record validation
    ->
Licensing and provenance validation
    ->
Corpus completeness checks
    ->
Deterministic normalization
    ->
Stable content hashing
    ->
Deterministic document construction
    ->
Embedding generation
    ->
Versioned Qdrant collection
    ->
Idempotent ingestion
    ->
Dense retrieval
    ->
Exact-reference retrieval
    ->
Optional lexical retrieval
    ->
Evidence sufficiency
    ->
Programmatic citations
    ->
Offline retrieval evaluation
    ->
JSON and Markdown reports

REPOSITORY INSPECTION

Before implementation, inspect:

- Existing config.py
- Existing corpus validation code
- Existing ingestion script
- Existing vector-store abstraction
- Existing retriever
- Existing embedding provider
- Existing citation validator
- Existing Gemini generator
- Existing service layer
- Existing Pydantic schemas
- Existing tests
- Existing demo corpus
- Existing evaluation fixtures
- Existing README
- Existing .env.example
- Existing Docker Compose file
- Existing requirements.txt

Adapt to the current architecture.

Do not blindly replace working Phase 1 code.

RECOMMENDED STRUCTURE

Use the existing structure where possible.

Add only the files and layers that are necessary.

A reasonable Phase 2 structure may include:

backend/
  app/
    corpus/
      __init__.py
      models.py
      loader.py
      validator.py
      normalizer.py
      provenance.py
      document_builder.py
      hashing.py
      reports.py

    evaluation/
      __init__.py
      models.py
      metrics.py
      runner.py
      reports.py

    rag/
      retriever.py
      reference_parser.py
      hybrid_retriever.py
      reranker.py

    services/
      retrieval_service.py

  scripts/
    validate_corpus.py
    normalize_corpus.py
    ingest_qdrant.py
    inspect_collection.py
    evaluate_retrieval.py

  data/
    README.md
    source_manifest.template.json
    corpus_profile.template.json
    bhagavad_gita.verified.template.json
    evaluation_questions.template.json
    evaluation_questions.sample.json

  reports/
    .gitkeep

  tests/
    fixtures/
    test_source_manifest.py
    test_corpus_schema.py
    test_corpus_validation.py
    test_corpus_completeness.py
    test_normalization.py
    test_content_hashing.py
    test_document_builder.py
    test_idempotent_ingestion.py
    test_reference_parser.py
    test_metadata_filters.py
    test_retrieval_metrics.py
    test_evaluation_runner.py
    test_phase2_regression.py

Do not create empty architectural layers.

SOURCE MANIFEST REQUIREMENTS

Create a source manifest model and template.

Suggested structure:

{
  "source_id": "replace-with-verified-source-id",
  "title": "Bhagavad Gita",
  "translator": "",
  "editor": "",
  "commentator": "",
  "edition": "",
  "publisher": "",
  "publication_year": null,
  "publication_country": "",
  "language": "English",
  "original_language": "Sanskrit",
  "source_reference": "",
  "source_type": "",
  "accessed_date": "",
  "copyright_status": "UNVERIFIED",
  "license_name": "",
  "license_reference": "",
  "redistribution_permitted": false,
  "commercial_use_permitted": false,
  "modification_permitted": false,
  "attribution_required": false,
  "required_attribution": "",
  "verification_status": "PENDING",
  "verified_by": "",
  "verified_date": "",
  "notes": ""
}

Production validation must require meaningful values for:

- source_id
- title
- translator
- edition
- source_reference
- copyright_status
- license information
- redistribution decision
- verification status
- verified_by
- verified_date

An empty field must not count as valid merely because the key exists.

Allowed source states should be explicit, for example:

- PENDING
- VERIFIED
- REJECTED

Production ingestion must accept only an approved source state.

Do not decide the legal status automatically.

The project owner must supply and verify the legal information.

CORPUS PROFILE REQUIREMENTS

Create a corpus-profile model and template.

Suggested structure:

{
  "profile_id": "bhagavad-gita-edition-profile",
  "scripture": "Bhagavad Gita",
  "source_id": "replace-with-verified-source-id",
  "expected_chapters": 18,
  "expected_verse_counts": {},
  "allow_numbering_variants": true,
  "numbering_notes": "",
  "profile_version": 1,
  "review_status": "PENDING",
  "reviewed_by": "",
  "reviewed_date": ""
}

Do not populate expected verse counts without verified user-supplied information.

The validator must function when only expected_chapters is available.

Verse-count differences among editions must be reported and reviewed rather than silently classified as corruption.

CORPUS RECORD REQUIREMENTS

Create a typed record model.

Suggested structure:

{
  "id": "gita-2-47",
  "source_id": "replace-with-verified-source-id",
  "scripture": "Bhagavad Gita",
  "chapter": 2,
  "verse": 47,
  "verse_end": null,
  "sanskrit": "",
  "transliteration": "",
  "translation": "",
  "commentary": "",
  "translator": "",
  "commentator": "",
  "edition": "",
  "language": "English",
  "source_reference": "",
  "copyright_status": "UNVERIFIED",
  "license_name": "",
  "license_reference": "",
  "content_hash": "",
  "record_version": 1,
  "review_status": "PENDING",
  "reviewed_by": "",
  "reviewed_date": "",
  "notes": ""
}

Production records must have:

- Unique id
- Source ID
- Scripture name
- Positive chapter
- Positive verse
- Translation
- Translator
- Edition
- Language
- Source reference
- Copyright status
- License information
- Record version
- Review status
- Reviewer
- Review date

Optional content:

- Sanskrit
- Transliteration
- Commentary
- Commentator
- Notes
- Verse range

Keep translation and commentary separate.

Do not merge commentary into the translation field.

Do not tag transliteration as Sanskrit.

CORPUS VALIDATION

Implement comprehensive record-level validation.

Validate:

1. Unique IDs.
2. Unique source, chapter, and verse combinations.
3. Positive chapter numbers.
4. Positive verse numbers.
5. Valid optional verse ranges.
6. Non-empty scripture name.
7. Non-empty production translation.
8. Non-empty production translator.
9. Non-empty production edition.
10. Non-empty source reference.
11. Valid source-manifest reference.
12. Valid copyright status.
13. Valid review status.
14. Valid date formats.
15. Positive record version.
16. Safe maximum field lengths.
17. No invalid control characters.
18. No malformed Unicode replacement characters.
19. No obvious script payloads.
20. No duplicate normalized records.
21. No duplicate content hashes.
22. No demo records in production ingestion.
23. No unverified records in production ingestion.
24. No source-manifest mismatch.
25. No translation and commentary field misuse.

Implement corpus-level validation.

Report:

- Total record count
- Records by chapter
- Missing chapters
- Unexpected chapters
- Missing verse numbers
- Duplicate verses
- Suspicious numbering gaps
- Empty translations
- Missing translators
- Missing editions
- Missing references
- Unknown source IDs
- Inconsistent source IDs
- Mixed translators
- Mixed editions
- Mixed licensing states
- Mixed review states
- Duplicate text
- Duplicate content hashes
- Unicode anomalies
- Very short records
- Very long records
- Demo records
- Unverified records

Do not silently skip any invalid record.

VALIDATION REPORTS

Generate:

- Human-readable Markdown validation report
- Machine-readable JSON validation report

Suggested locations:

backend/reports/corpus_validation_<timestamp>.json

backend/reports/corpus_validation_<timestamp>.md

Reports must include:

- Run ID
- Timestamp
- Corpus path
- Manifest path
- Profile path
- Environment
- Schema version
- Valid count
- Invalid count
- Warning count
- Error categories
- Chapter distribution
- Missing records
- Duplicate records
- License issues
- Provenance issues
- Whether fixtures or production records were used

Do not commit large timestamped reports by default.

Commit report templates and small fixture examples only.

NORMALIZATION

Implement deterministic normalization.

Allowed operations:

- Unicode normalization
- Consistent line endings
- Trim accidental leading and trailing whitespace
- Collapse clearly accidental repeated whitespace
- Standardize optional empty values
- Normalize metadata key handling
- Parse integer fields safely
- Create stable content hashes

Do not:

- Rewrite translations
- Correct Sanskrit automatically
- Paraphrase commentary
- Translate content automatically
- Remove meaningful punctuation
- Merge verses automatically
- Split verses automatically
- Modify scripture wording silently

Every normalized record must preserve:

- Original record ID
- Source ID
- Record version
- Normalization version
- Content hash

CONTENT HASHING

Implement stable content hashing.

Use deterministic field ordering.

The hash must include meaningful fields such as:

- Scripture
- Chapter
- Verse
- Verse end
- Sanskrit
- Transliteration
- Translation
- Commentary
- Translator
- Commentator
- Edition
- Source ID

Do not include volatile fields such as:

- Ingestion timestamp
- Evaluation run ID
- Qdrant score
- Current processing time

Use hashes for:

- Duplicate detection
- Change detection
- Idempotent ingestion
- Incremental updates
- Audit reporting

DOCUMENT CONSTRUCTION

Create deterministic embedding-document strategies.

STRATEGY A: TRANSLATION ONLY

Example logical form:

Scripture: Bhagavad Gita
Chapter: 2
Verse: 47
Translation: [translation]

STRATEGY B: TRANSLITERATION AND TRANSLATION

Example logical form:

Scripture: Bhagavad Gita
Chapter: 2
Verse: 47
Transliteration: [transliteration]
Translation: [translation]

STRATEGY C: TRANSLATION AND COMMENTARY

Example logical form:

Scripture: Bhagavad Gita
Chapter: 2
Verse: 47
Translation: [translation]
Commentary: [commentary]

STRATEGY D: CONTEXT WINDOW

Support an optional context document containing:

- Previous verse
- Current verse
- Next verse

The current verse must remain the primary citation record.

Requirements:

1. Strategy must be configurable.
2. Construction must be deterministic.
3. Empty optional fields must be omitted cleanly.
4. Licensing text must not be embedded.
5. Operational metadata must not be embedded.
6. Tests must compare exact generated document strings.
7. Translation content must remain distinguishable from commentary.
8. Context boundaries must be handled safely for first and last verses.

Do not assume that combining all content produces better retrieval.

The evaluation pipeline must allow strategy comparison.

EMBEDDING REQUIREMENTS

Preserve the existing embedding-provider abstraction.

Requirements:

1. Embedding provider must be explicit.
2. Embedding model must be explicit.
3. Embedding dimension must be validated.
4. Model name must be stored in Qdrant payload metadata.
5. Provider must be stored in Qdrant payload metadata.
6. Changing the embedding model must require a new collection version or explicit recreation.
7. Do not mix embeddings from different models in one unnamed vector space.
8. Support configurable batching.
9. Support configurable batch size.
10. Validate returned vector length.
11. Reject empty vectors.
12. Reject NaN values.
13. Reject infinite values.
14. Add safe retry behavior for transient hosted-provider errors.
15. Add deterministic embedding mocks for unit tests.
16. Do not use Gemini generation as the embedding provider by default.
17. Do not silently switch embedding models.
18. Fail clearly when embedding configuration is missing.
19. Phase 2 unit tests must not download a large model.
20. Phase 2 tests must not consume paid API credits.

Keep future multilingual support possible for:

- English
- Sanskrit
- Hindi
- Transliteration

Do not claim multilingual quality without evaluation.

QDRANT COLLECTION VERSIONING

Use a configurable, versioned collection name.

Suggested default pattern:

vedagpt_bhagavad_gita_v1

Track:

- Collection name
- Source ID
- Corpus profile ID
- Corpus version
- Pipeline version
- Schema version
- Normalization version
- Embedding provider
- Embedding model
- Embedding dimension
- Distance metric
- Document strategy
- Ingestion run ID
- Environment
- Point count
- Creation timestamp

Do not delete an existing collection automatically.

Any destructive collection recreation must require an explicit command flag:

--recreate

Show a clear warning before destructive collection recreation.

QDRANT PAYLOAD

Store payload metadata similar to:

{
  "document_id": "gita-2-47",
  "source_id": "verified-source-id",
  "scripture": "Bhagavad Gita",
  "chapter": 2,
  "verse": 47,
  "verse_end": null,
  "sanskrit": "",
  "transliteration": "",
  "translation": "",
  "commentary": "",
  "translator": "",
  "commentator": "",
  "edition": "",
  "language": "English",
  "source_reference": "",
  "copyright_status": "VERIFIED",
  "license_name": "",
  "review_status": "VERIFIED",
  "record_version": 1,
  "content_hash": "",
  "schema_version": 1,
  "pipeline_version": "phase2-v1",
  "normalization_version": 1,
  "embedding_provider": "",
  "embedding_model": "",
  "embedding_dimension": 0,
  "document_strategy": "",
  "is_demo": false
}

Do not store secrets.

Do not store sensitive absolute local paths.

IDEMPOTENT INGESTION

Improve ingestion to support:

1. Stable point ID generation.
2. No duplicate points after repeated ingestion.
3. Add new records.
4. Update records whose content hash changed.
5. Skip unchanged records.
6. Reject invalid records.
7. Report failed records.
8. Configurable batch size.
9. Dry-run mode.
10. Retry behavior for transient errors.
11. Safe failure after repeated errors.
12. Collection-schema compatibility validation.
13. Embedding-dimension compatibility validation.
14. Embedding-model compatibility validation.
15. Ingestion run ID.
16. Ingestion timestamp.
17. JSON ingestion report.
18. Markdown ingestion report.
19. Non-zero exit status on production failure.
20. No Gemini requirement.

The ingestion report must contain:

- Added
- Updated
- Unchanged
- Rejected
- Failed
- Total
- Duration
- Collection
- Embedding model
- Document strategy
- Source ID
- Environment
- Whether dry-run was enabled

Dry-run mode must:

- Run all validation
- Build deterministic documents
- Validate embedding configuration using mocks where appropriate
- Calculate planned actions
- Write no Qdrant points
- Delete no Qdrant points

EXACT VERSE REFERENCE PARSING

Implement deterministic reference parsing without Gemini.

Support inputs such as:

- Bhagavad Gita 2.47
- Gita 2:47
- Gita chapter 2 verse 47
- Chapter 2 verse 47
- What does verse 2.47 say?
- Explain Bhagavad Gita 6.5

Requirements:

1. Parse chapter and verse safely.
2. Validate numeric ranges.
3. Apply metadata filters.
4. Retrieve the exact record.
5. Optionally retrieve neighboring context.
6. Return the requested verse as the primary citation.
7. Do not substitute a similar verse when the exact verse does not exist.
8. Return insufficient evidence for a missing explicit reference.
9. Reject malformed and ambiguous references safely.
10. Add tests for maliciously long input.
11. Add tests for conflicting references.
12. Do not use an LLM for reference parsing.

RETRIEVAL

Improve retrieval while preserving existing API behavior.

Support:

- Dense semantic retrieval
- Explicit verse retrieval
- Scripture filter
- Source ID filter
- Chapter filter
- Verse filter
- Language filter
- Edition filter
- Translation field retrieval
- Commentary field retrieval
- Configurable top-k
- Configurable candidate-k
- Configurable threshold
- Result deduplication
- Stable ordering
- Payload validation

Validate all filters before sending them to Qdrant.

Do not construct unsafe database filters from unchecked input.

DENSE RETRIEVAL BASELINE

Build and evaluate dense retrieval first.

Do not immediately add complex hybrid retrieval.

Dense evaluation must test:

- Exact references
- Exact phrases
- Concept questions
- Synonyms
- Paraphrases
- Chapter filters
- Unsupported questions
- Ambiguous questions
- Sanskrit terms where data exists
- Transliteration where data exists

HYBRID RETRIEVAL

Add lightweight lexical retrieval only if:

1. Dense retrieval performs poorly in measurable categories.
2. Exact Sanskrit terms are missed.
3. Transliteration queries are missed.
4. Rare names are missed.
5. Exact phrases are missed.
6. The improvement is demonstrated through evaluation.

If implemented, use a configurable design:

Dense candidates
    +
Lexical candidates
    ->
Reciprocal rank fusion
    ->
Deduplication
    ->
Optional reranking

Requirements:

- Dense-only mode must remain available.
- Hybrid mode must be optional.
- Fusion parameters must be configurable.
- Metrics must compare dense and hybrid modes.
- Do not claim hybrid is better without measurements.
- Avoid mandatory external search infrastructure for Phase 2.
- Keep the implementation local and testable where possible.

RERANKING

Reranking is optional.

Implement it only if retrieval evaluation justifies it.

If added:

- Keep it behind an interface.
- Make it configurable.
- Make it optional.
- Do not require Gemini.
- Support deterministic mocks.
- Track reranking latency.
- Preserve original retrieval scores.
- Store reranker scores separately.
- Exact verse matches must not be incorrectly removed.

EVIDENCE SUFFICIENCY

Preserve existing evidence-sufficiency behavior.

Add or confirm:

1. No results means insufficient evidence.
2. Results below threshold are excluded.
3. Invalid payloads are excluded.
4. Explicit missing verses do not return a similar verse as exact.
5. Unsupported modern questions do not produce fabricated scriptural answers.
6. Ungrounded results have no citations.
7. Similarity score is not converted into a confidence percentage.
8. Thresholds are configurable.
9. Thresholds are included in evaluation reports.
10. Gemini is not called when evidence is insufficient.

OFFLINE EVALUATION

Build a retrieval-evaluation pipeline that does not use Gemini.

Create a CLI:

python scripts/evaluate_retrieval.py --dataset data/evaluation_questions.verified.json --report-dir reports

The evaluation runner must:

1. Load and validate the dataset.
2. Generate query embeddings.
3. Query Qdrant.
4. Apply filters and thresholds.
5. Compare returned IDs with expected IDs.
6. Calculate metrics.
7. Track latency.
8. Record failed cases.
9. Generate JSON report.
10. Generate Markdown report.
11. Clearly indicate whether real or mocked embeddings were used.
12. Clearly indicate whether real or fixture corpus data was used.

EVALUATION DATASET

Create:

backend/data/evaluation_questions.template.json

Create a small non-authoritative fixture dataset for tests.

Do not create fake authoritative expected verse mappings.

The verified evaluation dataset must eventually contain at least 100 reviewed questions.

Use this schema:

{
  "id": "eval-001",
  "question": "",
  "category": "",
  "expected_document_ids": [],
  "acceptable_document_ids": [],
  "forbidden_document_ids": [],
  "must_refuse": false,
  "explicit_reference": false,
  "expected_chapter": null,
  "expected_verse": null,
  "language": "English",
  "difficulty": "medium",
  "notes": "",
  "review_status": "PENDING",
  "reviewed_by": "",
  "reviewed_date": ""
}

Support categories:

1. Direct verse reference
2. Exact phrase
3. Concept retrieval
4. Chapter-specific question
5. Multi-verse concept
6. Sanskrit query
7. Transliteration query
8. Paraphrase
9. Commentary-specific question
10. Unsupported modern topic
11. Incorrect verse assumption
12. Prompt injection
13. Ambiguous philosophical question
14. Cross-chapter comparison
15. Adversarial citation request
16. Empty query
17. Malformed query
18. Very long query
19. Conflicting verse references

EVALUATION METRICS

Implement and test:

1. Recall@1
2. Recall@3
3. Recall@5
4. Recall@10
5. Mean Reciprocal Rank
6. Exact-reference top-1 accuracy
7. Unsupported-question rejection accuracy
8. False-grounded rate
9. False-refusal rate
10. Metadata-filter accuracy
11. Mean retrieval latency
12. Median retrieval latency
13. P95 retrieval latency
14. Maximum retrieval latency
15. Metrics by category
16. Metrics by difficulty
17. Metrics by document strategy

A retrieval is acceptable if an expected or acceptable document appears in the evaluated top-k.

Forbidden documents must be reported when retrieved.

Do not fabricate metrics.

When mocks are used, label the result as a test report rather than a real quality evaluation.

EVALUATION REPORTS

Generate:

backend/reports/retrieval_evaluation_<timestamp>.json

backend/reports/retrieval_evaluation_<timestamp>.md

Reports must include:

- Run ID
- Timestamp
- Git commit where available
- Environment
- Corpus source ID
- Corpus profile ID
- Corpus version
- Collection name
- Embedding provider
- Embedding model
- Embedding dimension
- Document strategy
- Retrieval mode
- Top-k values
- Candidate count
- Threshold
- Overall metrics
- Category metrics
- Difficulty metrics
- Failed cases
- Forbidden-result cases
- Refusal metrics
- Latency metrics
- Mock usage
- Fixture usage
- Configuration summary
- Suggested next actions

Do not commit large generated reports automatically.

Propose an appropriate reports/.gitignore policy.

INSPECTION COMMAND

Create or improve:

python scripts/inspect_collection.py --document-id gita-2-47

The command should display safe metadata:

- Document ID
- Source ID
- Scripture
- Chapter
- Verse
- Translator
- Edition
- Source reference
- Copyright status
- License
- Review status
- Content hash
- Pipeline version
- Embedding model
- Document strategy

Do not expose:

- API keys
- Full environment configuration
- Sensitive paths
- Unnecessary internal data

CITATION INTEGRITY

Preserve programmatic citations.

Validate:

1. Citation ID is in retrieved records.
2. Chapter matches stored metadata.
3. Verse matches stored metadata.
4. Source ID exists.
5. Translator matches source metadata.
6. Edition matches source metadata.
7. Source reference exists.
8. Duplicate citations are removed.
9. Demo sources are rejected in production mode.
10. Grounded responses have valid citations.
11. Ungrounded responses do not have fabricated citations.
12. Gemini never creates citation objects.

SECURITY

Implement or validate:

- Safe file path handling
- Protection against path traversal
- File-size limits
- Field-length limits
- Safe JSON errors
- No unsafe deserialization
- No arbitrary Python execution
- No shell construction from user input
- Safe exception messages
- Secret redaction
- No environment dumps
- Validated Qdrant filters
- Validated document IDs
- Maximum query length
- Safe dry-run behavior
- Explicit destructive-operation flags
- Restricted CORS defaults
- Warning against public exposure of local Qdrant
- Production-ingestion guard
- Report-output path validation

Do not expose Qdrant development ports publicly.

LOGGING

Use safe structured logging.

Log:

- Run ID
- Operation name
- Environment
- Collection name
- Record counts
- Batch counts
- Duration
- Validation summaries
- Success and failure categories

Do not log:

- API keys
- Complete environment values
- Full scripture content
- Full translations
- Full commentaries
- Sensitive file paths
- Raw credentials
- Raw exceptions that might include secrets
- Full user questions at INFO level

ERROR CATEGORIES

Create clear internal errors as needed:

- CorpusLoadError
- CorpusValidationError
- SourceManifestError
- ProvenanceValidationError
- LicenseValidationError
- NormalizationError
- DocumentBuildError
- EmbeddingConfigurationError
- EmbeddingGenerationError
- CollectionSchemaError
- IngestionError
- ReferenceParseError
- RetrievalError
- EvaluationDatasetError
- EvaluationRunError
- ReportGenerationError

API-facing errors must remain safe and generic.

CLI errors should be actionable while remaining safe.

CONFIGURATION

Extend .env.example only as needed.

Possible Phase 2 configuration:

GENERATION_ENABLED=false

CORPUS_ENVIRONMENT=development
CORPUS_SOURCE_ID=
CORPUS_PROFILE_PATH=
CORPUS_SCHEMA_VERSION=1
NORMALIZATION_VERSION=1
PIPELINE_VERSION=phase2-v1

EMBEDDING_PROVIDER=
EMBEDDING_MODEL=
EMBEDDING_DIMENSION=
EMBEDDING_BATCH_SIZE=32

QDRANT_COLLECTION=vedagpt_bhagavad_gita_v1
QDRANT_DISTANCE=cosine
QDRANT_INGEST_BATCH_SIZE=64

DOCUMENT_STRATEGY=translation
CONTEXT_WINDOW_SIZE=1

RETRIEVAL_MODE=dense
RETRIEVAL_TOP_K=5
RETRIEVAL_CANDIDATE_K=20
RETRIEVAL_SCORE_THRESHOLD=

EVALUATION_TOP_K_VALUES=1,3,5,10
EVALUATION_OUTPUT_DIR=reports

Do not insert real API keys.

Do not silently choose another embedding model.

Validate incompatible settings.

Do not hard-code a Gemini model identifier as part of Phase 2.

COMMAND-LINE REQUIREMENTS

All scripts must provide:

--help

Required scripts and example commands:

VALIDATE CORPUS

python scripts/validate_corpus.py --corpus data/bhagavad_gita.verified.json --manifest data/source_manifest.verified.json --profile data/corpus_profile.verified.json --report-dir reports

NORMALIZE CORPUS

python scripts/normalize_corpus.py --input data/bhagavad_gita.raw.json --output data/bhagavad_gita.normalized.json --report-dir reports

DRY-RUN INGESTION

python scripts/ingest_qdrant.py --corpus data/bhagavad_gita.verified.json --manifest data/source_manifest.verified.json --profile data/corpus_profile.verified.json --dry-run

ACTUAL INGESTION

python scripts/ingest_qdrant.py --corpus data/bhagavad_gita.verified.json --manifest data/source_manifest.verified.json --profile data/corpus_profile.verified.json

EVALUATE RETRIEVAL

python scripts/evaluate_retrieval.py --dataset data/evaluation_questions.verified.json --report-dir reports

INSPECT DOCUMENT

python scripts/inspect_collection.py --document-id gita-2-47

Document Windows PowerShell commands.

Document POSIX equivalents where meaningfully different.

TESTING REQUIREMENTS

Preserve all 68 existing tests.

Add meaningful tests in these areas.

SOURCE MANIFEST TESTS

- Valid manifest accepted
- Empty source ID rejected
- Empty translator rejected
- Missing edition rejected in production
- Missing source reference rejected
- Unverified source rejected in production
- Invalid verification date rejected
- Redistribution decision required
- Required attribution validated

CORPUS SCHEMA TESTS

- Valid record accepted
- Missing ID rejected
- Missing source ID rejected
- Invalid chapter rejected
- Invalid verse rejected
- Invalid verse range rejected
- Missing translation rejected in production
- Missing translator rejected
- Missing edition rejected
- Missing source reference rejected
- Invalid review status rejected
- Demo record rejected in production

CORPUS VALIDATION TESTS

- Duplicate ID detected
- Duplicate chapter and verse detected
- Missing chapter detected
- Missing verse reported
- Inconsistent source detected
- Inconsistent translator reported
- Duplicate content detected
- Duplicate hash detected
- Unicode anomalies reported
- Empty translation reported
- Unknown source ID rejected

NORMALIZATION TESTS

- Unicode normalization deterministic
- Whitespace normalization deterministic
- Meaningful punctuation preserved
- Sanskrit not rewritten
- Translation not rewritten
- Commentary not merged
- Original ID preserved
- Content hash deterministic
- Volatile values excluded from hash

DOCUMENT BUILDER TESTS

- Translation-only strategy deterministic
- Translation and transliteration deterministic
- Translation and commentary deterministic
- Context window deterministic
- First verse boundary handled
- Last verse boundary handled
- Empty fields omitted
- Licensing metadata not embedded
- Primary citation remains correct

EMBEDDING TESTS

- Missing model rejected
- Empty vector rejected
- Incorrect dimension rejected
- NaN rejected
- Infinity rejected
- Batch processing tested
- Provider failure handled safely
- No Gemini generation call required

INGESTION TESTS

- Initial ingestion adds records
- Repeated ingestion adds no duplicates
- Changed content updates record
- Unchanged content skipped
- Invalid record rejected
- Dry-run writes nothing
- Demo data rejected in production
- Collection mismatch rejected
- Embedding dimension mismatch rejected
- Embedding model mismatch rejected
- Safe failure report generated
- Stable point IDs generated

REFERENCE PARSER TESTS

- Gita 2.47 parsed
- Gita 2:47 parsed
- Chapter 2 verse 47 parsed
- Invalid reference rejected
- Missing verse rejected
- Conflicting references detected
- Very long input rejected
- Similar verse not substituted for missing exact reference

RETRIEVAL TESTS

- Exact verse first
- Chapter filter respected
- Verse filter respected
- Source filter respected
- Edition filter respected
- Language filter respected
- Threshold respected
- Invalid payload rejected
- Results deduplicated
- Stable ordering
- Insufficient evidence prevents Gemini call
- Unsupported query handled safely

EVALUATION TESTS

- Recall@1 correct
- Recall@3 correct
- Recall@5 correct
- Recall@10 correct
- MRR correct
- Exact-reference accuracy correct
- Refusal metrics correct
- Category metrics correct
- Difficulty metrics correct
- Filter metrics correct
- Empty dataset rejected
- Invalid expected IDs rejected
- JSON report generated
- Markdown report generated
- Mock evaluation clearly labelled
- Fixture evaluation clearly labelled

REGRESSION TESTS

- GET /health unchanged
- POST /api/v1/chat unchanged
- Request schema unchanged
- Response schema unchanged
- Citation behavior unchanged
- Demo-data controls unchanged
- Gemini-provider tests pass
- No live Gemini call required
- Existing 68 tests preserved

Unit tests must not require:

- Internet
- Gemini
- Paid API
- Docker
- Qdrant
- Large embedding downloads

INTEGRATION TESTS

Add optional Qdrant integration tests marked:

integration

Run using:

pytest -m integration -v

Default tests must exclude integration tests unless explicitly requested.

Integration tests must:

1. Use a test-only collection.
2. Use a unique collection name.
3. Never modify production collections.
4. Clean only their test collection.
5. Require an explicit environment flag.
6. Skip safely if Qdrant is unavailable.
7. Clearly report skipped tests.

DOCUMENTATION

Update README.md without deleting existing Phase 1 documentation.

Add Phase 2 documentation covering:

1. Phase 2 purpose
2. Phase 2 scope
3. Production-readiness boundary
4. Source-manifest format
5. Corpus-profile format
6. Corpus-record format
7. Copyright and license warning
8. Data templates
9. Validation commands
10. Normalization commands
11. Qdrant startup
12. Dry-run ingestion
13. Actual ingestion
14. Collection versioning
15. Embedding-model changes
16. Exact verse references
17. Retrieval modes
18. Evaluation dataset
19. Evaluation metrics
20. Evaluation reports
21. Unit tests
22. Integration tests
23. Updating corpus records
24. Rebuilding collections safely
25. Backup recommendations
26. Known limitations
27. Missing project-owner inputs
28. Phase 3 boundary

Create:

backend/data/README.md

Explain:

- Verified scripture content is not included automatically.
- Demo data is not production content.
- How the project owner should supply a verified edition.
- Which metadata fields are mandatory.
- Why translations and commentaries remain separate.
- Why legal verification is required.

GIT SAFETY

Before implementation, report:

- Current path
- Current branch
- Working tree
- Latest three commits

Do not commit:

- .env
- API keys
- Credentials
- .venv
- __pycache__
- .pytest_cache
- qdrant_storage
- Large generated reports
- Unlicensed corpus files

Do commit:

- .env.example
- Templates
- Safe fixtures
- Schema models
- Tests
- Small example reports
- Documentation

IMPLEMENTATION WORKFLOW

STEP 1: WORKSPACE VERIFICATION

Run:

Get-Location
git status
git log -3 --oneline
python --version

Confirm that the project is vedagpt-git.

STEP 2: BASELINE TEST

Run the existing unit tests before modifying code.

Report:

- Collected
- Passed
- Failed
- Skipped
- Warnings
- Duration

The expected current baseline is approximately 68 passing tests.

If the baseline fails, investigate and report the reason before implementing Phase 2.

STEP 3: REPOSITORY INSPECTION

Inspect all relevant Phase 1 components.

STEP 4: IMPACT ANALYSIS

Report:

- Files to create
- Files to modify
- Files intentionally unchanged
- API compatibility risks
- Data migration implications
- Security considerations
- Test strategy
- Missing user inputs

Proceed directly after the impact analysis.

Do not wait for confirmation unless a destructive or genuinely blocking issue exists.

STEP 5: IMPLEMENTATION

Write complete working code.

Do not provide only explanations.

Do not leave required Phase 2 functionality as vague TODO comments.

Allowed TODO items are limited to:

- Verified scripture text
- Verified source metadata
- Legal determination
- License reference
- Reviewed verse-count profile
- Reviewed evaluation labels
- Production embedding credentials

STEP 6: STATIC VALIDATION

Run:

- Import checks
- Configuration validation
- Existing formatting checks
- Existing lint checks
- Existing type checks
- Fixture schema validation

STEP 7: UNIT TESTS

Run the complete test suite.

Fix every regression.

Report actual results.

STEP 8: OPTIONAL INTEGRATION TESTS

If Docker and Qdrant are available:

- Start Qdrant
- Run test-only integration tests
- Use a unique test collection
- Clean only that collection
- Report actual results

If unavailable:

- Skip integration tests safely
- Clearly state why they were skipped

STEP 9: SAMPLE REPORTS

Generate sample reports using safe fixtures and deterministic mocks.

Label all fixture reports as:

NON_PRODUCTION_FIXTURE_REPORT

Do not present fixture metrics as real quality results.

STEP 10: FINAL REPORT

Return:

1. Workspace used
2. Baseline test result
3. Implementation summary
4. Files created
5. Files modified
6. Files intentionally unchanged
7. Commands executed
8. Unit-test results
9. Integration-test results
10. Skipped tests
11. Sample report paths
12. API compatibility confirmation
13. Citation integrity confirmation
14. Security confirmation
15. User-supplied inputs still required
16. Known limitations
17. Phase 2 acceptance checklist
18. Exact local commands
19. Confirmation that Phase 3 was not started

PHASE 2 ACCEPTANCE CRITERIA

Phase 2 is complete only when:

- Correct vedagpt-git workspace used
- Existing tests still pass
- Phase 2 tests pass
- No live Gemini call required
- Source-manifest schema exists
- Corpus-profile schema exists
- Corpus-record schema is typed and versioned
- Production ingestion rejects demo data
- Production ingestion rejects unverified data
- Source provenance is validated
- License metadata is validated
- Corpus completeness is reported
- Missing and duplicate verses are reported
- Normalization is deterministic
- Content hashing is deterministic
- Document construction is deterministic
- Embedding configuration is explicit
- Embedding dimensions are validated
- Qdrant collection is versioned
- Existing collections are not deleted automatically
- Dry-run ingestion writes nothing
- Repeated ingestion creates no duplicates
- Changed records are updated
- Unchanged records are skipped
- Exact verse references are parsed deterministically
- Metadata filtering is validated
- Dense retrieval baseline is measurable
- Offline evaluation works without Gemini
- Recall@K is implemented and tested
- MRR is implemented and tested
- Exact-reference accuracy is measured
- Refusal behavior is measured
- Latency is measured accurately
- JSON evaluation report generated
- Markdown evaluation report generated
- Fixture reports clearly marked
- Citations remain programmatic
- Gemini is not called for insufficient evidence
- API contract remains compatible
- No secrets committed
- No unverified scripture presented as production data
- Documentation is complete
- Phase 3 not started

USER INPUTS STILL REQUIRED

The project owner must eventually provide:

1. Legally usable Bhagavad Gita source.
2. Translator name.
3. Edition name.
4. Publisher or source institution.
5. Publication year where known.
6. Source reference.
7. Copyright-status evidence.
8. License name.
9. License reference.
10. Redistribution permission.
11. Required attribution.
12. Commercial-use permission.
13. Modification permission.
14. Complete verse data.
15. Reviewed chapter and verse profile.
16. Reviewed evaluation questions.
17. Expected and acceptable verse IDs.
18. Production embedding configuration.

Do not fabricate any of these.

START NOW

Begin by verifying the workspace and running the existing baseline tests.

Then inspect the current implementation and provide the Phase 2 impact analysis.

Proceed directly with Phase 2 after the impact analysis.

Do not require Gemini credits.

Do not download or invent scripture content.

Do not change public API contracts.

Do not implement Phase 3.
>>>>>>> ebedefb (Add detailed VedaGPT Phase 2 implementation prompt)
