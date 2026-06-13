from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    required_files = [
        ROOT / "distribution.yaml",
        ROOT / "config.yaml",
        ROOT / "SOUL.md",
        ROOT / "mcp.json",
        ROOT / ".env.EXAMPLE",
        ROOT / "README.md",
        ROOT / "skills/devops/catalog.yaml",
        ROOT / "skills/devops/specs/profiles/gitops-agent.yaml",
        ROOT / "skills/devops/specs/subagents/jenkins-pipeline.yaml",
        ROOT / "skills/devops/specs/subagents/argocd.yaml",
        ROOT / "skills/devops/specs/subagents/gitops.yaml",
    ]
    for path in required_files:
        assert path.exists(), f"missing gitops-agent file: {path}"

    print("gitops_agent_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())