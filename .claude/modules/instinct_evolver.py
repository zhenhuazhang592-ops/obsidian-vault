"""本能 → Skill 自动进化引擎"""

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from .skill_manager import SkillManager


INSTINCTS_DIR = Path.home() / ".claude" / "instincts"
REGISTRY_PATH = INSTINCTS_DIR / "registry.json"


@dataclass
class Instinct:
    id: str
    name: str
    confidence: float
    domain: str
    scope: str
    trigger: str
    behavior: str
    evidence: str
    file_path: Path


class InstinctEvolver:
    def __init__(self,
                 skill_manager: Optional[SkillManager] = None,
                 instincts_dir: Path = INSTINCTS_DIR,
                 registry_path: Path = REGISTRY_PATH):
        self.skills = skill_manager or SkillManager()
        self.instincts_dir = instincts_dir
        self.registry_path = registry_path

    def load_instincts(self) -> list[Instinct]:
        """加载所有本能文件"""
        instincts = []
        if not self.instincts_dir.exists():
            return instincts

        for yaml_file in self.instincts_dir.rglob("*.yaml"):
            raw = yaml_file.read_text(encoding="utf-8")
            try:
                instinct = self._parse_instinct(yaml_file, raw)
                if instinct:
                    instincts.append(instinct)
            except Exception:
                continue

        # 也支持 .md 格式
        for md_file in self.instincts_dir.rglob("*.md"):
            if md_file.name == "registry.json":
                continue
            raw = md_file.read_text(encoding="utf-8")
            try:
                instinct = self._parse_instinct(md_file, raw)
                if instinct:
                    instincts.append(instinct)
            except Exception:
                continue

        return instincts

    def _parse_instinct(self, path: Path, raw: str) -> Optional[Instinct]:
        """解析本能文件"""
        if "---" not in raw:
            return None
        parts = raw.split("---", 2)
        if len(parts) < 3:
            return None
        meta = yaml.safe_load(parts[1]) or {}
        body = parts[2]

        # 提取 trigger（从 trigger: 行）
        trigger = ""
        for line in body.splitlines():
            if line.strip().startswith("trigger:"):
                trigger = line.split("trigger:", 1)[1].strip().strip('"').strip("'")
                break

        # 提取 behavior（简单截取 ## 行为 后的内容）
        behavior = ""
        lines = body.splitlines()
        in_behavior = False
        for line in lines:
            if "## 行为" in line:
                in_behavior = True
                continue
            if in_behavior and line.startswith("## "):
                break
            if in_behavior:
                behavior += line + "\n"

        return Instinct(
            id=meta.get("id", path.stem),
            name=meta.get("name", path.stem),
            confidence=meta.get("confidence", 0.5),
            domain=meta.get("domain", "general"),
            scope=meta.get("scope", "global"),
            trigger=trigger,
            behavior=behavior.strip(),
            evidence=body,
            file_path=path
        )

    def should_evolve(self, instinct: Instinct) -> bool:
        """判断本能是否达到进化阈值"""
        return instinct.confidence >= 0.9

    def find_evolvable_clusters(self) -> list[list[Instinct]]:
        """找出可以通过聚类进化的本能组（相同 domain，置信度 >= 0.7）"""
        instincts = self.load_instincts()
        by_domain: dict[str, list[Instinct]] = {}
        for i in instincts:
            if i.confidence >= 0.7:
                by_domain.setdefault(i.domain, []).append(i)
        return [group for group in by_domain.values() if len(group) >= 2]

    def evolve_to_skill(self, instincts: list[Instinct], skill_name: str) -> Path:
        """
        将多个本能合并为一个 Skill。
        skill_name 应为 kebab-case。
        """
        merged_behavior = []
        for i in instincts:
            merged_behavior.append(f"## From: {i.name}\n\n{i.behavior}\n")

        content = f"""# {skill_name.replace('-', ' ').title()}

> 自动进化生成 | 来源本能：{[i.name for i in instincts]}

## Overview
{[i.trigger for i in instincts][0]}

## Triggers
"""
        for i in instincts:
            content += f"- {i.trigger}\n"

        content += "\n## Behaviors\n" + "\n".join(merged_behavior)

        all_tags = set()
        for i in instincts:
            all_tags.add(i.domain)

        return self.skills.create(
            name=skill_name,
            description=f"Auto-evolved from instincts: {[i.name for i in instincts]}",
            content=content,
            version="1.0.0",
            tags=list(all_tags)
        )

    def suggest_evolution(self) -> list[str]:
        """返回建议进化的本能列表（供用户确认）"""
        instincts = self.load_instincts()
        suggestions = []

        for i in instincts:
            if self.should_evolve(i):
                suggestions.append(
                    f"CONF_0.9: {i.name} (confidence={i.confidence}) → Skill"
                )

        for cluster in self.find_evolvable_clusters():
            names = [i.name for i in cluster]
            suggestions.append(
                f"CLUSTER: {names} → Unified Skill (domain={cluster[0].domain})"
            )

        return suggestions
