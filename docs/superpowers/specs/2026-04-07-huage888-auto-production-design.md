# huage888 全自动漫剧生产系统 · 设计文档

> 日期：2026-04-07
> 目标：参考 Toonflow v1.0.7，在 Claude Code 中实现全自动漫剧生产
> 方案：纯 Claude Code（方案 B），不引入 Python 微服务

---

## 一、整体架构

```
剧本 (.md)
    │
    ▼
┌─────────────────────────────────────────────┐
│  outline-agent（Claude Code + Python验证）    │
│  输入：剧本正文 + style prompt                │
│  输出：outline JSON（Zod校验）                │
│  → 写入 outputs/S01E01-outline.md           │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│  storyboard-agent（Claude Code）             │
│  输入：outline JSON + assets                 │
│  输出：shots → outputs/S01E01-shots.md      │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
          assets/（characters/scenes/props）
                      │
                      ▼
              Doubao API / LibTV 手动
```

**Python 职责仅限**：
- 格式校验（Zod/Pydantic）
- JSON Schema 定义
- 图像切割（Pillow）
- API 封装调用

**Claude Code 职责**：
- 所有 Agent 逻辑（system prompt + tool calling 模拟）
- 内容生成编排
- 资产一致性约束
- 质量审核

---

## 二、数据存储

### 2.1 目录结构

```
AI工具箱/huage888/
├── agents/
│   ├── outline-agent.md       # outline-agent system prompt
│   └── storyboard-agent.md    # storyboard-agent system prompt
├── assets/
│   └── S01E01-assets.md      # frontmatter + JSON 资产表
├── outputs/
│   ├── S01E01-outline.md     # 大纲 JSON（Zod 校验后）
│   ├── S01E01-shots.md      # 分镜列表
│   └── S01E01-shot-guide.md # LibTV 操作指南
├── scripts/
│   ├── validate_outline.py   # Zod/Pydantic 校验
│   ├── check_asset_consistency.py  # 资产一致性检查
│   └── grid_split.py        # Pillow 宫格切割
└── config/
    └── outline_schema.py     # Zod schema 定义
```

### 2.2 Outline JSON Schema

```json
{
  "episodeIndex": 1,
  "title": "断桥奇遇",
  "chapterRange": [1],
  "scenes": [{"name": "...", "description": "..."}],
  "characters": [{"name": "漠玫", "description": "..."}],
  "props": [{"name": "...", "description": "..."}],
  "coreConflict": "漠玫以自然树熟折服大圣",
  "outline": "100-300字剧情主干",
  "openingHook": "第一个镜头画面",
  "keyEvents": ["起", "承", "转", "合"],
  "emotionalCurve": "2(压抑)→5(反抗)→9(爆发)→3(余波)",
  "visualHighlights": ["标志性镜头1", "标志性镜头2"],
  "endingHook": "悬念延伸",
  "classicQuotes": ["金句1", "金句2"]
}
```

### 2.3 Shots Schema

```json
{
  "episode": "S01E01",
  "style": "赛博墨韵",
  "shots": [
    {
      "index": 1,
      "segmentTitle": "断桥初遇",
      "description": "镜头画面描述（50-100字）",
      "emotion": "平静",
      "shotType": "中景",
      "characters": ["漠玫"],
      "scene": "断桥",
      "props": [],
      "imagePrompt": "英文生图提示词（含赛博墨韵锚定词）",
      "videoPrompt": "英文生视频提示词（可选）",
      "notes": "运镜/时长备注"
    }
  ]
}
```

---

## 三、Agent 设计

### 3.1 outline-agent

**调用**：`python3 config/qwen_pipeline.py --agent outline --user "<剧本正文>" --output outputs/S01E01-outline.md`

**System Prompt 核心**：
- 角色：资深短剧编剧
- 输出格式：Markdown 包含 ```json 代码块
- 规则：outline 是唯一权威，keyEvents 严格按顺序，禁止捏造资产

**Validator**（`scripts/validate_outline.py`）：
1. 提取 ```json ``` 块内容
2. JSON.parse
3. Zod Schema 校验
4. 通过 → 写入 `outputs/S01E01-outline.md`（带 frontmatter）
5. 失败 → 打印错误字段 + exit 1，Claude Code 重新生成

### 3.2 storyboard-agent

**调用**：`python3 config/qwen_pipeline.py --agent storyboard --user "基于以下大纲生成shots" --asset-output assets/S01E01-assets.json`

**System Prompt 头部（资产一致性硬约束）**：
```
⚠️ 资产一致性规则：
1. characters 字段必须使用 outline 中的角色全名，禁止近义词/缩写
2. scene 字段必须使用 outline 中的场景名称，禁止自行发挥
3. props 数组只能包含 outline 中已有的道具
4. 违反以上规则，Validator 将拒绝输出
```

**Shot 生成规则**：
- 每个 keyEvent 展开为 3-5 个镜头
- 情绪曲线决定节奏（压抑→慢/近景；爆发→快/特写）
- imagePrompt 必须包含风格锚定词
- 同一角色连续镜头保持描述一致性

### 3.3 衔接流程

```
outline-agent → outputs/S01E01-outline.md
                      │
                      ▼
         storyboard-agent 读取 outline JSON
                      │
                      ▼
         assets/S01E01-assets.json（提取 characters/scenes/props）
                      │
                      ▼
         shots → outputs/S01E01-shots.md
```

---

## 四、资产一致性检查

**文件**：`scripts/check_asset_consistency.py`

```
shots.md 的 characters/scene/props
        │
        ▼
scripts/check_asset_consistency.py
        │
        ├── 读取 outline JSON 中的 assets 列表
        ├── 对比 shots 中的引用
        └── 发现不一致 → 报错并列出具体字段
```

**检查项**：
- [ ] shots 中出现的每个 character 在 outline characters 中存在
- [ ] shots 中出现的每个 scene 在 outline scenes 中存在
- [ ] shots 中出现的每个 prop 在 outline props 中存在
- [ ] 所有必填字段（index/description/emotion/imagePrompt）非空

---

## 五、图像管线

### 5.1 执行模式

| 模式 | 说明 | 优先级 |
|------|------|--------|
| **manual** | 生成操作指南，用户在 LibTV 手动执行 | P0 先跑通 |
| **api** | 直接调用 Doubao 图生图 API | P1 |
| **batch** | 分镜批量出图（宫格合并） | P2 |

### 5.2 宫格切割（`scripts/grid_split.py`）

```
shots 1-9 合并 → 单张宫格图（16:9）
        │
        ▼
python3 scripts/grid_split.py --input grid.png --rows 3 --cols 3
        │
        └── 输出 shot_01.png ... shot_09.png
```

### 5.3 Shot Guide 生成

`outputs/S01E01-shot-guide.md` 包含：
- 每个 shot 的操作步骤（LibTV 操作序列）
- 对应的 imagePrompt（英文原文）
- 参考图（已在 assets/ 中的角色/场景图）
- 风格锚定词提示

---

## 六、首批实施（漠玫传 S01E01）

**测试项目**：漠玫传 S01E01《断桥奇遇》

### 6.1 实施步骤

```
Step 1  outline-agent
        → 喂入漠玫传剧本（已有）
        → 输出 assets/S01E01-character-list.md
        → Python Validator 校验通过
        │
Step 2  手工补全 scenes/props（如剧本缺场景描述）
        → 编辑 assets/S01E01-assets.md
        │
Step 3  storyboard-agent
        → 基于完整 assets 生成 shots
        → 输出 outputs/S01E01-shots.md
        │
Step 4  资产一致性检查
        → scripts/check_asset_consistency.py
        │
Step 5  生成 shot-guide.md
        → 用户在 LibTV 执行出图
```

### 6.2 验收标准

- [ ] outline JSON 通过 Zod 校验（必填字段 100%）
- [ ] shots 的 characters/scenes/props 与 outline 100% 一致
- [ ] shot-guide.md 可直接在 LibTV 执行
- [ ] 无需手动修改生成的 JSON/YAML

---

## 七、技术参考

- Toonflow 全架构分析：`.claude/knowledge/toonflow-architecture.md`
- huage888 现有脚手架：event_emitter.py / task_state.py / task_queue.py / asset_version.py / art_styles.py / prompts_registry.py
- 调用方式：qwen_pipeline.py（已有）
