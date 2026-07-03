"""Offline tests for DevOps Kanban reply-target parsing."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "devops_agent"
PKG = "devops_agent_under_test"


def _load_pkg():
    spec = importlib.util.spec_from_file_location(
        PKG,
        PLUGIN_DIR / "__init__.py",
        submodule_search_locations=[str(PLUGIN_DIR)],
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[PKG] = mod
    spec.loader.exec_module(mod)
    return mod


_load_pkg()
kanban_reply = sys.modules[f"{PKG}.kanban_reply"]


def test_parse_bare_feishu_chat_id():
    assert kanban_reply.parse_reply_target("reply_target: oc_abc123") == "oc_abc123"


def test_parse_explicit_feishu_target():
    assert kanban_reply.parse_reply_target("reply_target: feishu:oc_abc123") == "oc_abc123"


def test_reject_placeholder_reply_target():
    assert kanban_reply.parse_reply_target("reply_target: current_conversation") is None


def test_session_reply_target_fallback_for_feishu(monkeypatch):
    monkeypatch.setenv("HERMES_SESSION_PLATFORM", "feishu")
    monkeypatch.setenv("HERMES_SESSION_CHAT_ID", "oc_abc123")
    assert kanban_reply._session_reply_target() == "oc_abc123"


def test_session_reply_target_ignores_non_feishu(monkeypatch):
    monkeypatch.setenv("HERMES_SESSION_PLATFORM", "tui")
    monkeypatch.setenv("HERMES_SESSION_CHAT_ID", "oc_abc123")
    assert kanban_reply._session_reply_target() is None
