/**
 * Engine 单元测试
 * 验证 WritingEngine + SessionCompactor 核心逻辑
 *
 * Fixes (plan-eng-review):
 * - Issue 5: 补充 engine.test.ts（plan 代码是存根）
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { WritingEngine, createSession, createReadlineLoop } from '../src/engine';
import { SessionCompactor } from '../src/runtime/compact';
import { ConversationMessage } from '../src/types';

// Mock RunLoop
const mockRunLoop = {
  prompt: vi.fn().mockResolvedValue('/exit'),
};

describe('WritingEngine', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should create session with correct id', async () => {
    const engine = await createSession('测试主题', mockRunLoop);
    expect(engine.session.sessionId).toMatch(/^session-\d+$/);
    expect(engine.session.topic).toBe('测试主题');
    expect(engine.session.phase).toBe('idle');
  });

  it('should create output directory path', async () => {
    const engine = await createSession('测试主题', mockRunLoop);
    expect(engine.session.outputDir).toContain('测试主题');
    expect(engine.session.outputDir).toContain('01-资源库');
  });

  it('should accept custom runLoop', async () => {
    const customLoop = { prompt: vi.fn().mockResolvedValue('/exit') };
    const engine = await createSession('自定义循环', customLoop);
    expect(engine.session.topic).toBe('自定义循环');
  });
});

describe('SessionCompactor', () => {
  const makeMessages = (n: number): ConversationMessage[] =>
    Array.from({ length: n }, (_, i) => ({
      role: 'user' as const,
      content: `Message ${i}: ${'x'.repeat(100)}`,
    }));

  it('should not compact short sessions', async () => {
    const msgs = makeMessages(20);
    const compacted = await SessionCompactor.compact(msgs);
    expect(compacted.length).toBe(20);
  });

  it('should compact long sessions with head+tail protection', async () => {
    const msgs = makeMessages(100);
    const compacted = await SessionCompactor.compact(msgs);
    // 保留 HEAD(10) + summary(1) + TAIL(20) = 31
    expect(compacted.length).toBe(31);
    expect(compacted[10].role).toBe('system'); // 摘要
  });

  it('should estimate tokens correctly', () => {
    const msgs = [
      { role: 'user' as const, content: 'abcd' },      // 1 token
      { role: 'user' as const, content: 'abcdefgh' }, // 2 tokens
    ];
    const tokens = SessionCompactor.estimateTokens(msgs);
    expect(tokens).toBeGreaterThan(0);
  });

  it('should not compact at threshold', async () => {
    // 每条消息 100 字符 ≈ 25 tokens，30 条 ≈ 750 tokens < 60K
    const msgs = makeMessages(30);
    expect(SessionCompactor.shouldCompact(msgs)).toBe(false);
  });

  it('should trigger compaction above threshold', async () => {
    // 需要超过 60K tokens ≈ 240K 字符
    const msgs = makeMessages(2500);
    expect(SessionCompactor.shouldCompact(msgs)).toBe(true);
  });
});
