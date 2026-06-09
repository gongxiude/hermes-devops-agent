#!/usr/bin/env python3
"""
k8s MCP Server
==============
Kubernetes management tools via kubectl, translated from kagent-tools/pkg/k8s.

Read-only tools (always registered):
  k8s_get_resources, k8s_get_pod_logs, k8s_get_events,
  k8s_get_available_api_resources, k8s_get_cluster_configuration,
  k8s_get_resource_yaml, k8s_describe_resource

Write tools (registered when K8S_READ_ONLY=false):
  k8s_scale, k8s_patch_resource, k8s_patch_status,
  k8s_apply_manifest, k8s_create_resource, k8s_create_resource_from_url,
  k8s_delete_resource, k8s_rollout,
  k8s_label_resource, k8s_annotate_resource,
  k8s_remove_label, k8s_remove_annotation,
  k8s_execute_command, k8s_check_service_connectivity

Environment variables:
  KUBECTL_BIN       — kubectl binary path (default: kubectl)
  KUBECONFIG        — kubeconfig file path (default: ~/.kube/config)
  K8S_READ_ONLY     — disable write tools when "true" (default: true)
  MCP_SERVER_NAME   — server name (default: k8s)
  MCP_LOG_LEVEL     — logging level (default: INFO)
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

from src.tools import READONLY_TOOLS, WRITE_TOOLS

for _tool in READONLY_TOOLS:
    mcp.tool(_tool)

if not Config.READ_ONLY:
    for _tool in WRITE_TOOLS:
        mcp.tool(_tool)
    logger.info("Write tools enabled (K8S_READ_ONLY=false)")
else:
    logger.info("Read-only mode (K8S_READ_ONLY=true), write tools not registered")

# ---------------------------------------------------------------------------
# Register resources
# ---------------------------------------------------------------------------

from src.resources import server_info

mcp.resource("info://server")(server_info)

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

logger.info(
    "k8s MCP server loaded (tools=%d, read_only=%s)",
    len(READONLY_TOOLS) + (0 if Config.READ_ONLY else len(WRITE_TOOLS)),
    Config.READ_ONLY,
)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="k8s FastMCP server (stdio)")
    parser.add_argument("--test", action="store_true", help="Validate imports and exit")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.test:
        tool_count = len(READONLY_TOOLS) + (0 if Config.READ_ONLY else len(WRITE_TOOLS))
        print(f"Server    : {Config.SERVER_NAME} v{Config.SERVER_VERSION}")
        print(f"Read-only : {Config.READ_ONLY}")
        print(f"Tools     : {tool_count}")
        print(f"kubectl   : {Config.KUBECTL_BIN}")
        print("Status    : OK")
        sys.exit(0)

    mcp.run()
