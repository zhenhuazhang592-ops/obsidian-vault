"""
Dify API Client
Dify Chatflow 集成客户端
"""
import asyncio
import httpx
import logging
import time
from typing import Optional, AsyncIterator
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DifyConfig:
    """Dify API 配置"""
    api_key: str
    base_url: str = "https://api.dify.ai/v1"
    timeout: float = 60.0
    max_retries: int = 3
    retry_base_delay: float = 1.0  # seconds


@dataclass
class DifyMetrics:
    """Dify API 指标（内存计数器，可导出到 Prometheus）"""
    requests_total: int = 0
    requests_success: int = 0
    requests_error: int = 0
    requests_retry: int = 0
    hitl_triggered: int = 0
    last_request_at: Optional[float] = None

    # 分 method 计数
    method_counts: dict[str, int] = field(default_factory=dict)

    def reset(self):
        self.requests_total = 0
        self.requests_success = 0
        self.requests_error = 0
        self.requests_retry = 0
        self.hitl_triggered = 0
        self.last_request_at = None
        self.method_counts.clear()

    def to_dict(self) -> dict:
        return {
            "requests_total": self.requests_total,
            "requests_success": self.requests_success,
            "requests_error": self.requests_error,
            "requests_retry": self.requests_retry,
            "hitl_triggered": self.hitl_triggered,
            "last_request_at": self.last_request_at,
            "method_counts": dict(self.method_counts),
        }


class DifyClient:
    """
    Dify API 客户端

    支持：
    - 创建 Chatflow 会话（streaming / blocking）
    - SSE 流式响应
    - HITL 恢复（通过 task_id）
    - 会话历史查询
    - 429 指数退避重试
    - 结构化日志
    - 请求指标
    """

    def __init__(self, config: DifyConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self.metrics = DifyMetrics()

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

    def _log(self, level: str, method: str, path: str, **kwargs):
        """Structured log helper"""
        extra = {"method": method, "path": path, **kwargs}
        getattr(logger, level)(
            "[%s] %s %s — %s",
            method,
            path,
            " | ".join(f"{k}={v}" for k, v in kwargs.items()),
            " | ".join(f"{k}={v}" for k, v in extra.items()),
        )

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> httpx.Response:
        """
        发送 HTTP 请求，带 429 指数退避重试

        Args:
            method: GET / POST
            path: API 路径
            **kwargs: 传递给 httpx 请求的参数

        Returns:
            httpx.Response

        Raises:
            DifyClientError: 所有重试失败后
        """
        client = await self._get_client()
        last_exc: Optional[Exception] = None

        for attempt in range(self.config.max_retries):
            try:
                self.metrics.last_request_at = time.time()
                self.metrics.requests_total += 1
                self.metrics.method_counts[method] = \
                    self.metrics.method_counts.get(method, 0) + 1

                self._log("info", method, path, attempt=attempt)

                response = await client.request(method, path, **kwargs)

                if response.status_code == 429:
                    # Rate limit — 指数退避
                    self.metrics.requests_retry += 1
                    retry_after = float(
                        response.headers.get("Retry-After", self.config.retry_base_delay * (2 ** attempt))
                    )
                    logger.warning(
                        "[%s] %s — rate limited, retry after %.1fs (attempt %d/%d)",
                        method, path, retry_after, attempt + 1, self.config.max_retries,
                    )
                    await asyncio.sleep(retry_after)
                    continue

                response.raise_for_status()
                self.metrics.requests_success += 1
                self._log("info", method, path, status=response.status_code, attempt=attempt)
                return response

            except httpx.HTTPStatusError as e:
                last_exc = e
                if e.response.status_code in (429, 500, 502, 503, 504):
                    self.metrics.requests_retry += 1
                    delay = self.config.retry_base_delay * (2 ** attempt)
                    logger.warning(
                        "[%s] %s — HTTP %d, retry in %.1fs (attempt %d/%d)",
                        method, path, e.response.status_code, delay, attempt + 1, self.config.max_retries,
                    )
                    await asyncio.sleep(delay)
                    continue
                # 其他 HTTP 错误不重试
                self.metrics.requests_error += 1
                self._log("error", method, path, status=e.response.status_code, exc=str(e))
                raise DifyClientError(f"HTTP {e.response.status_code}: {path}") from e

            except httpx.RequestError as e:
                last_exc = e
                self.metrics.requests_error += 1
                self._log("error", method, path, exc=str(e))
                raise DifyClientError(f"Request error: {path}") from e

        # 所有重试耗尽
        self.metrics.requests_error += 1
        self._log("error", method, path, exc="max retries exceeded")
        raise DifyClientError(f"Max retries exceeded for {method} {path}") from last_exc

    async def create_chatflow_session(
        self,
        chatflow_id: str,
        user_id: str,
        query: Optional[str] = None,
        inputs: Optional[dict] = None,
    ) -> dict:
        """
        创建 Chatflow 会话（blocking 模式）

        Args:
            chatflow_id: Chatflow ID
            user_id: 用户 ID
            query: 初始查询
            inputs: 输入变量

        Returns:
            包含 conversation_id, task_id, message_id 等信息
        """
        payload = {
            "chatflow_id": chatflow_id,
            "user": user_id,
        }
        if query:
            payload["query"] = query
        if inputs:
            payload["inputs"] = inputs

        response = await self._request_with_retry(
            "POST",
            "/chat-messages",
            json=payload,
        )
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

        self.metrics.last_request_at = time.time()
        self.metrics.requests_total += 1
        self.metrics.method_counts["POST"] = \
            self.metrics.method_counts.get("POST", 0) + 1

        try:
            async with client.stream("POST", "/chat-messages", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data:
                            yield data
        except httpx.HTTPStatusError as e:
            self.metrics.requests_error += 1
            self._log("error", "POST", "/chat-messages", exc=str(e))
            raise DifyClientError(f"Stream error: HTTP {e.response.status_code}") from e

    async def resume_from_hitl(
        self,
        task_id: str,
        action: str = "approve",
        data: Optional[dict] = None,
        user: Optional[str] = None,
    ) -> dict:
        """
        从 HITL 节点恢复（发送人工响应）

        Dify Chatflow 在 HITL 节点暂停时，调用此方法恢复执行。

        Args:
            task_id: Dify 返回的 task_id
            action: 用户操作 ("approve" 或 "reject")
            data: 额外数据（human_feedback 内容）
            user: 用户标识

        Returns:
            后续响应
        """
        payload: dict = {
            "task_id": task_id,
            "action": action,
        }
        if data:
            payload["data"] = data
        if user:
            payload["user"] = user

        self.metrics.hitl_triggered += 1
        response = await self._request_with_retry(
            "POST",
            "/resume",
            json=payload,
        )
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
        response = await self._request_with_retry(
            "GET",
            f"/conversations/{conversation_id}/messages",
            params={"user": user_id, "limit": limit},
        )
        data = response.json()
        return data.get("data", [])


class DifyClientError(Exception):
    """Dify API 错误"""
    pass
