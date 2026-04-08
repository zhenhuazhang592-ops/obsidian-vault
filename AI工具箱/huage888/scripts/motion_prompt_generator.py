#!/usr/bin/env python3
"""
motion_prompt_generator.py — Motion Prompt 生成器

将分镜脚本中的 libtvPrompt 转化为增强 Motion Prompt，
参考 Toonflow generateVideoPrompt.ts 的五维度输出格式。

用法：
  python3 scripts/motion_prompt_generator.py \
    --shots outputs/S01E01/S01E01-storyboard.md \
    --output outputs/S01E01/S01E01-motion-prompts.json

  # 模块调用
  from motion_prompt_generator import MotionPromptGenerator, generate_motion_prompts
  prompts = generate_motion_prompts(shots_file=Path("shots.md"), episode="S01E01")
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class MotionPrompt:
    """单条 Motion Prompt"""
    shot_index: int        # 镜头序号
    name: str              # 2-6字概括（镜头动态/情绪）
    time: int              # 时长（秒）
    content: str           # 80-150字动态描述（英文）
    style_keywords: str     # 风格锚定词

    def to_json(self) -> dict:
        return {
            "shot_index": self.shot_index,
            "name": self.name,
            "time": self.time,
            "content": self.content,
            "style_keywords": self.style_keywords,
        }


class MotionPromptGenerator:
    """
    Motion Prompt 生成器

    参考 Toonflow generateVideoPrompt.ts：
      输出格式 = 五维度（Visual/Motion/Camera/Audio/Narrative）
      注入风格锚定 + 运镜描述
    """

    def __init__(self, style_name: str = "赛博墨韵"):
        self.style_name = style_name

    def parse_shots_from_md(self, shots_path: Path) -> list[dict]:
        """
        从 Markdown 分镜脚本解析镜头列表。
        支持格式：| 01 | 全景 | 固定 | ... | C001 | S001 | 3s | libtvPrompt文本 |
        返回：[{"index": 1, "shot_type": "全景", "movement": "固定", "description": "...",
               "characters": "C001", "scene": "S001", "duration": 3, "libtv_prompt": "..."}]
        """
        lines = shots_path.read_text(encoding="utf-8").splitlines()
        shots = []
        for line in lines:
            if not (line.startswith("|") and line.endswith("|")):
                continue
            stripped = line.strip("| ")
            if all(c in "- |:" for c in stripped):
                continue
            cols = [c.strip() for c in stripped.split("|")]
            if len(cols) < 7:
                continue
            # 尝试解析：镜头号/景别/运镜/画面描述/台词/音效/主体/场景/时长/libtvPrompt
            try:
                shot_num = int(cols[0]) if cols[0].isdigit() else 0
            except (ValueError, IndexError):
                continue
            shots.append({
                "index": shot_num,
                "shot_type": cols[1] if len(cols) > 1 else "",
                "movement": cols[2] if len(cols) > 2 else "",
                "description": cols[3] if len(cols) > 3 else "",
                "dialogue": cols[4] if len(cols) > 4 else "",
                "sound": cols[5] if len(cols) > 6 else "",
                "characters": cols[6] if len(cols) > 6 else "",
                "scene": cols[7] if len(cols) > 7 else "",
                "duration": self._parse_duration(cols[8] if len(cols) > 8 else "5s"),
                "libtv_prompt": cols[9] if len(cols) > 9 else "",
            })
        return shots

    def _parse_duration(self, s: str) -> int:
        """解析时长字符串 '3s' → 3"""
        m = re.search(r"(\d+)", s)
        return int(m.group(1)) if m else 5

    def generate(self, shot: dict) -> MotionPrompt:
        """
        将单个镜头 dict 转化为 MotionPrompt。

        生成逻辑（参考 Toonflow 五维度）：
          1. Visual: 从 libtv_prompt + description 提取视觉主体
          2. Motion: 解析 movement 字段
          3. Camera: 从 shot_type + movement 构建镜头描述
          4. Audio: 从 dialogue + sound 构建音效描述
          5. Narrative: 情绪基调从 description 推断
        """
        idx = shot.get("index", 1)
        duration = shot.get("duration", 5)
        shot_type = shot.get("shot_type", "")
        movement = shot.get("movement", "")
        description = shot.get("description", "")
        libtv = shot.get("libtv_prompt", "")
        dialogue = shot.get("dialogue", "")
        sound = shot.get("sound", "")
        characters = shot.get("characters", "")

        # 镜头名称（2-6字概括）
        name = self._generate_shot_name(description, shot_type)

        # 动态描述（80-150字英文）
        content_parts = []

        # Visual 主体描述
        if libtv:
            content_parts.append(libtv.strip())
        elif description:
            content_parts.append(description)

        # Camera 镜头
        camera_desc = self._build_camera(shot_type, movement)
        if camera_desc:
            content_parts.append(camera_desc)

        # Audio 音效
        if sound and sound not in ("—", "-", "无", ""):
            content_parts.append(f"Audio: {sound}")
        if dialogue and dialogue not in ("—", "-", "无", ""):
            content_parts.append(f"Dialogue: {dialogue}")

        content = ". ".join(content_parts)

        return MotionPrompt(
            shot_index=idx,
            name=name,
            time=duration,
            content=content,
            style_keywords=self._get_style_keywords(),
        )

    def _generate_shot_name(self, description: str, shot_type: str) -> str:
        """生成2-6字镜头名称"""
        if not description:
            return f"{shot_type}镜头"
        # 取前4个字符
        return description[:4].strip() or f"{shot_type}镜头"

    def _build_camera(self, shot_type: str, movement: str) -> str:
        """构建镜头描述"""
        type_map = {
            "全景": "Wide establishing shot",
            "中景": "Medium shot",
            "近景": "Close-up shot",
            "特写": "Extreme close-up shot",
            "大特写": "Extreme close-up shot",
            "远景": "Extreme wide shot",
        }
        move_map = {
            "固定": "static camera",
            "静止": "static camera",
            "推进": "slow dolly forward",
            "拉远": "slow dolly backward",
            "跟踪": "tracking shot",
            "摇镜": "slow pan",
            "甩镜": "whip pan",
            "升降": "crane up",
            "环绕": "orbiting shot",
        }
        shot_en = type_map.get(shot_type, shot_type)
        move_en = move_map.get(movement, movement)
        return f"{shot_en}, {move_en}"

    def _get_style_keywords(self) -> str:
        """获取风格锚定词"""
        style_map = {
            "赛博墨韵": "cyber ink painting style, ink wash texture, blue-teal glow, golden pupils",
            "古风烟雨": "traditional Chinese painting style, misty atmosphere, soft lighting",
            "3D国漫CG": "3D CG anime style, PBR materials, cinematic lighting",
        }
        return style_map.get(self.style_name, self.style_name)

    def generate_all(self, shots: list[dict]) -> list[MotionPrompt]:
        """批量生成 Motion Prompts"""
        return [self.generate(s) for s in shots if s.get("libtv_prompt") or s.get("description")]


def generate_motion_prompts(
    shots_file: Path,
    episode: str = "S01E01",
    style_name: str = "赛博墨韵",
    output_path: Path | None = None,
) -> list[dict]:
    """
    主入口函数：从分镜 Markdown 生成 Motion Prompts JSON。

    Args:
        shots_file: 分镜脚本 Markdown 路径
        episode: 集数标识
        style_name: 视觉风格
        output_path: 可选，输出 JSON 路径

    Returns:
        list[dict]，每项含 shot_index / name / time / content / style_keywords
    """
    gen = MotionPromptGenerator(style_name=style_name)
    shots = gen.parse_shots_from_md(shots_file)
    motion_prompts = gen.generate_all(shots)

    result = {
        "episode": episode,
        "style": style_name,
        "total_shots": len(motion_prompts),
        "total_duration": sum(p.time for p in motion_prompts),
        "prompts": [p.to_json() for p in motion_prompts],
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"✅ Motion Prompts → {output_path}")

    return result["prompts"]


# ── CLI ─────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="Motion Prompt 生成器")
    parser.add_argument("--shots", required=True, help="分镜脚本 Markdown 路径")
    parser.add_argument("--output", help="输出 JSON 路径")
    parser.add_argument("--episode", default="S01E01", help="集数")
    parser.add_argument("--style", default="赛博墨韵", help="视觉风格")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    shots_path = Path(args.shots)
    output_path = Path(args.output) if args.output else None
    result = generate_motion_prompts(
        shots_file=shots_path,
        episode=args.episode,
        style_name=args.style,
        output_path=output_path,
    )
    print(f"生成 {len(result)} 条 Motion Prompts")
    for p in result:
        print(f"  镜头{p['shot_index']:02d}: {p['name']} ({p['time']}s)")
