"""Prompt 生成器 — Schema 驱动的 Prompt 构建，保证约束内嵌"""

from typing import Optional
from .schema import ShotScript, ShotScriptMeta, IPProfile, Step45Output, IPCharacter, IPLocation
from .constants import SHOT_TYPES, CAMERA_ACTIONS, EMOTION_LEVELS


class PromptBuilder:
    """
    Prompt 构建器

    使用方式：
        builder = PromptBuilder(ip_profile, step45_output, project_config)
        prompt_text = builder.build_image_prompt(shot)

    约束注入：
        1. 从 ip_profile 注入角色外貌描述
        2. 从 step45 注入情绪/景别/运镜约束
        3. 从 constants 注入禁止词列表
        4. 自动检查禁止词，生成时即过滤
    """

    def __init__(
        self,
        ip_profile: IPProfile,
        step45_output: Step45Output,
        style_preset: str = "real",
        aspect_ratio: str = "9:16",
    ):
        self.ip_profile = ip_profile
        self.step45 = step45_output
        self.style_preset = style_preset
        self.aspect_ratio = aspect_ratio

    # ------------------------------------------------------------------ 角色引用

    def _get_char_description(self, char_id: str) -> str:
        """从 IP档案 获取角色描述，注入 Prompt"""
        char = self.ip_profile.characters.get(char_id)
        if not char:
            return f"[警告: 角色 {char_id} 不在IP档案中]"
        parts = [
            f"角色: {char.name}",
            f"外貌: {char.appearance.face}，{char.appearance.body}",
            f"发型: {char.appearance.hair}",
            f"标志性特征: {char.appearance.distinguishing}",
            f"服装: {char.clothing.daily}",
        ]
        return "，".join(filter(None, parts))

    def _get_loc_description(self, loc_id: str) -> str:
        """从 IP档案 获取场景描述"""
        loc = self.ip_profile.locations.get(loc_id)
        if not loc:
            return f"[警告: 场景 {loc_id} 不在IP档案中]"
        parts = [
            f"场景: {loc.name}",
            f"时代: {loc.time}",
            f"天气: {loc.weather}",
            f"色调: {loc.color_temp}",
            f"光线: {loc.lighting}",
            f"关键元素: {'，'.join(loc.key_elements)}",
        ]
        return "，".join(filter(None, parts))

    # ------------------------------------------------------------------ 约束注入

    def _build_constraints_block(self, shot: ShotScript) -> str:
        """生成约束块，嵌入 Prompt"""
        constraints = self.step45.get_shot_constraints(shot.shot_id)
        emotion = constraints.get("emotion", shot.emotion_level)
        prohibited = constraints.get("prohibited", [])

        lines = [
            "【强制约束】",
            f"- 情绪: {emotion}（{EMOTION_LEVELS.get(emotion, {}).get('name', '')}）",
            f"- 景别: {shot.shot_type}（{SHOT_TYPES.get(shot.shot_type, '')}）",
            f"- 运镜: {shot.camera_action}（{CAMERA_ACTIONS.get(shot.camera_action, '')}）",
            f"- 禁止: {' '.join(prohibited) if prohibited else '无'}",
            f"- 风格: {self.style_preset}，{self.aspect_ratio}竖屏",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------ Prompt 构建

    def build_image_prompt(self, shot: ShotScript) -> str:
        """
        构建 Image Prompt

        结构：
        [角色描述] + [场景描述] + [分场内容] + [约束块]
        """
        # 角色描述
        char_descs = [self._get_char_description(cid) for cid in shot.character_ids]
        chars_text = "\n".join(char_descs)

        # 场景描述
        loc_text = self._get_loc_description(shot.location_id)

        # 约束块
        constraints = self._build_constraints_block(shot)

        prompt_parts = [
            f"# Image Prompt（{shot.shot_id}）",
            chars_text,
            loc_text,
            f"\n【分场内容】{shot.script}",
            f"\n【对白】{shot.dialogue}" if shot.dialogue else "",
            f"\n{constraints}",
            f"\n【禁止词自检】生成前请确认以上禁止词未出现在画面描述中",
        ]
        return "\n\n".join(filter(None, prompt_parts))

    def build_video_prompt(self, shot: ShotScript) -> str:
        """
        构建 Video Prompt

        结构：
        [分场内容] + [景别/运镜约束] + [情绪状态] + [禁止特效]
        """
        constraints = self.step45.get_shot_constraints(shot.shot_id)
        emotion = constraints.get("emotion", shot.emotion_level)
        prohibited = constraints.get("prohibited", [])

        prompt_parts = [
            f"# Video Prompt（{shot.shot_id}）",
            f"\n【分场内容】{shot.script}",
            f"\n【运镜指令】",
            f"- 景别: {shot.shot_type}",
            f"- 运镜: {shot.camera_action}",
            f"- 情绪: {emotion}（{EMOTION_LEVELS.get(emotion, {}).get('name', '')}）",
            f"\n【禁止特效】{' '.join(prohibited) if prohibited else '无特效'}",
        ]
        return "\n".join(filter(None, prompt_parts))

    def build_shot_system_prompt(self, episode: str, style_guide: str = "") -> str:
        """
        生成单镜生成任务的 System Prompt

        注入：
        - IP档案角色列表
        - 本集禁止词
        - 情绪跳转规则
        - 输出格式要求（携带 meta）
        """
        # 角色列表
        char_list = []
        for char_id, char in self.ip_profile.characters.items():
            char_list.append(f"- {char_id}: {char.name}（{char.role_type}）")
        chars_text = "\n".join(char_list) if char_list else "（无角色档案）"

        # 禁止词
        prohibited = " ".join(self.step45.prohibited_keywords)

        # 场景列表
        loc_list = []
        for loc_id, loc in self.ip_profile.locations.items():
            loc_list.append(f"- {loc_id}: {loc.name}（{loc.color_temp}）")
        locs_text = "\n".join(loc_list) if loc_list else "（无场景档案）"

        return f"""你是漫舟导演助手，负责为AI漫剧生成单镜脚本。

【IP档案 — 角色】（以下ID为唯一合法引用）
{chars_text}

【IP档案 — 场景】
{locs_text}

【本集禁止词】（Prompt中严禁出现）
{prohibited or '无'}

【情绪跳转规则】
- L1(平静) → L2/L3
- L2(克制) → L1/L3/L4
- L3(隐忍) → L2/L4
- L4(爆发) → L3/L5
- L5(高潮) → L4
禁止跨度过大的情绪跳转（如L1→L4直接跳转）

【输出格式】
每镜必须输出以下JSON结构（携带meta字段）：
{{
  "shot_id": "P01",
  "script": "...",
  "character_ids": ["char_fugui"],
  "location_id": "loc_naowu",
  "emotion_level": "L3",
  "shot_type": "MCU",
  "camera_action": "固定",
  "dialogue": "...",
  "image_prompt": "...",
  "video_prompt": "...",
  "meta": {{
    "char_ids_source": ["char_fugui"],
    "loc_id_source": "loc_naowu",
    "emotion_from_d3": "L3",
    "shot_type_from_d4": "MCU",
    "prohibited_check": [],
    "style_anchor": "{self.style_preset}"
  }}
}}

【禁止行为】
- 不得引用IP档案中不存在的char_id或loc_id
- 不得出现禁止词
- 不得生成L1→L4等禁止的情绪跳转
- 不得在image_prompt中出现"滤镜""美颜""卡通"等词
""" + (f"\n\n【风格补充】\n{style_guide}" if style_guide else "")

    def print_prompt_preview(self, shot: ShotScript) -> None:
        """预览生成的 Prompt（调试用）"""
        text = self.build_image_prompt(shot)
        preview = text[:500] + "..." if len(text) > 500 else text
        print("\n" + "=" * 50)
        print(f"📝 Image Prompt 预览（{shot.shot_id}）")
        print("=" * 50)
        print(preview)
        print("=" * 50)
