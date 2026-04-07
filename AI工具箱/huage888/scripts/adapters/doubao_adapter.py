"""
doubao_adapter.py — 火山引擎 Doubao 视频/图片适配器

支持：Seedance 2.0（视频）、Seedream 5.0（图片）
"""

import sys
from pathlib import Path
from typing import Optional

try:
    from openai import OpenAI as ImageClient
except ImportError:
    ImageClient = None

from .video_adapter_base import VideoAdapterBase, AdapterConfig, ImageResult


class DoubaoAdapter(VideoAdapterBase):
    """Doubao / 即梦视频生成适配器"""

    provider = "doubao"
    default_video_model = "doubao-seedance-2-0-260128"
    default_image_model = "doubao-seedream-5-0-260128"

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self._base_url = config.base_url or "https://ark.cn-beijing.volces.com/api/v3"
        self._image_client = None

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
    ) -> str:
        model = model or self.default_video_model
        dur = duration or self.config.duration

        # 构建 content
        content = [
            {
                "type": "text",
                "text": f"{prompt} --wm {'true' if self.config.watermark else 'false'} --dur {dur}"
            }
        ]
        if img1:
            content.append({"type": "image_url", "image_url": {"url": img1}})
        if img2:
            content.append({"type": "image_url", "image_url": {"url": img2}})

        payload = {"model": model, "content": content}
        url = f"{self._base_url}/content_generation/tasks"

        result = self._http_post(url, payload)
        if "id" not in result:
            raise RuntimeError(f"创建任务失败：{result}")
        return result["id"]

    def _get_task_status(self, task_id: str) -> dict:
        url = f"{self._base_url}/content_generation/tasks/{task_id}"
        return self._http_get(url)

    # ─────────────────────────────────────────────────────────────────
    # 图片任务
    # ─────────────────────────────────────────────────────────────────

    def _create_image_task(
        self,
        prompt: str,
        model: Optional[str],
    ) -> str:
        if ImageClient is None:
            raise ImportError("缺少 openai 库，请运行：pip install openai")

        model = model or self.default_image_model
        if self._image_client is None:
            self._image_client = ImageClient(
                api_key=self.config.api_key,
                base_url=self._base_url,
            )

        response = self._image_client.images.generate(
            model=model,
            prompt=prompt,
            size="2K",
            extra_body={"watermark": self.config.watermark},
        )
        return response.data[0].url

    # ─────────────────────────────────────────────────────────────────
    # 健康检查
    # ─────────────────────────────────────────────────────────────────

    def _do_health_check(self) -> bool:
        url = f"{self._base_url}/content_generation/tasks"
        payload = {
            "model": self.default_video_model,
            "content": [{"type": "text", "text": "test --wm true --dur 5"}],
        }
        try:
            result = self._http_post(url, payload)
            return "id" in result
        except Exception:
            return False
