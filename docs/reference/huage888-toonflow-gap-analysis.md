# huage888 借鉴 Toonflow-app 清单

> 生成时间：2026-04-07
> 对比基准：Toonflow-app v1.0.7 vs huage888 v4.0
> 输出目标：为 huage888 提供可落地的改进路径

---

## 一句话结论

> huage888 的**叙事体系**和**资产一致性机制**已超过 Toonflow，但 Toonflow 的**执行层自动化**和**实时反馈系统**是 huage888 最需要补齐的短板。

---

## P0 级：必须借鉴（核心差距）

### P0-1：EventEmitter + WebSocket 实时反馈系统

**Toonflow 做法：**
```typescript
// Storyboard Agent 事件推送
agent.emitter.on("stream", (text) => ws.send({ type: "stream", data: text }));
agent.emitter.on("toolCall", (data) => ws.send({ type: "toolCall", data }));
agent.emitter.on("shotsUpdated", (data) => ws.send({ type: "shotsUpdated", data }));
agent.emitter.on("shotImageGenerateProgress", (data) => ws.send({...}));
```

**huage888 现状：** 无实时反馈，依赖用户轮询或手动检查

**借鉴方案：**
```
qwen_pipeline.py / doubao_pipeline.py
    ↓
增加 EventEmitter 事件推送
    ↓
WebSocket 服务（可选，或输出到 stderr/文件）
    ↓
前端 / CLI 实时展示进度
```

**落地文件：**
- `scripts/event_emitter.py`（新建）
- `scripts/progress_server.py`（新建，WebSocket 服务）

---

### P0-2：完整的任务状态机

**Toonflow 做法：**
```typescript
t_video.state = 0  // 生成中
t_video.state = 1   // 生成成功
t_video.state = -1  // 生成失败（含 reason 字段）
```

**huage888 现状：** 仅部分 API 调用有重试，无统一状态管理

**借鉴方案：**
```python
# scripts/task_state.py（新建）
class TaskState:
    PENDING = 0      # 待执行
    RUNNING = 1      # 执行中
    SUCCESS = 2      # 成功
    FAILED = -1      # 失败
    RETRYING = 3     # 重试中

# 所有 Pipeline 增加状态追踪
def track_task(task_id, state, error_reason=None):
    # 写入 .huage888/tasks/<task_id>.json
    pass
```

**落地文件：**
- `scripts/task_state.py`（新建）
- 更新 `qwen_pipeline.py`、`doubao_pipeline.py`、`video_pipeline.py`

---

### P0-3：批量任务队列 + 自动重试

**Toonflow 做法：**
```typescript
// 批量视频生成，失败自动重试
async function generateVideoAsync(videoId, ...) {
  for (let retry = 0; retry < 3; retry++) {
    try {
      const videoPath = await u.ai.video(...);
      await u.db("t_video").where("id", videoId).update({ state: 1 });
      return;
    } catch (err) {
      await sleep(1000 * Math.pow(2, retry)); // 指数退避
    }
  }
  await u.db("t_video").where("id", videoId).update({ state: -1 });
}
```

**huage888 现状：** 仅 Doubao/Kling API 有基础重试（3次），qwen-max 无重试

**借鉴方案：**
```python
# scripts/task_queue.py（新建）
class TaskQueue:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    def execute_with_retry(self, task_fn, *args):
        for attempt in range(self.max_retries):
            try:
                return task_fn(*args)
            except RetryableError as e:
                wait = 2 ** attempt
                time.sleep(wait)  # 指数退避
        raise PermanentError(f"Failed after {self.max_retries} retries")
```

**落地文件：**
- `scripts/task_queue.py`（新建）
- 更新所有 pipeline 脚本

---

## P1 级：重要借鉴（体验提升）

### P1-1：资产版本控制机制

**Toonflow 做法：**
```typescript
// t_assets 表含完整历史
t_assets {
  filePath: string,      // 最新版本
  state: string,         // 状态
  // 历史通过 t_image 表管理
}
```

**huage888 现状：** 仅靠文件系统，资产更新无版本记录

**借鉴方案：**
```
assets/
├── C001漠玫/
│   ├── v1.0_2026-04-03_front.png    # 版本标记
│   ├── v1.0_2026-04-03_front.json   # 元数据
│   ├── v1.1_2026-04-05_refined.png  # 迭代版本
│   └── current.json                  # 指向最新版本
```

**落地文件：**
- `scripts/asset_version.py`（新建）
- 更新 `libtv-skill/SKILL.md` 增加版本规范

---

### P1-2：多厂商适配器的统一错误处理

**Toonflow 做法：**
```typescript
// utils/ai/video/index.ts
const adapters = {
  volcengine: volcengineAdapter,
  kling: klingAdapter,
  vidu: viduAdapter,
  wan: wanAdapter,
  gemini: geminiAdapter,
  runninghub: runninghubAdapter,
};

export default async (input, config) => {
  const adapter = adapters[config.manufacturer];
  if (!adapter) throw new Error(`Unknown manufacturer: ${config.manufacturer}`);
  return await adapter(input, config);
};
```

**huage888 现状：** `video_adapter_registry.py` 已实现适配器模式，但不够统一

**借鉴方案：**
```python
# scripts/adapters/base_adapter.py
class BaseAdapter(ABC):
    @abstractmethod
    def generate(self, config: VideoConfig) -> VideoResult:
        pass

    @abstractmethod
    def get_status(self, task_id: str) -> TaskStatus:
        pass

    def _handle_error(self, err: Exception) -> ErrorResult:
        # 统一错误格式化
        return ErrorResult(
            code=err.code if hasattr(err, 'code') else 'UNKNOWN',
            message=str(err),
            retryable=self._is_retryable(err)
        )
```

**落地文件：**
- 更新 `scripts/adapters/video_adapter_base.py`
- 更新 `scripts/adapters/doubao_adapter.py`
- 更新 `scripts/adapters/kling_adapter.py`

---

### P1-3：多模态 Prompt 注册表（双轨机制）

**Toonflow 做法：**
```typescript
// t_prompts 表管理所有 Prompt
interface t_prompts {
  id: number;
  type: string;      // role/scene/props/video
  name: string;
  systemPrompt: string;
  userPrompt: string;
  model?: string;
}
```

**huage888 现状：** `prompts-registry.md` 是静态 Markdown，动态性不足

**借鉴方案：**
```python
# config/prompts_registry.py（新建，替代 prompts-registry.md）
class PromptsRegistry:
    def __init__(self):
        self._cache = {}

    def get(self, agent_type: str, model: str = None) -> PromptConfig:
        # 支持覆盖机制：global → agent_type → model_override
        base = self._load_base(agent_type)
        override = self._load_override(agent_type, model)
        return merge_prompts(base, override)
```

**落地文件：**
- `config/prompts_registry.py`（新建）

---

### P1-4：完整的艺术风格库（200+）

**Toonflow 做法：**
```typescript
// lib/artStyle.ts
export const artStyles = [
  { category: "常用风格", items: ["2D动漫", "真人写实", "3D国创"] },
  { category: "IP风格", items: ["龙族传说", "蜡笔小新", "动森"] },
  { category: "插画风格", items: ["浮世绘", "波普印刷", "水彩"] },
  // ... 200+ 风格
];
```

**huage888 现状：** `visual-bible.md` 有 7 层身份锚点，但风格库规模较小

**借鉴方案：**
```python
# config/art_styles.py（新建）
ART_STYLES = {
    "常用风格": ["2D动漫", "真人写实", "三渲二", "吉卜力"],
    "IP风格": ["龙族传说", "比奇堡", "蜡笔小新", "动森"],
    "插画风格": ["浮世绘", "波普印刷", "水彩", "哥特霓虹"],
    "赛博墨韵": ["流动墨滴", "金色瞳孔", "青蓝水墨眼线"],  # 漠玫专属
    # ... 从 Toonflow artStyle.ts 迁移
}
```

**落地文件：**
- `config/art_styles.py`（新建，从 Toonflow 迁移）

---

## P2 级：增强借鉴（长期价值）

### P2-1：分镜 Agent 的 Tool Calling 模式

**Toonflow 做法：**
```typescript
// Storyboard Agent 内部有专门的 Tool 函数
segmentAgent.tools = {
  getScript: () => t_script.findAll({ scriptId }),
  getAssets: () => t_assets.findAll({ scriptId }),
  updateSegments: (segments) => t_segments.bulkUpdate(segments),
};

shotAgent.tools = {
  getSegments: () => t_segments.findAll({ scriptId }),
  addShots: (shots) => t_shots.insert(shots),
  generateShotImage: () => u.ai.image({ prompt }),
};
```

**huage888 现状：** 分镜脚本由 qwen-max 一次性生成，无交互式修正

**借鉴方案：**
```python
# skills/storyboard_agent.py（新建）
class StoryboardAgent:
    def __init__(self, project_id):
        self.tools = {
            "get_script": self._get_script,
            "get_assets": self._get_assets,
            "add_shots": self._add_shots,
            "update_shots": self._update_shots,
            "generate_shot_image": self._generate_shot_image,
        }

    def chat(self, user_message: str) -> str:
        # 调用 qwen-max，注入 tool definitions
        response = qwen.invoke(
            messages=[{"role": "user", "content": user_message}],
            tools=self._build_tool_definitions()
        )
        # 执行 Tool Calling
        for tool_call in response.tool_calls:
            result = self.tools[tool_call.name](**tool_call.arguments)
            response = qwen.continue_with(result)
        return response.content
```

**落地文件：**
- `skills/storyboard_agent.py`（新建）
- 更新 `skills/storyboard-skill.md`

---

### P2-2：Webhooks 通知机制

**Toonflow 做法：** 视频生成完成后通过 WebSocket 推送

**huage888 现状：** 无通知机制

**借鉴方案：**
```python
# scripts/webhook_notifier.py（新建）
class WebhookNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def notify(self, event: str, data: dict):
        requests.post(self.webhook_url, json={
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })

# 使用示例
notifier = WebhookNotifier(os.environ["WEBHOOK_URL"])
notifier.notify("video_generated", {"task_id": "xxx", "url": "..."})
```

**落地文件：**
- `scripts/webhook_notifier.py`（新建）

---

### P2-3：资产-镜头关联查询

**Toonflow 做法：**
```typescript
// t_assets 表完整关联
t_assets {
  type: "角色" | "场景" | "道具" | "分镜",
  scriptId: number,    // 关联剧本
  segmentId: number,   // 关联片段
  shotIndex: number,   // 关联镜头
}
```

**huage888 现状：** 资产在 `asset-registry.md` 中管理，但与分镜脚本关联不紧密

**借鉴方案：**
```python
# assets/03-asset-registry.md 增加字段
| C001 | 漠玫 | 角色 | 12345 | 1,3,5,7,9,11,13,15,17,19,21,23,25 | # 绑定到具体镜头 |
```

**落地文件：**
- 更新 `assets/03-asset-registry.md`

---

## P3 级：架构升级（可选）

### P3-1：数据库持久化（取代文件系统）

**Toonflow 做法：** SQLite + Knex ORM，82 个 API 端点

**huage888 现状：** 纯文件系统 + Markdown 配置

**评估：** 当前架构适合轻量，但规模扩大后需考虑数据库

**建议：** P3 阶段再评估

---

### P3-2：Electron 桌面应用

**Toonflow 做法：** Electron 打包，跨平台桌面应用

**huage888 现状：** Claude Code 编排 + 命令行脚本

**评估：** 当前定位是 Claude Code 插件，无需桌面应用

---

## 借鉴优先级总表

| 优先级 | 借鉴项 | 来源 | 难度 | 价值 |
|--------|--------|------|------|------|
| **P0-1** | EventEmitter + 实时反馈 | Toonflow | 中 | 🔴 核心差距 |
| **P0-2** | 完整任务状态机 | Toonflow | 低 | 🔴 核心差距 |
| **P0-3** | 批量队列 + 自动重试 | Toonflow | 中 | 🔴 核心差距 |
| **P1-1** | 资产版本控制 | Toonflow | 中 | 🟡 重要 |
| **P1-2** | 统一错误处理 | Toonflow | 低 | 🟡 重要 |
| **P1-3** | 双轨 Prompt 注册表 | Toonflow | 中 | 🟡 重要 |
| **P1-4** | 200+ 艺术风格库 | Toonflow | 低 | 🟡 重要 |
| **P2-1** | 分镜 Agent Tool Calling | Toonflow | 高 | 🟢 增强 |
| **P2-2** | Webhooks 通知 | Toonflow | 低 | 🟢 增强 |
| **P2-3** | 资产-镜头关联 | Toonflow | 低 | 🟢 增强 |

---

## 落地行动计划

### 第一阶段（1-2周）：执行层自动化

```
1. 新建 scripts/task_state.py      # 任务状态机
2. 新建 scripts/task_queue.py     # 批量队列
3. 新建 scripts/event_emitter.py  # 事件推送
4. 更新 doubao_pipeline.py         # 接入状态机
5. 更新 video_pipeline.py          # 接入队列
```

### 第二阶段（2-4周）：体验增强

```
1. 新建 config/art_styles.py        # 风格库扩展
2. 更新 assets/03-asset-registry.md # 镜头关联
3. 更新 scripts/adapters/          # 统一错误处理
4. 新建 config/prompts_registry.py # 双轨配置
```

### 第三阶段（长期）：智能增强

```
1. 新建 skills/storyboard_agent.py # 分镜 Agent
2. 新建 scripts/webhook_notifier.py # Webhooks
3. 评估数据库迁移（P3）
```

---

## huage888 独有的优势（Toonflow 应学习）

| 优势 | huage888 做法 | Toonflow 差距 |
|------|-------------|--------------|
| **7层身份锚点** | 视觉+气质+禁止变体+说话风格 | 仅外观描述 |
| **情绪弧线量化** | emotion 1-10 量表 | 无量化指标 |
| **资产一致性强制** | 禁用修饰词+禁止捏造 | 无强制规则 |
| **审核 Agent 三审制** | script→art→storyboard 三审 | 无细分审核 |

> huage888 在**叙事精细度**和**资产一致性**上已超过 Toonflow，核心差距是**执行层自动化**。
