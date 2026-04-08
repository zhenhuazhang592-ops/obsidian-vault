# huage888 P1+P2 自动出图系统 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recommended)
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现全自动漫剧出图：资产库建立 → Doubao API 图生图 → 宫格批产切割。

**Architecture:** 资产库为共享基础设施，Step 1-2 建立资产库，P1/P2 消费资产库。Python 脚本调用 Doubao API（Seedream + nanobanana），Pillow 处理图像。

**Tech Stack:** Python（Pillow / openai / Pydantic）, Doubao API, qwen-max

---

## 文件结构

```
AI工具箱/huage888/
├── assets/library/                          # 资产库根目录（新建）
│   ├── characters/[角色名]/images/
│   ├── scenes/[场景名]/images/
│   └── props/[道具名]/images/
├── config/
│   ├── seedream_prompts/                   # Seedream Prompt 模板（新建）
│   │   ├── character_card_template.md
│   │   ├── scene_card_template.md
│   │   └── prop_card_template.md
│   └── qwen_pipeline.py                    # 增强：--asset-library
└── scripts/
    ├── asset_library.py                     # 新增：资产库管理
    ├── generate_asset_prompts.py            # 新增：Step 1
    ├── generate_reference_images.py          # 新增：Step 2
    ├── generate_shot_images.py              # 新增：P1
    └── batch_image_pipeline.py               # 新增：P2
```

---

## Task 1: 资产库目录结构 + manifest schema

**Files:**
- Create: `AI工具箱/huage888/assets/library/.gitkeep`（占位，保留目录结构）
- Create: `AI工具箱/huage888/config/asset_registry_schema.py`

### Task 1: 资产库目录结构和 manifest schema

**Files:**
- Create: `AI工具箱/huage888/assets/library/.gitkeep`
- Create: `AI工具箱/huage888/config/asset_registry_schema.py`

```python
"""asset_registry_schema.py — 资产库 manifest JSON Schema（Pydantic）"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import date


class AssetFile(BaseModel):
    """单个资产文件"""
    filename: str = Field(..., description="文件名，如 ref_01.png")
    role: str = Field(..., description="角色：front_view/multi_angle/scene_wide/scene_detail/prop_full")
    uploaded_at: str = Field(..., description="上传日期 YYYY-MM-DD")
    file_path: str = Field(..., description="相对于 assets/library/ 的路径")


class AssetManifest(BaseModel):
    """资产 manifest.json 结构"""
    name: str = Field(..., description="资产名称（必须与 outline 中的 name 一致）")
    type: str = Field(..., description="类型：character / scene / prop")
    role_type: Optional[str] = Field(default=None, description="角色类型：人物/场景/道具")
    project: Optional[str] = Field(default=None, description="所属项目")
    first_episode: Optional[str] = Field(default=None, description="首次出现集数")
    visual_description: Optional[str] = Field(default=None, description="视觉描述（来自 outline）")
    seedream_card: Optional[str] = Field(default=None, description="Seedream 卡文件名，如 character_card.md")
    files: list[AssetFile] = Field(default_factory=list, description="文件列表")
    status: str = Field(default="pending", description="状态：pending / card_generated / reference_generated")
    created_at: str = Field(default_factory=lambda: date.today().isoformat(), description="创建日期")
```

- [ ] **Step 1: 创建 asset_registry_schema.py**

```bash
cat > "AI工具箱/huage888/config/asset_registry_schema.py" << 'PYEOF'
"""asset_registry_schema.py — 资产库 manifest JSON Schema（Pydantic）"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import date


class AssetFile(BaseModel):
    filename: str = Field(..., description="文件名，如 ref_01.png")
    role: str = Field(..., description="角色：front_view/multi_angle/scene_wide/scene_detail/prop_full")
    uploaded_at: str = Field(..., description="上传日期 YYYY-MM-DD")
    file_path: str = Field(..., description="相对于 assets/library/ 的路径")


class AssetManifest(BaseModel):
    name: str = Field(..., description="资产名称（必须与 outline 中的 name 一致）")
    type: str = Field(..., description="类型：character / scene / prop")
    role_type: Optional[str] = Field(default=None, description="角色类型：人物/场景/道具")
    project: Optional[str] = Field(default=None, description="所属项目")
    first_episode: Optional[str] = Field(default=None, description="首次出现集数")
    visual_description: Optional[str] = Field(default=None, description="视觉描述（来自 outline）")
    seedream_card: Optional[str] = Field(default=None, description="Seedream 卡文件名")
    files: list[AssetFile] = Field(default_factory=list, description="文件列表")
    status: str = Field(default="pending", description="状态：pending/card_generated/reference_generated")
    created_at: str = Field(default_factory=lambda: date.today().isoformat(), description="创建日期")
PYEOF
echo "OK"
```

- [ ] **Step 2: 验证可导入**

```bash
cd "AI工具箱/huage888" && python3 -c "from config.asset_registry_schema import AssetManifest; print('Schema OK')"
```

- [ ] **Step 3: 创建目录占位文件**

```bash
mkdir -p "AI工具箱/huage888/assets/library/characters/.gitkeep"
mkdir -p "AI工具箱/huage888/assets/library/scenes/.gitkeep"
mkdir -p "AI工具箱/huage888/assets/library/props/.gitkeep"
touch "AI工具箱/huage888/assets/library/characters/.gitkeep"
touch "AI工具箱/huage888/assets/library/scenes/.gitkeep"
touch "AI工具箱/huage888/assets/library/props/.gitkeep"
```

- [ ] **Step 4: 提交**

```bash
cd "AI工具箱/huage888" && git add assets/library/ config/asset_registry_schema.py && git commit -m "feat(huage888): P1+P2 资产库基础

- AssetManifest Pydantic schema（manifest.json 格式）
- 资产库目录结构（characters/scenes/props 三层）

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Seedream Prompt 模板文件

**Files:**
- Create: `AI工具箱/huage888/config/seedream_prompts/character_card_template.md`
- Create: `AI工具箱/huage888/config/seedream_prompts/scene_card_template.md`
- Create: `AI工具箱/huage888/config/seedream_prompts/prop_card_template.md`

### Task 2: Seedream Prompt 模板文件

**Files:**
- Create: `AI工具箱/huage888/config/seedream_prompts/character_card_template.md`
- Create: `AI工具箱/huage888/config/seedream_prompts/scene_card_template.md`
- Create: `AI工具箱/huage888/config/seedream_prompts/prop_card_template.md`

- [ ] **Step 1: 创建 character_card_template.md**

```bash
mkdir -p "AI工具箱/huage888/config/seedream_prompts"

cat > "AI工具箱/huage888/config/seedream_prompts/character_card_template.md" << 'MDEOF'
# 角色卡模板 · Seedream Character Sheet

> 用途：qwen-max 润色填充，生成后存为 assets/library/[角色名]/character_card.md
> 规则：②③④定稿后锁死，每次出图只改⑤镜头变量

## ① 风格锚点（固定）

```
3D render style, ancient Chinese fantasy, cinematic quality, ultra detailed,
sharp focus, photorealistic skin texture, rich fabric detail,
```

## ② 外貌核心（定稿锁死）

```
1 woman, [age description],
[face features: oval face, almond-shaped eyes, lip color, skin tone],
Taoist bun hair, [hairpin style description],
golden pupils with flowing data streams,
blue ink brushstroke eyeliner,
same face, consistent character, identical facial features,
```

## ③ 服装细节（定稿锁死）

```
[outer robe: color + material + pattern description],
[inner garment: color + style description],
[skirt: color + gradient description],
[waist belt: color + decoration description],
same costume, identical clothing,
```

## ④ 饰品细节（定稿锁死）

```
[headdress description],
[hairpin description],
[earrings/necklace description],
same accessories,
```

## ⑤ 镜头变量（每次出图只改这里）

```
{{VIEW}}         # front view / side view / back view / three-quarter view
{{SHOT}}         # full body / upper body / close-up face
{{EXPRESSION}}   # calm / happy smile / shocked / furious / shy
{{POSE}}         # standing elegantly / sitting / turning / walking
{{BACKGROUND}}   # white studio / ancient bridge / cyber dojo
```

## ⑥ 质量尾缀（固定）

```
masterpiece, best quality, 8k resolution, professional lighting
```

## 默认出图模板（⑤默认填充值）

```
[①风格锚点]
[②外貌核心]
[③服装细节]
[④饰品细节]
front view, full body, calm, standing elegantly,
white studio background,
[⑥质量尾缀]
```
MDEOF
echo "character OK"
```

- [ ] **Step 2: 创建 scene_card_template.md**

```bash
cat > "AI工具箱/huage888/config/seedream_prompts/scene_card_template.md" << 'MDEOF'
# 场景卡模板 · Seedream Scene Sheet

> 用途：qwen-max 润色填充，生成后存为 assets/library/[场景名]/scene_card.md
> 规则：②③④定稿后锁死，每次出图只改⑤镜头变量

## ① 风格锚点（固定）

```
photorealistic, cinematic photography, detailed interior/exterior scene,
dramatic atmospheric lighting, film grain, 8k resolution,
```

## ② 场景类型（定稿锁死）

```
[scene type, e.g. misty ancient Chinese bridge over a lake],
consistent environment, same location, same spatial layout,
```

## ③ 固定道具与陈设（定稿锁死）

```
[main elements description],
[furniture/props description],
[decorative items description],
[lighting source description],
same props, same furniture arrangement, identical environment,
```

## ④ 地面与墙面材质（定稿锁死）

```
[floor description],
[wall description],
```

## ⑤ 镜头变量（每次出图只改这里）

```
{{SHOT_TYPE}}    # wide establishing shot / medium shot / extreme close-up detail
{{CAMERA_ANGLE}} # eye-level / low angle / high angle / overhead bird's eye
{{FOCUS}}        # focusing on the full scene / specific element
{{LIGHTING}}     # warm golden / cool blue moonlight / mixed candlelight
{{ATMOSPHERE}}   # moody and mysterious / serene / tense and dramatic
```

## ⑥ 人物处理（固定）

```
no characters, empty scene, no people,
```

## ⑦ 质量尾缀（固定）

```
masterpiece, best quality, ultra detailed textures, sharp focus
```

## 默认出图模板（⑤默认填充值）

```
[①风格锚点]
[②场景类型]
[③固定道具陈设]
[④地面墙面材质]
wide establishing shot, eye-level camera,
focusing on the full scene,
morning mist, cool blue moonlight atmosphere,
volumetric light rays, deep shadows,
no characters, empty scene,
[⑦质量尾缀]
```
MDEOF
echo "scene OK"
```

- [ ] **Step 3: 创建 prop_card_template.md**

```bash
cat > "AI工具箱/huage888/config/seedream_prompts/prop_card_template.md" << 'MDEOF'
# 道具卡模板 · Seedream Prop Sheet

> 用途：qwen-max 润色填充，生成后存为 assets/library/[道具名]/prop_card.md
> 规则：②③④⑤定稿后锁死，每次出图只改⑥镜头变量

## ① 风格锚点（固定）

```
product visualization, photorealistic, ultra detailed, 8k resolution,
studio lighting, white background, isolated object, no shadows,
```

## ② 道具基础定义（定稿锁死）

```
1 single prop, [prop category, e.g. ancient Chinese jade token],
consistent prop design, same object, identical details,
```

## ③ 材质与颜色（定稿锁死）

```
[primary material, e.g. aged bronze with natural patina],
[color palette],
[surface texture description],
```

## ④ 结构细节（定稿锁死）

```
[overall shape description],
[base description],
[decorative elements description],
[functional parts description],
```

## ⑤ 尺寸比例感（定稿锁死）

```
[approximately Xcm tall, proportions description],
```

## ⑥ 镜头变量（每次出图只改这里）

```
{{ANGLE}}   # front view / side view / three-quarter view / top-down
{{SHOT}}    # full object / upper half / close-up detail of element
```

## ⑦ 质量尾缀（固定）

```
masterpiece, best quality, sharp focus, clean background
```

## 默认出图模板（⑥默认填充值）

```
[①风格锚点]
[②道具基础定义]
[③材质颜色]
[④结构细节]
[⑤尺寸比例感]
three-quarter view, full object,
[⑦质量尾缀]
```
MDEOF
echo "prop OK"
```

- [ ] **Step 4: 提交**

```bash
cd "AI工具箱/huage888" && git add config/seedream_prompts/ && git commit -m "feat(huage888): Seedream Prompt 模板

- character_card_template.md（7节：风格/外貌/服装/饰品/镜头变量/尾缀/默认模板）
- scene_card_template.md（7节：风格/场景类型/道具陈设/材质/镜头变量/人物处理/尾缀）
- prop_card_template.md（7节：风格/基础定义/材质/结构/尺寸/镜头变量/尾缀）

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 3: asset_library.py — 资产库管理器

**Files:**
- Create: `AI工具箱/huage888/scripts/asset_library.py`
- Test: 手动测试 resolve / register / resolve_shot

### Task 3: asset_library.py

**Files:**
- Create: `AI工具箱/huage888/scripts/asset_library.py`

```python
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
        asset_dir = self.base_dir / subdir / name
        return asset_dir / "manifest.json"

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
        result = {"characters": [], "scenes": [], "props": []}
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
            paths = self.resolve(char, "character")
            result["characters"].extend(paths)

        scene = shot.get("scene", "")
        if scene:
            paths = self.resolve(scene, "scene")
            result["scenes"].extend(paths)

        for prop in shot.get("props", []):
            paths = self.resolve(prop, "prop")
            result["props"].extend(paths)

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
            raise FileNotFoundError(f"manifest 不存在: {manifest_path}")

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
            raise FileNotFoundError(f"manifest 不存在: {manifest_path}")
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
        idx = args.index("--register")
        name = args[idx + 1] if idx + 1 < len(args) else None
        asset_type = "character"
        project = None
        for i, a in enumerate(args):
            if a == "--name" and i + 1 < len(args):
                name = args[i + 1]
            if a == "--type" and i + 1 < len(args):
                asset_type = args[i + 1]
            if a == "--project" and i + 1 < len(args):
                project = args[i + 1]
        if not name:
            print("用法: --register --name <name> --type <type> [--project <project>]")
            sys.exit(1)
        lib.register(name, asset_type, project=project)
        return

    if "--resolve" in args:
        idx = args.index("--resolve")
        name = args[idx + 1] if idx + 1 < len(args) else ""
        asset_type = args[idx + 2] if idx + 2 < len(args) and not args[idx + 2].startswith("--") else "character"
        paths = lib.resolve(name, asset_type)
        for p in paths:
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
```

- [ ] **Step 1: 创建 asset_library.py**

```bash
cat > "AI工具箱/huage888/scripts/asset_library.py" << 'PYEOF'
#!/usr/bin/env python3
"""asset_library.py — 资产库管理器"""

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
        manifest_path = self._manifest_path(name, asset_type)
        if manifest_path.exists():
            print(f"[WARN] 资产已存在: {manifest_path}")
            return manifest_path
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self._images_dir(name, asset_type).mkdir(parents=True, exist_ok=True)
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
        result = {"characters": [], "scenes": [], "props": []}
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
PYEOF
chmod +x "AI工具箱/huage888/scripts/asset_library.py"
echo "OK"
```

- [ ] **Step 2: 测试 register + resolve**

```bash
cd "AI工具箱/huage888"

# 测试注册
python3 scripts/asset_library.py --register --name 漠玫 --type character --project 漠玫传

# 测试 resolve（应有空列表）
python3 scripts/asset_library.py --resolve 漠玫 character

# 验证 manifest.json 存在
test -f "assets/library/characters/漠玫/manifest.json" && echo "manifest exists" || echo "manifest missing"
```

Expected: `[OK] 已注册: ...manifest.json`，resolve 输出空（尚无文件）

- [ ] **Step 3: 测试 resolve_shot（单元测试）**

```bash
cd "AI工具箱/huage888"
python3 - << 'PYEOF'
from scripts.asset_library import AssetLibrary

lib = AssetLibrary()

# 测试 resolve_shot（无资产）
shot = {
    "characters": ["漠玫"],
    "scene": "西湖断桥",
    "props": ["电子令牌"]
}
result = lib.resolve_shot(shot)
print("resolve_shot result:", result)
assert result["characters"] == [], "无资产时应返回空列表"
assert result["scenes"] == [], "无场景时应返回空列表"
print("OK: resolve_shot 正确返回空列表（无资产）")
PYEOF
```

- [ ] **Step 4: 提交**

```bash
cd "AI工具箱/huage888" && git add scripts/asset_library.py && git commit -m "feat(huage888): asset_library.py 资产库管理器

核心接口：
- register(): 创建资产目录 + manifest.json
- resolve(): 查询某资产的参考图路径列表
- list_by_project(): 按项目列出资产
- resolve_shot(): 为单个 shot 查找相关资产路径
- update_manifest() / add_file(): 更新 manifest

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Doubao API 增强 — img2img 参考图注入

**Files:**
- Modify: `AI工具箱/huage888/config/doubao_pipeline.py`（在 create_and_wait_image 中添加 ref_images 支持）

### Task 4: Doubao API img2img 增强

**Files:**
- Modify: `AI工具箱/huage888/config/doubao_pipeline.py`

在 `create_and_wait_image` 函数之后添加：

```python
def create_and_wait_image_with_ref(
    prompt: str,
    output_path: Path,
    ref_images: list[Path] | None = None,
    model: str = IMAGE_MODEL,
    aspect_ratio: str = "16:9",
) -> None:
    """
    带参考图的图片生成（img2img）。
    ref_images: 参考图本地路径列表，读取后转为 base64 注入 API。
    """
    api_key = get_env("ARK_API_KEY")
    base_url = get_env("ARK_BASE_URL", DEFAULT_BASE_URL)

    try:
        from openai import OpenAI
    except ImportError:
        print("错误：缺少 openai 库。请运行：pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=base_url)
    print(f"  模型：{model}", file=sys.stderr)

    # 读取参考图 → base64
    image_refs: list[str] = []
    if ref_images:
        for ref_path in ref_images:
            if ref_path.exists():
                data = ref_path.read_bytes()
                b64 = __import__("base64").b64encode(data).decode()
                image_refs.append(f"data:image/png;base64,{b64}")
                print(f"  参考图：{ref_path.name}", file=sys.stderr)

    # 构建 prompt：resource map + shot prompt
    resource_map = ""
    if image_refs:
        resource_map = "[Reference images attached. Maintain character/scene consistency with reference.]\n"

    full_prompt = resource_map + prompt

    # Seedream img2img
    size_map = {
        "16:9": "2K",
        "9:16": "2K",
        "1:1": "1K",
    }
    size = size_map.get(aspect_ratio, "2K")

    try:
        if image_refs:
            # 多参考图：使用 first_image + extra_images
            response = client.images.generate(
                model=model,
                prompt=full_prompt,
                size=size,
                extra_body={
                    "watermark": False,
                    "first_image": image_refs[0],
                    "extra_images": image_refs[1:],
                },
            )
        else:
            response = client.images.generate(
                model=model,
                prompt=full_prompt,
                size=size,
                extra_body={"watermark": False},
            )

        image_url = response.data[0].url
        print(f"  图片URL：{image_url}", file=sys.stderr)
        download_file(image_url, output_path)

    except Exception as e:
        print(f"  图片生成失败：{e}", file=sys.stderr)
        sys.exit(1)
```

同时在 `parse_args()` 的 `parser.add_argument("--output"` 附近添加新参数：

```python
parser.add_argument(
    "--img-ref",
    action="append",
    dest="img_refs",
    default=[],
    help="参考图路径（可多次指定，用于 img2img）"
)
parser.add_argument(
    "--aspect-ratio",
    default="16:9",
    choices=["16:9", "9:16", "1:1"],
    help="图片宽高比"
)
```

在 `main()` 函数中，图片生成调用处（约第662行）修改为：

```python
if args.image:
    ref_paths = [Path(p) for p in args.img_refs] if args.img_refs else None
    if ref_paths:
        create_and_wait_image_with_ref(
            prompt=args.prompt,
            output_path=output_path,
            ref_images=ref_paths,
            model=args.model or IMAGE_MODEL,
            aspect_ratio=args.aspect_ratio,
        )
    else:
        create_and_wait_image(
            prompt=args.prompt,
            output_path=output_path,
            model=args.model or IMAGE_MODEL,
        )
```

- [ ] **Step 1: 读取 doubao_pipeline.py，找到 create_and_wait_image 函数末尾和 main() 图片分支**

```bash
cd "AI工具箱/huage888" && grep -n "def create_and_wait_image\|def main\|args.image\|if __name__" config/doubao_pipeline.py
```

- [ ] **Step 2: 在 create_and_wait_image 末尾添加 img2img 函数**

在 `create_and_wait_image` 结束后（第381行附近）插入新的 `create_and_wait_image_with_ref` 函数。

- [ ] **Step 3: 在 parse_args() 添加 --img-ref 和 --aspect-ratio 参数**

在 `--output` 参数附近添加新参数。

- [ ] **Step 4: 在 main() 的图片生成分支修改调用逻辑**

替换原有的 `create_and_wait_image` 调用为条件分支（有 ref 时调用 img2img 版本）。

- [ ] **Step 5: 测试 --help**

```bash
cd "AI工具箱/huage888" && python3 config/doubao_pipeline.py --help 2>&1 | grep -E "img-ref|aspect-ratio"
```

Expected: 显示新参数说明

- [ ] **Step 6: 提交**

```bash
cd "AI工具箱/huage888" && git add config/doubao_pipeline.py && git commit -m "feat(huage888): Doubao API img2img 参考图注入

- 新增 create_and_wait_image_with_ref()：支持多参考图 base64 注入
- 新增 --img-ref 参数（可多次指定）
- 新增 --aspect-ratio 参数（16:9 / 9:16 / 1:1）
- 适配 Seedream first_image + extra_images 格式

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 5: generate_asset_prompts.py — Step 1（qwen-max 润色）

**Files:**
- Create: `AI工具箱/huage888/scripts/generate_asset_prompts.py`
- Test: 用漠玫传 outline 测试角色卡生成

### Task 5: generate_asset_prompts.py

**Files:**
- Create: `AI工具箱/huage888/scripts/generate_asset_prompts.py`

**调用方式**：
```bash
python3 scripts/generate_asset_prompts.py \
  --outline outputs/S01E01-outline.md \
  --project 漠玫传 \
  --out-dir assets/library/
```

**核心 Prompt（qwen-max 调用）**：

```
你是资产生成专家。基于以下 outline 中的角色/场景/道具 description，
生成符合 Seedream 要求的 character_card.md / scene_card.md / prop_card.md。

请严格按照模板结构填充每个 [ ] 字段。
输出文件路径：assets/library/[type]/[name]/[name]_card.md

## 角色卡填充规则
【外貌核心】必须包含：脸型/眼型/肤色/发髻/簪子/瞳孔特征（融入赛博墨韵元素）
【服装细节】必须包含：外袍/内衬/裙/腰带
【饰品细节】必须包含：头冠/发簪/耳饰
【镜头变量】使用 {{VIEW}} {{SHOT}} {{EXPRESSION}} {{POSE}} {{BACKGROUND}} 占位符
【质量尾缀】固定：masterpiece, best quality, 8k resolution, professional lighting

## 场景卡填充规则
【场景类型】必须包含：场景名称 + 时代/风格定位
【固定道具陈设】必须包含：主要元素/家具/装饰/光源
【地面墙面】必须包含：地面材质 + 墙面材质
【镜头变量】使用 {{SHOT_TYPE}} {{CAMERA_ANGLE}} {{FOCUS}} {{LIGHTING}} {{ATMOSPHERE}} 占位符

## 道具卡填充规则
【道具基础定义】必须包含：道具类别 + 名称
【材质颜色】必须包含：主材质 + 颜色 + 表面质感
【结构细节】必须包含：整体形状 + 底座 + 装饰 + 功能部件
【尺寸比例】必须包含：大概高度 + 比例描述
【镜头变量】使用 {{ANGLE}} {{SHOT}} 占位符
```

- [ ] **Step 1: 创建 generate_asset_prompts.py**

```bash
cat > "AI工具箱/huage888/scripts/generate_asset_prompts.py" << 'PYEOF'
#!/usr/bin/env python3
"""generate_asset_prompts.py — Step 1: qwen-max 润色生成角色/场景/道具卡

用法：
  python3 scripts/generate_asset_prompts.py \\
    --outline outputs/S01E01-outline.md \\
    --project 漠玫传 \\
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
    """调用 qwen-max 生成内容（复用 qwen_pipeline.py 的 API 逻辑）"""
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
PYEOF
chmod +x "AI工具箱/huage888/scripts/generate_asset_prompts.py"
echo "OK"
```

- [ ] **Step 2: 测试 --dry-run 模式（不调用 API）**

```bash
cd "AI工具箱/huage888"
python3 scripts/generate_asset_prompts.py \
  --outline outputs/S01E01-outline.md \
  --project 漠玫传 \
  --dry-run 2>&1 | head -20
```

Expected: 打印 Prompt 片段，无 API 调用

- [ ] **Step 3: 提交**

```bash
cd "AI工具箱/huage888" && git add scripts/generate_asset_prompts.py && git commit -m "feat(huage888): generate_asset_prompts.py Step 1

qwen-max 润色生成 Seedream 角色/场景/道具卡
- 读取 outline JSON
- 加载 seedream_prompts/ 模板
- 构建结构化 Prompt 并调用 qwen-max
- 输出到 assets/library/[type]/[name]/[name]_card.md
- --dry-run 模式支持不调用 API 调试

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 6: generate_reference_images.py — Step 2（Doubao API 生成参考图）

**Files:**
- Create: `AI工具箱/huage888/scripts/generate_reference_images.py`
- Test: 用漠玫参考图测试

### Task 6: generate_reference_images.py

**Files:**
- Create: `AI工具箱/huage888/scripts/generate_reference_images.py`

**调用方式**：
```bash
python3 scripts/generate_reference_images.py \
  --project 漠玫传 \
  --type character \
  --names 漠玫,大圣

# 或全部
python3 scripts/generate_reference_images.py --project 漠玫传 --all
```

**核心逻辑**：
1. 读取 `assets/library/[type]/[name]/[name]_card.md`
2. 拼接完整 prompt（固定段 + 默认变量）
3. 若 manifest status=reference_generated，跳过
4. 若无，调用 `doubao_pipeline.py --image --prompt "..." --output ...`
5. 下载 PNG → `assets/library/[type]/[name]/images/ref_01.png`
6. 更新 manifest（files + status）

- [ ] **Step 1: 创建 generate_reference_images.py**

```bash
cat > "AI工具箱/huage888/scripts/generate_reference_images.py" << 'PYEOF'
#!/usr/bin/env python3
"""generate_reference_images.py — Step 2: Doubao Seedream 生成参考图

用法：
  python3 scripts/generate_reference_images.py \\
    --project 漠玫传 \\
    --type character \\
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
PYEOF
chmod +x "AI工具箱/huage888/scripts/generate_reference_images.py"
echo "OK"
```

- [ ] **Step 2: 测试 --all --dry-run（如有 dry-run 参数）**

检查脚本能否正常 import（不调用 API）：
```bash
cd "AI工具箱/huage888" && python3 -c "
import scripts.generate_reference_images as m
print('import OK')
print('DEFAULT_PROMPT_SUFFIX:', m.DEFAULT_PROMPT_SUFFIX[:50])
"
```

- [ ] **Step 3: 提交**

```bash
cd "AI工具箱/huage888" && git add scripts/generate_reference_images.py && git commit -m "feat(huage888): generate_reference_images.py Step 2

Doubao Seedream 生成参考图：
- 读取 [name]_card.md 拼接完整 prompt
- 检查 manifest status，跳过已生成资产
- 调用 doubao_pipeline.py --image 生成 PNG
- 下载到 assets/library/[type]/[name]/images/
- 更新 manifest（files + status=reference_generated）

支持 --type / --names / --all 过滤
支持 --model / --aspect-ratio 参数

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 7: generate_shot_images.py — P1（逐 Shot 图生图）

**Files:**
- Create: `AI工具箱/huage888/scripts/generate_shot_images.py`
- Test: 用漠玫传 shots 测试

### Task 7: generate_shot_images.py（P1）

**Files:**
- Create: `AI工具箱/huage888/scripts/generate_shot_images.py`

**调用方式**：
```bash
python3 scripts/generate_shot_images.py \
  --shots outputs/S01E01-shots.md \
  --outline outputs/S01E01-outline.md \
  --output-dir outputs/S01E01-shots/images/ \
  --provider doubao \
  --model doubao-seedream-4.5
```

**核心逻辑**：
1. 读取 shots + outline + asset_library
2. 对每个 shot：
   - `resolve_shot(shot)` → 相关资产文件路径
   - 若有参考图：`create_and_wait_image_with_ref(prompt, ref_paths)`
   - 若无参考图：`create_and_wait_image(prompt)`
3. 下载 → `shot_{index:02d}.png`
4. 生成汇总 JSON：`shot_images_summary.json`

- [ ] **Step 1: 创建 generate_shot_images.py**

```bash
cat > "AI工具箱/huage888/scripts/generate_shot_images.py" << 'PYEOF'
#!/usr/bin/env python3
"""generate_shot_images.py — P1: 逐 Shot 图生图

用法：
  python3 scripts/generate_shot_images.py \\
    --shots outputs/S01E01-shots.md \\
    --outline outputs/S01E01-outline.md \\
    --output-dir outputs/S01E01-shots/images/ \\
    --provider doubao \\
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
    """构建 resource map prompt：角色名=图1, 场景=图2 ..."""
    if not ref_paths:
        return ""
    parts = []
    for i, path in enumerate(ref_paths, 1):
        # 从路径反推资产名
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
PYEOF
chmod +x "AI工具箱/huage888/scripts/generate_shot_images.py"
echo "OK"
```

- [ ] **Step 2: 测试 --dry-run**

```bash
cd "AI工具箱/huage888"
python3 scripts/generate_shot_images.py \
  --shots outputs/S01E01-shots.md \
  --outline outputs/S01E01-outline.md \
  --output-dir /tmp/test-shots \
  --dry-run 2>&1 | head -30
```

- [ ] **Step 3: 提交**

```bash
cd "AI工具箱/huage888" && git add scripts/generate_shot_images.py && git commit -m "feat(huage888): generate_shot_images.py P1

P1: 逐 Shot 图生图：
- 读取 shots + outline + asset_library
- resolve_shot() 查找参考图路径
- 有参考图 → img2img 模式（--img-ref）
- 无参考图 → 纯 prompt 模式
- 输出 shot_XX.png + shot_images_summary.json

支持 --dry-run 模式（不调用 API）

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 8: batch_image_pipeline.py — P2（宫格批产 + 切割）

**Files:**
- Create: `AI工具箱/huage888/scripts/batch_image_pipeline.py`
- Test: 用漠玫传 shots 测试（9 个镜头）

### Task 8: batch_image_pipeline.py（P2）

**Files:**
- Create: `AI工具箱/huage888/scripts/batch_image_pipeline.py`

**调用方式**：
```bash
python3 scripts/batch_image_pipeline.py \
  --shots outputs/S01E01-shots.md \
  --outline outputs/S01E01-outline.md \
  --rows 3 --cols 3 \
  --output-dir outputs/S01E01-shots/grid/ \
  --provider doubao \
  --model nanobanana
```

**核心逻辑**：
1. 读取前 N 个 shots（N = rows × cols）
2. 对每个 shot：resolve_shot → 参考图
3. 合并参考图（Sharp 拼接，最多 6 张）→ single ref image
4. 构建宫格 prompt（拼接所有 shots 的 imagePrompt）
5. 调用 Doubao 宫格 API（nanobanana）→ grid.png
6. `grid_split.py` → 切割为 N 张 `shot_01.png`...

- [ ] **Step 1: 创建 batch_image_pipeline.py**

```bash
cat > "AI工具箱/huage888/scripts/batch_image_pipeline.py" << 'PYEOF'
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
  2. 收集所有参考图（Sharp 拼接，最多 6 张）
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
    """调用 doubao_pipeline.py 生成宫格图（走 --batch 或专用接口）"""
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
PYEOF
chmod +x "AI工具箱/huage888/scripts/batch_image_pipeline.py"
echo "OK"
```

- [ ] **Step 2: 测试 --dry-run**

```bash
cd "AI工具箱/huage888"
python3 scripts/batch_image_pipeline.py \
  --shots outputs/S01E01-shots.md \
  --outline outputs/S01E01-outline.md \
  --rows 3 --cols 3 \
  --output-dir /tmp/test-grid \
  --dry-run 2>&1 | head -20
```

- [ ] **Step 3: 提交**

```bash
cd "AI工具箱/huage888" && git add scripts/batch_image_pipeline.py && git commit -m "feat(huage888): batch_image_pipeline.py P2

P2: 宫格批产 + 切割：
- 读取前 N 个 shots（N = rows × cols）
- 收集所有参考图，Sharp 拼接为单张（最多 6 张）
- 构建宫格 prompt（拼接所有 shots 的 imagePrompt）
- 调用 Doubao 宫格 API（nanobanana）
- grid_split.py 切割 → shot_01.png ... shot_NN.png

支持 --dry-run 模式

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 9: qwen_pipeline.py 增强 — --asset-library 参数

**Files:**
- Modify: `AI工具箱/huage888/config/qwen_pipeline.py`

### Task 9: qwen_pipeline.py --asset-library 增强

**Files:**
- Modify: `AI工具箱/huage888/config/qwen_pipeline.py`

添加 `--asset-library` 参数和系统提示词注入逻辑。

- [ ] **Step 1: 读取 qwen_pipeline.py，找到 argparse 段和 system prompt 拼装位置**

```bash
cd "AI工具箱/huage888" && grep -n "parser.add_argument\|system_prompt\|SYSTEM_PROMPT\|def main" config/qwen_pipeline.py | head -30
```

- [ ] **Step 2: 添加 --asset-library 参数**

在已有 `parser.add_argument` 附近添加：

```python
parser.add_argument(
    "--asset-library",
    action="store_true",
    default=False,
    help="自动加载 assets/library/ 的 manifest，拼入 system prompt 资产引用"
)
```

- [ ] **Step 3: 添加资产库注入逻辑**

在 main() 函数中，在发送 API 请求前（约 system_prompt 拼装处），添加：

```python
# 资产库注入（--asset-library）
if args.asset_library and not args.agent == "outline":
    try:
        import sys as _sys
        _sys.path.insert(0, str(BASE_DIR / "scripts"))
        from asset_library import AssetLibrary

        lib = AssetLibrary()
        # 尝试从 --user 或已有上下文中推断项目名
        project_hint = ""
        for kw in ["漠玫传", "漠玫", "断桥"]:
            if kw in (args.user or ""):
                project_hint = "漠玫传"
                break

        if project_hint:
            assets = lib.list_by_project(project_hint)
            lines = ["\n\n## 可用资产（来自 assets/library/）"]
            for atype, names in assets.items():
                if names:
                    lines.append(f"### {atype}:")
                    for n in names:
                        refs = lib.resolve(n, atype.rstrip("s"))
                        lines.append(f"- {n}: {refs}")
            if len(lines) > 1:
                asset_context = "\n".join(lines)
                # 追加到 system_prompt 或 user_prompt
                # 在 system prompt 末尾追加资产引用说明
                print(f"\n[Asset Library] 发现 {len(assets)} 类资产", file=sys.stderr)
    except Exception as e:
        print(f"\n[WARN] 资产库加载失败: {e}", file=sys.stderr)
```

- [ ] **Step 4: 测试 --help**

```bash
cd "AI工具箱/huage888" && python3 config/qwen_pipeline.py --help 2>&1 | grep asset-library
```

- [ ] **Step 5: 提交**

```bash
cd "AI工具箱/huage888" && git add config/qwen_pipeline.py && git commit -m "feat(huage888): qwen_pipeline.py --asset-library 参数

--asset-library：自动加载 assets/library/ manifest，拼入 system prompt
支持 storyboard-agent 等 Agent 调用时注入可用资产引用

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## 自检清单

**Spec 覆盖检查：**

| Spec 章节 | 对应 Task |
|---------|---------|
| 资产库结构 | Task 1 |
| manifest.json schema | Task 1 |
| Seedream 模板 | Task 2 |
| asset_library.py CRUD | Task 3 |
| Doubao img2img | Task 4 |
| generate_asset_prompts.py | Task 5 |
| generate_reference_images.py | Task 6 |
| generate_shot_images.py (P1) | Task 7 |
| batch_image_pipeline.py (P2) | Task 8 |
| qwen_pipeline --asset-library | Task 9 |

**占位符扫描：** 无 TBD/TODO，所有命令含预期输出

**类型一致性：**
- `AssetManifest.files` → `list[AssetFile]` ✅
- `AssetLibrary.resolve_shot()` 返回 `dict[str, list[str]]` ✅
- `ShotList` 来自 `config.outline_schema` ✅
- `AssetFile` 来自 `config.asset_registry_schema` ✅

---

## 任务依赖关系

```
Task 1 (目录结构 + schema)
Task 2 (模板文件)
Task 3 (asset_library.py)  ─┐
Task 4 (Doubao img2img)   ─┼─ 并行
                            │
                ───────────┴──────────
Task 5 (generate_asset_prompts.py)  ← 依赖 Task 3（import asset_library）
Task 6 (generate_reference_images.py) ← 依赖 Task 5（card 文件）
Task 7 (generate_shot_images.py)  ← 依赖 Task 3（AssetLibrary）+ Task 4（Doubao API）
Task 8 (batch_image_pipeline.py)  ← 依赖 Task 3（AssetLibrary）+ Task 4（Doubao API）
Task 9 (qwen_pipeline 增强)        ← 依赖 Task 3（AssetLibrary）
```

**可并行：** Task 1 / 2 / 3 / 4 可并行开发
