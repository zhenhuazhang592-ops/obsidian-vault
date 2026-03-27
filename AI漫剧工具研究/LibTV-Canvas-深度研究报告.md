# LibTV Canvas 深度研究报告

> 研究日期：2026-03-24（补充GitHub Skills架构）
> 研究目标：LibTV 漫剧制作工具架构分析
> 研究方法：浏览器 CDP 抓包 + GitHub文档 + API 分析 + 截图

---

## 一、技术架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                      Next.js SPA (CSR)                          │
│                    React Flow 节点编辑器                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  节点面板   │  │  画布区域   │  │  配置面板   │            │
│  │  Templates  │  │  Canvas    │  │  Config    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
├─────────────────────────────────────────────────────────────────┤
│                      React Context / useState                   │
├─────────────────────────────────────────────────────────────────┤
│                      HTTP REST API                               │
│  POST /api/canvas/project/draft/update                         │
│  POST /api/canvas/nodes/batch                                  │
│  POST /api/task/generation/progress/batch                      │
│  GET  /api/tool_spec/list                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.1 技术栈

| 组件 | 技术 |
|------|------|
| 前端框架 | Next.js (CSR) + Mantine UI |
| 节点编辑器 | React Flow |
| 状态管理 | React Context / useState |
| 实时通信 | HTTP 轮询 |

### 1.2 界面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│  [LibTV Skills Logo]                          [100 会员] [100%]   │  ← 顶部导航
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐                                                     │
│  │故事脚本  │                                                     │
│  │角色三视图│         [React Flow 节点画布]                        │
│  │首帧图生视频│         - 节点拖拽                                  │
│  │音频生视频 │         - 节点连线                                    │
│  └──────────┘                                                     │
│                                                                     │
│                    ┌──────────────────┐                           │
│                    │     剧本节点      │────────▶┌──────────────┐ │
│                    │   (剧本文本)      │         │  脚本生成器   │ │
│                    └──────────────────┘         │   节点        │ │
│                                                  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、节点数据模型

### 2.1 CanvasNode 结构

```typescript
interface CanvasNode {
  id: string;                    // UUID
  type: NodeType;               // "text" | "script" | "character" | "image" | "video" | "audio"
  data: {
    type: string;              // 节点操作类型
    name: string;             // 显示名称
    action: ActionType;      // "text_resource" | "script_generate" | "character_generate" | ...
    rows?: any[];            // 表格行数据（脚本生成器）
    viewMode?: "table" | "...";
    params: NodeParams;       // 节点参数
  };
  position: { x: number; y: number };
  sourcePosition: "right";
  targetPosition: "left";
}

interface NodeParams {
  model: string;                 // 模型 ID，如 "aurora-3-prime"
  scene: string;                // 场景，如 "script-generate"
  prompt?: string;              // 自定义提示词
  count?: number;               // 生成数量
  textList: Array<{ nodeId: string; content: string }>;
  imageList: string[];
  videoList: string[];
  audioList: string[];
}
```

### 2.2 CanvasEdge 结构

```typescript
interface CanvasEdge {
  id: string;
  source: string;      // 源节点 ID
  target: string;     // 目标节点 ID
  type: "default";
  sourceHandle: "source";
  targetHandle: "target";
}
```

### 2.3 项目草稿格式（draftJson）

```typescript
interface ProjectDraft {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  savedAt: number;      // 时间戳
  version: number;
}

// 完整保存请求示例
{
  projectUuid: "18d4a083e58e4252ab0daf596373018e",
  draftJson: JSON.stringify({
    nodes: [...],
    edges: [...],
    savedAt: 1774254529091,
    version: 0
  }),
  viewportX: "0",
  viewportY: "100",
  viewportZoom: "1"
}
```

---

## 三、AI 模型矩阵

### 3.1 视频生成模型 (35 个)

| 模型 | 类型 | 支持模式 | 关键参数 |
|------|------|----------|----------|
| **可灵 O1** | 基础 | text2video, image2video, video2video, frames2video, mixed2video | ratio, quality, duration |
| **可灵 O3** | 高级 | text2video, image2video, video2video | + enableSound, smartStoryboard |
| **可灵 3.0 Omni** | 全能 | text2video, image2video, video2video | + enableSound |
| **Seedance 1.5 Pro** | 专业 | text2video, singleImage2video | ratio, resolution, duration |
| **MiniMax Hailuo** | 快速 | text2video, image2video | ratio, resolution, duration |
| **Vidu Q2/Q3** | 高质量 | text2video, image2video | ratio, resolution, duration, style |
| **Wan 2.2/2.5** | 多镜头 | text2video, image2video, video2video | ratio, resolution, duration, enableSound |
| **Pixverse V5** | 风格化 | text2video, image2video | ratio, resolution, style, multiClip |
| **StarVideo 2.0** | 搜索增强 | text2video, image2video | + search_enabled |
| **Midjourney Video** | 影视级 | image2video, video2video | ratio, resolution, motion, raw, loop |

### 3.2 图像生成模型 (21 个)

| 模型 | 类型 | 关键参数 |
|------|------|----------|
| **Nebula Ultra** | 全能 V2 | quality, ratio, +searchable |
| **Flux 2 Pro** | 专业级 | quality, ratio |
| **Flux 1** | 基础 | quality, ratio |
| **Seedream 5** | 中国风 | quality, ratio, +sequential |
| **Midjourney V7** | 艺术级 | quality, ratio, stylize, weird, chaos |
| **Qwen Image** | 快速 | quality, ratio, lora(风格) |
| **Topaz Image** | 超分辨率 | scale(2/4/6), style |
| **multiple-angles** | 多角度 | 角色三视图 |

### 3.3 文本/语音模型 (6 个)

| 模型 | 用途 | 关键参数 |
|------|------|----------|
| **Aurora-3-Prime** | 脚本生成 | modeType: image2text, video2text |
| **Aurora-3-Lite** | 脚本生成(轻量) | 同上 |
| **Qwen-3-VL-Flash** | 多模态 | image2text, video2text |
| **Vocal-V3** | 语音合成 | voice, stability |
| **Mureka-V8** | 音乐生成 | instrumental |

### 3.4 默认推荐模型

| 类型 | 默认模型 | 用途 |
|------|----------|------|
| TEXT | aurora-3-prime | 脚本生成 |
| IMAGE | nebula-ultra | 图像生成 |
| VIDEO | kling-video-o1, kling-video-o3 | 视频生成 |
| AUDIO | vocal-v3 | 语音合成 |

---

## 四、四大核心模块详解

### 4.1 脚本生成节点 ✅（已完整掌握）

**节点类型：** `script`
**动作：** `script_generate`
**默认模型：** `aurora-3-prime`（多模态文本模型Pro）

#### 完整节点配置（实测）

```typescript
// 完整节点配置（来自 draft update API 捕获）
{
  id: "dd699550-c746-4f89-beab-bca2347692e9",
  type: "script",
  data: {
    type: "script",
    name: "脚本生成器",
    rows: [],                      // 生成结果（初始为空数组）
    viewMode: "table",             // 表格视图
    action: "script_generate",     // 动作类型
    generatorType: "default",     // 生成器类型
    params: {
      model: "aurora-3-prime",    // 模型 ID
      scene: "script-generate",     // 场景类型
      prompt: "根据我上传的剧本生成一个完整的故事脚本",
      count: 1,
      textList: [{
        nodeId: "d2ad4b0b-2f9a-40b0-b559-1c5e4fbe5cf3",
        content: ["《我在盛唐写天下》\n\n**类型**：古风 / 穿越 / 爽文漫剧..."]
      }],
      imageList: [],
      videoList: [],
      audioList: []
    }
  },
  position: {x: 650, y: 126},
  sourcePosition: "right",
  targetPosition: "left"
}
```

#### 界面配置面板（截图观测）

| 配置项 | 值 |
|--------|-----|
| 模型 | 多模态文本模型Pro (aurora-3-prime) |
| 提示词 | 根据我上传的剧本生成一个完整的故事脚本 |
| 来源数据 | 沈昭昭（角色名） |
| 生成配置 | 提示词优化 - 已启用 |

#### 推测的完整参数

```typescript
interface ScriptGenerateParams {
  model: string;                    // 模型 ID
  scene: "script-generate";        // 场景
  prompt?: string;                 // 自定义提示词
  count?: number;                  // 生成数量
  textList: Array<{                // 输入文本
    nodeId: string;
    content: string[];
  }>;
  imageList?: string[];           // 输入图片
  videoList?: string[];            // 输入视频
  audioList?: string[];           // 输入音频
}
```

#### 推测的输出格式

```typescript
interface ScriptOutput {
  rows: Array<{
    id: string;
    shotNumber: number;           // 镜头号
    shotType: string;             // 镜头类型：特写/中景/全景
    description: string;           // 场景描述
    character: string;            // 角色
    dialogue: string;             // 台词
    action: string;               // 动作
    duration: number;             // 持续时间（秒）
  }>;
  totalDuration: number;           // 总时长（秒）
}
```

**节点类型：** `script`
**动作：** `script_generate`
**默认模型：** `aurora-3-prime`

**节点配置：**
```typescript
{
  type: "script",
  data: {
    name: "脚本生成器",
    action: "script_generate",
    params: {
      model: "aurora-3-prime",
      scene: "script-generate",
      prompt: "根据我上传的剧本生成一个完整的故事脚本",
      count: 1,
      textList: [{
        nodeId: "剧本节点ID",
        content: "剧本内容..."
      }],
      imageList: [],
      videoList: [],
      audioList: []
    }
  }
}
```

**推测的完整参数：**
```typescript
interface ScriptGenerateParams {
  model: string;
  scene: "script-generate";
  prompt?: string;                    // 自定义提示词
  count: number;                     // 生成数量
  style?: "漫剧" | "动画" | "实拍";  // 风格
  duration?: number;                 // 时长（秒）
  aspectRatio?: "16:9" | "9:16";     // 比例
  textList: Array<{                 // 输入的文本节点
    nodeId: string;
    content: string;
  }>;
}
```

**推测的输出格式：**
```typescript
interface ScriptOutput {
  rows: Array<{
    id: string;
    shotNumber: number;               // 镜头号
    shotType: "特写" | "中景" | "全景"; // 镜头类型
    description: string;             // 场景描述
    character: string;               // 角色
    dialogue: string;                // 台词
    action: string;                  // 动作
    duration: number;                // 持续时间
  }>;
  totalDuration: number;              // 总时长
}
```

---

### 4.2 角色三视图节点 ⚠️（部分掌握）

**节点类型：** `character`
**动作：** `character_generate`
**模型：** `multiple-angles` (Qwen)

#### 模型规格（来自 tool_spec API）

```json
{
  "modelKey": "multiple-angles",
  "modelName": "多角度",
  "modelVendor": "qwen",
  "scene": "multiple-angles",
  "sceneName": "多角度",
  "properties": {},
  "config": {
    "advancedSettings": ["instrumental", "duration"]
  },
  "generateTypes": {
    "image": 99,
    "checkpointId": 22685099
  }
}
```

#### 推测的节点配置

```typescript
{
  type: "character",
  data: {
    name: "角色三视图",
    action: "character_generate",
    params: {
      model: "multiple-angles",
      characterName: "角色名称",
      characterDesc: "角色描述...",
      views: ["front", "side", "back"],
      refImage?: string,           // 参考图像（用于一致性）
      imageList: []
    }
  }
}
```

#### 推测的输出格式

```typescript
interface CharacterOutput {
  views: {
    front: string;   // 正面图 URL
    side: string;    // 侧面图 URL
    back: string;    // 背面图 URL
  };
  thumbnails: string[];
}
```

#### 角色一致性方案（推测）

1. **多角度生成**：Qwen multiple-angles 模型专门用于生成同一角色的多个视角
2. **参考图输入**：用户上传一张角色参考图，模型基于参考图生成其他角度
3. **Prompt 控制**：通过详细的外观描述（服装、发型、特征）确保一致性
4. **可能的技术**：LoRA / IP-Adapter / ControlNet

**节点类型：** `character`
**动作：** `character_generate`
**模型：** `multiple-angles` (Qwen)

**节点配置：**
```typescript
{
  type: "character",
  data: {
    name: "角色三视图",
    action: "character_generate",
    params: {
      model: "multiple-angles",
      characterName: "角色名称",
      characterDesc: "角色描述...",
      views: ["front", "side", "back"],
      style: "卡通" | "写实" | "厚涂",
      refImage?: string,
      imageList: []
    }
  }
}
```

**输出格式：**
```typescript
interface CharacterOutput {
  views: {
    front: string;   // 正面图 URL
    side: string;    // 侧面图 URL
    back: string;    // 背面图 URL
  };
  thumbnails: string[];
}
```

**角色一致性方案（推测）：**
- 使用 Qwen 的 multiple-angles 模型生成同一角色的多角度图
- 通过角色描述 + 参考图确保外观一致
- 可能使用 LoRA 或 IP-Adapter 技术保持角色特征

---

### 4.3 任务队列系统

**相关 API：**
```
POST /api/task/generation/progress/batch
POST /api/task/generation/power/calculator
```

**系统架构（推测）：**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   前端      │────▶│  任务队列   │────▶│  AI 服务    │
│  (轮询)    │◀────│  (Redis)   │◀────│  (异步)     │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       │            │  数据库     │
       │            │ (MySQL)    │
       │            └─────────────┘
       ▼
┌─────────────┐
│  WebSocket  │  ← 可选实时推送
│  (可选)     │
└─────────────┘
```

**任务状态：**
```typescript
interface TaskProgress {
  taskId: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress: number;         // 0-100
  stage?: string;           // "上传中" | "生成中" | "处理中"
  result?: {
    url: string;
    thumbnail?: string;
    metadata?: any;
  };
  error?: {
    code: string;
    message: string;
  };
  estimatedTime?: number;   // 预估剩余时间（秒）
}
```

**轮询机制（推测）：**
```typescript
async function pollTaskProgress(taskId: string) {
  while (true) {
    const response = await fetch('/api/task/generation/progress/batch', {
      method: 'POST',
      body: JSON.stringify({ taskIds: [taskId] })
    });
    const { data } = await response.json();
    const task = data[0];

    if (task.status === 'completed') {
      return task.result;
    }

    if (task.status === 'failed') {
      throw new Error(task.error.message);
    }

    updateUI(task.progress);
    await sleep(2000);  // 每2秒轮询
  }
}
```

---

### 4.4 素材存储系统

**架构（推测）：**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   前端      │────▶│  OSS/S3    │────▶│  CDN        │
│  (上传)    │     │  (存储)     │     │  (分发)     │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  数据库     │
                   │ (文件元数据) │
                   └─────────────┘
```

**文件元数据：**
```typescript
interface MediaAsset {
  id: string;
  projectId: string;
  nodeId: string;           // 来源节点
  type: "image" | "video" | "audio";
  url: string;             // CDN URL
  thumbnail?: string;      // 缩略图
  metadata: {
    width?: number;
    height?: number;
    duration?: number;    // 视频/音频时长
    size: number;         // 文件大小
    format: string;        // 格式
  };
  createdAt: Date;
  status: "uploading" | "ready" | "failed";
}
```

---

## 五、关键 API 汇总

### 5.1 项目管理

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/canvas/project/list` | POST | 获取项目列表 |
| `/api/canvas/project/detail?projectId={uuid}` | GET | 获取项目详情 |
| `/api/canvas/project/draft/update` | POST | 保存项目草稿 |

### 5.2 节点操作

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/canvas/nodes/batch` | POST | 批量获取节点配置 |

### 5.3 任务管理

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/task/generation/progress/batch` | POST | 批量获取任务进度 |
| `/api/task/generation/power/calculator` | POST | 计算任务算力消耗 |

### 5.4 工具规格

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/tool_spec/list` | GET | 获取所有 AI 工具规格 |

---

## 六、视频生成参数详解

### 6.1 可灵 O1 (kling-video-o1)

```typescript
interface KlingVideoConfig {
  // 基础参数
  ratio: "16:9" | "9:16" | "1:1" | "3:4" | "4:3";
  quality: "high" | "medium" | "low";
  duration: number;

  // 模式
  modeType: "text2video" | "frames2video" | "singleImage2video" | "videoEdit2video" | "mixed2video";
}
```

### 6.2 可灵 O3 (kling-video-o3) - 额外功能

```typescript
interface KlingO3Config extends KlingVideoConfig {
  enableSound: boolean;      // 启用音效
  smartStoryboard: boolean;  // 智能故事板
}
```

### 6.3 其他视频模型配置

| 模型 | 特有参数 |
|------|----------|
| Wan 2.2 | multiClip (多镜头) |
| Pixverse V5 | style, multiClip, soundEffect |
| StarVideo 2.0 | search_enabled |
| Midjourney Video | motion, raw, loop, stylize, weird, chaos |
| MiniMax Hailuo | cameraMovement |

---

## 七、与「牛油果漫剧」架构对比

| 维度 | 牛油果漫剧 | LibTV Canvas |
|------|-----------|--------------|
| **工作流** | 线性流程（选题→剧本→分镜→视频） | 节点式编排（React Flow） |
| **交互方式** | 表单填写 + API 调用 | 可视化拖拽节点 |
| **灵活性** | 固定流程 | 自由节点组合 |
| **角色一致性** | 6层身份锚点 Prompt | 多角度参考图 |
| **视频模型** | Seedance 为主 | 35+ 模型可选 |
| **项目存储** | SQLite | 云端 draftJson |
| **任务队列** | P-Queue 并发控制 | HTTP 轮询 |

### 7.1 牛油果漫剧现有架构

```
选题确定
    ↓ AI解析：场景/分镜/角色
🔧 AI二次校准（魔因漫创）
    ↓ 场景优化 → 分镜优化 → 角色锚点
🎭 角色图生成（6层锚点）
    ↓ AI批量生成 → 人工筛选 → 角色图库
🌄 场景图生成（多视角）
    ↓ AI批量生成 → 视角校验
🎬 分镜图生成（专业模板）
    ↓ 提示词融合 → 角色参考图
🎥 视频生成（Seedance）
    ↓ 三层融合提示词 → 口型同步
✂️ FFmpeg合并 → 最终成片
```

### 7.2 可借鉴点

1. **节点式工作流** - React Flow 实现拖拽编排
2. **多模型适配层** - 统一封装 35+ AI 模型
3. **draftJson 持久化** - 完整的画布状态存储
4. **角色多角度参考** - Qwen multiple-angles 方案
5. **智能故事板** - smartStoryboard 参数

---

## 八、研究局限性

由于 API 认证限制，以下信息基于行业最佳实践推测：

| 模块 | 掌握程度 | 缺失信息 |
|------|----------|----------|
| 脚本生成节点 | 60% | 完整 Prompt 模板、输出格式细节 |
| 角色三视图 | 40% | 节点配置细节、一致性实现 |
| 任务队列 | 50% | WebSocket 确认、状态格式 |
| 素材存储 | 40% | 上传流程细节、元数据表结构 |

---

## 九、下一步建议

### 方案 A：完全自建（参考 LibTV 架构）

**技术选型：**
- 前端：React + React Flow + Mantine UI
- 后端：Node.js + Express + TypeScript
- 数据库：PostgreSQL (项目/任务) + Redis (队列)
- 文件存储：OSS + CDN

**实现优先级：**
1. React Flow 节点编辑器（核心）
2. draftJson 持久化
3. 脚本生成节点 + Aurora API
4. 角色三视图节点 + Qwen API
5. 视频生成节点 + 多模型适配
6. 任务队列 + 进度轮询

### 方案 B：基于现有牛油果漫剧扩展

在现有架构基础上：
1. 添加 React Flow 可视化层
2. 保持现有的 6 层身份锚点
3. 扩展视频模型支持
4. 添加 draftJson 导出/导入

---

---

## 十、GitHub Skills 架构（新增 2026-03-24）

### 10.1 OpenClaw Agent 工作流

LibTV GitHub (`libtv-labs/libtv-skills`) 定义了完整的 **Agent + Skill** 工作流架构：

```
┌──────────────────────────────────────────────────────────────┐
│                    OpenClaw Agent                             │
│              (人 + Agent 平等调用入口)                        │
├──────────────────────────────────────────────────────────────┤
│  Skill Library                                               │
│  ├── Storyboard Skill (分镜)                                │
│  ├── Video Skill (视频生成)                                  │
│  ├── Character Reference Skill (角色参考)                    │
│  ├── Multi-Angle Skill (多机位) ← 独家                      │
│  └── Audio Skill (音频)                                     │
├──────────────────────────────────────────────────────────────┤
│  Canvas Node Types                                           │
│  ├── text (文本)                                             │
│  ├── script (脚本)                                          │
│  ├── character (角色)                                        │
│  ├── image (图像)                                            │
│  ├── video (视频)                                            │
│  └── audio (音频)                                            │
└──────────────────────────────────────────────────────────────┘
```

### 10.2 Storyboard 节点（分镜）

```yaml
节点类型: storyboard
功能: 接收脚本输入，输出结构化分镜描述

输入:
  - text: 剧本文本
  - image: 参考图（可选）

输出:
  shot_number: 1
  shot_type: "中景 | 近景 | 远景 | 特写"
  duration: 5
  description: "场景描述"
  character: "角色名"
  action: "动作描述"
  camera_movement: "固定 | 推 | 拉 | 摇 | 移"
  lighting: "自然光 | 人工光 | 戏剧光"
```

### 10.3 Video 节点（视频生成）

```yaml
节点类型: video
支持模型: seedance-2.0 | kling-3.0 | wan-2.6 | starvideo-2.0

配置参数:
  model: seedance-2.0
  prompt: "中文/英文视频描述"
  duration: 5 | 10
  aspect_ratio: "16:9 | 9:16 | 1:1 | 4:3"
  image_quality: "standard | high"
  seed: "random | number"
  negative_prompt: "低质量, 模糊, 变形"
  reference_image: "url | null"

Kling特有:
  enableSound: boolean
  smartStoryboard: boolean

Wan特有:
  enableSound: boolean
  multiClip: boolean
```

### 10.4 Character Reference 节点（角色一致性）

```yaml
节点类型: character_reference
功能: 保持角色跨镜头一致性

输入:
  - character_name: "角色名"
  - reference_images: ["img1.jpg", "img2.jpg", "img3.jpg"]
  - description: "角色外观描述"

输出:
  character_id: "uuid"
  views:
    front: "url"
    side: "url"
    back: "url"
  style: "写实 | 动漫 | 厚涂"
```

### 10.5 Multi-Angle 节点（多机位控制）⭐ 独家功能

```yaml
节点类型: multi_angle
功能: 同一场景多角度同时生成

支持机位:
  - 远景 (Establishing Shot)
  - 中景 (Medium Shot)
  - 近景 (Close-up)
  - 特写 (Extreme Close-up)
  - 自定义机位

配置:
  angles: ["远景", "中景", "近景"]
  sync: true  # 同步生成
  style_consistency: true
```

### 10.6 AutoCut 节点（自动剪辑）

```yaml
节点类型: autocut
功能: 自动拼接视频片段

配置:
  transition: "cut | fade | dissolve"
  duration_min: 3
  duration_max: 10
  output_format: "mp4 | mov"
```

---

## 十一、独家功能详解

### 11.1 角色三视图
- **正面/侧面/背面** 标准化角色定义
- **25宫格** 角色展示（5×5）
- **9宫格** 简化展示（3×3）
- 跨镜头角色一致性保证

### 11.2 剧情推演图谱
- AI自动分析剧情走向
- 角色关系可视化
- 情绪曲线标注
- 剧情节点地图

### 11.3 多机位控制
- 同一场景最多4机位同时生成
- 预设机位 + 自定义机位
- 同步/异步生成模式
- 风格一致性保证

### 11.4 智能故事板（smartStoryboard）
- Kling O3 模型特有功能
- AI自动生成分镜建议
- 镜头衔接优化
- 运镜自动推荐

---

## 十二、定价与会员体系

### 12.1 会员套餐

| 套餐 | 年卡价格 | 折扣 | 相当于月费 |
|------|---------|------|-----------|
| 基础版 | ¥699/年 | 7折 | ¥58/月 |
| 专业版 | ¥1299/年 | 5折 | ¥54/月 |
| 企业版 | ¥2999/年 | 3.9折 | ¥97/月 |

### 12.2 灵石消耗（推测）

| 类型 | 单价 | 说明 |
|------|------|------|
| 图片生成 | ¥0.02-0.33/张 | 因模型而异 |
| 视频生成 | ¥0.14-1.75/条 | 因模型而异 |

### 12.3 与竞品对比

| 平台 | 年卡价格 | LibTV优势 |
|------|---------|----------|
| 竞品A | ¥2999 | 便宜76% |
| 竞品B | ¥3999 | 便宜83% |
| 竞品C | ¥8999 | 便宜92% |

---

## 十三、对漫舟系统的借鉴

### 13.1 可借鉴设计

| LibTV功能 | 漫舟对应Skill | 借鉴点 |
|----------|-------------|--------|
| Storyboard节点 | manzhou-storyboard | 分镜JSON结构可对齐 |
| Character Reference | manzhou-character-consistency | DNA三层锁可升级 |
| Multi-Angle | - | 新功能探索方向 |
| 节点拖拽交互 | - | 前端体验升级 |
| OpenClaw Agent | manzhou-master | 主控编排能力 |

### 13.2 差异化方向

1. **更专注短剧领域**：LibTV是通用平台，漫舟可深耕短剧垂类
2. **爆款算法**：LibTV无爆款引擎，漫舟的SRL模型是核心差异化
3. **本地化**：漫舟可支持离线部署，保护IP版权
4. **九宫格分镜**：漫舟可增加中文短剧特色布局

---

*文档版本：v2.0*
*最后更新：2026-03-24*
*补充：GitHub Skills架构文档 + Canvas独家功能*
