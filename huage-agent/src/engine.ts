/**
 * Writing Workflow Engine
 *
 * 核心架构参考：claw-code ConversationRuntime
 * - 工具循环：Messages API + handleToolResult()
 * - 阶段状态机：idle → phase0 → stage1-5 → output → completed
 * - 断点续传：每个阶段完成后写入 JSONL checkpoint
 * - Hook 系统：PreToolUse/PostToolUse
 * - Session Compaction：head+tail 保护压缩（async）
 *
 * Fixes (plan-eng-review):
 * - Issue 3: 使用 Messages API（v0.32 无 agent.generate()）
 * - Issue 6: 提取 runLoop 接口，engine 与 CLI 解耦
 * - Failure Mode 1: SIGINT guard flag 防止竞态
 */

import { Anthropic } from '@anthropic-ai/sdk';
import * as fs from 'fs';
import * as path from 'path';
import { config } from './config';
import { logger } from './logger';
import { HookRunner } from './runtime/hooks';
import { SessionCompactor } from './runtime/compact';
import {
  AgentSession,
  PhaseState,
  StageState,
  StageOutput,
  ConversationMessage,
} from './types';
import { Memory } from './memory';

export interface RunLoop {
  prompt(): Promise<string>;
}

export class WritingEngine {
  private client: Anthropic;
  private session: AgentSession;
  private memory: Memory;
  private hooks: HookRunner;
  private outputDir: string;
  private messages: ConversationMessage[] = [];
  private checkpointDir: string;
  private runLoop: RunLoop;

  // Failure Mode 1: SIGINT guard flag
  private isShuttingDown = false;
  private isSavingCheckpoint = false;

  constructor(sessionId: string, topic: string, runLoop: RunLoop) {
    this.client = new Anthropic({ apiKey: config.anthropicApiKey });
    this.memory = new Memory();
    this.hooks = new HookRunner();
    this.runLoop = runLoop;

    // 创建输出目录和 checkpoint 目录
    const date = new Date().toISOString().split('T')[0];
    const slug = topic.slice(0, 20).replace(/\s+/g, '-');
    this.outputDir = path.join(
      config.outputPath,
      `01-资源库/${date}/${slug}`
    );
    this.checkpointDir = path.join(this.outputDir, 'checkpoints');
    fs.mkdirSync(this.checkpointDir, { recursive: true });

    this.session = {
      sessionId,
      topic,
      outputDir: this.outputDir,
      phase: 'idle',
      currentStage: 'pending',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    // 注册退出时自动保存（带 guard）
    process.on('SIGINT', () => this.saveCheckpoint());
  }

  // ==================== Checkpoint（JSONL 格式） ====================

  private async saveCheckpoint(): Promise<void> {
    // Failure Mode 1 guard: 防止竞态
    if (this.isShuttingDown) return;
    if (this.isSavingCheckpoint) return;

    this.isSavingCheckpoint = true;
    try {
      const checkpointFile = path.join(
        this.checkpointDir,
        `${this.session.phase}.jsonl`
      );
      const entry = {
        ts: new Date().toISOString(),
        stage: this.session.phase,
        data: {
          session: this.session,
          messages: this.messages.slice(-10),
        },
      };
      fs.appendFileSync(checkpointFile, JSON.stringify(entry) + '\n', 'utf-8');
      logger.info(`Checkpoint saved: ${checkpointFile}`);
    } finally {
      this.isSavingCheckpoint = false;
    }
  }

  private async loadCheckpoint(stage: string): Promise<ConversationMessage[] | null> {
    const checkpointFile = path.join(this.checkpointDir, `${stage}.jsonl`);
    if (!fs.existsSync(checkpointFile)) return null;
    const lines = fs.readFileSync(checkpointFile, 'utf-8').trim().split('\n');
    if (!lines.length) return null;
    const last = JSON.parse(lines[lines.length - 1]);
    return last.data?.messages ?? null;
  }

  // ==================== 阶段状态管理 ====================

  private async saveStageOutput(stage: string, output: StageOutput): Promise<void> {
    const filePath = path.join(this.outputDir, `${stage}.json`);
    fs.writeFileSync(filePath, JSON.stringify(output, null, 2), 'utf-8');
    await this.saveCheckpoint();
    this.session.updatedAt = new Date().toISOString();
  }

  private async loadStageOutput(stage: string): Promise<StageOutput | null> {
    const filePath = path.join(this.outputDir, `${stage}.json`);
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    }
    return null;
  }

  // ==================== 工具循环（核心）====================

  /**
   * 主循环：读取 → PreHook → Agent生成 → PostHook → 处理结果
   * Issue 6: runLoop 注入解耦，engine 不依赖 readline
   * Issue 3: 使用 Messages API（而非不存在的 agent.generate()）
   */
  async run(): Promise<void> {
    logger.info(`启动 Writing Workflow Engine，会话ID: ${this.session.sessionId}`);
    logger.info(`主题: ${this.session.topic}`);
    logger.info(`输出目录: ${this.outputDir}`);

    // 尝试恢复 checkpoint
    const recoveredMessages = await this.loadCheckpoint(this.session.phase);
    if (recoveredMessages) {
      this.messages = recoveredMessages;
      logger.info('Checkpoint 恢复成功');
    }

    await this.memory.save(this.session);

    let running = true;
    while (running) {
      // Issue 6: 通过 runLoop 接口读取输入（可替换为 CLI/readline/其他）
      const input = await this.runLoop.prompt();

      if (input === '/exit') {
        running = false;
        continue;
      }

      // 添加用户消息
      this.messages.push({ role: 'user', content: input });

      // 检查是否需要压缩（async）
      if (SessionCompactor.shouldCompact(this.messages)) {
        logger.info('Session compaction triggered...');
        this.messages = await SessionCompactor.compact(this.messages);
      }

      // Issue 3: Messages API 调用
      const response = await this.client.messages.create({
        model: config.claudeModel,
        max_tokens: 4096,
        temperature: 0.7,
        messages: this.messages.map((m) => ({
          role: m.role as 'user' | 'assistant',
          content: m.content,
        })),
      });

      const text = response.content[0].type === 'text'
        ? response.content[0].text
        : '';

      // 添加 Assistant 响应
      this.messages.push({ role: 'assistant', content: text });

      // PostToolUse Hook
      const hookResult = await this.hooks.runPostToolUse(
        'user',
        {},
        text,
        false
      );
      if (hookResult.messages.length > 0) {
        logger.warn(`Hook 警告: ${hookResult.messages.join(', ')}`);
      }

      // 输出响应
      logger.info('Engine 响应:');
      console.log(text);

      // 保存 checkpoint
      await this.saveCheckpoint();
    }

    logger.success('会话结束');
  }

  private buildSystemPrompt(): string {
    return `你是 huage Agent，专注文章创作的 Writing Workflow Engine。

核心理念：huage Agent + Obsidian Vault + LLM-Wiki = 知识复利增长的创作 Agent

你的职责：
1. 按照 Dan Koe 五阶段方法论引导用户完成文章创作
2. 每个阶段都要展示你的思考过程
3. 遇到关键决策点，等待用户确认
4. 调用工具完成任务

当前阶段：${this.session.phase}
当前状态：${this.session.currentStage}
`;
  }
}

// ==================== CLI 入口 ====================

export async function createSession(
  topic: string,
  runLoop: RunLoop
): Promise<WritingEngine> {
  const sessionId = `session-${Date.now()}`;
  return new WritingEngine(sessionId, topic, runLoop);
}

// ==================== 内置 RunLoop 实现 ====================

export async function createReadlineLoop(): Promise<RunLoop> {
  const readline = await import('readline');
  return {
    async prompt(): Promise<string> {
      const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
      });
      return new Promise<string>((resolve) => {
        rl.question('\n> ', (answer) => {
          rl.close();
          resolve(answer);
        });
      });
    },
  };
}
