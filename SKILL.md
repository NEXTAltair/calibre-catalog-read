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

## Subagent support (model-agnostic)

- Prompt template: `references/subagent-analysis.prompt.md`
- Output schema: `references/subagent-analysis.schema.json`

Rules:
- Use subagent only for analysis generation.
- Keep final DB upsert and Calibre metadata apply in main agent.
- Process one book per run.
- Ask model/thinking/timeout in conversation and do not hardcode provider-specific model IDs.
