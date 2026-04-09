#!/usr/bin/env python3
"""
prompts_registry.py — 双轨 Prompt 注册表（Python 实现）

参考 Toonflow t_prompts 表 + huage888 prompts-registry.md，
提供动态的 Agent 参数加载，支持：
- 全局默认参数（default）
- 项目级覆盖参数（override）
- 命令行手动覆盖（优先级最高）

设计原则：
- 双轨机制：default（只读）→ override（项目级，可写）→ CLI override（最高）
- Python 优先（代码直接调用），Markdown 文档作为参考
- qwen_pipeline.py 集成：自动加载参数，无需手动指定

用法：

  from prompts_registry import PromptsRegistry

  registry = PromptsRegistry()

  # 1. 获取参数（default）
  params = registry.get("director")
  print(params.temperature, params.max_tokens)

  # 2. 获取参数（指定项目）
  params = registry.get("director", project_path="projects/断桥奇遇/")
  # → 自动加载 override

  # 3. 合并 CLI 参数（优先级最高）
  params = registry.get("director", overrides={"temperature": 0.8})
  # → 以 override 格式临时覆盖

  # 4. 列出所有 Agent
  agents = registry.list_agents()
  print([a.code for a in agents])
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
try:
    from task_db import TaskDB
    _HAS_TASK_DB = True
except ImportError:
    _HAS_TASK_DB = False


# ─────────────────────────────────────────────────────────────────────────────
# 数据模型
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentParams:
    """Agent 调用参数"""
    code: str
    name: str
    phase: str = ""
    priority: str = "P1"
    model: str = "qwen-max"
    temperature: float = 0.7
    top_p: float = 0.95
    max_tokens: int = 8192
    top_k: int = 50
    reasoning_depth: str = "medium"  # low / medium / high
    output_format: str = "text/markdown"
    system_prompt_file: str = ""
    skill_file: str = ""
    input_template: str = ""

    def to_dict(self) -> dict:
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "top_k": self.top_k,
            "model": self.model,
            "reasoning_depth": self.reasoning_depth,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 注册表
# ─────────────────────────────────────────────────────────────────────────────

class PromptsRegistry:
    """
    Agent 参数注册表

    三层优先级（从低到高）：
      1. default（系统默认，只读）
      2. override（项目级覆盖）
      3. overrides（CLI 参数，临时覆盖）
    """

    # 内置 Agent 默认参数（与 prompts-registry.md 同步）
    DEFAULT_AGENTS: dict[str, AgentParams] = {
        "director": AgentParams(
            code="director",
            name="导演讲戏",
            phase="阶段一",
            priority="P0",
            model="qwen-max",
            temperature=0.75,
            top_p=0.95,
            max_tokens=8192,
            top_k=50,
            reasoning_depth="medium",
            system_prompt_file="agents/director.md",
            skill_file="skills/director-skill.md",
        ),
        "art-designer": AgentParams(
            code="art-designer",
            name="角色/场景资产管理",
            phase="阶段二A",
            priority="P0",
            model="qwen-max",
            temperature=0.65,
            top_p=0.95,
            max_tokens=8192,
            top_k=50,
            reasoning_depth="medium",
            system_prompt_file="agents/art-designer.md",
            skill_file="skills/art-design-skill.md",
        ),
        "prop-designer": AgentParams(
            code="prop-designer",
            name="道具资产管理",
            phase="阶段二B",
            priority="P1",
            model="qwen-max",
            temperature=0.60,
            top_p=0.95,
            max_tokens=6144,
            top_k=50,
            reasoning_depth="medium",
            system_prompt_file="agents/prop-designer.md",
            skill_file="skills/prop-design-skill.md",
        ),
        "storyboard-artist": AgentParams(
            code="storyboard-artist",
            name="分镜脚本撰写",
            phase="阶段三",
            priority="P0",
            model="qwen-max",
            temperature=0.55,
            top_p=0.95,
            max_tokens=8192,
            top_k=50,
            reasoning_depth="medium",
            system_prompt_file="agents/storyboard-artist.md",
            skill_file="skills/storyboard-skill.md",
        ),
        "script-review": AgentParams(
            code="script-review",
            name="剧本/讲戏本审核",
            phase="阶段一末尾",
            priority="P1",
            model="qwen-max",
            temperature=0.40,
            top_p=0.90,
            max_tokens=2048,
            top_k=50,
            reasoning_depth="high",
            system_prompt_file="agents/script-review.md",
            skill_file="skills/compliance-skill.md",
        ),
        "art-review": AgentParams(
            code="art-review",
            name="资产审核",
            phase="阶段二末尾",
            priority="P1",
            model="qwen-max",
            temperature=0.40,
            top_p=0.90,
            max_tokens=2048,
            top_k=50,
            reasoning_depth="high",
            system_prompt_file="agents/art-review.md",
            skill_file="skills/compliance-skill.md",
        ),
        "storyboard-review": AgentParams(
            code="storyboard-review",
            name="分镜脚本审核",
            phase="阶段三末尾",
            priority="P1",
            model="qwen-max",
            temperature=0.40,
            top_p=0.90,
            max_tokens=2048,
            top_k=50,
            reasoning_depth="high",
            system_prompt_file="agents/storyboard-review.md",
            skill_file="skills/compliance-skill.md",
        ),
    }

    def __init__(self, base_dir: str | Path | None = None, db: 'TaskDB | None' = None):
        """
        Args:
            base_dir: huage888 根目录（用于定位项目 override）
            db: TaskDB 实例（传入则复用，否则自动初始化）
        """
        self.base_dir = Path(base_dir) if base_dir else self._detect_base_dir()
        self._db: 'TaskDB | None' = None
        if db is not None:
            self._db = db
        elif _HAS_TASK_DB:
            try:
                self._db = TaskDB()
                self._db.seed_default_prompts()   # 确保表已初始化
            except Exception:
                pass   # DB 不可用时降级到纯内存模式

    def _detect_base_dir(self) -> Path:
        """自动检测 huage888 根目录"""
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / "CLAUDE.md").exists() and (parent / "config").exists():
                return parent
        return current

    # ─────────────────────────────────────────────────────────────────
    # 核心 API
    # ─────────────────────────────────────────────────────────────────

    def get(
        self,
        agent_code: str,
        project_path: str | Path | None = None,
        overrides: dict | None = None,
    ) -> AgentParams:
        """
        获取 Agent 参数

        Args:
            agent_code: Agent 代码（如 "director"）
            project_path: 项目目录（用于加载 override）
            overrides: CLI 参数覆盖（优先级最高）

        Returns:
            AgentParams

        Raises:
            KeyError: Agent 不存在
        """
        if agent_code not in self.DEFAULT_AGENTS:
            raise KeyError(f"未知 Agent：{agent_code}，可用：{list(self.DEFAULT_AGENTS.keys())}")

        # Layer 1: DB 层（custom_value 覆盖 DEFAULT_AGENTS）
        #    优先级：DB custom_value > DEFAULT_AGENTS
        params = self._deep_copy(self.DEFAULT_AGENTS[agent_code])
        if self._db is not None:
            try:
                db_row = self._db.get_prompt(agent_code)
                if db_row and db_row.get("custom_value"):
                    db_params = json.loads(db_row["custom_value"])
                    for key, val in db_params.items():
                        if hasattr(params, key):
                            setattr(params, key, val)
            except Exception:
                pass   # DB 查询失败，降级到纯内存

        # Layer 2: 项目级 JSON override
        if project_path:
            override = self._load_override(Path(project_path), agent_code)
            if override:
                self._apply_override(params, override)

        # Layer 3: CLI 参数覆盖（优先级最高）
        if overrides:
            self._apply_override(params, overrides)

        return params

    def list_agents(self, phase: str | None = None) -> list[AgentParams]:
        """
        列出所有 Agent

        Args:
            phase: 过滤阶段（如 "阶段一"）

        Returns:
            Agent 列表
        """
        agents = list(self.DEFAULT_AGENTS.values())
        if phase:
            agents = [a for a in agents if a.phase == phase]
        return agents

    def has_override(self, project_path: str | Path, agent_code: str) -> bool:
        """检查是否存在项目 override"""
        return self._load_override(Path(project_path), agent_code) is not None

    def write_override(
        self,
        project_path: str | Path,
        agent_code: str,
        params: dict,
    ) -> None:
        """
        写入项目 override（自动创建目录和文件）

        Args:
            project_path: 项目目录
            agent_code: Agent 代码
            params: 被覆盖的参数（如 {"temperature": 0.80}）
        """
        project_path = Path(project_path)
        override_dir = project_path / "config"
        override_dir.mkdir(parents=True, exist_ok=True)

        override_file = override_dir / f"prompts_override_{agent_code}.json"

        # 追加到现有 override
        existing = {}
        if override_file.exists():
            existing = json.loads(override_file.read_text(encoding="utf-8"))
        existing.update(params)

        override_file.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_effective_params(
        self,
        agent_code: str,
        project_path: str | Path | None = None,
    ) -> dict:
        """
        获取最终生效参数（用于 qwen_pipeline.py 调用）

        Returns:
            仅含 qwen API 调用所需字段的 dict
        """
        params = self.get(agent_code, project_path)
        return params.to_dict()

    # ─────────────────────────────────────────────────────────────────
    # 内部工具
    # ─────────────────────────────────────────────────────────────────

    def _load_override(self, project_path: Path, agent_code: str) -> dict | None:
        """从项目目录加载 override 参数"""
        override_file = project_path / "config" / f"prompts_override_{agent_code}.json"
        if not override_file.exists():
            return None
        try:
            return json.loads(override_file.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _apply_override(self, params: AgentParams, override: dict) -> None:
        """将 override 字典应用到 AgentParams"""
        for key, value in override.items():
            if hasattr(params, key):
                current_type = type(getattr(params, key))
                try:
                    setattr(params, key, current_type(value))
                except (ValueError, TypeError):
                    pass

    def _deep_copy(self, params: AgentParams) -> AgentParams:
        """深拷贝 AgentParams"""
        return AgentParams(
            code=params.code,
            name=params.name,
            phase=params.phase,
            priority=params.priority,
            model=params.model,
            temperature=params.temperature,
            top_p=params.top_p,
            max_tokens=params.max_tokens,
            top_k=params.top_k,
            reasoning_depth=params.reasoning_depth,
            output_format=params.output_format,
            system_prompt_file=params.system_prompt_file,
            skill_file=params.skill_file,
            input_template=params.input_template,
        )


# ─────────────────────────────────────────────────────────────────────────────
# CLI（集成到 qwen_pipeline.py）
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    """命令行调试入口"""
    import argparse
    parser = argparse.ArgumentParser(description="huage888 Prompt 注册表")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", help="列出所有 Agent")
    p_list.add_argument("--phase", help="过滤阶段")

    p_get = sub.add_parser("get", help="查看 Agent 参数")
    p_get.add_argument("agent", help="Agent 代码")
    p_get.add_argument("--project", help="项目路径")

    p_override = sub.add_parser("override", help="写入项目 override")
    p_override.add_argument("agent", help="Agent 代码")
    p_override.add_argument("--params", required=True, help="JSON 参数")
    p_override.add_argument("--project", required=True, help="项目路径")

    args = parser.parse_args()
    registry = PromptsRegistry()

    if args.cmd == "list":
        for agent in registry.list_agents(phase=args.phase):
            print(f"[{agent.priority}] {agent.code:<20} {agent.name:<15} temp={agent.temperature} phase={agent.phase}")

    elif args.cmd == "get":
        p = registry.get(args.agent, project_path=args.project)
        import json
        print(json.dumps(p.to_dict(), ensure_ascii=False, indent=2))

    elif args.cmd == "override":
        import json
        params = json.loads(args.params)
        registry.write_override(args.project, args.agent, params)
        print(f"✅ override 已写入：{args.project}/config/prompts_override_{args.agent}.json")


if __name__ == "__main__":
    _cli()
