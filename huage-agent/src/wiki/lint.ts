import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';

export interface LintResult {
  passed: boolean;
  issues: LintIssue[];
}

export interface LintIssue {
  type: 'orphan' | 'broken' | 'contradiction' | 'stale' | 'missing-entity';
  file: string;
  detail: string;
  severity: 'error' | 'warning';
}

export class WikiLint {
  private wikiDir: string;

  constructor(wikiDir?: string) {
    this.wikiDir = wikiDir ?? config.wikiPath();
  }

  async lint(): Promise<LintResult> {
    const issues: LintIssue[] = [];
    const orphans = await this.findOrphans(this.wikiDir);
    for (const [page, links] of orphans) {
      issues.push({ type: 'orphan', file: page, detail: `页面被 ${links} 个其他页面引用，但自身没有引用任何页面`, severity: 'warning' });
    }
    const broken = await this.findBrokenLinks(this.wikiDir);
    for (const { source, target } of broken) {
      issues.push({ type: 'broken', file: source, detail: `wikilink [[${target}]] 指向不存在的页面`, severity: 'error' });
    }
    const stale = await this.findStalePages(this.wikiDir);
    for (const { page, days } of stale) {
      issues.push({ type: 'stale', file: page, detail: `页面超过 ${days} 天未更新`, severity: 'warning' });
    }
    const pending = await this.findPendingPlaceholders(this.wikiDir);
    for (const { page, field } of pending) {
      issues.push({ type: 'stale', file: page, detail: `字段 "${field}" 仍为"待填充"占位符`, severity: 'warning' });
    }
    return { passed: issues.filter((i) => i.severity === 'error').length === 0, issues };
  }

  private async findOrphans(wikiDir: string): Promise<[string, number][]> {
    const orphans: [string, number][] = [];
    const incoming: Map<string, Set<string>> = new Map();
    for (const file of this.listMdFiles(wikiDir)) {
      const content = fs.readFileSync(file, 'utf-8');
      const links = content.match(/\[\[([^\]|]+)\]\]/g) || [];
      for (const link of links) {
        const target = link.slice(2, -2).split('/').pop() || '';
        if (!incoming.has(target)) incoming.set(target, new Set());
        incoming.get(target)!.add(path.basename(file, '.md'));
      }
    }
    for (const file of this.listMdFiles(wikiDir)) {
      const pageName = path.basename(file, '.md');
      const content = fs.readFileSync(file, 'utf-8');
      const hasLinks = /\[\[[^\]]+\]\]/.test(content);
      const hasIncoming = (incoming.get(pageName)?.size ?? 0) > 0;
      if (!hasLinks && hasIncoming && pageName !== 'index') orphans.push([pageName, incoming.get(pageName)!.size]);
    }
    return orphans;
  }

  private async findBrokenLinks(wikiDir: string): Promise<{ source: string; target: string }[]> {
    const broken: { source: string; target: string }[] = [];
    const existingPages = new Set(this.listMdFiles(wikiDir).map((f) => path.basename(f, '.md')));
    for (const file of this.listMdFiles(wikiDir)) {
      const content = fs.readFileSync(file, 'utf-8');
      const links = content.match(/\[\[([^\]|]+)\]\]/g) || [];
      for (const link of links) {
        const target = link.slice(2, -2).split('/').pop() || '';
        if (!existingPages.has(target)) broken.push({ source: path.basename(file, '.md'), target });
      }
    }
    return broken;
  }

  private async findStalePages(wikiDir: string): Promise<{ page: string; days: number }[]> {
    const stale: { page: string; days: number }[] = [];
    const now = Date.now();
    const THIRTY_DAYS = 30 * 24 * 60 * 60 * 1000;
    for (const file of this.listMdFiles(wikiDir)) {
      const content = fs.readFileSync(file, 'utf-8');
      const dateMatch = content.match(/^date:\s*(\S+)/m);
      const lastUpdated = dateMatch?.[1];
      if (lastUpdated) {
        const parts = lastUpdated.split('-').map(Number);
        const updatedAt = new Date(parts[0], parts[1] - 1, parts[2]).getTime();
        const days = Math.floor((now - updatedAt) / (24 * 60 * 60 * 1000));
        if (days > 30) stale.push({ page: path.basename(file, '.md'), days });
      }
    }
    return stale;
  }

  private async findPendingPlaceholders(wikiDir: string): Promise<{ page: string; field: string }[]> {
    const pending: { page: string; field: string }[] = [];
    for (const file of this.listMdFiles(wikiDir)) {
      const content = fs.readFileSync(file, 'utf-8');
      if (content.includes('待填充')) pending.push({ page: path.basename(file, '.md'), field: '待填充' });
    }
    return pending;
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
}
