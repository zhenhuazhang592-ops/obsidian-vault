#!/usr/bin/env python3
"""Seedream Adapter —— 即梦图像生成（占位实现）

TODO: 华哥提供 Seedream SDK 文档后，替换 invoke() 和 poll() 为真实 API 调用。
当前为 mock 模式，mock=True。
"""
import json, time, logging
from ..base import BaseAdapter, AdapterRegistry

logger = logging.getLogger(__name__)


class SeedreamAdapter(BaseAdapter):
    """即梦 Seedream 图像生成"""

    def invoke(
        self,
        prompt: str,
        schema: dict | None = None,
        reference_image: str | None = None,
        aspect_ratio: str = "16:9",
        **kwargs,
    ) -> dict:
        """
        调用 Seedream API。
        华哥提供 SDK 文档后，替换为真实 API 调用。
        目前返回占位结构。
        """
        task_id = f"mock-seedream-{int(time.time())}"

        logger.info(
            f"[Seedream] Mock generate: prompt={prompt[:50]!r}... "
            f"task_id={task_id} aspect_ratio={aspect_ratio}"
        )
        return {
            "status": "pending",
            "task_id": task_id,
            "prompt": prompt,
            "reference_image": reference_image,
            "aspect_ratio": aspect_ratio,
            "mock": True,
        }

    def poll(self, task_id: str) -> dict:
        """
        轮询任务状态。
        华哥提供 SDK 后实现真实轮询逻辑。
        mock 模式：直接返回成功。
        """
        logger.info(f"[Seedream] Poll: {task_id}")
        return {
            "status": "success",
            "image_url": f"mock://seedream/{task_id}.png",
            "mock": True,
        }


AdapterRegistry.register("seedream", SeedreamAdapter)
