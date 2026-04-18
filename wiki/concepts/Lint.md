---
title: "Lint"
type: concept
tags: [operation, workflow, quality]
sources: [2026-04-18-llm-wiki]
last_updated: 2026-04-18
---

## Definition

健康检查 — 定期检查 wiki 的健康状态，发现矛盾、孤儿页面、断链、过时内容、缺失实体。

## Key Principles

- **定期执行**：建议每周一次
- **Agent 擅长发现问题**：矛盾、孤儿、断链、缺失
- **建议新问题和新来源**：Agent 可以建议下一步调查什么

## Check Items

| 检查项 | 说明 |
|--------|------|
| 矛盾 | 页面间冲突的主张 |
| 孤儿页面 | 没有入站链接的页面 |
| 断链 | 指向不存在页面的 wikilink |
| 过时摘要 | 含"待填充"或超过 30 天未更新 |
| 缺失实体页 | 在 3+ 页面提及但没有独立页面的实体 |
| 数据缺口 | wiki 无法回答的问题 |

## Applications

- 保持 wiki 健康：随时间增长不腐烂
- 发现知识缺口：知道还有什么需要补充

## Related Concepts

- [[LLM-Wiki]] — 整体模式
- [[Ingest]] — 摄入操作
- [[Query]] — 查询操作
