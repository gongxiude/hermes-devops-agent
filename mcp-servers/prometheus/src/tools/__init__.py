"""Tool registry — aggregates all tool groups."""
from .discovery import DISCOVERY_TOOLS
from .info import INFO_TOOLS
from .query import QUERY_TOOLS

__all__ = ["DISCOVERY_TOOLS", "INFO_TOOLS", "QUERY_TOOLS"]
