"""
doubao_adapter.py — 火山引擎 Doubao 视频/图片适配器

支持：Seedance 2.0（视频）、Seedream 5.0（图片）
多参考图模式：参考 https://github.com/Toonflow-app/Toonflow-app 火山引擎适配器的实现，
    所有参考图通过 content 数组传入，role 标记为 first_frame / last_frame / reference_image
"""

import sys
import base64
from pathlib import Path
from typing import Optional

try:
    from openai import OpenAI as ImageClient
except ImportError:
    ImageClient = None

from .video_adapter_base import VideoAdapterBase, AdapterConfig, ImageResult, IMAGE_ROLE_FIRST_FRAME, IMAGE_ROLE_LAST_FRAME, IMAGE_ROLE_REFERENCE


def _local_to_base64(file_path: str) -> str:
    """将本地文件转为 base64 data URL（供 Doubao API 使用）"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"本地文件不存在：{file_path}")
    mime = "image/png" if path.suffix.lower() in (".png", ".webp") else "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{data}"


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
        references: Optional[list[dict]] = None,
    ) -> str:
        """
        创建视频任务（支持多参考图）。

        Toonflow 模式（content 数组）：
          content = [
              {"type": "text", "text": prompt},
              {"type": "image_url", "image_url": {"url": img1_url, "role": "first_frame"}},
              {"type": "image_url", "image_url": {"url": img2_url, "role": "last_frame"}},
              ...  # 更多 reference_image
          ]

        references 优先级高于 img1/img2（向后兼容）。
        """
        model_id = model or self.default_video_model
        dur = duration or self.config.duration

        # 构建 content 数组
        content: list[dict] = [
            {
                "type": "text",
                "text": f"{prompt} --wm {'true' if self.config.watermark else 'false'} --dur {dur}"
            }
        ]

        # 收集所有图片引用（去重，references 优先级最高）
        seen_urls: set[str] = set()
        refs_to_add: list[dict] = []

        # 1. references 列表（最高优先级）
        if references:
            for ref in references:
                url = ref.get("url", "")
                if not url or url in seen_urls:
                    continue
                role = ref.get("role", IMAGE_ROLE_REFERENCE)
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": self._resolve_url(url),
                        "role": role,
                    },
                })
                seen_urls.add(url)

        # 2. img1 降级（向后兼容）
        if img1 and img1 not in seen_urls:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": self._resolve_url(img1),
                    "role": IMAGE_ROLE_FIRST_FRAME,
                },
            })
            seen_urls.add(img1)

        # 3. img2 降级（向后兼容）
        if img2 and img2 not in seen_urls:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": self._resolve_url(img2),
                    "role": IMAGE_ROLE_LAST_FRAME,
                },
            })

        payload = {"model": model_id, "content": content}
        url = f"{self._base_url}/contents/generations/tasks"

        result = self._http_post(url, payload)
        if "id" not in result:
            raise RuntimeError(f"创建任务失败：{result}")
        return result["id"]

    def _resolve_url(self, url_or_path: str) -> str:
        """
        解析 URL 或本地路径：
        - 以 http:// 或 https:// 开头 → 直接返回
        - 否则视为本地文件 → 转为 base64 data URL
        """
        url_or_path = url_or_path.strip()
        if url_or_path.startswith(("http://", "https://", "data:")):
            return url_or_path
        return _local_to_base64(url_or_path)

    def _get_task_status(self, task_id: str) -> dict:
        url = f"{self._base_url}/contents/generations/tasks/{task_id}"
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
            size="2k",
            extra_body={"watermark": self.config.watermark},
        )
        return response.data[0].url

    # ─────────────────────────────────────────────────────────────────
    # 健康检查
    # ─────────────────────────────────────────────────────────────────

    def _do_health_check(self) -> bool:
        url = f"{self._base_url}/contents/generations/tasks"
        payload = {
            "model": self.default_video_model,
            "content": [{"type": "text", "text": "test --wm true --dur 5"}],
        }
        try:
            result = self._http_post(url, payload)
            return "id" in result
        except Exception:
            return False
