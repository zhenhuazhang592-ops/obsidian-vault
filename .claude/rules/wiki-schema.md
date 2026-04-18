# Wiki 维护 Schema

> 本文件是 LLM-wiki 模式的核心配置 — 让 Agent 成为"有纪律的 wiki 维护者"
> 基于 [llm-wiki.md](https://github.com/tobi) 模式

---

## 核心理念

**不是 RAG 检索，而是 Agent 持续编译 wiki。**

- Obsidian 是 IDE
- Agent 是程序员
- Wiki 是代码库
- 知识编译一次，持续更新，复利增长

---

## 三层架构

| 层 | 位置 | 所有者 | 说明 |
|------|------|--------|------|
| Raw | `raw/` | 人类 | 不可变源文件，Agent 只读不写 |
| Wiki | `wiki/` | Agent | 结构化知识页面，Agent 完全控制 |
| Graph | 图谱视图 | Obsidian | 可视化 wikilinks 关系 |

---

## 目录约定

```
raw/
├── articles/       # 文章（web clipper 导入）
├── papers/         # 论文 PDF
├── notes/          # 手写笔记
└── assets/         # 图片等附件

wiki/
├── sources/        # 来源摘要页
├── entities/       # 实体页（人物/公司/产品）
├── concepts/       # 概念页（方法/理论/框架）
├── syntheses/      # 综合页（查询产生的新洞察）
├── index.md        # 内容目录（每次 ingest 更新）
├── log.md          # 时间线日志（append-only）
└── overview.md     # 领域全景图（持续演进）
```

---

## 页面格式

### 来源页模板

**命名**：`wiki/sources/YYYY-MM-DD-slug.md`

```markdown
---
title: "Source Title"
type: source
date: YYYY-MM-DD
source_file: raw/path/to/source.md
tags: []
---

## Summary

2-4 句摘要。核心内容概括。

## Key Claims

- 主张 1：具体内容
- 主张 2：具体内容

## Key Quotes

> "引用内容" — 上下文说明

## Connections

- [[EntityName]] — 关联方式
- [[ConceptName]] — 连接方式

## Contradictions

（如有）与 [[OtherPage]] 矛盾：矛盾点描述
```

### 实体页模板

**命名**：`wiki/entities/PascalCase.md`（如 `OpenAI.md`、`Vannevar-Bush.md`）

```markdown
---
title: "Entity Name"
type: entity
tags: [person | company | product | place]
sources: [source-slug-1, source-slug-2]
last_updated: YYYY-MM-DD
---

## Overview

实体概述。

## Key Facts

- 事实 1
- 事实 2

## Mentions

在以下来源中被提及：

- [[sources/YYYY-MM-DD-slug-1]] — 提及上下文

## Related Entities

- [[RelatedEntity]] — 关系描述
```

### 概念页模板

**命名**：`wiki/concepts/PascalCase.md`（如 `LLM-Wiki.md`、`Ingest.md`）

```markdown
---
title: "Concept Name"
type: concept
tags: [framework | method | theory | pattern]
sources: [source-slug-1]
last_updated: YYYY-MM-DD
---

## Definition

概念定义。

## Key Principles

- 原则 1
- 原则 2

## Applications

- 应用场景 1

## Related Concepts

- [[RelatedConcept]] — 关系描述
```

### 综合页模板

**命名**：`wiki/syntheses/YYYY-MM-DD-topic.md`

```markdown
---
title: "Synthesis Topic"
type: synthesis
date: YYYY-MM-DD
trigger: "用户问题或洞察"
---

## Question

原始问题或触发点。

## Answer

综合回答。

## Sources

- [[sources/source-1]] — 贡献要点
- [[sources/source-2]] — 贡献要点

## New Insights

此次综合发现的新洞察。
```

---

## 快捷命令

| 命令 | 用途 |
|------|------|
| `/wiki-ingest raw/xxx.md` | 摄入源文件 |
| `/wiki-query 问题` | 查询知识库 |
| `/wiki-lint` | 健康检查 |
| `/wiki-graph` | 构建知识图谱 |

---

## 操作流程

### Ingest（摄入）

> "逐条摄入，人类参与，一篇源 → 触动 10-15 个 wiki 页"

**触发**：用户说"摄入这个来源"或 `/wiki-ingest raw/articles/xxx.md`

**流程**：

1. **读取源文件**：`Read raw/path/to/source.md`
2. **读取当前上下文**：`Read wiki/index.md` + `Read wiki/overview.md`
3. **与用户讨论要点**：确认核心内容、重点领域
4. **选择模板**：根据源文件类型选择通用/日记/会议模板
5. **生成来源页**：`Write wiki/sources/YYYY-MM-DD-slug.md`
6. **提取实体**：识别人物/公司/产品，`Write` 或 `Edit` 实体页
7. **提取概念**：识别方法/理论/框架，`Write` 或 `Edit` 概念页
8. **更新索引**：`Edit wiki/index.md`，添加新条目
9. **更新全景图**：`Edit wiki/overview.md`（如有必要）
10. **追加日志**：`Edit wiki/log.md`，追加日志条目
11. **Post-ingest 验证**（必做）：
    - 用 `Grep` 检查新页面中的 `[[wikilinks]]` 是否指向存在的页面
    - 验证所有新页面都在 `index.md` 中
    - 输出变更摘要 + 验证结果

**日志格式**：
```
## [YYYY-MM-DD] ingest | Source Title
- 来源：raw/path/to/source.md
- 创建：wiki/sources/YYYY-MM-DD-slug.md
- 实体：Entity1, Entity2
- 概念：Concept1
```

### Query（查询）

**触发**：用户问"wiki 里有什么关于 X 的内容"

**流程**：

1. **读索引**：`Read wiki/index.md`，定位相关类别
2. **搜关键词**：`Grep "keyword" wiki/` 或 `grep "keyword" wiki/`
3. **读相关页**：`Read wiki/sources/xxx.md`、`wiki/entities/Xxx.md`
4. **综合回答**：整合多个来源，标注 `[[wikilink]]` 引用
5. **可选回流**：如果是好回答，保存为 `wiki/syntheses/YYYY-MM-DD-topic.md`

### Lint（健康检查）

**触发**：用户说"检查 wiki 健康"或定期执行

**检查项**：

| 检查项 | 方法 | 修复 |
|--------|------|------|
| 孤儿页面 | 无入站链接 | 在相关页添加 wikilink |
| 断链 | wikilink 目标不存在 | 创建页面或修正链接 |
| 矛盾 | 同一实体有冲突主张 | 标记矛盾，等待确认 |
| 过时 | 含"待填充"或超 30 天未更新 | 重新摄入或更新 |
| 缺失实体 | 在 3+ 页面提及但无实体页 | 创建实体页 |

**工具**：
- `Grep "\\[\\[" wiki/` 提取所有 wikilinks
- `Glob "wiki/**/*.md"` 获取所有页面
- 对比找出孤儿和断链

---

## 与 Obsidian 的协作

> "左 Agent 右 Obsidian，实时浏览更新"

**典型工作流**：

1. 用户在 Obsidian 中用 Web Clipper 剪藏文章 → 保存到 `raw/articles/`
2. 用户切换到 Agent（Claude Code）说"摄入这个来源"
3. Agent 执行 ingest，更新 `wiki/` 下的多个文件
4. 用户在 Obsidian 中刷新，浏览图谱视图，检查更新结果
5. 用户发现遗漏或错误，告诉 Agent 修正

**Obsidian 插件推荐**：

- **Web Clipper**：快速剪藏网页到 `raw/`
- **Dataview**：基于 frontmatter 查询生成动态列表
- **Graph View**：可视化 wikilinks 关系
- **Marp**：从 wiki 内容生成幻灯片

---

## 命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 来源页 | `YYYY-MM-DD-slug.md` | `2026-04-18-llm-wiki.md` |
| 实体页 | `PascalCase.md` | `OpenAI.md`、`Vannevar-Bush.md` |
| 概念页 | `PascalCase.md` | `Ingest.md`、`Compounding-Knowledge.md` |
| 综合页 | `YYYY-MM-DD-topic.md` | `2026-04-18-agent-workflow.md` |

**slug 规则**：小写、连字符分隔、去除停用词

---

## 质量标准

### 来源页

- [ ] Summary 2-4 句，信息密度高
- [ ] Key Claims 至少 2 条，具体可验证
- [ ] Key Quotes 至少 1 条直接引用
- [ ] Connections 至少 2 个 wikilink
- [ ] 无"待填充"

### 实体页

- [ ] Overview 一段完整描述
- [ ] Key Facts 至少 3 条
- [ ] Mentions 至少 1 个来源链接
- [ ] sources 字段完整

### 概念页

- [ ] Definition 清晰定义
- [ ] Key Principles 至少 2 条
- [ ] sources 字段完整

---

## 禁止事项

1. **禁止修改 raw/**：源文件不可变，只能读取
2. **禁止删除 index/log**：这两个文件是 wiki 的导航核心
3. **禁止跳过用户确认**：ingest 时必须与用户讨论要点
4. **禁止批量摄入**：一次只摄入一个来源，确保质量

---

## 领域专用模板

当源文件属于特定领域时，使用专用模板而非通用模板。

### 日记/日志模板

**适用**：个人日志、周记、月度回顾

```markdown
---
title: "YYYY-MM-DD 日记"
type: source
tags: [diary]
date: YYYY-MM-DD
source_file: raw/journal/YYYY-MM-DD.md
---

## Event Summary

当天/当周事件概要。

## Key Decisions

- 决策 1：背景 + 选择 + 结果
- 决策 2：...

## Energy & Mood

能量状态和情绪变化。

## Connections

- [[相关人物]] — 互动内容
- [[相关项目]] — 进展

## Shifts & Contradictions

与之前的认知或行为变化。
```

### 会议记录模板

**适用**：团队会议、访谈、客户对话

```markdown
---
title: "会议标题"
type: source
tags: [meeting]
date: YYYY-MM-DD
source_file: raw/meetings/YYYY-MM-DD-meeting.md
---

## Goal

会议目的。

## Key Discussions

- 讨论点 1：各方观点 + 结论
- 讨论点 2：...

## Decisions Made

- 决策 1：负责人 + 时间线
- 决策 2：...

## Action Items

- [ ] 任务 1（负责人，截止日期）
- [ ] 任务 2（负责人，截止日期）

## Connections

- [[相关项目]]
- [[相关人员]]
```

### 论文/研究模板

**适用**：学术论文、研究报告

```markdown
---
title: "论文标题"
type: source
tags: [paper]
date: YYYY-MM-DD
source_file: raw/papers/paper-name.md
---

## Summary

研究问题、方法、结论（2-4 句）。

## Key Claims

- 主张 1：证据支持
- 主张 2：证据支持

## Methodology

研究方法概述。

## Key Quotes

> "引用内容" — 页码/章节

## Connections

- [[相关作者]]
- [[相关机构]]
- [[相关概念]]

## Limitations & Contradictions

研究局限，与其他研究的矛盾点。
```
