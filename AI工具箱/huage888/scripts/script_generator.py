#!/usr/bin/env python3
"""
script_generator.py — 剧本生成器（outline → script）

对标 Toonflow t_outline → t_script 流程：
- 输入：EpisodeOutline（大纲 JSON） + 小说原文（可无）
- 处理：调用 qwen-max，按"起承转合"四段结构生成纯台词剧本
- 输出：保存到 task_db.scripts + `outputs/{episode}/{episode}-script.md`

格式要求：
- 场景切换用 `=== 场景名 ===` 标注
- 台词格式：`角色：台词`
- 旁白/动作：`- [旁白] ...` / `- [动作] ...`
- 每场 ≤ 30 句对白，控制节奏

用法：
  python3 scripts/script_generator.py \
    --outline outputs/S01E01/S01E01-outline.md \
    --novel docs/小说.txt \
    --project 漠玫传 \
    --episode S01E01 \
    --output outputs/S01E01/S01E01-script.md
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.outline_schema import EpisodeOutline
from pydantic import BaseModel
from scripts.task_db import TaskDB

BASE_DIR = Path(__file__).parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# Schema：剧本结构
# ─────────────────────────────────────────────────────────────────────────────

class ScriptScene(BaseModel):
    """单场剧本"""
    scene_index: int
    scene_name: str
    emotional_tone: str          # 本场情绪基调
    key_event: str               # 属于哪个 keyEvent（起/承/转/合）
    lines: list[str]             # 纯台词行


class ScriptDocument(BaseModel):
    """完整剧本"""
    episode: str
    title: str
    emotional_curve: str         # 全局情绪曲线
    scenes: list[ScriptScene]


# ─────────────────────────────────────────────────────────────────────────────
# 辅助
# ─────────────────────────────────────────────────────────────────────────────

def extract_json_from_markdown(content: str) -> str:
    """提取 Markdown 中的 JSON 块"""
    import re
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, content, re.DOTALL)
    if not matches:
        raise ValueError("Markdown 中未找到 ```json ``` 代码块")
    return matches[-1].strip()


def load_outline(outline_path: Path) -> EpisodeOutline:
    content = outline_path.read_text(encoding="utf-8")
    json_str = extract_json_from_markdown(content)
    data = json.loads(json_str)
    return EpisodeOutline.model_validate(data)


def build_script_prompt(outline: EpisodeOutline, novel_text: str = "") -> str:
    """
    构建生成剧本的系统+用户 prompt。

    关键要素：
    - 角色说话风格锚点（从 outline.characters 提取）
    - 情绪曲线（起承转合）
    - 核心矛盾
    - 小说原文（若有，用于台词创作）
    """
    # 角色说话风格（从 characters 字段的 description 提取）
    char_speaking_styles = []
    for char in outline.characters:
        # 尝试从 description 中提取语气信息
        desc = char.description
        char_speaking_styles.append(f"- **{char.name}**：{desc[:100] if desc else '标准对话'}")
    char_section = "\n".join(char_speaking_styles) if char_speaking_styles else "（无角色风格说明）"

    # 核心矛盾
    core_conflict = outline.coreConflict

    # 情绪曲线
    emotional_curve = outline.emotionalCurve

    # 起承转合
    key_events = outline.keyEvents
    if len(key_events) == 4:
        ke_section = "\n".join(
            f"- **{label}**：{desc}"
            for label, desc in zip(["起", "承", "转", "合"], key_events)
        )
    else:
        ke_section = "\n".join(f"- {ke}" for ke in key_events)

    # 小说原文（若有，用于参考台词风格）
    novel_section = f"\n\n## 小说原文（参考用）\n\n{novel_text[:5000]}" if novel_text else ""

    # 场景列表（用于场景名称）
    scene_names = [s.name for s in outline.scenes]
    scene_section = "\n".join(f"- {name}" for name in scene_names)

    prompt = f"""你是资深短剧编剧，负责将大纲转化为**纯台词剧本**。

## 大纲信息

**集数**：{outline.episodeIndex}
**标题**：{outline.title}
**核心矛盾**：{core_conflict}
**情绪曲线**：{emotional_curve}

## 角色说话风格

{char_section}

## 起承转合结构（4个段落，各需 ≥ 1 场）

{ke_section}

## 可用场景

{scene_section}

## 剧本格式规范

```
=== 场景1：场景名 ===
[情绪基调：本场情绪]
- 角色A：台词
- 角色B：台词
- [旁白] 旁白内容
- [动作] 动作描述

=== 场景2：场景名 ===
...
```

**严格要求**：
1. 每场控制在 10-25 句对白（含旁白/动作）
2. 台词必须符合角色说话风格（从角色风格表中选择）
3. 场景切换必须用 `=== 场景名 ===` 标注
4. 禁止出现 outline 中未列出的角色
5. 禁止出现违反视觉圣经的场景
6. 金句必须从小说原文中提取（若有原文），否则原创但要 ≤ 15 字

{novel_section}

## 输出要求

直接输出完整剧本 Markdown，不需要 JSON 包裹。确保 4 个 keyEvent 全部覆盖。"""

    return prompt


def call_qwen_script(user_prompt: str, output_path: Path, model: str = "qwen-max") -> bool:
    """调用 qwen_pipeline.py 生成剧本"""
    cmd = [
        sys.executable,
        str(BASE_DIR / "config" / "qwen_pipeline.py"),
        "--agent", "director",          # director 的 system prompt 含讲戏指导
        "--user", user_prompt,
        "--output", str(output_path),
        "--no-emit",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [ERROR] {result.stderr[:300]}", file=sys.stderr)
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# ScriptGenerator
# ─────────────────────────────────────────────────────────────────────────────

class ScriptGenerator:
    """
    剧本生成器

    工作流：
      outline + novel_text → qwen-max → script.md + task_db.scripts
    """

    def __init__(self, db: TaskDB | None = None):
        self._db = db or TaskDB()

    def generate(
        self,
        outline: EpisodeOutline,
        novel_text: str = "",
        project_id: int | None = None,
        episode: str = "S01E01",
        output_path: Path | None = None,
        dry_run: bool = False,
    ) -> Path:
        """
        生成剧本

        Args:
            outline: EpisodeOutline 对象
            novel_text: 小说原文（可选，用于台词参考）
            project_id: 项目 ID（用于 DB 存储）
            episode: 集数标识
            output_path: 输出文件路径
            dry_run: 不调用 API，仅返回 prompt

        Returns:
            生成的剧本文件路径
        """
        if output_path is None:
            output_path = BASE_DIR / "outputs" / episode / f"{episode}-script.md"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 构建 prompt
        user_prompt = build_script_prompt(outline, novel_text)

        if dry_run:
            print("[DRY] ====== 剧本生成 Prompt ======")
            print(user_prompt[:2000])
            print("...（省略）")
            return output_path

        # 调用 qwen-max
        print(f"[ScriptGenerator] 调用 qwen-max 生成剧本...")
        ok = call_qwen_script(user_prompt, output_path)
        if not ok:
            raise RuntimeError(f"qwen-max 调用失败，输出：{output_path}")

        # 存入 DB
        if project_id is not None:
            script_content = output_path.read_text(encoding="utf-8")
            # 找 outline_id
            outline_id = None
            if hasattr(outline, "episodeIndex"):
                outlines = self._db.get_outlines(project_id)
                for o in outlines:
                    odata = json.loads(o.get("data", "{}"))
                    if odata.get("episodeIndex") == outline.episodeIndex:
                        outline_id = o.get("id")
                        break
            self._db.save_script(
                project_id=project_id,
                name=episode,
                content=script_content,
                outline_id=outline_id,
            )
            print(f"[ScriptGenerator] 已保存到 DB（project_id={project_id}）")

        return output_path


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    parser = argparse.ArgumentParser(description="剧本生成器（outline → script）")
    parser.add_argument("--outline", required=True, help="大纲文件（Markdown，含 JSON 块）")
    parser.add_argument("--novel", help="小说原文文件（可选）")
    parser.add_argument("--project", help="项目名称（用于 DB 存储）")
    parser.add_argument("--project-id", type=int, help="项目 ID（优先于 --project）")
    parser.add_argument("--episode", default="S01E01", help="集数标识")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--dry-run", action="store_true", help="不调用 API，仅打印 prompt")
    args = parser.parse_args()

    # 加载 outline
    outline = load_outline(Path(args.outline))
    print(f"[ScriptGenerator] outline: {outline.title}（{outline.episodeIndex}集）")

    # 加载小说原文
    novel_text = ""
    if args.novel:
        novel_text = Path(args.novel).read_text(encoding="utf-8")
        print(f"[ScriptGenerator] 小说原文：{len(novel_text)} 字")

    # 解析 project_id
    db = TaskDB()
    project_id = args.project_id
    if project_id is None and args.project:
        projects = db.list_projects()
        for p in projects:
            if p.get("name") == args.project:
                project_id = p.get("id")
                break

    # 生成
    output_path = Path(args.output) if args.output else None
    gen = ScriptGenerator(db)
    path = gen.generate(
        outline=outline,
        novel_text=novel_text,
        project_id=project_id,
        episode=args.episode,
        output_path=output_path,
        dry_run=args.dry_run,
    )
    if not args.dry_run:
        print(f"✅ 剧本已生成：{path}")


if __name__ == "__main__":
    _cli()
