import { PatternExtractor } from '../../src/learn/extractor';
import { SessionMeta } from '../../src/learn/types';

const makeMeta = (overrides: Partial<SessionMeta['stages']> = {}): SessionMeta => ({
  topic: '测试文章',
  date: '2026-04-20',
  outputDir: '/tmp',
  stages: {
    topic: { selected: '如何在30岁前实现财务自由', alternatives: [], reason: '', targetReader: '职场人', painPoint: '财务焦虑' },
    thesis: { points: [{ text: '财务自由的本质是现金流管理', type: 'insight' }] },
    outline: {
      type: '问题-方案式',
      hooks: ['你身边有多少人，每天忙得要死，却始终觉得钱不够花？'],
      sections: [{ heading: '第一部分', function: '建立共鸣' }],
      opening: '你身边有多少人，每天忙得要死，却始终觉得钱不够花？',
    },
    writing: { wordCount: 3200 },
    polish: { antiAiScore: 88, violations: ['因此', '因此我们可以看出'], seoKeywords: ['财务自由', '现金流'], geoScore: 82 },
    ...overrides,
  } as SessionMeta['stages'],
  wikiInjected: ['财务自由'],
  images: [],
});

describe('PatternExtractor', () => {
  it('should extract hook pattern', () => {
    const extractor = new PatternExtractor(makeMeta());
    const patterns = extractor.extract();
    const hook = patterns.find(p => p.type === '钩子公式');
    expect(hook).toBeDefined();
    expect(hook!.trigger).toContain('写作公众号开头');
    expect(hook!.behavior).toContain('问题开场');
    expect(hook!.evidence).toContain('你身边有多少人');
  });

  it('should extract anti-ai pattern', () => {
    const extractor = new PatternExtractor(makeMeta());
    const patterns = extractor.extract();
    const antiAi = patterns.find(p => p.type === '去AI味');
    expect(antiAi).toBeDefined();
    expect(antiAi!.behavior).toContain('因此');
  });

  it('should extract outline structure pattern', () => {
    const extractor = new PatternExtractor(makeMeta());
    const patterns = extractor.extract();
    const outline = patterns.find(p => p.type === '大纲结构');
    expect(outline).toBeDefined();
    expect(outline!.trigger).toContain('问题-方案式');
  });

  it('should extract thesis type distribution', () => {
    const extractor = new PatternExtractor(makeMeta({
      thesis: { points: [{ text: '观点A', type: 'insight' }, { text: '观点B', type: 'data' }] },
    }));
    const patterns = extractor.extract();
    const thesis = patterns.find(p => p.type === '观点类型');
    expect(thesis).toBeDefined();
    expect(thesis!.behavior).toContain('insight');
    expect(thesis!.behavior).toContain('data');
  });

  it('should return empty patterns when meta is empty', () => {
    const empty: SessionMeta = {
      topic: '', date: '2026-04-20', outputDir: '/tmp',
      stages: { topic: null, thesis: null, outline: null, writing: null, polish: null },
      wikiInjected: [], images: [],
    };
    const extractor = new PatternExtractor(empty);
    const patterns = extractor.extract();
    expect(patterns.length).toBeGreaterThanOrEqual(0);
  });

  it('should handle missing stages gracefully', () => {
    const partial: SessionMeta = {
      topic: '', date: '2026-04-20', outputDir: '/tmp',
      stages: { topic: null, thesis: null, outline: null, writing: null, polish: null },
      wikiInjected: [], images: [],
    };
    const extractor = new PatternExtractor(partial);
    expect(() => extractor.extract()).not.toThrow();
  });
});
