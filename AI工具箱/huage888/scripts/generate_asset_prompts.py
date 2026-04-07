#!/usr/bin/env python3
"""generate_asset_prompts.py — Step 1: qwen-max 润色生成角色/场景/道具卡

用法：
  python3 scripts/generate_asset_prompts.py \
    --outline outputs/S01E01-outline.md \
    --project 漠玫传 \
    --out-dir assets/library/

输入：outline JSON（characters / scenes / props + description）
输出：assets/library/[type]/[name]/[name]_card.md
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.outline_schema import EpisodeOutline

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
CONFIG_DIR = BASE_DIR / "config"
TEMPLATE_DIR = CONFIG_DIR / "seedream_prompts"


def extract_json_from_markdown(content: str) -> str:
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, content, re.DOTALL)
    if not matches:
        raise ValueError("Markdown 中未找到 ```json ``` 代码块")
    return matches[0].strip()


def load_outline(outline_path: Path) -> EpisodeOutline:
    content = outline_path.read_text(encoding="utf-8")
    json_str = extract_json_from_markdown(content)
    data = json.loads(json_str)
    return EpisodeOutline.model_validate(data)


def build_character_prompt(character: dict, template: str) -> str:
    """构建角色卡生成 Prompt（给 qwen-max）"""
    name = character.get("name", "")
    desc = character.get("description", "")
    return f"""基于以下角色信息，生成完整的 Seedream 角色卡。

角色名称：{name}
角色描述：{desc}

请严格按照以下模板填充每个 [ ] 字段，生成完整的 character_card.md 文件。

{template}

要求：
1. [ ] 内必须填入具体内容，禁止留空
2. 融入赛博墨韵风格（道姑髻/数据簪/金色瞳孔数据流/青蓝水墨眼线）
3. 服装描述需与角色气质一致
4. 输出只需包含完整的 character_card.md 内容（不含解释）
"""


def build_scene_prompt(scene: dict, template: str) -> str:
    """构建场景卡生成 Prompt"""
    name = scene.get("name", "")
    desc = scene.get("description", "")
    return f"""基于以下场景信息，生成完整的 Seedream 场景卡。

场景名称：{name}
场景描述：{desc}

请严格按照以下模板填充每个 [ ] 字段，生成完整的 scene_card.md 文件。

{template}

要求：
1. [ ] 内必须填入具体内容，禁止留空
2. 融入赛博墨韵风格（墨色数据流/青蓝霓虹/赛博古典融合）
3. 光线描述需有氛围感
4. 输出只需包含完整的 scene_card.md 内容（不含解释）
"""


def build_prop_prompt(prop: dict, template: str) -> str:
    """构建道具卡生成 Prompt"""
    name = prop.get("name", "")
    desc = prop.get("description", "")
    return f"""基于以下道具信息，生成完整的 Seedream 道具卡。

道具名称：{name}
道具描述：{desc}

请严格按照以下模板填充每个 [ ] 字段，生成完整的 prop_card.md 文件。

{template}

要求：
1. [ ] 内必须填入具体内容，禁止留空
2. 可融入数字元素（如发光的令牌）
3. 材质描述需具体（颜色/质感/磨损状态）
4. 输出只需包含完整的 prop_card.md 内容（不含解释）
"""


def call_qwen_max(prompt: str, system: str = "") -> str:
    """调用 qwen-max 生成内容"""
    api_key = Path.home() / ".config" / "huage888" / "api_key"
    if api_key.exists():
        import os
        os.environ.setdefault("QWEN_API_KEY", api_key.read_text().strip())

    import os
    api_key_val = os.environ.get("QWEN_API_KEY", "")
    if not api_key_val:
        raise RuntimeError("请设置 QWEN_API_KEY 环境变量")

    base_url = os.environ.get("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    import urllib.request
    import urllib.error

    headers = {
        "Authorization": f"Bearer {api_key_val}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "qwen-max",
        "messages": [
            {"role": "system", "content": system or "你是一个资产生成专家，输出直接是文件内容，不需要任何解释。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"API 错误 {e.code}: {e.read().decode()}")


def save_card(output_dir: Path, filename: str, content: str) -> Path:
    """保存 card 文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_text(content.strip(), encoding="utf-8")
    print(f"  [OK] {path.relative_to(BASE_DIR)}")
    return path


def main():
    parser = argparse.ArgumentParser(description="生成 Seedream 资产卡（Step 1）")
    parser.add_argument("--outline", required=True, help="outline JSON 文件路径")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--out-dir", default="assets/library/", help="资产库根目录")
    parser.add_argument("--dry-run", action="store_true", help="仅打印 Prompt，不调用 API")
    args = parser.parse_args()

    outline = load_outline(Path(args.outline))
    out_dir = Path(args.outline).parent.parent / args.out_dir

    # 加载模板
    char_template = (TEMPLATE_DIR / "character_card_template.md").read_text(encoding="utf-8")
    scene_template = (TEMPLATE_DIR / "scene_card_template.md").read_text(encoding="utf-8")
    prop_template = (TEMPLATE_DIR / "prop_card_template.md").read_text(encoding="utf-8")

    system = "你是资产生成专家，输出直接是文件内容，不需要任何解释。"

    # 生成角色卡
    print(f"\n[角色卡] 共 {len(outline.characters)} 个")
    for char in outline.characters:
        prompt = build_character_prompt(char.model_dump(), char_template)
        if args.dry_run:
            print(f"  [DRY] {char.name}: {prompt[:80]}...")
            continue
        try:
            content = call_qwen_max(prompt, system)
            asset_dir = out_dir / "characters" / char.name
            save_card(asset_dir, f"{char.name}_card.md", content)
        except Exception as e:
            print(f"  [ERROR] {char.name}: {e}")

    # 生成场景卡
    print(f"\n[场景卡] 共 {len(outline.scenes)} 个")
    for scene in outline.scenes:
        prompt = build_scene_prompt(scene.model_dump(), scene_template)
        if args.dry_run:
            print(f"  [DRY] {scene.name}: {prompt[:80]}...")
            continue
        try:
            content = call_qwen_max(prompt, system)
            asset_dir = out_dir / "scenes" / scene.name
            save_card(asset_dir, f"{scene.name}_card.md", content)
        except Exception as e:
            print(f"  [ERROR] {scene.name}: {e}")

    # 生成道具卡
    print(f"\n[道具卡] 共 {len(outline.props)} 个")
    for prop in outline.props:
        prompt = build_prop_prompt(prop.model_dump(), prop_template)
        if args.dry_run:
            print(f"  [DRY] {prop.name}: {prompt[:80]}...")
            continue
        try:
            content = call_qwen_max(prompt, system)
            asset_dir = out_dir / "props" / prop.name
            save_card(asset_dir, f"{prop.name}_card.md", content)
        except Exception as e:
            print(f"  [ERROR] {prop.name}: {e}")

    print("\n[完成] 资产卡生成完毕")


if __name__ == "__main__":
    main()
