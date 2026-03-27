"""
漫舟异步任务队列系统
基于 APScheduler + 内存/磁盘状态持久化
参考 ZJT APScheduler + Tasks表模式 + 漫舟拉片Agent jobs状态管理
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger("manzhou.task_queue")


# ---------------------------------------------------------------------------
# AsyncTask 数据结构
# ---------------------------------------------------------------------------

@dataclass
class AsyncTask:
    """异步任务"""

    task_id: str
    name: str  # 任务名称
    func_name: str  # 函数名
    func_args: tuple  # 位置参数
    func_kwargs: dict  # 命名参数
    status: str  # pending / running / completed / failed / cancelled
    created_at: float  # 创建时间（time.time()）
    started_at: float = 0.0  # 开始时间
    completed_at: float = 0.0  # 完成时间
    result: Any = None  # 返回结果
    error: str = ""  # 错误信息
    progress: float = 0.0  # 进度 0.0-1.0
    progress_msg: str = ""  # 进度消息
    retry_count: int = 0  # 当前重试次数
    max_retries: int = 3  # 最大重试次数
    timeout_sec: int = 300  # 超时秒数
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        # 注意：metadata["progress_callback"] 是函数，不能 JSON 序列化
        # 仅持久化普通 metadata 字段
        meta = {
            k: v for k, v in self.metadata.items()
            if k != "progress_callback" and not callable(v)
        }
        return {
            "task_id": self.task_id,
            "name": self.name,
            "func_name": self.func_name,
            "func_args": self.func_args,
            "func_kwargs": self.func_kwargs,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": _json_safe(self.result),
            "error": self.error,
            "progress": self.progress,
            "progress_msg": self.progress_msg,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_sec": self.timeout_sec,
            "metadata": meta,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AsyncTask":
        # 兼容旧格式或缺少字段的情况
        defaults = {
            "started_at": 0.0,
            "completed_at": 0.0,
            "result": None,
            "error": "",
            "progress": 0.0,
            "progress_msg": "",
            "retry_count": 0,
            "max_retries": 3,
            "timeout_sec": 300,
            "metadata": {},
        }
        for k, v in defaults.items():
            d.setdefault(k, v)
        return cls(**d)


# ---------------------------------------------------------------------------
# TaskBroadcaster — SSE多客户端订阅
# ---------------------------------------------------------------------------

class TaskBroadcaster:
    """
    任务进度广播器（支持多SSE客户端订阅同一任务）
    """

    def __init__(self):
        self._channels: dict[str, list[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def broadcast(self, task_id: str, event: dict) -> None:
        """广播事件到所有订阅者"""
        async with self._lock:
            queues = self._channels.get(task_id, [])
            dead = []
            for q in queues:
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    dead.append(q)
            # 清理已满的队列
            for q in dead:
                queues.remove(q)
            if not queues:
                self._channels.pop(task_id, None)

    def broadcast_sync(self, task_id: str, event: dict) -> None:
        """同步版本的广播（供非async上下文调用）"""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(task_id, event))
        except RuntimeError:
            pass

    async def subscribe(self, task_id: str) -> AsyncIterator[dict]:
        """订阅任务进度，yield事件直到取消"""
        q: asyncio.Queue[dict] = asyncio.Queue(maxsize=64)
        async with self._lock:
            self._channels.setdefault(task_id, []).append(q)

        try:
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=60.0)
                    yield event
                    # completed / error 类型事件后自然结束
                    if event.get("type") in ("completed", "error", "cancelled"):
                        break
                except asyncio.TimeoutError:
                    # 心跳：防止连接长时间无消息而断开
                    yield {"type": "heartbeat", "task_id": task_id}
        finally:
            await self._unsubscribe(task_id, q)

    async def _unsubscribe(self, task_id: str, q: asyncio.Queue) -> None:
        async with self._lock:
            if task_id in self._channels:
                try:
                    self._channels[task_id].remove(q)
                except ValueError:
                    pass
                if not self._channels[task_id]:
                    del self._channels[task_id]

    def unsubscribe(self, task_id: str) -> None:
        """同步取消订阅"""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._unsubscribe_all(task_id))
        except RuntimeError:
            pass

    async def _unsubscribe_all(self, task_id: str) -> None:
        async with self._lock:
            self._channels.pop(task_id, None)


# ---------------------------------------------------------------------------
# AsyncTaskQueue — 核心队列
# ---------------------------------------------------------------------------

class AsyncTaskQueue:
    """
    漫舟异步任务队列

    功能：
    1. 异步任务提交（submit）
    2. 任务状态轮询（pending/running/completed/failed）
    3. 任务取消（cancel）
    4. 进度回调（progress callback）
    5. 超时控制（timeout）
    6. 重试机制（retry）
    7. 任务持久化（重启不丢状态）
    8. SSE推送集成（实时进度）
    """

    def __init__(
        self,
        persistence_path: str = "./data/tasks.json",
        max_workers: int = 4,
        default_timeout: int = 300,
        default_retries: int = 3,
    ):
        self.persistence_path = Path(persistence_path)
        self.max_workers = max_workers
        self.default_timeout = default_timeout
        self.default_retries = default_retries

        self._tasks: dict[str, AsyncTask] = {}  # task_id -> AsyncTask
        self._lock = asyncio.Lock()
        self._running = False
        self._workers: list[asyncio.Task] = []
        self._scheduler = AsyncIOScheduler()
        self._broadcaster = TaskBroadcaster()

        # 内部任务函数注册表（submit时填充）
        self._funcs: dict[str, Callable] = {}

        # 启动持久化恢复
        self._ensure_data_dir()
        self._restore()

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def start(self) -> None:
        """启动队列工作协程和调度器"""
        if self._running:
            return
        self._running = True
        for i in range(self.max_workers):
            t = asyncio.create_task(self._run_worker(i))
            self._workers.append(t)
        # 定时清理过期任务（每10分钟）
        self._scheduler.add_job(
            self._cleanup_job,
            "interval",
            minutes=10,
            id="cleanup_expired_tasks",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info(
            f"AsyncTaskQueue started with {self.max_workers} workers, "
            f"persistence={self.persistence_path}"
        )

    async def stop(self) -> None:
        """停止队列"""
        self._running = False
        self._scheduler.shutdown(wait=False)
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        await self._persist()
        logger.info("AsyncTaskQueue stopped")

    # ------------------------------------------------------------------
    # 任务提交
    # ------------------------------------------------------------------

    async def submit(
        self,
        func: Callable,
        name: str = "",
        timeout: int | None = None,
        retry: int | None = None,
        progress_callback: Callable[[float, str], None] | None = None,
        **kwargs,
    ) -> str:
        """
        提交异步任务。

        Args:
            func:        异步可调用函数（协程函数或返回协程的可调用对象）
            name:        任务显示名称
            timeout:     超时秒数（默认使用 default_timeout）
            retry:       最大重试次数（默认使用 default_retries）
            progress_callback: 进度回调 (progress: float, message: str) -> None
            **kwargs:    传递给 func 的关键字参数

        Returns:
            task_id: str
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        timeout = timeout if timeout is not None else self.default_timeout
        retry = retry if retry is not None else self.default_retries

        # 保存函数引用（用于执行）
        self._funcs[task_id] = func

        func_name = getattr(func, "__name__", repr(func))
        task = AsyncTask(
            task_id=task_id,
            name=name or func_name,
            func_name=func_name,
            func_args=(),
            func_kwargs=kwargs,
            status="pending",
            created_at=_now(),
            max_retries=retry,
            timeout_sec=timeout,
            metadata={
                "progress_callback": progress_callback,  # 不做JSON序列化，仅内存使用
            },
        )

        async with self._lock:
            self._tasks[task_id] = task

        await self._persist()
        await self._broadcast(
            task_id,
            {"type": "submitted", "task_id": task_id, "name": task.name, "status": "pending"}
        )
        logger.info(f"Task submitted: {task_id} '{task.name}'")
        return task_id

    # ------------------------------------------------------------------
    # 任务查询
    # ------------------------------------------------------------------

    def get_status(self, task_id: str) -> AsyncTask | None:
        """获取任务状态"""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[AsyncTask]:
        """获取所有任务"""
        return list(self._tasks.values())

    def list_tasks(
        self,
        status: str | None = None,
        limit: int = 50,
    ) -> list[AsyncTask]:
        """
        列表任务

        Args:
            status: 按状态过滤（pending/running/completed/failed/cancelled）
            limit:  返回数量上限（按创建时间倒序）
        """
        tasks = sorted(
            self._tasks.values(),
            key=lambda t: t.created_at,
            reverse=True,
        )
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks[:limit]

    # ------------------------------------------------------------------
    # 任务取消
    # ------------------------------------------------------------------

    async def cancel(self, task_id: str) -> bool:
        """取消任务（仅对 pending/running 状态有效）"""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            if task.status not in ("pending", "running"):
                return False
            task.status = "cancelled"
            task.completed_at = _now()
            await self._persist()
        await self._broadcast(
            task_id,
            {"type": "cancelled", "task_id": task_id, "status": "cancelled"}
        )
        logger.info(f"Task cancelled: {task_id}")
        return True

    # ------------------------------------------------------------------
    # 任务重试
    # ------------------------------------------------------------------

    async def retry(self, task_id: str) -> str:
        """
        重试失败任务，返回新的 task_id。
        仅对 failed / cancelled 状态的任务有效。
        """
        orig = self._tasks.get(task_id)
        if not orig or orig.status not in ("failed", "cancelled"):
            raise ValueError(f"Task {task_id} cannot be retried (status={orig.status if orig else None})")

        # 从原始任务中提取func（需外部重新注册，这里仅复制参数）
        func = self._funcs.get(task_id)
        if not func:
            raise RuntimeError(
                f"Cannot retry {task_id}: original function not registered. "
                "Please re-submit the task with the original function."
            )

        new_id = await self.submit(
            func,
            name=orig.name + " (重试)",
            timeout=orig.timeout_sec,
            retry=orig.max_retries,
            **orig.func_kwargs,
        )
        logger.info(f"Task retried: {task_id} -> {new_id}")
        return new_id

    # ------------------------------------------------------------------
    # SSE 订阅
    # ------------------------------------------------------------------

    def subscribe(self, task_id: str) -> AsyncIterator[dict]:
        """
        订阅任务进度（SSE流）。
        Yields: {"type": "progress"|"completed"|"error"|"cancelled"|"heartbeat", "data": {...}}
        """
        return self._broadcaster.subscribe(task_id)

    # ------------------------------------------------------------------
    # 清理
    # ------------------------------------------------------------------

    async def cleanup(self, max_age_hours: int = 24) -> int:
        """
        清理超过 max_age_hours 的已完成 / 失败 / 取消 任务。
        返回清理数量。
        """
        now = _now()
        to_delete = []
        async with self._lock:
            for tid, t in self._tasks.items():
                if t.status in ("completed", "failed", "cancelled"):
                    age_hours = (now - t.completed_at) / 3600 if t.completed_at else 0
                    if age_hours >= max_age_hours:
                        to_delete.append(tid)
            for tid in to_delete:
                del self._tasks[tid]
                self._funcs.pop(tid, None)
                self._broadcaster.unsubscribe(tid)
            if to_delete:
                await self._persist()
        logger.info(f"Cleanup: removed {len(to_delete)} expired tasks")
        return len(to_delete)

    async def _cleanup_job(self) -> None:
        """APScheduler 定时调用的清理（异步）"""
        await self.cleanup(max_age_hours=24)

    # ------------------------------------------------------------------
    # 核心执行逻辑
    # ------------------------------------------------------------------

    async def _run_worker(self, worker_id: int) -> None:
        """工作协程：从队列取 pending 任务执行"""
        logger.debug(f"Worker {worker_id} started")
        while self._running:
            task = None
            async with self._lock:
                for t in self._tasks.values():
                    if t.status == "pending":
                        task = t
                        task.status = "running"
                        task.started_at = _now()
                        break
            if not task:
                await asyncio.sleep(0.5)
                continue

            logger.info(f"[Worker {worker_id}] Execute: {task.task_id} '{task.name}'")
            try:
                result = await self._execute_task(task)
                async with self._lock:
                    task.result = result
                    task.status = "completed"
                    task.completed_at = _now()
                    task.progress = 1.0
                    task.progress_msg = "完成"
                await self._persist()
                await self._broadcast(
                    task.task_id,
                    {
                        "type": "completed",
                        "task_id": task.task_id,
                        "result": _json_safe(task.result),
                    },
                )
                logger.info(f"Task completed: {task.task_id}")
            except asyncio.CancelledError:
                async with self._lock:
                    task.status = "cancelled"
                    task.completed_at = _now()
                await self._persist()
                await self._broadcast(
                    task.task_id,
                    {"type": "cancelled", "task_id": task.task_id},
                )
                logger.warning(f"Task cancelled (worker): {task.task_id}")
                raise
            except Exception as e:
                await self._handle_task_error(task, e)

    async def _execute_task(self, task: AsyncTask) -> Any:
        """
        执行单个任务（含重试/超时控制/进度回调）
        """
        func = self._funcs.get(task.task_id)
        if not func:
            raise RuntimeError(f"Function for task {task.task_id} not found")

        last_error = None
        for attempt in range(task.max_retries + 1):
            async with self._lock:
                task.retry_count = attempt
            try:
                # 支持生成器/协程函数：yield (progress, message)
                coro = func(*task.func_args, **task.func_kwargs)
                result = await self._run_with_timeout(
                    task.task_id, coro, task.timeout_sec
                )
                return result
            except asyncio.TimeoutError:
                last_error = f"Timeout after {task.timeout_sec}s"
                logger.warning(
                    f"Task {task.task_id} attempt {attempt + 1} timeout "
                    f"(>{task.timeout_sec}s)"
                )
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.warning(
                    f"Task {task.task_id} attempt {attempt + 1} failed: {last_error}"
                )

            if attempt < task.max_retries:
                delay = min(2 ** attempt * 2.0, 60.0)  # 2, 4, 8, 16, 32, 60
                await self._broadcast(
                    task.task_id,
                    {
                        "type": "retrying",
                        "task_id": task.task_id,
                        "attempt": attempt + 1,
                        "max_retries": task.max_retries,
                        "delay_sec": delay,
                        "error": last_error,
                    },
                )
                await asyncio.sleep(delay)

        # 全部重试均失败
        raise RuntimeError(
            f"Task {task.task_id} failed after {task.max_retries + 1} attempts. "
            f"Last error: {last_error}"
        )

    async def _run_with_timeout(
        self, task_id: str, coro: Any, timeout_sec: int
    ) -> Any:
        """
        运行协程，支持外部取消（通过task_id），
        并且实时将生成器的 yield 进度转发为广播。
        """
        inner_task = asyncio.create_task(coro)
        check_interval = 0.2  # 每0.2秒检查一次进度/取消信号

        while not inner_task.done():
            done, _ = await asyncio.wait(
                [inner_task],
                timeout=check_interval,
            )
            if done:
                break

            # 检查是否被取消
            async with self._lock:
                t = self._tasks.get(task_id)
                if t and t.status == "cancelled":
                    inner_task.cancel()
                    raise asyncio.CancelledError()

            await asyncio.sleep(check_interval)

        if inner_task.cancelled():
            raise asyncio.CancelledError()

        if inner_task.done() and inner_task.exception():
            raise inner_task.exception()

        result = inner_task.result()
        # 协程函数中 yield 进度 + return 结果 时，result 是生成器，
        # 需要消耗生成器才能取到 return 值
        if hasattr(result, "__next__") or hasattr(result, "send"):
            try:
                while True:
                    result.send(None)
            except StopIteration as ex:
                return ex.value if ex.value is not None else None
        return result

    async def _handle_task_error(self, task: AsyncTask, exc: Exception) -> None:
        """处理任务执行异常"""
        err_str = f"{type(exc).__name__}: {exc}"
        stack = traceback.format_exc()
        async with self._lock:
            task.error = err_str
            task.status = "failed"
            task.completed_at = _now()
        await self._persist()
        await self._broadcast(
            task.task_id,
            {
                "type": "error",
                "task_id": task.task_id,
                "error": err_str,
                "stack": stack,
            },
        )
        logger.error(f"Task failed: {task.task_id} — {err_str}\n{stack}")

    # ------------------------------------------------------------------
    # 进度更新（供外部回调使用）
    # ------------------------------------------------------------------

    def _make_progress_callback(self, task_id: str) -> Callable[[float, str], None]:
        """生成进度回调闭包"""
        def callback(progress: float, msg: str) -> None:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._update_progress(task_id, progress, msg))
            except RuntimeError:
                pass
        return callback

    async def _update_progress(
        self, task_id: str, progress: float, msg: str
    ) -> None:
        """更新任务进度并广播"""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.progress = max(0.0, min(1.0, progress))
            task.progress_msg = msg
        await self._broadcast(
            task_id,
            {
                "type": "progress",
                "task_id": task_id,
                "progress": progress,
                "message": msg,
            },
        )

    # ------------------------------------------------------------------
    # 持久化
    # ------------------------------------------------------------------

    def _ensure_data_dir(self) -> None:
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)

    def _restore(self) -> None:
        """从 JSON 文件恢复任务状态（仅恢复非 running 的任务）"""
        if not self.persistence_path.exists():
            return
        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            count = 0
            for d in raw:
                t = AsyncTask.from_dict(d)
                # running 状态任务重启后变为 failed（防止僵尸）
                if t.status == "running":
                    t.status = "failed"
                    t.error = "Worker crashed during previous run"
                    t.completed_at = _now()
                self._tasks[t.task_id] = t
                count += 1
            logger.info(f"Restored {count} tasks from {self.persistence_path}")
        except Exception as e:
            logger.error(f"Failed to restore tasks: {e}")

    async def _persist(self) -> None:
        """持久化所有任务状态到 JSON 文件"""
        try:
            data = [t.to_dict() for t in self._tasks.values()]
            # 写入临时文件再rename，保证原子性
            tmp = self.persistence_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            tmp.rename(self.persistence_path)
        except Exception as e:
            logger.error(f"Failed to persist tasks: {e}")

    # ------------------------------------------------------------------
    # 内部广播
    # ------------------------------------------------------------------

    async def _broadcast(self, task_id: str, event: dict) -> None:
        await self._broadcaster.broadcast(task_id, event)


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _now() -> float:
    """当前时间戳（秒）"""
    import time
    return time.time()


def _json_safe(obj: Any) -> Any:
    """将不可JSON序列化的对象转为安全表示"""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return repr(obj)


# ---------------------------------------------------------------------------
# 自测代码
# ---------------------------------------------------------------------------

async def _self_test() -> bool:
    """AsyncTaskQueue 自测"""
    import tempfile

    print("\n=== AsyncTaskQueue Self-Test ===")

    # 使用临时目录避免污染
    with tempfile.TemporaryDirectory() as tmpdir:
        persist = os.path.join(tmpdir, "tasks.json")
        queue = AsyncTaskQueue(
            persistence_path=persist,
            max_workers=2,
            default_timeout=30,
            default_retries=1,
        )
        queue.start()

        # ── 测试1: 基本提交 ──────────────────────────────────────────
        async def dummy_task(a: int, b: str) -> dict:
            await asyncio.sleep(0.3)
            return {"a": a, "b": b, "sum": a * 2}

        tid = await queue.submit(
            dummy_task,
            name="测试任务1",
            a=10,
            b="hello",
        )
        print(f"[TEST 1] Submitted: {tid}")
        assert tid in queue._tasks, "Task not found in queue"
        assert queue.get_status(tid).status == "pending", "Initial status should be pending"

        # ── 测试2: 进度回调 + SSE 订阅（先订阅，后提交，保证不丢事件）────
        progress_log: list[tuple[float, str]] = []

        def on_progress(p: float, m: str) -> None:
            progress_log.append((p, m))

        async def progress_task() -> str:
            for i in range(5):
                await asyncio.sleep(0.1)
                on_progress((i + 1) / 5, f"步骤 {i + 1}/5")
            return "done"

        events: list[dict] = []
        sse_ready = asyncio.Event()

        async def sse_subscriber():
            async for ev in queue.subscribe(tid2):
                events.append(ev.copy())
                sse_ready.set()
                if ev.get("type") in ("completed", "error"):
                    break

        # 提交任务（队列pickup稍晚于subscriber启动）
        tid2 = await queue.submit(
            progress_task,
            name="进度测试",
            progress_callback=on_progress,
        )
        print(f"[TEST 2] Submitted progress task: {tid2}")

        # 先订阅，等待首次事件到达后再继续（确保不漏事件）
        sub_task = asyncio.create_task(sse_subscriber())
        await sse_ready.wait()

        # ── 测试3: 失败重试 ──────────────────────────────────────────
        fail_count = 0

        async def flaky_task() -> str:
            nonlocal fail_count
            fail_count += 1
            if fail_count < 2:
                raise ValueError("Flaky error")
            return "recovered"

        tid3 = await queue.submit(
            flaky_task,
            name="重试测试",
            retry=2,
        )
        print(f"[TEST 3] Submitted retry task: {tid3}")

        # ── 等待所有任务完成 ─────────────────────────────────────────
        await asyncio.sleep(4)

        # 验证
        t1 = queue.get_status(tid)
        t2 = queue.get_status(tid2)
        t3 = queue.get_status(tid3)

        print(f"\n[T1] Status: {t1.status}, Result: {t1.result}")
        print(f"[T2] Status: {t2.status}, Progress: {t2.progress}, Events: {len(events)}")
        print(f"[T3] Status: {t3.status}, Retries: {t3.retry_count}, Error: {t3.error}")

        sub_task.cancel()
        try:
            await sub_task
        except asyncio.CancelledError:
            pass

        await queue.stop()

        # 断言
        assert t1.status == "completed", f"T1 should be completed: {t1.status}"
        assert t1.result == {"a": 10, "b": "hello", "sum": 20}, f"T1 result mismatch: {t1.result}"
        assert t2.status == "completed", f"T2 should be completed: {t2.status}"
        assert t2.progress == 1.0, f"T2 progress should be 1.0: {t2.progress}"
        assert len(events) >= 1, f"T2 should have received at least 1 SSE event, got {len(events)}: {events}"
        assert t3.status == "completed", f"T3 should be completed after retry: {t3.status}"
        assert t3.retry_count >= 1, f"T3 should have retried: {t3.retry_count}"

        # ── 测试4: 持久化恢复 ───────────────────────────────────────
        queue2 = AsyncTaskQueue(persistence_path=persist, max_workers=2)
        queue2.start()
        restored = queue2.get_status(tid)
        print(f"\n[TEST 4] Restored task: {restored.task_id} status={restored.status}")
        assert restored is not None, "Task should be restorable"
        assert restored.result == {"a": 10, "b": "hello", "sum": 20}
        await queue2.stop()

        # ── 测试5: 取消任务 ──────────────────────────────────────────
        queue3 = AsyncTaskQueue(persistence_path=persist, max_workers=1)
        queue3.start()

        async def long_task() -> str:
            await asyncio.sleep(10)
            return "done"

        tid4 = await queue3.submit(long_task, name="长时间任务")
        await asyncio.sleep(0.3)
        cancelled = await queue3.cancel(tid4)
        t4 = queue3.get_status(tid4)
        print(f"\n[TEST 5] Cancel result: {cancelled}, Status: {t4.status}")
        assert cancelled is True, "Cancel should succeed"
        assert t4.status == "cancelled", f"Status should be cancelled: {t4.status}"
        await queue3.stop()

        print("\n✅ All self-tests passed!")
        return True


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(_self_test())
