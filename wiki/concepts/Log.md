---
title: "Log"
type: concept
tags: [navigation, tool]
sources: [2026-04-18-llm-wiki]
last_updated: 2026-04-18
---

## Definition

时间线日志（wiki/log.md）— append-only 记录 wiki 的演变历史。条目格式统一，可用 grep 解析。

## Key Principles

- **时间导向**：按时间顺序记录 ingests、queries、lint passes
- **Append-only**：只追加，不删除或修改
- **可解析**：统一前缀格式，如 `## [YYYY-MM-DD] ingest | Title`
- **用 grep 查最近**：`grep "^## \[" log.md | tail -5` 查最近 5 条

## Applications

- 理解 wiki 的演变历史
- Agent 了解最近做了什么
- 审计和回溯

## Related Concepts

- [[LLM-Wiki]] — 整体模式
- [[Index]] — 内容目录（互补）
- [[Ingest]] — 每次摄入追加 log
