#!/usr/bin/env python3
"""
video_pipeline.py — huage888 统一视频生成管道

统一调用多个视频模型（Doubao / Kling），支持 prompt 模板渲染。

用法：
  python3 scripts/video_pipeline.py --list          # 列出可用适配器
  python3 scripts/video_pipeline.py --test         # 测试所有适配器连接

  # 单条视频
  python3 scripts/video_pipeline.py \
    --video \
    --provider doubao \
    --prompt "古风少女在赛博竹林中缓缓睁眼" \
    --output /tmp/v001.mp4

  # 单条图片
  python3 scripts/video_pipeline.py \
    --image \
    --provider doubao \
    --prompt "古风少女，道姑髻，超写实，电影级" \
    --output /tmp/i001.png

  # 指定模型和参数
  python3 scripts/video_pipeline.py \
    --video \
    --provider kling \
    --model kling-o1-std-10s \
    --duration 10 \
    --aspect 9:16 \
    --prompt "..." \
    --output /tmp/v.mp4

  # 使用 prompt 模板
  python3 scripts/video_pipeline.py \
    --video \
    --provider doubao \
    --template character-motion \
    --vars "character=漠玫,scene=赛博竹林,action=睁眼" \
    --output /tmp/v.mp4

  # 批量视频（从分镜脚本）
  python3 scripts/video_pipeline.py \
    --batch \
    --provider doubao \
    --shots-file outputs/02-storyboard-script.md \
    --output-dir outputs/videos/

环境变量：
  ARK_API_KEY      Doubao API Key
  KLING_API_KEY    Kling API Key
  KLING_KEY_ID     Kling Key ID
"""

import argparse
import os
import sys
import json
import re
from pathlib import Path

# 添加 scripts 到路径
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(BASE_DIR / "config"))

from adapters import get_registry, VideoResult, ImageResult
from art_styles import get_style, search_styles, ART_STYLES
from task_queue import TaskQueue, create_queue

# 延迟导入追踪模块
_task_state_mod = None
_event_emitter_mod = None


def _lazy_task_state():
    global _task_state_mod
    if _task_state_mod is None:
        from task_state import TaskManager, TaskState, TaskType
        _task_state_mod = (TaskManager, TaskState, TaskType)
    return _task_state_mod


def _lazy_event_emitter(log_file: str | None = None, emit_console: bool = True):
    global _event_emitter_mod
    if _event_emitter_mod is None:
        from event_emitter import EventEmitter, ConsoleSink, JSONLSink
        _event_emitter_mod = (EventEmitter, ConsoleSink, JSONLSink)
    EventEmitter, ConsoleSink, JSONLSink = _event_emitter_mod
    sinks = []
    if emit_console:
        sinks.append(ConsoleSink(color=True, progress_bar=True))
    if log_file:
        sinks.append(JSONLSink(log_file))
    return EventEmitter(sinks=sinks if sinks else None)


# ─────────────────────────────────────────────────────────────────
# Prompt 模板系统
# ─────────────────────────────────────────────────────────────────

def render_template(template_id: str, variables: dict) -> str:
    """
    渲染 prompt 模板，支持 {{variable}} 占位符。

    模板来源：prompts/templates/{template_id}.txt
    """
    template_path = BASE_DIR / "prompts" / "templates" / f"{template_id}.txt"
    if not template_path.exists():
        raise FileNotFoundError(f"模板不存在：{template_path}")

    template = template_path.read_text(encoding="utf-8")

    # 简单 Mustache 风格替换
    for key, value in variables.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))

    # 检查未替换的占位符
    remaining = re.findall(r"\{\{(\w+)\}\}", template)
    if remaining:
        print(f"⚠️  未填充的占位符：{remaining}", file=sys.stderr)

    return template.strip()


def parse_vars(vars_str: str) -> dict:
    """解析 --vars 参数：key1=value1,key2=value2"""
    result = {}
    for pair in vars_str.split(","):
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        result[key.strip()] = value.strip()
    return result


# ─────────────────────────────────────────────────────────────────
# 批量处理（task_queue 并行）
# ─────────────────────────────────────────────────────────────────

def _batch_with_queue(
    rows: list,
    col_idx: int,
    output_dir: Path,
    provider_name: str,
    max_workers: int,
    max_retries: int,
    emitter,
    task_id: str | None,
    task_name_prefix: str,
    style_name: str,
    **kwargs,
) -> tuple[list[Path], list]:
    """使用 task_queue 并行批量生成"""
    import time as time_module

    def gen_video_fn(
        shot_num: int,
        prompt: str,
        output_path_str: str,
        style: str,
        pvd: str,
        kw: dict,
    ):
        """闭包：避免 pickle 问题"""
        return generate_video(
            provider_name=pvd,
            prompt=prompt,
            output_path=Path(output_path_str),
            style_name=style,
            **kw,
        )

    queue = create_queue(
        max_workers=max_workers,
        max_retries=max_retries,
        tasks_dir=str(BASE_DIR / ".huage888" / "tasks"),
        log_file=str(BASE_DIR / ".huage888" / "queue_events.jsonl"),
    )

    # 构建任务
    task_map = {}  # task_id → (shot_num, output_path)
    for i, row in enumerate(rows, 1):
        if col_idx >= len(row):
            continue
        prompt = row[col_idx].strip()
        if not prompt:
            continue
        output_path = output_dir / f"shot_{i:03d}.mp4"
        task_id_gen = queue.add(
            name=f"{task_name_prefix}-shot-{i:03d}",
            fn=gen_video_fn,
            shot_num=i,
            prompt=prompt,
            output_path_str=str(output_path),
            style=style_name,
            pvd=provider_name,
            kw=kwargs,
        )
        task_map[task_id_gen] = (i, output_path)

    # 执行
    task_results = queue.run()
    results = [Path(r.result) for r in task_results if r.success]

    total = len(task_results)
    success = len(results)
    print(f"\n✅ 批量完成：{success}/{total} 成功", file=sys.stderr)
    return results, task_results


def batch_from_shots(
    shots_file: Path,
    output_dir: Path,
    provider_name: str,
    prompt_column: str = "libtvPrompt",
    # ── task_queue 参数 ────────────────────────────────────────────
    max_workers: int = 4,
    max_retries: int = 3,
    # ── 追踪参数 ───────────────────────────────────────────────────
    emitter=None,
    task_id: str | None = None,
    task_name_prefix: str = "video-batch",
    style_name: str = "",
    **kwargs,
) -> list[Path]:
    """从分镜脚本批量生成视频"""
    if not shots_file.exists():
        raise FileNotFoundError(f"分镜文件不存在：{shots_file}")

    content = shots_file.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 解析 Markdown 表格
    lines = content.split("\n")
    rows = []
    for line in lines:
        if not (line.startswith("|") and line.endswith("|")):
            continue
        stripped = line.strip("| ")
        # 跳过表格分隔行
        if all(c in "- |:" for c in stripped):
            continue
        cols = [c.strip() for c in stripped.split("|")]
        rows.append(cols)

    if len(rows) < 2:
        raise ValueError("分镜文件格式错误，找不到 Markdown 表格")

    # 第一行是表头
    header = rows[0]
    try:
        col_idx = header.index(prompt_column)
    except ValueError:
        # 尝试模糊匹配
        col_idx = None
        for i, h in enumerate(header):
            if "prompt" in h.lower() or "libtv" in h.lower():
                col_idx = i
                break
        if col_idx is None:
            raise ValueError(f"找不到列 '{prompt_column}'，表头：{header}")

    print(f"📋 找到 {len(rows)-1} 个镜头，Prompt 列：'{header[col_idx]}'", file=sys.stderr)

    # 使用 task_queue 并行执行（可选降级）
    use_queue = max_workers > 1
    if use_queue:
        print(f"🔄 启用任务队列（并发 {max_workers}，最大重试 {max_retries}）", file=sys.stderr)
        results, task_queue_results = _batch_with_queue(
            rows[1:], col_idx, output_dir,
            provider_name, max_workers, max_retries,
            emitter, task_id, task_name_prefix, style_name,
            **kwargs,
        )
    else:
        results = []
        for i, row in enumerate(rows[1:], 1):
            if col_idx >= len(row):
                continue
            prompt = row[col_idx].strip()
            if not prompt:
                continue

            output_path = output_dir / f"shot_{i:03d}.mp4"
            print(f"\n[镜头 {i:03d}] → {output_path.name}", file=sys.stderr)

            try:
                generate_video(
                    provider_name=provider_name,
                    prompt=prompt,
                    output_path=output_path,
                    style_name=style_name,
                    **kwargs,
                )
                results.append(output_path)
            except Exception as e:
                print(f"  ❌ 失败：{e}", file=sys.stderr)
                continue

    return results


# ─────────────────────────────────────────────────────────────────
# 核心生成函数
# ─────────────────────────────────────────────────────────────────

def generate_video(
    provider_name: str,
    prompt: str,
    output_path: Path,
    model: str = "",
    duration: int = 5,
    watermark: bool = True,
    aspect_ratio: str = "16:9",
    img1: str = "",
    img2: str = "",
    style_name: str = "",
    # ── 追踪参数（可选）─────────────────────────────────────────────
    emitter=None,
    task_id: str | None = None,
    task_name: str = "video-gen",
    **kwargs,
) -> VideoResult:
    """生成视频（统一入口）"""
    registry = get_registry()
    adapter = registry.get(provider_name)

    # 更新配置
    adapter.config.duration = duration
    adapter.config.watermark = watermark
    adapter.config.aspect_ratio = aspect_ratio

    # 风格锚定（art_styles 集成）
    if style_name:
        style = get_style(style_name)
        if style:
            prompt = prompt.rstrip() + "，" + style["prompt"]
            print(f"  🎨 风格锚定：{style_name}", file=sys.stderr)

    if emitter and task_id:
        emitter.emit_task_start(task_name, params={"prompt": prompt[:50], "provider": provider_name})

    print(f"\n🎬 生成视频", file=sys.stderr)
    print(f"  适配器：{provider_name}", file=sys.stderr)
    print(f"  模型：{model or adapter.default_video_model}", file=sys.stderr)
    print(f"  时长：{duration}s | 比例：{aspect_ratio} | 水印：{watermark}", file=sys.stderr)
    print(f"  Prompt：{prompt[:60]}{'...' if len(prompt) > 60 else ''}", file=sys.stderr)

    result = adapter.generate_video(
        prompt=prompt,
        output_path=output_path,
        img1=img1 or None,
        img2=img2 or None,
        duration=duration,
        model=model or None,
    )

    print(f"  ✅ 完成（{result.elapsed_seconds:.0f}s）：{output_path}", file=sys.stderr)

    if emitter and task_id:
        emitter.emit_task_end(
            task_id, task_name,
            result={"output": str(output_path)},
            elapsed=result.elapsed_seconds,
            result_preview=f"{result.elapsed_seconds:.0f}s → {output_path.name}",
        )

    return result


def generate_image(
    provider_name: str,
    prompt: str,
    output_path: Path,
    model: str = "",
    **kwargs,
) -> ImageResult:
    """生成图片（统一入口）"""
    registry = get_registry()
    adapter = registry.get(provider_name)

    print(f"\n🖼️  生成图片", file=sys.stderr)
    print(f"  适配器：{provider_name}", file=sys.stderr)
    print(f"  Prompt：{prompt[:60]}{'...' if len(prompt) > 60 else ''}", file=sys.stderr)

    result = adapter.generate_image(
        prompt=prompt,
        output_path=output_path,
        model=model or None,
    )

    print(f"  ✅ 完成：{output_path}", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────
# Pipeline Stage 5：视频生成
# ─────────────────────────────────────────────────────────────────

def stage5_video(
    shots_path: Path,
    episode: str,
    output_dir: Path | None = None,
    provider: str = "doubao",
    duration: int = 5,
    watermark: bool = True,
    workers: int = 4,
    max_retries: int = 3,
    task_db=None,
    conv_mgr=None,
    emitter=None,
    dry_run: bool = False,
) -> dict:
    """
    Stage 5: 分镜脚本 → 批量视频生成

    对应 run_episode_pipeline.py 的最终输出阶段。

    Args:
        shots_path: 分镜脚本文件路径（.md，含 libtvPrompt 列）
        episode: 集数（如 S01E01）
        output_dir: 输出目录（默认 outputs/{episode}/videos/）
        provider: 视频提供商（doubao / kling）
        duration: 视频时长（秒）
        watermark: 是否添加水印
        workers: 并发数
        max_retries: 最大重试次数
        task_db: TaskDB 实例（可选）
        conv_mgr: ConversationManager 实例（可选）
        emitter: EventEmitter 实例（可选）
        dry_run: dry-run 模式

    Returns:
        {"generated": N, "failed": M, "files": [file_paths], "summary": {...}}
    """
    base = output_dir or (BASE_DIR / "outputs")
    video_dir = base / episode / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🎬 Stage 5: 视频生成")
    print(f"  集数：{episode}")
    print(f"  分镜脚本：{shots_path.name}")
    print(f"  输出目录：{video_dir.relative_to(BASE_DIR)}")
    print(f"  提供商：{provider}，时长：{duration}s，水印：{watermark}")

    if dry_run:
        print(f"\n[DRY] 跳过视频生成")
        return {"generated": 0, "failed": 0, "files": [], "summary": {}}

    # task 追踪
    batch_task_id = None
    if task_db:
        try:
            from task_db import TaskState
            batch_task_id = task_db.create(
                task_type="video_batch",
                name=f"stage5_video_{episode}",
                params={
                    "episode": episode,
                    "provider": provider,
                    "duration": duration,
                    "shots": str(shots_path),
                },
                episode=episode,
                stage="video",
            )
            task_db.update(batch_task_id, TaskState.RUNNING)
            print(f"  📊 task_db 已记录（ID: {batch_task_id}）", file=sys.stderr)
        except Exception as e:
            print(f"  [WARN] task_db 记录失败: {e}", file=sys.stderr)

    try:
        results = batch_from_shots(
            shots_file=shots_path,
            output_dir=video_dir,
            provider_name=provider,
            max_workers=workers,
            max_retries=max_retries,
            emitter=emitter,
            task_id=batch_task_id,
            task_name_prefix=f"video_{episode}",
            duration=duration,
            watermark=watermark,
        )

        generated = len(results)
        failed = 0

        print(f"\n  📊 视频生成完成：成功 {generated} / 失败 {failed}")

        if task_db and batch_task_id:
            try:
                from task_db import TaskState
                task_db.update(
                    batch_task_id, TaskState.SUCCESS,
                    result={"generated": generated, "failed": failed, "files": [str(r) for r in results]},
                )
            except Exception:
                pass

        return {
            "generated": generated,
            "failed": failed,
            "files": [str(r) for r in results],
            "summary": {
                "episode": episode,
                "provider": provider,
                "duration": duration,
                "output_dir": str(video_dir),
            },
        }

    except Exception as e:
        print(f"\n  ❌ Stage 5 失败: {e}", file=sys.stderr)

        if task_db and batch_task_id:
            try:
                from task_db import TaskState
                task_db.update(batch_task_id, TaskState.FAILED, error=str(e))
            except Exception:
                pass

        return {"generated": 0, "failed": 1, "files": [], "error": str(e)}


# ─────────────────────────────────────────────────────────────────
# 命令行参数
# ─────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="huage888 统一视频生成管道",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--list", action="store_true", help="列出所有已注册适配器")
    parser.add_argument("--test", action="store_true", help="测试所有适配器连接")

    mode = parser.add_argument_group("模式（互斥）")
    mode_g = mode.add_mutually_exclusive_group()
    mode_g.add_argument("--video",  action="store_true", help="视频生成")
    mode_g.add_argument("--image",  action="store_true", help="图片生成")
    mode_g.add_argument("--batch",  action="store_true", help="批量视频")

    parser.add_argument("--provider", "-p",
                        default="doubao",
                        choices=["doubao", "kling"],
                        help="视频模型提供商")
    parser.add_argument("--model", "-m", default="",
                        help="具体模型 ID")
    parser.add_argument("--prompt", help="Prompt 文本")
    parser.add_argument("--template", help="Prompt 模板 ID（prompts/templates/{id}.txt）")
    parser.add_argument("--vars", help="模板变量，格式：key1=value1,key2=value2")
    parser.add_argument("--duration", "-d", type=int, default=5, help="视频时长（秒）")
    parser.add_argument("--aspect", default="16:9",
                        choices=["16:9", "9:16", "1:1", "4:3"],
                        help="画面比例")
    parser.add_argument("--watermark", action="store_true", default=True,
                        help="添加水印（默认）")
    parser.add_argument("--no-watermark", action="store_true",
                        help="无水印")
    parser.add_argument("--img1", default="", help="首帧参考图 URL（图生视频）")
    parser.add_argument("--img2", default="", help="尾帧参考图 URL（首尾帧视频）")
    parser.add_argument("--shots-file", type=Path, help="分镜脚本路径（批量模式）")
    parser.add_argument("--shots-column", default="libtvPrompt",
                        help="分镜脚本中 Prompt 列名")
    parser.add_argument("--output-dir", type=Path, help="批量输出目录")
    parser.add_argument("--output", "-o", type=Path, help="输出文件路径（单条）")

    # ── 风格参数 ───────────────────────────────────────────────────
    parser.add_argument("--style", default="",
                        help="艺术风格名称（从 art_styles 库查找，如 吉卜力/赛博竹林）")

    # ── 批量并行参数 ───────────────────────────────────────────────
    batch = parser.add_argument_group("批量并行参数")
    batch.add_argument("--workers", "-w", type=int, default=4,
                       help="批量并发数，默认 4")
    batch.add_argument("--retries", "-r", type=int, default=3,
                       help="批量最大重试次数，默认 3")

    # ── 追踪参数 ───────────────────────────────────────────────────
    tracking = parser.add_argument_group("追踪参数（可选）")
    tracking.add_argument("--track", action="store_true", default=False,
                           help="开启任务追踪")
    tracking.add_argument("--no-track", action="store_true", default=False,
                           help="禁用任务追踪")
    tracking.add_argument("--log-file", default=None,
                           help="事件日志文件路径")
    tracking.add_argument("--no-emit", action="store_true", default=False,
                           help="禁用控制台事件输出")

    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────
# 主函数
# ─────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    registry = get_registry()

    # ── 追踪初始化 ─────────────────────────────────────────────────
    do_track = args.track and not args.no_track
    emit_console = not args.no_emit
    emitter = None
    task_id = None

    if do_track:
        log_file = args.log_file or str(BASE_DIR / ".huage888" / "events.jsonl")
        emitter = _lazy_event_emitter(log_file=log_file, emit_console=emit_console)
        print(f"\n📊 任务追踪已开启", file=sys.stderr)

    # ── 列出适配器 ─────────────────────────────────────────────────
    if args.list:
        providers = registry.list()
        if not providers:
            print("⚠️  未注册任何适配器，请设置环境变量：")
            print("  ARK_API_KEY  → Doubao")
            print("  KLING_API_KEY + KLING_KEY_ID → Kling")
        else:
            print("已注册的适配器：")
            for p in providers:
                print(f"  ✅ {p}")
        return

    # 测试连接
    if args.test:
        providers = registry.list()
        if not providers:
            print("⚠️  未注册任何适配器，请设置环境变量")
            sys.exit(1)

        print("=" * 50)
        print("huage888 适配器连接测试")
        print("=" * 50)
        for name in providers:
            adapter = registry.get(name)
            status = "✅ 正常" if adapter.health_check() else "❌ 失败"
            print(f"  {name}: {status}")
        print("=" * 50)
        return

    # 解析 prompt（模板 或 直接文本）
    if args.template:
        if not args.vars:
            print("错误：使用 --template 时必须提供 --vars", file=sys.stderr)
            sys.exit(1)
        prompt = render_template(args.template, parse_vars(args.vars))
    elif args.prompt:
        prompt = args.prompt
    else:
        print("错误：请提供 --prompt 或 --template", file=sys.stderr)
        sys.exit(1)

    watermark = not args.no_watermark

    # 批量模式
    if args.batch:
        if not args.shots_file:
            print("错误：批量模式需要 --shots-file", file=sys.stderr)
            sys.exit(1)
        output_dir = args.output_dir or (BASE_DIR / "outputs" / "videos")
        results = batch_from_shots(
            shots_file=args.shots_file,
            output_dir=output_dir,
            provider_name=args.provider,
            prompt_column=args.shots_column,
            model=args.model,
            duration=args.duration,
            watermark=watermark,
            aspect_ratio=args.aspect,
            max_workers=args.workers,
            max_retries=args.retries,
            emitter=emitter,
            task_id=task_id,
            task_name_prefix=f"{args.provider}-batch",
            style_name=args.style,
        )
        print(f"\n✅ 批量完成：{len(results)} 个镜头", file=sys.stderr)
        return

    # 单条模式
    if not args.output:
        print("错误：请提供 --output", file=sys.stderr)
        sys.exit(1)

    if args.image:
        generate_image(
            provider_name=args.provider,
            prompt=prompt,
            output_path=args.output,
            model=args.model,
        )
    else:
        generate_video(
            provider_name=args.provider,
            prompt=prompt,
            output_path=args.output,
            model=args.model,
            duration=args.duration,
            watermark=watermark,
            aspect_ratio=args.aspect,
            img1=args.img1,
            img2=args.img2,
            style_name=args.style,
            emitter=emitter,
            task_name=f"{args.provider}-video",
        )


if __name__ == "__main__":
    main()
