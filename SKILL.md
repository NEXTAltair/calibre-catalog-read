---
name: calibre-catalog-read
description: Read-only lookup of existing Calibre library metadata via calibredb over a Content server. Use when you need to search/list books, inspect existing title/author/series/tags/formats, or fetch current metadata before planning changes.
---

# calibre-catalog-read

Read existing Calibre data only. Do not write changes.

## Requirements

- `calibredb` available on PATH in the runtime where the script is executed.
- Reachable Calibre Content server URL in `--with-library` format:
  - `http://HOST:PORT/#LIBRARY_ID`
- If auth is enabled, pass:
  - `--username <user>`
  - `--password-env <ENV_VAR_NAME>` (recommended)

## Usage

List books (JSON):

```bash
python3 skills/calibre-catalog-read/scripts/calibredb_read.py list \
  --with-library "http://127.0.0.1:8080/#-" \
  --limit 50
```

Search books (JSON):

```bash
python3 skills/calibre-catalog-read/scripts/calibredb_read.py search \
  --with-library "http://127.0.0.1:8080/#MyLibrary" \
  --query 'series:"My Series"'
```

Get one book by id (JSON):

```bash
python3 skills/calibre-catalog-read/scripts/calibredb_read.py id \
  --with-library "http://127.0.0.1:8080/#MyLibrary" \
  --book-id 123
```

## Notes

- This skill is read-only by design.
- Prefer this skill first to confirm current metadata before any write operation.
