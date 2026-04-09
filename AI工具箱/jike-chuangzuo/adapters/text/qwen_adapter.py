#!/usr/bin/env python3
"""千问 Adapter —— 基于 DashScope API"""
import json
from ..base import BaseAdapter, AdapterRegistry

logger = __import__("logging").getLogger(__name__)


class QwenAdapter(BaseAdapter):
    """通义千问文本推理"""

    def invoke(self, prompt: str, schema: dict | None = None, **kwargs) -> dict:
        """调用 DashScope /v1/chat/completions"""
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

    def stream(self, prompt: str, schema: dict | None = None, **kwargs) -> dict:
        import requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }

        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()

        full = ""
        for line in resp.iter_lines():
            if line:
                text = line.decode()
                if text.startswith("data: "):
                    if text[6:].strip() == "[DONE]":
                        break
                    chunk = json.loads(text[6:])
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    full += delta
                    yield {"type": "stream", "token": delta}

        try:
            yield {"type": "done", "result": json.loads(full)}
        except json.JSONDecodeError:
            yield {"type": "done", "result": {"text": full}}


AdapterRegistry.register("qwen", QwenAdapter)
