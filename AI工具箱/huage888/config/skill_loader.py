#!/usr/bin/env python3
"""
skill_loader.py — 两层渐进式技能加载器

模拟 Claude Code 的 Skill 工具，从 .claude/skills/ 目录加载技能配置。

两层机制：
  Layer 1：只加载 YAML front matter（name + description），~100 tokens/skill
  Layer 2：按需加载完整 SKILL.md 内容

用法：
  from skill_loader import SkillLoader

  loader = SkillLoader(".claude/skills/")

  # Layer 1：快速列出所有技能（不加载内容）
  print(loader.build_skills_summary())

  # Layer 2：按需加载完整内容
  prompt = loader.get_skill_prompt("director")
"""

import re
from pathlib import Path
from typing import Optional


class SkillLoader:
    """两层渐进式技能加载器"""

    def __init__(self, skills_dir: str = ".claude/skills/"):
        self.skills_dir = Path(skills_dir)
        self.skills_metadata: dict = {}  # Layer 1：只存 name + description
        self.skills_full_cache: dict = {}  # Layer 2：缓存完整内容
        self._load_all_metadata()

    # ─────────────────────────────────────────────────────────────────────────
    # Layer 1：元数据加载（启动时只做这个）
    # ─────────────────────────────────────────────────────────────────────────

    def _load_all_metadata(self):
        """扫描所有技能目录，只解析 front matter 的 name + description"""
        if not self.skills_dir.exists():
            print(f"警告：技能目录不存在：{self.skills_dir}")
            return

        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            metadata = self._parse_front_matter(skill_file)
            if metadata:
                self.skills_metadata[skill_dir.name] = metadata

        print(f"已加载 {len(self.skills_metadata)} 个技能：{', '.join(self.skills_metadata.keys())}")

    def _parse_front_matter(self, skill_file: Path) -> Optional[dict]:
        """只解析 YAML front matter，提取 name 和 description"""
        try:
            content = skill_file.read_text(encoding="utf-8")
            yaml_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
            if not yaml_match:
                return None

            yaml_content = yaml_match.group(1)
            metadata = {"name": None, "description": None}

            for line in yaml_content.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    if key in metadata and value:
                        metadata[key] = value

            return metadata if metadata["name"] else None
        except Exception:
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # Layer 2：按需加载完整内容
    # ─────────────────────────────────────────────────────────────────────────

    def get_skill_prompt(self, skill_name: str) -> Optional[str]:
        """按需加载完整 SKILL.md 内容（不含 front matter）"""
        if skill_name in self.skills_full_cache:
            return self.skills_full_cache[skill_name]

        skill_file = self.skills_dir / skill_name / "SKILL.md"
        if not skill_file.exists():
            return None

        try:
            content = skill_file.read_text(encoding="utf-8")
            # 去掉 YAML front matter，只留正文
            md_match = re.match(r"^---\s*\n.*?\n---\s*\n(.*)$", content, re.DOTALL)
            body = md_match.group(1).strip() if md_match else content.strip()

            self.skills_full_cache[skill_name] = body
            return body
        except Exception:
            return None

    def get_skill_full(self, skill_name: str) -> Optional[dict]:
        """获取技能完整数据（含 metadata）"""
        metadata = self.skills_metadata.get(skill_name)
        prompt = self.get_skill_prompt(skill_name)
        if metadata and prompt:
            return {"name": metadata["name"], "description": metadata["description"], "prompt": prompt}
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # 工具方法
    # ─────────────────────────────────────────────────────────────────────────

    def list_skills(self) -> list:
        """列出所有技能名称"""
        return list(self.skills_metadata.keys())

    def get_metadata(self, skill_name: str) -> Optional[dict]:
        """获取技能元数据（Layer 1）"""
        return self.skills_metadata.get(skill_name)

    def build_system_prompt(
        self, skill_name: str, additional_context: str = ""
    ) -> str:
        """构建包含技能的系统 prompt"""
        skill = self.get_skill_full(skill_name)
        if not skill:
            raise ValueError(f"技能不存在：{skill_name}")

        parts = [f"# 技能：{skill['name']}", skill["description"] or "", skill["prompt"]]
        if additional_context:
            parts += ["", f"## 额外上下文\n{additional_context}"]
        return "\n\n".join(parts)

    def build_skills_summary(self) -> str:
        """
        构建技能摘要（Layer 1，用于系统 prompt 里的技能列表）
        格式与 rules/skill-loading.md 一致
        """
        if not self.skills_metadata:
            return ""

        lines = [
            "## 可用技能（渐进式披露）",
            "",
            "**强制执行流程**：",
            "1. 🛑 立即停止 - 发现相关任务时不要直接工作",
            "2. 📞 必须先加载完整技能内容（Layer 2）",
            "3. ⏳ 等待技能内容返回",
            "4. ✅ 基于完整指导执行任务",
            "",
            "**技能列表**：",
            "",
        ]
        for name, meta in sorted(self.skills_metadata.items()):
            desc = meta.get("description") or "无描述"
            lines.append(f"- **{name}**：{desc}")

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 演示
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader = SkillLoader(".claude/skills/")

    print("\n" + "=" * 60)
    print("Layer 1：技能摘要（~100 tokens/skill）")
    print("=" * 60)
    print(loader.build_skills_summary())

    print("\n" + "=" * 60)
    print("Layer 2：按需加载完整内容")
    print("=" * 60)

    if "director" in loader.list_skills():
        prompt = loader.get_skill_prompt("director")
        print(f"\ndirector 完整提示词：{len(prompt)} 字符")
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
