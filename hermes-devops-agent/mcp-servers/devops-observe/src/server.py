#!/usr/bin/env python3
"""
devops-observe MCP Server
=========================
Read-only observability MCP server for DevOps agents.

Tools:
  prometheus_query      — PromQL instant/range query
  loki_query_range      — LogQL range query
  k8s_get_workload      — Kubernetes workload GET (read-only)
  readonly_guard_check  — Validate action against mutation deny-list
  intlsms_inspect       — Full intlsms runtime inspection

Resources:
  info://server                     — Server metadata and tool inventory
  observe://env/{env}/status        — Endpoint config status per environment
"""
import logging
import sys
from pathlib import Path

# Allow `from src.xxx import` when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent))

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

from src.tools import (
    prometheus_query,
    loki_query_range,
    k8s_get_workload,
    readonly_guard_check,
    intlsms_inspect,
)

for _tool in [prometheus_query, loki_query_range, k8s_get_workload,
              readonly_guard_check, intlsms_inspect]:
    mcp.tool(_tool)

# ---------------------------------------------------------------------------
# Register resources
# ---------------------------------------------------------------------------

from src.resources import server_info, environment_status

mcp.resource("info://server")(server_info)
mcp.resource("observe://env/{env}/status")(environment_status)

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

logger.info("devops-observe MCP server loaded (tools=5)")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="devops-observe FastMCP server (stdio)")
    parser.add_argument("--test", action="store_true", help="Validate imports and exit")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.test:
        print(f"Server : {Config.SERVER_NAME} v{Config.SERVER_VERSION}")
        print("Tools  : prometheus_query, loki_query_range, k8s_get_workload, "
              "readonly_guard_check, intlsms_inspect")
        print("Status : OK")
        sys.exit(0)

    mcp.run()
