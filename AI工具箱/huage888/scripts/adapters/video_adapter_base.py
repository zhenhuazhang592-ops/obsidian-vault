"""
video_adapter_base.py — 视频生成适配器基类

所有视频模型适配器必须继承此基类，实现统一的接口。
"""

import time
import urllib.request
import urllib.error
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# 图片引用角色类型
IMAGE_ROLE_FIRST_FRAME = "first_frame"   # 首帧
IMAGE_ROLE_LAST_FRAME = "last_frame"    # 尾帧
IMAGE_ROLE_REFERENCE = "reference_image"  # 参考图（角色/场景一致性）


@dataclass
class VideoResult:
    """视频生成结果"""
    video_url: str
    task_id: str
    model: str
    duration: int
    elapsed_seconds: float


@dataclass
class ImageResult:
    """图片生成结果"""
    image_url: str
    task_id: str = ""
    model: str = ""


@dataclass
class AdapterConfig:
    """适配器配置"""
    api_key: str
    base_url: str = ""
    timeout: int = 60
    poll_interval: int = 5
    poll_timeout: int = 300
    # 通用参数
    duration: int = 5
    watermark: bool = True
    resolution: str = "1080p"
    aspect_ratio: str = "16:9"
    # 模型特定参数
    extra: dict = field(default_factory=dict)


class VideoAdapterBase(ABC):
    """视频生成适配器基类"""

    # 子类必须设置
    provider: str = ""
    default_video_model: str = ""
    default_image_model: str = ""

    def __init__(self, config: AdapterConfig):
        self.config = config
        self._poll_interval = config.poll_interval
        self._poll_timeout = config.poll_timeout

    # ─────────────────────────────────────────────────────────────────
    # 公开 API
    # ─────────────────────────────────────────────────────────────────

    def generate_video(
        self,
        prompt: str,
        output_path: Path,
        img1: Optional[str] = None,
        img2: Optional[str] = None,
        duration: Optional[int] = None,
        model: Optional[str] = None,
        references: Optional[list[dict]] = None,
    ) -> VideoResult:
        """生成视频（文生 / 图生 / 首尾帧 / 多参考图）

        Args:
            prompt:      视频提示词文本
            output_path: 输出文件路径
            img1:        首帧图片 URL（向后兼容，单图首帧）
            img2:        尾帧图片 URL（向后兼容，单图尾帧）
            duration:    视频时长（秒）
            model:       具体模型 ID
            references: 参考图列表，每项 dict:
                {
                    "url": str,        # 图片 URL 或本地路径
                    "role": str,       # "first_frame" | "last_frame" | "reference_image"
                    "label": str,      # 可选，标签如"漠玫参考图"，用于 debug
                }
        """
        # references 优先级高于 img1/img2
        task_id = self._create_video_task(
            prompt,
            img1=img1,
            img2=img2,
            duration=duration,
            model=model,
            references=references,
        )
        return self._poll_and_download(task_id, output_path, model)

    def generate_image(
        self,
        prompt: str,
        output_path: Path,
        model: Optional[str] = None,
    ) -> ImageResult:
        """生成图片"""
        image_url = self._create_image_task(prompt, model)
        self._download_file(image_url, output_path)
        return ImageResult(image_url=image_url, model=model or self.default_image_model)

    def health_check(self) -> bool:
        """健康检查"""
        try:
            return self._do_health_check()
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────────
    # 子类必须实现
    # ─────────────────────────────────────────────────────────────────

    @abstractmethod
    def _create_video_task(
        self,
        prompt: str,
        img1: Optional[str],
        img2: Optional[str],
        duration: Optional[int],
        model: Optional[str],
        references: Optional[list[dict]] = None,
    ) -> str:
        """创建视频任务，返回 task_id

        Args:
            references: 参考图列表，每项 dict:
                {
                    "url": str,        # 图片 URL
                    "role": str,       # "first_frame" | "last_frame" | "reference_image"
                    "label": str,      # 可选，标签
                }
        """
        ...

    @abstractmethod
    def _create_image_task(
        self,
        prompt: str,
        model: Optional[str],
    ) -> str:
        """创建图片任务，返回 image_url"""
        ...

    @abstractmethod
    def _get_task_status(self, task_id: str) -> dict:
        """查询任务状态，返回 {'status': 'pending'|'processing'|'succeeded'|'failed', ...}"""
        ...

    # ─────────────────────────────────────────────────────────────────
    # 通用工具
    # ─────────────────────────────────────────────────────────────────

    def _poll_and_download(
        self,
        task_id: str,
        output_path: Path,
        model: Optional[str],
    ) -> VideoResult:
        """轮询任务状态，成功后下载"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > self._poll_timeout:
                raise TimeoutError(f"任务超时（>{self._poll_timeout}s），task_id={task_id}")

            result = self._get_task_status(task_id)
            status = result.get("status", "unknown")

            if status == "succeeded":
                video_url = result.get("content", {}).get("video_url", "")
                if not video_url:
                    video_url = result.get("video_url", "")

                self._download_file(video_url, output_path)
                return VideoResult(
                    video_url=video_url,
                    task_id=task_id,
                    model=model or self.default_video_model,
                    duration=self._get_duration_from_result(result),
                    elapsed_seconds=elapsed,
                )

            elif status == "failed":
                error = result.get("error", {}) or result.get("message", str(result))
                raise RuntimeError(f"视频生成失败：{error}")

            # pending / processing
            time.sleep(self._poll_interval)

    def _download_file(self, url: str, output_path: Path) -> None:
        """下载文件"""
        try:
            urllib.request.urlretrieve(url, str(output_path))
        except Exception as e:
            raise RuntimeError(f"下载失败：{e}")

    def _get_duration_from_result(self, result: dict) -> int:
        """从结果中提取时长"""
        return self.config.duration

    def _http_post(self, url: str, body: dict) -> dict:
        """发送 POST 请求"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body_text = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}：{body_text}")
        except Exception as e:
            raise RuntimeError(f"请求失败：{e}")

    def _http_get(self, url: str) -> dict:
        """发送 GET 请求"""
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            raise RuntimeError(f"GET 请求失败：{e}")

    def _do_health_check(self) -> bool:
        """子类可覆盖的健康检查"""
        return True
