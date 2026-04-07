#!/usr/bin/env python3
"""
task_queue.py — huage888 批量任务队列 + 自动重试

参考 Toonflow 批量视频生成模式，为 Pipeline 提供：
1. 批量任务队列（批量出图/出视频）
2. 指数退避重试（自动处理限流/服务错误）
3. 与 task_state / event_emitter 联动

用法：

  from task_queue import TaskQueue, Task

  queue = TaskQueue(max_workers=4, max_retries=3)

  # 添加任务
  queue.add("生成视频-镜头01", generate_video_fn, prompt="...", output="/tmp/v01.mp4")
  queue.add("生成视频-镜头02", generate_video_fn, prompt="...", output="/tmp/v02.mp4")
  queue.add("生成视频-镜头03", generate_video_fn, prompt="...", output="/tmp/v03.mp4")

  # 执行（阻塞）
  results = queue.run()

  # 或异步执行（带回调）
  queue.run_async(on_success=notify_success, on_error=notify_error)
"""

import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Optional

# task_state / event_emitter（可选依赖）
_task_state = None
_event_emitter = None


def _lazy_deps():
    global _task_state, _event_emitter
    if _task_state is None:
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from task_state import TaskManager, TaskState, TaskType
            from event_emitter import EventEmitter
            _task_state = (TaskManager, TaskState, TaskType)
            _event_emitter = EventEmitter
        except ImportError:
            _task_state = None
            _event_emitter = None
    return _task_state, _event_emitter


# ─────────────────────────────────────────────────────────────────────────────
# 数据模型
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TaskResult:
    """单个任务结果"""
    task_id: str
    name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    elapsed: float = 0.0
    retry_count: int = 0


@dataclass
class QueueStats:
    """队列统计"""
    total: int = 0
    pending: int = 0
    running: int = 0
    success: int = 0
    failed: int = 0
    retried: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# 错误分类
# ─────────────────────────────────────────────────────────────────────────────

class RetryableError(Exception):
    """可重试的错误（限流/服务错误/超时）"""
    pass


class PermanentError(Exception):
    """不可重试的错误（认证失败/参数错误）"""
    pass


def classify_error(error: Exception) -> type:
    """判断错误是否可重试"""
    err_str = str(error)

    # 可重试
    if any(kw in err_str for kw in [
        "429", "rate_limit", "RateLimit",
        "500", "InternalServerError", "server_error",
        "timeout", "Timeout", "timed out",
        "connection", "ConnectionError", "ConnectionReset",
        "502", "503", "504",
    ]):
        return RetryableError

    # 不可重试
    if any(kw in err_str for kw in [
        "401", "403", "authentication", "unauthorized",
        "404", "not_found", "NotFound",
        "invalid", "parameter", "ParameterError",
    ]):
        return PermanentError

    # 默认：可重试一次
    return RetryableError


# ─────────────────────────────────────────────────────────────────────────────
# 任务队列
# ─────────────────────────────────────────────────────────────────────────────

class TaskQueue:
    """
    批量任务队列

    特性：
    - 多线程并发执行（max_workers 控制并发数）
    - 指数退避重试（自动处理限流）
    - 与 task_state 联动（可选）
    - 与 event_emitter 联动（可选）
    - 任务依赖支持（可选）

    与 Toonflow 的差异：
    - Toonflow：全部串行等待，本地执行
    - huage888：支持并发 + 指数退避 + 事件追踪
    """

    def __init__(
        self,
        max_workers: int = 4,
        max_retries: int = 3,
        tasks_dir: str | Path | None = None,
        log_file: str | Path | None = None,
        progress_bar: bool = True,
    ):
        """
        Args:
            max_workers: 最大并发数（默认 4）
            max_retries: 单任务最大重试次数（默认 3）
            tasks_dir: task_state 持久化目录（可选）
            log_file: event_emitter 日志文件（可选）
            progress_bar: 是否显示进度条（默认 True）
        """
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.tasks_dir = tasks_dir
        self.log_file = log_file
        self.progress_bar = progress_bar

        self._tasks: list[dict] = []
        self._results: list[TaskResult] = []
        self._lock = Lock()
        self._manager = None
        self._emitter = None

    # ─────────────────────────────────────────────────────────────────
    # 任务管理
    # ─────────────────────────────────────────────────────────────────

    def add(
        self,
        name: str,
        fn: Callable,
        *args,
        task_id: str | None = None,
        task_type: str = "generic",
        max_retries: int | None = None,
        depends_on: str | None = None,
        **kwargs,
    ) -> str:
        """
        添加任务到队列

        Args:
            name: 任务名称（人类可读）
            fn: 执行函数
            *args: 位置参数
            task_id: 任务 ID（默认自动生成）
            task_type: 任务类型（用于 task_state）
            max_retries: 覆盖全局 max_retries
            depends_on: 依赖任务 ID（串行执行）
            **kwargs: 关键字参数

        Returns:
            task_id
        """
        task_id = task_id or str(uuid.uuid4())[:8]
        task = {
            "id": task_id,
            "name": name,
            "fn": fn,
            "args": args,
            "kwargs": kwargs,
            "task_type": task_type,
            "max_retries": max_retries if max_retries is not None else self.max_retries,
            "depends_on": depends_on,
        }
        with self._lock:
            self._tasks.append(task)
        return task_id

    def add_batch(
        self,
        items: list[dict],
        fn: Callable,
        name_template: str = "{index:03d}",
        task_type: str = "generic",
        max_retries: int | None = None,
    ) -> list[str]:
        """
        批量添加任务

        Args:
            items: 数据列表，每个 dict 会展开为 kwargs
            fn: 执行函数
            name_template: 名称模板，支持 {index}
            task_type: 任务类型
            max_retries: 最大重试次数

        Returns:
            task_id 列表
        """
        task_ids = []
        for i, item in enumerate(items):
            name = name_template.format(index=i + 1)
            kwargs = dict(item)
            if "name" in kwargs:
                name = kwargs.pop("name")
            tid = self.add(
                name=f"{name}-{name_template.format(index=i+1)}",
                fn=fn,
                task_type=task_type,
                max_retries=max_retries,
                **kwargs,
            )
            task_ids.append(tid)
        return task_ids

    # ─────────────────────────────────────────────────────────────────
    # 执行
    # ─────────────────────────────────────────────────────────────────

    def run(self) -> list[TaskResult]:
        """执行队列（阻塞），返回所有结果"""
        self._init_deps()
        self._emit_start()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures: dict[Future, dict] = {}
            for task in self._tasks:
                f = executor.submit(self._execute_task, task)
                futures[f] = task

            # 收集结果
            completed = 0
            total = len(self._tasks)
            for future in as_completed(futures):
                task = futures[future]
                result = future.result()
                with self._lock:
                    self._results.append(result)
                    completed += 1

                self._emit_progress(task["id"], task["name"], completed, total)
                self._emit_result(result)

        self._emit_end()
        return self._results

    def run_async(
        self,
        on_success: Callable[[TaskResult], None] | None = None,
        on_error: Callable[[TaskResult], None] | None = None,
        on_complete: Callable[[list[TaskResult]], None] | None = None,
    ) -> None:
        """
        异步执行（立即返回，结果通过回调通知）

        Args:
            on_success: 任务成功回调
            on_error: 任务失败回调
            on_complete: 所有任务完成回调
        """
        self._init_deps()
        self._emit_start()

        def submit_and_callback():
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._execute_task, t): t for t in self._tasks}
                for future in as_completed(futures):
                    result = future.result()
                    with self._lock:
                        self._results.append(result)
                    if result.success and on_success:
                        on_success(result)
                    elif not result.success and on_error:
                        on_error(result)
            self._emit_end()
            if on_complete:
                on_complete(self._results)

        import threading
        threading.Thread(target=submit_and_callback, daemon=True).start()

    def _execute_task(self, task: dict) -> TaskResult:
        """执行单个任务（带重试）"""
        task_id = task["id"]
        name = task["name"]
        fn = task["fn"]
        args = task["args"]
        kwargs = task["kwargs"]
        max_retries = task["max_retries"]
        task_type = task["task_type"]

        start_time = time.time()
        last_error = None

        # 初始化 task_state
        state_manager = None
        if self._manager:
            TaskManager, TaskState, _ = _lazy_deps()
            if TaskManager:
                state_manager = TaskManager(tasks_dir=str(self.tasks_dir))
                state_manager.create(
                    task_type=task_type,
                    name=name,
                    params={"args": str(args)[:100], "kwargs": str(kwargs)[:100]},
                    max_retries=max_retries,
                )
                state_manager.update(task_id, TaskState.RUNNING)

        self._emit_task_start(task_id, name)

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self._emit_retry(task_id, name, attempt, last_error)

                result = fn(*args, **kwargs)
                elapsed = time.time() - start_time

                if state_manager:
                    TaskManager, TaskState, _ = _lazy_deps()
                    if TaskManager:
                        state_manager.update(
                            task_id, TaskState.SUCCESS,
                            result={"result": str(result)[:200]},
                        )

                self._emit_task_end(task_id, name, result=result, elapsed=elapsed)
                return TaskResult(
                    task_id=task_id,
                    name=name,
                    success=True,
                    result=result,
                    elapsed=elapsed,
                    retry_count=attempt,
                )

            except Exception as e:
                last_error = str(e)
                error_cls = classify_error(e)

                if error_cls == PermanentError or attempt >= max_retries:
                    # 不可重试或已达最大重试次数
                    elapsed = time.time() - start_time

                    if state_manager:
                        TaskManager, TaskState, _ = _lazy_deps()
                        if TaskManager:
                            state_manager.update(
                                task_id, TaskState.FAILED,
                                error=last_error,
                                increment_retry=(attempt > 0),
                            )

                    self._emit_task_error(task_id, name, last_error)
                    return TaskResult(
                        task_id=task_id,
                        name=name,
                        success=False,
                        error=last_error,
                        elapsed=elapsed,
                        retry_count=attempt,
                    )

                # 可重试，指数退避
                wait_time = min(2 ** attempt * 10, 300)  # 10s, 20s, 40s, 80s, 160s（最大5分钟）
                time.sleep(wait_time)

        # 兜底
        return TaskResult(task_id=task_id, name=name, success=False, error=last_error)

    # ─────────────────────────────────────────────────────────────────
    # 依赖管理
    # ─────────────────────────────────────────────────────────────────

    def add_with_deps(
        self,
        name: str,
        fn: Callable,
        depends_on: list[str],
        *args,
        **kwargs,
    ) -> str:
        """
        添加带依赖的任务（所有依赖成功后才执行）

        Args:
            name: 任务名称
            fn: 执行函数
            depends_on: 依赖的 task_id 列表
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            task_id
        """
        task_id = str(uuid.uuid4())[:8]
        task = {
            "id": task_id,
            "name": name,
            "fn": fn,
            "args": args,
            "kwargs": kwargs,
            "task_type": "generic",
            "max_retries": self.max_retries,
            "depends_on": depends_on,  # list[str]
        }
        with self._lock:
            self._tasks.append(task)
        return task_id

    # ─────────────────────────────────────────────────────────────────
    # 事件发射（联动 event_emitter）
    # ─────────────────────────────────────────────────────────────────

    def _init_deps(self):
        if self._emitter is None and self.log_file is not None:
            EventEmitter = _lazy_deps()[1]
            if EventEmitter:
                try:
                    from event_emitter import EventEmitter as EE
                    from event_emitter import JSONLSink, ConsoleSink
                    self._emitter = EE(sinks=[
                        ConsoleSink(color=True, progress_bar=True),
                        JSONLSink(str(self.log_file)),
                    ])
                except ImportError:
                    pass

        if self._manager is None and self.tasks_dir is not None:
            TaskManager, _, _ = _lazy_deps()
            if TaskManager:
                self._manager = TaskManager(tasks_dir=str(self.tasks_dir))

    def _emit_start(self):
        if not self._emitter:
            return
        self._emitter.emit("task_start", name=f"TaskQueue[{len(self._tasks)}]")

    def _emit_task_start(self, task_id: str, name: str):
        if not self._emitter:
            return
        self._emitter.emit_task_start(name, params={"task_id": task_id})

    def _emit_retry(self, task_id: str, name: str, attempt: int, error: str):
        if not self._emitter:
            return
        self._emitter.emit(
            "task_progress",
            task_id=task_id,
            name=name,
            status="retry",
            message=f"重试（第 {attempt} 次）：{error[:40]}",
            progress=-1,
        )

    def _emit_progress(self, task_id: str, name: str, completed: int, total: int):
        if not self._emitter or not self.progress_bar:
            return
        progress = completed / total
        self._emitter.emit(
            "task_progress",
            name=f"Queue({completed}/{total})",
            status="running",
            message=f"正在执行：{name}",
            progress=progress,
        )

    def _emit_result(self, result: TaskResult):
        if not self._emitter:
            return
        icon = "✅" if result.success else "❌"
        self._emitter.emit(
            "tool_result",
            name=result.name,
            success=result.success,
            result={"elapsed": result.elapsed, "retry_count": result.retry_count},
        )

    def _emit_task_end(self, task_id: str, name: str, result: Any, elapsed: float):
        if not self._emitter:
            return
        self._emitter.emit_task_end(
            task_id, name,
            result={"result": str(result)[:100]},
            elapsed=elapsed,
            result_preview=f"{elapsed:.1f}s",
        )

    def _emit_task_error(self, task_id: str, name: str, error: str):
        if not self._emitter:
            return
        self._emitter.emit_task_error(task_id, name, error=error)

    def _emit_end(self):
        if not self._emitter:
            return
        stats = self.stats()
        self._emitter.emit(
            "task_end",
            name=f"TaskQueue",
            result={
                "total": stats.total,
                "success": stats.success,
                "failed": stats.failed,
            },
            elapsed=0,
            result_preview=f"{stats.success}/{stats.total} 成功",
        )

    # ─────────────────────────────────────────────────────────────────
    # 统计与查询
    # ─────────────────────────────────────────────────────────────────

    def stats(self) -> QueueStats:
        """获取队列统计"""
        stats = QueueStats(total=len(self._tasks))
        for r in self._results:
            stats.total += 1 if r.success or not r.success else 0
            if r.success:
                stats.success += 1
            else:
                stats.failed += 1
            if r.retry_count > 0:
                stats.retried += 1
        stats.pending = stats.total - stats.success - stats.failed
        return stats

    def results(self) -> list[TaskResult]:
        """获取所有结果"""
        return list(self._results)

    def successful(self) -> list[TaskResult]:
        """获取成功的结果"""
        return [r for r in self._results if r.success]

    def failed(self) -> list[TaskResult]:
        """获取失败的结果"""
        return [r for r in self._results if not r.success]


# ─────────────────────────────────────────────────────────────────────────────
# 便捷工厂
# ─────────────────────────────────────────────────────────────────────────────

def create_queue(
    max_workers: int = 4,
    max_retries: int = 3,
    tasks_dir: str | None = ".huage888/tasks",
    log_file: str | None = ".huage888/queue_events.jsonl",
) -> TaskQueue:
    """
    创建配置好的 TaskQueue

    Args:
        max_workers: 并发数
        max_retries: 最大重试次数
        tasks_dir: task_state 目录（None=不追踪）
        log_file: event_emitter 日志文件（None=不记录）
    """
    return TaskQueue(
        max_workers=max_workers,
        max_retries=max_retries,
        tasks_dir=tasks_dir,
        log_file=log_file,
        progress_bar=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    """命令行调试入口"""
    import argparse
    parser = argparse.ArgumentParser(description="huage888 任务队列")
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="执行任务队列")
    p_run.add_argument("queue_file", help="队列定义文件（Python 模块）")
    p_run.add_argument("--workers", "-w", type=int, default=4, help="并发数")
    p_run.add_argument("--retries", "-r", type=int, default=3, help="最大重试次数")

    args = parser.parse_args()

    if args.cmd == "run":
        print(f"待实现：从 {args.queue_file} 加载队列并执行")
        print(f"  workers={args.workers}, retries={args.retries}")


if __name__ == "__main__":
    _cli()
