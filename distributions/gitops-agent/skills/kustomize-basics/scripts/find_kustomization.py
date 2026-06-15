#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


NAMES = ("kustomization.yaml", "kustomization.yml", "Kustomization")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: find_kustomization.py <repo_root> <relative_overlay_path>", file=sys.stderr)
        return 2

    repo = Path(sys.argv[1]).expanduser().resolve()
    overlay = (repo / sys.argv[2]).resolve()
    if not str(overlay).startswith(str(repo)):
        print(json.dumps({"ok": False, "error": "overlay_outside_repo", "overlay": str(overlay)}, ensure_ascii=False))
        return 1

    found = [name for name in NAMES if (overlay / name).is_file()]
    result = {
        "ok": bool(found),
        "repo": str(repo),
        "overlay": str(overlay),
        "relative_overlay": sys.argv[2],
        "kustomization_files": found,
    }
    if not found:
        result["error"] = "kustomization_not_found"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if found else 1


if __name__ == "__main__":
    raise SystemExit(main())
