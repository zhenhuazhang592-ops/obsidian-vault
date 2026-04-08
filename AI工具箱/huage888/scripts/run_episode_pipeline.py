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
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── 路径配置 ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent

# ── .env 自动加载（优先级：环境变量 > .env 文件）───────────────────
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
    session_id: str | None = None,
    max_history: int = 10,
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
    if session_id:
        cmd += ["--session-id", session_id]
        cmd += ["--max-history", str(max_history)]

    print(f"\n{'[DRY] ' if dry_run else ''}→ qwen_pipeline --agent {agent}")
    print(f"    输出: {output_path.resolve().relative_to(BASE_DIR.resolve())}")
    if session_id:
        print(f"    session: {session_id} (max_history={max_history})")

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
    """调用 validate_outline.py 校验大纲，FAIL 直接阻断执行"""
    cmd = [sys.executable, str(VALIDATE_OUTLINE), str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [FAIL] outline 校验未通过 → 阻断执行")
        print(f"    {result.stdout[:300]}", file=sys.stderr)
        sys.exit(1)
    print(f"    [OK] outline 校验通过")
    return True


def check_asset_consistency(path: Path) -> bool:
    """调用 check_asset_consistency.py 校验分镜，FAIL 直接阻断执行"""
    cmd = [sys.executable, str(CHECK_ASSET), str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [FAIL] 分镜资产一致性校验未通过 → 阻断执行")
        print(f"    {result.stdout[:300]}", file=sys.stderr)
        sys.exit(1)
    print(f"    [OK] 分镜资产一致性校验通过")
    return True


# ── AI 审核函数（Toonflow Director Agent 对标）────────────────────────────────

def run_review(
    review_agent: str,
    content_path: Path,
    dry_run: bool = False,
    max_retries: int = 3,
) -> bool:
    """
    调用 AI 审核 Agent（script-review / art-review / storyboard-review），
    参考 Toonflow outlineScript-director 审核流程。

    流程：
      1. 读取待审核内容（outline / storyboard 文件）
      2. 调用 qwen_pipeline --agent {review_agent}
      3. 解析输出：PASS → 继续；FAIL → 输出问题清单 + 询问是否重写
      4. 最多重试 max_retries 次

    Returns:
        True = PASS（审核通过）
        False = FAIL 但已达重试上限，或用户选择跳过
    """
    agent_display = {
        "script-review": "讲戏本审核",
        "art-review": "资产审核",
        "storyboard-review": "分镜脚本审核",
    }
    display_name = agent_display.get(review_agent, review_agent)

    if not content_path.exists():
        print(f"    [WARN] 审核文件不存在：{content_path}，跳过审核")
        return True

    content = content_path.read_text(encoding="utf-8")
    # 截断过长内容（审核 prompt 有 max_tokens 上限）
    max_chars = 6000
    if len(content) > max_chars:
        content = content[:max_chars] + f"\n\n[... 内容截断，原始文件共 {len(content)} 字 ...]"

    review_user = (
        f"请严格审核以下内容，对照审核标准给出 PASS 或 FAIL：\n\n"
        f"## 待审核内容\n\n{content}\n\n"
        f"## 审核要求\n\n"
        f"严格按照 agents/{review_agent}.md 中的审核标准逐项检查，"
        f"输出格式：\n"
        f"  ## 审核结果：PASS 或 FAIL\n"
        f"  ## 问题清单（如有 FAIL）\n"
        f"  ## 通过项目\n"
    )

    for attempt in range(1, max_retries + 1):
        print(f"    ── {display_name} [尝试 {attempt}/{max_retries}] ──")

        if dry_run:
            print(f"    [DRY] 跳过审核")
            return True

        # 调用本地 call_qwen（封装了 qwen_pipeline.py CLI）
        # 审核结果直接打印到 stdout，不写文件
        result = call_qwen(
            agent=review_agent,
            user=review_user,
            output_path=Path("/dev/null"),  # 审核结果不落盘，统一打印
            dry_run=dry_run,
        )

        if result is None:
            print(f"    [WARN] 审核调用失败，跳过")
            return False

        # 解析审核结果（subprocess.CompletedProcess.stdout）
        output = result.stdout or ""

        # 判断 PASS / FAIL
        is_pass = "审核结果：PASS" in output or "审核结果: PASS" in output
        is_fail = "审核结果：FAIL" in output or "审核结果: FAIL" in output

        if is_pass:
            print(f"    ✅ {display_name} → PASS")
            # 打印通过项目摘要
            if "通过项目" in output:
                lines = output.splitlines()
                in_pass = False
                for line in lines:
                    if "通过项目" in line:
                        in_pass = True
                        continue
                    if in_pass and line.strip().startswith("##"):
                        break
                    if in_pass and line.strip():
                        print(f"       {line.strip()}")
            return True

        if is_fail:
            print(f"    ❌ {display_name} → FAIL")
            # 打印问题清单
            print(f"    ── 问题清单 ──")
            lines = output.splitlines()
            in_problems = False
            for line in lines:
                if "问题清单" in line:
                    in_problems = True
                    continue
                if in_problems and line.strip().startswith("##"):
                    break
                if in_problems and line.strip():
                    print(f"       {line.strip()}")
            print()
            if attempt < max_retries:
                print(f"    ↺ 审核失败，")
            continue

        # 无法解析结果
        print(f"    [WARN] 无法解析审核结果，视为 FAIL")
        if attempt < max_retries:
            print(f"    ↺ 重新审核 [尝试 {attempt + 1}/{max_retries}]")

    print(f"    ⚠️  审核已达重试上限（{max_retries}），继续执行（建议手动检查）")
    return False


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
    session_id: str | None = None,
    max_history: int = 10,
    storyline_path: Path | None = None,
) -> Path | None:
    """Stage 1: outline-agent 生成大纲

    若 storyline_path 存在（Stage 0 产出），优先使用其作为输入；
    否则回退到 script_arg（原始剧本）。
    """
    outline_dir = output_dir / episode
    outline_dir.mkdir(parents=True, exist_ok=True)
    outline_path = outline_dir / f"{episode}-outline.md"

    # ── Stage 0→1 数据流：优先使用 storyling.json ───────────────────────
    if storyline_path and storyline_path.exists():
        print(f"    [INFO] Stage 0→1：使用 storyline.json → {storyline_path.name}")
        script_content = storyline_path.read_text(encoding="utf-8")
        user_prompt = (
            f"项目：{project}，集数：{episode}\n"
            f"（以下为 Stage 0 生成的 storyline.json，请基于此生成结构化大纲）\n\n"
            f"{script_content}"
        )
    elif script_arg:
        # 回退：使用原始剧本文件或文本
        script_path = Path(script_arg)
        if script_path.exists() and script_path.is_file():
            script_content = script_path.read_text(encoding="utf-8")
        else:
            script_content = script_arg  # 视作直接传入的剧本文本
        user_prompt = (
            f"项目：{project}，集数：{episode}\n\n"
            f"以下是原始剧本内容，请生成结构化大纲：\n\n"
            f"{script_content}"
        )
    else:
        if dry_run:
            script_content = "[剧本内容占位 - dry-run 模式]"
            user_prompt = f"项目：{project}，集数：{episode}\n\n{script_content}"
        else:
            print("[ERROR] 请提供 --script 参数（剧本文件路径）或 --storyline 启用 Stage 0")
            return None

    result = call_qwen(
        agent="outline",
        user=user_prompt,
        output_path=outline_path,
        asset_library=asset_library,
        dry_run=dry_run,
        session_id=session_id,
        max_history=max_history,
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
    session_id: str | None = None,
    max_history: int = 10,
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
        session_id=session_id,
        max_history=max_history,
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
    optimize_prompts: bool = False,
) -> bool:
    """Stage 3: P1 — 逐 Shot 图生图"""
    print(f"\n{'[DRY] ' if dry_run else ''}→ Stage 3: P1 逐 Shot 图生图")
    if optimize_prompts:
        print(f"    [OPT] 提示词优化层已开启（T2I七维度）")

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
    if optimize_prompts:
        cmd.append("--optimize")

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
        "--model", "doubao-seedream-5-0-260128",
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
    img1_dir: Path | None = None,
    optimize_prompts: bool = False,
) -> dict:
    """Stage 5: 视频生成（支持 P1 首帧参考图 + 提示词优化）"""
    print(f"\n{'[DRY] ' if dry_run else ''}→ Stage 5: 视频生成")
    if optimize_prompts:
        print(f"    [OPT] 提示词优化层已开启（视频prompt增强）")
    if img1_dir and img1_dir.exists():
        print(f"    [INFO] 使用 P1 首帧参考图：{img1_dir}")

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
        img1_dir=img1_dir,
        optimize_prompts=optimize_prompts,
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
        "--skip-review",
        action="store_true",
        help="跳过 AI 审核阶段（script-review / storyboard-review）",
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
        default=False,
        help="跳过 Stage 5 视频生成（默认 False，即默认开启）",
    )
    stage.add_argument(
        "--run-video",
        action="store_true",
        help="执行 Stage 5：视频生成（默认开启，可用 --skip-video 跳过）",
    )
    stage.add_argument(
        "--optimize-prompts",
        action="store_true",
        default=bool(os.environ.get("HUAGE888_OPTIMIZE", "")),
        help="开启提示词优化层（T2I七维度 + 视频prompt增强）",
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
    parser.add_argument(
        "--report-level",
        default="stage",
        choices=["stage", "shot"],
        help="报告颗粒度：stage（默认，日常用）/ shot（精查用）",
    )

    args = parser.parse_args()

    # ── 初始化 ReportLogger ───────────────────────────────────────────────
    report_logger = None
    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        from report_logger import ReportLogger
        report_logger = ReportLogger(project=args.project, episode=args.episode)
        report_logger.log_pipeline_start(report_level=args.report_level)
        print(f"  📝 ReportLogger 已连接")
    except Exception as e:
        print(f"  [INFO] ReportLogger 不可用: {e}")

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
          f"review1({'skip' if args.skip_review else 'run'}) / "
          f"asset_images({'run' if args.run_asset_images else 'skip'}) / "
          f"storyboard({'skip' if args.skip_storyboard else 'run'}) / "
          f"review2({'skip' if args.skip_review else 'run'}) / "
          f"P1({'run' if args.run_p1 else 'skip'}) / "
          f"P2({'run' if args.run_p2 else 'skip'}) / "
          f"video({'run' if not args.skip_video else 'skip'})")
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

        # ── ReportLogger 埋点 ─────────────────────────────────────────
        if report_logger:
            report_logger.log_stage_end(
                stage=0, name="storyline",
                status="success" if storyline_path else "failed",
                output_file=_rel(storyline_path) if storyline_path else "",
            )
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
            session_id=args.session_id,
            max_history=args.max_history,
            storyline_path=storyline_path,
        )
        if outline_path is None and not args.dry_run:
            print("[ERROR] Stage 1 失败，停止执行")
            sys.exit(1)

        # ── Stage 1 审核（Toonflow Director Agent 对标）──────────────
        if outline_path and outline_path.exists() and not args.dry_run and not args.skip_review:
            print(f"\n[Review-1] script-review — 讲戏本质量审核")
            review_pass = run_review(
                review_agent="script-review",
                content_path=outline_path,
                dry_run=args.dry_run,
                max_retries=3,
            )
            if not review_pass:
                print(f"    [WARN] 讲戏本审核未通过，继续执行（建议手动修复）")
    else:
        outline_path = output_dir / args.episode / f"{args.episode}-outline.md"
        if not outline_path.exists() and not args.dry_run:
            print(f"[ERROR] --skip-outline 但文件不存在: {outline_path}")
            sys.exit(1)
        print(f"\n[Stage 1] SKIP（使用已有: {outline_path}）")

    if outline_path is None:
        outline_path = output_dir / args.episode / f"{args.episode}-outline.md"

    # ── Stage 1 埋点 ─────────────────────────────────────────────────
    # 放在 if/else 之后，只埋一次
    if report_logger:
        if args.skip_outline:
            report_logger.log_stage_end(stage=1, name="outline", status="skipped")
        else:
            _review_pass = (
                outline_path and outline_path.exists()
                and not args.dry_run and not args.skip_review
            )
            report_logger.log_stage_end(
                stage=1, name="outline",
                status="success" if outline_path else "failed",
                output_file=_rel(outline_path) if outline_path else "",
                review_result="PASS" if _review_pass else "WARNING",
                model="qwen-plus",
            )

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
        if report_logger:
            report_logger.log_stage_end(
                stage=1.5, name="asset_images",
                status="success" if asset_ok else "failed",
                model="doubao",
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
            session_id=args.session_id,
            max_history=args.max_history,
        )
        if shots_path is None and not args.dry_run:
            print("[ERROR] Stage 2 失败，停止执行")
            sys.exit(1)

        # ── Stage 2 审核（Toonflow storyboard-agent 对标）────────────
        if shots_path and shots_path.exists() and not args.dry_run and not args.skip_review:
            print(f"\n[Review-2] storyboard-review — 分镜脚本质量审核")
            # 先运行规则校验（快速）
            try:
                check_asset_consistency(shots_path)
            except SystemExit:
                print(f"    [WARN] 分镜资产一致性校验失败，继续 AI 审核")
            review_pass = run_review(
                review_agent="storyboard-review",
                content_path=shots_path,
                dry_run=args.dry_run,
                max_retries=3,
            )
            if not review_pass:
                print(f"    [WARN] 分镜脚本审核未通过，继续执行（建议手动修复）")
    else:
        shots_path = output_dir / args.episode / f"{args.episode}-shots.md"
        if not shots_path.exists() and not args.dry_run:
            print(f"[ERROR] --skip-storyboard 但文件不存在: {shots_path}")
            sys.exit(1)
        print(f"\n[Stage 2] SKIP（使用已有: {shots_path}）")

    if shots_path is None:
        shots_path = output_dir / args.episode / f"{args.episode}-shots.md"

    # ── Stage 2 埋点 ─────────────────────────────────────────────────
    # 放在 if/else 之后，只埋一次
    if report_logger:
        if args.skip_storyboard:
            report_logger.log_stage_end(stage=2, name="storyboard", status="skipped")
        else:
            _review2_pass = (
                shots_path and shots_path.exists()
                and not args.dry_run and not args.skip_review
            )
            report_logger.log_stage_end(
                stage=2, name="storyboard",
                status="success" if shots_path else "failed",
                output_file=_rel(shots_path) if shots_path else "",
                review_result="PASS" if _review2_pass else "WARNING",
                model="qwen-plus",
            )

    # ── Stage 3: P1 ─────────────────────────────────────────────────────
    p1_ok = True
    if args.run_p1:
        p1_ok = stage3_p1(
            shots_path=shots_path,
            outline_path=outline_path,
            episode=args.episode,
            output_dir=output_dir,
            dry_run=args.dry_run,
            optimize_prompts=args.optimize_prompts,
        )
        if report_logger:
            report_logger.log_stage_end(
                stage=3, name="p1",
                status="success" if p1_ok else "failed",
                model="doubao-seedream-4.5",
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
        if report_logger:
            report_logger.log_stage_end(
                stage=4, name="p2",
                status="success" if p2_ok else "failed",
                model="doubao-seedream-5-0-260128",
            )

    # ── Stage 5: video（默认开启，可用 --skip-video 跳过）────────────────
    video_ok = True
    video_result = {}
    # P1 首帧参考图目录：outputs/{episode}/shots/images/
    p1_images_dir: Path | None = None
    if not args.skip_video and shots_path and shots_path.exists():
        p1_images_dir = output_dir / args.episode / "shots" / "images"
        if not p1_images_dir.exists():
            p1_images_dir = None
            print(f"    [INFO] 未找到 P1 首帧图片目录（跳过 img1 传图）")
        else:
            print(f"    [INFO] 找到 P1 首帧图片目录：{p1_images_dir}")
        video_result = stage5_video(
            shots_path=shots_path,
            episode=args.episode,
            output_dir=output_dir,
            provider=args.video_provider,
            duration=args.video_duration,
            workers=args.workers,
            dry_run=args.dry_run,
            task_db=task_db,
            img1_dir=p1_images_dir,
            optimize_prompts=args.optimize_prompts,
        )
        video_ok = video_result.get("failed", 1) == 0
    elif not args.skip_video:
        print(f"\n[Stage 5] SKIP（需 shots 文件存在）")
    else:
        print(f"\n[Stage 5] SKIP（已用 --skip-video 跳过）")

    # ── ReportLogger 埋点 & 生成制作文档 ──────────────────────────────
    if report_logger:
        if not args.skip_video and shots_path and shots_path.exists():
            report_logger.log_stage_end(
                stage=5, name="video",
                status="success" if video_ok else "failed",
                model=args.video_provider,
            )
        else:
            report_logger.log_stage_end(stage=5, name="video", status="skipped")
        # ── 生成制作文档 ───────────────────────────────────────────
        try:
            import subprocess as _subprocess
            _subprocess.run([
                sys.executable,
                str(SCRIPT_DIR / "production_report.py"),
                "--project", args.project,
                "--episode", args.episode,
                "--report-level", args.report_level,
            ], check=False)
        except Exception as e:
            print(f"  [WARN] 制作文档生成失败: {e}")

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
