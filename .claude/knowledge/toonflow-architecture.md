# Toonflow 全架构深度分析
> 来源：`/Users/huage/Downloads/Toonflow-app-master`（v1.0.7，AGPL-3.0）
> 分析时间：2026-04-07
> 目的：为 huage888（Claude漫剧生产系统）提供完整参考蓝图

---

## 一、核心技术架构

### 1.1 技术栈快照

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 后端框架 | Express.js 5 + TypeScript | 轻量、高性能 |
| 数据库 | SQLite（better-sqlite3） | 单文件、零运维 |
| AI SDK | `ai` SDK（Vercel AI）| 统一文本/图像/视频调用 |
| 流式传输 | WebSocket（express-ws） | 实时 token 推送 |
| 桌面端 | Electron 40 | 可选 GUI 包装 |
| 图像处理 | Sharp | 高性能 Node.js 图像库 |
| ORM | Knex.js | SQLite 查询构造器 |
| 前端 | 独立仓库（Toonflow-web） | 可单独部署 |
| 容器化 | Docker + docker-compose | 一键部署 |

### 1.2 目录结构

```
Toonflow-app-master/
├── src/
│   ├── agents/                    # AI Agent 核心模块
│   │   ├── outlineScript/         # 大纲脚本 Agent（小说→大纲→资产）
│   │   └── storyboard/            # 分镜 Agent（大纲→分镜→图片）
│   ├── routes/                    # 路由层（按业务域划分）
│   │   ├── novel/                 # 小说管理
│   │   ├── outline/               # 大纲管理（含 agentsOutline WS）
│   │   ├── script/                 # 剧本生成
│   │   ├── storyboard/            # 分镜管理（含 chatStoryboard WS）
│   │   ├── assets/                # 资产管理
│   │   ├── video/                  # 视频生成
│   │   ├── setting/                # 模型配置
│   │   ├── project/                # 项目管理
│   │   ├── prompt/                 # Prompt 管理
│   │   └── task/                   # 任务中心
│   ├── utils/ai/
│   │   ├── text/                   # LLM 调用（modelList + adapter）
│   │   ├── image/                  # 图像生成（多厂商适配器）
│   │   │   └── owned/              # volcengine/kling/vidu/wan/gemini/...
│   │   └── video/                  # 视频生成（多厂商适配器）
│   │       └── owned/              # volcengine/kling/vidu/wan/...
│   ├── lib/
│   │   ├── artStyle.ts             # 200+ 艺术风格库
│   │   ├── initDB.ts               # 数据库初始化
│   │   └── responseFormat.ts       # 统一响应格式
│   ├── types/database.d.ts         # 完整 TypeScript 类型声明
│   └── app.ts                       # Express 入口，JWT 鉴权
├── docker/                          # Docker 配置
├── scripts/                          # 构建脚本 + Electron 入口
└── docs/                             # 文档资源
```

---

## 二、数据模型（完整 TypeScript 类型）

### 2.1 核心业务表

| 表名 | 用途 | 核心字段 |
|------|------|---------|
| `t_project` | 项目 | id, name, intro, type, artStyle, videoRatio |
| `t_novel` | 小说原文 | id, projectId, chapterIndex, chapter, chapterData, reel |
| `t_storyline` | 故事线 | id, projectId, content, novelIds |
| `t_outline` | 大纲（JSON字段） | id, projectId, episode, **data(JSON)** |
| `t_script` | 剧本 | id, projectId, outlineId, name, content |
| `t_assets` | 资产（角色/场景/道具） | id, projectId, type, name, intro, prompt, filePath, segmentId, shotIndex |
| `t_storyboardScript` | 分镜-剧本关联 | scriptId, storyboardId |
| `t_video` | 生成的视频 | id, projectId, scriptId, configId, model, prompt, filePath, state |
| `t_videoConfig` | 视频配置 | id, projectId, scriptId, images, prompt, duration, resolution, manufacturer, mode |
| `t_chatHistory` | Agent对话历史 | id, projectId, type, data(JSON), novel(JSON) |
| `t_prompts` | Prompt模板 | code, name, type, defaultValue, customValue |
| `t_artStyle` | 用户自定义风格 | id, name, styles |
| `t_config` | AI模型配置 | id, manufacturer, model, apiKey, baseUrl, modelType, type |
| `t_taskList` | 任务队列 | id, name, state, prompt, startTime, endTime |

### 2.2 Outline Data（JSON字段）核心结构

```typescript
interface EpisodeData {
  episodeIndex: number;         // 集数
  title: string;                 // 8字标题
  chapterRange: number[];       // 章节范围
  scenes: { name, description }[];     // 场景列表
  characters: { name, description }[]; // 角色列表
  props: { name, description }[];     // 道具列表
  coreConflict: string;          // 核心矛盾
  outline: string;               // 剧情主干（最高优先级）
  openingHook: string;           // 开场镜头
  keyEvents: string[4];          // [起, 承, 转, 合]
  emotionalCurve: string;         // 情绪曲线
  visualHighlights: string[];     // 标志性镜头
  endingHook: string;            // 结尾悬念
  classicQuotes: string[];       // 金句
}
```

### 2.3 Shot 数据结构

```typescript
interface Shot {
  id: number;                    // 分镜独立ID
  segmentId: number;              // 所属片段ID
  title: string;
  x: number; y: number;
  cells: { src?, prompt?, id? }[]; // 镜头数组（每个cell=一个镜头）
  fragmentContent: string;
  assetsTags: { type: "role"|"props"|"scene", text }[];
}
```

---

## 三、Agent 系统详解

### 3.1 OutlineScript Agent（大纲师）

**文件**：`src/agents/outlineScript/index.ts`

**职责**：将小说原文转换为结构化大纲和资产

**三个 Sub-Agent**：
- **AI1（故事师）**：分析小说原文 → 生成故事线（saveStoryline）
- **AI2（大纲师）**：根据故事线 → 生成多集大纲（saveOutline，Zod验证）
- **Director（导演）**：审核故事线和大纲，调用 updateOutline 修改

**核心 Tool**：
| Tool | 功能 |
|------|------|
| `getChapter` | 按章节号批量获取小说原文 |
| `getStoryline` | 获取当前故事线 |
| `saveStoryline` | 保存/覆盖故事线 |
| `deleteStoryline` | 删除故事线 |
| `getOutline(simplified)` | 获取大纲（列表或详细） |
| `saveOutline(episodes, overwrite)` | 批量保存大纲（Zod强校验） |
| `updateOutline(id, data)` | 更新指定集大纲 |
| `deleteOutline(ids)` | 删除大纲及关联数据 |
| `generateAssets` | 从所有大纲提取角色/场景/道具，存入t_assets |

**Context 构建**：
```
<环境信息>
项目ID, 系统时间
小说名称/简介/类型/风格/画幅
已加载章节列表
故事线状态, 大纲状态
可用工具清单
</环境信息>

<对话历史>
role: content 对话记录
</对话历史>

<当前任务>
用户任务描述
</当前任务>
```

**资产生成流程**：
1. 读取所有 outline 的 data(JSON) 字段
2. 提取 characters/props/scenes → 去重（uniqueByName）
3. upsert 到 t_assets 表（insert/update/skipped 三种状态）

**流式输出**：通过 `EventEmitter` → WebSocket 推送 `stream` / `response_end` / `toolCall` / `transfer` / `refresh` 事件

---

### 3.2 Storyboard Agent（分镜师）

**文件**：`src/agents/storyboard/index.ts`

**职责**：将剧本转换为分镜和图像

**两个 Sub-Agent**：
- **segmentAgent（片段师）**：读取剧本 → 生成片段（Segment[]）
- **shotAgent（分镜师）**：读取片段 → 生成分镜（Shot，含多个cells）

**核心 Tool**：
| Tool | 功能 |
|------|------|
| `getScript` | 获取剧本内容 |
| `getAssets` | 获取资产列表（含一致性约束警告） |
| `getSegments` | 获取当前片段数据 |
| `updateSegments(segments)` | 保存片段结果 |
| `addShots(shots[])` | 添加分镜（分配独立ID） |
| `updateShots(shotId, prompts[])` | 更新指定分镜的镜头提示词 |
| `deleteShots(shotIds[])` | 删除分镜 |
| `generateShotImage(shotIds[])` | 异步生成分镜图（后台执行） |

**分镜图生成流程**（异步，不阻塞Agent）：
1. `generateShotImage` 标记 shotIds 为 generating 状态
2. 调用 `generateImageTool`：多个prompt → 合并为宫格图
3. 调用 `imageSplitting`：Sharp 切割宫格为单张
4. 上传到 OSS
5. 更新 cells 的 src 字段
6. 触发 `shotImageGenerateComplete` 事件

**资产一致性强制规则**（在 `getAssets` Tool 中硬编码）：
```
⚠️ 重要规则：
1. 必须原封不动地使用上述资产名称，禁止使用近义词、缩写或任何变体
2. 禁止在资产名称前后添加修饰词
3. 禁止捏造资产列表中不存在的角色、场景、道具
```

---

## 四、AI 适配器架构

### 4.1 多厂商图像生成适配器

**注册中心**：`src/utils/ai/image/index.ts`

```typescript
const modelInstance = {
  gemini: gemini,
  volcengine: volcengine,
  kling: kling,
  vidu: vidu,
  runninghub: runninghub,
  modelScope: modelScope,
  other: other,
  grsai: grsai,
  formal: formal,
};
// 调用：manufacturerFn(input, { model, apiKey, baseURL })
```

**各厂商实现**（`src/utils/ai/image/owned/`）：
- `volcengine.ts` — 火山引擎
- `kling.ts` — 快手可灵
- `vidu.ts` — 生数 Vidu
- `gemini.ts` — Google Gemini
- `wan.ts` — 通义万相
- `runninghub.ts` — RunningHub
- `apimart.ts` — API Mart
- `modelScope.ts` — 魔搭
- `other.ts` — OpenAI 兼容格式
- `formal.ts` — 备用通道

### 4.2 多厂商视频生成适配器

**注册中心**：`src/utils/ai/video/index.ts`

```typescript
const modelInstance = {
  volcengine: volcengine,
  kling: kling,
  vidu: vidu,
  wan: wan,
  gemini: gemini,
  runninghub: runninghub,
  apimart: apimart,
  other: other,
  grsai: grsai,
  formal: formal,
};
```

### 4.3 文本模型适配器

**文件**：`src/utils/ai/text/index.ts` + `src/utils/ai/text/modelList.ts`

支持：Anthropic / DeepSeek / Google / OpenAI / xAI 等，通过 `ai` SDK 统一调用。

### 4.4 配置模型表（t_config）

```typescript
interface t_config {
  id: number;
  manufacturer: string;    // 厂商标识
  model: string;           // 模型名称
  apiKey: string;
  baseUrl: string;        // API 端点
  modelType: string;       // text | image | video
  type: string;           // 用途分类
  userId: number;
}
```

---

## 五、WebSocket 实时通信架构

### 5.1 两个核心 WS 端点

**1. 大纲 Agent**：`POST /outline/agents` → WebSocket upgrade
**2. 分镜 Agent**：`POST /storyboard/chat` → WebSocket upgrade

### 5.2 统一事件类型

| 事件名 | 方向 | 含义 |
|--------|------|------|
| `init` | 服务端→客户端 | 初始化完成，可以发消息 |
| `stream` | 服务端→客户端 | Agent 逐 token 流式输出 |
| `response_end` | 服务端→客户端 | 完整回复结束 |
| `toolCall` | 服务端→客户端 | 工具被调用 |
| `transfer` | 服务端→客户端 | Sub-Agent 切换 |
| `refresh` | 服务端→客户端 | 数据刷新通知 |
| `subAgentStream` | 服务端→客户端 | Sub-Agent 流式输出 |
| `subAgentEnd` | 服务端→客户端 | Sub-Agent 结束 |
| `segmentsUpdated` | 服务端→客户端 | 片段数据更新 |
| `shotsUpdated` | 服务端→客户端 | 分镜数据更新 |
| `shotImageGenerateStart` | 服务端→客户端 | 分镜图开始生成 |
| `shotImageGenerateProgress` | 服务端→客户端 | 分镜图生成进度 |
| `shotImageGenerateComplete` | 服务端→客户端 | 分镜图生成完成 |
| `shotImageGenerateError` | 服务端→客户端 | 分镜图生成失败 |
| `error` | 服务端→客户端 | 异常错误 |

### 5.3 客户端消息类型

| 类型 | 含义 |
|------|------|
| `msg` | 发送对话消息 |
| `cleanHistory` | 清空对话历史 |
| `generateShotImage` | 触发分镜图生成 |
| `replaceShot` | 手动替换分镜图片 |

---

## 六、完整生产流水线

```
小说原文 (t_novel)
    │
    ▼
[OutlineScript Agent] ──WebSocket──▶ 前端实时流
    │
    ├── AI1 (故事师) ──▶ 故事线 (t_storyline)
    │
    ├── AI2 (大纲师) ──▶ 大纲 (t_outline, EpisodeData[])
    │                        ├── episodeIndex, title
    │                        ├── characters/props/scenes
    │                        ├── coreConflict, outline
    │                        ├── keyEvents[起承转合]
    │                        └── emotionalCurve, visualHighlights
    │
    └── Director (导演) ──▶ 审核/修改大纲
           │
           ▼
    [资产生成] ──▶ t_assets (角色/场景/道具)
           │
           ▼
    剧本生成 (t_script.content)
           │
           ▼
[Storyboard Agent] ──WebSocket──▶ 前端实时流
           │
           ├── segmentAgent ──▶ Segment[] (片段)
           │
           └── shotAgent ──▶ Shot[] (分镜)
                                └── cells: [{prompt, src?}]
           │
           ▼
    [分镜图生成] ──异步──▶ t_assets.filePath
           │
           ├── generateImageTool() ──▶ 宫格图（多prompt合并）
           ├── imageSplitting() ──▶ Sharp 切割
           └── OSS 上传
           │
           ▼
    视频合成 (t_video)
           │
           ├── 选择分镜图 (t_videoConfig.images)
           ├── 视频提示词 (t_videoConfig.prompt)
           ├── 厂商选择 (manufacturer: kling|vidu|wan|...)
           └── 视频生成 → OSS → t_video.filePath
```

---

## 七、图像生成细节

### 7.1 generateImageTool 流程

```
输入：cells: { prompt }[], scriptId, projectId

1. 从 t_assets 提取相关资产（AI过滤 + 按type排序）
2. 构建资产映射提示词："人物A=图片1, 场景B=图片2"
3. 调用 generateImagePromptsTool 生成优化后的prompt + 宫格布局
4. 图片预处理（压缩 ≤3MB/张，总计 ≤10MB）
5. 调用图像适配器（u.ai.image），传入资产图片作为参考
6. 返回宫格图 Buffer
```

### 7.2 imageSplitting 宫格切割

使用 Sharp 将宫格图按 cols×rows 切割为单张，返回 Buffer[]。

---

## 八、艺术风格库

**文件**：`src/lib/artStyle.ts`

200+ 风格，分为 6 大类：
- **常用风格**：2D动漫、真人写实、3D国创、三渲二、吉卜力等
- **IP风格**：龙族传说、比奇堡、草帽团、蜡笔小新等
- **插画风格**：水彩、素描、波普、赛璐璐、浮世绘等
- **可爱Q版**：Q萌马克笔、比奇堡、像素、动森等
- **立体风格**：Q版3D、空灵现实、方块世界、乐高等
- **日系风格**：少女漫、东方古典、80s年代等

每个风格包含：`name`, `prompt`（中英文版本）, `fileUrl`（预览图）。

---

## 九、huage888 实现差距分析

### 已具备能力（对照 MEMORY.md）
- ✅ 漠玫传分镜脚本（25镜头/45秒）
- ✅ 资产注册表（待填element_id）
- ✅ 赛博墨韵风格锚定词
- ✅ 角色描述词/场景描述词
- ✅ LibTV 手动执行流程

### 差距项

| 差距 | Toonflow 方案 | huage888 现状 |
|------|-------------|-------------|
| Agent 系统 | 完整 Multi-Agent（AI1/AI2/Director/segmentAgent/shotAgent） | 无，需新建 |
| WebSocket 流式 | 完整 WS 事件系统 | 无 |
| 数据库持久化 | SQLite 完整表结构 | Obsidian Vault Markdown |
| 资产一致性 | getAssets Tool 强制约束 | 手动对照 |
| 风格库 | 200+ 风格预设 | 仅赛博墨韵锚定词 |
| 图像适配器 | 多厂商适配器注册中心 | 仅 Doubao/即梦 |
| 视频适配器 | 同上 + OSS 上传 | 仅即梦图生视频 |
| 宫格图+切割 | Sharp 自动处理 | 手动9宫格 |
| Prompt 工程 | t_prompts 表模板化 | 散落在文档中 |
| 任务队列 | t_taskList 表 | 无 |

---

## 十、关键源码文件索引

| 文件 | 行数 | 核心价值 |
|------|------|---------|
| `src/agents/outlineScript/index.ts` | 736 | **最重要参考** - 完整Agent模式 |
| `src/agents/storyboard/index.ts` | 734 | 分镜Agent + 工具调用模式 |
| `src/agents/storyboard/generateImageTool.ts` | 337 | 图像生成完整流程 |
| `src/agents/storyboard/imageSplitting.ts` | ~100 | 宫格切割 Sharp 实现 |
| `src/lib/artStyle.ts` | 1412 | 200+风格模板 |
| `src/types/database.d.ts` | 447 | 完整类型系统 |
| `src/routes/outline/agentsOutline.ts` | 149 | WS大纲Agent路由 |
| `src/routes/storyboard/chatStoryboard.ts` | 188 | WS分镜Agent路由 |
| `src/utils/ai/video/index.ts` | 91 | 视频适配器注册中心 |
| `src/utils/ai/image/index.ts` | 99 | 图像适配器注册中心 |
| `src/routes/video/generateVideo.ts` | ~100+ | 视频生成路由 |
| `src/app.ts` | 108 | Express + JWT + 文件服务 |
| `src/core.ts` | 60 | 自动路由注册 |
| `src/utils/oss.ts` | ~100+ | OSS 上传封装 |
| `src/utils/getPromptAi.ts` | ~50+ | Prompt配置读取 |

---

*本文件为 Toonflow 深度研究产出，为 huage888 全自动漫剧生产系统提供完整架构参考。*
