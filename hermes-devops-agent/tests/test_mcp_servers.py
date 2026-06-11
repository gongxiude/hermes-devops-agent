from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


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
        ROOT / "mcp-servers/git-workspace/src/server.py",
        ROOT / "mcp-servers/release-gate/src/server.py",
        ROOT / "mcp-servers/release-executor/src/server.py",
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


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    original_path = list(sys.path)
    original_module = sys.modules.get(name)
    original_utils = sys.modules.get("utils")
    sys.path.insert(0, str(path.parent))
    sys.modules[name] = module
    sys.modules.pop("utils", None)
    try:
        spec.loader.exec_module(module)
    finally:
        if original_module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = original_module
        if original_utils is None:
            sys.modules.pop("utils", None)
        else:
            sys.modules["utils"] = original_utils
        sys.path = original_path
    return module


def test_git_workspace_repo_contract_and_path_boundary() -> None:
    utils = load_module("git_workspace_utils_test", ROOT / "mcp-servers/git-workspace/src/utils.py")

    with tempfile.TemporaryDirectory() as tmpdir, patch.dict(
        os.environ,
        {"GIT_WORKSPACE_ROOT": tmpdir, "GIT_WORKSPACE_CHECK_COMMANDS": '{"yuexin-infra":["make validate"]}'},
    ):
        utils.Config.WORKSPACE_ROOT = tmpdir
        utils.Config.CHECK_COMMANDS_JSON = os.environ["GIT_WORKSPACE_CHECK_COMMANDS"]

        repos = utils.repos()
        assert repos["jenkins-pipeline"].remote == (
            "git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/jenkins-pipeline.git"
        )
        assert repos["jenkins-pipeline"].branch == "master"
        assert repos["yuexin-infra"].remote == (
            "git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/yuexin-infra.git"
        )
        assert repos["yuexin-infra"].kind == "gitops-kubernetes-infra"

        assert utils.allowed_check_commands("yuexin-infra") == [["make", "validate"]]
        assert utils.worktree_path("yuexin-infra", "../../escape").is_relative_to(Path(tmpdir).resolve())

        try:
            utils.repo_spec("unknown")
        except RuntimeError as exc:
            assert "unknown repo prefix" in str(exc)
        else:
            raise AssertionError("unknown repo prefix should be rejected")


def test_git_workspace_builtin_checks_match_target_repo_shapes() -> None:
    server = load_module("git_workspace_server_test", ROOT / "mcp-servers/git-workspace/src/server.py")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        yuexin = root / "yuexin"
        for rel in [
            "Makefile",
            "bin/generate-argo",
            "bin/validate-conf",
            "bin/yaml-lint",
            "deploy/manifest.yaml",
            "workloads",
        ]:
            path = yuexin / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        yuexin_results = server._builtin_checks("yuexin-infra", yuexin)
        assert all(item["returncode"] == 0 for item in yuexin_results)

        jenkins = root / "jenkins"
        for rel in [
            "README.md",
            "jenkinsfiles",
            "jobs",
            "share-library/vars",
            "share-library/resources",
            "share-library/vars/argoDeploy.groovy",
        ]:
            path = jenkins / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if "." in path.name:
                path.write_text("", encoding="utf-8")
            else:
                path.mkdir(exist_ok=True)
        jenkins_results = server._builtin_checks("jenkins-pipeline", jenkins)
        assert all(item["returncode"] == 0 for item in jenkins_results)


def test_git_workspace_defaults_to_mirror_branch_ref() -> None:
    server = load_module("git_workspace_server_base_ref_test", ROOT / "mcp-servers/git-workspace/src/server.py")

    with patch.object(server, "mirror_path", return_value=Path("/tmp/mirrors/yuexin-infra.git")), patch.object(
        server, "worktree_path", return_value=Path("/tmp/worktrees/yuexin-infra/task")
    ), patch.object(server, "run_checked", return_value={"returncode": 0, "stdout": "", "stderr": ""}) as run_checked:
        server.git_workspace_create_worktree("yuexin-infra", "task", "codex/test")

    assert run_checked.call_args.args[0][-1] == "master"


def test_release_gate_allows_only_complete_approved_supported_scope() -> None:
    server = load_module("release_gate_server_test", ROOT / "mcp-servers/release-gate/src/server.py")

    allow = server.release_gate_decide(
        actor="ou_x",
        repo_prefix="yuexin-infra",
        environment="prod",
        action="argocd_sync",
        change_reference="cr-123",
        approval_id="approval-1",
        ticket_id="ticket-1",
        post_check_plan="check ArgoCD app health and workload rollout status",
    )
    assert allow["allow"] is True
    assert allow["execution_note"] == "decision only; execution tools are not exposed by this MCP server"

    deny = server.release_gate_decide(
        actor="ou_x",
        repo_prefix="other",
        environment="prod",
        action="argocd_sync",
        change_reference="cr-123",
        approval_id="",
        ticket_id="ticket-1",
        post_check_plan="check health",
    )
    assert deny["allow"] is False
    assert any("repo_prefix is not allowed" in reason for reason in deny["reasons"])
    assert any("approval_id" in reason for reason in deny["reasons"])


def test_release_executor_fails_closed_until_enabled() -> None:
    with patch.dict(os.environ, {"RELEASE_EXECUTION_ENABLED": "false"}):
        utils = load_module("release_executor_utils_closed_test", ROOT / "mcp-servers/release-executor/src/utils.py")

    decision = utils.decide_scope(
        actor="ou_x",
        repo_prefix="yuexin-infra",
        environment="prod",
        action="argocd_sync",
        change_reference="cr-123",
        approval_id="approval-1",
        ticket_id="ticket-1",
        post_check_plan="check health",
    )
    assert decision["allow"] is False
    assert "RELEASE_EXECUTION_ENABLED is not true" in decision["reasons"]


def test_release_executor_build_and_sync_construct_approved_requests() -> None:
    env = {
        "RELEASE_EXECUTION_ENABLED": "true",
        "JENKINS_BASE_URL": "https://jenkins.example",
        "JENKINS_USER": "svc",
        "JENKINS_API_TOKEN": "token",
        "ARGOCD_API_URL": "https://argocd.example",
        "ARGOCD_AUTH_TOKEN": "argocd-token",
    }
    with patch.dict(os.environ, env):
        server = load_module("release_executor_server_test", ROOT / "mcp-servers/release-executor/src/server.py")

    calls = []

    def fake_request_json(**kwargs):
        calls.append(kwargs)
        return {"status": 200, "body": {"ok": True}}

    with patch.object(server, "request_json", side_effect=fake_request_json):
        jenkins = server.release_execute_jenkins_build(
            actor="ou_x",
            repo_prefix="jenkins-pipeline",
            environment="prod",
            change_reference="cr-123",
            approval_id="approval-1",
            ticket_id="ticket-1",
            post_check_plan="check Jenkins build and ArgoCD health",
            job_name="folder/deploy",
            parameters_json='{"BRANCH":"master"}',
        )
        sync = server.release_execute_argocd_sync(
            actor="ou_x",
            repo_prefix="yuexin-infra",
            environment="prod",
            change_reference="cr-123",
            approval_id="approval-1",
            ticket_id="ticket-1",
            post_check_plan="check ArgoCD app health",
            application="intlsms",
            revision="master",
        )

    assert jenkins["decision"]["allow"] is True
    assert sync["decision"]["allow"] is True
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == "https://jenkins.example/job/folder/job/deploy/buildWithParameters?BRANCH=master"
    assert calls[1]["url"] == "https://argocd.example/api/v1/applications/intlsms/sync"
    assert calls[1]["body"]["revision"] == "master"
