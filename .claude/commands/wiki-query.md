Query the wiki knowledge base.

Usage: /wiki-query $ARGUMENTS

$ARGUMENTS should be your question, e.g. `what are the main themes?` or `tell me about AI Agent`

Follow the Query Workflow defined in rules/wiki-schema.md:

1. Read wiki/index.md to find relevant pages
2. Read matching pages from wiki/sources/, wiki/entities/, wiki/concepts/
3. Synthesize an answer with [[wikilink]] citations
4. Mark any information gaps
5. Ask if the user wants to save the answer as wiki/syntheses/YYYY-MM-DD-topic.md

Output format:
- Answer with inline [[wikilinks]]
- List of sources consulted
- Information gaps (if any)
