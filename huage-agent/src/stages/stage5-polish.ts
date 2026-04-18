/**
 * Stage 5: 优化与润色
 *
 * 流程：
 * 1. 读取 Stage 4 草稿
 * 2. 调用 LLM 去除 AI 味 + SEO/GEO 优化
 * 3. 保存润色结果
 * 4. 返回 StageOutput（status: waiting_user）
 */

import * as fs from 'fs';
import * as path from 'path';
import { z } from 'zod';
import { logger } from '../logger';
import { PromptEngine } from '../prompts/shared';
import {
  STAGE5_PROMPT,
  STAGE5_MODEL,
  STAGE5_TEMPERATURE,
} from '../prompts/stage5-polish';
import { StageOutput, Stage5Polished, AntiAiCheckResult, SEOResult, GEOResult } from '../types';
import { parseJsonResponse } from './utils';

// ==================== Schema ====================

const AntiAiCheckSchema = z.object({
  passed: z.boolean(),
  violations: z.array(z.string()),
});

const SEOOptimizationSchema = z.object({
  keywords: z.array(z.string()),
  densityCheck: z.boolean(),
  metaDescription: z.string(),
});

const Stage5ResultSchema = z.object({
  polishedContent: z.string(),
  antiAiCheck: AntiAiCheckSchema,
  seoOptimization: SEOOptimizationSchema,
  changes: z.array(z.string()).optional(),
});

// ==================== Stage 5 ====================

export class Stage5Polish {
  constructor(private outputDir: string) {}

  async execute(params: {
    title: string;
    draftFilePath: string;
    antiAiRules?: string;
    seoKeywords?: string[];
  }): Promise<StageOutput> {
    logger.stage('Stage 5', '润色与优化');

    const { title, draftFilePath, antiAiRules, seoKeywords } = params;

    if (!fs.existsSync(draftFilePath)) {
      throw new Error(`草稿文件不存在：${draftFilePath}`);
    }

    const draft = fs.readFileSync(draftFilePath, 'utf-8');

    logger.thinking('润色中：去 AI 味 + SEO/GEO 优化...');

    const defaultAntiAiRules =
      '1. 避免空洞的肯定句（如"非常重要的"、"大家普遍认为"）\n' +
      '2. 使用具体数据替代模糊表述\n' +
      '3. 加入个人经历或具体案例\n' +
      '4. 句子长度要有变化，避免平均分配\n' +
      '5. 使用第二人称"你"，避免"人们"、"大家"';

    const seoDefault = '时间管理,效率,深度工作,注意力';

    const rawText = await PromptEngine.callLLM({
      template: STAGE5_PROMPT,
      vars: {
        draft,
        title,
        antiAiRules: antiAiRules ?? defaultAntiAiRules,
        seoKeywords: (seoKeywords ?? seoDefault.split(',')).join(', '),
      },
      model: STAGE5_MODEL,
      temperature: STAGE5_TEMPERATURE,
      thinking: { type: 'disabled' },
      maxTokens: 16000,
    }) as string;

    const parsed = parseJsonResponse(rawText, Stage5ResultSchema);
    if (!parsed) {
      throw new Error(`Stage 5 LLM 返回无法解析：${rawText.slice(0, 200)}`);
    }

    // Save polished content
    const polishedPath = path.join(this.outputDir, 'stage5-polished.md');
    fs.writeFileSync(polishedPath, parsed.polishedContent, 'utf-8');

    const wordCount = parsed.polishedContent.replace(/[#*>\[\]`\s]/g, '').length;

    const result: Stage5Polished = {
      title,
      content: parsed.polishedContent,
      wordCount,
      antiAiCheck: parsed.antiAiCheck,
      seoOptimization: parsed.seoOptimization,
      geoOptimization: { citations: [], entityOptimization: [], aiReadableScore: 0 },
      finalAt: new Date().toISOString(),
    };

    fs.writeFileSync(
      path.join(this.outputDir, 'stage5-confirmed.json'),
      JSON.stringify(result, null, 2),
      'utf-8'
    );
    fs.writeFileSync(polishedPath, parsed.polishedContent, 'utf-8');

    logger.success(`润色完成：${polishedPath}`);
    logger.info(
      `去 AI 味检查：${parsed.antiAiCheck.passed ? '通过' : `违规 ${parsed.antiAiCheck.violations.length} 项`}`
    );

    const output: StageOutput = {
      stage: 'stage5',
      status: 'waiting_user',
      thinking: `润色完成，主要改动：${(parsed.changes ?? []).join('; ')}`,
      result,
    };

    await this.saveOutput(output);
    return output;
  }

  async confirm(): Promise<Stage5Polished> {
    const filePath = path.join(this.outputDir, 'stage5-confirmed.json');
    const result: Stage5Polished = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    logger.success('润色已确认！');
    return result;
  }

  private async saveOutput(output: StageOutput): Promise<void> {
    fs.writeFileSync(
      path.join(this.outputDir, 'stage5-polish.json'),
      JSON.stringify(output, null, 2),
      'utf-8'
    );
  }
}
