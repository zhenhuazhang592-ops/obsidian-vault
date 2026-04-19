/**
 * {{VAR}} 模板替换引擎
 * 参考：dankoe-writer shared/prompts.ts
 *
 * 规则：
 * 1. 所有 prompt 使用 {{VAR}} 占位符，运行时替换
 * 2. 所有 prompt 都是 user role（不含 system wrapper）
 * 3. 替换时做 JSON schema 校验，缺失变量抛出错误
 */

import { z } from 'zod';

// ==================== Schema 定义 ====================

export const Stage1InputSchema = z.object({
  topic: z.string().describe('用户提出的原始主题'),
  researchSummary: z.string().describe('Phase 0 研究摘要'),
  wikiKnowledge: z.string().optional().describe('wiki 预注入知识'),
});

export const Stage2InputSchema = z.object({
  title: z.string().describe('选定的标题'),
  subtitle: z.string().describe('副标题'),
  targetReader: z.string().describe('目标读者'),
  painPoint: z.string().describe('痛点描述'),
  researchSummary: z.string().describe('Phase 0 研究摘要'),
  wikiKnowledge: z.string().optional().describe('wiki 预注入知识'),
});

export const Stage3InputSchema = z.object({
  title: z.string(),
  subtitle: z.string(),
  coreThesis: z.string(),
  supportingPoints: z.array(z.object({
    point: z.string(),
    commonMisconception: z.string(),
    thinkersToCite: z.array(z.string()),
  })),
  wikiKnowledge: z.string().optional(),
});

export const Stage4InputSchema = z.object({
  title: z.string(),
  outline: z.object({
    opening: z.record(z.string()),
    sections: z.array(z.object({
      heading: z.string(),
      keyPoints: z.array(z.string()),
      examples: z.array(z.string()),
    })),
    conclusion: z.record(z.string()),
  }),
  wordCountTarget: z.number().default(2500),
  wikiKnowledge: z.string().optional(),
});

export const Stage5InputSchema = z.object({
  draft: z.string(),
  title: z.string(),
  antiAiRules: z.string(),
  seoKeywords: z.array(z.string()),
});

export const ResearchInputSchema = z.object({
  topic: z.string(),
  wikiKnowledge: z.string().optional(),
});

export const WikiRefluxInputSchema = z.object({
  title: z.string(),
  content: z.string(),
  sources: z.array(z.object({ title: z.string(), url: z.string() })),
  entities: z.array(z.string()).optional(),
  concepts: z.array(z.string()).optional(),
});

// ==================== 模板引擎 ====================

export class PromptEngine {
  /**
   * 替换 prompt 中的 {{VAR}} 占位符
   * 参考：dankoe-writer template substitution
   */
  /**
   * 替换 prompt 中的 {{VAR}} 占位符
   * 支持：
   * - {{VAR}} 普通替换
   * - {{#if VAR}}...{{/if}} 条件块（VAR 存在时保留，否则移除）
   * - {{#each VAR}}...{{VAR}}...{{/each}} 循环（VAR 为数组时展开）
   * 参考：dankoe-writer template substitution + Handlebars 简化子集
   */
  static render(template: string, vars: Record<string, string | string[] | undefined>): string {
    let result = template;

    // 处理 {{#each VAR}}...{{/each}} 循环（支持 dot notation）
    result = result.replace(/\{\{#each ([\w.]+)\}\}([\s\S]*?)\{\{\/each\}\}/g, (_match, varName, block) => {
      const arr = vars[varName];
      if (!Array.isArray(arr)) return '';
      return arr.map(item => {
        let blockResult = block;
        blockResult = blockResult.replace(/\{\{([\w.]+)\}\}/g, (_m: string, key: string) => {
          const itemObj = typeof item === 'object' && item !== null ? item as Record<string, unknown> : {};
          const val = itemObj[key];
          return val !== undefined ? String(val) : '';
        });
        return blockResult;
      }).join('');
    });

    // 处理 {{#if VAR}}...{{/if}} 条件块（支持 dot notation）
    result = result.replace(/\{\{#if ([\w.]+)\}\}([\s\S]*?)\{\{\/if\}\}/g, (_match, varName, block) => {
      const val = vars[varName];
      return val !== undefined && val !== '' ? block : '';
    });

    // 处理普通 {{VAR}} 替换（支持 dot notation）
    for (const [key, value] of Object.entries(vars)) {
      if (Array.isArray(value)) continue;
      if (value === undefined) continue;
      const pattern = new RegExp(`\\{\\{${key.replace(/\./g, '\\.')}\\}\\}`, 'g');
      result = result.replace(pattern, value);
    }

    // 检查未替换的变量
    const unresolved = result.match(/\{\{([\w.]+)\}\}/g);
    if (unresolved) {
      const missing = unresolved.filter(v => {
        const key = v.replace(/\{\{|\}\}/g, '');
        return !(key in vars);
      });
      if (missing.length > 0) {
        throw new Error(`Unresolved prompt variables: ${missing.join(', ')}`);
      }
    }
    return result;
  }

  /**
   * 构建 user role message（不含 system wrapper）
   * 参考：dankoe-writer — user-role-only prompts
   */
  static userMessage(template: string, vars: Record<string, string>): string {
    return this.render(template, vars);
  }

  /**
   * 调用 LLM（统一入口）
   * 模型选择、温度设置参考 dankoe-writer llm.ts
   */
  static async callLLM(params: {
    template: string;
    vars: Record<string, string>;
    model: 'claude-sonnet' | 'claude-opus' | 'qwen3-max';
    temperature: number;
    outputSchema?: z.ZodSchema;
    maxTokens?: number;
    thinking?: { type: 'disabled' };
  }): Promise<unknown> {
    const { Anthropic } = await import('@anthropic-ai/sdk');
    const { config } = await import('../config');

    const modelMap: Record<string, string> = {
      'claude-sonnet': 'MiniMax-M2.7',
      'claude-opus': 'MiniMax-M2.7',
      'qwen3-max': 'MiniMax-M2.7',
    };

    const clientOptions: { apiKey: string; baseURL?: string } = {
      apiKey: config.anthropicApiKey,
    };
    if (config.anthropicBaseUrl) {
      clientOptions.baseURL = config.anthropicBaseUrl;
    }
    const client = new Anthropic(clientOptions);
    const content = this.render(params.template, params.vars);

    const response = await client.messages.create({
      model: modelMap[params.model] ?? params.model,
      max_tokens: params.maxTokens ?? 4096,
      temperature: params.temperature,
      thinking: params.thinking ?? { type: 'disabled' },
      messages: [{ role: 'user', content }],
    });

    // Collect all text blocks (skip thinking blocks)
    const text = response.content
      .filter((block): block is { type: 'text'; text: string } => block.type === 'text')
      .map(block => block.text)
      .join('\n');

    if (params.outputSchema) {
      return params.outputSchema.parse(JSON.parse(text));
    }
    return text;
  }
}
