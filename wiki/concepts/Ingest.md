---
title: "Ingest"
type: concept
tags: [operation, workflow]
sources: [2026-04-18-llm-wiki]
last_updated: 2026-04-18
---

## Definition

摄入操作 — 将 raw/ 目录下的源文件转化为 wiki/ 目录下的结构化知识。一篇源可能触动 10-15 个 wiki 页面。

## Key Principles

- **逐条摄入，人类参与**：读源 → 与用户讨论要点 → 生成页面
- **一篇源触动多个页面**：来源页 + 实体页 + 概念页 + 索引 + 日志
- **标记矛盾**：新源与已有页面矛盾时，标记矛盾，等待确认

## Workflow

```
raw/source.md
    │
    ▼ 读源文件
    │
    ▼ 与用户讨论要点
    │
    ▼ 生成来源页（wiki/sources/）
    │
    ▼ 提取实体（wiki/entities/）
    │
    ▼ 提取概念（wiki/concepts/）
    │
    ▼ 更新索引（wiki/index.md）
    │
    ▼ 追加日志（wiki/log.md）
```

## Applications

- 剪藏网页 → 摄入进 wiki
- 阅读 PDF → 摄入进 wiki
- 手写笔记 → 摄入进 wiki

## Related Concepts

- [[LLM-Wiki]] — 整体模式
- [[Query]] — 查询操作
- [[Lint]] — 健康检查
- [[Index]] — 更新索引
- [[Log]] — 追加日志
