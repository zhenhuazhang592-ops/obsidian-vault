#!/usr/bin/env python3
"""
Agent 子进程基类。
每个 Agent 运行在独立子进程中，通过 stdin/stdout JSON 流与主进程通信。

协议：
  主进程 → Agent:  {"action": "xxx", "params": {...}}
  Agent → 主进程:  {"type": "stream", "token": "..."}
                   {"type": "tool_call", "tool": "...", "args": {...}}
                   {"type": "done", "result": {...}}
                   {"type": "error", "message": "..."}
"""
import json, sys, logging
from abc import ABC, abstractmethod
from typing import Any

logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")
logger = logging.getLogger("agent")


class BaseAgent(ABC):
    """所有 Agent 的基类（子进程模式）"""

    name: str = "base_agent"

    def __init__(self):
        self._history: list[dict] = []
        self._running = True

    # ── 子类必须实现 ───────────────────────────────────────

    @abstractmethod
    def handle_action(self, action: str, params: dict) -> Any:
        """处理主进程发来的 action，返回结果"""
        ...

    # ── 协议接口 ───────────────────────────────────────────

    def send(self, msg: dict):
        """发送 JSON 消息到主进程"""
        print(json.dumps(msg, ensure_ascii=False), flush=True)

    def send_stream(self, token: str):
        self.send({"type": "stream", "token": token})

    def send_tool_call(self, tool: str, args: dict):
        self.send({"type": "tool_call", "tool": tool, "args": args})

    def send_done(self, result: Any):
        self.send({"type": "done", "result": result})

    def send_error(self, message: str):
        self.send({"type": "error", "message": message})

    # ── 运行循环 ───────────────────────────────────────────

    def run(self):
        """读取 stdin 的 JSON 命令，执行并返回结果"""
        logger.info(f"[{self.name}] Agent started")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                action = msg.get("action")
                params = msg.get("params", {})
                logger.info(f"[{self.name}] Action: {action}")

                try:
                    result = self.handle_action(action, params)
                    self.send_done(result)
                except Exception as e:
                    self.send_error(str(e))

            except json.JSONDecodeError:
                self.send_error(f"Invalid JSON: {line[:100]}")

    def add_history(self, role: str, content: str):
        self._history.append({"role": role, "content": content})

    def get_history(self) -> list[dict]:
        return self._history[-20:]


class ToolRegistry:
    """Agent 可调用的工具集"""

    def __init__(self):
        self._tools: dict[str, callable] = {}

    def register(self, name: str, fn: callable):
        self._tools[name] = fn

    def call(self, name: str, **kwargs) -> Any:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return self._tools[name](**kwargs)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())
