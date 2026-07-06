#!/usr/bin/env python3
"""把 repo 根 skills/ 的 canonical 通用方法论 skill 物理复制进各 distribution。

背景：hermes 的 `profile install/update` 会拒绝 distribution 内的任何软连接
（hermes_cli/profile_distribution.py::_reject_distribution_symlinks）。因此
"一份真源、多处复用" 只能用物理拷贝（vendoring），不能用 symlink。

真源唯一放在 repo 根 skills/<name>/（不在任何 distribution.yaml 目录内，install
扫不到）。本脚本按 skills/skills-map.yaml 把需要的 skill 复制进
distributions/<dist>/skills/<name>/。

用法：
  python scripts/sync-shared-skills.py          # 同步（写入拷贝）
  python scripts/sync-shared-skills.py --check   # 只校验拷贝与真源一致，不写入
                                                 # 有漂移/缺失则非零退出（用于 CI）
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML：pip install pyyaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL = REPO_ROOT / "skills"
MAP_FILE = CANONICAL / "skills-map.yaml"
PROFILE_LINKS = CANONICAL / "profile-links"
DISTRIBUTIONS = REPO_ROOT / "distributions"


def load_map() -> dict[str, list[str]]:
    data = yaml.safe_load(MAP_FILE.read_text(encoding="utf-8")) or {}
    dists = data.get("distributions") or {}
    if not isinstance(dists, dict):
        sys.exit(f"{MAP_FILE} 的 distributions 必须是 mapping")
    return {str(d): list(skills or []) for d, skills in dists.items()}


def load_profile_links() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    if not PROFILE_LINKS.is_dir():
        return result
    canonical_root = CANONICAL.resolve()
    for profile_dir in sorted(p for p in PROFILE_LINKS.iterdir() if p.is_dir()):
        skills: list[str] = []
        for link in sorted(profile_dir.iterdir()):
            if not link.is_symlink():
                sys.exit(f"profile-links 只允许软链接：{link}")
            target = link.resolve()
            if not target.is_dir() or not (target / "SKILL.md").is_file():
                sys.exit(f"profile-links 指向的 skill 无效：{link} -> {target}")
            if target.parent != canonical_root:
                sys.exit(f"profile-links 必须指向 repo 根 skills/<name>：{link} -> {target}")
            skills.append(target.name)
        result[profile_dir.name] = skills
    return result


GITIGNORE_BEGIN = "# >>> vendored-skills (auto-managed by scripts/sync-shared-skills.py) >>>"
GITIGNORE_END = "# <<< vendored-skills <<<"


def update_gitignore(vendored_paths: list[str]) -> None:
    """把 vendored 拷贝路径写进 .gitignore 的受管块（保持 git 单一真源）。

    仅在真 repo 根（存在 .git）时执行；Docker 构建的 /opt 下无 .git，跳过，
    避免产生游离的 .gitignore。
    """
    if not (REPO_ROOT / ".git").exists():
        return
    gitignore = REPO_ROOT / ".gitignore"
    block = "\n".join([GITIGNORE_BEGIN, *sorted(vendored_paths), GITIGNORE_END])
    text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if GITIGNORE_BEGIN in text and GITIGNORE_END in text:
        head = text[: text.index(GITIGNORE_BEGIN)]
        tail = text[text.index(GITIGNORE_END) + len(GITIGNORE_END):]
        new_text = f"{head}{block}{tail}"
    else:
        sep = "" if text.endswith("\n") or not text else "\n"
        new_text = f"{text}{sep}\n{block}\n"
    if new_text != text:
        gitignore.write_text(new_text, encoding="utf-8")
        print(f"  gitignore  已更新受管块（{len(vendored_paths)} 条 vendored 路径）")


def dir_identical(a: Path, b: Path) -> bool:
    """递归比较两个目录内容是否完全一致。"""
    if not b.exists():
        return False
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
        return False
    for sub in cmp.common_dirs:
        if not dir_identical(a / sub, b / sub):
            return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="只校验拷贝是否与真源一致，不写入；有漂移则非零退出")
    args = ap.parse_args()

    mapping = load_map()
    for dist, linked_skills in load_profile_links().items():
        current = mapping.setdefault(dist, [])
        for skill in linked_skills:
            if skill not in current:
                current.append(skill)
    drift: list[str] = []
    vendored: list[str] = []
    synced = 0

    for dist, skills in mapping.items():
        dist_skills = DISTRIBUTIONS / dist / "skills"
        if not (DISTRIBUTIONS / dist).is_dir():
            sys.exit(f"distribution 不存在：{dist}")
        for skill in skills:
            src = CANONICAL / skill
            if not (src / "SKILL.md").is_file():
                sys.exit(f"真源缺失或不含 SKILL.md：{src}")
            dst = dist_skills / skill
            vendored.append(f"distributions/{dist}/skills/{skill}/")

            if args.check:
                if not dir_identical(src, dst):
                    drift.append(f"{dist}/skills/{skill}")
                continue

            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            synced += 1
            print(f"  synced  {dist}/skills/{skill}  ← skills/{skill}")

    if args.check:
        if drift:
            print("拷贝与真源不一致（请运行 sync-shared-skills.py 重新同步）：")
            for d in drift:
                print(f"  DRIFT  {d}")
            return 1
        print("✅ 所有 vendored 拷贝与真源一致")
        return 0

    update_gitignore(vendored)
    print(f"✅ 同步完成，共 {synced} 个 skill 拷贝")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
