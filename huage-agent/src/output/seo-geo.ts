import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';
import { logger } from '../logger';
import { SEOResult, GEOResult } from '../types';

export class SEOGEOptimizer {
  constructor(private outputDir: string) {}

  async optimizeSEO(content: string): Promise<SEOResult> {
    logger.info('开始 SEO 优化...');

    const keywords = this.extractKeywords(content);
    const density = this.calculateDensity(content, keywords);
    const metaDescription = this.generateMetaDescription(content);

    return {
      keywords,
      densityCheck: density >= 0.5 && density <= 3,
      metaDescription,
    };
  }

  async optimizeGEO(content: string): Promise<GEOResult> {
    logger.info('开始 GEO 优化...');

    const citations = this.extractCitations(content);
    const entities = this.extractEntities(content);
    const aiScore = await this.calculateAIReadableScore(content);

    return {
      citations,
      entityOptimization: entities,
      aiReadableScore: aiScore,
    };
  }

  private extractKeywords(content: string): string[] {
    // Extract CJK n-grams (2-4 chars) from CJK sequences
    const freq: Record<string, number> = {};
    const cjkSequences = content.match(/[\u4e00-\u9fa5]+/g) || [];
    for (const seq of cjkSequences) {
      for (let len = 2; len <= 4 && len <= seq.length; len++) {
        for (let i = 0; i <= seq.length - len; i++) {
          const gram = seq.slice(i, i + len);
          freq[gram] = (freq[gram] || 0) + 1;
        }
      }
    }
    // Also extract English words
    const english = content.toLowerCase().match(/[a-z]{3,}/g) || [];
    english.forEach((w) => { freq[w] = (freq[w] || 0) + 1; });

    return Object.entries(freq)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([word]) => word);
  }

  private calculateDensity(content: string, keywords: string[]): number {
    if (!keywords.length) return 0;
    const totalWords = content.length;
    const keywordCount = keywords.reduce(
      (sum, k) => sum + (content.toLowerCase().match(new RegExp(k, 'g'))?.length || 0),
      0
    );
    return (keywordCount / totalWords) * 100;
  }

  private generateMetaDescription(content: string): string {
    const plain = content.replace(/[#*>\[\]]/g, '').trim();
    return plain.slice(0, 160) + (plain.length > 160 ? '...' : '');
  }

  private extractCitations(content: string): string[] {
    const citations: string[] = [];
    const regex = />\s*[""]([^""]+)[""]\s*—/g;
    let match;
    while ((match = regex.exec(content)) !== null) {
      citations.push(match[1]);
    }
    return citations;
  }

  private extractEntities(content: string): string[] {
    // TODO: 接入 wiki/ingest.ts 的实体识别（当前返回空，待 Task 10 CLI 集成后接入）
    return [];
  }

  private async calculateAIReadableScore(content: string): Promise<number> {
    // TODO: 调用 LLM 评估 AI 可读性
    return 80;
  }

  async saveResults(seo: SEOResult, geo: GEOResult): Promise<void> {
    fs.writeFileSync(
      path.join(this.outputDir, 'seo-geo-optimization.json'),
      JSON.stringify({ seo, geo }, null, 2),
      'utf-8'
    );
  }
}
