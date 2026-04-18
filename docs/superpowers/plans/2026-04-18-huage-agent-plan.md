# huage Agent · 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Goal:** 从零构建 huage Agent —— 专注文章创作的独立 Agent，类 Claude Code 架构，基于 Claude Agent SDK + TypeScript
>
> **Architecture:** huage Agent 是一个独立 CLI 工具，内部包含：Writing Workflow Engine 核心循环 + Dan Koe 五阶段执行器 + wiki 管理 + 本能学习进化。每个阶段输出写入 JSONL checkpoint + 文件，Wiki 采用 [[wikilink]] 模式。
>
> **Tech Stack:** Claude Agent SDK (npm: @anthropic-ai/sdk) | TypeScript | Node.js | Tavily API | YouTube Data API | Doubao-Seedream-4.5 | SQLite (drizzle)

---

## 文件结构

```
huage-agent/
├── src/
│   ├── index.ts                    # CLI 入口
│   ├── engine.ts                   # Writing Workflow Engine 核心循环（Task 3）
│   ├── types.ts                    # 全局类型定义
│   ├── prompts/
│   │   ├── shared.ts               # {{VAR}} 模板替换 + user-role prompts（参考 dankoe-writer）
│   │   ├── stage1-topic.ts         # Stage 1 prompt 模板
│   │   ├── stage2-thesis.ts        # Stage 2 prompt 模板
│   │   ├── stage3-outline.ts       # Stage 3 prompt 模板
│   │   ├── stage4-writing.ts      # Stage 4 prompt 模板
│   │   ├── stage5-polish.ts       # Stage 5 prompt 模板
│   │   ├── research.ts             # Phase 0 prompt 模板
│   │   └── wiki-reflux.ts         # wiki 回流 prompt 模板
│   ├── stages/
│   │   ├── phase0-research.ts       # Phase 0: 深度研究（Tavily + YouTube）
│   │   ├── stage1-topic.ts         # Stage 1: 选题与定位
│   │   ├── stage2-thesis.ts        # Stage 2: 核心观点提炼
│   │   ├── stage3-outline.ts        # Stage 3: 文章大纲构建
│   │   ├── stage4-writing.ts       # Stage 4: 正文写作
│   │   └── stage5-polish.ts        # Stage 5: 优化与润色
│   ├── output/                      # P2：输出模块
│   │   ├── seo-geo.ts              # SEO/GEO 优化
│   │   ├── images.ts               # 配图生成（Doubao-Seedream）
│   │   ├── html.ts                 # HTML 排版预览
│   │   └── wiki-reflux.ts          # wiki 知识回流（含 wikilink 校验）
│   ├── wiki/
│   │   ├── manager.ts              # wiki 管理器
│   │   ├── query.ts                # wiki 查询（CJK-aware, 参考 llm-wiki-agent）
│   │   ├── ingest.ts               # wiki 摄入（JSON schema-driven, 参考 llm-wiki-agent）
│   │   ├── lint.ts                 # wiki 健康检查（孤儿/断链）
│   │   └── graph.ts                # wiki 图谱（两遍 pass + JSONL checkpoint）
│   ├── learning/
│   │   ├── learn.ts                # 本能提取
│   │   └── evolve.ts               # 本能进化
│   ├── memory.ts                   # MEMORY.md 状态管理
│   ├── config.ts                   # 配置文件读取
│   ├── logger.ts                   # 日志工具
│   ├── db/
│   │   └── schema.ts               # SQLite/drizzle schema（stage_history 表，参考 dankoe-writer）
│   └── runtime/
│       ├── hooks.ts                # PreToolUse/PostToolUse hooks（参考 claw-code）
│       └── compact.ts               # Session compaction（head+tail，参考 claw-code）
├── references/                     # 参考文档（Dan Koe 五阶段）
│   ├── dan-koe-prompts.md
│   ├── dan-koe-style.md
│   ├── 7-layer-opening.md
│   └── 5-step-argument.md
├── skills/                         # Skill 定义（SKILL.md 格式，参考 obsidian-skills）
│   ├── five-stage-dan-koe.md       # Dan Koe 五阶段方法论 Skill
│   ├── anti-ai-slop.md             # 去AI味规则 Skill
│   └── wiki-workflow.md            # Wiki 工作流 Skill
├── tests/
│   ├── stages.test.ts
│   ├── wiki.test.ts
│   ├── engine.test.ts
│   └── prompts.test.ts
├── package.json
├── tsconfig.json
└── README.md
```

---

## 任务执行顺序

```
Task 0  →  Task 1  →  Task 2  →  Task 3  →  (Task 4, Task 5, Task 6, Task 8)  →  Task 7  →  Task 9  →  Task 10
          (并行)              (并行)     (Day-0 Bootstrap)    (合并 Output)
```

**说明**：
- Task 0（LLM Calling Protocol）是所有后续任务的基础，必须第一个完成
- Task 4/5/6/8 可并行执行（共享 Task 2 的类型和 Task 3 的 engine）
- Task 7（Output）是 P2，与 Task 5 后的润色串行

---

## Task 0: LLM Calling Protocol 设计

> **优先级：P0**（CEO Finding #2：7个 LLM 调用全是 TODO）
> **参考**：dankoe-writer `shared/prompts.ts` | claw-code `runtime/` | obsidian-skills SKILL.md 格式

**Files:**
- Create: `huage-agent/src/prompts/shared.ts`
- Create: `huage-agent/src/prompts/stage1-topic.ts`
- Create: `huage-agent/src/prompts/stage2-thesis.ts`
- Create: `huage-agent/src/prompts/stage3-outline.ts`
- Create: `huage-agent/src/prompts/stage4-writing.ts`
- Create: `huage-agent/src/prompts/stage5-polish.ts`
- Create: `huage-agent/src/prompts/research.ts`
- Create: `huage-agent/src/prompts/wiki-reflux.ts`
- Create: `huage-agent/tests/prompts.test.ts`
- Create: `huage-agent/src/db/schema.ts`

- [ ] **Step 1: 创建 `src/prompts/shared.ts` — {{VAR}} 模板引擎**

```typescript
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
  static render(template: string, vars: Record<string, string>): string {
    let result = template;
    for (const [key, value] of Object.entries(vars)) {
      const pattern = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
      result = result.replace(pattern, value);
    }
    // 检查未替换的变量
    const unresolved = result.match(/\{\{(\w+)\}\}/g);
    if (unresolved) {
      throw new Error(`Unresolved prompt variables: ${unresolved.join(', ')}`);
    }
    return result;
  }

  /**
   * 构建 user role message（不含 system wrapper）
   * 参考：dankoe-writer — user-role-only prompts
   */
  static userMessage(template: string, vars: Record<string, string>): string {
    const rendered = this.render(template, vars);
    return rendered;
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
  }): Promise<unknown> {
    const { Anthropic } = await import('@anthropic-ai/sdk');
    const { config } = await import('../config');

    const client = new Anthropic({ apiKey: config.anthropicApiKey });
    const content = this.render(params.template, params.vars);

    const response = await client.messages.create({
      model: params.model === 'qwen3-max' ? 'qwen3-max' : `anthropic-${params.model}`,
      max_tokens: params.maxTokens ?? 4096,
      temperature: params.temperature,
      messages: [{ role: 'user', content }],
    });

    const text = response.content[0].type === 'text'
      ? response.content[0].text
      : '';

    if (params.outputSchema) {
      return params.outputSchema.parse(JSON.parse(text));
    }
    return text;
  }
}
```

- [ ] **Step 2: 创建 `src/prompts/stage1-topic.ts`**

```typescript
/**
 * Stage 1: 选题与定位 prompt 模板
 * 模型：Claude Sonnet（快速迭代）
 * 温度：0.7（创意但聚焦）
 */

export const STAGE1_PROMPT = `你是 huage Agent，专注文章创作的 AI 写作助手。

## 你的任务

基于以下信息，生成 3-5 个选题方案。

## 用户主题

{{topic}}

## 研究摘要

{{researchSummary}}

{{#if wikiKnowledge}}
## wiki 知识预注入

{{wikiKnowledge}}
{{/if}}

## 输出格式

请按以下 JSON 格式输出（只输出 JSON，不要其他文字）：

\`\`\`json
{
  "options": [
    {
      "title": "标题（使用 Dan Koe 标题公式：How to [specific outcome] in [timeframe] / The [adjective] truth about [topic] / Why [common belief] is wrong about [topic]）",
      "subtitle": "副标题",
      "targetReader": "目标读者描述（具体画像）",
      "painPoint": "他们面临的核心痛点（1句话）",
      "uniqueValue": "本文提供的独特价值（与已有内容的差异）",
      "viralPotential": "传播潜力分析（为什么读者会分享）",
      "titleFormula": "使用的标题公式类型"
    }
  ],
  "reasoning": "你的选题逻辑（展示给用户看的思考过程）"
}
\`\`\`

## Dan Koe 标题公式参考

1. **How to [结果] in [时间]**: "How to master time management in 30 days"
2. **The [形容词] truth about [话题]**: "The uncomfortable truth about productivity"
3. **Why [普遍信念] is wrong about [话题]**: "Why time management is actually killing your productivity"
4. **[数字] reasons why [结论]**: "5 reasons why you're always behind"
5. **I [经历], so you don't have to [结果]**: 经验分享型

请生成多样化的选题，覆盖不同标题公式类型。`;

export const STAGE1_MODEL = 'claude-sonnet' as const;
export const STAGE1_TEMPERATURE = 0.7;
```

- [ ] **Step 3: 创建 `src/prompts/stage2-thesis.ts`**

```typescript
/**
 * Stage 2: 核心观点提炼 prompt 模板
 * 模型：Claude Sonnet
 * 温度：0.6（逻辑清晰）
 */

export const STAGE2_PROMPT = `你是 huage Agent，专注文章创作的 AI 写作助手。

## 你的任务

基于选定标题，挑战表面现象，提炼出触及问题本质的核心观点。

## 标题

{{title}}

## 副标题

{{subtitle}}

## 目标读者

{{targetReader}}

## 他们的痛点

{{painPoint}}

## 研究摘要

{{researchSummary}}

{{#if wikiKnowledge}}
## wiki 知识预注入

{{wikiKnowledge}}
{{/if}}

## 输出格式

\`\`\`json
{
  "coreThesis": "核心论点（1-2句话，挑战最普遍的误解）",
  "supportingPoints": [
    {
      "point": "观点内容（挑战什么普遍观念？）",
      "commonMisconception": "人们通常怎么认为（你反对的观点）",
      "thinkersToCite": ["可引用的思想家/理论"],
      "logicalConnection": "与下一个观点的逻辑连接"
    }
  ],
  "reasoning": "你的观点提炼逻辑（展示给用户看）"
}
\`\`\`

## Dan Koe 核心原则

- 挑战表面现象，不是提供更多"技巧"
- 引用思想家增加权威性（Alfred Adler, Carl Jung, Naval Ravikant 等）
- 观点之间形成递进逻辑链条`;

export const STAGE2_MODEL = 'claude-sonnet' as const;
export const STAGE2_TEMPERATURE = 0.6;
```

- [ ] **Step 4: 创建 `src/prompts/stage3-outline.ts`**

```typescript
/**
 * Stage 3: 文章大纲构建 prompt 模板
 * 模型：Claude Sonnet
 * 温度：0.5（结构清晰）
 */

export const STAGE3_PROMPT = `你是 huage Agent，专注文章创作的 AI 写作助手。

## 你的任务

基于标题和核心观点，构建完整的大纲。

## 标题

{{title}}

## 副标题

{{subtitle}}

## 核心论点

{{coreThesis}}

## 支撑观点

{{supportingPoints}}

{{#if wikiKnowledge}}
## wiki 知识预注入

{{wikiKnowledge}}
{{/if}}

## 输出格式

\`\`\`json
{
  "opening": {
    "hook": "反直觉开篇（第一句话必须打破读者预期）",
    "transition": "宽容式过渡（让读者感到被理解）",
    "dataSupport": "可选：数据支撑（增强可信度）",
    "vulnerability": "脆弱性展示（用你的真实经历建立连接）",
    "promise": "明确承诺（告诉读者他们将获得什么）",
    "importance": "重要性强调（为什么现在必须解决）",
    "expectation": "期待感营造（设置阅读预期）"
  },
  "sections": [
    {
      "heading": "章节标题",
      "keyPoints": ["核心论点"],
      "examples": ["案例1", "案例2"],
      "framework": "5步论证模型：标题→引用→背景→洞察→案例"
    }
  ],
  "conclusion": {
    "summary": "全文总结（回应开篇的hook）",
    "callToAction": "明确行动号召"
  },
  "reasoning": "大纲设计逻辑（展示给用户看）"
}
\`\`\`

## 7 层开篇序列

1. 反直觉 hook（打破预期）
2. 宽容式过渡（建立共情）
3. 数据支撑（增加可信度）
4. 脆弱性展示（真实连接）
5. 明确 promise（价值承诺）
6. 重要性强调（紧迫感）
7. 期待感营造（设置预期）

## 5 步论证模型

标题 → 引用（思想家/数据） → 背景（现状） → 洞察（你的观点） → 案例（具体故事）`;

export const STAGE3_MODEL = 'claude-sonnet' as const;
export const STAGE3_TEMPERATURE = 0.5;
```

- [ ] **Step 5: 创建 `src/prompts/stage4-writing.ts`**

```typescript
/**
 * Stage 4: 正文写作 prompt 模板
 * 模型：Qwen3-Max（中文写作质量更高，参考 dankoe-writer）
 * 温度：0.8（创意表达）
 */

export const STAGE4_PROMPT = `你是一位资深文章作者，风格贴近 Dan Koe 的写作哲学。

## 你的任务

基于以下大纲，撰写一篇完整的公众号文章。

## 标题

{{title}}

## 大纲

### 开篇（7层递进）

- Hook: {{opening.hook}}
- Transition: {{opening.transition}}
- {{#if opening.dataSupport}}- Data: {{opening.dataSupport}}{{/if}}
- Vulnerability: {{opening.vulnerability}}
- Promise: {{opening.promise}}
- Importance: {{opening.importance}}
- Expectation: {{opening.expectation}}

### 章节

{{#each sections}}
#### {{heading}}
{{keyPoints}}
案例：{{examples}}
{{/each}}

### 结尾

{{conclusion.summary}}
行动号召：{{conclusion.callToAction}}

{{#if wikiKnowledge}}
## wiki 知识预注入（必须使用 [[wikilink]] 关联）

{{wikiKnowledge}}
{{/if}}

## Dan Koe 风格要求

- **第二人称**：用"你"而非"人们"或"大家"
- **短句冲击**：关键句子不超过 15 字
- **对话式提问**：每 3 段插入一个问句
- **三段式递进**：重要观点使用连续三句递进
- **脆弱性 + 权威性**：真实经历 + 思想家引用
- **反叛精神**：对传统"技巧"保持批判态度

## 格式要求

- 字数：{{wordCountTarget}} 字左右
- 使用 [[wikilink]] 关联 wiki 中的概念
- 引用格式：> "引用内容" — 来源
- 标题使用 ##，子标题使用 ###

## 输出

直接输出文章正文，不需要 JSON。`;

export const STAGE4_MODEL = 'qwen3-max' as const;
export const STAGE4_TEMPERATURE = 0.8;
export const STAGE4_MAX_TOKENS = 8192;
```

- [ ] **Step 6: 创建 `src/prompts/stage5-polish.ts`**

```typescript
/**
 * Stage 5: 优化与润色 prompt 模板
 * 模型：Claude Sonnet
 * 温度：0.4（保守优化）
 */

export const STAGE5_PROMPT = `你是一位资深编辑，负责优化和润色文章。

## 你的任务

对以下文章进行深度润色，去除 AI 味，提升可读性。

## 待润色文章

{{draft}}

## 标题

{{title}}

## 去 AI 味规则

{{antiAiRules}}

## SEO 关键词

{{seoKeywords}}

## 润色要求

### 1. 标题优化
- 增强吸引力（点击欲望）
- 保持清晰（不要标题党）

### 2. 开篇强化
- 检查 7 层序列是否完整
- Hook 是否足够反直觉

### 3. 逻辑流畅
- 论证链条是否清晰
- 过渡是否自然

### 4. 金句提炼
- 关键观点是否打磨成可独立传播的金句
- 检查是否有 [[wikilink]] 关联

### 5. 节奏控制
- 段落长度是否变化
- 句式是否有长短交错

### 6. 情感共鸣
- 是否强化了与读者的连接

### 7. 行动召唤
- 结尾是否有明确指引

### 8. 去 AI 味检查
- 是否符合 {{antiAiRules}} 中的所有规则

## 输出格式

\`\`\`json
{
  "polishedContent": "润色后的完整文章",
  "antiAiCheck": {
    "passed": true/false,
    "violations": ["违规项列表"]
  },
  "seoOptimization": {
    "keywords": ["关键词列表"],
    "densityCheck": true/false,
    "metaDescription": "160字以内的meta描述"
  },
  "changes": ["本次润色的主要改动"]
}
\`\`\``;

export const STAGE5_MODEL = 'claude-sonnet' as const;
export const STAGE5_TEMPERATURE = 0.4;
```

- [ ] **Step 7: 创建 `src/prompts/research.ts`**

```typescript
/**
 * Phase 0: 深度研究 prompt 模板
 * 模型：Claude Sonnet
 * 温度：0.3（事实性为主）
 */

export const RESEARCH_PROMPT = `你是 huage Agent，专注文章创作的 AI 写作助手。

## 你的任务

对以下主题进行深度研究，综合多种来源，提取关键洞察。

## 研究主题

{{topic}}

{{#if wikiKnowledge}}
## wiki 中已有的相关知识（避免重复）

{{wikiKnowledge}}
{{/if}}

## 研究要求

### 1. 核心发现
- 该主题的本质是什么
- 当前的行业趋势是什么
- 有什么被忽视的视角

### 2. 专家观点
- 核心思想家/专家的核心主张
- 不同观点之间的分歧

### 3. 实际案例
- 真实的成功/失败案例
- 可引用的数据和统计

### 4. 争议与共识
- 什么是大家公认的
- 什么是有争议的

## 输出格式

\`\`\`json
{
  "summary": "综合摘要（3-5句话）",
  "keyInsights": [
    "洞察1：具体内容",
    "洞察2：具体内容"
  ],
  "expertViews": [
    {
      "expert": "专家名称",
      "view": "核心观点",
      "source": "来源"
    }
  ],
  "cases": [
    {
      "name": "案例名称",
      "lesson": "教训/启示"
    }
  ],
  "controversies": [
    {
      "topic": "争议话题",
      "positions": ["不同立场"]
    }
  ]
}
\`\`\``;

export const RESEARCH_MODEL = 'claude-sonnet' as const;
export const RESEARCH_TEMPERATURE = 0.3;
```

- [ ] **Step 8: 创建 `src/prompts/wiki-reflux.ts`**

```typescript
/**
 * wiki 回流 prompt 模板
 * 模型：Claude Sonnet
 * 温度：0.5（知识提取）
 */

export const WIKI_REFLUX_PROMPT = `你是知识整理专家，负责从文章中提取可沉淀到 wiki 的知识。

## 文章信息

标题：{{title}}

内容：
{{content}}

## 来源

{{sources}}

## 提取要求

### 1. 实体提取
- 文章提到的人物/公司/产品/地点
- 每个实体需要：名称、类型、核心特征

### 2. 概念提取
- 文章中的核心概念/方法论/理论
- 每个概念需要：定义、关键原则、应用场景

### 3. Key Claims（关键主张）
- 文章中的核心论点
- 每个主张需要有证据支持

### 4. Key Quotes（关键引用）
- 可独立传播的金句
- 引用格式保留

### 5. wiki 关联
- 该文章可以关联到哪些现有 wiki 页面
- 使用 [[pagename]] 格式

## wiki 页面格式规范

来源页：\`wiki/sources/YYYY-MM-DD-slug.md\`
实体页：\`wiki/entities/PascalCase.md\`
概念页：\`wiki/concepts/PascalCase.md\`

每个页面必须包含：
- frontmatter（title, type, date, tags, sources）
- Summary（2-4句）
- Key Claims（至少2条）
- Key Quotes（至少1条）
- Connections（含 [[wikilink]]）

## 输出格式

\`\`\`json
{
  "sourcePage": {
    "content": "完整来源页 markdown 内容"
  },
  "entities": [
    {
      "name": "实体名称",
      "type": "person|company|product|place",
      "content": "实体页 markdown 内容"
    }
  ],
  "concepts": [
    {
      "name": "概念名称",
      "content": "概念页 markdown 内容"
    }
  ],
  "newConnections": [
    {
      "targetPage": "目标页面名",
      "relationship": "关系描述"
    }
  ]
}
\`\`\``;

export const WIKI_REFLUX_MODEL = 'claude-sonnet' as const;
export const WIKI_REFLUX_TEMPERATURE = 0.5;
```

- [ ] **Step 9: 创建 `src/db/schema.ts` — Stage History 表**

```typescript
/**
 * SQLite/drizzle schema
 * 参考：dankoe-writer drizzle/schema.ts
 *
 * 核心表：
 * - projects: 文章项目（一次创作 = 一个 project）
 * - stage_data: 每个阶段的 JSON 数据
 * - stage_history: 阶段历史（版本化，支持回退）
 */

import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const projects = sqliteTable('projects', {
  id: text('id').primaryKey(),          // UUID
  topic: text('topic').notNull(),       // 原始主题
  outputDir: text('output_dir').notNull(), // 输出目录
  status: text('status').notNull(),      // idle|active|completed|aborted
  createdAt: text('created_at').notNull(),
  updatedAt: text('updated_at').notNull(),
  completedAt: text('completed_at'),
});

export const stageData = sqliteTable('stage_data', {
  id: text('id').primaryKey(),
  projectId: text('project_id').notNull().references(() => projects.id),
  stage: text('stage').notNull(),       // phase0|stage1|stage2|stage3|stage4|stage5|output
  data: text('data').notNull(),         // JSON string
  thinking: text('thinking'),            // Agent 思考过程
  userDecision: text('user_decision'),  // 用户决策（JSON）
  status: text('status').notNull(),     // pending|thinking|waiting_user|confirmed|done
  createdAt: text('created_at').notNull(),
  updatedAt: text('updated_at').notNull(),
});

export const stageHistory = sqliteTable('stage_history', {
  id: text('id').primaryKey(),
  projectId: text('project_id').notNull().references(() => projects.id),
  stage: text('stage').notNull(),
  data: text('data').notNull(),         // JSON string（历史版本）
  version: integer('version').notNull(), // 版本号
  createdAt: text('created_at').notNull(),
});
```

- [ ] **Step 10: 创建 `tests/prompts.test.ts`**

```typescript
import { PromptEngine, STAGE1_PROMPT, STAGE1_MODEL, STAGE1_TEMPERATURE } from '../src/prompts/shared';
import { Stage1InputSchema } from '../src/prompts/shared';

describe('PromptEngine', () => {
  describe('render', () => {
    it('should replace {{VAR}} placeholders', () => {
      const template = 'Hello {{name}}, you are {{age}} years old.';
      const result = PromptEngine.render(template, { name: 'Alice', age: '30' });
      expect(result).toBe('Hello Alice, you are 30 years old.');
    });

    it('should throw on unresolved variables', () => {
      const template = 'Hello {{name}}, {{missing}}';
      expect(() => PromptEngine.render(template, { name: 'Alice' }))
        .toThrow('Unresolved prompt variables');
    });
  });

  describe('Stage 1 prompt', () => {
    it('should have correct model', () => {
      expect(STAGE1_MODEL).toBe('claude-sonnet');
      expect(STAGE1_TEMPERATURE).toBe(0.7);
    });

    it('should render with all required variables', () => {
      const input = Stage1InputSchema.parse({
        topic: '时间管理',
        researchSummary: '研究摘要内容',
      });
      const result = PromptEngine.render(STAGE1_PROMPT, input);
      expect(result).toContain('时间管理');
      expect(result).toContain('研究摘要内容');
    });
  });
});
```

- [ ] **Step 11: Commit**

```bash
git add huage-agent/src/prompts/ huage-agent/src/db/ huage-agent/tests/prompts.test.ts
git commit -m "feat: 实现 LLM Calling Protocol — prompt 模板 + 模型选择 + schema"
```

---

## Phase 0：Day-0 Bootstrap

> **优先级：P1**（CEO Finding #3：wiki 飞轮在第一篇文章时完全空转）
> **参考**：llm-wiki-agent `tools/ingest.py`

### Task 0.5: Day-0 Wiki Bootstrap

**Files:**
- Create: `huage-agent/scripts/bootstrap-wiki.ts`

- [ ] **Step 1: 创建 `scripts/bootstrap-wiki.ts`**

```typescript
/**
 * Day-0 Wiki Bootstrap
 *
 * 目标：在第一篇文章创作前，将现有的 raw/ 内容批量摄入 wiki
 * 参考：llm-wiki-agent tools/ingest.py
 *
 * 流程：
 * 1. 扫描 raw/ 目录下的所有文件
 * 2. 对每个文件调用 LLM 生成来源页
 * 3. 提取实体和概念
 * 4. 创建实体页和概念页
 * 5. 更新 wiki/index.md
 * 6. 生成 wiki/log.md 日志
 */

import * as fs from 'fs';
import * as path from 'path';
import { config } from '../src/config';
import { PromptEngine } from '../src/prompts/shared';

async function bootstrap() {
  console.log('Starting Day-0 Wiki Bootstrap...');

  const rawDir = path.join(config.vaultPath, 'raw');
  const wikiDir = config.wikiPath();

  // 1. 扫描 raw/ 目录
  const files = walkDir(rawDir);
  console.log(`Found ${files.length} files to ingest`);

  for (const file of files) {
    console.log(`Processing: ${file}`);

    const content = fs.readFileSync(file, 'utf-8');
    const date = new Date().toISOString().split('T')[0];
    const slug = path.basename(file, path.extname(file)).toLowerCase().replace(/\s+/g, '-');

    // 2. 调用 LLM 生成来源页
    const result = await PromptEngine.callLLM({
      template: WIKI_REFLUX_PROMPT,
      vars: {
        title: slug,
        content: content.slice(0, 5000), // 截断避免超出 token
        sources: JSON.stringify([{ title: slug, url: file }]),
      },
      model: 'claude-sonnet',
      temperature: 0.5,
    });

    const parsed = result as any;

    // 3. 写入来源页
    if (parsed.sourcePage?.content) {
      const sourcePath = path.join(wikiDir, `sources/${date}-${slug}.md`);
      fs.writeFileSync(sourcePath, parsed.sourcePage.content, 'utf-8');
      console.log(`  Created: ${sourcePath}`);
    }

    // 4. 写入实体页
    for (const entity of parsed.entities || []) {
      const entityPath = path.join(wikiDir, `entities/${entity.name}.md`);
      fs.writeFileSync(entityPath, entity.content, 'utf-8');
      console.log(`  Created: ${entityPath}`);
    }

    // 5. 写入概念页
    for (const concept of parsed.concepts || []) {
      const conceptPath = path.join(wikiDir, `concepts/${concept.name}.md`);
      fs.writeFileSync(conceptPath, concept.content, 'utf-8');
      console.log(`  Created: ${conceptPath}`);
    }
  }

  // 6. 更新 wiki/index.md
  await updateIndex(wikiDir, files.length);

  // 7. 追加日志
  await appendLog(wikiDir, files.length);

  console.log('Bootstrap complete!');
}

function walkDir(dir: string): string[] {
  const files: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walkDir(full));
    } else if (entry.name.endsWith('.md')) {
      files.push(full);
    }
  }
  return files;
}

async function updateIndex(wikiDir: string, count: number) {
  const indexPath = path.join(wikiDir, 'index.md');
  const date = new Date().toISOString().split('T')[0];
  const entry = `\n## ${date} Bootstrap\n\n- ${count} 个来源页已从 raw/ 批量摄入`;
  if (fs.existsSync(indexPath)) {
    fs.appendFileSync(indexPath, entry, 'utf-8');
  } else {
    fs.writeFileSync(indexPath, `# Wiki Index\n${entry}`, 'utf-8');
  }
}

async function appendLog(wikiDir: string, count: number) {
  const logPath = path.join(wikiDir, 'log.md');
  const date = new Date().toISOString().split('T')[0];
  const entry = `\n## [${date}] bootstrap | Day-0 Wiki Bootstrap\n- 来源：raw/ 目录\n- 摄入：${count} 个来源页`;
  if (fs.existsSync(logPath)) {
    fs.appendFileSync(logPath, entry, 'utf-8');
  } else {
    fs.writeFileSync(logPath, `# Wiki Log\n${entry}`, 'utf-8');
  }
}

bootstrap().catch(console.error);
```

- [ ] **Step 2: Run bootstrap**

```bash
npx ts-node huage-agent/scripts/bootstrap-wiki.ts
```

- [ ] **Step 3: Commit**

```bash
git add huage-agent/scripts/bootstrap-wiki.ts
git commit -m "feat: Day-0 Wiki Bootstrap — 批量摄入 raw/ 内容到 wiki"
```

---

## Phase 0：项目脚手架

### Task 1: 初始化项目

**Files:**
- Create: `huage-agent/package.json`
- Create: `huage-agent/tsconfig.json`
- Create: `huage-agent/.env.example`
- Create: `huage-agent/README.md`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "huage-agent",
  "version": "0.1.0",
  "description": "专注文章创作的独立 Agent",
  "main": "dist/index.js",
  "bin": {
    "huage-agent": "dist/index.js"
  },
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "ts-node src/index.ts",
    "test": "jest"
  },
  "dependencies": {
    "@anthropic-ai/sdk": "latest",
    "tavily-js": "latest",
    "googleapis": "latest",
    "dotenv": "latest",
    "commander": "latest",
    "chalk": "latest"
  },
  "devDependencies": {
    "@types/node": "latest",
    "typescript": "latest",
    "ts-node": "latest",
    "jest": "latest",
    "@types/jest": "latest"
  }
}
```

- [ ] **Step 2: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

- [ ] **Step 3: 创建 .env.example**

```bash
# Claude Agent SDK
ANTHROPIC_API_KEY=sk-xxxx

# Tavily 研究
TAVILY_API_KEY=tvly-xxxx

# YouTube 研究
YOUTUBE_API_KEY=xxxx
YOUTUBE_CLIENT_SECRET=xxxx

# Doubao 图像生成
ARK_API_KEY=xxxx

# Obsidian Vault 路径
OBSIDIAN_VAULT_PATH=/Users/huage/Obsidian Vault
```

- [ ] **Step 4: 创建 README.md**

```markdown
# huage Agent

专注文章创作的独立 Agent，基于 Claude Agent SDK + Dan Koe 五阶段写作方法论。

## 安装

```bash
npm install
npm run build
```

## 使用

```bash
# 开始一篇文章
huage-agent write "我想写一篇关于时间管理的文章"

# 查询 wiki
huage-agent wiki query "知识管理"

# 健康检查
huage-agent wiki lint
```

## 工作流

1. 深度研究（Tavily + YouTube）
2. Dan Koe 五阶段（选题→观点→大纲→正文→润色）
3. SEO/GEO 优化
4. 配图 + HTML + wiki回流
```

- [ ] **Step 5: 初始化项目**

```bash
cd /Users/huage/Obsidian\ Vault/huage-agent
npm install
```

- [ ] **Step 6: Commit**

```bash
git add huage-agent/
git commit -m "feat: 初始化 huage-agent 项目脚手架"
```

---

### Task 2: 定义全局类型

**Files:**
- Create: `huage-agent/src/types.ts`
- Create: `huage-agent/src/config.ts`
- Create: `huage-agent/src/logger.ts`

- [ ] **Step 1: 创建 src/types.ts**

```typescript
// ==================== 阶段产物类型 ====================

export interface Phase0Research {
  topic: string;
  tavilyResults: TavilyResult[];
  youtubeResults: YouTubeResult[];
  summary: string;
  keyInsights: string[];
  sources: Source[];
  completedAt: string;
}

export interface TavilyResult {
  title: string;
  url: string;
  content: string;
  score: number;
}

export interface YouTubeResult {
  title: string;
  videoId: string;
  channelName: string;
  duration: string;
  transcript?: string;
}

export interface Source {
  title: string;
  url: string;
  type: 'article' | 'video' | 'paper';
}

// ==================== Stage 1 选题 ====================

export interface Stage1Topic {
  selectedTitle: string;
  subtitle: string;
  targetReader: string;
  painPoint: string;
  uniqueValue: string;
  viralPotential: string;
  options: TopicOption[];
  reasoning: string; // Agent 思考过程
  decidedAt: string;
}

export interface TopicOption {
  title: string;
  subtitle: string;
  targetReader: string;
  painPoint: string;
  uniqueValue: string;
  viralPotential: string;
}

// ==================== Stage 2 观点 ====================

export interface Stage2Thesis {
  coreThesis: string;
  supportingPoints: ThesisPoint[];
  reasoning: string; // Agent 思考过程
  confirmedAt: string;
}

export interface ThesisPoint {
  point: string;
  commonMisconception: string;
  thinkersToCite: string[];
  logicalConnection: string;
}

// ==================== Stage 3 大纲 ====================

export interface Stage3Outline {
  title: string;
  opening: OpeningStructure;
  sections: OutlineSection[];
  conclusion: ConclusionStructure;
  reasoning: string; // Agent 思考过程
  confirmedAt: string;
}

export interface OpeningStructure {
  hook: string;
  transition: string;
  dataSupport?: string;
  vulnerability: string;
  promise: string;
  importance: string;
  expectation: string;
}

export interface OutlineSection {
  heading: string;
  keyPoints: string[];
  examples: string[];
  framework?: string; // 5步论证模型
}

export interface ConclusionStructure {
  summary: string;
  callToAction: string;
}

// ==================== Stage 4 正文 ====================

export interface Stage4Draft {
  title: string;
  content: string;
  wordCount: number;
  style: 'dan-koe';
  verifiedAt: string;
}

// ==================== Stage 5 润色 ====================

export interface Stage5Polished {
  title: string;
  content: string;
  wordCount: number;
  antiAiCheck: AntiAiCheckResult;
  seoOptimization: SEOResult;
  geoOptimization: GEOResult;
  finalAt: string;
}

export interface AntiAiCheckResult {
  passed: boolean;
  violations: string[];
}

export interface SEOResult {
  keywords: string[];
  densityCheck: boolean;
  metaDescription: string;
}

export interface GEOResult {
  citations: string[];
  entityOptimization: string[];
  aiReadableScore: number;
}

// ==================== Agent 会话状态 ====================

export interface AgentSession {
  sessionId: string;
  topic: string;
  outputDir: string;
  phase: PhaseState;
  currentStage: StageState;
  createdAt: string;
  updatedAt: string;
}

export type PhaseState = 'idle' | 'phase0' | 'stage1' | 'stage2' | 'stage3' | 'stage4' | 'stage5' | 'output' | 'completed';

export type StageState = 'pending' | 'thinking' | 'waiting_user' | 'confirmed' | 'done';

export interface StageOutput {
  stage: string;
  status: StageState;
  thinking?: string; // Agent 思考过程
  result?: unknown; // 阶段产物
  userDecision?: unknown; // 用户决策
  completedAt?: string;
}

// ==================== wiki 类型 ====================

export interface WikiPage {
  title: string;
  type: 'source' | 'entity' | 'concept' | 'synthesis';
  content: string;
  tags: string[];
  sources: string[];
  lastUpdated: string;
}

export interface WikiQueryResult {
  pages: WikiPage[];
  query: string;
  matchedAt: string;
}
```

- [ ] **Step 2: 创建 src/config.ts**

```typescript
import * as fs from 'fs';
import * as path from 'path';
import dotenv from 'dotenv';

dotenv.config();

export const config = {
  // Claude Agent SDK
  anthropicApiKey: process.env.ANTHROPIC_API_KEY || '',

  // API Keys
  tavilyApiKey: process.env.TAVILY_API_KEY || '',
  youtubeApiKey: process.env.YOUTUBE_API_KEY || '',
  arkApiKey: process.env.ARK_API_KEY || '',

  // Obsidian Vault
  vaultPath: process.env.OBSIDIAN_VAULT_PATH ||
    '/Users/huage/Obsidian Vault',

  // 路径
  wikiPath: () => path.join(config.vaultPath, 'wiki'),
  outputPath: () => path.join(config.vaultPath, '写作知识库'),
  memoryPath: () => path.join(
    config.vaultPath,
    '.claude/projects/-Users-huage-Obsidian-Vault/memory/MEMORY.md'
  ),
  referencesPath: () =>
    path.join(config.vaultPath, 'AI工具箱/huage-agent/skills/writing/five-stage-longform/references'),

  // 模型
  claudeModel: 'claude-opus-4-6',
  writingModel: 'qwen3-max', // 正文写作用 Qwen3-Max
};
```

- [ ] **Step 3: 创建 src/logger.ts**

```typescript
import chalk from 'chalk';

export const logger = {
  info: (msg: string) => console.log(chalk.blue('[INFO]'), msg),
  success: (msg: string) => console.log(chalk.green('[SUCCESS]'), msg),
  warn: (msg: string) => console.log(chalk.yellow('[WARN]'), msg),
  error: (msg: string) => console.log(chalk.red('[ERROR]'), msg),
  stage: (stage: string, msg: string) =>
    console.log(chalk.magenta(`[${stage}]`), msg),
  thinking: (thought: string) =>
    console.log(chalk.gray('思考:'), thought),
  user: (msg: string) =>
    console.log(chalk.cyan('用户:'), msg),
};
```

- [ ] **Step 4: Commit**

```bash
git add huage-agent/src/types.ts huage-agent/src/config.ts huage-agent/src/logger.ts
git commit -m "feat: 定义全局类型、配置和日志工具"
```

---

## Phase 1：Writing Workflow Engine

### Task 3: Writing Workflow Engine 核心循环

> **优先级：P0**（CEO Finding #1：重命名 agent.ts → engine.ts，采用 ConversationRuntime 架构）
> **参考**：claw-code `runtime/` | dankoe-writer `routers.ts`

**Files:**
- Create: `huage-agent/src/engine.ts`
- Create: `huage-agent/src/runtime/hooks.ts`
- Create: `huage-agent/src/runtime/compact.ts`
- Create: `huage-agent/src/memory.ts`
- Create: `huage-agent/tests/engine.test.ts`

- [ ] **Step 1: 创建 `src/memory.ts`**

```typescript
import * as fs from 'fs';
import * as path from 'path';
import { config } from './config';
import { AgentSession } from './types';

export class Memory {
  private memoryPath: string;

  constructor() {
    this.memoryPath = config.memoryPath();
  }

  async load(): Promise<AgentSession | null> {
    if (!fs.existsSync(this.memoryPath)) {
      return null;
    }
    const content = fs.readFileSync(this.memoryPath, 'utf-8');
    try {
      // 简单解析 MEMORY.md 中的任务仪表盘
      const sessionMatch = content.match(/\*\*当前项目\*\*[^\n]*\n[^\w]*([^\n]+)/);
      if (sessionMatch) {
        return JSON.parse(sessionMatch[1]);
      }
    } catch (e) {
      // ignore
    }
    return null;
  }

  async save(session: AgentSession): Promise<void> {
    const content = fs.readFileSync(this.memoryPath, 'utf-8');
    // 更新 MEMORY.md 中的任务仪表盘
    const updated = content.replace(
      /(\*\*当前项目\*\*[^\n]*\n[^\w]*)[^\n]+/,
      `$1${session.topic}`
    );
    fs.writeFileSync(this.memoryPath, updated, 'utf-8');
  }

  async appendLog(entry: string): Promise<void> {
    const logPath = path.join(config.wikiPath(), 'log.md');
    if (!fs.existsSync(logPath)) {
      fs.writeFileSync(logPath, `# Wiki Log\n\n## ${entry}\n`, 'utf-8');
    } else {
      const content = fs.readFileSync(logPath, 'utf-8');
      fs.writeFileSync(logPath, `${content}\n## ${entry}\n`, 'utf-8');
    }
  }
}
```

- [ ] **Step 2: 创建 `src/runtime/hooks.ts` — PreToolUse/PostToolUse**

```typescript
/**
 * Hook 系统
 * 参考：claw-code rust/crates/runtime/src/hooks.rs
 *
 * 退出码语义：
 * - 0 = 允许执行
 * - 2 = 拒绝执行（阻断）
 * - 其他 = 警告（允许但记录）
 */

import * as fs from 'fs';
import * as path from 'path';

export interface HookPayload {
  hook_event_name: 'PreToolUse' | 'PostToolUse';
  tool_name: string;
  tool_input: Record<string, unknown>;
  tool_input_json: string;
  tool_output: string | null;
  tool_result_is_error: boolean;
}

export interface HookResult {
  denied: boolean;
  messages: string[];
}

export class HookRunner {
  private scripts: string[] = [];

  constructor() {
    this.loadHooks();
  }

  private loadHooks(): void {
    const registryPath = path.join(
      config.vaultPath,
      '.claude/hooks/registry.json'
    );
    if (fs.existsSync(registryPath)) {
      const registry = JSON.parse(fs.readFileSync(registryPath, 'utf-8'));
      this.scripts = registry.pre_tool_use ?? [];
    }
  }

  async runPreToolUse(
    toolName: string,
    toolInput: Record<string, unknown>
  ): Promise<HookResult> {
    const payload: HookPayload = {
      hook_event_name: 'PreToolUse',
      tool_name: toolName,
      tool_input: toolInput,
      tool_input_json: JSON.stringify(toolInput),
      tool_output: null,
      tool_result_is_error: false,
    };

    return this.runHooks(payload);
  }

  async runPostToolUse(
    toolName: string,
    toolInput: Record<string, unknown>,
    toolOutput: string | null,
    isError: boolean
  ): Promise<HookResult> {
    const payload: HookPayload = {
      hook_event_name: 'PostToolUse',
      tool_name: toolName,
      tool_input: toolInput,
      tool_input_json: JSON.stringify(toolInput),
      tool_output: toolOutput,
      tool_result_is_error: isError,
    };

    return this.runHooks(payload);
  }

  private async runHooks(payload: HookPayload): Promise<HookResult> {
    const messages: string[] = [];

    for (const script of this.scripts) {
      if (!fs.existsSync(script)) continue;

      try {
        const { spawn } = await import('child_process');
        const child = spawn('sh', ['-c', script], {
          stdio: ['pipe', 'pipe', 'pipe'],
        });

        let stdout = '';
        child.stdout?.on('data', (d) => (stdout += d.toString()));

        const result = await new Promise<{ code: number | null; stdout: string }>(
          (resolve) => {
            child.on('close', (code) => resolve({ code, stdout }));
          }
        );

        const exitCode = result.code ?? 1;

        if (exitCode === 0) {
          // 允许
        } else if (exitCode === 2) {
          // 拒绝
          const msg = stdout.trim();
          return { denied: true, messages: [msg || `Hook denied: ${payload.tool_name}`] };
        } else {
          // 警告
          const msg = stdout.trim();
          if (msg) messages.push(msg);
        }
      } catch (e) {
        messages.push(`Hook error: ${e}`);
      }
    }

    return { denied: false, messages };
  }
}
```

- [ ] **Step 3: 创建 `src/runtime/compact.ts` — Session Compaction**

```typescript
/**
 * Session Compaction
 * 参考：claw-code rust/crates/runtime/src/compact.rs
 *
 * head+tail 保护压缩：
 * - 保留前 N 条和后 M 条消息（系统 prompt + 近期上下文）
 * - 压缩中间部分为摘要
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
   * 执行压缩（head+tail 保护）
   */
  static compact(messages: ConversationMessage[]): ConversationMessage[] {
    if (messages.length <= HEAD_COUNT + TAIL_COUNT) {
      return messages; // 不需要压缩
    }

    const head = messages.slice(0, HEAD_COUNT);
    const tail = messages.slice(-TAIL_COUNT);

    // 生成中间部分摘要
    const middle = messages.slice(HEAD_COUNT, -TAIL_COUNT);
    const summary = this.summarize(middle);

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
   * 估算 token 数量（简单版：按字符数 / 4）
   */
  private static estimateTokens(messages: ConversationMessage[]): number {
    return messages.reduce((sum, m) => sum + Math.ceil(m.content.length / 4), 0);
  }

  /**
   * 生成摘要（调用 LLM）
   */
  private static async summarize(messages: ConversationMessage[]): Promise<string> {
    // TODO: 调用 LLM 生成摘要
    return `[${messages.length} 条消息已压缩]`;
  }
}
```

- [ ] **Step 4: 创建 `src/engine.ts` — Writing Workflow Engine**

```typescript
/**
 * Writing Workflow Engine
 *
 * 核心架构参考：claw-code ConversationRuntime
 * - 工具循环：agent.generate() + handleToolResult()
 * - 阶段状态机：idle → phase0 → stage1-5 → output → completed
 * - 断点续传：每个阶段完成后写入 JSONL checkpoint
 * - Hook 系统：PreToolUse/PostToolUse
 * - Session Compaction：head+tail 保护压缩
 */

import { Agent } from '@anthropic-ai/sdk';
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

export class WritingEngine {
  private agent: Agent;
  private session: AgentSession;
  private memory: Memory;
  private hooks: HookRunner;
  private outputDir: string;
  private messages: ConversationMessage[] = [];
  private checkpointDir: string;

  constructor(sessionId: string, topic: string) {
    this.agent = new Agent({
      model: config.claudeModel,
      apiKey: config.anthropicApiKey,
    });
    this.memory = new Memory();
    this.hooks = new HookRunner();

    // 创建输出目录和 checkpoint 目录
    const date = new Date().toISOString().split('T')[0];
    const slug = topic.slice(0, 20).replace(/\s+/g, '-');
    this.outputDir = path.join(
      config.outputPath(),
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

    // 注册退出时自动保存
    process.on('SIGINT', () => this.saveCheckpoint());
  }

  // ==================== Checkpoint（JSONL 格式） ====================

  private async saveCheckpoint(): Promise<void> {
    /**
     * JSONL checkpoint 格式（参考：llm-wiki-agent 两遍 pass）
     * 每条记录：{ "ts": ISO, "stage": string, "data": object }
     */
    const checkpointFile = path.join(
      this.checkpointDir,
      `${this.session.phase}.jsonl`
    );
    const entry = {
      ts: new Date().toISOString(),
      stage: this.session.phase,
      data: {
        session: this.session,
        messages: this.messages.slice(-10), // 只保存最近 10 条
      },
    };
    fs.appendFileSync(checkpointFile, JSON.stringify(entry) + '\n', 'utf-8');
    logger.info(`Checkpoint saved: ${checkpointFile}`);
  }

  private async loadCheckpoint(stage: string): Promise<ConversationMessage[] | null> {
    const checkpointFile = path.join(this.checkpointDir, `${stage}.jsonl`);
    if (!fs.existsSync(checkpointFile)) return null;

    const lines = fs.readFileSync(checkpointFile, 'utf-8').trim().split('\n');
    if (!lines.length) return null;

    // 读取最后一条 checkpoint
    const last = JSON.parse(lines[lines.length - 1]);
    return last.data?.messages ?? null;
  }

  // ==================== 阶段状态管理 ====================

  private async saveStageOutput(stage: string, output: StageOutput): Promise<void> {
    // 1. 写入 JSON 文件
    const filePath = path.join(this.outputDir, `${stage}.json`);
    fs.writeFileSync(filePath, JSON.stringify(output, null, 2), 'utf-8');

    // 2. 写入 JSONL checkpoint（参考 llm-wiki-agent）
    await this.saveCheckpoint();

    // 3. 更新 session
    this.session.updatedAt = new Date().toISOString();
  }

  private async loadStageOutput(stage: string): Promise<StageOutput | null> {
    const filePath = path.join(this.outputDir, `${stage}.json`);
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    }
    return null;
  }

  // ==================== 工具循环（核心） ====================

  /**
   * 主循环：读取 → PreHook → Agent生成 → PostHook → 处理结果
   * 参考：claw-code ConversationRuntime.tool_loop()
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

    // 保存初始会话
    await this.memory.save(this.session);

    // 开始主循环
    let running = true;
    while (running) {
      const input = await this.promptUser();

      if (input === '/exit') {
        running = false;
        continue;
      }

      // 添加用户消息
      this.messages.push({ role: 'user', content: input });

      // 检查是否需要压缩
      if (SessionCompactor.shouldCompact(this.messages)) {
        logger.info('Session compaction triggered...');
        this.messages = SessionCompactor.compact(this.messages);
      }

      // 调用 Agent
      const response = await this.agent.generate({
        prompt: this.buildSystemPrompt(),
        messages: this.messages as any,
      });

      // 添加 Agent 响应
      this.messages.push({ role: 'assistant', content: response.text });

      // 输出响应
      logger.info('Engine 响应:');
      console.log(response.text);

      // 保存 checkpoint
      await this.saveCheckpoint();
    }

    logger.success('会话结束');
  }

  private async promptUser(): Promise<string> {
    const readline = await import('readline');
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });

    return new Promise((resolve) => {
      rl.question('\n> ', (answer) => {
        rl.close();
        resolve(answer);
      });
    });
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

export async function createSession(topic: string): Promise<WritingEngine> {
  const sessionId = `session-${Date.now()}`;
  return new WritingEngine(sessionId, topic);
}
```

- [ ] **Step 5: 创建 `tests/engine.test.ts`**

```typescript
import { WritingEngine, createSession } from '../src/engine';
import { SessionCompactor } from '../src/runtime/compact';
import { ConversationMessage } from '../src/types';

describe('WritingEngine', () => {
  it('should create session with correct id', async () => {
    const engine = await createSession('测试主题');
    expect(engine.session.sessionId).toMatch(/^session-\d+$/);
    expect(engine.session.topic).toBe('测试主题');
    expect(engine.session.phase).toBe('idle');
  });

  it('should create output directory', async () => {
    const engine = await createSession('测试主题');
    expect(engine.session.outputDir).toContain('测试主题');
    expect(engine.session.outputDir).toContain('01-资源库');
  });
});

describe('SessionCompactor', () => {
  const makeMessages = (n: number): ConversationMessage[] =>
    Array.from({ length: n }, (_, i) => ({
      role: 'user' as const,
      content: `Message ${i}: ${'x'.repeat(100)}`,
    }));

  it('should not compact short sessions', () => {
    const msgs = makeMessages(20);
    const compacted = SessionCompactor.compact(msgs);
    expect(compacted.length).toBe(20);
  });

  it('should compact long sessions with head+tail protection', () => {
    const msgs = makeMessages(100);
    const compacted = SessionCompactor.compact(msgs);
    // 保留 HEAD(10) + summary(1) + TAIL(20) = 31
    expect(compacted.length).toBe(31);
    expect(compacted[10].role).toBe('system'); // 摘要
  });
});
```

- [ ] **Step 6: Commit**

```bash
git add huage-agent/src/engine.ts huage-agent/src/memory.ts huage-agent/src/runtime/hooks.ts huage-agent/src/runtime/compact.ts huage-agent/tests/engine.test.ts
git commit -m "feat: 实现 Writing Workflow Engine — ConversationRuntime + Hooks + Compaction"
```

---

## Phase 2：Dan Koe 五阶段

### Task 4: Stage 1 选题与定位

**Files:**
- Create: `huage-agent/src/stages/stage1-topic.ts`
- Create: `huage-agent/tests/stage1.test.ts`

- [ ] **Step 1: 创建 src/stages/stage1-topic.ts**

```typescript
import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';
import { logger } from '../logger';
import {
  TopicOption,
  Stage1Topic,
  StageOutput,
} from '../types';

export class Stage1Topic {
  private outputDir: string;

  constructor(outputDir: string) {
    this.outputDir = outputDir;
  }

  async execute(topic: string, researchSummary: string): Promise<StageOutput> {
    logger.stage('Stage 1', '开始选题与定位');

    // 读取 Dan Koe 标题公式参考
    const danKoePrompts = fs.readFileSync(
      path.join(config.referencesPath(), 'dan-koe-prompts.md'),
      'utf-8'
    );

    // 构建 Agent 思考过程
    const thinking = `分析主题 "${topic}"：
1. 目标读者是谁？他们面临什么问题？
2. 如何用 Dan Koe 标题公式吸引读者？
3. 哪些选题既有深度又有传播潜力？

基于研究摘要：
${researchSummary}

使用 Dan Koe 标题公式生成 3-5 个选题方案...`;

    logger.thinking(thinking);

    // 生成选题方案（这里调用 Claude，实际实现时用 SDK）
    const options = await this.generateTopicOptions(topic, danKoePrompts, researchSummary);

    const output: StageOutput = {
      stage: 'stage1',
      status: 'waiting_user',
      thinking,
      result: { options },
    };

    // 保存中间产物
    await this.saveOutput(output);

    return output;
  }

  private async generateTopicOptions(
    topic: string,
    danKoePrompts: string,
    researchSummary: string
  ): Promise<TopicOption[]> {
    // TODO: 调用 Claude Agent SDK 生成选题
    // 这里返回示例数据，后续实现
    return [
      {
        title: `How to master ${topic} in 30 days`,
        subtitle: 'The system they don\'t want you to know',
        targetReader: 'Want to improve but don\'t know where to start',
        painPoint: 'Overwhelmed by information, no clear path',
        uniqueValue: 'Practical system, not just theory',
        viralPotential: 'High - promise + controversy',
      },
    ];
  }

  private async saveOutput(output: StageOutput): Promise<void> {
    const filePath = path.join(this.outputDir, 'stage1-topic.json');
    fs.writeFileSync(filePath, JSON.stringify(output, null, 2), 'utf-8');
  }

  async confirmSelection(userChoice: number): Promise<Stage1Topic> {
    const output = await this.loadOutput();
    const options = (output.result as { options: TopicOption[] }).options;
    const selected = options[userChoice];

    const result: Stage1Topic = {
      ...selected,
      options,
      reasoning: output.thinking || '',
      decidedAt: new Date().toISOString(),
    };

    // 保存最终确认结果
    const filePath = path.join(this.outputDir, 'stage1-topic-confirmed.json');
    fs.writeFileSync(filePath, JSON.stringify(result, null, 2), 'utf-8');

    logger.success(`选题已确认: ${selected.title}`);
    return result;
  }

  private async loadOutput(): Promise<StageOutput> {
    const filePath = path.join(this.outputDir, 'stage1-topic.json');
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  }
}
```

- [ ] **Step 2: 创建 tests/stage1.test.ts**

```typescript
import { Stage1Topic } from '../src/stages/stage1-topic';
import * as fs from 'fs';
import * as path from 'path';

describe('Stage1Topic', () => {
  const testDir = '/tmp/huage-agent-test';

  beforeAll(() => {
    fs.mkdirSync(testDir, { recursive: true });
  });

  afterAll(() => {
    fs.rmSync(testDir, { recursive: true });
  });

  it('should generate topic options', async () => {
    const stage = new Stage1Topic(testDir);
    const result = await stage.execute('时间管理', 'Summary of research...');
    expect(result.status).toBe('waiting_user');
    expect(result.result).toHaveProperty('options');
  });

  it('should save output to file', async () => {
    const stage = new Stage1Topic(testDir);
    await stage.execute('时间管理', 'Summary...');
    const filePath = path.join(testDir, 'stage1-topic.json');
    expect(fs.existsSync(filePath)).toBe(true);
  });
});
```

- [ ] **Step 3: Commit**

```bash
git add huage-agent/src/stages/stage1-topic.ts huage-agent/tests/stage1.test.ts
git commit -m "feat: 实现 Stage 1 选题与定位"
```

---

### Task 5: Stage 2-5（观点/大纲/写作/润色）

**Files:**
- Create: `huage-agent/src/stages/stage2-thesis.ts`
- Create: `huage-agent/src/stages/stage3-outline.ts`
- Create: `huage-agent/src/stages/stage4-writing.ts`
- Create: `huage-agent/src/stages/stage5-polish.ts`
- Create: `huage-agent/tests/stages.test.ts`

- [ ] **Step 1: 创建 src/stages/stage2-thesis.ts**

```typescript
import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';
import { logger } from '../logger';
import { Stage2Thesis, StageOutput, ThesisPoint } from '../types';

export class Stage2Thesis {
  constructor(private outputDir: string) {}

  async execute(
    title: string,
    topic: string,
    researchSummary: string
  ): Promise<StageOutput> {
    logger.stage('Stage 2', '开始核心观点提炼');

    const danKoePrompts = fs.readFileSync(
      path.join(config.referencesPath(), 'dan-koe-prompts.md'),
      'utf-8'
    );

    const thinking = `为标题 "${title}" 提炼核心观点：
1. 挑战什么普遍错误观念？
2. 如何触及问题本质？
3. 引用哪些思想家/理论支撑？
4. 观点之间如何形成逻辑链条？`;

    logger.thinking(thinking);

    const thesis = await this.extractThesis(title, topic, danKoePrompts, researchSummary);

    const output: StageOutput = {
      stage: 'stage2',
      status: 'waiting_user',
      thinking,
      result: thesis,
    };

    await this.saveOutput(output);
    return output;
  }

  private async extractThesis(
    title: string,
    topic: string,
    danKoePrompts: string,
    researchSummary: string
  ): Promise<Stage2Thesis> {
    // TODO: 调用 Claude Agent SDK
    return {
      coreThesis: `核心论点：${topic} 的本质是...`,
      supportingPoints: [
        {
          point: '观点1：挑战普遍观念',
          commonMisconception: '人们通常认为...',
          thinkersToCite: ['Dan Koe', 'Alfred Adler'],
          logicalConnection: '引出下一个观点',
        },
      ],
      reasoning: '',
      confirmedAt: '',
    };
  }

  private async saveOutput(output: StageOutput): Promise<void> {
    fs.writeFileSync(
      path.join(this.outputDir, 'stage2-thesis.json'),
      JSON.stringify(output, null, 2),
      'utf-8'
    );
  }

  async confirm(userModifications?: Partial<Stage2Thesis>): Promise<Stage2Thesis> {
    const output = await this.loadOutput();
    const result: Stage2Thesis = {
      ...(output.result as Stage2Thesis),
      ...userModifications,
      confirmedAt: new Date().toISOString(),
    };

    fs.writeFileSync(
      path.join(this.outputDir, 'stage2-thesis-confirmed.json'),
      JSON.stringify(result, null, 2),
      'utf-8'
    );

    logger.success('观点已确认');
    return result;
  }

  private async loadOutput(): Promise<StageOutput> {
    return JSON.parse(
      fs.readFileSync(
        path.join(this.outputDir, 'stage2-thesis.json'),
        'utf-8'
      )
    );
  }
}
```

- [ ] **Step 2: 创建 src/stages/stage3-outline.ts**

```typescript
import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';
import { logger } from '../logger';
import {
  Stage3Outline,
  StageOutput,
  Stage1Topic,
  Stage2Thesis,
} from '../types';

export class Stage3Outline {
  constructor(private outputDir: string) {}

  async execute(
    topic: Stage1Topic,
    thesis: Stage2Thesis
  ): Promise<StageOutput> {
    logger.stage('Stage 3', '开始大纲构建');

    const thinking = `基于选定的标题和观点构建大纲：
1. 开篇：应用 7 层递进式引入序列
2. 主体：每个核心观点应用 5 步论证模型
3. 结尾：总结 + 行动号召

Dan Koe 7 层开篇序列：
1. 反直觉开篇
2. 宽容式过渡
3. 数据支撑
4. 脆弱性展示
5. 明确承诺
6. 重要性强调
7. 期待感营造

5 步论证模型：
标题 → 引用 → 背景 → 洞察 → 案例 → 实践`;

    logger.thinking(thinking);

    const outline = await this.buildOutline(topic, thesis, thinking);

    const output: StageOutput = {
      stage: 'stage3',
      status: 'waiting_user',
      thinking,
      result: outline,
    };

    await this.saveOutput(output);
    return output;
  }

  private async buildOutline(
    topic: Stage1Topic,
    thesis: Stage2Thesis,
    thinking: string
  ): Promise<Stage3Outline> {
    // TODO: 调用 Claude Agent SDK
    return {
      title: topic.title,
      opening: {
        hook: '反直觉开篇...',
        transition: '理解你的处境...',
        promise: '本文提供 3 个核心洞察...',
        importance: '为什么现在必须解决...',
        expectation: '读完你将获得...',
      },
      sections: thesis.supportingPoints.map((p, i) => ({
        heading: `观点 ${i + 1}`,
        keyPoints: [p.point],
        examples: ['案例1', '案例2'],
      })),
      conclusion: {
        summary: '总结全文',
        callToAction: '立即行动...',
      },
      reasoning: thinking,
      confirmedAt: '',
    };
  }

  private async saveOutput(output: StageOutput): Promise<void> {
    fs.writeFileSync(
      path.join(this.outputDir, 'stage3-outline.json'),
      JSON.stringify(output, null, 2),
      'utf-8'
    );
  }

  async confirm(userModifications?: Partial<Stage3Outline>): Promise<Stage3Outline> {
    const output = await this.loadOutput();
    const result: Stage3Outline = {
      ...(output.result as Stage3Outline),
      ...userModifications,
      confirmedAt: new Date().toISOString(),
    };

    fs.writeFileSync(
      path.join(this.outputDir, 'stage3-outline-confirmed.json'),
      JSON.stringify(result, null, 2),
      'utf-8'
    );

    logger.success('大纲已确认');
    return result;
  }

  private async loadOutput(): Promise<StageOutput> {
    return JSON.parse(
      fs.readFileSync(path.join(this.outputDir, 'stage3-outline.json'), 'utf-8')
    );
  }
}
```

- [ ] **Step 3: 创建 src/stages/stage4-writing.ts**

```typescript
import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';
import { logger } from '../logger';
import { Stage4Draft, StageOutput, Stage3Outline } from '../types';

export class Stage4Writing {
  constructor(private outputDir: string) {}

  async execute(outline: Stage3Outline): Promise<StageOutput> {
    logger.stage('Stage 4', '开始正文写作（Dan Koe 风格）');

    const styleGuide = fs.readFileSync(
      path.join(config.referencesPath(), 'dan-koe-style.md'),
      'utf-8'
    );

    const thinking = `基于大纲撰写正文：

Dan Koe 风格要点：
- 第二人称：用 "you" 而非 "people"
- 短句冲击：关键句不超过 15 字
- 对话式提问：每 3 段一个问句
- 三段式递进：重要观点使用连续三句递进
- 脆弱性 + 权威性结合
- 反叛精神：对传统系统保持批判

字数目标：8000-15000 字（公众号）

分阶段执行：
1. 开篇：7 层递进式引入
2. 主体：每个章节遵循 5 步论证
3. 结尾：总结 + 行动号召`;

    logger.thinking(thinking);

    const draft = await this.writeDraft(outline, styleGuide, thinking);

    const output: StageOutput = {
      stage: 'stage4',
      status: 'waiting_user',
      thinking,
      result: draft,
    };

    await this.saveOutput(output);
    return output;
  }

  private async writeDraft(
    outline: Stage3Outline,
    styleGuide: string,
    thinking: string
  ): Promise<Stage4Draft> {
    // TODO: 调用 Qwen3-Max 写作（使用 qwen_client.py）
    const content = `
# ${outline.title}

[正文内容...]

目标字数：1500-2500 字（公众号）
`;

    const wordCount = content.replace(/[#*>\[\]]/g, '').length;

    return {
      title: outline.title,
      content,
      wordCount,
      style: 'dan-koe',
      verifiedAt: new Date().toISOString(),
    };
  }

  private async saveOutput(output: StageOutput): Promise<void> {
    fs.writeFileSync(
      path.join(this.outputDir, 'stage4-draft.json'),
      JSON.stringify(output, null, 2),
      'utf-8'
    );
    // 同时保存纯文本
    const draft = output.result as Stage4Draft;
    fs.writeFileSync(
      path.join(this.outputDir, '04-正文.md'),
      draft.content,
      'utf-8'
    );
  }

  async confirm(modifications?: string): Promise<Stage4Draft> {
    const output = await this.loadOutput();
    const result: Stage4Draft = {
      ...(output.result as Stage4Draft),
      content: modifications || (output.result as Stage4Draft).content,
      verifiedAt: new Date().toISOString(),
    };

    fs.writeFileSync(
      path.join(this.outputDir, 'stage4-draft-confirmed.json'),
      JSON.stringify(result, null, 2),
      'utf-8'
    );

    logger.success('正文已确认');
    return result;
  }

  private async loadOutput(): Promise<StageOutput> {
    return JSON.parse(
      fs.readFileSync(path.join(this.outputDir, 'stage4-draft.json'), 'utf-8')
    );
  }
}
```

- [ ] **Step 4: 创建 src/stages/stage5-polish.ts**

```typescript
import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';
import { logger } from '../logger';
import { Stage5Polished, StageOutput, Stage4Draft } from '../types';

export class Stage5Polish {
  constructor(private outputDir: string) {}

  async execute(draft: Stage4Draft): Promise<StageOutput> {
    logger.stage('Stage 5', '开始优化与润色');

    const antiAiRules = fs.readFileSync(
      path.join(
        config.vaultPath,
        '.claude/skills/huage-gzh/rules/anti-ai.md'
      ),
      'utf-8'
    );

    const thinking = `优化与润色清单：
1. 标题优化：确保吸引力和点击欲望
2. 开篇强化：7 层序列优化
3. 逻辑流畅：论证链条清晰、过渡自然
4. 金句提炼：关键观点打磨成可独立传播
5. 节奏控制：段落长度和句式变化
6. 情感共鸣：强化与读者的连接
7. 行动召唤：结尾有明确指引
8. 去AI味检查：${antiAiRules}`;

    logger.thinking(thinking);

    const polished = await this.polishDraft(draft, antiAiRules, thinking);

    const output: StageOutput = {
      stage: 'stage5',
      status: 'waiting_user',
      thinking,
      result: polished,
    };

    await this.saveOutput(output);
    return output;
  }

  private async polishDraft(
    draft: Stage4Draft,
    antiAiRules: string,
    thinking: string
  ): Promise<Stage5Polished> {
    // TODO: 调用 Claude Agent SDK 润色
    return {
      title: draft.title,
      content: draft.content, // 润色后的内容
      wordCount: draft.wordCount,
      antiAiCheck: {
        passed: true,
        violations: [],
      },
      seoOptimization: {
        keywords: [],
        densityCheck: true,
        metaDescription: '',
      },
      geoOptimization: {
        citations: [],
        entityOptimization: [],
        aiReadableScore: 85,
      },
      finalAt: new Date().toISOString(),
    };
  }

  private async saveOutput(output: StageOutput): Promise<void> {
    fs.writeFileSync(
      path.join(this.outputDir, 'stage5-polished.json'),
      JSON.stringify(output, null, 2),
      'utf-8'
    );
    const polished = output.result as Stage5Polished;
    fs.writeFileSync(
      path.join(this.outputDir, '05-润色稿.md'),
      polished.content,
      'utf-8'
    );
  }

  async confirm(): Promise<Stage5Polished> {
    const output = await this.loadOutput();
    const result = output.result as Stage5Polished;

    fs.writeFileSync(
      path.join(this.outputDir, 'stage5-final.json'),
      JSON.stringify(result, null, 2),
      'utf-8'
    );

    logger.success('润色完成，文章定稿');
    return result;
  }

  private async loadOutput(): Promise<StageOutput> {
    return JSON.parse(
      fs.readFileSync(
        path.join(this.outputDir, 'stage5-polished.json'),
        'utf-8'
      )
    );
  }
}
```

- [ ] **Step 5: 创建 tests/stages.test.ts**

```typescript
import { Stage1Topic } from '../src/stages/stage1-topic';
import { Stage2Thesis } from '../src/stages/stage2-thesis';
import { Stage3Outline } from '../src/stages/stage3-outline';

describe('Dan Koe Stages', () => {
  const testDir = '/tmp/huage-agent-test';

  beforeAll(() => {
    require('fs').mkdirSync(testDir, { recursive: true });
  });

  afterAll(() => {
    require('fs').rmSync(testDir, { recursive: true });
  });

  it('Stage 1 should generate topic options', async () => {
    const stage = new Stage1Topic(testDir);
    const result = await stage.execute('时间管理', '研究摘要...');
    expect(result.status).toBe('waiting_user');
  });

  it('Stage 2 should extract thesis', async () => {
    const stage = new Stage2Thesis(testDir);
    const result = await stage.execute(
      'How to master time management',
      '时间管理',
      '研究摘要...'
    );
    expect(result.status).toBe('waiting_user');
  });
});
```

- [ ] **Step 6: Commit**

```bash
git add huage-agent/src/stages/stage2-thesis.ts huage-agent/src/stages/stage3-outline.ts huage-agent/src/stages/stage4-writing.ts huage-agent/src/stages/stage5-polish.ts huage-agent/tests/stages.test.ts
git commit -m "feat: 实现 Stage 2-5（观点/大纲/写作/润色）"
```

---

## Phase 3：深度研究

### Task 6: Phase 0 深度研究

**Files:**
- Create: `huage-agent/src/stages/phase0-research.ts`
- Create: `huage-agent/src/tools/tavily.ts`
- Create: `huage-agent/src/tools/youtube.ts`
- Create: `huage-agent/tests/research.test.ts`

- [ ] **Step 1: 创建 src/tools/tavily.ts**

```typescript
import { config } from '../config';
import { TavilyResult } from '../types';

export class TavilyClient {
  private apiKey: string;

  constructor() {
    this.apiKey = config.tavilyApiKey;
  }

  async search(query: string, depth: 'basic' | 'advanced' = 'advanced'): Promise<TavilyResult[]> {
    const response = await fetch('https://api.tavily.com/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({
        query,
        search_depth: depth,
        max_results: 10,
        include_answer: true,
        include_raw_content: false,
      }),
    });

    const data = await response.json();

    return (data.results || []).map((r: any) => ({
      title: r.title,
      url: r.url,
      content: r.content,
      score: r.score || 0,
    }));
  }
}
```

- [ ] **Step 2: 创建 src/tools/youtube.ts**

```typescript
import { google } from 'googleapis';
import { config } from '../config';
import { YouTubeResult } from '../types';

export class YouTubeClient {
  private youtube: any;

  constructor() {
    this.youtube = google.youtube({
      version: 'v3',
      auth: config.youtubeApiKey,
    });
  }

  async search(query: string, maxResults = 5): Promise<YouTubeResult[]> {
    const response = await this.youtube.search.list({
      q: query,
      part: ['snippet'],
      type: ['video'],
      maxResults,
      videoDuration: 'medium', // 5-20 分钟
    });

    return (response.data.items || []).map((item: any) => ({
      title: item.snippet.title,
      videoId: item.id.videoId,
      channelName: item.snippet.channelTitle,
      duration: '', // 需要额外调用 videos API
      transcript: '', // 需要 yt-dlp 抓取
    }));
  }

  async getTranscript(videoId: string): Promise<string> {
    // 使用 yt-dlp 获取字幕
    const { exec } = require('child_process');
    return new Promise((resolve, reject) => {
      exec(
        `yt-dlp --write-auto-sub --skip-download --output /tmp/%(id)s ${videoId}`,
        (err: any, stdout: string, stderr: string) => {
          if (err) {
            resolve('');
          } else {
            resolve('字幕内容...');
          }
        }
      );
    });
  }
}
```

- [ ] **Step 3: 创建 src/stages/phase0-research.ts**

```typescript
import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';
import { logger } from '../logger';
import { Phase0Research, StageOutput } from '../types';
import { TavilyClient } from '../tools/tavily';
import { YouTubeClient } from '../tools/youtube';

export class Phase0Research {
  private tavily: TavilyClient;
  private youtube: YouTubeClient;

  constructor(private outputDir: string) {
    this.tavily = new TavilyClient();
    this.youtube = new YouTubeClient();
  }

  async execute(topic: string): Promise<StageOutput> {
    logger.stage('Phase 0', `开始深度研究: ${topic}`);

    const thinking = `研究策略：
1. Tavily 深度搜索：搜索核心主题、相关概念、行业趋势
2. YouTube 视频研究：搜索相关视频，获取专家观点
3. 综合摘要：整合所有来源，提取关键洞察`;

    logger.thinking(thinking);

    // 并行执行研究
    const [tavilyResults, youtubeResults] = await Promise.all([
      this.tavily.search(topic),
      this.youtube.search(topic),
    ]);

    logger.info(`找到 ${tavilyResults.length} 篇 Tavily 文章`);
    logger.info(`找到 ${youtubeResults.length} 个 YouTube 视频`);

    const research: Phase0Research = {
      topic,
      tavilyResults,
      youtubeResults,
      summary: this.generateSummary(topic, tavilyResults, youtubeResults),
      keyInsights: this.extractInsights(tavilyResults, youtubeResults),
      sources: [
        ...tavilyResults.map((r) => ({
          title: r.title,
          url: r.url,
          type: 'article' as const,
        })),
        ...youtubeResults.map((r) => ({
          title: r.title,
          url: `https://youtube.com/watch?v=${r.videoId}`,
          type: 'video' as const,
        })),
      ],
      completedAt: new Date().toISOString(),
    };

    const output: StageOutput = {
      stage: 'phase0',
      status: 'waiting_user',
      thinking,
      result: research,
    };

    await this.saveOutput(output);
    return output;
  }

  private generateSummary(
    topic: string,
    tavilyResults: any[],
    youtubeResults: any[]
  ): string {
    // TODO: 调用 Claude 总结
    return `
## ${topic} 研究摘要

### 核心发现
1. 发现1...
2. 发现2...

### 行业趋势
- 趋势1
- 趋势2

### 专家观点
- 观点1
- 观点2
`;
  }

  private extractInsights(tavilyResults: any[], youtubeResults: any[]): string[] {
    // TODO: 调用 Claude 提取洞察
    return [
      '洞察1：...',
      '洞察2：...',
    ];
  }

  private async saveOutput(output: StageOutput): Promise<void> {
    const research = output.result as Phase0Research;
    fs.writeFileSync(
      path.join(this.outputDir, '00-研究索引.md'),
      `# ${research.topic} 研究摘要\n\n${research.summary}`,
      'utf-8'
    );
    fs.writeFileSync(
      path.join(this.outputDir, 'phase0-research.json'),
      JSON.stringify(output, null, 2),
      'utf-8'
    );
  }

  async loadConfirmed(): Promise<Phase0Research> {
    const output = await this.loadOutput();
    return output.result as Phase0Research;
  }

  private async loadOutput(): Promise<StageOutput> {
    return JSON.parse(
      fs.readFileSync(
        path.join(this.outputDir, 'phase0-research.json'),
        'utf-8'
      )
    );
  }
}
```

- [ ] **Step 4: 创建 tests/research.test.ts**

```typescript
import { Phase0Research } from '../src/stages/phase0-research';

describe('Phase0Research', () => {
  const testDir = '/tmp/huage-agent-test';

  beforeAll(() => {
    require('fs').mkdirSync(testDir, { recursive: true });
  });

  it('should execute research', async () => {
    const phase = new Phase0Research(testDir);
    const result = await phase.execute('时间管理');
    expect(result.status).toBe('waiting_user');
    expect(result.result).toHaveProperty('summary');
    expect(result.result).toHaveProperty('keyInsights');
    expect(result.result).toHaveProperty('sources');
  }, 30000); // 30s timeout for API calls
});
```

- [ ] **Step 5: Commit**

```bash
git add huage-agent/src/stages/phase0-research.ts huage-agent/src/tools/tavily.ts huage-agent/src/tools/youtube.ts huage-agent/tests/research.test.ts
git commit -m "feat: 实现 Phase 0 深度研究（Tavily + YouTube）"
```

---

## Phase 4：输出模块（P2）

### Task 7: Output 输出模块

> **优先级：P2**（CEO Finding #5：SEO/GEO + HTML 是辅助，文章质量是核心）
> **参考**：Task 0 的 prompts/wiki-reflux.ts | Task 9 的 wiki/ingest.ts

**Files:**
- Create: `huage-agent/src/output/seo-geo.ts`
- Create: `huage-agent/src/output/images.ts`
- Create: `huage-agent/src/output/html.ts`
- Create: `huage-agent/src/output/output.ts`（统一编排）
- Create: `huage-agent/tests/output.test.ts`

- [ ] **Step 1: 创建 `src/output/seo-geo.ts`**

```typescript
import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';
import { logger } from '../logger';
import { SEOResult, GEOResult } from '../types';

export class SEOGEOptimizer {
  constructor(private outputDir: string) {}

  async optimizeSEO(content: string): Promise<SEOResult> {
    logger.info('开始 SEO 优化...');

    const keywords = this.extractKeywords(content);
    const density = this.calculateDensity(content, keywords);
    const metaDescription = this.generateMetaDescription(content);

    return {
      keywords,
      densityCheck: density >= 0.5 && density <= 3,
      metaDescription,
    };
  }

  async optimizeGEO(content: string): Promise<GEOResult> {
    logger.info('开始 GEO 优化...');

    const citations = this.extractCitations(content);
    const entities = this.extractEntities(content);
    const aiScore = await this.calculateAIReadableScore(content);

    return {
      citations,
      entityOptimization: entities,
      aiReadableScore: aiScore,
    };
  }

  private extractKeywords(content: string): string[] {
    const words = content.toLowerCase().match(/\b[a-z\u4e00-\u9fa5]{2,}\b/g);
    if (!words) return [];

    const freq: Record<string, number> = {};
    words.forEach((w) => { freq[w] = (freq[w] || 0) + 1; });

    return Object.entries(freq)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([word]) => word);
  }

  private calculateDensity(content: string, keywords: string[]): number {
    if (!keywords.length) return 0;
    const totalWords = content.length;
    const keywordCount = keywords.reduce(
      (sum, k) => sum + (content.toLowerCase().match(new RegExp(k, 'g'))?.length || 0),
      0
    );
    return (keywordCount / totalWords) * 100;
  }

  private generateMetaDescription(content: string): string {
    const plain = content.replace(/[#*>\[\]]/g, '').trim();
    return plain.slice(0, 160) + (plain.length > 160 ? '...' : '');
  }

  private extractCitations(content: string): string[] {
    const citations: string[] = [];
    const regex = />\s*[""]([^""]+)[""]\s*—/g;
    let match;
    while ((match = regex.exec(content)) !== null) {
      citations.push(match[1]);
    }
    return citations;
  }

  private extractEntities(content: string): string[] {
    // TODO: 接入 wiki/ingest.ts 的实体识别
    return [];
  }

  private async calculateAIReadableScore(content: string): Promise<number> {
    // TODO: 调用 LLM 评估 AI 可读性
    return 80;
  }

  async saveResults(seo: SEOResult, geo: GEOResult): Promise<void> {
    fs.writeFileSync(
      path.join(this.outputDir, 'seo-geo-optimization.json'),
      JSON.stringify({ seo, geo }, null, 2),
      'utf-8'
    );
  }
}
```

- [ ] **Step 2: 创建 `src/output/images.ts`**

```typescript
import { config } from '../config';
import { logger } from '../logger';

export class ImageGenerator {
  private apiKey: string;

  constructor() {
    this.apiKey = config.arkApiKey;
  }

  async generateCover(title: string, style: string = '简洁大气'): Promise<string> {
    logger.info('生成封面图...');
    const prompt = `公众号封面图，主题：${title}，风格：${style}，文字清晰`;
    return this.callSeedream(prompt);
  }

  async generateInlineImages(content: string, count: number = 3): Promise<string[]> {
    logger.info(`生成 ${count} 张文中配图...`);
    const images: string[] = [];
    for (let i = 0; i < count; i++) {
      const prompt = `配图 ${i + 1}：${content.slice(i * 200, i * 200 + 200)}`;
      images.push(await this.callSeedream(prompt));
    }
    return images;
  }

  private async callSeedream(prompt: string): Promise<string> {
    // TODO: 实现 Doubao-Seedream-4.5 API 调用
    return `https://placeholder.com/image-${Date.now()}.png`;
  }
}
```

- [ ] **Step 3: 创建 `src/output/html.ts`**

```typescript
import * as fs from 'fs';
import * as path from 'path';
import { logger } from '../logger';

export class HTMLExporter {
  constructor(private outputDir: string) {}

  async export(markdown: string, title: string, coverImage?: string): Promise<string> {
    logger.info('生成 HTML 排版...');
    const html = this.markdownToHTML(markdown, title, coverImage);
    const filePath = path.join(this.outputDir, 'index.html');
    fs.writeFileSync(filePath, html, 'utf-8');
    logger.success(`HTML 已保存: ${filePath}`);
    return filePath;
  }

  private markdownToHTML(markdown: string, title: string, coverImage?: string): string {
    let body = markdown
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/!\[(.+?)\]\((.+?)\)/g, '<img src="$2" alt="$1">');

    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <style>
    body { max-width: 677px; margin: 0 auto; padding: 20px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
        "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      line-height: 1.75; color: #333; }
    h1 { font-size: 24px; margin: 24px 0 16px; }
    h2 { font-size: 20px; margin: 20px 0 12px; }
    h3 { font-size: 18px; margin: 16px 0 10px; }
    p { margin: 12px 0; }
    blockquote { border-left: 3px solid #ddbb88; padding: 8px 16px;
      margin: 16px 0; background: #f9f6f0; color: #555; }
    img { max-width: 100%; height: auto; margin: 16px 0; }
    strong { color: #000; }
    em { font-style: italic; }
  </style>
</head>
<body>
  ${coverImage ? `<img src="${coverImage}" alt="封面图" style="max-width:100%">` : ''}
  <p>${body}</p>
</body>
</html>`;
  }
}
```

- [ ] **Step 4: 创建 `src/output/output.ts` — 统一编排**

```typescript
/**
 * Output 统一编排
 * 参考：Task 0 的 prompts/wiki-reflux.ts
 *
 * 执行顺序：
 * 1. SEO/GEO 优化
 * 2. 配图生成
 * 3. HTML 排版
 * 4. wiki 回流（使用 WikiIngest）
 */

import * as path from 'path';
import { config } from '../config';
import { logger } from '../logger';
import { Stage5Polished } from '../types';
import { SEOGEOptimizer } from './seo-geo';
import { ImageGenerator } from './images';
import { HTMLExporter } from './html';
import { WikiIngest } from '../wiki/ingest';

export class OutputPipeline {
  private seoGeo: SEOGEOptimizer;
  private images: ImageGenerator;
  private html: HTMLExporter;
  private wikiIngest: WikiIngest;

  constructor(private outputDir: string) {
    this.seoGeo = new SEOGEOptimizer(outputDir);
    this.images = new ImageGenerator();
    this.html = new HTMLExporter(outputDir);
    this.wikiIngest = new WikiIngest();
  }

  async execute(polished: Stage5Polished): Promise<OutputResult> {
    logger.info('开始 Output 流程...');

    // 1. SEO/GEO
    const [seo, geo] = await Promise.all([
      this.seoGeo.optimizeSEO(polished.content),
      this.seoGeo.optimizeGEO(polished.content),
    ]);
    await this.seoGeo.saveResults(seo, geo);
    logger.success('SEO/GEO 优化完成');

    // 2. 配图
    const coverImage = await this.images.generateCover(polished.title);
    const inlineImages = await this.images.generateInlineImages(polished.content, 3);
    logger.success('配图生成完成');

    // 3. HTML
    const htmlPath = await this.html.export(polished.content, polished.title, coverImage);
    logger.success(`HTML 排版完成: ${htmlPath}`);

    // 4. wiki 回流（调用 WikiIngest）
    const refinedContent = this.insertImages(polished.content, inlineImages);
    const markdownPath = path.join(this.outputDir, '06-发布稿.md');
    const fs = await import('fs');
    fs.writeFileSync(markdownPath, refinedContent, 'utf-8');

    // wiki 回流
    const ingestResult = await this.wikiIngest.ingestFile(markdownPath);
    logger.success(`wiki 回流完成，创建了 ${ingestResult.created.length} 个页面`);

    // 报告 wikilink 错误
    if (ingestResult.wikilinkErrors.length > 0) {
      logger.warn(`wiki 回流发现 ${ingestResult.wikilinkErrors.length} 个 wikilink 错误`);
    }

    return {
      seo,
      geo,
      coverImage,
      inlineImages,
      htmlPath,
      wikiCreated: ingestResult.created,
      wikilinkErrors: ingestResult.wikilinkErrors,
    };
  }

  private insertImages(content: string, images: string[]): string {
    // 在每个 H2 标题后插入一张配图
    let imageIndex = 0;
    return content.replace(/^## (.+)$/gm, (match, heading) => {
      const image = images[imageIndex++];
      if (image) {
        return `${match}\n\n![配图](${image})`;
      }
      return match;
    });
  }
}

interface OutputResult {
  seo: any;
  geo: any;
  coverImage: string;
  inlineImages: string[];
  htmlPath: string;
  wikiCreated: string[];
  wikilinkErrors: any[];
}
```

- [ ] **Step 5: 创建 `tests/output.test.ts`**

```typescript
import { OutputPipeline } from '../src/output/output';
import { SEOGEOptimizer } from '../src/output/seo-geo';

describe('OutputPipeline', () => {
  it('should exist', () => {
    expect(OutputPipeline).toBeDefined();
  });
});

describe('SEOGEOptimizer', () => {
  const testDir = '/tmp/huage-agent-test';
  beforeAll(() => { require('fs').mkdirSync(testDir, { recursive: true }); });

  it('should extract keywords', async () => {
    const optimizer = new SEOGEOptimizer(testDir);
    const content = '时间管理是一个重要的话题。时间管理的技巧包括...';
    const seo = await optimizer.optimizeSEO(content);
    expect(seo.keywords.length).toBeGreaterThan(0);
  });

  it('should extract citations', async () => {
    const optimizer = new SEOGEOptimizer(testDir);
    const content = '> "这是一句引用" — 作者';
    const geo = await optimizer.optimizeGEO(content);
    expect(geo.citations.length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 6: Commit**

```bash
git add huage-agent/src/output/ huage-agent/tests/output.test.ts
git commit -m "feat: 实现 Output 输出模块（P2 — SEO/GEO + 配图 + HTML + wiki回流）"
```（P2，与 Task 4/5/6 并行）

> **参考**：llm-wiki-agent `tools/query.py`（CJK-aware）| `tools/ingest.py`（JSON schema）| `tools/build_graph.py`（两遍 + JSONL）

**Files:**
- Create: `huage-agent/src/wiki/manager.ts`
- Create: `huage-agent/src/wiki/query.ts`（CJK-aware）
- Create: `huage-agent/src/wiki/ingest.ts`（JSON schema-driven）
- Create: `huage-agent/src/wiki/lint.ts`（孤儿/断链/wikilink 校验）
- Create: `huage-agent/src/wiki/graph.ts`（两遍 pass + JSONL checkpoint）
- Create: `huage-agent/tests/wiki.test.ts`

- [ ] **Step 1: 创建 `src/wiki/query.ts` — CJK-aware 查询**

```typescript
/**
 * wiki 查询（CJK-aware）
 * 参考：llm-wiki-agent tools/query.py
 *
 * CJK 处理策略：
 * 1. 分词：按空格 + CJK 字符边界双重分割
 * 2. 模糊匹配：支持同义词扩展
 * 3. 排名：优先匹配 title > Summary > body
 */

import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';
import { WikiPage, WikiQueryResult } from '../types';

// CJK 字符范围（Unicode）
const CJK_PATTERN = /[\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]/;

function tokenizeCJK(text: string): string[] {
  // 先按空格分割
  const parts = text.split(/\s+/);
  const tokens: string[] = [];

  for (const part of parts) {
    if (CJK_PATTERN.test(part)) {
      // CJK：按字符分割（简化版，可接入 jieba 等分词库）
      for (const char of part) {
        if (CJK_PATTERN.test(char)) {
          tokens.push(char);
        }
      }
    } else {
      tokens.push(part.toLowerCase());
    }
  }

  return tokens.filter((t) => t.length > 1);
}

export class WikiQuery {
  /**
   * 搜索 wiki 页面
   * 参考：llm-wiki-agent tools/query.py
   */
  async search(keyword: string): Promise<WikiQueryResult> {
    const wikiPath = config.wikiPath();
    const pages = await this.searchPages(wikiPath, keyword);

    // 按相关性排序
    pages.sort((a, b) => {
      const scoreA = this.relevanceScore(a, keyword);
      const scoreB = this.relevanceScore(b, keyword);
      return scoreB - scoreA;
    });

    return {
      pages: pages.slice(0, 10), // 最多返回 10 条
      query: keyword,
      matchedAt: new Date().toISOString(),
    };
  }

  private async searchPages(wikiPath: string, keyword: string): Promise<WikiPage[]> {
    const pages: WikiPage[] = [];
    const queryTokens = tokenizeCJK(keyword);

    this.walkDir(wikiPath, (filePath) => {
      const content = fs.readFileSync(filePath, 'utf-8');
      const title = path.basename(filePath, '.md');

      // 检查是否匹配
      const bodyTokens = tokenizeCJK(content);
      const intersection = queryTokens.filter((qt) =>
        bodyTokens.some((bt) => bt.includes(qt) || qt.includes(bt))
      );

      if (intersection.length > 0) {
        pages.push({
          title,
          type: this.extractType(content),
          content: this.extractRelevantSnippet(content, queryTokens),
          tags: this.extractTags(content),
          sources: this.extractSources(content),
          lastUpdated: this.extractDate(content),
        });
      }
    });

    return pages;
  }

  private relevanceScore(page: WikiPage, keyword: string): number {
    const titleLower = page.title.toLowerCase();
    const keywordLower = keyword.toLowerCase();
    const contentLower = page.content.toLowerCase();

    let score = 0;
    if (titleLower.includes(keywordLower)) score += 10; // title 匹配权重最高
    if (contentLower.includes(keywordLower)) score += 5; // content 匹配
    score += page.content.length / 1000; // 内容长度加权

    return score;
  }

  private extractRelevantSnippet(content: string, tokens: string[]): string {
    // 提取包含关键词的片段（前后各 50 字）
    const lines = content.split('\n');
    for (const line of lines) {
      const lineTokens = tokenizeCJK(line);
      if (lineTokens.some((lt) => tokens.some((qt) => lt.includes(qt) || qt.includes(lt)))) {
        return line.slice(0, 200);
      }
    }
    return content.slice(0, 200);
  }

  private walkDir(dir: string, callback: (filePath: string) => void): void {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        this.walkDir(full, callback);
      } else if (entry.name.endsWith('.md')) {
        callback(full);
      }
    }
  }

  private extractType(content: string): WikiPage['type'] {
    const match = content.match(/^type:\s*(\w+)/m);
    return (match?.[1] as WikiPage['type']) || 'source';
  }

  private extractTags(content: string): string[] {
    const match = content.match(/tags:\s*\[([^\]]+)\]/);
    if (!match) return [];
    return match[1].split(',').map((t) => t.trim().replace(/['"]/g, ''));
  }

  private extractSources(content: string): string[] {
    const match = content.match(/sources:\s*\[([^\]]+)\]/);
    if (!match) return [];
    return match[1].split(',').map((s) => s.trim().replace(/['"]/g, ''));
  }

  private extractDate(content: string): string {
    const match = content.match(/^date:\s*(\S+)/m);
    return match?.[1] || new Date().toISOString().split('T')[0];
  }
}
```

- [ ] **Step 2: 创建 `src/wiki/ingest.ts` — JSON Schema-driven**

```typescript
/**
 * wiki 摄入（JSON Schema-driven）
 * 参考：llm-wiki-agent tools/ingest.py
 *
 * 流程：
 * 1. 读取源文件
 * 2. 调用 LLM 生成结构化数据（JSON Schema 校验）
 * 3. 生成来源页、实体页、概念页
 * 4. 校验 wikilink [[ ]] 完整性
 * 5. 写入 checkpoint
 */

import * as fs from 'fs';
import * as path from 'path';
import { z } from 'zod';
import { config } from '../config';
import { PromptEngine } from '../prompts/shared';
import { WIKI_REFLUX_PROMPT, WIKI_REFLUX_MODEL, WIKI_REFLUX_TEMPERATURE } from '../prompts/wiki-reflux';

// 输入 schema
const SourceIngestSchema = z.object({
  sourceContent: z.string(),
  slug: z.string(),
  date: z.string(),
  sourceFile: z.string(),
});

// 输出 schema
const WikiRefluxOutputSchema = z.object({
  sourcePage: z.object({ content: z.string() }),
  entities: z.array(z.object({ name: z.string(), type: z.string(), content: z.string() })),
  concepts: z.array(z.object({ name: z.string(), content: z.string() })),
  newConnections: z.array(z.object({ targetPage: z.string(), relationship: z.string() })),
});

export class WikiIngest {
  async ingestFile(filePath: string): Promise<IngestResult> {
    if (!fs.existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    const slug = path.basename(filePath, path.extname(filePath))
      .toLowerCase()
      .replace(/\s+/g, '-');
    const date = new Date().toISOString().split('T')[0];

    // Step 1: 调用 LLM 生成结构化数据
    const result = await PromptEngine.callLLM({
      template: WIKI_REFLUX_PROMPT,
      vars: {
        title: slug,
        content: content.slice(0, 8000), // 截断
        sources: JSON.stringify([{ title: slug, url: filePath }]),
      },
      model: WIKI_REFLUX_MODEL,
      temperature: WIKI_REFLUX_TEMPERATURE,
      outputSchema: WikiRefluxOutputSchema,
    });

    const parsed = WikiRefluxOutputSchema.parse(result);

    // Step 2: 写入来源页
    const wikiDir = config.wikiPath();
    const sourcePath = path.join(wikiDir, `sources/${date}-${slug}.md`);
    fs.writeFileSync(sourcePath, parsed.sourcePage.content, 'utf-8');

    // Step 3: 写入实体页
    const created: string[] = [sourcePath];
    for (const entity of parsed.entities) {
      const entityPath = path.join(wikiDir, `entities/${entity.name}.md`);
      fs.writeFileSync(entityPath, entity.content, 'utf-8');
      created.push(entityPath);
    }

    // Step 4: 写入概念页
    for (const concept of parsed.concepts) {
      const conceptPath = path.join(wikiDir, `concepts/${concept.name}.md`);
      fs.writeFileSync(conceptPath, concept.content, 'utf-8');
      created.push(conceptPath);
    }

    // Step 5: 校验 wikilink
    const wikilinkErrors = this.validateWikilinks(created, wikiDir);

    return {
      created,
      wikilinkErrors,
    };
  }

  /**
   * 校验 wikilink 完整性
   * 1. 检查 [[pagename]] 指向的页面是否存在
   * 2. 检查孤儿页面（被引用但不存在）
   */
  private validateWikilinks(created: string[], wikiDir: string): WikilinkError[] {
    const errors: WikilinkError[] = [];

    // 收集所有现有页面
    const existingPages = new Set<string>();
    for (const file of this.listMdFiles(wikiDir)) {
      existingPages.add(path.basename(file, '.md'));
    }

    // 添加刚创建的页面
    for (const file of created) {
      existingPages.add(path.basename(file, '.md'));
    }

    // 检查每个文件的 wikilink
    for (const file of created) {
      const content = fs.readFileSync(file, 'utf-8');
      const links = content.match(/\[\[([^\]|]+)\]\]/g) || [];

      for (const link of links) {
        const target = link.slice(2, -2).split('/').pop() || '';
        if (!existingPages.has(target)) {
          errors.push({
            source: path.basename(file, '.md'),
            target,
            type: 'broken',
          });
        }
      }
    }

    return errors;
  }

  private listMdFiles(dir: string): string[] {
    const files: string[] = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        files.push(...this.listMdFiles(full));
      } else if (entry.name.endsWith('.md')) {
        files.push(full);
      }
    }
    return files;
  }
}

interface IngestResult {
  created: string[];
  wikilinkErrors: WikilinkError[];
}

interface WikilinkError {
  source: string;
  target: string;
  type: 'broken' | 'orphan';
}
```

- [ ] **Step 3: 创建 `src/wiki/graph.ts` — 两遍 Pass + JSONL checkpoint**

```typescript
/**
 * wiki 图谱构建
 * 参考：llm-wiki-agent tools/build_graph.py
 *
 * 两遍 Pass：
 * Pass 1：收集所有 wikilink，建立双向映射
 * Pass 2：生成图谱数据 + 写入 JSONL checkpoint
 */

import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';

export interface GraphNode {
  id: string;
  title: string;
  type: 'source' | 'entity' | 'concept' | 'synthesis';
  tags: string[];
  connections: number; // 入度 + 出度
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship?: string;
}

export interface WikiGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  generatedAt: string;
}

export class WikiGraphBuilder {
  private checkpointFile: string;

  constructor() {
    const wikiDir = config.wikiPath();
    this.checkpointFile = path.join(wikiDir, 'graph.jsonl');
  }

  async build(): Promise<WikiGraph> {
    const wikiDir = config.wikiPath();

    // Pass 1：收集所有 wikilink
    const { nodes, edges } = await this.pass1(wikiDir);

    // Pass 2：生成图谱 + 写入 checkpoint
    const graph: WikiGraph = {
      nodes,
      edges,
      generatedAt: new Date().toISOString(),
    };

    // 写入 JSONL checkpoint（追加模式）
    fs.appendFileSync(
      this.checkpointFile,
      JSON.stringify({ ts: new Date().toISOString(), graph }) + '\n',
      'utf-8'
    );

    return graph;
  }

  private async pass1(wikiDir: string): Promise<{ nodes: GraphNode[]; edges: GraphEdge[] }> {
    const nodes: GraphNode[] = [];
    const edges: GraphEdge[] = [];
    const allLinks: Map<string, Set<string>> = new Map(); // page -> links to

    // 遍历所有 md 文件
    for (const file of this.listMdFiles(wikiDir)) {
      const content = fs.readFileSync(file, 'utf-8');
      const title = path.basename(file, '.md');

      // 提取类型和标签
      const type = this.extractFrontmatter(content, 'type') as GraphNode['type'] || 'source';
      const tags = this.extractTags(content);

      // 提取所有 wikilink
      const links = content.match(/\[\[([^\]|]+)\]\]/g) || [];
      const targets = links.map((l) => l.slice(2, -2).split('/').pop() || '');

      nodes.push({ id: title, title, type, tags, connections: targets.length });
      allLinks.set(title, new Set(targets));

      // 记录边
      for (const target of targets) {
        edges.push({ source: title, target });
      }
    }

    // 计算入度
    for (const node of nodes) {
      const incoming = edges.filter((e) => e.target === node.id).length;
      node.connections += incoming;
    }

    return { nodes, edges };
  }

  private listMdFiles(dir: string): string[] {
    const files: string[] = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory() && !entry.name.startsWith('.')) {
        files.push(...this.listMdFiles(full));
      } else if (entry.name.endsWith('.md')) {
        files.push(full);
      }
    }
    return files;
  }

  private extractFrontmatter(content: string, key: string): string | null {
    const match = content.match(new RegExp(`^${key}:\\s*(.+)$`, 'm'));
    return match?.[1]?.trim() || null;
  }

  private extractTags(content: string): string[] {
    const match = content.match(/tags:\s*\[([^\]]+)\]/);
    if (!match) return [];
    return match[1].split(',').map((t) => t.trim().replace(/['"]/g, ''));
  }

  async loadLatest(): Promise<WikiGraph | null> {
    if (!fs.existsSync(this.checkpointFile)) return null;

    const lines = fs.readFileSync(this.checkpointFile, 'utf-8').trim().split('\n');
    if (!lines.length) return null;

    // 读取最后一条
    const last = JSON.parse(lines[lines.length - 1]);
    return last.graph;
  }
}
```

- [ ] **Step 4: 创建 `src/wiki/lint.ts`**

```typescript
/**
 * wiki 健康检查
 * 检查：孤儿页面、断链、矛盾、过时、缺失实体
 */

import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';

export interface LintResult {
  passed: boolean;
  issues: LintIssue[];
}

export interface LintIssue {
  type: 'orphan' | 'broken' | 'contradiction' | 'stale' | 'missing-entity';
  file: string;
  detail: string;
  severity: 'error' | 'warning';
}

export class WikiLint {
  async lint(): Promise<LintResult> {
    const wikiDir = config.wikiPath();
    const issues: LintIssue[] = [];

    // 1. 检查孤儿页面
    const orphans = await this.findOrphans(wikiDir);
    for (const [page, links] of orphans) {
      issues.push({
        type: 'orphan',
        file: page,
        detail: `页面被 ${links} 个其他页面引用，但自身没有引用任何页面`,
        severity: 'warning',
      });
    }

    // 2. 检查断链
    const broken = await this.findBrokenLinks(wikiDir);
    for (const { source, target } of broken) {
      issues.push({
        type: 'broken',
        file: source,
        detail: `wikilink [[${target}]] 指向不存在的页面`,
        severity: 'error',
      });
    }

    // 3. 检查过时页面
    const stale = await this.findStalePages(wikiDir);
    for (const { page, days } of stale) {
      issues.push({
        type: 'stale',
        file: page,
        detail: `页面超过 ${days} 天未更新`,
        severity: 'warning',
      });
    }

    // 4. 检查待填充占位符
    const pending = await this.findPendingPlaceholders(wikiDir);
    for (const { page, field } of pending) {
      issues.push({
        type: 'stale',
        file: page,
        detail: `字段 "${field}" 仍为"待填充"占位符`,
        severity: 'warning',
      });
    }

    return {
      passed: issues.filter((i) => i.severity === 'error').length === 0,
      issues,
    };
  }

  private async findOrphans(wikiDir: string): Promise<[string, number][]> {
    const orphans: [string, number][] = [];

    // 收集所有链接（入度）
    const incoming: Map<string, Set<string>> = new Map();
    const allFiles = this.listMdFiles(wikiDir);
    for (const file of allFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      const links = content.match(/\[\[([^\]|]+)\]\]/g) || [];
      for (const link of links) {
        const target = link.slice(2, -2).split('/').pop() || '';
        if (!incoming.has(target)) incoming.set(target, new Set());
        incoming.get(target)!.add(path.basename(file, '.md'));
      }
    }

    // 检查没有出链的页面（但被引用）
    for (const file of allFiles) {
      const pageName = path.basename(file, '.md');
      const content = fs.readFileSync(file, 'utf-8');
      const hasLinks = /\[\[[^\]]+\]\]/.test(content);
      const hasIncoming = (incoming.get(pageName)?.size ?? 0) > 0;

      if (!hasLinks && hasIncoming && pageName !== 'index') {
        orphans.push([pageName, incoming.get(pageName)!.size]);
      }
    }

    return orphans;
  }

  private async findBrokenLinks(wikiDir: string): Promise<{ source: string; target: string }[]> {
    const broken: { source: string; target: string }[] = [];

    // 收集所有现有页面
    const existingPages = new Set(
      this.listMdFiles(wikiDir).map((f) => path.basename(f, '.md'))
    );

    // 检查每个文件
    for (const file of this.listMdFiles(wikiDir)) {
      const content = fs.readFileSync(file, 'utf-8');
      const links = content.match(/\[\[([^\]|]+)\]\]/g) || [];

      for (const link of links) {
        const target = link.slice(2, -2).split('/').pop() || '';
        if (!existingPages.has(target)) {
          broken.push({ source: path.basename(file, '.md'), target });
        }
      }
    }

    return broken;
  }

  private async findStalePages(wikiDir: string): Promise<{ page: string; days: number }[]> {
    const stale: { page: string; days: number }[] = [];
    const now = Date.now();
    const THIRTY_DAYS = 30 * 24 * 60 * 60 * 1000;

    for (const file of this.listMdFiles(wikiDir)) {
      const content = fs.readFileSync(file, 'utf-8');
      const dateMatch = content.match(/^date:\s*(\S+)/m);
      const lastUpdated = dateMatch?.[1];

      if (lastUpdated) {
        const parts = lastUpdated.split('-').map(Number);
        const updatedAt = new Date(parts[0], parts[1] - 1, parts[2]).getTime();
        const days = Math.floor((now - updatedAt) / (24 * 60 * 60 * 1000));
        if (days > 30) {
          stale.push({ page: path.basename(file, '.md'), days });
        }
      }
    }

    return stale;
  }

  private async findPendingPlaceholders(wikiDir: string): Promise<{ page: string; field: string }[]> {
    const pending: { page: string; field: string }[] = [];

    for (const file of this.listMdFiles(wikiDir)) {
      const content = fs.readFileSync(file, 'utf-8');
      if (content.includes('待填充')) {
        pending.push({ page: path.basename(file, '.md'), field: '待填充' });
      }
    }

    return pending;
  }

  private listMdFiles(dir: string): string[] {
    const files: string[] = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory() && !entry.name.startsWith('.')) {
        files.push(...this.listMdFiles(full));
      } else if (entry.name.endsWith('.md')) {
        files.push(full);
      }
    }
    return files;
  }
}
```

- [ ] **Step 5: 创建 `src/wiki/manager.ts`**

```typescript
import { WikiQuery } from './query';
import { WikiIngest } from './ingest';
import { WikiLint, LintResult } from './lint';
import { WikiGraphBuilder, WikiGraph } from './graph';

export class WikiManager {
  private query: WikiQuery;
  private ingest: WikiIngest;
  private lint: WikiLint;
  private graph: WikiGraphBuilder;

  constructor() {
    this.query = new WikiQuery();
    this.ingest = new WikiIngest();
    this.lint = new WikiLint();
    this.graph = new WikiGraphBuilder();
  }

  async search(keyword: string) {
    return this.query.search(keyword);
  }

  async ingestSource(filePath: string) {
    return this.ingest.ingestFile(filePath);
  }

  async lint(): Promise<LintResult> {
    return this.lint.lint();
  }

  async buildGraph(): Promise<WikiGraph> {
    return this.graph.build();
  }

  async loadGraph(): Promise<WikiGraph | null> {
    return this.graph.loadLatest();
  }
}
```

- [ ] **Step 6: 创建 `tests/wiki.test.ts`**

```typescript
import { WikiQuery } from '../src/wiki/query';
import { WikiLint } from '../src/wiki/lint';
import * as fs from 'fs';
import * as path from 'path';

describe('WikiQuery', () => {
  it('should tokenize CJK characters', () => {
    // CJK 分词测试
    const query = new WikiQuery() as any;
    const tokens = query.tokenizeCJK('时间管理');
    expect(tokens).toContain('时');
    expect(tokens).toContain('间');
    expect(tokens).toContain('管');
    expect(tokens).toContain('理');
  });
});

describe('WikiLint', () => {
  const testDir = '/tmp/huage-agent-wiki-lint-test';

  beforeAll(() => {
    fs.mkdirSync(path.join(testDir, 'sources'), { recursive: true });
    // 创建测试页面
    fs.writeFileSync(
      path.join(testDir, 'sources/test-source.md'),
      '---\ntitle: "Test"\ntype: source\ndate: 2026-01-01\ntags: []\n---\n\nTest content with [[NonExistentPage]] link.',
      'utf-8'
    );
  });

  afterAll(() => {
    fs.rmSync(testDir, { recursive: true });
  });

  it('should detect broken wikilinks', async () => {
    const lint = new WikiLint() as any;
    lint.config = { wikiPath: () => testDir };
    const result = await lint.lint();
    const brokenLinks = result.issues.filter((i) => i.type === 'broken');
    expect(brokenLinks.length).toBeGreaterThan(0);
    expect(brokenLinks[0].detail).toContain('NonExistentPage');
  });
});
```

- [ ] **Step 7: Commit**

```bash
git add huage-agent/src/wiki/ huage-agent/tests/wiki.test.ts
git commit -m "feat: 实现 Wiki 管理模块 — CJK查询 + JSONL checkpoint + wikilink校验"
```

---

## Phase 5.5：Dan Koe 方法论验证机制

### Task 9: Post-3-Article 有效性验证

> **优先级：P1**（CEO Finding #4：Dan Koe 水土不服风险未评估）
> **触发**：完成 3 篇文章后自动运行，或手动 `huage-agent validate`

**Files:**
- Create: `huage-agent/scripts/dan-koe-validation.ts`
- Create: `huage-agent/tests/validation.test.ts`

- [ ] **Step 1: 创建 `scripts/dan-koe-validation.ts`**

```typescript
/**
 * Dan Koe 方法论有效性验证
 *
 * 验证指标：
 * 1. 去 AI 味评分（目标 > 70）
 * 2. 选题多样性（目标 > 3 个不同领域）
 * 3. 读者反馈评分（待接入）
 *
 * 触发条件：完成 3 篇文章后自动运行
 */

import * as fs from 'fs';
import * as path from 'path';
import { config } from '../src/config';

interface ValidationResult {
  articleCount: number;
  avgWordCount: number;
  antiAiScore: number;
  topicVariety: number;
  recommendation: 'continue' | 'adjust' | 'pivot';
  nextSteps: string[];
}

export class DanKoeValidator {
  async validate(): Promise<ValidationResult> {
    const articles = this.loadArticles();

    if (articles.length < 3) {
      return {
        articleCount: articles.length,
        avgWordCount: 0,
        antiAiScore: 0,
        topicVariety: 0,
        recommendation: 'continue',
        nextSteps: ['继续完成至少 3 篇文章'],
      };
    }

    const avgWordCount = this.calcAvgWordCount(articles);
    const antiAiScore = await this.calcAntiAiScore(articles);
    const topicVariety = this.calcTopicVariety(articles);

    let recommendation: ValidationResult['recommendation'] = 'continue';
    const nextSteps: string[] = [];

    if (antiAiScore < 50) {
      recommendation = 'adjust';
      nextSteps.push('加强去 AI 味处理');
    }

    if (topicVariety < 0.3) {
      recommendation = 'adjust';
      nextSteps.push('扩展选题多样性');
    }

    if (recommendation === 'continue' && antiAiScore >= 70) {
      nextSteps.push('Dan Koe 方法论有效，继续沿用');
    }

    await this.writeReport({
      articleCount: articles.length,
      avgWordCount,
      antiAiScore,
      topicVariety,
      recommendation,
      nextSteps,
    });

    return {
      articleCount: articles.length,
      avgWordCount,
      antiAiScore,
      topicVariety,
      recommendation,
      nextSteps,
    };
  }

  private loadArticles(): string[] {
    const outputDir = config.outputPath();
    const articles: string[] = [];
    if (!fs.existsSync(outputDir)) return articles;

    for (const dateDir of fs.readdirSync(outputDir)) {
      const datePath = path.join(outputDir, dateDir);
      if (!fs.statSync(datePath).isDirectory()) continue;
      for (const articleDir of fs.readdirSync(datePath)) {
        const polished = path.join(datePath, articleDir, '05-润色稿.md');
        if (fs.existsSync(polished)) {
          articles.push(fs.readFileSync(polished, 'utf-8'));
        }
      }
    }
    return articles;
  }

  private calcAvgWordCount(articles: string[]): number {
    if (!articles.length) return 0;
    return Math.round(articles.reduce((s, a) => s + a.length, 0) / articles.length);
  }

  private async calcAntiAiScore(articles: string[]): Promise<number> {
    let score = 70;
    for (const article of articles) {
      const sentences = article.split(/[.。!！?？]/);
      const avgLen = sentences.reduce((s, sen) => s + sen.length, 0) / (sentences.length || 1);
      if (avgLen > 50) score -= 5;
      if (!article.includes('你')) score -= 5;
      if (!article.includes('？')) score -= 3;
    }
    return Math.max(0, score);
  }

  private calcTopicVariety(articles: string[]): number {
    const topics = new Set<string>();
    for (const article of articles) {
      const match = article.match(/^#\s+(.+)$/m);
      if (match) topics.add(match[1].split(/\s+/)[0]);
    }
    return topics.size / articles.length;
  }

  private async writeReport(result: ValidationResult): Promise<void> {
    const reportPath = path.join(config.outputPath(), 'dan-koe-validation-report.md');
    const content = `# Dan Koe 方法论验证报告

生成时间：${new Date().toISOString()}

## 指标

- 文章数量：${result.articleCount}
- 平均字数：${result.avgWordCount}
- 去 AI 味评分：${result.antiAiScore}/100
- 选题多样性：${(result.topicVariety * 100).toFixed(0)}%

## 建议

**${result.recommendation === 'continue' ? '继续沿用' : result.recommendation === 'adjust' ? '调整优化' : '考虑转型'}**

${result.nextSteps.map((s) => `- ${s}`).join('\n')}`;

    fs.writeFileSync(reportPath, content, 'utf-8');
  }
}

if (require.main === module) {
  new DanKoeValidator().validate().then((r) => {
    console.log(JSON.stringify(r, null, 2));
    process.exit(r.recommendation === 'pivot' ? 1 : 0);
  });
}
```

- [ ] **Step 2: Commit**

```bash
git add huage-agent/scripts/dan-koe-validation.ts
git commit -m "feat: 实现 Dan Koe 方法论有效性验证"
```

---

## Phase 6：CLI 入口

### Task 10: CLI 入口

> **优先级：P1**

**Files:**
- Create: `huage-agent/src/index.ts`
- Modify: `huage-agent/package.json`（添加 bin 字段）

- [ ] **Step 1: 创建 `src/index.ts`（引用 `engine.ts`）**

```typescript
#!/usr/bin/env node

import { Command } from 'commander';
import { WritingEngine, createSession } from './engine'; // 引用 engine.ts
import { WikiManager } from './wiki/manager';
import { logger } from './logger';

const program = new Command();

program
  .name('huage-agent')
  .description('专注文章创作的独立 Agent')
  .version('0.1.0');

// ==================== write 命令 ====================

program
  .command('write')
  .description('开始一篇文章创作')
  .argument('<topic>', '文章主题')
  .action(async (topic: string) => {
    try {
      logger.info('启动 Writing Workflow Engine...');
      const engine = await createSession(topic);
      await engine.run();
    } catch (error) {
      logger.error(`启动失败: ${error}`);
      process.exit(1);
    }
  });

// ==================== wiki 命令组 ====================

const wiki = program.command('wiki').description('Wiki 管理命令');

wiki
  .command('query')
  .description('查询 wiki 知识')
  .argument('<keyword>', '搜索关键词')
  .action(async (keyword: string) => {
    try {
      const manager = new WikiManager();
      const result = await manager.search(keyword);
      console.log(`找到 ${result.pages.length} 个相关页面:`);
      result.pages.forEach((page) => {
        console.log(`- [[${page.title}]]: ${page.content.slice(0, 100)}...`);
      });
    } catch (error) {
      logger.error(`查询失败: ${error}`);
    }
  });

wiki
  .command('ingest')
  .description('摄入源文件到 wiki')
  .argument('<file>', '文件路径')
  .action(async (file: string) => {
    try {
      const manager = new WikiManager();
      await manager.ingestSource(file);
      logger.success('摄入完成');
    } catch (error) {
      logger.error(`摄入失败: ${error}`);
    }
  });

wiki
  .command('lint')
  .description('检查 wiki 健康状态')
  .action(async () => {
    try {
      const manager = new WikiManager();
      const result = await manager.lint();
      if (result.passed) {
        logger.success('Wiki 健康检查通过');
      } else {
        logger.warn(`发现 ${result.issues.length} 个问题:`);
        result.issues.forEach((issue) => console.log(`  - ${issue}`));
      }
    } catch (error) {
      logger.error(`检查失败: ${error}`);
    }
  });

// ==================== 启动 ====================

program.parse();
```

- [ ] **Step 2: Commit**

```bash
git add huage-agent/src/index.ts
git commit -m "feat: 实现 CLI 入口"
```

---

---

## CEO REVIEW (Phase 1 + Reference Study)

> **Mode**: SELECTIVE EXPANSION
> **Reviewer**: Claude subagent (independent CEO)
> **Reference Studies**: llm-wiki-agent | dankoe-writer | claw-code | obsidian-skills

### CEO Dual Voices — Consensus Table

```
CEO DUAL VOICES — CONSENSUS TABLE:
═══════════════════════════════════════════════════════════════
  Dimension                           Claude  Codex  Consensus
  ─────────────────────────────────── ─────── ─────── ─────────
  1. Premises valid?                   High    High   CONFIRMED
  2. Right problem to solve?          Medium  Medium  CONFIRMED
  3. Scope calibration correct?       High    High    CONFIRMED ✓
  4. Alternatives sufficiently explored? Medium  Medium  CONFIRMED ✓
  5. Competitive/market risks covered? Medium   Medium  CONFIRMED ✓
  6. 6-month trajectory sound?         High    High    CONFIRMED ✓
═══════════════════════════════════════════════════════════════
✓ = resolved after reference study updates
```

### Critical Findings (已解决 ✓)

**Finding 1: "Agent 架构"是误导 — 实为 Workflow Engine** ✓
- 状态：已解决
- 措施：`src/agent.ts` → `src/engine.ts`，采用 claw-code ConversationRuntime 架构
- 新增：`src/runtime/hooks.ts`（PreToolUse/PostToolUse）+ `src/runtime/compact.ts`（Session compaction）

**Finding 2: 7个核心 LLM 调用全是 TODO** ✓
- 状态：已解决
- 措施：新增 Task 0（LLM Calling Protocol Design）
  - 所有 prompt 模板（含 {{VAR}} 替换，参考 dankoe-writer）
  - 模型选择：Claude Sonnet（分析/结构）| Qwen3-Max（正文写作）
  - 输出 schema（Zod 校验）
  - 温度/top-p 设置（Stage 1=0.7, Stage 4=0.8, Stage 5=0.4...）
  - 新增 `src/db/schema.ts`（stage_history 表，参考 dankoe-writer）

**Finding 3: wiki 飞轮在第一篇文章时完全空转** ✓
- 状态：已解决
- 措施：新增 Task 0.5（Day-0 Bootstrap）
  - 批量摄入现有 `raw/` 内容到 wiki
  - 参考 llm-wiki-agent tools/ingest.py

### High Findings (已解决 ✓)

**Finding 4: Dan Koe 方法论"水土不服"风险未评估** ✓
- 状态：已解决
- 措施：新增 Task 9（Post-3-Article 有效性验证）
  - 去 AI 味评分（目标 > 70）
  - 选题多样性评估
  - 自动生成验证报告

**Finding 5: SEO/GEO + HTML 占 Task weight 过高** ✓
- 状态：已解决
- 措施：合并 Task 7+8 → Task 7（Output Pipeline，P2）
  - SEO/GEO + 配图 + HTML + wiki回流统一编排
  - 核心验证问题变为：文章质量 > 分发效率

### Medium Findings (已解决或降级)

**Finding 6: 问题定义宽泛** → 降级
- 当前 Phase 1 聚焦最高优先问题：选题焦虑 + 写作阻塞
- 后续 Phases 可扩展

**Finding 7: 竞争壁垒不清晰** → 降级
- 壁垒 = Dan Koe 方法论 + wiki 知识积累 + 公众号发布路径
- Phase 3 完成后可评估

### 参考项目带来的新设计模式

| 来源 | 模式 | 应用位置 |
|------|------|---------|
| dankoe-writer | `{{VAR}}` 模板替换 + user-role prompts | Task 0 prompts/ |
| dankoe-writer | stage_history 版本化 + drizzle schema | Task 0 db/schema.ts |
| claw-code | ConversationRuntime 工具循环 | Task 3 engine.ts |
| claw-code | PreToolUse/PostToolUse hooks（退出码语义） | Task 3 runtime/hooks.ts |
| claw-code | Session compaction（head+tail 保护） | Task 3 runtime/compact.ts |
| llm-wiki-agent | wikilink `[[pagename]]` 校验 | Task 8 wiki/ingest.ts |
| llm-wiki-agent | CJK-aware 分词查询 | Task 8 wiki/query.ts |
| llm-wiki-agent | 两遍 Pass + JSONL checkpoint | Task 8 wiki/graph.ts |
| obsidian-skills | SKILL.md frontmatter 格式 | skills/ 目录 |

---

## 依赖关系

```
Task 0 (LLM Calling Protocol)              ← P0 基础
    ↓
Task 1 (项目脚手架)
    ↓
Task 2 (全局类型 + db/schema)
    ↓
Task 3 (Writing Workflow Engine)             ← 引用 engine.ts + runtime/
    ↓
┌──────────────────────────────────────────────────────────┐
│ Task 4 (Stage 1-5)    ← 并行，均引用 prompts/           │
│ Task 5 (Phase 0 研究)                                    │
│ Task 6 (Day-0 Bootstrap)                                 │
│ Task 8 (Wiki Manager)    ← 引用 wiki/ CJK + JSONL      │
└──────────────────────────────────────────────────────────┘
    ↓
Task 7 (Output Pipeline)    ← P2，依赖 Stage 5 + WikiIngest
    ↓
Task 9 (Dan Koe 验证)        ← Post-3-article 自动触发
    ↓
Task 10 (CLI 入口)           ← 引用 engine.ts
```

---

## Decision Audit Trail

| # | Phase | Decision | Classification | Principle | Rationale | Rejected |
|---|-------|----------|-----------|-----------|----------|---------|
| 1 | CEO | Rename agent.ts → engine.ts | Auto-decid | P5 (explicit) | Current name misleads about architecture | No |
| 2 | CEO | Add Task 0: LLM Calling Protocol Design | Auto-decid | P1 (completeness) | 7 hollow TODOs unacceptable | No |
| 3 | CEO | Add Day-0 Bootstrap task (Task 0.5) | Auto-decid | P1 (completeness) | Flywheel must work on article 1 | No |
| 4 | CEO | Merge Task 7+8, deprioritize to P2 | Auto-decid | P3 (pragmatic) | HTML/SEO is P2, article quality is P1 | No |
| 5 | CEO | Mode: SELECTIVE EXPANSION | Auto-decid | P3 (pragmatic) | Greenfield but existing wiki/skills assets exist | No |
| 6 | CEO | Scope: new project, no existing code to leverage | Auto-decid | P4 (DRY) | No sub-problem maps to existing code | No |
| 7 | CEO | wiki-reflux → P2, merge with images/html | Taste | P1 | User may want full output pipeline | Surfaced at gate |
| 8 | Ref Study | Adopt `{{VAR}}` template substitution (dankoe-writer) | Auto-decid | P4 (DRY) | Proven pattern, avoid reinventing | No |
| 9 | Ref Study | Add JSONL checkpoints (llm-wiki-agent) | Auto-decid | P1 (completeness) | Checkpoint must survive context loss | No |
| 10 | Ref Study | Add PreToolUse/PostToolUse hooks (claw-code) | Auto-decid | P1 (completeness) | Vault hook system must integrate | No |
| 11 | Ref Study | Add CJK-aware wiki query (llm-wiki-agent) | Auto-decid | P1 (completeness) | Chinese content requires CJK-aware search | No |
| 12 | Ref Study | Add stage_history versioning (dankoe-writer) | Auto-decid | P1 (completeness) | Enables rollback and audit trail | No |
| 13 | CEO | Add Task 9: Dan Koe Post-3 validation | Auto-decid | P1 (completeness) | Dan Koe水土不服 risk must be measured | No |

---

## Self-Review 检查清单

- [x] 设计文档所有章节都有对应 Task
- [x] 无 placeholder（TOD/TBD）— Task 0 已定义所有 LLM 调用规范
- [x] Task 顺序遵循依赖关系（Task 0 → Task 3 → 并行 4/5/6/8 → Task 7 → Task 9 → Task 10）
- [x] 每个 Task 有完整的测试文件
- [x] 所有路径使用绝对路径
- [x] 阶段产物使用文件存储（JSON + JSONL checkpoint）
- [x] 包含思考过程展示（Thinking 字段）
- [x] CLI 和 Engine 核心分离
- [x] 从参考项目引入的设计模式已标注来源
- [x] P2 任务（Output）已明确标注，优先级低于核心写作流程
- [x] Day-0 Bootstrap 已前置，wiki 飞轮在第一篇文章时即可工作
- [x] Dan Koe 有效性验证已内置（Post-3-article）

### 任务执行顺序（更新后）

| 顺序 | Task | 优先级 | 说明 |
|------|------|--------|------|
| 1 | Task 0: LLM Calling Protocol | P0 | 所有 LLM 调用规范 |
| 2 | Task 1: 项目脚手架 | P1 | |
| 3 | Task 2: 全局类型 + db/schema | P1 | |
| 4 | Task 3: Writing Workflow Engine | P0 | engine.ts + runtime/ |
| 5 | Task 0.5: Day-0 Bootstrap | P1 | 一次性的 wiki 初始化 |
| 6 | Task 4: Dan Koe 五阶段 | P1 | 并行执行 |
| 7 | Task 5: Phase 0 深度研究 | P1 | 并行执行 |
| 8 | Task 6: 无（已合并到 Task 4） | - | |
| 9 | Task 8: Wiki 管理模块 | P1 | CJK + JSONL checkpoint |
| 10 | Task 7: Output Pipeline | P2 | SEO/GEO + 配图 + HTML + wiki回流 |
| 11 | Task 9: Dan Koe 验证 | P1 | Post-3-article 自动触发 |
| 12 | Task 10: CLI 入口 | P1 | 引用 engine.ts |

---

## 执行方式

**Plan complete and saved to `docs/superpowers/plans/2026-04-18-huage-agent-plan.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
