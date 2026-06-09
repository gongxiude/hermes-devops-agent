#!/usr/bin/env python3
"""
Prometheus MCP Server
=====================
FastMCP port of https://github.com/idanfishman/prometheus-mcp

Tools (10 total, all read-only):
  Discovery (6): prometheus_list_metrics, prometheus_metric_metadata,
                 prometheus_list_labels,  prometheus_label_values,
                 prometheus_list_targets, prometheus_scrape_pool_targets
  Info      (2): prometheus_runtime_info, prometheus_build_info
  Query     (2): prometheus_query,        prometheus_query_range

Environment variables:
  PROMETHEUS_URL          — Prometheus base URL, e.g. http://localhost:9090 (required)
  PROMETHEUS_TOKEN        — Bearer token for authenticated endpoints (optional)
  ENABLE_DISCOVERY_TOOLS  — enable discovery tool group (default: true)
  ENABLE_INFO_TOOLS       — enable info tool group     (default: true)
  ENABLE_QUERY_TOOLS      — enable query tool group    (default: true)
  MCP_SERVER_NAME         — server name                (default: prometheus)
  MCP_LOG_LEVEL           — logging level              (default: INFO)
  MCP_REQUEST_TIMEOUT     — HTTP timeout in seconds    (default: 30)
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastmcp import FastMCP
from src.utils import Config

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

mcp = FastMCP(name=Config.SERVER_NAME, version=Config.SERVER_VERSION)

# ---------------------------------------------------------------------------
# Register tools
# ---------------------------------------------------------------------------

from src.tools import DISCOVERY_TOOLS, INFO_TOOLS, QUERY_TOOLS

_registered = 0

if Config.ENABLE_DISCOVERY_TOOLS:
    for _tool in DISCOVERY_TOOLS:
        mcp.tool(_tool)
    _registered += len(DISCOVERY_TOOLS)
    logger.info("Discovery tools enabled (%d)", len(DISCOVERY_TOOLS))

if Config.ENABLE_INFO_TOOLS:
    for _tool in INFO_TOOLS:
        mcp.tool(_tool)
    _registered += len(INFO_TOOLS)
    logger.info("Info tools enabled (%d)", len(INFO_TOOLS))

if Config.ENABLE_QUERY_TOOLS:
    for _tool in QUERY_TOOLS:
        mcp.tool(_tool)
    _registered += len(QUERY_TOOLS)
    logger.info("Query tools enabled (%d)", len(QUERY_TOOLS))

# ---------------------------------------------------------------------------
# Register resources
# ---------------------------------------------------------------------------

from src.resources import server_info

mcp.resource("info://server")(server_info)

# ---------------------------------------------------------------------------
# Lifecycle log
# ---------------------------------------------------------------------------

logger.info(
    "Prometheus MCP server loaded (tools=%d, url=%s, auth=%s)",
    _registered,
    Config.PROMETHEUS_URL or "(not set)",
    "token" if Config.PROMETHEUS_TOKEN else "none",
)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Prometheus FastMCP server (stdio)")
    parser.add_argument("--test",  action="store_true", help="Validate imports and exit")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.test:
        print(f"Server  : {Config.SERVER_NAME} v{Config.SERVER_VERSION}")
        print(f"URL     : {Config.PROMETHEUS_URL or '(not set)'}")
        print(f"Auth    : {'Bearer token' if Config.PROMETHEUS_TOKEN else 'none'}")
        print(f"Tools   : {_registered}")
        print("Status  : OK")
        sys.exit(0)

    mcp.run()
