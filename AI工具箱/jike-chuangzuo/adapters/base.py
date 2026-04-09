#!/usr/bin/env python3
"""Adapter 基类 —— 统一文本/图像/视频调用接口"""
import json, logging
from abc import ABC, abstractmethod
from typing import Generator, Any

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """所有 Adapter 的基类"""

    def __init__(self, config: dict):
        self.config = config
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "")
        self.base_url = config.get("base_url", "")
        self.manufacturer = config.get("manufacturer", "")

    @abstractmethod
    def invoke(self, prompt: str, schema: dict | None = None, **kwargs) -> dict:
        """同步调用，返回 dict 结果"""
        ...


class AdapterRegistry:
    """Adapter 注册中心 —— 配置驱动"""

    _registry: dict[str, type[BaseAdapter]] = {}

    @classmethod
    def register(cls, name: str, adapter_cls: type[BaseAdapter]):
        cls._registry[name] = adapter_cls

    @classmethod
    def get(cls, name: str, config: dict) -> BaseAdapter:
        if name not in cls._registry:
            available = list(cls._registry.keys())
            raise ValueError(f"Unknown adapter: {name}. Available: {available}")
        return cls._registry[name](config)
