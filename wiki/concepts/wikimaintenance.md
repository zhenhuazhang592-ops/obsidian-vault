---
title: Wiki Maintenance
type: concept
date: 2024-01-01
tags:
  - knowledge-management
  - workflow
sources:
  - wiki/sources/2024-01-01-llm-wiki.md
---

# Summary

Wiki Maintenance encompasses the ongoing operations that keep the wiki healthy as it grows: ingesting new sources, answering queries, and periodically running lint passes to check for contradictions, stale claims, orphan pages, and missing cross-references. The LLM handles all maintenance tasks.

## Core Operations

1. **Ingest**: Process new sources, update wiki pages, log entries
2. **Query**: Search relevant pages, synthesize answers with citations
3. **Lint**: Health-check for consistency and gaps

## Lint Checklist

- Contradictions between pages
- Stale claims superseded by newer sources
- Orphan pages with no inbound links
- Important concepts lacking their own page
- Missing cross-references
- Data gaps fillable with web search

## Connections

- [[LLMWikiPattern]] - Applied in this context
- [[KnowledgeSynthesis]] - Part of maintenance
- [[IncrementalKnowledgeBuilding]] - Result of maintenance