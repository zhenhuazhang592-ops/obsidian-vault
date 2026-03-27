"""漫舟拉片智能体 - 数据类型定义"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AudioLayer:
    """Audio Layer v6.2 四分栏"""
    music: str = "无"           # MUSIC
    sfx_ambient: str = "无"     # SFX-AMBIENT
    sfx_narrative: str = "无"  # SFX-NARRATIVE
    sfx_emotion: str = "无"    # SFX-EMOTION

    def to_markdown(self) -> str:
        lines = [
            f"MUSIC:         {self.music}",
            f"SFX-AMBIENT:   {self.sfx_ambient}",
            f"SFX-NARRATIVE: {self.sfx_narrative}",
            f"SFX-EMOTION:   {self.sfx_emotion}",
        ]
        return "\n".join(lines)


@dataclass
class ShotAnalysis:
    """单个镜头的分镜分析结果（TapNow 14列 + 漫舟增强）"""
    shot_number: int
    start_time: float
    end_time: float
    duration: float
    shot_size: str = ""             # MS / CU / MCU / WS / ELS
    camera_angle: str = ""          # 平视 / 俯拍 / 仰拍 / 过肩
    camera_movement: str = ""       # 固定 / 推 / 拉 / 摇 / 移 / 跟随
    yaw: int = 0                   # 水平角（度）
    pitch: int = 0                 # 垂直角（度）
    dolly: str = "z"               # z=固定, in=推, out=拉
    lighting_style: str = ""        # 自然光 / 三点布光 / ...
    color_temperature: int = 0      # K值
    depth_of_field: str = ""        # Shallow / Deep / f/1.4
    description: str = ""           # 分镜描述（含【【char_XX】】标记）
    visual_description: str = ""    # 画面描述（含色温K值）
    dialogue: str = "无"
    viseme: str = "无"              # V0-V11 音素序列
    audio_layer: AudioLayer = field(default_factory=AudioLayer)
    keyframe_times: list[float] = field(default_factory=list)
    extracted_frames: list[str] = field(default_factory=list)   # 帧路径
    transition: str = "硬切"
    narrative_function: str = ""
    visual_hook: str = ""
    props: str = "无"
    imagePrompt: str = ""
    videoPrompt: str = ""


@dataclass
class LapianConfig:
    """CLI 配置"""
    video_path: str
    output_dir: str = "./拉片分析"
    cdp_path: Optional[str] = None
    model: str = "gemini"          # zhipu / claude / gemini
    threshold: float = 27.0         # PySceneDetect 阈值
    shots_per_shot: int = 3         # 每镜头抽帧数
    dry_run: bool = False


@dataclass
class LapianResult:
    """完整拉片结果"""
    video_path: str
    video_id: str
    video_duration: float
    total_shots: int
    analysis_model: str
    scene_threshold: float
    shots: list[ShotAnalysis] = field(default_factory=list)
    output_dir: str = ""
    video_filename: str = ""


@dataclass
class CDPData:
    """CDP 资产库数据"""
    characters: dict = field(default_factory=dict)
    locations: dict = field(default_factory=dict)

    def get_context(self) -> str:
        """生成 AI 可用的 CDP 上下文"""
        lines = []
        for cid, c in self.characters.items():
            desc = c.get("description", c.get("name", ""))
            lines.append(f"【【{cid}】】：{desc}")
        for lid, l in self.locations.items():
            desc = l.get("description", l.get("name", ""))
            lines.append(f"【【{lid}】】：{desc}")
        return "\n".join(lines) if lines else "无CDP上下文"
