"""Discovery tools — metric/label/target enumeration."""
from __future__ import annotations

from typing import Annotated, Optional
from ..utils import _api_get


def prometheus_list_metrics() -> dict:
    """List all available metric names in Prometheus."""
    body = _api_get("label/__name__/values")
    metrics = body.get("data", [])
    return {"count": len(metrics), "metrics": metrics}


def prometheus_metric_metadata(
    metric: Annotated[str, "Metric name to look up metadata for"],
) -> dict:
    """Get metadata (type, help text, unit) for a specific metric."""
    body = _api_get("metadata", {"metric": metric})
    return {"metric": metric, "metadata": body.get("data", {})}


def prometheus_list_labels() -> dict:
    """List all label names available in Prometheus."""
    body = _api_get("labels")
    labels = body.get("data", [])
    return {"count": len(labels), "labels": labels}


def prometheus_label_values(
    label: Annotated[str, "Label name whose values to retrieve"],
) -> dict:
    """Get all values for a specific label."""
    body = _api_get(f"label/{label}/values")
    values = body.get("data", [])
    return {"label": label, "count": len(values), "values": values}


def prometheus_list_targets() -> dict:
    """List all scrape targets and their current health status."""
    body = _api_get("targets")
    data = body.get("data", {})
    active   = data.get("activeTargets", [])
    dropped  = data.get("droppedTargets", [])
    return {
        "active_count":  len(active),
        "dropped_count": len(dropped),
        "active":  [
            {
                "scrapePool": t.get("scrapePool"),
                "scrapeUrl":  t.get("scrapeUrl"),
                "health":     t.get("health"),
                "labels":     t.get("labels"),
                "lastError":  t.get("lastError") or None,
            }
            for t in active
        ],
        "dropped": dropped,
    }


def prometheus_scrape_pool_targets(
    scrape_pool: Annotated[str, "Name of the scrape pool to filter by"],
) -> dict:
    """Get all targets belonging to a specific scrape pool."""
    body = _api_get("targets", {"state": "active"})
    all_active = body.get("data", {}).get("activeTargets", [])
    filtered = [t for t in all_active if t.get("scrapePool") == scrape_pool]
    return {
        "scrapePool": scrape_pool,
        "count": len(filtered),
        "targets": filtered,
    }


DISCOVERY_TOOLS = [
    prometheus_list_metrics,
    prometheus_metric_metadata,
    prometheus_list_labels,
    prometheus_label_values,
    prometheus_list_targets,
    prometheus_scrape_pool_targets,
]
