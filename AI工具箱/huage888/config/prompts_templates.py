#!/usr/bin/env python3
"""
prompts_templates.py — huage888 提示词模板库（对标 Toonflow t_prompts 表）

功能：
  - 主 Agent 提示词模板（大纲师 / 分镜师 / 导演）
  - Sub-Agent 提示词模板（故事师 / 片段师 / 分镜师）
  - Tool 调用提示词模板
  - 支持 custom_value 覆盖（TaskDB prompts 表集成）
  - 支持通过 TaskDB 持久化自定义模板

模板结构（对标 Toonflow）：
  {
    "code": str,           # 唯一标识（dot notation）
    "name": str,           # 人类可读名称
    "type": str,           # mainAgent / subAgent / tool / system
    "parent_code": str,    # 父模板 code（subAgent 用）
    "default_value": str,   # 默认 prompt 内容
    "custom_value": str,    # 用户覆盖（可空）
    "description": str,     # 说明
  }

用法：

  # 直接使用（Python）
  from config.prompts_templates import (
      get_template, apply_template, list_templates, render_agent_system_prompt,
  )
  prompt = get_template("outlineScript-main")
  print(prompt["value"])  # custom_value 优先于 default_value

  # CLI
  python3 config/prompts_templates.py get outlineScript-main
  python3 config/prompts_templates.py list --type mainAgent
  python3 config/prompts_templates.py render outlineScript-main --vars "project=漠玫传,episode=S01E01"
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

# ── TaskDB 集成（延迟导入）───────────────────────────────────────────
_TASK_DB = None


def _lazy_task_db():
    global _TASK_DB
    if _TASK_DB is None:
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
            from task_db import TaskDB
            _TASK_DB = TaskDB()
        except Exception:
            pass
    return _TASK_DB


# ═══════════════════════════════════════════════════════════════════════════════════
# 模板数据（内嵌默认模板，运行时可从 TaskDB 覆盖）
# ═══════════════════════════════════════════════════════════════════════════════════

PROMPT_TEMPLATES: list[dict] = [
    # ───────────────────────────────────────────────────────────────────────────
    # 主 Agent 模板（mainAgent）
    # ───────────────────────────────────────────────────────────────────────────
    {
        "code": "outlineScript-main",
        "name": "大纲故事线主 Agent",
        "type": "mainAgent",
        "parent_code": None,
        "description": "大纲故事线协调 Agent，协调 AI1(故事师)、AI2(大纲师)、director(导演) 三个子 Agent 工作",
        "default_value": """# 大纲故事线主 Agent

## 角色
你是故事线和大纲的协调者，管理 AI1（故事师）、AI2（大纲师）和导演三个子 Agent 的工作流程。

## 约束
1. 故事线必须忠于原著剧本
2. 大纲 JSON 必须结构完整，字段齐全
3. 每个 keyEvent 必须有 visualHighlights
4. 不捏造剧本中未出现的人物/场景/道具

## 工作流程
1. 调用 AI1 故事师：分析剧本 → 生成故事线
2. 调用 AI2 大纲师：基于故事线 → 生成大纲 JSON
3. 调用导演审核：质量打分 → PASS/FAIL

## 输出
最终输出：结构化大纲 JSON（包含 characters/scenes/props/keyEvents）""",
    },
    {
        "code": "storyboard-main",
        "name": "分镜协调 Agent",
        "type": "mainAgent",
        "parent_code": None,
        "description": "分镜协调 Agent，管理 segmentAgent 和 shotAgent",
        "default_value": """# 分镜协调 Agent

## 角色
你是分镜脚本的协调者，管理 segmentAgent（片段师）和 shotAgent（分镜师）的工作流程。

## 约束
1. 分镜脚本忠实还原大纲 JSON
2. 主体 ID 精确匹配大纲 characters[].id
3. 场景 ID 精确匹配大纲 scenes[].id
4. 禁止捏造未在 JSON 中声明的资产

## 工作流程
1. 调用 segmentAgent：识别剧本关键片段 → 生成 segments
2. 调用 shotAgent：每个 segment → 多个镜头
3. 输出完整分镜 Markdown

## 输出
分镜脚本 Markdown（含表格 + 镜头详解）""",
    },

    # ───────────────────────────────────────────────────────────────────────────
    # Sub-Agent 模板（subAgent）
    # ───────────────────────────────────────────────────────────────────────────
    {
        "code": "outlineScript-a1",
        "name": "故事师",
        "type": "subAgent",
        "parent_code": "outlineScript-main",
        "description": "分析小说章节，生成故事线",
        "default_value": """# 故事师

## 角色
分析剧本章节，提取关键情节点，生成线性故事线。

## 输入
原始剧本文本

## 任务
1. 识别主要人物（列出 ID 和名字）
2. 识别主要场景（列出 ID 和名字）
3. 提取关键道具（列出 ID 和名字）
4. 按时间顺序排列关键情节点
5. 每个情节点标注：动作、场景、情绪变化

## 资产声明规则
- 人物首次出现时声明 → 格式：id=C001, name=漠玫
- 后续复用直接引用 ID，不得改名
- 禁止捏造剧本中不存在的人物""",
    },
    {
        "code": "outlineScript-a2",
        "name": "大纲师",
        "type": "subAgent",
        "parent_code": "outlineScript-main",
        "description": "根据故事线生成大纲 JSON",
        "default_value": """# 大纲师

## 角色
根据故事线输出结构化大纲 JSON。

## 约束
1. JSON 格式严格遵循 schema（见下方）
2. characters[]/scenes[]/props[] 必须完整
3. keyEvents[].visualHighlights 必须具体描述
4. 不得遗漏剧本中的任何主要资产

## JSON Schema
```json
{
  "title": "剧集标题",
  "episode": "S01E01",
  "summary": "一句话简介",
  "characters": [{"id": "C001", "name": "漠玫", "description": "..."}],
  "scenes": [{"id": "S001", "name": "赛博竹林", "description": "..."}],
  "props": [{"id": "P001", "name": "发光玉佩", "description": "..."}],
  "keyEvents": [
    {
      "index": 1,
      "title": "场景标题",
      "visualHighlights": "画面描述（3-5句话）",
      "dialogue": "关键台词（可选）"
    }
  ]
}
```""",
    },
    {
        "code": "outlineScript-director",
        "name": "导演审核",
        "type": "subAgent",
        "parent_code": "outlineScript-main",
        "description": "审核故事线和大纲的质量",
        "default_value": """# 导演审核

## 角色
审核故事线和大纲 JSON 的质量和完整性。

## 审核标准
1. 故事线连贯，无逻辑断层
2. JSON 格式完整，所有字段齐全
3. 资产引用准确（ID 与声明一致）
4. 视觉亮点描述具体可执行
5. 无捏造资产（对照剧本核查）

## 输出格式
```json
{
  "pass": true/false,
  "score": 1-10,
  "issues": ["问题1", "问题2"]
}
```""",
    },
    {
        "code": "storyboard-segment",
        "name": "片段师",
        "type": "subAgent",
        "parent_code": "storyboard-main",
        "description": "识别剧本关键片段，生成 segments",
        "default_value": """# 片段师

## 角色
将剧本切分为逻辑连续的片段（segment）。

## 约束
1. 每个 segment 有明确的开始和结束
2. segment 内镜头连续，场景统一
3. segment 数量控制在 3-8 个（短剧）
4. segment 之间有过渡描述

## 资产声明
- 每个 segment 开头标注使用的主角 ID 和场景 ID
- 不得引入未在大纲 JSON 中声明的资产""",
    },
    {
        "code": "storyboard-shot",
        "name": "分镜师",
        "type": "subAgent",
        "parent_code": "storyboard-main",
        "description": "生成电影级分镜提示词",
        "default_value": """# 分镜师

## 角色
基于 segment 生成电影级分镜提示词。

## 约束
1. 主体列必须使用大纲 JSON 中的精确 ID（如 C001）
2. 场景列必须使用大纲 JSON 中的精确 ID（如 S001）
3. 禁止用近义词替换（如"漠玫"不能写成"道姑"）
4. 禁止捏造未声明的资产
5. imagePrompt 必须包含：主体描述 + 场景描述 + 光影 + 情绪

## 输出格式
每个镜头：
| 镜头号 | 景别 | 运镜 | 画面描述 | imagePrompt |
""",
    },

    # ───────────────────────────────────────────────────────────────────────────
    # Tool 提示词模板（tool）
    # ───────────────────────────────────────────────────────────────────────────
    {
        "code": "generateImagePrompts",
        "name": "宫格分镜提示词生成",
        "type": "tool",
        "parent_code": None,
        "description": "为分镜脚本中的多个镜头批量生成图像 prompt",
        "default_value": """# 宫格分镜提示词生成

## 角色
为分镜脚本批量生成图像 prompt，用于宫格图合成。

## 输入
分镜脚本（Markdown 格式的镜头列表）

## 输出
每个镜头生成一个 JSON：
```json
{
  "shot_index": 1,
  "character": "C001",
  "scene": "S001",
  "imagePrompt": "完整的图像生成 prompt（包含主体+场景+光影+风格）",
  "negative_prompt": "反向 prompt（可选）"
}
```

## 规则
1. imagePrompt 锚定 Visual Bible 风格
2. 角色描述与大纲 JSON 一致（不得改名）
3. 场景描述与大纲 JSON 一致（不得改 ID）
4. 每个 prompt 独立完整，不引用其他镜头""",
    },
    {
        "code": "generateVideoPrompts",
        "name": "视频生成 prompt 优化",
        "type": "tool",
        "parent_code": None,
        "description": "将分镜脚本中的画面描述转化为视频生成 prompt",
        "default_value": """# 视频生成 prompt 优化

## 角色
将分镜画面描述转化为视频生成模型可执行的 prompt。

## 约束
1. 保留镜头核心动作（不少于 3 个动词）
2. 添加运动描述（camera movement / subject movement）
3. 风格锚定 Visual Bible
4. 长度控制在 200 字以内
5. 格式：动作描述 + 场景 + 风格

## 输出
单个 prompt 字符串（可直接用于 Doubao/Kling API）""",
    },

    # ───────────────────────────────────────────────────────────────────────────
    # System 提示词模板（system）
    # ───────────────────────────────────────────────────────────────────────────
    {
        "code": "system.asset-consistency",
        "name": "资产一致性强制规则",
        "type": "system",
        "parent_code": None,
        "description": "所有 Agent 必须遵守的资产一致性规则（硬性约束）",
        "default_value": """## 资产一致性强制规则（硬性约束，不得违反）

### 禁止规则
- ❌ 禁止捏造资产：不得生成任何未在上下文中声明的角色 ID、场景 ID、道具 ID
- ❌ 禁止近义词替换：主体名称必须与声明完全一致
- ❌ 禁止默认复用：未声明的资产不得出现

### 正确引用方式
| 资产类型 | 正确引用 | 禁止写法 |
|---------|---------|---------|
| 角色 | C001 | 漠玫 / 道姑 / 那位女子 |
| 场景 | S001 | 竹林 / 赛博竹林（除非 S001 名称包含"赛博竹林"）|
| 道具 | P001 | 玉佩 / 发光饰品 |

### 自检
输出前检查：
1. 所有角色 ID 是否在 characters[] 中声明
2. 所有场景 ID 是否在 scenes[] 中声明
3. 无新资产出现""",
    },
    {
        "code": "system.visual-bible-anchor",
        "name": "Visual Bible 风格锚定",
        "type": "system",
        "parent_code": None,
        "description": "视觉风格锚定规则（从 Visual Bible 继承）",
        "default_value": """## Visual Bible 风格锚定

### 当前项目风格
当前项目使用「赛博墨韵」风格：
- 核心元素：道姑髻 + 金色瞳孔数据流 + 青蓝色水墨眼线
- 场景：赛博竹林（竹竿嵌电路 + 青蓝发光粒子）
- 色调：深青蓝 + 墨黑 + 金色点缀
- 禁止：日系动漫大眼睛（除非角色有特殊设定）

### 质量标准
- 图像 prompt：主体 + 场景 + 光影 + 风格关键词
- 视频 prompt：动作 + 运镜 + 风格 + 时长
- 禁止空洞描述（如"美""帅"等主观词）
- 必须用结构化描述（颜色/材质/光影/构图）""",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════════
# 索引
# ═══════════════════════════════════════════════════════════════════════════════════

# code → template
_TPL_BY_CODE: dict[str, dict] = {t["code"]: t for t in PROMPT_TEMPLATES}


def get_template(code: str) -> dict | None:
    """
    获取模板（custom_value 优先于 default_value）。

    实现逻辑：
    1. 先查 TaskDB.prompts 表（运行时覆盖）
    2. 后查内嵌模板（作为 fallback）
    """
    # TaskDB 优先
    db = _lazy_task_db()
    if db is not None:
        db_row = db.get_prompt(code)
        if db_row:
            return db_row

    # 内嵌 fallback
    tpl = _TPL_BY_CODE.get(code)
    if tpl is None:
        return None

    # 计算 effective value
    result = dict(tpl)
    result["value"] = tpl.get("custom_value") or tpl.get("default_value", "")
    return result


def apply_template(code: str, **variables) -> str:
    """
    使用变量渲染模板。

    Args:
        code: 模板 code
        **variables: 变量键值对，如 project="漠玫传", episode="S01E01"

    Returns:
        渲染后的 prompt 字符串
    """
    tpl = get_template(code)
    if tpl is None:
        return ""

    tmpl = tpl["value"]
    for key, val in variables.items():
        tmpl = tmpl.replace(f"{{{key}}}", str(val))
        # 也支持 $key 格式
        tmpl = tmpl.replace(f"${key}", str(val))

    return tmpl


def list_templates(
    type_filter: str | None = None,
    parent_filter: str | None = None,
) -> list[dict]:
    """列出模板（可选过滤）"""
    results = []
    for t in PROMPT_TEMPLATES:
        if type_filter and t.get("type") != type_filter:
            continue
        if parent_filter and t.get("parent_code") != parent_filter:
            continue
        results.append({**t, "value": t.get("custom_value") or t.get("default_value", "")})
    return results


def render_agent_system_prompt(agent_code: str, **variables) -> str:
    """
    渲染 Agent 的完整 system prompt。

    拼接顺序：
      1. system.asset-consistency（资产一致性）
      2. agent 自身模板（default_value / custom_value）
      3. system.visual-bible-anchor（Visual Bible 锚定）
      4. 变量替换

    Args:
        agent_code: Agent code（如 "outlineScript-main"）
        **variables: 渲染变量

    Returns:
        完整 system prompt 字符串
    """
    parts = []

    # 1. 资产一致性规则（固定）
    consistency = get_template("system.asset-consistency")
    if consistency:
        parts.append(consistency["value"])

    # 2. Agent 模板
    agent = get_template(agent_code)
    if agent:
        parts.append(agent["value"])

    # 3. Visual Bible 锚定（如果存在）
    vb = get_template("system.visual-bible-anchor")
    if vb:
        parts.append(vb["value"])

    # 拼接
    prompt = "\n\n".join(parts)

    # 变量替换
    for key, val in variables.items():
        prompt = prompt.replace(f"{{{key}}}", str(val))
        prompt = prompt.replace(f"${key}", str(val))

    return prompt


def upsert_custom_template(
    code: str,
    custom_value: str,
    description: str | None = None,
) -> None:
    """
    保存用户自定义模板到 TaskDB。

    用法：
      upsert_custom_template("outlineScript-main", "我的自定义大纲模板...")
    """
    db = _lazy_task_db()
    if db is None:
        raise RuntimeError("TaskDB 不可用，无法保存自定义模板")
    tpl = _TPL_BY_CODE.get(code)
    db.upsert_prompt(
        code=code,
        name=tpl.get("name") if tpl else code,
        prompt_type=tpl.get("type") if tpl else "custom",
        default_value=tpl.get("default_value", "") if tpl else "",
        custom_value=custom_value,
        parent_code=tpl.get("parent_code") if tpl else None,
        description=description or tpl.get("description", "") if tpl else "",
    )


def reset_custom_template(code: str) -> None:
    """重置自定义模板（删除 custom_value，恢复 default_value）"""
    db = _lazy_task_db()
    if db is not None:
        db.upsert_prompt(code=code, custom_value=None)


def seed_templates_to_db() -> None:
    """将内嵌模板同步到 TaskDB（幂等）"""
    db = _lazy_task_db()
    if db is None:
        return
    for t in PROMPT_TEMPLATES:
        db.upsert_prompt(
            code=t["code"],
            name=t.get("name"),
            prompt_type=t.get("type"),
            default_value=t.get("default_value", ""),
            custom_value=t.get("custom_value"),
            parent_code=t.get("parent_code"),
            description=t.get("description", ""),
        )


# ═══════════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="huage888 提示词模板库")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list", help="列出所有模板")
    p_list = sub.add_parser("list", help="列出模板")
    p_list.add_argument("--type", help="按类型过滤（mainAgent/subAgent/tool/system）")
    p_list.add_argument("--parent", help="按父模板过滤")

    p_get = sub.add_parser("get", help="获取模板")
    p_get.add_argument("code", help="模板 code")
    p_get.add_argument("--show-value", action="store_true", help="显示 value 字段")

    p_render = sub.add_parser("render", help="渲染模板")
    p_render.add_argument("code", help="模板 code")
    p_render.add_argument("--var", action="append", dest="vars_", metavar="KEY=VALUE",
                          help="变量（可多次指定）")

    p_seed = sub.add_parser("seed", help="同步模板到 TaskDB")
    p_seed = sub.add_parser("seed", help="同步内嵌模板到 TaskDB")

    args = parser.parse_args()

    if args.cmd == "list":
        templates = list_templates(type_filter=args.type, parent_filter=args.parent)
        print(f"共 {len(templates)} 个模板：")
        for t in templates:
            parent = f" ← {t['parent_code']}" if t.get("parent_code") else ""
            has_custom = "★" if t.get("custom_value") else " "
            print(f"  {has_custom}[{t['type']}] {t['code']}{parent}")

    elif args.cmd == "get":
        t = get_template(args.code)
        if t:
            print(f"code:        {t['code']}")
            print(f"name:        {t.get('name', '')}")
            print(f"type:        {t.get('type', '')}")
            print(f"parent_code: {t.get('parent_code', '')}")
            print(f"description: {t.get('description', '')}")
            if args.show_value:
                print("-" * 60)
                print(t["value"])
            else:
                print(f"value:       {t['value'][:100]}...")
        else:
            print(f"模板不存在：{args.code}")

    elif args.cmd == "render":
        vars_dict = {}
        if args.vars_:
            for v in args.vars_:
                if "=" in v:
                    k, val = v.split("=", 1)
                    vars_dict[k.strip()] = val.strip()
        rendered = apply_template(args.code, **vars_dict)
        print(rendered)

    elif args.cmd == "seed":
        seed_templates_to_db()
        print("✅ 模板已同步到 TaskDB")
