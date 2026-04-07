# task_state.py 集成指南

> 为 huage888 Pipeline 添加统一任务状态追踪

---

## 模块概述

`scripts/task_state.py` 提供统一的任务状态管理，参考 Toonflow `t_video.state` 模式：

| 状态 | 值 | 说明 |
|------|-----|------|
| `PENDING` | 0 | 待执行 |
| `RUNNING` | 1 | 执行中 |
| `SUCCESS` | 2 | 成功完成 |
| `FAILED` | -1 | 执行失败 |
| `RETRYING` | 3 | 重试中 |

---

## 快速开始

### 基本用法

```python
from task_state import TaskManager, TaskState, TaskType

manager = TaskManager()

# 1. 创建任务
task_id = manager.create(
    task_type=TaskType.QWEN,
    name="导演讲戏-阶段一",
    params={"agent": "director", "user": "..."},
)

# 2. 执行前更新为 RUNNING
manager.update(task_id, TaskState.RUNNING)

# 3. 执行业务逻辑
try:
    result = call_api(...)
    manager.update(task_id, TaskState.SUCCESS, result={"output": result})
except Exception as e:
    manager.update(task_id, TaskState.FAILED, error=str(e))

# 4. 查询状态
record = manager.get(task_id)
print(f"状态: {record.state.name}")  # SUCCESS / FAILED
```

### 使用 `run_with_tracking`（推荐）

自动处理 RUNNING → SUCCESS/FAILED 状态转换和重试：

```python
from task_state import run_with_tracking

def director_call(params):
    """实际调用 qwen-max"""
    from qwen_pipeline import call_qwen
    return call_qwen(
        system=params["system"],
        user=params["user"],
    )

state, result = run_with_tracking(
    manager=TaskManager(),
    task_type=TaskType.QWEN,
    name="导演讲戏",
    params={"system": "...", "user": "..."},
    execute_fn=director_call,
    max_retries=3,
)

print(f"最终状态: {state.name}")  # SUCCESS / FAILED
```

---

## 集成到 qwen_pipeline.py

在 `config/qwen_pipeline.py` 中添加状态追踪：

```python
# 1. 导入
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from task_state import TaskManager, TaskState, TaskType, run_with_tracking

# 2. 在 main() 中创建任务
def main():
    args = parse_args()

    # 创建任务记录
    manager = TaskManager()
    task_id = manager.create(
        task_type=TaskType.QWEN,
        name=f"qwen-{args.agent or 'adhoc'}",
        params={
            "agent": args.agent,
            "model": args.model,
            "temperature": args.temperature,
        },
    )

    # 3. 定义执行函数
    def execute(params):
        # 从 params 构建 prompt...
        return call_qwen(system, user, model, temperature, top_p, max_tokens)

    # 4. 使用 run_with_tracking
    state, content = run_with_tracking(
        manager=manager,
        task_type=TaskType.QWEN,
        name=f"qwen-{args.agent or 'adhoc'}",
        params={"system": system, "user": user, "model": args.model},
        execute_fn=lambda p: call_qwen(
            system=p["system"],
            user=p["user"],
            model=p["model"],
            # 从 agent defaults 获取
            temperature=AGENT_DEFAULTS.get(args.agent, {}).get("temperature"),
            top_p=AGENT_DEFAULTS.get(args.agent, {}).get("top_p"),
            max_tokens=AGENT_DEFAULTS.get(args.agent, {}).get("max_tokens"),
        ),
    )

    # 5. 处理结果
    if state == TaskState.SUCCESS:
        if args.output:
            Path(args.output).write_text(content, encoding="utf-8")
            print(f"✅ 已写入：{args.output}", file=sys.stderr)
        else:
            print(content)
    else:
        print(f"❌ 任务失败: {content}", file=sys.stderr)
        sys.exit(1)
```

---

## 集成到 video_pipeline.py

在 `scripts/video_pipeline.py` 的 `generate_video()` 中添加状态追踪：

```python
# 1. 导入
sys.path.insert(0, str(SCRIPT_DIR))
from task_state import TaskManager, TaskState, TaskType

# 2. 在文件顶部创建 manager（延迟初始化）
_manager: TaskManager | None = None

def get_manager():
    global _manager
    if _manager is None:
        _manager = TaskManager()
    return _manager

# 3. 在 generate_video() 中使用
def generate_video(
    provider_name: str,
    prompt: str,
    output_path: Path,
    model: str = "",
    # ... 其他参数
) -> VideoResult:
    manager = get_manager()

    # 创建任务
    task_id = manager.create(
        task_type=TaskType.DOUBAO_VIDEO if provider_name == "doubao" else TaskType.KLING_VIDEO,
        name=f"{provider_name}-video-{output_path.stem}",
        params={
            "provider": provider_name,
            "prompt": prompt[:100],
            "model": model,
            "duration": duration,
            "output": str(output_path),
        },
    )

    # 更新为运行中
    manager.update(task_id, TaskState.RUNNING)

    try:
        result = adapter.generate_video(...)
        manager.update(
            task_id,
            TaskState.SUCCESS,
            result={
                "video_url": result.video_url,
                "task_id": result.task_id,
                "elapsed_seconds": result.elapsed_seconds,
            },
            external_id=result.task_id,
        )
        return result
    except Exception as e:
        manager.update(task_id, TaskState.FAILED, error=str(e))
        raise
```

---

## 集成到 doubao_pipeline.py

```python
# 在 create_and_wait_video() 中

def create_and_wait_video(
    prompt: str,
    output_path: Path,
    # ... 其他参数
) -> None:
    # 创建任务
    task_id = manager.create(
        task_type=TaskType.DOUBAO_VIDEO,
        name=f"doubao-video-{output_path.stem}",
        params={"prompt": prompt[:100], "duration": duration},
    )
    manager.update(task_id, TaskState.RUNNING)

    try:
        task_id_api = create_video_task(prompt, img1, img2, duration, ...)
        manager.update(task_id, TaskState.RUNNING, external_id=task_id_api)

        poll_video_task(task_id_api, output_path, model)
        manager.update(task_id, TaskState.SUCCESS, result={"output": str(output_path)})
    except Exception as e:
        manager.update(task_id, TaskState.FAILED, error=str(e))
        raise
```

---

## 持久化位置

```
.huage888/
└── tasks/
    ├── tasks_index.json    # 任务索引
    └── {task_id}.json     # 每个任务一条记录
```

**示例任务文件**：

```json
{
  "id": "553a4a51",
  "type": "qwen",
  "name": "导演讲戏-测试",
  "state": 2,
  "created_at": "2026-04-07T12:35:43.081561",
  "started_at": "2026-04-07T12:35:43.082309",
  "finished_at": "2026-04-07T12:35:43.082647",
  "params": {
    "agent": "director",
    "user": "请分析剧本：..."
  },
  "result": {
    "output": "outputs/01-director-analysis.md"
  },
  "error": null,
  "retry_count": 0,
  "max_retries": 3,
  "external_id": null
}
```

---

## CLI 命令

```bash
# 查看汇总统计
python3 scripts/task_state.py summary

# 列出所有任务
python3 scripts/task_state.py list

# 按类型过滤
python3 scripts/task_state.py list --type qwen

# 按状态过滤（2=SUCCESS, -1=FAILED）
python3 scripts/task_state.py list --state 2

# 查看任务详情
python3 scripts/task_state.py get 553a4a51
```

---

## 与现有 Pipeline 的兼容性

| Pipeline | 集成方式 | 侵入性 |
|---------|---------|--------|
| qwen_pipeline.py | `run_with_tracking` 包装 | 低 |
| video_pipeline.py | `generate_video()` 增加 task_id 参数 | 中 |
| doubao_pipeline.py | `create_and_wait_video()` 增加 task_id 参数 | 中 |

**向后兼容**：
- 不传 task_id 参数时，使用旧逻辑（无状态追踪）
- 传 task_id 参数时，开启状态追踪
- 不影响现有 `--test` / `--list` 等 CLI 功能
