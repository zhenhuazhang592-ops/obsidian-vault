# AI 漫剧智能创作系统 · 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个规范驱动的 AI 漫剧创作系统，用户输入小说原文，系统输出完整 5 步文档包（S0-S5），每步引用上游输出，全链路零自由发挥。

**Architecture:** 单 Agent 状态机（S0-S5），每步输出 Schema 化文档，上下游通过 ID 引用链式传递。复用 manzhou-agent 的状态机框架，扩展 S0-S1 解析与风格锚定，新增链式引用追踪器和断点恢复模块。

**Tech Stack:** Python + Claude Code Agent CLI + Markdown 文件系统

---

## 实施策略

- 复用 `manzhou-agent/` 现有代码（state_machine / schema / quality_gate）
- 新增模块全部新建独立文件，不污染已有代码
- 每完成一个模块，同步更新 MEMORY.md 任务状态
- 先建基础设施（Schema + 引用追踪），再逐层构建 S0-S5

---

## 前置检查：现有代码结构

**Files:**
- Modify: `AI漫剧项目/skills/manzhou-agent/manzhou/schema.py`
- Modify: `AI漫剧项目/skills/manzhou-agent/manzhou/state_machine.py`
- Create: `AI漫剧项目/skills/manzhou-agent/manzhou/chain_ref.py`
- Create: `AI漫剧项目/skills/manzhou-agent/manzhou/recovery.py`
- Create: `AI漫剧项目/skills/manzhou-agent/manzhou/style_guide.py`

**Step 1: 查看现有 manzhou-agent 目录结构**

Run: `ls -la "AI漫剧项目/skills/manzhou-agent/manzhou/"`

**Step 2: 查看 state_machine.py 现有状态定义**

Read: `AI漫剧项目/skills/manzhou-agent/manzhou/state_machine.py`

**Step 3: 查看 schema.py 现有 Schema 定义**

Read: `AI漫剧项目/skills/manzhou-agent/manzhou/schema.py`

---

## 第一阶段：Schema 扩展（基础设施）

### Task 1: 扩展 CDP Schema — 角色/场景/道具 DNA 字段

**Files:**
- Modify: `AI漫剧项目/skills/manzhou-agent/manzhou/schema.py`

**Step 1: 添加角色 DNA Schema**

在 `schema.py` 中追加：

```python
# ─── S2: CDP 角色 DNA ───────────────────────────────────────
CHARACTER_DNA_SCHEMA = {
    "id": {"type": "string", "pattern": "^char_[a-z_]+$", "required": True},
    "name": {"type": "string", "required": True},
    "gender": {"type": "enum", "values": ["male", "female", "unknown"], "required": True},
    "age_range": {"type": "string", "required": True, "example": "20-80"},
    "visual": {
        "type": "object",
        "required": True,
        "fields": {
            "face_shape": {"type": "string", "required": True},
            "skin_tone": {"type": "string", "required": True},
            "eye_features": {"type": "string", "required": True},
            "body_type": {"type": "string", "required": True},
            "clothing": {
                "type": "object",
                "required": True,
                "fields": {
                    "young": {"type": "string", "required": True},
                    "middle": {"type": "string", "required": True},
                    "old": {"type": "string", "required": True},
                }
            },
            "palette": {"type": "string", "required": True},  # 引用S1色调
        }
    },
    "expression_normal": {"type": "string", "required": True},
    "expression_strong": {"type": "string", "required": True},
    "constraints": {
        "type": "list",
        "required": True,
        "min_items": 1,
        "item_type": "string",
        "example": ["禁止: 年轻时不能画皱纹", "禁止: 不能画现代发型"]
    },
    "reference_prompt": {"type": "string", "required": True},
    "used_in_scenes": {"type": "list", "item_type": "string", "required": True},
}
```

**Step 2: 添加场景 DNA Schema**

```python
# ─── S2: CDP 场景 DNA ───────────────────────────────────────
SCENE_DNA_SCHEMA = {
    "id": {"type": "string", "pattern": "^scene_[a-z_]+$", "required": True},
    "name": {"type": "string", "required": True},
    "era": {"type": "string", "required": True},  # 必须匹配S0
    "description": {"type": "string", "required": True},
    "visual": {
        "type": "object",
        "required": True,
        "fields": {
            "space_type": {"type": "enum", "values": ["indoor", "outdoor", "semi_indoor"], "required": True},
            "architecture": {"type": "string", "required": True},
            "lighting": {"type": "string", "required": True},
            "color_temperature": {"type": "enum", "values": ["warm", "cool", "neutral"], "required": True},
            "key_props": {"type": "list", "item_type": "string", "required": True},
        }
    },
    "constraints": {
        "type": "list",
        "required": True,
        "min_items": 1,
        "item_type": "string",
    },
    "reference_prompt": {"type": "string", "required": True},
}
```

**Step 3: 添加道具 DNA Schema**

```python
# ─── S2: CDP 道具 DNA ───────────────────────────────────────
ITEM_DNA_SCHEMA = {
    "id": {"type": "string", "pattern": "^item_[a-z_]+$", "required": True},
    "name": {"type": "string", "required": True},
    "era": {"type": "string", "required": True},
    "description": {"type": "string", "required": True},
    "visual": {
        "type": "object",
        "required": True,
        "fields": {
            "material": {"type": "string", "required": True},
            "color": {"type": "string", "required": True},
            "size": {"type": "string", "required": True},
        }
    },
    "constraints": {"type": "list", "item_type": "string", "required": True},
    "reference_prompt": {"type": "string", "required": True},
}
```

**Step 4: 添加 S1 风格指南 Schema**

```python
# ─── S1: 风格指南 ───────────────────────────────────────────
STYLE_GUIDE_SCHEMA = {
    "version": {"type": "string", "required": True, "example": "v1.0.0"},
    "style": {"type": "string", "required": True},  # 如: 写实/动漫/水墨
    "aspect_ratio": {"type": "string", "required": True, "example": "9:16"},
    "shot_duration_sec": {"type": "integer", "required": True, "example": 15},
    "color_palette": {
        "type": "object",
        "required": True,
        "fields": {
            "dominant": {"type": "string", "required": True},  # 主色调
            "secondary": {"type": "string", "required": True},  # 辅助色
            "accent": {"type": "string", "required": True},    # 点缀色
            "prohibition": {"type": "list", "item_type": "string", "required": True},  # 禁用色
        }
    },
    "lighting_rules": {
        "type": "object",
        "required": True,
        "fields": {
            "type": {"type": "enum", "values": ["natural", "hard", "soft", "mixed"], "required": True},
            "time_of_day": {"type": "string", "required": True},  # 如: 自然光/黄昏/夜晚
            "prohibition": {"type": "list", "item_type": "string", "required": True},
        }
    },
    "camera_rules": {
        "type": "object",
        "required": True,
        "fields": {
            "standard_lens": {"type": "string", "required": True},  # 标准镜头
            "movement_patterns": {"type": "list", "item_type": "string", "required": True},
            "prohibition": {"type": "list", "item_type": "string", "required": True},
        }
    },
    "sound_rules": {
        "type": "object",
        "required": True,
        "fields": {
            "bgm_style": {"type": "string", "required": True},  # 背景乐风格
            "sfx_types": {"type": "list", "item_type": "string", "required": True},
            "prohibition": {"type": "list", "item_type": "string", "required": True},
        }
    },
    "character_design_rules": {
        "type": "object",
        "required": True,
        "fields": {
            "proportions": {"type": "string", "required": True},
            "prohibition": {"type": "list", "item_type": "string", "required": True},
        }
    },
    "era_constraints": {
        "type": "object",
        "required": True,
        "fields": {
            "allowed_eras": {"type": "list", "item_type": "string", "required": True},
            "prohibition": {"type": "list", "item_type": "string", "required": True},
        }
    },
}
```

**Step 5: 导出汇总函数**

```python
def validate_all_schemas():
    """验证所有 Schema 定义完整性"""
    schemas = {
        "character_dna": CHARACTER_DNA_SCHEMA,
        "scene_dna": SCENE_DNA_SCHEMA,
        "item_dna": ITEM_DNA_SCHEMA,
        "style_guide": STYLE_GUIDE_SCHEMA,
    }
    # 验证每个 schema 的 required 字段不为空
    for name, schema in schemas.items():
        for field, spec in schema.get("fields", {}).items():
            if spec.get("required") and spec.get("example") is None:
                raise ValueError(f"{name}.{field} required but no example provided")
    return schemas
```

---

### Task 2: 链式引用追踪器（chain_ref.py）

**Files:**
- Create: `AI漫剧项目/skills/manzhou-agent/manzhou/chain_ref.py`

**Step 1: 定义引用追踪类**

```python
"""
链式引用追踪器
确保每步输出正确引用上游 ID，规范链式数据流。
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StepRef:
    step: str          # S0/S1/S2/S3/S4/S5
    file: str          # 输出文件路径
    anchors: dict      # 关键 ID 映射 {角色ID: 角色名, 场景ID: 场景名, ...}


@dataclass
class ChainRef:
    """引用追踪器"""
    project_path: str
    refs: dict = field(default_factory=dict)  # {step: StepRef}

    def register(self, step: str, anchors: dict, file: str):
        """注册某步的输出锚点"""
        self.refs[step] = StepRef(step=step, file=file, anchors=anchors)

    def get_ref(self, step: str) -> Optional[StepRef]:
        return self.refs.get(step)

    def check_shot_refs(self, shot_entry: dict) -> tuple[bool, list]:
        """
        检查某镜脚本是否正确引用了上游 ID
        返回: (is_valid, violation_list)
        """
        violations = []
        required_refs = {
            "location_id": "S2",
            "character_ids": "S2",
            "item_ids": "S2",
        }
        for field, upstream_step in required_refs.items():
            if upstream_step in self.refs:
                upstream_anchors = self.refs[upstream_step].anchors
                value = shot_entry.get(field)
                if value:
                    # 检查 value 是否在 upstream_anchors 中
                    if isinstance(value, list):
                        for v in value:
                            if v not in upstream_anchors:
                                violations.append(f"{field}: {v} not in {upstream_step} anchors")
                    elif value not in upstream_anchors:
                        violations.append(f"{field}: {value} not in {upstream_step} anchors")
        return (len(violations) == 0, violations)

    def save(self, path: str):
        """保存到 JSON 文件"""
        import json
        data = {
            step: {"file": r.file, "anchors": r.anchors}
            for step, r in self.refs.items()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "ChainRef":
        """从 JSON 文件恢复"""
        import json
        import os
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ref = cls(project_path=os.path.dirname(path))
        for step, rdata in data.items():
            ref.refs[step] = StepRef(
                step=step,
                file=rdata["file"],
                anchors=rdata["anchors"]
            )
        return ref
```

---

## 第二阶段：断点恢复（recovery.py）

### Task 3: 断点恢复模块

**Files:**
- Create: `AI漫剧项目/skills/manzhou-agent/manzhou/recovery.py`

**Step 1: 定义状态机状态枚举**

```python
"""
断点恢复模块
管理 Agent 状态持久化，支持从断点恢复。
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import json
import os


class AgentState(Enum):
    INIT = "init"
    S0_PARSING = "s0_parsing"
    S0_DONE = "s0_done"
    S1_SETTINGS = "s1_settings"
    S1_DONE = "s1_done"
    S2_CDP = "s2_cdp"
    S2_DONE = "s2_done"
    S3_ASSETS = "s3_assets"
    S3_DONE = "s3_done"
    S4_SHOTS = "s4_shots"
    S4_DONE = "s4_done"
    S5_VIDEO = "s5_video"
    S5_DONE = "s5_done"
    COMPLETED = "completed"


@dataclass
class Checkpoint:
    state: AgentState
    project_name: str
    current_step: str
    completed_steps: list = field(default_factory=list)
    checkpoint_data: dict = field(default_factory=dict)
    error: Optional[str] = None

    def to_json(self) -> dict:
        return {
            "state": self.state.value,
            "project_name": self.project_name,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "checkpoint_data": self.checkpoint_data,
            "error": self.error,
        }

    @classmethod
    def from_json(cls, data: dict) -> "Checkpoint":
        return cls(
            state=AgentState(data["state"]),
            project_name=data["project_name"],
            current_step=data["current_step"],
            completed_steps=data.get("completed_steps", []),
            checkpoint_data=data.get("checkpoint_data", {}),
            error=data.get("error"),
        )


class RecoveryManager:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.checkpoint_dir = os.path.join(project_path, ".manzhou")
        self.state_file = os.path.join(self.checkpoint_dir, "state.json")
        self.chain_ref_file = os.path.join(self.checkpoint_dir, "chain_ref.json")

    def save_checkpoint(self, checkpoint: Checkpoint):
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint.to_json(), f, ensure_ascii=False, indent=2)

    def load_checkpoint(self) -> Optional[Checkpoint]:
        if not os.path.exists(self.state_file):
            return None
        with open(self.state_file, "r", encoding="utf-8") as f:
            return Checkpoint.from_json(json.load(f))

    def get_recovery_point(self) -> Optional[str]:
        """返回应该从哪个步骤恢复"""
        cp = self.load_checkpoint()
        if cp is None:
            return None
        if cp.state in [AgentState.S0_DONE, AgentState.S1_SETTINGS]:
            return "S1"
        elif cp.state in [AgentState.S1_DONE, AgentState.S2_CDP]:
            return "S2"
        elif cp.state in [AgentState.S2_DONE, AgentState.S3_ASSETS]:
            return "S3"
        elif cp.state in [AgentState.S3_DONE, AgentState.S4_SHOTS]:
            return "S4"
        elif cp.state in [AgentState.S4_DONE, AgentState.S5_VIDEO]:
            return "S5"
        elif cp.state == AgentState.S5_DONE:
            return "COMPLETED"
        return None
```

---

## 第三阶段：状态机扩展（state_machine.py）

### Task 4: 扩展状态机到 S0-S5

**Files:**
- Modify: `AI漫剧项目/skills/manzhou-agent/manzhou/state_machine.py`

**Step 1: 读取现有状态机**

Read: `AI漫剧项目/skills/manzhou-agent/manzhou/state_machine.py`

**Step 2: 替换状态枚举和状态机逻辑**

将现有的 `State` 枚举和 `DramStateMachine` 类替换为新的 S0-S5 版本：

```python
from enum import Enum
from typing import Optional
from dataclasses import dataclass
from .chain_ref import ChainRef
from .recovery import AgentState, Checkpoint, RecoveryManager
from .schema import STYLE_GUIDE_SCHEMA, CHARACTER_DNA_SCHEMA, SCENE_DNA_SCHEMA, ITEM_DNA_SCHEMA


class DramStateMachine:
    """
    漫剧创作状态机 (S0-S5)

    S0: 解析小说 → 输出解析报告
    S1: 全局设置 → 输出风格指南 (规范锚点)
    S2: CDP资产包 → 输出角色/场景/道具DNA
    S3: 资产库 → 输出图像生成提示词
    S4: 分镜脚本 → 输出每镜脚本+运镜规范
    S5: 视频生成 → 输出Kling+Seedance双版本提示词
    """

    STATES = [
        "init", "s0_parsing", "s0_done",
        "s1_settings", "s1_done",
        "s2_cdp", "s2_done",
        "s3_assets", "s3_done",
        "s4_shots", "s4_done",
        "s5_video", "s5_done",
        "completed"
    ]

    def __init__(self, project_path: str, project_name: str):
        self.project_path = project_path
        self.project_name = project_name
        self.recovery = RecoveryManager(project_path)
        self.chain_ref = ChainRef(project_path=project_path)
        self.state = "init"
        self._load_or_init()

    def _load_or_init(self):
        cp = self.recovery.load_checkpoint()
        if cp:
            self.state = cp.state.value
            # 恢复 chain_ref
            loaded_ref = ChainRef.load(self.recovery.chain_ref_file)
            if loaded_ref:
                self.chain_ref = loaded_ref

    def advance(self, step_output: dict) -> str:
        """推进状态机，step_output 包含当前步骤的输出摘要"""
        transitions = {
            "init": ("s0_parsing", "s0_done"),
            "s0_parsing": ("s0_done", "s1_settings"),
            "s0_done": ("s1_settings", "s1_done"),
            "s1_settings": ("s1_done", "s2_cdp"),
            "s1_done": ("s2_cdp", "s2_done"),
            "s2_cdp": ("s2_done", "s3_assets"),
            "s2_done": ("s3_assets", "s3_done"),
            "s3_assets": ("s3_done", "s4_shots"),
            "s3_done": ("s4_shots", "s4_done"),
            "s4_shots": ("s4_done", "s5_video"),
            "s5_video": ("s5_done", "completed"),
        }

        current = self.state
        if current in transitions:
            next_state = transitions[current][1]
            self.state = next_state
            self._save_state(step_output)
            return next_state
        return current

    def _save_state(self, step_output: dict):
        """保存状态和链式引用"""
        completed = self._get_completed_steps()
        cp = Checkpoint(
            state=AgentState(self.state),
            project_name=self.project_name,
            current_step=self.state,
            completed_steps=completed,
            checkpoint_data=step_output,
        )
        self.recovery.save_checkpoint(cp)
        self.chain_ref.save(self.recovery.chain_ref_file)

    def _get_completed_steps(self) -> list:
        done_states = ["s0_done", "s1_done", "s2_done", "s3_done", "s4_done", "s5_done", "completed"]
        return [s for s in self.STATES if s <= self.state and s in done_states]

    def get_next_action(self) -> str:
        """返回下一个应执行的动作"""
        action_map = {
            "init": "S0_PARSE_NOVEL",
            "s0_done": "S1_GLOBAL_SETTINGS",
            "s1_done": "S2_BUILD_CDP",
            "s2_done": "S3_GENERATE_ASSETS",
            "s3_done": "S4_WRITE_SHOT_SCRIPTS",
            "s4_done": "S5_GENERATE_VIDEO_PROMPTS",
            "completed": "ALL_DONE",
        }
        return action_map.get(self.state, "UNKNOWN")

    def can_proceed(self) -> bool:
        """检查是否可以继续"""
        return self.state != "completed"

    def status(self) -> dict:
        return {
            "state": self.state,
            "next_action": self.get_next_action(),
            "can_proceed": self.can_proceed(),
            "chain_ref_steps": list(self.chain_ref.refs.keys()),
        }
```

---

## 第四阶段：Prompt 模板（S0-S5 各步骤）

### Task 5: 创建 S0-S5 Prompt 模板

**Files:**
- Create: `AI漫剧项目/skills/manzhou-agent/manzhou/prompts/s0_parse_novel.md`
- Create: `AI漫剧项目/skills/manzhou-agent/manzhou/prompts/s1_global_settings.md`
- Create: `AI漫剧项目/skills/manzhou-agent/manzhou/prompts/s2_build_cdp.md`
- Create: `AI漫剧项目/skills/manzhou-agent/manzhou/prompts/s3_generate_assets.md`
- Create: `AI漫剧项目/skills/manzhou-agent/manzhou/prompts/s4_write_shot_scripts.md`
- Create: `AI漫剧项目/skills/manzhou-agent/manzhou/prompts/s5_video_prompts.md`
- Create: `AI漫剧项目/skills/manzhou-agent/manzhou/prompts/_template_header.md`

**Step 1: 创建通用模板头部（所有 Prompt 必须引用）**

```markdown
# Prompt 模板头部（所有步骤必须引用）

## 链式引用规范

每步 Prompt 输出时，必须在文档头部声明引用来源：

```yaml
引用声明:
  上游步骤: [文件路径]
  引用ID列表: [char_xxx, scene_xxx, item_xxx]
  风格指南版本: [v1.0.0]
```

## Schema 约束

- 所有字段必须填写，不能留空
- 不能写"待定"/"参考实际情况"/"由用户决定"
- 遇到不确定内容，返回上一步要求补充

## 输出格式

- 主要内容: Markdown
- 数据结构: YAML in Markdown code block
- 提示词内容: 中文描述，平台无关时用英文
```

**Step 2: 创建 S0 解析小说 Prompt**

```markdown
# S0: 解析小说

## 任务

输入用户提供的小说原文，提取创作所需的基础信息。

## 输入

用户粘贴的小说文本（xxx字），或 Obsidian 笔记路径。

## 输出文件

`S0-解析报告.md`

## 输出内容

```yaml
时代背景:
  period: [具体年代，如1940年代中国农村]
  location: [地理区域]
  social_environment: [社会环境描述]
  material_culture: [物质文化特征]

故事基调:
  tone: [悲情/温暖/悬疑/热血等]
  emotional_arc: [情感走向描述]
  target_audience: [目标受众]

章节结构:
  - chapter: 第X章
    title: 章节名
    core_event: 核心事件（一句话）
    characters_involved: [主要角色列表]
    key_scenes: [关键场景列表]

主要角色（不超过10个）:
  - id: char_xxx
    name: 角色名
    one_line: 一句话描述
    first_appearance: 第X章

关键场景（不超过10个）:
  - id: scene_xxx
    name: 场景名
    one_line: 一句话描述
    era_consistency: [年代一致性说明]

故事主线:
  one_sentence: [一句话概括核心冲突]
  theme: [核心主题]
```

## 约束

- 时代背景必须从原文提取，不能推断
- 角色不超过10个，选取戏份最多的
- 场景不超过10个，选取有画面表现的
- 章节结构只列核心事件，不展开细节
```

**Step 3: 创建 S1 全局设置 Prompt**

```markdown
# S1: 全局设置（规范锚点）

## 任务

基于 S0 解析报告，生成全局风格指南。这是全链路的规范锚点，后续所有步骤必须引用。

## 输入

S0-解析报告.md

## 输出文件

`00-全局设置.md`
`S1-风格指南.md`

## 输出内容：全局设置

```yaml
项目名: [从小说名提取]
原作: [小说名]
作者: [作者名]

全局配置:
  style: [写实/动漫/水墨/漫画风]
  aspect_ratio: "9:16"
  shot_duration_sec: 15
  total_eps: [集数]
  total_shots: [估算总镜头数]

统计:
  characters: [角色数量]
  scenes: [场景数量]
  episodes: [集数]
```

## 输出内容：风格指南（必须完整）

```yaml
style_guide:
  version: "v1.0.0"  # 固定格式，后续引用此版本

  color_palette:
    dominant: [主色调描述，如"暖黄色，如1930年代老照片"]
    secondary: [辅助色描述]
    accent: [点缀色描述]
    prohibition: [禁用色列表]

  lighting_rules:
    type: [natural/hard/soft/mixed]
    time_of_day: [如"自然光为主，室内用暖色灯光"]
    prohibition:
      - [如"禁止霓虹灯效果"]
      - [如"禁止现代补光设备"]

  camera_rules:
    standard_lens: [标准镜头，如"中景镜头为主"]
    movement_patterns:
      - [如"横移用于场景转换"]
      - [如"推镜头用于强调"]
    prohibition:
      - [如"禁止快速摇镜"]
      - [如"禁止航拍俯冲"]

  sound_rules:
    bgm_style: [如"忧伤的小提琴配乐，节奏缓慢"]
    sfx_types: [音效类型列表]
    prohibition:
      - [如"禁止电子音乐"]

  character_design_rules:
    proportions: [如"写实比例，接近真人"]
    prohibition:
      - [如"禁止日漫大眼"]
      - [如"禁止网红脸"]

  era_constraints:
    allowed_eras: [[1940s, 1960s]]
    prohibition:
      - [如"禁止出现塑料制品"]
      - [如"禁止水泥地面"]
      - [如"禁止钢筋混凝土建筑"]
```

## 约束

- 这是规范锚点，后续所有步骤必须引用 `style_guide.version`
- 所有规则必须具体，不能写"视情况而定"
- prohibition 列表至少3条，针对具体禁止项
```

（其余 S2-S5 Prompt 模板结构相同，逐步创建）
```

**Step 4: 创建 S2 CDP 资产包 Prompt**

```markdown
# S2: CDP 资产包（硬约束层）

## 任务

基于 S1 风格指南 + S0 解析报告，构建角色/场景/道具 DNA。

## 输入

- S0-解析报告.md
- S1-风格指南.md

## 输出文件

`01-CDP资产包/CDP-JSON.md`

## 输出内容：角色 DNA（每个角色一条）

每个角色按 schema.py 的 CHARACTER_DNA_SCHEMA 填写，示例：

```yaml
char_fugui:
  id: char_fugui
  name: 福贵
  gender: male
  age_range: "20-80"
  visual:
    face_shape: "长脸，颧骨略高，年轻时皮肤白皙，晚年黝黑粗糙 [引用S1]"
    skin_tone: "年轻时白皙微黄，中年黝黑，晚年古铜色 [引用S1色调]"
    eye_features: "眼睛有神，年轻时明亮，晚年温和 [引用S1]"
    body_type: "年轻时修长挺拔，中年弯腰驼背，晚年瘦削 [引用S1]"
    clothing:
      young: "绸衣绸裤，民国公子打扮 [引用S1-era]"
      middle: "粗布短褂，农民打扮 [引用S1-era]"
      old: "破旧棉袄，补丁衣服 [引用S1-era]"
    palette: "棕色系为主，蓝色为辅 [引用S1]"
  expression_normal: "平静温和，偶尔苦笑 [引用S1]"
  expression_strong: "悲痛时沉默，愤怒时握拳不语 [引用S1]"
  constraints:
    - "禁止画年轻时有皱纹 [S1禁止规则]"
    - "禁止画民国后的发型和服装 [S1-era]"
    - "禁止画现代眼镜 [S1-era]"
  reference_prompt: |
    [生成角色参考图的完整提示词，必须包含:]
    - S1 风格规范: [引用颜色/光线/构图规则]
    - 角色DNA visual字段全部内容
    - 角色专属色板
    - 禁止项遵守声明
    格式: "写实风格，1940年代中国农村，[角色描述]，[服装]，[光线]，[禁止项]"
  used_in_scenes: [scene_maowu, scene_tianjian, scene_chengli]
```

## 约束

- 每条角色记录必须引用 S1 风格指南的版本号
- constraints 禁止项至少2条
- reference_prompt 必须包含 S1 规范和 S2 DNA 字段
- used_in_scenes 引用场景 DNA ID
```

**Step 5: 创建 S3 资产库 Prompt**

**Step 6: 创建 S4 分镜脚本 Prompt**

**Step 7: 创建 S5 视频生成 Prompt**

（后续逐步完成，每个 Prompt 结构遵循统一规范：输入→输出文件→输出内容示例→约束）

---

## 第五阶段：CLI 入口（cli.py 扩展）

### Task 6: 扩展 CLI 支持 S0-S5 流程

**Files:**
- Modify: `AI漫剧项目/skills/manzhou-agent/manzhou/cli.py`

**Step 1: 添加新命令**

在 `run` 命令中新增状态判断：

```python
def run(args):
    project_path = Path(args.project)
    project_name = project_path.name

    sm = DramStateMachine(project_path=str(project_path), project_name=project_name)

    # 检查断点恢复
    recovery_point = sm.recovery.get_recovery_point()
    if recovery_point:
        print(f"[恢复] 从 {recovery_point} 继续...")
        print(f"[状态] {sm.status()}")

    # 根据当前状态执行下一步
    action = sm.get_next_action()
    if action == "S0_PARSE_NOVEL":
        # 读取 S0 Prompt 模板
        prompt = load_prompt_template("s0_parse_novel.md")
        # TODO: 注入用户小说文本
        output = execute_prompt(prompt, user_input=args.input)
        write_output(project_path, "S0-解析报告.md", output)
        sm.advance({"step": "S0", "anchors": extract_anchors(output)})
```

---

## 实施顺序

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | Task 1: Schema 扩展 | 所有后续的基础 |
| P0 | Task 2: 链式引用追踪器 | 保障数据链完整 |
| P0 | Task 3: 断点恢复模块 | 开发期快速迭代 |
| P1 | Task 4: 状态机扩展 | S0-S5 状态流转 |
| P1 | Task 5: Prompt 模板 | S0-S5 各步骤指令 |
| P2 | Task 6: CLI 扩展 | 命令行入口 |

---

## 成功验证

每个模块完成后：
1. 运行 `python -m manzhou.schema` 验证 Schema 定义
2. 运行 `python -m manzhou.recovery` 验证恢复逻辑
3. 运行 `python -m manzhou.chain_ref` 验证引用追踪
4. 用 `活着-v9` 的已有分镜数据做端到端测试
