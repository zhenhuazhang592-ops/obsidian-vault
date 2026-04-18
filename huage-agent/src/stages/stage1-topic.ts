/**
 * Stage 1: 选题与定位
 *
 * 流程：
 * 1. 调用 LLM 生成 3-5 个选题方案（Dan Koe 标题公式）
 * 2. 保存 JSON 到输出目录
 * 3. 返回 StageOutput（status: waiting_user）
 */

import * as fs from 'fs';
import * as path from 'path';
import { z } from 'zod';
import { logger } from '../logger';
import { PromptEngine } from '../prompts/shared';
import {
  STAGE1_PROMPT,
  STAGE1_MODEL,
  STAGE1_TEMPERATURE,
} from '../prompts/stage1-topic';
import {
  StageOutput,
  TopicOption,
  Stage1Topic,
} from '../types';
import { parseJsonResponse } from './utils';

// ==================== Schema ====================

const TopicOptionSchema = z.object({
  title: z.string(),
  subtitle: z.string(),
  targetReader: z.string(),
  painPoint: z.string(),
  uniqueValue: z.string(),
  viralPotential: z.string(),
  titleFormula: z.string(),
});

const Stage1ResultSchema = z.object({
  options: z.array(TopicOptionSchema),
  reasoning: z.string().optional(),
});

// ==================== Stage 1 ====================

export class Stage1Topic {
  constructor(private outputDir: string) {}

  async execute(params: {
    topic: string;
    researchSummary: string;
    wikiKnowledge?: string;
  }): Promise<StageOutput> {
    logger.stage('Stage 1', '选题与定位');

    const { topic, researchSummary, wikiKnowledge } = params;

    logger.thinking(`分析主题 "${topic}"，生成 3-5 个选题方案...`);

    const rawText = await PromptEngine.callLLM({
      template: STAGE1_PROMPT,
      vars: {
        topic,
        researchSummary: researchSummary || '（暂无研究摘要）',
        ...(wikiKnowledge ? { wikiKnowledge } : {}),
      },
      model: STAGE1_MODEL,
      temperature: STAGE1_TEMPERATURE,
      thinking: { type: 'disabled' },
      maxTokens: 8000,
    }) as string;

    const parsed = parseJsonResponse(rawText, Stage1ResultSchema);
    if (!parsed) {
      throw new Error(`Stage 1 LLM 返回无法解析：${rawText.slice(0, 200)}`);
    }

    const output: StageOutput = {
      stage: 'stage1',
      status: 'waiting_user',
      thinking: parsed.reasoning ?? '',
      result: { options: parsed.options },
    };

    await this.saveOutput(output);
    return output;
  }

  async confirm(selectedIndex: number): Promise<Stage1Topic> {
    const output = await this.loadOutput();
    const options = (output.result as { options: TopicOption[] }).options;

    if (selectedIndex < 0 || selectedIndex >= options.length) {
      throw new Error(`选题索引 ${selectedIndex} 超出范围（0-${options.length - 1}）`);
    }

    const selected = options[selectedIndex];
    const result: Stage1Topic = {
      selectedTitle: selected.title,
      subtitle: selected.subtitle,
      targetReader: selected.targetReader,
      painPoint: selected.painPoint,
      uniqueValue: selected.uniqueValue,
      viralPotential: selected.viralPotential,
      options,
      reasoning: output.thinking ?? '',
      decidedAt: new Date().toISOString(),
    };

    fs.writeFileSync(
      path.join(this.outputDir, 'stage1-confirmed.json'),
      JSON.stringify(result, null, 2),
      'utf-8'
    );
    logger.success(`选题已确认: ${selected.title}`);
    return result;
  }

  private async saveOutput(output: StageOutput): Promise<void> {
    fs.writeFileSync(
      path.join(this.outputDir, 'stage1-topic.json'),
      JSON.stringify(output, null, 2),
      'utf-8'
    );
  }

  private async loadOutput(): Promise<StageOutput> {
    return JSON.parse(
      fs.readFileSync(path.join(this.outputDir, 'stage1-topic.json'), 'utf-8')
    );
  }
}

