---
title: Wiki Overview
type: overview
date: 2026-04-18
---

# Wiki Overview

> 领域全景图 — 随知识增长持续演进
> 本文件回答：这个 wiki 覆盖哪些领域？核心主题是什么？

## 领域范围

知识管理与个人知识库构建 — 以 LLM 为驱动力的知识编译、组织与维护模式。

## 核心主题

### 知识管理范式

- **RAG vs Wiki**：检索式 vs 编译式知识管理
- **Memex 传统**：从 Vannevar Bush（1945）到 LLM-Wiki 的思想演进
- **复利知识**：持久、累积、越用越有价值的知识体系

### Agent 工作流

- **Ingest**：摄入源文件，更新 10-15 个页面
- **Query**：查询知识，好回答可回流
- **Lint**：健康检查，保持 wiki 不腐烂

### 工具链

- **Obsidian**：IDE，图谱视图、Web Clipper、Dataview
- **Schema**：配置文件（CLAUDE.md/rules/），定义 wiki 维护约定
- **Index + Log**：双导航系统（内容导向 + 时间导向）

## 关键洞察

1. LLM 解决了 Memex 无法解决的问题：谁来维护知识库
2. 维护成本接近零 → 人类放弃 wiki 的主要原因被消除
3. 好的回答应该回流进 wiki，不消失在聊天历史中
4. Schema 是让 Agent 从"通用聊天机器人"变成"有纪律的 wiki 维护者"的关键

## 待探索

- 向量搜索集成（qmd 或自建），应对 wiki 规模增长
- wiki → 文章输出的接通
- 文章 → wiki 回流机制
- 团队知识库场景的适用性
- Obsidian Dataview 动态查询的利用

---

## 更新历史

| 日期 | 更新内容 |
|------|----------|
| 2026-04-18 | 初始化 + 第一次 ingest（LLM Wiki） |
