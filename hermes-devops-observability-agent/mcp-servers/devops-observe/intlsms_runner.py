from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


AGENT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = AGENT_ROOT / "skills/devops/domain-governance/domains/intlsms-runtime-inspection.yaml"
MUTATION_WORDS = {
    "restart",
    "rollback",
    "scale",
    "sync",
    "apply",
    "patch",
    "delete",
    "db_change",
    "exec",
    "rollout",
}
WINDOW_RE = re.compile(r"^(?P<value>\d+)(?P<unit>[smhd])$")
WINDOW_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


@dataclass(frozen=True)
class ToolCall:
    tool: str
    query_name: str
    service: str
    status: str
    summary: str


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def render_template(template: str, values: dict[str, str]) -> str:
    result = template
    for key, value in values.items():
        result = result.replace("{{" + key + "}}", value)
    return result


def make_correlation_id(service_domain: str, window: str) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha1(f"{service_domain}:{window}:{now}".encode()).hexdigest()[:8]
    return f"insp-{now}-{suffix}"


def assert_readonly(action: str) -> None:
    normalized = re.sub(r"[^a-z_]+", "_", action.lower()).strip("_")
    if normalized in MUTATION_WORDS:
        raise PermissionError(f"mutation_denied: action={normalized}")


def duration_to_seconds(value: str) -> int:
    match = WINDOW_RE.match(value)
    if not match:
        raise ValueError(f"invalid duration: {value}")
    return int(match.group("value")) * WINDOW_SECONDS[match.group("unit")]


def assert_window_allowed(window: str, max_window: str) -> None:
    if duration_to_seconds(window) > duration_to_seconds(max_window):
        raise PermissionError(f"window_denied: window={window} max_window={max_window}")


def prometheus_get(base_url: str, path: str, params: dict[str, str], timeout: int) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    url = base_url.rstrip("/") + path + "?" + query
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if payload.get("status") != "success":
        raise RuntimeError(f"prometheus error: {payload.get('error') or payload}")
    return payload


def loki_get(base_url: str, params: dict[str, str], timeout: int) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    url = base_url.rstrip("/") + "/loki/api/v1/query_range?" + query
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if payload.get("status") != "success":
        raise RuntimeError(f"loki error: {payload.get('error') or payload}")
    return payload


def safe_name(value: str, field: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
        raise ValueError(f"invalid {field}: {value}")
    return value


def kubectl_get_json(kind: str, name: str, namespace: str, timeout: int = 10) -> dict[str, Any]:
    kubectl_bin = os.environ.get("KUBECTL_BIN", "kubectl")
    kubeconfig = os.environ.get("KUBECONFIG_READONLY") or os.environ.get("KUBECONFIG")
    command = [
        kubectl_bin,
        "get",
        safe_name(kind.lower(), "kind"),
        safe_name(name, "name"),
        "-n",
        safe_name(namespace, "namespace"),
        "-o",
        "json",
    ]
    if kubeconfig:
        command[1:1] = ["--kubeconfig", kubeconfig]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"kubectl get failed: {result.returncode}")
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise RuntimeError("kubectl returned non-object JSON")
    return payload


def summarize_kubernetes_workload(payload: dict[str, Any]) -> tuple[str, str]:
    status_obj = payload.get("status") or {}
    spec_obj = payload.get("spec") or {}
    replicas = int(spec_obj.get("replicas") or status_obj.get("replicas") or 0)
    ready = int(status_obj.get("readyReplicas") or 0)
    available = int(status_obj.get("availableReplicas") or 0)
    unavailable = int(status_obj.get("unavailableReplicas") or 0)
    if replicas == 0:
        return "critical", "replicas=0"
    if unavailable > 0 or available < replicas or ready < replicas:
        return "warning", f"replicas={replicas} ready={ready} available={available} unavailable={unavailable}"
    return "healthy", f"replicas={replicas} ready={ready} available={available}"


def dry_value(service: str, query_name: str) -> float:
    seed = int(hashlib.sha1(f"{service}:{query_name}".encode()).hexdigest()[:6], 16)
    if query_name == "availability":
        return 1.0
    if query_name == "restarts":
        return float(seed % 2)
    if query_name == "pod_phase":
        return 0.0
    if query_name == "panics":
        return 0.0
    if query_name == "errors":
        return float(seed % 3)
    return float(seed % 100) / 100.0


def classify_numeric(query_spec: dict[str, Any], value: float) -> str:
    critical = query_spec.get("critical_threshold")
    warn = query_spec.get("warn_threshold", query_spec.get("warn_threshold_bytes"))
    if critical is not None and value >= float(critical):
        return "critical"
    if warn is not None and value >= float(warn):
        return "warning"
    if query_spec.get("severity_if_zero") and value <= 0:
        return str(query_spec["severity_if_zero"])
    if query_spec.get("severity_if_present") and value > 0:
        return str(query_spec["severity_if_present"])
    return "healthy"


def prometheus_numeric_values(payload: dict[str, Any]) -> list[float]:
    result = payload.get("data", {}).get("result", [])
    values: list[float] = []
    if not isinstance(result, list):
        return values
    for item in result:
        if not isinstance(item, dict):
            continue
        value = item.get("value")
        if isinstance(value, list) and len(value) >= 2:
            try:
                values.append(float(value[1]))
            except (TypeError, ValueError):
                pass
        matrix_values = item.get("values")
        if isinstance(matrix_values, list):
            for sample in matrix_values:
                if isinstance(sample, list) and len(sample) >= 2:
                    try:
                        values.append(float(sample[1]))
                    except (TypeError, ValueError):
                        pass
    return values


def summarize_prometheus_payload(query_spec: dict[str, Any], payload: dict[str, Any]) -> tuple[str, str]:
    values = prometheus_numeric_values(payload)
    value = max(values) if values else 0.0
    status = classify_numeric(query_spec, value)
    return status, f"max={value:g} series={len(payload.get('data', {}).get('result', []))}"


def summarize_loki_payload(query_spec: dict[str, Any], payload: dict[str, Any]) -> tuple[str, str]:
    streams = payload.get("data", {}).get("result", [])
    if not isinstance(streams, list):
        return "unknown", "invalid loki result"
    entries = 0
    for stream in streams:
        if isinstance(stream, dict) and isinstance(stream.get("values"), list):
            entries += len(stream["values"])
    status = classify_numeric(query_spec, float(entries))
    return status, f"streams={len(streams)} entries={entries}"


def inspect(config: dict[str, Any], *, dry_run: bool, action: str, actor: str, window: str) -> dict[str, Any]:
    assert_readonly(action)
    assert_window_allowed(window, str(config["inspection"]["max_window"]))
    profile = str(config["profile"])
    domain = config["service_domain"]["name"]
    namespace = str(config["service_domain"]["production_namespace"])
    cluster = str(config["service_domain"]["production_cluster"])
    correlation_id = make_correlation_id(domain, window)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    evidence: list[dict[str, Any]] = []
    tool_calls: list[ToolCall] = []
    failures: list[dict[str, str]] = []

    prometheus_base_url = os.environ.get("OBSERVE_PROMETHEUS_BASE_URL", "")
    loki_base_url = os.environ.get("OBSERVE_LOKI_BASE_URL", "")
    for service in config["services"]:
        service_name = service["name"]
        values = {
            "namespace": namespace,
            "workload": service["workload"],
            "window": window,
        }
        for query_name, query_spec in config["queries"]["prometheus"].items():
            promql = render_template(query_spec["promql"], values)
            if dry_run:
                value = dry_value(service_name, query_name)
                status = classify_numeric(query_spec, value)
                summary = f"dry-run value={value:g}"
            elif not prometheus_base_url:
                status = "unknown"
                summary = "missing OBSERVE_PROMETHEUS_BASE_URL"
                failures.append({"source": "prometheus", "query": query_name, "service": service_name, "reason": summary})
            else:
                try:
                    payload = prometheus_get(
                        prometheus_base_url,
                        "/api/v1/query",
                        {"query": promql},
                        timeout=10,
                    )
                    status, summary = summarize_prometheus_payload(query_spec, payload)
                except Exception as exc:
                    status = "unknown"
                    summary = f"prometheus query failed: {exc}"
                    failures.append({"source": "prometheus", "query": query_name, "service": service_name, "reason": str(exc)})
            tool_calls.append(ToolCall("devops-observe:prometheus_query", query_name, service_name, status, summary))
            evidence.append(
                {
                    "source": "prometheus",
                    "service": service_name,
                    "query": query_name,
                    "promql": promql,
                    "status": status,
                    "summary": summary,
                }
            )
        for query_name, query_spec in config["queries"]["loki"].items():
            logql = render_template(query_spec["logql"], values)
            if dry_run:
                value = dry_value(service_name, query_name)
                status = classify_numeric(query_spec, value)
                summary = "dry-run no matching logs" if value == 0 else f"dry-run matches={int(value)}"
            elif not loki_base_url:
                status = "unknown"
                summary = "missing OBSERVE_LOKI_BASE_URL"
                failures.append({"source": "loki", "query": query_name, "service": service_name, "reason": summary})
            else:
                try:
                    payload = loki_get(
                        loki_base_url,
                        {"query": logql, "limit": str(query_spec.get("limit", 20))},
                        timeout=10,
                    )
                    status, summary = summarize_loki_payload(query_spec, payload)
                except Exception as exc:
                    status = "unknown"
                    summary = f"loki query failed: {exc}"
                    failures.append({"source": "loki", "query": query_name, "service": service_name, "reason": str(exc)})
            tool_calls.append(ToolCall("devops-observe:loki_query_range", query_name, service_name, status, summary))
            evidence.append(
                {
                    "source": "loki",
                    "service": service_name,
                    "query": query_name,
                    "logql": logql,
                    "status": status,
                    "summary": summary,
                }
            )
        if dry_run:
            k8s_status = "healthy"
            k8s_summary = f"dry-run {service['kind']}/{service['workload']} readable in namespace {namespace}"
        else:
            try:
                payload = kubectl_get_json(str(service["kind"]), str(service["workload"]), namespace)
                k8s_status, k8s_summary = summarize_kubernetes_workload(payload)
            except Exception as exc:
                k8s_status = "unknown"
                k8s_summary = f"kubernetes read failed: {exc}"
                failures.append({"source": "kubernetes", "query": "workload_status", "service": service_name, "reason": str(exc)})
        tool_calls.append(ToolCall("devops-observe:k8s_get", "workload_status", service_name, k8s_status, k8s_summary))
        evidence.append(
            {
                "source": "kubernetes",
                "service": service_name,
                "query": "workload_status",
                "resource": f"{service['kind']}/{service['workload']}",
                "status": k8s_status,
                "summary": k8s_summary,
            }
        )

    statuses = [item["status"] for item in evidence]
    if "critical" in statuses:
        overall = "critical"
    elif "warning" in statuses:
        overall = "warning"
    elif "unknown" in statuses:
        overall = "unknown"
    elif statuses:
        overall = "healthy"
    else:
        overall = "unknown"

    risks = [
        {
            "service": item["service"],
            "level": item["status"],
            "evidence": f"{item['source']}:{item['query']}",
            "summary": item["summary"],
        }
        for item in evidence
        if item["status"] in {"warning", "critical", "unknown"}
    ]
    next_actions = [
        "人工复核 warning/critical 证据对应服务的近期发布和业务影响",
        "若出现 critical，转 incident-triage profile 做故障初诊",
        "任何 restart/rollback/scale/sync 请求必须进入审批或 break-glass 流程",
    ]
    audit = {
        "correlation_id": correlation_id,
        "actor": actor,
        "profile": profile,
        "service_domain": domain,
        "environment": "prod",
        "cluster": cluster,
        "namespace": namespace,
        "autonomy": ["observe", "recommend"],
        "policy_decision": "allow_readonly",
        "dry_run": dry_run,
        "tool_calls": [call.__dict__ for call in tool_calls],
        "failures": failures,
        "created_at": now,
    }
    return {
        "correlation_id": correlation_id,
        "profile": profile,
        "service_domain": domain,
        "environment": "prod",
        "cluster": cluster,
        "namespace": namespace,
        "window": window,
        "max_window": str(config["inspection"]["max_window"]),
        "overall_status": overall,
        "evidence": evidence,
        "risks": risks,
        "next_actions": next_actions,
        "audit": audit,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 国际短信运行巡检报告",
        "",
        f"- correlation_id: `{report['correlation_id']}`",
        f"- profile: `{report['profile']}`",
        f"- cluster: `{report['cluster']}`",
        f"- namespace: `{report['namespace']}`",
        f"- window: `{report['window']}`",
        f"- overall_status: `{report['overall_status']}`",
        "",
        "## 风险",
    ]
    if report["risks"]:
        for risk in report["risks"]:
            lines.append(f"- `{risk['level']}` {risk['service']} {risk['evidence']}: {risk['summary']}")
    else:
        lines.append("- 未发现 warning/critical 风险。")
    lines.extend(["", "## 下一步动作"])
    for action in report["next_actions"]:
        lines.append(f"- {action}")
    lines.extend(["", "## 证据摘要"])
    for item in report["evidence"]:
        lines.append(f"- {item['source']} `{item['service']}` `{item['query']}`: {item['status']}，{item['summary']}")
    return "\n".join(lines) + "\n"


def write_outputs(report: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    correlation_id = safe_name(str(report["correlation_id"]), "correlation_id")
    report_json = output_dir / f"{correlation_id}.report.json"
    report_md = output_dir / f"{correlation_id}.report.md"
    audit_json = output_dir / f"{correlation_id}.audit.json"
    report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_md.write_text(render_markdown(report), encoding="utf-8")
    audit_json.write_text(json.dumps(report["audit"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "report_json": str(report_json),
        "report_markdown": str(report_md),
        "audit_json": str(audit_json),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run intlsms read-only runtime inspection.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--window", default="15m")
    parser.add_argument("--actor", default="cron:intlsms-runtime-inspection")
    parser.add_argument("--action", default="inspect")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        report = inspect(config, dry_run=args.dry_run, action=args.action, actor=args.actor, window=args.window)
    except (PermissionError, ValueError) as exc:
        denial = {
            "status": "denied",
            "reason": str(exc),
            "action": args.action,
            "audit": {
                "actor": args.actor,
                "policy_decision": "deny_mutation",
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            },
        }
        print(json.dumps(denial, ensure_ascii=False, indent=2))
        return 2

    if args.output_dir:
        paths = write_outputs(report, args.output_dir)
        print(json.dumps({"status": "written", "correlation_id": report["correlation_id"], "paths": paths}, ensure_ascii=False, indent=2))
    elif args.format == "markdown":
        print(render_markdown(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
