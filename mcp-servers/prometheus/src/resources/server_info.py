"""Server info resource."""
from __future__ import annotations
from ..utils import Config


def server_info() -> str:
    """Return server configuration summary."""
    url = Config.PROMETHEUS_URL or "(not set)"
    auth = "Bearer token" if Config.PROMETHEUS_TOKEN else "none"
    tools = []
    if Config.ENABLE_DISCOVERY_TOOLS: tools.append("discovery(6)")
    if Config.ENABLE_INFO_TOOLS:      tools.append("info(2)")
    if Config.ENABLE_QUERY_TOOLS:     tools.append("query(2)")
    return (
        f"Prometheus MCP Server v{Config.SERVER_VERSION}\n"
        f"URL:  {url}\n"
        f"Auth: {auth}\n"
        f"Tool groups: {', '.join(tools) or 'none'}"
    )
