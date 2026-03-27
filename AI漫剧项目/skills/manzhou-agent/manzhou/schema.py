"""
Schema 定义模块
定义 S0-S5 全链路数据结构规范
"""

# ─── S2: CDP 角色 DNA ───────────────────────────────────────
CHARACTER_DNA_SCHEMA = {
    "id": {"type": "string", "pattern": "^char_[a-z_]+$", "required": True},
    "name": {"type": "string", "required": True},
    "gender": {"type": "enum", "values": ["male", "female", "unknown"], "required": True},
    "age_range": {"type": "string", "required": True, "example": "20-80"},
    "visual": {
        "type": "object",
        "required": True,
        "fields": {
            "face_shape": {"type": "string", "required": True},
            "skin_tone": {"type": "string", "required": True},
            "eye_features": {"type": "string", "required": True},
            "body_type": {"type": "string", "required": True},
            "clothing": {
                "type": "object",
                "required": True,
                "fields": {
                    "young": {"type": "string", "required": True},
                    "middle": {"type": "string", "required": True},
                    "old": {"type": "string", "required": True},
                }
            },
            "palette": {"type": "string", "required": True},  # 引用S1色调
        }
    },
    "expression_normal": {"type": "string", "required": True},
    "expression_strong": {"type": "string", "required": True},
    "constraints": {
        "type": "list",
        "required": True,
        "min_items": 1,
        "item_type": "string",
        "example": ["禁止: 年轻时不能画皱纹", "禁止: 不能画现代发型"]
    },
    "reference_prompt": {"type": "string", "required": True},
    "used_in_scenes": {"type": "list", "item_type": "string", "required": True},
}

# ─── S2: CDP 场景 DNA ───────────────────────────────────────
SCENE_DNA_SCHEMA = {
    "id": {"type": "string", "pattern": "^scene_[a-z_]+$", "required": True},
    "name": {"type": "string", "required": True},
    "era": {"type": "string", "required": True},  # 必须匹配S0
    "description": {"type": "string", "required": True},
    "visual": {
        "type": "object",
        "required": True,
        "fields": {
            "space_type": {"type": "enum", "values": ["indoor", "outdoor", "semi_indoor"], "required": True},
            "architecture": {"type": "string", "required": True},
            "lighting": {"type": "string", "required": True},
            "color_temperature": {"type": "enum", "values": ["warm", "cool", "neutral"], "required": True},
            "key_props": {"type": "list", "item_type": "string", "required": True},
        }
    },
    "constraints": {
        "type": "list",
        "required": True,
        "min_items": 1,
        "item_type": "string",
    },
    "reference_prompt": {"type": "string", "required": True},
}

# ─── S2: CDP 道具 DNA ───────────────────────────────────────
ITEM_DNA_SCHEMA = {
    "id": {"type": "string", "pattern": "^item_[a-z_]+$", "required": True},
    "name": {"type": "string", "required": True},
    "era": {"type": "string", "required": True},
    "description": {"type": "string", "required": True},
    "visual": {
        "type": "object",
        "required": True,
        "fields": {
            "material": {"type": "string", "required": True},
            "color": {"type": "string", "required": True},
            "size": {"type": "string", "required": True},
        }
    },
    "constraints": {"type": "list", "item_type": "string", "required": True},
    "reference_prompt": {"type": "string", "required": True},
}

# ─── S1: 风格指南 ───────────────────────────────────────────
STYLE_GUIDE_SCHEMA = {
    "version": {"type": "string", "required": True, "example": "v1.0.0"},
    "style": {"type": "string", "required": True},  # 如: 写实/动漫/水墨
    "aspect_ratio": {"type": "string", "required": True, "example": "9:16"},
    "shot_duration_sec": {"type": "integer", "required": True, "example": 15},
    "color_palette": {
        "type": "object",
        "required": True,
        "fields": {
            "dominant": {"type": "string", "required": True},  # 主色调
            "secondary": {"type": "string", "required": True},  # 辅助色
            "accent": {"type": "string", "required": True},    # 点缀色
            "prohibition": {"type": "list", "item_type": "string", "required": True},  # 禁用色
        }
    },
    "lighting_rules": {
        "type": "object",
        "required": True,
        "fields": {
            "type": {"type": "enum", "values": ["natural", "hard", "soft", "mixed"], "required": True},
            "time_of_day": {"type": "string", "required": True},  # 如: 自然光/黄昏/夜晚
            "prohibition": {"type": "list", "item_type": "string", "required": True},
        }
    },
    "camera_rules": {
        "type": "object",
        "required": True,
        "fields": {
            "standard_lens": {"type": "string", "required": True},  # 标准镜头
            "movement_patterns": {"type": "list", "item_type": "string", "required": True},
            "prohibition": {"type": "list", "item_type": "string", "required": True},
        }
    },
    "sound_rules": {
        "type": "object",
        "required": True,
        "fields": {
            "bgm_style": {"type": "string", "required": True},  # 背景乐风格
            "sfx_types": {"type": "list", "item_type": "string", "required": True},
            "prohibition": {"type": "list", "item_type": "string", "required": True},
        }
    },
    "character_design_rules": {
        "type": "object",
        "required": True,
        "fields": {
            "proportions": {"type": "string", "required": True},
            "prohibition": {"type": "list", "item_type": "string", "required": True},
        }
    },
    "era_constraints": {
        "type": "object",
        "required": True,
        "fields": {
            "allowed_eras": {"type": "list", "item_type": "string", "required": True},
            "prohibition": {"type": "list", "item_type": "string", "required": True},
        }
    },
}


def validate_all_schemas():
    """验证所有 Schema 定义完整性"""
    schemas = {
        "character_dna": CHARACTER_DNA_SCHEMA,
        "scene_dna": SCENE_DNA_SCHEMA,
        "item_dna": ITEM_DNA_SCHEMA,
        "style_guide": STYLE_GUIDE_SCHEMA,
    }
    # 验证每个 schema 的 required 字段不为空
    for name, schema in schemas.items():
        for field, spec in schema.get("fields", {}).items():
            if spec.get("required") and spec.get("example") is None:
                raise ValueError(f"{name}.{field} required but no example provided")
    return schemas


if __name__ == "__main__":
    # 验证 Schema 定义
    print("[Schema] 验证所有 Schema 定义...")
    result = validate_all_schemas()
    print(f"[Schema] ✓ 验证通过，共 {len(result)} 个 Schema")
    for name in result:
        print(f"  - {name}")
