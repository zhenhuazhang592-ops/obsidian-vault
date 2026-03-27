# ZJT（智剧通）· API层详细研究报告

## 一、整体架构概览

```
server.py (主入口)
├── script_writer_router (智能体剧本生成)
├── admin_router (后台管理)
└── system_router (系统状态)
```

---

## 二、智能体剧本生成 API（script_writer.py）

这是 ZJT 的核心模块，负责 **世界创建 → 剧本生成 → 资产管理的完整链路**。

### 2.1 核心组件初始化

```python
task_manager = TaskManager()       # 任务管理器
file_manager = FileManager(...)    # 文件管理器
tool_executor = ToolExecutor(...)   # 工具执行器
sessions_storage: Dict[str, ChatSession] = {}  # 内存会话存储
```

### 2.2 核心 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/session/create` | POST | 创建新会话 |
| `/api/session/{id}/history` | GET | 获取会话历史 |
| `/api/session/{id}/task` | POST | 创建智能体任务 |
| `/api/task/{id}/stream` | GET | **SSE 流式获取任务消息** |
| `/api/sync-files` | POST | 同步数据库到文件系统 |
| `/api/submit-to-database` | POST | 批量提交到数据库 |
| `/api/characters-files` | GET/POST | 角色卡管理 |
| `/api/scripts-files` | GET/POST | 剧本管理 |
| `/api/check-assets-complete` | POST | 检查资产完成状态 |

### 2.3 会话创建流程

```python
POST /api/session/create
→ 验证 auth_token
→ 同步数据库到文件系统（sync_database_to_files）
→ 生成 UUID 作为 session_id
→ 创建 ChatSession 实例（含 PMAgent）
→ 存入 sessions_storage
→ 后台线程启动任务
```

### 2.4 SSE 流式响应机制

```python
async def event_generator():
    while True:
        msg = await asyncio.to_thread(task.message_queue.get, timeout=5)
        yield f"data: {json.dumps(msg)}\n\n"
        # 5秒超时发送心跳
        # 完成或错误时结束流
```

**消息格式**：
```json
{"type": "message", "role": "assistant", "content": "..."}
{"type": "done", "status": "COMPLETED"}
{"type": "heartbeat", "timestamp": "2026-03-25T..."}
{"type": "error", "error": "..."}
```

### 2.5 数据库同步机制

```python
POST /api/sync-files
→ 从 WorldModel/CharacterModel/ScriptModel/LocationModel/PropsModel 读取
→ 写入文件系统（worlds/*.json, characters/*.json, scripts/*.json 等）
```

```python
POST /api/submit-to-database
→ 从文件系统读取
→ 批量写入数据库
→ 返回成功/失败/跳过统计
```

---

## 三、供应商客户端封装

### 3.1 Duomi 客户端（duomi_client.py）

**视频生成 API**：

| 方法 | 说明 |
|------|------|
| `create_image_to_video` | Sora2 图生视频 |
| `create_image_to_video_veo` | Veo3.1 图生视频（首尾帧模式） |
| `create_character` | 创建角色生成任务 |
| `create_video_remix` | 视频重混 |
| `get_ai_task_result` | 统一任务查询接口 |
| `create_kling_image_to_video` | Kling 图生视频 |

**Kling 参数**：
```python
def create_kling_image_to_video(
    image_url,
    prompt,
    mode="std",           # "std"=5秒, "pro">5秒
    duration=5,          # 5或10秒
    model_name="kling-v2-5-turbo",
    cfg_scale=0.5,       # 创意相关性 0-1
    negative_prompt=""
)
```

### 3.2 RunningHub 客户端（runninghub_client.py）

**核心数据结构**：

```python
class TaskStatus(Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SUCCESS = "SUCCESS"

class RunningHubClient:
    WEBAPP_ID = "1960639129312780290"  # NanoBanana 图片编辑

    def run_task(self, node_info_list, transaction_id) -> Dict
    def check_status(self, task_id) -> TaskStatus
    def get_outputs(self, task_id) -> List[TaskResult]
    def wait_for_completion(self, task_id, timeout=?, check_interval=?)
    def run_and_wait(self, node_info_list, timeout=?, max_retries=3)
```

**LTX2 图生视频 Node 配置**：

| nodeId | fieldName | 说明 |
|-------|-----------|------|
| 67 | image | 上传图像 |
| 123 | text | 魔搭社区key |
| 66 | value | 最长边 |
| 52 | value | 时长 |
| 108 | select | 镜头运动选择 |
| 160 | select | 提示词设置 |
| 96 | text | 提示词 |

**Wan2.2 图生视频 Node 配置**：

| nodeId | fieldName | 说明 |
|-------|-----------|------|
| 135 | image | 上传图像 |
| 107 | value | 时长（秒） |
| 153 | select | 高清版/极速版切换 |
| 247 | select | 设置比例 |
| 116 | text | 手写/润色文本 |

**数字人 Node 配置**：

| nodeId | fieldName | 说明 |
|-------|-----------|------|
| 126 | image | 上传图像 |
| 127 | aspect_ratio | 输出比例 |
| 184 | text | 讲话内容 |
| 185 | audio | 音频 |
| 217 | select | 选择模式 |

### 3.3 Vidu 客户端（vidu_client.py）

| 方法 | 说明 |
|------|------|
| `create_vidu_image_to_video` | Vidu 图生视频 |
| `create_vidu_text_to_video` | Vidu 文生视频 |
| `create_vidu_start_end_to_video` | 首尾帧图生视频 |
| `get_vidu_task_status` | 状态查询 |

**首尾帧参数**：
```python
def create_vidu_start_end_to_video(
    start_image_url,
    end_image_url,
    prompt,
    model="viduq2-pro-fast",
    duration=5,
    resolution="720p",
    movement_amplitude="auto"  # auto/small/medium/large
)
```

---

## 四、管理后台 API（admin.py）

### 4.1 权限校验

```python
async def require_admin(auth_token: str = Header) -> User:
    # 1. 验证 token 存在
    # 2. 获取用户ID
    # 3. 检查用户角色为 'admin'
```

### 4.2 核心端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/admin/dashboard` | GET | 仪表盘统计 |
| `/api/admin/users` | GET/PUT | 用户管理 |
| `/api/admin/config` | GET/PUT | 配置管理 |
| `/api/admin/config/batch` | PUT | 批量更新配置 |
| `/api/admin/config/test-google` | POST | 测试 Google API |
| `/api/admin/users/{id}/power` | POST | 调整算力 |

### 4.3 算力调整

```python
class AdjustPowerRequest(BaseModel):
    amount: int   # 正数增加，负数扣减
    reason: str    # 调整原因（必填）
```

**逻辑**：调用 `ComputingPowerModel.admin_adjust()`，自动记录日志。

---

## 五、系统状态 API（system.py）

```json
GET /api/system/task-configs
{
  "data": {
    "task_list": [...],      // 支持的任务类型
    "categories": [...],     // 分类信息
    "vendors": [...]         // 供应商信息
  }
}
```

前端通过此接口动态获取所有任务配置，无需硬编码。

---

## 六、通用抽象模式分析

### 6.1 客户端统一模式

```python
# 1. Token 获取（动态配置）
def _get_token():
    return get_dynamic_config_value("vendor", "token", default="")

# 2. 测试模式支持
def _is_test_mode_enabled() -> bool

# 3. 请求日志
logger.info(f"[Vendor API] Request Payload: {json.dumps(payload)}")

# 4. 错误处理
except requests.exceptions.RequestException as e:
    return {"error": str(e)}
```

### 6.2 状态统一映射

```python
# 外部状态 -> 内部状态
state = "succeeded" -> status = 1
state = "processing" -> status = 0
state = "error" -> status = 2
```

### 6.3 异步任务处理模式

```python
# 1. 提交任务（返回 task_id）
def submit_task(ai_tool) -> task_id

# 2. 轮询状态
def check_status(task_id) -> (status, result_url)

# 3. 获取结果
def get_outputs(task_id) -> List[TaskResult]
```

---

## 七、关键设计决策

### 7.1 内存会话存储（临时方案）

```python
sessions_storage: Dict[str, ChatSession] = {}  # 内存会话
```

**注意**：生产环境应使用数据库或 Redis。

### 7.2 后台线程执行任务

```python
task_thread = threading.Thread(target=run_task_sync, daemon=True)
task_thread.start()
```

### 7.3 SSE 流式响应

- 使用 `asyncio.to_thread` 避免阻塞
- 5秒超时发送心跳
- 6次心跳后断开

### 7.4 三层驱动架构

```
业务层 (Business) → 实现层 (Implementation) → 供应商层 (Vendor)
```

允许在不修改业务代码的情况下切换供应商。
