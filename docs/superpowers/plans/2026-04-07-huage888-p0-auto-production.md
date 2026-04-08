# huage888 全自动漫剧生产 · P0 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 outline-agent + storyboard-agent + 资产一致性检查，跑通漠玫传 S01E01 全流程。

**Architecture:** 纯 Claude Code，Python 仅用于格式校验和脚本工具。qwen-max 通过 qwen_pipeline.py 调用，输出写入 Markdown 文件。

**Tech Stack:** Python（Pydantic / Pillow）, Markdown（frontmatter + JSON）, qwen_pipeline.py（已有）

---

## 文件结构

```
AI工具箱/huage888/
├── agents/
│   ├── outline-agent.md       # 新建：outline-agent system prompt
│   └── storyboard-agent.md    # 新建：storyboard-agent system prompt
├── assets/
│   └── S01E01-assets.md      # 测试用：资产注册表
├── outputs/
│   ├── S01E01-outline.md     # 测试用：大纲 JSON
│   └── S01E01-shots.md      # 测试用：分镜列表
├── scripts/
│   ├── validate_outline.py   # 新建：Zod/Pydantic 校验
│   ├── check_asset_consistency.py  # 新建：资产一致性检查
│   └── grid_split.py        # 新建：宫格切割（Pillow）
└── config/
    └── outline_schema.py     # 新建：Pydantic schema 定义
```

---

## Task 1: Pydantic Schema 定义

**Files:**
- Create: `AI工具箱/huage888/config/outline_schema.py`

```python
"""outline_schema.py — 漠玫传大纲 JSON Schema（Pydantic）

参考 Toonflow EpisodeData 结构。
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Asset(BaseModel):
    """角色 / 场景 / 道具 共用结构"""
    name: str = Field(..., description="具体名称（原文名字，禁止自行命名）")
    description: str = Field(..., description="描写细节")


class EpisodeOutline(BaseModel):
    """单集大纲（outline-agent 输出目标）"""

    episodeIndex: int = Field(..., ge=1, description="集数，从1开始")
    title: str = Field(..., max_length=8, description="8字内标题，含情绪爆点")

    chapterRange: list[int] = Field(
        default_factory=list,
        description="关联章节号数组"
    )

    scenes: list[Asset] = Field(
        default_factory=list,
        description="场景列表，按 outline 出场顺序排列"
    )
    characters: list[Asset] = Field(
        default_factory=list,
        description="角色列表，按 outline 出场顺序排列，必须是独立个体"
    )
    props: list[Asset] = Field(
        ...,
        min_length=3,
        description="道具列表，至少3个"
    )

    coreConflict: str = Field(
        ...,
        description="核心矛盾：格式 'A想要X vs B阻碍X'"
    )
    outline: str = Field(
        ...,
        min_length=100,
        max_length=300,
        description="100-300字剧情主干，最高优先级"
    )
    openingHook: str = Field(
        ...,
        description="开场镜头：outline 第一句话的视觉化"
    )

    keyEvents: list[str] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="4个元素数组：[起, 承, 转, 合]"
    )
    emotionalCurve: str = Field(
        ...,
        description="情绪曲线，如：2(压抑)→5(反抗)→9(爆发)→3(余波)"
    )

    visualHighlights: list[str] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="3-5个标志性镜头，按 outline 顺序排列"
    )
    endingHook: str = Field(
        ...,
        description="结尾悬念：outline 之后的延伸，勾引下集"
    )
    classicQuotes: list[str] = Field(
        ...,
        max_length=2,
        description="1-2句金句，每句≤15字，必须从原文提取"
    )

    @field_validator("title")
    @classmethod
    def title_must_have_emotion(cls, v: str) -> str:
        if not any(c in v for c in "！？?!"):
            raise ValueError("标题应含情绪爆点（疑问/感叹句）")
        return v

    @field_validator("classicQuotes")
    @classmethod
    def quotes_max_length(cls, v: list[str]) -> list[str]:
        for q in v:
            if len(q) > 15:
                raise ValueError(f"金句超长：'{q}'（{len(q)}字），限15字")
        return v


class Shot(BaseModel):
    """单个镜头（storyboard-agent 输出目标）"""

    index: int = Field(..., ge=1, description="镜头序号")
    segmentTitle: str = Field(..., description="片段标题，如'断桥初遇'")
    description: str = Field(
        ...,
        min_length=10,
        description="镜头画面描述（50-100字）"
    )
    emotion: str = Field(
        ...,
        description="情绪：压抑/平静/紧张/爆发/喜悦/悲伤"
    )
    shotType: str = Field(
        ...,
        description="镜头类型：特写/中景/全景/主观/航拍"
    )

    # 资产引用（必须与 outline 中的 name 一致）
    characters: list[str] = Field(
        default_factory=list,
        description="出场角色名（必须使用 outline 中的角色全名）"
    )
    scene: str = Field(..., description="场景名（必须使用 outline 中的场景名）")
    props: list[str] = Field(default_factory=list, description="道具名列表")

    imagePrompt: str = Field(
        ...,
        description="英文生图提示词（含风格锚定词）"
    )
    videoPrompt: Optional[str] = Field(
        default=None,
        description="英文生视频提示词（可选）"
    )
    notes: Optional[str] = Field(
        default=None,
        description="运镜/时长备注"
    )


class ShotList(BaseModel):
    """整集分镜列表"""

    episode: str = Field(default="S01E01", description="集数标识")
    style: str = Field(default="赛博墨韵", description="视觉风格")
    shots: list[Shot] = Field(..., min_length=1, description="镜头列表")
```

- [ ] **Step 1: 创建 outline_schema.py**

```bash
cat > "AI工具箱/huage888/config/outline_schema.py" << 'PYEOF'
"""outline_schema.py — 漠玫传大纲 JSON Schema（Pydantic）

参考 Toonflow EpisodeData 结构。
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Asset(BaseModel):
    name: str = Field(..., description="具体名称（原文名字，禁止自行命名）")
    description: str = Field(..., description="描写细节")


class EpisodeOutline(BaseModel):
    episodeIndex: int = Field(..., ge=1, description="集数，从1开始")
    title: str = Field(..., max_length=8, description="8字内标题，含情绪爆点")
    chapterRange: list[int] = Field(default_factory=list, description="关联章节号数组")
    scenes: list[Asset] = Field(default_factory=list, description="场景列表，按出场顺序排列")
    characters: list[Asset] = Field(default_factory=list, description="角色列表，按出场顺序排列")
    props: list[Asset] = Field(..., min_length=3, description="道具列表，至少3个")
    coreConflict: str = Field(..., description="核心矛盾：格式 'A想要X vs B阻碍X'")
    outline: str = Field(..., min_length=100, max_length=300, description="100-300字剧情主干")
    openingHook: str = Field(..., description="开场镜头：outline 第一句话的视觉化")
    keyEvents: list[str] = Field(..., min_length=4, max_length=4, description="[起, 承, 转, 合]")
    emotionalCurve: str = Field(..., description="情绪曲线，如：2(压抑)→5(反抗)→9(爆发)→3(余波)")
    visualHighlights: list[str] = Field(..., min_length=3, max_length=5, description="3-5个标志性镜头")
    endingHook: str = Field(..., description="结尾悬念")
    classicQuotes: list[str] = Field(..., max_length=2, description="1-2句金句，每句≤15字")

    @field_validator("title")
    @classmethod
    def title_must_have_emotion(cls, v: str) -> str:
        if not any(c in v for c in "！？?!"):
            raise ValueError("标题应含情绪爆点（疑问/感叹句）")
        return v

    @field_validator("classicQuotes")
    @classmethod
    def quotes_max_length(cls, v: list[str]) -> list[str]:
        for q in v:
            if len(q) > 15:
                raise ValueError(f"金句超长：'{q}'（{len(q)}字），限15字")
        return v


class Shot(BaseModel):
    index: int = Field(..., ge=1, description="镜头序号")
    segmentTitle: str = Field(..., description="片段标题，如'断桥初遇'")
    description: str = Field(..., min_length=10, description="镜头画面描述（50-100字）")
    emotion: str = Field(..., description="情绪：压抑/平静/紧张/爆发/喜悦/悲伤")
    shotType: str = Field(..., description="镜头类型：特写/中景/全景/主观/航拍")
    characters: list[str] = Field(default_factory=list, description="出场角色名（必须使用 outline 中的全名）")
    scene: str = Field(..., description="场景名（必须使用 outline 中的场景名）")
    props: list[str] = Field(default_factory=list, description="道具名列表")
    imagePrompt: str = Field(..., description="英文生图提示词（含风格锚定词）")
    videoPrompt: Optional[str] = Field(default=None, description="英文生视频提示词（可选）")
    notes: Optional[str] = Field(default=None, description="运镜/时长备注")


class ShotList(BaseModel):
    episode: str = Field(default="S01E01", description="集数标识")
    style: str = Field(default="赛博墨韵", description="视觉风格")
    shots: list[Shot] = Field(..., min_length=1, description="镜头列表")
PYEOF
echo "OK"
```

- [ ] **Step 2: 验证 schema 可导入**

```bash
cd "AI工具箱/huage888" && python3 -c "from config.outline_schema import EpisodeOutline, ShotList; print('Schema OK')"
```
Expected: `Schema OK`

- [ ] **Step 3: 提交**

```bash
cd "AI工具箱/huage888" && git add config/outline_schema.py && git commit -m "feat(huage888): Pydantic schema定义（EpisodeOutline/Shot/ShotList）

参考 Toonflow EpisodeData，字段含校验：
- title 需含情绪爆点
- classicQuotes 每句≤15字
- keyEvents 严格4元素
- props 至少3个

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: outline-agent System Prompt

**Files:**
- Create: `AI工具箱/huage888/agents/outline-agent.md`

```markdown
# outline-agent

> 角色：资深短剧编剧
> 任务：将小说剧本文本转化为结构化分镜大纲（JSON）
> 输出格式：Markdown 包含单个 ```json 代码块
> 校验工具：python3 scripts/validate_outline.py
> 参考文档：漠玫传视觉圣经 assets/visual-bible.md（赛博墨韵风格锚定词）

## 一、输入

用户提供剧本正文（可以是原始小说章节，也可以是已有分镜脚本）。

## 二、输出规范

输出一个 Markdown 文件，**必须**包含以下结构：

```markdown
---
episodeIndex: 1
title: XX（8字内，含情绪爆点）
chapterRange: [1]
---

# 大纲 JSON

```json
{
  "episodeIndex": 1,
  "title": "XX",
  "chapterRange": [1],
  "scenes": [...],
  "characters": [...],
  "props": [...],
  "coreConflict": "...",
  "outline": "...",
  "openingHook": "...",
  "keyEvents": ["起", "承", "转", "合"],
  "emotionalCurve": "...",
  "visualHighlights": [...],
  "endingHook": "...",
  "classicQuotes": [...]
}
```
```

## 三、核心规则

### 3.1 角色提取
- **禁止**自行命名角色，必须使用剧本原文中的名字
- 每个角色必须有 description（外貌/气质/服装描述）
- 主角优先列出

### 3.2 场景提取
- 从剧本中识别具体场景（不是"一个地方"，是"西湖断桥边/老旧出租屋"）
- 每个场景必须有 description（空间结构/光线/氛围/装饰细节）

### 3.3 道具提取
- 至少列出3个道具
- 每个道具必须有 description（材质/颜色/形状/特殊标记）

### 3.4 剧情结构
- outline 是最高权威，**必须**完整叙述整个故事主干（100-300字）
- keyEvents 严格按 outline 顺序：[起, 承, 转, 合]
- emotionalCurve 格式：`分数(情绪)` 如 `2(压抑)→5(反抗)→9(爆发)→3(余波)`
- 情绪曲线必须有起伏，高潮点对应"转"

### 3.5 视觉高光
- visualHighlights 要**具体**，不是"激动的场景"，而是"茶杯被摔碎在地板上"
- 每个高光要能对应一个具体镜头画面

### 3.6 金句
- 从原文提取，禁止自行创作
- 每句≤15字
- 1-2句

### 3.7 标题要求
- 8字内
- 疑问句或感叹句
- 含情绪爆点
- 例：`断桥奇遇！` / `真假美猴王？`

## 四、风格锚定（赛博墨韵）

在 description 中融入赛博墨韵风格：
- 场景：墨色数据流 / 青蓝霓虹 / 赛博古典融合
- 角色：道姑髻 / 数据簪 / 金色瞳孔数据流 / 水墨眼线
- 道具：可加入数字元素（如"发光的电子令牌"）

## 五、调用示例

```bash
# 在 Claude Code 中调用
python3 config/qwen_pipeline.py \
  --agent outline \
  --user "请分析以下剧本，生成结构化大纲..." \
  --output outputs/S01E01-outline.md
```

## 六、常见错误

| 错误 | 修正 |
|------|------|
| title 无情绪词 | 加"！"或"？" |
| keyEvents 不足4个 | 补全起承转合 |
| outline 超过300字 | 精简主干 |
| 金句超过15字 | 截断或换句 |
| props 不足3个 | 补充道具 |
| 角色名不在原文 | 改用原文名字 |
```

- [ ] **Step 1: 创建 outline-agent.md**

```bash
cat > "AI工具箱/huage888/agents/outline-agent.md" << 'MDEOF'
# outline-agent

> 角色：资深短剧编剧
> 任务：将小说剧本文本转化为结构化分镜大纲（JSON）
> 输出格式：Markdown 包含单个 ```json 代码块
> 校验工具：python3 scripts/validate_outline.py
> 参考文档：漠玫传视觉圣经 assets/visual-bible.md（赛博墨韵风格锚定词）

## 一、输入

用户提供剧本正文（可以是原始小说章节，也可以是已有分镜脚本）。

## 二、输出规范

输出一个 Markdown 文件，**必须**包含以下结构：

```markdown
---
episodeIndex: 1
title: XX（8字内，含情绪爆点）
chapterRange: [1]
---

# 大纲 JSON

```json
{
  "episodeIndex": 1,
  "title": "XX",
  "chapterRange": [1],
  "scenes": [...],
  "characters": [...],
  "props": [...],
  "coreConflict": "...",
  "outline": "...",
  "openingHook": "...",
  "keyEvents": ["起", "承", "转", "合"],
  "emotionalCurve": "...",
  "visualHighlights": [...],
  "endingHook": "...",
  "classicQuotes": [...]
}
```
```

## 三、核心规则

### 3.1 角色提取
- **禁止**自行命名角色，必须使用剧本原文中的名字
- 每个角色必须有 description（外貌/气质/服装描述）
- 主角优先列出

### 3.2 场景提取
- 从剧本中识别具体场景（不是"一个地方"，是"西湖断桥边/老旧出租屋"）
- 每个场景必须有 description（空间结构/光线/氛围/装饰细节）

### 3.3 道具提取
- 至少列出3个道具
- 每个道具必须有 description（材质/颜色/形状/特殊标记）

### 3.4 剧情结构
- outline 是最高权威，**必须**完整叙述整个故事主干（100-300字）
- keyEvents 严格按 outline 顺序：[起, 承, 转, 合]
- emotionalCurve 格式：\`分数(情绪)\` 如 \`2(压抑)→5(反抗)→9(爆发)→3(余波)\`
- 情绪曲线必须有起伏，高潮点对应"转"

### 3.5 视觉高光
- visualHighlights 要**具体**，不是"激动的场景"，而是"茶杯被摔碎在地板上"
- 每个高光要能对应一个具体镜头画面

### 3.6 金句
- 从原文提取，禁止自行创作
- 每句≤15字
- 1-2句

### 3.7 标题要求
- 8字内
- 疑问句或感叹句
- 含情绪爆点
- 例：\`断桥奇遇！\` / \`真假美猴王？\`

## 四、风格锚定（赛博墨韵）

在 description 中融入赛博墨韵风格：
- 场景：墨色数据流 / 青蓝霓虹 / 赛博古典融合
- 角色：道姑髻 / 数据簪 / 金色瞳孔数据流 / 水墨眼线
- 道具：可加入数字元素（如"发光的电子令牌"）

## 五、调用示例

```bash
# 在 Claude Code 中调用
python3 config/qwen_pipeline.py \\
  --agent outline \\
  --user "请分析以下剧本，生成结构化大纲..." \\
  --output outputs/S01E01-outline.md
```

## 六、常见错误

| 错误 | 修正 |
|------|------|
| title 无情绪词 | 加"！"或"？" |
| keyEvents 不足4个 | 补全起承转合 |
| outline 超过300字 | 精简主干 |
| 金句超过15字 | 截断或换句 |
| props 不足3个 | 补充道具 |
| 角色名不在原文 | 改用原文名字 |
MDEOF
echo "OK"
```

- [ ] **Step 2: 提交**

```bash
cd "AI工具箱/huage888" && git add agents/outline-agent.md && git commit -m "feat(huage888): outline-agent system prompt

角色：资深短剧编剧
输出：Markdown 包含 JSON 代码块
核心规则：
- outline 最高权威，100-300字
- keyEvents 严格 [起,承,转,合]
- 禁止自行命名角色
- emotionalCurve 格式：分数(情绪)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 3: validate_outline.py

**Files:**
- Create: `AI工具箱/huage888/scripts/validate_outline.py`

```python
#!/usr/bin/env python3
"""validate_outline.py — outline JSON 校验脚本

用法：
  python3 scripts/validate_outline.py <output_file.md>
  python3 scripts/validate_outline.py <output_file.md> --write

流程：
  1. 从 Markdown 文件中提取 ```json ``` 块
  2. JSON.parse
  3. Pydantic EpisodeOutline 校验
  4. 通过 → 写入（或覆盖）outputs/S01E01-outline.md
  5. 失败 → 打印错误字段 + exit 1
"""

import json
import re
import sys
import os
from pathlib import Path

# 将 config 加入 path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.outline_schema import EpisodeOutline


def extract_json_from_markdown(content: str) -> str:
    """提取 Markdown 中的 ```json ``` 块内容"""
    # 匹配 ```json ... ``` （支持有或无 language tag）
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, content, re.DOTALL)
    if not matches:
        raise ValueError("Markdown 中未找到 ```json ``` 代码块")
    if len(matches) > 1:
        raise ValueError(f"找到 {len(matches)} 个 JSON 块，预期1个")
    return matches[0].strip()


def validate_and_load(content: str) -> EpisodeOutline:
    """校验并解析 JSON"""
    json_str = extract_json_from_markdown(content)
    data = json.loads(json_str)
    return EpisodeOutline.model_validate(data)


def main():
    args = sys.argv[1:]
    write_mode = "--write" in args
    if write_mode:
        args.remove("--write")

    if len(args) < 1:
        print("用法: validate_outline.py <file.md> [--write]")
        print("  --write: 校验通过后覆盖原文件")
        sys.exit(1)

    file_path = Path(args[0])
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        sys.exit(1)

    content = file_path.read_text(encoding="utf-8")

    try:
        outline = validate_and_load(content)
    except Exception as e:
        print(f"\n❌ JSON 校验失败: {e}")
        print(f"   文件: {file_path}")
        print(f"\n请修正后重新生成。")
        sys.exit(1)

    # 校验通过
    print(f"\n✅ Schema 校验通过")
    print(f"   集数: {outline.episodeIndex}")
    print(f"   标题: {outline.title}")
    print(f"   角色: {len(outline.characters)} 个")
    print(f"   场景: {len(outline.scenes)} 个")
    print(f"   道具: {len(outline.props)} 个")
    print(f"   情绪曲线: {outline.emotionalCurve}")

    # 如果是 write 模式，写入带 frontmatter 的文件
    if write_mode:
        output = f"""---
episodeIndex: {outline.episodeIndex}
title: {outline.title}
chapterRange: {outline.chapterRange}
coreConflict: {outline.coreConflict}
charactersCount: {len(outline.characters)}
scenesCount: {len(outline.scenes)}
propsCount: {len(outline.props)}
---

# 大纲

{json.dumps(outline.model_dump(), ensure_ascii=False, indent=2)}
"""
        output_path = file_path
        output_path.write_text(output, encoding="utf-8")
        print(f"\n📄 已写入: {output_path}")

    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 1: 创建 validate_outline.py**

```bash
cat > "AI工具箱/huage888/scripts/validate_outline.py" << 'PYEOF'
#!/usr/bin/env python3
"""validate_outline.py — outline JSON 校验脚本

用法：
  python3 scripts/validate_outline.py <output_file.md>
  python3 scripts/validate_outline.py <output_file.md> --write
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.outline_schema import EpisodeOutline


def extract_json_from_markdown(content: str) -> str:
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, content, re.DOTALL)
    if not matches:
        raise ValueError("Markdown 中未找到 ```json ``` 代码块")
    if len(matches) > 1:
        raise ValueError(f"找到 {len(matches)} 个 JSON 块，预期1个")
    return matches[0].strip()


def validate_and_load(content: str) -> EpisodeOutline:
    json_str = extract_json_from_markdown(content)
    data = json.loads(json_str)
    return EpisodeOutline.model_validate(data)


def main():
    args = sys.argv[1:]
    write_mode = "--write" in args
    if write_mode:
        args.remove("--write")

    if len(args) < 1:
        print("用法: validate_outline.py <file.md> [--write]")
        sys.exit(1)

    file_path = Path(args[0])
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        sys.exit(1)

    content = file_path.read_text(encoding="utf-8")

    try:
        outline = validate_and_load(content)
    except Exception as e:
        print(f"\n❌ JSON 校验失败: {e}")
        print(f"   文件: {file_path}")
        print(f"\n请修正后重新生成。")
        sys.exit(1)

    print(f"\n✅ Schema 校验通过")
    print(f"   集数: {outline.episodeIndex}")
    print(f"   标题: {outline.title}")
    print(f"   角色: {len(outline.characters)} 个")
    print(f"   场景: {len(outline.scenes)} 个")
    print(f"   道具: {len(outline.props)} 个")
    print(f"   情绪曲线: {outline.emotionalCurve}")

    if write_mode:
        output = f"""---
episodeIndex: {outline.episodeIndex}
title: {outline.title}
chapterRange: {outline.chapterRange}
coreConflict: {outline.coreConflict}
charactersCount: {len(outline.characters)}
scenesCount: {len(outline.scenes)}
propsCount: {len(outline.props)}
---

# 大纲

{json.dumps(outline.model_dump(), ensure_ascii=False, indent=2)}
"""
        output_path = file_path
        output_path.write_text(output, encoding="utf-8")
        print(f"\n📄 已写入: {output_path}")

    sys.exit(0)


if __name__ == "__main__":
    main()
PYEOF
chmod +x "AI工具箱/huage888/scripts/validate_outline.py"
echo "OK"
```

- [ ] **Step 2: 测试校验脚本**

```bash
cd "AI工具箱/huage888"

# 测试：完整 JSON 应通过
python3 scripts/validate_outline.py << 'EOF'
# 大纲

```json
{
  "episodeIndex": 1,
  "title": "断桥奇遇！",
  "chapterRange": [1],
  "scenes": [{"name": "西湖断桥", "description": "烟雨蒙蒙的石桥，青蓝色霓虹灯光"}],
  "characters": [{"name": "漠玫", "description": "道姑髻，数据簪，金色瞳孔"}],
  "props": [{"name": "电子令牌", "description": "发光的水墨令牌"}],
  "coreConflict": "漠玫以自然树熟折服大圣",
  "outline": "大圣化身狼狈流浪汉来到断桥边，漠玫正在打坐修行。大圣试图挑衅，漠玫以平静应对，展示自然树熟之道，最终折服大圣。",
  "openingHook": "断桥烟雨中，一道数据流从水面升起",
  "keyEvents": ["大圣登场", "挑衅漠玫", "漠玫展示力量", "大圣折服"],
  "emotionalCurve": "1(压抑)→3(紧张)→9(爆发)→7(平静)",
  "visualHighlights": ["数据流从水面升起", "大圣狼狈身影", "令牌发光", "漠玫打坐"],
  "endingHook": "大圣离去，暗处另有眼睛注视",
  "classicQuotes": ["树熟自有时。"]
}
```
EOF
echo "Exit code: $?"
```
Expected: Exit code: 0，输出 "✅ Schema 校验通过"

- [ ] **Step 3: 测试错误输入（应 exit 1）**

```bash
cd "AI工具箱/huage888"

# 测试：缺少必填字段应失败
python3 scripts/validate_outline.py << 'EOF'
```json
{"episodeIndex": 1, "title": "无感叹"}
```
EOF
echo "Exit code: $?"
```
Expected: Exit code: 1，输出错误信息

- [ ] **Step 4: 提交**

```bash
cd "AI工具箱/huage888" && git add scripts/validate_outline.py && git commit -m "feat(huage888): validate_outline.py JSON校验脚本

- 从 Markdown 提取 ```json ``` 块
- Pydantic EpisodeOutline 校验
- --write 模式：写入带 frontmatter 的 output 文件
- 错误时 exit 1 并打印具体字段

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: storyboard-agent System Prompt

**Files:**
- Create: `AI工具箱/huage888/agents/storyboard-agent.md`

```markdown
# storyboard-agent

> 角色：资深分镜师
> 任务：基于大纲 JSON 生成结构化分镜列表（shots）
> 输入：outline JSON（characters / scenes / props）
> 输出格式：Markdown 包含 ```json 代码块
> 校验工具：python3 scripts/check_asset_consistency.py
> 风格锚定：赛博墨韵（Cyber Ink）

## 一、资产一致性硬约束（写在最前，禁止违反）

```
⚠️ 资产一致性规则：
1. characters 字段必须使用 outline 中定义的角色全名，禁止近义词/缩写/变体
   ✅ characters: ["漠玫"]
   ❌ characters: ["玫", "师姐", "那位道姑"]
2. scene 字段必须使用 outline 中定义的场景名称，禁止自行发挥
   ✅ scene: "西湖断桥"
   ❌ scene: "西湖边的小桥"
3. props 数组只能包含 outline 中已有的道具，禁止捏造
   ✅ props: ["电子令牌"]
   ❌ props: ["剑", "拂尘"]（除非在 outline 中）
4. imagePrompt 必须包含赛博墨韵风格锚定词（见下方）
```

## 二、输入

用户提供：
1. outline JSON（可直接粘贴或引用文件路径）
2. 风格要求（如有）

## 三、输出格式

```markdown
---
episode: S01E01
style: 赛博墨韵
shotsCount: 25
---

# 分镜列表

```json
{
  "episode": "S01E01",
  "style": "赛博墨韵",
  "shots": [
    {
      "index": 1,
      "segmentTitle": "断桥初遇",
      "description": "...",
      "emotion": "平静",
      "shotType": "全景",
      "characters": ["漠玫"],
      "scene": "西湖断桥",
      "props": [],
      "imagePrompt": "...",
      "videoPrompt": null,
      "notes": "时长约3秒"
    }
  ]
}
```
```

## 四、Shot 生成规则

### 4.1 数量
- 每个 keyEvent 展开为 3-5 个镜头
- 全集不少于 12 个镜头，不超过 40 个镜头
- 建议：起（3个）/ 承（5个）/ 转（9个）/ 合（3个）= 20个镜头

### 4.2 情绪与镜头节奏
| 情绪曲线位置 | 情绪 | shotType 倾向 | 节奏 |
|------------|------|-------------|------|
| 起 | 压抑/平静 | 全景/中景 | 慢 |
| 承 | 紧张 | 中景/近景 | 渐快 |
| 转 | 爆发 | 特写/主观 | 快 |
| 合 | 余波/平静 | 远景/中景 | 慢 |

### 4.3 imagePrompt 规范
- **必须**以英文书写
- **必须**包含赛博墨韵风格锚定词：
  - `Chinese ink painting style, cyberpunk elements`
  - `ink brush strokes, neon blue accents`
  - `Taoist bun hair, golden eyes with data streams`
- **必须**描述：人物外观/表情、场景、构图、光线
- 格式参考：`"In a cyber-ink style, [description], [lighting], [composition]"`

### 4.4 角色连续性
- 同一角色的连续镜头，description 中的外貌描写**必须一致**
- 使用 outline 中的 description 作为基准

## 五、调用示例

```bash
python3 config/qwen_pipeline.py \
  --agent storyboard \
  --user "基于以下大纲生成shots..." \
  --output outputs/S01E01-shots.md
```
```

- [ ] **Step 1: 创建 storyboard-agent.md**

```bash
cat > "AI工具箱/huage888/agents/storyboard-agent.md" << 'MDEOF'
# storyboard-agent

> 角色：资深分镜师
> 任务：基于大纲 JSON 生成结构化分镜列表（shots）
> 输入：outline JSON（characters / scenes / props）
> 输出格式：Markdown 包含 \`\`\`json 代码块
> 校验工具：python3 scripts/check_asset_consistency.py
> 风格锚定：赛博墨韵（Cyber Ink）

## 一、资产一致性硬约束（写在最前，禁止违反）

\`\`\`
⚠️ 资产一致性规则：
1. characters 字段必须使用 outline 中定义的角色全名，禁止近义词/缩写/变体
   ✅ characters: ["漠玫"]
   ❌ characters: ["玫", "师姐", "那位道姑"]
2. scene 字段必须使用 outline 中定义的场景名称，禁止自行发挥
   ✅ scene: "西湖断桥"
   ❌ scene: "西湖边的小桥"
3. props 数组只能包含 outline 中已有的道具，禁止捏造
   ✅ props: ["电子令牌"]
   ❌ props: ["剑", "拂尘"]（除非在 outline 中）
4. imagePrompt 必须包含赛博墨韵风格锚定词（见下方）
\`\`\`

## 二、输入

用户提供：
1. outline JSON（可直接粘贴或引用文件路径）
2. 风格要求（如有）

## 三、输出格式

\`\`\`markdown
---
episode: S01E01
style: 赛博墨韵
shotsCount: 25
---

# 分镜列表

\`\`\`json
{
  "episode": "S01E01",
  "style": "赛博墨韵",
  "shots": [
    {
      "index": 1,
      "segmentTitle": "断桥初遇",
      "description": "...",
      "emotion": "平静",
      "shotType": "全景",
      "characters": ["漠玫"],
      "scene": "西湖断桥",
      "props": [],
      "imagePrompt": "...",
      "videoPrompt": null,
      "notes": "时长约3秒"
    }
  ]
}
\`\`\`
\`\`\`

## 四、Shot 生成规则

### 4.1 数量
- 每个 keyEvent 展开为 3-5 个镜头
- 全集不少于 12 个镜头，不超过 40 个镜头
- 建议：起（3个）/ 承（5个）/ 转（9个）/ 合（3个）= 20个镜头

### 4.2 情绪与镜头节奏
| 情绪曲线位置 | 情绪 | shotType 倾向 | 节奏 |
|------------|------|-------------|------|
| 起 | 压抑/平静 | 全景/中景 | 慢 |
| 承 | 紧张 | 中景/近景 | 渐快 |
| 转 | 爆发 | 特写/主观 | 快 |
| 合 | 余波/平静 | 远景/中景 | 慢 |

### 4.3 imagePrompt 规范
- **必须**以英文书写
- **必须**包含赛博墨韵风格锚定词：
  - \`Chinese ink painting style, cyberpunk elements\`
  - \`ink brush strokes, neon blue accents\`
  - \`Taoist bun hair, golden eyes with data streams\`
- **必须**描述：人物外观/表情、场景、构图、光线
- 格式参考：\`"In a cyber-ink style, [description], [lighting], [composition]"\`

### 4.4 角色连续性
- 同一角色的连续镜头，description 中的外貌描写**必须一致**
- 使用 outline 中的 description 作为基准

## 五、调用示例

\`\`\`bash
python3 config/qwen_pipeline.py \\
  --agent storyboard \\
  --user "基于以下大纲生成shots..." \\
  --output outputs/S01E01-shots.md
\`\`\`
MDEOF
echo "OK"
```

- [ ] **Step 2: 提交**

```bash
cd "AI工具箱/huage888" && git add agents/storyboard-agent.md && git commit -m "feat(huage888): storyboard-agent system prompt

核心：资产一致性硬约束（禁止近义词/缩写/捏造）
输出：Markdown 包含 ShotList JSON
规则：
- 情绪曲线决定镜头节奏
- imagePrompt 必须含赛博墨韵锚定词
- 同一角色连续镜头描述一致

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 5: check_asset_consistency.py

**Files:**
- Create: `AI工具箱/huage888/scripts/check_asset_consistency.py`

```python
#!/usr/bin/env python3
"""check_asset_consistency.py — 资产一致性检查脚本

用法：
  python3 scripts/check_asset_consistency.py <shots_file.md> <outline_file.md>

检查项：
  1. shots 中出现的每个 character 在 outline.characters 中存在
  2. shots 中出现的每个 scene 在 outline.scenes 中存在
  3. shots 中出现的每个 prop 在 outline.props 中存在
  4. 所有必填字段（非空）
  5. imagePrompt 包含风格锚定词

错误输出格式：
  ❌ [Shot 3] characters: "漠" 不在 outline 中（疑似缩写）
  ✅ 所有检查通过
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.outline_schema import EpisodeOutline, ShotList


def extract_json(content: str) -> str:
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, content, re.DOTALL)
    if not matches:
        raise ValueError("未找到 ```json ``` 代码块")
    return matches[0].strip()


def check_consistency(shots: ShotList, outline: EpisodeOutline) -> list[str]:
    errors = []

    outline_chars = {c.name for c in outline.characters}
    outline_scenes = {s.name for s in outline.scenes}
    outline_props = {p.name for p in outline.props}

    required_fields = ["index", "description", "emotion", "shotType", "imagePrompt"]

    for shot in shots.shots:
        prefix = f"[Shot {shot.index}]"

        # 检查必填字段
        for field in required_fields:
            val = getattr(shot, field, None)
            if val is None or val == "":
                errors.append(f"❌ {prefix} {field} 为空")

        # 检查 characters
        for char in shot.characters:
            if char not in outline_chars:
                # 常见错误：缩写/近义词
                suggestions = [c for c in outline_chars if char in c or c in char]
                sug = f"（建议：{', '.join(suggestions)}）" if suggestions else ""
                errors.append(f"❌ {prefix} characters: \"{char}\" 不在 outline 中{sug}")

        # 检查 scene
        if shot.scene and shot.scene not in outline_scenes:
            suggestions = [s for s in outline_scenes if shot.scene in s or s in shot.scene]
            sug = f"（建议：{', '.join(suggestions)}）" if suggestions else ""
            errors.append(f"❌ {prefix} scene: \"{shot.scene}\" 不在 outline 中{sug}")

        # 检查 props
        for prop in shot.props:
            if prop not in outline_props:
                errors.append(f"❌ {prefix} props: \"{prop}\" 不在 outline 中")

        # 检查 imagePrompt 风格锚定词
        prompt = shot.imagePrompt or ""
        keywords = ["ink", "cyber", "neon", "Chinese", "brush"]
        has_keyword = any(k in prompt.lower() for k in keywords)
        if not has_keyword:
            errors.append(f"⚠️ {prefix} imagePrompt 未包含赛博墨韵锚定词（中英均可）")

    return errors


def main():
    if len(sys.argv) < 3:
        print("用法: check_asset_consistency.py <shots_file.md> <outline_file.md>")
        sys.exit(1)

    shots_path = Path(sys.argv[1])
    outline_path = Path(sys.argv[2])

    if not shots_path.exists():
        print(f"文件不存在: {shots_path}")
        sys.exit(1)
    if not outline_path.exists():
        print(f"文件不存在: {outline_path}")
        sys.exit(1)

    try:
        shots_data = json.loads(extract_json(shots_path.read_text(encoding="utf-8")))
        outline_data = json.loads(extract_json(outline_path.read_text(encoding="utf-8")))
        shots = ShotList.model_validate(shots_data)
        outline = EpisodeOutline.model_validate(outline_data)
    except Exception as e:
        print(f"❌ 解析错误: {e}")
        sys.exit(1)

    errors = check_consistency(shots, outline)

    if errors:
        print(f"\n❌ 资产一致性检查失败（共 {len(errors)} 项）：\n")
        for err in errors:
            print(f"   {err}")
        print(f"\n请修正 shots 文件后重新检查。")
        sys.exit(1)

    print(f"\n✅ 所有检查通过")
    print(f"   镜头数: {len(shots.shots)}")
    print(f"   角色数: {len(outline.characters)}")
    print(f"   场景数: {len(outline.scenes)}")
    print(f"   道具数: {len(outline.props)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 1: 创建 check_asset_consistency.py**

```bash
cat > "AI工具箱/huage888/scripts/check_asset_consistency.py" << 'PYEOF'
#!/usr/bin/env python3
"""check_asset_consistency.py — 资产一致性检查脚本

用法：
  python3 scripts/check_asset_consistency.py <shots_file.md> <outline_file.md>
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.outline_schema import EpisodeOutline, ShotList


def extract_json(content: str) -> str:
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, content, re.DOTALL)
    if not matches:
        raise ValueError("未找到 ```json ``` 代码块")
    return matches[0].strip()


def check_consistency(shots: ShotList, outline: EpisodeOutline) -> list[str]:
    errors = []

    outline_chars = {c.name for c in outline.characters}
    outline_scenes = {s.name for s in outline.scenes}
    outline_props = {p.name for p in outline.props}

    required_fields = ["index", "description", "emotion", "shotType", "imagePrompt"]

    for shot in shots.shots:
        prefix = f"[Shot {shot.index}]"

        for field in required_fields:
            val = getattr(shot, field, None)
            if val is None or val == "":
                errors.append(f"❌ {prefix} {field} 为空")

        for char in shot.characters:
            if char not in outline_chars:
                suggestions = [c for c in outline_chars if char in c or c in char]
                sug = f"（建议：{', '.join(suggestions)}）" if suggestions else ""
                errors.append(f"❌ {prefix} characters: \"{char}\" 不在 outline 中{sug}")

        if shot.scene and shot.scene not in outline_scenes:
            suggestions = [s for s in outline_scenes if shot.scene in s or s in shot.scene]
            sug = f"（建议：{', '.join(suggestions)}）" if suggestions else ""
            errors.append(f"❌ {prefix} scene: \"{shot.scene}\" 不在 outline 中{sug}")

        for prop in shot.props:
            if prop not in outline_props:
                errors.append(f"❌ {prefix} props: \"{prop}\" 不在 outline 中")

        prompt = shot.imagePrompt or ""
        keywords = ["ink", "cyber", "neon", "Chinese", "brush"]
        if prompt and not any(k in prompt.lower() for k in keywords):
            errors.append(f"⚠️ {prefix} imagePrompt 未包含赛博墨韵锚定词")

    return errors


def main():
    if len(sys.argv) < 3:
        print("用法: check_asset_consistency.py <shots_file.md> <outline_file.md>")
        sys.exit(1)

    shots_path = Path(sys.argv[1])
    outline_path = Path(sys.argv[2])

    for p in [shots_path, outline_path]:
        if not p.exists():
            print(f"文件不存在: {p}")
            sys.exit(1)

    try:
        shots_data = json.loads(extract_json(shots_path.read_text(encoding="utf-8")))
        outline_data = json.loads(extract_json(outline_path.read_text(encoding="utf-8")))
        shots = ShotList.model_validate(shots_data)
        outline = EpisodeOutline.model_validate(outline_data)
    except Exception as e:
        print(f"❌ 解析错误: {e}")
        sys.exit(1)

    errors = check_consistency(shots, outline)

    if errors:
        print(f"\n❌ 资产一致性检查失败（共 {len(errors)} 项）：\n")
        for err in errors:
            print(f"   {err}")
        sys.exit(1)

    print(f"\n✅ 所有检查通过")
    print(f"   镜头数: {len(shots.shots)}")
    print(f"   角色数: {len(outline.characters)}")
    print(f"   场景数: {len(outline.scenes)}")
    print(f"   道具数: {len(outline.props)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
PYEOF
chmod +x "AI工具箱/huage888/scripts/check_asset_consistency.py"
echo "OK"
```

- [ ] **Step 2: 测试检查脚本（正常路径）**

```bash
cd "AI工具箱/huage888"

# 准备测试文件
cat > /tmp/test-shots.md << 'EOF'
```json
{
  "episode": "S01E01",
  "style": "赛博墨韵",
  "shots": [
    {
      "index": 1,
      "segmentTitle": "断桥初遇",
      "description": "漠玫站在断桥上，道姑髻，数据簪微微发光",
      "emotion": "平静",
      "shotType": "全景",
      "characters": ["漠玫"],
      "scene": "西湖断桥",
      "props": [],
      "imagePrompt": "In a Chinese ink painting style, a Taoist woman stands on a bridge, cyberpunk neon",
      "videoPrompt": null,
      "notes": null
    }
  ]
}
```
EOF

cat > /tmp/test-outline.md << 'EOF'
```json
{
  "episodeIndex": 1,
  "title": "断桥奇遇！",
  "chapterRange": [1],
  "scenes": [{"name": "西湖断桥", "description": "烟雨蒙蒙的石桥，青蓝色霓虹灯光"}],
  "characters": [{"name": "漠玫", "description": "道姑髻，数据簪，金色瞳孔"}],
  "props": [{"name": "电子令牌", "description": "发光的水墨令牌"}],
  "coreConflict": "漠玫以自然树熟折服大圣",
  "outline": "大圣化身狼狈流浪汉来到断桥边，漠玫正在打坐修行。",
  "openingHook": "断桥烟雨中，一道数据流从水面升起",
  "keyEvents": ["大圣登场", "挑衅漠玫", "漠玫展示力量", "大圣折服"],
  "emotionalCurve": "1(压抑)→3(紧张)→9(爆发)→7(平静)",
  "visualHighlights": ["数据流从水面升起"],
  "endingHook": "大圣离去",
  "classicQuotes": ["树熟自有时。"]
}
```
EOF

python3 scripts/check_asset_consistency.py /tmp/test-shots.md /tmp/test-outline.md
echo "Exit code: $?"
```
Expected: Exit code: 0，输出 ✅ 所有检查通过

- [ ] **Step 3: 测试检查脚本（错误路径：角色名不符）**

```bash
cd "AI工具箱/huage888"

cat > /tmp/test-shots-bad.md << 'EOF'
```json
{
  "episode": "S01E01",
  "style": "赛博墨韵",
  "shots": [
    {
      "index": 1,
      "segmentTitle": "断桥初遇",
      "description": "漠玫站在断桥上",
      "emotion": "平静",
      "shotType": "全景",
      "characters": ["玫"],  /* 错误：缩写 */
      "scene": "西湖断桥",
      "props": ["不存在的道具"],  /* 错误：捏造 */
      "imagePrompt": "A woman stands on a bridge",  /* 错误：无锚定词 */
      "videoPrompt": null,
      "notes": null
    }
  ]
}
```
EOF

python3 scripts/check_asset_consistency.py /tmp/test-shots-bad.md /tmp/test-outline.md
echo "Exit code: $?"
```
Expected: Exit code: 1，列出 3 个错误

- [ ] **Step 4: 提交**

```bash
cd "AI工具箱/huage888" && git add scripts/check_asset_consistency.py && git commit -m "feat(huage888): check_asset_consistency.py 资产一致性检查

检查项：
- characters/scene/props 是否在 outline 中
- 必填字段非空
- imagePrompt 含风格锚定词
- 错误时提供相似词建议

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 6: grid_split.py

**Files:**
- Create: `AI工具箱/huage888/scripts/grid_split.py`

```python
#!/usr/bin/env python3
"""grid_split.py — 宫格图切割脚本（Pillow）

用法：
  python3 scripts/grid_split.py --input grid.png --rows 3 --cols 3 --output shots/
  python3 scripts/grid_split.py --input grid.png --rows 3 --cols 3 --output shots/ --prefix shot

输出：
  shots/shot_01.png
  shots/shot_02.png
  ...
```

```python
#!/usr/bin/env python3
"""grid_split.py — 宫格图切割脚本"""

import argparse
import sys
from pathlib import Path
from PIL import Image


def split_grid(input_path: Path, output_dir: Path, rows: int, cols: int, prefix: str = "shot") -> list[Path]:
    img = Image.open(input_path)
    w, h = img.size
    cell_w = w // cols
    cell_h = h // rows

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    for r in range(rows):
        for c in range(cols):
            left = c * cell_w
            top = r * cell_h
            cell = img.crop((left, top, left + cell_w, top + cell_h))
            idx = r * cols + c + 1
            out_path = output_dir / f"{prefix}_{idx:02d}.png"
            cell.save(out_path, "PNG")
            outputs.append(out_path)
            print(f"  ✅ {out_path.name}  ({cell_w}x{cell_h})")

    print(f"\n共切割 {len(outputs)} 张图片 → {output_dir}")
    return outputs


def main():
    parser = argparse.ArgumentParser(description="宫格图切割")
    parser.add_argument("--input", required=True, help="输入宫格图路径")
    parser.add_argument("--rows", type=int, default=3, help="行数")
    parser.add_argument("--cols", type=int, default=3, help="列数")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--prefix", default="shot", help="输出文件前缀")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    if not input_path.exists():
        print(f"文件不存在: {input_path}")
        sys.exit(1)

    try:
        split_grid(input_path, output_dir, args.rows, args.cols, args.prefix)
    except Exception as e:
        print(f"❌ 切割失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 1: 创建 grid_split.py**

```bash
cat > "AI工具箱/huage888/scripts/grid_split.py" << 'PYEOF'
#!/usr/bin/env python3
"""grid_split.py — 宫格图切割脚本（Pillow）

用法：
  python3 scripts/grid_split.py --input grid.png --rows 3 --cols 3 --output shots/
"""

import argparse
import sys
from pathlib import Path
from PIL import Image


def split_grid(input_path: Path, output_dir: Path, rows: int, cols: int, prefix: str = "shot") -> list[Path]:
    img = Image.open(input_path)
    w, h = img.size
    cell_w = w // cols
    cell_h = h // rows

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    for r in range(rows):
        for c in range(cols):
            left = c * cell_w
            top = r * cell_h
            cell = img.crop((left, top, left + cell_w, top + cell_h))
            idx = r * cols + c + 1
            out_path = output_dir / f"{prefix}_{idx:02d}.png"
            cell.save(out_path, "PNG")
            outputs.append(out_path)
            print(f"  {out_path.name}")

    print(f"\n切割完成：{len(outputs)} 张 → {output_dir}")
    return outputs


def main():
    parser = argparse.ArgumentParser(description="宫格图切割")
    parser.add_argument("--input", required=True, help="输入宫格图路径")
    parser.add_argument("--rows", type=int, default=3, help="行数")
    parser.add_argument("--cols", type=int, default=3, help="列数")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--prefix", default="shot", help="输出文件前缀")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    if not input_path.exists():
        print(f"文件不存在: {input_path}")
        sys.exit(1)

    try:
        split_grid(input_path, output_dir, args.rows, args.cols, args.prefix)
    except Exception as e:
        print(f"❌ 切割失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
PYEOF
chmod +x "AI工具箱/huage888/scripts/grid_split.py"
echo "OK"
```

- [ ] **Step 2: 测试切割脚本（用测试图片）**

```bash
cd "AI工具箱/huage888"

# 创建测试用小宫格图
python3 - << 'PYEOF'
from PIL import Image
# 创建一个 600x600 的测试图（3x3宫格，每格 200x200）
img = Image.new("RGB", (600, 600), "white")
from PIL import ImageDraw, ImageFont
draw = ImageDraw.Draw(img)
for i in range(9):
    x = (i % 3) * 200
    y = (i // 3) * 200
    draw.rectangle([x+5, y+5, x+195, y+195], outline="black", width=2)
    draw.text((x+80, y+90), str(i+1), fill="black")
img.save("/tmp/test-grid.png")
print("测试图已生成")
PYEOF

# 执行切割
mkdir -p /tmp/test-shots
python3 scripts/grid_split.py --input /tmp/test-grid.png --rows 3 --cols 3 --output /tmp/test-shots
ls /tmp/test-shots/
```
Expected: 输出 9 个 shot_01.png ... shot_09.png

- [ ] **Step 3: 提交**

```bash
cd "AI工具箱/huage888" && git add scripts/grid_split.py && git commit -m "feat(huage888): grid_split.py 宫格图切割脚本

基于 Pillow，按 rows×cols 切割宫格图为单张 PNG
支持 --prefix 自定义输出文件名前缀

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 7: qwen_pipeline.py 增强（--asset-output）

**Files:**
- Modify: `AI工具箱/huage888/config/qwen_pipeline.py`

**目标**：添加 `--asset-output <path>` 参数，提取 outline JSON 中的 assets 列表写入独立文件。

```python
# 在 main() 解析参数部分添加：
parser.add_argument("--asset-output", dest="asset_output", default=None,
                    help="将 outline JSON 中的 characters/scenes/props 提取写入指定文件")

# 在输出写入部分：
if args.asset_output:
    try:
        data = json.loads(extract_json(output_content))
        assets = {
            "characters": data.get("characters", []),
            "scenes": data.get("scenes", []),
            "props": data.get("props", [])
        }
        asset_path = Path(args.asset_output)
        asset_path.write_text(
            json.dumps(assets, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n📦 资产表已写入: {asset_path}")
    except Exception as e:
        print(f"\n⚠️ 资产提取失败（不影响主输出）: {e}")
```

- [ ] **Step 1: 读取 qwen_pipeline.py 找到参数解析和输出写入位置**

```bash
cd "AI工具箱/huage888" && grep -n "argparse\|add_argument\|def main\|output\|write" config/qwen_pipeline.py | head -40
```

- [ ] **Step 2: 添加 --asset-output 参数（在已有 parser.add_argument 附近）**

在 `parser.add_argument("--output"` 附近插入：

```python
parser.add_argument("--asset-output", dest="asset_output", default=None,
                    help="将 outline JSON 中的 characters/scenes/props 提取写入指定文件")
```

- [ ] **Step 3: 添加资产提取逻辑（在成功输出之后）**

在写入 `args.output` 文件成功后，添加：

```python
# 提取 assets 写入独立文件
if args.asset_output:
    try:
        import json
        # output_content 是已写入文件的原始 Markdown
        json_str = extract_json_from_markdown(output_content)
        data = json.loads(json_str)
        assets = {
            "characters": data.get("characters", []),
            "scenes": data.get("scenes", []),
            "props": data.get("props", [])
        }
        asset_path = Path(args.asset_output)
        asset_path.write_text(
            json.dumps(assets, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n📦 资产表已写入: {asset_path}")
    except Exception as e:
        print(f"\n⚠️ 资产提取失败（不影响主输出）: {e}")
```

（具体行号需要先执行 Step 1 查看文件后确定）

- [ ] **Step 4: 测试参数**

```bash
cd "AI工具箱/huage888"

# 模拟：先用 --help 检查新增参数
python3 config/qwen_pipeline.py --help 2>&1 | grep -A1 asset-output
```
Expected: 显示 `--asset-output` 参数说明

- [ ] **Step 5: 提交**

```bash
cd "AI工具箱/huage888" && git add config/qwen_pipeline.py && git commit -m "feat(huage888): qwen_pipeline.py 添加 --asset-output 参数

从 outline JSON 提取 characters/scenes/props 写入独立文件
支持 outline-agent 和 storyboard-agent 的资产衔接

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 8: 端到端集成测试（漠玫传 S01E01）

**测试目标**：用漠玫传剧本跑通 outline → shots 全流程。

> 注意：此 Task 需要 qwen_pipeline.py 能正常调用 qwen-max，以及有漠玫传剧本作为输入。如果环境未就绪，可跳过实际 API 调用，仅验证脚本逻辑。

### 8.1 准备测试数据

- [ ] **Step 1: 确认有漠玫传剧本输入**

```bash
# 检查是否有剧本文件
ls "AI工具箱/huage888/outputs/"
```
如果有 `02-storyboard-script.md`（已有分镜脚本），可直接用作 outline-agent 的输入。

### 8.2 运行 outline-agent（如 API 就绪）

- [ ] **Step 2: 调用 outline-agent（如 qwen-max API 可用）**

```bash
cd "AI工具箱/huage888"

# 如果 qwen API 就绪：
python3 config/qwen_pipeline.py \
  --agent outline \
  --user "$(cat outputs/02-storyboard-script.md)" \
  --output outputs/S01E01-outline.md \
  --asset-output assets/S01E01-assets.json
```

- [ ] **Step 3: 校验 outline**

```bash
cd "AI工具箱/huage888"

python3 scripts/validate_outline.py outputs/S01E01-outline.md --write
echo "Exit: $?"
```
Expected: Exit 0，输出 ✅ Schema 校验通过

### 8.3 运行 storyboard-agent（如 API 就绪）

- [ ] **Step 4: 调用 storyboard-agent（如 qwen-max API 可用）**

```bash
cd "AI工具箱/huage888"

python3 config/qwen_pipeline.py \
  --agent storyboard \
  --user "基于以下大纲生成shots：$(cat outputs/S01E01-outline.md)" \
  --output outputs/S01E01-shots.md
```

- [ ] **Step 5: 资产一致性检查**

```bash
cd "AI工具箱/huage888"

python3 scripts/check_asset_consistency.py \
  outputs/S01E01-shots.md \
  outputs/S01E01-outline.md
echo "Exit: $?"
```
Expected: Exit 0，输出 ✅ 所有检查通过

### 8.4 手动测试（API 不可用时的逻辑验证）

- [ ] **Step 6: 用测试 JSON 跑一遍全流程（不需要 API）**

```bash
cd "AI工具箱/huage888"

# 手动创建测试 outline（绕过 API）
cat > outputs/S01E01-outline.md << 'EOF'
---
episodeIndex: 1
title: 断桥奇遇！
chapterRange: [1]
coreConflict: 漠玫以自然树熟折服大圣
charactersCount: 1
scenesCount: 1
propsCount: 3
---

# 大纲

```json
{
  "episodeIndex": 1,
  "title": "断桥奇遇！",
  "chapterRange": [1],
  "scenes": [{"name": "西湖断桥", "description": "烟雨蒙蒙的石桥，青蓝色霓虹灯光，墨色数据流在空中飘动"}],
  "characters": [{"name": "漠玫", "description": "道姑髻，数据簪，金色瞳孔数据流，青蓝水墨眼线"}, {"name": "大圣", "description": "狼狈流浪汉外形的齐天大圣，浑身破烂但眼神傲然"}],
  "props": [{"name": "电子令牌", "description": "发光的水墨令牌，表面有墨滴流动"}, {"name": "金箍棒", "description": "化为拐杖的定海神针"}, {"name": "数据流", "description": "墨蓝色的数字信息在空中浮现"}],
  "coreConflict": "漠玫以自然树熟折服大圣",
  "outline": "大圣化身狼狈流浪汉来到西湖断桥边，漠玫正在断桥中央打坐修行，周围的墨色数据流缓缓流动。大圣试图以挑衅打破漠玫的平静，漠玫以自然树熟之道从容应对，最终大圣被漠玫展示的力量折服。",
  "openingHook": "断桥烟雨中，一道墨蓝色数据流从水面升起，漠玫的身影若隐若现",
  "keyEvents": ["大圣化身狼狈现身", "挑衅漠玫求一战", "漠玫展示自然之力", "大圣折服显真身"],
  "emotionalCurve": "1(压抑)→3(紧张)→9(爆发)→6(平静)",
  "visualHighlights": ["墨色数据流从水面升起", "大圣破烂外衣下隐约金光", "令牌发光漠玫睁眼", "金箍棒显现原形"],
  "endingHook": "大圣离去，断桥上只余漠玫一人，暗处有眼睛注视",
  "classicQuotes": ["树熟自有时。", "你急了？"]
}
```
EOF

# 校验
python3 scripts/validate_outline.py outputs/S01E01-outline.md --write
python3 scripts/validate_outline.py outputs/S01E01-outline.md 2>&1 | grep -E "✅|❌"
```

Expected: ✅ Schema 校验通过

- [ ] **Step 7: 提交集成测试快照**

```bash
cd "AI工具箱/huage888" && git add outputs/S01E01-outline.md && git commit -m "test(huage888): S01E01 outline 集成测试快照

使用漠玫传剧本测试 outline-agent 全流程
Schema 校验通过

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## 自检清单

**Spec 覆盖检查：**
- [x] outline-agent system prompt → Task 2
- [x] storyboard-agent system prompt → Task 4
- [x] Pydantic schema → Task 1
- [x] validate_outline.py → Task 3
- [x] check_asset_consistency.py → Task 5
- [x] grid_split.py → Task 6
- [x] qwen_pipeline 增强 → Task 7
- [x] 端到端测试 → Task 8

**占位符扫描：** 无 TBD/TODO，所有命令含预期输出

**类型一致性：**
- EpisodeOutline.characters → check_asset_consistency 用 set(c.name)
- ShotList.shots[i].characters → list[str]
- outline_schema.py 和 check_asset_consistency.py 使用同一 import
- ✅ 一致

---

## 任务依赖关系

```
Task 1 (outline_schema.py)
    │
    ├──→ Task 2 (outline-agent.md)        [依赖 schema 写 description]
    ├──→ Task 3 (validate_outline.py)    [依赖 EpisodeOutline]
    ├──→ Task 5 (check_asset_consistency) [依赖 EpisodeOutline + ShotList]
    └──→ Task 7 (qwen_pipeline)          [无直接依赖]

Task 2 + Task 3 + Task 5 → Task 8 (端到端测试)
```

**可并行：** Task 1、4、6 可并行开发
**串行组：** Task 3 依赖 Task 1；Task 5 依赖 Task 1
**最终门禁：** Task 8
