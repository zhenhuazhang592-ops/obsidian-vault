---
title: "Query"
type: concept
tags: [operation, workflow]
sources: [2026-04-18-llm-wiki]
last_updated: 2026-04-18
---

## Definition

查询操作 — 从 wiki 中查找知识，综合多个来源生成答案。好的回答可以回流进 wiki 作为新页面。

## Key Principles

- **先查索引**：读 wiki/index.md 定位相关类别
- **再读页面**：读来源页、实体页、概念页
- **综合回答**：整合多个来源，标注 [[wikilink]] 引用
- **可回流**：优质回答可存为 wiki/syntheses/ 下的综合页

## Workflow

```
用户问题
    │
    ▼ 读 wiki/index.md
    │
    ▼ 搜索/读相关页面
    │
    ▼ 综合回答（带 [[wikilink]]）
    │
    ▼ 可选：保存到 wiki/syntheses/
```

## Applications

- 问答：从 wiki 中找答案
- 对比：比较多个实体/概念
- 分析：综合多个来源得出洞察

## Related Concepts

- [[LLM-Wiki]] — 整体模式
- [[Ingest]] — 摄入操作
- [[Lint]] — 健康检查
- [[Index]] — 查索引
