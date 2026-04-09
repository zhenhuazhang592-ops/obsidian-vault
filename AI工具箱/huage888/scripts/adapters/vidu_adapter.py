"""
vidu_adapter.py — Vidu 视频生成适配器（Stub）

支持：Vidu Q3-pro / Vidu 2.0
API 端点：https://api.vidu.cn（需 platform.vidu.cn 注册获取 API Key）
环境变量：VIDU_API_KEY

当前状态：框架骨架，API 调用部分需补充文档后实现。
"""

import time
import json
from pathlib import Path
from typing import Optional

from .video_adapter_base import VideoAdapterBase, AdapterConfig


class ViduAdapter(VideoAdapterBase):
    """
    Vidu 视频生成适配器

    支持模型：
      - viduq3-pro  I2V 有声 1-16s，540p-1080p（长时长首选）
      - vidu2.0    I2V 无声 4-8s，支持 reference（多参考图）
    """

    provider = "vidu"
    default_video_model = "viduq3-pro"

    MODELS = {
        "viduq3-pro": "viduq3-pro",
        "vidu2.0":    "vidu2.0",
    }

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self._base_url = config.base_url or "https://api.vidu.cn"
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
        """创建 Vidu 视频任务（仅 I2V）"""
        model_id = model or self.default_video_model
        dur = duration or self.config.duration
        api_model = model_id if model_id in self.MODELS else "viduq3-pro"

        # Vidu 仅支持 I2V，首图参考
        ref_url = img1
        if not ref_url and references:
            ref_url = references[0].get("url", "")

        body = {
            "model": api_model,
            "duration": dur,
            "image_url": ref_url,
            "prompt": prompt,
        }
        if img2:
            body["end_image_url"] = img2

        resp = self._http_post(f"{self._base_url}/v1/video/generate", body)
        task_id = resp.get("task_id") or resp.get("data", {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"Vidu 创建任务失败：{resp}")
        return task_id

    def _create_image_task(
        self,
        prompt: str,
        model: Optional[str],
    ) -> str:
        """Vidu 不支持独立图片生成"""
        raise NotImplementedError("Vidu 适配器暂不支持图片生成，请使用 DoubaoAdapter")

    def _get_task_status(self, task_id: str) -> dict:
        """查询 Vidu 任务状态"""
        resp = self._http_get(f"{self._base_url}/v1/video/generate/{task_id}")
        data = resp.get("data", {})
        raw = data.get("status", "unknown")
        status_map = {
            "pending": "pending",
            "processing": "processing",
            "succeed": "succeeded",
            "failed": "failed",
        }
        return {
            "status": status_map.get(raw, raw),
            "video_url": data.get("video_url", ""),
            "duration": data.get("duration", self.config.duration),
        }

    def _do_health_check(self) -> bool:
        try:
            resp = self._http_get(f"{self._base_url}/v1/models")
            return resp is not None
        except Exception:
            return False
