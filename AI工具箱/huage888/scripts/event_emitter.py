#!/usr/bin/env python3
"""
event_emitter.py — huage888 事件推送系统

参考 Toonflow EventEmitter 模式，为 Pipeline 提供实时进度反馈。

设计原则：
- 事件驱动：所有 Pipeline 执行时发出标准事件
- 多目标输出：控制台（带颜色）/ 文件（JSONL）/ WebSocket（实时推送）
- 零侵入：作为 Pipeline 的副作用存在，不改变核心逻辑
- CLI 友好：grep 友好格式，方便在 Claude Code 中查看

事件类型（参考 Toonflow）：

  生命周期：task_start → task_stream → task_end
  进度类：  task_progress（可细分为 pending/generating/splitting/saving）
  工具类：  tool_call / tool_result
  错误类：  task_error
  自定义：  task_custom（任意扩展）

用法：

  # 1. 基础：控制台输出
  emitter = EventEmitter()
  emitter.on("task_start", lambda e: print(f"🚀 {e['name']}"))
  emitter.on("task_progress", format_progress_bar)
  emitter.on("task_stream", lambda e: print(e["text"], end="", flush=True))
  emitter.on("task_end", lambda e: print(f"\n✅ {e['name']} 完成（{e['elapsed']:.1f}s）"))
  emitter.on("task_error", lambda e: print(f"\n❌ {e['name']} 失败：{e['error']}", file=sys.stderr))

  # 2. 绑定到 Pipeline
  from qwen_pipeline import call_qwen
  def tracked_call_qwen(system, user, **kwargs):
      task_id = emitter.emit_task_start("qwen-director", {"system": "..."})
      try:
          result = call_qwen(system, user, **kwargs)
          emitter.emit_task_end(task_id, result=result)
          return result
      except Exception as e:
          emitter.emit_task_error(task_id, error=str(e))
          raise

  # 3. 文件记录（JSONL，每行一个事件）
  emitter = EventEmitter(sinks=[JSONLSink(".huage888/events.jsonl")])

  # 4. WebSocket 推送（供前端实时展示）
  emitter = EventEmitter(sinks=[WebSocketSink("ws://localhost:8080")])

  # 5. 多 Sink 同时输出
  emitter = EventEmitter(sinks=[
      ConsoleSink(color=True, progress_bar=True),
      JSONLSink(".huage888/events.jsonl"),
  ])
"""

import json
import sys
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
from threading import Lock


# ─────────────────────────────────────────────────────────────────────────────
# 事件类型常量
# ─────────────────────────────────────────────────────────────────────────────

class EventType:
    """事件类型枚举（与 Toonflow 保持语义一致）"""

    # 生命周期
    TASK_START = "task_start"          # 任务开始
    TASK_STREAM = "task_stream"         # 流式输出（文本片段）
    TASK_END = "task_end"              # 任务完成（成功）
    TASK_ERROR = "task_error"          # 任务失败

    # 进度（可细分子状态）
    TASK_PROGRESS = "task_progress"     # 进度更新

    # 工具调用（Toonflow toolCall）
    TOOL_CALL = "tool_call"           # 开始调用工具
    TOOL_RESULT = "tool_result"       # 工具返回结果

    # 数据刷新（Toonflow refresh）
    DATA_REFRESH = "data_refresh"     # 数据已更新

    # Sub-Agent 嵌套（Toonflow transfer/subAgentStream/subAgentEnd）
    TRANSFER = "transfer"             # 父→子 Agent 切换
    SUB_AGENT_START = "sub_agent_start"   # 子 Agent 启动
    SUB_AGENT_STREAM = "sub_agent_stream" # 子 Agent 流式输出
    SUB_AGENT_END = "sub_agent_end"  # 子 Agent 结束

    # 自定义
    CUSTOM = "task_custom"            # 自定义事件


# ─────────────────────────────────────────────────────────────────────────────
# 事件数据模型
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Event:
    """
    标准事件对象

    字段说明：
    - id: 事件唯一 ID（UUID）
    - type: 事件类型（EventType 常量）
    - task_id: 关联任务 ID（可选，同一任务的多个事件共享）
    - timestamp: 事件时间（ISO 格式，毫秒精度）
    - data: 事件数据（JSON 可序列化）
    """
    id: str
    type: str
    task_id: Optional[str] = None
    timestamp: str = ""
    data: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat(timespec="milliseconds")

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────────────────
# Sink 接口（事件输出目标）
# ─────────────────────────────────────────────────────────────────────────────

class Sink(ABC):
    """事件输出目标抽象基类"""

    @abstractmethod
    def write(self, event: Event) -> None:
        """写入单个事件"""
        ...

    @abstractmethod
    def flush(self) -> None:
        """刷新缓冲区"""
        ...

    def close(self) -> None:
        """关闭 Sink（可选实现）"""
        pass


class ConsoleSink(Sink):
    """
    控制台输出 Sink（Toonflow 的 stream / data / toolCall 事件）

    输出格式（grep 友好）：
      [task_start]  导演讲戏-阶段一 | 任务已启动
      [task_progress] 导演讲戏 | ████████░░ 80% | 正在生成第三段...
      [task_stream] 导演讲戏 | # 第一幕 #\n镜头1：...
      [task_end]    导演讲戏 | ✅ 完成（12.3s）
      [task_error]  导演讲戏 | ❌ 失败：429 Rate Limit
    """

    def __init__(
        self,
        color: bool = True,
        progress_bar: bool = True,
        stream_mode: str = "append",  # "append" | "line"
        stderr_for_error: bool = True,
    ):
        self.color = color
        self.progress_bar = progress_bar
        self.stream_mode = stream_mode
        self.stderr_for_error = stderr_for_error
        self._lock = Lock()
        self._progress_cache: dict[str, str] = {}  # task_id → 上次打印的进度行
        self._ansi_support = self._check_ansi_support()

    def _check_ansi_support(self) -> bool:
        """检查终端是否支持 ANSI 颜色"""
        if not sys.stdout.isatty():
            return False
        return True

    def _color(self, text: str, code: str) -> str:
        """添加 ANSI 颜色"""
        if not self.color or not self._ansi_support:
            return text
        return f"\033[{code}m{text}\033[0m"

    def _format_progress_bar(self, progress: float, width: int = 20) -> str:
        """格式化进度条"""
        filled = int(width * progress)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {progress * 100:5.1f}%"

    def write(self, event: Event) -> None:
        with self._lock:
            task_name = event.data.get("name", event.task_id or "")
            etype = event.type
            data = event.data

            if etype == EventType.TASK_START:
                msg = data.get("message", "任务已启动")
                tag = self._color("START", "36")  # 青色
                line = f"[{tag}] {task_name} | {msg}"
                print(line, file=sys.stderr)

            elif etype == EventType.TASK_STREAM:
                text = data.get("text", "")
                tag = self._color("STREAM", "33")  # 黄色
                if self.stream_mode == "append":
                    # 同一行追加（覆盖式）
                    line = f"\r[{tag}] {task_name} | {text[:80]}"
                    print(line, end="", file=sys.stderr, flush=True)
                else:
                    # 逐行输出
                    for line in text.split("\n"):
                        if line.strip():
                            print(f"[{tag}] {task_name} | {line}", file=sys.stderr)

            elif etype == EventType.TASK_PROGRESS:
                status = data.get("status", "")
                message = data.get("message", "")
                progress = data.get("progress", 0.0)

                tag = self._color("PROGRESS", "35")  # 洋红
                if self.progress_bar and 0 <= progress <= 1:
                    bar = self._format_progress_bar(progress)
                    line = f"[{tag}] {task_name} | {bar} | {status} {message}"
                else:
                    line = f"[{tag}] {task_name} | {status} | {message}"

                # 覆盖式打印（同任务 ID）
                cache_key = event.task_id or task_name
                prev = self._progress_cache.get(cache_key, "")
                if prev:
                    # 清除上一行
                    print("\r" + " " * len(prev), end="", file=sys.stderr, flush=True)
                print(f"\r{line}", end="", file=sys.stderr, flush=True)
                self._progress_cache[cache_key] = line

            elif etype == EventType.TASK_END:
                elapsed = data.get("elapsed", 0)
                tag = self._color("END", "32")  # 绿色
                # 清除进度条
                cache_key = event.task_id or task_name
                if cache_key in self._progress_cache:
                    print("\r" + " " * len(self._progress_cache[cache_key]),
                          end="", file=sys.stderr, flush=True)
                    del self._progress_cache[cache_key]
                result_preview = data.get("result_preview", "")
                if result_preview:
                    result_preview = f" | {result_preview[:40]}"
                print(f"\r[{tag}] {task_name} | ✅ 完成（{elapsed:.1f}s）{result_preview}",
                      file=sys.stderr)

            elif etype == EventType.TASK_ERROR:
                error = data.get("error", "未知错误")
                tag = self._color("ERROR", "31")  # 红色
                # 清除进度条
                cache_key = event.task_id or task_name
                if cache_key in self._progress_cache:
                    print("\r" + " " * len(self._progress_cache[cache_key]),
                          end="", file=sys.stderr, flush=True)
                    del self._progress_cache[cache_key]
                stream = sys.stderr if self.stderr_for_error else sys.stdout
                print(f"\n[{tag}] {task_name} | ❌ 失败：{error}", file=stream)

            elif etype == EventType.TOOL_CALL:
                tool_name = data.get("name", "")
                tag = self._color("TOOL", "34")  # 蓝色
                print(f"[{tag}] {task_name} | 🔧 调用工具：{tool_name}", file=sys.stderr)

            elif etype == EventType.TOOL_RESULT:
                success = data.get("success", True)
                tool_name = data.get("name", "")
                tag = self._color("TOOL", "34")  # 蓝色
                icon = "✅" if success else "❌"
                print(f"[{tag}] {task_name} | {icon} 工具返回：{tool_name}", file=sys.stderr)

            elif etype == EventType.DATA_REFRESH:
                refresh_type = data.get("refresh_type", "")
                tag = self._color("REFRESH", "36")  # 青色
                print(f"[{tag}] {task_name} | 🔄 数据刷新：{refresh_type}", file=sys.stderr)

            elif etype == EventType.CUSTOM:
                # 完全自定义输出
                message = data.get("message", json.dumps(data, ensure_ascii=False))
                tag = self._color("CUSTOM", "90")  # 灰色
                print(f"[{tag}] {task_name} | {message}", file=sys.stderr)

    def flush(self) -> None:
        sys.stderr.flush()


class JSONLSink(Sink):
    """
    JSONL 文件 Sink（每行一个 JSON 事件）

    用途：
    - 事件日志持久化
    - 事后分析 / 调试
    - WebSocket 重放
    """

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def write(self, event: Event) -> None:
        with self._lock:
            with self.file_path.open("a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")

    def flush(self) -> None:
        pass  # 立即写入，无需 flush

    def read_events(self, task_id: str | None = None) -> list[Event]:
        """读取事件日志（可按 task_id 过滤）"""
        events = []
        if not self.file_path.exists():
            return events
        with self.file_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    if task_id and d.get("task_id") != task_id:
                        continue
                    events.append(Event(**d))
                except Exception:
                    continue
        return events


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket Sink（可选，需要 websockets 库）
# ─────────────────────────────────────────────────────────────────────────────

class WebSocketSink(Sink):
    """
    WebSocket Sink — 实时推送到前端

    用途：
    - 供 Claude Code Web UI 实时展示进度
    - 与前端应用集成

    注意：需要 websockets 库（pip install websockets）
    """

    def __init__(self, url: str, reconnect: bool = True, reconnect_delay: float = 3.0):
        self.url = url
        self.reconnect = reconnect
        self.reconnect_delay = reconnect_delay
        self._ws = None
        self._lock = Lock()
        self._connect()

    def _connect(self) -> None:
        try:
            import websockets
            import asyncio
            # 延迟导入，避免无 websockets 库时报错
            self._websockets = websockets
            self._connected = True
        except ImportError:
            print(
                "⚠️  WebSocket Sink 需要 websockets 库：pip install websockets",
                file=sys.stderr
            )
            self._connected = False

    def write(self, event: Event) -> None:
        if not self._connected:
            return
        # 异步发送，非阻塞
        try:
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                self._send_async(event.to_json())
            )
        except Exception:
            pass  # 非阻塞，发送失败不阻断主流程

    async def _send_async(self, message: str) -> None:
        try:
            async with self._websockets.connect(self.url) as ws:
                await ws.send(message)
        except Exception:
            pass

    def flush(self) -> None:
        pass

    def close(self) -> None:
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# EventEmitter 核心
# ─────────────────────────────────────────────────────────────────────────────

class EventEmitter:
    """
    事件发射器（参考 Toonflow EventEmitter 模式）

    核心功能：
    - 注册监听器（按事件类型过滤）
    - 发射事件到所有 Sink
    - 提供便捷方法自动构造标准事件

    与 Toonflow 的对应关系：
      Toonflow              →  huage888 EventEmitter
      agent.emitter.emit()  →  emitter.emit()
      ws.send({type,data})  →  sink.write(event)
    """

    # 全局默认 Sink（控制台）
    _default_sinks: list[Sink] | None = None

    def __init__(self, sinks: list[Sink] | None = None):
        """
        Args:
            sinks: 输出目标列表，None 时使用默认 ConsoleSink
        """
        self._sinks = sinks if sinks is not None else self._get_default_sinks()
        self._listeners: dict[str, list[Callable[[Event], None]]] = {}
        self._lock = Lock()
        self._task_counter = 0

    @classmethod
    def _get_default_sinks(cls) -> list[Sink]:
        if cls._default_sinks is None:
            cls._default_sinks = [ConsoleSink(color=True, progress_bar=True)]
        return cls._default_sinks

    @classmethod
    def set_default_sinks(cls, sinks: list[Sink]) -> None:
        """设置全局默认 Sink（影响后续所有 EventEmitter 实例）"""
        cls._default_sinks = sinks

    # ─────────────────────────────────────────────────────────────────
    # 监听器管理
    # ─────────────────────────────────────────────────────────────────

    def on(self, event_type: str, callback: Callable[[Event], None]) -> "EventEmitter":
        """
        注册事件监听器

        Args:
            event_type: 事件类型（EventType 常量或 "*" 表示所有事件）
            callback: 回调函数

        Returns:
            self（支持链式调用）
        """
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(callback)
        return self

    def off(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """取消注册监听器"""
        with self._lock:
            if event_type in self._listeners:
                self._listeners[event_type].remove(callback)

    def once(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """注册一次性监听器（触发后自动移除）"""
        def wrapper(event: Event):
            callback(event)
            self.off(event_type, wrapper)
        self.on(event_type, wrapper)

    # ─────────────────────────────────────────────────────────────────
    # 事件发射
    # ─────────────────────────────────────────────────────────────────

    def emit(self, event_type: str, task_id: str | None = None, **data) -> Event:
        """
        发射事件

        Args:
            event_type: 事件类型
            task_id: 关联任务 ID
            **data: 事件数据（展开为 data 字段）

        Returns:
            构造的 Event 对象
        """
        event = Event(
            id=str(uuid.uuid4())[:8],
            type=event_type,
            task_id=task_id,
            data=data,
        )

        # 写入所有 Sink
        for sink in self._sinks:
            try:
                sink.write(event)
            except Exception as e:
                print(f"⚠️  Sink {sink.__class__.__name__} 写入失败：{e}", file=sys.stderr)

        # 触发监听器
        listeners = []
        with self._lock:
            listeners.extend(self._listeners.get(event_type, []))
            listeners.extend(self._listeners.get("*", []))

        for listener in listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"⚠️  监听器执行失败：{e}", file=sys.stderr)

        return event

    def flush(self) -> None:
        """刷新所有 Sink"""
        for sink in self._sinks:
            try:
                sink.flush()
            except Exception as e:
                print(f"⚠️  Sink {sink.__class__.__name__} flush 失败：{e}", file=sys.stderr)

    # ─────────────────────────────────────────────────────────────────
    # 便捷方法（自动构造标准事件）
    # ─────────────────────────────────────────────────────────────────

    def emit_task_start(self, name: str, params: dict | None = None) -> str:
        """
        发射 task_start 事件，返回 task_id

        Args:
            name: 任务名称（人类可读）
            params: 任务参数

        Returns:
            task_id（短 UUID）
        """
        self._task_counter += 1
        task_id = f"t{self._task_counter:03d}"
        self.emit(
            EventType.TASK_START,
            task_id=task_id,
            name=name,
            params=params or {},
            message="任务已启动",
        )
        return task_id

    def emit_task_stream(self, task_id: str, name: str, text: str) -> None:
        """发射流式文本片段（追加到上一行）"""
        self.emit(EventType.TASK_STREAM, task_id=task_id, name=name, text=text)

    def emit_task_progress(
        self,
        task_id: str,
        name: str,
        status: str,
        message: str = "",
        progress: float = -1.0,
    ) -> None:
        """
        发射进度更新

        Args:
            task_id: 任务 ID
            name: 任务名称
            status: 状态描述（如 "pending" / "generating" / "splitting" / "saving"）
            message: 详细消息
            progress: 进度 0.0-1.0（-1 表示未知）
        """
        self.emit(
            EventType.TASK_PROGRESS,
            task_id=task_id,
            name=name,
            status=status,
            message=message,
            progress=progress,
        )

    def emit_task_end(
        self,
        task_id: str,
        name: str,
        result: Any | None = None,
        elapsed: float = 0.0,
        result_preview: str = "",
    ) -> None:
        """发射任务完成事件"""
        self.emit(
            EventType.TASK_END,
            task_id=task_id,
            name=name,
            elapsed=elapsed,
            result=result,
            result_preview=result_preview,
        )

    def emit_task_error(
        self,
        task_id: str,
        name: str,
        error: str,
        error_type: str = "RuntimeError",
    ) -> None:
        """发射任务失败事件"""
        self.emit(
            EventType.TASK_ERROR,
            task_id=task_id,
            name=name,
            error=error,
            error_type=error_type,
        )

    def emit_tool_call(self, task_id: str, name: str, tool_name: str, args: dict | None = None) -> None:
        """发射工具调用事件（Toonflow toolCall）"""
        self.emit(
            EventType.TOOL_CALL,
            task_id=task_id,
            name=name,
            tool_name=tool_name,
            args=args or {},
        )

    def emit_tool_result(
        self,
        task_id: str,
        name: str,
        tool_name: str,
        success: bool = True,
        result: Any | None = None,
    ) -> None:
        """发射工具返回事件（Toonflow toolCall response）"""
        self.emit(
            EventType.TOOL_RESULT,
            task_id=task_id,
            name=name,
            tool_name=tool_name,
            success=success,
            result=result,
        )

    def emit_data_refresh(self, task_id: str, name: str, refresh_type: str) -> None:
        """发射数据刷新事件（Toonflow refresh）"""
        self.emit(
            EventType.DATA_REFRESH,
            task_id=task_id,
            name=name,
            refresh_type=refresh_type,
        )

    # ─────────────────────────────────────────────────────────────────
    # Sub-Agent 嵌套事件
    # ─────────────────────────────────────────────────────────────────

    def emit_transfer(
        self,
        task_id: str | None,
        from_agent: str,
        to_agent: str,
    ) -> None:
        """
        发射 Sub-Agent 切换事件（Toonflow transfer）。

        通知前端：当前 Agent 从 from_agent 切换到 to_agent。
        用于 Sub-Agent 嵌套时，前端 UI 显示角色切换动画。
        """
        self.emit(
            EventType.TRANSFER,
            task_id=task_id,
            from_agent=from_agent,
            to_agent=to_agent,
        )

    def emit_sub_agent_start(
        self,
        task_id: str | None,
        agent: str,
        task_description: str | None = None,
    ) -> None:
        """发射 Sub-Agent 启动事件"""
        self.emit(
            EventType.SUB_AGENT_START,
            task_id=task_id,
            agent=agent,
            task_description=task_description,
        )

    def emit_sub_agent_stream(
        self,
        task_id: str | None,
        agent: str,
        text: str,
    ) -> None:
        """
        发射 Sub-Agent 流式文本输出事件（Toonflow subAgentStream）。

        注意：huage888 不支持真实流式推送，text 为完整内容块，
        前端按需分片显示。
        """
        self.emit(
            EventType.SUB_AGENT_STREAM,
            task_id=task_id,
            agent=agent,
            text=text,
        )

    def emit_sub_agent_end(
        self,
        task_id: str | None,
        agent: str,
        full_response: str | None = None,
    ) -> None:
        """发射 Sub-Agent 结束事件（Toonflow subAgentEnd）"""
        self.emit(
            EventType.SUB_AGENT_END,
            task_id=task_id,
            agent=agent,
            full_response=full_response,
        )



    def task(self, name: str, params: dict | None = None) -> "TaskContext":
        """
        创建任务追踪上下文（推荐用法）

        用法：
            emitter = EventEmitter()
            with emitter.task("导演讲戏") as ctx:
                ctx.set_progress("generating", "正在调用 qwen-max...", 0.5)
                result = call_api(...)
                ctx.set_result(result)
            # 自动发射 task_end

            # 失败时自动发射 task_error
            with emitter.task("视频生成") as ctx:
                raise RuntimeError("API 错误")

        注意：需要配合 try/except 或使用 ctx.fail() 手动标记失败
        """
        return TaskContext(self, name, params)


class TaskContext:
    """
    任务追踪上下文

    用法：
        with emitter.task("导演讲戏") as ctx:
            ctx.set_progress("pending", "初始化...", 0.1)
            ctx.emit_stream("# 正在分析剧本...")
            result = call_api(...)
            ctx.set_progress("complete", "完成", 1.0)
            ctx.set_result(result)
    """

    def __init__(self, emitter: EventEmitter, name: str, params: dict | None = None):
        self.emitter = emitter
        self.name = name
        self.params = params
        self.task_id: str | None = None
        self.start_time: float = 0.0
        self._ended = False

    def __enter__(self) -> "TaskContext":
        self.start_time = time.time()
        self.task_id = self.emitter.emit_task_start(self.name, self.params)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._ended:
            return False

        elapsed = time.time() - self.start_time

        if exc_type is not None:
            # 任务失败
            error_msg = str(exc_val) if exc_val else "未知错误"
            self.emitter.emit_task_error(self.task_id, self.name, error=error_msg)
        elif not self._ended:
            # 任务成功（调用了 set_result 或正常退出）
            self.emitter.emit_task_end(
                self.task_id,
                self.name,
                elapsed=elapsed,
                result_preview=self._result_preview if hasattr(self, "_result_preview") else "",
            )

        return False  # 不吞没异常

    def set_progress(
        self,
        status: str,
        message: str = "",
        progress: float = -1.0,
    ) -> None:
        """设置进度"""
        self.emitter.emit_task_progress(
            self.task_id, self.name,
            status=status,
            message=message,
            progress=progress,
        )

    def emit_stream(self, text: str) -> None:
        """发送流式文本片段"""
        self.emitter.emit_task_stream(self.task_id, self.name, text)

    def set_result(self, result: Any, preview: str = "") -> None:
        """标记结果（触发 task_end）"""
        self._result_preview = preview
        self._ended = True
        elapsed = time.time() - self.start_time
        self.emitter.emit_task_end(
            self.task_id,
            self.name,
            result=result,
            elapsed=elapsed,
            result_preview=preview,
        )

    def fail(self, error: str, error_type: str = "RuntimeError") -> None:
        """标记失败（触发 task_error）"""
        self._ended = True
        self.emitter.emit_task_error(self.task_id, self.name, error=error, error_type=error_type)


# ─────────────────────────────────────────────────────────────────────────────
# 便捷工厂函数
# ─────────────────────────────────────────────────────────────────────────────

def create_emitter(
    mode: str = "console",
    log_file: str | None = None,
    ws_url: str | None = None,
    **kwargs,
) -> EventEmitter:
    """
    创建 EventEmitter 的便捷工厂函数

    Args:
        mode: 输出模式
          - "console": 仅控制台（默认）
          - "file": 仅文件（JSONL）
          - "console+file": 控制台 + 文件
          - "all": 控制台 + 文件 + WebSocket
        log_file: JSONL 日志文件路径（mode 含 file 时使用）
        ws_url: WebSocket URL（mode 含 ws 时使用）
        **kwargs: 透传给 Sink

    Returns:
        配置好的 EventEmitter 实例
    """
    sinks: list[Sink] = []

    if mode in ("console", "console+file", "all"):
        sinks.append(ConsoleSink(**kwargs))

    if mode in ("file", "console+file", "all"):
        path = log_file or ".huage888/events.jsonl"
        sinks.append(JSONLSink(path))

    if mode == "all" and ws_url:
        sinks.append(WebSocketSink(ws_url))

    return EventEmitter(sinks=sinks)


# ─────────────────────────────────────────────────────────────────────────────
# 预设Emitter（全局单例，方便复用）
# ─────────────────────────────────────────────────────────────────────────────

# 默认仅控制台输出
default_emitter = EventEmitter()

# 带文件记录的Emitter
logging_emitter = EventEmitter(sinks=[
    ConsoleSink(color=True, progress_bar=True),
    JSONLSink(".huage888/events.jsonl"),
])
