"""Slash commands and CLI commands for the DevOps plugin."""
from __future__ import annotations

import argparse
import json
import os
from typing import Optional

from . import audit as _audit

# ---------------------------------------------------------------------------
# /devops_status  — show profile / tool / MCP status
# ---------------------------------------------------------------------------

_STATUS_HELP = """\
/devops_status — DevOps Agent status

Subcommands:
  (none)     Show active profile, MCP servers, and recent audit summary
  audit      Alias for /devops_audit
"""


def handle_devops_status(raw_args: str) -> str:
    """Handle the /devops_status slash command."""
    argv = raw_args.strip().split()
    if argv and argv[0] in {"audit"}:
        return handle_devops_audit(" ".join(argv[1:]))

    profile = os.environ.get("HERMES_PROFILE", "(unknown)")
    hermes_home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))

    recent = _audit.tail(10)
    tool_counts: dict[str, int] = {}
    for ev in recent:
        tool = ev.get("tool", "")
        tool_counts[tool] = tool_counts.get(tool, 0) + 1

    lines = [
        "╭─ DevOps Agent Status ───────────────────────────────────╮",
        f"  Profile   : {profile}",
        f"  Home      : {hermes_home}",
        f"  Audit log : {hermes_home}/logs/devops_audit.jsonl",
        "",
        f"  Recent tools ({len(recent)} events):",
    ]
    if tool_counts:
        for tool, cnt in sorted(tool_counts.items(), key=lambda x: -x[1])[:5]:
            lines.append(f"    {cnt:>3}×  {tool}")
    else:
        lines.append("    (no recent audit events)")

    lines.append("╰─────────────────────────────────────────────────────────╯")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# /devops_audit  — query the audit trail
# ---------------------------------------------------------------------------

_AUDIT_HELP = """\
/devops_audit — Query DevOps audit trail

Subcommands:
  tail [N]            Show last N events (default: 20)
  search <keyword>    Search recent events for keyword
"""


def handle_devops_audit(raw_args: str) -> str:
    """Handle the /devops_audit slash command."""
    argv = raw_args.strip().split()
    if not argv or argv[0] in {"help", "-h", "--help"}:
        return _AUDIT_HELP

    sub = argv[0]

    if sub == "tail":
        n = int(argv[1]) if len(argv) > 1 and argv[1].isdigit() else 20
        events = _audit.tail(n)
        if not events:
            return "No audit events found."
        lines = [f"Last {len(events)} events:"]
        for ev in events:
            policy = ev.get("policy", {})
            allow = "✅" if policy.get("allow", True) else "❌"
            lines.append(
                f"  {allow} [{ev.get('ts','')}] {ev.get('profile','')} "
                f"→ {ev.get('tool','')} (task={ev.get('task_id','')[:8]})"
            )
        return "\n".join(lines)

    if sub == "search":
        kw = " ".join(argv[1:])
        if not kw:
            return "Usage: /devops_audit search <keyword>"
        results = _audit.search(kw)
        if not results:
            return f"No audit events matching '{kw}'."
        return f"Found {len(results)} event(s):\n" + json.dumps(results, indent=2, ensure_ascii=False)

    return f"Unknown subcommand: {sub}\n\n{_AUDIT_HELP}"


# ---------------------------------------------------------------------------
# hermes devops <subcommand>  — CLI command
# ---------------------------------------------------------------------------

def setup_devops_cli(parser: argparse.ArgumentParser) -> None:
    """Register CLI subcommands under `hermes devops`."""
    sub = parser.add_subparsers(dest="devops_cmd")

    # hermes devops status
    sub.add_parser("status", help="Show DevOps agent profile and MCP status")

    # hermes devops audit
    audit_p = sub.add_parser("audit", help="Query the DevOps audit trail")
    audit_p.add_argument("audit_cmd", nargs="?", default="tail",
                         choices=["tail", "search"], help="Subcommand")
    audit_p.add_argument("audit_arg", nargs="?", default="",
                         help="N for tail, keyword for search")

    # hermes devops check-profile
    sub.add_parser("check-profile", help="Validate active profile config")


def handle_devops_cli(args: argparse.Namespace) -> None:
    """Dispatch `hermes devops` CLI subcommands."""
    cmd = getattr(args, "devops_cmd", None) or "status"

    if cmd == "status":
        print(handle_devops_status(""))

    elif cmd == "audit":
        sub = getattr(args, "audit_cmd", "tail")
        arg = getattr(args, "audit_arg", "") or ""
        print(handle_devops_audit(f"{sub} {arg}".strip()))

    elif cmd == "check-profile":
        profile = os.environ.get("HERMES_PROFILE", "(unknown)")
        home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
        print(f"Active profile : {profile}")
        print(f"HERMES_HOME    : {home}")
        config = f"{home}/config.yaml"
        env = f"{home}/.env"
        import pathlib
        print(f"config.yaml    : {'✅' if pathlib.Path(config).exists() else '❌'} {config}")
        print(f".env           : {'✅' if pathlib.Path(env).exists() else '❌'} {env}")

    else:
        print(f"Unknown command: {cmd}\nUsage: hermes devops [status|audit|check-profile]")
