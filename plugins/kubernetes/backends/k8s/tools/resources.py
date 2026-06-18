"""Read-only Kubernetes resource tools (get / yaml / describe / logs / events).

Dependencies (catalog / selectors / runner / safeguards) are injected by the
backend's ``build(cfg)``. The cluster is selected from the prompt via the
shared selectors; the kubectl runner enforces the read-verb allowlist. Handlers
obey the four rules: ``(args, **kwargs) -> str``, always JSON, never raise.
"""

from __future__ import annotations

from typing import Any, Dict, List


def build_specs(cfg, *, section, backend, catalog, selectors, runner, safeguards) -> List[Dict[str, Any]]:
    sel_props = selectors.selector_properties(section, backend, cfg)
    sg = safeguards

    def _resolve(args: Dict[str, Any]):
        return catalog.resolve(
            selectors.extract_selectors(args), backend, section,
            require=["kubeconfig", "context"],
        )

    def _check() -> bool:
        try:
            return bool(catalog.targets(section, backend))
        except Exception:  # noqa: BLE001
            return False

    # -- k8s_get_resources -------------------------------------------------
    def handle_get(args: Dict[str, Any], **_: Any) -> str:
        rt = str(args.get("resource_type") or "").strip()
        if not sg.safe_token(rt):
            return sg.err("resource_type is required and must be a valid kubectl type")
        name = str(args.get("name") or "").strip()
        if name and not sg.safe_token(name):
            return sg.err(f"invalid resource name: {name!r}")
        output = str(args.get("output") or "").strip()
        if not sg.allowed_output(output):
            return sg.err("output must be one of: wide, json, yaml, name")
        selector = str(args.get("label_selector") or "").strip()
        if selector and not sg.safe_label_selector(selector):
            return sg.err(f"invalid label_selector: {selector!r}")
        try:
            target = _resolve(args)
        except catalog.CatalogError as exc:
            return sg.err(str(exc))

        kargs: List[str] = ["get", rt]
        if name:
            kargs.append(name)
        if str(args.get("all_namespaces") or "").lower() in {"true", "1", "yes"} or args.get("all_namespaces") is True:
            kargs.append("-A")
        else:
            ns = sg.resolve_namespace(args, target)
            if ns:
                if not sg.safe_namespace(ns):
                    return sg.err(f"invalid namespace: {ns!r}")
                kargs += ["-n", ns]
        if output:
            kargs += ["-o", output]
        if selector:
            kargs += ["-l", selector]
        return sg.finalize(target, runner.run_kubectl(target, *kargs))

    # -- k8s_get_resource_yaml --------------------------------------------
    def handle_yaml(args: Dict[str, Any], **_: Any) -> str:
        rt = str(args.get("resource_type") or "").strip()
        name = str(args.get("name") or "").strip()
        if not sg.safe_token(rt) or not sg.safe_token(name):
            return sg.err("resource_type and name are required and must be valid")
        if sg.is_secret_type(rt):
            return sg.err("secret contents are not exposed; use k8s_get_resources for names only")
        try:
            target = _resolve(args)
        except catalog.CatalogError as exc:
            return sg.err(str(exc))
        kargs = ["get", rt, name, "-o", "yaml"]
        ns = sg.resolve_namespace(args, target)
        if ns:
            if not sg.safe_namespace(ns):
                return sg.err(f"invalid namespace: {ns!r}")
            kargs += ["-n", ns]
        return sg.finalize(target, runner.run_kubectl(target, *kargs))

    # -- k8s_describe_resource --------------------------------------------
    def handle_describe(args: Dict[str, Any], **_: Any) -> str:
        rt = str(args.get("resource_type") or "").strip()
        name = str(args.get("name") or "").strip()
        if not sg.safe_token(rt) or not sg.safe_token(name):
            return sg.err("resource_type and name are required and must be valid")
        try:
            target = _resolve(args)
        except catalog.CatalogError as exc:
            return sg.err(str(exc))
        kargs = ["describe", rt, name]
        ns = sg.resolve_namespace(args, target)
        if ns:
            if not sg.safe_namespace(ns):
                return sg.err(f"invalid namespace: {ns!r}")
            kargs += ["-n", ns]
        return sg.finalize(target, runner.run_kubectl(target, *kargs))

    # -- k8s_get_pod_logs --------------------------------------------------
    def handle_logs(args: Dict[str, Any], **_: Any) -> str:
        pod = str(args.get("pod") or "").strip()
        if not sg.safe_token(pod):
            return sg.err("pod is required and must be a valid pod name")
        container = str(args.get("container") or "").strip()
        if container and not sg.safe_token(container):
            return sg.err(f"invalid container: {container!r}")
        try:
            tail = int(args.get("tail") or 200)
        except (TypeError, ValueError):
            tail = 200
        tail = max(1, min(tail, 5000))
        try:
            target = _resolve(args)
        except catalog.CatalogError as exc:
            return sg.err(str(exc))
        kargs = ["logs", pod, f"--tail={tail}"]
        ns = sg.resolve_namespace(args, target)
        if ns:
            if not sg.safe_namespace(ns):
                return sg.err(f"invalid namespace: {ns!r}")
            kargs += ["-n", ns]
        if container:
            kargs += ["-c", container]
        if str(args.get("previous") or "").lower() in {"true", "1", "yes"} or args.get("previous") is True:
            kargs.append("--previous")
        return sg.finalize(target, runner.run_kubectl(target, *kargs, timeout=45))

    # -- k8s_get_events ----------------------------------------------------
    def handle_events(args: Dict[str, Any], **_: Any) -> str:
        try:
            target = _resolve(args)
        except catalog.CatalogError as exc:
            return sg.err(str(exc))
        kargs = ["get", "events", "--sort-by=.metadata.creationTimestamp"]
        if str(args.get("all_namespaces") or "").lower() in {"true", "1", "yes"} or args.get("all_namespaces") is True:
            kargs.append("-A")
        else:
            ns = sg.resolve_namespace(args, target)
            if ns:
                if not sg.safe_namespace(ns):
                    return sg.err(f"invalid namespace: {ns!r}")
                kargs += ["-n", ns]
        return sg.finalize(target, runner.run_kubectl(target, *kargs))

    base = dict(toolset="kubernetes", requires_env=["KUBECONFIG_READONLY_PROD"], check_fn=_check)

    get_schema = {
        "name": "k8s_get_resources",
        "description": (
            "在指定集群上 kubectl get 资源(只读)。按业务线/环境/集群选择集群;命名空间默认取该集群配置,"
            "可用 namespace 覆盖或 all_namespaces=true。用于列资源、看状态。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "resource_type": {"type": "string", "description": "资源类型,如 pods/deployments/svc/nodes"},
                "name": {"type": "string", "description": "可选,具体资源名"},
                "namespace": {"type": "string", "description": "可选,命名空间(默认取集群配置)"},
                "all_namespaces": {"type": "boolean", "description": "可选,跨所有命名空间(-A)"},
                "output": {"type": "string", "description": "可选输出格式", "enum": ["wide", "json", "yaml", "name"]},
                "label_selector": {"type": "string", "description": "可选,标签选择器 -l(如 app=api)"},
                **sel_props,
            },
            "required": ["resource_type"],
        },
    }
    yaml_schema = {
        "name": "k8s_get_resource_yaml",
        "description": "获取某个资源的完整 YAML(只读)。Secret 内容不暴露。集群选择同 k8s_get_resources。",
        "parameters": {
            "type": "object",
            "properties": {
                "resource_type": {"type": "string", "description": "资源类型"},
                "name": {"type": "string", "description": "资源名"},
                "namespace": {"type": "string", "description": "可选,命名空间"},
                **sel_props,
            },
            "required": ["resource_type", "name"],
        },
    }
    describe_schema = {
        "name": "k8s_describe_resource",
        "description": "kubectl describe 某资源(事件、状态、调度信息,只读)。集群选择同 k8s_get_resources。",
        "parameters": {
            "type": "object",
            "properties": {
                "resource_type": {"type": "string", "description": "资源类型"},
                "name": {"type": "string", "description": "资源名"},
                "namespace": {"type": "string", "description": "可选,命名空间"},
                **sel_props,
            },
            "required": ["resource_type", "name"],
        },
    }
    logs_schema = {
        "name": "k8s_get_pod_logs",
        "description": "获取 Pod 日志(只读)。集群选择同 k8s_get_resources。",
        "parameters": {
            "type": "object",
            "properties": {
                "pod": {"type": "string", "description": "Pod 名"},
                "namespace": {"type": "string", "description": "可选,命名空间"},
                "container": {"type": "string", "description": "可选,容器名(多容器 Pod)"},
                "tail": {"type": "integer", "description": "可选,尾部行数(默认 200,上限 5000)"},
                "previous": {"type": "boolean", "description": "可选,上一个已崩溃容器的日志"},
                **sel_props,
            },
            "required": ["pod"],
        },
    }
    events_schema = {
        "name": "k8s_get_events",
        "description": "获取命名空间事件(按时间排序,只读),排障首选。集群选择同 k8s_get_resources。",
        "parameters": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string", "description": "可选,命名空间(默认取集群配置)"},
                "all_namespaces": {"type": "boolean", "description": "可选,所有命名空间"},
                **sel_props,
            },
        },
    }

    return [
        {**base, "name": "k8s_get_resources", "schema": get_schema, "handler": handle_get,
         "description": "K8s 资源查询(多集群只读)", "emoji": "📦"},
        {**base, "name": "k8s_get_resource_yaml", "schema": yaml_schema, "handler": handle_yaml,
         "description": "K8s 资源 YAML(多集群只读)", "emoji": "📄"},
        {**base, "name": "k8s_describe_resource", "schema": describe_schema, "handler": handle_describe,
         "description": "K8s describe(多集群只读)", "emoji": "🔍"},
        {**base, "name": "k8s_get_pod_logs", "schema": logs_schema, "handler": handle_logs,
         "description": "K8s Pod 日志(多集群只读)", "emoji": "📜"},
        {**base, "name": "k8s_get_events", "schema": events_schema, "handler": handle_events,
         "description": "K8s 事件(多集群只读)", "emoji": "📅"},
    ]
