#!/usr/bin/env python3
"""配置加载器"""
import json, pathlib

CONFIG_PATH = pathlib.Path(__file__).parent / "jike_config.json"


def load() -> dict:
    """加载配置文件"""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config not found: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text())


def save(cfg: dict):
    """保存配置"""
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
