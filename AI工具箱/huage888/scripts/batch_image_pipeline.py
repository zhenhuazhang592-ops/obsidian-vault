#!/usr/bin/env python3
"""batch_image_pipeline.py — P2: 宫格批产 + 切割

用法：
  python3 scripts/batch_image_pipeline.py \\
    --shots outputs/S01E01-shots.md \\
    --outline outputs/S01E01-outline.md \\
    --rows 3 --cols 3 \\
    --output-dir outputs/S01E01-shots/grid/ \\
    --provider doubao \\
    --model nanobanana

流程：
  1. 读取前 N 个 shots（N = rows × cols）
  2. 收集所有参考图，Sharp 拼接为单张（最多 6 张）
  3. 构建宫格 prompt（拼接所有 shots 的 imagePrompt）
  4. 调用 Doubao 宫格 API → grid.png
  5. grid_split.py → shot_01.png ... shot_0N.png
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
GRID_SCRIPT = BASE_DIR / "scripts" / "grid_split.py"
MAX_REF_IMAGES = 6  # Doubao API 最多支持 6 张参考图


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


def resolve_ref_images(shot: dict, lib: AssetLibrary) -> list[Path]:
    lib_base = BASE_DIR / "assets" / "library"
    resolved = lib.resolve_shot(shot)
    refs = []
    for category, paths in resolved.items():
        for rel_path in paths:
            full_path = lib_base / rel_path
            if full_path.exists():
                refs.append(full_path)
    return refs


def merge_ref_images(ref_paths: list[Path], output_path: Path) -> Path | None:
    """用 Pillow 将多张参考图拼接为一张"""
    if not ref_paths:
        return None
    try:
        from PIL import Image
    except ImportError:
        print("[WARN] Pillow 未安装，跳过参考图合并", file=sys.stderr)
        return None

    images = []
    for p in ref_paths[:MAX_REF_IMAGES]:
        try:
            images.append(Image.open(p))
        except Exception as e:
            print(f"  [WARN] 无法打开参考图 {p}: {e}", file=sys.stderr)

    if not images:
        return None

    # 横向拼接（strip 形式）
    widths, heights = zip(*(img.size for img in images))
    total_width = sum(widths)
    max_height = max(heights)

    merged = Image.new("RGB", (total_width, max_height), "white")
    x_offset = 0
    for img in images:
        merged.paste(img, (x_offset, 0))
        x_offset += img.width

    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.save(output_path, "PNG")
    print(f"  [合并] {len(images)} 张参考图 → {output_path.name}")
    return output_path


def build_grid_prompt(shots: list) -> str:
    """拼接所有 shots 的 imagePrompt 为宫格 prompt"""
    parts = []
    for i, shot in enumerate(shots, 1):
        parts.append(f"[Cell {i}]: {shot.imagePrompt}")
    return "\n\n".join(parts)


def call_doubao_grid(
    prompt: str,
    output_path: Path,
    ref_image: Path | None,
    model: str,
    rows: int,
    cols: int,
    aspect_ratio: str,
) -> bool:
    """调用 doubao_pipeline.py 生成宫格图"""
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
    if ref_image:
        cmd += ["--img-ref", str(ref_image)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [ERROR] {result.stderr[:300]}", file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="P2: 宫格批产 + 切割")
    parser.add_argument("--shots", required=True)
    parser.add_argument("--outline", required=True)
    parser.add_argument("--rows", type=int, default=3, help="宫格行数")
    parser.add_argument("--cols", type=int, default=3, help="宫格列数")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--provider", default="doubao")
    parser.add_argument("--model", default="nanobanana")
    parser.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16", "1:1"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    shots_data = load_shots(Path(args.shots))
    lib = AssetLibrary()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    n = args.rows * args.cols
    target_shots = shots_data.shots[:n]
    print(f"\n[P2] 宫格 {args.rows}×{args.cols} = {n} 个镜头")

    # 收集参考图
    all_refs: list[Path] = []
    for shot in target_shots:
        shot_dict = {
            "characters": shot.characters,
            "scene": shot.scene,
            "props": shot.props,
        }
        refs = resolve_ref_images(shot_dict, lib)
        all_refs.extend(refs)

    # 去重 + 最多保留 MAX_REF_IMAGES
    seen = set()
    unique_refs = []
    for r in all_refs:
        if r not in seen:
            seen.add(r)
            unique_refs.append(r)
    unique_refs = unique_refs[:MAX_REF_IMAGES]

    merged_ref = None
    if unique_refs:
        merged_ref = out_dir / "_merged_ref.png"
        merge_ref_images(unique_refs, merged_ref)

    # 构建宫格 prompt
    grid_prompt = build_grid_prompt(target_shots)
    print(f"  prompt 预览: {grid_prompt[:100]}...")

    if args.dry_run:
        print(f"  [DRY] 共 {len(unique_refs)} 张参考图")
        return

    # 生成宫格图
    grid_path = out_dir / "grid.png"
    ok = call_doubao_grid(
        prompt=grid_prompt,
        output_path=grid_path,
        ref_image=merged_ref,
        model=args.model,
        rows=args.rows,
        cols=args.cols,
        aspect_ratio=args.aspect_ratio,
    )

    if not ok:
        print("[FAIL] 宫格图生成失败")
        sys.exit(1)

    # 切割
    split_dir = out_dir / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(GRID_SCRIPT),
        "--input", str(grid_path),
        "--rows", str(args.rows),
        "--cols", str(args.cols),
        "--output", str(split_dir),
        "--prefix", "shot",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] 切割失败: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"\n[完成] 宫格 {args.rows}×{args.cols} → {split_dir}/")
    # 重命名 shots
    for i, shot in enumerate(target_shots, 1):
        src = split_dir / f"shot_{i:02d}.png"
        dst = out_dir / f"shot_{shot.index:02d}.png"
        if src.exists():
            src.rename(dst)
            print(f"  {dst.name}")


if __name__ == "__main__":
    main()
