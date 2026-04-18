Ingest a source document into the LLM Wiki.

Usage: /wiki-ingest $ARGUMENTS

$ARGUMENTS should be the path to a file in raw/, e.g. `raw/articles/my-article.md`

Follow the Ingest Workflow defined in rules/wiki-schema.md exactly:

1. Read the source file at the given path using the Read tool
2. Read wiki/index.md and wiki/overview.md for current context
3. **Discuss key takeaways with the user** before generating pages
4. Write wiki/sources/YYYY-MM-DD-slug.md (source page format per wiki-schema.md)
5. Update wiki/index.md — add the new entry under Sources section
6. Update wiki/overview.md — revise synthesis if warranted
7. Create/update entity pages (wiki/entities/) for key people, companies, projects
8. Create/update concept pages (wiki/concepts/) for key ideas and frameworks
9. Flag any contradictions with existing wiki content
10. Append to wiki/log.md: ## [YYYY-MM-DD] ingest | <Title>
11. **Post-ingest validation**: check for broken [[wikilinks]] and verify all new pages are in index.md

After completing all writes, summarize: what was added, which pages were created or updated, any contradictions found, and validation results.
