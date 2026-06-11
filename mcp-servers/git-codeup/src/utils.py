from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


class Config:
    SERVER_NAME = os.getenv("MCP_SERVER_NAME", "git-codeup")
    SERVER_VERSION = "1.0.0"
    LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO")
    REQUEST_TIMEOUT = int(os.getenv("MCP_REQUEST_TIMEOUT", "30"))
    CODEUP_BASE_URL = os.getenv("CODEUP_BASE_URL", "").rstrip("/")
    CODEUP_ACCESS_TOKEN = os.getenv("CODEUP_ACCESS_TOKEN", "").strip()
    CODEUP_ORGANIZATION_ID = os.getenv("CODEUP_ORGANIZATION_ID", "").strip()
    LOCAL_GIT_ROOT = os.getenv("LOCAL_GIT_ROOT", "").strip()


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if Config.CODEUP_ACCESS_TOKEN:
        headers["x-yunxiao-token"] = Config.CODEUP_ACCESS_TOKEN
    return headers


def codeup_get(path: str, params: dict[str, str] | None = None) -> Any:
    if not Config.CODEUP_BASE_URL:
        raise RuntimeError("CODEUP_BASE_URL is not set")
    url = f"{Config.CODEUP_BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=Config.REQUEST_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def codeup_post(path: str, body: dict[str, Any]) -> Any:
    if not Config.CODEUP_BASE_URL:
        raise RuntimeError("CODEUP_BASE_URL is not set")
    url = f"{Config.CODEUP_BASE_URL}{path}"
    headers = _headers()
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=Config.REQUEST_TIMEOUT) as resp:
        payload = resp.read().decode("utf-8")
        return json.loads(payload) if payload.strip() else {}


def safe_repo_path(repo_path: str) -> Path:
    if not Config.LOCAL_GIT_ROOT:
        raise RuntimeError("LOCAL_GIT_ROOT is not set")
    root = Path(Config.LOCAL_GIT_ROOT).resolve()
    target = (root / repo_path).resolve()
    if root not in target.parents and target != root:
        raise RuntimeError(f"repo path escapes LOCAL_GIT_ROOT: {repo_path}")
    return target


def run_git(repo_path: str, *args: str) -> dict[str, str]:
    target = safe_repo_path(repo_path)
    result = subprocess.run(
        ["git", "-C", str(target), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=Config.REQUEST_TIMEOUT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git exited {result.returncode}")
    return {"stdout": result.stdout, "stderr": result.stderr}
