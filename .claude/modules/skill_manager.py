"""Skill 管理：CRUD 操作"""

import re
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


SKILLS_DIR = Path.home() / ".claude" / "skills"


@dataclass
class Skill:
    name: str
    description: str
    version: str
    author: str
    metadata: dict
    content: str
    file_path: Path


class SkillManager:
    def __init__(self, skills_dir: Path = SKILLS_DIR):
        self.skills_dir = skills_dir
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def create(self, name: str, description: str,
               content: str, version: str = "1.0.0",
               author: str = "vault",
               tags: Optional[list[str]] = None) -> Path:
        """
        创建新 Skill：生成 SKILL.md 文件。
        name 应为 kebab-case（skill-name）。
        """
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "-", name.lower())
        skill_dir = self.skills_dir / safe_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        file_path = skill_dir / "SKILL.md"

        frontmatter = {
            "name": safe_name,
            "description": description,
            "version": version,
            "author": author,
            "metadata": {
                "hermes": {
                    "tags": tags or [],
                    "confidence": 0.5
                }
            }
        }

        full_content = "---\n" + yaml.dump(frontmatter) + "---\n\n" + content
        file_path.write_text(full_content, encoding="utf-8")
        return file_path

    def patch(self, name: str, old: str, new: str) -> bool:
        """
        对 SKILL.md 做 find-and-replace（精确替换）。
        Returns True if replacement was made.
        """
        file_path = self._resolve(name)
        if not file_path:
            return False
        content = file_path.read_text(encoding="utf-8")
        if old not in content:
            return False
        content = content.replace(old, new)
        file_path.write_text(content, encoding="utf-8")
        return True

    def delete(self, name: str) -> bool:
        """删除整个 Skill 目录"""
        skill_dir = self.skills_dir / name
        if not skill_dir.exists():
            return False
        import shutil
        shutil.rmtree(skill_dir)
        return True

    def list_skills(self) -> list[str]:
        """列出所有 Skill"""
        if not self.skills_dir.exists():
            return []
        return [d.name for d in self.skills_dir.iterdir() if d.is_dir()]

    def get_skill(self, name: str) -> Optional[Skill]:
        """加载指定 Skill 的完整内容"""
        file_path = self._resolve(name)
        if not file_path:
            return None
        raw = file_path.read_text(encoding="utf-8")
        parts = raw.split("---\n", 2)
        if len(parts) < 3:
            return None
        meta = yaml.safe_load(parts[1]) or {}
        return Skill(
            name=meta.get("name", name),
            description=meta.get("description", ""),
            version=meta.get("version", "1.0.0"),
            author=meta.get("author", "vault"),
            metadata=meta.get("metadata", {}),
            content=parts[2].strip(),
            file_path=file_path
        )

    def _resolve(self, name: str) -> Optional[Path]:
        """将 name 解析为文件路径"""
        candidates = [
            self.skills_dir / name / "SKILL.md",
            self.skills_dir / name.replace("_", "-") / "SKILL.md"
        ]
        for c in candidates:
            if c.exists():
                return c
        return None
