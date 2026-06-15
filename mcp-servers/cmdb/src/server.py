#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
from typing import Annotated

from fastmcp import FastMCP

from utils import Config, _fuzzy_search, _get_services, _match_service

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

mcp = FastMCP(name=Config.SERVER_NAME, version=Config.SERVER_VERSION)


@mcp.tool
def cmdb_list_services(
    environment: Annotated[str, "Optional environment filter (prod/test/staging)"] = "",
) -> dict:
    """List all registered services in the CMDB.

    Args:
        environment: Optional filter by deployment environment.

    Returns:
        Dictionary with service list and count.
    """
    services = _get_services()
    if environment:
        services = [s for s in services if environment in s.get("environments", [])]

    summary = []
    for svc in services:
        summary.append({
            "name": svc.get("name"),
            "owner": svc.get("owner"),
            "sla": svc.get("sla"),
            "environments": svc.get("environments", []),
            "tags": svc.get("tags", []),
        })

    return {
        "total": len(summary),
        "services": summary,
    }


@mcp.tool
def cmdb_get_service(
    name: Annotated[str, "Service name to look up"],
) -> dict:
    """Get detailed information about a specific service.

    Args:
        name: Exact service name.

    Returns:
        Full service record including owner, repo, SLA, dependencies, and tags.
    """
    services = _get_services()
    svc = _match_service(name, services)
    if not svc:
        return {
            "found": False,
            "name": name,
            "message": f"Service '{name}' not found in CMDB",
        }

    return {
        "found": True,
        **svc,
    }


@mcp.tool
def cmdb_get_dependencies(
    name: Annotated[str, "Service name"],
    direction: Annotated[str, "upstream, downstream, or both"] = "both",
) -> dict:
    """Get upstream and/or downstream dependencies for a service.

    Args:
        name: Exact service name.
        direction: 'upstream', 'downstream', or 'both'.

    Returns:
        Dependency graph with service names and SLAs.
    """
    services = _get_services()
    svc = _match_service(name, services)
    if not svc:
        return {"found": False, "name": name, "message": f"Service '{name}' not found"}

    deps = svc.get("dependencies", {})
    result = {"found": True, "name": name}

    if direction in ("upstream", "both"):
        upstream_names = deps.get("upstream", [])
        upstream = []
        for dep_name in upstream_names:
            dep_svc = _match_service(dep_name, services)
            upstream.append({
                "name": dep_name,
                "sla": dep_svc.get("sla") if dep_svc else None,
                "owner": dep_svc.get("owner") if dep_svc else None,
            })
        result["upstream"] = upstream

    if direction in ("downstream", "both"):
        downstream_names = deps.get("downstream", [])
        downstream = []
        for dep_name in downstream_names:
            dep_svc = _match_service(dep_name, services)
            downstream.append({
                "name": dep_name,
                "sla": dep_svc.get("sla") if dep_svc else None,
                "owner": dep_svc.get("owner") if dep_svc else None,
            })
        result["downstream"] = downstream

    return result


@mcp.tool
def cmdb_search_services(
    query: Annotated[str, "Search query — matches name, owner, or tags"],
) -> dict:
    """Search services by name, owner, or tag.

    Args:
        query: Case-insensitive search string.

    Returns:
        Matching services with basic details.
    """
    services = _get_services()
    results = _fuzzy_search(query, services)

    return {
        "query": query,
        "total": len(results),
        "results": [
            {
                "name": s.get("name"),
                "owner": s.get("owner"),
                "sla": s.get("sla"),
                "tags": s.get("tags", []),
            }
            for s in results
        ],
    }


@mcp.tool
def cmdb_list_environments() -> dict:
    """List all configured environments across all services.

    Returns:
        Unique environments and service counts per environment.
    """
    services = _get_services()
    env_counts: dict[str, int] = {}
    for svc in services:
        for env in svc.get("environments", []):
            env_counts[env] = env_counts.get(env, 0) + 1

    return {
        "environments": [
            {"name": env, "service_count": count}
            for env, count in sorted(env_counts.items())
        ],
    }


if __name__ == "__main__":
    mcp.run()