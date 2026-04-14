"""
Mock Dify API Server
用于 Day 1-2 无需真实 Dify 账号的本地测试
"""
import asyncio
import json
import time
import random
import hashlib
from typing import Optional


class MockDifySSEGenerator:
    """Mock SSE 流式响应生成器"""

    def __init__(self, task_id: str, conversation_id: str, user_response: str = ""):
        self.task_id = task_id
        self.conversation_id = conversation_id
        self.user_response = user_response
        self.hitl_triggered = False
        self._stream_delay = 0.05  # 50ms between events

    async def generate_events(self):
        """生成 SSE 事件流"""
        # 事件1: message
        yield self._make_event("message", {
            "task_id": self.task_id,
            "conversation_id": self.conversation_id,
            "message_id": f"msg_{self.task_id}",
            "answer": "",
            "created_at": int(time.time()),
        })
        await asyncio.sleep(self._stream_delay)

        # 检查是否触发 HITL（用户响应为 "hitl" 时触发）
        if self.user_response.lower() == "hitl":
            self.hitl_triggered = True
            yield self._make_event("message", {
                "task_id": self.task_id,
                "conversation_id": self.conversation_id,
                "message_id": f"msg_{self.task_id}",
                "answer": "等待人工确认...",
                "created_at": int(time.time()),
            })
            await asyncio.sleep(self._stream_delay)
            yield self._make_event("hitl_message", {
                "task_id": self.task_id,
                "conversation_id": self.conversation_id,
                "message_id": f"msg_{self.task_id}_hitl",
                "answer": json.dumps({
                    "hitl_type": "strategy",
                    "node_id": "hitl_strategy",
                    "message": "请确认创作策略",
                }),
                "created_at": int(time.time()),
            })
            yield self._make_event("message_end", {
                "task_id": self.task_id,
                "conversation_id": self.conversation_id,
                "created_at": int(time.time()),
            })
            return

        # 正常响应
        answers = [
            "我理解了，让我们开始创作。",
            "好的，我将为您撰写这篇公众号文章。",
            "收到，让我为您进行深度研究。",
        ]
        answer = random.choice(answers)

        # 分段输出模拟 token
        for i in range(0, len(answer), 10):
            chunk = answer[i:i+10]
            yield self._make_event("message", {
                "task_id": self.task_id,
                "conversation_id": self.conversation_id,
                "message_id": f"msg_{self.task_id}",
                "answer": chunk,
                "created_at": int(time.time()),
            })
            await asyncio.sleep(self._stream_delay)

        # 结束
        yield self._make_event("message_end", {
            "task_id": self.task_id,
            "conversation_id": self.conversation_id,
            "created_at": int(time.time()),
        })

    def _make_event(self, event_type: str, data: dict) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


class MockDifyServer:
    """
    Mock Dify API Server

    模拟 Dify Chatflow API 的关键端点：
    - POST /v1/chat-messages
    - POST /v1/hitl/resume
    - GET  /v1/conversations/{id}/messages
    """

    def __init__(self):
        self._conversations: dict[str, list[dict]] = {}
        self._tasks: dict[str, dict] = {}
        self._hitl_pending: dict[str, dict] = {}
        self._default_response_mode = "blocking"

    async def chat_messages(
        self,
        chatflow_id: str,
        query: str,
        user: str,
        conversation_id: Optional[str] = None,
        response_mode: str = "streaming",
        inputs: Optional[dict] = None,
    ) -> tuple[dict, str]:
        """
        模拟 POST /v1/chat-messages

        Returns:
            (headers dict, response_body or SSE_generator)
        """
        task_id = f"task_{hashlib.md5(f'{user}{time.time()}'.encode()).hexdigest()[:8]}"
        conv_id = conversation_id or f"conv_{hashlib.md5(user.encode()).hexdigest()[:8]}"

        # 存储任务
        self._tasks[task_id] = {
            "chatflow_id": chatflow_id,
            "query": query,
            "user": user,
            "conversation_id": conv_id,
            "status": "running",
            "inputs": inputs or {},
        }

        # 存储对话
        if conv_id not in self._conversations:
            self._conversations[conv_id] = []
        self._conversations[conv_id].append({
            "message_id": f"msg_{task_id}",
            "task_id": task_id,
            "query": query,
            "answer": "",
            "created_at": int(time.time()),
        })

        headers = {
            "Content-Type": "application/json",
            "X-Task-ID": task_id,
            "X-Conversation-ID": conv_id,
        }

        if response_mode == "streaming":
            return headers, MockDifySSEGenerator(
                task_id=task_id,
                conversation_id=conv_id,
                user_response=query,
            )
        else:
            # blocking 模式
            return headers, {
                "task_id": task_id,
                "conversation_id": conv_id,
                "message_id": f"msg_{task_id}",
                "answer": "这是模拟的 Dify 响应。",
                "created_at": int(time.time()),
            }

    async def resume(
        self,
        task_id: str,
        action: str,
        data: Optional[dict] = None,
        user: Optional[str] = None,
    ) -> dict:
        """
        模拟 POST /v1/resume (HITL 恢复)
        """
        task = self._tasks.get(task_id, {})
        conv_id = task.get("conversation_id", "conv_unknown")

        return {
            "task_id": task_id,
            "conversation_id": conv_id,
            "message_id": f"msg_{task_id}_resume",
            "answer": f"已处理您的{'批准' if action == 'approve' else '拒绝'}操作。",
            "created_at": int(time.time()),
        }

    async def get_conversation_messages(
        self,
        conversation_id: str,
        user: str,
        limit: int = 20,
    ) -> tuple[dict, dict]:
        """模拟 GET /v1/conversations/{id}/messages"""
        messages = self._conversations.get(conversation_id, [])
        headers = {"Content-Type": "application/json"}
        return headers, {"data": messages[-limit:]}


# 全局单例
_mock_server: Optional[MockDifyServer] = None


def get_mock_server() -> MockDifyServer:
    global _mock_server
    if _mock_server is None:
        _mock_server = MockDifyServer()
    return _mock_server


def reset_mock_server():
    """重置 Mock 服务器状态（用于测试隔离）"""
    global _mock_server
    _mock_server = None
