# core/llm_client.py - 统一 LLM 客户端接口
# 解决：QwenAdapter.invoke() vs Agent期望的 .chat() 接口不兼容问题

import os
import json
import time
import threading
from typing import Protocol, Any, Optional, runtime_checkable
from pathlib import Path


@runtime_checkable
class LLMClient(Protocol):
    """LLM 客户端统一接口"""

    def chat(self, prompt: str, *, schema: Optional[dict] = None, **kwargs) -> str:
        """
        发送对话请求，返回字符串响应。

        Args:
            prompt: 用户输入的提示词
            schema: 可选，期望的 JSON schema（用于结构化输出）
            **kwargs: 其他参数（如 temperature, max_tokens）

        Returns:
            LLM 输出的字符串（调用方负责解析 JSON）
        """
        ...

    def chat_json(self, prompt: str, schema: dict, **kwargs) -> dict:
        """
        发送对话请求，直接返回解析后的 dict。

        内部自动处理 JSON 序列化/反序列化。

        Args:
            prompt: 用户输入的提示词
            schema: JSON schema（期望的响应结构）
            **kwargs: 其他参数

        Returns:
            解析后的 dict
        """
        ...


class LLMCallError(Exception):
    """LLM 调用失败"""
    pass


class RateLimitError(LLMCallError):
    """限速错误"""
    pass


class QwenLLMClient:
    """
    千问 LLM 客户端
    封装 QwenAdapter，适配 LLMClient 接口（.chat()）
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: str = "qwen-plus",
        max_retries: int = 3,
        timeout: int = 120,
    ):
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")
        self.base_url = base_url
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY not set. "
                "Set it via environment variable or pass api_key."
            )

    def chat(self, prompt: str, *, schema: Optional[dict] = None, **kwargs) -> str:
        """返回原始字符串响应"""
        result = self._call_with_retry(prompt, schema=schema, **kwargs)
        if isinstance(result, dict):
            return json.dumps(result, ensure_ascii=False)
        return str(result)

    def chat_json(self, prompt: str, schema: dict, **kwargs) -> dict:
        """返回解析后的 dict"""
        result = self._call_with_retry(prompt, schema=schema, **kwargs)
        if isinstance(result, dict):
            return result
        raise LLMCallError(f"Expected dict, got {type(result)}: {result}")

    def _call_with_retry(
        self, prompt: str, schema: Optional[dict] = None, **kwargs
    ) -> Any:
        """带重试的 LLM 调用"""
        import requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = [{"role": "user", "content": prompt}]

        payload: dict = {
            "model": self.model,
            "messages": messages,
        }

        if schema:
            payload["response_format"] = {"type": "json_object", "schema": schema}

        # 合并额外参数
        for k, v in kwargs.items():
            if k in ("temperature", "max_tokens", "top_p"):
                payload[k] = v

        last_error = None
        for attempt in range(self.max_retries):
            try:
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )

                if resp.status_code == 429:
                    # Rate limit — 指数退避
                    wait = 2 ** attempt + threading.current_thread().name.__hash__() % 5
                    time.sleep(wait)
                    last_error = RateLimitError(f"Rate limited, retry {attempt + 1}")
                    continue

                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]

                if schema:
                    return json.loads(content)
                return content

            except requests.exceptions.Timeout:
                last_error = LLMCallError(f"Timeout after {self.timeout}s")
            except requests.exceptions.HTTPError as e:
                last_error = LLMCallError(f"HTTP {e.response.status_code}: {e}")
            except json.JSONDecodeError as e:
                last_error = LLMCallError(f"JSON parse error: {e}")

            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)

        raise last_error or LLMCallError("Unknown LLM error")


class MockLLMClient:
    """
    测试用 Mock LLM 客户端
    返回预配置的响应，用于测试和无 API Key 的降级场景
    """

    def __init__(self, response: Any = None, delay: float = 0):
        self._response = response
        self._delay = delay
        self._call_count = 0
        self._calls: list[dict] = []

    def chat(self, prompt: str, *, schema: Optional[dict] = None, **kwargs) -> str:
        self._call_count += 1
        self._calls.append({"prompt": prompt, "schema": schema, "kwargs": kwargs})

        if self._delay:
            time.sleep(self._delay)

        if self._response is not None:
            if isinstance(self._response, dict):
                return json.dumps(self._response, ensure_ascii=False)
            return str(self._response)

        return '{"topic": "测试主题", "target_audience": {"persona": "测试读者"}}'

    def chat_json(self, prompt: str, schema: dict, **kwargs) -> dict:
        result = self.chat(prompt, schema=schema, **kwargs)
        if isinstance(result, dict):
            return result
        return json.loads(result)

    @property
    def call_count(self) -> int:
        return self._call_count

    def get_calls(self) -> list[dict]:
        return list(self._calls)

    def reset(self):
        self._call_count = 0
        self._calls.clear()


def create_llm_client(
    provider: str = "qwen",
    **kwargs
) -> LLMClient:
    """工厂函数：根据 provider 创建 LLM 客户端"""
    if provider == "qwen":
        return QwenLLMClient(**kwargs)
    elif provider == "mock":
        return MockLLMClient(**kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
