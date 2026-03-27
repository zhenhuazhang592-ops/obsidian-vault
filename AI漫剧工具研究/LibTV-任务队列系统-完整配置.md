# LibTV 任务队列系统 - 完整配置

> 研究日期：2026-03-23
> 研究方法：CDP抓包 + API分析 + UI观测
> 状态：⚠️ 部分掌握（约60%）

---

## 一、系统概述

LibTV 使用**HTTP轮询**机制处理AI生成任务，而非WebSocket实时推送。

```
┌─────────────────────────────────────────────────────────────┐
│                        任务队列系统架构                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用户操作（点击"生成"）                                        │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              POST /api/task/submit                   │   │
│  │              提交生成任务                             │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              返回 taskId                             │   │
│  │              { taskId: "xxx" }                      │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              POST /api/task/generation/progress/batch│   │
│  │              轮询任务进度（每2秒）                     │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              任务状态: pending → processing → completed │   │
│  │              或: failed                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、核心API

### 2.1 提交任务

```
POST /api/task/submit
```

**请求体：**
```typescript
{
  nodeId: string;           // 节点ID
  action: string;           // 动作类型，如 "script_generate"
  params: {
    model: string;          // 模型ID
    scene: string;          // 场景类型
    prompt?: string;        // 提示词
    textList?: Array<{      // 文本输入
      nodeId: string;
      content: string[];
    }>;
    imageList?: Array<{     // 图像输入
      nodeId: string;
      content: string[];
    }>;
    // ... 其他参数
  }
}
```

**响应：**
```typescript
{
  code: 0;
  message: "success";
  data: {
    taskId: string;         // 任务ID
    submitTime: number;     // 提交时间戳
  }
}
```

### 2.2 批量查询进度

```
POST /api/task/generation/progress/batch
```

**请求体：**
```typescript
{
  taskIds: string[];        // 任务ID数组
}
```

**响应：**
```typescript
{
  code: 0;
  message: "success";
  data: Array<{
    taskId: string;
    status: "pending" | "processing" | "completed" | "failed";
    progress: number;       // 0-100
    stage?: string;         // 阶段：上传中 | 生成中 | 处理中
    result?: {
      url: string;          // 结果URL
      thumbnail?: string;    // 缩略图
      metadata?: any;       // 其他元数据
    };
    error?: {
      code: string;
      message: string;
    };
    estimatedTime?: number; // 预估剩余时间（秒）
  }>;
}
```

### 2.3 任务功率计算器

```
POST /api/task/generation/power/calculator
```

**用途：** 计算任务所需的计算功率/配额

---

## 三、任务状态机

```
                    ┌─────────────┐
                    │   pending   │  等待中
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
            ┌──────│ processing  │  处理中
            │      └──────┬──────┘
            │             │
            │             ▼
            │      ┌─────────────────┐
            │      │  progress: 0-100│  实时进度
            │      └─────────────────┘
            │             │
            │      ┌──────┴──────┐
            │      │             │
            ▼      ▼             ▼
     ┌──────────┐ ┌────────┐ ┌─────────┐
     │ failed   │ │completed│ │ timeout │
     │  失败    │ │  完成  │ │  超时  │
     └──────────┘ └────────┘ └─────────┘
```

---

## 四、轮询机制实现

### 4.1 前端轮询代码

```typescript
class TaskQueue {
  private pollInterval = 2000;  // 2秒
  private maxRetries = 300;    // 最多300次（约10分钟）

  async submitAndWait(
    nodeData: NodeData,
    onProgress: (progress: number, stage?: string) => void,
    onComplete: (result: TaskResult) => void,
    onError: (error: Error) => void
  ): Promise<void> {
    // 1. 提交任务
    const { taskId } = await this.submitTask(nodeData);

    // 2. 轮询进度
    let retries = 0;
    while (retries < this.maxRetries) {
      const tasks = await this.pollProgress([taskId]);
      const task = tasks[0];

      if (task.status === 'completed') {
        onProgress(100);
        onComplete(task.result);
        return;
      }

      if (task.status === 'failed') {
        onError(new Error(task.error?.message || 'Task failed'));
        return;
      }

      onProgress(task.progress, task.stage);
      retries++;
      await this.sleep(this.pollInterval);
    }

    onError(new Error('Task timeout'));
  }

  private async submitTask(nodeData: NodeData): Promise<{ taskId: string }> {
    const response = await fetch('/api/task/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nodeId: nodeData.id,
        action: nodeData.data.action,
        params: nodeData.data.params
      })
    });

    const { data } = await response.json();
    return data;
  }

  private async pollProgress(taskIds: string[]): Promise<TaskProgress[]> {
    const response = await fetch('/api/task/generation/progress/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ taskIds })
    });

    const { data } = await response.json();
    return data;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### 4.2 并发控制

```typescript
class ConcurrentTaskQueue {
  private concurrency = 5;  // 最大并发数
  private queue: Task[] = [];

  async addTask(task: Task): Promise<void> {
    if (this.runningCount >= this.concurrency) {
      await new Promise(resolve => this.queue.push(resolve));
    }
    return this.executeTask(task);
  }

  private async executeTask(task: Task): Promise<void> {
    try {
      await task.execute();
    } finally {
      this.runningCount--;
      // 取出下一个任务
      if (this.queue.length > 0) {
        const next = this.queue.shift();
        this.runningCount++;
        next();
      }
    }
  }
}
```

---

## 五、任务数据结构

### 5.1 任务定义

```typescript
interface GenerationTask {
  id: string;
  nodeId: string;
  action: string;           // "script_generate" | "image_generate" | "video_generate"
  params: {
    model: string;
    scene: string;
    prompt?: string;
    textList?: TextSource[];
    imageList?: ImageSource[];
    videoList?: VideoSource[];
    audioList?: AudioSource[];
    [key: string]: any;
  };
  status: TaskStatus;
  progress: number;
  stage?: string;
  result?: TaskResult;
  error?: TaskError;
  createdAt: number;
  updatedAt: number;
  estimatedTime?: number;
}

type TaskStatus = "pending" | "processing" | "completed" | "failed";

interface TaskResult {
  url: string;
  thumbnail?: string;
  metadata?: {
    width?: number;
    height?: number;
    duration?: number;
    format?: string;
    [key: string]: any;
  };
}

interface TaskError {
  code: string;
  message: string;
  details?: any;
}
```

### 5.2 节点任务映射

| 节点类型 | 动作 | 任务类型 |
|---------|------|---------|
| `text` | `text_resource` | 资源管理 |
| `script` | `script_generate` | 脚本生成 |
| `image` | `image_generate` | 图片生成 |
| `video` | `video_generate` | 视频生成 |
| `audio` | `audio_generate` | 音频生成 |
| `character` | `character_generate` | 角色生成 |

---

## 六、进度显示

### 6.1 UI进度条

```typescript
// 进度条组件
interface ProgressBarProps {
  progress: number;      // 0-100
  stage?: string;        // 当前阶段
  showPercentage: boolean;
  animated: boolean;
}

// 阶段文案
const STAGE_LABELS: Record<string, string> = {
  "uploading": "上传中",
  "queued": "排队中",
  "generating": "生成中",
  "processing": "处理中",
  "finalizing": "完成中"
};
```

### 6.2 节点内进度显示

```
┌─────────────────────────────────────┐
│ 多角度                               │
│                                     │
│ 生成中 67%...          [取消]       │
│ ████████████░░░░░░░░  67%         │
│                                     │
│ 阶段: 生成中                         │
│ 预估剩余: 30秒                       │
└─────────────────────────────────────┘
```

---

## 七、错误处理

### 7.1 错误类型

```typescript
enum TaskErrorCode {
  // 客户端错误（4xx）
  INVALID_PARAMS = "INVALID_PARAMS",       // 参数错误
  NODE_NOT_FOUND = "NODE_NOT_FOUND",       // 节点不存在
  UNAUTHORIZED = "UNAUTHORIZED",           // 未授权
  QUOTA_EXCEEDED = "QUOTA_EXCEEDED",       // 配额超限

  // 服务端错误（5xx）
  INTERNAL_ERROR = "INTERNAL_ERROR",       // 内部错误
  MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE", // 模型不可用
  SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE", // 服务不可用

  // 超时错误
  TIMEOUT = "TIMEOUT",                     // 任务超时
  USER_CANCELLED = "USER_CANCELLED"        // 用户取消
}
```

### 7.2 重试策略

```typescript
const RETRY_CONFIG = {
  maxRetries: 3,
  initialDelay: 1000,    // 1秒
  maxDelay: 10000,       // 10秒
  backoffMultiplier: 2   // 指数退避
};

async function withRetry<T>(
  fn: () => Promise<T>,
  onRetry?: (attempt: number, error: Error) => void
): Promise<T> {
  let lastError: Error;
  let delay = RETRY_CONFIG.initialDelay;

  for (let i = 0; i < RETRY_CONFIG.maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      onRetry?.(i + 1, error);

      if (i < RETRY_CONFIG.maxRetries - 1) {
        await sleep(delay);
        delay = Math.min(delay * RETRY_CONFIG.backoffMultiplier, RETRY_CONFIG.maxDelay);
      }
    }
  }

  throw lastError!;
}
```

---

## 八、任务取消

### 8.1 取消API

```
POST /api/task/cancel
```

**请求体：**
```typescript
{
  taskId: string;
}
```

**响应：**
```typescript
{
  code: 0;
  message: "success";
}
```

### 8.2 前端取消实现

```typescript
class TaskManager {
  private activeTasks = new Map<string, AbortController>();

  async cancelTask(taskId: string): Promise<void> {
    const controller = this.activeTasks.get(taskId);
    if (controller) {
      controller.abort();
      this.activeTasks.delete(taskId);

      await fetch('/api/task/cancel', {
        method: 'POST',
        body: JSON.stringify({ taskId })
      });
    }
  }
}
```

---

## 九、与牛油果漫剧任务队列对比

| 维度 | 牛油果漫剧 | LibTV |
|------|-----------|-------|
| **通信方式** | WebSocket | HTTP轮询 |
| **提交API** | `/script/generate` | `/api/task/submit` |
| **进度API** | WebSocket推送 | `/api/task/generation/progress/batch` |
| **并发控制** | P-Queue | 推测：服务端控制 |
| **超时** | 120秒 | 推测：300轮询（约10分钟） |
| **重试** | 3次 | 推测：3次 |

---

## 十、总结

LibTV 的任务队列系统核心特点：

1. **HTTP轮询**：每2秒轮询一次进度
2. **批量查询**：支持同时查询多个任务进度
3. **状态完整**：pending → processing → completed/failed
4. **进度反馈**：实时百分比 + 阶段描述
5. **取消支持**：用户可随时取消任务
6. **错误处理**：分类错误码 + 重试机制

---

*文档版本：v1.0*
*最后更新：2026-03-23*
