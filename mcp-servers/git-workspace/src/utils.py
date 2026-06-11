from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RepoSpec:
    prefix: str
    remote: str
    branch: str
    kind: str


class Config:
    SERVER_NAME = os.getenv("MCP_SERVER_NAME", "git-workspace")
    SERVER_VERSION = "1.0.0"
    LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO")
    REQUEST_TIMEOUT = int(os.getenv("MCP_REQUEST_TIMEOUT", "120"))
    WORKSPACE_ROOT = os.getenv("GIT_WORKSPACE_ROOT", "").strip()
    CHECK_COMMANDS_JSON = os.getenv("GIT_WORKSPACE_CHECK_COMMANDS", "{}").strip() or "{}"
    ENABLE_PUSH = os.getenv("GIT_WORKSPACE_ENABLE_PUSH", "false").lower() == "true"


DEFAULT_REPOS = {
    "jenkins-pipeline": RepoSpec(
        prefix="jenkins-pipeline",
        remote="git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/jenkins-pipeline.git",
        branch="master",
        kind="jenkins-shared-library",
    ),
    "yuexin-infra": RepoSpec(
        prefix="yuexin-infra",
        remote="git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/yuexin-infra.git",
        branch="master",
        kind="gitops-kubernetes-infra",
    ),
}


def repos() -> dict[str, RepoSpec]:
    raw = os.getenv("GIT_WORKSPACE_REPOS_JSON", "").strip()
    if not raw:
        return DEFAULT_REPOS
    data = json.loads(raw)
    result: dict[str, RepoSpec] = {}
    for prefix, item in data.items():
        result[prefix] = RepoSpec(
            prefix=prefix,
            remote=str(item["remote"]),
            branch=str(item.get("branch", "master")),
            kind=str(item.get("kind", "unknown")),
        )
    return result


def repo_spec(prefix: str) -> RepoSpec:
    all_repos = repos()
    if prefix not in all_repos:
        raise RuntimeError(f"unknown repo prefix: {prefix}")
    return all_repos[prefix]


def workspace_root() -> Path:
    if not Config.WORKSPACE_ROOT:
        raise RuntimeError("GIT_WORKSPACE_ROOT is not set")
    root = Path(Config.WORKSPACE_ROOT).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "mirrors").mkdir(exist_ok=True)
    (root / "worktrees").mkdir(exist_ok=True)
    return root


def safe_child(*parts: str) -> Path:
    root = workspace_root()
    target = root.joinpath(*parts).resolve()
    if target != root and root not in target.parents:
        raise RuntimeError(f"path escapes workspace root: {target}")
    return target


def mirror_path(prefix: str) -> Path:
    repo_spec(prefix)
    return safe_child("mirrors", f"{prefix}.git")


def worktree_path(prefix: str, task_id: str) -> Path:
    repo_spec(prefix)
    safe_task = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in task_id)
    if not safe_task:
        raise RuntimeError("task_id is required")
    return safe_child("worktrees", prefix, safe_task)


def run(cmd: list[str], cwd: Path | None = None, timeout: int | None = None) -> dict[str, Any]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout or Config.REQUEST_TIMEOUT,
        check=False,
    )
    return {
        "command": cmd,
        "cwd": str(cwd) if cwd else "",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def run_checked(cmd: list[str], cwd: Path | None = None, timeout: int | None = None) -> dict[str, Any]:
    result = run(cmd, cwd=cwd, timeout=timeout)
    if result["returncode"] != 0:
        raise RuntimeError(result["stderr"].strip() or f"command failed: {cmd}")
    return result


def allowed_check_commands(prefix: str) -> list[list[str]]:
    data = json.loads(Config.CHECK_COMMANDS_JSON)
    commands = data.get(prefix, [])
    if not isinstance(commands, list):
        raise RuntimeError(f"check commands for {prefix} must be a list")
    parsed: list[list[str]] = []
    for command in commands:
        if isinstance(command, str):
            parsed.append(shlex.split(command))
        elif isinstance(command, list) and all(isinstance(part, str) for part in command):
            parsed.append(command)
        else:
            raise RuntimeError(f"invalid check command for {prefix}: {command!r}")
    return parsed


def validate_branch_name(branch_name: str) -> str:
    branch = branch_name.strip()
    if not branch:
        raise RuntimeError("branch_name is required")
    if branch in {"master", "main"} or branch.startswith("refs/"):
        raise RuntimeError(f"branch_name is not allowed: {branch_name}")
    if branch.startswith("-") or ".." in branch or branch.endswith("/") or " " in branch:
        raise RuntimeError(f"branch_name is not allowed: {branch_name}")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._/-")
    if any(ch not in allowed for ch in branch):
        raise RuntimeError(f"branch_name contains unsupported characters: {branch_name}")
    return branch
