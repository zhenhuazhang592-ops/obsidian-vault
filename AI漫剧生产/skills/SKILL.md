# AI Short Drama Studio — Skill 索引

> 版本: 3.0.0
> 更新: 2026-03-26（新增漫舟·导演版：LibTV一体化Agent）

## 系统说明

AI Short Drama Studio 是一个小说→AI漫剧的工业化生产系统。
每个 Engine 做成独立的 `.md` Skill 文件，主控 Agent 统一接收用户输入并调度子 Agent。

## Skill 清单

### 第一期（剧本创作系统）

| 序号 | Skill 文件 | 职责 | 状态 |
|------|-----------|------|------|
| 1 | `manzhou-master.md` | 主控 Agent，统一调度所有子 Agent | ✅ |
| 2 | `manzhou-ip-parser.md` | IP解析：小说→世界观/人物/冲突 | ✅ |
| 3 | `manzhou-script.md` | 剧本生成：三维一体执行脚本 | ✅ |
| 4 | `manzhou-storyboard.md` | 分镜输出：Seedance/Kling Prompt | ✅ |
| 5 | `manzhou-safety.md` | 风控审核：敏感词/合规检查 | ✅ |
| 6 | `obsidian-storage.md` | Obsidian 存储规范 | ✅ |

### 第二期（爆款+视觉系统）

| 序号 | Skill 文件 | 职责 | 状态 |
|------|-----------|------|------|
| 7 | `manzhou-hit-engine.md` | 爆款算法：SRL模型/3-15-30规则/爆点触发矩阵 | ✅ |
| 8 | `manzhou-visual-style.md` | 视觉风格库：5种风格包/四维度锚点 | ✅ |
| 9 | `manzhou-character-consistency.md` | 角色一致性：DNA三层锁/九宫格定妆表 | ✅ |

### 第三期（音频系统）

| 序号 | Skill 文件 | 职责 | 状态 |
|------|-----------|------|------|
| 10 | `manzhou-voice.md` | VO参数 → 注入分镜Prompt：`voice:(情绪)"台词"` | ✅ v2.0.0 |
| 11 | `manzhou-bgm.md` | BGM参数 → 注入分镜Prompt：`[BGM: 情绪描述]` | ✅ v2.0.0 |
| 12 | `manzhou-sfx.md` | SFX参数 → 注入分镜Prompt：`[SFX: 音效]` | ✅ v2.0.0 |
| 13 | `manzhou-audio.md` | 音频三要素同步注入规范（三合一） | ✅ v2.0.0 |

### 第四期（LibTV一体化 - 漫舟·导演版）

| 序号 | Skill 文件 | 职责 | 状态 |
|------|-----------|------|------|
| 14 | `manzhou-director-v2.md` | **漫舟·导演版**：从LibTV Agent脱胎，复用执行层+漫舟逻辑能力 | ✅ v2.0.0 NEW |

## 漫舟·导演版 vs LibTV Agent

| 能力 | LibTV Agent | 漫舟·导演版 |
|------|-------------|------------|
| 执行层（API调用） | ✅ | ✅ 完整复用 |
| 轮询+下载 | ✅ | ✅ 完整复用 |
| 小说理解 | ❌ | ✅ |
| IP解析 | ❌ | ✅ |
| 剧本生成 | ❌ | ✅ |
| 导演控制塔 | ❌ | ✅ |
| 角色DNA | ❌ | ✅ |
| 分镜编排 | ❌ | ✅ |
| 运镜意图传递 | ❌ | ✅ |
| **核心差异** | 传话筒 | **总导演** |

## 使用流程

```
用户输入 → manzhou-master（主控）
                ↓
        manzhou-ip-parser（IP解析）
                ↓
        manzhou-script（剧本生成）
                ↓
        manzhou-hit-engine（爆款检测）
                ↓
        manzhou-visual-style（视觉风格）
                ↓
        manzhou-character-consistency（角色一致性）
                ↓
        manzhou-storyboard（分镜Prompt）
                ↓
        ┌───────────────────────────────┐
        │ manzhou-voice  → voice: 行    │──┐
        │ manzhou-bgm    → [BGM:] 行   │──┼──▶ 分镜Prompt（完整7要素）
        │ manzhou-sfx    → [SFX:] 行   │──┘
        └───────────────────────────────┘
                ↓
        manzhou-safety（风控审核）
                ↓
        写入 Obsidian → Seedance/Kling 生成
```

## 核心规范

### 目录结构（统一标准）

```
AI漫剧生产/[项目名]/
├── 00-项目信息/
├── 01-IP档案/
├── 02-剧本/
├── 03-分镜/              ← 含完整Prompt（画面+voice:+[BGM:]+[SFX:]）
├── 04-Prompts/           ← 测试用Prompt包
├── 05-资产库/
├── 07-音频包/           ← 配音标签、BGM时间轴、SFX标注（v2.0.0新增）
└── 99-归档/
```

### 角色双层ID体系

| 层级 | 格式 | 用途 |
|------|------|------|
| YAML机器码 | `protagonist_01` / `antagonist_01` | IP档案.yaml、frontmatter |
| 英文名 | `LinFeng` / `WangYanMei` | Prompt引用、wikilink、文件命名 |
| 指纹ID | `LinFeng_V1` / `LinFeng_V2` | Seedance/Kling角色锁定 |

### 核心规则

1. **绝对禁止占位符** — 禁止"..."、"等"、"以此类推"
2. **每个镜头必须完整输出** — 要求12集就写满12集
3. **Prompt 可直接复制使用** — 无需用户二次加工
4. **情绪与听觉必须绑定** — 每镜头含 SFX/Emotion 标签

## 调用子 Agent 格式

### 模式A：分步执行（传统方式）

```
===CALL_AGENT===
agent: manzhou-ip-parser
input: [用户输入的小说文本]
===END_CALL===
...
```

### 模式B：漫舟·导演版一体化执行（推荐）

```
===CALL_AGENT===
agent: manzhou-director-v2
input: [小说文本 或 项目名 + 集数]
===END_CALL===
```

**manzhou-director-v2 调用说明**：

| 输入场景 | 说明 |
|---------|------|
| 小说文本 | 从头生成完整漫剧（Step 1-9） |
| 项目名 + 集数 | 读取已有项目，执行LibTV生成 |
===CALL_AGENT===
agent: manzhou-ip-parser
input: [用户输入的小说文本]
===END_CALL===

===CALL_AGENT===
agent: manzhou-script
input: [IP档案内容 + 用户要求]
===END_CALL===

===CALL_AGENT===
agent: manzhou-hit-engine
input: [分集剧本 + 用户要求的爆点密度]
===END_CALL===

===CALL_AGENT===
agent: manzhou-visual-style
input: [分集剧本 + 用户选择的视觉风格]
===END_CALL===

===CALL_AGENT===
agent: manzhou-character-consistency
input: [IP档案人物体系 + 九宫格定妆要求]
===END_CALL===

===CALL_AGENT===
agent: manzhou-storyboard
input: [剧本 + 视觉风格选择 + 角色DNA手册]
===END_CALL===

===CALL_AGENT===
agent: manzhou-storyboard
input: [剧本 + 视觉风格选择 + 角色DNA手册]
===END_CALL===

===CALL_AGENT===
agent: manzhou-voice
input: [分集剧本] → 输出：逐镜voice:行
===END_CALL===

===CALL_AGENT===
agent: manzhou-bgm
input: [分集剧本] → 输出：逐镜[BGM:]行
===END_CALL===

===CALL_AGENT===
agent: manzhou-sfx
input: [分集剧本 + 分镜描述] → 输出：逐镜[SFX:]行
===END_CALL===

===CALL_AGENT===
agent: manzhou-audio
input: [分集剧本 + 分镜] → 验证三要素完整注入Prompt
===END_CALL===

===CALL_AGENT===
agent: manzhou-safety
input: [全部内容]
===END_CALL===
```

## 文件路径

```
AI漫剧生产/skills/
├── SKILL.md                        # 本文件（索引）
├── manzhou-master.md               # 主控 Agent
├── manzhou-director-v2.md         # 漫舟·导演版（LibTV一体化）⭐ NEW
├── manzhou-ip-parser.md            # IP 解析引擎
├── manzhou-script.md              # 剧本生成引擎
├── manzhou-storyboard.md           # 分镜输出引擎
├── manzhou-safety.md               # 风控审核引擎
├── manzhou-hit-engine.md           # 爆款算法引擎
├── manzhou-visual-style.md         # 视觉风格库
├── manzhou-character-consistency.md # 角色一致性引擎
├── manzhou-voice.md                # 配音标签引擎
├── manzhou-bgm.md                 # BGM 生成引擎
├── manzhou-sfx.md                  # SFX 音效引擎
├── manzhou-audio.md               # 音频系统整合引擎
└── obsidian-storage.md             # Obsidian 存储规范

AI漫剧生产/libtv-skills-main/      # LibTV 执行层
└── skills/libtv-skill/
    └── scripts/
        ├── create_session.py      # 创建会话
        ├── query_session.py       # 轮询结果
        ├── upload_file.py         # 上传参考图
        └── download_results.py    # 下载结果
```

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-24 | 第一期 6 个 Skill 全部完成 |
| 1.1.0 | 2026-03-24 | 新增目录结构规范和角色双层ID体系说明 |
| 1.2.0 | 2026-03-24 | 第二期 3 个 Skill 完成：爆款算法/视觉风格库/角色一致性 |
| 1.3.0 | 2026-03-24 | 修复第二期：时间轴对齐/命名代号歧义/集成规则矛盾 |
| 1.4.0 | 2026-03-24 | 第三期 4 个 Skill 完成：配音标签/BGM/SFX/音频整合；更新工作流和调用格式 |
| 1.5.0 | 2026-03-24 | 全局审查修复：更新使用流程，加入visual-style步骤；完善Agent调用参数 |
| 2.0.0 | 2026-03-25 | 音频系统架构重构：voice/BGM/SFX三要素直接注入分镜Prompt |
| **3.0.0** | **2026-03-26** | **第四期：新增漫舟·导演版（manzhou-director-v2.md），从LibTV Agent脱胎，完整执行层+漫舟逻辑能力一体化** |
