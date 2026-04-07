#!/usr/bin/env python3
"""
task_state.py — huage888 任务状态机

参考 Toonflow t_video.state 模式，统一管理所有任务的生命周期。

设计原则：
- 状态持久化到 .huage888/tasks/ 目录
- 所有 Pipeline 执行前创建任务，执行后更新状态
- 支持重试追踪和错误归因

用法：
  from task_state import TaskManager, TaskState

  manager = TaskManager()

  # 创建任务
  task_id = manager.create("qwen", "director", {"agent": "director", "user": "..."})

  # 执行前更新为 RUNNING
  manager.update(task_id, TaskState.RUNNING)

  try:
      result = call_api(...)
      manager.update(task_id, TaskState.SUCCESS, result={"output": "..."})
  except Exception as e:
      manager.update(task_id, TaskState.FAILED, error=str(e))

  # 查询状态
  task = manager.get(task_id)
  print(task.state, task.error)
"""

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Optional, Any


# ─────────────────────────────────────────────────────────────────────────────
# 状态枚举（参考 Toonflow：0=pending, 1=success, -1=failed）
# ─────────────────────────────────────────────────────────────────────────────

class TaskState(IntEnum):
    """任务状态枚举（整数便于排序和比较）"""
    PENDING = 0      # 待执行
    RUNNING = 1      # 执行中
    SUCCESS = 2       # 成功完成
    FAILED = -1      # 执行失败（不可重试）
    RETRYING = 3     # 重试中（可重试的错误）


class TaskType(str):
    """任务类型常量"""
    QWEN = "qwen"           # qwen-max 文本生成
    DOUBAO_IMAGE = "doubao_image"   # Doubao 图片生成
    DOUBAO_VIDEO = "doubao_video"   # Doubao 视频生成
    KLING_VIDEO = "kling_video"     # Kling 视频生成
    LIBTV_SESSION = "libtv_session"  # LibTV 会话管理


# ─────────────────────────────────────────────────────────────────────────────
# 数据模型
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TaskRecord:
    """
    任务记录（对应 Toonflow 的 t_video / t_myTasks 表行）

    字段说明：
    - id: 唯一标识（UUID）
    - type: 任务类型（qwen / doubao_video / kling_video 等）
    - name: 人类可读名称（如 "导演讲戏-阶段一"）
    - state: 当前状态
    - created_at: 创建时间（ISO 格式）
    - started_at: 开始时间（ISO 格式，可选）
    - finished_at: 结束时间（ISO 格式，可选）
    - params: 执行参数（JSON）
    - result: 执行结果（JSON，可选）
    - error: 错误信息（可选）
    - retry_count: 重试次数
    - max_retries: 最大重试次数
    - external_id: 外部任务 ID（如 API 返回的 task_id）
    """
    id: str
    type: str
    name: str
    state: TaskState = TaskState.PENDING
    created_at: str = ""
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    params: dict = field(default_factory=dict)
    result: Optional[dict] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    external_id: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """序列化为字典"""
        d = asdict(self)
        d["state"] = self.state.value  # IntEnum → int
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TaskRecord":
        """从字典反序列化"""
        d = dict(d)  # 复制
        d["state"] = TaskState(d["state"])
        return cls(**d)

    def is_retryable(self) -> bool:
        """是否可重试"""
        return self.state == TaskState.FAILED and self.retry_count < self.max_retries


# ─────────────────────────────────────────────────────────────────────────────
# 任务管理器
# ─────────────────────────────────────────────────────────────────────────────

class TaskManager:
    """
    任务状态管理器

    持久化策略：
    - 所有任务记录存储在 .huage888/tasks/ 目录
    - 每个任务一个 JSON 文件，文件名 = task_id.json
    - 索引文件 tasks_index.json 加速查询

    线程安全：单进程写入，多进程读取无冲突
    """

    DEFAULT_TASKS_DIR = ".huage888/tasks"

    def __init__(self, tasks_dir: str | Path | None = None):
        self.tasks_dir = Path(tasks_dir) if tasks_dir else Path(self.DEFAULT_TASKS_DIR)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.tasks_dir / "tasks_index.json"
        self._index: dict[str, str] = self._load_index()  # task_id → file_path

    # ─────────────────────────────────────────────────────────────────
    # 索引管理
    # ─────────────────────────────────────────────────────────────────

    def _load_index(self) -> dict[str, str]:
        """加载索引文件"""
        if self._index_path.exists():
            return json.loads(self._index_path.read_text(encoding="utf-8"))
        return {}

    def _save_index(self) -> None:
        """保存索引文件"""
        self._index_path.write_text(
            json.dumps(self._index, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    # ─────────────────────────────────────────────────────────────────
    # 核心 CRUD
    # ─────────────────────────────────────────────────────────────────

    def create(
        self,
        task_type: str,
        name: str,
        params: dict | None = None,
        max_retries: int = 3,
    ) -> str:
        """
        创建新任务

        Args:
            task_type: 任务类型（TaskType 常量）
            name: 任务名称（人类可读）
            params: 执行参数
            max_retries: 最大重试次数

        Returns:
            task_id: 新建任务的 UUID
        """
        task_id = str(uuid.uuid4())[:8]  # 短 UUID，便于阅读
        record = TaskRecord(
            id=task_id,
            type=task_type,
            name=name,
            params=params or {},
            max_retries=max_retries,
        )

        # 持久化
        file_path = self.tasks_dir / f"{task_id}.json"
        file_path.write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # 更新索引
        self._index[task_id] = str(file_path)
        self._save_index()

        return task_id

    def get(self, task_id: str) -> Optional[TaskRecord]:
        """获取任务记录"""
        if task_id not in self._index:
            file_path = self.tasks_dir / f"{task_id}.json"
            if not file_path.exists():
                return None
            self._index[task_id] = str(file_path)
            self._save_index()

        file_path = Path(self._index[task_id])
        if not file_path.exists():
            return None

        return TaskRecord.from_dict(
            json.loads(file_path.read_text(encoding="utf-8"))
        )

    def update(
        self,
        task_id: str,
        state: TaskState,
        result: dict | None = None,
        error: str | None = None,
        external_id: str | None = None,
        increment_retry: bool = False,
    ) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务 ID
            state: 新状态
            result: 执行结果（SUCCESS 时填写）
            error: 错误信息（FAILED 时填写）
            external_id: 外部任务 ID（如 API task_id）
            increment_retry: 是否增加重试计数

        Returns:
            是否更新成功
        """
        record = self.get(task_id)
        if not record:
            return False

        # 更新状态
        record.state = state

        # 时间戳
        if state == TaskState.RUNNING and not record.started_at:
            record.started_at = datetime.now().isoformat()

        if state in (TaskState.SUCCESS, TaskState.FAILED):
            record.finished_at = datetime.now().isoformat()

        # 结果 / 错误
        if result is not None:
            record.result = result
        if error is not None:
            record.error = error
        if external_id is not None:
            record.external_id = external_id

        # 重试计数
        if increment_retry:
            record.retry_count += 1

        # 持久化
        file_path = Path(self._index[task_id])
        file_path.write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return True

    def delete(self, task_id: str) -> bool:
        """删除任务"""
        if task_id not in self._index:
            return False

        file_path = Path(self._index[task_id])
        if file_path.exists():
            file_path.unlink()

        del self._index[task_id]
        self._save_index()
        return True

    # ─────────────────────────────────────────────────────────────────
    # 批量查询
    # ─────────────────────────────────────────────────────────────────

    def list(
        self,
        task_type: str | None = None,
        state: TaskState | None = None,
        limit: int = 100,
    ) -> list[TaskRecord]:
        """
        列出任务

        Args:
            task_type: 按类型过滤（可选）
            state: 按状态过滤（可选）
            limit: 返回数量限制

        Returns:
            任务记录列表（按创建时间倒序）
        """
        records = []
        for task_id in list(self._index.keys())[:limit]:
            record = self.get(task_id)
            if not record:
                continue
            if task_type and record.type != task_type:
                continue
            if state is not None and record.state != state:
                continue
            records.append(record)

        # 按创建时间倒序
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records

    def count(self, state: TaskState | None = None) -> int:
        """统计任务数量"""
        if state is None:
            return len(self._index)

        return len([r for r in self.list(state=state) if r.state == state])

    # ─────────────────────────────────────────────────────────────────
    # 便捷方法
    # ─────────────────────────────────────────────────────────────────

    def wait_for_completion(
        self,
        task_id: str,
        poll_interval: float = 2.0,
        poll_timeout: float = 300.0,
    ) -> TaskRecord:
        """
        等待任务完成（轮询）

        Args:
            task_id: 任务 ID
            poll_interval: 轮询间隔（秒）
            poll_timeout: 超时时间（秒）

        Returns:
            最终任务记录

        Raises:
            TimeoutError: 超时
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > poll_timeout:
                raise TimeoutError(f"任务 {task_id} 等待超时（>{poll_timeout}s）")

            record = self.get(task_id)
            if not record:
                raise ValueError(f"任务 {task_id} 不存在")

            if record.state in (TaskState.SUCCESS, TaskState.FAILED):
                return record

            time.sleep(poll_interval)

    def summary(self) -> dict:
        """获取任务汇总统计"""
        all_tasks = self.list()
        return {
            "total": len(all_tasks),
            "pending": len([r for r in all_tasks if r.state == TaskState.PENDING]),
            "running": len([r for r in all_tasks if r.state == TaskState.RUNNING]),
            "success": len([r for r in all_tasks if r.state == TaskState.SUCCESS]),
            "failed": len([r for r in all_tasks if r.state == TaskState.FAILED]),
            "retrying": len([r for r in all_tasks if r.state == TaskState.RETRYING]),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 辅助函数（Pipeline 集成用）
# ─────────────────────────────────────────────────────────────────────────────

def run_with_tracking(
    manager: TaskManager,
    task_type: str,
    name: str,
    params: dict,
    execute_fn,
    max_retries: int = 3,
) -> tuple[TaskState, Any]:
    """
    带状态追踪的通用执行函数

    用法：
        def my_api_call(params):
            # 实际 API 调用
            return result

        state, result = run_with_tracking(
            manager=TaskManager(),
            task_type=TaskType.QWEN,
            name="导演讲戏",
            params={"agent": "director", "user": "..."},
            execute_fn=my_api_call,
        )

    Args:
        manager: TaskManager 实例
        task_type: 任务类型
        name: 任务名称
        params: 执行参数
        execute_fn: 执行函数（接受 params，返回 result）
        max_retries: 最大重试次数

    Returns:
        (最终状态, 结果或错误信息)
    """
    task_id = manager.create(task_type, name, params, max_retries)

    for attempt in range(max_retries + 1):
        # 更新为运行中
        manager.update(task_id, TaskState.RUNNING)

        try:
            result = execute_fn(params)

            # 成功
            manager.update(
                task_id,
                TaskState.SUCCESS,
                result={"output": result} if isinstance(result, str) else result,
            )
            return TaskState.SUCCESS, result

        except Exception as e:
            error_msg = str(e)

            # 判断是否可重试
            is_retryable = (
                "429" in error_msg or
                "rate_limit" in error_msg.lower() or
                "500" in error_msg or
                "InternalServerError" in error_msg or
                "timeout" in error_msg.lower()
            )

            if is_retryable and attempt < max_retries:
                # 重试
                wait_time = 2 ** attempt  # 指数退避
                manager.update(
                    task_id,
                    TaskState.RETRYING,
                    error=error_msg,
                    increment_retry=True,
                )
                print(f"⏳ 任务 {task_id} 重试（第 {attempt + 1}/{max_retries} 次），{wait_time}s 后重试...", file=__import__("sys").stderr)
                time.sleep(wait_time)
                continue

            # 失败（不可重试或已达最大重试次数）
            manager.update(
                task_id,
                TaskState.FAILED,
                error=error_msg,
                increment_retry=(attempt > 0),
            )
            return TaskState.FAILED, error_msg

    # 兜底（不应到达）
    manager.update(task_id, TaskState.FAILED, error="未知错误")
    return TaskState.FAILED, "未知错误"


# ─────────────────────────────────────────────────────────────────────────────
# CLI（调试用）
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    """命令行调试入口"""
    import argparse

    parser = argparse.ArgumentParser(description="huage888 任务状态管理")
    sub = parser.add_subparsers(dest="cmd")

    # list
    p_list = sub.add_parser("list", help="列出任务")
    p_list.add_argument("--type", help="按类型过滤")
    p_list.add_argument("--state", type=int, help="按状态过滤（0=pending,1=running,2=success,-1=failed）")

    # get
    p_get = sub.add_parser("get", help="查看任务详情")
    p_get.add_argument("task_id", help="任务 ID")

    # summary
    sub.add_parser("summary", help="任务统计")

    args = parser.parse_args()
    manager = TaskManager()

    if args.cmd == "list":
        state = TaskState(args.state) if args.state is not None else None
        records = manager.list(task_type=args.type, state=state)
        if not records:
            print("无任务记录")
            return
        print(f"{'ID':<10} {'TYPE':<15} {'NAME':<20} {'STATE':<10} {'CREATED':<25}")
        print("-" * 80)
        for r in records:
            print(f"{r.id:<10} {r.type:<15} {r.name:<20} {r.state.name:<10} {r.created_at:<25}")

    elif args.cmd == "get":
        record = manager.get(args.task_id)
        if not record:
            print(f"任务 {args.task_id} 不存在")
            return
        print(json.dumps(record.to_dict(), ensure_ascii=False, indent=2))

    elif args.cmd == "summary":
        s = manager.summary()
        print(f"总任务数：{s['total']}")
        print(f"  待执行：{s['pending']}")
        print(f"  执行中：{s['running']}")
        print(f"  成功：  {s['success']}")
        print(f"  失败：  {s['failed']}")
        print(f"  重试中：{s['retrying']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
