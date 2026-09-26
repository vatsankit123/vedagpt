# VedaGPT — Corpus Data Directory

## Overview

This directory holds corpus files, source manifests, corpus profiles, and evaluation datasets.

**IMPORTANT: Verified scripture content is NOT included in this repository.**

This repository contains only:
- Template files (`.template.json`) — structural guides for the project owner
- Sample demo fixtures (`*.sample.json`) — for unit testing only
- This README

---

## Why Verified Content Is Not Included

The Bhagavad Gita has many translations and editions.  Each edition has different:
- Copyright status
- License terms
- Redistribution permissions
- Attribution requirements

VedaGPT cannot determine legal status automatically.  **The project owner must supply, verify, and take legal responsibility for any corpus included in a deployment.**

Demo fixtures (`DEMO_DATA_NOT_FOR_PRODUCTION`) are provided for testing pipeline mechanics only.  They must never be used as the basis for a production deployment.

---

## Mandatory Fields for Every Corpus Record

| Field | Required for Production |
|-------|------------------------|
| `id` | ✓ (unique) |
| `source_id` | ✓ (must match manifest) |
| `scripture` | ✓ |
| `chapter` | ✓ (positive integer) |
| `verse` | ✓ (positive integer) |
| `translation` | ✓ (non-empty) |
| `translator` | ✓ |
| `edition` | ✓ |
| `source_reference` | ✓ |
| `copyright_status` | ✓ |
| `license_name` | ✓ |
| `license_reference` | ✓ |
| `record_version` | ✓ (≥ 1) |
| `review_status` | ✓ (must be VERIFIED) |
| `reviewed_by` | ✓ |
| `reviewed_date` | ✓ (YYYY-MM-DD) |

Optional:
- `sanskrit`, `transliteration`, `commentary`, `commentator`, `verse_end`, `notes`

---

## How to Supply a Verified Edition

1. Obtain a legally licensed Bhagavad Gita translation.
2. Verify copyright status with your legal advisor.
3. Complete `source_manifest.template.json` → rename to `source_manifest.verified.json`.
4. Complete `corpus_profile.template.json` → rename to `corpus_profile.verified.json`.
5. Prepare your corpus as `bhagavad_gita.verified.json` (array of records).
6. Run: `python scripts\validate_corpus.py --corpus data\bhagavad_gita.verified.json --manifest data\source_manifest.verified.json --production`
7. Run: `python scripts\ingest_qdrant.py --corpus data\bhagavad_gita.verified.json --manifest data\source_manifest.verified.json --dry-run`
8. If dry-run passes, run without `--dry-run`.

---

## Why Translations and Commentaries Are Kept Separate

- Translations and commentaries have independent copyright ownership.
- Mixing them in a single field makes attribution impossible.
- The retrieval pipeline can apply separate embedding strategies (e.g. translation-only vs. translation-and-commentary).
- A commentator's interpretation must never be presented as the primary translation.

---

## Legal Verification Required

The following fields require legal verification by the project owner:
- `copyright_status`
- `license_name`
- `license_reference`
- `redistribution_permitted`
- `commercial_use_permitted`
- `modification_permitted`
- `attribution_required`
- `required_attribution`

Do not assume Public Domain status without verification.  Even older translations may have been republished under new copyright.
