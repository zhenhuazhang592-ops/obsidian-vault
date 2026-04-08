"""
kling_adapter.py — 可灵 Kling 视频生成适配器

支持：Kling O1（STD/PRO，5s/10s）、Kling v2.6-turbo
API：https://api.klingai.com
"""

import time
import hashlib
import hmac
import base64
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

from .video_adapter_base import VideoAdapterBase, AdapterConfig


class KlingAdapter(VideoAdapterBase):
    """可灵视频生成适配器"""

    provider = "kling"
    default_video_model = "kling-v1(STD)"

    # Kling 模型 ID
    MODELS = {
        "kling-o1-std-5s":  "kling-v1(STD)",  # O1 STD 5秒
        "kling-o1-std-10s": "kling-v1(STD)",  # O1 STD 10秒
        "kling-o1-pro-5s":  "kling-v1(PRO)",  # O1 PRO 5秒
        "kling-o1-pro-10s": "kling-v1(PRO)",  # O1 PRO 10秒
        "kling-v2-turbo":    "kling-v2-6(PRO)",  # v2.6 turbo
    }

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self._base_url = config.base_url or "https://api.klingai.com"
        self._key_id = config.extra.get("key_id", "")
        self._poll_interval = 3  # Kling 轮询更频繁

    # ─────────────────────────────────────────────────────────────────
    # 签名认证（Kling 专用）
    # ─────────────────────────────────────────────────────────────────

    def _sign(self, method: str, path: str, body: str, timestamp: str) -> str:
        """Kling HMAC-SHA256 签名"""
        sign_str = f"{method}\n{path}\n{timestamp}\n{body}"
        mac = hmac.new(
            self.config.api_key.encode(),
            sign_str.encode(),
            hashlib.sha256,
        )
        return base64.b64encode(mac.digest()).decode()

    def _kling_headers(self, body: str = "") -> dict:
        """构建 Kling 认证 headers"""
        timestamp = str(int(time.time()))
        path = "/v1/videos/generation"
        signature = self._sign("POST", path, body, timestamp)
        return {
            "Content-Type": "application/json",
            "Authorization": f"CK_PUBLIC {self._key_id}:{timestamp}:{signature}",
        }

    # ─────────────────────────────────────────────────────────────────
    # 视频任务
    # ─────────────────────────────────────────────────────────────────

    def _create_video_task(
        self,
        prompt: str,
        img1: Optional[str],
        img2: Optional[str],
        duration: Optional[int],
        model: Optional[str],
        references: Optional[list[dict]] = None,
    ) -> str:
        model_id = self._resolve_model(model, duration)
        dur = duration or self.config.duration

        # 解析 aspect_ratio
        ratio_map = {
            "16:9": "16:9",
            "9:16": "9:16",
            "1:1":  "1:1",
            "4:3":  "4:3",
        }
        aspect = ratio_map.get(self.config.aspect_ratio, "16:9")

        # 构建请求体（Kling 格式）
        # references 优先级高于 img1（向后兼容）
        resolved_img1 = img1
        resolved_img2 = img2
        if references:
            for ref in references:
                if ref.get("role") == "first_frame" or resolved_img1 is None:
                    resolved_img1 = ref.get("url", img1)
                if ref.get("role") == "last_frame":
                    resolved_img2 = ref.get("url", img2)

        payload: dict = {
            "model": model_id,
            "aspect_ratio": aspect,
            "duration": dur,
            "prompt": prompt,
        }

        if resolved_img1:
            payload["image_url"] = resolved_img1
        if resolved_img2:
            # Kling v2 支持尾帧图，v1 忽略
            payload["negative_prompt"] = resolved_img2

        body_str = json.dumps(payload, separators=(",", ":"))
        url = f"{self._base_url}/v1/videos/generation"
        headers = self._kling_headers(body_str)

        req = urllib.request.Request(
            url,
            data=body_str.encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                result = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code}：{e.read().decode()}")
        except Exception as e:
            raise RuntimeError(f"请求失败：{e}")

        if "data" not in result or "task_id" not in result.get("data", {}):
            raise RuntimeError(f"创建任务失败：{result}")

        return result["data"]["task_id"]

    def _resolve_model(self, model: Optional[str], duration: Optional[int]) -> str:
        """解析模型 ID"""
        if model in self.MODELS:
            return self.MODELS[model]
        if model:
            return model
        # 默认 O1 STD 5秒
        return self.default_video_model

    def _get_task_status(self, task_id: str) -> dict:
        """查询任务状态"""
        timestamp = str(int(time.time()))
        path = f"/v1/videos/generation/{task_id}"
        signature = self._sign("GET", path, "", timestamp)

        headers = {
            "Authorization": f"CK_PUBLIC {self._key_id}:{timestamp}:{signature}",
        }
        url = f"{self._base_url}{path}"
        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                result = json.loads(resp.read().decode())
        except Exception as e:
            raise RuntimeError(f"查询状态失败：{e}")

        # Kling 状态映射
        data = result.get("data", {})
        kling_status = data.get("task_status", "")

        status_map = {
            "submitted":  "pending",
            "processing": "processing",
            "succeed":    "succeeded",
            "failed":     "failed",
        }
        mapped = status_map.get(kling_status, "processing")

        out = {"status": mapped}

        if mapped == "succeeded":
            videos = data.get("videos", [])
            if videos:
                out["content"] = {"video_url": videos[0].get("url", "")}

        if mapped == "failed":
            out["error"] = data.get("status_message", "unknown")

        return out

    # ─────────────────────────────────────────────────────────────────
    # 图片（Kling 不支持，抛异常）
    # ─────────────────────────────────────────────────────────────────

    def _create_image_task(self, prompt: str, model: Optional[str]) -> str:
        raise NotImplementedError("Kling 适配器暂不支持图片生成，请使用 DoubaoAdapter")
