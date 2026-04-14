"""
Dify API Client
Dify Chatflow 集成客户端
"""
import httpx
import logging
from typing import Optional, AsyncIterator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DifyConfig:
    """Dify API 配置"""
    api_key: str
    base_url: str = "https://api.dify.ai/v1"
    timeout: float = 60.0


class DifyClient:
    """
    Dify API 客户端

    支持：
    - 创建 Chatflow 会话
    - 发送消息
    - 获取 HITL 状态
    - SSE 流式响应
    """

    def __init__(self, config: DifyConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.config.timeout,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def create_chatflow_session(
        self,
        chatflow_id: str,
        user_id: str,
        query: Optional[str] = None,
        inputs: Optional[dict] = None,
    ) -> dict:
        """
        创建 Chatflow 会话

        Args:
            chatflow_id: Chatflow ID
            user_id: 用户 ID
            query: 初始查询
            inputs: 输入变量

        Returns:
            包含 session_id 等信息
        """
        client = await self._get_client()

        payload = {
            "chatflow_id": chatflow_id,
            "user": user_id,
        }
        if query:
            payload["query"] = query
        if inputs:
            payload["inputs"] = inputs

        response = await client.post("/chat-messages", json=payload)
        response.raise_for_status()
        return response.json()

    async def send_message(
        self,
        session_id: str,
        message: str,
        conversation_id: Optional[str] = None,
    ) -> dict:
        """
        发送消息到现有会话

        Args:
            session_id: 会话 ID
            message: 消息内容
            conversation_id: 对话 ID

        Returns:
            响应数据
        """
        client = await self._get_client()

        payload = {
            "session_id": session_id,
            "message": message,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        response = await client.post("/messages", json=payload)
        response.raise_for_status()
        return response.json()

    async def send_message_stream(
        self,
        chatflow_id: str,
        user_id: str,
        query: str,
        inputs: Optional[dict] = None,
    ) -> AsyncIterator[dict]:
        """
        发送消息并获取 SSE 流式响应

        Args:
            chatflow_id: Chatflow ID
            user_id: 用户 ID
            query: 查询内容
            inputs: 输入变量

        Yields:
            流式响应事件
        """
        client = await self._get_client()

        payload = {
            "chatflow_id": chatflow_id,
            "user": user_id,
            "query": query,
            "response_mode": "streaming",
        }
        if inputs:
            payload["inputs"] = inputs

        async with client.stream("POST", "/chat-messages", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data:
                        yield data

    async def get_hitl_status(self, session_id: str) -> dict:
        """
        获取 HITL 节点状态

        Args:
            session_id: 会话 ID

        Returns:
            HITL 状态信息
        """
        client = await self._get_client()
        response = await client.get(f"/hitl/status/{session_id}")
        response.raise_for_status()
        return response.json()

    async def resume_from_hitl(
        self,
        session_id: str,
        action: str,
        data: Optional[dict] = None,
    ) -> dict:
        """
        从 HITL 节点恢复

        Args:
            session_id: 会话 ID
            action: 用户操作 (approved/modify)
            data: 额外数据

        Returns:
            后续响应
        """
        client = await self._get_client()

        payload = {
            "session_id": session_id,
            "action": action,
        }
        if data:
            payload["data"] = data

        response = await client.post("/hitl/resume", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 20,
    ) -> list[dict]:
        """
        获取会话消息历史

        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID
            limit: 返回消息数量

        Returns:
            消息列表
        """
        client = await self._get_client()
        response = await client.get(
            f"/conversations/{conversation_id}/messages",
            params={"user": user_id, "limit": limit},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])


class DifyClientError(Exception):
    """Dify API 错误"""
    pass
