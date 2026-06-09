#!/usr/bin/env python3
from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import FastMCP

from utils import Config, codeup_get, run_git

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

mcp = FastMCP(name=Config.SERVER_NAME, version=Config.SERVER_VERSION)


@mcp.tool
def codeup_list_repositories(
    page: Annotated[int, "Page number"] = 1,
    per_page: Annotated[int, "Page size"] = 20,
    search: Annotated[str, "Optional search keyword"] = "",
) -> dict:
    org = Config.CODEUP_ORGANIZATION_ID
    params = {"page": str(page), "perPage": str(per_page)}
    if search:
        params["search"] = search
    return codeup_get(f"/oapi/v1/codeup/organizations/{org}/repositories", params)


@mcp.tool
def codeup_list_change_requests(
    repository_id: Annotated[str, "Repository ID"],
    page: Annotated[int, "Page number"] = 1,
    per_page: Annotated[int, "Page size"] = 20,
    state: Annotated[str, "Optional state"] = "",
) -> dict:
    params = {"page": str(page), "perPage": str(per_page)}
    if state:
        params["state"] = state
    return codeup_get(
        f"/oapi/v1/codeup/organizations/{Config.CODEUP_ORGANIZATION_ID}/repositories/{repository_id}/changeRequests",
        params,
    )


@mcp.tool
def codeup_get_change_request(
    repository_id: Annotated[str, "Repository ID"],
    local_id: Annotated[str, "Change request local ID"],
) -> dict:
    return codeup_get(
        f"/oapi/v1/codeup/organizations/{Config.CODEUP_ORGANIZATION_ID}/repositories/{repository_id}/changeRequests/{local_id}"
    )


@mcp.tool
def codeup_list_commits(
    repository_id: Annotated[str, "Repository ID"],
    ref_name: Annotated[str, "Optional branch or tag"] = "",
    page: Annotated[int, "Page number"] = 1,
    per_page: Annotated[int, "Page size"] = 20,
) -> dict:
    params = {"page": str(page), "perPage": str(per_page)}
    if ref_name:
        params["refName"] = ref_name
    return codeup_get(
        f"/oapi/v1/codeup/organizations/{Config.CODEUP_ORGANIZATION_ID}/repositories/{repository_id}/commits",
        params,
    )


@mcp.tool
def git_repo_status(
    repo_path: Annotated[str, "Repository path under LOCAL_GIT_ROOT"],
) -> dict:
    status = run_git(repo_path, "status", "--short", "--branch")
    recent = run_git(repo_path, "log", "--oneline", "-5")
    return {"status": status["stdout"], "recent_commits": recent["stdout"]}


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Git / Codeup FastMCP server (stdio)")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        print(f"Server : {Config.SERVER_NAME} v{Config.SERVER_VERSION}")
        print(f"URL    : {Config.CODEUP_BASE_URL or '(not set)'}")
        print(f"Root   : {Config.LOCAL_GIT_ROOT or '(not set)'}")
        print("Tools  : 5")
        print("Status : OK")
        sys.exit(0)
    mcp.run()
