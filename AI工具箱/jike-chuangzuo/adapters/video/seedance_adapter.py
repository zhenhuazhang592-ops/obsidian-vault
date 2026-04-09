#!/usr/bin/env python3
"""Seedance Adapter —— 即梦 Seedance 2.0 视频生成（Volcengine Ark SDK）

依赖: pip install 'volcengine-python-sdk[ark]'
环境变量: ARK_API_KEY
视频生成是异步任务：invoke() 创建任务返回 task_id，poll() 轮询状态。
"""
import os, time, logging
from adapters.base import BaseAdapter, AdapterRegistry

logger = logging.getLogger(__name__)


def _get_ark_client(config: dict):
    """延迟构造 Ark 客户端"""
    from volcenginesdkarkruntime import Ark
    api_key = config.get("api_key") or os.environ.get(config.get("api_key_env", "ARK_API_KEY"), "")
    base_url = config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
    return Ark(base_url=base_url, api_key=api_key)


class SeedanceAdapter(BaseAdapter):
    """即梦 Seedance 2.0 视频生成（异步任务 + 轮询）"""

    def invoke(
        self,
        prompt: str,
        reference_image: str | None = None,
        duration: int = 5,
        **kwargs,
    ) -> dict:
        """
        创建 Seedance 2.0 视频生成任务。

        Args:
            prompt: 视频生成提示词（可包含 --dur 5 --wm true 等参数）
            reference_image: 可选，首帧参考图 URL
            duration: 视频时长（秒），支持 5s / 10s（模型决定上限）
        """
        client = _get_ark_client(self.config)
        model = self.model or "doubao-seedance-2-0-260128"

        # 构造 content（文本 + 可选首帧图）
        content = [{"type": "text", "text": f"{prompt} --dur {duration}"}]
        if reference_image:
            content.append({"type": "image_url", "image_url": {"url": reference_image}})

        logger.info(f"[Seedance] Creating task: prompt={prompt[:60]!r}... duration={duration}s")

        create_result = client.content_generation.tasks.create(
            model=model,
            content=content,
        )

        task_id = create_result.id
        logger.info(f"[Seedance] Task created: {task_id}")
        return {
            "status": "pending",
            "task_id": task_id,
            "model": model,
            "mock": False,
        }

    def poll(self, task_id: str, poll_interval: int = 3) -> dict:
        """
        轮询 Seedance 视频任务状态，直到成功或失败。

        Args:
            task_id: invoke() 返回的 task_id
            poll_interval: 轮询间隔（秒）
        """
        client = _get_ark_client(self.config)

        while True:
            result = client.content_generation.tasks.get(task_id=task_id)
            status = result.status

            if status == "succeeded":
                video_url = result.content.video_url if hasattr(result, "content") else None
                logger.info(f"[Seedance] Task {task_id} succeeded: {video_url}")
                return {
                    "status": "success",
                    "task_id": task_id,
                    "video_url": video_url,
                    "mock": False,
                }
            elif status == "failed":
                error = result.error
                msg = f"{error.code}: {error.message}" if error else "unknown error"
                logger.error(f"[Seedance] Task {task_id} failed: {msg}")
                return {
                    "status": "error",
                    "task_id": task_id,
                    "error": msg,
                    "mock": False,
                }
            else:
                logger.info(f"[Seedance] Task {task_id} status: {status}, retrying in {poll_interval}s...")
                time.sleep(poll_interval)


AdapterRegistry.register("seedance", SeedanceAdapter)
