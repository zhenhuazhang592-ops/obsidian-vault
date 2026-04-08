# Toonflow-app 深度研究报告

> 研究时间：2026-04-07
> 项目版本：v1.0.7
> 研究深度：完整源码分析（82个API端点，6大核心模块）

---

## 1. 项目概览

### 1.1 项目定位

Toonflow 是一款 AI 短剧漫剧工具，能够利用 AI 技术将小说自动转化为剧本，并结合 AI 生成的图片和视频，实现高效的短剧创作。

### 1.2 技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端框架 | Express.js + TypeScript |
| 数据库 | SQLite（better-sqlite3 + Knex ORM）|
| AI 集成 | Vercel AI SDK（多厂商适配）|
| 实时通信 | WebSocket（express-ws）|
| 图像处理 | Sharp |
| 部署方式 | Electron 桌面应用 + Docker |

### 1.3 目录结构

```
Toonflow-app-master/
├── src/
│   ├── agents/                    # AI Agent 核心逻辑
│   │   ├── outlineScript/        # 大纲/故事线 Agent
│   │   └── storyboard/          # 分镜 Agent
│   ├── lib/                      # 核心库
│   │   ├── initDB.ts            # 数据库初始化
│   │   ├── artStyle.ts         # 艺术风格配置（200+种）
│   │   └── responseFormat.ts    # 响应格式化
│   ├── routes/                   # API 路由（82个端点）
│   │   ├── novel/               # 小说管理
│   │   ├── outline/             # 大纲管理
│   │   ├── script/              # 剧本管理
│   │   ├── storyboard/          # 分镜管理
│   │   ├── assets/              # 资产管理
│   │   ├── video/               # 视频管理
│   │   ├── project/             # 项目管理
│   │   ├── setting/             # 设置管理
│   │   └── task/                # 任务管理
│   ├── utils/                   # 工具函数
│   │   ├── ai/                  # AI 适配层
│   │   │   ├── text/           # 文本模型
│   │   │   ├── image/          # 图像模型
│   │   │   └── video/          # 视频模型
│   │   ├── db.ts               # 数据库访问
│   │   ├── oss.ts               # OSS 存储
│   │   └── generateScript.ts     # 剧本生成
│   ├── middleware/               # 中间件
│   ├── types/                   # 类型定义
│   │   └── database.d.ts        # 数据库 Schema
│   ├── app.ts                   # 应用入口
│   └── router.ts                # 路由生成器
├── docs/                        # 文档
└── docker/                      # Docker 配置
```

---

## 2. 剧本管理系统

### 2.1 核心数据模型

**t_script 表结构：**

```typescript
interface t_script {
  id: number;           // 剧本 ID
  name: string;         // 剧本名称（如"第1集"）
  content: string;      // 剧本正文内容
  projectId: number;   // 关联项目 ID
  outlineId: number;   // 关联大纲 ID
}
```

**关联关系：**
- `t_script.outlineId` -> `t_outline.id`（多对一）
- `t_script.projectId` -> `t_project.id`（多对一）

### 2.2 大纲 Schema（EpisodeData）

项目定义了严格的剧本结构 Schema，确保 AI 生成的剧本符合叙事规范：

```typescript
interface EpisodeData {
  episodeIndex: number;      // 集数索引
  title: string;           // 8字内标题
  chapterRange: number[];   // 关联章节号数组

  // 资产（按出场顺序排列）
  scenes: { name: string; description: string }[];       // 场景
  characters: { name: string; description: string }[];  // 角色
  props: { name: string; description: string }[];        // 道具

  // 叙事结构
  coreConflict: string;      // 核心矛盾
  outline: string;          // 剧情主干（最高优先级）
  openingHook: string;      // 开场镜头
  keyEvents: string[4];     // [起, 承, 转, 合]
  emotionalCurve: string;    // 情绪曲线

  // 视觉与台词
  visualHighlights: string[];  // 标志性镜头
  endingHook: string;          // 结尾悬念
  classicQuotes: string[];     // 黄金金句
}
```

### 2.3 剧本生成流程

```
generateScript API
    │
    ▼
1. 获取 outlineData（大纲数据）
    │
    ▼
2. 获取 novelData（原文章节）
    │
    ▼
3. 调用 generateScript() 函数
    │
    ├── 格式化 Episode 为结构化提示
    └── 调用 AI 生成剧本（500-800字）
    │
    ▼
4. 保存到 t_script.content
```

**核心实现（`utils/generateScript.ts`）：**

```typescript
export async function generateScript(episode: Episode, novelData: string): Promise<string> {
  // 1. 格式化大纲为结构化提示
  const episodePrompt = formatEpisodePrompt(episode);

  // 2. 构建用户提示（强调优先级）
  const userPrompt = `
    【最高优先级：剧情主干(outline)是唯一权威】
    1. 【开场镜头】必须是剧本的第一个镜头
    2. 严格按【剧情主干】顺序展开剧情
    3. 【剧情节点】四步必须严格按顺序：起→承→转→合
    ...
  `;

  // 3. 调用 AI 生成
  return await u.ai.text.invoke({
    messages: [
      { role: "system", content: mainPrompts },
      { role: "user", content: userPrompt },
    ]
  });
}
```

### 2.4 CRUD 操作

| 操作 | 路由 | 说明 |
|------|------|------|
| 生成剧本 | POST `/script/generateScriptApi` | 基于大纲生成 |
| 保存剧本 | POST `/script/generateScriptSave` | 手动保存 |
| 获取剧本 | GET `/script/geScriptApi` | 获取内容 |

---

## 3. 角色场景设计系统

### 3.1 资产数据模型（t_assets）

```typescript
interface t_assets {
  id: number;
  name: string;              // 资产名称
  intro: string;             // 简介/描述
  prompt: string;            // 提示词
  remark: string;            // 备注
  videoPrompt: string;       // 视频提示词
  type: "角色" | "场景" | "道具" | "分镜";
  episode: string;           // 集数
  duration: string;          // 时长
  filePath: string;          // 文件路径
  state: string;             // 状态
  projectId: number;
  scriptId: number;          // 关联剧本 ID
  segmentId: number;         // 片段 ID
  shotIndex: number;         // 镜头索引
}
```

### 3.2 资产类型

| 类型 | 说明 | 生成方式 |
|------|------|----------|
| 角色 | 人物外观、性格设定 | AI 生成四视图 |
| 场景 | 环境、空间、光线 | AI 生成场景图 |
| 道具 | 物品样式、材质 | AI 生成道具图 |
| 分镜 | 镜头画面描述 | AI 生成分镜图 |

### 3.3 资产生成流程

```typescript
// routes/assets/generateAssets.ts
router.post("/", async (req, res) => {
  const { id, type, projectId, name, prompt } = req.body;

  // 1. 获取项目风格
  const project = await u.db("t_project").where("id", projectId).first();

  // 2. 根据类型选择系统提示词
  let systemPrompt = "";
  if (type == "role") systemPrompt = rolePrompt;
  if (type == "scene") systemPrompt = scenePrompt;
  if (type == "props") systemPrompt = toolPrompt;

  // 3. 调用 AI 生成图片
  const contentStr = await u.ai.image({
    systemPrompt,
    prompt: userPrompt,
    size: "2K",
    aspectRatio: project.videoRatio ?? "16:9"
  });

  // 4. 保存到 OSS 并更新数据库
  await u.oss.writeFile(imagePath, buffer);
  await u.db("t_image").insert({ state: "生成成功", filePath: imagePath });
});
```

### 3.4 艺术风格库

项目内置了 **200+ 种艺术风格**（`lib/artStyle.ts`），分类如下：

| 分类 | 示例风格 |
|------|----------|
| 常用风格 | 2D动漫、真人写实、3D国创、三渲二、吉卜力 |
| IP风格 | 龙族传说、比奇堡、蜡笔小新、动森 |
| 插画风格 | 浮世绘、波普印刷、水彩、哥特霓虹 |
| 可爱Q版 | Q版3D、火柴人、像素、日本小人 |
| 立体风格 | 方块世界、折纸艺术、莱卡定格 |
| 日系风格 | 日式少女漫、油画釉光、藤本树风格 |

---

## 4. 导演计划与分镜系统

### 4.1 分镜数据结构

**Segment（片段）：**

```typescript
interface Segment {
  index: number;           // 片段序号
  description: string;     // 片段描述
  emotion?: string;        // 情绪氛围
  action?: string;         // 主要动作
}
```

**Shot（分镜）：**

```typescript
interface Shot {
  id: number;               // 分镜独立 ID
  segmentId: number;         // 所属片段 ID
  title: string;            // 标题（如"分镜 1"）
  x: number;                // 画布 X 坐标
  y: number;                // 画布 Y 坐标
  cells: Cell[];            // 镜头数组
  fragmentContent: string;  // 片段内容
  assetsTags: AssetsType[]; // 资产标签
}

interface Cell {
  id: string;              // 镜头唯一 ID
  src?: string;            // 图片 URL
  prompt?: string;          // 提示词
}
```

### 4.2 Storyboard Agent 架构

**核心类：** `agents/storyboard/index.ts`

```
                    ┌─────────────────────────────────────┐
                    │         Storyboard Agent             │
                    │                                     │
                    │  - history: ModelMessage[]           │
                    │  - segments: Segment[]               │
                    │  - shots: Shot[]                   │
                    │  - emitter: EventEmitter           │
                    └──────────────┬──────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  segmentAgent   │    │   shotAgent    │    │  main Agent     │
│  (片段师)       │    │   (分镜师)     │    │  (主控)         │
│                 │    │                 │    │                 │
│ Tools:         │    │ Tools:          │    │ Tools:          │
│ - getScript    │    │ - getScript     │    │ - segmentAgent  │
│ - getAssets    │    │ - getAssets     │    │ - shotAgent     │
│ - updateSegs   │    │ - getSegments   │    │ - getScript     │
│                │    │ - addShots       │    │ - generateShot  │
│                │    │ - updateShots    │    │   Image         │
│                │    │ - deleteShots    │    │                 │
│                │    │ - generateShot   │    │                 │
│                │    │   Image          │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 4.3 分镜对话流程

```typescript
// routes/storyboard/chatStoryboard.ts
router.ws("/", async (ws, req) => {
  const agent = new Storyboard(projectId, scriptId);

  // 监听事件并通过 WebSocket 推送
  agent.emitter.on("stream", (text) => ws.send({ type: "stream", data: text }));
  agent.emitter.on("toolCall", (data) => ws.send({ type: "toolCall", data }));
  agent.emitter.on("shotsUpdated", (data) => ws.send({ type: "shotsUpdated", data }));
  agent.emitter.on("shotImageGenerateProgress", (data) => ws.send({...}));
  agent.emitter.on("shotImageGenerateComplete", (data) => ws.send({...}));

  // 处理客户端消息
  ws.on("message", async (data) => {
    switch (data.type) {
      case "msg": await agent.call(msg.data); break;
      case "cleanHistory": agent.history = []; break;
      case "replaceShot": agent.updatePreShots(...); break;
    }
  });
});
```

### 4.4 分镜图生成流程

```
shotAgent 调用 generateShotImage
            │
            ▼
    提取所有镜头的提示词
            │
            ▼
    生成宫格图片（多提示词合并）
            │
            ▼
    分割宫格为单张镜头图
            │
            ▼
    上传到 OSS
            │
            ▼
    更新每个镜头的 src 字段
            │
            ▼
    触发 shotImageGenerateComplete 事件
```

---

## 5. 视频生产系统

### 5.1 视频模型能力矩阵

项目定义了完整的视频模型注册表（`utils/ai/video/modelList.ts`）：

```typescript
interface VideoModel {
  manufacturer: string;      // 厂商
  model: string;              // 模型名称
  durationResolutionMap: {   // 支持的时长和分辨率
    duration: number[];
    resolution: string[];
  }[];
  aspectRatio: string[];     // 支持的宽高比
  type: VideoGenerationType[]; // 生成类型
  audio: boolean;           // 是否支持音频
}

type VideoGenerationType =
  | "singleImage"        // 单图
  | "startEndRequired"   // 首尾帧（必须）
  | "endFrameOptional"   // 首尾帧（尾帧可选）
  | "startFrameOptional" // 首尾帧（首帧可选）
  | "multiImage"         // 多图模式
  | "reference"          // 参考图模式
  | "text";              // 文本生视频
```

### 5.2 支持的视频模型

| 厂商 | 模型 | 类型 | 音频 |
|------|------|------|------|
| **火山引擎** | doubao-seedance-1-5-pro | text/i2v | 支持 |
| **可灵** | kling-v2-6(PRO) | text/i2v | 不支持 |
| **Vidu** | viduq3-pro | i2v | 支持 |
| **万象** | wan2.6-t2v/i2v | t2v/i2v | 支持 |
| **Gemini** | Veo 3.1 | text/i2v/参考 | 支持 |
| **RunningHub** | Sora 2 | t2v/i2v | 不支持 |

### 5.3 视频生成流程

```typescript
// routes/video/generateVideo.ts
router.post("/", async (req, res) => {
  const {
    projectId, scriptId, configId,
    resolution, filePath, duration,
    prompt, mode, audioEnabled
  } = req.body;

  // 1. 获取 AI 配置
  const aiConfigData = await u.db("t_config").where("id", aiConfigId).first();

  // 2. 处理图片（上传 OSS 或合并宫格）
  if (filePath.length > 1 && aiConfigData.model?.includes("sora")) {
    filePath = [await sharpProcessingImage(filePath)]; // 合并为宫格
  }

  // 3. 创建视频记录（立即返回）
  const [videoId] = await u.db("t_video").insert({
    state: 0,  // 生成中
    filePath: savePath
  });
  res.status(200).send({ id: videoId });

  // 4. 异步生成视频
  generateVideoAsync(videoId, ...);
});

async function generateVideoAsync(videoId, fileUrl, savePath, ...) {
  try {
    // 调用视频生成 API
    const videoPath = await u.ai.video({
      imageBase64: images,
      prompt: enhancedPrompt,
      duration,
      mode,
      audio: audioEnabled
    }, aiConfigData);

    // 更新状态
    await u.db("t_video").where("id", videoId).update({
      state: videoPath ? 1 : -1  // 成功/失败
    });
  } catch (err) {
    await u.db("t_video").where("id", videoId).update({
      state: -1,
      errorReason: err.message
    });
  }
}
```

### 5.4 视频适配器模式

项目采用**厂商适配器模式**统一调用不同视频 API：

```typescript
// utils/ai/video/index.ts
const modelInstance = {
  volcengine: volcengineAdapter,
  kling: klingAdapter,
  vidu: viduAdapter,
  wan: wanAdapter,
  gemini: geminiAdapter,
  runninghub: runninghubAdapter,
  apimart: apimartAdapter,
  // ...
};

export default async (input: VideoConfig, config: AIConfig) => {
  const manufacturerFn = modelInstance[config.manufacturer];
  return await manufacturerFn(input, config);
};
```

---

## 6. 监督层与工作流

### 6.1 工作流状态

| 状态 | 说明 |
|------|------|
| `t_video.state = 0` | 生成中 |
| `t_video.state = 1` | 生成成功 |
| `t_video.state = -1` | 生成失败 |
| `t_image.state` | 生成中/生成成功/生成失败 |
| `t_assets.state` | 资产状态 |

### 6.2 任务追踪

```typescript
interface t_myTasks {
  id: number;
  projectId: number;
  taskClass: string;       // 任务类型
  relatedObjects: string;  // 关联对象
  model: string;           // 使用模型
  describe: string;         // 描述
  state: string;           // 进行中/已完成/生成失败
  startTime: number;
  reason: string;          // 失败原因
}
```

### 6.3 监督机制

**Agent 事件流：**

```
Agent 执行
    │
    ▼
emitter.emit("transfer")   // 切换到 Sub-Agent
    │
    ▼
emitter.emit("toolCall")   // 工具调用
    │
    ▼
emitter.emit("data")       // 流式输出
    │
    ▼
emitter.emit("response")   // 完整响应
    │
    ▼
emitter.emit("refresh")    // 刷新数据
```

**分镜图生成事件：**

```
shotImageGenerateStart    // 开始生成
    │
    ▼
shotImageGenerateProgress // 进度更新 (generating/splitting/saving)
    │
    ▼
shotImageGenerateComplete  // 生成完成
    │
    ▼
shotImageGenerateError     // 生成失败
```

---

## 7. 完整链路数据流

### 7.1 端到端流程图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Toonflow 完整链路                               │
└─────────────────────────────────────────────────────────────────────────┘

  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
  │  小说   │────▶│ 故事线  │────▶│  大纲   │────▶│ 剧本    │
  │(t_novel)│     │(t_story│     │(t_outline)│   │(t_script│
  │         │     │ line)   │     │          │     │)        │
  └─────────┘     └─────────┘     └─────────┘     └────┬────┘
       │                                      │          │
       │                                      │          │
       │                              ┌───────▼───────┐
       │                              │  衍生资产      │
       │                              │(t_assets)     │
       │                              │  - 角色        │
       │                              │  - 场景        │
       │                              │  - 道具        │
       │                              └───────┬───────┘
       │                                      │
       ▼                                      ▼
  ┌─────────────────────────────────────────────────────┐
  │              分镜系统 (Storyboard Agent)            │
  │                                                     │
  │   片段(Segment) ──▶ 分镜(Shot) ──▶ 镜头(Cell)      │
  │                                                     │
  │   getSegments() / addShots() / updateShots()        │
  └──────────────────────┬──────────────────────────────┘
                         │
                         ▼
  ┌─────────────────────────────────────────────────────┐
  │              分镜图生成 (generateShotImage)          │
  │                                                     │
  │   多提示词 ──▶ 宫格图 ──▶ 分割 ──▶ OSS 上传         │
  └──────────────────────┬──────────────────────────────┘
                         │
                         ▼
  ┌─────────────────────────────────────────────────────┐
  │              视频配置 (t_videoConfig)               │
  │                                                     │
  │   - manufacturer    - mode (startEnd/multi/single)  │
  │   - resolution       - duration                      │
  │   - audioEnabled     - prompt                       │
  └──────────────────────┬──────────────────────────────┘
                         │
                         ▼
  ┌─────────────────────────────────────────────────────┐
  │              视频生成 (generateVideo)                │
  │                                                     │
  │   分镜图 ──▶ AI 视频模型 ──▶ MP4 文件               │
  └─────────────────────────────────────────────────────┘
```

### 7.2 数据库关系图

```
t_project ─────────────────────────────────────────────────┐
    │                                                        │
    ├── 1:N ──▶ t_novel                                     │
    │           (小说章节)                                   │
    │                                                        │
    ├── 1:N ──▶ t_storyline                                 │
    │           (故事线)                                     │
    │                                                        │
    ├── 1:N ──▶ t_outline                                   │
    │           (大纲集)                                     │
    │           │                                           │
    │           └── 1:1 ──▶ t_script (剧本)                 │
    │                        │                               │
    │                        ├── 1:N ──▶ t_assets            │
    │                        │        (分镜资产)              │
    │                        │        │                      │
    │                        │        └── 1:N ──▶ t_image    │
    │                        │             (资产图片)          │
    │                        │                               │
    │                        └── 1:N ──▶ t_videoConfig       │
    │                                 (视频配置)             │
    │                                 │                      │
    │                                 └── 1:N ──▶ t_video    │
    │                                          (视频成品)     │
    │                                                        │
    └── 1:N ──▶ t_chatHistory                               │
                (对话历史)                                   │
```

---

## 8. 协同机制与状态管理

### 8.1 WebSocket 实时通信

```typescript
// 路由层：WebSocket 端点
router.ws("/", async (ws, req) => {
  const agent = new OutlineScript(projectId);

  // 推送事件
  ws.send(JSON.stringify({ type: "init", data: { projectId } }));

  // 监听 Agent 事件
  agent.emitter.on("stream", (text) => {
    ws.send(JSON.stringify({ type: "stream", data: text }));
  });

  agent.emitter.on("refresh", (data) => {
    ws.send(JSON.stringify({ type: "refresh", data }));
  });

  // 处理客户端消息
  ws.on("message", async (data) => {
    const { type, data: msg } = JSON.parse(data);
    if (type === "msg") await agent.call(msg);
  });
});
```

### 8.2 状态持久化

```typescript
// 对话历史持久化
async function saveHistory() {
  const existing = await u.db("t_chatHistory")
    .where({ projectId, type: "outlineAgent" })
    .first();

  if (existing) {
    await u.db("t_chatHistory").where("id", existing.id).update({
      data: JSON.stringify(history),
      novel: JSON.stringify(novelChapters)
    });
  } else {
    await u.db("t_chatHistory").insert({
      projectId,
      data: JSON.stringify(history),
      novel: JSON.stringify(novelChapters),
      type: "outlineAgent"
    });
  }
}
```

### 8.3 错误处理与回退

```typescript
// 统一错误处理
export default (err: any, req: Request, res: Response, next: NextFunction) => {
  res.locals.message = err.message;
  res.locals.error = err;
  console.error(err);
  res.status(err.status || 500).send(err);
};

// 视频生成错误处理
async function generateVideoAsync(videoId, ...) {
  try {
    const videoPath = await u.ai.video(...);
    if (videoPath) {
      await u.db("t_video").where("id", videoId).update({ state: 1 });
    } else {
      await u.db("t_video").where("id", videoId).update({ state: -1 });
    }
  } catch (err) {
    await u.db("t_video").where("id", videoId).update({
      state: -1,
      errorReason: u.error(err).message
    });
  }
}
```

---

## 9. 设计模式总结

### 9.1 适配器模式（Adapter Pattern）

**应用场景：** 多厂商 AI API 统一调用

```typescript
// 定义统一接口
interface VideoAdapter {
  (input: VideoConfig, config: AIConfig): Promise<string>;
}

// 各厂商实现
const volcengineAdapter: VideoAdapter = async (input, config) => { /* ... */ };
const klingAdapter: VideoAdapter = async (input, config) => { /* ... */ };

// 工厂选择
const adapter = adapters[config.manufacturer];
return await adapter(input, config);
```

### 9.2 Agent 模式（Agent Pattern）

**应用场景：** 复杂任务分解与执行

```
Main Agent
    │
    ├── segmentAgent（片段师）
    │       └── getScript, getAssets, updateSegments
    │
    ├── shotAgent（分镜师）
    │       └── getSegments, addShots, updateShots, generateShotImage
    │
    └── director（导演）- 审核与修改
```

**关键特点：**
- 使用 `EventEmitter` 实现事件驱动
- 支持流式响应（Streaming）
- 工具调用自动持久化

### 9.3 工厂模式（Factory Pattern）

**应用场景：** 路由自动注册

```typescript
// core.ts - 自动扫描路由文件
async function generateRouter() {
  const entries = await fg(["src/routes/**/*.ts"]);
  for (const entry of entries) {
    const routePath = fileNameToRoutePath(entry);
    const routeModule = await import(entry);
    app.use(routePath, routeModule.default);
  }
}
```

### 9.4 Schema 验证模式

**应用场景：** 数据验证

```typescript
import { z } from "zod";

const episodeSchema = z.object({
  episodeIndex: z.number(),
  title: z.string().max(8),
  keyEvents: z.array(z.string()).length(4),
  emotionalCurve: z.string(),
  // ...
});
```

---

## 10. 对漠玫项目的启示

### 10.1 可复用的架构模式

| 模式 | 漠玫项目适配 |
|------|-------------|
| **多厂商适配器** | 统一调用 Doubao/即梦/海螺等 |
| **资产管理系统** | 漠玫角色/场景/道具资产 |
| **分镜 Agent** | 断桥奇遇分镜生成 |
| **艺术风格库** | 赛博墨韵风格预设 |
| **视频能力矩阵** | 文生视频/图生视频配置 |

### 10.2 数据模型映射

| Toonflow | 漠玫项目 |
|----------|---------|
| `t_project` | 漠玫 IP 项目 |
| `t_outline` | 漠玫剧情大纲 |
| `t_script` | 分镜剧本 |
| `t_assets` (角色) | 漠玫角色资产 |
| `t_assets` (场景) | 场景参考图 |
| `t_video` | 生成的视频 |

### 10.3 关键实现建议

**1. 赛博墨韵风格库**

```typescript
// 参考 artStyle.ts 实现
export const cyberInkStyles = [
  {
    name: "赛博墨韵",
    styles: [
      { name: "流动墨滴", prompt: "(画风:赛博墨韵,墨滴数据流)" },
      { name: "金色瞳孔", prompt: "(画风:赛博墨韵,金色数据流瞳孔)" },
      // ...
    ]
  }
];
```

**2. 分镜 Agent 集成**

```typescript
// 参考 Storyboard Agent 实现漠玫分镜逻辑
class MoMeiStoryboard extends Storyboard {
  // 定制化：赛博墨韵风格强化
  // 资产引用：漠玫角色描述词
}
```

**3. 视频生成配置**

```typescript
// 参考 video/modelList.ts 实现
export const moMeiVideoModels = [
  {
    manufacturer: "doubao",
    model: "doubao-seedance-1-5-pro",
    type: ["text", "endFrameOptional"],
    audio: true
  },
  // 即梦、海螺等
];
```

### 10.4 核心文件位置汇总

| 功能模块 | 源文件路径 |
|---------|-----------|
| 数据模型定义 | `src/types/database.d.ts` |
| 数据库初始化 | `src/lib/initDB.ts` |
| 大纲 Agent | `src/agents/outlineScript/index.ts` |
| 分镜 Agent | `src/agents/storyboard/index.ts` |
| 视频适配器 | `src/utils/ai/video/index.ts` |
| 视频模型配置 | `src/utils/ai/video/modelList.ts` |
| 艺术风格库 | `src/lib/artStyle.ts` |
| 剧本生成 | `src/utils/generateScript.ts` |
| 资产生成 | `src/routes/assets/generateAssets.ts` |
| 视频生成 | `src/routes/video/generateVideo.ts` |

---

## 附录：漠玫项目可借鉴的 5 个核心机制

### A. 叙事结构 Schema 验证

Toonflow 的 `EpisodeData` Schema 是整个系统的锚点。建议为漠玫剧本引入类似约束：

```typescript
const moMeiEpisodeSchema = {
  title: "断桥奇遇",           // 8字内
  scene: "西湖断桥",           // 场景锚定
  emotionalArc: "平→惊→悟",   // 情绪曲线
  coreConflict: "身份对决",   // 核心矛盾
  keyShots: 25,               // 镜头数
  duration: 45,               // 秒数
};
```

### B. 资产-剧本关联机制

`t_assets.scriptId` + `t_assets.segmentId` + `t_assets.shotIndex` 是关键关联字段，漠玫可直接复用：

- 漠玫角色（C001/C002）绑定到具体镜头
- 场景参考图绑定到具体 segment
- 道具资产绑定到 shot 级别

### C. 分镜 Agent 的 Tool Calling 模式

Storyboard Agent 的核心优势是让 AI 自主决定：
1. 调用 `getScript()` 获取剧本
2. 调用 `getAssets()` 获取资产
3. 调用 `addShots()` 添加分镜
4. 调用 `generateShotImage()` 生成分镜图

漠玫的断桥奇遇分镜可以引入类似机制。

### D. 事件驱动的实时反馈

`EventEmitter` + WebSocket 是 Toonflow 的实时核心：
- `stream`: AI 思考过程实时展示
- `toolCall`: 工具调用日志
- `shotsUpdated`: 分镜更新推送
- `shotImageGenerateProgress`: 生成进度

漠玫的前端可以直接复用这套事件协议。

### E. 视频模型的类型系统

Toonflow 的 `VideoGenerationType` 枚举是适配多模型的关键：

```typescript
// 漠玫视频能力矩阵
type MoMeiVideoType =
  | "text-to-video"        // 文生视频（开场动画）
  | "character-consistent"  // 角色一致性（图生视频）
  | "scene-transition"      // 场景转换
  | "action-loop";          // 动作循环（分镜衔接）
```

---

**研究完成时间：** 2026-04-07
**研究深度：** 完整源码（31个核心文件）
**核心文件路径：** `/Users/huage/Downloads/Toonflow-app-master/`
