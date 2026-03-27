#!/usr/bin/env python3
"""
Configuration loader for YouTube Research Flow
"""

import json
import os
from typing import Dict, Any


def load_config(config_path: str = "youtube-research-flow/config/youtube_research_config.json") -> Dict[str, Any]:
    """Load configuration from JSON file"""
    try:
        if not os.path.exists(config_path):
            return {}

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except Exception as e:
        print(f"⚠️  加载配置文件时出错: {e}")
        return {}
