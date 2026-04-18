/**
 * Session Compaction
 * 参考：claw-code rust/crates/runtime/src/compact.rs
 *
 * head+tail 保护压缩：
 * - 保留前 N 条和后 M 条消息（系统 prompt + 近期上下文）
 * - 压缩中间部分为摘要
 *
 * Fixes (plan-eng-review):
 * - Issue 4/7: compact() 改为 async，解决 sync/async 不匹配
 */

import { ConversationMessage } from '../types';

const HEAD_COUNT = 10;   // 保留前 10 条
const TAIL_COUNT = 20;   // 保留后 20 条
const COMPACTION_THRESHOLD = 60000; // 60K tokens 触发压缩

export class SessionCompactor {
  /**
   * 检查是否需要压缩
   */
  static shouldCompact(messages: ConversationMessage[]): boolean {
    const totalTokens = this.estimateTokens(messages);
    return totalTokens > COMPACTION_THRESHOLD;
  }

  /**
   * 估算 token 数量（简单版：按字符数 / 4）
   */
  static estimateTokens(messages: ConversationMessage[]): number {
    return messages.reduce((sum, m) => sum + Math.ceil(m.content.length / 4), 0);
  }

  /**
   * 执行压缩（head+tail 保护）
   * 注意：summarize() 是 async，compact() 也是 async
   */
  static async compact(messages: ConversationMessage[]): Promise<ConversationMessage[]> {
    if (messages.length <= HEAD_COUNT + TAIL_COUNT) {
      return messages; // 不需要压缩
    }

    const head = messages.slice(0, HEAD_COUNT);
    const tail = messages.slice(-TAIL_COUNT);

    // 生成中间部分摘要
    const middle = messages.slice(HEAD_COUNT, -TAIL_COUNT);
    const summary = await this.summarize(middle);

    // 插入摘要作为过渡
    const compacted: ConversationMessage[] = [
      ...head,
      {
        role: 'system',
        content: `[${new Date().toISOString()}] 早期 ${middle.length} 条消息已压缩为摘要`,
        thinking: summary,
      },
      ...tail,
    ];

    return compacted;
  }

  /**
   * 生成摘要（调用 LLM）
   * Failure Mode 2: 需在 Task 4 集成时注入 LLM credentials
   */
  private static async summarize(messages: ConversationMessage[]): Promise<string> {
    // TODO (Task 4): 注入 LLM credentials 并调用
    // const summary = await callLLM({ prompt: `Summarize: ${messages.map(m => m.content).join('\n')}` });
    return `[${messages.length} 条消息已压缩，精简摘要]`;
  }
}
