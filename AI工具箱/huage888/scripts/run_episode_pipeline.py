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
STORYLINE_PIPELINE = BASE_DIR / "scripts" / "storyline_pipeline.py"
ASSET_IMAGE_PIPELINE = BASE_DIR / "scripts" / "asset_image_pipeline.py"
VIDEO_PIPELINE = BASE_DIR / "scripts" / "video_pipeline.py"


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

def stage0_storyline(
    script_arg: str | None,
    episode: str,
    project: str,
    output_dir: Path,
    dry_run: bool,
    task_db=None,
    conv_mgr=None,
) -> Path | None:
    """Stage 0: storyline-agent 生成故事线"""
    storyline_dir = BASE_DIR / ".huage888" / "storylines" / project / episode
    storyline_dir.mkdir(parents=True, exist_ok=True)

    # 读取剧本
    if script_arg:
        script_path = Path(script_arg)
        if script_path.exists() and script_path.is_file():
            script_content = script_path.read_text(encoding="utf-8")
        else:
            script_content = script_arg
    else:
        if dry_run:
            script_content = "[剧本内容占位 - dry-run]"
        else:
            print("[ERROR] Stage 0 需要 --script 参数")
            return None

    print(f"\n{'[DRY] ' if dry_run else ''}→ Stage 0: storyline 生成")

    if dry_run:
        print(f"    [DRY] 剧本前80字：{script_content[:80]}...")
        return storyline_dir / "storyline.json"

    # 调用 storyline_pipeline
    cmd = [
        sys.executable,
        str(STORYLINE_PIPELINE),
        "--script", script_arg or script_content,
        "--episode", episode,
        "--project", project,
        "--output-base", str(BASE_DIR),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [FAIL] Stage 0 storyline 失败", file=sys.stderr)
        print(f"    stderr: {result.stderr[:300]}", file=sys.stderr)
        return None

    storyline_path = storyline_dir / "storyline.json"
    print(f"    [OK] storyline 完成 → {storyline_path.absolute().relative_to(BASE_DIR.absolute()) if storyline_path else None}")
    return storyline_path


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


def stage1_5_asset_images(
    outline_path: Path,
    episode: str,
    project: str,
    output_dir: Path,
    dry_run: bool,
    task_db=None,
) -> bool:
    """Stage 1.5: 资产图 API 生成"""
    print(f"\n{'[DRY] ' if dry_run else ''}→ Stage 1.5: 资产图生成")

    if dry_run:
        print(f"    [DRY] outline: {outline_path}")
        return True

    cmd = [
        sys.executable,
        str(ASSET_IMAGE_PIPELINE),
        "--outline", str(outline_path),
        "--episode", episode,
        "--project", project,
        "--output-dir", str(output_dir),
        "--provider", "doubao",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [FAIL] Stage 1.5 资产图失败", file=sys.stderr)
        print(f"    stderr: {result.stderr[:300]}", file=sys.stderr)
        return False

    print(f"    [OK] Stage 1.5 完成")
    return True


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


def stage5_video(
    shots_path: Path,
    episode: str,
    output_dir: Path,
    provider: str,
    duration: int,
    workers: int,
    dry_run: bool,
    task_db=None,
) -> dict:
    """Stage 5: 视频生成"""
    print(f"\n{'[DRY] ' if dry_run else ''}→ Stage 5: 视频生成")

    # 延迟导入避免循环依赖
    sys.path.insert(0, str(SCRIPT_DIR))
    from video_pipeline import stage5_video as _stage5_video

    result = _stage5_video(
        shots_path=shots_path,
        episode=episode,
        output_dir=output_dir,
        provider=provider,
        duration=duration,
        workers=workers,
        task_db=task_db,
        dry_run=dry_run,
    )
    return result


# ── 主函数 ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent 委托链编排：storyline → outline → asset_images → storyboard → P1 → P2 → video",
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

    # ── 新增阶段参数 ───────────────────────────────────────────────────────
    stage = parser.add_argument_group("Pipeline 阶段控制")
    stage.add_argument(
        "--storyline",
        action="store_true",
        help="执行 Stage 0：故事线生成",
    )
    stage.add_argument(
        "--run-asset-images",
        action="store_true",
        help="执行 Stage 1.5：资产图 API 生成（需 outline 完成）",
    )
    stage.add_argument(
        "--skip-video",
        action="store_true",
        default=True,
        help="跳过 Stage 5 视频生成（默认 True，需显式开启）",
    )
    stage.add_argument(
        "--run-video",
        action="store_true",
        help="执行 Stage 5：视频生成",
    )
    stage.add_argument(
        "--video-provider",
        default="doubao",
        choices=["doubao", "kling"],
        help="视频生成提供商（默认 doubao）",
    )
    stage.add_argument(
        "--video-duration",
        type=int,
        default=5,
        help="视频时长（秒，默认 5）",
    )
    stage.add_argument(
        "--workers",
        type=int,
        default=4,
        help="视频批量并发数（默认 4）",
    )
    stage.add_argument(
        "--session-id",
        default=None,
        help="对话 session ID（用于对话历史续接）",
    )
    stage.add_argument(
        "--max-history",
        type=int,
        default=10,
        help="对话历史注入条数上限（默认 10，设为 0 禁用）",
    )

    args = parser.parse_args()

    # ── 初始化 TaskDB 和 ConversationManager ─────────────────────────────────
    task_db = None
    conv_mgr = None
    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        from task_db import TaskDB
        task_db = TaskDB()
        project_id = task_db.upsert_project(name=args.project)
        print(f"  📊 TaskDB 已连接（project_id: {project_id}）")
    except Exception as e:
        print(f"  [INFO] TaskDB 不可用: {e}")

    try:
        from conversation_manager import ConversationManager
        conv_mgr = ConversationManager()
        print(f"  💬 ConversationManager 已连接")
    except Exception as e:
        print(f"  [INFO] ConversationManager 不可用: {e}")

    output_dir = Path(args.output_dir)

    def _rel(path: Path) -> str:
        """安全获取相对路径（处理 dry-run 中的相对路径）"""
        if path is None:
            return None
        try:
            return str(path.relative_to(BASE_DIR))
        except ValueError:
            return str(path.resolve().relative_to(BASE_DIR.resolve()))

    print(f"{'='*60}")
    print(f"  Episode Pipeline · {args.episode} · {args.project}")
    print(f"  输出目录: {output_dir}")
    print(f"  阶段: storyline({('run' if args.storyline else 'skip')}) / "
          f"outline({'skip' if args.skip_outline else 'run'}) / "
          f"asset_images({'run' if args.run_asset_images else 'skip'}) / "
          f"storyboard({'skip' if args.skip_storyboard else 'run'}) / "
          f"P1({'run' if args.run_p1 else 'skip'}) / "
          f"P2({'run' if args.run_p2 else 'skip'}) / "
          f"video({'run' if args.run_video and not args.skip_video else 'skip'})")
    print(f"{'='*60}")

    # ── Stage 0: storyline ──────────────────────────────────────────────
    storyline_path: Path | None = None

    if args.storyline:
        print(f"\n[Stage 0] storyline-agent")
        storyline_path = stage0_storyline(
            script_arg=args.script,
            episode=args.episode,
            project=args.project,
            output_dir=output_dir,
            dry_run=args.dry_run,
            task_db=task_db,
            conv_mgr=conv_mgr,
        )
        if storyline_path is None and not args.dry_run:
            print("[ERROR] Stage 0 失败，停止执行")
            sys.exit(1)
    else:
        print(f"\n[Stage 0] SKIP（需 --storyline 显式开启）")

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

    # ── Stage 1.5: asset_images ───────────────────────────────────────
    asset_ok = True
    if args.run_asset_images and outline_path and outline_path.exists():
        print(f"\n[Stage 1.5] 资产图生成")
        asset_ok = stage1_5_asset_images(
            outline_path=outline_path,
            episode=args.episode,
            project=args.project,
            output_dir=output_dir,
            dry_run=args.dry_run,
            task_db=task_db,
        )
    else:
        print(f"\n[Stage 1.5] SKIP（需 --run-asset-images 且 outline 存在）")

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

    # ── Stage 5: video ──────────────────────────────────────────────────
    video_ok = True
    video_result = {}
    if args.run_video and not args.skip_video and shots_path and shots_path.exists():
        video_result = stage5_video(
            shots_path=shots_path,
            episode=args.episode,
            output_dir=output_dir,
            provider=args.video_provider,
            duration=args.video_duration,
            workers=args.workers,
            dry_run=args.dry_run,
            task_db=task_db,
        )
        video_ok = video_result.get("failed", 1) == 0
    elif args.run_video:
        print(f"\n[Stage 5] SKIP（需 shots 文件存在）")
    else:
        print(f"\n[Stage 5] SKIP（默认关闭，需 --run-video 开启）")

    # ── 汇总 ────────────────────────────────────────────────────────────
    summary = {
        "episode": args.episode,
        "project": args.project,
        "generated_at": datetime.now().isoformat(),
        "stages": {
            "storyline": {
                "path": _rel(storyline_path),
                "status": "success" if storyline_path else ("skipped" if not args.storyline else "failed"),
            },
            "outline": {
                "path": _rel(outline_path),
                "status": "success" if outline_path else "skipped",
            },
            "asset_images": {
                "status": "success" if asset_ok else "failed",
            },
            "storyboard": {
                "path": _rel(shots_path),
                "status": "success" if shots_path else "skipped",
            },
            "p1": {
                "status": "success" if p1_ok else "failed",
            },
            "p2": {
                "status": "success" if p2_ok else "failed",
            },
            "video": {
                "status": "success" if video_ok else "failed",
                "generated": video_result.get("generated", 0),
                "failed": video_result.get("failed", 0),
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
    print(f"  storyline:   {summary['stages']['storyline']['status']}")
    print(f"  outline:     {summary['stages']['outline']['status']}")
    print(f"  asset_images:{summary['stages']['asset_images']['status']}")
    print(f"  storyboard:  {summary['stages']['storyboard']['status']}")
    print(f"  P1:          {summary['stages']['p1']['status']}")
    print(f"  P2:          {summary['stages']['p2']['status']}")
    print(f"  video:       {summary['stages']['video']['status']}"
          f" ({video_result.get('generated', 0)} 个)")
    print(f"{'='*60}")

    # 关闭 TaskDB
    if task_db:
        task_db.close()

    # 检查失败
    failed = [k for k, v in summary["stages"].items() if v.get("status") == "failed"]
    if failed:
        print(f"[WARN] 失败阶段: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
