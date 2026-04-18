import { tokenizeCJK } from '../src/wiki/query';
import { WikiLint } from '../src/wiki/lint';
import * as fs from 'fs';
import * as path from 'path';

describe('tokenizeCJK', () => {
  it('should tokenize CJK characters', () => {
    const tokens = tokenizeCJK('时间管理');
    expect(tokens).toContain('时');
    expect(tokens).toContain('间');
    expect(tokens).toContain('管');
    expect(tokens).toContain('理');
  });

  it('should handle mixed CJK and English', () => {
    const tokens = tokenizeCJK('AI 人工智能 agent');
    expect(tokens).toContain('人');
    expect(tokens).toContain('工');
    expect(tokens).toContain('智');
    expect(tokens).toContain('能');
    expect(tokens).toContain('ai');
  });
});

describe('WikiLint', () => {
  const testDir = '/tmp/huage-agent-wiki-lint-test';

  beforeAll(() => {
    fs.mkdirSync(path.join(testDir, 'sources'), { recursive: true });
    fs.writeFileSync(
      path.join(testDir, 'sources/test-source.md'),
      '---\ntitle: "Test"\ntype: source\ndate: 2026-01-01\ntags: []\n---\n\nTest content with [[NonExistentPage]] link.',
      'utf-8'
    );
  });

  afterAll(() => {
    fs.rmSync(testDir, { recursive: true });
  });

  it('should detect broken wikilinks', async () => {
    const lint = new WikiLint(testDir);
    const result = await lint.lint();
    const brokenLinks = result.issues.filter((i) => i.type === 'broken');
    expect(brokenLinks.length).toBeGreaterThan(0);
    expect(brokenLinks[0].detail).toContain('NonExistentPage');
  });

  it('should pass with no broken links', async () => {
    const cleanDir = '/tmp/huage-agent-wiki-lint-clean';
    fs.mkdirSync(cleanDir, { recursive: true });
    fs.writeFileSync(
      path.join(cleanDir, 'index.md'),
      '---\ntitle: "Index"\ntype: source\ndate: 2026-04-19\ntags: []\n---\n\n# Index\n\nWelcome to the wiki.',
      'utf-8'
    );
    const lint = new WikiLint(cleanDir);
    const result = await lint.lint();
    const brokenLinks = result.issues.filter((i) => i.type === 'broken');
    expect(brokenLinks.length).toBe(0);
    fs.rmSync(cleanDir, { recursive: true });
  });
});
