#!/usr/bin/env python3
"""asset_library.py — 资产库管理器

用法：
  python3 scripts/asset_library.py --resolve 漠玫 character
  python3 scripts/asset_library.py --list --project 漠玫传
  python3 scripts/asset_library.py --register --name 漠玫 --type character --project 漠玫传
"""

import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.asset_registry_schema import AssetManifest, AssetFile
from config.outline_schema import Shot


LIBRARY_BASE = Path(__file__).parent.parent / "assets" / "library"

TYPE_SUBDIRS = {
    "character": "characters",
    "scene": "scenes",
    "prop": "props",
}


class AssetLibrary:
    """资产库管理器"""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or LIBRARY_BASE

    def _manifest_path(self, name: str, asset_type: str) -> Path:
        subdir = TYPE_SUBDIRS.get(asset_type, asset_type)
        return self.base_dir / subdir / name / "manifest.json"

    def _images_dir(self, name: str, asset_type: str) -> Path:
        subdir = TYPE_SUBDIRS.get(asset_type, asset_type)
        return self.base_dir / subdir / name / "images"

    def register(
        self,
        name: str,
        asset_type: str,
        project: str | None = None,
        first_episode: str | None = None,
        visual_description: str | None = None,
    ) -> Path:
        """注册新资产：创建目录 + manifest.json"""
        manifest_path = self._manifest_path(name, asset_type)
        if manifest_path.exists():
            print(f"[WARN] 资产已存在: {manifest_path}")
            return manifest_path

        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        (self._images_dir(name, asset_type)).mkdir(parents=True, exist_ok=True)

        manifest = AssetManifest(
            name=name,
            type=asset_type,
            project=project,
            first_episode=first_episode,
            visual_description=visual_description,
        )
        manifest_path.write_text(
            manifest.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"[OK] 已注册: {manifest_path}")
        return manifest_path

    def resolve(self, name: str, asset_type: str) -> list[str]:
        """查询某资产的参考图文件路径列表（相对于 library 根）"""
        manifest_path = self._manifest_path(name, asset_type)
        if not manifest_path.exists():
            return []
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = AssetManifest.model_validate(data)
            return [f["file_path"] for f in manifest.files]
        except Exception:
            return []

    def list_by_project(self, project: str) -> dict[str, list[str]]:
        """列出某项目的所有资产，按类型分组"""
        result: dict[str, list[str]] = {"characters": [], "scenes": [], "props": []}
        for asset_type, subdir_key in TYPE_SUBDIRS.items():
            subdir = self.base_dir / subdir_key
            if not subdir.exists():
                continue
            for asset_dir in subdir.iterdir():
                if not asset_dir.is_dir():
                    continue
                manifest_path = asset_dir / "manifest.json"
                if not manifest_path.exists():
                    continue
                try:
                    data = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest = AssetManifest.model_validate(data)
                    if manifest.project == project:
                        result[subdir_key].append(manifest.name)
                except Exception:
                    pass
        return result

    def resolve_shot(self, shot: dict) -> dict[str, list[str]]:
        """
        为单个 shot 字典查找相关资产文件路径。
        输入: shot dict（包含 characters/scene/props 字段）
        输出: {"characters": [...], "scenes": [...], "props": [...]}
        """
        result: dict[str, list[str]] = {"characters": [], "scenes": [], "props": []}

        for char in shot.get("characters", []):
            result["characters"].extend(self.resolve(char, "character"))

        scene = shot.get("scene", "")
        if scene:
            result["scenes"].extend(self.resolve(scene, "scene"))

        for prop in shot.get("props", []):
            result["props"].extend(self.resolve(prop, "prop"))

        return result

    def update_manifest(
        self,
        name: str,
        asset_type: str,
        new_files: list[AssetFile] | None = None,
        status: str | None = None,
        seedream_card: str | None = None,
    ) -> None:
        """更新 manifest.json（追加文件或更新状态）"""
        manifest_path = self._manifest_path(name, asset_type)
        if not manifest_path.exists():
            raise FileNotFoundError(f"manifest not found: {manifest_path}")

        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = AssetManifest.model_validate(data)

        if new_files is not None:
            manifest.files = new_files
        if status is not None:
            manifest.status = status
        if seedream_card is not None:
            manifest.seedream_card = seedream_card

        manifest_path.write_text(
            manifest.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_file(self, name: str, asset_type: str, asset_file: AssetFile) -> None:
        """追加单个文件到 manifest"""
        manifest_path = self._manifest_path(name, asset_type)
        if not manifest_path.exists():
            raise FileNotFoundError(f"manifest not found: {manifest_path}")
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = AssetManifest.model_validate(data)
        manifest.files.append(asset_file)
        manifest_path.write_text(
            manifest.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def main():
    lib = AssetLibrary()
    args = sys.argv[1:]

    if "--register" in args:
        kwargs = {"name": None, "asset_type": "character", "project": None}
        i = 0
        while i < len(args):
            if args[i] == "--name" and i + 1 < len(args):
                kwargs["name"] = args[i + 1]
            if args[i] == "--type" and i + 1 < len(args):
                kwargs["asset_type"] = args[i + 1]
            if args[i] == "--project" and i + 1 < len(args):
                kwargs["project"] = args[i + 1]
            i += 1
        if not kwargs["name"]:
            print("用法: --register --name <name> --type <type> [--project <project>]")
            sys.exit(1)
        lib.register(**kwargs)
        return

    if "--resolve" in args:
        idx = args.index("--resolve")
        name = args[idx + 1] if idx + 1 < len(args) and not args[idx + 1].startswith("--") else ""
        asset_type = args[idx + 2] if idx + 2 < len(args) and not args[idx + 2].startswith("--") else "character"
        for p in lib.resolve(name, asset_type):
            print(p)
        return

    if "--list" in args:
        project = None
        for i, a in enumerate(args):
            if a == "--project" and i + 1 < len(args):
                project = args[i + 1]
        result = lib.list_by_project(project or "")
        for k, v in result.items():
            print(f"{k}: {v}")
        return

    print("用法:")
    print("  --register --name <name> --type <character|scene|prop> [--project <project>]")
    print("  --resolve <name> <type>")
    print("  --list [--project <project>]")


if __name__ == "__main__":
    main()
