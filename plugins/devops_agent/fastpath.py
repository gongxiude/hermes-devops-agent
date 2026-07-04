"""Deterministic DevOps routing fast paths.

These handlers run before the LLM gateway dispatch. They are intentionally
narrow: when a common Feishu observability request is fully inferable, create
the Kanban task directly and skip the model. This prevents prompt/tool loops
from blocking routine production observation queries.
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

_CPU_MEM_RE = re.compile(r"(cpu|CPU).*(内存|memory)|(?:内存|memory).*(cpu|CPU)")
_WINDOW_10M_RE = re.compile(r"(近|最近)\s*10\s*分钟|last[_\s-]*10[_\s-]*min", re.IGNORECASE)
_GATEWAY_RE = re.compile(r"\bgateway\b|gateway\s*服务", re.IGNORECASE)
_INTLSMS_RE = re.compile(r"国际短信|intl-?sms|intlsms", re.IGNORECASE)
_PROD_RE = re.compile(r"生产环境|线上|prod(?:uction)?", re.IGNORECASE)
_FEISHU_CHAT_RE = re.compile(r"^(oc_|ou_)[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class ObservabilityFastPath:
    service: str
    domain: str
    environment: str
    request_type: str
    window: str
    original_request: str


def parse_observability_fastpath(text: str) -> Optional[ObservabilityFastPath]:
    """Parse the routine intlsms gateway CPU/memory observation request."""
    raw = (text or "").strip()
    if not raw:
        return None
    if not _INTLSMS_RE.search(raw):
        return None
    if not _GATEWAY_RE.search(raw):
        return None
    if not _PROD_RE.search(raw):
        return None
    if not _WINDOW_10M_RE.search(raw):
        return None
    if not _CPU_MEM_RE.search(raw):
        return None
    return ObservabilityFastPath(
        service="gateway",
        domain="intlsms",
        environment="production",
        request_type="metrics_cpu_memory",
        window="last_10_minutes",
        original_request=raw,
    )


def _source_chat_id(event: Any) -> Optional[str]:
    source = getattr(event, "source", None)
    chat_id = getattr(source, "chat_id", "") or ""
    chat_id = str(chat_id).strip()
    if _FEISHU_CHAT_RE.match(chat_id):
        return chat_id
    return None


def _source_user_id(event: Any) -> str:
    source = getattr(event, "source", None)
    return str(getattr(source, "user_id", "") or "feishu").strip() or "feishu"


def _source_platform(event: Any) -> str:
    source = getattr(event, "source", None)
    platform = getattr(source, "platform", "") or ""
    return str(getattr(platform, "value", platform) or "").strip().lower()


def _create_task(
    parsed: ObservabilityFastPath,
    *,
    chat_id: str,
    actor: str,
    session_id: str = "",
    message_id: str = "",
) -> str:
    from hermes_cli import kanban_db as kb

    body = "\n".join(
        [
            f"actor: {actor}",
            f"service: {parsed.service}",
            f"domain: {parsed.domain}",
            f"environment: {parsed.environment}",
            f"request_type: {parsed.request_type}",
            f"window: {parsed.window}",
            f"original_request: {parsed.original_request}",
            f"reply_target: feishu:{chat_id}",
            "notes: Query CPU and memory metrics for the production intlsms gateway over the last 10 minutes. Return concise values, trend, and abnormal findings.",
        ]
    )
    idempotency_key = f"feishu-message:{message_id}" if message_id else (
        f"feishu:{chat_id}:{parsed.domain}:{parsed.service}:"
        f"{parsed.environment}:{parsed.window}:{parsed.request_type}:{int(time.time() // 300)}"
    )
    with kb.connect_closing() as conn:
        task_id = kb.create_task(
            conn,
            title="国际短信 gateway production last_10_minutes CPU和内存",
            body=body,
            assignee="observability",
            created_by="orchestrator-fastpath",
            tenant=parsed.domain,
            priority=0,
            idempotency_key=idempotency_key,
            max_retries=2,
            initial_status="running",
            session_id=session_id or None,
        )
        kb.add_notify_sub(
            conn,
            task_id=task_id,
            platform="feishu",
            chat_id=chat_id,
            thread_id=None,
            user_id=actor,
            notifier_profile="orchestrator",
        )
    return task_id


async def _send_receipt(gateway: Any, event: Any, task_id: str) -> None:
    source = getattr(event, "source", None)
    adapter = getattr(gateway, "adapters", {}).get(getattr(source, "platform", None))
    if adapter is None:
        return
    try:
        await adapter.send(
            chat_id=getattr(source, "chat_id", ""),
            content=f"已创建观测任务 {task_id}，正在由 observability 查询 CPU 和内存。",
            reply_to=getattr(event, "message_id", None),
            metadata={"notify": True},
        )
    except Exception as exc:
        logger.warning("[fastpath] failed to send Feishu receipt for %s: %s", task_id, exc)


async def _send_result(gateway: Any, event: Any, task_id: str, result: str) -> None:
    source = getattr(event, "source", None)
    adapter = getattr(gateway, "adapters", {}).get(getattr(source, "platform", None))
    if adapter is None:
        return
    try:
        await adapter.send(
            chat_id=getattr(source, "chat_id", ""),
            content=f"观测任务 {task_id} 查询结果：\n\n{result}",
            reply_to=getattr(event, "message_id", None),
            metadata={"notify": True, "task_id": task_id},
        )
    except Exception as exc:
        logger.warning("[fastpath] failed to send Feishu result for %s: %s", task_id, exc)


def maybe_handle_observability_fastpath(
    *,
    event: Any = None,
    gateway: Any = None,
    session_store: Any = None,
) -> Optional[dict]:
    """Create a Kanban task directly for routine Feishu observability queries."""
    if event is None:
        return None
    if _source_platform(event) != "feishu":
        return None
    text = str(getattr(event, "text", "") or "").strip()
    parsed = parse_observability_fastpath(text)
    if parsed is None:
        return None
    chat_id = _source_chat_id(event)
    if not chat_id:
        return None

    session_id = ""
    if session_store is not None:
        try:
            session_id = str(session_store.get_session_id(getattr(event, "source", None)) or "")
        except Exception:
            session_id = ""

    message_id = str(getattr(event, "message_id", "") or "")
    task_id = _create_task(
        parsed,
        chat_id=chat_id,
        actor=_source_user_id(event),
        session_id=session_id,
        message_id=message_id,
    )
    logger.info("[fastpath] created observability task=%s for Feishu request", task_id)

    try:
        from . import observability_fastpath

        result = observability_fastpath.complete(task_id, parsed)
    except Exception as exc:
        logger.warning("[fastpath] failed to start observability completion for %s: %s", task_id, exc)
        result = ""

    if gateway is not None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_send_receipt(gateway, event, task_id))
            if result:
                loop.create_task(_send_result(gateway, event, task_id, result))
        except RuntimeError:
            pass

    return {
        "action": "skip",
        "reason": f"[fastpath] created observability task {task_id}",
        "task_id": task_id,
    }
