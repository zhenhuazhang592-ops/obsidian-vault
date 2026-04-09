"""
gemini_veo_adapter.py — Gemini Veo 视频生成适配器（Stub）

支持：Gemini Veo 3 / Veo 3.1
API 端点：Google AI Studio（需 ai.google.dev API Key）
环境变量：GEMINI_API_KEY

当前状态：框架骨架，API 调用部分需补充文档后实现。
Gemini Veo 通过 Vertex AI 或 Google AI Studio 的 OpenAI-compatible API 访问。
"""

import time
import json
from pathlib import Path
from typing import Optional

from .video_adapter_base import VideoAdapterBase, AdapterConfig


class GeminiVeoAdapter(VideoAdapterBase):
    """
    Gemini Veo 视频生成适配器

    支持模型：
      - veo-3.1-generate-preview  T2V+I2V 有声 4-8s，720p/1080p，多生成类型
      - veo-3.0-generate-preview  T2V+I2V 有声 4-8s，720p/1080p
    """

    provider = "gemini"
    default_video_model = "veo-3.1-generate-preview"

    MODELS = {
        "veo-3.1-generate-preview": "veo-3.1-generate-preview",
        "veo-3.0-generate-preview": "veo-3.0-generate-preview",
    }

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        # Gemini OpenAI-compatible endpoint
        self._base_url = config.base_url or "https://generativelanguage.googleapis.com/v1beta"
        self._poll_interval = 5

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
        """创建 Gemini Veo 视频任务"""
        model_id = model or self.default_video_model
        dur = duration or self.config.duration
        api_model = model_id if model_id in self.MODELS else "veo-3.1-generate-preview"

        # Veo 支持多参考图模式（reference_image）
        contents = [{"type": "text", "text": prompt}]

        # I2V：加入首帧参考图
        ref_url = img1
        if not ref_url and references:
            for ref in references:
                if ref.get("role") in ("first_frame", "reference_image"):
                    ref_url = ref.get("url", "")
                    break

        if ref_url:
            contents.append({
                "type": "image_url",
                "image_url": {"url": ref_url},
            })

        # Gemini 使用 requests 格式（与 OpenAI 不同）
        body = {
            "model": api_model,
            "contents": contents,
            "video_duration": dur,
            "aspect_ratio": self.config.aspect_ratio,
        }

        # Google AI Studio endpoint
        resp = self._http_post(
            f"https://aiplatform.googleapis.com/v1/projects/*/locations/*/publishers/google/"
            f"models/{api_model}:predict",
            body,
        )
        task_id = (
            resp.get("task_id")
            or resp.get("name")
            or resp.get("predictions", [{}])[0].get("task_id", "")
        )
        if not task_id:
            raise RuntimeError(f"Gemini Veo 创建任务失败：{resp}")
        return task_id

    def _create_image_task(
        self,
        prompt: str,
        model: Optional[str],
    ) -> str:
        """Gemini 图片生成（使用 Imagen）"""
        raise NotImplementedError(
            "Gemini Veo 适配器不支持图片生成，图片请使用 DoubaoAdapter"
        )

    def _get_task_status(self, task_id: str) -> dict:
        """查询 Gemini Veo 任务状态"""
        resp = self._http_get(
            f"https://aiplatform.googleapis.com/v1/{task_id}"
        )
        data = resp if isinstance(resp, dict) else {}
        raw = data.get("state", data.get("status", "unknown"))
        status_map = {
            "STATE_UNSPECIFIED": "pending",
            "PENDING": "pending",
            "RUNNING": "processing",
            "SUCCEEDED": "succeeded",
            "FAILED": "failed",
            "CANCELLED": "failed",
        }
        video_url = ""
        predictions = data.get("predictions", [])
        if predictions:
            video_url = predictions[0].get("bytesBase64Encoded", "")
        return {
            "status": status_map.get(raw, raw),
            "video_url": video_url,
            "duration": self.config.duration,
        }

    def _do_health_check(self) -> bool:
        """健康检查"""
        try:
            resp = self._http_get(
                "https://generativelanguage.googleapis.com/v1beta/models?key="
                f"{self.config.api_key}"
            )
            return resp is not None
        except Exception:
            return False
