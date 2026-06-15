#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


KNOWN_DIRS = ("vars", "src", "resources", "jenkinsfiles", "jobs", "share-library", "pipeline", "pipelines")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: inspect_repo_layout.py <repo_root>", file=sys.stderr)
        return 2

    repo = Path(sys.argv[1]).expanduser().resolve()
    if not repo.is_dir():
        print(json.dumps({"ok": False, "error": "repo_not_found", "repo": str(repo)}, ensure_ascii=False))
        return 1

    dirs = []
    for name in KNOWN_DIRS:
        path = repo / name
        if path.exists():
            files = [str(p.relative_to(repo)) for p in path.rglob("*") if p.is_file()]
            dirs.append({"path": name, "file_count": len(files), "sample_files": files[:20]})

    jenkinsfiles = [str(p.relative_to(repo)) for p in repo.rglob("*") if p.is_file() and "jenkinsfile" in p.name.lower()]

    print(json.dumps({
        "ok": True,
        "repo": str(repo),
        "known_dirs": dirs,
        "jenkinsfiles": jenkinsfiles[:50],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
