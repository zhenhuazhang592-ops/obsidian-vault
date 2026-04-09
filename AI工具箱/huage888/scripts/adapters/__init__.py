# scripts/adapters/__init__.py
from .video_adapter_base import (
    VideoAdapterBase, AdapterConfig, VideoResult, ImageResult,
    IMAGE_ROLE_FIRST_FRAME, IMAGE_ROLE_LAST_FRAME, IMAGE_ROLE_REFERENCE,
)
from .doubao_adapter import DoubaoAdapter
from .kling_adapter import KlingAdapter
from .wan_adapter import WanAdapter
from .vidu_adapter import ViduAdapter
from .gemini_veo_adapter import GeminiVeoAdapter
from .video_adapter_registry import VideoAdapterRegistry, get_registry

__all__ = [
    "VideoAdapterBase",
    "AdapterConfig",
    "VideoResult",
    "ImageResult",
    "IMAGE_ROLE_FIRST_FRAME",
    "IMAGE_ROLE_LAST_FRAME",
    "IMAGE_ROLE_REFERENCE",
    "DoubaoAdapter",
    "KlingAdapter",
    "WanAdapter",
    "ViduAdapter",
    "GeminiVeoAdapter",
    "VideoAdapterRegistry",
    "get_registry",
]
