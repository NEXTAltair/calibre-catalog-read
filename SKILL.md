---
name: calibre-catalog-read
description: Read Calibre catalog data via calibredb over a Content server, and run one-book analysis workflow that writes HTML analysis block back to comments while caching analysis state in SQLite. Use for list/search/id lookups and AI reading pipeline for a selected book.
---

# calibre-catalog-read

Use this skill for:
- Read-only catalog lookup (`list/search/id`)
- One-book AI reading workflow (`export -> analyze -> cache -> comments HTML apply`)

## Requirements

- `calibredb` available on PATH in the runtime where scripts are executed.
- `ebook-convert` available for text extraction.
- Reachable Calibre Content server URL in `--with-library` format:
  - `http://HOST:PORT/#LIBRARY_ID`
- Do not assume localhost/127.0.0.1; always pass explicit reachable `HOST:PORT`.
- If auth is enabled, pass:
  - `--username <user>`
  - `--password-env <ENV_VAR_NAME>`

## Commands

List books (JSON):

```bash
node skills/calibre-catalog-read/scripts/calibredb_read.mjs list \
  --with-library "http://192.168.11.20:8080/#Calibreライブラリ" \
  --username user --password-env CALIBRE_PASSWORD \
  --limit 50
```

Search books (JSON):

```bash
node skills/calibre-catalog-read/scripts/calibredb_read.mjs search \
  --with-library "http://192.168.11.20:8080/#Calibreライブラリ" \
  --username user --password-env CALIBRE_PASSWORD \
  --query 'series:"中公文庫"'
```

Get one book by id (JSON):

```bash
node skills/calibre-catalog-read/scripts/calibredb_read.mjs id \
  --with-library "http://192.168.11.20:8080/#Calibreライブラリ" \
  --username user --password-env CALIBRE_PASSWORD \
  --book-id 3
```

Run one-book pipeline (analyze + comments HTML apply + cache):

```bash
python3 skills/calibre-catalog-read/scripts/run_analysis_pipeline.py \
  --with-library "http://192.168.11.20:8080/#Calibreライブラリ" \
  --username user --password-env CALIBRE_PASSWORD \
  --book-id 3 --lang ja
```

## Cache DB

Initialize DB schema:

```bash
python3 skills/calibre-catalog-read/scripts/analysis_db.py init \
  --db /home/altair/clawd/data/calibre_analysis.sqlite
```

Check current hash state:

```bash
python3 skills/calibre-catalog-read/scripts/analysis_db.py status \
  --db /home/altair/clawd/data/calibre_analysis.sqlite \
  --book-id 3 --format EPUB
```

## Subagent pre-flight (required)

Before spawning a subagent for analysis, ask the user and confirm:
- `model` (lightweight model id they want)
- `thinking` (`low`/`medium`/`high`)
- `runTimeoutSeconds`

If the user did not specify these in the current request, do not assume defaults silently.
Ask once, then proceed with the confirmed values.

## Subagent support (model-agnostic)

Book-reading analysis is a heavy task. Use a subagent with a lightweight model for analysis generation, then return results to main agent for cache/apply steps.

- Prompt template: `references/subagent-analysis.prompt.md`
- Output schema: `references/subagent-analysis.schema.json`

Rules:
- Use subagent only for analysis generation.
- Keep final DB upsert and Calibre metadata apply in main agent.
- Process one book per run.
- Ask model/thinking/timeout in conversation before spawn and do not hardcode provider-specific model IDs.
- Configure callback/announce behavior and rate-limit fallbacks using OpenClaw default model/subagent/fallback settings (not hardcoded in this skill).
- Exclude manga/comic-centric books from this text pipeline (skip when title/tags indicate manga/comic).
- If extracted text is too short, stop and ask user for confirmation before continuing.
  - The pipeline returns `reason: low_text_requires_confirmation` with `prompt_en` text.

## Language policy

- Do not hardcode user-language prose in pipeline scripts.
- Generate user-visible analysis text from subagent output, with language controlled by user-selected settings and `lang` input.
- Fallback local analysis in scripts is generic/minimal; preferred path is subagent output following the prompt template.
