#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from typing import Any


def run(cmd: list[str]) -> str:
    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if cp.returncode != 0:
        raise RuntimeError(f"calibredb failed ({cp.returncode})\nCMD: {' '.join(shlex.quote(x) for x in cmd)}\nERR:\n{cp.stderr.strip()}")
    return cp.stdout


def common_args(ns: argparse.Namespace) -> list[str]:
    args = ["--with-library", ns.with_library]
    if ns.username:
        args += ["--username", ns.username]
    if ns.password_env:
        pw = os.environ.get(ns.password_env, "")
        if pw:
            args += ["--password", pw]
    return args


def cmd_list(ns: argparse.Namespace) -> dict[str, Any]:
    fields = ns.fields or "id,title,authors,series,series_index,tags,formats,publisher,pubdate,languages,last_modified"
    cmd = ["calibredb", "list", "--for-machine", "--fields", fields, "--limit", str(ns.limit)] + common_args(ns)
    out = run(cmd)
    return {"ok": True, "mode": "list", "fields": fields, "items": json.loads(out)}


def cmd_search(ns: argparse.Namespace) -> dict[str, Any]:
    fields = ns.fields or "id,title,authors,series,series_index,tags,formats,publisher,pubdate,languages,last_modified"
    cmd = [
        "calibredb", "list", "--for-machine", "--fields", fields,
        "--search", ns.query, "--limit", str(ns.limit)
    ] + common_args(ns)
    out = run(cmd)
    return {"ok": True, "mode": "search", "query": ns.query, "fields": fields, "items": json.loads(out)}


def cmd_id(ns: argparse.Namespace) -> dict[str, Any]:
    # Reuse list+search by id for machine-readable JSON
    fields = ns.fields or "id,title,authors,series,series_index,tags,formats,publisher,pubdate,languages,last_modified,comments"
    cmd = [
        "calibredb", "list", "--for-machine", "--fields", fields,
        "--search", f"id:{ns.book_id}", "--limit", "5"
    ] + common_args(ns)
    out = run(cmd)
    rows = json.loads(out)
    hit = [r for r in rows if str(r.get("id")) == str(ns.book_id)]
    return {"ok": True, "mode": "id", "book_id": ns.book_id, "item": (hit[0] if hit else None)}


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_common(p: argparse.ArgumentParser):
        p.add_argument("--with-library", required=True, help="http://HOST:PORT/#LIBRARY_ID")
        p.add_argument("--username")
        p.add_argument("--password-env", default="CALIBRE_PASSWORD")
        p.add_argument("--fields")

    p_list = sub.add_parser("list")
    add_common(p_list)
    p_list.add_argument("--limit", type=int, default=100)

    p_search = sub.add_parser("search")
    add_common(p_search)
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--limit", type=int, default=100)

    p_id = sub.add_parser("id")
    add_common(p_id)
    p_id.add_argument("--book-id", required=True)

    ns = ap.parse_args()

    try:
        if ns.cmd == "list":
            res = cmd_list(ns)
        elif ns.cmd == "search":
            res = cmd_search(ns)
        else:
            res = cmd_id(ns)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
