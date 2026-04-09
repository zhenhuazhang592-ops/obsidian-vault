#!/usr/bin/env python3
"""Seedance Adapter —— 即梦 Seedance 2.0 视频生成（占位实现）

TODO: 华哥提供 Seedance 2.0 SDK 文档后，替换为真实 API 调用。
当前为 mock 模式，mock=True。
"""
import time, logging
from ..base import BaseAdapter, AdapterRegistry

logger = logging.getLogger(__name__)


class SeedanceAdapter(BaseAdapter):
    """即梦 Seedance 2.0 视频生成"""

    def invoke(
        self,
        prompt: str,
        schema: dict | None = None,
        reference_image: str | None = None,
        duration: int = 4,
        resolution: str = "720p",
        **kwargs,
    ) -> dict:
        """
        调用 Seedance 2.0 API。
        华哥提供 SDK 文档后，替换为真实 API 调用。
        """
        task_id = f"mock-seedance-{int(time.time())}"

        logger.info(
            f"[Seedance] Mock generate: prompt={prompt[:50]!r}... "
            f"task_id={task_id} duration={duration}s"
        )
        return {
            "status": "pending",
            "task_id": task_id,
            "prompt": prompt,
            "reference_image": reference_image,
            "duration": duration,
            "resolution": resolution,
            "mock": True,
        }

    def poll(self, task_id: str) -> dict:
        """
        轮询任务状态。
        mock 模式：直接返回成功。
        """
        logger.info(f"[Seedance] Poll: {task_id}")
        return {
            "status": "success",
            "video_url": f"mock://seedance/{task_id}.mp4",
            "mock": True,
        }


AdapterRegistry.register("seedance", SeedanceAdapter)
