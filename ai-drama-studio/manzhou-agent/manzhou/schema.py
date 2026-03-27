"""数据Schema定义 - 12个Step的输入/输出规范（使用dataclass + TypedDict混合）"""

import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional


# =============================================================================
# 通用工具
# =============================================================================

def new_project_id() -> str:
    return f"proj_{uuid.uuid4().hex[:8]}"

def new_shot_id(episode: int, shot: int) -> str:
    return f"EP{episode:02d}_shot_{shot:02d}"

def new_scene_id(episode: int, scene: int) -> str:
    return f"EP{episode:02d}_scene_{scene:02d}"

def new_char_id(index: int) -> str:
    return f"char_{index:02d}"

def new_loc_id(index: int) -> str:
    return f"loc_{index:02d}"


# =============================================================================
# Step 0: 项目配置
# =============================================================================

@dataclass
class ProjectConfig:
    project_id:       str
    project_name:     str
    created_at:       str          # ISO格式时间
    style_preset:     str          # 风格预设枚举
    aspect_ratio:     str          # "9:16" | "16:9"
    shot_duration:    int          # 秒
    target_episodes: int
    main_view_char:  str          # char_XX
    target_platform: str          # 抖音/快手/视频号
    source_type:      str          # "url" | "file" | "existing"
    source_path:      str
    word_count:       int          # 小说字数
    version:          str = "v1.0.0"

    def to_markdown(self) -> str:
        return f"""# 项目配置单

## 基本信息
- **项目ID**: {self.project_id}
- **项目名称**: {self.project_name}
- **创建时间**: {self.created_at}
- **版本**: {self.version}

## 配置选项
| 选项 | 值 |
|------|-----|
| 风格预设 | {self.style_preset} |
| 画幅比例 | {self.aspect_ratio} |
| 单镜头时长 | {self.shot_duration}秒 |
| 目标集数 | {self.target_episodes}集 |
| 主视角角色 | {self.main_view_char} |
| 目标平台 | {self.target_platform} |

## 小说来源
- 类型: {self.source_type}
- 路径/URL: {self.source_path}
- 内容长度: {self.word_count}字
"""


# =============================================================================
# Step 1: 改编Schema
# =============================================================================

@dataclass
class AdaptedScene:
    scene_id:        str
    scene_title:     str
    location:        str
    time:            str          # "白天"/"夜晚"
    characters:      list[str]    # [char_01, char_02]
    conflict:        str          # 核心冲突一句话
    highlight:       bool
    emotion_spike_at: str        # "00:30"
    opening_hook:    str          # 开场5秒抓人描述
    dialogue_count:  int
    avg_dialogue_chars: float

@dataclass
class AdaptedChapter:
    chapter_id:      str
    chapter_title:   str
    scene_count:     int
    total_duration_sec: int
    scenes:          list[AdaptedScene]

@dataclass
class CharacterListItem:
    char_id:   str
    name:      str
    role_type: str          # "主角"/"反派"/"配角"
    appearance_summary: str

@dataclass
class LocationListItem:
    loc_id:      str
    name:        str
    type:        str          # "室内"/"室外"
    atmosphere_keywords: list[str]

@dataclass
class AdaptationResult:
    project_id:         str
    adaptation_version: str
    adapted_chapters:   list[AdaptedChapter]
    character_list:     list[CharacterListItem]
    location_list:      list[LocationListItem]

    def quality_check(self) -> dict:
        """Step 1 质量自检"""
        checks = {
            "has_opening_conflict": False,
            "dialogues_under_15_chars": True,
            "no_inner_monologue": True,
            "emotion_spike_count": 0,
        }
        for ch in self.adapted_chapters:
            for sc in ch.scenes:
                if sc.highlight:
                    checks["emotion_spike_count"] += 1
                if sc.opening_hook:
                    checks["has_opening_conflict"] = True
                if sc.avg_dialogue_chars > 15:
                    checks["dialogues_under_15_chars"] = False
        return checks


# =============================================================================
# Step 2: IP档案Schema
# =============================================================================

@dataclass
class CharacterAppearance:
    face: str; body: str; distinguishing: str; hair: str

@dataclass
class CharacterClothing:
    daily: str; work: str; special: str

@dataclass
class CharacterPersonality:
    traits: list[str]; speech: str; habits: list[str]; conflict_style: str

@dataclass
class CharacterVoice:
    timbre: str; speed: str; accent: str

@dataclass
class CharacterRelationship:
    target: str; type: str; tension: str

@dataclass
class IPCharacter:
    id:               str
    name:             str
    role_type:        str
    age_range:        str
    aliases:          list[str]
    appearance:        CharacterAppearance
    clothing:          CharacterClothing
    personality:       CharacterPersonality
    voice:             CharacterVoice
    relationships:    list[CharacterRelationship]

@dataclass
class IPLocation:
    id:          str
    name:        str
    type:        str
    time:        str
    weather:     str
    atmosphere:  str
    color_temp:   str
    lighting:     str
    key_elements: list[str]
    visual_tags:  list[str]

@dataclass
class IPItem:
    id:          str
    name:        str
    type:        str
    owner:       str
    appearance:   str
    symbolic:     str
    key_scenes:   list[str]

@dataclass
class IPProfile:
    project_id:      str
    ip_profile_version: str
    ip_name:         str
    ip_type:         str
    characters:      dict[str, IPCharacter]   # {char_XX: IPCharacter}
    locations:       dict[str, IPLocation]     # {loc_XX: IPLocation}
    items:           dict[str, IPItem]          # {item_XX: IPItem}
    relationship_map: dict = field(default_factory=dict)


# =============================================================================
# Step 3: 剧本大纲Schema
# =============================================================================

@dataclass
class SceneInfo:
    scene_id:          str
    location_id:       str
    scene_name:        str
    scene_type:        str
    time:              str
    characters:        list[str]
    scene_function:    str   # TENSION/MOOD/REVEAL/ACTION...
    emotion_value:     str   # L1-L5
    beat_position:     str   # B01-B15
    emotion_turning_point: str

@dataclass
class EmotionCurvePoint:
    time:       str
    level:      str
    description: str

@dataclass
class EmotionTurningPoint:
    time:       str
    type:       str
    description: str

@dataclass
class EmotionCurve:
    curve_data:      list[EmotionCurvePoint]
    turning_points: list[EmotionTurningPoint]

@dataclass
class ScriptOutline:
    project_id:    str
    episode:       str
    script_version: str
    basic_info:     dict
    scene_list:    list[SceneInfo]
    emotion_curve: EmotionCurve


# =============================================================================
# Step 4.5: 导演控制塔Schema
# =============================================================================

@dataclass
class D1EmotionBaseline:
    emotion_type:       str
    color_temp:         str
    narrative_pace:     str
    core_emotion:       str
    emotion_turning_points: list[str]

@dataclass
class D2SceneBeat:
    scene_id:     str
    scene_name:   str
    function:     str
    emotion_value: str
    beat_position: str
    core_action:  str

@dataclass
class D3BeatTracking:
    time_range:      str
    shot_id:        str
    emotion_curve:  str   # "L1→L2"
    beat_type:      str
    director_intent: str

@dataclass
class CameraIntent:
    shot_type:    str
    camera_action: str
    lighting_note: str
    color_note:   str

@dataclass
class AxisConstraint:
    enabled:    bool
    axis_line:  str
    char_a_side: str
    char_b_side: str

@dataclass
class D4CameraIntent:
    shot_id:        str
    time_range:     str
    emotion_state: str
    beat_position:  str
    camera_intent: CameraIntent
    axis_constraint: AxisConstraint
    prohibited:     list[str]

@dataclass
class ConstraintSummary:
    total_shots:       int
    emotion_jump_rules: str
    ecu_rules:         str
    axis_rules:        str
    prohibited_keywords: list[str]  # 全集统一的禁止词列表
    prohibited_style:   list[str]  # 风格特定的禁止词

@dataclass
class DirectorControlTower:
    project_id:            str
    episode:               str
    control_tower_version: str
    D1_emotion_baseline:   D1EmotionBaseline
    D2_scene_beat_table:   list[D2SceneBeat]
    D3_beat_tracking:      list[D3BeatTracking]
    D4_camera_intent:      list[D4CameraIntent]
    constraint_summary:    ConstraintSummary


# =============================================================================
# Step 5: 资产库Schema
# =============================================================================

@dataclass
class AppearanceLock:
    姓名: str; 性别: str; 年龄区间: str
    面部特征: dict; 体型: str; 标志性特征: str
    发型: str; 发色: str

@dataclass
class StyleLock:
    服装风格: dict; 妆容风格: str; 配饰: list[str]; 道具: list[str]

@dataclass
class BehaviorLock:
    表情习惯: str; 肢体语言: str; 动态特征: str; 声音特征: str

@dataclass
class DNALock:
    appearance_lock: AppearanceLock
    style_lock:      StyleLock
    behavior_lock:   BehaviorLock

@dataclass
class NineGridRef:
    slot:        str
    oss_url:     str
    description: str
    scene_tag:   str

@dataclass
class CharacterAsset:
    id:             str
    name:           str
    dna_lock:       DNALock
    nine_grid_refs: list[NineGridRef]
    dna_prompt_keywords: str

@dataclass
class AtmosphereDesc:
    光线: str; 色调: str; 陈设: str

@dataclass
class LocationAsset:
    id:               str
    name:             str
    type:             str
    time:             str
    atmosphere_desc:  AtmosphereDesc
    key_elements:     list[str]
    atmosphere_image_oss_url: str
    ai_prompt_template: str

@dataclass
class AssetLibrary:
    project_id:        str
    asset_library_version: str
    characters:        dict[str, CharacterAsset]
    locations:         dict[str, LocationAsset]


# =============================================================================
# Step 7: 分镜脚本Schema（核心产出）
# =============================================================================

@dataclass
class AudioLayer:
    bgm:  str   # "爵士乐，萨克斯风，渐弱"
    sfx:  str   # "雨声渐弱，远处传来汽车喇叭"

@dataclass
class ShotScriptMeta:
    """每镜 Prompt 元数据 — 强制携带，不可缺失"""
    char_ids_source:   list[str]   # 必须在 IP档案 中存在
    loc_id_source:     str         # 必须在 IP档案 中存在
    emotion_from_d3:   str         # 必须来自 D3_beat_tracking
    shot_type_from_d4: str         # 必须来自 D4_camera_intent
    prohibited_check:  list[str]   # 必须来自 DirectorControlTower.prohibited
    style_anchor:     str         # 必须来自项目配置（写实/动漫/古风等）
    prompt_meta_version: str = "v10"  # 版本锁定，不允许降级


@dataclass
class ShotScript:
    shot_id:       str
    duration_sec:  int
    location_id:   str
    character_ids: list[str]
    script:        str          # 分场内容描述
    dialogue:      str          # ≤15字对白
    image_prompt:  str          # AI生图Prompt（供人工执行）
    video_prompt:  str          # AI视频Prompt（供人工执行）
    emotion_level: str          # L1-L5
    beat_position: str          # B01-B15
    shot_type:     str          # ECU/CU/MS/LS...
    camera_action: str          # 固定/推进/拉远...
    audio_layer:   Optional[AudioLayer] = None
    meta:          Optional["ShotScriptMeta"] = None  # 约束引用元数据

    def to_markdown(self, index: int) -> str:
        audio = self.audio_layer
        bgm_line = f"- **BGM**: {audio.bgm}" if (audio and audio.bgm) else ""
        sfx_line = f"- **SFX**: {audio.sfx}" if (audio and audio.sfx) else ""
        meta_line = ""
        if self.meta:
            meta_line = (
                f"- **约束引用**: char={self.meta.char_ids_source} "
                f"loc={self.meta.loc_id_source} "
                f"emotion={self.meta.emotion_from_d3} "
                f"prohibited={self.meta.prohibited_check}"
            )
        return f"""### 镜头 {index}: {self.shot_type}（{self.duration_sec}秒）

**[{self.beat_position}] {self.script}**

- **角色**: {', '.join(self.character_ids)}
- **场景**: {self.location_id}
- **情绪**: {self.emotion_level}
- **景别**: {self.shot_type}
- **运镜**: {self.camera_action}
- **对白**: 「{self.dialogue}」
{bgm_line}
{sfx_line}
{meta_line}

**Image Prompt:**（供人工执行）
{self.image_prompt}

**Video Prompt:**（供人工执行）
{self.video_prompt}
"""

@dataclass
class EpisodeShotScript:
    project_id:          str
    episode:             str
    shot_script_version: str
    total_duration_sec:  int
    total_shots:         int
    shots:               list[ShotScript]
    asset_library_ref:   str   # 资产库路径
    control_tower_ref:   str   # 导演控制塔路径


# =============================================================================
# 跨步 Schema 契约 — 定义 Step 间的输入/输出约束
# =============================================================================

@dataclass
class Step0Output:
    """Step 0 输出契约"""
    project_id:       str
    style_preset:     str
    aspect_ratio:     str
    shot_duration:    int
    prohibited_global: list[str]   # 全局禁止词（来自 constants.PROHIBITED_KEYWORDS）


@dataclass
class Step45Output:
    """Step 4.5（导演控制塔）输出契约"""
    project_id:         str
    episode:            str
    emotion_baseline:   str         # "虐/悲" / "甜/爽" 等
    color_temp_range:   tuple       # (start_color, end_color) e.g. ("暖黄", "灰暗")
    emotion_curve:      list[str]   # ["L1→L2", "L2→L3", ...]
    prohibited_keywords: list[str]  # 本集禁止词
    shot_emotion_map:   dict[str, str]   # {"P01": "L1", "P02": "L2", ...}
    shot_camera_map:    dict[str, dict]   # {"P01": {"shot_type": "LS", "camera_action": "固定"}, ...}

    def get_shot_constraints(self, shot_id: str) -> dict:
        """获取指定镜头的所有约束（供 schema_validator 调用）"""
        return {
            "emotion":       self.shot_emotion_map.get(shot_id, "L1"),
            "shot_type":     self.shot_camera_map.get(shot_id, {}).get("shot_type", "MS"),
            "camera_action": self.shot_camera_map.get(shot_id, {}).get("camera_action", "固定"),
            "prohibited":    self.prohibited_keywords,
        }

    def validate_emotion_curve(self) -> list[str]:
        """返回所有违规的情绪跳转"""
        from .constants import is_emotion_jump_allowed
        violations = []
        for item in self.emotion_curve:
            # 每项格式如 "L1→L2" → 校验 L1→L2 是否允许
            parts = item.split("→")
            if len(parts) == 2:
                from_lvl, to_lvl = parts[0].strip(), parts[1].strip()
                if not is_emotion_jump_allowed(from_lvl, to_lvl):
                    violations.append(f"禁止跳转: {from_lvl}→{to_lvl}")
        return violations
