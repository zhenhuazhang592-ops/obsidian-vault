/**
 * LocalEvolve — 本地进化检查
 * 判断 pattern 是否达到进化阈值，或可以聚类进化。
 * 不做实际的 Skill 创建（委派给 vault-bridge）。
 */

import { ExtractedPattern } from './types.js';

export interface EvolveResult {
  highConfidence: ExtractedPattern[];  // confidence >= 0.9
  clusters: ExtractedPattern[][];       // 同 domain >= 2 个，>= 0.7
}

export class LocalEvolve {
  /** confidence >= 0.9 时认为可以单独进化为 Skill */
  shouldEvolve(pattern: ExtractedPattern): boolean {
    return pattern.confidence >= 0.9;
  }

  /**
   * 找可以聚类的本能组：
   * 同一 domain，>= 2 个，>= 0.7 confidence
   */
  findClusters(patterns: ExtractedPattern[]): ExtractedPattern[][] {
    const byDomain = new Map<string, ExtractedPattern[]>();
    for (const p of patterns) {
      if (p.confidence >= 0.7) {
        const group = byDomain.get(p.domain) ?? [];
        group.push(p);
        byDomain.set(p.domain, group);
      }
    }
    return Array.from(byDomain.values()).filter(g => g.length >= 2);
  }

  /** 检查所有进化机会 */
  check(patterns: ExtractedPattern[]): EvolveResult {
    const highConfidence = patterns.filter(p => this.shouldEvolve(p));
    const clusters = this.findClusters(patterns);
    return { highConfidence, clusters };
  }
}
