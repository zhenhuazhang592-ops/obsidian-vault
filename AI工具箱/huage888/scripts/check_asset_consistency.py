#!/usr/bin/env python3
"""check_asset_consistency.py — 资产一致性检查脚本

用法：
  python3 scripts/check_asset_consistency.py <shots_file.md> <outline_file.md>

检查项：
  1. shots 中出现的每个 character 在 outline.characters 中存在
  2. shots 中出现的每个 scene 在 outline.scenes 中存在
  3. shots 中出现的每个 prop 在 outline.props 中存在
  4. 所有必填字段（非空）
  5. imagePrompt 包含风格锚定词
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.outline_schema import EpisodeOutline, ShotList


def extract_json(content: str) -> str:
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, content, re.DOTALL)
    if not matches:
        raise ValueError("未找到 ```json ``` 代码块")
    return matches[0].strip()


def check_consistency(shots: ShotList, outline: EpisodeOutline) -> list[str]:
    errors = []

    outline_chars = {c.name for c in outline.characters}
    outline_scenes = {s.name for s in outline.scenes}
    outline_props = {p.name for p in outline.props}

    required_fields = ["index", "description", "emotion", "shotType", "imagePrompt"]

    for shot in shots.shots:
        prefix = f"[Shot {shot.index}]"

        for field in required_fields:
            val = getattr(shot, field, None)
            if val is None or val == "":
                errors.append(f"❌ {prefix} {field} 为空")

        for char in shot.characters:
            if char not in outline_chars:
                suggestions = [c for c in outline_chars if char in c or c in char]
                sug = f"（建议：{', '.join(suggestions)}）" if suggestions else ""
                errors.append(f"❌ {prefix} characters: \"{char}\" 不在 outline 中{sug}")

        if shot.scene and shot.scene not in outline_scenes:
            suggestions = [s for s in outline_scenes if shot.scene in s or s in shot.scene]
            sug = f"（建议：{', '.join(suggestions)}）" if suggestions else ""
            errors.append(f"❌ {prefix} scene: \"{shot.scene}\" 不在 outline 中{sug}")

        for prop in shot.props:
            if prop not in outline_props:
                errors.append(f"❌ {prefix} props: \"{prop}\" 不在 outline 中")

        prompt = shot.imagePrompt or ""
        keywords = ["ink", "cyber", "neon", "Chinese", "brush"]
        if prompt and not any(k in prompt.lower() for k in keywords):
            errors.append(f"⚠️ {prefix} imagePrompt 未包含赛博墨韵锚定词")

    return errors


def main():
    if len(sys.argv) < 3:
        print("用法: check_asset_consistency.py <shots_file.md> <outline_file.md>")
        sys.exit(1)

    shots_path = Path(sys.argv[1])
    outline_path = Path(sys.argv[2])

    for p in [shots_path, outline_path]:
        if not p.exists():
            print(f"文件不存在: {p}")
            sys.exit(1)

    try:
        shots_data = json.loads(extract_json(shots_path.read_text(encoding="utf-8")))
        outline_data = json.loads(extract_json(outline_path.read_text(encoding="utf-8")))
        shots = ShotList.model_validate(shots_data)
        outline = EpisodeOutline.model_validate(outline_data)
    except Exception as e:
        print(f"❌ 解析错误: {e}")
        sys.exit(1)

    errors = check_consistency(shots, outline)

    if errors:
        print(f"\n❌ 资产一致性检查失败（共 {len(errors)} 项）：\n")
        for err in errors:
            print(f"   {err}")
        sys.exit(1)

    print(f"\n✅ 所有检查通过")
    print(f"   镜头数: {len(shots.shots)}")
    print(f"   角色数: {len(outline.characters)}")
    print(f"   场景数: {len(outline.scenes)}")
    print(f"   道具数: {len(outline.props)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
