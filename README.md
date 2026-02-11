# calibre-catalog-read

Calibre catalog lookup + one-book AI reading pipeline.

Note: this pipeline excludes manga/comic-centric titles by design (cost/quality guard for text-only analysis).

## Setup

1. Install Calibre in the OpenClaw execution environment (the machine/runtime that executes this skill).
   - This provides required binaries: `calibredb` and `ebook-convert`
2. Ensure binaries are on PATH.
3. Ensure Calibre Content server is reachable.
4. Always use explicit `HOST:PORT` in:
   - `http://HOST:PORT/#LIBRARY_ID`
5. If auth is enabled, pass username/password env.

## Important

OpenClaw alone is not enough: install Calibre in the OpenClaw execution environment so required binaries are available.

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

## Subagent input chunking (recommended)

To avoid read-tool line-size issues, split extracted text and pass file list to subagent via `subagent_input.json`:

```bash
python3 scripts/prepare_subagent_input.py \
  --book-id 3 --title "<title>" --lang ja \
  --text-path /tmp/book_3.txt --out-dir /tmp/calibre_subagent_3
```


## Low-text safeguard

If extracted text is too short, the pipeline exits with `reason: low_text_requires_confirmation` and asks for user confirmation (English prompt).
Use `--force-low-text` only after user confirmation.
