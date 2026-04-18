/**
 * Dan Koe 五阶段执行器
 *
 * 编排 Stage 1-5 的执行流程：
 * 1. Stage 1: 选题 → 用户选择
 * 2. Stage 2: 提炼观点 → 用户确认
 * 3. Stage 3: 构建大纲 → 用户确认
 * 4. Stage 4: 撰写正文（Qwen3-Max）
 * 5. Stage 5: 润色与优化
 */

import * as fs from 'fs';
import * as path from 'path';
import { logger } from '../logger';
import { config } from '../config';
import { Stage1Topic } from './stage1-topic';
import { Stage2Thesis } from './stage2-thesis';
import { Stage3Outline } from './stage3-outline';
import { Stage4Writing } from './stage4-writing';
import { Stage5Polish } from './stage5-polish';
import { Stage1Topic as Stage1TopicType, Stage3Outline as Stage3OutlineType } from '../types';

export interface ExecuteOptions {
  topic: string;
  researchSummary?: string;
  wikiKnowledge?: string;
  outputDir?: string;
  wordCountTarget?: number;
}

export interface StageProgress {
  stage: string;
  status: 'pending' | 'completed';
  outputPath?: string;
}

/**
 * 五阶段执行器
 *
 * 使用方式：
 * ```ts
 * const orchestrator = new FiveStageOrchestrator('/path/to/output');
 * const topic = await orchestrator.run();
 * ```
 */
export class FiveStageOrchestrator {
  private outputDir: string;

  constructor(outputDir?: string) {
    this.outputDir = outputDir ?? path.join(config.outputPath, new Date().toISOString().split('T')[0]);
    fs.mkdirSync(this.outputDir, { recursive: true });
  }

  /**
   * 完整执行五阶段（自动流程，无用户交互）
   * 适用于 batch 模式或测试。
   */
  async runFull(options: ExecuteOptions): Promise<void> {
    const { topic, researchSummary, wikiKnowledge, wordCountTarget = 2500 } = options;

    logger.info(`=== Dan Koe 五阶段开始 ===`);
    logger.info(`主题: ${topic}`);
    logger.info(`输出目录: ${this.outputDir}`);

    // Stage 1: 选题
    logger.stage('→', 'Stage 1: 选题');
    const stage1 = new Stage1Topic(this.outputDir);
    const stage1Output = await stage1.execute({ topic, researchSummary: researchSummary ?? '', wikiKnowledge });
    this.saveStageOutput('stage1', stage1Output);

    const topicOptions = (stage1Output.result as { options: unknown[] }).options;
    if (topicOptions.length === 0) {
      throw new Error('Stage 1 未生成任何选题方案');
    }
    logger.success(`生成了 ${topicOptions.length} 个选题`);
    logger.info('请从以下选项中选择（传入 selectedIndex）：');
    topicOptions.forEach((opt: any, i: number) => {
      logger.info(`  [${i}] ${opt.title}`);
    });

    // Stage 2: 观点（假设选择第 0 个）
    logger.stage('→', 'Stage 2: 提炼观点');
    const stage2 = new Stage2Thesis(this.outputDir);
    // Re-load confirmed topic from file
    const confirmed = await stage1.confirm(0);
    const stage2Output = await stage2.execute({
      title: confirmed.selectedTitle,
      subtitle: confirmed.subtitle,
      targetReader: confirmed.targetReader,
      painPoint: confirmed.painPoint,
      researchSummary: researchSummary ?? '',
      wikiKnowledge,
    });
    this.saveStageOutput('stage2', stage2Output);
    const confirmedThesis = await stage2.confirm();

    // Stage 3: 大纲
    logger.stage('→', 'Stage 3: 构建大纲');
    const stage3 = new Stage3Outline(this.outputDir);
    const stage3Output = await stage3.execute({
      topic: confirmed,
      thesis: confirmedThesis,
      wikiKnowledge,
    });
    this.saveStageOutput('stage3', stage3Output);
    const confirmedOutline = await stage3.confirm();

    // Stage 4: 正文
    logger.stage('→', 'Stage 4: 撰写正文（Qwen3-Max）');
    const stage4 = new Stage4Writing(this.outputDir);
    const stage4Output = await stage4.execute({
      outline: confirmedOutline,
      wordCountTarget,
      wikiKnowledge,
    });
    this.saveStageOutput('stage4', stage4Output);
    await stage4.confirm();

    // Stage 5: 润色
    logger.stage('→', 'Stage 5: 润色与优化');
    const stage5 = new Stage5Polish(this.outputDir);
    const draftFile = (stage4Output.result as { filePath: string }).filePath;
    const stage5Output = await stage5.execute({
      title: confirmedOutline.title,
      draftFilePath: draftFile,
    });
    this.saveStageOutput('stage5', stage5Output);
    const polished = await stage5.confirm();

    logger.success(`=== 五阶段完成 ===`);
    logger.info(`润色结果：${path.join(this.outputDir, 'stage5-polished.md')}`);
    logger.info(`字数：${polished.wordCount}`);
    logger.info(`去 AI 味检查：${polished.antiAiCheck.passed ? '通过' : `违规 ${polished.antiAiCheck.violations.length} 项`}`);
  }

  /**
   * 交互式执行（单步，用户每阶段确认）
   * 返回最终润色结果。
   */
  async runInteractive(options: ExecuteOptions): Promise<void> {
    // 交互模式由 CLI（Task 10）实现
    // 这里只做结构占位
    logger.info('交互模式由 CLI 实现（Task 10）');
    throw new Error('TODO: runInteractive — 实现于 Task 10 CLI');
  }

  private saveStageOutput(stage: string, output: unknown): void {
    fs.writeFileSync(
      path.join(this.outputDir, `${stage}.json`),
      JSON.stringify(output, null, 2),
      'utf-8'
    );
  }

  getOutputDir(): string {
    return this.outputDir;
  }
}
