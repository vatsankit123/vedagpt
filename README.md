# VedaGPT

VedaGPT is a source-grounded educational RAG application for understanding selected Indian scriptures.

## Current phase

Phase 1: Bhagavad Gita RAG proof of concept using:

- FastAPI
- Qdrant
- Claude
- Multilingual embeddings
- Structured citations
- Citation validation

## Implementation prompt

The Phase 1 implementation specification is available here:

prompts/VedaGPT_Phase1_Claude_Prompt.md

## Important

Do not upload API keys, `.env` files, copyrighted scripture datasets, or private credentials to this repository.


PROMPT:

Read prompts/VedaGPT_Phase1_Claude_Prompt.md completely before making any changes.

Treat that file as the authoritative project specification.

Start by inspecting the current workspace and provide the required impact analysis.

After the impact analysis, proceed directly with implementing Phase 1 only. Do not wait for further confirmation unless there is a genuinely blocking issue.

Requirements:
- Create complete working files, not only explanations or pseudocode.
- Build the FastAPI, Qdrant, embedding and Claude RAG implementation described in the prompt.
- Use structured citations generated from retrieved metadata.
- Add corpus validation, citation validation and evidence-sufficiency handling.
- Add Docker Compose, .env.example, tests and README instructions.
- Do not invent scripture text or translations.
- Do not treat unverified scripture content as production data.
- Use clearly labelled demo fixtures only where required for testing.
- Run all available tests and report the actual results.
- Do not claim that a command or test succeeded unless it was actually executed.
- Do not implement any Phase 2 functionality.
- Do not implement React, React Native, authentication, agents, LangGraph, payments or mobile features.

Begin now.