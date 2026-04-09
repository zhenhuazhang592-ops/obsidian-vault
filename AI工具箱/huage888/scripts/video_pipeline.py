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

# ── .env 自动加载（优先级：环境变量 > .env 文件）──────────────────
_env_path = BASE_DIR / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _k = _k.strip()
                _v = _v.strip()
                if _k and os.environ.get(_k) is None:
                    os.environ[_k] = _v

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
# 资产库查询（打通资产库 → 视频提示词）
# ─────────────────────────────────────────────────────────────────

def resolve_shot_references(
    shot: dict,
    asset_library=None,
    asset_dir: Path | None = None,
) -> list[dict]:
    """
    为单个 shot 解析资产参考图列表（参考 Toonflow 多参考图模式）。

    查询优先级：
      1. asset_dir（Stage 1.5 输出目录，episode 专用资产）
      2. AssetLibrary 全局库（assets/library/）

    Args:
        shot:         分镜 dict，需包含 characters / scene / props 字段
        asset_library: AssetLibrary 实例
        asset_dir:    Stage 1.5 输出目录（如 outputs/S01E01/assets/）

    Returns:
        references: list[dict]，每项 {
            "url": str,       # 本地绝对路径
            "role": str,      # "reference_image"
            "label": str,     # 标签，如 "漠玫参考图"
            "asset_name": str, # 资产名称
            "asset_type": str, # character / scene / prop
        }
    """
    from adapters.video_adapter_base import IMAGE_ROLE_REFERENCE

    refs: list[dict] = []
    seen_urls: set[str] = set()

    def _add_ref(file_path: str, label: str, asset_name: str, asset_type: str, base: Path):
        """添加单个参考图（去重）"""
        if file_path in seen_urls:
            return
        abs_path = base / file_path
        if abs_path.exists():
            refs.append({
                "url": str(abs_path.resolve()),
                "role": IMAGE_ROLE_REFERENCE,
                "label": label,
                "asset_name": asset_name,
                "asset_type": asset_type,
            })
            seen_urls.add(file_path)

    # ── 1. 优先：asset_dir（episode 输出目录）───────────────────
    if asset_dir and asset_dir.exists() and asset_library:
        for char_name in shot.get("characters", []):
            for fp in asset_library.resolve(char_name, "character", base_dir=asset_dir):
                _add_ref(fp, f"{char_name}参考图", char_name, "character", asset_dir)

        scene_name = shot.get("scene", "")
        if scene_name:
            for fp in asset_library.resolve(scene_name, "scene", base_dir=asset_dir):
                _add_ref(fp, f"{scene_name}场景参考图", scene_name, "scene", asset_dir)

        for prop_name in shot.get("props", []):
            for fp in asset_library.resolve(prop_name, "prop", base_dir=asset_dir):
                _add_ref(fp, f"{prop_name}道具参考图", prop_name, "prop", asset_dir)

    # ── 2. 降级：AssetLibrary 全局库 + 目录扫描 ─────────────────
    global_base = BASE_DIR / "assets" / "library"

    if asset_library:
        for char_name in shot.get("characters", []):
            for fp in asset_library.resolve(char_name, "character", base_dir=global_base):
                _add_ref(fp, f"{char_name}参考图(全局)", char_name, "character", global_base)

        scene_name = shot.get("scene", "")
        if scene_name:
            for fp in asset_library.resolve(scene_name, "scene", base_dir=global_base):
                _add_ref(fp, f"{scene_name}场景参考图(全局)", scene_name, "scene", global_base)

        for prop_name in shot.get("props", []):
            for fp in asset_library.resolve(prop_name, "prop", base_dir=global_base):
                _add_ref(fp, f"{prop_name}道具参考图(全局)", prop_name, "prop", global_base)

    # ── 3. 降级：asset_dir 目录直接扫描（无 manifest 时兜底）───
    if asset_dir and asset_dir.exists():
        for char_name in shot.get("characters", []):
            char_dir = asset_dir / char_name
            if not char_dir.is_dir():
                continue
            for img in char_dir.glob("*.png"):
                if img.name in seen_urls:
                    continue
                refs.append({
                    "url": str(img.resolve()),
                    "role": IMAGE_ROLE_REFERENCE,
                    "label": f"{char_name}参考图",
                    "asset_name": char_name,
                    "asset_type": "character",
                })
                seen_urls.add(img.name)

        scene_name = shot.get("scene", "")
        if scene_name:
            scene_dir = asset_dir / scene_name
            if scene_dir.is_dir():
                for img in scene_dir.glob("*.png"):
                    if img.name in seen_urls:
                        continue
                    refs.append({
                        "url": str(img.resolve()),
                        "role": IMAGE_ROLE_REFERENCE,
                        "label": f"{scene_name}场景参考图",
                        "asset_name": scene_name,
                        "asset_type": "scene",
                    })
                    seen_urls.add(img.name)

    return refs


def build_video_prompt_with_references(
    base_prompt: str,
    references: list[dict],
    style_name: str = "",
    art_style: dict | None = None,
) -> str:
    """
    构建增强后的视频 prompt（含资产 Reference Section）。

    参考 @图N 格式（来自视频提示词生成 Skill）：
      [References]
      @图1 : [漠玫参考图]
      @图2 : [赛博西湖断桥场景图]
      [Instruction]
      Based on @图1 ..., set in the environment of @图2 ...

    Toonflow 的实际 API 传图方式是 content 数组，
    此函数同时输出 Reference Section（供日志/debug）和纯 prompt 文本。

    Returns:
        (enhanced_prompt, ref_section)
        - enhanced_prompt: 含 @图N 引用标记的完整 prompt（用于日志）
        - ref_section: [References] ... 部分（可嵌入 prompt）
    """
    parts: list[str] = []

    # 1. [References] Section（@图N 格式）
    if references:
        ref_lines = ["[References]"]
        for i, ref in enumerate(references, 1):
            label = ref.get("label", ref.get("asset_name", f"图{i}"))
            ref_lines.append(f"@图{i} : [{label}]")
        parts.append("\n".join(ref_lines))

    # 2. [Instruction] Section
    if references:
        parts.append("[Instruction]")
        # 注入 @图N 引用到主体内容
        ref_usage_parts = []
        for i, ref in enumerate(references, 1):
            asset_name = ref.get("asset_name", "")
            asset_type = ref.get("asset_type", "")
            if asset_type == "character":
                ref_usage_parts.append(f"@图{i} (character reference: {asset_name})")
            elif asset_type == "scene":
                ref_usage_parts.append(f"@图{i} (scene reference: {asset_name})")
            else:
                ref_usage_parts.append(f"@图{i} ({asset_name})")
        parts.append("Reference assets: " + ", ".join(ref_usage_parts) + ".")
        parts.append("Content: " + base_prompt)
    else:
        parts.append(base_prompt)

    # 3. [Style Mandate]
    style_constraint = ""
    if art_style and isinstance(art_style, dict):
        style_text = art_style.get("prompt", "")
        style_en = art_style.get("prompt_en", "")
        style_constraint = f"[Style Mandate]: Strictly maintain {style_name or 'specified'} art style. {style_en or style_text}"
    elif style_name:
        style_constraint = f"[Style Mandate]: Strictly maintain {style_name} art style."

    if style_constraint:
        parts.append(style_constraint)

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────
# Prompt 模板系统
# ─────────────────────────────────────────────────────────────────

def build_video_prompt(
    base_prompt: str,
    style_name: str = "",
    art_style: str = "",
    characters: str = "",
    scene: str = "",
) -> str:
    """
    构建增强后的视频 prompt（对标 Toonflow generateVideo.ts）。

    Toonflow 模式：
      "请完全参照以下内容生成视频：${prompt}\n重要强调：\n风格高度保持..."

    注入层次：
    1. 资产引用（角色名=参考图）
    2. 风格锚定（Art Style 强制）
    3. 技术参数（时长/比例）

    Args:
        base_prompt:   原始 libtvPrompt
        style_name:     风格名称（如"赛博墨韵"）
        art_style:      Art Style 对象（dict，含 prompt/prompt_en）
        characters:     角色名列表（逗号分隔）
        scene:          场景名

    Returns:
        增强后的完整 prompt
    """
    parts = []

    # 1. 角色一致性锚定
    if characters:
        parts.append(f"[Character Reference]: {characters}")

    # 2. 场景锚定
    if scene:
        parts.append(f"[Scene Reference]: {scene}")

    # 3. 主体内容
    parts.append(f"[Content]: {base_prompt}")

    # 4. 风格强制（最高优先级）
    style_constraint = ""
    if art_style and isinstance(art_style, dict):
        # 从 art_style 提取中英文 prompt
        style_text = art_style.get("prompt", "")
        style_en = art_style.get("prompt_en", "")
        style_constraint = f"[Style Mandate]: Strictly maintain {style_name or 'specified'} art style. {style_en or style_text}"
    elif style_name:
        style_constraint = f"[Style Mandate]: Strictly maintain {style_name} art style."

    if style_constraint:
        parts.append(style_constraint)

    return "\n".join(parts)


def _find_column(header: list[str], candidates: list[str]) -> int | None:
    """从表头中查找匹配的列索引（不区分大小写）"""
    for i, h in enumerate(header):
        h_clean = h.lower().strip()
        for c in candidates:
            if c.lower() in h_clean or h_clean in c.lower():
                return i
    return None


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
    img1_dir: Path | None = None,
    optimizer=None,  # PromptOptimizer instance
    # ── 资产库参数（新增）────────────────────────────────────────
    shots: list[dict] | None = None,   # 分镜 dict 列表（带 characters/scene/props）
    asset_dir: Path | None = None,     # Stage 1.5 资产图目录（优先级高于 manifest）
    **kwargs,
) -> tuple[list[Path], list]:
    """使用 task_queue 并行批量生成（支持 prompt 优化 + 资产库参考图）"""

    # 延迟初始化 AssetLibrary
    asset_library = None
    try:
        from asset_library import AssetLibrary
        asset_library = AssetLibrary()
    except Exception:
        pass

    def gen_video_fn(
        shot_num: int,
        prompt: str,
        output_path_str: str,
        style: str,
        pvd: str,
        shot_img1: str,
        shot_references: list[dict],
        kw: dict,
    ):
        """闭包：避免 pickle 问题"""
        return generate_video(
            provider_name=pvd,
            prompt=prompt,
            output_path=Path(output_path_str),
            style_name=style,
            img1=shot_img1,
            references=shot_references,
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

        # ── P1 首帧图（旧逻辑，降级保留）─────────────────────────
        shot_img1 = ""
        if img1_dir and img1_dir.exists():
            for fmt in [f"shot_{i:02d}.png", f"shot_{i:02d}.jpg",
                        f"shot_{i:03d}.png", f"shot_{i:03d}.jpg"]:
                p = img1_dir / fmt
                if p.exists():
                    shot_img1 = str(p.resolve())
                    break

        # ── 资产库参考图（新逻辑，打通核心）─────────────────────
        shot_references: list[dict] = []
        if shots and i - 1 < len(shots):
            shot_dict = shots[i - 1]
            shot_references = resolve_shot_references(
                shot=shot_dict,
                asset_library=asset_library,
                asset_dir=asset_dir,
            )
            # P1 图作为额外 reference_image（如果未被 manifest 图覆盖）
            if shot_img1 and not any(r.get("url") == shot_img1 for r in shot_references):
                from adapters.video_adapter_base import IMAGE_ROLE_REFERENCE
                shot_references.append({
                    "url": shot_img1,
                    "role": IMAGE_ROLE_REFERENCE,
                    "label": f"分镜图-shot_{i:03d}",
                    "asset_name": "",
                    "asset_type": "storyboard",
                })

        # 提示词优化（video 模式，在入队前主进程执行）
        optimized_prompt = prompt
        if optimizer:
            try:
                optimized_prompt = optimizer.optimize(prompt, mode="video", dry_run=False)
                print(f"  [OPT] shot {i:03d}: {optimized_prompt[:60]}...", file=sys.stderr)
            except Exception as e:
                print(f"  [OPT] shot {i:03d} 优化失败: {e}", file=sys.stderr)
                optimized_prompt = prompt

        task_id_gen = queue.add(
            name=f"{task_name_prefix}-shot-{i:03d}",
            fn=gen_video_fn,
            shot_num=i,
            prompt=optimized_prompt,
            output_path_str=str(output_path),
            style=style_name,
            pvd=provider_name,
            shot_img1=shot_img1,
            shot_references=shot_references,
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
    # ── P1 图生视频（img1_dir = Stage 3 P1 输出目录）───────────────
    img1_dir: Path | None = None,
    # ── 提示词优化 ─────────────────────────────────────────────────
    optimize_prompts: bool = False,
    # ── 资产库（打通关键：Stage 1.5 输出目录，含 manifest.json）───
    asset_dir: Path | None = None,
    **kwargs,
) -> list[Path]:
    """从分镜脚本批量生成视频

    若 img1_dir 存在（Stage 3 P1 输出目录），自动为每个镜头匹配 P1 图片作为首帧参考。
    若 asset_dir 存在（Stage 1.5 输出目录），优先从 manifest.json 查资产参考图注入视频。
    若 optimize_prompts=True，使用 PromptOptimizer（video 模式）增强每个 libtvPrompt。
    P1 图片命名规范：shot_01.png, shot_02.png, ...
    """
    if not shots_file.exists():
        raise FileNotFoundError(f"分镜文件不存在：{shots_file}")

    content = shots_file.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 提示词优化器（延迟初始化）
    optimizer = None
    if optimize_prompts:
        try:
            sys.path.insert(0, str(BASE_DIR / "config"))
            from prompt_optimizer import PromptOptimizer
            optimizer = PromptOptimizer()
            print(f"  [OPT] PromptOptimizer 已就绪（mode=video）", file=sys.stderr)
        except Exception as e:
            print(f"  [OPT] PromptOptimizer 初始化失败: {e}", file=sys.stderr)

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
    col_idx = None
    fallback_used = None
    try:
        col_idx = header.index(prompt_column)
    except ValueError:
        # 优先精确匹配 libtvPrompt（视频专用），降级 imagePrompt（质量较低）
        for i, h in enumerate(header):
            if "libtvprompt" in h.lower():
                col_idx = i
                fallback_used = "libtvPrompt"
                break
        if col_idx is None:
            for i, h in enumerate(header):
                if h.lower() in ("imageprompt", "prompt", "videoprompt"):
                    col_idx = i
                    fallback_used = "imagePrompt (no libtvPrompt available — video quality may suffer)"
                    break
        if col_idx is None:
            raise ValueError(f"找不到列 '{prompt_column}'，表头：{header}")

    actual_col = header[col_idx]
    if fallback_used:
        print(f"⚠️  找不到 '{prompt_column}' 列，降级使用：'{actual_col}' — {fallback_used}", file=sys.stderr)
    print(f"📋 找到 {len(rows)-1} 个镜头，Prompt 列：'{actual_col}'", file=sys.stderr)

    # ── 解析分镜字典列表（用于资产库查询）────────────────────────
    # 从表头推断列位置
    shot_dicts: list[dict] = []
    char_col = _find_column(header, ["characters", "主体", "出场人物"])
    scene_col = _find_column(header, ["scene", "场景", "场景名"])
    props_col = _find_column(header, ["props", "道具"])

    for row in rows[1:]:
        shot_dict: dict = {"characters": [], "scene": "", "props": []}
        # 解析 characters 列（可能为空字符串）
        if char_col is not None and char_col < len(row):
            names = row[char_col].strip()
            shot_dict["characters"] = [n.strip() for n in names.split("/") if n.strip()]
        if scene_col is not None and scene_col < len(row):
            shot_dict["scene"] = row[scene_col].strip()
        if props_col is not None and props_col < len(row):
            props = row[props_col].strip()
            shot_dict["props"] = [p.strip() for p in props.split("/") if p.strip()]
        shot_dicts.append(shot_dict)

    print(f"  📋 资产库查询：{len(shot_dicts)} 个镜头已解析 characters/scene/props", file=sys.stderr)

    # 使用 task_queue 并行执行（可选降级）
    use_queue = max_workers > 1
    if use_queue:
        print(f"🔄 启用任务队列（并发 {max_workers}，最大重试 {max_retries}）", file=sys.stderr)
        # 解析 asset_dir（显式参数优先，否则从 img1_dir 推导）
        resolved_asset_dir: Path | None = asset_dir
        if resolved_asset_dir is None and img1_dir is not None:
            resolved_asset_dir = img1_dir.parent / "assets"
        results, task_queue_results = _batch_with_queue(
            rows[1:], col_idx, output_dir,
            provider_name, max_workers, max_retries,
            emitter, task_id, task_name_prefix, style_name,
            img1_dir=img1_dir,
            optimizer=optimizer,
            shots=shot_dicts,
            asset_dir=resolved_asset_dir,
            **kwargs,
        )
    else:
        # 延迟初始化 AssetLibrary
        asset_library = None
        try:
            from asset_library import AssetLibrary
            asset_library = AssetLibrary()
        except Exception:
            pass

        # 解析 asset_dir（显式参数优先，否则从 img1_dir 推导）
        resolved_asset_dir: Path | None = asset_dir
        if resolved_asset_dir is None and img1_dir is not None:
            resolved_asset_dir = img1_dir.parent / "assets"

        results = []
        for i, row in enumerate(rows[1:], 1):
            if col_idx >= len(row):
                continue
            prompt = row[col_idx].strip()
            if not prompt:
                continue

            # 提示词优化层（video 模式）
            if optimizer:
                try:
                    prompt = optimizer.optimize(prompt, mode="video", dry_run=False)
                    print(f"  [OPT] shot {i:03d} 优化后: {prompt[:60]}...", file=sys.stderr)
                except Exception as e:
                    print(f"  [OPT] shot {i:03d} 优化失败: {e}", file=sys.stderr)

            # 查找 P1 首帧图
            shot_img1 = ""
            if img1_dir and img1_dir.exists():
                for fmt in [f"shot_{i:02d}.png", f"shot_{i:02d}.jpg",
                            f"shot_{i:03d}.png", f"shot_{i:03d}.jpg"]:
                    p = img1_dir / fmt
                    if p.exists():
                        shot_img1 = str(p.resolve())
                        break

            # ── 资产库查询（新逻辑，打通核心）─────────────────────
            shot_dict = shot_dicts[i - 1] if i - 1 < len(shot_dicts) else {}
            shot_references = resolve_shot_references(
                shot=shot_dict,
                asset_library=asset_library,
                asset_dir=resolved_asset_dir,
            )
            # 合并 P1 图
            if shot_img1 and not any(r.get("url") == shot_img1 for r in shot_references):
                from adapters.video_adapter_base import IMAGE_ROLE_REFERENCE
                shot_references.append({
                    "url": shot_img1,
                    "role": IMAGE_ROLE_REFERENCE,
                    "label": f"分镜图-shot_{i:03d}",
                    "asset_name": "",
                    "asset_type": "storyboard",
                })

            output_path = output_dir / f"shot_{i:03d}.mp4"
            print(f"\n[镜头 {i:03d}] → {output_path.name}", file=sys.stderr)
            if shot_references:
                print(f"  📷 资产参考图：{len(shot_references)} 张", file=sys.stderr)
                for r in shot_references:
                    print(f"    [{r.get('role', 'ref')}] {r.get('label', r.get('asset_name', '?'))}", file=sys.stderr)
            elif shot_img1:
                print(f"  📷 首帧参考：{Path(shot_img1).name}", file=sys.stderr)

            try:
                generate_video(
                    provider_name=provider_name,
                    prompt=prompt,
                    output_path=output_path,
                    style_name=style_name,
                    img1=shot_img1,
                    references=shot_references if shot_references else None,
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
    # ── 资产库参考图（打通关键）──────────────────────────────────
    references: list[dict] | None = None,
    shot: dict | None = None,   # 可选，直接传 shot dict 替代 references
    asset_dir: Path | None = None,  # 备选：从目录扫描资产图
    # ── 追踪参数（可选）─────────────────────────────────────────────
    emitter=None,
    task_id: str | None = None,
    task_name: str = "video-gen",
    **kwargs,
) -> VideoResult:
    """生成视频（统一入口，支持多参考图）"""
    registry = get_registry()
    adapter = registry.get(provider_name)

    # 更新配置
    adapter.config.duration = duration
    adapter.config.watermark = watermark
    adapter.config.aspect_ratio = aspect_ratio

    # 自动模型选型（video_model_registry）
    # 若未指定 model，使用 select_video_model 自动匹配最优模型
    if not model:
        try:
            from config.video_model_registry import select_video_model
            selected = select_video_model(
                has_audio=None,        # 不限定音频（由 adapter 决定）
                duration=duration,
                aspect_ratio=aspect_ratio,
                mode="T2V" if not final_refs else "I2V",
            )
            if selected and selected.manufacturer == provider_name:
                model = selected.model_id
                print(f"  [Registry] 自动选型：{selected.name}", file=sys.stderr)
        except Exception:
            pass

    # 风格锚定 + prompt 增强
    art_style_obj = None
    if style_name:
        art_style_obj = get_style(style_name)
        if art_style_obj:
            print(f"  🎨 风格锚定：{style_name}", file=sys.stderr)

    # ── 解析 references ────────────────────────────────────────────
    final_refs: list[dict] = list(references) if references else []

    # 如果传的是 shot dict，直接在函数内解析（简化调用方）
    if not final_refs and shot:
        # 延迟导入 AssetLibrary（避免硬依赖）
        asset_library = None
        try:
            from asset_library import AssetLibrary
            asset_library = AssetLibrary()
        except Exception:
            pass

        final_refs = resolve_shot_references(shot, asset_library, asset_dir)

    # 注入 @图N Reference Section 到 prompt（日志/debug 用）
    enhanced_prompt, _ = build_video_prompt_with_references(
        base_prompt=prompt,
        references=final_refs,
        style_name=style_name,
        art_style=art_style_obj,
    )

    if emitter and task_id:
        emitter.emit_task_start(task_name, params={"prompt": prompt[:50], "provider": provider_name})

    print(f"\n🎬 生成视频", file=sys.stderr)
    print(f"  适配器：{provider_name}", file=sys.stderr)
    print(f"  模型：{model or adapter.default_video_model}", file=sys.stderr)
    print(f"  时长：{duration}s | 比例：{aspect_ratio} | 水印：{watermark}", file=sys.stderr)
    print(f"  参考图：{len(final_refs)} 张", file=sys.stderr)
    for r in final_refs:
        print(f"    [{r.get('role', 'ref')}] {r.get('label', r.get('asset_name', '?'))}", file=sys.stderr)
    print(f"  Prompt：{enhanced_prompt[:80]}{'...' if len(enhanced_prompt) > 80 else ''}", file=sys.stderr)

    result = adapter.generate_video(
        prompt=enhanced_prompt,
        output_path=output_path,
        img1=img1 or None,
        img2=img2 or None,
        duration=duration,
        model=model or None,
        references=final_refs if final_refs else None,
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
    img1_dir: Path | None = None,
    optimize_prompts: bool = False,
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
        img1_dir: P1 阶段输出目录（shots/images/），自动匹配 shot_XX.png 作为首帧参考图

    Returns:
        {"generated": N, "failed": M, "files": [file_paths], "summary": {...}}
    """
    base = (output_dir or (BASE_DIR / "outputs")).resolve()
    video_dir = base / episode / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)

    try:
        rel_video_dir = video_dir.relative_to(BASE_DIR)
    except ValueError:
        rel_video_dir = video_dir

    print(f"\n🎬 Stage 5: 视频生成")
    print(f"  集数：{episode}")
    print(f"  分镜脚本：{shots_path.name}")
    print(f"  输出目录：{rel_video_dir}")
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

    if img1_dir:
        try:
            print(f"  📷 P1 首帧参考目录：{img1_dir.relative_to(BASE_DIR)}")
        except ValueError:
            print(f"  📷 P1 首帧参考目录：{img1_dir}")

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
            img1_dir=img1_dir,
            optimize_prompts=optimize_prompts,
            asset_dir=img1_dir.parent / "assets" if img1_dir else None,
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
    parser.add_argument("--test-model",
                        metavar="MODEL_ID",
                        help="检测指定模型是否可用（如 doubao-seedance-2-0-260128）")

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


def test_model_availability(adapter, model: str) -> tuple[bool, str]:
    """
    检测指定模型是否可用。

    实现：尝试用该模型创建一个最小任务，通过返回结果判断。
    Doubao → POST /contents/generations/tasks
    Kling  → 依赖 KlingAdapter 的健康检查

    返回：(ok: bool, reason: str)
    """
    try:
        # Doubao 适配器
        if hasattr(adapter, "_create_video_task"):
            # 最小化测试：发一个 5 秒测试任务
            task_id = adapter._create_video_task(
                prompt="test --wm true --dur 5",
                img1=None, img2=None, duration=5, model=model,
            )
            return True, task_id

        # 通用健康检查
        if hasattr(adapter, "health_check") and adapter.health_check():
            return True, "health_check passed"

        return False, "unknown adapter type"

    except Exception as e:
        err = str(e)
        if "401" in err or "authentication" in err.lower():
            return False, "API Key 无效或未设置"
        if "403" in err:
            return False, "权限不足（余额可能为 0）"
        if "404" in err:
            return False, f"模型 {model} 不存在（404）"
        if "400" in err:
            return False, f"模型 {model} 参数错误（400）：{err[:200]}"
        if "429" in err:
            return False, "限流（429）"
        return False, err[:300]


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

    # 测试指定模型可用性
    if args.test_model:
        print(f"检测模型：{args.test_model}", file=sys.stderr)
        model = args.test_model
        # 根据模型前缀推断提供商
        if "seedance" in model.lower() or "seedream" in model.lower() or "doubao" in model.lower():
            provider = "doubao"
        elif "kling" in model.lower():
            provider = "kling"
        else:
            provider = args.provider

        adapter = registry.get(provider)
        if adapter is None:
            print(f"❌ 提供商 {provider} 未注册", file=sys.stderr)
            sys.exit(1)

        print(f"提供商：{provider}", file=sys.stderr)
        ok, reason = test_model_availability(adapter, model)
        if ok:
            print(f"\n✅ 模型 {model} 可用", file=sys.stderr)
        else:
            print(f"\n❌ 模型 {model} 不可用：{reason}", file=sys.stderr)
            sys.exit(1)
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
