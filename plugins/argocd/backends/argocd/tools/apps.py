"""ArgoCD application/project/settings tools (read-only).

Dependencies (catalog / selectors / client) are injected by the backend's
``build``. The ArgoCD instance is picked by ``env`` (single control plane);
``category`` / ``dest_cluster`` / ``project`` filter *applications*. Handlers
obey the four rules: ``(args, **kwargs) -> str``, always JSON, never raise.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

_TOOLSET = "argocd"
_REQUIRES_ENV = ["ARGOCD_SERVER"]
_DUMP_LIMIT = 60000


def _err(message: str) -> str:
    return json.dumps({"status": "error", "error": message}, ensure_ascii=False)


def _dump(target: Dict[str, Any], obj: Any) -> str:
    if isinstance(obj, dict):
        obj.setdefault("instance", target.get("id"))
    text = json.dumps(obj, ensure_ascii=False)
    if len(text) > _DUMP_LIMIT:
        text = text[:_DUMP_LIMIT] + '...[truncated]"}'
    return text


def build_specs(cfg, *, catalog, selectors, load, require, label, client) -> List[Dict[str, Any]]:
    candidates, _ = load(cfg)
    inst_props = selectors.instance_properties(candidates)

    def _resolve(args: Dict[str, Any]):
        cands, defaults = load(None)
        return catalog.resolve(
            selectors.extract_instance(args), cands,
            defaults=defaults, require=require, label=label,
        )

    def _check() -> bool:
        try:
            cands, _ = load(None)
            return bool(cands)
        except Exception:  # noqa: BLE001
            return False

    def _instance(args):
        try:
            return _resolve(args), None
        except catalog.CatalogError as exc:
            return None, _err(str(exc))

    def handle_list_apps(args: Dict[str, Any], **_: Any) -> str:
        target, err = _instance(args)
        if err:
            return err
        body = client.list_applications(target, project=args.get("project"), repo=args.get("repo"))
        summary = client.summarize_apps(
            body, dest_cluster=args.get("dest_cluster"), category=args.get("category"),
        )
        return _dump(target, summary)

    def handle_get_app(args: Dict[str, Any], **_: Any) -> str:
        name = str(args.get("name") or "").strip()
        if not name:
            return _err("name (application name) is required")
        target, err = _instance(args)
        if err:
            return err
        return _dump(target, client.get_application(target, name, app_namespace=args.get("app_namespace")))

    def handle_get_project(args: Dict[str, Any], **_: Any) -> str:
        name = str(args.get("name") or "").strip()
        if not name:
            return _err("name (project name) is required")
        target, err = _instance(args)
        if err:
            return err
        return _dump(target, client.get_project(target, name))

    def handle_settings(args: Dict[str, Any], **_: Any) -> str:
        target, err = _instance(args)
        if err:
            return err
        return _dump(target, client.settings(target))

    def handle_version(args: Dict[str, Any], **_: Any) -> str:
        target, err = _instance(args)
        if err:
            return err
        return _dump(target, client.version(target))

    base = dict(toolset=_TOOLSET, requires_env=_REQUIRES_ENV, check_fn=_check)

    list_schema = {
        "name": "argocd_list_applications",
        "description": (
            "列出 ArgoCD 应用及其 sync/health 状态(只读,精简摘要)。可按 project / 目标集群 "
            "dest_cluster / 业务线 category 过滤。GitOps 排障与发布状态查看首选。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "可选,ArgoCD project 过滤"},
                "dest_cluster": {"type": "string", "description": "可选,按目标集群名/URL 过滤(客户端)"},
                "category": {"type": "string", "description": "可选,按应用 category 标签过滤(客户端)"},
                "repo": {"type": "string", "description": "可选,按仓库 URL 过滤"},
                **inst_props,
            },
        },
    }
    get_app_schema = {
        "name": "argocd_get_application",
        "description": "获取单个 ArgoCD 应用的完整详情(spec/status/资源树/sync 历史,只读)。",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "应用名"},
                "app_namespace": {"type": "string", "description": "可选,应用所在命名空间"},
                **inst_props,
            },
            "required": ["name"],
        },
    }
    get_proj_schema = {
        "name": "argocd_get_project",
        "description": "获取单个 ArgoCD project 的定义(允许的源/目标/集群范围,只读)。",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "project 名"}, **inst_props},
            "required": ["name"],
        },
    }
    settings_schema = {
        "name": "argocd_get_settings",
        "description": "获取 ArgoCD 实例设置(只读)。",
        "parameters": {"type": "object", "properties": {**inst_props}},
    }
    version_schema = {
        "name": "argocd_get_version",
        "description": "获取 ArgoCD 版本信息(只读)。",
        "parameters": {"type": "object", "properties": {**inst_props}},
    }

    return [
        {**base, "name": "argocd_list_applications", "schema": list_schema, "handler": handle_list_apps,
         "description": "ArgoCD 应用列表+状态(只读)", "emoji": "🚦"},
        {**base, "name": "argocd_get_application", "schema": get_app_schema, "handler": handle_get_app,
         "description": "ArgoCD 应用详情(只读)", "emoji": "🔎"},
        {**base, "name": "argocd_get_project", "schema": get_proj_schema, "handler": handle_get_project,
         "description": "ArgoCD project 详情(只读)", "emoji": "🗂️"},
        {**base, "name": "argocd_get_settings", "schema": settings_schema, "handler": handle_settings,
         "description": "ArgoCD 设置(只读)", "emoji": "⚙️"},
        {**base, "name": "argocd_get_version", "schema": version_schema, "handler": handle_version,
         "description": "ArgoCD 版本(只读)", "emoji": "🏷️"},
    ]
