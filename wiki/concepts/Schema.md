---
title: "Schema"
type: concept
tags: [configuration, architecture]
sources: [2026-04-18-llm-wiki]
last_updated: 2026-04-18
---

## Definition

Schema 是 wiki 的配置文件（如 CLAUDE.md 或 AGENTS.md），告诉 Agent 如何组织 wiki、遵循什么约定、执行什么工作流。它是让 Agent 成为"有纪律的 wiki 维护者"而非"通用聊天机器人"的关键。

## Key Principles

- **人类和 Agent 共同演进**：随着使用发现什么有效，更新 schema
- **领域定制**：不同领域的目录结构、页面格式、工作流不同
- **关键配置文件**：定义页面模板、命名规范、ingest/query/lint 流程

## Applications

- 在 CLAUDE.md 或 rules/ 中定义 wiki 维护约定
- 随领域变化调整 wiki 结构和流程

## Related Concepts

- [[LLM-Wiki]] — 整体模式
- [[Ingest]] — 摄入流程由 schema 定义
- [[Query]] — 查询流程由 schema 定义
- [[Lint]] — 检查项由 schema 定义
