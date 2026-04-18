/**
 * Stage 3: 文章大纲构建
 *
 * 流程：
 * 1. 基于标题+观点，调用 LLM 构建完整大纲
 * 2. 保存 JSON 到输出目录
 * 3. 返回 StageOutput（status: waiting_user）
 */

import * as fs from 'fs';
import * as path from 'path';
import { z } from 'zod';
import { logger } from '../logger';
import { PromptEngine } from '../prompts/shared';
import {
  STAGE3_PROMPT,
  STAGE3_MODEL,
  STAGE3_TEMPERATURE,
} from '../prompts/stage3-outline';
import { StageOutput, Stage1Topic, Stage2Thesis, Stage3Outline } from '../types';
import { parseJsonResponse, stringifyForTemplate } from './utils';

// ==================== Schema ====================

const OpeningStructureSchema = z.object({
  hook: z.string(),
  transition: z.string(),
  dataSupport: z.string().optional(),
  vulnerability: z.string(),
  promise: z.string(),
  importance: z.string(),
  expectation: z.string(),
});

const OutlineSectionSchema = z.object({
  heading: z.string(),
  keyPoints: z.array(z.string()),
  examples: z.array(z.string()),
  framework: z.string().optional(),
});

const ConclusionStructureSchema = z.object({
  summary: z.string(),
  callToAction: z.string(),
});

const Stage3ResultSchema = z.object({
  opening: OpeningStructureSchema,
  sections: z.array(OutlineSectionSchema),
  conclusion: ConclusionStructureSchema,
  reasoning: z.string().optional(),
});

// ==================== Stage 3 ====================

export class Stage3Outline {
  constructor(private outputDir: string) {}

  async execute(params: {
    topic: Stage1Topic;
    thesis: Stage2Thesis;
    wikiKnowledge?: string;
  }): Promise<StageOutput> {
    logger.stage('Stage 3', '大纲构建');

    const { topic, thesis, wikiKnowledge } = params;

    logger.thinking(`基于标题和观点构建大纲：${topic.selectedTitle}...`);

    const supportingPointsStr = thesis.supportingPoints
      .map(
        (p, i) =>
          `[观点${i + 1}] ${p.point}\n  误解：${p.commonMisconception}\n  引用：${p.thinkersToCite.join(', ')}\n  连接：${p.logicalConnection}`
      )
      .join('\n\n');

    const rawText = await PromptEngine.callLLM({
      template: STAGE3_PROMPT,
      vars: {
        title: topic.selectedTitle,
        subtitle: topic.subtitle,
        coreThesis: thesis.coreThesis,
        supportingPoints: supportingPointsStr,
        ...(wikiKnowledge ? { wikiKnowledge } : {}),
      },
      model: STAGE3_MODEL,
      temperature: STAGE3_TEMPERATURE,
      thinking: { type: 'disabled' },
      maxTokens: 8000,
    }) as string;

    const parsed = parseJsonResponse(rawText, Stage3ResultSchema);
    if (!parsed) {
      throw new Error(`Stage 3 LLM 返回无法解析：${rawText.slice(0, 200)}`);
    }

    const output: StageOutput = {
      stage: 'stage3',
      status: 'waiting_user',
      thinking: parsed.reasoning ?? '',
      result: {
        title: topic.selectedTitle,
        opening: parsed.opening,
        sections: parsed.sections,
        conclusion: parsed.conclusion,
      },
    };

    await this.saveOutput(output);
    return output;
  }

  async confirm(userModifications?: Partial<Stage3Outline>): Promise<Stage3Outline> {
    const output = await this.loadOutput();
    const data = output.result as Partial<Stage3Outline>;

    const result: Stage3Outline = {
      title: userModifications?.title ?? data.title ?? '',
      opening: userModifications?.opening ?? (data as Stage3Outline).opening,
      sections: userModifications?.sections ?? (data as Stage3Outline).sections,
      conclusion: userModifications?.conclusion ?? (data as Stage3Outline).conclusion,
      reasoning: output.thinking ?? '',
      confirmedAt: new Date().toISOString(),
    };

    fs.writeFileSync(
      path.join(this.outputDir, 'stage3-confirmed.json'),
      JSON.stringify(result, null, 2),
      'utf-8'
    );
    logger.success('大纲已确认');
    return result;
  }

  private async saveOutput(output: StageOutput): Promise<void> {
    fs.writeFileSync(
      path.join(this.outputDir, 'stage3-outline.json'),
      JSON.stringify(output, null, 2),
      'utf-8'
    );
  }

  private async loadOutput(): Promise<StageOutput> {
    return JSON.parse(
      fs.readFileSync(path.join(this.outputDir, 'stage3-outline.json'), 'utf-8')
    );
  }
}
