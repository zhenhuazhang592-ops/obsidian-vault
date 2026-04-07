# event_emitter.py 集成指南

> 为 huage888 Pipeline 添加实时进度反馈

---

## 快速参考

### 事件类型速查

| 事件 | 触发时机 | Toonflow 对应 |
|------|---------|--------------|
| `task_start` | 任务开始 | Agent 创建 |
| `task_stream` | 流式文本 | `data` / `subAgentStream` |
| `task_progress` | 进度更新 | `shotImageGenerateProgress` |
| `task_end` | 任务完成 | `shotsUpdated` (success) |
| `task_error` | 任务失败 | `shotImageGenerateError` |
| `tool_call` | 工具调用 | `toolCall` |
| `tool_result` | 工具返回 | `toolCall` response |
| `data_refresh` | 数据刷新 | `refresh` |

---

## 最简集成（推荐）

使用 `TaskContext` 自动管理生命周期，只需 4 行代码：

```python
from event_emitter import default_emitter, logging_emitter

# 方式 A：仅控制台（调试用）
emitter = default_emitter

# 方式 B：控制台 + 文件（生产用）
emitter = logging_emitter

with emitter.task("导演讲戏") as ctx:
    ctx.set_progress("pending", "读取剧本...", 0.1)
    # ... 执行业务逻辑 ...
    ctx.set_progress("generating", "调用 qwen-max...", 0.5)
    result = call_api(...)
    ctx.set_progress("complete", "完成", 1.0)
    ctx.set_result(result, preview=f"{len(result)}字")
# 自动发射 task_end / task_error（无需手动处理）
```

---

## 集成到 qwen_pipeline.py

```python
# config/qwen_pipeline.py

import sys
from pathlib import Path

# 添加 scripts 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from event_emitter import logging_emitter

# 在 main() 中替换原来的 call_qwen 调用

def main():
    args = parse_args()
    # ... prompt 构建 ...

    with logging_emitter.task(f"qwen-{args.agent or 'adhoc'}") as ctx:
        ctx.set_progress("generating", "调用 qwen-max...", 0.3)

        try:
            content = call_qwen(
                system=system,
                user=user,
                model=args.model,
                temperature=args.temperature,
                top_p=args.top_p,
                max_tokens=args.max_tokens,
            )
            ctx.set_progress("complete", "生成完成", 1.0)
            ctx.set_result(content, preview=f"{len(content)}字")
        except Exception as e:
            ctx.fail(str(e))
            sys.exit(1)

    # ... 输出 ...
```

---

## 集成到 video_pipeline.py

```python
# scripts/video_pipeline.py

from event_emitter import logging_emitter

def generate_video(..., emitter=None):
    emitter = emitter or logging_emitter

    with emitter.task(f"{provider_name}-video-{output_path.stem}") as ctx:
        ctx.set_progress("pending", "初始化适配器...", 0.1)

        registry = get_registry()
        adapter = registry.get(provider_name)
        ctx.set_progress("generating", "创建视频任务...", 0.2)
        ctx.set_progress("polling", "等待生成...", 0.6)
        ctx.set_progress("downloading", "下载文件...", 0.9)

        result = adapter.generate_video(...)
        ctx.set_result(result, preview=result.video_url[:60])
        return result
```

---

## 集成到 doubao_pipeline.py

```python
# config/doubao_pipeline.py

from event_emitter import logging_emitter

def create_and_wait_video(..., emitter=None):
    emitter = emitter or logging_emitter

    with emitter.task(f"doubao-video-{output_path.stem}") as ctx:
        ctx.set_progress("creating", "创建任务...", 0.1)
        task_id = create_video_task(prompt, img1, img2, ...)

        ctx.set_progress("polling", "等待生成...", 0.3)
        # 轮询中定期更新进度
        while True:
            status = poll_status(task_id)
            if status == "succeeded":
                ctx.set_progress("downloading", "下载视频...", 0.9)
                download_file(video_url, output_path)
                ctx.set_result(str(output_path))
                return
            elif status == "failed":
                ctx.fail(f"API 返回失败：{error}")
                sys.exit(1)
            ctx.set_progress("polling", f"状态：{status}", 0.4)
            time.sleep(POLL_INTERVAL)
```

---

## 自定义 Sink

### 仅文件记录（静默模式）

```python
from event_emitter import EventEmitter, JSONLSink

emitter = EventEmitter(sinks=[
    JSONLSink(".huage888/events.jsonl")
])
```

### WebSocket 推送（实时 Web UI）

```python
from event_emitter import EventEmitter, WebSocketSink

emitter = EventEmitter(sinks=[
    ConsoleSink(color=True),
    WebSocketSink("ws://localhost:8080/events"),
])
```

### 自定义格式化

```python
from event_emitter import EventEmitter, Sink, Event

class CustomSink(Sink):
    def write(self, event: Event):
        # 完全自定义输出格式
        if event.type == "task_end":
            print(f"🎬 {event.data['name']}: {event.data['elapsed']:.1f}s")

    def flush(self):
        pass

emitter = EventEmitter(sinks=[CustomSink()])
```

---

## 监听器（高级用法）

```python
from event_emitter import EventEmitter, EventType

emitter = EventEmitter()

# 监听所有 task_error 事件
def on_error(event):
    print(f"告警：{event.data['name']} 失败")
    # 发送通知 / 记录监控指标

emitter.on(EventType.TASK_ERROR, on_error)

# 监听所有事件（通配符）
emitter.on("*", lambda e: print(f"事件: {e.type}"))
```

---

## 与 task_state.py 联动

```python
from event_emitter import logging_emitter
from task_state import TaskManager, TaskState, TaskType

manager = TaskManager()
emitter = logging_emitter

def tracked_call(params):
    task_id = manager.create(TaskType.QWEN, params["name"], params)
    emitter.emit_task_start(params["name"])

    try:
        result = call_qwen(...)
        manager.update(task_id, TaskState.SUCCESS)
        emitter.emit_task_end(task_id, params["name"], result=result)
        return result
    except Exception as e:
        manager.update(task_id, TaskState.FAILED, error=str(e))
        emitter.emit_task_error(task_id, params["name"], error=str(e))
        raise
```

---

## 持久化日志分析

```python
# 分析事件日志
from event_emitter import JSONLSink

sink = JSONLSink(".huage888/events.jsonl")

# 所有任务
all_events = sink.read_events()
print(f"总事件数: {len(all_events)}")

# 按任务过滤
task_events = sink.read_events(task_id="t001")
print(f"任务 t001 事件数: {len(task_events)}")

# 统计
from collections import Counter
type_counts = Counter(e.type for e in all_events)
print(f"事件类型分布: {type_counts}")
```

---

## CLI 工具

```bash
# 实时查看事件流
tail -f .huage888/events.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    e = json.loads(line)
    print(f\"[{e['type']}] {e.get('task_id', '')} | {e['data'].get('name', '')}\")
"

# 过滤特定事件
grep '"task_error"' .huage888/events.jsonl

# 统计任务成功率
python3 -c "
import json
events = [json.loads(l) for l in open('.huage888/events.jsonl')]
from collections import defaultdict
tasks = defaultdict(dict)
for e in events:
    if e['type'] in ('task_start', 'task_end', 'task_error'):
        tasks[e['task_id']][e['type']] = e
success = sum(1 for t in tasks.values() if 'task_end' in t)
failed = sum(1 for t in tasks.values() if 'task_error' in t)
print(f'成功: {success}, 失败: {failed}, 成功率: {success/(success+failed)*100:.1f}%')
"
```

---

## 输出效果示例

```
[START] 导演讲戏 | 任务已启动
[PROGRESS] 导演讲戏 | [████████░░░░░░░░░░░░]  40.0% | generating 调用 qwen-max...
[STREAM] 导演讲戏 | # 第一幕
镜头1：建立镜头，西湖断桥...
[TOOL] 导演讲戏 | 🔧 调用工具：getAssets
[TOOL] 导演讲戏 | ✅ 工具返回：getAssets
[PROGRESS] 导演讲戏 | [██████████████░░░░░░]  70.0% | generating 生成分镜...
[END] 导演讲戏 | ✅ 完成（12.3s） | 442行 | 25镜头
```
