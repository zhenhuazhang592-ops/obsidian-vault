#!/usr/bin/env python3
"""generate_shot_images.py — P1: 逐 Shot 图生图（多视角版）

用法：
  python3 scripts/generate_shot_images.py \
    --shots outputs/S01E01-shots.md \
    --outline outputs/S01E01-outline.md \
    --output-dir outputs/S01E01-shots/images/ \
    --provider doubao \
    --model doubao-seedream-4.5

流程：
  1. 读取 shots + outline + asset_library（manifest.json）
  2. 对每个 shot:
     - 根据景别自动选取最匹配的资产视图
       · close-up face → character_face_closeup
       · full body / 中景 → character_front_full / character_three_quarter_full
       · 场景 → scene_wide / scene_medium
       · 场景特写 → scene_detail_closeup
       · 道具 → prop_front / prop_three_quarter
     - 有参考图 → img2img 模式
     - 无参考图 → 纯 prompt 模式
  3. 下载 PNG → shot_XX.png
  4. 输出 shot_images_summary.json
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
IMAGE_MODEL = "doubao-seedream-5-0-260128"


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


def resolve_ref_images(
    shot: dict,
    lib: AssetLibrary,
    shot_type: str = "medium",
) -> list[tuple[str, Path]]:
    """
    为 shot 查找最匹配的资产参考图（多视角自动选取）。

    Args:
        shot: shot dict（包含 characters/scene/props 字段）
        lib: AssetLibrary 实例
        shot_type: 景别类型，用于选取对应视图：
            - "closeup" / "特写" → character_face_closeup / scene_detail_closeup
            - "medium" / "中景" → character_three_quarter_full / scene_medium
            - "wide" / "全景" → character_front_full / scene_wide
            - "side" → character_side / character_side_closeup
            - "back" → character_back
            - 默认 → 自动选取最优视图

    Returns:
        list[(role_label, file_path)]，按优先级排序
    """
    refs: list[tuple[str, Path]] = []
    lib_base = BASE_DIR / "assets" / "library"
    resolved = lib.resolve_shot(shot)

    # 角色视图优先级映射
    char_role_priority: dict[str, list[str]] = {
        "closeup":  ["character_face_closeup", "character_side_closeup",
                     "character_three_quarter_full", "character_front_full", "character_front"],
        "medium":   ["character_three_quarter_full", "character_front_full",
                     "character_side_full", "character_face_closeup"],
        "wide":     ["character_front_full", "character_three_quarter_full",
                     "character_side_full", "character_back_full"],
        "side":     ["character_side_full", "character_side_closeup",
                     "character_three_quarter_full"],
        "back":     ["character_back_full", "character_back_closeup"],
        "default":  ["character_three_quarter_full", "character_front_full",
                     "character_face_closeup", "character_side_full", "character_back_full"],
    }

    # 场景视图优先级映射
    scene_role_priority: dict[str, list[str]] = {
        "closeup":  ["scene_detail_closeup", "scene_medium"],
        "medium":   ["scene_medium", "scene_wide", "scene_detail_closeup"],
        "wide":     ["scene_wide", "scene_medium"],
        "default":  ["scene_wide", "scene_medium", "scene_detail_closeup"],
    }

    # 道具视图优先级映射
    prop_role_priority: dict[str, list[str]] = {
        "closeup":  ["prop_detail", "prop_closeup_detail"],
        "medium":   ["prop_three_quarter", "prop_front", "prop_side"],
        "wide":     ["prop_front", "prop_three_quarter"],
        "default":  ["prop_front", "prop_three_quarter", "prop_detail"],
    }

    priority_map = {
        "characters": char_role_priority,
        "scenes": scene_role_priority,
        "props": prop_role_priority,
    }

    # 标准化 shot_type
    normalized_type = _normalize_shot_type(shot_type)

    for category, paths in resolved.items():
        priority = priority_map.get(category, {})
        type_priority = priority.get(normalized_type, priority.get("default", []))

        for rel_path in paths:
            full_path = lib_base / rel_path
            if not full_path.exists():
                continue
            # 从文件名推断 role
            role = _infer_role_from_path(full_path.name)
            refs.append((role, full_path))

    # 按优先级排序
    def role_sort_key(item: tuple[str, Path]) -> int:
        role, _ = item
        for idx, p in enumerate(type_priority):
            if p in role:
                return idx
        return 99

    refs.sort(key=role_sort_key)
    return refs


def _normalize_shot_type(shot_type: str) -> str:
    """将中文/英文景别映射到标准化键"""
    mapping = {
        "closeup": "closeup", "特写": "closeup", "close-up": "closeup", "大特写": "closeup",
        "medium": "medium", "中景": "medium", "中": "medium",
        "wide": "wide", "全景": "wide", "full": "wide", "全身": "wide", "全景": "wide",
        "side": "side", "侧面": "side", "侧": "side",
        "back": "back", "背面": "back",
        "overhead": "wide", "俯": "wide", "航拍": "wide",
        "subjective": "medium", "主观": "medium",
    }
    key = shot_type.lower().strip()
    return mapping.get(key, "default")


def _extract_shot_type(shot) -> str:
    """从 Shot 对象提取 shotType 字段并标准化"""
    raw_type = getattr(shot, "shotType", "medium") or "medium"
    return _normalize_shot_type(raw_type)


def _infer_role_from_path(filename: str) -> str:
    """从文件名推断 role 类型"""
    filename_lower = filename.lower()
    if "face_closeup" in filename_lower or "face_close" in filename_lower:
        return "character_face_closeup"
    if "side_closeup" in filename_lower or "side_close" in filename_lower:
        return "character_side_closeup"
    if "side_full" in filename_lower or "side_" in filename_lower:
        return "character_side_full"
    if "back_closeup" in filename_lower or "back_close" in filename_lower:
        return "character_back_closeup"
    if "back_full" in filename_lower or "back_" in filename_lower:
        return "character_back_full"
    if "three_quarter" in filename_lower or "3qtr" in filename_lower:
        return "character_three_quarter_full"
    if "front_full" in filename_lower or "front_" in filename_lower:
        return "character_front_full"
    if "front" in filename_lower:
        return "character_front"
    if "scene_wide" in filename_lower or "scene_" in filename_lower:
        return "scene_wide"
    if "scene_detail" in filename_lower or "detail_closeup" in filename_lower:
        return "scene_detail_closeup"
    if "scene_medium" in filename_lower:
        return "scene_medium"
    if "prop_detail" in filename_lower or "detail" in filename_lower:
        return "prop_detail"
    if "prop_side" in filename_lower:
        return "prop_side"
    if "prop_three_quarter" in filename_lower or "prop_3qtr" in filename_lower:
        return "prop_three_quarter"
    if "prop_front" in filename_lower:
        return "prop_front"
    return "unknown"


def build_resource_map(shot: dict, ref_paths: list[Path]) -> str:
    """
    根据参考图构建 img2img prompt 片段。
    返回 Seedream reference 指令，用于锁定角色/场景一致性。
    """
    if not ref_paths:
        return ""
    filenames = ", ".join(f"[Ref: {p.name}]" for p in ref_paths[:3])
    return (
        f"[Maintain character and scene consistency with reference images: {filenames}.]\n"
    )


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
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="开启提示词优化层（T2I七维度重写，调用 PromptOptimizer）",
    )
    args = parser.parse_args()

    shots = load_shots(Path(args.shots))
    outline = load_outline(Path(args.outline))
    lib = AssetLibrary()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 提示词优化器（延迟初始化）
    optimizer = None
    if args.optimize:
        try:
            sys.path.insert(0, str(BASE_DIR / "config"))
            from prompt_optimizer import PromptOptimizer
            optimizer = PromptOptimizer()
            print(f"\n[OPT] PromptOptimizer 已就绪（mode=t2i）")
        except Exception as e:
            print(f"  [WARN] PromptOptimizer 初始化失败: {e}", file=sys.stderr)

    summary: list[dict] = []

    print(f"\n[P1] 共 {len(shots.shots)} 个镜头")
    for shot in shots.shots:
        print(f"\n[Shot {shot.index:02d}] {shot.segmentTitle}")
        print(f"  scene: {shot.scene}")
        print(f"  chars: {shot.characters}")

        # 从 shot 字段推断 shot_type（景别）
        shot_type = _extract_shot_type(shot)

        # 查找参考图（多视角自动选取）
        shot_dict = {
            "characters": shot.characters,
            "scene": shot.scene,
            "props": shot.props,
        }
        ref_items = resolve_ref_images(shot_dict, lib, shot_type=shot_type)
        ref_paths = [p for _, p in ref_items]
        print(f"  参考图: {len(ref_paths)} 张（shot_type={shot_type}）")
        for role, p in ref_items:
            print(f"    - [{role}] {p.name}")

        # 构建完整 prompt
        resource_map = build_resource_map(shot_dict, ref_paths)
        full_prompt = resource_map + shot.imagePrompt

        # 提示词优化层（T2I 七维度）
        if optimizer:
            try:
                optimized = optimizer.optimize(full_prompt, mode="t2i", dry_run=args.dry_run)
                if not args.dry_run:
                    print(f"  [OPT] 优化后 prompt 前80字: {optimized[:80]}...")
                    full_prompt = optimized
                else:
                    print(f"  [OPT][DRY] {optimized}")
            except Exception as e:
                print(f"  [OPT] 优化失败，使用原文: {e}", file=sys.stderr)

        if args.dry_run:
            print(f"  [DRY] prompt: {full_prompt[:100]}...")
            continue

        output_path = out_dir / f"shot_{shot.index:02d}.png"
        ok = call_doubao_image(
            prompt=full_prompt,
            output_path=output_path,
            ref_paths=ref_paths,  # list[Path] extracted from list[tuple[str, Path]]
            model=args.model,
            aspect_ratio=args.aspect_ratio,
        )

        summary.append({
            "shot_index": shot.index,
            "segment_title": shot.segmentTitle,
            "shot_type": shot_type,
            "prompt": shot.imagePrompt,
            "ref_images": [{"role": role, "path": str(p)} for role, p in ref_items],
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
