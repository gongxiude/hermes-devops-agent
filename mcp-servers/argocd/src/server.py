#!/usr/bin/env python3
from __future__ import annotations

import logging
import urllib.parse
from typing import Annotated

from fastmcp import FastMCP

from utils import Config, _request

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

mcp = FastMCP(name=Config.SERVER_NAME, version=Config.SERVER_VERSION)


@mcp.tool
def argocd_get_version() -> dict:
    return _request("version")


@mcp.tool
def argocd_list_applications(
    project: Annotated[str, "Optional project filter"] = "",
    repo: Annotated[str, "Optional repo URL filter"] = "",
) -> dict:
    params: dict[str, str] = {}
    if project:
        params["project"] = project
    if repo:
        params["repo"] = repo
    return _request("applications", params)


@mcp.tool
def argocd_get_application(
    name: Annotated[str, "Application name"],
    app_namespace: Annotated[str, "Optional app namespace"] = "",
) -> dict:
    params = {"appNamespace": app_namespace} if app_namespace else None
    return _request(f"applications/{urllib.parse.quote(name, safe='')}", params)


@mcp.tool
def argocd_get_project(
    name: Annotated[str, "Project name"],
) -> dict:
    return _request(f"projects/{urllib.parse.quote(name, safe='')}")


@mcp.tool
def argocd_get_settings() -> dict:
    return _request("settings")


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="ArgoCD FastMCP server (stdio)")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        print(f"Server : {Config.SERVER_NAME} v{Config.SERVER_VERSION}")
        print(f"URL    : {Config.ARGOCD_API_URL or '(not set)'}")
        print("Tools  : 5")
        print("Status : OK")
        sys.exit(0)
    mcp.run()
