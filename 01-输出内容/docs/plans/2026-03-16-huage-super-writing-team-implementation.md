# 华哥超级写作工作团智能体 - 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use mcp-builder 创建 MCP 服务器来实现多智能体编排

**Goal:** 创建一个多智能体编排系统，自动完成小红书爆款内容从研究到创作的完整工作流

**Architecture:** 采用 MCP (Model Context Protocol) 架构，主智能体 huage-super-writing-team 作为编排中心，协调 huage-deep-research、youtube-research-flow、notebooklm、obsidian、huagexiaohongshu、humanizer-zh、baoyu-xhs-images 等子智能体完成工作流

**Tech Stack:** MCP Server、Node.js/TypeScript、Claude API

---

## 任务1: 创建 MCP 服务器项目结构

**Files:**
- Create: `mcp-servers/huage-super-writing-team/package.json`
- Create: `mcp-servers/huage-super-writing-team/tsconfig.json`
- Create: `mcp-servers/huage-super-writing-team/src/index.ts`
- Create: `mcp-servers/huage-super-writing-team/src/types.ts`

**Step 1: 创建项目目录和初始化**

```bash
mkdir -p mcp-servers/huage-super-writing-team/src
cd mcp-servers/huage-super-writing-team
npm init -y
npm install @modelcontextprotocol/sdk typescript @types/node
```

**Step 2: 创建 package.json**

```json
{
  "name": "huage-super-writing-team",
  "version": "1.0.0",
  "description": "华哥超级写作工作团 - 小红书爆款内容创作多智能体系统",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0"
  }
}
```

**Step 3: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true
  }
}
```

**Step 4: 创建 types.ts**

```typescript
export interface ResearchResult {
  articles: string[];
  videos: string[];
  summary: string;
}

export interface NotebookAnalysis {
  notebookId: string;
  insights: string[];
}

export interface DraftContent {
  title: string;
  body: string;
  tags: string[];
  images: string[];
}

export interface FinalContent extends DraftContent {
  finalBody: string;
  coverImage: string;
  supportingImages: string[];
}

export type WorkflowStage =
  | 'research'
  | 'notebooklm_analysis'
  | 'knowledge_archive'
  | 'user_confirm_direction'
  | 'draft_creation'
  | 'user_confirm_draft'
  | 'humanize'
  | 'image_generation'
  | 'final_archive';

export interface WorkflowState {
  stage: WorkflowStage;
  topic: string;
  researchResult?: ResearchResult;
  notebookAnalysis?: NotebookAnalysis;
  draftContent?: DraftContent;
  finalContent?: FinalContent;
  userFeedback?: string;
}
```

---

## 任务2: 实现 MCP 服务器主逻辑

**Files:**
- Modify: `mcp-servers/huage-super-writing-team/src/index.ts`

**Step 1: 编写主服务器代码**

```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

class HuageSuperWritingTeam {
  private server: Server;
  private state: any = {};

  constructor() {
    this.server = new Server(
      { name: 'huage-super-writing-team', version: '1.0.0' },
      { capabilities: { tools: {} } }
    );
    this.setupTools();
  }

  private setupTools() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'start_writing_workflow',
          description: '启动华哥超级写作工作团工作流，从研究到创作完整流程',
          inputSchema: {
            type: 'object',
            properties: {
              topic: { type: 'string', description: '创作主题' }
            },
            required: ['topic']
          }
        },
        {
          name: 'research_topic',
          description: '双通道并行研究：文章+视频',
          inputSchema: {
            type: 'object',
            properties: {
              topic: { type: 'string', description: '研究主题' }
            },
            required: ['topic']
          }
        },
        {
          name: 'create_notebooklm_analysis',
          description: '调用 NotebookLM 整理研究结果',
          inputSchema: {
            type: 'object',
            properties: {
              researchData: { type: 'object', description: '研究数据' }
            },
            required: ['researchData']
          }
        },
        {
          name: 'archive_to_obsidian',
          description: '归档到 Obsidian 知识库',
          inputSchema: {
            type: 'object',
            properties: {
              content: { type: 'string', description: '归档内容' }
            },
            required: ['content']
          }
        },
        {
          name: 'create_draft_with_xiaohongshu',
          description: '用 huagexiaohongshu 共创初稿',
          inputSchema: {
            type: 'object',
            properties: {
              researchSummary: { type: 'string', description: '研究摘要' }
            },
            required: ['researchSummary']
          }
        },
        {
          name: 'humanize_content',
          description: '降AI味生成终稿',
          inputSchema: {
            type: 'object',
            properties: {
              content: { type: 'string', description: '待优化内容' }
            },
            required: ['content']
          }
        },
        {
          name: 'generate_images',
          description: '生成封面和配图',
          inputSchema: {
            type: 'object',
            properties: {
              title: { type: 'string', description: '笔记标题' },
              content: { type: 'string', description: '笔记内容' }
            },
            required: ['title', 'content']
          }
        },
        {
          name: 'get_user_feedback',
          description: '获取用户反馈',
          inputSchema: {
            type: 'object',
            properties: {
              stage: { type: 'string', description: '当前阶段' }
            },
            required: ['stage']
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case 'start_writing_workflow':
          return await this.startWorkflow(args.topic);
        case 'research_topic':
          return await this.researchTopic(args.topic);
        case 'create_notebooklm_analysis':
          return await this.createNotebookAnalysis(args.researchData);
        case 'archive_to_obsidian':
          return await this.archiveToObsidian(args.content);
        case 'create_draft_with_xiaohongshu':
          return await this.createDraft(args.researchSummary);
        case 'humanize_content':
          return await this.humanizeContent(args.content);
        case 'generate_images':
          return await this.generateImages(args.title, args.content);
        case 'get_user_feedback':
          return await this.getUserFeedback(args.stage);
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });
  }

  private async startWorkflow(topic: string) {
    this.state = { topic, stage: 'research' };
    return {
      content: [{ type: 'text', text: `工作流已启动，主题：${topic}` }]
    };
  }

  private async researchTopic(topic: string) {
    // 并行调用 huage-deep-research 和 youtube-research-flow
    return {
      content: [{ type: 'text', text: `正在研究：${topic}` }]
    };
  }

  private async createNotebookAnalysis(researchData: any) {
    return {
      content: [{ type: 'text', text: 'NotebookLM 分析完成' }]
    };
  }

  private async archiveToObsidian(content: string) {
    return {
      content: [{ type: 'text', text: '已归档到 Obsidian 知识库' }]
    };
  }

  private async createDraft(researchSummary: string) {
    return {
      content: [{ type: 'text', text: '初稿已生成' }]
    };
  }

  private async humanizeContent(content: string) {
    return {
      content: [{ type: 'text', text: '降AI味完成' }]
    };
  }

  private async generateImages(title: string, content: string) {
    return {
      content: [{ type: 'text', text: '图片生成完成' }]
    };
  }

  private async getUserFeedback(stage: string) {
    return {
      content: [{ type: 'text', text: `请确认${stage}阶段的成果` }]
    };
  }

  async start() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('华哥超级写作工作团 MCP 服务器已启动');
  }
}

const server = new HuageSuperWritingTeam();
server.start();
```

**Step 2: 编译并测试**

```bash
npm run build
```

---

## 任务3: 创建智能体定义文件

**Files:**
- Create: `AI智能体/huage-super-writing-team.md`

**Step 1: 创建智能体定义**

```markdown
---
name: 华哥超级写作工作团
description: 多智能体编排系统，自动完成小红书爆款内容从研究到创作的完整工作流。触发条件：用户需要创作小红书笔记且需要进行前期研究时使用。
color: "#FF2442"
---

# 华哥超级写作工作团

你是**华哥超级写作工作团**的智能体编排中心，负责协调多个子智能体完成小红书爆款内容创作的完整工作流。

## 你的身份

- **角色**：智能体编排师 + 内容创作流程管理者
- **个性**：有条理、注重用户体验、善于协调

## 核心工作流

1. **双通道并行研究**
   - 调用 huage-deep-research 搜索文章
   - 调用 youtube-research-flow 搜索视频

2. **NotebookLM 整理**
   - 创建笔记本分析研究结果
   - 生成可交付的研究报告

3. **Obsidian 归档**
   - 存档为知识库
   - 建立索引

4. **用户确认方向** ⚠️
   - 展示研究结果
   - 让用户选择创作角度

5. **共创初稿**
   - 调用 huagexiaohongshu
   - 与用户讨论标题/风格

6. **用户确认初稿** ⚠️
   - 展示初稿
   - 收集修改意见

7. **降AI味**
   - 调用 humanizer-zh

8. **生图配图**
   - 调用 baoyu-xhs-images

9. **最终存档**
   - 排版输出
   - Obsidian 归档

## 交互节点

| 节点 | 交互内容 |
|------|----------|
| 1 | 输入创作主题 |
| 2 | 研究完成后确认方向 |
| 3 | 初稿完成后确认 |
| 4 | 终稿完成后确认 |
```

---

## 任务4: 创建技能包装器

为了在实际工作流中调用各个子技能，需要创建技能调用封装。

**Files:**
- Create: `mcp-servers/huage-super-writing-team/src/skills/invoke-skill.ts`

```typescript
// 技能调用封装示例
export async function invokeSkill(skillName: string, args: any): Promise<any> {
  // 这里需要集成实际的技能调用逻辑
  // 可以通过子进程调用或 MCP 协议
  console.log(`调用技能: ${skillName}`, args);
  return { success: true };
}
```

---

## 实现检查清单

- [ ] MCP 服务器项目结构创建完成
- [ ] 主服务器逻辑实现
- [ ] 智能体定义文件创建
- [ ] 技能调用封装
- [ ] 本地测试运行

---

## 依赖技能

- @mcp-builder (创建 MCP 服务器)
- huage-deep-research
- youtube-research-flow
- notebooklm
- obsidian
- huagexiaohongshu
- humanizer-zh
- baoyu-xhs-images
