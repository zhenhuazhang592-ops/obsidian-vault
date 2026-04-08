#!/usr/bin/env python3
"""
seedream_templates.py — Seedream 多视角提示词模板库

功能：
  - 角色多视角提示词生成（front/side/back/view_closeup 四视角）
  - 场景多视角提示词生成（establishing/medium/detail 三镜头）
  - 道具多视角提示词生成（3-4 个标准角度）
  - 支持 Visual Bible 风格注入
  - 生成 seedream_card.md（角色卡文档）

用法：
  from config.seedream_templates import (
      build_character_card, build_scene_prompts, build_prop_prompts,
      render_character_prompt, inject_visual_bible_style,
  )
"""

from pathlib import Path
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════
# 风格锚定词库（按 Visual Bible 风格注入）
# ═══════════════════════════════════════════════════════════════════════════

STYLE_ANCHORS: dict[str, str] = {
    "赛博墨韵": (
        "cyberpunk ink wash aesthetic, dark teal and ink black color palette, "
        "glowing blue data particles, chinese ink brushstroke textures, "
        "neo-taoist temple atmosphere, cinematic, ultra detailed, 8k"
    ),
    "古风烟雨": (
        "ancient chinese style, ink wash painting aesthetic, misty rain atmosphere, "
        "traditional chinese architecture, cool grey-blue tones with white accents, "
        "cinematic, ultra detailed, 8k"
    ),
    "古风喜剧": (
        "ancient chinese comedy style, warm golden lighting, vibrant colors, "
        "traditional chinese costume drama aesthetic, cinematic, ultra detailed, 8k"
    ),
    "3D国漫CG": (
        "3D CGI chinese animation style, PBR materials, cinematic lighting, "
        "high contrast, ultra detailed, 8k resolution, professional studio lighting"
    ),
    "写实都市": (
        "realistic modern urban style, natural lighting, warm tones, "
        "photorealistic, cinematic, ultra detailed, 8k"
    ),
    "自然纪录": (
        "nature documentary style, macro photography, sunlit, bokeh background, "
        "product photography aesthetic, ultra detailed, 8k"
    ),
    "赛博朋克": (
        "cyberpunk aesthetic, neon lighting, dark city atmosphere, "
        "rain-soaked streets, holographic displays, cinematic, ultra detailed, 8k"
    ),
    "东方禅意": (
        "eastern zen aesthetic, minimalist composition, soft natural lighting, "
        "meditation atmosphere, ultra detailed, 8k, cinematic"
    ),
    "default": (
        "cinematic quality, ultra detailed, 8k resolution, "
        "professional lighting, sharp focus"
    ),
}


def get_style_anchor(style_keywords: str | None) -> str:
    """根据 Visual Bible 风格关键词匹配锚定词"""
    if not style_keywords:
        return STYLE_ANCHORS["default"]
    # 精确匹配
    for key in STYLE_ANCHORS:
        if key in style_keywords or style_keywords in key:
            return STYLE_ANCHORS[key]
    # 模糊匹配
    for key, anchor in STYLE_ANCHORS.items():
        kw_list = style_keywords.lower().split()
        if any(k in key.lower() for k in kw_list if len(k) > 3):
            return anchor
    return STYLE_ANCHORS["default"]


def inject_visual_bible_style(
    base_prompt: str,
    style_keywords: str | None = None,
    extra_tags: str | None = None,
) -> str:
    """
    将 Visual Bible 风格注入 prompt。

    Args:
        base_prompt: 资产的基础描述
        style_keywords: Visual Bible 中的风格关键词（如"赛博墨韵"）
        extra_tags: 额外追加的标签（如"古风书房"场景词）
    """
    anchor = get_style_anchor(style_keywords)
    parts = [anchor]
    if base_prompt:
        parts.append(base_prompt)
    if extra_tags:
        parts.append(extra_tags)
    return ", ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# 角色多视角提示词模板
# ═══════════════════════════════════════════════════════════════════════════

CHARACTER_VIEW_TEMPLATES: dict[str, str] = {
    # ── 核心锚定（定稿后永远不改）────────────────────────────────────────
    "core_anchor": (
        "{style_anchor}, "
        "same face, consistent character, identical facial features, "
        "same costume, identical clothing, same accessories, "
        "consistent character design sheet, 3D render style"
    ),
    # ── 正面全身 ────────────────────────────────────────────────────────
    "front_full": (
        "{core_anchor}, "
        "front view, full body, standing pose, neutral calm expression, "
        "facing camera directly, hands at sides or gentle gesture"
    ),
    # ── 正面特写 ────────────────────────────────────────────────────────
    "front_closeup": (
        "{core_anchor}, "
        "front view, close-up face, upper body framing, "
        "neutral expression, slight smile optional, eyes looking at camera"
    ),
    # ── 侧面全身 ────────────────────────────────────────────────────────
    "side_full": (
        "{core_anchor}, "
        "side view, full body, profile pose, "
        "3/4 turned away from camera, confident stance"
    ),
    # ── 侧面特写 ──────────────────────────────────────────────────────
    "side_closeup": (
        "{core_anchor}, "
        "side view, close-up face, profile angle, "
        "looking into distance or slightly downward"
    ),
    # ── 背面全身 ─────────────────────────────────────────────────────────
    "back_full": (
        "{core_anchor}, "
        "back view, full body, walking or standing away from camera, "
        "showing hairstyle and back details of costume"
    ),
    # ── 背面特写 ───────────────────────────────────────────────────────
    "back_closeup": (
        "{core_anchor}, "
        "back view, close-up, showing back of hairstyle and accessories, "
        "3/4 back angle"
    ),
    # ── 四分之三视角（最常用）───────────────────────────────────────────
    "three_quarter_full": (
        "{core_anchor}, "
        "three-quarter view, full body, slightly turned from camera, "
        "confident elegant stance, natural arm position"
    ),
    # ── 动作姿态（按情绪变化）───────────────────────────────────────────
    "action_happy": (
        "{core_anchor}, "
        "three-quarter view, full body, happy smile expression, "
        "joyful open posture, dynamic pose"
    ),
    "action_angry": (
        "{core_anchor}, "
        "front view, full body, intense angry expression, "
        "dramatic power pose, commanding stance"
    ),
    "action_shy": (
        "{core_anchor}, "
        "side view, full body, shy expression, blushing cheeks, "
        "nervous subtle pose, arms slightly raised"
    ),
    "action_turning": (
        "{core_anchor}, "
        "dynamic turning motion, mid-turn, showing transition from side to front, "
        "dramatic movement blur optional"
    ),
}


def render_character_prompt(
    view_key: str,
    character_desc: str,
    style_keywords: str | None = None,
    extra_fixed_desc: str = "",
) -> str:
    """
    渲染角色单视角 Seedream prompt。

    Args:
        view_key: 视角键（如 "front_full", "side_closeup"）
        character_desc: 角色外貌核心描述（定稿后不改）
        style_keywords: Visual Bible 风格关键词
        extra_fixed_desc: 服装/饰品/道具等固定描述（定稿后不改）
    """
    template = CHARACTER_VIEW_TEMPLATES.get(view_key, CHARACTER_VIEW_TEMPLATES["three_quarter_full"])
    core_anchor = (
        "{style_anchor}, "
        "same face, consistent character, identical facial features, "
        "same costume, identical clothing, same accessories, "
        "consistent character design sheet, 3D render style"
    ).format(style_anchor=get_style_anchor(style_keywords))

    prompt = template.format(core_anchor=core_anchor)
    # 组装完整 prompt：风格锚定 → 角色描述 → 固定描述 → 视角变量 → 质量尾缀
    full_parts = [
        get_style_anchor(style_keywords),
        character_desc,
        extra_fixed_desc,
        prompt,
        "masterpiece, best quality, 8k resolution, professional lighting",
    ]
    return ", ".join(p for p in full_parts if p)


def build_character_card(
    name: str,
    character_desc: str,
    costume_desc: str = "",
    accessory_desc: str = "",
    style_keywords: str | None = None,
    view_list: list[str] | None = None,
) -> dict[str, str]:
    """
    生成角色完整 Seedream 卡（含多视角 prompt + 角色卡 Markdown）。

    Returns:
        {
            "prompts": {"front_full": "...", "side_full": "...", ...},
            "card_md": "..."  # seedream_card.md 内容
        }
    """
    if view_list is None:
        view_list = [
            "front_full",      # 正面全身（最基础）
            "front_closeup",   # 正面特写
            "side_full",       # 侧面全身
            "side_closeup",   # 侧面特写
            "back_full",       # 背面全身
            "three_quarter_full",  # 四分之三视角
        ]

    # 定稿部分（用于所有视角）
    fixed_parts = [character_desc]
    if costume_desc:
        fixed_parts.append(costume_desc)
    if accessory_desc:
        fixed_parts.append(accessory_desc)
    fixed_text = ", ".join(fixed_parts)

    prompts: dict[str, str] = {}
    for view_key in view_list:
        prompts[view_key] = render_character_prompt(
            view_key=view_key,
            character_desc=character_desc,
            style_keywords=style_keywords,
            extra_fixed_desc=fixed_text,
        )

    # 生成角色卡 Markdown
    card_lines = [
        f"# Seedream Character Card — {name}",
        "",
        "## 使用说明",
        "以下 prompt 为角色一致性标准。每次出图必须：",
        "1. 整段复制【定稿描述】部分（①②③）",
        "2. 仅修改【本镜变量】的视角/表情/姿态",
        "3. 固定【质量尾缀】不变",
        "",
        "## 定稿描述（定稿后永远不改）",
        "",
        "### ① 风格锚定",
        f"```\n{get_style_anchor(style_keywords)}\n```",
        "",
        "### ② 外貌核心",
        f"```\n{character_desc}\n```",
        "",
        "### ③ 服装饰品（已定稿）",
    ]
    if costume_desc:
        card_lines.append(f"```\n{costume_desc}\n```\n")
    if accessory_desc:
        card_lines.append(f"```\n{accessory_desc}\n```\n")

    card_lines += [
        "",
        "## 多视角 prompt（按需选用）",
    ]
    view_labels = {
        "front_full": "正面全身",
        "front_closeup": "正面特写",
        "side_full": "侧面全身",
        "side_closeup": "侧面特写",
        "back_full": "背面全身",
        "back_closeup": "背面特写",
        "three_quarter_full": "四分之三全身",
        "action_happy": "开心动作",
        "action_angry": "愤怒动作",
        "action_shy": "害羞动作",
        "action_turning": "转身动作",
    }
    for view_key, prompt in prompts.items():
        label = view_labels.get(view_key, view_key)
        card_lines += [
            f"### {label}（{view_key}）",
            "```",
            prompt,
            "```",
            "",
        ]

    card_lines += [
        "## 质量尾缀（固定不变）",
        "```",
        "masterpiece, best quality, 8k resolution, professional lighting",
        "```",
    ]

    return {
        "prompts": prompts,
        "card_md": "\n".join(card_lines),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 场景多视角提示词模板
# ═══════════════════════════════════════════════════════════════════════════

SCENE_VIEW_TEMPLATES: dict[str, str] = {
    "establishing": (
        "{style_anchor}, "
        "wide establishing shot, full scene overview, "
        "consistent environment, same room, same spatial layout, "
        "no characters, empty room, establishing atmosphere, "
        "{lighting_desc}, "
        "wide angle, eye-level, showing full room"
    ),
    "medium": (
        "{style_anchor}, "
        "medium shot, consistent environment, same room, same spatial layout, "
        "no characters, empty room, "
        "{lighting_desc}, "
        "medium angle, focusing on {focus_area}, "
        "cinematic framing"
    ),
    "detail_closeup": (
        "{style_anchor}, "
        "close-up detail shot, consistent environment, same room, same props, "
        "no characters, empty room, "
        "{lighting_desc}, "
        "macro lens feel, focusing on {focus_detail}, "
        "ultra detailed textures"
    ),
    "overhead": (
        "{style_anchor}, "
        "overhead bird's eye view, consistent environment, same room layout, "
        "no characters, empty room, "
        "{lighting_desc}, "
        "top-down angle, architectural view"
    ),
    "low_angle": (
        "{style_anchor}, "
        "low angle looking up, consistent environment, same room, same props, "
        "no characters, empty room, "
        "{lighting_desc}, "
        "dramatic perspective, impressive atmosphere"
    ),
}


def render_scene_prompt(
    view_key: str,
    scene_desc: str,
    props_furniture: str = "",
    style_keywords: str | None = None,
    lighting_desc: str = "natural ambient light, cinematic",
    focus_area: str = "the scene",
    focus_detail: str = "detailed textures",
) -> str:
    """渲染场景单视角 Seedream prompt"""
    template = SCENE_VIEW_TEMPLATES.get(view_key, SCENE_VIEW_TEMPLATES["establishing"])
    prompt = template.format(
        style_anchor=get_style_anchor(style_keywords),
        lighting_desc=lighting_desc,
        focus_area=focus_area,
        focus_detail=focus_detail,
    )
    parts = [
        get_style_anchor(style_keywords),
        scene_desc,
        props_furniture,
        prompt,
        "masterpiece, best quality, ultra detailed textures, sharp focus",
    ]
    return ", ".join(p for p in parts if p)


def build_scene_prompts(
    name: str,
    scene_desc: str,
    props_furniture: str = "",
    floor_walls: str = "",
    style_keywords: str | None = None,
    lighting_options: dict[str, str] | None = None,
) -> dict[str, str]:
    """
    生成场景多视角 prompt 字典。

    Args:
        name: 场景名称
        scene_desc: 场景类型描述（定稿后不改）
        props_furniture: 道具家具清单（定稿后不改）
        floor_walls: 地面墙面材质描述
        style_keywords: Visual Bible 风格关键词
        lighting_options: 光线变体 {"day": "...", "night": "...", "candlelight": "..."}
    """
    if lighting_options is None:
        lighting_options = {
            "default": "natural ambient light, cinematic atmosphere",
            "moody": "dramatic moody lighting, volumetric light rays, deep shadows",
            "bright": "bright warm lighting, high key, clean atmosphere",
        }

    view_list = ["establishing", "medium", "detail_closeup"]
    prompts: dict[str, str] = {}

    for view_key in view_list:
        lighting = lighting_options.get("default", lighting_options.get(list(lighting_options)[0]))
        prompts[view_key] = render_scene_prompt(
            view_key=view_key,
            scene_desc=scene_desc,
            props_furniture=props_furniture,
            style_keywords=style_keywords,
            lighting_desc=lighting,
            focus_area="the room" if view_key == "medium" else "decorative details",
            focus_detail="textures and materials" if view_key == "detail_closeup" else "furniture details",
        )

    return prompts


# ═══════════════════════════════════════════════════════════════════════════
# 道具多视角提示词模板
# ═══════════════════════════════════════════════════════════════════════════

PROP_VIEW_TEMPLATES: dict[str, str] = {
    "front": (
        "{style_anchor}, "
        "product visualization, isolated object, consistent prop design, "
        "same object, identical details, "
        "front view, centered, "
        "studio lighting, white background, no shadows, "
        "{material_desc}, "
        "{size_desc}"
    ),
    "side": (
        "{style_anchor}, "
        "product visualization, isolated object, consistent prop design, "
        "same object, identical details, "
        "side view, profile angle, "
        "studio lighting, white background, no shadows, "
        "{material_desc}, "
        "{size_desc}"
    ),
    "three_quarter": (
        "{style_anchor}, "
        "product visualization, isolated object, consistent prop design, "
        "same object, identical details, "
        "three-quarter view, slightly rotated, "
        "studio lighting, white background, no shadows, "
        "{material_desc}, "
        "{size_desc}"
    ),
    "top_down": (
        "{style_anchor}, "
        "product visualization, isolated object, consistent prop design, "
        "same object, identical details, "
        "top-down overhead view, bird's eye, "
        "studio lighting, white background, no shadows, "
        "{material_desc}, "
        "{size_desc}"
    ),
    "closeup_detail": (
        "{style_anchor}, "
        "product visualization, isolated object, consistent prop design, "
        "same object, identical details, "
        "extreme close-up detail, macro shot, "
        "studio lighting, white background, "
        "focusing on {detail_focus}, "
        "{material_desc}, "
        "{size_desc}"
    ),
}


def render_prop_prompt(
    view_key: str,
    prop_desc: str,
    material_desc: str,
    style_keywords: str | None = None,
    size_desc: str = "realistic proportions",
    detail_focus: str = "surface details and textures",
) -> str:
    """渲染道具单视角 Seedream prompt"""
    template = PROP_VIEW_TEMPLATES.get(view_key, PROP_VIEW_TEMPLATES["front"])
    prompt = template.format(
        style_anchor=get_style_anchor(style_keywords),
        material_desc=material_desc,
        size_desc=size_desc,
        detail_focus=detail_focus,
    )
    parts = [
        get_style_anchor(style_keywords),
        prop_desc,
        prompt,
        "masterpiece, best quality, sharp focus, clean background",
    ]
    return ", ".join(p for p in parts if p)


def build_prop_prompts(
    name: str,
    prop_desc: str,
    material_desc: str,
    structure_desc: str = "",
    style_keywords: str | None = None,
    size_desc: str = "realistic proportions",
) -> dict[str, str]:
    """
    生成道具多视角 prompt 字典。

    Args:
        name: 道具名称
        prop_desc: 道具基础定义（类型+名称）
        material_desc: 材质与颜色描述（定稿后不改）
        structure_desc: 结构细节（定稿后不改）
        style_keywords: Visual Bible 风格关键词
        size_desc: 尺寸比例感描述
    """
    base_desc = ", ".join(p for p in [prop_desc, structure_desc] if p)

    prompts: dict[str, str] = {}
    for view_key in ["front", "side", "three_quarter", "closeup_detail"]:
        prompts[view_key] = render_prop_prompt(
            view_key=view_key,
            prop_desc=base_desc,
            material_desc=material_desc,
            style_keywords=style_keywords,
            size_desc=size_desc,
            detail_focus="decorative patterns and textures",
        )

    return prompts


# ═══════════════════════════════════════════════════════════════════════════
# 批量生成工具（给 asset_image_pipeline.py 调用）
# ═══════════════════════════════════════════════════════════════════════════

def generate_asset_seedream_card(
    asset_name: str,
    asset_type: str,  # character / scene / prop
    outline_entry: dict,
    style_keywords: str | None = None,
) -> dict:
    """
    从 outline JSON 条目生成完整 Seedream 卡。

    Args:
        asset_name: 资产名称
        asset_type: character / scene / prop
        outline_entry: outline JSON 中对应条目（需含 description/imagePrompt 等字段）
        style_keywords: Visual Bible 风格关键词

    Returns:
        {
            "prompts": dict[str, str],   # view_key → prompt
            "card_md": str,               # seedream_card.md 内容
            "files": list[dict],          # 生成后应写入 manifest.files[] 的条目
        }
    """
    description = outline_entry.get("description", outline_entry.get("imagePrompt", ""))
    image_prompt = outline_entry.get("imagePrompt", outline_entry.get("prompt", ""))
    # 优先用 imagePrompt（更结构化）
    base_desc = image_prompt if image_prompt else description

    if asset_type == "character":
        # 角色：拆解 description 为外貌+服装+饰品
        result = build_character_card(
            name=asset_name,
            character_desc=description,  # 外貌核心
            costume_desc=outline_entry.get("costume", ""),
            accessory_desc=outline_entry.get("accessories", ""),
            style_keywords=style_keywords,
        )
        file_roles = {
            "front_full": "character_front",
            "front_closeup": "character_face_closeup",
            "side_full": "character_side",
            "side_closeup": "character_side_closeup",
            "back_full": "character_back",
            "three_quarter_full": "character_three_quarter",
        }

    elif asset_type == "scene":
        result = build_scene_prompts(
            name=asset_name,
            scene_desc=description,
            props_furniture=outline_entry.get("props", outline_entry.get("furniture", "")),
            floor_walls=outline_entry.get("materials", ""),
            style_keywords=style_keywords,
        )
        file_roles = {
            "establishing": "scene_wide",
            "medium": "scene_medium",
            "detail_closeup": "scene_detail_closeup",
        }

    else:  # prop
        result = build_prop_prompts(
            name=asset_name,
            prop_desc=description,
            material_desc=outline_entry.get("material", outline_entry.get("texture", "")),
            structure_desc=outline_entry.get("structure", ""),
            style_keywords=style_keywords,
        )
        file_roles = {
            "front": "prop_front",
            "side": "prop_side",
            "three_quarter": "prop_three_quarter",
            "closeup_detail": "prop_detail",
        }

    # 统一文件列表结构（供 manifest.files[] 使用）
    files = []
    for view_key, prompt_text in result["prompts"].items():
        role = file_roles.get(view_key, view_key)
        # 生成的图片文件名规范
        filename = f"{role}_{view_key}.png"
        files.append({
            "filename": filename,
            "role": role,
            "view_key": view_key,
            "prompt": prompt_text,
        })

    return {
        "prompts": result.get("prompts", result) if isinstance(result, dict) else result,
        "card_md": result.get("card_md", ""),
        "files": files,
    }


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse, json

    parser = argparse.ArgumentParser(description="Seedream 多视角提示词模板")
    sub = parser.add_subparsers(dest="cmd")

    p_char = sub.add_parser("character", help="生成角色多视角 prompt")
    p_char.add_argument("--name", required=True)
    p_char.add_argument("--desc", required=True, help="外貌描述")
    p_char.add_argument("--costume", default="", help="服装描述")
    p_char.add_argument("--accessory", default="", help="饰品描述")
    p_char.add_argument("--style", default=None, help="Visual Bible 风格关键词")
    p_char.add_argument("--view", action="append", dest="views", help="指定视角（可多次）")
    p_char.add_argument("--card-only", action="store_true", help="只输出角色卡 Markdown")

    p_scene = sub.add_parser("scene", help="生成场景多视角 prompt")
    p_scene.add_argument("--name", required=True)
    p_scene.add_argument("--desc", required=True, help="场景描述")
    p_scene.add_argument("--props", default="", help="道具家具清单")
    p_scene.add_argument("--style", default=None)

    p_prop = sub.add_parser("prop", help="生成道具多视角 prompt")
    p_prop.add_argument("--name", required=True)
    p_prop.add_argument("--desc", required=True, help="道具描述")
    p_prop.add_argument("--material", required=True, help="材质描述")
    p_prop.add_argument("--style", default=None)

    args = parser.parse_args()

    if args.cmd == "character":
        result = build_character_card(
            name=args.name,
            character_desc=args.desc,
            costume_desc=args.costume,
            accessory_desc=args.accessory,
            style_keywords=args.style,
            view_list=args.views,
        )
        if args.card_only:
            print(result["card_md"])
        else:
            for k, v in result["prompts"].items():
                print(f"## {k}")
                print(v)
                print()

    elif args.cmd == "scene":
        result = build_scene_prompts(
            name=args.name,
            scene_desc=args.desc,
            props_furniture=args.props,
            style_keywords=args.style,
        )
        for k, v in result.items():
            print(f"## {k}")
            print(v)
            print()

    elif args.cmd == "prop":
        result = build_prop_prompts(
            name=args.name,
            prop_desc=args.desc,
            material_desc=args.material,
            style_keywords=args.style,
        )
        for k, v in result.items():
            print(f"## {k}")
            print(v)
            print()
