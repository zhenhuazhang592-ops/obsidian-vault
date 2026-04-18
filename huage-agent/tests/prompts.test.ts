/**
 * Prompt 模板单元测试
 * 验证 {{VAR}} 替换逻辑和 schema 校验
 */

import { describe, it, expect } from 'vitest';
import { PromptEngine, Stage1InputSchema, Stage2InputSchema, Stage3InputSchema, Stage4InputSchema, Stage5InputSchema, ResearchInputSchema, WikiRefluxInputSchema } from '../src/prompts/shared';
import { STAGE1_PROMPT } from '../src/prompts/stage1-topic';
import { STAGE2_PROMPT } from '../src/prompts/stage2-thesis';
import { STAGE3_PROMPT } from '../src/prompts/stage3-outline';
import { STAGE4_PROMPT } from '../src/prompts/stage4-writing';
import { STAGE5_PROMPT } from '../src/prompts/stage5-polish';
import { RESEARCH_PROMPT } from '../src/prompts/research';
import { WIKI_REFLUX_PROMPT } from '../src/prompts/wiki-reflux';

describe('PromptEngine.render', () => {
  it('替换单个变量', () => {
    const result = PromptEngine.render('Hello {{name}}', { name: 'World' });
    expect(result).toBe('Hello World');
  });

  it('替换多个变量', () => {
    const result = PromptEngine.render('{{greeting}} {{name}}!', {
      greeting: 'Hi',
      name: 'Alice',
    });
    expect(result).toBe('Hi Alice!');
  });

  it('未提供的变量抛出错误', () => {
    expect(() => PromptEngine.render('Hello {{name}}', {})).toThrow(
      'Unresolved prompt variables: {{name}}',
    );
  });

  it('wikiKnowledge 条件替换', () => {
    const template = `Pre {{#if wikiKnowledge}}Wiki: {{wikiKnowledge}}{{/if}} Post`;
    const withWiki = PromptEngine.render(template, { wikiKnowledge: 'test' });
    const withoutWiki = PromptEngine.render(template, { wikiKnowledge: '' });
    expect(withWiki).toContain('Wiki: test');
    expect(withoutWiki).not.toContain('Wiki: test');
  });
});

describe('Stage Schemas', () => {
  it('Stage1InputSchema 验证通过', () => {
    const input = {
      topic: '如何提高写作能力',
      researchSummary: '写作需要刻意练习',
    };
    expect(Stage1InputSchema.parse(input)).toEqual(input);
  });

  it('Stage2InputSchema 验证通过', () => {
    const input = {
      title: '写作的本质',
      subtitle: '不是技巧，是思考',
      targetReader: '想提升写作的人',
      painPoint: '过于关注技巧',
      researchSummary: '刻意练习很重要',
    };
    expect(Stage2InputSchema.parse(input)).toEqual(input);
  });

  it('Stage3InputSchema 验证通过', () => {
    const input = {
      title: '写作的本质',
      subtitle: '不是技巧，是思考',
      coreThesis: '写作是思考的延伸',
      supportingPoints: [
        { point: '观点1', commonMisconception: '误解', thinkersToCite: ['author'] },
      ],
    };
    expect(Stage3InputSchema.parse(input)).toEqual(input);
  });

  it('Stage4InputSchema 验证通过', () => {
    const input = {
      title: '写作的本质',
      outline: {
        opening: { hook: 'start' },
        sections: [{ heading: '章节1', keyPoints: [], examples: [] }],
        conclusion: { summary: 'end' },
      },
      wordCountTarget: 2500,
    };
    expect(Stage4InputSchema.parse(input)).toEqual(input);
  });

  it('Stage5InputSchema 验证通过', () => {
    const input = {
      draft: '文章正文...',
      title: '写作的本质',
      antiAiRules: '禁止空洞词',
      seoKeywords: ['写作', '技巧'],
    };
    expect(Stage5InputSchema.parse(input)).toEqual(input);
  });

  it('ResearchInputSchema 验证通过', () => {
    const input = { topic: '写作方法论' };
    expect(ResearchInputSchema.parse(input)).toEqual(input);
  });

  it('WikiRefluxInputSchema 验证通过', () => {
    const input = {
      title: '写作的本质',
      content: '文章内容',
      sources: [{ title: '来源1', url: 'https://example.com' }],
    };
    expect(WikiRefluxInputSchema.parse(input)).toEqual(input);
  });
});

describe('Prompt Templates', () => {
  it('STAGE1_PROMPT 包含必要变量', () => {
    const vars = {
      topic: '测试主题',
      researchSummary: '测试摘要',
    };
    const rendered = PromptEngine.render(STAGE1_PROMPT, vars);
    expect(rendered).toContain('测试主题');
    expect(rendered).toContain('测试摘要');
  });

  it('STAGE2_PROMPT 包含必要变量', () => {
    const vars = {
      title: '测试标题',
      subtitle: '测试副标题',
      targetReader: '测试读者',
      painPoint: '测试痛点',
      researchSummary: '测试摘要',
    };
    const rendered = PromptEngine.render(STAGE2_PROMPT, vars);
    expect(rendered).toContain('测试标题');
    expect(rendered).toContain('测试副标题');
  });

  it('STAGE3_PROMPT 包含必要变量', () => {
    const vars = {
      title: '测试标题',
      subtitle: '测试副标题',
      coreThesis: '核心论点',
      supportingPoints: '支撑观点',
    };
    const rendered = PromptEngine.render(STAGE3_PROMPT, vars);
    expect(rendered).toContain('测试标题');
    expect(rendered).toContain('核心论点');
  });

  it('STAGE4_PROMPT 包含必要变量', () => {
    // dot notation vars matching STAGE4_PROMPT variable names
    const vars = {
      title: '测试标题',
      'opening.hook': '开篇钩子',
      'opening.transition': '过渡',
      'opening.dataSupport': '',
      'opening.vulnerability': '脆弱',
      'opening.promise': '承诺',
      'opening.importance': '重要',
      'opening.expectation': '期待',
      sections: [
        { heading: '章节一', keyPoints: '要点', examples: '案例', framework: '' },
      ],
      'conclusion.summary': '总结',
      'conclusion.callToAction': '行动号召',
      wordCountTarget: '2500',
    };
    const rendered = PromptEngine.render(STAGE4_PROMPT, vars);
    expect(rendered).toContain('测试标题');
    expect(rendered).toContain('2500');
    expect(rendered).toContain('章节一');
  });

  it('STAGE5_PROMPT 包含必要变量', () => {
    const vars = {
      draft: '草稿内容',
      title: '测试标题',
      antiAiRules: '禁止空洞词',
      seoKeywords: JSON.stringify(['写作', '技巧']),
    };
    const rendered = PromptEngine.render(STAGE5_PROMPT, vars);
    expect(rendered).toContain('草稿内容');
    expect(rendered).toContain('测试标题');
  });

  it('RESEARCH_PROMPT 包含必要变量', () => {
    const vars = {
      topic: '测试主题',
      _researchContent: '搜索结果内容...',
    };
    const rendered = PromptEngine.render(RESEARCH_PROMPT, vars);
    expect(rendered).toContain('测试主题');
    expect(rendered).toContain('搜索结果内容...');
  });

  it('WIKI_REFLUX_PROMPT 包含必要变量', () => {
    const vars = {
      title: '测试标题',
      content: '测试内容',
      sources: '来源信息',
    };
    const rendered = PromptEngine.render(WIKI_REFLUX_PROMPT, vars);
    expect(rendered).toContain('测试标题');
    expect(rendered).toContain('测试内容');
  });
});
