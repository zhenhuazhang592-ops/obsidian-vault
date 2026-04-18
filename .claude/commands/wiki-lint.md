Lint the wiki for health issues.

Usage: /wiki-lint

Check for:

1. **Orphan pages** — wiki pages with no inbound [[links]] from other pages
2. **Broken links** — [[WikiLinks]] pointing to pages that don't exist
3. **Missing entity pages** — entities mentioned in 3+ pages but lacking their own page
4. **Stale content** — pages containing "待填充" or not updated after newer sources
5. **Contradictions** — claims that conflict across pages
6. **Data gaps** — questions the wiki can't answer; suggest new sources

Use Grep and Read tools to analyze. Output a markdown lint report and ask if the user wants it saved to wiki/lint-report.md.
