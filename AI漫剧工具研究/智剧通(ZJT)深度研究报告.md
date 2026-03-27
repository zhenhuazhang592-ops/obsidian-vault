# 智剧通（ZJT）深度研究报告

> 分析时间：2026-03-25
> 分析目的：为漫舟 AI Short Drama Studio 优化提供借鉴

---

## 一、项目定位与架构总览

**智剧通（ZJT）** = AI短剧创作平台，覆盖**剧本创作 → 分镜解析 → AI视频生成**完整链路。

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | MySQL + SQLAlchemy + Alembic |
| LLM调用 | Gemini API（代理/官方端点自动探测） |
| 任务调度 | APScheduler |
| 认证 | JWT Token |
| 前端 | 原生JavaScript + Vue 3 |
| 图表 | Canvas 2D（自定义节点编辑器） |
| 日志 | Sentry SDK |

### 项目目录结构

```
ZJT-main/
├── server.py                    # 主入口 (~280KB，所有路由和逻辑)
├── api/
│   ├── script_writer.py        # 剧本创作API（核心）
│   ├── admin.py                # 管理后台API
│   └── clients/                # 外部API客户端
│       ├── runninghub_client.py
│       ├── duomi_client.py
│       └── vidu_client.py
├── script_writer_core/          # 剧本创作核心（多智能体系统）
│   ├── agents/                 # 智能体实现
│   ├── mcp_tool.py            # MCP工具定义
│   ├── file_manager.py        # 文件管理
│   └── skill_loader.py        # 技能加载
├── task/                        # 任务执行层
│   └── visual_drivers/         # 视频生成驱动
│       ├── base_video_driver.py
│       ├── driver_factory.py
│       └── *.py                # 各模型驱动
├── llm/                         # LLM调用层
│   ├── gemini_client.py
│   └── script_parser.py        # 剧本解析（核心）
├── model/                       # 数据模型层
│   ├── world.py
│   ├── character.py
│   ├── location.py
│   ├── script.py
│   └── ...
├── web/                         # 前端资源
│   ├── index.html
│   ├── video_workflow.html     # 视频工作流编辑器
│   ├── script_writer.html      # 剧本创作系统
│   └── js/
│       ├── workflow.js          # 工作流核心
│       ├── nodes.js             # 节点定义
│       ├── canvas.js            # 画布编辑器
│       ├── events.js
│       └── timeline.js
└── config/
    ├── unified_config.py        # 统一配置管理
    ├── constant.py              # 常量定义
    └── default_configs.py       # 默认配置
```

---

## 二、多智能体协作系统（最核心模块）

### 2.1 整体架构

```
用户输入
    │
    ▼
┌─────────────────────────────┐
│       PM Agent              │  ← 项目经理智能体（协调器）
│   (Project Manager)          │
│                             │
│ • 任务拆分                  │
│ • 派发专家智能体            │
│ • 验证结果                  │
│ • 失败熔断                  │
└──────────────┬──────────────┘
               │
               ▼ 调用工具
┌─────────────────────────────┐
│     Tool Executor           │  ← 工具执行器
│                             │
│ • MCP工具调用               │
│ • 文件读写                  │
│ • AI生图                    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│     Expert Agents            │  ← 专家智能体池
│                             │
│ • story-writer    剧本创作  │
│ • character-creator 角色创建  │
│ • location-creator 场景创建  │
│ • prop-creator     道具创建  │
└─────────────────────────────┘
```

### 2.2 PM Agent 完整实现

**文件**: `script_writer_core/agents/pm_agent.py`（608行）

#### 系统提示词

```python
base_prompt = """你是剧本架构师（Script Orchestrator），负责协调专家智能体完成剧本创作。

**核心原则**：
- 你是协调者，不是内容创作者
- 严禁直接编写剧本、角色卡、场景描述、道具信息等内容
- 所有内容创作必须通过调用对应的专家智能体完成

**可用工具**：
1. call_agent(AgentName, task_description): 调用专家智能体执行任务
2. request_human_verification(...): 请求人工验证确认

**约束**：
- 任务必须串行执行，一次只能调用一个专家
- 连续失败3次或累计失败7次时必须停止并报告
- 绝不直接生成剧本内容，必须通过 call_agent 调用专家
"""
```

#### 环境上下文构建

```python
# 1. 初始化时获取环境上下文
env_context = self.file_manager.get_context_for_ai(
    user_id, world_id,
    summary_only=True  # PM初始化用摘要模式，节省token
)

# 2. 截断超长上下文（>5000字符）
if len(env_context) > 5000:
    env_context = self._truncate_environment_context(...)

# 3. 构建增强提示词
enhanced_system_prompt = f"""{base_system_prompt}

{'='*60}
# 【重要】当前项目已有的环境内容

在制定创作计划时，你必须：
1. 仔细阅读已有的剧本内容，了解故事进展
2. 确保新内容与现有角色、场景、道具保持一致
3. 续集剧本要承接已有剧情，保持连贯性

{env_context}
"""
```

#### PM 主循环逻辑

```python
def _run_pm_loop(self, task, session_data, max_iterations=50):
    """PM主循环"""
    while iteration < max_iterations:
        # 1. 检查熔断
        if self.should_stop():
            break

        # 2. 发送进度消息
        task.message_queue.put({"type": "progress", "step": "..."})

        # 3. 构建消息列表
        messages = self._build_messages_for_api()
        # system_prompt + conversation_history

        # 4. 获取工具定义
        tool_defs = self._get_tool_definitions()

        # 5. 调用LLM
        response = self.gemini_client.call_api(
            messages=messages,
            tools=tool_defs
        )

        # 6. 处理响应
        if hasattr(response, 'tool_calls'):
            self._handle_tool_calls(response, task, session_data)
        else:
            return response.content
```

#### 失败熔断机制

```python
# 双层熔断
self.consecutive_failures = 0      # 连续失败计数
self.total_failures = 0            # 累计失败计数
self.max_consecutive_failures = 3   # 连续失败阈值
self.max_total_failures = 7         # 累计失败阈值

def should_stop(self) -> tuple[bool, str]:
    if self.consecutive_failures >= self.max_consecutive_failures:
        return True, f"连续失败{self.max_consecutive_failures}次"
    if self.total_failures >= self.max_total_failures:
        return True, f"累计失败{self.max_total_failures}次"
    return False, ""
```

### 2.3 Expert Agent 完整实现

**文件**: `script_writer_core/agents/expert_agent.py`（325行）

```python
def execute_task(self, task):
    """专家任务执行流程"""
    # 1. 添加对话历史
    for msg in task.conversation_history:
        self.add_to_history(msg.role, msg.content)

    # 2. 添加用户任务描述
    self.add_to_history("user", task.description)

    # 3. 执行任务循环（最多10轮）
    while iteration < 10:
        response = self.gemini_client.call_api(...)
        if hasattr(response, 'tool_calls'):
            self._handle_tool_calls(response)
        else:
            return {"success": True, "result": response.content}

    # 4. 保存会话历史到文件
    self._save_session_history(...)

    return {"success": True, "result": ...}
```

### 2.4 工具调用链路

```
PM Agent
    │
    ├─► _handle_tool_calls(tool_calls)
    │       │
    │       ▼
    │     _execute_tool("call_agent", args)
    │       │
    │       ▼
    │     _handle_agent_call(AgentName, task_description)
    │       │
    │       ├─► 检查 expert_agents 配置
    │       ├─► _build_context_for_expert()
    │       │     summary_only=False（专家用完整上下文）
    │       ├─► 创建 ExpertAgent 实例
    │       └─► expert.execute_task()
    │             │
    │             ├─► gemini_client.call_api()
    │             ├─► 处理响应
    │             └─► 返回结果
    │
    ├─► 成功 → consecutive_failures = 0
    └─► 失败 → total_failures++, consecutive_failures++
```

### 2.5 可借鉴的实现模式

| 模式 | 实现方式 | 借鉴价值 |
|------|----------|----------|
| **渐进式上下文披露** | PM用summary_only=True，Expert用False | 控制token消耗 |
| **双层熔断** | 连续3次+累计7次双重熔断 | 系统健壮性 |
| **工具白名单** | 每个Agent配置allowed_tools | 安全隔离 |
| **后台任务+消息队列** | 后台线程+Queue+SSE推送 | 实时进度 |
| **长文本分片** | >5000字保存文件，AI按需读取 | 避免截断 |
| **会话历史持久化** | 完整对话保存到文件 | 问题复盘 |
| **Human-in-loop** | request_human_verification | 关键节点审核 |

---

## 三、剧本解析核心算法

### 3.1 函数签名

**文件**: `llm/script_parser.py`

```python
async def parse_script_to_shots(
    script_content: str,
    max_group_duration: int = 15,        # 每组分镜最大时长
    world_id: Optional[int] = None,      # 关联数据库
    model: Optional[str] = None,
    temperature: float = 0.7,
    force_medium_shot: bool = False,    # 强制对话镜头中景
    no_bg_music: bool = False,
    split_multi_dialogue: bool = False,  # 多人对话拆分
    narration_as_dialogue: bool = False, # 解说剧模式
    auth_token: Optional[str] = None,
    vendor_id: Optional[int] = None,
    model_id: Optional[int] = None
) -> Dict[str, Any]:
```

### 3.2 系统提示词（完整内容）

```python
SCRIPT_PARSER_SYSTEM_PROMPT = """你是一个专业的影视剧本分析师和分镜师，擅长将剧本拆解为人物、场景和分镜。
你需要根据输入的剧本内容，输出结构化的JSON格式数据。

输出要求：
1. 必须严格按照指定的JSON格式输出
2. 分镜组默认每个15秒，可根据剧情需要调整
3. 人物信息要完整，包括角色定位和描述
4. **【重要警告】在分镜描述中严禁描写人物外貌特征**：系统的角色库中已有完整的外貌信息...
5. 场景信息要详细，包括时间、天气、氛围、环境音、背景音乐等
6. **场景支持嵌套层级**：通过parent_id和level字段表示场景的层级关系
7. **场景与数据库关联**：每个location必须包含location_db_id字段
8. **道具与数据库关联**：每个props必须包含props_db_id字段
9. 分镜要包含镜头类型、运动方式、对话、动作等详细信息
10. opening_frame_description是最关键字段，用于AI生成首帧图像...
11. 确保所有ID引用关系正确
12. 只输出纯JSON内容，不要添加```json```标记或任何解释性文字
13. **【重要】在shot节点的所有文本字段中，只要涉及角色名称，必须用【【角色名】】格式包裹**
```

### 3.3 数据库上下文注入

```python
# 获取数据库已有场景列表
db_locations = LocationModel.get_tree_by_world(world_id=world_id, limit=20)

# 格式化场景树
def format_location_tree(locations, indent=0):
    result = []
    for loc in locations:
        result.append(f"- ID: {loc['id']}, 名称: {loc['name']}, 描述: {loc.get('description', '无')}")
        if loc.get('children'):
            result.extend(format_location_tree(loc['children'], indent + 1))
    return result

# 构建用户提示词
user_prompt = f"""请将以下剧本内容解析为结构化的JSON数据。

剧本内容：
```{script_content} ```

数据库中的场景列表：
```{db_locations_text} ```

**【核心要求 - 必须严格遵守】**

1. **镜头组时长限制（最重要）**：
   - 【硬性规则】每个shot_group内所有shots的duration总和绝对不能超过{max_group_duration}秒
   - 【强制分组规则】相同地点的连续镜头，只要总时长不超过限制，必须强制放在同一个shot_group中
   - 【成本优化要求】每个shot_group的总时长应该尽可能接近{max_group_duration}秒
"""
```

### 3.4 JSON响应解析策略

```python
# 1. 清理markdown代码块
cleaned_content = response_content.strip()
if cleaned_content.startswith("```json"):
    cleaned_content = cleaned_content[7:]
cleaned_content = cleaned_content.strip()

# 2. 解析JSON
parsed_data = json.loads(cleaned_content)

# 3. 验证必需字段
required_keys = ["characters", "locations", "shot_groups"]
missing_keys = [key for key in required_keys if key not in parsed_data]
if missing_keys:
    raise Exception(f"返回的JSON缺少必需字段: {', '.join(missing_keys)}")

# 4. JSON截断修复
if not cleaned_content.endswith('}'):
    last_bracket = cleaned_content.rfind(']')
    if last_bracket > 0:
        fixed_content = cleaned_content[:last_bracket+1] + '\n}'
        parsed_data = json.loads(fixed_content)
```

### 3.5 分镜组重组算法（贪心）

```python
def reorganize_shot_groups(parsed_data, max_group_duration):
    """
    策略：
    1. 提取所有shots并按shot_number排序（保持全局顺序）
    2. 按顺序遍历shots，根据时长限制进行分组
    3. 尽量让每个分镜组接近max_group_duration秒（贪心算法）
    """
    all_shots = []
    for group in shot_groups:
        shots = group.get("shots", [])
        all_shots.extend(shots)

    # 按shot_number排序
    all_shots.sort(key=lambda s: s.get("shot_number", 0))

    # 贪心重组
    new_shot_groups = []
    group_counter = 1
    current_group_shots = []
    current_group_duration = 0.0

    for shot in all_shots:
        shot_duration = float(shot.get("duration", 0))

        # 如果加入当前镜头会超过限制，则创建新组
        if current_group_shots and (current_group_duration + shot_duration) > max_group_duration:
            new_shot_groups.append({
                "group_id": f"grp_{group_counter:03d}",
                "group_name": f"分镜组{group_counter}",
                "shots": current_group_shots
            })
            group_counter += 1
            current_group_shots = [shot]
            current_group_duration = shot_duration
        else:
            current_group_shots.append(shot)
            current_group_duration += shot_duration
```

### 3.6 解说剧模式转换

```python
async def convert_script_to_narration(script_content, model=None, temperature=0.5, ...):
    """
    将包含角色对话的剧本转换为纯旁白解说格式
    """
    user_prompt = f"""请将以下包含角色对话的剧本转换为纯旁白解说风格的剧本。
    原始剧本：
    ```{script_content} ```

    转换要求：
    1. 保留原剧本的场景划分
    2. 每个场景输出两部分：
       - 【画面描述】：详细描述画面中发生的一切
       - 【旁白台本】：用旁白的方式讲述这个场景
    3. 将所有角色对话转化为旁白叙述
    """
```

---

## 四、视频生成驱动工厂

### 4.1 三层解耦架构

```
任务类型 (type=10)
    │
    ▼
业务驱动名称 (driver_name="wan22_image_to_video")
    │
    ▼
实现驱动名称 (implementation="wan22_runninghub_v1")
    │
    ▼
驱动类实例 (Wan22RunninghubV1Driver)
```

### 4.2 驱动工厂实现

```python
class VideoDriverFactory:
    _registered_drivers: Dict[str, type] = {}

    @classmethod
    def register_driver(cls, driver_name: str, driver_class: type):
        """注册驱动类"""
        if not issubclass(driver_class, BaseVideoDriver):
            raise ValueError(f"Driver class must inherit from BaseVideoDriver")
        cls._registered_drivers[driver_name] = driver_class

    @classmethod
    def create_driver_by_type(cls, driver_type: int) -> Optional[BaseVideoDriver]:
        # 第一层：任务类型 → 业务驱动名称
        config = UnifiedConfigRegistry.get_by_id(driver_type)
        business_driver_name = config.driver_name

        # 第二层：业务驱动名称 → 实现驱动名称
        implementation_driver_name = config.implementation

        # 第三层：实现驱动名称 → 驱动类实例
        driver_class = cls._registered_drivers.get(implementation_driver_name)
        return driver_class()
```

### 4.3 抽象基类

```python
class BaseVideoDriver(ABC):
    @abstractmethod
    def submit_task(self, ai_tool) -> Dict[str, Any]:
        """提交任务到外部API"""

    @abstractmethod
    def check_status(self, project_id: str) -> Dict[str, Any]:
        """检查任务状态"""

    @abstractmethod
    def build_create_request(self, ai_tool) -> Dict[str, Any]:
        """构建创建请求"""

    @abstractmethod
    def build_check_query(self, project_id: str) -> Dict[str, Any]:
        """构建状态查询请求"""

    # 共有方法
    def _request(self, url, method="POST", json=None, headers=None):
        """统一HTTP请求，自动记录日志"""

    def _validate_required(self, configs: Dict[str, str]):
        """验证必要配置"""

    def get_first_last_frames(self, ai_tool) -> tuple:
        """获取首尾帧"""

    def get_reference_images(self, ai_tool) -> list:
        """获取参考图"""
```

### 4.4 已注册驱动清单

| 驱动 | 实现类 | 供应商 | API类型 |
|------|--------|--------|---------|
| Sora2 | `Sora2DuomiV1Driver` | 多米 | 异步 |
| Kling | `KlingDuomiV1Driver` | 多米 | 异步 |
| Gemini | `GeminiDuomiV1Driver` | 多米 | 异步 |
| VEO3 | `Veo3DuomiV1Driver` | 多米 | 异步 |
| LTX2 | `Ltx2RunninghubV1Driver` | RunningHub | 异步 |
| Wan22 | `Wan22RunninghubV1Driver` | RunningHub | 异步 |
| 数字人 | `DigitalHumanRunninghubV1Driver` | RunningHub | 异步 |
| Vidu | `ViduDefaultDriver` | Vidu | 异步 |
| Vidu Q2 | `ViduQ2Driver` | Vidu | 异步 |
| Seedream | `Seedream5VolcengineV1Driver` | 火山引擎 | **同步** |

### 4.5 调用链路

```
调度器 (scheduler.py)
    │
    ▼
process_generate_video(task)
    │
    ├─► 状态=PENDING → _submit_new_task()
    │       │
    │       ├─► VideoDriverFactory.create_driver_by_type(type)
    │       ├─► driver.submit_task(ai_tool)
    │       └─► 返回 project_id
    │
    └─► 状态=PROCESSING → _check_task_status()
            │
            ├─► VideoDriverFactory.create_driver_by_type(type)
            ├─► driver.check_status(project_id)
            │
            ├─► SUCCESS → download_and_cache() + 更新数据库
            ├─► FAILED → 退还算力
            └─► RUNNING → 继续轮询
```

### 4.6 设计模式总结

| 模式 | 应用位置 | 价值 |
|------|----------|------|
| **工厂模式** | `create_driver_by_type()` | 解耦业务与实现 |
| **策略模式** | 各驱动不同实现 | 灵活切换 |
| **模板方法** | `BaseVideoDriver._request()` | 代码复用 |
| **单例模式** | `UnifiedConfigRegistry` | 全局配置 |
| **外观模式** | 驱动统一封装 | 简化调用 |

---

## 五、Gemini 客户端封装

### 5.1 端点自动探测

```python
GEMINI_URL_FORMATS = {
    "proxy": "/gemini/v1/models/{model}:generateContent",      # 第三方代理
    "official": "/v1beta/models/{model}:generateContent"       # 官方格式
}

def _build_url(self, model: str) -> str:
    base_url = self.base_url.rstrip('/')

    # 1. 检查缓存
    if base_url in GeminiClient._url_format_cache:
        fmt = GeminiClient._url_format_cache[base_url]
        return f"{base_url}{GEMINI_URL_FORMATS[fmt].format(model=model_name)}"

    # 2. 探测格式
    for fmt_name, fmt_path in GEMINI_URL_FORMATS.items():
        url = f"{base_url}{fmt_path.format(model=model_name)}"
        if self._probe_url_format(url):
            GeminiClient._url_format_cache[base_url] = fmt_name
            return url

    # 3. 探测失败，使用默认格式
    return f"{base_url}{GEMINI_URL_FORMATS['proxy'].format(model=model_name)}"

def _probe_url_format(self, url: str) -> bool:
    """轻量级探测URL格式是否有效"""
    test_payload = {
        "contents": [{"role": "user", "parts": [{"text": "Hi"}]}],
        "generationConfig": {"maxOutputTokens": 1}
    }
    response = requests.post(url, headers=headers, json=test_payload, timeout=10)

    if response.status_code == 404:
        return False  # 格式错误
    if response.status_code in [401, 403]:
        return True   # 格式正确但认证失败
    if response.status_code == 200:
        return "candidates" in response.json()
```

### 5.2 OpenAI → Gemini 格式转换

```python
def _convert_to_gemini_format(self, messages, tools=None):
    gemini_data = {
        "contents": [],
        "generationConfig": {}
    }

    for msg in messages:
        role = msg.get("role")

        if role == "system":
            gemini_data["systemInstruction"] = {"parts": [{"text": msg["content"]}]}
        elif role == "user":
            gemini_data["contents"].append({"role": "user", "parts": [{"text": msg["content"]}]})
        elif role == "assistant":
            parts = []
            if msg.get("content"):
                parts.append({"text": msg["content"]})
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    # 添加 thought_signature（Gemini特殊要求）
                    parts.append(function_call_part)
            gemini_data["contents"].append({"role": "model", "parts": parts})
        elif role == "tool":
            gemini_data["contents"].append({
                "role": "user",
                "parts": [{"toolResult": {...}}]
            })
```

### 5.3 Token使用统计

```python
def _analyze_token_usage(self, usage_metadata: Dict) -> Dict[str, int]:
    prompt_tokens = usage_metadata.get("promptTokenCount", 0)
    completion_tokens = usage_metadata.get("candidatesTokenCount", 0)
    total_tokens = usage_metadata.get("totalTokenCount", 0)
    cached_tokens = usage_metadata.get("cachedContentTokenCount", 0)

    # 上报到计费系统
    make_perseids_request(
        endpoint='user/token_log',
        method='POST',
        data={
            "input_token": total_tokens - completion_tokens,
            "output_token": completion_tokens,
            "cache_read": cached_tokens,
            "model_id": model_id,
            "vendor_id": vendor_id
        }
    )
```

---

## 六、API 接口设计

### 6.1 剧本创作API

**文件**: `api/script_writer.py`

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/session/create` | POST | 创建会话 |
| `/api/session/{id}/task` | POST | 创建智能体任务 |
| `/api/task/{id}/stream` | GET | SSE流式获取消息 |
| `/api/task/{id}/status` | GET | 获取任务状态 |
| `/api/verification/{id}` | POST | 提交人工验证 |
| `/api/characters-files` | GET/POST | 角色卡CRUD |
| `/api/scripts-files` | GET/POST | 剧本CRUD |
| `/api/locations-files` | GET/POST | 场景CRUD |
| `/api/props-files` | GET/POST | 道具CRUD |
| `/api/sync-files` | POST | 数据库→文件系统同步 |
| `/api/submit-to-database` | POST | 文件系统→数据库提交 |

### 6.2 SSE流式实现

```python
@router.get('/task/{task_id}/stream')
async def stream_task_messages(request: Request, task_id: str):
    async def event_generator():
        heartbeat_counter = 0

        while True:
            try:
                # 从消息队列获取消息（超时5秒）
                msg = await asyncio.to_thread(task.message_queue.get, timeout=5)
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"

                # 完成/错误消息结束流
                if msg.get('type') in ['done', 'error']:
                    break

                heartbeat_counter = 0

            except:
                # 超时发送心跳（30秒无消息）
                heartbeat_counter += 1
                if heartbeat_counter >= 6:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    heartbeat_counter = 0

                # 检查任务状态
                if task.status in [COMPLETED, FAILED, CANCELLED]:
                    break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
        }
    )
```

### 6.3 前端SSE消费

```javascript
const eventSource = new EventSource(`/api/task/${taskId}/stream`);

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'message') {
        // 文本消息，逐字追加
        fullText += data.content + '\n\n';
        contentDiv.innerHTML = renderMarkdown(fullText);
    } else if (data.type === 'progress') {
        // 进度更新
        updateStatus(`执行中: ${data.step || ''}`);
    } else if (data.type === 'done') {
        eventSource.close();
        loadComputingPower();
        refreshFiles();
    } else if (data.type === 'error') {
        eventSource.close();
        showError('任务执行错误: ' + data.error);
    }
};
```

---

## 七、可视化工作流编辑器

### 7.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│                   video_workflow.html                │
├──────────────┬─────────────────────┬────────────────┤
│   节点面板   │      画布区域        │    小地图      │
│  (addMenu)   │     (canvas)       │   (minimap)    │
│              │                     │                │
│  • 视频      │  ┌────┐            │  ┌──────────┐  │
│  • 图片      │  │节点│──────────│  │  ┌──┐     │  │
│  • 剧本      │  └──┬─┘            │  │  │  │    │  │
│  • 分镜组    │     │              │  └──────────┘  │
│  • 角色      │     ▼              │                 │
│  • 场景      │  ┌────┐            │  ┌────────────┐ │
│  • 道具      │  │节点│            │  │  时间轴    │ │
│  • 语音      │  └────┘            │  └────────────┘ │
│  └──────────┘   (SVG贝塞尔曲线)   └─────────────────┘
└─────────────────────────────────────────────────────┘
```

### 7.2 节点类型

| 节点类型 | 用途 | 关键配置 |
|---------|------|---------|
| `video` | 本地视频上传 | file, url, duration |
| `image` | 文生图/图片编辑 | prompt, model, ratio |
| `image_to_video` | 图生视频 | prompt, startUrl, endUrl, videoModel |
| `script` | 剧本输入 | scriptContent, maxGroupDuration |
| `shot_group` | 分镜组 | shots[], groupDuration |
| `shot_frame` | 分镜节点 | imagePrompt, videoPrompt, shotType |
| `character` | 角色引用 | name, referenceImage, emotionVoices |
| `location` | 场景引用 | name, parentId, referenceImage |
| `props` | 道具引用 | name, referenceImage |
| `text_to_speech` | 语音合成 | text, voice, emotion |
| `dialogue_group` | 对话组 | dialogues[], duration |

### 7.3 状态管理

```javascript
const state = {
    ratio: '16:9',           // 画面比例
    nodes: [],               // 节点数组
    connections: [],          // 连接线

    // 视口状态
    panX: 0, panY: 0,
    zoom: 1,

    // 时间轴
    timeline: {
        clips: [],
        audioClips: [],
        pillars: [],  // 分镜时间区域
    },

    // 历史记录（撤销/重做）
    history: [],
    historyPointer: -1,
    historyLimit: 50
};
```

### 7.4 序列化

```javascript
function serializeWorkflow(){
    return {
        version: '1.0',
        ratio: state.ratio,
        viewport: { panX, panY, zoom },
        nodes: state.nodes.map(node => ({
            id: node.id,
            type: node.type,
            x: node.x,
            y: node.y,
            data: { ...node.data, file: null, url: '' }  // 清理临时数据
        })),
        connections: state.connections,
        timeline: state.timeline
    };
}
```

---

## 八、数据模型层

### 8.1 核心实体关系

```
World (世界设定)
    │
    ├── Character (角色) ── N:1 ── World
    ├── Location (场景) ── N:1 ── World (支持树形自引用 parent_id)
    ├── Props (道具) ── N:1 ── World
    └── Script (剧本) ── N:1 ── World

VideoWorkflow (工作流) ── N:1 ── World
Task (任务) ── N:1 ── VideoWorkflow
AiTools (AI工具) ── N:1 ── Task
```

### 8.2 关键字段设计

**World模型**
```python
class World:
    id, name, description
    story_outline          # 故事大纲
    visual_style           # 视觉风格
    era_environment        # 时代背景
    color_language         # 色彩语言
    composition_preference # 构图偏好
    user_id, create_time, update_time
```

**Character模型**
```python
class Character:
    id, world_id, name, age, identity
    appearance             # 外貌描述（系统角色库）
    personality            # 性格特点
    behavior               # 行为特征
    reference_image        # 参考图
    emotion_voices: Dict  # 情感语音映射 {"开心": "voice_xxx", "悲伤": "voice_yyy"}
    default_voice
```

**Location模型**
```python
class Location:
    id, world_id, name
    parent_id              # 树形支持（父场景ID）
    level                  # 层级深度
    reference_image
    description            # 场景描述
```

---

## 九、统一配置系统

### 9.1 任务配置

```python
@dataclass
class UnifiedTaskConfig:
    id: int                          # 任务类型ID
    key: str                         # 唯一标识符
    name: str                         # 显示名称
    category: str                      # 主分类（IMAGE_TO_VIDEO等）
    provider: str                      # 供应商（DUOMI/RUNNINGHUB/VIDU）
    driver_name: str                  # 业务驱动名称
    implementation: str               # 实现驱动类名
    computing_power: Union[int, Dict] # 算力消耗 {5: 6, 10: 12} 表示5秒6算力，10秒12算力
    supported_ratios: List[str]       # 支持的比例
    supported_durations: List[int]    # 支持的时长
    supported_image_modes: List[str]   # 支持的图片模式
```

### 9.2 关键配置表

| ID | Key | 名称 | 分类 | 算力 |
|----|-----|------|------|------|
| 3 | sora2_image_to_video | Sora2图生视频 | 图生视频 | 18 |
| 10 | ltx2_image_to_video | LTX2.0图生视频 | 图生视频 | 6 |
| 11 | wan22_image_to_video | Wan2.2图生视频 | 图生视频 | {5:6, 10:12} |
| 12 | kling_image_to_video | 可灵v2.5-turbo | 图生视频 | {5:38, 10:70} |
| 14 | vidu_image_to_video | Vidu-q2-pro-fast | 图生视频 | {5:16, 8:22} |
| 16 | seedream-5.0 | Seedream 5.0 | 文生图 | 6 |

---

## 十、MCP工具定义

### 10.1 完整工具清单

**文件**: `script_writer_core/mcp_tool.py`

```python
MCP_TOOLS = [
    # 角色管理（4个）
    {"name": "create_character_json", ...},
    {"name": "read_character_json", ...},
    {"name": "update_character_json", ...},
    {"name": "list_character_jsons", ...},

    # 剧本管理（4个）
    {"name": "create_script_json", ...},
    {"name": "read_script_json", ...},
    {"name": "update_script_json", ...},
    {"name": "list_script_jsons", ...},

    # 场景管理（4个）
    {"name": "create_location_json", ...},
    {"name": "read_location_json", ...},
    {"name": "update_location_json", ...},
    {"name": "list_location_jsons", ...},

    # 道具管理（4个）
    {"name": "create_prop_json", ...},
    {"name": "read_prop_json", ...},
    {"name": "update_prop_json", ...},
    {"name": "list_prop_jsons", ...},

    # 世界管理（2个）
    {"name": "read_world", ...},
    {"name": "update_world", ...},

    # 审核（2个）
    {"name": "get_script_problem", ...},
    {"name": "set_script_problem", ...},

    # 技能（1个）
    {"name": "skill", ...},

    # 生图（5个）
    {"name": "generate_text_to_image", ...},
    {"name": "generate_4grid_character_images", ...},
    {"name": "generate_4grid_location_images", ...},
    {"name": "generate_4grid_prop_images", ...},
    {"name": "get_task_status", ...},

    # 长文本（1个）
    {"name": "get_long_user_input", ...},
]
```

### 10.2 工具执行器

```python
def execute_tool(self, tool_name, tool_args, user_id, world_id, auth_token):
    # 1. 检查工具是否存在
    if tool_name not in self.tool_map:
        return {"error": f"未知工具: {tool_name}"}

    # 2. 区分MCP工具和普通工具
    mcp_tool_names = ["read_world", "update_world", ...]

    if tool_name in mcp_tool_names:
        # MCP工具：前三个参数是user_id, world_id, auth_token
        result = self.tool_map[tool_name](user_id, world_id, auth_token, **tool_args)
    else:
        result = self.tool_map[tool_name](**tool_args)

    return result
```

---

## 十一、对话摘要系统

### 11.1 摘要Prompt

```python
summary_prompt = """你是一个专业的对话精简助手。

**精简原则**：
1. 保留关键决策和结论
2. 保留重要的文件操作（创建了什么、修改了什么）
3. 保留失败信息和错误原因
4. 删除冗余的问答和重复内容
5. 删除系统提示和工具调用的技术细节

**输出格式**：
{
    "task": "任务简述",
    "expert": "执行的专家名称",
    "status": "success/failed/partial",
    "key_outputs": ["输出1", "输出2"],
    "decisions": ["决策1", "决策2"],
    "issues": ["问题1"],
    "summary": "一句话总结"
}
"""
```

### 11.2 summary_only模式

```python
def get_context_for_ai(self, user_id, world_id, summary_only=False):
    context = "# 项目文件资源\n\n"

    for char in characters:
        if summary_only:
            # 只返回前200字符作为摘要
            context += f"```\n{char_data[:200]}\n... (内容已截断)\n```\n\n"
        else:
            context += f"```\n{char_data}\n```\n\n"

    return context
```

---

## 十二、任务生命周期管理

### 12.1 长文本处理

```python
def process_long_input(user_id, world_id, user_message):
    # 判断长度
    if len(user_message) <= 5000:
        return {"processed_message": user_message, "file_reference": None}

    # 截取：前4000字 + 后1000字
    prefix = user_message[:4000]
    suffix = user_message[-1000:]

    # 保存完整内容到文件
    filename = f"{timestamp}.txt"
    file_path = f"files/{user_id}/{world_id}/user_long_input/{filename}"

    # 构造处理后的消息
    processed_message = f"""【系统提示】用户输入的内容超过5000字，已自动保存完整内容。
    - 文件名：{filename}
    - 原始长度：{len(user_message)} 字
    - 如需读取完整内容，请调用工具：get_long_user_input(name="{filename}")
    """
```

### 12.2 后台线程启动

```python
def start_task(self, task, pm_agent, session_data, on_complete=None):
    def run_task():
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

            # 发送状态消息
            task.message_queue.put({
                "type": "status",
                "status": "running",
                "message": "任务开始执行"
            })

            # 调用PM Agent执行
            result = pm_agent.execute(task, session_data)

            task.status = TaskStatus.COMPLETED
            task.result = result

            task.message_queue.put({"type": "done", "result": result})

            if on_complete:
                on_complete(result)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.message_queue.put({"type": "error", "error": str(e)})

    # 启动后台线程
    thread = threading.Thread(target=run_task, daemon=True)
    self.task_threads[task.task_id] = thread
    thread.start()
```

---

## 十三、错误处理架构

### 13.1 错误分类

| error_type | 含义 | 处理方式 |
|------------|------|----------|
| USER | 用户可见错误 | 返回给用户，不重试 |
| SYSTEM | 系统级错误 | Sentry报警，不重试 |

### 13.2 重试策略

```python
# 仅网络异常允许重试
try:
    result = self._request(...)
except (ConnectionError, TimeoutError) as e:
    return {"success": False, "retry": True}

# 格式错误/系统异常 → 报警，不重试
```

### 13.3 Sentry报警类型

```python
INVALID_RESPONSE_FORMAT  # API响应格式不符合预期
UNEXPECTED_EXCEPTION    # 未预期的代码异常
MISSING_TASK_ID         # 响应中缺少任务ID
```

---

## 十四、借鉴清单（漫舟优化方向）

### 14.1 多智能体架构

| ZJT做法 | 漫舟可借鉴 | 优先级 |
|---------|-----------|--------|
| PM-Agent协调器模式 | 引入任务协调层，避免单Agent全权负责 | 高 |
| 双层熔断机制 | 连续3次+累计7次熔断 | 高 |
| 渐进式上下文披露 | PM用摘要，Expert用完整 | 高 |
| 工具白名单 | 每个Agent配置allowed_tools | 中 |
| Human-in-loop | 关键节点人工验证 | 中 |

### 14.2 剧本解析

| ZJT做法 | 漫舟可借鉴 | 优先级 |
|---------|-----------|--------|
| 【【角色名】】占位符 | 解耦生成与角色库 | 高 |
| 数据库关联 | 场景/道具ID关联 | 高 |
| 分镜组贪心重组 | 确保时长约束 | 高 |
| JSON截断修复 | 增强鲁棒性 | 中 |
| 解说剧模式 | 多剧本风格支持 | 中 |

### 14.3 视频驱动

| ZJT做法 | 漫舟可借鉴 | 优先级 |
|---------|-----------|--------|
| 三层解耦工厂模式 | 多模型配置化切换 | 高 |
| 算力消耗建模 | 支持时长分档算力 | 高 |
| 供应商抽象 | 支持多API供应商 | 中 |

### 14.4 工程实践

| ZJT做法 | 漫舟可借鉴 | 优先级 |
|---------|-----------|--------|
| SSE心跳机制 | 30秒超时保活 | 高 |
| 会话历史持久化 | 问题复盘 | 中 |
| Gemini端点探测 | 支持代理/官方切换 | 中 |
| Token使用统计 | 精确计费上报 | 低 |
| 每日日志文件 | 全链路记录 | 低 |

---

## 十五、关键文件索引

| 模块 | 文件路径 |
|------|----------|
| PM Agent | `script_writer_core/agents/pm_agent.py` |
| Expert Agent | `script_writer_core/agents/expert_agent.py` |
| Base Agent | `script_writer_core/agents/base_agent.py` |
| Task Manager | `script_writer_core/agents/task_manager.py` |
| Tool Executor | `script_writer_core/agents/tool_executor.py` |
| Summarizer | `script_writer_core/agents/summarizer.py` |
| MCP Tools | `script_writer_core/mcp_tool.py` |
| File Manager | `script_writer_core/file_manager.py` |
| Skill Loader | `script_writer_core/skill_loader.py` |
| Script Parser | `llm/script_parser.py` |
| Gemini Client | `llm/gemini_client.py` |
| API Routes | `api/script_writer.py` |
| Video Drivers | `task/visual_drivers/*.py` |
| Driver Factory | `task/visual_drivers/driver_factory.py` |
| Base Driver | `task/visual_drivers/base_video_driver.py` |
| Config | `config/unified_config.py` |
| Constants | `config/constant.py` |
| Workflow Editor | `web/video_workflow.html` |
| Script Writer UI | `web/script_writer.html` |
| Workflow JS | `web/js/workflow.js` |
| Nodes JS | `web/js/nodes.js` |
| Canvas JS | `web/js/canvas.js` |
| World Model | `model/world.py` |
| Character Model | `model/character.py` |
| Location Model | `model/location.py` |
| Script Model | `model/script.py` |
