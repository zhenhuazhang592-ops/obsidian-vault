---
title: Schema-Driven LLM
type: concept
date: 2024-01-01
tags:
  - llm
  - configuration
sources:
  - wiki/sources/2024-01-01-llm-wiki.md
---

# Summary

Schema-Driven LLM refers to the practice of providing LLMs with explicit schema documents (like CLAUDE.md or AGENTS.md) that define structure, conventions, and workflows. In the LLM Wiki pattern, the schema is the key configuration that transforms a generic chatbot into a disciplined wiki maintainer with specific behaviors for ingesting sources, answering queries, and maintaining the wiki.

## Key Elements

- Defines wiki structure and conventions
- Specifies workflows for operations (ingest, query, lint)
- Co-evolved between human and LLM over time
- Example: CLAUDE.md for Claude Code, AGENTS.md for Codex

## Why It Matters

Without schema, LLMs are generic chatbots. With schema, they become specialized agents with consistent behaviors and domain knowledge.

## Connections

- [[LLMWikiPattern]] - Core application of this concept
- [[ClaudeCode]] - Uses CLAUDE.md
- [[OpenAICodex]] - Uses AGENTS.md
- [[AgentConfiguration]] - Broader context