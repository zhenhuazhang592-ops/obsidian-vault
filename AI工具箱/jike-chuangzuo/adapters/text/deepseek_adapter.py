#!/usr/bin/env python3
"""DeepSeek Adapter —— 基于 DeepSeek API"""
import json
from .base import BaseAdapter, AdapterRegistry

logger = __import__("logging").getLogger(__name__)


class DeepSeekAdapter(BaseAdapter):
    """DeepSeek 文本推理"""

    def invoke(self, prompt: str, schema: dict | None = None, **kwargs) -> dict:
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

        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"text": content}


AdapterRegistry.register("deepseek", DeepSeekAdapter)
