#!/usr/bin/env python3
"""grid_split.py — 宫格图切割脚本（Pillow）

用法：
  python3 scripts/grid_split.py --input grid.png --rows 3 --cols 3 --output shots/
  python3 scripts/grid_split.py --input grid.png --rows 3 --cols 3 --output shots/ --prefix shot

输出：
  shots/shot_01.png
  shots/shot_02.png
  ...
"""

import argparse
import sys
from pathlib import Path
from PIL import Image


def split_grid(input_path: Path, output_dir: Path, rows: int, cols: int, prefix: str = "shot") -> list[Path]:
    """切割宫格图为单张 PNG"""
    img = Image.open(input_path)
    w, h = img.size
    cell_w = w // cols
    cell_h = h // rows

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    for r in range(rows):
        for c in range(cols):
            left = c * cell_w
            top = r * cell_h
            cell = img.crop((left, top, left + cell_w, top + cell_h))
            idx = r * cols + c + 1
            out_path = output_dir / f"{prefix}_{idx:02d}.png"
            cell.save(out_path, "PNG")
            outputs.append(out_path)
            print(f"  {out_path.name}")

    print(f"\n切割完成：{len(outputs)} 张 → {output_dir}")
    return outputs


def main():
    parser = argparse.ArgumentParser(description="宫格图切割")
    parser.add_argument("--input", required=True, help="输入宫格图路径")
    parser.add_argument("--rows", type=int, default=3, help="行数")
    parser.add_argument("--cols", type=int, default=3, help="列数")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--prefix", default="shot", help="输出文件名前缀")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    if not input_path.exists():
        print(f"文件不存在: {input_path}")
        sys.exit(1)

    try:
        split_grid(input_path, output_dir, args.rows, args.cols, args.prefix)
    except Exception as e:
        print(f"❌ 切割失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
