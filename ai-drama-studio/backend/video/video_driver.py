"""ai-drama-studio/backend/video/video_driver.py

漫舟视频生成驱动工厂 v1.0
参考 ZJT 三层视频驱动架构（Seedance / Kling / Runway / Vidu / 即梦）
支持模式：文生视频（text-to-video）、图生视频（image-to-video）

驱动统一接口：VideoDriver 抽象基类
工厂入口：VideoDriverFactory
Prompt适配层：adapt_prompt() 将漫舟v6.2格式适配为各驱动特定格式

调用示例：
    factory = VideoDriverFactory()
    driver = factory.get_driver("seedance")
    result = await driver.generate(
        prompt="【【潭斌】】走进格子间，阳光从右侧窗户射入 ...",
        image_path="/path/to/shot_frame.png",
        duration=5,
    )
    # 轮询等待完成
    final = await driver.wait_completed(result.task_id, timeout=120)
"""

import os
import uuid
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 数据模型
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VideoResult:
    """视频生成结果"""
    success: bool
    task_id: str
    video_url: str = ""
    thumbnail_url: str = ""
    error: str = ""
    provider: str = ""
    duration_sec: int = 5
    resolution: tuple[int, int] = (1280, 720)
    metadata: dict = field(default_factory=dict)


@dataclass
class VideoStatus:
    """视频任务状态"""
    state: str        # "pending" | "processing" | "completed" | "failed"
    progress: float   # 0.0 - 1.0
    video_url: str = ""
    error: str = ""
    estimated_wait_sec: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# 抽象基类
# ─────────────────────────────────────────────────────────────────────────────

class VideoDriver(ABC):
    """
    视频生成驱动抽象基类
    所有驱动必须实现 generate() / query_status() / wait_completed()
    """

    @property
    @abstractmethod
    def provider(self) -> str:
        """驱动名称"""

    @property
    @abstractmethod
    def supports_image_mode(self) -> bool:
        """是否支持图生视频"""

    @property
    @abstractmethod
    def max_duration_sec(self) -> int:
        """最长支持时长（秒）"""

    @property
    @abstractmethod
    def max_resolution(self) -> tuple[int, int]:
        """最大分辨率 (width, height)"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        image_path: str = "",
        duration: int = 5,
        **kwargs,
    ) -> VideoResult:
        """
        提交视频生成任务。

        Args:
            prompt:     视频Prompt（漫舟v6.2格式）
            image_path:  参考图路径（空则文生视频）
            duration:    时长（秒）
            **kwargs:    驱动特定参数

        Returns: VideoResult
        """
        ...

    @abstractmethod
    async def query_status(self, task_id: str) -> VideoStatus:
        """
        查询任务状态。

        Returns: VideoStatus
        """
        ...

    async def wait_completed(
        self,
        task_id: str,
        timeout: int = 120,
        poll_interval: int = 5,
    ) -> VideoResult:
        """
        轮询等待任务完成。

        Args:
            task_id:       任务ID
            timeout:       超时秒数
            poll_interval: 轮询间隔秒数

        Returns: VideoResult（最终状态）
        """
        elapsed = 0
        while elapsed < timeout:
            status = await self.query_status(task_id)
            if status.state == "completed":
                return VideoResult(
                    success=True,
                    task_id=task_id,
                    video_url=status.video_url,
                    provider=self.provider,
                )
            elif status.state == "failed":
                return VideoResult(
                    success=False,
                    task_id=task_id,
                    error=status.error,
                    provider=self.provider,
                )
            logger.debug(
                f"[{self.provider}] task={task_id} state={status.state} "
                f"progress={status.progress:.0%} wait={elapsed}s"
            )
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        return VideoResult(
            success=False,
            task_id=task_id,
            error=f"等待超时（>{timeout}s）",
            provider=self.provider,
        )

    # ── Prompt适配层（子类可重写）───────────────────────────────────────

    def adapt_prompt(self, raw_prompt: str) -> str:
        """
        将漫舟v6.2格式prompt适配为本驱动特定格式。
        子类可重写以实现驱动特定的转换逻辑。
        """
        return raw_prompt


# ─────────────────────────────────────────────────────────────────────────────
# SeedanceDriver — 字节Seedance（火山引擎）
# ─────────────────────────────────────────────────────────────────────────────

class SeedanceDriver(VideoDriver):
    """
    字节 Seedance 视频驱动
    API: 火山引擎（volcengine）Seedance API
    特点: 图生视频支持 --cref 风格引用，10秒/720p-1080p

    环境变量:
        SEEDANCE_API_KEY     — API密钥
        SEEDANCE_ENDPOINT    — 端点（默认火山引擎）
        SEEDANCE_REGION      — 区域（默认 cn-north-1）
    """

    def __init__(self, api_key: str = "", endpoint: str = "", region: str = "cn-north-1"):
        self.api_key = api_key or os.getenv("SEEDANCE_API_KEY", "")
        self.endpoint = endpoint or os.getenv(
            "SEEDANCE_ENDPOINT",
            "https://visual.volcengineapi.com/api/v1/seedance/video/generation",
        )
        self.region = region or os.getenv("SEEDANCE_REGION", "cn-north-1")

    @property
    def provider(self) -> str:
        return "seedance"

    @property
    def supports_image_mode(self) -> bool:
        return True

    @property
    def max_duration_sec(self) -> int:
        return 10

    @property
    def max_resolution(self) -> tuple[int, int]:
        return (1920, 1080)

    def adapt_prompt(self, raw_prompt: str) -> str:
        """
        Seedance 特定适配：
        - 保留 【【】】角色标记（Seedance 支持中文角色名）
        - 移除 [Audio Layer] 等漫舟特有标签（Seedance 不支持）
        - 添加电影感后缀提升质量
        """
        adapted = raw_prompt
        # 移除 Audio Layer 标签块
        import re
        adapted = re.sub(r'\[Audio Layer\].*?(?=\n\n|\Z)', '', adapted, flags=re.DOTALL)
        # 移除 Lip-sync 标注
        adapted = re.sub(r'\[Lip-sync\].*?(?=\n\n|\Z)', '', adapted, flags=re.DOTALL)
        # 移除空行压缩
        adapted = re.sub(r'\n{3,}', '\n\n', adapted).strip()
        # 添加 Seedance 质量后缀
        adapted += "\nCinematic lighting, film grain, 35mm lens, f/2.8 depth of field"
        return adapted

    async def generate(
        self,
        prompt: str,
        image_path: str = "",
        duration: int = 5,
        **kwargs,
    ) -> VideoResult:
        if not self.api_key:
            return VideoResult(
                success=False,
                task_id="",
                error="SEEDANCE_API_KEY 未设置",
                provider=self.provider,
            )

        adapted_prompt = self.adapt_prompt(prompt)
        duration = min(duration, self.max_duration_sec)

        # 分辨率映射
        resolution_map = {(1280, 720): "720p", (1920, 1080): "1080p"}
        resolution = resolution_map.get(kwargs.get("resolution", (1280, 720)), "720p")

        payload = {
            "model": "seedance-1.0",
            "prompt": adapted_prompt,
            "duration": duration,
            "resolution": resolution,
            "style_strength": float(kwargs.get("seedance_style_strength", 0.7)),
            "motion_intensity": float(kwargs.get("seedance_motion_intensity", 0.5)),
        }

        if image_path and self.supports_image_mode:
            # 图生视频模式：Base64 编码参考图
            import base64
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            payload["image"] = img_b64
            payload["mode"] = "image-to-video"
        else:
            payload["mode"] = "text-to-video"

        headers = {
            "Authorization": f"Bearer;{self.api_key}",
            "Content-Type": "application/json",
            "X-Region": self.region,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(self.endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                task_id = data.get("task_id") or data.get("data", {}).get("task_id", "")
                return VideoResult(
                    success=True,
                    task_id=task_id,
                    provider=self.provider,
                    duration_sec=duration,
                    metadata={"raw_response": data},
                )
        except httpx.HTTPStatusError as e:
            return VideoResult(
                success=False,
                task_id="",
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                provider=self.provider,
            )
        except Exception as e:
            return VideoResult(
                success=False,
                task_id="",
                error=str(e),
                provider=self.provider,
            )

    async def query_status(self, task_id: str) -> VideoStatus:
        """轮询 Seedance 任务状态"""
        query_url = self.endpoint.replace("/generation", "/query")
        headers = {
            "Authorization": f"Bearer;{self.api_key}",
            "Content-Type": "application/json",
            "X-Region": self.region,
        }
        payload = {"task_id": task_id}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(query_url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                # Seedance 状态映射
                raw_state = data.get("status", "pending")
                state_map = {
                    "pending": "pending",
                    "processing": "processing",
                    "done": "completed",
                    "failed": "failed",
                }
                state = state_map.get(raw_state, "pending")
                progress = data.get("progress", 0.0)
                video_url = data.get("video_url", "") or data.get("data", {}).get("video_url", "")
                error = data.get("error_message", "")

                return VideoStatus(
                    state=state,
                    progress=float(progress),
                    video_url=video_url,
                    error=error,
                )
        except Exception as e:
            return VideoStatus(state="failed", progress=0.0, error=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# KlingDriver — 快手可灵
# ─────────────────────────────────────────────────────────────────────────────

class KlingDriver(VideoDriver):
    """
    快手可灵（Kling）视频驱动
    API: 快手开放平台
    特点: 图生视频支持首尾帧，10秒/720p-1080p，负向提示词

    环境变量:
        KLING_API_KEY  — API密钥
        KLING_ENDPOINT — 端点（默认快手开放平台）
    """

    def __init__(self, api_key: str = "", endpoint: str = ""):
        self.api_key = api_key or os.getenv("KLING_API_KEY", "")
        self.endpoint = endpoint or os.getenv(
            "KLING_ENDPOINT",
            "https://api.kling.ai.com/v1/video/generation",
        )

    @property
    def provider(self) -> str:
        return "kling"

    @property
    def supports_image_mode(self) -> bool:
        return True

    @property
    def max_duration_sec(self) -> int:
        return 10

    @property
    def max_resolution(self) -> tuple[int, int]:
        return (1920, 1080)

    def adapt_prompt(self, raw_prompt: str) -> str:
        """
        Kling 特定适配：
        - 移除 [Audio Layer] / [Lip-sync] 标签
        - 移除 【【】】角色标记（Kling 对中文方括号支持差）
        - 替换为英文角色描述
        """
        import re
        adapted = raw_prompt
        adapted = re.sub(r'\[Audio Layer\].*?(?=\n\n|\Z)', '', adapted, flags=re.DOTALL)
        adapted = re.sub(r'\[Lip-sync\].*?(?=\n\n|\Z)', '', adapted, flags=re.DOTALL)
        # 保留角色名，去掉【【】】包裹
        adapted = re.sub(r'【【(.*?)】】', r'\1', adapted)
        adapted = re.sub(r'\n{3,}', '\n\n', adapted).strip()
        return adapted

    async def generate(
        self,
        prompt: str,
        image_path: str = "",
        duration: int = 5,
        **kwargs,
    ) -> VideoResult:
        if not self.api_key:
            return VideoResult(
                success=False,
                task_id="",
                error="KLING_API_KEY 未设置",
                provider=self.provider,
            )

        adapted_prompt = self.adapt_prompt(prompt)
        duration = min(duration, self.max_duration_sec)

        resolution = kwargs.get("resolution", (1280, 720))
        aspect_map = {
            (1280, 720): "16:9",
            (1920, 1080): "16:9",
            (720, 1280): "9:16",
            (1080, 1920): "9:16",
        }
        aspect_ratio = aspect_map.get(resolution, "16:9")

        payload = {
            "model_name": "kling-v1",
            "prompt": adapted_prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "negative_prompt": kwargs.get("kling_negative_prompt", "低质量,模糊,变形,错误的手"),
            "seed": kwargs.get("kling_seed", -1),
        }

        if image_path and self.supports_image_mode:
            import base64
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            payload["image_url"] = f"data:image/jpeg;base64,{img_b64}"
            payload["mode"] = "image-to-video"
        else:
            payload["mode"] = "text-to-video"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(self.endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                task_id = data.get("task_id") or data.get("data", {}).get("task_id", "")
                return VideoResult(
                    success=True,
                    task_id=task_id,
                    provider=self.provider,
                    duration_sec=duration,
                    metadata={"raw_response": data},
                )
        except httpx.HTTPStatusError as e:
            return VideoResult(
                success=False,
                task_id="",
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                provider=self.provider,
            )
        except Exception as e:
            return VideoResult(
                success=False,
                task_id="",
                error=str(e),
                provider=self.provider,
            )

    async def query_status(self, task_id: str) -> VideoStatus:
        """轮询 Kling 任务状态"""
        query_url = self.endpoint.replace("/generation", "/query")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    query_url,
                    json={"task_id": task_id},
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

                raw_state = data.get("status", "pending")
                state_map = {
                    "WAITING": "pending",
                    "PROCESSING": "processing",
                    "SUCCEEDED": "completed",
                    "FAILED": "failed",
                }
                state = state_map.get(raw_state, "pending")
                progress = float(data.get("progress", 0))
                video_url = data.get("video_url", "") or data.get("data", {}).get("video_url", "")
                error = data.get("message", "") or data.get("error_message", "")

                return VideoStatus(
                    state=state,
                    progress=progress / 100.0 if progress > 1 else progress,
                    video_url=video_url,
                    error=error,
                )
        except Exception as e:
            return VideoStatus(state="failed", progress=0.0, error=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# ViduDriver — 智谱Vidu
# ─────────────────────────────────────────────────────────────────────────────

class ViduDriver(VideoDriver):
    """
    智谱 Vidu 视频驱动
    API: 智谱 GLM-4V-plus 或 Vidu API
    特点: 8秒/720p，智谱生态集成度高

    环境变量:
        VIDU_API_KEY   — API密钥
        VIDU_ENDPOINT  — 端点
        ZHIPU_API_KEY  — 智谱通用API密钥（Vidu复用）
    """

    def __init__(self, api_key: str = "", endpoint: str = ""):
        self.api_key = api_key or os.getenv("VIDU_API_KEY", "") or os.getenv("ZHIPU_API_KEY", "")
        self.endpoint = endpoint or os.getenv(
            "VIDU_ENDPOINT",
            "https://open.bigmodel.cn/api/paas/v4/videos/generations",
        )

    @property
    def provider(self) -> str:
        return "vidu"

    @property
    def supports_image_mode(self) -> bool:
        return True

    @property
    def max_duration_sec(self) -> int:
        return 8

    @property
    def max_resolution(self) -> tuple[int, int]:
        return (1280, 720)

    def adapt_prompt(self, raw_prompt: str) -> str:
        """
        Vidu 特定适配：
        - 移除 [Audio Layer] / [Lip-sync] / 【【】】标记
        - Vidu 对中文支持好，【【】】可替换为逗号分隔角色名
        """
        import re
        adapted = raw_prompt
        adapted = re.sub(r'\[Audio Layer\].*?(?=\n\n|\Z)', '', adapted, flags=re.DOTALL)
        adapted = re.sub(r'\[Lip-sync\].*?(?=\n\n|\Z)', '', adapted, flags=re.DOTALL)
        # 【【角色】】替换为 "角色："
        adapted = re.sub(r'【【(.*?)】】', r'\1：', adapted)
        adapted = re.sub(r'\n{3,}', '\n\n', adapted).strip()
        # Vidu 质量后缀
        adapted += "\nofficial lighting, sharp focus, high contrast, cinematic"
        return adapted

    async def generate(
        self,
        prompt: str,
        image_path: str = "",
        duration: int = 5,
        **kwargs,
    ) -> VideoResult:
        if not self.api_key:
            return VideoResult(
                success=False,
                task_id="",
                error="VIDU_API_KEY 未设置",
                provider=self.provider,
            )

        adapted_prompt = self.adapt_prompt(prompt)
        duration = min(duration, self.max_duration_sec)

        # Vidu 分辨率选项
        resolution_map = {
            (1280, 720): "720p",
            (720, 1280): "720p_9_16",
            (1024, 1024): "1024p_square",
        }
        resolution = resolution_map.get(kwargs.get("resolution", (1280, 720)), "720p")

        payload = {
            "model": "vidu-1.0",
            "prompt": adapted_prompt,
            "duration": duration,
            "aspect_ratio": kwargs.get("vidu_aspect_ratio", resolution),
        }

        if image_path and self.supports_image_mode:
            import base64
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            payload["image_url"] = f"data:image/jpeg;base64,{img_b64}"
            payload["mode"] = "image-to-video"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(self.endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                task_id = data.get("id") or data.get("task_id", "")
                return VideoResult(
                    success=True,
                    task_id=task_id,
                    provider=self.provider,
                    duration_sec=duration,
                    metadata={"raw_response": data},
                )
        except httpx.HTTPStatusError as e:
            return VideoResult(
                success=False,
                task_id="",
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                provider=self.provider,
            )
        except Exception as e:
            return VideoResult(
                success=False,
                task_id="",
                error=str(e),
                provider=self.provider,
            )

    async def query_status(self, task_id: str) -> VideoStatus:
        """轮询 Vidu 任务状态"""
        query_url = self.endpoint.replace("/generations", f"/generations/{task_id}")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(query_url, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                raw_state = data.get("status", "pending")
                state_map = {
                    "QUEUED": "pending",
                    "PROCESSING": "processing",
                    "SUCCESS": "completed",
                    "FAIL": "failed",
                }
                state = state_map.get(raw_state, "pending")
                video_url = data.get("video_url", "")
                error = data.get("error", {}).get("message", "") if isinstance(data.get("error"), dict) else str(data.get("error", ""))

                # 估算进度
                progress_map = {"QUEUED": 0.05, "PROCESSING": 0.5, "SUCCESS": 1.0, "FAIL": 0.0}
                progress = progress_map.get(raw_state, 0.0)

                return VideoStatus(
                    state=state,
                    progress=progress,
                    video_url=video_url,
                    error=error,
                )
        except Exception as e:
            return VideoStatus(state="failed", progress=0.0, error=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# DreaminaDriver — 即梦（字节剪映）
# ─────────────────────────────────────────────────────────────────────────────

class DreaminaDriver(VideoDriver):
    """
    即梦（Dreamina / 吉卜力）视频驱动
    API: 字节剪映即梦开放平台
    特点: 6秒/720p，字节生态，与Seedance互补

    环境变量:
        DREAMINA_API_KEY  — API密钥
        DREAMINA_ENDPOINT — 端点
    """

    def __init__(self, api_key: str = "", endpoint: str = ""):
        self.api_key = api_key or os.getenv("DREAMINA_API_KEY", "")
        self.endpoint = endpoint or os.getenv(
            "DREAMINA_ENDPOINT",
            "https://api.jimeng.jianying.com/ai/bisheng-rt/video/generation",
        )

    @property
    def provider(self) -> str:
        return "dreamina"

    @property
    def supports_image_mode(self) -> bool:
        return True

    @property
    def max_duration_sec(self) -> int:
        return 6

    @property
    def max_resolution(self) -> tuple[int, int]:
        return (1280, 720)

    def adapt_prompt(self, raw_prompt: str) -> str:
        """
        Dreamina 特定适配：
        - 移除 [Audio Layer] / [Lip-sync] / 【【】】标记
        - 即梦对动漫风格优化，添加风格提示词
        """
        import re
        adapted = raw_prompt
        adapted = re.sub(r'\[Audio Layer\].*?(?=\n\n|\Z)', '', adapted, flags=re.DOTALL)
        adapted = re.sub(r'\[Lip-sync\].*?(?=\n\n|\Z)', '', adapted, flags=re.DOTALL)
        adapted = re.sub(r'【【(.*?)】】', r'\1', adapted)
        adapted = re.sub(r'\n{3,}', '\n\n', adapted).strip()
        # 即梦动漫/插画风格后缀
        adapted += "\nanimation style, vibrant colors, smooth motion, high quality"
        return adapted

    async def generate(
        self,
        prompt: str,
        image_path: str = "",
        duration: int = 5,
        **kwargs,
    ) -> VideoResult:
        if not self.api_key:
            return VideoResult(
                success=False,
                task_id="",
                error="DREAMINA_API_KEY 未设置",
                provider=self.provider,
            )

        adapted_prompt = self.adapt_prompt(prompt)
        duration = min(duration, self.max_duration_sec)

        model_version = kwargs.get("dreamina_model_version", "jimeng-1.0")

        payload = {
            "model": model_version,
            "prompt": adapted_prompt,
            "duration": duration,
            "resolution": "720p",
        }

        if image_path and self.supports_image_mode:
            import base64
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            payload["image_url"] = f"data:image/jpeg;base64,{img_b64}"
            payload["mode"] = "image_to_video"
        else:
            payload["mode"] = "text_to_video"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(self.endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                task_id = data.get("task_id") or data.get("data", {}).get("task_id", "")
                return VideoResult(
                    success=True,
                    task_id=task_id,
                    provider=self.provider,
                    duration_sec=duration,
                    metadata={"raw_response": data},
                )
        except httpx.HTTPStatusError as e:
            return VideoResult(
                success=False,
                task_id="",
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                provider=self.provider,
            )
        except Exception as e:
            return VideoResult(
                success=False,
                task_id="",
                error=str(e),
                provider=self.provider,
            )

    async def query_status(self, task_id: str) -> VideoStatus:
        """轮询 Dreamina 任务状态"""
        query_url = self.endpoint.replace("/generation", "/query")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    query_url,
                    json={"task_id": task_id},
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

                raw_state = data.get("status", "pending")
                state_map = {
                    "PENDING": "pending",
                    "RUNNING": "processing",
                    "SUCCESS": "completed",
                    "FAIL": "failed",
                }
                state = state_map.get(raw_state, "pending")
                video_url = data.get("video_url", "") or data.get("data", {}).get("video_url", "")
                error = data.get("error_msg", "")

                progress_map = {"PENDING": 0.05, "RUNNING": 0.5, "SUCCESS": 1.0, "FAIL": 0.0}
                progress = progress_map.get(raw_state, 0.0)

                return VideoStatus(
                    state=state,
                    progress=progress,
                    video_url=video_url,
                    error=error,
                )
        except Exception as e:
            return VideoStatus(state="failed", progress=0.0, error=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# RunwayDriver — Runway Gen-3
# ─────────────────────────────────────────────────────────────────────────────

class RunwayDriver(VideoDriver):
    """
    Runway Gen-3 视频驱动
    API: Runway API
    特点: 10秒/1280x768，专业影视工作流，支持补帧/超分后处理

    环境变量:
        RUNWAY_API_KEY  — API密钥
        RUNWAY_ENDPOINT — 端点
    """

    def __init__(self, api_key: str = "", endpoint: str = ""):
        self.api_key = api_key or os.getenv("RUNWAY_API_KEY", "")
        self.endpoint = endpoint or os.getenv(
            "RUNWAY_ENDPOINT",
            "https://api.runwayml.com/v1/generations",
        )

    @property
    def provider(self) -> str:
        return "runway"

    @property
    def supports_image_mode(self) -> bool:
        return True

    @property
    def max_duration_sec(self) -> int:
        return 10

    @property
    def max_resolution(self) -> tuple[int, int]:
        return (1280, 768)

    def adapt_prompt(self, raw_prompt: str) -> str:
        """
        Runway 特定适配：
        - 移除 [Audio Layer] / [Lip-sync] / 【【】】标记
        - 全部翻译为英文（Runway 对英文支持最佳）
        - 移除中文角色名，替换为英文描述
        """
        import re
        adapted = raw_prompt
        adapted = re.sub(r'\[Audio Layer\].*?(?=\n\n|\Z)', '', adapted, flags=re.DOTALL)
        adapted = re.sub(r'\[Lip-sync\].*?(?=\n\n|\Z)', '', adapted, flags=re.DOTALL)
        # 移除【【】】标记（Runway 不支持中文）
        adapted = re.sub(r'【【(.*?)】】', r'\1', adapted)
        adapted = re.sub(r'\n{3,}', '\n\n', adapted).strip()
        # Runway 电影感后缀
        adapted += "\ncinematic, film production, anamorphic lens, shallow depth of field"
        return adapted

    async def generate(
        self,
        prompt: str,
        image_path: str = "",
        duration: int = 5,
        **kwargs,
    ) -> VideoResult:
        if not self.api_key:
            return VideoResult(
                success=False,
                task_id="",
                error="RUNWAY_API_KEY 未设置",
                provider=self.provider,
            )

        adapted_prompt = self.adapt_prompt(prompt)
        duration = min(duration, self.max_duration_sec)

        payload = {
            "model": "gen3",
            "prompt_text": adapted_prompt,
            "num_frames": duration * 24,  # Runway 24fps
            "interpolate": bool(kwargs.get("runway_interpolate", True)),
            "upscale": bool(kwargs.get("runway_upscale", False)),
        }

        if image_path and self.supports_image_mode:
            import base64
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            payload["image_url"] = f"data:image/jpeg;base64,{img_b64}"
            payload["mode"] = "image-to-video"
        else:
            payload["mode"] = "text-to-video"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(self.endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                task_id = data.get("id", "")
                return VideoResult(
                    success=True,
                    task_id=task_id,
                    provider=self.provider,
                    duration_sec=duration,
                    metadata={"raw_response": data},
                )
        except httpx.HTTPStatusError as e:
            return VideoResult(
                success=False,
                task_id="",
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                provider=self.provider,
            )
        except Exception as e:
            return VideoResult(
                success=False,
                task_id="",
                error=str(e),
                provider=self.provider,
            )

    async def query_status(self, task_id: str) -> VideoStatus:
        """轮询 Runway 任务状态"""
        query_url = f"{self.endpoint}/{task_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(query_url, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                raw_state = data.get("status", "pending")
                state_map = {
                    "pending": "pending",
                    "starting": "processing",
                    "running": "processing",
                    "succeeded": "completed",
                    "failed": "failed",
                }
                state = state_map.get(raw_state, "pending")
                progress = float(data.get("progress", 0.0))
                video_url = data.get("output", {}).get("video_url", "") if isinstance(data.get("output"), dict) else data.get("video_url", "")
                error = data.get("error", {}).get("message", "") if isinstance(data.get("error"), dict) else str(data.get("error", ""))

                return VideoStatus(
                    state=state,
                    progress=progress,
                    video_url=video_url,
                    error=error,
                )
        except Exception as e:
            return VideoStatus(state="failed", progress=0.0, error=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# VideoDriverFactory — 工厂入口
# ─────────────────────────────────────────────────────────────────────────────

DRIVER_REGISTRY = {
    "seedance": SeedanceDriver,
    "kling":    KlingDriver,
    "vidu":     ViduDriver,
    "dreamina": DreaminaDriver,
    "runway":   RunwayDriver,
}


class VideoDriverFactory:
    """
    漫舟视频驱动工厂

    用法:
        factory = VideoDriverFactory()

        # 按名称获取驱动
        driver = factory.get_driver("seedance")

        # 自动选择最佳驱动
        driver = factory.get_best_driver(mode="image-to-video", duration=5)

        # Prompt适配
        adapted = factory.adapt_prompt(raw_prompt, provider="seedance")
    """

    def get_driver(self, provider: str) -> VideoDriver:
        """
        获取指定驱动实例。

        Args:
            provider: 驱动名称（seedance / kling / vidu / dreamina / runway）

        Returns: VideoDriver 实例

        Raises:
            ValueError: 不支持的驱动
        """
        cls = DRIVER_REGISTRY.get(provider.lower())
        if not cls:
            available = list(DRIVER_REGISTRY.keys())
            raise ValueError(
                f"不支持的视频驱动: {provider}，可用驱动: {available}"
            )
        return cls()

    def get_best_driver(
        self,
        mode: str = "text-to-video",
        duration: int = 5,
        resolution: tuple[int, int] = (1280, 720),
    ) -> VideoDriver:
        """
        根据需求自动选择最佳驱动。

        选型策略（参考ZJT驱动选型逻辑）:
        - 图生视频优先: Seedance（--cref支持）> Kling（首尾帧）> Vidu > Runway > Dreamina
        - 文生视频: Seedance > Runway > Kling > Vidu > Dreamina
        - 时长 > 8秒: Seedance / Kling / Runway
        - 1080p: Seedance / Kling

        Args:
            mode:       "text-to-video" | "image-to-video"
            duration:   期望时长（秒）
            resolution: 期望分辨率

        Returns: 最合适的 VideoDriver 实例
        """
        w, h = resolution

        if mode == "image-to-video":
            # 图生视频优先级
            if w >= 1920 or h >= 1080:
                # 1080p 图生视频 → Seedance 或 Kling
                return self.get_driver("seedance")
            elif duration <= 6:
                # 短时长 → Dreamina 或 Vidu
                return self.get_driver("dreamina")
            else:
                # 标准 5s 720p → Seedance
                return self.get_driver("seedance")
        else:
            # 文生视频优先级
            if duration > 8:
                # 长视频 → Seedance / Runway / Kling
                return self.get_driver("seedance")
            elif w >= 1920:
                # 高分辨率 → Seedance
                return self.get_driver("seedance")
            elif w <= 720:
                # 竖屏/低分辨率 → Vidu / Dreamina
                return self.get_driver("vidu")
            else:
                # 标准 720p → Runway（质量优先）
                return self.get_driver("runway")

    def adapt_prompt(self, raw_prompt: str, provider: str) -> str:
        """
        将漫舟v6.2格式prompt适配为指定驱动的特定格式。

        Args:
            raw_prompt: 漫舟v6.2格式原始prompt
            provider:    驱动名称

        Returns: 适配后的prompt字符串
        """
        try:
            driver = self.get_driver(provider)
            return driver.adapt_prompt(raw_prompt)
        except ValueError:
            # 不支持的驱动，原样返回
            return raw_prompt

    def list_providers(self) -> list[str]:
        """返回所有可用驱动名称"""
        return list(DRIVER_REGISTRY.keys())

    def get_driver_info(self, provider: str) -> dict:
        """
        返回驱动能力信息。

        Returns:
            {
                "provider": str,
                "supports_image_mode": bool,
                "max_duration_sec": int,
                "max_resolution": tuple,
                "api_key_set": bool,
            }
        """
        try:
            driver = self.get_driver(provider)
            return {
                "provider": provider,
                "supports_image_mode": driver.supports_image_mode,
                "max_duration_sec": driver.max_duration_sec,
                "max_resolution": driver.max_resolution,
                "api_key_set": bool(
                    os.getenv(f"{provider.upper()}_API_KEY", "")
                ),
            }
        except ValueError:
            return {"error": f"未知驱动: {provider}"}


# ─────────────────────────────────────────────────────────────────────────────
# 自测
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("漫舟 VideoDriverFactory 自测")
    print("=" * 60)

    factory = VideoDriverFactory()

    # 列出所有驱动
    print(f"\n可用驱动: {factory.list_providers()}")

    # 驱动能力概览
    print("\n驱动能力概览:")
    for p in factory.list_providers():
        info = factory.get_driver_info(p)
        key_ok = "已设置" if info.get("api_key_set") else "未设置"
        print(
            f"  [{p}] {info['supports_image_mode']} | "
            f"max {info['max_duration_sec']}s | "
            f"{info['max_resolution'][0]}x{info['max_resolution'][1]} | "
            f"API_KEY: {key_ok}"
        )

    # Prompt适配测试
    sample_prompt = """
【【潭斌】】走进格子间，阳光从右侧窗户斜射进来。
他在办公桌前坐下，翻开文件夹。
[Audio Layer] ambient office hum, subtle footsteps
[Lip-sync] viseme_sequence: V0→V2→V5
Cinematic lighting, wide shot, 35mm lens
"""
    print("\nPrompt适配测试（seedance）:")
    adapted = factory.adapt_prompt(sample_prompt, "seedance")
    print(adapted[:200] + "...")

    print("\nPrompt适配测试（kling）:")
    adapted = factory.adapt_prompt(sample_prompt, "kling")
    print(adapted[:200] + "...")

    # 驱动选型测试
    print("\n自动选型测试:")
    for mode in ["text-to-video", "image-to-video"]:
        for dur in [5, 10]:
            for res in [(1280, 720), (1920, 1080), (720, 1280)]:
                driver = factory.get_best_driver(mode=mode, duration=dur, resolution=res)
                print(f"  mode={mode:<20} dur={dur}s res={res[0]}x{res[1]} → {driver.provider}")

    # API Key检查
    print("\nAPI Key 环境变量检查:")
    for p in factory.list_providers():
        env_key = f"{p.upper()}_API_KEY"
        val = os.getenv(env_key, "")
        print(f"  {env_key}: {'已设置' if val else '未设置'}")

    print("\n自测完成。")
