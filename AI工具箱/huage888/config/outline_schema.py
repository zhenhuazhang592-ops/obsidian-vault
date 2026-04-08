"""outline_schema.py — 漠玫传大纲 JSON Schema（Pydantic）

参考 Toonflow EpisodeData 结构。
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Asset(BaseModel):
    """角色 / 场景 / 道具 共用结构"""
    name: str = Field(..., description="具体名称（原文名字，禁止自行命名）")
    description: str = Field(..., description="描写细节")


class EpisodeOutline(BaseModel):
    """单集大纲（outline-agent 输出目标）"""
    episodeIndex: int = Field(..., ge=1, description="集数，从1开始")
    title: str = Field(..., max_length=8, description="8字内标题，含情绪爆点")
    chapterRange: list[int] = Field(default_factory=list, description="关联章节号数组")
    scenes: list[Asset] = Field(default_factory=list, description="场景列表，按 outline 出场顺序排列")
    characters: list[Asset] = Field(default_factory=list, description="角色列表，按 outline 出场顺序排列，必须是独立个体")
    props: list[Asset] = Field(..., min_length=3, description="道具列表，至少3个")
    coreConflict: str = Field(..., description="核心矛盾：格式 'A想要X vs B阻碍X'")
    outline: str = Field(..., min_length=100, max_length=300, description="100-300字剧情主干，最高优先级")
    openingHook: str = Field(..., description="开场镜头：outline 第一句话的视觉化")
    keyEvents: list[str] = Field(..., min_length=4, max_length=4, description="4个元素数组：[起, 承, 转, 合]")
    emotionalCurve: str = Field(..., description="情绪曲线，如：2(压抑)→5(反抗)→9(爆发)→3(余波)")
    visualHighlights: list[str] = Field(..., min_length=3, max_length=5, description="3-5个标志性镜头，按 outline 顺序排列")
    endingHook: str = Field(..., description="结尾悬念：outline 之后的延伸，勾引下集")
    classicQuotes: list[str] = Field(..., max_length=2, description="1-2句金句，每句≤15字，必须从原文提取")

    @field_validator("title")
    @classmethod
    def title_must_have_emotion(cls, v: str) -> str:
        if not any(c in v for c in "！？?!"):
            raise ValueError("标题应含情绪爆点（疑问/感叹句）")
        return v

    @field_validator("classicQuotes")
    @classmethod
    def quotes_max_length(cls, v: list[str]) -> list[str]:
        for q in v:
            if len(q) > 15:
                raise ValueError(f"金句超长：'{q}'（{len(q)}字），限15字")
        return v


class Shot(BaseModel):
    """单个镜头（storyboard-agent 输出目标）"""
    index: int = Field(..., ge=1, description="镜头序号")
    segmentTitle: str = Field(..., description="片段标题，如'断桥初遇'")
    description: str = Field(..., min_length=10, description="镜头画面描述（50-100字）")
    emotion: str = Field(..., description="情绪：压抑/平静/紧张/爆发/喜悦/悲伤")
    shotType: str = Field(..., description="镜头类型：特写/中景/全景/主观/航拍")
    characters: list[str] = Field(default_factory=list, description="出场角色名（必须使用 outline 中的全名）")
    scene: str = Field(..., description="场景名（必须使用 outline 中的场景名）")
    props: list[str] = Field(default_factory=list, description="道具名列表")
    imagePrompt: str = Field(..., description="英文生图提示词（含风格锚定词）")
    libtvPrompt: Optional[str] = Field(
        default=None,
        description="英文生视频提示词（LibTV直用，≤200字，含动作+运镜+风格）",
    )
    notes: Optional[str] = Field(default=None, description="运镜/时长备注")


class ShotList(BaseModel):
    """整集分镜列表"""
    episode: str = Field(default="S01E01", description="集数标识")
    style: str = Field(default="赛博墨韵", description="视觉风格")
    shots: list[Shot] = Field(..., min_length=1, description="镜头列表")
