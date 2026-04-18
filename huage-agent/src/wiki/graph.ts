import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';

export interface GraphNode {
  id: string;
  title: string;
  type: 'source' | 'entity' | 'concept' | 'synthesis';
  tags: string[];
  connections: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship?: string;
}

export interface WikiGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  generatedAt: string;
}

export class WikiGraphBuilder {
  private checkpointFile: string;

  constructor() {
    const wikiDir = config.wikiPath;
    this.checkpointFile = path.join(wikiDir, 'graph.jsonl');
  }

  async build(): Promise<WikiGraph> {
    const wikiDir = config.wikiPath;
    const { nodes, edges } = await this.pass1(wikiDir);
    const graph: WikiGraph = { nodes, edges, generatedAt: new Date().toISOString() };
    fs.appendFileSync(this.checkpointFile, JSON.stringify({ ts: new Date().toISOString(), graph }) + '\n', 'utf-8');
    return graph;
  }

  private async pass1(wikiDir: string): Promise<{ nodes: GraphNode[]; edges: GraphEdge[] }> {
    const nodes: GraphNode[] = [];
    const edges: GraphEdge[] = [];
    const allLinks: Map<string, Set<string>> = new Map();
    for (const file of this.listMdFiles(wikiDir)) {
      const content = fs.readFileSync(file, 'utf-8');
      const title = path.basename(file, '.md');
      const type = (this.extractFrontmatter(content, 'type') as GraphNode['type']) || 'source';
      const tags = this.extractTags(content);
      const links = content.match(/\[\[([^\]|]+)\]\]/g) || [];
      const targets = links.map((l) => l.slice(2, -2).split('/').pop() || '');
      nodes.push({ id: title, title, type, tags, connections: targets.length });
      allLinks.set(title, new Set(targets));
      for (const target of targets) edges.push({ source: title, target });
    }
    for (const node of nodes) {
      const incoming = edges.filter((e) => e.target === node.id).length;
      node.connections += incoming;
    }
    return { nodes, edges };
  }

  private listMdFiles(dir: string): string[] {
    const files: string[] = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory() && !entry.name.startsWith('.')) files.push(...this.listMdFiles(full));
      else if (entry.name.endsWith('.md')) files.push(full);
    }
    return files;
  }

  private extractFrontmatter(content: string, key: string): string | null {
    const match = content.match(new RegExp(`^${key}:\\s*(.+)$`, 'm'));
    return match?.[1]?.trim() || null;
  }

  private extractTags(content: string): string[] {
    const match = content.match(/tags:\s*\[([^\]]+)\]/);
    if (!match) return [];
    return match[1].split(',').map((t) => t.trim().replace(/['"]/g, ''));
  }

  async loadLatest(): Promise<WikiGraph | null> {
    if (!fs.existsSync(this.checkpointFile)) return null;
    const lines = fs.readFileSync(this.checkpointFile, 'utf-8').trim().split('\n');
    if (!lines.length) return null;
    const last = JSON.parse(lines[lines.length - 1]);
    return last.graph;
  }
}
