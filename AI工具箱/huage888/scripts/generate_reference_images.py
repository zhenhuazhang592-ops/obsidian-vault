#!/usr/bin/env python3
"""generate_reference_images.py — Step 2: Doubao Seedream 生成参考图

用法：
  python3 scripts/generate_reference_images.py \
    --project 漠玫传 \
    --type character \
    --names 漠玫,大圣

  # 全部资产
  python3 scripts/generate_reference_images.py --project 漠玫传 --all
"""

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.asset_registry_schema import AssetFile
from scripts.asset_library import AssetLibrary, TYPE_SUBDIRS

BASE_DIR = Path(__file__).parent.parent
DEFAULT_PROMPT_SUFFIX = "front view, full body, calm, standing elegantly, white studio background, masterpiece, best quality, 8k resolution, professional lighting"

SCENE_DEFAULT = "wide establishing shot, eye-level camera, focusing on the full scene, cool blue moonlight atmosphere, volumetric light rays, no characters, empty scene, masterpiece, best quality, ultra detailed textures, sharp focus"

PROP_DEFAULT = "three-quarter view, full object, masterpiece, best quality, sharp focus, clean background"


def build_prompt_from_card(card_path: Path, default_suffix: str = DEFAULT_PROMPT_SUFFIX) -> str | None:
    """从 card.md 提取固定段落 + 追加默认变量"""
    if not card_path.exists():
        return None
    content = card_path.read_text(encoding="utf-8")

    # 提取 ①+②+③+④ 节（固定段）
    sections = []
    in_fixed = True
    for line in content.split("\n"):
        if "⑤ 镜头变量" in line or "{{" in line:
            in_fixed = False
        if in_fixed and line.strip() and not line.startswith("#"):
            sections.append(line.strip())
        if "⑥ 质量尾缀" in line:
            break

    if not sections:
        return None

    # 追加默认变量
    prompt = "\n".join(sections)
    if not any(kw in prompt for kw in default_suffix.split(",")):
        prompt += f"\n{default_suffix}"
    return prompt


def call_doubao_image(prompt: str, output_path: Path, model: str, aspect_ratio: str = "16:9") -> bool:
    """调用 doubao_pipeline.py 生成图片"""
    cmd = [
        sys.executable,
        str(BASE_DIR / "config" / "doubao_pipeline.py"),
        "--image",
        "--prompt", prompt,
        "--output", str(output_path),
        "--model", model,
        "--aspect-ratio", aspect_ratio,
        "--no-emit",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [ERROR] {result.stderr[:200]}", file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="生成资产参考图（Step 2）")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--type", choices=["character", "scene", "prop"], help="资产类型")
    parser.add_argument("--names", help="资产名称（逗号分隔，不指定则全部）")
    parser.add_argument("--all", action="store_true", help="处理全部资产")
    parser.add_argument("--model", default="doubao-seedream-5.0-lite", help="模型名称")
    parser.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16", "1:1"])
    args = parser.parse_args()

    lib = AssetLibrary()
    asset_types = [args.type] if args.type else ["character", "scene", "prop"]
    target_names: set[str] | None = None

    if args.names:
        target_names = {n.strip() for n in args.names.split(",")}

    today = date.today().isoformat()
    model = args.model
    aspect = args.aspect_ratio

    for asset_type in asset_types:
        subdir = TYPE_SUBDIRS[asset_type]
        type_dir = BASE_DIR / "assets" / "library" / subdir
        if not type_dir.exists():
            continue

        for asset_path in type_dir.iterdir():
            if not asset_path.is_dir():
                continue
            name = asset_path.name

            # 过滤名称
            if target_names and name not in target_names:
                continue

            # 检查 manifest
            manifest_path = asset_path / "manifest.json"
            if not manifest_path.exists():
                continue

            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                from config.asset_registry_schema import AssetManifest
                manifest = AssetManifest.model_validate(data)
            except Exception:
                continue

            # 检查项目匹配
            if manifest.project and manifest.project != args.project:
                continue

            # 检查是否已生成
            if manifest.status == "reference_generated":
                print(f"  [SKIP] {name} ({asset_type}): already generated")
                continue

            # 找 card 文件
            card_name = f"{name}_card.md"
            card_path = asset_path / card_name
            if not card_path.exists():
                print(f"  [WARN] {name}: card 文件不存在 ({card_path})")
                continue

            # 构建 prompt
            suffix = DEFAULT_PROMPT_SUFFIX
            if asset_type == "scene":
                suffix = SCENE_DEFAULT
            elif asset_type == "prop":
                suffix = PROP_DEFAULT

            prompt = build_prompt_from_card(card_path, suffix)
            if not prompt:
                print(f"  [WARN] {name}: 无法从 card 构建 prompt")
                continue

            # 生成图片
            print(f"\n[生成] {name} ({asset_type})")
            print(f"  prompt: {prompt[:100]}...")

            images_dir = asset_path / "images"
            images_dir.mkdir(parents=True, exist_ok=True)
            output_path = images_dir / "ref_01.png"

            if call_doubao_image(prompt, output_path, model, aspect):
                # 更新 manifest
                asset_file = AssetFile(
                    filename="ref_01.png",
                    role="front_view" if asset_type == "character" else "scene_wide",
                    uploaded_at=today,
                    file_path=f"{subdir}/{name}/images/ref_01.png",
                )
                lib.add_file(name, asset_type, asset_file)
                lib.update_manifest(name, asset_type, status="reference_generated")
                print(f"  [OK] {name} 参考图已保存")
            else:
                print(f"  [FAIL] {name} 生成失败")

    print("\n[完成] 参考图生成完毕")


if __name__ == "__main__":
    main()
