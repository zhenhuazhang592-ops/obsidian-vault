---
name: multi-model-adapter
description: 多模型适配器架构。当你需要统一调用多个 AI 服务（图像/视频/文字）时触发——新增 API、替换模型、或者想用类似 prompt-optimizer 的 Adapter Registry 模式时使用。触发词：统一多 API / adapter / 注册中心 / 多模型调用 / 适配器模式 / 统一图像生成 / 统一视频生成 / huage888 重构 / baoyu 重构
tags:
  - architecture
  - llm
  - adapter-pattern
  - typescript
---

# Multi-Model Adapter · 多模型适配器架构

> 参考：prompt-optimizer `packages/core/src/services/llm/adapters/` 的 Adapter Registry 模式
> 用途：统一管理多个 AI 服务调用，新增 API 只需注册适配器，不动核心逻辑

---

## 核心理念

**一个接口，多个实现。切换模型只需换适配器，不改调用方。**

```
你的服务
    │
    ▼
AdapterRegistry.get('openai')  ← 换这一行代码就换模型
    │
    ├── OpenAIAdapter    → OpenAI API
    ├── AnthropicAdapter → Claude API
    ├── DashScopeAdapter → 通义千问/豆包
    ├── DoubaoAdapter    → 即梦/可灵
    └── ...              → 新增模型只需写新适配器
```

---

## 1. 核心接口定义

```typescript
// types/adapter.ts

/** 消息格式 */
export interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

/** 模型配置 */
export interface ModelConfig {
  model: string;
  apiKey: string;
  baseUrl?: string;
  maxTokens?: number;
  temperature?: number;
  timeout?: number;
  // 特定模型的参数（如图像的 size、风格等）
  extra?: Record<string, unknown>;
}

/** LLM 响应 */
export interface LLMResponse {
  content: string;
  model: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  finishReason?: 'stop' | 'length' | 'content_filter';
}

/** 流式响应块 */
export interface LLMStreamChunk {
  delta: string;
  done: boolean;
  usage?: LLMResponse['usage'];
}

/** 适配器接口 */
export interface ILLMAdapter {
  /** 同步调用 */
  sendMessage(messages: Message[], config: ModelConfig): Promise<LLMResponse>;

  /** 流式调用 */
  sendMessageStream(
    messages: Message[],
    config: ModelConfig
  ): AsyncGenerator<LLMStreamChunk>;

  /** 健康检查 */
  healthCheck?(config: ModelConfig): Promise<boolean>;
}
```

---

## 2. 适配器注册中心

```typescript
// adapters/registry.ts

import type { ILLMAdapter, Message, ModelConfig, LLMResponse } from '../types/adapter';

export class AdapterRegistry {
  private adapters = new Map<string, ILLMAdapter>();

  /** 注册适配器 */
  register(name: string, adapter: ILLMAdapter): void {
    if (this.adapters.has(name)) {
      console.warn(`Adapter "${name}" 已被注册，将被覆盖`);
    }
    this.adapters.set(name, adapter);
  }

  /** 获取适配器 */
  get(name: string): ILLMAdapter {
    const adapter = this.adapters.get(name);
    if (!adapter) {
      const available = Array.from(this.adapters.keys()).join(', ');
      throw new Error(
        `未找到适配器 "${name}"。可用适配器: ${available}`
      );
    }
    return adapter;
  }

  /** 判断是否存在 */
  has(name: string): boolean {
    return this.adapters.has(name);
  }

  /** 列出所有适配器 */
  list(): string[] {
    return Array.from(this.adapters.keys());
  }

  /** 统一调用入口 */
  async sendMessage(
    adapterName: string,
    messages: Message[],
    config: ModelConfig
  ): Promise<LLMResponse> {
    return this.get(adapterName).sendMessage(messages, config);
  }
}

// 全局单例
export const globalRegistry = new AdapterRegistry();
```

---

## 3. 适配器基类

```typescript
// adapters/base-adapter.ts

import type { ILLMAdapter, Message, ModelConfig, LLMResponse, LLMStreamChunk } from '../types/adapter';

export abstract class BaseAdapter implements ILLMAdapter {
  protected abstract provider: string;

  abstract sendMessage(
    messages: Message[],
    config: ModelConfig
  ): Promise<LLMResponse>;

  async *sendMessageStream(
    messages: Message[],
    config: ModelConfig
  ): AsyncGenerator<LLMStreamChunk> {
    // 默认实现：调用同步版本并包装
    const response = await this.sendMessage(messages, config);
    yield { delta: response.content, done: true, usage: response.usage };
  }

  async healthCheck(config: ModelConfig): Promise<boolean> {
    try {
      await this.sendMessage([{ role: 'user', content: 'hi' }], {
        ...config,
        maxTokens: 5,
      });
      return true;
    } catch {
      return false;
    }
  }

  /** 通用工具：从 messages 构建请求体 */
  protected abstract buildRequestBody(
    messages: Message[],
    config: ModelConfig
  ): Record<string, unknown>;

  /** 通用工具：解析响应 */
  protected abstract parseResponse(raw: unknown): LLMResponse;

  /** 通用工具：构建 headers */
  protected buildHeaders(apiKey: string): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    };
  }

  /** 通用工具：fetch 封装 */
  protected async fetch(
    url: string,
    options: RequestInit & { timeout?: number }
  ): Promise<Response> {
    const controller = new AbortController();
    const timeout = options.timeout ?? 60000;
    const timer = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      return response;
    } finally {
      clearTimeout(timer);
    }
  }
}
```

---

## 4. 具体适配器示例

### 4.1 OpenAI 适配器

```typescript
// adapters/openai-adapter.ts

import { BaseAdapter } from './base-adapter';
import type { Message, ModelConfig, LLMResponse } from '../types/adapter';

export class OpenAIAdapter extends BaseAdapter {
  protected provider = 'openai';

  protected buildRequestBody(messages: Message[], config: ModelConfig): Record<string, unknown> {
    return {
      model: config.model || 'gpt-4o',
      messages: messages.map(m => ({
        role: m.role,
        content: m.content,
      })),
      max_tokens: config.maxTokens ?? 4096,
      temperature: config.temperature ?? 0.7,
      ...config.extra,
    };
  }

  protected parseResponse(raw: unknown): LLMResponse {
    const r = raw as {
      choices: Array<{ message: { content: string }; finish_reason: string }>;
      usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
    };
    return {
      content: r.choices[0]?.message?.content ?? '',
      model: this.provider,
      usage: r.usage,
      finishReason: r.choices[0]?.finish_reason as LLMResponse['finishReason'],
    };
  }

  async sendMessage(
    messages: Message[],
    config: ModelConfig
  ): Promise<LLMResponse> {
    const baseUrl = config.baseUrl || 'https://api.openai.com/v1';
    const url = `${baseUrl}/chat/completions`;

    const body = this.buildRequestBody(messages, config);
    const response = await this.fetch(url, {
      method: 'POST',
      headers: this.buildHeaders(config.apiKey),
      body: JSON.stringify(body),
      timeout: config.timeout,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`OpenAI API 错误 ${response.status}: ${error}`);
    }

    const data = await response.json();
    return this.parseResponse(data);
  }
}
```

### 4.2 DashScope（通义千问/豆包）适配器

```typescript
// adapters/dashscope-adapter.ts

import { BaseAdapter } from './base-adapter';
import type { Message, ModelConfig, LLMResponse } from '../types/adapter';

export class DashScopeAdapter extends BaseAdapter {
  protected provider = 'dashscope';

  protected buildRequestBody(messages: Message[], config: ModelConfig): Record<string, unknown> {
    // DashScope 的 messages 格式与 OpenAI 兼容
    return {
      model: config.model || 'qwen-max',
      messages: messages.map(m => ({
        role: m.role === 'assistant' ? 'assistant' : m.role,
        content: m.content,
      })),
      max_tokens: config.maxTokens ?? 4096,
      temperature: config.temperature ?? 0.7,
      ...config.extra,
    };
  }

  protected parseResponse(raw: unknown): LLMResponse {
    const r = raw as {
      output: { text: string };
      usage: { input_tokens: number; output_tokens: number };
      request_id: string;
    };
    return {
      content: r.output?.text ?? '',
      model: this.provider,
      usage: {
        promptTokens: r.usage?.input_tokens ?? 0,
        completionTokens: r.usage?.output_tokens ?? 0,
        totalTokens: (r.usage?.input_tokens ?? 0) + (r.usage?.output_tokens ?? 0),
      },
    };
  }

  async sendMessage(
    messages: Message[],
    config: ModelConfig
  ): Promise<LLMResponse> {
    const baseUrl = config.baseUrl || 'https://dashscope.aliyuncs.com/api/v1';
    const url = `${baseUrl}/services/aigc/text-generation/generation`;

    const body = this.buildRequestBody(messages, config);
    const response = await this.fetch(url, {
      method: 'POST',
      headers: {
        ...this.buildHeaders(config.apiKey),
        'X-DashScope-Sse': 'disable', // 同步调用
      },
      body: JSON.stringify(body),
      timeout: config.timeout,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`DashScope API 错误 ${response.status}: ${error}`);
    }

    const data = await response.json();
    return this.parseResponse(data);
  }
}
```

### 4.3 即梦/可灵图像适配器

```typescript
// adapters/doubao-image-adapter.ts

import type { Message, ModelConfig, LLMResponse } from '../types/adapter';
import { BaseAdapter } from './base-adapter';

interface DoubaoImageResponse {
  data: Array<{
    url: string;          // 直接返回图片 URL
    base64?: string;      // 或 base64
  }>;
  model: string;
  request_id: string;
}

/** 即梦/可灵图像生成适配器 */
export class DoubaoImageAdapter extends BaseAdapter {
  protected provider = 'doubao-image';

  async sendMessage(
    messages: Message[],
    config: ModelConfig
  ): Promise<LLMResponse> {
    // 图像生成的 messages[0] 是图片 prompt
    const prompt = messages.find(m => m.role === 'user')?.content ?? '';

    const baseUrl = config.baseUrl || 'https://ark.cn-beijing.volces.com/api/v3';
    const url = `${baseUrl}/images/generations`;

    const body = {
      model: config.model || 'doubao-image-240312',
      prompt,
      size: (config.extra?.size as string) || '1024x1024',
      n: (config.extra?.n as number) || 1,
      response_format: 'url',
    };

    const response = await this.fetch(url, {
      method: 'POST',
      headers: this.buildHeaders(config.apiKey),
      body: JSON.stringify(body),
      timeout: config.timeout ?? 120000,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Doubao Image API 错误 ${response.status}: ${error}`);
    }

    const data = (await response.json()) as { data: DoubaoImageResponse['data'] };
    const imageUrl = data.data?.[0]?.url ?? '';

    return {
      content: imageUrl,
      model: config.model || 'doubao-image',
    };
  }

  protected buildRequestBody(
    messages: Message[],
    config: ModelConfig
  ): Record<string, unknown> {
    throw new Error('Not used in image adapter');
  }

  protected parseResponse(raw: unknown): LLMResponse {
    const r = raw as DoubaoImageResponse;
    return {
      content: r.data?.[0]?.url ?? '',
      model: r.model,
    };
  }
}
```

---

## 5. 工厂函数

```typescript
// factories/service-factory.ts

import { globalRegistry } from '../adapters/registry';
import { OpenAIAdapter } from '../adapters/openai-adapter';
import { DashScopeAdapter } from '../adapters/dashscope-adapter';
import { DoubaoImageAdapter } from '../adapters/doubao-image-adapter';
import type { ILLMService, Message, ModelConfig, LLMResponse } from '../types/adapter';

export interface LLMServiceConfig {
  defaultAdapter?: string;
  timeout?: number;
}

/** LLM 服务接口 */
export interface ILLMService {
  sendMessage(
    messages: Message[],
    adapterName: string,
    config: Partial<ModelConfig>
  ): Promise<LLMResponse>;
}

/** 创建 LLM 服务（自动注册所有内置适配器）*/
export function createLLMService(config: LLMServiceConfig = {}): ILLMService {
  // 注册内置适配器（只注册一次）
  if (!globalRegistry.has('openai')) {
    globalRegistry.register('openai', new OpenAIAdapter());
    globalRegistry.register('dashscope', new DashScopeAdapter());
    globalRegistry.register('doubao-image', new DoubaoImageAdapter());
  }

  return {
    async sendMessage(
      messages: Message[],
      adapterName: string,
      config: Partial<ModelConfig>
    ): Promise<LLMResponse> {
      const fullConfig: ModelConfig = {
        model: config.model || '',
        apiKey: config.apiKey || process.env.API_KEY || '',
        baseUrl: config.baseUrl,
        maxTokens: config.maxTokens ?? 4096,
        temperature: config.temperature ?? 0.7,
        timeout: config.timeout ?? 60000,
        extra: config.extra,
      };

      return globalRegistry.sendMessage(adapterName, messages, fullConfig);
    },
  };
}
```

---

## 6. 使用示例

### 6.1 基础调用

```typescript
// example-usage.ts

import { createLLMService } from './factories/service-factory';
import type { Message } from './types/adapter';

const llm = createLLMService();

async function main() {
  const messages: Message[] = [
    { role: 'system', content: '你是一个有帮助的助手' },
    { role: 'user', content: '用一句话介绍漫舟工作室' },
  ];

  // 用 OpenAI
  const openaiResult = await llm.sendMessage(messages, 'openai', {
    apiKey: process.env.OPENAI_API_KEY!,
    model: 'gpt-4o',
  });
  console.log('OpenAI:', openaiResult.content);

  // 换成通义千问（一行代码）
  const dashscopeResult = await llm.sendMessage(messages, 'dashscope', {
    apiKey: process.env.DASHSCOPE_API_KEY!,
    model: 'qwen-max',
  });
  console.log('DashScope:', dashscopeResult.content);
}

main().catch(console.error);
```

### 6.2 新增适配器（扩展）

```typescript
// 任何时候，只需注册新适配器，不改核心代码
globalRegistry.register('anthropic', new AnthropicAdapter());
globalRegistry.register('deepseek', new DeepseekAdapter());
globalRegistry.register('kling', new KlingVideoAdapter()); // 视频生成
globalRegistry.register('haloworld', new HaloWorldAdapter()); // 未来新增
```

---

## 7. 目录结构模板

```
your-project/
├── types/
│   └── adapter.ts           # 核心类型定义
├── adapters/
│   ├── base-adapter.ts      # 基类
│   ├── registry.ts          # 注册中心
│   ├── openai-adapter.ts
│   ├── anthropic-adapter.ts
│   ├── dashscope-adapter.ts
│   ├── doubao-image-adapter.ts
│   └── your-new-adapter.ts  # 新增只需加这个文件
├── factories/
│   └── service-factory.ts   # 工厂函数
├── services/
│   └── your-service.ts      # 业务逻辑（通过注册中心调用）
└── example/
    └── usage.ts
```

---

## 8. 参考来源

- 完整实现：`/Users/huage/Downloads/prompt-optimizer-develop/packages/core/src/services/llm/adapters/registry.ts`
- 适配器集合：`/Users/huage/Downloads/prompt-optimizer-develop/packages/core/src/services/llm/adapters/`
- MCP Server 适配器层：`/Users/huage/Downloads/prompt-optimizer-develop/packages/mcp-server/src/adapters/`
