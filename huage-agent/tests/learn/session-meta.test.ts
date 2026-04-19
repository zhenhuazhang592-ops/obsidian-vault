import { SessionMetaBuilder } from '../../src/learn/session-meta';
import * as fs from 'fs';
import * as path from 'path';

describe('SessionMetaBuilder', () => {
  const testDir = '/tmp/huage-learn-session-test';

  beforeAll(() => {
    fs.mkdirSync(testDir, { recursive: true });
    fs.writeFileSync(
      path.join(testDir, 'stage1-confirmed.json'),
      JSON.stringify({
        selectedTitle: '测试文章标题',
        subtitle: '副标题',
        targetReader: '职场人',
        painPoint: '时间管理',
        options: [{ title: '方案A' }, { title: '方案B' }],
      }),
      'utf-8'
    );
    fs.writeFileSync(
      path.join(testDir, 'stage2-confirmed.json'),
      JSON.stringify({
        coreThesis: '核心观点',
        supportingPoints: [
          { point: '观点1', type: 'insight' },
          { point: '观点2', type: 'story' },
        ],
      }),
      'utf-8'
    );
    fs.writeFileSync(
      path.join(testDir, 'stage3-confirmed.json'),
      JSON.stringify({
        title: '大纲标题',
        opening: { hook: '用问题开场' },
        sections: [
          { heading: '第一部分', function: '建立共鸣' },
          { heading: '第二部分', function: '提出方案' },
        ],
        conclusion: {},
      }),
      'utf-8'
    );
    fs.writeFileSync(
      path.join(testDir, 'stage5-confirmed.json'),
      JSON.stringify({
        title: '润色标题',
        wordCount: 3200,
        antiAiCheck: { passed: false, violations: ['空洞词A', '空洞词B'] },
        seoOptimization: { keywords: ['关键词A', '关键词B'] },
        geoOptimization: { aiReadableScore: 82 },
      }),
      'utf-8'
    );
    fs.writeFileSync(
      path.join(testDir, 'stage4-writing.json'),
      JSON.stringify({ result: { wordCount: 3100 } }),
      'utf-8'
    );
  });

  afterAll(() => {
    fs.rmSync(testDir, { recursive: true });
  });

  it('should build session-meta.json from stage files', async () => {
    const builder = new SessionMetaBuilder(testDir);
    await builder.build();
    const meta = builder.getMeta();

    expect(meta.topic).toBe('测试文章标题');
    expect(meta.stages.topic?.selected).toBe('测试文章标题');
    expect(meta.stages.topic?.targetReader).toBe('职场人');
    expect(meta.stages.topic?.painPoint).toBe('时间管理');
    expect(meta.stages.polish?.violations).toEqual(['空洞词A', '空洞词B']);
    expect(meta.stages.polish?.seoKeywords).toEqual(['关键词A', '关键词B']);
    expect(meta.stages.polish?.geoScore).toBe(82);
    expect(meta.stages.writing?.wordCount).toBe(3200); // stage5-confirmed wins (max with stage4)
    expect(meta.stages.outline?.hooks).toContain('用问题开场');
    expect(meta.stages.outline?.sections[0].function).toBe('建立共鸣');
  });

  it('should handle missing stage files gracefully', async () => {
    const emptyDir = '/tmp/huage-learn-empty';
    fs.mkdirSync(emptyDir, { recursive: true });
    const builder = new SessionMetaBuilder(emptyDir);
    await builder.build();
    const meta = builder.getMeta();
    expect(meta.topic).toBe('');
    expect(meta.stages.topic).toBeNull();
    fs.rmSync(emptyDir, { recursive: true });
  });

  it('should save session-meta.json to outputDir', async () => {
    const builder = new SessionMetaBuilder(testDir);
    await builder.build();
    await builder.save();
    const saved = fs.readFileSync(path.join(testDir, 'session-meta.json'), 'utf-8');
    const parsed = JSON.parse(saved);
    expect(parsed.topic).toBe('测试文章标题');
  });
});
