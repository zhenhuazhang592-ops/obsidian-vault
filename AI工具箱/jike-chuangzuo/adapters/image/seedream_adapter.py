#!/usr/bin/env python3
"""Seedream Adapter —— 即梦图像生成（Volcengine Ark SDK）

依赖: pip install 'volcengine-python-sdk[ark]'
环境变量: ARK_API_KEY
"""
import os, logging
from adapters.base import BaseAdapter, AdapterRegistry

logger = logging.getLogger(__name__)


def _get_ark_client(config: dict):
    """延迟构造 Ark 客户端（避免未安装 SDK 时 import 报错）"""
    from volcenginesdkarkruntime import Ark
    api_key = config.get("api_key") or os.environ.get(config.get("api_key_env", "ARK_API_KEY"), "")
    base_url = config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
    return Ark(base_url=base_url, api_key=api_key)


class SeedreamAdapter(BaseAdapter):
    """即梦 Seedream 5.0 图像生成（流式）"""

    def invoke(
        self,
        prompt: str,
        reference_image: str | None = None,
        aspect_ratio: str = "16:9",
        size: str = "2K",
        num_images: int = 1,
        watermark: bool = True,
        **kwargs,
    ) -> dict:
        """
        调用 Seedream 流式 API，返回已解析的图片 URL 列表。

        Args:
            prompt: 图像生成提示词
            reference_image: 可选，参考图 URL（image_to_image）
            aspect_ratio: 尺寸比例 (1:1 / 16:9 / 9:16 / 3:4 / 4:3)
            size: 图片尺寸 (2K / 1K / HD)
            num_images: 生成数量（sequential 模式）
            watermark: 是否带水印
        """
        client = _get_ark_client(self.config)
        model = self.model or "doubao-seedream-5-0-260128"

        # size 映射
        size_map = {"1:1": "1:1", "16:9": "16:9", "9:16": "9:16", "3:4": "3:4", "4:3": "4:3"}
        resolved_size = size_map.get(aspect_ratio, "16:9")

        # image 参数（参考图）
        image_args = []
        if reference_image:
            image_args.append(reference_image)

        logger.info(f"[Seedream] Generating: {prompt[:60]!r}... ref={bool(reference_image)}")

        # 流式调用
        if num_images > 1:
            # 顺序多图模式
            from volcenginesdkarkruntime.types.images.images import SequentialImageGenerationOptions
            response = client.images.generate(
                model=model,
                prompt=prompt,
                image=image_args or None,
                sequential_image_generation="auto",
                sequential_image_generation_options=SequentialImageGenerationOptions(max_images=num_images),
                response_format="url",
                size=resolved_size,
                stream=True,
                watermark=watermark,
            )
        else:
            response = client.images.generate(
                model=model,
                prompt=prompt,
                image=image_args or None,
                response_format="url",
                size=resolved_size,
                stream=True,
                watermark=watermark,
            )

        # 收集结果
        urls = []
        error_msg = None
        for event in response:
            if event is None:
                continue
            etype = event.type
            if etype == "image_generation.partial_succeeded":
                if event.url:
                    urls.append(event.url)
                    logger.info(f"[Seedream] partial: {event.url}")
            elif etype == "image_generation.completed":
                if event.usage:
                    logger.info(f"[Seedream] completed usage: {event.usage}")
            elif etype == "image_generation.partial_failed":
                err = event.error
                error_msg = f"{err.code}: {err.message}" if err else "unknown error"
                logger.warning(f"[Seedream] partial failed: {error_msg}")

        if not urls and error_msg:
            return {"status": "error", "error": error_msg, "mock": False}

        return {
            "status": "success",
            "urls": urls,
            "count": len(urls),
            "mock": False,
        }

    def poll(self, task_id: str) -> dict:
        """Seedream 5.0 为流式返回，无需单独 poll（保留接口兼容）"""
        return {"status": "success", "task_id": task_id, "note": "stream mode, no poll needed"}


AdapterRegistry.register("seedream", SeedreamAdapter)
