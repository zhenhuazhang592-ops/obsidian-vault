# tests/test_prompts.py
from manzhou_lapian.prompts import build_analysis_prompt, build_system_prompt
from manzhou_lapian.types import CDPData


def test_build_prompt_without_cdp():
    prompt = build_analysis_prompt(shot_number=1, duration=8.0, cdp_context=None)
    # 用户 prompt 不含 CDP
    assert "char_01" not in prompt
    assert "【【CDP角色库】】" not in prompt
    # 用户 prompt 引用了系统 prompt 中的 JSON 格式
    assert "JSON格式" in prompt


def test_build_prompt_with_cdp():
    cdp_ctx = "【【char_01_谭斌】】：女，26岁。"
    prompt = build_analysis_prompt(shot_number=1, duration=8.0, cdp_context=cdp_ctx)
    assert "char_01_谭斌" in prompt
    assert "【【CDP角色库】】" in prompt


def test_system_prompt_contains_required_fields():
    """系统 prompt 必须包含完整 JSON schema"""
    cdp = CDPData()
    prompt = build_system_prompt(
        shot_number=1,
        start_time=0.0,
        end_time=8.0,
        duration=8.0,
        keyframe_times=[0.0, 4.0, 8.0],
        cdp_data=cdp,
    )
    required = ["shot_number", "shot_size", "camera_angle", "camera_movement",
                "lighting_style", "depth_of_field", "description",
                "dialogue", "viseme", "audio_layer", "imagePrompt", "videoPrompt"]
    for field in required:
        assert field in prompt, f"Missing field: {field}"


def test_system_prompt_with_cdp_context():
    """带 CDP 的 system prompt"""
    cdp = CDPData(characters={"char_01_谭斌": {"name": "谭斌", "description": "女"}})
    prompt = build_system_prompt(
        shot_number=1,
        start_time=0.0,
        end_time=8.0,
        duration=8.0,
        keyframe_times=[0.0, 4.0, 8.0],
        cdp_data=cdp,
    )
    assert "char_01_谭斌" in prompt
    assert "【【CDP角色库】】" in prompt
    assert "shot_number" in prompt
