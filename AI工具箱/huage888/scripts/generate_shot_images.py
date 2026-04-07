#!/usr/bin/env python3
"""generate_shot_images.py — P1: 逐 Shot 图生图

用法：
  python3 scripts/generate_shot_images.py \
    --shots outputs/S01E01-shots.md \
    --outline outputs/S01E01-outline.md \
    --output-dir outputs/S01E01-shots/images/ \
    --provider doubao \
    --model doubao-seedream-4.5

流程：
  1. 读取 shots + outline + asset_library
  2. 对每个 shot: resolve_shot → 参考图
  3. 有参考图 → img2img 模式
  4. 无参考图 → 纯 prompt 模式
  5. 下载 PNG → shot_XX.png
  6. 输出 shot_images_summary.json
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.outline_schema import ShotList
from scripts.asset_library import AssetLibrary

BASE_DIR = Path(__file__).parent.parent
IMAGE_MODEL = "doubao-seedream-4.5"


def extract_json_from_markdown(content: str) -> str:
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, content, re.DOTALL)
    if not matches:
        raise ValueError("Markdown 中未找到 ```json ``` 代码块")
    return matches[0].strip()


def load_shots(shots_path: Path) -> ShotList:
    content = shots_path.read_text(encoding="utf-8")
    json_str = extract_json_from_markdown(content)
    data = json.loads(json_str)
    return ShotList.model_validate(data)


def load_outline(outline_path: Path) -> dict:
    content = outline_path.read_text(encoding="utf-8")
    json_str = extract_json_from_markdown(content)
    return json.loads(json_str)


def resolve_ref_images(shot: dict, lib: AssetLibrary) -> list[Path]:
    """为 shot 查找所有参考图的完整路径"""
    refs: list[Path] = []
    lib_base = BASE_DIR / "assets" / "library"
    resolved = lib.resolve_shot(shot)
    for category, paths in resolved.items():
        for rel_path in paths:
            full_path = lib_base / rel_path
            if full_path.exists():
                refs.append(full_path)
    return refs


def build_resource_map(shot: dict, ref_paths: list[Path]) -> str:
    """构建 resource map prompt"""
    if not ref_paths:
        return ""
    parts = []
    for i, path in enumerate(ref_paths, 1):
        parts.append(f"[Ref image {i}]")
    return "[Maintain consistency with reference images above.]\n"


def call_doubao_image(
    prompt: str,
    output_path: Path,
    ref_paths: list[Path],
    model: str,
    aspect_ratio: str = "16:9",
) -> bool:
    """调用 doubao_pipeline.py"""
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
    for ref in ref_paths:
        cmd += ["--img-ref", str(ref)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [ERROR] {result.stderr[:300]}", file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="P1: 逐 Shot 图生图")
    parser.add_argument("--shots", required=True, help="分镜文件（Markdown）")
    parser.add_argument("--outline", required=True, help="大纲文件（Markdown）")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument("--provider", default="doubao", help="提供商")
    parser.add_argument("--model", default=IMAGE_MODEL, help="模型名称")
    parser.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16", "1:1"])
    parser.add_argument("--dry-run", action="store_true", help="不调用 API，仅打印")
    args = parser.parse_args()

    shots = load_shots(Path(args.shots))
    outline = load_outline(Path(args.outline))
    lib = AssetLibrary()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary: list[dict] = []

    print(f"\n[P1] 共 {len(shots.shots)} 个镜头")
    for shot in shots.shots:
        print(f"\n[Shot {shot.index:02d}] {shot.segmentTitle}")
        print(f"  scene: {shot.scene}")
        print(f"  chars: {shot.characters}")

        # 查找参考图
        shot_dict = {
            "characters": shot.characters,
            "scene": shot.scene,
            "props": shot.props,
        }
        ref_paths = resolve_ref_images(shot_dict, lib)
        print(f"  参考图: {len(ref_paths)} 张")
        for r in ref_paths:
            print(f"    - {r.name}")

        # 构建完整 prompt
        resource_map = build_resource_map(shot_dict, ref_paths)
        full_prompt = resource_map + shot.imagePrompt

        if args.dry_run:
            print(f"  [DRY] prompt: {full_prompt[:100]}...")
            continue

        output_path = out_dir / f"shot_{shot.index:02d}.png"
        ok = call_doubao_image(
            prompt=full_prompt,
            output_path=output_path,
            ref_paths=ref_paths,
            model=args.model,
            aspect_ratio=args.aspect_ratio,
        )

        summary.append({
            "shot_index": shot.index,
            "segment_title": shot.segmentTitle,
            "prompt": shot.imagePrompt,
            "ref_images": [str(r) for r in ref_paths],
            "output": str(output_path),
            "status": "success" if ok else "failed",
        })

    # 写入汇总
    summary_path = out_dir / "shot_images_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[完成] 汇总写入: {summary_path}")
    success_count = sum(1 for s in summary if s["status"] == "success")
    print(f"  成功: {success_count}/{len(summary)}")


if __name__ == "__main__":
    main()
