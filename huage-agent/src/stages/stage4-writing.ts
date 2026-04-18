/**
 * Stage 4: 正文写作
 *
 * 流程：
 * 1. 基于大纲，调用 Qwen3-Max 撰写正文
 * 2. 保存 .md 文件到输出目录
 * 3. 返回 StageOutput（status: waiting_user）
 *
 * 模型：Qwen3-Max（中文写作质量高）
 */

import * as fs from 'fs';
import * as path from 'path';
import { logger } from '../logger';
import { PromptEngine } from '../prompts/shared';
import {
  STAGE4_PROMPT,
  STAGE4_MODEL,
  STAGE4_TEMPERATURE,
  STAGE4_MAX_TOKENS,
} from '../prompts/stage4-writing';
import { StageOutput, Stage3Outline } from '../types';

export class Stage4Writing {
  constructor(private outputDir: string) {}

  async execute(params: {
    outline: Stage3Outline;
    wordCountTarget?: number;
    wikiKnowledge?: string;
  }): Promise<StageOutput> {
    logger.stage('Stage 4', '正文写作（Qwen3-Max）');

    const { outline, wordCountTarget = 2500, wikiKnowledge } = params;

    logger.thinking(`撰写正文：${outline.title}，目标 ${wordCountTarget} 字...`);

    // Build vars matching STAGE4_PROMPT variable names (dot notation supported by template engine)
    const vars: Record<string, unknown> = {
      title: outline.title,
      wordCountTarget: String(wordCountTarget),
      // Opening fields — template uses {{opening.hook}}, {{opening.dataSupport}}, etc.
      'opening.hook': outline.opening.hook,
      'opening.transition': outline.opening.transition,
      'opening.dataSupport': outline.opening.dataSupport ?? '',
      'opening.vulnerability': outline.opening.vulnerability,
      'opening.promise': outline.opening.promise,
      'opening.importance': outline.opening.importance,
      'opening.expectation': outline.opening.expectation,
      // Sections — template uses {{#each sections}}...{{heading}}...{{keyPoints}}...{{/each}}
      sections: outline.sections.map(s => ({
        heading: s.heading,
        keyPoints: s.keyPoints.join('\n'),   // array → newline-separated for readability
        examples: s.examples.join(', '),     // array → comma-separated string
        framework: s.framework ?? '',
      })),
      // Conclusion — template uses {{conclusion.summary}}, {{conclusion.callToAction}}
      'conclusion.summary': outline.conclusion.summary,
      'conclusion.callToAction': outline.conclusion.callToAction,
    };
    if (wikiKnowledge) vars['wikiKnowledge'] = wikiKnowledge;

    const rawText = await PromptEngine.callLLM({
      template: STAGE4_PROMPT,
      vars: vars as Record<string, string>,
      model: STAGE4_MODEL,
      temperature: STAGE4_TEMPERATURE,
      thinking: { type: 'disabled' },
      maxTokens: STAGE4_MAX_TOKENS,
    }) as string;

    if (!rawText || rawText.trim().length === 0) {
      throw new Error('Stage 4 返回为空');
    }

    // Save as markdown file
    const draftPath = path.join(this.outputDir, 'stage4-draft.md');
    fs.writeFileSync(draftPath, rawText, 'utf-8');
    logger.success(`正文已保存：${draftPath}`);

    const wordCount = rawText.replace(/[#*>\[\]`\s]/g, '').length;

    const output: StageOutput = {
      stage: 'stage4',
      status: 'waiting_user',
      thinking: `使用 Qwen3-Max 撰写 ${wordCount} 字正文`,
      result: {
        title: outline.title,
        content: rawText,
        wordCount,
        filePath: draftPath,
      },
    };

    await this.saveOutput(output);
    return output;
  }

  async confirm(): Promise<void> {
    logger.success('正文已确认，进入润色阶段');
  }

  private async saveOutput(output: StageOutput): Promise<void> {
    fs.writeFileSync(
      path.join(this.outputDir, 'stage4-writing.json'),
      JSON.stringify(output, null, 2),
      'utf-8'
    );
  }
}
