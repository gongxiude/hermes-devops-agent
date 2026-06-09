from __future__ import annotations

import http.server
import json
import os
import subprocess
import sys
import threading
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "mcp-servers/devops-observe/intlsms_runner.py"
MCP_SERVER = ROOT / "mcp-servers/devops-observe/devops_observe_mcp.py"


def run_cmd(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=ROOT,
        env=run_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_dry_run_json_report() -> None:
    result = run_cmd("--dry-run")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["profile"] == "observability-query"
    assert payload["service_domain"] == "intlsms"
    assert payload["environment"] == "prod"
    assert payload["audit"]["policy_decision"] == "allow_readonly"
    assert payload["evidence"]


def test_dry_run_test_environment_report() -> None:
    result = run_cmd("--dry-run", "--environment", "test")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["environment"] == "test"
    assert payload["namespace"] == "intl-test"
    assert payload["cluster"] == "test-aliyun-zjk-intlsms"


def test_output_dir_writes_report_and_audit(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"
    result = run_cmd("--dry-run", "--output-dir", str(output_dir))
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "written"
    report_json = Path(payload["paths"]["report_json"])
    report_md = Path(payload["paths"]["report_markdown"])
    audit_json = Path(payload["paths"]["audit_json"])
    assert report_json.exists()
    assert report_md.exists()
    assert audit_json.exists()
    report = json.loads(report_json.read_text(encoding="utf-8"))
    audit = json.loads(audit_json.read_text(encoding="utf-8"))
    assert report["correlation_id"] == payload["correlation_id"]
    assert audit["correlation_id"] == payload["correlation_id"]
    assert "国际短信运行巡检报告" in report_md.read_text(encoding="utf-8")


def test_mutation_action_denied() -> None:
    result = run_cmd("--dry-run", "--action", "restart")
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "denied"
    assert payload["audit"]["policy_decision"] == "deny_mutation"


def test_window_over_limit_denied() -> None:
    result = run_cmd("--dry-run", "--window", "3h")
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert "window_denied" in payload["reason"]


def test_live_missing_endpoints_degrades_to_unknown() -> None:
    result = run_cmd(
        env={
            "OBSERVE_PROMETHEUS_BASE_URL_PROD": "",
            "OBSERVE_LOKI_BASE_URL_PROD": "",
            "KUBECTL_BIN_PROD": "/missing/kubectl",
        }
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["overall_status"] == "unknown"
    assert payload["audit"]["failures"]
    assert any(item["source"] == "prometheus" for item in payload["audit"]["failures"])
    assert any(item["source"] == "loki" for item in payload["audit"]["failures"])
    assert any(item["source"] == "kubernetes" for item in payload["audit"]["failures"])


def test_live_kubectl_readonly_summary(tmp_path: Path) -> None:
    fake_kubectl = tmp_path / "kubectl"
    fake_kubectl.write_text(
        """#!/usr/bin/env python3
import json
print(json.dumps({
  "kind": "Deployment",
  "spec": {"replicas": 2},
  "status": {"replicas": 2, "readyReplicas": 2, "availableReplicas": 2, "unavailableReplicas": 0}
}))
""",
        encoding="utf-8",
    )
    fake_kubectl.chmod(0o755)
    result = run_cmd(
        env={
            "OBSERVE_PROMETHEUS_BASE_URL_PROD": "",
            "OBSERVE_LOKI_BASE_URL_PROD": "",
            "KUBECTL_BIN_PROD": str(fake_kubectl),
        }
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    k8s = [item for item in payload["evidence"] if item["source"] == "kubernetes"]
    assert k8s
    assert all(item["status"] == "healthy" for item in k8s)
    assert all("replicas=2" in item["summary"] for item in k8s)


def test_live_prometheus_loki_values_drive_risk(tmp_path: Path) -> None:
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            query = params.get("query", [""])[0]
            if parsed.path == "/api/v1/query":
                if "restarts_total" in query:
                    value = "4"
                elif "phase!=\"Running\"" in query:
                    value = "0"
                else:
                    value = "1"
                body = {
                    "status": "success",
                    "data": {
                        "resultType": "vector",
                        "result": [{"metric": {"pod": "gateway-abc"}, "value": [0, value]}],
                    },
                }
            elif parsed.path == "/loki/api/v1/query_range":
                if "panic" in query.lower():
                    result = [{"stream": {"pod": "gateway-abc"}, "values": [["0", "panic: boom"]]}]
                else:
                    result = []
                body = {"status": "success", "data": {"resultType": "streams", "result": result}}
            else:
                self.send_response(404)
                self.end_headers()
                return
            payload = json.dumps(body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_args: object) -> None:
            return

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    fake_kubectl = tmp_path / "kubectl"
    fake_kubectl.write_text(
        """#!/usr/bin/env python3
import json
print(json.dumps({
  "kind": "Deployment",
  "spec": {"replicas": 1},
  "status": {"replicas": 1, "readyReplicas": 1, "availableReplicas": 1, "unavailableReplicas": 0}
}))
""",
        encoding="utf-8",
    )
    fake_kubectl.chmod(0o755)
    try:
        base_url = f"http://127.0.0.1:{server.server_port}"
        result = run_cmd(
            env={
                "OBSERVE_PROMETHEUS_BASE_URL_PROD": base_url,
                "OBSERVE_LOKI_BASE_URL_PROD": base_url,
                "KUBECTL_BIN_PROD": str(fake_kubectl),
            }
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["overall_status"] == "critical"
    restart_evidence = [item for item in payload["evidence"] if item["query"] == "restarts"]
    panic_evidence = [item for item in payload["evidence"] if item["query"] == "panics"]
    assert restart_evidence
    assert all(item["status"] == "critical" for item in restart_evidence)
    assert panic_evidence
    assert all(item["status"] == "critical" for item in panic_evidence)


def test_minimal_mcp_tools_list_and_call() -> None:
    messages = "\n".join(
        [
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "readonly_guard_check",
                        "arguments": {"action": "restart"},
                    },
                }
            ),
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "intlsms_runtime_inspection",
                        "arguments": {"actor": "pytest", "environment": "prod", "dry_run": True},
                    },
                }
            ),
            "",
        ]
    )
    result = subprocess.run(
        [sys.executable, str(MCP_SERVER)],
        cwd=ROOT,
        input=messages,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    responses = [json.loads(line) for line in result.stdout.splitlines()]
    assert responses[1]["result"]["tools"][0]["name"] == "intlsms_runtime_inspection"
    guard = responses[2]["result"]["structuredContent"]
    assert guard["allowed"] is False
    assert guard["policy_decision"] == "deny_mutation"
    report = responses[3]["result"]["structuredContent"]
    assert report["profile"] == "observability-query"
    assert report["audit"]["policy_decision"] == "allow_readonly"
