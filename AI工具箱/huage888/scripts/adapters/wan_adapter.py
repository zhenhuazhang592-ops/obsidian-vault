"""
wan_adapter.py — 万象 Wan 视频生成适配器（Stub）

支持：Wan 2.6-t2v / Wan 2.6-i2v-flash / Wan 2.6-i2v
API 端点：待获取（需火山引擎 Ark 订阅）
环境变量：WAN_API_KEY

当前状态：框架骨架，API 调用部分需补充文档后实现。
"""

import time
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

from .video_adapter_base import VideoAdapterBase, AdapterConfig


class WanAdapter(VideoAdapterBase):
    """
    万象 Wan 视频生成适配器

    支持模型：
      - wan2.6-t2v      T2V 有声 2-15s
      - wan2.6-i2v      I2V 有声 2-15s
      - wan2.6-i2v-flash I2V 有声快速版 2-15s
    """

    provider = "wan"
    default_video_model = "wan2.6-t2v"

    # model_id 映射
    MODELS = {
        "wan2.6-t2v":       "wan2.6-t2v",
        "wan2.6-i2v-flash": "wan2.6-i2v-flash",
        "wan2.6-i2v":       "wan2.6-i2v",
    }

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self._base_url = config.base_url or "https://visual.volcengineapi.com"
        # Wan 2.6 可能走 Ark 端点
        if not config.base_url:
            self._base_url = "https://ark.cn-beijing.volces.com/api/v3"
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
        """创建 Wan 视频任务"""
        model_id = model or self.default_video_model
        dur = duration or self.config.duration

        # I2V：使用第一个参考图
        is_i2v = img1 or (references and len(references) > 0)
        api_model = model_id if model_id in self.MODELS else "wan2.6-t2v"

        body = {
            "model": api_model,
            "duration": dur,
            "aspect_ratio": self.config.aspect_ratio,
            "prompt": prompt,
        }
        if is_i2v and references:
            ref = references[0]
            body["image_url"] = ref.get("url", img1 or "")

        resp = self._http_post(f"{self._base_url}/v1/videos/generation", body)
        task_id = resp.get("task_id") or resp.get("data", {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"Wan 创建任务失败：{resp}")
        return task_id

    def _create_image_task(
        self,
        prompt: str,
        model: Optional[str],
    ) -> str:
        """Wan 不支持独立图片生成（使用 Doubao）"""
        raise NotImplementedError("Wan 适配器暂不支持独立图片生成，请使用 DoubaoAdapter")

    def _get_task_status(self, task_id: str) -> dict:
        """查询 Wan 任务状态"""
        resp = self._http_get(f"{self._base_url}/v1/videos/generation/{task_id}")
        data = resp.get("data", {})
        status_map = {
            "submitted": "pending",
            "processing": "processing",
            "succeed": "succeeded",
            "failed": "failed",
        }
        raw_status = data.get("status", "unknown")
        return {
            "status": status_map.get(raw_status, raw_status),
            "video_url": data.get("video_url", ""),
            "duration": data.get("duration", self.config.duration),
        }

    def _do_health_check(self) -> bool:
        """健康检查"""
        try:
            resp = self._http_get(f"{self._base_url}/v1/videos/models")
            return resp is not None
        except Exception:
            return False
