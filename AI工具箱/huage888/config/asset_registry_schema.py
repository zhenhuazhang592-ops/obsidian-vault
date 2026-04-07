"""asset_registry_schema.py — 资产库 manifest JSON Schema（Pydantic）"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import date


class AssetFile(BaseModel):
    filename: str = Field(..., description="文件名，如 ref_01.png")
    role: str = Field(..., description="角色：front_view/multi_angle/scene_wide/scene_detail/prop_full")
    uploaded_at: str = Field(..., description="上传日期 YYYY-MM-DD")
    file_path: str = Field(..., description="相对于 assets/library/ 的路径")


class AssetManifest(BaseModel):
    name: str = Field(..., description="资产名称（必须与 outline 中的 name 一致）")
    type: str = Field(..., description="类型：character / scene / prop")
    role_type: Optional[str] = Field(default=None, description="角色类型：人物/场景/道具")
    project: Optional[str] = Field(default=None, description="所属项目")
    first_episode: Optional[str] = Field(default=None, description="首次出现集数")
    visual_description: Optional[str] = Field(default=None, description="视觉描述（来自 outline）")
    seedream_card: Optional[str] = Field(default=None, description="Seedream 卡文件名，如 character_card.md")
    files: list[AssetFile] = Field(default_factory=list, description="文件列表")
    status: str = Field(default="pending", description="状态：pending/card_generated/reference_generated")
    created_at: str = Field(default_factory=lambda: date.today().isoformat(), description="创建日期")
