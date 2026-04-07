#!/usr/bin/env python3
"""
storyline_pipeline.py — 故事线生成 Stage 0

对应 Toonflow AI1 故事师（t_storyline 表）的行为：
读取原始剧本 → 分析章节节奏 → 输出结构化 storybeat 序列

用法：
  # CLI
  python3 scripts/storyline_pipeline.py \
    --script docs/剧本.md \
    --episode S01E01 \
    --project 漠玫传

  # 模块调用
  from storyline_pipeline import stage0_storyline

  path = stage0_storyline(
      script_input="...",
      episode="S01E01",
      project="漠玫传",
      task_db=db,
      conv_mgr=mgr,
  )
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ── 路径配置 ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
QWEN_PIPELINE = BASE_DIR / "config" / "qwen_pipeline.py"

sys.path.insert(0, str(BASE_DIR / "config"))
sys.path.insert(0, str(SCRIPT_DIR))

# ── 工具函数 ─────────────────────────────────────────────────────────────────

def extract_json_from_markdown(content: str) -> dict:
    """从 Markdown 提取 ```json ``` 块内容"""
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError("Markdown 中未找到 JSON 块")
    return json.loads(match.group(1).strip())


def validate_storyline(data: dict) -> list[str]:
    """
    校验 storyline JSON 格式。

    返回错误列表（空 = 校验通过）。
    """
    errors = []

    if "chapters" not in data or not isinstance(data["chapters"], list):
        errors.append("缺少 chapters 字段或类型错误")
        return errors

    if not data["chapters"]:
        errors.append("chapters 数组为空")
        return errors

    valid_beat_types = {"起", "承", "转", "合"}
    valid_emotions = {"铺垫", "期待", "紧张", "爆发", "释然", "悬念"}

    for i, chapter in enumerate(data["chapters"]):
        if "beats" not in chapter or not chapter["beats"]:
            errors.append(f"章节 {i+1} 缺少 beats 或为空")
            continue

        for j, beat in enumerate(chapter["beats"]):
            beat_type = beat.get("beat_type", "")
            if beat_type not in valid_beat_types:
                errors.append(f"章节 {i+1} beat {j+1}：beat_type={beat_type!r} 不在 起/承/转/合 中")

            desc = beat.get("description", "")
            if not desc:
                errors.append(f"章节 {i+1} beat {j+1}：缺少 description")
            elif len(desc) < 10:
                errors.append(f"章节 {i+1} beat {j+1}：description 过短（<10字）")

            shots = beat.get("shots_hint", 0)
            if not isinstance(shots, int) or shots < 1 or shots > 10:
                errors.append(f"章节 {i+1} beat {j+1}：shots_hint={shots} 超出范围（1-10）")

            emotion = beat.get("emotional_temperature", "")
            if emotion and emotion not in valid_emotions:
                errors.append(
                    f"章节 {i+1} beat {j+1}：emotional_temperature={emotion!r} "
                    f"不在 {valid_emotions} 中"
                )

    return errors


# ── stage0 函数 ──────────────────────────────────────────────────────────────

def stage0_storyline(
    script_input: str | Path,
    episode: str,
    project: str,
    task_db=None,
    conv_mgr=None,
    emitter=None,
    output_base: Path | None = None,
    dry_run: bool = False,
) -> Path | None:
    """
    Stage 0: 剧本 → 故事线 JSON

    Args:
        script_input: 剧本文本或文件路径
        episode: 集数（如 S01E01）
        project: 项目名（如 漠玫传）
        task_db: TaskDB 实例（可选，用于任务追踪）
        conv_mgr: ConversationManager 实例（可选，用于对话历史）
        emitter: EventEmitter 实例（可选，用于事件推送）
        output_base: 输出根目录（默认 .huage888/）
        dry_run: 是否 dry-run（不调用 API）

    Returns:
        storyline.json 文件路径，或 None（失败）
    """
    # ── 输出目录 ──────────────────────────────────────────────────────────
    base = output_base or (BASE_DIR / ".huage888")
    storyline_dir = base / "storylines" / project / episode
    storyline_dir.mkdir(parents=True, exist_ok=True)
    storyline_path = storyline_dir / "storyline.json"

    # ── 读取剧本 ──────────────────────────────────────────────────────────
    if isinstance(script_input, Path) and script_input.exists() and script_input.is_file():
        script_content = script_input.read_text(encoding="utf-8")
        script_src = str(script_input.relative_to(BASE_DIR))
    else:
        script_content = str(script_input)
        script_src = "<直接文本>"

    if not script_content.strip():
        print("[ERROR] 剧本内容为空", file=sys.stderr)
        return None

    print(f"\n📖 Stage 0: 故事线生成")
    print(f"  集数：{episode}")
    print(f"  项目：{project}")
    print(f"  剧本：{script_src}")
    print(f"  输出：{storyline_path.relative_to(BASE_DIR)}")

    if dry_run:
        print(f"\n[DRY] 跳过 API 调用")
        print(f"  [DRY] 剧本前80字：{script_content[:80]}...")
        return storyline_path

    # ── 构建 user prompt ──────────────────────────────────────────────────
    user_prompt = (
        f"项目：{project}，集数：{episode}\n\n"
        f"请分析以下剧本，生成结构化故事线（JSON 格式）：\n\n"
        f"{script_content}"
    )

    # ── 调用 storyline agent ──────────────────────────────────────────────
    from qwen_pipeline import call_qwen_with_conversation, build_system_prompt

    # session 管理
    conv_session_id = None
    if conv_mgr:
        conv_session_id = conv_mgr.new_session("storyline")
        print(f"  对话 session：{conv_session_id}", file=sys.stderr)

    # task 管理
    task_id = None
    if task_db:
        try:
            from task_db import TaskState
            task_id = task_db.create(
                task_type="qwen",
                name=f"stage0_storyline_{episode}",
                params={"episode": episode, "project": project},
                episode=episode,
                stage="storyline",
            )
            if emitter:
                emitter.emit_task_start(
                    f"stage0_storyline_{episode}",
                    params={"episode": episode, "project": project},
                )
                task_db.update(task_id, TaskState.RUNNING)
        except Exception as e:
            print(f"  [WARN] task_db 记录失败: {e}", file=sys.stderr)
            task_id = None

    try:
        # 调用 API（带对话历史）
        content = call_qwen_with_conversation(
            agent="storyline",
            user=user_prompt,
            session_id=conv_session_id or "",
            conv_mgr=conv_mgr,
            output_path=None,  # 自己处理写入
            emitter=emitter,
            task_id=task_id,
            task_name=f"stage0_storyline_{episode}",
        )

        # ── 解析 JSON ────────────────────────────────────────────────────
        storyline_data = extract_json_from_markdown(content)

        # 补充元数据
        storyline_data.setdefault("project", project)
        storyline_data.setdefault("episode", episode)

        # ── 校验 ─────────────────────────────────────────────────────────
        errors = validate_storyline(storyline_data)
        if errors:
            print(f"\n  [WARN] storyline 校验发现问题（非阻断）：")
            for err in errors[:5]:
                print(f"    ⚠️  {err}")
        else:
            print(f"  [OK] storyline 格式校验通过")

        # ── 写入文件 ────────────────────────────────────────────────────
        storyline_path.write_text(
            json.dumps(storyline_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n  ✅ 故事线已保存：{storyline_path.relative_to(BASE_DIR)}")
        print(f"     章节数：{len(storyline_data.get('chapters', []))}")

        # ── 更新 task 状态 ───────────────────────────────────────────────
        if task_db and task_id:
            try:
                from task_db import TaskState
                task_db.update(
                    task_id, TaskState.SUCCESS,
                    result={"path": str(storyline_path), "chapters": len(storyline_data.get("chapters", []))},
                )
            except Exception:
                pass

        return storyline_path

    except Exception as e:
        print(f"\n  ❌ Stage 0 失败: {e}", file=sys.stderr)

        if task_db and task_id:
            try:
                from task_db import TaskState
                task_db.update(task_id, TaskState.FAILED, error=str(e))
            except Exception:
                pass

        return None


# ── CLI 入口 ─────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="Stage 0: 故事线生成")
    parser.add_argument("--script", required=True, help="剧本文件路径或直接文本")
    parser.add_argument("--episode", required=True, help="集数（如 S01E01）")
    parser.add_argument("--project", required=True, help="项目名")
    parser.add_argument("--output-base", default=None, help="输出根目录")
    parser.add_argument("--dry-run", action="store_true", help="不调用 API")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # 可选初始化
    task_db = None
    conv_mgr = None

    try:
        from task_db import TaskDB
        task_db = TaskDB()
    except Exception as e:
        print(f"[INFO] task_db 不可用: {e}", file=sys.stderr)

    try:
        from conversation_manager import ConversationManager
        conv_mgr = ConversationManager()
    except Exception as e:
        print(f"[INFO] conversation_manager 不可用: {e}", file=sys.stderr)

    path = stage0_storyline(
        script_input=args.script,
        episode=args.episode,
        project=args.project,
        task_db=task_db,
        conv_mgr=conv_mgr,
        output_base=Path(args.output_base) if args.output_base else None,
        dry_run=args.dry_run,
    )

    if path:
        sys.exit(0)
    else:
        sys.exit(1)
