"""Deterministic completion for routine observability Kanban tasks.

This module intentionally supports only the narrow Feishu fast path created by
``devops_agent.fastpath``. It keeps the user-facing Kanban/notify contract, but
avoids sending the common CPU/memory query through a model loop.
"""
from __future__ import annotations

import os
import statistics
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CPU_QUERY = (
    'sum by (pod) (rate(container_cpu_usage_seconds_total{'
    'namespace="prod",pod=~"gateway.*",container!="",container!="POD"}[1m]))'
)
MEMORY_QUERY = (
    'sum by (pod) (container_memory_working_set_bytes{'
    'namespace="prod",pod=~"gateway.*",container!="",container!="POD"})'
)


@dataclass(frozen=True)
class SeriesSummary:
    pod: str
    current: float
    avg: float
    max: float


def complete_async(task_id: str, parsed: Any, *, profile_dir: str = "/opt/data/profiles/observability") -> None:
    """Complete a supported observability task in a daemon thread."""
    thread = threading.Thread(
        target=_complete_task,
        args=(task_id, parsed, profile_dir),
        name=f"observability-fastpath-{task_id}",
        daemon=True,
    )
    thread.start()


def complete(task_id: str, parsed: Any, *, profile_dir: str = "/opt/data/profiles/observability") -> str:
    """Complete a supported observability task before the dispatcher spawns a worker."""
    return _complete_task(task_id, parsed, profile_dir)


def _complete_task(task_id: str, parsed: Any, profile_dir: str) -> str:
    from hermes_cli import kanban_db as kb

    try:
        result = run_gateway_cpu_memory_query(profile_dir=profile_dir)
        summary = "国际短信 gateway production 最近 10 分钟 CPU/内存查询完成"
        metadata = {"fastpath": "intlsms_gateway_cpu_memory", "source_profile": "observability"}
    except Exception as exc:  # noqa: BLE001 - complete task with a visible failure
        result = (
            "国际短信 gateway production 最近 10 分钟 CPU/内存查询失败。\n\n"
            f"- task: {task_id}\n"
            f"- error: {type(exc).__name__}: {str(exc)[:300]}"
        )
        summary = "国际短信 gateway production 最近 10 分钟 CPU/内存查询失败"
        metadata = {"fastpath": "intlsms_gateway_cpu_memory", "error": type(exc).__name__}

    with kb.connect_closing() as conn:
        kb.complete_task(conn, task_id, result=result, summary=summary, metadata=metadata)
    return result


def run_gateway_cpu_memory_query(*, profile_dir: str) -> str:
    env = _load_env(Path(profile_dir) / ".env")
    cfg = _load_config(Path(profile_dir) / "config.yaml", env)
    target = _resolve_prometheus_target(cfg)

    end = int(time.time())
    start = end - 10 * 60
    cpu = _query_range(target, CPU_QUERY, start=start, end=end, step="60s")
    memory = _query_range(target, MEMORY_QUERY, start=start, end=end, step="60s")

    cpu_rows = _summarize(cpu, scale=1000.0)
    mem_rows = _summarize(memory, scale=1 / 1024 / 1024)
    return _format_result(cpu_rows, mem_rows)


def _load_env(path: Path) -> dict[str, str]:
    env = dict(os.environ)
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        env[key.strip()] = value
    return env


def _expand(value: Any, env: dict[str, str]) -> Any:
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return env.get(value[2:-1], "")
    if isinstance(value, dict):
        return {k: _expand(v, env) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v, env) for v in value]
    return value


def _load_config(path: Path, env: dict[str, str]) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return _expand(data, env)


def _resolve_prometheus_target(cfg: dict[str, Any]) -> dict[str, Any]:
    block = ((cfg.get("observability") or {}).get("prometheus") or {})
    for target in block.get("targets") or []:
        if target.get("category") == "intlsms" and target.get("env") == "prod":
            base_url = str(target.get("base_url") or "").strip()
            if not base_url:
                raise RuntimeError("observability.prometheus intlsms-prod base_url is empty")
            return target
    raise RuntimeError("observability.prometheus intlsms-prod target not found")


def _query_range(target: dict[str, Any], query: str, *, start: int, end: int, step: str) -> dict[str, Any]:
    base_url = str(target.get("base_url") or "").rstrip("/")
    params = urllib.parse.urlencode(
        {"query": query, "start": str(start), "end": str(end), "step": step}
    )
    req = urllib.request.Request(f"{base_url}/api/v1/query_range?{params}", method="GET")
    req.add_header("Accept", "application/json")
    token = str(target.get("token") or "").strip()
    if token:
        scheme = str(target.get("auth_scheme") or "Bearer").strip()
        req.add_header("Authorization", f"{scheme} {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = yaml.safe_load(resp.read().decode("utf-8")) or {}
    if body.get("status") != "success":
        raise RuntimeError(str(body.get("error") or body)[:500])
    return body


def _summarize(body: dict[str, Any], *, scale: float) -> list[SeriesSummary]:
    rows: list[SeriesSummary] = []
    for item in ((body.get("data") or {}).get("result") or []):
        pod = str((item.get("metric") or {}).get("pod") or "unknown")
        values = []
        for pair in item.get("values") or []:
            try:
                values.append(float(pair[1]) * scale)
            except (TypeError, ValueError, IndexError):
                continue
        if not values:
            continue
        rows.append(
            SeriesSummary(
                pod=pod,
                current=values[-1],
                avg=statistics.fmean(values),
                max=max(values),
            )
        )
    return sorted(rows, key=lambda x: x.pod)


def _format_result(cpu: list[SeriesSummary], memory: list[SeriesSummary]) -> str:
    lines = [
        "国际短信生产环境 gateway 服务最近 10 分钟 CPU 和内存使用情况：",
        "",
        "CPU（mCore）：",
    ]
    if cpu:
        lines.extend(
            f"- {r.pod}: 当前 {r.current:.1f}, 平均 {r.avg:.1f}, 最大 {r.max:.1f}"
            for r in cpu
        )
    else:
        lines.append("- 未查询到 gateway pod CPU 数据")

    lines.extend(["", "内存（MiB）："])
    if memory:
        lines.extend(
            f"- {r.pod}: 当前 {r.current:.1f}, 平均 {r.avg:.1f}, 最大 {r.max:.1f}"
            for r in memory
        )
    else:
        lines.append("- 未查询到 gateway pod 内存数据")

    cpu_spike = any(r.max > max(r.avg * 2, r.current * 1.8, 100.0) for r in cpu)
    mem_spike = any(r.max > max(r.avg * 1.3, r.current * 1.2) for r in memory)
    conclusion = "未发现明显 CPU 或内存尖峰。"
    if cpu_spike or mem_spike:
        parts = []
        if cpu_spike:
            parts.append("CPU 有尖峰")
        if mem_spike:
            parts.append("内存有尖峰")
        conclusion = "发现" + "、".join(parts) + "，建议继续查看对应 pod 日志和发布变更。"
    lines.extend(["", f"结论：{conclusion}"])
    return "\n".join(lines)
