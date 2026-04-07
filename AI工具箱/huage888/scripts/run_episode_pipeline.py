#!/usr/bin/env python3
"""run_episode_pipeline.py — Multi-Agent 委托链编排脚本

用法：
  # 完整流水线（大纲 + 分镜）
  python3 scripts/run_episode_pipeline.py \
    --script docs/剧本.md \
    --episode S01E01 \
    --project 漠玫传

  # 仅 P0，跳过大纲（直接生成分镜）
  python3 scripts/run_episode_pipeline.py \
    --episode S01E01 \
    --skip-outline

  # 完整流水线 + P1 + P2
  python3 scripts/run_episode_pipeline.py \
    --script docs/剧本.md \
    --episode S01E01 \
    --project 漠玫传 \
    --run-p1 --run-p2

  # dry-run（不调用 API）
  python3 scripts/run_episode_pipeline.py \
    --episode S01E01 \
    --dry-run
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── 路径配置 ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
QWEN_PIPELINE = BASE_DIR / "config" / "qwen_pipeline.py"
VALIDATE_OUTLINE = BASE_DIR / "scripts" / "validate_outline.py"
CHECK_ASSET = BASE_DIR / "scripts" / "check_asset_consistency.py"
GENERATE_SHOTS = BASE_DIR / "scripts" / "generate_shot_images.py"
BATCH_PIPELINE = BASE_DIR / "scripts" / "batch_image_pipeline.py"


# ── 辅助函数 ───────────────────────────────────────────────────────────────

def extract_json_from_markdown(path: Path) -> dict:
    """从 Markdown 提取 ```json ``` 块内容"""
    content = path.read_text(encoding="utf-8")
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError(f"Markdown 中未找到 JSON 块: {path}")
    return json.loads(match.group(1).strip())


def call_qwen(
    agent: str,
    user: str,
    output_path: Path,
    asset_library: bool = False,
    dry_run: bool = False,
) -> subprocess.CompletedProcess | None:
    """调用 qwen_pipeline.py --agent"""
    cmd = [
        sys.executable,
        str(QWEN_PIPELINE),
        "--agent", agent,
        "--user", user,
        "--output", str(output_path),
    ]
    if asset_library:
        cmd.append("--asset-library")

    print(f"\n{'[DRY] ' if dry_run else ''}→ qwen_pipeline --agent {agent}")
    print(f"    输出: {output_path.resolve().relative_to(BASE_DIR.resolve())}")

    if dry_run:
        print(f"    [DRY] prompt 前80字: {user[:80]}...")
        return None

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [FAIL] qwen_pipeline --agent {agent} 失败", file=sys.stderr)
        print(f"    stderr: {result.stderr[:500]}", file=sys.stderr)
        return None

    print(f"    [OK] {agent} 完成")
    return result


def validate_outline(path: Path) -> bool:
    """调用 validate_outline.py 校验大纲"""
    cmd = [sys.executable, str(VALIDATE_OUTLINE), str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [WARN] outline 校验未通过（非阻断）")
        print(f"    {result.stdout[:300]}", file=sys.stderr)
        return False
    print(f"    [OK] outline 校验通过")
    return True


def check_asset_consistency(path: Path) -> bool:
    """调用 check_asset_consistency.py 校验分镜"""
    cmd = [sys.executable, str(CHECK_ASSET), str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [WARN] 分镜资产一致性校验未通过（非阻断）")
        print(f"    {result.stdout[:300]}", file=sys.stderr)
        return False
    print(f"    [OK] 分镜资产一致性校验通过")
    return True


# ── Stage 函数 ─────────────────────────────────────────────────────────────

def stage1_outline(
    script_arg: str | None,
    episode: str,
    project: str,
    output_dir: Path,
    asset_library: bool,
    dry_run: bool,
) -> Path | None:
    """Stage 1: outline-agent 生成大纲"""
    outline_dir = output_dir / episode
    outline_dir.mkdir(parents=True, exist_ok=True)
    outline_path = outline_dir / f"{episode}-outline.md"

    # 读取剧本内容
    if script_arg:
        script_path = Path(script_arg)
        if script_path.exists() and script_path.is_file():
            script_content = script_path.read_text(encoding="utf-8")
        else:
            script_content = script_arg  # 视作直接传入的剧本文本
    else:
        if dry_run:
            script_content = "[剧本内容占位 - dry-run 模式]"
        else:
            print("[ERROR] 请提供 --script 参数（剧本文件路径）")
            return None

    # 追加任务说明
    user_prompt = (
        f"项目：{project}，集数：{episode}\n\n"
        f"以下是原始剧本内容，请生成结构化大纲：\n\n"
        f"{script_content}"
    )

    result = call_qwen(
        agent="outline",
        user=user_prompt,
        output_path=outline_path,
        asset_library=asset_library,
        dry_run=dry_run,
    )
    if result is None and not dry_run:
        return None

    # 校验（dry-run 跳过）
    if not dry_run:
        validate_outline(outline_path)

    return outline_path


def stage2_storyboard(
    outline_path: Path,
    episode: str,
    project: str,
    output_dir: Path,
    asset_library: bool,
    dry_run: bool,
) -> Path | None:
    """Stage 2: storyboard-agent 生成分镜"""
    # 读取 outline JSON 并提取关键信息
    try:
        outline_json = extract_json_from_markdown(outline_path)
    except Exception as e:
        print(f"    [WARN] 无法解析 outline JSON: {e}，使用原始文件内容")
        outline_json = None

    # 构建 user prompt：注入 outline 关键信息
    if outline_json:
        chars = [c["name"] for c in outline_json.get("characters", [])]
        scenes = [s["name"] for s in outline_json.get("scenes", [])]
        props = [p["name"] for p in outline_json.get("props", [])]
        outline_summary = f"""基于以下大纲 JSON 生成分镜列表：

## 大纲摘要
- 集数：{episode}
- 项目：{project}
- 标题：{outline_json.get('title', '')}
- 情绪曲线：{outline_json.get('emotionalCurve', '')}

## 资产清单
- 角色（{len(chars)}个）：{', '.join(chars)}
- 场景（{len(scenes)}个）：{', '.join(scenes)}
- 道具（{len(props)}个）：{', '.join(props)}

## keyEvents
{chr(10).join('- ' + e for e in outline_json.get('keyEvents', []))}

## 完整大纲 JSON
```json
{json.dumps(outline_json, ensure_ascii=False, indent=2)}
```
"""
    else:
        # fallback: 直接传递文件内容
        if dry_run:
            outline_summary = (
                f"基于以下 outline.md 生成分镜列表：\n\n"
                f"[outline 文件内容占位 - dry-run 模式]"
            )
        else:
            outline_summary = (
                f"基于以下 outline.md 生成分镜列表：\n\n"
                f"{outline_path.read_text(encoding='utf-8')}"
            )

    shots_dir = output_dir / episode
    shots_dir.mkdir(parents=True, exist_ok=True)
    shots_path = shots_dir / f"{episode}-shots.md"

    result = call_qwen(
        agent="storyboard",
        user=outline_summary,
        output_path=shots_path,
        asset_library=asset_library,
        dry_run=dry_run,
    )
    if result is None and not dry_run:
        return None

    # 校验（dry-run 跳过）
    if not dry_run:
        check_asset_consistency(shots_path)

    return shots_path


def stage3_p1(
    shots_path: Path,
    outline_path: Path,
    episode: str,
    output_dir: Path,
    dry_run: bool,
) -> bool:
    """Stage 3: P1 — 逐 Shot 图生图"""
    print(f"\n{'[DRY] ' if dry_run else ''}→ Stage 3: P1 逐 Shot 图生图")

    shots_images_dir = output_dir / episode / "shots" / "images"
    shots_images_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(GENERATE_SHOTS),
        "--shots", str(shots_path),
        "--outline", str(outline_path),
        "--output-dir", str(shots_images_dir),
        "--provider", "doubao",
        "--model", "doubao-seedream-4.5",
    ]

    if dry_run:
        print(f"    [DRY] {' '.join(cmd)}")
        return True

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [FAIL] P1 图生图失败: {result.stderr[:300]}", file=sys.stderr)
        return False

    print(f"    [OK] P1 完成 → {shots_images_dir}")
    return True


def stage4_p2(
    shots_path: Path,
    outline_path: Path,
    episode: str,
    output_dir: Path,
    dry_run: bool,
) -> bool:
    """Stage 4: P2 — 宫格批产"""
    print(f"\n{'[DRY] ' if dry_run else ''}→ Stage 4: P2 宫格批产")

    grid_dir = output_dir / episode / "shots" / "grid"
    grid_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(BATCH_PIPELINE),
        "--shots", str(shots_path),
        "--outline", str(outline_path),
        "--rows", "3",
        "--cols", "3",
        "--output-dir", str(grid_dir),
        "--provider", "doubao",
        "--model", "nanobanana",
    ]

    if dry_run:
        print(f"    [DRY] {' '.join(cmd)}")
        return True

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [FAIL] P2 宫格批产失败: {result.stderr[:300]}", file=sys.stderr)
        return False

    print(f"    [OK] P2 完成 → {grid_dir}")
    return True


# ── 主函数 ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent 委托链编排：outline → storyboard → P1 → P2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--script",
        help="剧本文件路径（支持 .md/.txt），或直接传入剧本文本",
    )
    parser.add_argument(
        "--episode",
        required=True,
        help="集数标识，如 S01E01",
    )
    parser.add_argument(
        "--project",
        default="漠玫传",
        help="项目名称",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/",
        help="输出根目录（默认 outputs/）",
    )
    parser.add_argument(
        "--skip-outline",
        action="store_true",
        help="跳过大纲阶段（使用已有 outline 文件）",
    )
    parser.add_argument(
        "--skip-storyboard",
        action="store_true",
        help="跳过分镜阶段（使用已有 shots 文件）",
    )
    parser.add_argument(
        "--run-p1",
        action="store_true",
        help="执行 P1 逐 Shot 图生图",
    )
    parser.add_argument(
        "--run-p2",
        action="store_true",
        help="执行 P2 宫格批产",
    )
    parser.add_argument(
        "--asset-library",
        action="store_true",
        help="调用 Agent 时启用 --asset-library 参数",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="不调用 API，仅打印执行计划",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    print(f"{'='*60}")
    print(f"  Episode Pipeline · {args.episode} · {args.project}")
    print(f"  输出目录: {output_dir}")
    print(f"  阶段: outline({'skip' if args.skip_outline else 'run'}) / "
          f"storyboard({'skip' if args.skip_storyboard else 'run'}) / "
          f"P1({'run' if args.run_p1 else 'skip'}) / "
          f"P2({'run' if args.run_p2 else 'skip'})")
    print(f"{'='*60}")

    # ── Stage 1: outline ────────────────────────────────────────────────
    outline_path: Path | None = None

    if not args.skip_outline:
        print(f"\n[Stage 1] outline-agent")
        outline_path = stage1_outline(
            script_arg=args.script,
            episode=args.episode,
            project=args.project,
            output_dir=output_dir,
            asset_library=args.asset_library,
            dry_run=args.dry_run,
        )
        if outline_path is None and not args.dry_run:
            print("[ERROR] Stage 1 失败，停止执行")
            sys.exit(1)
    else:
        outline_path = output_dir / args.episode / f"{args.episode}-outline.md"
        if not outline_path.exists() and not args.dry_run:
            print(f"[ERROR] --skip-outline 但文件不存在: {outline_path}")
            sys.exit(1)
        print(f"\n[Stage 1] SKIP（使用已有: {outline_path}）")

    if outline_path is None:
        outline_path = output_dir / args.episode / f"{args.episode}-outline.md"

    # ── Stage 2: storyboard ────────────────────────────────────────────
    shots_path: Path | None = None

    if not args.skip_storyboard:
        print(f"\n[Stage 2] storyboard-agent")
        shots_path = stage2_storyboard(
            outline_path=outline_path,
            episode=args.episode,
            project=args.project,
            output_dir=output_dir,
            asset_library=args.asset_library,
            dry_run=args.dry_run,
        )
        if shots_path is None and not args.dry_run:
            print("[ERROR] Stage 2 失败，停止执行")
            sys.exit(1)
    else:
        shots_path = output_dir / args.episode / f"{args.episode}-shots.md"
        if not shots_path.exists() and not args.dry_run:
            print(f"[ERROR] --skip-storyboard 但文件不存在: {shots_path}")
            sys.exit(1)
        print(f"\n[Stage 2] SKIP（使用已有: {shots_path}）")

    if shots_path is None:
        shots_path = output_dir / args.episode / f"{args.episode}-shots.md"

    # ── Stage 3: P1 ─────────────────────────────────────────────────────
    p1_ok = True
    if args.run_p1:
        p1_ok = stage3_p1(
            shots_path=shots_path,
            outline_path=outline_path,
            episode=args.episode,
            output_dir=output_dir,
            dry_run=args.dry_run,
        )

    # ── Stage 4: P2 ─────────────────────────────────────────────────────
    p2_ok = True
    if args.run_p2:
        p2_ok = stage4_p2(
            shots_path=shots_path,
            outline_path=outline_path,
            episode=args.episode,
            output_dir=output_dir,
            dry_run=args.dry_run,
        )

    # ── 汇总 ────────────────────────────────────────────────────────────
    summary = {
        "episode": args.episode,
        "project": args.project,
        "generated_at": datetime.now().isoformat(),
        "stages": {
            "outline": {
                "path": str(outline_path.resolve().relative_to(BASE_DIR.resolve())) if outline_path else None,
                "status": "success" if outline_path else "skipped",
            },
            "storyboard": {
                "path": str(shots_path.resolve().relative_to(BASE_DIR.resolve())) if shots_path else None,
                "status": "success" if shots_path else "skipped",
            },
            "p1": {
                "status": "success" if p1_ok else "failed",
            },
            "p2": {
                "status": "success" if p2_ok else "failed",
            },
        },
    }

    summary_path = output_dir / args.episode / f"{args.episode}-pipeline-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n{'='*60}")
    print(f"  Pipeline 完成")
    print(f"  汇总: {summary_path.resolve().relative_to(BASE_DIR.resolve())}")
    print(f"  outline: {summary['stages']['outline']['status']}")
    print(f"  storyboard: {summary['stages']['storyboard']['status']}")
    print(f"  P1: {summary['stages']['p1']['status']}")
    print(f"  P2: {summary['stages']['p2']['status']}")
    print(f"{'='*60}")

    # 检查失败
    failed = [k for k, v in summary["stages"].items() if v.get("status") == "failed"]
    if failed:
        print(f"[WARN] 失败阶段: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
