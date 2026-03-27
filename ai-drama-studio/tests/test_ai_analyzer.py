# tests/test_ai_analyzer.py
import sys
from pathlib import Path

# ai_analyzer 是 backend 内部的模块，需要从 backend/ 上层运行
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from pipeline.ai_analyzer import AIAnalyzer
from manzhou_lapian.types import ShotAnalysis, AudioLayer


def test_normalize_tapnow():
    """测试 TapNow 14列 JSON 标准化"""
    raw = {
        "shot_number": 1,
        "start_time": 0.0,
        "end_time": 8.0,
        "duration": 8.0,
        "shot_size": "MS",
        "camera_angle": "平视",
        "camera_movement": "固定",
        "yaw": 0,
        "pitch": 0,
        "dolly": "z",
        "lighting_style": "自然光",
        "color_temperature": 5200,
        "depth_of_field": "Shallow",
        "description": "【【char_01_谭斌】】站在落地窗前。",
        "visual_description": "女主站在落地窗前，晨光5200K。",
        "dialogue": "无",
        "viseme": "无",
        "audio_layer": {
            "MUSIC": "piano_ambient-0-8s-fade_in",
            "SFX_AMBIENT": "office-0-8s",
            "SFX_NARRATIVE": "无",
            "SFX_EMOTION": "无",
        },
        "keyframe_times": [0.0, 4.0],
        "transition": "硬切",
        "narrative_function": "环境交代",
        "visual_hook": "城市天际线",
        "props": "无",
        "imagePrompt": "A woman stands by a window...",
        "videoPrompt": "MS, 固定, 自然光...",
    }

    result = AIAnalyzer.normalize_tapnow(raw)

    assert isinstance(result, ShotAnalysis)
    assert result.shot_number == 1
    assert result.shot_size == "MS"
    assert result.lighting_style == "自然光"
    assert result.color_temperature == 5200
    assert isinstance(result.audio_layer, AudioLayer)
    assert result.audio_layer.music == "piano_ambient-0-8s-fade_in"


def test_normalize_flat_schema():
    """测试扁平 Schema 降级兼容（Zhipu 输出）"""
    raw = {
        "shot_number": 1,
        "start_time": 0.0,
        "end_time": 8.0,
        "duration": 8.0,
        "shot_size": "MS",
        "camera_movement": "固定",
        "lighting": "自然光",
        "color_palette": "冷色",
        "scene_description": "女主站在落地窗前",
        "dialogue": "无",
        "vo_emotion": "无",
        "sfx": "无",
        "bgm_style": "钢琴",
        "transition": "硬切",
        "generation_prompt": "A woman stands by window...",
    }

    result = AIAnalyzer.normalize_tapnow(raw)

    assert isinstance(result, ShotAnalysis)
    assert result.shot_size == "MS"
    assert result.description == "女主站在落地窗前"
    assert result.imagePrompt == "A woman stands by window..."
