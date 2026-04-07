# scripts/adapters/__init__.py
from .video_adapter_base import VideoAdapterBase, AdapterConfig, VideoResult, ImageResult
from .doubao_adapter import DoubaoAdapter
from .kling_adapter import KlingAdapter
from .video_adapter_registry import VideoAdapterRegistry, get_registry

__all__ = [
    "VideoAdapterBase",
    "AdapterConfig",
    "VideoResult",
    "ImageResult",
    "DoubaoAdapter",
    "KlingAdapter",
    "VideoAdapterRegistry",
    "get_registry",
]
