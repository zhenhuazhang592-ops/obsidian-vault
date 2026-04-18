---
title: LLM Wiki Pattern
type: concept
date: 2024-01-01
tags:
  - llm
  - knowledge-management
  - architecture
sources:
  - wiki/sources/2024-01-01-llm-wiki.md
---

# Summary

The LLM Wiki Pattern is a methodology for building personal knowledge bases where an LLM incrementally builds and maintains a persistent wiki between users and their raw sources. Unlike traditional RAG systems that re-derive knowledge on every query, this pattern creates a compounding artifact where knowledge accumulates, cross-references exist proactively, and contradictions are flagged. The human provides sources and questions; the LLM handles all writing and maintenance.

## Key Principles

1. **Persistence Over Retrieval**: Knowledge is compiled once and kept current, not re-derived on every query
2. **LLM as Maintainer**: The LLM writes, updates, cross-references, and maintains the wiki entirely
3. **Human as Curator**: Humans focus on sourcing, exploration, and asking the right questions
4. **Compounding Value**: Both ingested sources AND query explorations become wiki pages

## Three-Layer Architecture

- **Raw Sources**: Immutable source documents (articles, papers, images)
- **The Wiki**: LLM-generated markdown files (summaries, entities, concepts)
- **The Schema**: Configuration file (CLAUDE.md/AGENTS.md) defining structure and workflows

## Core Operations

- **Ingest**: Process new sources into wiki updates
- **Query**: Ask questions, receive synthesized answers
- **Lint**: Health-check for contradictions and gaps

## Applications

- Personal goal/health/psychology tracking
- Research synthesis over weeks/months
- Book reading companion
- Business/team internal wikis
- Competitive analysis, due diligence, trip planning

## Connections

- [[RAGPattern]] - Contrast: traditional retrieval approach
- [[PersonalKnowledgeBase]] - Broader context
- [[SchemaDrivenLLM]] - Configuration mechanism
- [[KnowledgeSynthesis]] - Core process
- [[Obsidian]] - Recommended IDE
- [[ClaudeCode]] - Target agent platform
- [[OpenAICodex]] - Target agent platform