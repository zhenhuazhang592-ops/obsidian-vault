# .claude/modules/user_modeler.py
"""用户建模：USER.md Peer Card 管理"""

import re
import yaml
from pathlib import Path
from typing import Optional
from datetime import datetime


USER_DIR = Path.home() / ".claude" / "user"
USER_MD = USER_DIR / "USER.md"


class UserModeler:
    def __init__(self, user_md_path: Path = USER_MD):
        self.path = user_md_path
        self._ensure_initialized()

    def _ensure_initialized(self):
        """首次使用时创建初始模板"""
        if self.path.exists():
            return
        USER_DIR.mkdir(parents=True, exist_ok=True)
        self._write_template()

    def _write_template(self):
        """写入初始 Peer Card 模板"""
        content = """---
name: huage
last_updated: {date}
version: 1.0
recallMode: hybrid
observationMode: unified
dialecticReasoningLevel: medium
---

# User Profile

## Communication Style
- 称呼：喜欢被称为"华哥"
- 响应偏好：简洁、直接、不废话
- 反馈模式：明确表达满意/不满意

## Project Context
- 当前项目：待配置
- 角色：制作人/决策者
- 目标：待记录

## Persistent Conclusions
- 不喜欢空洞词（"delve", "crucial", "robust"等）
- 偏好中文优先
- 对 AI 味敏感（去 AI 腔是核心诉求）

## Observed Patterns
- 每次任务完成后会问"有其他需要吗"
- 纠正行为时会直接说"不是这样"
- 偏好小步提交而非大而全
- 确认后立即执行，不拖沓
""".format(date=datetime.now().date().isoformat())
        self.path.write_text(content, encoding="utf-8")

    def get_peer_card(self) -> dict:
        """读取当前用户模型"""
        if not self.path.exists():
            return {}
        raw = self.path.read_text(encoding="utf-8")
        # 解析 frontmatter
        if m := re.match(r"^---\n(.*?)\n---", raw, re.DOTALL):
            return yaml.safe_load(m.group(1)) or {}
        return {}

    def get_profile_text(self) -> str:
        """返回完整 USER.md 文本（不含 frontmatter）"""
        if not self.path.exists():
            return ""
        raw = self.path.read_text(encoding="utf-8")
        if m := re.search(r"^---\n.*?\n---\n(.*)", raw, re.DOTALL):
            return m.group(1).strip()
        return raw

    def update_field(self, section: str, key: str, value: str):
        """更新指定 section 下的 key-value"""
        if not self.path.exists():
            self._ensure_initialized()

        lines = self.path.read_text(encoding="utf-8").splitlines()
        section_found = False
        key_found = False
        new_lines = []

        for line in lines:
            if line.strip() == f"## {section}":
                section_found = True
            if section_found and key in line and ":" in line:
                new_lines.append(f"- {key}：{value}")
                key_found = True
                continue
            new_lines.append(line)

        if not key_found and section_found:
            # append at end of section
            for i, line in enumerate(new_lines):
                if line.strip() == f"## {section}":
                    # find end of this section
                    j = i + 1
                    while j < len(new_lines) and not new_lines[j].startswith("## "):
                        j += 1
                    new_lines.insert(j, f"- {key}：{value}")
                    break

        self.path.write_text("\n".join(new_lines), encoding="utf-8")
        self._update_timestamp()

    def append_observation(self, observation: str):
        """追加新的观察结论到 Observed Patterns"""
        if not self.path.exists():
            self._ensure_initialized()
        raw = self.path.read_text(encoding="utf-8")
        # 找到 Observed Patterns section，追加
        if "## Observed Patterns" in raw:
            lines = raw.splitlines()
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if line.strip() == "## Observed Patterns":
                    new_lines.append(f"- {observation}")
            raw = "\n".join(new_lines)
        self.path.write_text(raw, encoding="utf-8")
        self._update_timestamp()

    def _update_timestamp(self):
        """更新 last_updated 时间戳"""
        raw = self.path.read_text(encoding="utf-8")
        raw = re.sub(
            r"^last_updated: .+$", f"last_updated: {datetime.now().date().isoformat()}", raw,
            flags=re.MULTILINE
        )
        self.path.write_text(raw, encoding="utf-8")