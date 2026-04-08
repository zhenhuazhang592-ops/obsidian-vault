#!/usr/bin/env python3
"""
new_project.py — huage888 新项目初始化脚本

用法：
  # 新建项目（完整结构）
  python3 scripts/new_project.py --name 断桥奇遇 --episode S01E01 --project 漠玫传

  # 新建项目（复用已有 Visual Bible）
  python3 scripts/new_project.py --name 断桥奇遇 --episode S01E01 --project 漠玫传 \
    --visual-bible config/visual-bible.md

  # 仅打印结构，不创建
  python3 scripts/new_project.py --name 断桥奇遇 --dry-run

  # 列出已有项目
  python3 scripts/new_project.py --list

自动创建项目结构（参考 CLAUDE.md 启动前检查规则）：
  projects/{集数名}/
  ├── CLAUDE.md        ← 复制根目录 CLAUDE.md
  ├── config/
  │   └── visual-bible.md  ← 复制全局或指定 VB
  ├── assets/          ← 空目录
  ├── outputs/         ← 空目录
  ├── docs/            ← 原始剧本存放目录（剧本放这里）
  └── .gitignore       ← Python/Node产物忽略规则
"""

import argparse
import os
import shutil
import sys
from datetime import date
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
PROJECTS_DIR = BASE_DIR / "projects"
GLOBAL_CLAUDE = BASE_DIR / "CLAUDE.md"
GLOBAL_VB = BASE_DIR / "config" / "visual-bible.md"


def _mkdir(path: Path) -> None:
    """创建目录（已存在不报错）"""
    path.mkdir(parents=True, exist_ok=True)


def _copy(src: Path, dst: Path, force: bool = False) -> bool:
    """复制文件（src 存在才复制）"""
    if not src.exists():
        return False
    if dst.exists() and not force:
        return False
    _mkdir(dst.parent)
    shutil.copy2(src, dst)
    return True


def create_project(
    name: str,
    episode: str,
    project: str,
    visual_bible: Path | None = None,
    dry_run: bool = False,
) -> Path | None:
    """
    创建新项目结构。

    Args:
        name:        项目名称（如 "断桥奇遇"）
        episode:     集数标识（如 "S01E01"）
        project:     所属项目名（如 "漠玫传"）
        visual_bible: Visual Bible 路径（默认使用全局 config/visual-bible.md）
        dry_run:     仅打印，不创建

    Returns:
        项目根目录路径，或 None（dry_run）
    """
    project_root = PROJECTS_DIR / name

    if project_root.exists() and not dry_run:
        print(f"[ERROR] 项目目录已存在：{project_root}")
        print(f"  提示：换一个项目名称，或先删除旧目录")
        return None

    # 解析集数文件夹名
    episode_dir = project_root
    if dry_run:
        episode_dir = Path(f"[dry-run] projects/{name}")

    if dry_run:
        print(f"\n[DRY RUN] 将创建以下结构：")
    else:
        print(f"\n创建项目：{project} · {episode} · {name}")
        print(f"目录：{episode_dir.relative_to(BASE_DIR) if episode_dir.is_relative_to(BASE_DIR) else episode_dir}")

    # ── 目录结构 ─────────────────────────────────────────────────
    dirs = {
        "config":     episode_dir / "config",
        "assets":     episode_dir / "assets",
        "outputs":    episode_dir / "outputs",
        "docs":       episode_dir / "docs",
    }

    for label, d in dirs.items():
        if dry_run:
            print(f"  + {d.relative_to(BASE_DIR) if d.is_relative_to(BASE_DIR) else d}/")
        else:
            _mkdir(d)
            print(f"  ✅ {label}/")

    # ── CLAUDE.md ─────────────────────────────────────────────────
    if dry_run:
        print(f"  + {GLOBAL_CLAUDE.relative_to(BASE_DIR)} → {episode_dir}/CLAUDE.md")
    else:
        if _copy(GLOBAL_CLAUDE, episode_dir / "CLAUDE.md"):
            print(f"  ✅ CLAUDE.md（复制根目录）")
        else:
            print(f"  ⚠️  CLAUDE.md 未复制（源文件不存在）")

    # ── Visual Bible ─────────────────────────────────────────────
    vb_src = visual_bible or GLOBAL_VB
    if dry_run:
        print(f"  + {vb_src.relative_to(BASE_DIR)} → {episode_dir}/config/visual-bible.md")
    else:
        if _copy(vb_src, episode_dir / "config" / "visual-bible.md"):
            print(f"  ✅ config/visual-bible.md（复制全局）")
        else:
            print(f"  ⚠️  Visual Bible 未复制（源文件不存在，跳过）")

    # ── .gitignore ───────────────────────────────────────────────
    gitignore = episode_dir / ".gitignore"
    if not dry_run:
        gitignore.write_text(
            "# Python\n__pycache__/\n*.pyc\n*.pyo\n.huage888/\n*.egg-info/\n\n"
            "# Node\nnode_modules/\n\n"
            "# 资产和输出（按需提交）\nassets/library/\noutputs/*\n!outputs/.gitkeep\n\n"
            "# 环境变量\n.env\n.env.local\n",
            encoding="utf-8",
        )
        print(f"  ✅ .gitignore")

    # ── outputs/.gitkeep ─────────────────────────────────────────
    if not dry_run:
        outputs_gitkeep = episode_dir / "outputs" / ".gitkeep"
        if not outputs_gitkeep.exists():
            outputs_gitkeep.write_text("", encoding="utf-8")

    # ── README.md ───────────────────────────────────────────────
    readme = episode_dir / "README.md"
    if not dry_run:
        readme.write_text(
            f"# {name} · {episode}\n\n"
            f"> 项目：{project} · 创建日期：{date.today().isoformat()}\n\n"
            f"## 目录结构\n\n"
            f"| 目录 | 用途 |\n"
            f"|------|------|\n"
            f"| `config/` | Visual Bible |\n"
            f"| `docs/` | 原始剧本 |\n"
            f"| `assets/` | 本集资产（manifest.json）|\n"
            f"| `outputs/` | 本集输出（大纲/分镜/视频）|\n\n"
            f"## 执行命令\n\n"
            f"```bash\n"
            f"# 完整流水线\n"
            f"python3 scripts/run_episode_pipeline.py \\\n"
            f"  --script docs/剧本.md \\\n"
            f"  --episode {episode} \\\n"
            f"  --project {project}\n\n"
            f"# 或分步执行\n"
            f"python3 scripts/run_episode_pipeline.py --episode {episode} --skip-outline\n"
            f"```\n",
            encoding="utf-8",
        )
        print(f"  ✅ README.md")

    # ── 剧本占位符 ─────────────────────────────────────────────
    script_placeholder = episode_dir / "docs" / "README.md"
    if not dry_run:
        script_placeholder.write_text(
            "# 原始剧本存放目录\n\n"
            "将剧本文件（如 `剧本.md`）放在这里，然后执行：\n\n"
            "```bash\n"
            "python3 scripts/run_episode_pipeline.py \\\n"
            f"  --script docs/剧本.md \\\n"
            f"  --episode {episode} \\\n"
            f"  --project {project}\n"
            "```\n",
            encoding="utf-8",
        )

    print()
    if dry_run:
        print(f"[DRY RUN] 上述结构将会被创建（加 --dry-run 仅预览）")
        return None
    else:
        rel = episode_dir.relative_to(BASE_DIR) if episode_dir.is_relative_to(BASE_DIR) else episode_dir
        print(f"✅ 项目创建完成：{rel}")
        print(f"\n下一步：")
        print(f"  1. 将剧本文件放入 {rel}/docs/")
        print(f"  2. 执行：")
        print(f"     python3 scripts/run_episode_pipeline.py \\")
        print(f"       --script docs/剧本.md \\")
        print(f"       --episode {episode} \\")
        print(f"       --project {project}")
        return episode_dir


def list_projects() -> None:
    """列出已有项目"""
    if not PROJECTS_DIR.exists():
        print("尚无项目目录（projects/）")
        return

    projects = sorted(PROJECTS_DIR.iterdir())
    if not projects:
        print("尚无项目目录")
        return

    print(f"\n已有项目（{len(projects)} 个）：\n")
    for p in projects:
        claude = p / "CLAUDE.md"
        vb = p / "config" / "visual-bible.md"
        readme = p / "README.md"
        date_str = ""
        if readme.exists():
            content = readme.read_text(encoding="utf-8")
            for line in content.splitlines():
                if "创建日期" in line:
                    date_str = line.split("：")[-1].strip()
                    break
        status = []
        if claude.exists(): status.append("CLAUDE")
        if vb.exists(): status.append("VB")
        status_str = " | ".join(status) if status else "空目录"
        print(f"  📁 {p.name}  {status_str}  {date_str}")


# ── CLI ─────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="huage888 新项目初始化")
    parser.add_argument("--list", action="store_true", help="列出已有项目")
    parser.add_argument("--name", help="项目名称（文件夹名，如 断桥奇遇）")
    parser.add_argument("--episode", default="S01E01", help="集数标识（默认 S01E01）")
    parser.add_argument("--project", default="", help="所属项目名（如 漠玫传）")
    parser.add_argument(
        "--visual-bible",
        type=Path,
        default=None,
        help="Visual Bible 路径（默认使用 config/visual-bible.md）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览结构，不创建文件",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.list:
        list_projects()
        sys.exit(0)

    if not args.name:
        print("错误：缺少 --name 参数\n")
        print("用法：")
        print("  新建项目：python3 scripts/new_project.py --name 断桥奇遇 --episode S01E01 --project 漠玫传")
        print("  预览结构：python3 scripts/new_project.py --name 断桥奇遇 --dry-run")
        print("  列出已有：python3 scripts/new_project.py --list")
        sys.exit(1)

    # 目录不存在时提示
    if not PROJECTS_DIR.exists():
        print(f"[INFO] 创建项目根目录：{PROJECTS_DIR.relative_to(BASE_DIR)}")
        _mkdir(PROJECTS_DIR)

    project_path = create_project(
        name=args.name,
        episode=args.episode,
        project=args.project,
        visual_bible=args.visual_bible,
        dry_run=args.dry_run,
    )
    sys.exit(0 if project_path is not None or args.dry_run else 1)
