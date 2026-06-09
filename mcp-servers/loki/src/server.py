#!/usr/bin/env python3
from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import FastMCP

from utils import Config, _request

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

mcp = FastMCP(name=Config.SERVER_NAME, version=Config.SERVER_VERSION)


@mcp.tool
def loki_query_range(
    logql: Annotated[str, "LogQL expression"],
    start: Annotated[str, "RFC3339 or ns timestamp"] = "",
    end: Annotated[str, "RFC3339 or ns timestamp"] = "",
    limit: Annotated[int, "Max log entries"] = 100,
) -> dict:
    params = {"query": logql, "limit": str(limit)}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    return _request("/loki/api/v1/query_range", params)


@mcp.tool
def loki_labels() -> dict:
    return _request("/loki/api/v1/labels")


@mcp.tool
def loki_label_values(
    label_name: Annotated[str, "Label name"],
) -> dict:
    return _request(f"/loki/api/v1/label/{label_name}/values")


@mcp.tool
def loki_series(
    match: Annotated[str, "One match[] selector"],
    start: Annotated[str, "Optional start"] = "",
    end: Annotated[str, "Optional end"] = "",
) -> dict:
    params = {"match[]": match}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    return _request("/loki/api/v1/series", params)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Loki FastMCP server (stdio)")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        print(f"Server : {Config.SERVER_NAME} v{Config.SERVER_VERSION}")
        print(f"URL    : {Config.LOKI_URL or '(not set)'}")
        print("Tools  : 4")
        print("Status : OK")
        sys.exit(0)
    mcp.run()
