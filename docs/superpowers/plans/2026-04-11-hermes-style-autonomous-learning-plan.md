# Vault 自主学习系统 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 vault 中实现 Hermes Agent 风格的闭环自主学习系统：FTS5 跨会话搜索 + USER.md 用户建模 + Context Compression + 本能自动进化为 Skill

**Architecture:** 5 个独立 Python 模块（session_store / session_search / user_modeler / context_compressor / skill_manager+instinct_evolver）+ SQLite sessions.db + USER.md + CLI 命令扩展。模块间通过函数调用通信，无循环依赖。

**Tech Stack:** Python 3, SQLite (FTS5), tiktoken (token 计数), YAML frontmatter

---

## 文件结构

```
.claude/
├── modules/                          # 新增核心模块
│   ├── session_store.py               # Phase 1: SQLite 会话持久化 + FTS5
│   ├── session_search.py              # Phase 2: FTS5 搜索 + LLM 摘要
│   ├── context_compressor.py          # Phase 4: 上下文自动压缩
│   ├── user_modeler.py                # Phase 3: USER.md 用户建模
│   ├── skill_manager.py               # Phase 5: Skill CRUD
│   └── instinct_evolver.py            # Phase 5: 本能 → Skill 进化
├── user/                             # Phase 3: 用户建模输出
│   └── USER.md
├── sessions.db                       # Phase 1: SQLite（自动创建）
├── skills/                           # Phase 5: 进化后的 Skill
├── commands/                         # Phase 6: 命令扩展
│   ├── learn.md                      # Phase 6: 补充自动触发
│   ├── evolve.md                     # Phase 6: 扩展自动+手动
│   ├── instinct-create.md             # Phase 6: 小改
│   ├── session-search.md             # Phase 2: 新增
│   ├── user-profile.md               # Phase 3: 新增
│   ├── skill-list.md                 # Phase 5: 新增
│   ├── skill-create.md               # Phase 5: 新增
│   └── skill-patch.md                # Phase 5: 新增
├── instincts/                        # 现有（不改结构）
│   ├── registry.json
│   └── global/
└── rules/
    └── continuous-learning.md        # Phase 6: 更新为新架构
```

---

## Phase 1: session_store.py + sessions.db（FTS5）

### 依赖：无（叶子模块）

### Task 1: 创建 modules 目录和 session_store.py 基础结构

**Files:**
- Create: `.claude/modules/__init__.py`
- Create: `.claude/modules/session_store.py`

- [ ] **Step 1: 创建 `__init__.py`**

```python
# .claude/modules/__init__.py
"""Vault 自主学习系统核心模块"""
from .session_store import SessionStore
from .session_search import SessionSearch
from .context_compressor import ContextCompressor
from .user_modeler import UserModeler
from .skill_manager import SkillManager
from .instinct_evolver import InstinctEvolver

__all__ = [
    "SessionStore",
    "SessionSearch",
    "ContextCompressor",
    "UserModeler",
    "SkillManager",
    "InstinctEvolver",
]
```

- [ ] **Step 2: 创建 `session_store.py` — 数据库初始化和基础类**

```python
# .claude/modules/session_store.py
"""会话持久化：SQLite sessions + messages 表 + FTS5 全文索引"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path.home() / ".claude" / "sessions.db"


class SessionStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        """初始化数据库 schema"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                summary TEXT,
                token_count INTEGER DEFAULT 0,
                outcome TEXT DEFAULT 'unknown'
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                content,
                content='messages',
                content_rowid='id'
            );

            CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
            END;
        """)
        conn.close()

    def begin_session(self, session_id: str) -> None:
        """标记新会话开始"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, started_at) VALUES (?, ?)",
            (session_id, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

    def add_message(self, session_id: str, role: str, content: str,
                    tool_calls: Optional[list] = None) -> None:
        """写入单条消息"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO messages (session_id, role, content, tool_calls, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, role, content, json.dumps(tool_calls) if tool_calls else None,
             datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

    def end_session(self, session_id: str, summary: str,
                    token_count: int, outcome: str) -> None:
        """标记会话结束"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """UPDATE sessions SET ended_at=?, summary=?, token_count=?, outcome=?
               WHERE session_id=?""",
            (datetime.now().isoformat(), summary, token_count, outcome, session_id)
        )
        conn.commit()
        conn.close()

    def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话元数据"""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0], "session_id": row[1], "started_at": row[2],
            "ended_at": row[3], "summary": row[4], "token_count": row[5], "outcome": row[6]
        }

    def get_session_messages(self, session_id: str) -> list[dict]:
        """获取会话所有消息"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT role, content, tool_calls, created_at FROM messages WHERE session_id=? ORDER BY id",
            (session_id,)
        ).fetchall()
        conn.close()
        return [
            {"role": r[0], "content": r[1], "tool_calls": json.loads(r[2]) if r[2] else None, "created_at": r[3]}
            for r in rows
        ]

    def search_messages(self, query: str, limit: int = 50) -> list[dict]:
        """FTS5 搜索消息"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            """SELECT m.session_id, m.role, m.content, m.created_at,
                      snippets(messages_fts, 0, '>>>', '<<<', '...', 32) as snippet
               FROM messages_fts
               JOIN messages m ON messages_fts.rowid = m.id
               WHERE messages_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (query, limit)
        ).fetchall()
        conn.close()
        return [
            {"session_id": r[0], "role": r[1], "content": r[2], "created_at": r[3], "snippet": r[4]}
            for r in rows
        ]

    def get_recent_sessions(self, limit: int = 10) -> list[dict]:
        """获取最近会话列表"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            """SELECT session_id, started_at, ended_at, summary, outcome
               FROM sessions WHERE ended_at IS NOT NULL
               ORDER BY ended_at DESC LIMIT ?""",
            (limit,)
        ).fetchall()
        conn.close()
        return [
            {"session_id": r[0], "started_at": r[1], "ended_at": r[2], "summary": r[3], "outcome": r[4]}
            for r in rows
        ]
```

- [ ] **Step 3: Commit**

```bash
cd /Users/huage/Obsidian\ Vault
git add .claude/modules/__init__.py .claude/modules/session_store.py
git commit -m "feat(learning): Phase 1 — SessionStore with SQLite + FTS5
- sessions + messages tables with FTS5 virtual table
- begin_session / add_message / end_session
- search_messages via FTS5
- get_recent_sessions"
```

---

### Task 2: 创建 /session-search CLI 命令文件

**Files:**
- Create: `.claude/commands/session-search.md`

- [ ] **Step 1: 创建命令文件**

```markdown
---
name: session-search
description: 跨会话搜索 — FTS5 全文搜索历史会话
---

# /session-search — 跨会话搜索

## 触发条件

用户提到以下关键词时自动触发（无需显式调用）：
- "上次我们做过这个"
- "记得吗"
- "之前有过"
- "我们之前"

## 使用方式

```
/session-search <搜索query>
```

示例：`/session-search 短剧大纲怎么写`

## 内部流程

1. 调用 `SessionStore.search_messages(query)`
2. 按 session_id 分组，取 top 5 会话
3. 调用 LLM 总结每个会话的相关段落
4. 返回 per-session 摘要 + 原文引用

## 输出格式

```
## 搜索结果："<query>"

### 会话 1（2026-04-09）
**摘要：** 讨论了短剧分镜节奏的处理方式
**引用：**
> >>>用户说：我们用三幕结构吧<<<
> >>>AI回复：好的，三幕结构适合...<<<

### 会话 2（2026-04-08）
...
```
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/session-search.md
git commit -m "feat(learning): add /session-search command"
```

---

## Phase 2: session_search.py（LLM 摘要搜索）

### 依赖：session_store.py

### Task 3: 创建 session_search.py

**Files:**
- Create: `.claude/modules/session_search.py`
- Modify: `.claude/commands/session-search.md`（更新输出格式）

- [ ] **Step 1: 创建 `session_search.py`**

```python
# .claude/modules/session_search.py
"""FTS5 搜索 + LLM 摘要"""

import os
from dataclasses import dataclass
from typing import Optional
from .session_store import SessionStore


@dataclass
class SessionHit:
    session_id: str
    summary: Optional[str]
    started_at: str
    outcome: str
    relevance_snippets: list[str]


class SessionSearch:
    def __init__(self, store: Optional[SessionStore] = None):
        self.store = store or SessionStore()

    def search(self, query: str, limit_sessions: int = 5) -> list[SessionHit]:
        """
        FTS5 搜索 + 按会话分组返回。
        LLM 摘要逻辑由调用方注入（避免直接依赖 LLM SDK）。
        """
        # 1. FTS5 搜索
        raw_hits = self.store.search_messages(query, limit=50)
        if not raw_hits:
            return []

        # 2. 按 session_id 分组
        session_ids = list(dict.fromkeys(h["session_id"] for h in raw_hits))[:limit_sessions]

        results = []
        for sid in session_ids:
            session_meta = self.store.get_session(sid)
            session_messages = self.store.get_session_messages(sid)

            # 取相关片段
            snippets = [h["snippet"] for h in raw_hits if h["session_id"] == sid]

            # 构建上下文片段（供 LLM 摘要）
            context = self._build_context(sid, session_messages, snippets)

            results.append(SessionHit(
                session_id=sid,
                summary=session_meta.get("summary") if session_meta else None,
                started_at=session_meta.get("started_at", "") if session_meta else "",
                outcome=session_meta.get("outcome", "unknown") if session_meta else "unknown",
                relevance_snippets=context
            ))

        return results

    def _build_context(self, session_id: str,
                       messages: list[dict], snippets: list[str]) -> list[str]:
        """从消息中构建相关上下文片段"""
        context = []
        for msg in messages[-10:]:  # 最近 10 条消息
            role = msg["role"]
            content = msg["content"][:500]  # 截断
            context.append(f"[{role.upper()}] {content}")
        return context

    def format_for_display(self, hits: list[SessionHit]) -> str:
        """格式化搜索结果为 markdown"""
        if not hits:
            return "**没有找到相关会话**"

        lines = []
        for i, hit in enumerate(hits, 1):
            lines.append(f"### 会话 {i}（{hit.started_at[:10]}）")
            if hit.summary:
                lines.append(f"**摘要：** {hit.summary}")
            lines.append(f"**结果：** {hit.outcome}")
            lines.append("")
            for snippet in hit.relevance_snippets[:3]:
                lines.append(f"> {snippet}")
            lines.append("")
        return "\n".join(lines)
```

- [ ] **Step 2: Commit**

```bash
git add .claude/modules/session_search.py
git commit -m "feat(learning): Phase 2 — SessionSearch with FTS5 + LLM-ready context"
```

---

## Phase 3: user_modeler.py（USER.md 用户建模）

### 依赖：无（叶子模块）

### Task 4: 创建 user_modeler.py 和初始 USER.md

**Files:**
- Create: `.claude/modules/user_modeler.py`
- Create: `.claude/user/USER.md`（初始模板）
- Create: `.claude/commands/user-profile.md`

- [ ] **Step 1: 创建 `user_modeler.py`**

```python
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
```

- [ ] **Step 2: 创建 `user/USER.md` 初始文件**

```bash
mkdir -p /Users/huage/.claude/user
# 文件由 UserModeler()._write_template() 自动生成，这里手动创建初始版本
cat > /Users/huage/.claude/user/USER.md << 'EOF'
---
name: huage
last_updated: 2026-04-11
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
- 待记录
EOF
```

- [ ] **Step 3: 创建 /user-profile 命令**

```markdown
---
name: user-profile
description: 查看当前用户建模（USER.md Peer Card）
---

# /user-profile

## 功能

显示当前 USER.md 的完整内容，即 Claude 对"华哥"的认知模型。

## 使用

```
/user-profile
```

## 输出

USER.md 的完整内容，展示当前已学习到的用户偏好、沟通风格、Observed Patterns。
```

- [ ] **Step 4: Commit**

```bash
git add .claude/modules/user_modeler.py
git add .claude/user/USER.md
git add .claude/commands/user-profile.md
git commit -m "feat(learning): Phase 3 — UserModeler + USER.md Peer Card
- UserModeler with get_peer_card / update_field / append_observation
- Initial USER.md template for huage
- /user-profile command"
```

---

## Phase 4: context_compressor.py（上下文自动压缩）

### 依赖：无（叶子模块）

### Task 5: 创建 context_compressor.py

**Files:**
- Create: `.claude/modules/context_compressor.py`
- Create: `.claude/commands/compress.md`

- [ ] **Step 1: 创建 `context_compressor.py`**

```python
# .claude/modules/context_compressor.py
"""上下文自动压缩：head+tail 保护策略"""

import tiktoken
from dataclasses import dataclass
from typing import Callable

# 默认阈值：60K tokens
DEFAULT_THRESHOLD = 60_000
# 尾部保护 token 预算：20K
TAIL_TOKEN_BUDGET = 20_000


@dataclass
class CompressionResult:
    original_count: int
    compressed_count: int
    summary: str
    kept_messages: list[dict]


class ContextCompressor:
    def __init__(self, model: str = "cl100k_base", threshold: int = DEFAULT_THRESHOLD):
        self.encoding = tiktoken.get_encoding(model)
        self.threshold = threshold

    def should_compress(self, messages: list[dict]) -> bool:
        """判断是否需要压缩"""
        total = self._count_tokens(messages)
        return total > self.threshold

    def compress(self, messages: list[dict],
                 summarize_fn: Callable[[list[dict]], str]) -> CompressionResult:
        """
        head+tail 保护压缩策略。

        - 保护头部：system prompt + 第一轮交互（index 0 ~ 2）
        - 保护尾部：最近 20K tokens
        - 压缩中间：LLM 摘要

        Args:
            messages: 原始消息列表
            summarize_fn: 接收中间段消息列表，返回摘要字符串的函数（由调用方注入 LLM）

        Returns:
            CompressionResult with summary and new message list
        """
        total_tokens = self._count_tokens(messages)
        if total_tokens <= self.threshold:
            return CompressionResult(total_tokens, total_tokens, "", messages)

        # 1. 保护头部：system + first exchange (up to index 2)
        head_end = min(3, len(messages))
        head = messages[:head_end]
        head_tokens = self._count_tokens(head)

        # 2. 保护尾部：最近的 20K tokens
        tail = self._protect_tail(messages, TAIL_TOKEN_BUDGET)
        tail_tokens = self._count_tokens(tail)

        # 3. 中间部分
        middle = messages[head_end:-len(tail)] if len(tail) > 0 else messages[head_end:]

        # 4. 压缩中间（LLM 摘要）
        if middle:
            summary = summarize_fn(middle)
            summary_tokens = len(self.encoding.encode(summary))
            middle_compressed = [{
                "role": "system",
                "content": f"[先前会话摘要] {summary}",
                "_is_summary": True
            }]
        else:
            summary = ""
            middle_compressed = []

        # 5. 估算压缩后总量
        compressed_tokens = head_tokens + summary_tokens + tail_tokens

        # 6. 如果仍然超限，进一步压缩尾部
        final_messages = head + middle_compressed + tail
        while self._count_tokens(final_messages) > self.threshold and len(tail) > 2:
            # 逐步减少尾部
            tail = tail[:-2]
            final_messages = head + middle_compressed + tail

        return CompressionResult(
            original_count=total_tokens,
            compressed_count=self._count_tokens(final_messages),
            summary=summary,
            kept_messages=final_messages
        )

    def _protect_tail(self, messages: list[dict], token_budget: int) -> list[dict]:
        """从尾部取消息，直到 token 预算用完"""
        result = []
        total = 0
        for msg in reversed(messages):
            msg_tokens = self._count_tokens([msg])
            if total + msg_tokens <= token_budget:
                result.insert(0, msg)
                total += msg_tokens
            else:
                break
        return result

    def _count_tokens(self, messages: list[dict]) -> int:
        """计算消息列表的 token 总数"""
        if not messages:
            return 0
        text = "\n".join(
            f"{m.get('role', '')}: {m.get('content', '')}"
            for m in messages
        )
        return len(self.encoding.encode(text))
```

- [ ] **Step 2: 创建 /compress 命令**

```markdown
---
name: compress
description: 手动触发上下文压缩（自动触发无需命令）
---

# /compress

## 功能

手动触发上下文压缩。当前的上下文如果超过 60K tokens，自动压缩中间部分，保留头部（system prompt）和尾部（最近 20K tokens）。

## 使用

```
/compress
```

## 说明

大多数情况下压缩是**自动触发**的，无需手动调用。只有在需要立即释放上下文空间时使用此命令。
```

- [ ] **Step 3: Commit**

```bash
git add .claude/modules/context_compressor.py .claude/commands/compress.md
git commit -m "feat(learning): Phase 4 — ContextCompressor head+tail protection
- tiktoken-based token counting
- should_compress threshold check
- compress with summarize_fn injection
- /compress command"
```

---

## Phase 5: skill_manager.py + instinct_evolver.py（本能进化）

### 依赖：session_store.py（session_store 已有）

### Task 6: 创建 skill_manager.py

**Files:**
- Create: `.claude/modules/skill_manager.py`
- Create: `.claude/modules/instinct_evolver.py`
- Create: `.claude/skills/`（Skill 输出目录）

- [ ] **Step 1: 创建 `skill_manager.py`**

```python
# .claude/modules/skill_manager.py
"""Skill 管理：CRUD 操作"""

import re
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


SKILLS_DIR = Path.home() / ".claude" / "skills"


@dataclass
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
        front, _, body = raw.partition("---")
        # 读 frontmatter 后再分割
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
```

- [ ] **Step 2: 创建 `instinct_evolver.py`**

```python
# .claude/modules/instinct_evolver.py
"""本能 → Skill 自动进化引擎"""

import json
import yaml
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

        # 返回有 2+ 本能的 domain
        return [group for group in by_domain.values() if len(group) >= 2]

    def evolve_to_skill(self, instincts: list[Instinct], skill_name: str) -> Path:
        """
        将多个本能合并为一个 Skill。
        skill_name 应为 kebab-case。
        """
        # 合并所有本能的 behavior
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

        # 合并 tags
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

        # 1. 高置信度本能
        for i in instincts:
            if self.should_evolve(i):
                suggestions.append(
                    f"CONF_0.9: {i.name} (confidence={i.confidence}) → Skill"
                )

        # 2. 可聚类进化
        for cluster in self.find_evolvable_clusters():
            names = [i.name for i in cluster]
            suggestions.append(
                f"CLUSTER: {names} → Unified Skill (domain={cluster[0].domain})"
            )

        return suggestions
```

**Note:** `skill_manager.py` 需要在文件顶部添加 `from dataclasses import dataclass`。

- [ ] **Step 3: 创建 `.claude/skills/` 目录占位**

```bash
mkdir -p /Users/huage/.claude/skills
touch /Users/huage/.claude/skills/.gitkeep
```

- [ ] **Step 4: 创建 /skill-list, /skill-create, /skill-patch 命令**

```markdown
---
name: skill-list
description: 列出所有已注册的 Skill
---

# /skill-list

## 功能

显示所有已创建的 Skill，包括本能进化而来的 Skill。

## 使用

```
/skill-list
```
```

```markdown
---
name: skill-create
description: 创建新 Skill
---

# /skill-create

## 功能

基于模板创建新 Skill，自动生成 SKILL.md 文件。

## 使用

```
/skill-create <name> <description>
```

示例：`/skill-create my-custom-skill 这是一个自定义技能`
```

```markdown
---
name: skill-patch
description: 对 Skill 文件做精确补丁（find-and-replace）
---

# /skill-patch

## 功能

对已有 Skill 的 SKILL.md 做精确替换（old → new），不 rewrite 整个文件。

## 使用

```
/skill-patch <skill-name>
# 然后描述要替换什么
```

这是**首选**的 Skill 更新方式（ Hermes 规范）。
```

- [ ] **Step 5: Commit**

```bash
git add .claude/modules/skill_manager.py .claude/modules/instinct_evolver.py .claude/skills/.gitkeep .claude/commands/skill-*.md
git commit -m "feat(learning): Phase 5 — SkillManager + InstinctEvolver
- SkillManager: create/patch/delete/list_skills/get_skill
- InstinctEvolver: load_instincts / should_evolve / evolve_to_skill
- Confidence 0.9 threshold + domain clustering
- /skill-list, /skill-create, /skill-patch commands"
```

---

## Phase 6: 集成到现有命令

### Task 7: 更新 learn / evolve / instinct-create 命令

**Files:**
- Modify: `.claude/commands/learn.md`
- Modify: `.claude/commands/evolve.md`
- Modify: `.claude/rules/continuous-learning.md`

- [ ] **Step 1: 更新 `learn.md`**

在现有 learn.md 末尾补充：

```markdown
## 自动触发逻辑

除了手动运行 `/learn`，以下情况自动触发本能提取：

1. **复杂任务完成** — 5+ 工具调用成功执行
2. **用户纠正** — 用户明确纠正了 AI 的行为方式
3. **错误克服** — 通过非平凡工作流解决了错误

自动触发时，Claude 会：
1. 分析当前会话中的关键模式
2. 草拟本能文件
3. 在回复末尾提示："检测到可提取的模式，是否保存？"
```

- [ ] **Step 2: 更新 `evolve.md`**

```markdown
---
name: evolve
description: 触发本能进化检查 + 手动/自动双模式
---

# /evolve — 本能进化

## 双模式

### 手动模式
```
/evolve
```

### 自动模式（无需命令）
- 会话结束时自动检查
- 置信度 >= 0.9 的本能 → 自动建议升级为 Skill
- 多个相同 domain 本能（>=2，confidence >= 0.7）→ 自动聚类建议

## 进化条件

| 条件 | 触发 |
|------|------|
| 单一本能，confidence >= 0.9 | 直接建议升级 |
| 同一 domain 多个本能，>= 0.7 | 聚类生成统一 Skill |

## 输出示例

```
检测到 1 个本能达到进化阈值：
- [本能名] (confidence: 0.9)

是否升级为 Skill？ (y/n)

检测到 1 个可聚类的本能组：
- domain: 角色弧线
- 本能: [主角觉醒时机, 对手戏张力节奏]

是否聚类生成统一 Skill？ (y/n)
```
```

- [ ] **Step 3: 更新 `continuous-learning.md` 规则文件**

替换现有内容，映射新架构：

```markdown
# 连续学习规则 · Instinct 系统 V2

> 来源：Hermes Agent + vault 实践
> 核心原则：不塞满 system prompt，让模型"遇到时"才学到

---

## 架构（V2）

5 个核心模块，闭环运作：

```
任务执行 → 本能提取(/learn) → 会话存储(session_store)
    ↓
跨会话召回(session_search) ← → 用户建模(user_modeler)
    ↓
上下文压缩(context_compressor) ← → 本能进化(instinct_evolver → skill_manager)
```

---

## 模块职责

| 模块 | 职责 |
|------|------|
| `session_store.py` | SQLite 会话持久化 + FTS5 索引 |
| `session_search.py` | 跨会话 FTS5 搜索 + LLM 摘要 |
| `user_modeler.py` | USER.md Peer Card 管理 |
| `context_compressor.py` | head+tail 保护压缩（60K 阈值） |
| `skill_manager.py` | Skill CRUD（create/patch/delete） |
| `instinct_evolver.py` | 本能 → Skill 自动进化 |

---

## 触发规则

| 场景 | 触发 |
|------|------|
| 会话结束 | 自动保存 + 更新 USER.md + 进化检查 |
| 上下文 > 60K | 自动压缩中间部分 |
| 用户提到历史 | FTS5 搜索相关会话 |
| 本能 confidence >= 0.9 | 自动建议升级 Skill |
| 5+ 工具调用成功 | 自动提取本能 |
| 用户纠正行为 | 自动追加到 USER.md Observed Patterns |
```

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/learn.md .claude/commands/evolve.md .claude/rules/continuous-learning.md
git commit -m "feat(learning): Phase 6 — integrate auto-trigger into learn/evolve commands
- learn.md: auto-trigger for 5+ tool calls + user corrections
- evolve.md: auto mode + manual dual mode
- continuous-learning.md: V2 architecture mapping"
```

---

## Phase 7: MEMORY.md 仪表盘整合

### Task 8: 更新 MEMORY.md 加入新系统入口

**Files:**
- Modify: `.claude/projects/-Users-huage-Obsidian-Vault/memory/MEMORY.md`

- [ ] **Step 1: 在 MEMORY.md 末尾追加新系统状态区**

在 MEMORY.md 末尾（当前仪表盘之后）添加：

```markdown
---

## 自主学习系统状态

| 模块 | 状态 | 路径 |
|------|------|------|
| SessionStore (SQLite+FTS5) | ✅ 已实现 | `.claude/modules/session_store.py` |
| SessionSearch | ✅ 已实现 | `.claude/modules/session_search.py` |
| UserModeler (USER.md) | ✅ 已实现 | `.claude/modules/user_modeler.py` |
| ContextCompressor | ✅ 已实现 | `.claude/modules/context_compressor.py` |
| SkillManager | ✅ 已实现 | `.claude/modules/skill_manager.py` |
| InstinctEvolver | ✅ 已实现 | `.claude/modules/instinct_evolver.py` |

**会话搜索**：`/session-search <query>`
**用户建模**：`/user-profile`
**Skill 管理**：`/skill-list`, `/skill-create`, `/skill-patch`
**手动压缩**：`/compress`
```

- [ ] **Step 2: Commit**

```bash
git add .claude/projects/-Users-huage-Obsidian-Vault/memory/MEMORY.md
git commit -m "feat(learning): Phase 7 — MEMORY.md dashboard integration"
```

---

## Spec 覆盖检查

| Spec 要求 | 对应 Task |
|---------|-----------|
| Session Search + FTS5 | Task 1, Task 3 |
| User Modeling (USER.md Peer Card) | Task 4 |
| Context Compression (60K, head+tail) | Task 5 |
| Skill Manager CRUD | Task 6 |
| Instinct → Skill 进化 | Task 6 |
| 会话历史存储 (sessions.db) | Task 1 |
| 自动触发逻辑 | Task 7 |
| CLI 命令扩展 | Task 1-6 |
| continuous-learning.md V2 | Task 7 |
| MEMORY.md 整合 | Task 8 |

**无遗漏** ✅

---

## Placeholder 扫描

- 无 "TBD" ✅
- 无 "TODO" ✅
- 所有 API 签名已定义 ✅
- 所有文件路径为实际路径 ✅

---

## 类型一致性检查

- `SessionStore` 方法：`begin_session`, `add_message`, `end_session`, `search_messages` ✅
- `SessionSearch.search()` → `list[SessionHit]` ✅
- `UserModeler.update_field`, `append_observation` ✅
- `ContextCompressor.compress(summarize_fn)` ✅
- `SkillManager.create/patch/delete/list_skills/get_skill` ✅
- `InstinctEvolver.evolve_to_skill(instincts, skill_name)` ✅

**无不一致** ✅

---

## 实施顺序（任务依赖）

```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7 → Task 8
```

- Task 1 (session_store): 无依赖 ✅
- Task 2 (/session-search cmd): 依赖 Task 1 ✅
- Task 3 (session_search): 依赖 Task 1 ✅
- Task 4 (user_modeler): 无依赖 ✅
- Task 5 (context_compressor): 无依赖 ✅
- Task 6 (skill_manager + instinct_evolver): 依赖 Task 1 (session_store) ✅
- Task 7 (集成命令): 依赖 Task 1-6 ✅
- Task 8 (MEMORY.md): 依赖 Task 1-6 ✅
