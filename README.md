# calibre-catalog-read

Calibre catalog lookup + one-book AI reading pipeline.

## Setup

1. Install Calibre on the runtime machine.
   - Required: `calibredb`
   - Required for extraction: `ebook-convert`
2. Ensure binaries are on PATH.
3. Ensure Calibre Content server is reachable.
4. Always use explicit `HOST:PORT` in:
   - `http://HOST:PORT/#LIBRARY_ID`
5. If auth is enabled, pass username/password env.

## Important

OpenClaw alone is not enough: runtime must have `calibredb`.

On Windows, metadata/file operations can fail under Defender Controlled Folder Access.
If writes fail with WinError 2/5, add Calibre library folder/binaries to allowlist.

## Quick test (catalog)

```bash
node scripts/calibredb_read.mjs list \
  --with-library "http://192.168.11.20:8080/#Calibreライブラリ" \
  --username user --password-env CALIBRE_PASSWORD \
  --limit 5
```

## Quick test (one-book pipeline)

```bash
python3 scripts/run_analysis_pipeline.py \
  --with-library "http://192.168.11.20:8080/#Calibreライブラリ" \
  --username user --password-env CALIBRE_PASSWORD \
  --book-id 3 --lang ja
```
