from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_server_test(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(path), "--test"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_local_mcp_servers_smoke() -> None:
    servers = [
        ROOT / "mcp-servers/prometheus/src/server.py",
        ROOT / "mcp-servers/k8s/src/server.py",
        ROOT / "mcp-servers/loki/src/server.py",
        ROOT / "mcp-servers/argocd/src/server.py",
        ROOT / "mcp-servers/git-codeup/src/server.py",
        ROOT / "mcp-servers/aliyun/src/server.py",
    ]
    for path in servers:
        result = run_server_test(path)
        assert result.returncode == 0, f"{path} failed: {result.stderr}"
        assert "Status" in result.stdout


def test_jenkins_remote_mcp_example_exists() -> None:
    example = ROOT / "mcp-servers/jenkins/mcp.json.example"
    readme = ROOT / "mcp-servers/jenkins/README.md"
    assert example.exists()
    assert readme.exists()
    assert "streamable_http" in example.read_text(encoding="utf-8")
