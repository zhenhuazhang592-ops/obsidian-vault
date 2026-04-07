#!/usr/bin/env python3
"""
asset_image_pipeline.py — Stage 1.5：资产图 API 生成

对应 Toonflow generateAssets.ts 的行为：
从 outline JSON 提取角色/场景/道具描述 → 调用 Doubao Seedream API → 保存图片
→ 更新 assets/03-asset-registry.md 的 element_id 和 image_url

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
from dataclasses import dataclass
from pathlib import Path

# ── 路径配置 ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
ADAPTERS_DIR = SCRIPT_DIR / "adapters"

sys.path.insert(0, str(ADAPTERS_DIR))
sys.path.insert(0, str(SCRIPT_DIR))


# ── 数据模型 ─────────────────────────────────────────────────────────────────

@dataclass
class AssetSpec:
    """单个资产规格"""
    name: str          # 资产名称（如 "漠玫"）
    type: str          # character / scene / prop
    element_id: str    # element_id（"[待填写]" = 未生成）
    image_url: str     # 图片 URL（"[待填写]" = 未生成）
    image_prompt: str  # 图像生成 Prompt
    version: str       # v1.0 / v1.1 ...
    index: int        # 行号


# ── 工具函数 ─────────────────────────────────────────────────────────────────

def parse_outline_json(outline_path: Path) -> dict:
    """从 outline Markdown 中提取 JSON"""
    content = outline_path.read_text(encoding="utf-8")
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError(f"outline 中未找到 JSON 块: {outline_path}")
    return json.loads(match.group(1).strip())


def parse_asset_registry(registry_path: Path) -> list[AssetSpec]:
    """解析 assets/03-asset-registry.md Markdown 表格"""
    if not registry_path.exists():
        return []

    lines = registry_path.read_text(encoding="utf-8").splitlines()
    assets = []

    # 找到表头和表体
    header_idx = -1
    for i, line in enumerate(lines):
        if "| 名称 |" in line or "| 资产名称 |" in line:
            header_idx = i
            break

    if header_idx < 0:
        return []

    for i, line in enumerate(lines[header_idx + 2:], start=header_idx + 2):
        line = line.strip()
        if not line or line.startswith("|"):
            # 空行或分隔符
            if "---" in line or not line:
                continue
        if not line.startswith("|"):
            continue

        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 5:
            continue

        # 解析列（格式：| 名称 | 类型 | element_id | image_url | 描述词/版本 |
        name = cells[0]
        atype = cells[1] if len(cells) > 1 else ""
        element_id = cells[2] if len(cells) > 2 else "[待填写]"
        image_url = cells[3] if len(cells) > 3 else "[待填写]"
        version = cells[4] if len(cells) > 4 else "v1.0"

        # 映射中文类型
        type_map = {
            "角色": "character",
            "场景": "scene",
            "道具": "prop",
            "Character": "character",
            "Scene": "scene",
            "Prop": "prop",
        }
        atype = type_map.get(atype, atype.lower())

        if atype in ("character", "scene", "prop"):
            assets.append(AssetSpec(
                name=name,
                type=atype,
                element_id=element_id,
                image_url=image_url,
                image_prompt="",
                version=version,
                index=i,
            ))

    return assets


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
) -> dict:
    """
    Stage 1.5: 资产图 API 生成

    流程：
    1. 解析 outline JSON → 提取 characters/scenes/props 描述词
    2. 解析 assets/03-asset-registry.md → 找出 element_id == "[待填写]" 的资产
    3. 对每个待生成资产：
       - 构建 image prompt
       - 调用 DoubaoAdapter.generate_image()
       - 保存到 outputs/{ep}/assets/{C001}_v1.png
    4. 更新 03-asset-registry.md 的 element_id 和 image_url 列

    Returns:
        {"generated": N, "skipped": M, "failed": F, "assets": [...]}
    """
    base = output_dir or (BASE_DIR / "outputs")
    asset_dir = base / episode / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)

    # 解析 outline
    print(f"\n🖼️  Stage 1.5: 资产图生成")
    print(f"  集数：{episode}")
    print(f"  项目：{project}")
    print(f"  输出目录：{asset_dir.relative_to(BASE_DIR)}")

    try:
        outline_data = parse_outline_json(outline_path)
    except Exception as e:
        print(f"  [ERROR] outline JSON 解析失败: {e}", file=sys.stderr)
        return {"generated": 0, "skipped": 0, "failed": 1, "assets": []}

    # 解析资产注册表
    reg_path = registry_path or (BASE_DIR / "assets" / "03-asset-registry.md")
    registry_assets = parse_asset_registry(reg_path) if reg_path.exists() else []
    registry_map = {a.name: a for a in registry_assets}

    print(f"  资产注册表：{len(registry_assets)} 个资产")

    # 合并 outline 中的资产（以 outline 为准）
    all_assets: list[AssetSpec] = []

    for c in outline_data.get("characters", []):
        name = c.get("name", "")
        spec = registry_map.get(name, AssetSpec(
            name=name, type="character",
            element_id="[待填写]", image_url="[待填写]",
            image_prompt=c.get("imagePrompt", ""), version="v1.0", index=-1,
        ))
        if not spec.image_prompt:
            spec.image_prompt = build_asset_prompt(spec, outline_data)
        all_assets.append(spec)

    for s in outline_data.get("scenes", []):
        name = s.get("name", "")
        spec = registry_map.get(name, AssetSpec(
            name=name, type="scene",
            element_id="[待填写]", image_url="[待填写]",
            image_prompt=s.get("imagePrompt", ""), version="v1.0", index=-1,
        ))
        if not spec.image_prompt:
            spec.image_prompt = build_asset_prompt(spec, outline_data)
        all_assets.append(spec)

    for p in outline_data.get("props", []):
        name = p.get("name", "")
        spec = registry_map.get(name, AssetSpec(
            name=name, type="prop",
            element_id="[待填写]", image_url="[待填写]",
            image_prompt=p.get("imagePrompt", ""), version="v1.0", index=-1,
        ))
        if not spec.image_prompt:
            spec.image_prompt = build_asset_prompt(spec, outline_data)
        all_assets.append(spec)

    # 过滤出需要生成的资产（element_id == "[待填写]"）
    to_generate = [a for a in all_assets if a.element_id in ("[待填写]", "", None)]

    print(f"  待生成资产：{len(to_generate)} 个")
    print(f"  已完成资产：{len(all_assets) - len(to_generate)} 个")

    if dry_run:
        print(f"\n[DRY] 跳过 API 调用")
        for a in to_generate:
            print(f"  [DRY] {a.type}: {a.name}")
            print(f"         prompt: {a.image_prompt[:80]}...")
        return {
            "generated": 0, "skipped": len(to_generate),
            "failed": 0, "assets": to_generate,
        }

    if not to_generate:
        print(f"\n  [OK] 所有资产已完成，无需生成")
        return {"generated": 0, "skipped": len(all_assets), "failed": 0, "assets": all_assets}

    # ── 初始化适配器 ──────────────────────────────────────────────────────
    try:
        from video_adapter_registry import get_registry
        registry = get_registry()
        adapter = registry.get(provider)
        if adapter is None:
            raise ValueError(f"未找到适配器: {provider}")
    except Exception as e:
        print(f"  [ERROR] 适配器初始化失败: {e}", file=sys.stderr)
        print(f"  提示：设置 ARK_API_KEY 环境变量", file=sys.stderr)
        return {"generated": 0, "skipped": 0, "failed": len(to_generate), "assets": []}

    # ── 逐资产生成 ─────────────────────────────────────────────────────────
    generated = 0
    failed = 0
    results: list[dict] = []

    for spec in to_generate:
        # 生成文件名
        type_prefix = {"character": "C", "scene": "S", "prop": "P"}
        prefix = type_prefix.get(spec.type, "X")
        # 从名称提取编号（C001, C002...）
        filename = f"{prefix}_{spec.name.replace(' ', '_')}_v1.png"
        output_path = asset_dir / filename

        # 去除非法字符
        output_path = asset_dir / "".join(
            c if c.isalnum() or c in (".", "_", "-") else "_"
            for c in filename
        )

        print(f"\n  生成 {spec.type}: {spec.name}")
        print(f"    prompt: {spec.image_prompt[:100]}...")
        print(f"    输出: {output_path.relative_to(BASE_DIR)}")

        # task 追踪
        task_id = None
        if task_db:
            try:
                from task_db import TaskState
                task_id = task_db.create(
                    task_type="doubao_image",
                    name=f"asset_image_{spec.name}_{spec.type}",
                    params={"episode": episode, "project": project, "asset": spec.name},
                    episode=episode,
                    stage="asset_images",
                )
                task_db.update(task_id, TaskState.RUNNING)
            except Exception:
                pass

        try:
            result = adapter.generate_image(
                prompt=spec.image_prompt,
                output_path=output_path,
            )

            # 生成成功 → 更新 registry
            # 由于不知道具体列索引，用保守方式：追加到 registry
            if reg_path.exists() and spec.index >= 0:
                # element_id 在第3列（col_index=3），image_url 在第4列（col_index=4）
                update_registry_cell(reg_path, spec.index, 3, f"[API-GENERATED-{spec.name}]")
                update_registry_cell(reg_path, spec.index, 4, result.image_url)
            else:
                # 如果没有 registry 或行索引无效，创建新的 registry 条目
                _append_to_registry(reg_path, spec, result.image_url)

            print(f"    ✅ 完成：{result.image_url[:60]}...")
            generated += 1
            results.append({
                "name": spec.name, "type": spec.type,
                "path": str(output_path), "url": result.image_url,
            })

            if task_db and task_id:
                try:
                    from task_db import TaskState
                    task_db.update(task_id, TaskState.SUCCESS, result={
                        "path": str(output_path), "url": result.image_url,
                    })
                except Exception:
                    pass

        except Exception as e:
            print(f"    ❌ 失败: {e}", file=sys.stderr)
            failed += 1
            results.append({"name": spec.name, "type": spec.type, "error": str(e)})

            if task_db and task_id:
                try:
                    from task_db import TaskState
                    task_db.update(task_id, TaskState.FAILED, error=str(e))
                except Exception:
                    pass

    print(f"\n  📊 资产图生成完成：成功 {generated} / 失败 {failed} / 跳过 {len(all_assets) - len(to_generate)}")

    return {
        "generated": generated,
        "skipped": len(all_assets) - len(to_generate),
        "failed": failed,
        "assets": results,
    }


def _append_to_registry(
    registry_path: Path | None,
    spec: AssetSpec,
    image_url: str,
) -> None:
    """追加新资产到 registry"""
    if registry_path is None:
        return

    type_cn = {"character": "角色", "scene": "场景", "prop": "道具"}

    new_row = (
        f"| {spec.name} | {type_cn.get(spec.type, spec.type)} "
        f"| [API-GENERATED-{spec.name}] | {image_url} | {spec.image_prompt[:50]} | {spec.version} |"
    )

    if registry_path.exists():
        content = registry_path.read_text(encoding="utf-8")
        registry_path.write_text(content + "\n" + new_row + "\n", encoding="utf-8")
    else:
        header = (
            "| 资产名称 | 类型 | element_id | image_url | 描述词/版本 |\n"
            "|---|---|---|---|---|\n"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(header + new_row + "\n", encoding="utf-8")


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
