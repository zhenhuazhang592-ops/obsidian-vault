---
tags:
  - reference
  - architecture
  - llm
  - prompt-engineering
date: 2026-04-07
---

# Prompt Optimizer 深度拆解 · 参考文档

> 来源：[linshenkx/prompt-optimizer](https://github.com/linshenkx/prompt-optimizer)（AGPL-3.0）
> 分析深度：packages/core、packages/mcp-server、docs/workspace、docs/core
> 用途：提取可复用架构，为漫舟工作室的 AI 工具链提供基础设施参考

---

## 1. 项目架构总览

```
prompt-optimizer/
├── packages/
│   ├── core/          # TypeScript 核心库（算法/模型/模板/评估）
│   ├── ui/            # Vue 3 组件库
│   ├── web/           # Vite Web 应用
│   ├── desktop/       # Electron 桌面应用
│   ├── extension/     # 浏览器插件
│   └── mcp-server/    # MCP 协议服务端
├── docs/
│   ├── core/          # 核心概念文档
│   ├── workspace/     # 工作区模式
│   └── user/          # 用户部署指南
├── api/               # Vercel Serverless 函数
├── docker/            # Docker 部署
└── scripts/           # 构建/测试脚本
```

**技术栈**：TypeScript + Vue 3 + Vite + pnpm monorepo + Vitest + tsup

---

## 2. 核心模块职责

### 2.1 Core 包服务层（packages/core/src/services/）

| 模块 | 职责 | 核心文件 |
|------|------|---------|
| `prompt/` | 提示词优化/迭代/测试 | `service.ts` |
| `llm/` | 多模型统一调用 | `service.ts` + `adapters/` |
| `template/` | 模板管理 + Mustache 渲染 | `manager.ts` + `processor.ts` |
| `model/` | 模型配置管理 | `manager.ts` |
| `evaluation/` | 单结果评估 + 对比评估 | `service.ts` |
| `history/` | 优化历史记录 | `manager.ts` |
| `variable-extraction/` | 从提示词提取 `{{变量}}` | `service.ts` |
| `variable-value-gen/` | 智能生成变量示例值 | `service.ts` |
| `storage/` | 存储抽象（IndexedDB/local/memory/file） | `factory.ts` + providers |

### 2.2 MCP Server 包（packages/mcp-server/）

| 文件 | 职责 |
|------|------|
| `src/index.ts` | 主入口，支持 stdio + HTTP 双传输 |
| `src/start.ts` | 运行时启动 |
| `src/adapters/core-services.ts` | Core 服务单例管理器 |
| `src/adapters/parameter-adapter.ts` | 参数验证 |
| `src/adapters/error-handler.ts` | 错误标准化 |
| `src/config/environment.ts` | 环境变量配置 |

---

## 3. 关键设计模式

### 3.1 Adapter Registry（适配器注册中心）

**核心思想**：所有 LLM 调用通过统一接口，底层切换不同模型只需注册新适配器。

```
TextAdapterRegistry
  │
  ├── register('openai',    OpenAIAdapter)
  ├── register('anthropic', AnthropicAdapter)
  ├── register('gemini',    GeminiAdapter)
  ├── register('deepseek',  DeepseekAdapter)
  ├── register('dashscope', DashScopeAdapter)   ← 阿里云通义
  └── ...
```

**统一接口**：
```typescript
interface ILLMAdapter {
  sendMessage(messages: Message[], config: ModelConfig): Promise<LLMResponse>;
  sendMessageStream(...): AsyncGenerator<LLMResponse>;
}
```

**我们的应用场景**：
- `baoyu-image-gen`：统一 OpenAI/Google/DashScope/Doubao/Replicate 图像 API
- `huage888`：统一即梦/可灵/海螺/通义视频 API
- 未来：任何新增 AI 服务只需注册适配器，不动核心逻辑

### 3.2 模板引擎（Mustache + 工厂函数）

```
TemplateManager
  │
  ├── 内置模板（StaticLoader）  → 14 种模板类型
  ├── 用户模板（Storage）       → 导入/导出/CRUD
  └── 语言切换（zh/en）
         │
         ▼
  TemplateProcessor（Mustache）
    ├── {{variable}}           → 变量替换
    ├── {{#var}}...{{/var}}   → 条件渲染
    └── helpers.toJson()       → JSON 序列化
```

**14 种模板类型**：
```
optimize / userOptimize / text2imageOptimize / image2imageOptimize
multiimageOptimize / imageIterate / iterate
conversationMessageOptimize / contextUserOptimize / contextIterate
contextSystemOptimize / evaluation / variable-extraction / variable-value-generation
```

**我们的应用场景**：
- 分镜脚本模板：`{{scene}}/{{shot}}/{{dialogue}}/{{action}}`
- 视觉圣经模板：`{{character}}/{{setting}}/{{mood}}/{{camera}}`
- 漠玫 IP 模板：`{{pose}}/{{expression}}/{{lighting}}/{{colorPalette}}`

### 3.3 工厂函数模式（核心服务创建）

```typescript
// 每个服务都有统一的工厂函数，依赖注入透明
export function createLLMService(modelManager: ModelManager): ILLMService
export function createTemplateManager(storage, languageService): TemplateManager
export function createPromptService(...): PromptService
export function createModelManager(storageProvider): ModelManager
export function createHistoryManager(storage, modelManager): HistoryManager
export function createCompareService(): ICompareService
```

**我们的应用场景**：我们的 `baoyu-image-gen`、`huage888` 也可以用这套工厂模式重构，核心逻辑和 API 调用完全解耦。

### 3.4 存储抽象（Storage Factory）

```
StorageFactory
  │
  ├── DexieStorageProvider    → IndexedDB（浏览器）
  ├── LocalStorageProvider     → localStorage（轻量）
  ├── MemoryStorageProvider    → 内存（MCP Server）
  └── FileStorageProvider      → 文件系统（桌面/CI）
```

**我们的应用场景**：我们的 Obsidian 插件 + Web 应用 + 未来桌面端可以共用同一套存储抽象。

### 3.5 单例模式（CoreServicesManager）

```typescript
class CoreServicesManager {
  private static instance: CoreServicesManager;
  static getInstance(): CoreServicesManager { ... }
}
```

MCP Server 使用单例确保全局只有一套服务实例，避免重复初始化。

---

## 4. Prompt 优化流程

### 4.1 基础优化流程

```
用户输入 prompt
      │
      ▼
┌──────────────────┐
│ Validation        │ ← 非空、长度、超限检查
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Template         │ ← 获取模板（system/user）+ 模型配置
│ Resolution       │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Context Building  │ ← 注入 originalPrompt / mode / variables
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Mustache Render   │ ← 渲染 system prompt + user prompt
└────────┬─────────┘
         ▼
┌──────────────────┐
│ LLM Call         │ ← adapterRegistry.sendMessage()
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Response Check    │ ← 验证非空、结构正确
└────────┬─────────┘
         ▼
   优化后的 prompt
```

### 4.2 迭代优化流程

比基础优化多两个输入：
- `lastOptimizedPrompt`：上次优化结果
- `iterateInput`：改进需求（如"让语气更专业"）

使用 `iterate` 模板类型渲染，包含 `{{lastOptimizedPrompt}}` 和 `{{iterateInput}}`。

### 4.3 评估流程

```
Test Results (snapshots)
      │
      ▼
┌──────────────────────────────────────┐
│         Evaluation Service            │
│                                       │
│  Generic Compare    Structured Compare │
│  • summary         • pairwise judge   │
│  • improvements   • synthesis        │
│  • patchPlan       • stop signals     │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│      Rewrite From Evaluation          │
│  输入: eval result + prompt           │
│  输出: new prompt draft              │
└──────────────────────────────────────┘
```

**Structured Compare 输出**：
```typescript
interface CompareStopSignals {
  targetVsBaseline:      'improved' | 'flat' | 'regressed';
  targetVsReferenceGap:  'none' | 'minor' | 'major';
  improvementHeadroom:   'none' | 'low' | 'medium' | 'high';
  overfitRisk:           'low' | 'medium' | 'high';
  stopRecommendation:    'continue' | 'stop' | 'review';
}
```

---

## 5. MCP Server 实现要点

### 5.1 双传输模式

```typescript
// 通过命令行参数切换
const transport = process.argv.includes('--transport=http')
  ? 'http'
  : 'stdio';
```

| 模式 | 用途 | 场景 |
|------|------|------|
| stdio | 单会话，Claude Desktop 直连 | 桌面/本地 |
| HTTP Streamable | 多会话，会话管理 | Vercel/服务器部署 |

### 5.2 HTTP 会话管理

```typescript
// 每个会话独立创建 Transport 实例
const sessions = new Map<string, StreamableHTTPServerTransport>();

app.post('/mcp', (req, res) => {
  const sessionId = req.headers['mcp-session-id'];
  if (!sessions.has(sessionId)) {
    sessions.set(sessionId, new StreamableHTTPServerTransport());
  }
  // ...
});
```

### 5.3 暴露的 3 个工具

| 工具名 | 功能 |
|--------|------|
| `optimize-user-prompt` | 优化用户提示词 |
| `optimize-system-prompt` | 优化系统提示词 |
| `iterate-prompt` | 基于需求迭代已有提示词 |

---

## 6. 对我们的价值映射

### 6.1 直接可复用

| Prompt Optimizer 模块 | 对应我们的项目 | 复用方式 |
|----------------------|--------------|---------|
| LLM Adapter Registry | `baoyu-image-gen` | 统一多 API 图像调用 |
| LLM Adapter Registry | `huage888` | 统一多 API 视频调用 |
| Template System | 分镜脚本生成 | `{{scene}}/{{shot}}` 占位符 |
| Variable Extraction | 漠玫 IP 批量生成 | `{{expression}}/{{pose}}` |
| Structured Compare | 分镜版本评估 | 对比两个剧本/分镜版本 |
| MCP Server | 未来 AI 工具链集成 | MCP 协议接入 Claude Desktop |

### 6.2 架构参考

| 模式 | 在我们的项目中的形态 |
|------|-------------------|
| Adapter Registry | `scripts/adapters/` 目录，每个 API 一个文件 |
| Factory Pattern | `scripts/factories/` 工厂函数统一创建 |
| Template Engine | `prompts/templates/` 目录 + Mustache 渲染 |
| Storage Abstraction | `storage/` 接口 + Web/Node 实现 |
| Evaluation Service | `scripts/compare/` 版本对比脚本 |

---

## 7. 关键文件索引

| 来源文件 | 核心价值 |
|---------|---------|
| `packages/core/src/services/llm/adapters/registry.ts` | 适配器注册中心实现 |
| `packages/core/src/services/template/manager.ts` | 模板管理器 |
| `packages/core/src/services/template/processor.ts` | Mustache 渲染器 |
| `packages/core/src/services/evaluation/service.ts` | 评估服务（结构化对比） |
| `packages/mcp-server/src/index.ts` | MCP 服务器（512行） |
| `packages/mcp-server/src/adapters/core-services.ts` | 服务单例管理（269行） |
| `packages/core/src/services/storage/factory.ts` | 存储抽象工厂 |
| `packages/core/src/services/prompt/service.ts` | Prompt 服务（核心） |

---

## 8. 下一步行动

- [ ] 重构 `baoyu-image-gen`，引入 Adapter Registry 模式
- [ ] 提取漠玫 IP 模板系统（角色/表情/场景组合）
- [ ] 构建分镜版本评估工具（Structured Compare）
- [ ] 考虑 MCP Server 集成到我们的 AI 工具链
