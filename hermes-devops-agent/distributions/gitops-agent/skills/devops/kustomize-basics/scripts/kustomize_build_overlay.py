#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: kustomize_build_overlay.py <repo_root> <relative_overlay_path>", file=sys.stderr)
        return 2

    if not shutil.which("kustomize"):
        print(json.dumps({"ok": False, "error": "kustomize_not_found"}, ensure_ascii=False))
        return 1

    repo = Path(sys.argv[1]).expanduser().resolve()
    overlay = (repo / sys.argv[2]).resolve()
    if not str(overlay).startswith(str(repo)):
        print(json.dumps({"ok": False, "error": "overlay_outside_repo", "overlay": str(overlay)}, ensure_ascii=False))
        return 1

    proc = subprocess.run(
        ["kustomize", "build", str(overlay), "--load-restrictor", "LoadRestrictionsNone"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        print(json.dumps({"ok": False, "error": "kustomize_build_failed", "stderr": proc.stderr.strip()}, ensure_ascii=False))
        return proc.returncode

    resources = []
    for doc in yaml.safe_load_all(proc.stdout):
        if isinstance(doc, dict):
            meta = doc.get("metadata") or {}
            resources.append({"kind": doc.get("kind"), "name": meta.get("name"), "namespace": meta.get("namespace")})

    print(json.dumps({
        "ok": True,
        "repo": str(repo),
        "relative_overlay": sys.argv[2],
        "resource_count": len(resources),
        "resources": resources[:50],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
