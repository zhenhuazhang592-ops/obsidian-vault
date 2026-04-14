# MessageHub - 消息中枢
# 单例模式，所有Agent之间的消息流转都通过Hub
# 线程安全：每个session有独立的锁保护

import json
import time
import threading
from pathlib import Path
from typing import Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum


class MessageType(Enum):
    PLAN = "plan"          # 主题策划输出
    RESEARCH = "research"  # 深度研究输出
    STYLE = "style"        # 风格学习输出
    OUTLINE = "outline"    # 大纲规划输出
    DRAFT = "draft"         # 内容写作输出
    POLISHED = "polished"   # 润色优化输出
    REVIEW = "review"       # 质量审查输出
    IMAGE = "image"         # 配图封面输出
    FORMATTED = "formatted" # 排版输出
    ERROR = "error"
    STATUS = "status"


@dataclass
class Message:
    """消息单元"""
    type: MessageType
    agent: str
    content: Any
    timestamp: float = field(default_factory=time.time)
    session_id: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d['type'] = self.type.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> 'Message':
        d['type'] = MessageType(d['type'])
        return cls(**d)


class MessageHub:
    """消息中枢 - 线程安全单例"""

    _instance = None
    _init_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._init_lock:
                # Double-checked locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        # 核心数据结构
        self._messages: list[Message] = []
        self._session_id: str = ""
        self._listeners: dict[MessageType, list[Callable]] = {}
        # Session 级别的锁，保护 session 切换时的状态隔离
        self._session_lock = threading.Lock()
        # 发布锁，保护消息列表的并发访问
        self._publish_lock = threading.Lock()

    def set_session(self, session_id: str):
        """设置当前 session（线程安全）"""
        with self._session_lock:
            self._session_id = session_id
            self._messages = []

    def publish(self, msg: Message):
        """发布消息（线程安全）"""
        with self._publish_lock:
            if not msg.session_id:
                with self._session_lock:
                    msg.session_id = self._session_id
            self._messages.append(msg)

            # 通知监听器（在锁内调用，避免竞态）
            msg_type = msg.type
            if msg_type in self._listeners:
                for callback in self._listeners[msg_type]:
                    try:
                        callback(msg)
                    except Exception:
                        pass  # 不让监听器异常中断消息发布

    def subscribe(self, msg_type: MessageType, callback: Callable):
        """订阅消息类型"""
        if msg_type not in self._listeners:
            self._listeners[msg_type] = []
        self._listeners[msg_type].append(callback)

    def unsubscribe(self, msg_type: MessageType, callback: Callable):
        """取消订阅"""
        if msg_type in self._listeners:
            try:
                self._listeners[msg_type].remove(callback)
            except ValueError:
                pass

    def get_messages(self, msg_type: MessageType = None, agent: str = None) -> list[Message]:
        """查询消息（线程安全）"""
        with self._publish_lock:
            results = list(self._messages)

        if msg_type:
            results = [m for m in results if m.type == msg_type]
        if agent:
            results = [m for m in results if m.agent == agent]
        return results

    def get_latest(self, msg_type: MessageType = None) -> Message | None:
        """获取最新消息"""
        msgs = self.get_messages(msg_type)
        return msgs[-1] if msgs else None

    def get_session_history(self) -> list[Message]:
        """获取当前 session 的完整消息历史"""
        with self._publish_lock:
            return list(self._messages)

    def export_json(self, path: Path):
        """导出消息历史为 JSON"""
        with self._publish_lock:
            data = [m.to_dict() for m in self._messages]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def get_status(self) -> dict:
        """获取当前流水线状态"""
        with self._publish_lock:
            messages_snapshot = list(self._messages)

        status = {}
        for msg_type in MessageType:
            msgs = [m for m in messages_snapshot if m.type == msg_type]
            if msgs:
                latest = msgs[-1]
                status[msg_type.value] = {
                    "agent": latest.agent,
                    "timestamp": latest.timestamp,
                    "has_content": latest.content is not None
                }
        return status

    def clear(self):
        """清空所有消息（主要用于测试）"""
        with self._publish_lock:
            self._messages.clear()
