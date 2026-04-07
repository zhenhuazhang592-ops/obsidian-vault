"""
video_adapter_registry.py — 视频模型适配器注册中心

统一管理所有视频模型适配器，新增模型只需注册。
"""

import os
from typing import Optional
from .video_adapter_base import VideoAdapterBase, AdapterConfig
from .doubao_adapter import DoubaoAdapter
from .kling_adapter import KlingAdapter


class VideoAdapterRegistry:
    """视频适配器注册中心"""

    def __init__(self):
        self._adapters = {}

    def register(self, name: str, adapter: VideoAdapterBase) -> None:
        """注册适配器"""
        if name in self._adapters:
            print(f"⚠️  适配器 '{name}' 已存在，将被覆盖")
        self._adapters[name] = adapter

    def get(self, name: str) -> VideoAdapterBase:
        """获取适配器"""
        if name not in self._adapters:
            available = list(self._adapters.keys())
            raise KeyError(
                f"未找到适配器 '{name}'。"
                f"可用适配器：{available if available else '(空)'}"
            )
        return self._adapters[name]

    def has(self, name: str) -> bool:
        return name in self._adapters

    def list(self) -> list[str]:
        """列出所有已注册适配器"""
        return list(self._adapters.keys())

    # ─────────────────────────────────────────────────────────────────
    # 工厂方法：从环境变量创建适配器
    # ─────────────────────────────────────────────────────────────────

    @classmethod
    def from_env(cls) -> "VideoAdapterRegistry":
        """从环境变量创建并注册所有可用适配器"""
        registry = cls()

        # Doubao
        doubao_key = os.environ.get("ARK_API_KEY", "")
        if doubao_key:
            registry.register("doubao", DoubaoAdapter(AdapterConfig(
                api_key=doubao_key,
                base_url=os.environ.get("ARK_BASE_URL", ""),
            )))
            print("✅ Doubao 适配器已注册（环境变量 ARK_API_KEY）")

        # Kling
        kling_key = os.environ.get("KLING_API_KEY", "")
        kling_key_id = os.environ.get("KLING_KEY_ID", "")
        if kling_key and kling_key_id:
            registry.register("kling", KlingAdapter(AdapterConfig(
                api_key=kling_key,
                key_id=kling_key_id,
                base_url=os.environ.get("KLING_BASE_URL", "https://api.klingai.com"),
            )))
            print("✅ Kling 适配器已注册（环境变量 KLING_API_KEY）")

        return registry


# 全局单例
_global_registry: Optional[VideoAdapterRegistry] = None


def get_registry() -> VideoAdapterRegistry:
    """获取全局注册中心（延迟初始化）"""
    global _global_registry
    if _global_registry is None:
        _global_registry = VideoAdapterRegistry.from_env()
    return _global_registry
