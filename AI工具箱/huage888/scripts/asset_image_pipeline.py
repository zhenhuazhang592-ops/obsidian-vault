#!/usr/bin/env python3
"""
asset_image_pipeline.py — Stage 1.5：资产图 API 生成（多视角版）

对应 Toonflow generateAssets.ts 的行为：
从 outline JSON 提取角色/场景/道具描述 → 调用 Doubao Seedream API
→ 生成多视角参考图（角色3-6视图/场景3视图/道具4视图）
→ 保存 seedream_card.md（角色卡文档）
→ 更新 assets/library/{type}/{name}/manifest.json 的 files[]

用法：
  python3 scripts/asset_image_pipeline.py \
    --outline outputs/S01E01/S01E01-outline.md \
    --episode S01E01 \
    --project 漠玫传

  # 模块调用
  from asset_image_pipeline import stage1_5_asset_images
  ok = stage1_5_asset_images(outline_path=..., episode="S01E01", ...)
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.seedream_templates import (
    generate_asset_seedream_card,
    get_style_anchor,
    build_character_card,
    build_scene_prompts,
    build_prop_prompts,
)
from config.asset_registry_schema import AssetManifest, AssetFile

# ── 路径配置 ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
ADAPTERS_DIR = SCRIPT_DIR / "adapters"

sys.path.insert(0, str(ADAPTERS_DIR))
sys.path.insert(0, str(SCRIPT_DIR))


# ── 工具函数 ─────────────────────────────────────────────────────────────────

def parse_outline_json(outline_path: Path) -> dict:
    """从 outline Markdown 中提取 JSON"""
    content = outline_path.read_text(encoding="utf-8")
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError(f"outline 中未找到 JSON 块: {outline_path}")
    return json.loads(match.group(1).strip())


# ── Visual Bible 读取 ─────────────────────────────────────────────────────────

def load_visual_bible(vb_path: Path | None = None) -> dict:
    """
    读取 Visual Bible，提取风格关键词和光线配置。

    Returns:
        {"style_keywords": "...", "lighting": {...}, "project_style": "..."}
    """
    if vb_path is None:
        vb_path = BASE_DIR / "config" / "visual-bible.md"

    if not vb_path.exists():
        return {"style_keywords": None, "lighting": {}, "project_style": None}

    content = vb_path.read_text(encoding="utf-8")
    # 提取风格关键词（从 Visual Bible 项目基础表格）
    style_keywords = None
    for line in content.splitlines():
        if "视觉风格" in line or "美术风格" in line:
            style_keywords = line.split("|")[-1].strip()
            break
        if "画面比例" in line:
            # 提取项目风格描述（往前几行）
            pass

    # 提取色调基调（第一行有效数据）
    lighting: dict = {}
    in_tone_section = False
    for line in content.splitlines():
        if "色调基调" in line or "光影基准" in line:
            in_tone_section = True
            continue
        if in_tone_section and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 3 and cells[0] and "---" not in line:
                lighting[cells[0]] = {
                    "primary": cells[1] if len(cells) > 1 else "",
                    "secondary": cells[2] if len(cells) > 2 else "",
                }

    return {
        "style_keywords": style_keywords,
        "lighting": lighting,
        "project_style": style_keywords,
    }


# ── 多视角生成器 ─────────────────────────────────────────────────────────────

def generate_multi_view_assets(
    asset_entries: list[dict],
    asset_dir: Path,
    adapter,
    vb_style: str | None = None,
    dry_run: bool = False,
    task_db=None,
) -> list[dict]:
    """
    为每个资产生成多视角 Seedream 参考图。

    角色：front_full / front_closeup / side_full / side_closeup / back_full / three_quarter_full
    场景：establishing / medium / detail_closeup
    道具：front / side / three_quarter / closeup_detail

    Returns:
        [{
            "name": str,
            "type": str,
            "generated_files": [{"view_key": str, "path": Path, "url": str}],
            "card_md": str,
        }, ...]
    """
    results: list[dict] = []

    for entry in asset_entries:
        asset_name = entry["name"]
        asset_type = entry["type"]
        outline_data = entry.get("outline_data", {})

        print(f"\n  ── {asset_type}: {asset_name} ──")
        print(f"    风格: {vb_style or 'default'}")

        # 生成多视角 Seedream 卡
        seedream_result = generate_asset_seedream_card(
            asset_name=asset_name,
            asset_type=asset_type,
            outline_entry=outline_data,
            style_keywords=vb_style,
        )
        prompts: dict[str, str] = seedream_result["prompts"]
        card_md: str = seedream_result["card_md"]
        file_specs: list[dict] = seedream_result["files"]

        # 保存角色卡
        card_path = asset_dir / asset_name / "seedream_card.md"
        card_path.parent.mkdir(parents=True, exist_ok=True)
        if card_md:
            card_path.write_text(card_md, encoding="utf-8")
            print(f"    ✅ seedream_card.md → {card_path.name}")

        generated_files: list[dict] = []

        # 生成每个视角
        for spec in file_specs:
            view_key = spec["view_key"]
            prompt = spec["prompt"]
            filename = spec["filename"]
            output_path = asset_dir / asset_name / filename

            print(f"    [{view_key}] → {filename}")
            if dry_run:
                print(f"      [DRY] prompt: {prompt[:80]}...")
                generated_files.append({"view_key": view_key, "path": output_path, "url": ""})
                continue

            # task 追踪
            task_id = None
            if task_db:
                try:
                    from task_db import TaskState
                    task_id = task_db.create(
                        task_type="doubao_image_multiview",
                        name=f"asset_{asset_name}_{view_key}",
                        params={
                            "asset": asset_name,
                            "type": asset_type,
                            "view": view_key,
                        },
                        stage="asset_images",
                    )
                    task_db.update(task_id, TaskState.RUNNING)
                except Exception:
                    pass

            try:
                result = adapter.generate_image(
                    prompt=prompt,
                    output_path=output_path,
                )
                generated_files.append({
                    "view_key": view_key,
                    "path": output_path,
                    "url": result.image_url,
                    "role": spec["role"],
                    "prompt": prompt,
                })
                print(f"      ✅ {result.image_url[:60]}...")

                if task_db and task_id:
                    try:
                        from task_db import TaskState
                        task_db.update(task_id, TaskState.SUCCESS, result={
                            "path": str(output_path), "url": result.image_url,
                        })
                    except Exception:
                        pass

            except Exception as e:
                print(f"      ❌ {e}", file=sys.stderr)
                if task_db and task_id:
                    try:
                        from task_db import TaskState
                        task_db.update(task_id, TaskState.FAILED, error=str(e))
                    except Exception:
                        pass

        results.append({
            "name": asset_name,
            "type": asset_type,
            "generated_files": generated_files,
            "card_md": card_md,
            "card_path": str(card_path) if card_md else None,
        })

    return results


def update_manifest_with_multiview(
    lib_base: Path,
    results: list[dict],
    asset_type: str,
    vb_style: str | None = None,
) -> None:
    """
    用多视角生成结果更新资产库的 manifest.json。
    """
    from config.asset_registry_schema import AssetManifest, AssetFile

    type_subdir = {"character": "characters", "scene": "scenes", "prop": "props"}

    for result in results:
        asset_name = result["name"]
        subdir = type_subdir.get(asset_type, asset_type)
        manifest_path = lib_base / subdir / asset_name / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取或创建 manifest
        if manifest_path.exists():
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest = AssetManifest.model_validate(data)
            except Exception:
                manifest = AssetManifest(name=asset_name, type=asset_type)
        else:
            manifest = AssetManifest(name=asset_name, type=asset_type)

        # 更新 files[]
        manifest.files = []
        for f in result["generated_files"]:
            rel_path = f"characters/{asset_name}/{f['path'].name}" if asset_type == "character" else (
                f"scenes/{asset_name}/{f['path'].name}" if asset_type == "scene" else
                f"props/{asset_name}/{f['path'].name}"
            )
            manifest.files.append(AssetFile(
                filename=f["path"].name,
                role=f.get("role", f["view_key"]),
                uploaded_at=date.today().isoformat(),
                file_path=rel_path,
            ))

        # 更新状态和 seedream_card
        manifest.status = "reference_generated"
        manifest.seedream_card = result.get("card_path", "")

        # 保存
        manifest_path.write_text(
            manifest.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )




def build_asset_prompt(spec: AssetSpec, outline_data: dict) -> str:
    """
    为资产构建图像生成 prompt。

    从 outline JSON 的 characters/scenes/props 中查找对应描述词。
    """
    if spec.type == "character":
        for c in outline_data.get("characters", []):
            if c.get("name") == spec.name:
                return c.get("imagePrompt", c.get("prompt", c.get("description", "")))
        # fallback
        return f"Highly detailed character portrait of {spec.name}, cyber-ink style, oriental zen aesthetic"

    elif spec.type == "scene":
        for s in outline_data.get("scenes", []):
            if s.get("name") == spec.name:
                return s.get("imagePrompt", s.get("prompt", s.get("description", "")))
        return f"Detailed scene illustration of {spec.name}, cyber-ink style"

    elif spec.type == "prop":
        for p in outline_data.get("props", []):
            if p.get("name") == spec.name:
                return p.get("imagePrompt", p.get("prompt", p.get("description", "")))
        return f"Detailed prop illustration of {spec.name}, cyber-ink style"

    return f"{spec.type} of {spec.name}"


def update_registry_cell(
    registry_path: Path,
    row_index: int,
    col_index: int,
    new_value: str,
) -> None:
    """更新 Markdown 表格指定单元格"""
    lines = registry_path.read_text(encoding="utf-8").splitlines()
    # 行号是 0-based，表格从 header 后第2行开始（跳过 |---| 行）
    # row_index 来自 parse_asset_registry，返回的是文件的行号（0-based）
    if 0 <= row_index < len(lines):
        cells = lines[row_index].split("|")
        # cells[0] 是前导 "|" 拆分后的空字符串
        if col_index < len(cells):
            cells[col_index] = f" {new_value} "
            lines[row_index] = "|".join(cells)
            registry_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_adapter_registry():
    """确保适配器注册表存在"""
    registry_path = ADAPTERS_DIR / "video_adapter_registry.py"
    if not registry_path.exists():
        print(f"[WARN] 适配器注册表不存在: {registry_path}", file=sys.stderr)


def get_adapter(provider: str = "doubao", **kwargs):
    """获取图片生成适配器"""
    ensure_adapter_registry()

    from video_adapter_registry import get_registry

    registry = get_registry()
    adapter = registry.get(provider)

    if adapter is None:
        raise ValueError(f"未找到适配器: {provider}，可用: {list(registry.keys())}")

    return adapter


# ── stage1.5 函数 ────────────────────────────────────────────────────────────

def stage1_5_asset_images(
    outline_path: Path,
    episode: str,
    project: str,
    output_dir: Path | None = None,
    registry_path: Path | None = None,
    task_db=None,
    emitter=None,
    provider: str = "doubao",
    dry_run: bool = False,
    visual_bible_path: Path | None = None,
) -> dict:
    """
    Stage 1.5: 资产图 API 生成（多视角版）

    流程：
    1. 解析 outline JSON → 提取 characters/scenes/props 描述词
    2. 读取 Visual Bible → 提取风格关键词注入所有 prompt
    3. 对每个资产：
       - 调用 seedream_templates 生成多视角 prompt
       - 调用 DoubaoAdapter.generate_image() 生成每个视角
       - 保存 seedream_card.md
    4. 更新 assets/library/{type}/{name}/manifest.json

    Returns:
        {"generated": N, "skipped": M, "failed": F, "assets": [...]}
    """
    base = output_dir or (BASE_DIR / "outputs")
    asset_dir = base / episode / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    lib_base = BASE_DIR / "assets" / "library"

    print(f"\n🖼️  Stage 1.5: 资产图生成（多视角版）")
    print(f"  集数：{episode}")
    print(f"  项目：{project}")
    print(f"  输出目录：{asset_dir.relative_to(BASE_DIR)}")

    # ── 1. 解析 outline ──────────────────────────────────────────────────
    try:
        outline_data = parse_outline_json(outline_path)
    except Exception as e:
        print(f"  [ERROR] outline JSON 解析失败: {e}", file=sys.stderr)
        return {"generated": 0, "skipped": 0, "failed": 1, "assets": []}

    # ── 2. 读取 Visual Bible ─────────────────────────────────────────────
    vb = load_visual_bible(visual_bible_path)
    vb_style = vb.get("style_keywords") or vb.get("project_style")
    print(f"  Visual Bible 风格: {vb_style or '未找到，使用默认风格'}")

    # ── 3. 构建待生成资产列表 ────────────────────────────────────────────
    all_entries: list[dict] = []

    for c in outline_data.get("characters", []):
        name = c.get("name", "")
        if not name:
            continue
        all_entries.append({
            "name": name,
            "type": "character",
            "outline_data": c,
        })

    for s in outline_data.get("scenes", []):
        name = s.get("name", "")
        if not name:
            continue
        all_entries.append({
            "name": name,
            "type": "scene",
            "outline_data": s,
        })

    for p in outline_data.get("props", []):
        name = p.get("name", "")
        if not name:
            continue
        all_entries.append({
            "name": name,
            "type": "prop",
            "outline_data": p,
        })

    print(f"  待处理资产：{len(all_entries)} 个")

    if not all_entries:
        return {"generated": 0, "skipped": 0, "failed": 0, "assets": []}

    # ── 4. 初始化适配器 ──────────────────────────────────────────────────
    if dry_run:
        adapter = None
    else:
        try:
            from video_adapter_registry import get_registry
            registry = get_registry()
            adapter = registry.get(provider)
            if adapter is None:
                raise ValueError(f"未找到适配器: {provider}")
        except Exception as e:
            print(f"  [ERROR] 适配器初始化失败: {e}", file=sys.stderr)
            print(f"  提示：设置 ARK_API_KEY 环境变量", file=sys.stderr)
            return {"generated": 0, "skipped": 0, "failed": len(all_entries), "assets": []}

    # ── 5. 多视角生成 ───────────────────────────────────────────────────
    results = generate_multi_view_assets(
        asset_entries=all_entries,
        asset_dir=asset_dir,
        adapter=adapter,
        vb_style=vb_style,
        dry_run=dry_run,
        task_db=task_db,
    )

    # ── 6. 更新 manifest.json ───────────────────────────────────────────
    generated_total = 0
    failed_total = 0
    for entry, result in zip(all_entries, results):
        if not dry_run:
            update_manifest_with_multiview(
                lib_base=lib_base,
                results=[result],
                asset_type=entry["type"],
                vb_style=vb_style,
            )
        generated_total += len(result["generated_files"])

    # ── 7. 注册到全局 registry.md ────────────────────────────────────────
    update_global_registry_md(
        registry_path or (BASE_DIR / "assets" / "03-asset-registry.md"),
        all_entries,
        asset_dir,
    )

    print(f"\n  📊 多视角资产图完成：{generated_total} 张参考图 / {len(all_entries)} 个资产")
    return {
        "generated": generated_total,
        "skipped": 0,
        "failed": failed_total,
        "assets": [
            {
                "name": r["name"],
                "type": r["type"],
                "files": [str(f["path"]) for f in r["generated_files"]],
            }
            for r in results
        ],
    }


def update_global_registry_md(
    registry_path: Path | None,
    all_entries: list[dict],
    asset_dir: Path,
) -> None:
    """更新全局资产注册表 assets/03-asset-registry.md"""
    if registry_path is None:
        return

    registry_path.parent.mkdir(parents=True, exist_ok=True)

    type_cn = {"character": "角色", "scene": "场景", "prop": "道具"}
    new_rows = []
    for entry in all_entries:
        name = entry["name"]
        atype = entry["type"]
        asset_subdir = asset_dir / name
        files = list(asset_subdir.glob("*.png")) if asset_subdir.exists() else []
        image_count = len(files)
        status = f"{image_count}张多视角" if image_count > 0 else "[待生成]"

        front_file = next((f for f in files if "front" in f.name), files[0] if files else None)
        front_url = f"[本地]{front_file.name}" if front_file else "[待填写]"

        new_rows.append(f"| {name} | {type_cn.get(atype, atype)} | [待上传LibTV] | {front_url} | {status} |")

    if not registry_path.exists():
        header = (
            "| 资产名称 | 类型 | element_id | image_url | 状态 |\n"
            "|---|---|---|---|---|\n"
        )
        registry_path.write_text(header + "\n".join(new_rows) + "\n", encoding="utf-8")
    else:
        content = registry_path.read_text(encoding="utf-8")
        existing_names = set()
        for line in content.splitlines():
            if line.startswith("|"):
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if cells:
                    existing_names.add(cells[0])

        new_lines = []
        for row in new_rows:
            name = row.split("|")[1].strip()
            if name not in existing_names:
                new_lines.append(row)

        if new_lines:
            registry_path.write_text(
                content.rstrip() + "\n" + "\n".join(new_lines) + "\n",
                encoding="utf-8",
            )


# ── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="Stage 1.5: 资产图 API 生成")
    parser.add_argument("--outline", required=True, help="outline.md 文件路径")
    parser.add_argument("--episode", required=True, help="集数（如 S01E01）")
    parser.add_argument("--project", required=True, help="项目名")
    parser.add_argument("--output-dir", default=None, help="输出目录（默认 outputs/{episode}/assets/）")
    parser.add_argument("--registry", default=None, help="资产注册表路径")
    parser.add_argument("--provider", default="doubao", help="图片生成提供商")
    parser.add_argument("--dry-run", action="store_true", help="不调用 API")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    task_db = None
    try:
        from task_db import TaskDB
        task_db = TaskDB()
    except Exception as e:
        print(f"[INFO] task_db 不可用: {e}", file=sys.stderr)

    result = stage1_5_asset_images(
        outline_path=Path(args.outline),
        episode=args.episode,
        project=args.project,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        registry_path=Path(args.registry) if args.registry else None,
        task_db=task_db,
        provider=args.provider,
        dry_run=args.dry_run,
    )

    if task_db:
        task_db.close()

    sys.exit(0 if result["failed"] == 0 else 1)
