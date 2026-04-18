Build interactive knowledge graph from wiki pages.

Usage: /wiki-graph

Generate a knowledge graph visualization from all [[wikilinks]] in the wiki:

1. **Collect all pages** — Use Glob to find all wiki/**/*.md files
2. **Extract wikilinks** — Use Grep to find all [[link]] patterns
3. **Build node/edge list** — Each page is a node, each wikilink is a directed edge
4. **Write graph/graph.json** — Nodes with id/label/type, edges with source/target
5. **Write graph/graph.html** — Simple vis.js visualization (self-contained)

Node types from frontmatter `type:` field:
- source: green
- entity: blue
- concept: orange
- synthesis: purple

Output the number of nodes and edges, and the path to graph.html.
