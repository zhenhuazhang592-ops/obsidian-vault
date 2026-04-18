---
title: "LLM-Wiki"
type: concept
tags: [pattern, knowledge-management]
sources: [2026-04-18-llm-wiki]
last_updated: 2026-04-18
---

## Definition

LLM-Wiki 是一种用 LLM 构建个人知识库的模式：不是 RAG 检索（每次重新发现知识），而是让 LLM 持续编译和维护一个结构化的 wiki。知识编译一次，持续更新，复利增长。

## Key Principles

- **编译 vs 检索**：RAG 每次从原始文档重新检索 → 无积累；LLM-Wiki 编译后持续更新 → 复利增长
- **角色分工**：Obsidian 是 IDE，LLM 是程序员，Wiki 是代码库
- **人类职责**：策划源文件、指导分析、提出好问题、思考意义
- **Agent 职责**：总结、交叉引用、归档、维护 — 一切"体力活"

## Applications

- 个人成长：追踪目标、健康、心理学、自我提升
- 深度研究：阅读论文、文章、报告，逐步构建综合 wiki
- 阅读书籍：边读边建角色、主题、情节页面
- 团队知识：内部 wiki，由 Slack/会议/文档喂养
- 竞品分析、尽职调查、旅行规划、课程笔记、爱好深度研究

## Related Concepts

- [[Compounding-Knowledge]] — 复利增长的知识
- [[Ingest]] — 摄入操作
- [[Query]] — 查询操作
- [[Lint]] — 健康检查
- [[Schema]] — 配置文件
- [[Memex]] — 精神先驱
