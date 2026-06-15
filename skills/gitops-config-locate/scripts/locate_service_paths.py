#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


KUSTOMIZE_NAMES = {"kustomization.yaml", "kustomization.yml", "Kustomization"}


def score_path(path: Path, domain: str, service: str, environment: str) -> int:
    parts = {p.lower() for p in path.parts}
    text = str(path).lower()
    score = 0
    for token in (domain.lower(), service.lower(), environment.lower()):
        if token in parts:
            score += 4
        elif token in text:
            score += 2
    if path.name in KUSTOMIZE_NAMES:
        score += 3
    if "workloads" in parts:
        score += 1
    return score


def main() -> int:
    if len(sys.argv) != 5:
        print("usage: locate_service_paths.py <repo_root> <domain> <service> <environment>", file=sys.stderr)
        return 2

    repo = Path(sys.argv[1]).expanduser().resolve()
    domain, service, environment = sys.argv[2:5]
    if not repo.is_dir():
        print(json.dumps({"ok": False, "error": "repo_not_found", "repo": str(repo)}, ensure_ascii=False))
        return 1

    candidates: list[dict[str, object]] = []
    search_roots = [repo / "workloads", repo / "deploy", repo / "cluster-bootstrap", repo]
    seen: set[Path] = set()
    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path in seen or path.name == ".git" or ".git" in path.parts:
                continue
            seen.add(path)
            if path.is_dir() or path.suffix.lower() in {".yaml", ".yml", ".json", ".tpl"} or path.name in KUSTOMIZE_NAMES:
                score = score_path(path.relative_to(repo), domain, service, environment)
                if score >= 5:
                    candidates.append({
                        "path": str(path.relative_to(repo)),
                        "type": "directory" if path.is_dir() else "file",
                        "score": score,
                        "is_kustomization": path.name in KUSTOMIZE_NAMES,
                    })

    candidates.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
    overlay_candidates = []
    for item in candidates:
        p = repo / str(item["path"])
        directory = p if p.is_dir() else p.parent
        if any((directory / name).is_file() for name in KUSTOMIZE_NAMES):
            rel = str(directory.relative_to(repo))
            if rel not in overlay_candidates:
                overlay_candidates.append(rel)

    exact_overlay = repo / "workloads" / domain / service / environment
    best_match = None
    if exact_overlay.is_dir():
        best_match = str(exact_overlay.relative_to(repo))
    elif candidates:
        first = repo / str(candidates[0]["path"])
        best_match = str((first if first.is_dir() else first.parent).relative_to(repo))

    print(json.dumps({
        "ok": bool(candidates),
        "repo": str(repo),
        "domain": domain,
        "service": service,
        "environment": environment,
        "best_match": best_match,
        "matched_paths": candidates[:20],
        "overlay_candidates": overlay_candidates[:10],
    }, ensure_ascii=False, indent=2))
    return 0 if candidates else 1


if __name__ == "__main__":
    raise SystemExit(main())
