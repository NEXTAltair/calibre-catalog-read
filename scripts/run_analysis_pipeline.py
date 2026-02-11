#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, tempfile
from pathlib import Path


def run(cmd: list[str]) -> str:
    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if cp.returncode != 0:
        raise RuntimeError(f"cmd failed ({cp.returncode}): {' '.join(cmd)}\n{cp.stderr}")
    return cp.stdout


def extract_text(epub: Path, out_txt: Path) -> None:
    run(["ebook-convert", str(epub), str(out_txt)])


def simple_analysis(text: str, lang: str) -> dict:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    body = "\n".join(lines)
    head = body[:12000]
    if lang == "ja":
        summary = "本文冒頭を中心に要点を抽出した自動解析。必要箇所へ戻れる再読導線を付与。"
        highlights = [
            "主要トピックの把握に必要な語を抽出。",
            "後で読み返すための再読ガイドを保持。",
            "メタデータHTMLへ埋め込み可能な構造で保存。",
        ]
        reread = [{"section": "冒頭", "page": "EPUB-loc", "chunk_id": "auto-intro", "reason": "文脈の再確認"}]
    else:
        summary = "Auto analysis from opening sections with reread anchors."
        highlights = ["Extract key terms from opening content.", "Store reread guidance.", "Persist structure for metadata HTML."]
        reread = [{"section": "opening", "page": "EPUB-loc", "chunk_id": "auto-intro", "reason": "context refresh"}]

    kws = []
    for kw in ["海賊", "歴史", "設計", "章", "目次", "Python", "AI", "データ"]:
        if kw in head:
            kws.append(kw)
    if kws:
        highlights.append(("検出キーワード: " if lang == "ja" else "Detected keywords: ") + ", ".join(kws[:6]))
    return {"summary": summary, "highlights": highlights[:5], "reread": reread}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-library", required=True)
    ap.add_argument("--book-id", required=True, type=int)
    ap.add_argument("--db", default="/home/altair/clawd/data/calibre_analysis.sqlite")
    ap.add_argument("--username")
    ap.add_argument("--password-env", default="CALIBRE_PASSWORD")
    ap.add_argument("--format", default="EPUB")
    ap.add_argument("--lang", default="ja", choices=["ja", "en"])
    ap.add_argument("--cache-dir", default="/home/altair/clawd/.cache/calibre/pipeline")
    ap.add_argument("--analysis-json", help="Optional path to subagent-produced analysis JSON (schema in references/subagent-analysis.schema.json)")
    ns = ap.parse_args()

    pw = os.environ.get(ns.password_env, "")
    auth = []
    if ns.username:
        auth += ["--username", ns.username]
    if pw:
        auth += ["--password", pw]

    cdir = Path(ns.cache_dir) / str(ns.book_id)
    cdir.mkdir(parents=True, exist_ok=True)

    # metadata
    rows = json.loads(run(["calibredb", "--with-library", ns.with_library, *auth, "list", "--for-machine", "--search", f"id:{ns.book_id}", "--fields", "id,title", "--limit", "2"]))
    if not rows:
        raise SystemExit("book not found")
    title = rows[0].get("title", "")

    # export and hash
    run(["calibredb", "--with-library", ns.with_library, *auth, "export", str(ns.book_id), "--to-dir", str(cdir), "--single-dir", "--formats", ns.format, "--dont-write-opf", "--dont-save-cover", "--dont-save-extra-files", "--replace-whitespace"])
    exts = list(cdir.glob(f"*.{ns.format.lower()}"))
    if not exts:
        raise SystemExit(f"no exported {ns.format}")
    src = exts[0]
    fhash = "sha256:" + hashlib.sha256(src.read_bytes()).hexdigest()

    # status check
    st = json.loads(run(["python3", "skills/calibre-catalog-read/scripts/analysis_db.py", "status", "--db", ns.db, "--book-id", str(ns.book_id), "--format", ns.format]))
    if st.get("status") and st["status"].get("file_hash") == fhash:
        print(json.dumps({"ok": True, "skipped": True, "reason": "same_hash", "book_id": ns.book_id, "file_hash": fhash}, ensure_ascii=False))
        return

    txt = cdir / f"book_{ns.book_id}.txt"
    extract_text(src, txt)

    if ns.analysis_json:
        analysis_core = json.loads(Path(ns.analysis_json).read_text())
    else:
        analysis_core = simple_analysis(txt.read_text(errors="ignore"), ns.lang)

    record = {
        "book_id": ns.book_id,
        "library_id": ns.with_library.split("#", 1)[-1],
        "title": title,
        "format": ns.format,
        "file_hash": fhash,
        "lang": ns.lang,
        "summary": analysis_core["summary"],
        "highlights": analysis_core["highlights"],
        "reread": analysis_core["reread"],
        "tags": ["ai-summary", "cached-analysis"],
    }

    # upsert cache record
    subprocess.run(["python3", "skills/calibre-catalog-read/scripts/analysis_db.py", "upsert", "--db", ns.db],
                   input=json.dumps(record, ensure_ascii=False), text=True, check=True)

    payload = {"id": ns.book_id, "analysis": {"lang": ns.lang, "summary": record["summary"], "highlights": record["highlights"], "reread": record["reread"], "tags": record["tags"], "file_hash": fhash}}
    subprocess.run(["python3", "skills/calibre-metadata-apply/scripts/calibredb_apply.py", "--with-library", ns.with_library, *(["--username", ns.username] if ns.username else []), "--password-env", ns.password_env, "--lang", ns.lang, "--apply"],
                   input=json.dumps(payload, ensure_ascii=False)+"\n", text=True, check=True)

    print(json.dumps({"ok": True, "book_id": ns.book_id, "title": title, "file_hash": fhash, "updated": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
