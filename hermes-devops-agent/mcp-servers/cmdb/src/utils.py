from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class Config:
    SERVER_NAME = os.getenv("MCP_SERVER_NAME", "cmdb")
    SERVER_VERSION = "0.1.0"
    LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO")
    DATA_PATH = os.getenv("CMDB_DATA_PATH", "")


def _load_data() -> dict[str, Any]:
    """Load CMDB data from YAML file or JSON file."""
    if not Config.DATA_PATH:
        raise RuntimeError("CMDB_DATA_PATH is not set")

    path = Path(Config.DATA_PATH)
    if not path.exists():
        raise RuntimeError(f"CMDB_DATA_PATH not found: {Config.DATA_PATH}")

    raw = path.read_text(encoding="utf-8")

    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml
            return yaml.safe_load(raw) or {}
        except ImportError:
            raise RuntimeError("PyYAML is required for YAML CMDB data files. Install with: pip install pyyaml")
    elif path.suffix == ".json":
        import json
        return json.loads(raw)
    else:
        raise RuntimeError(f"Unsupported CMDB data format: {path.suffix}. Use .yaml or .json")


def _get_services() -> list[dict]:
    data = _load_data()
    return data.get("services", [])


def _match_service(name: str, services: list[dict]) -> dict | None:
    for svc in services:
        if svc.get("name", "").lower() == name.lower():
            return svc
    return None


def _fuzzy_search(query: str, services: list[dict]) -> list[dict]:
    q = query.lower()
    results = []
    for svc in services:
        name = svc.get("name", "").lower()
        owner = svc.get("owner", "").lower()
        tags = [t.lower() for t in svc.get("tags", [])]
        if q in name or q in owner or any(q in t for t in tags):
            results.append(svc)
    return results