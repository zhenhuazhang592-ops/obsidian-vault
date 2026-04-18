/**
 * Stage 2: 核心观点提炼
 *
 * 流程：
 * 1. 基于选定标题，调用 LLM 提炼核心观点
 * 2. 保存 JSON 到输出目录
 * 3. 返回 StageOutput（status: waiting_user）
 */

import * as fs from 'fs';
import * as path from 'path';
import { z } from 'zod';
import { logger } from '../logger';
import { PromptEngine } from '../prompts/shared';
import {
  STAGE2_PROMPT,
  STAGE2_MODEL,
  STAGE2_TEMPERATURE,
} from '../prompts/stage2-thesis';
import { StageOutput, Stage2Thesis, ThesisPoint } from '../types';
import { parseJsonResponse } from './utils';

// ==================== Schema ====================

const ThesisPointSchema = z.object({
  point: z.string(),
  commonMisconception: z.string(),
  thinkersToCite: z.array(z.string()),
  logicalConnection: z.string(),
});

const Stage2ResultSchema = z.object({
  coreThesis: z.string(),
  supportingPoints: z.array(ThesisPointSchema),
  reasoning: z.string().optional(),
});

// ==================== Stage 2 ====================

export class Stage2Thesis {
  constructor(private outputDir: string) {}

  async execute(params: {
    title: string;
    subtitle: string;
    targetReader: string;
    painPoint: string;
    researchSummary: string;
    wikiKnowledge?: string;
  }): Promise<StageOutput> {
    logger.stage('Stage 2', '核心观点提炼');

    const { title, subtitle, targetReader, painPoint, researchSummary, wikiKnowledge } = params;

    logger.thinking(`为标题 "${title}" 提炼核心观点...`);

    const rawText = await PromptEngine.callLLM({
      template: STAGE2_PROMPT,
      vars: {
        title,
        subtitle,
        targetReader,
        painPoint,
        researchSummary: researchSummary || '（暂无研究摘要）',
        ...(wikiKnowledge ? { wikiKnowledge } : {}),
      },
      model: STAGE2_MODEL,
      temperature: STAGE2_TEMPERATURE,
      thinking: { type: 'disabled' },
      maxTokens: 8000,
    }) as string;

    const parsed = parseJsonResponse(rawText, Stage2ResultSchema);
    if (!parsed) {
      throw new Error(`Stage 2 LLM 返回无法解析：${rawText.slice(0, 200)}`);
    }

    const output: StageOutput = {
      stage: 'stage2',
      status: 'waiting_user',
      thinking: parsed.reasoning ?? '',
      result: {
        coreThesis: parsed.coreThesis,
        supportingPoints: parsed.supportingPoints,
      },
    };

    await this.saveOutput(output);
    return output;
  }

  async confirm(userModifications?: Partial<Stage2Thesis>): Promise<Stage2Thesis> {
    const output = await this.loadOutput();
    const data = output.result as Partial<Stage2Thesis>;

    const result: Stage2Thesis = {
      coreThesis: userModifications?.coreThesis ?? data.coreThesis ?? '',
      supportingPoints: userModifications?.supportingPoints ?? data.supportingPoints ?? [],
      reasoning: output.thinking ?? '',
      confirmedAt: new Date().toISOString(),
    };

    fs.writeFileSync(
      path.join(this.outputDir, 'stage2-confirmed.json'),
      JSON.stringify(result, null, 2),
      'utf-8'
    );
    logger.success('观点已确认');
    return result;
  }

  private async saveOutput(output: StageOutput): Promise<void> {
    fs.writeFileSync(
      path.join(this.outputDir, 'stage2-thesis.json'),
      JSON.stringify(output, null, 2),
      'utf-8'
    );
  }

  private async loadOutput(): Promise<StageOutput> {
    return JSON.parse(
      fs.readFileSync(path.join(this.outputDir, 'stage2-thesis.json'), 'utf-8')
    );
  }
}
