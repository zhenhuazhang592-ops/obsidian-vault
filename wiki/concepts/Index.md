---
title: "Index"
type: concept
tags: [navigation, tool]
sources: [2026-04-18-llm-wiki]
last_updated: 2026-04-18
---

## Definition

内容目录（wiki/index.md）— wiki 的导航核心。按分类组织，每个条目有链接和一行摘要。Agent 在每次 ingest 时更新。

## Key Principles

- **内容导向**：按分类（sources/entities/concepts/syntheses）组织
- **每次 ingest 更新**：新页面创建后立即添加到 index
- **中等规模够用**：~100 源 / ~数百页面时，index 文件够用，不需要向量搜索

## Applications

- 查询时先读 index 定位相关页面
- 浏览 wiki 全貌

## Related Concepts

- [[LLM-Wiki]] — 整体模式
- [[Log]] — 时间线日志（互补）
- [[Ingest]] — 每次摄入更新 index
