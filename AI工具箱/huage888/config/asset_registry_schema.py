"""asset_registry_schema.py — 资产库 manifest JSON Schema（Pydantic）

角色类型说明（对应 seedream_templates.py 多视角生成）：
  角色（character）：
    character_front_full        正面全身
    character_face_closeup     正面特写（面部）
    character_side_full        侧面全身
    character_side_closeup     侧面特写
    character_back_full       背面全身
    character_three_quarter_full  四分之三视角全身
    action_happy / action_angry / action_shy / action_turning  情绪姿态
  场景（scene）：
    scene_wide                全景建立镜头
    scene_medium              中景
    scene_detail_closeup      特写细节
  道具（prop）：
    prop_front                正面
    prop_side                 侧面
    prop_three_quarter       四分之三视角
    prop_detail               细节特写
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import date


class AssetFile(BaseModel):
    """单个资产文件记录"""
    filename: str = Field(..., description="文件名，如 character_front_full.png")
    role: str = Field(..., description=(
        "资产视角角色，对应 seedream_templates 生成的角色类型："
        "character_front_full / character_face_closeup / character_side_full / "
        "character_back_full / character_three_quarter_full / "
        "scene_wide / scene_medium / scene_detail_closeup / "
        "prop_front / prop_side / prop_three_quarter / prop_detail"
    ))
    view_key: Optional[str] = Field(
        default=None,
        description="seedream_templates 中的 view_key（如 front_full, side_closeup）"
    )
    prompt: Optional[str] = Field(
        default=None,
        description="生成此文件时使用的完整 Seedream prompt"
    )
    uploaded_at: str = Field(..., description="上传日期 YYYY-MM-DD")
    file_path: str = Field(..., description="相对于 assets/library/ 的路径")


class AssetManifest(BaseModel):
    """资产完整 manifest（对应 assets/library/{type}/{name}/manifest.json）"""
    name: str = Field(..., description="资产名称（必须与 outline 中的 name 一致）")
    type: str = Field(..., description="类型：character / scene / prop")
    role_type: Optional[str] = Field(default=None, description="中文类型：角色/场景/道具")
    project: Optional[str] = Field(default=None, description="所属项目")
    first_episode: Optional[str] = Field(default=None, description="首次出现集数")
    visual_description: Optional[str] = Field(
        default=None,
        description="视觉描述（来自 outline JSON 的 description 字段）"
    )
    seedream_card: Optional[str] = Field(
        default=None,
        description="Seedream 角色卡路径，如 seedream_card.md"
    )
    files: list[AssetFile] = Field(
        default_factory=list,
        description="文件列表（多视角生成的各视角图）"
    )
    status: str = Field(
        default="pending",
        description=(
            "资产状态：pending（已注册待生成）/ card_generated（Seedream卡已生成）"
            "/ reference_generated（多视角参考图已生成）/ uploaded（已上传LibTV）"
        )
    )
    created_at: str = Field(
        default_factory=lambda: date.today().isoformat(),
        description="创建日期"
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="最后更新时间"
    )

