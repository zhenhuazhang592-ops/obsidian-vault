/**
 * wiki 查询（CJK-aware）
 * 参考：llm-wiki-agent tools/query.py
 */

import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';
import { WikiPage, WikiQueryResult } from '../types';

const CJK_PATTERN = /[\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]/;

export function tokenizeCJK(text: string): string[] {
  const parts = text.split(/\s+/);
  const tokens: string[] = [];
  for (const part of parts) {
    if (CJK_PATTERN.test(part)) {
      for (const char of part) {
        if (CJK_PATTERN.test(char)) tokens.push(char);
      }
    } else {
      tokens.push(part.toLowerCase());
    }
  }
  return tokens.filter((t) => CJK_PATTERN.test(t) || t.length > 1);
}

export class WikiQuery {
  async search(keyword: string): Promise<WikiQueryResult> {
    const wikiPath = config.wikiPath;
    const pages = await this.searchPages(wikiPath, keyword);
    pages.sort((a, b) => this.relevanceScore(b, keyword) - this.relevanceScore(a, keyword));
    return { pages: pages.slice(0, 10), query: keyword, matchedAt: new Date().toISOString() };
  }

  private async searchPages(wikiPath: string, keyword: string): Promise<WikiPage[]> {
    const pages: WikiPage[] = [];
    const queryTokens = tokenizeCJK(keyword);
    this.walkDir(wikiPath, (filePath) => {
      const content = fs.readFileSync(filePath, 'utf-8');
      const title = path.basename(filePath, '.md');
      const bodyTokens = tokenizeCJK(content);
      const intersection = queryTokens.filter((qt) =>
        bodyTokens.some((bt) => bt.includes(qt) || qt.includes(bt))
      );
      if (intersection.length > 0) {
        pages.push({
          title,
          type: this.extractType(content),
          content: this.extractRelevantSnippet(content, queryTokens),
          tags: this.extractTags(content),
          sources: this.extractSources(content),
          lastUpdated: this.extractDate(content),
        });
      }
    });
    return pages;
  }

  private relevanceScore(page: WikiPage, keyword: string): number {
    const titleLower = page.title.toLowerCase();
    const keywordLower = keyword.toLowerCase();
    let score = 0;
    if (titleLower.includes(keywordLower)) score += 10;
    if (page.content.toLowerCase().includes(keywordLower)) score += 5;
    score += page.content.length / 1000;
    return score;
  }

  private extractRelevantSnippet(content: string, tokens: string[]): string {
    const lines = content.split('\n');
    for (const line of lines) {
      const lineTokens = tokenizeCJK(line);
      if (lineTokens.some((lt) => tokens.some((qt) => lt.includes(qt) || qt.includes(lt)))) {
        return line.slice(0, 200);
      }
    }
    return content.slice(0, 200);
  }

  private walkDir(dir: string, callback: (filePath: string) => void): void {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) this.walkDir(full, callback);
      else if (entry.name.endsWith('.md')) callback(full);
    }
  }

  private extractType(content: string): WikiPage['type'] {
    const match = content.match(/^type:\s*(\w+)/m);
    return (match?.[1] as WikiPage['type']) || 'source';
  }

  private extractTags(content: string): string[] {
    const match = content.match(/tags:\s*\[([^\]]+)\]/);
    if (!match) return [];
    return match[1].split(',').map((t) => t.trim().replace(/['"]/g, ''));
  }

  private extractSources(content: string): string[] {
    const match = content.match(/sources:\s*\[([^\]]+)\]/);
    if (!match) return [];
    return match[1].split(',').map((s) => s.trim().replace(/['"]/g, ''));
  }

  private extractDate(content: string): string {
    const match = content.match(/^date:\s*(\S+)/m);
    return match?.[1] || new Date().toISOString().split('T')[0];
  }
}
