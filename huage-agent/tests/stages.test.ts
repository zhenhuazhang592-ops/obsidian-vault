/**
 * 五阶段执行器测试
 */

import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

// ==================== Template Render Tests ====================
// vi.mock hoisted to top; use vi.importActual to get the real render()
describe('Template Engine', () => {
  async function getPE() {
    const mod = await vi.importActual<typeof import('../src/prompts/shared')>(
      '../src/prompts/shared'
    );
    return mod.PromptEngine;
  }

  it('renders simple variables', async () => {
    const { render } = await getPE();
    expect(render('Hello {{name}}', { name: 'World' })).toBe('Hello World');
  });

  it('replaces multiple variables', async () => {
    const { render } = await getPE();
    expect(render('{{greeting}} {{name}}!', { greeting: 'Hi', name: 'Claude' })).toBe('Hi Claude!');
  });

  it('unresolved variable throws error (strict mode)', async () => {
    const { render } = await getPE();
    expect(() => render('Hello {{name}}', {})).toThrow('Unresolved prompt variables');
  });

  it('{{#if}} block renders when truthy', async () => {
    const { render } = await getPE();
    expect(render('S {{#if flag}}M{{/if}} E', { flag: 'yes' })).toBe('S M E');
  });

  it('{{#if}} block skipped when empty string', async () => {
    const { render } = await getPE();
    expect(render('S {{#if flag}}M{{/if}} E', { flag: '' })).toBe('S  E');
  });

  it('{{#each}} block iterates over array', async () => {
    const { render } = await getPE();
    const result = render('{{#each items}}{{name}}{{/each}}', {
      items: [{ name: 'A' }, { name: 'B' }],
    });
    expect(result).toBe('AB');
  });

  it('dot notation variable: {{opening.hook}}', async () => {
    const { render } = await getPE();
    expect(render('Hook: {{opening.hook}}', { 'opening.hook': '反直觉' })).toBe('Hook: 反直觉');
  });

  it('{{#each}} with object items resolves {{heading}} correctly', async () => {
    const { render } = await getPE();
    const result = render('{{#each sections}}{{heading}}|{{/each}}', {
      sections: [{ heading: 'S1' }, { heading: 'S2' }],
    });
    expect(result).toBe('S1|S2|');
  });

  it('{{#if}} with dot notation: truthy renders block', async () => {
    const { render } = await getPE();
    expect(render('A{{#if data.x}}B{{/if}}C', { 'data.x': 'yes' })).toBe('ABC');
  });

  it('{{#if}} with dot notation: empty string skips block', async () => {
    const { render } = await getPE();
    expect(render('A{{#if data.x}}B{{/if}}C', { 'data.x': '' })).toBe('AC');
  });
});

// ==================== Stage Tests (mock callLLM) ====================

vi.mock('../src/prompts/shared', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../src/prompts/shared')>();
  return {
    ...actual,
    PromptEngine: {
      ...actual.PromptEngine,
      callLLM: vi.fn(),
    },
  };
});

// ==================== Stage 1 Tests ====================

describe('Stage1Topic', () => {
  const testDir = '/tmp/huage-agent-stage1-test';

  beforeAll(() => fs.mkdirSync(testDir, { recursive: true }));
  afterAll(() => fs.rmSync(testDir, { recursive: true }));

  it('execute generates topic options and saves output', async () => {
    const { PromptEngine } = await import('../src/prompts/shared');
    (PromptEngine.callLLM as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      JSON.stringify({
        options: [
          {
            title: 'How to master time management in 30 days',
            subtitle: 'The uncomfortable truth',
            targetReader: '忙碌的职场人',
            painPoint: '时间不够用',
            uniqueValue: '实用系统而非空洞技巧',
            viralPotential: '高',
            titleFormula: 'How to',
          },
        ],
        reasoning: '基于 Dan Koe 标题公式生成',
      })
    );

    const { Stage1Topic } = await import('../src/stages/stage1-topic');
    const stage = new Stage1Topic(testDir);
    const output = await stage.execute({
      topic: '时间管理',
      researchSummary: '已有大量时间管理文章',
    });

    expect(output.status).toBe('waiting_user');
    expect(output.result).toHaveProperty('options');
    expect((output.result as any).options.length).toBeGreaterThan(0);

    const filePath = path.join(testDir, 'stage1-topic.json');
    expect(fs.existsSync(filePath)).toBe(true);
  });

  it('confirm throws on out-of-range index', async () => {
    fs.writeFileSync(
      path.join(testDir, 'stage1-topic.json'),
      JSON.stringify({
        stage: 'stage1',
        status: 'waiting_user',
        thinking: '',
        result: { options: [{ title: 'A' }, { title: 'B' }] },
      })
    );

    const { Stage1Topic } = await import('../src/stages/stage1-topic');
    const stage = new Stage1Topic(testDir);
    await expect(stage.confirm(5)).rejects.toThrow('超出范围');
  });
});

// ==================== Stage 2 Tests ====================

describe('Stage2Thesis', () => {
  const testDir = '/tmp/huage-agent-stage2-test';

  beforeAll(() => fs.mkdirSync(testDir, { recursive: true }));
  afterAll(() => fs.rmSync(testDir, { recursive: true }));

  it('execute generates thesis and saves output', async () => {
    const { PromptEngine } = await import('../src/prompts/shared');
    (PromptEngine.callLLM as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      JSON.stringify({
        coreThesis: '时间管理的本质是精力管理',
        supportingPoints: [
          {
            point: '人们浪费的不是时间，是注意力',
            commonMisconception: '时间是不可再生的',
            thinkersToCite: ['Cal Newport'],
            logicalConnection: '引出深度工作概念',
          },
        ],
        reasoning: '基于 Dan Koe 观点提炼逻辑',
      })
    );

    const { Stage2Thesis } = await import('../src/stages/stage2-thesis');
    const stage = new Stage2Thesis(testDir);
    const output = await stage.execute({
      title: 'How to master time management',
      subtitle: 'The uncomfortable truth',
      targetReader: '忙碌的职场人',
      painPoint: '时间不够用',
      researchSummary: '深度工作相关研究',
    });

    expect(output.status).toBe('waiting_user');
    expect((output.result as any)).toHaveProperty('coreThesis');

    const filePath = path.join(testDir, 'stage2-thesis.json');
    expect(fs.existsSync(filePath)).toBe(true);
  });
});

// ==================== Stage 3 Tests ====================

describe('Stage3Outline', () => {
  const testDir = '/tmp/huage-agent-stage3-test';

  beforeAll(() => fs.mkdirSync(testDir, { recursive: true }));
  afterAll(() => fs.rmSync(testDir, { recursive: true }));

  it('execute builds outline from topic and thesis', async () => {
    const { PromptEngine } = await import('../src/prompts/shared');
    (PromptEngine.callLLM as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      JSON.stringify({
        opening: {
          hook: '反直觉开篇',
          transition: '宽容过渡',
          vulnerability: '脆弱性',
          promise: '承诺',
          importance: '重要性',
          expectation: '期待感',
        },
        sections: [
          { heading: '第一观点', keyPoints: ['要点1'], examples: ['案例1'], framework: '5步' },
        ],
        conclusion: { summary: '总结', callToAction: '行动号召' },
        reasoning: '大纲构建逻辑',
      })
    );

    const { Stage3Outline } = await import('../src/stages/stage3-outline');
    const stage = new Stage3Outline(testDir);
    const output = await stage.execute({
      topic: {
        selectedTitle: '时间管理',
        subtitle: '真相',
        targetReader: '职场人',
        painPoint: '不够用',
        uniqueValue: '系统',
        viralPotential: '高',
        options: [],
        reasoning: '',
        decidedAt: '',
      },
      thesis: {
        coreThesis: '精力管理',
        supportingPoints: [
          {
            point: '注意力是关键',
            commonMisconception: '时间是问题',
            thinkersToCite: [],
            logicalConnection: '',
          },
        ],
        reasoning: '',
        confirmedAt: '',
      },
    });

    expect(output.status).toBe('waiting_user');
    expect(output.result).toHaveProperty('opening');
    expect(output.result).toHaveProperty('sections');
    expect(output.result).toHaveProperty('conclusion');
  });
});

// ==================== Stage 4 Tests ====================

describe('Stage4Writing', () => {
  const testDir = '/tmp/huage-agent-stage4-test';

  beforeAll(() => fs.mkdirSync(testDir, { recursive: true }));
  afterAll(() => fs.rmSync(testDir, { recursive: true }));

  it('writes draft and saves .md file', async () => {
    const { PromptEngine } = await import('../src/prompts/shared');
    (PromptEngine.callLLM as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      '# 时间管理的真相\n\n这是一篇测试文章。'
    );

    const { Stage4Writing } = await import('../src/stages/stage4-writing');
    const stage = new Stage4Writing(testDir);
    const output = await stage.execute({
      outline: {
        title: '时间管理的真相',
        opening: {
          hook: '反直觉',
          transition: '过渡',
          vulnerability: '脆弱',
          promise: '承诺',
          importance: '重要',
          expectation: '期待',
        },
        sections: [
          { heading: '第一部分', keyPoints: ['要点'], examples: ['案例'] },
        ],
        conclusion: { summary: '总结', callToAction: '行动' },
        reasoning: '',
        confirmedAt: '',
      },
      wordCountTarget: 2500,
    });

    expect(output.status).toBe('waiting_user');
    const draftFile = (output.result as any).filePath;
    expect(fs.existsSync(draftFile)).toBe(true);
    expect(fs.readFileSync(draftFile, 'utf-8')).toContain('时间管理的真相');
  });
});

// ==================== FiveStageOrchestrator Tests ====================

describe('FiveStageOrchestrator', () => {
  const testDir = '/tmp/huage-agent-orchestrator-test';

  beforeAll(() => fs.mkdirSync(testDir, { recursive: true }));
  afterAll(() => fs.rmSync(testDir, { recursive: true }));

  it('creates output directory on construction', async () => {
    const { FiveStageOrchestrator } = await import('../src/stages/index');
    const orch = new FiveStageOrchestrator(testDir);
    expect(fs.existsSync(testDir)).toBe(true);
    expect(orch.getOutputDir()).toBe(testDir);
  });

  it('runFull throws on invalid LLM response (not JSON)', async () => {
    const { PromptEngine } = await import('../src/prompts/shared');
    (PromptEngine.callLLM as ReturnType<typeof vi.fn>).mockResolvedValueOnce('not json');

    const { FiveStageOrchestrator } = await import('../src/stages/index');
    const orch = new FiveStageOrchestrator(testDir);

    await expect(
      orch.runFull({ topic: '时间管理' })
    ).rejects.toThrow();
  });
});
