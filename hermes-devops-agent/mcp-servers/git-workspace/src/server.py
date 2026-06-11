#!/usr/bin/env python3
from __future__ import annotations

import logging
import shutil
from typing import Annotated

from fastmcp import FastMCP

from utils import (
    Config,
    allowed_check_commands,
    mirror_path,
    repo_spec,
    repos,
    run,
    run_checked,
    validate_branch_name,
    workspace_root,
    worktree_path,
)

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

mcp = FastMCP(name=Config.SERVER_NAME, version=Config.SERVER_VERSION)


def _check_file(target, rel_path: str) -> dict:
    path = target / rel_path
    return {
        "name": f"exists:{rel_path}",
        "returncode": 0 if path.exists() else 1,
        "stdout": f"found {rel_path}" if path.exists() else "",
        "stderr": "" if path.exists() else f"missing {rel_path}",
        "command": ["builtin", "exists", rel_path],
        "cwd": str(target),
    }


def _check_any(target, rel_paths: list[str], name: str) -> dict:
    found = [rel_path for rel_path in rel_paths if (target / rel_path).exists()]
    return {
        "name": name,
        "returncode": 0 if found else 1,
        "stdout": "\n".join(found),
        "stderr": "" if found else f"none found: {', '.join(rel_paths)}",
        "command": ["builtin", "exists-any", *rel_paths],
        "cwd": str(target),
    }


def _builtin_checks(prefix: str, target) -> list[dict]:
    if prefix == "yuexin-infra":
        return [
            _check_file(target, "Makefile"),
            _check_file(target, "bin/generate-argo"),
            _check_file(target, "bin/validate-conf"),
            _check_file(target, "bin/yaml-lint"),
            _check_file(target, "deploy/manifest.yaml"),
            _check_file(target, "workloads"),
        ]
    if prefix == "jenkins-pipeline":
        return [
            _check_file(target, "README.md"),
            _check_file(target, "jenkinsfiles"),
            _check_file(target, "jobs"),
            _check_file(target, "share-library/vars"),
            _check_file(target, "share-library/resources"),
            _check_any(
                target,
                [
                    "share-library/vars/updateInfra.groovy",
                    "share-library/vars/updateInfraImage.groovy",
                    "share-library/vars/argoDeploy.groovy",
                ],
                "shared-library-delivery-vars",
            ),
        ]
    return [
        {
            "name": "known-prefix",
            "returncode": 1,
            "stdout": "",
            "stderr": f"no builtin checks for {prefix}",
            "command": ["builtin", "known-prefix", prefix],
            "cwd": str(target),
        }
    ]


@mcp.tool
def git_workspace_list_repos() -> dict:
    return {
        "workspace_root": str(workspace_root()),
        "repos": [
            {
                "prefix": item.prefix,
                "remote": item.remote,
                "branch": item.branch,
                "kind": item.kind,
            }
            for item in repos().values()
        ],
    }


@mcp.tool
def git_workspace_ensure_mirror(
    prefix: Annotated[str, "Repository prefix: jenkins-pipeline or yuexin-infra"],
    fetch: Annotated[bool, "Fetch remote after ensuring mirror exists"] = True,
) -> dict:
    spec = repo_spec(prefix)
    mirror = mirror_path(prefix)
    if mirror.exists():
        if fetch:
            result = run_checked(["git", "-C", str(mirror), "fetch", "--prune", "origin"])
        else:
            result = {"returncode": 0, "stdout": "", "stderr": "", "command": [], "cwd": str(mirror)}
        created = False
    else:
        result = run_checked(["git", "clone", "--mirror", spec.remote, str(mirror)], timeout=300)
        created = True
    return {
        "prefix": prefix,
        "remote": spec.remote,
        "branch": spec.branch,
        "mirror": str(mirror),
        "created": created,
        "fetch_result": result,
    }


@mcp.tool
def git_workspace_create_worktree(
    prefix: Annotated[str, "Repository prefix"],
    task_id: Annotated[str, "Kanban task id or correlation id"],
    branch_name: Annotated[str, "New local draft branch name"],
    base_ref: Annotated[str, "Base branch or ref"] = "",
) -> dict:
    spec = repo_spec(prefix)
    mirror = mirror_path(prefix)
    if not mirror.exists():
        git_workspace_ensure_mirror(prefix, fetch=True)
    base = base_ref or spec.branch
    target = worktree_path(prefix, task_id)
    if target.exists():
        status = run_checked(["git", "-C", str(target), "status", "--short", "--branch"])
        return {
            "prefix": prefix,
            "worktree": str(target),
            "branch": branch_name,
            "created": False,
            "status": status["stdout"],
        }
    target.parent.mkdir(parents=True, exist_ok=True)
    result = run_checked(["git", "-C", str(mirror), "worktree", "add", "-b", branch_name, str(target), base])
    return {
        "prefix": prefix,
        "worktree": str(target),
        "branch": branch_name,
        "base_ref": base,
        "created": True,
        "result": result,
    }


@mcp.tool
def git_workspace_status(
    prefix: Annotated[str, "Repository prefix"],
    task_id: Annotated[str, "Kanban task id or correlation id"],
) -> dict:
    target = worktree_path(prefix, task_id)
    status = run_checked(["git", "-C", str(target), "status", "--short", "--branch"])
    recent = run_checked(["git", "-C", str(target), "log", "--oneline", "-5"])
    return {"prefix": prefix, "worktree": str(target), "status": status["stdout"], "recent_commits": recent["stdout"]}


@mcp.tool
def git_workspace_diff(
    prefix: Annotated[str, "Repository prefix"],
    task_id: Annotated[str, "Kanban task id or correlation id"],
    base_ref: Annotated[str, "Base ref for diff"] = "",
) -> dict:
    spec = repo_spec(prefix)
    target = worktree_path(prefix, task_id)
    base = base_ref or spec.branch
    stat = run_checked(["git", "-C", str(target), "diff", "--stat", base, "--"])
    diff = run_checked(["git", "-C", str(target), "diff", base, "--"])
    return {"prefix": prefix, "worktree": str(target), "base_ref": base, "stat": stat["stdout"], "diff": diff["stdout"]}


@mcp.tool
def git_workspace_run_checks(
    prefix: Annotated[str, "Repository prefix"],
    task_id: Annotated[str, "Kanban task id or correlation id"],
) -> dict:
    target = worktree_path(prefix, task_id)
    commands = allowed_check_commands(prefix)
    results = _builtin_checks(prefix, target)
    for command in commands:
        results.append(run(command, cwd=target, timeout=300))
    return {
        "prefix": prefix,
        "worktree": str(target),
        "commands_configured": len(commands),
        "passed": all(item["returncode"] == 0 for item in results),
        "results": results,
    }


@mcp.tool
def git_workspace_push_branch(
    prefix: Annotated[str, "Repository prefix"],
    task_id: Annotated[str, "Kanban task id or correlation id"],
    branch_name: Annotated[str, "Remote branch name to create or update; master/main are denied"],
) -> dict:
    if not Config.ENABLE_PUSH:
        raise RuntimeError("GIT_WORKSPACE_ENABLE_PUSH is not true")
    spec = repo_spec(prefix)
    branch = validate_branch_name(branch_name)
    target = worktree_path(prefix, task_id)
    status = run_checked(["git", "-C", str(target), "status", "--short"])
    if status["stdout"].strip():
        raise RuntimeError("worktree has uncommitted changes; commit before pushing")
    current = run_checked(["git", "-C", str(target), "rev-parse", "--abbrev-ref", "HEAD"])["stdout"].strip()
    if current in {"master", "main"}:
        raise RuntimeError(f"refusing to push protected branch: {current}")
    result = run_checked(["git", "-C", str(target), "push", spec.remote, f"HEAD:refs/heads/{branch}"], timeout=300)
    return {
        "prefix": prefix,
        "remote": spec.remote,
        "worktree": str(target),
        "branch_name": branch,
        "result": result,
    }


@mcp.tool
def git_workspace_cleanup_worktree(
    prefix: Annotated[str, "Repository prefix"],
    task_id: Annotated[str, "Kanban task id or correlation id"],
    force: Annotated[bool, "Force remove after checking status"] = False,
) -> dict:
    target = worktree_path(prefix, task_id)
    if not target.exists():
        return {"prefix": prefix, "worktree": str(target), "removed": False, "reason": "not_found"}
    status = run(["git", "-C", str(target), "status", "--short"])
    if status["returncode"] == 0 and status["stdout"].strip() and not force:
        return {"prefix": prefix, "worktree": str(target), "removed": False, "reason": "dirty", "status": status["stdout"]}
    mirror = mirror_path(prefix)
    command = ["git", "-C", str(mirror), "worktree", "remove", str(target)]
    if force:
        command.append("--force")
    remove = run(command)
    if remove["returncode"] != 0 and target.exists() and force:
        shutil.rmtree(target)
    return {"prefix": prefix, "worktree": str(target), "removed": True, "git_result": remove}


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Git workspace FastMCP server (stdio)")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        print(f"Server : {Config.SERVER_NAME} v{Config.SERVER_VERSION}")
        print(f"Root   : {Config.WORKSPACE_ROOT or '(not set)'}")
        print(f"Repos  : {', '.join(sorted(repos()))}")
        print("Tools  : 8")
        print("Status : OK")
        sys.exit(0)
    mcp.run()
