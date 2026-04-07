#!/usr/bin/env python3
"""
asset_version.py — huage888 资产版本控制系统

参考 Toonflow t_assets 表的版本管理机制，为 huage888 提供：
1. 资产版本记录（角色/场景/道具）
2. 版本历史查询
3. 版本回滚（引用旧版本）
4. 版本差异对比

设计原则：
- 资产目录即版本仓库（.huage888/assets/<type>/<code>/）
- 每个版本一个 JSON 文件
- current.json 指向最新版本
- 不修改原始文件，只追加版本

目录结构：
  .huage888/assets/
  ├── character/
  │   ├── C001_漠玫/
  │   │   ├── v1.0_2026-04-03_front.png
  │   │   ├── v1.0_2026-04-03.json        # 元数据
  │   │   ├── v1.1_2026-04-05_refined.png  # 迭代版本
  │   │   ├── v1.1_2026-04-05.json
  │   │   └── current.json                  # → v1.1_2026-04-05.json
  ├── scene/
  │   └── S001_断桥雨中/
  └── prop/
      └── P001_破油纸伞/

用法：

  from asset_version import AssetVersionManager

  manager = AssetVersionManager(base_dir=".huage888/assets")

  # 注册新资产
  asset_id = manager.register(
      code="C001",
      name="漠玫",
      asset_type="character",
      version="v1.0",
      metadata={
          "element_id": "12345",
          "image_url": "https://...",
          "appearance_tags": ["道姑髻", "金色瞳孔"],
      },
      files=["C001_front.png"],
  )

  # 追加新版本
  manager.add_version(
      asset_id=asset_id,
      version="v1.1",
      metadata={"element_id": "12345", "note": "优化瞳孔光效"},
      files=["C001_v1.1.png"],
  )

  # 查询
  current = manager.get_current(asset_id)
  history = manager.get_history(asset_id)
  version = manager.get_version(asset_id, "v1.0")
"""

import json
import os
import re
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────────────────────
# 数据模型
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AssetVersion:
    """资产版本记录"""
    code: str              # 资产编号（C001 / S001 / P001）
    name: str              # 资产名称
    asset_type: str        # 资产类型（character / scene / prop）
    version: str           # 版本号（如 v1.0 / v1.1）
    created_at: str        # 创建时间
    metadata: dict = field(default_factory=dict)  # 元数据（element_id / image_url 等）
    files: list[str] = field(default_factory=list)  # 相关文件列表
    note: str = ""         # 版本说明
    parent_version: Optional[str] = None  # 父版本（用于分支追溯）


@dataclass
class AssetRecord:
    """资产完整记录（含当前版本 + 历史）"""
    code: str
    name: str
    asset_type: str
    current_version: str
    created_at: str
    versions: list[AssetVersion] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)  # 当前版本的 metadata


# ─────────────────────────────────────────────────────────────────────────────
# 核心管理器
# ─────────────────────────────────────────────────────────────────────────────

class AssetVersionManager:
    """
    资产版本管理器

    功能：
    - 注册新资产（创建第一个版本）
    - 追加新版本
    - 查询当前版本
    - 查询版本历史
    - 回滚到指定版本
    - 差异对比（两个版本之间）
    """

    ASSET_TYPES = ("character", "scene", "prop", "shotboard")

    def __init__(self, base_dir: str | Path = ".huage888/assets"):
        self.base_dir = Path(base_dir)

    # ─────────────────────────────────────────────────────────────────
    # 路径辅助
    # ─────────────────────────────────────────────────────────────────

    def _asset_dir(self, code: str, asset_type: str) -> Path:
        """获取资产目录"""
        d = self.base_dir / asset_type / code
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _version_file(self, code: str, asset_type: str, version: str) -> Path:
        """获取版本文件路径"""
        return self._asset_dir(code, asset_type) / f"{version}.json"

    def _current_file(self, code: str, asset_type: str) -> Path:
        """获取 current.json 路径"""
        return self._asset_dir(code, asset_type) / "current.json"

    def _index_file(self) -> Path:
        """获取索引文件路径"""
        return self.base_dir / "assets_index.json"

    # ─────────────────────────────────────────────────────────────────
    # 索引管理
    # ─────────────────────────────────────────────────────────────────

    def _load_index(self) -> dict:
        """加载资产索引"""
        idx = self._index_file()
        if idx.exists():
            return json.loads(idx.read_text(encoding="utf-8"))
        return {}

    def _save_index(self, index: dict) -> None:
        """保存资产索引"""
        idx = self._index_file()
        idx.parent.mkdir(parents=True, exist_ok=True)
        idx.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    def _register_in_index(
        self,
        code: str,
        name: str,
        asset_type: str,
        version: str,
        metadata: dict,
    ) -> None:
        """在索引中注册资产"""
        index = self._load_index()
        if code not in index:
            index[code] = {
                "name": name,
                "type": asset_type,
                "versions": [],
                "current": None,
            }
        index[code]["versions"].append(version)
        index[code]["current"] = version
        index[code]["metadata"] = metadata
        self._save_index(index)

    # ─────────────────────────────────────────────────────────────────
    # 核心操作
    # ─────────────────────────────────────────────────────────────────

    def register(
        self,
        code: str,
        name: str,
        asset_type: str,
        version: str = "v1.0",
        metadata: dict | None = None,
        files: list[str] | None = None,
        note: str = "",
    ) -> str:
        """
        注册新资产（创建第一个版本）

        Args:
            code: 资产编号（C001 / S001 / P001）
            name: 资产名称
            asset_type: 资产类型（character / scene / prop）
            version: 初始版本号
            metadata: 元数据
            files: 相关文件列表
            note: 版本说明

        Returns:
            asset_id（格式：{code}_{version}）
        """
        if asset_type not in self.ASSET_TYPES:
            raise ValueError(f"未知资产类型：{asset_type}，可用：{self.ASSET_TYPES}")

        asset_dir = self._asset_dir(code, asset_type)
        now = datetime.now().isoformat(timespec="seconds")

        # 创建版本记录
        ver = AssetVersion(
            code=code,
            name=name,
            asset_type=asset_type,
            version=version,
            created_at=now,
            metadata=metadata or {},
            files=files or [],
            note=note,
        )

        # 保存版本文件
        ver_file = self._version_file(code, asset_type, version)
        ver_file.write_text(
            json.dumps(ver, default=str, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # 更新 current.json
        current_file = self._current_file(code, asset_type)
        current_file.write_text(
            json.dumps({"version": version, "code": code}, ensure_ascii=False),
            encoding="utf-8",
        )

        # 更新索引
        self._register_in_index(code, name, asset_type, version, metadata or {})

        asset_id = f"{code}_{version}"
        print(f"✅ 注册资产：{asset_id}（{asset_dir.relative_to(self.base_dir)}）", file=__import__("sys").stderr)
        return asset_id

    def add_version(
        self,
        asset_id: str,
        version: str,
        metadata: dict | None = None,
        files: list[str] | None = None,
        note: str = "",
        parent_version: str | None = None,
    ) -> str:
        """
        追加新版本

        Args:
            asset_id: 资产 ID（如 C001_v1.0 或纯 code 如 C001）
            version: 新版本号（如 v1.1）
            metadata: 新版本元数据
            files: 新版本相关文件
            note: 版本说明
            parent_version: 父版本（用于追溯）

        Returns:
            asset_id
        """
        # 解析 asset_id
        if "_v" in asset_id:
            code = asset_id.split("_v")[0]
        else:
            code = asset_id

        index = self._load_index()
        if code not in index:
            raise ValueError(f"资产不存在：{code}")

        record = index[code]
        asset_type = record["type"]
        current_ver = record["current"]
        now = datetime.now().isoformat(timespec="seconds")

        # 创建新版本
        ver = AssetVersion(
            code=code,
            name=record["name"],
            asset_type=asset_type,
            version=version,
            created_at=now,
            metadata=metadata or {},
            files=files or [],
            note=note,
            parent_version=parent_version or current_ver,
        )

        # 保存版本文件
        ver_file = self._version_file(code, asset_type, version)
        ver_file.write_text(
            json.dumps(ver, default=str, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # 更新 current.json
        current_file = self._current_file(code, asset_type)
        current_file.write_text(
            json.dumps({"version": version, "code": code}, ensure_ascii=False),
            encoding="utf-8",
        )

        # 更新索引
        record["versions"].append(version)
        record["current"] = version
        if metadata:
            record["metadata"] = metadata
        self._save_index(index)

        new_id = f"{code}_{version}"
        print(f"✅ 追加版本：{new_id}（基于 {parent_version or current_ver}）", file=__import__("sys").stderr)
        return new_id

    # ─────────────────────────────────────────────────────────────────
    # 查询
    # ─────────────────────────────────────────────────────────────────

    def get_current(self, code: str) -> AssetVersion | None:
        """获取资产的当前版本"""
        index = self._load_index()
        if code not in index:
            return None

        record = index[code]
        version = record["current"]
        ver_file = self._version_file(code, record["type"], version)
        if not ver_file.exists():
            return None

        return AssetVersion(**json.loads(ver_file.read_text(encoding="utf-8")))

    def get_version(self, code: str, version: str) -> AssetVersion | None:
        """获取资产的指定版本"""
        index = self._load_index()
        if code not in index:
            return None

        record = index[code]
        ver_file = self._version_file(code, record["type"], version)
        if not ver_file.exists():
            return None

        return AssetVersion(**json.loads(ver_file.read_text(encoding="utf-8")))

    def get_history(self, code: str) -> list[AssetVersion]:
        """获取资产的所有版本（按时间倒序）"""
        index = self._load_index()
        if code not in index:
            return []

        record = index[code]
        versions = []
        for v in record["versions"]:
            ver = self.get_version(code, v)
            if ver:
                versions.append(ver)

        versions.sort(key=lambda x: x.created_at, reverse=True)
        return versions

    def list_assets(self, asset_type: str | None = None) -> list[dict]:
        """
        列出所有资产

        Args:
            asset_type: 过滤类型（可选）

        Returns:
            资产列表
        """
        index = self._load_index()
        if asset_type:
            return [r for r in index.values() if r["type"] == asset_type]
        return list(index.values())

    # ─────────────────────────────────────────────────────────────────
    # 高级操作
    # ─────────────────────────────────────────────────────────────────

    def rollback(self, code: str, version: str) -> bool:
        """
        回滚到指定版本

        Args:
            code: 资产编号
            version: 目标版本

        Returns:
            是否成功
        """
        ver = self.get_version(code, version)
        if not ver:
            print(f"❌ 版本不存在：{code} {version}", file=__import__("sys").stderr)
            return False

        # 更新 current.json
        current_file = self._current_file(code, ver.asset_type)
        current_file.write_text(
            json.dumps({"version": version, "code": code}, ensure_ascii=False),
            encoding="utf-8",
        )

        # 更新索引
        index = self._load_index()
        if code in index:
            index[code]["current"] = version
            index[code]["metadata"] = ver.metadata
            self._save_index(index)

        print(f"✅ 回滚成功：{code} → {version}", file=__import__("sys").stderr)
        return True

    def diff(self, code: str, version_a: str, version_b: str) -> dict:
        """
        对比两个版本之间的差异

        Args:
            code: 资产编号
            version_a: 版本 A（旧）
            version_b: 版本 B（新）

        Returns:
            差异报告
        """
        ver_a = self.get_version(code, version_a)
        ver_b = self.get_version(code, version_b)

        if not ver_a or not ver_b:
            raise ValueError(f"版本不存在")

        diff_keys = set(ver_a.metadata.keys()) | set(ver_b.metadata.keys())
        changes = {}

        for key in diff_keys:
            val_a = ver_a.metadata.get(key)
            val_b = ver_b.metadata.get(key)
            if val_a != val_b:
                changes[key] = {"from": val_a, "to": val_b}

        return {
            "code": code,
            "asset_type": ver_a.asset_type,
            "version_a": version_a,
            "version_b": version_b,
            "changed_fields": list(changes.keys()),
            "details": changes,
            "files_a": ver_a.files,
            "files_b": ver_b.files,
        }

    def export_manifest(self) -> dict:
        """
        导出完整资产清单（用于项目交付）

        Returns:
            资产清单（含所有版本的 element_id / image_url）
        """
        index = self._load_index()
        manifest = {}

        for code, record in index.items():
            versions = {}
            for v in record["versions"]:
                ver = self.get_version(code, v)
                if ver:
                    versions[v] = {
                        "metadata": ver.metadata,
                        "files": ver.files,
                        "created_at": ver.created_at,
                        "note": ver.note,
                    }

            manifest[code] = {
                "name": record["name"],
                "type": record["type"],
                "current": record["current"],
                "versions": versions,
            }

        return manifest

    def import_manifest(self, manifest: dict) -> None:
        """
        从清单恢复所有资产注册

        Args:
            manifest: export_manifest() 导出的清单
        """
        for code, data in manifest.items():
            for version, ver_data in data["versions"].items():
                if version == data["current"]:
                    self.register(
                        code=code,
                        name=data["name"],
                        asset_type=data["type"],
                        version=version,
                        metadata=ver_data["metadata"],
                        files=ver_data["files"],
                        note=ver_data.get("note", ""),
                    )
                else:
                    self.add_version(
                        asset_id=code,
                        version=version,
                        metadata=ver_data["metadata"],
                        files=ver_data["files"],
                        note=ver_data.get("note", ""),
                    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    import argparse
    parser = argparse.ArgumentParser(description="huage888 资产版本管理")
    sub = parser.add_subparsers(dest="cmd")

    p_reg = sub.add_parser("register", help="注册新资产")
    p_reg.add_argument("--code", required=True, help="资产编号（C001）")
    p_reg.add_argument("--name", required=True, help="资产名称")
    p_reg.add_argument("--type", required=True, choices=["character", "scene", "prop"], help="资产类型")
    p_reg.add_argument("--version", default="v1.0", help="版本号")
    p_reg.add_argument("--metadata", help="元数据（JSON 字符串）")
    p_reg.add_argument("--note", default="", help="版本说明")

    p_ver = sub.add_parser("add-version", help="追加版本")
    p_ver.add_argument("--asset-id", required=True, help="资产ID或编号")
    p_ver.add_argument("--version", required=True, help="新版本号")
    p_ver.add_argument("--metadata", help="元数据（JSON 字符串）")
    p_ver.add_argument("--note", default="", help="版本说明")

    p_list = sub.add_parser("list", help="列出资产")
    p_list.add_argument("--type", help="过滤类型")

    p_hist = sub.add_parser("history", help="查看版本历史")
    p_hist.add_argument("code", help="资产编号")

    p_diff = sub.add_parser("diff", help="对比版本")
    p_diff.add_argument("code", help="资产编号")
    p_diff.add_argument("version_a", help="版本 A")
    p_diff.add_argument("version_b", help="版本 B")

    p_export = sub.add_parser("export", help="导出清单")
    p_import = sub.add_parser("import", help="导入清单")
    p_import.add_argument("manifest_file", help="清单文件")

    args = parser.parse_args()
    manager = AssetVersionManager()

    if args.cmd == "register":
        import json as _json
        metadata = _json.loads(args.metadata) if args.metadata else {}
        manager.register(args.code, args.name, args.type, args.version, metadata, note=args.note)

    elif args.cmd == "add-version":
        import json as _json
        metadata = _json.loads(args.metadata) if args.metadata else {}
        manager.add_version(args.asset_id, args.version, metadata, note=args.note)

    elif args.cmd == "list":
        for asset in manager.list_assets(args.type):
            print(f"{asset['code']}: {asset['name']} ({asset['type']}) | 当前版本: {asset['current']}")

    elif args.cmd == "history":
        for v in manager.get_history(args.code):
            print(f"  [{v.version}] {v.created_at} | {v.note or '(无说明)'}")

    elif args.cmd == "diff":
        d = manager.diff(args.code, args.version_a, args.version_b)
        import json
        print(json.dumps(d, ensure_ascii=False, indent=2))

    elif args.cmd == "export":
        import json
        manifest = manager.export_manifest()
        print(json.dumps(manifest, ensure_ascii=False, indent=2))

    elif args.cmd == "import":
        import json
        manifest = json.loads(Path(args.manifest_file).read_text(encoding="utf-8"))
        manager.import_manifest(manifest)
        print(f"✅ 导入完成：{len(manifest)} 个资产")


if __name__ == "__main__":
    _cli()
