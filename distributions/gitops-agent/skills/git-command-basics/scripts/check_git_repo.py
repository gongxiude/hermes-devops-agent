#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_git(repo: Path, *args: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_git_repo.py <repo_path>", file=sys.stderr)
        return 2

    repo = Path(sys.argv[1]).expanduser().resolve()
    if not repo.exists():
        print(json.dumps({"ok": False, "error": "repo_path_not_found", "repo": str(repo)}, ensure_ascii=False))
        return 1

    code, top, err = run_git(repo, "rev-parse", "--show-toplevel")
    if code != 0:
        print(json.dumps({"ok": False, "error": "not_a_git_repo", "repo": str(repo), "stderr": err}, ensure_ascii=False))
        return 1

    _, branch, _ = run_git(repo, "branch", "--show-current")
    _, status, _ = run_git(repo, "status", "--short", "--branch")
    _, remotes, _ = run_git(repo, "remote", "-v")

    result = {
        "ok": True,
        "repo": str(repo),
        "top_level": top,
        "branch": branch,
        "status": status.splitlines(),
        "remotes": remotes.splitlines(),
        "dirty": any(line and not line.startswith("## ") for line in status.splitlines()),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
