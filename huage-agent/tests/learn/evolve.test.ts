import { LocalEvolve } from '../../src/learn/evolve';
import { ExtractedPattern } from '../../src/learn/types';

const makePattern = (overrides: Partial<ExtractedPattern> = {}): ExtractedPattern => ({
  type: '钩子公式',
  domain: '文章开头',
  trigger: '当写作开头时',
  behavior: '用问题开场',
  evidence: '你身边有多少人...',
  boundary: '适用于：观点型',
  confidence: 0.6,
  ...overrides,
});

describe('LocalEvolve', () => {
  describe('shouldEvolve', () => {
    it('should return true when confidence >= 0.9', () => {
      const evolve = new LocalEvolve();
      const p = makePattern({ confidence: 0.9 });
      expect(evolve.shouldEvolve(p)).toBe(true);
    });

    it('should return false when confidence < 0.9', () => {
      const evolve = new LocalEvolve();
      const p = makePattern({ confidence: 0.85 });
      expect(evolve.shouldEvolve(p)).toBe(false);
    });

    it('should return false when confidence = 0.6', () => {
      const evolve = new LocalEvolve();
      const p = makePattern({ confidence: 0.6 });
      expect(evolve.shouldEvolve(p)).toBe(false);
    });
  });

  describe('findClusters', () => {
    it('should cluster patterns of same domain with confidence >= 0.7', () => {
      const evolve = new LocalEvolve();
      const patterns = [
        makePattern({ type: '钩子公式', domain: '文章开头', confidence: 0.8 }),
        makePattern({ type: '钩子公式2', domain: '文章开头', confidence: 0.75 }),
        makePattern({ type: '选题', domain: '选题方向', confidence: 0.8 }),
      ];
      const clusters = evolve.findClusters(patterns);
      expect(clusters.length).toBe(1);
      expect(clusters[0][0].domain).toBe('文章开头');
    });

    it('should return empty when no cluster meets threshold', () => {
      const evolve = new LocalEvolve();
      const patterns = [
        makePattern({ domain: '文章开头', confidence: 0.65 }),
        makePattern({ domain: '文章开头', confidence: 0.65 }),
      ];
      const clusters = evolve.findClusters(patterns);
      expect(clusters.length).toBe(0);
    });
  });

  describe('check', () => {
    it('should return high-confidence evolvable patterns', () => {
      const evolve = new LocalEvolve();
      const patterns = [
        makePattern({ confidence: 0.9 }),
        makePattern({ confidence: 0.6 }),
      ];
      const result = evolve.check(patterns);
      expect(result.highConfidence.length).toBe(1);
      expect(result.clusters.length).toBe(0);
    });

    it('should return cluster suggestions', () => {
      const evolve = new LocalEvolve();
      const patterns = [
        makePattern({ domain: '文章开头', confidence: 0.8 }),
        makePattern({ domain: '文章开头', confidence: 0.75 }),
        makePattern({ domain: '文章开头', confidence: 0.7 }),
      ];
      const result = evolve.check(patterns);
      expect(result.clusters.length).toBe(1);
      expect(result.clusters[0].length).toBe(3);
    });

    it('should return empty when no evolvable patterns', () => {
      const evolve = new LocalEvolve();
      const patterns = [makePattern({ confidence: 0.5 })];
      const result = evolve.check(patterns);
      expect(result.highConfidence.length).toBe(0);
      expect(result.clusters.length).toBe(0);
    });
  });
});
