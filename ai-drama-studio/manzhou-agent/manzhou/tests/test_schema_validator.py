"""SchemaValidator 单元测试"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from manzhou.schema_validator import SchemaValidator, ValidationResult
from manzhou.schema import ShotScript, IPProfile, Step45Output, ShotScriptMeta
from manzhou.constants import is_emotion_jump_allowed


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def ip_profile():
    return IPProfile(
        project_id="proj_test",
        ip_profile_version="v10",
        ip_name="活着",
        ip_type="现实主义",
        characters={
            "char_fugui": None,
            "char_jiazhen": None,
        },
        locations={
            "loc_naowu": None,
            "loc_tian": None,
        },
        items={},
    )


@pytest.fixture
def step45_output():
    return Step45Output(
        project_id="proj_test",
        episode="EP01",
        emotion_baseline="虐/悲",
        color_temp_range=("暖黄", "灰暗"),
        emotion_curve=["L1→L2", "L2→L3", "L3→L4", "L4→L3", "L3→L2", "L2→L1"],
        prohibited_keywords=["美颜", "滤镜", "卡通化"],
        shot_emotion_map={
            "P01": "L1", "P02": "L2", "P03": "L3",
            "P04": "L4", "P05": "L3", "P06": "L4",
            "P07": "L2", "P08": "L1",
        },
        shot_camera_map={
            "P01": {"shot_type": "LS", "camera_action": "固定"},
            "P02": {"shot_type": "MS", "camera_action": "摇"},
            "P04": {"shot_type": "CU", "camera_action": "固定"},
        },
    )


@pytest.fixture
def validator(ip_profile, step45_output):
    return SchemaValidator(ip_profile, step45_output)


# =============================================================================
# D1 完整性测试
# =============================================================================

def test_D1_pass(validator):
    """D1: 所有必填字段完整 → 应通过"""
    shot = ShotScript(
        shot_id="P01",
        duration_sec=8,
        location_id="loc_naowu",
        character_ids=["char_fugui"],
        script="老人在田里耕地",
        dialogue="我是福贵",
        image_prompt="中国农村黄昏老人耕地夕阳写实摄影无美颜无卡通无特效",
        video_prompt="固定镜头老人耕地夕阳渐沉无滤镜无特效",
        emotion_level="L1",
        beat_position="B01",
        shot_type="LS",
        camera_action="固定",
    )
    result = validator.validate_shot(shot)
    assert result.d1_score >= 0.7, f"D1应有≥0.7，实际{result.d1_score}"
    assert result.is_passed, "无BLOCK错误应通过"


def test_D1_missing_prompt(validator):
    """D1: image_prompt 为空 → 应降分且报告BLOCK错误"""
    shot = ShotScript(
        shot_id="P01",
        duration_sec=8,
        location_id="loc_naowu",
        character_ids=["char_fugui"],
        script="老人耕地",
        dialogue="",
        image_prompt="",  # 空
        video_prompt="固定镜头",
        emotion_level="L1",
        beat_position="B01",
        shot_type="LS",
        camera_action="固定",
    )
    result = validator.validate_shot(shot)
    assert result.d1_score < 1.0, "image_prompt为空应降分"
    block_errors = [e for e in result.errors if e.severity == "BLOCK"]
    assert len(block_errors) > 0, "应有BLOCK错误"


# =============================================================================
# D2 一致性测试
# =============================================================================

def test_D2_char_id_valid(validator):
    """D2: char_id 在 IP档案中 → 应通过"""
    shot = ShotScript(
        shot_id="P01",
        duration_sec=8,
        location_id="loc_naowu",
        character_ids=["char_fugui"],
        script="",
        dialogue="",
        image_prompt="提示词",
        video_prompt="提示词",
        emotion_level="L1",
        beat_position="B01",
        shot_type="LS",
        camera_action="固定",
    )
    result = validator.validate_shot(shot)
    assert result.d2_score == 1.0, f"char_id有效D2应=1.0，实际{result.d2_score}"


def test_D2_char_id_invalid(validator, ip_profile, step45_output):
    """D2: char_id 不在 IP档案中 → 应报告BLOCK错误"""
    shot = ShotScript(
        shot_id="P01",
        duration_sec=8,
        location_id="loc_naowu",
        character_ids=["char_fake_id"],
        script="",
        dialogue="",
        image_prompt="提示词",
        video_prompt="提示词",
        emotion_level="L1",
        beat_position="B01",
        shot_type="LS",
        camera_action="固定",
    )
    result = validator.validate_shot(shot)
    block_errors = [e for e in result.errors if e.severity == "BLOCK"]
    assert len(block_errors) > 0, "未知char_id应报告BLOCK"
    assert result.d2_score < 1.0, "D2应降分"


def test_D2_loc_id_invalid(validator):
    """D2: loc_id 不在 IP档案中 → 应报告BLOCK错误"""
    shot = ShotScript(
        shot_id="P01",
        duration_sec=8,
        location_id="loc_fake",
        character_ids=["char_fugui"],
        script="",
        dialogue="",
        image_prompt="提示词",
        video_prompt="提示词",
        emotion_level="L1",
        beat_position="B01",
        shot_type="LS",
        camera_action="固定",
    )
    result = validator.validate_shot(shot)
    block_errors = [e for e in result.errors if e.severity == "BLOCK"]
    assert len(block_errors) > 0, "未知loc_id应报告BLOCK"


# =============================================================================
# D3 指令合规测试
# =============================================================================

def test_D3_prohibited_keyword_found(validator):
    """D3: Prompt 包含禁止词 → 应报告BLOCK错误"""
    shot = ShotScript(
        shot_id="P01",
        duration_sec=8,
        location_id="loc_naowu",
        character_ids=["char_fugui"],
        script="老人耕地",
        dialogue="",
        image_prompt="夕阳西下，使用了唯美滤镜和美颜效果，写实摄影",
        video_prompt="镜头推进",
        emotion_level="L1",
        beat_position="B01",
        shot_type="LS",
        camera_action="固定",
    )
    result = validator.validate_shot(shot)
    prohibited_errors = [e for e in result.errors if "美颜" in e.expected or "滤镜" in e.expected]
    assert len(prohibited_errors) > 0, "应发现禁止词美颜/滤镜"


def test_D3_emotion_mismatch_warn(validator, step45_output):
    """D3: emotion_level 与 D3 不符 → 应报告 WARN（不阻断）"""
    shot = ShotScript(
        shot_id="P01",
        duration_sec=8,
        location_id="loc_naowu",
        character_ids=["char_fugui"],
        script="老人在田里耕地，平静劳作",
        dialogue="",
        image_prompt="中国农村老人田地劳作写实摄影无滤镜无美颜",
        video_prompt="固定镜头无特效",
        emotion_level="L4",   # D3 要求 L1，但作为 WARN 不阻断
        beat_position="B01",
        shot_type="LS",
        camera_action="固定",
    )
    result = validator.validate_shot(shot)
    warn_errors = [e for e in result.errors if e.severity == "WARN"]
    assert len(warn_errors) > 0, "情绪不符应报告WARN"
    assert result.is_passed, "WARN不阻断，应通过"


# =============================================================================
# 情绪跳转矩阵测试
# =============================================================================

def test_emotion_jump_allowed():
    assert is_emotion_jump_allowed("L1", "L2") == True
    assert is_emotion_jump_allowed("L1", "L3") == True
    assert is_emotion_jump_allowed("L1", "L4") == False  # 禁止
    assert is_emotion_jump_allowed("L4", "L1") == False  # 禁止
    assert is_emotion_jump_allowed("L4", "L5") == True
    assert is_emotion_jump_allowed("L5", "L1") == False  # 禁止
    assert is_emotion_jump_allowed("L2", "L4") == True
    assert is_emotion_jump_allowed("L3", "L5") == False  # 禁止


# =============================================================================
# 批量校验测试
# =============================================================================

def test_validate_episode_all_pass(validator, step45_output):
    """整集所有镜头通过 → 集评分应优秀"""
    shots = [
        ShotScript(
            shot_id=f"P{i:02d}",
            duration_sec=8,
            location_id="loc_naowu",
            character_ids=["char_fugui"],
            script=f"场景{i}老人在田里平静劳作",
            dialogue="对白",
            image_prompt="夕阳西下老人耕地1950年代农村写实摄影无美颜无卡通无特效",
            video_prompt="固定镜头无特效无滤镜",
            emotion_level=step45_output.shot_emotion_map.get(f"P{i:02d}", "L1"),
            beat_position=f"B{i:02d}",
            shot_type="MS",
            camera_action="固定",
        )
        for i in range(1, 9)
    ]
    result = validator.validate_episode(shots)
    assert result["is_passed"] == True, "全通过应返回True"
    assert result["avg_composite"] >= 0.70, f"综合分应≥0.70，实际{result['avg_composite']}"


def test_validate_episode_one_fails(validator):
    """整集有一个镜头含禁止词 → 应报告失败"""
    shots = [
        ShotScript(
            shot_id="P01",
            duration_sec=8,
            location_id="loc_naowu",
            character_ids=["char_fugui"],
            script="场景1老人在田里耕地写实摄影无美颜无卡通",
            dialogue="对白",
            image_prompt="提示词内容无禁止词无滤镜无美颜无卡通",
            video_prompt="提示词内容无禁止词",
            emotion_level="L1",
            beat_position="B01",
            shot_type="LS",
            camera_action="固定",
        ),
        ShotScript(
            shot_id="P02",
            duration_sec=8,
            location_id="loc_naowu",
            character_ids=["char_fugui"],
            script="场景2使用了美颜滤镜画面唯美油画感",
            dialogue="",
            image_prompt="使用了美颜滤镜画面唯美",
            video_prompt="提示词",
            emotion_level="L2",
            beat_position="B02",
            shot_type="MS",
            camera_action="固定",
        ),
    ]
    result = validator.validate_episode(shots)
    assert result["failed"] == 1, f"应有1个失败镜头，实际{result['failed']}个"
    assert result["failed_shots"][0]["shot_id"] == "P02"


# =============================================================================
# Step45Output 方法测试
# =============================================================================

def test_step45_get_shot_constraints(step45_output):
    c = step45_output.get_shot_constraints("P01")
    assert c["emotion"] == "L1"
    assert c["shot_type"] == "LS"
    assert c["camera_action"] == "固定"


def test_step45_validate_emotion_curve_pass(step45_output):
    # 所有跳转都在矩阵中 → 无违规
    violations = step45_output.validate_emotion_curve()
    # P01:P02=L1→L2, P02:P03=L2→L3, P03:P04=L3→L4, P04:P05=L4→L3, P05:P06=L3→L2, P06:P07=L2→L1 全部合法
    assert len(violations) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
