# Toonflow 核心 Agent 实现

## 一、OutlineScript Agent（大纲剧本生成）

### 1.1 架构概述

```
用户请求
    ↓
WebSocket /outline/agentsOutline
    ↓
OutlineScript.call()
    ↓
┌────────────────────────────────────────────────────────────┐
│                     Main Agent                              │
│  - 协调 AI1(故事师)、AI2(大纲师)、director(导演)          │
│  - 管理对话历史                                            │
│  - 构建环境上下文                                          │
└────────────────────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────────────┐
│                    Tool System                             │
│  - getChapter / getStoryline / saveStoryline              │
│  - getOutline / saveOutline / updateOutline               │
│  - generateAssets                                         │
└────────────────────────────────────────────────────────────┘
```

### 1.2 三 Agent 协作流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    AI1      │     │    AI2      │     │  director   │
│  (故事师)   │     │  (大纲师)   │     │   (导演)    │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ 分析小说    │     │ 生成大纲    │     │ 审核质量    │
│ 生成故事线  │────▶│ 转换剧本    │────▶│ 75分及格    │
│             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 1.3 核心 Prompt（存储在 t_prompts 表）

#### outlineScript-main（主调度 Agent）

职责：
- 协调故事师(AI1)、大纲师(AI2)、导演(director)工作流程
- 强制执行阶段转换规则
- 管理用户确认环节
- 禁止自行生成/修改大纲内容

#### outlineScript-a1（故事师）

职责：
- 调用 getChapter 获取小说原文
- 分析生成故事线
- 调用 saveStoryline 保存结果

分析维度：
- 全局扫描：核心事件、节奏、转折点
- 深度解构：动机链、因果关系、情感波动
- 模式识别：叙事模式、伏笔布局、主题递进

#### outlineScript-a2（大纲师）

核心方法论（八大法则）：

| 法则 | 说明 |
|-----|------|
| 剃刀法则 | 删除冗余，3章压缩为1集 |
| 视觉外化 | 禁止心理描写，改用动作/表情 |
| 情绪过山车 | 压抑→爆发→打脸→获益 |
| 黄金节奏 | 前3秒冲突，15秒矛盾，45秒高潮 |
| 身份势能 | 阶级落差、身份反转 |
| 群像压迫 | 多对一格局 |
| 道具图腾化 | 道具承载情感 |
| 台词利刃化 | 金句≤15字 |

#### outlineScript-director（导演）

审核标准：
- 75分及格线
- 每轮最多5个问题
- 同一问题只要求修改1次
- 第3轮必须强制通过

### 1.4 工具定义示例

```typescript
// 定义工具（使用 Vercel AI SDK）
getChapter = tool({
  title: "getChapter",
  description: "获取小说章节原文",
  inputSchema: z.object({
    chapterNumbers: z.array(z.number())
  }),
  execute: async ({ chapterNumbers }) => {
    // 从数据库获取章节内容
    const results = await Promise.all(
      chapterNumbers.map(async (num) => {
        const chapter = await u.db("t_novel")
          .where({ projectId, chapterIndex: num })
          .first();
        return chapter;
      })
    );
    return results.join("\n\n---\n");
  }
});
```

### 1.5 核心数据结构

```typescript
// Episode 大纲数据结构
interface Episode {
  episodeIndex: number;      // 集数索引
  title: string;             // 8字内标题，含情绪爆点
  chapterRange: number[];    // 关联章节号

  scenes: AssetItem[];      // 场景列表（置景参考）
  characters: AssetItem[];  // 角色列表（选角参考）
  props: AssetItem[];        // 道具列表（≥3个）

  coreConflict: string;       // 核心矛盾
  outline: string;           // ★剧情主干，最高优先级
  openingHook: string;       // 开篇第一个镜头
  keyEvents: string[];       // [起, 承, 转, 合]
  emotionalCurve: string;    // 情绪曲线
  visualHighlights: string[]; // 标志性镜头
  endingHook: string;        // 结尾悬念
  classicQuotes: string[];   // 金句
}

interface AssetItem {
  name: string;
  description: string;
}
```

### 1.6 WebSocket 通信

```typescript
// routes/outline/agentsOutline.ts
router.ws("/", async (ws, req) => {
  const agent = new OutlineScript(projectId);

  // 事件监听
  agent.emitter.on("data", (text) => {
    ws.send(JSON.stringify({ type: "stream", data: text }));
  });

  agent.emitter.on("response", (text) => {
    ws.send(JSON.stringify({ type: "response_end", data: text }));
  });

  agent.emitter.on("subAgentStream", (data) => {
    ws.send(JSON.stringify({ type: "subAgentStream", data }));
  });

  agent.emitter.on("toolCall", (data) => {
    ws.send(JSON.stringify({ type: "toolCall", data }));
  });

  // 消息处理
  ws.on("message", async (rawData) => {
    const data = JSON.parse(rawData);
    if (data.type === "msg") {
      await agent.call(data.data);
    }
  });
});
```

---

## 二、Storyboard Agent（分镜生成）

### 2.1 架构概述

```
用户请求
    ↓
WebSocket /storyboard/chatStoryboard
    ↓
Storyboard.call()
    ↓
┌────────────────────────────────────────────────────────────┐
│                     Main Agent                              │
│  - 协调 segmentAgent(片段师)、shotAgent(分镜师)           │
│  - 管理片段和分镜数据                                      │
│  - 处理图片生成流程                                        │
└────────────────────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────────────┐
│                    Tool System                             │
│  - getScript / getAssets                                   │
│  - getSegments / updateSegments                            │
│  - addShots / updateShots / deleteShots                   │
│  - generateShotImage                                       │
└────────────────────────────────────────────────────────────┘
```

### 2.2 两 Agent 协作流程

```
用户: 生成片段
    ↓
Main Agent → segmentAgent
    ↓
segmentAgent.getScript() → 获取剧本
segmentAgent.updateSegments() → 保存片段
    ↓
返回片段列表给用户

用户: 生成分镜
    ↓
Main Agent → 获取用户选择的片段 + 宫格数量
    ↓
Main Agent → shotAgent
    ↓
shotAgent.getSegments() → 获取片段
shotAgent.addShots() → 保存分镜
shotAgent.generateShotImage() → 生成图片
    ↓
异步执行图片生成，完成后通知前端
```

### 2.3 数据结构

```typescript
// 片段
interface Segment {
  index: number;
  description: string;
  emotion?: string;
  action?: string;
}

// 分镜
interface Shot {
  id: number;              // 分镜独立ID
  segmentId: number;        // 所属片段ID
  title: string;
  x: number;
  y: number;
  cells: Array<{            // 镜头数组
    src?: string;
    prompt?: string;
    id?: string;
  }>;
  fragmentContent: string;
  assetsTags: AssetsType[];
}

interface AssetsType {
  type: "role" | "props" | "scene";
  text: string;
}
```

### 2.4 分镜图生成流程

```
1. 收集分镜中所有镜头的提示词
2. 合并为宫格图片生成提示词
3. 调用 AI 图片生成服务
4. 接收返回的宫格图片
5. 使用 Sharp 分割为单个镜头
6. 上传到 OSS 存储
7. 更新分镜数据结构中的 src 字段
8. 通知前端更新显示
```

---

## 三、通用 Agent 架构模式

### 3.1 工具系统

每个 Agent 都使用 Vercel AI SDK 的 `tool()` 定义工具：

```typescript
import { tool } from "ai";
import { z } from "zod";

const myTool = tool({
  title: "toolName",
  description: "工具描述",
  inputSchema: z.object({
    param1: z.string(),
    param2: z.number().optional()
  }),
  execute: async ({ param1, param2 }) => {
    // 执行逻辑
    return "结果";
  }
});
```

### 3.2 上下文构建

```typescript
private async buildEnvironmentContext(): Promise<string> {
  // 获取项目信息
  const projectInfo = await u.db("t_project").where({ id: this.projectId }).first();

  // 获取资产信息
  const assets = await u.db("t_assets").where({ projectId: this.projectId }).select();

  return `<环境信息>
项目ID: ${this.projectId}
项目名称: ${projectInfo?.name}
资产列表:
${assets.map(a => `- ${a.name}: ${a.intro}`).join("\n")}
</环境信息>`;
}
```

### 3.3 流式响应

```typescript
const { fullStream } = await u.ai.text.stream(
  {
    system: systemPrompt,
    tools: toolsObject,
    messages: this.history,
    maxStep: 100
  },
  promptConfig  // AI 模型配置
);

let fullResponse = "";
for await (const item of fullStream) {
  if (item.type === "text-delta") {
    fullResponse += item.text;
    this.emit("data", item.text);  // 实时推送
  }
}
```

### 3.4 事件驱动

```typescript
// 继承 EventEmitter
import { EventEmitter } from "events";

class MyAgent {
  readonly emitter = new EventEmitter();

  async call(msg: string) {
    // 触发事件
    this.emit("data", "部分响应");
    this.emit("response", "完整响应");
  }
}

// 监听事件
agent.emitter.on("data", (text) => {
  ws.send(JSON.stringify({ type: "stream", data: text }));
});
```
