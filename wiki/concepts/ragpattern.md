---
title: RAG Pattern
type: concept
date: 2024-01-01
tags:
  - llm
  - retrieval
sources:
  - wiki/sources/2024-01-01-llm-wiki.md
---

# Summary

RAG (Retrieval Augmented Generation) is the traditional approach to combining LLMs with documents, where the LLM retrieves relevant chunks at query time and generates an answer. The article critiques this approach as lacking accumulation—the LLM must rediscover and piece together knowledge from scratch on every question, with no persistent synthesis or cross-references.

## Key Characteristics

- Upload collection of files
- Retrieve relevant chunks at query time
- Generate answer without accumulation
- No persistent synthesis across queries
- Requires finding fragments every time

## Limitations

- No accumulation of knowledge
- No proactive cross-references
- Contradictions not flagged persistently
- Subtle questions requiring synthesis across documents are difficult

## Connections

- [[LLMWikiPattern]] - Proposed alternative
- [[NotebookLM]] - Example product using this approach
- [[EmbeddingBasedRetrieval]] - Technical foundation