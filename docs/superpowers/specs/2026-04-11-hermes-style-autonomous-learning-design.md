# Vault 自主学习系统升级设计方案

> 日期：2026-04-11
> 参照：Hermes Agent 自主学习闭环
> 决策：方案 A — Hermes-like 全链路

---

## 1. 目标

让 Claude 在 vault 中实现**闭环自主学习**：

```
任务执行 → 成功/失败检测 → 创建/更新本能 → 会话结束存储 →
跨会话搜索 → 用户建模 → 上下文压缩 → 本能自动进化为 Skill
```

---

## 2. 架构总览

```
.claude/
├── sessions.db              # SQLite：会话历史 + FTS5 搜索
├── user/
│   └── USER.md              # 用户建模（Peer Cards + Persistent Conclusions）
├── instincts/
│   ├── registry.json        # 本能注册表（现有）
│   ├── global/               # 全局本能（现有）
│   └── {project}/           # 项目本能（现有）
├── skills/
│   └── {name}/SKILL.md      # 进化后的完整 Skill
├── commands/                # 现有命令
│   ├── learn.md
│   ├── evolve.md
│   └── instinct-create.md
└── modules/                  # 新增核心模块
    ├── session_search.py     # FTS5 跨会话搜索
    ├── context_compressor.py # 上下文自动压缩
    ├── skill_manager.py      # Skill CRUD + 自动进化
    └── user_modeler.py       # 用户建模（Peer Cards）
```

---

## 3. 模块详细设计

### 3.1 Session Search（跨会话搜索）

**文件：** `.claude/modules/session_search.py`

**数据库 schema：**
```sql
CREATE TABLE sessions (
  id INTEGER PRIMARY KEY,
  session_id TEXT UNIQUE,
  started_at TEXT,
  ended_at TEXT,
  summary TEXT,          -- LLM 生成的会话摘要
  token_count INTEGER,
  outcome TEXT           -- success / partial / failed
);

CREATE TABLE messages (
  id INTEGER PRIMARY KEY,
  session_id TEXT,
  role TEXT,             -- user / assistant
  content TEXT,
  tool_calls TEXT,        -- JSON
  created_at TEXT
);

CREATE VIRTUAL TABLE messages_fts USING fts5(
  content, content='messages', content_rowid='id'
);
```

**触发场景：**
- 用户说"上次我们做过这个"、"记得吗"
- 涉及历史决策的上下文注入

**搜索流程：**
1. FTS5 匹配 query
2. 按 session_id 分组，取 top 5 会话
3. LLM 总结每个会话的相关段落
4. 返回 per-session 摘要 + 原文引用

**API 设计：**
```python
def search_sessions(query: str, limit: int = 5) -> list[SessionSummary]:
    """FTS5 search across all past sessions"""

def save_session(session_id: str, messages: list[Message], outcome: str):
    """Save completed session to SQLite"""

def get_session_context(session_id: str) -> str:
    """Retrieve full session transcript"""
```

---

### 3.2 User Modeling（用户建模）

**文件：** `.claude/modules/user_modeler.py`
**输出：** `.claude/user/USER.md`

**Peer Card 结构（YAML frontmatter + markdown）：**
```yaml
---
name: huage
last_updated: 2026-04-11
version: 1.0
recallMode: hybrid  # hybrid / context / tools
observationMode: unified
dialecticReasoningLevel: medium
---

# User Profile

## Communication Style
- 称呼：喜欢被称为"华哥"
- 响应偏好：简洁、直接、不废话
- 反馈模式：明确表达满意/不满意

## Project Context
- 当前项目：漠玫传 S01E01
- 角色：制作人/决策者
- 目标：短剧工业化生产

## Persistent Conclusions
- 不喜欢空洞词（"delve", "crucial", "robust"）
- 偏好中文优先
- 对 AI 味敏感（去 AI 腔是核心诉求）

## Observed Patterns
- 每次任务完成后会问"有其他需要吗"
- 纠正行为时会直接说"不是这样"
- 偏好小步提交而非大而全
```

**更新时机：**
- 会话结束时自动同步
- 用户纠正行为时立即更新
- 通过 `dialectic reasoning` 主动推理新结论

**API 设计：**
```python
def update_peer_card(observations: list[Observation]):
    """Update USER.md from session observations"""

def get_peer_card() -> dict:
    """Read current user model"""

def search_user_memory(query: str) -> list[str]:
    """Search USER.md for relevant context"""
```

---

### 3.3 Context Compression（上下文压缩）

**文件：** `.claude/modules/context_compressor.py`

**触发条件：** 上下文 > 60K tokens

**压缩策略（借鉴 Hermes）：**
1. **保护头部：** system prompt + 第一轮交互（不压缩）
2. **保护尾部：** 最近 20K tokens（不压缩）
3. **压缩中间：** LLM 迭代摘要

**摘要 prompt 结构：**
```
## 会话摘要

### 目标
[用户原始目标]

### 进展
[完成了什么]

### 关键决策
[做了哪些重要决定，理由]

### 文件
[涉及的文件路径]

### 下一步
[未完成的部分]
```

**迭代压缩：** 后续压缩在上一份摘要上继续，保留历史积累

**API 设计：**
```python
def compress_context(messages: list[Message], token_budget: int) -> list[Message]:
    """
    Compress middle turns, protect head + tail.
    Returns new message list within token budget.
    """

def should_compress(messages: list[Message], threshold: int = 60000) -> bool:
    """Check if compression is needed"""
```

---

### 3.4 Skills + Instincts 统一 + 自动进化

**文件：** `.claude/modules/skill_manager.py` + `.claude/modules/instinct_evolver.py`

**Skill 格式（对齐 Hermes SKILL.md）：**
```yaml
---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks
version: 1.1.0
author: vault
metadata:
  hermes:
    tags: [delegation, subagent, implementation, workflow, parallel]
    related_skills: [writing-plans, requesting-code-review]
    confidence: 0.9
---

# Subagent-Driven Development

## Overview
[Detailed procedure]

## Triggers
- When to use this skill
- When NOT to use this skill

## Steps
[Step-by-step process]

## Examples
[Code snippets]
```

**现有 Instinct → Skill 自动进化：**
```python
# instinct_evolver.py
def should_evolve(instinct: Instinct) -> bool:
    """Confidence >= 0.9 OR multiple related instincts share domain"""

def evolve_to_skill(instincts: list[Instinct]) -> Skill:
    """Merge related instincts into one SKILL.md"""

def auto_suggest_evolution():
    """Run at session end, suggest if threshold met"""
    # 置信度 0.9 的本能自动建议升级
    # 多个相关本能（相同 domain）自动聚类
```

**Skill Manager API：**
```python
class SkillManager:
    def create(self, name: str, content: str) -> Path:
        """Create new SKILL.md + directory"""

    def patch(self, name: str, old: str, new: str):
        """Find-and-replace on SKILL.md"""

    def delete(self, name: str):
        """Remove skill directory"""

    def list_skills(self) -> list[str]:
        """List all available skills"""

    def get_skill(self, name: str) -> Skill:
        """Load skill by name"""
```

---

### 3.5 会话历史存储

**文件：** `.claude/modules/session_store.py`

**会话结束时的写入流程：**
```python
def on_session_end(session_id: str, messages: list[Message], outcome: str):
    # 1. 生成 LLM 摘要
    summary = summarize_session(messages)

    # 2. 写入 sessions 表
    db.execute("INSERT INTO sessions ...", summary)

    # 3. 写入 messages 表
    for msg in messages:
        db.execute("INSERT INTO messages ...", msg)

    # 4. 重建 FTS5 索引
    rebuild_fts_index()

    # 5. 更新用户建模
    update_peer_card_from_session(session_id)

    # 6. 检查本能是否达到进化阈值
    auto_suggest_evolution()
```

---

## 4. 现有模块集成

| 现有模块 | 角色 | 改动 |
|---------|------|------|
| `.claude/commands/learn.md` | 本能提取入口 | 保持，补充自动触发逻辑 |
| `.claude/commands/evolve.md` | 本能进化入口 | 扩展为自动 + 手动双模式 |
| `.claude/commands/instinct-create.md` | 手动本能创建 | 保持 |
| `.claude/instincts/registry.json` | 本能注册表 | 扩展 domain 字段支持 |
| `.claude/rules/continuous-learning.md` | 规则定义 | 更新为新架构 |

---

## 5. CLI 命令扩展

```bash
# 会话管理
/clearn              # 从当前会话提取本能（现有）
/evolve             # 触发本能进化检查（现有）
/compress            # 手动触发上下文压缩

# 新增命令
/session-search <q>  # 跨会话搜索
/user-profile        # 查看当前用户建模
/skill-list          # 列出所有 Skill
/skill-create <name> # 创建新 Skill
/skill-patch <name>  # 打补丁 Skill

# 自动触发（无需命令）
- 会话结束 → 自动保存 + FTS5 索引 + 用户建模更新
- 上下文 > 60K → 自动压缩
- 本能置信度 >= 0.9 → 自动建议升级为 Skill
```

---

## 6. 数据流总图

```
[用户输入]
    ↓
[上下文预取] → user_modeler.get_peer_card()
    ↓
[Claude 处理]
    ↓
[上下文 > 60K?] → yes → compress_context()
    ↓
[任务完成]
    ↓
[save_session()] → sessions.db
    ↓
[update_peer_card()] → USER.md
    ↓
[auto_suggest_evolution()] → 本能阈值检测
    ↓
[置信度 >= 0.9?] → yes → 建议升级 Skill
    ↓
[下次会话]
    ↓
[用户提到历史?] → session_search.search_sessions()
```

---

## 7. 依赖关系

```
skill_manager.py     # 无依赖（叶子）
instinct_evolver.py  # → skill_manager.py
user_modeler.py      # → instinct_evolver.py（进化时更新用户）
session_store.py     # → user_modeler.py, instinct_evolver.py
context_compressor.py # 无依赖（叶子）
session_search.py    # → session_store.py（查询历史）
```

---

## 8. 暂不纳入范围

- RL 训练基础设施（trajectory_compressor / rl_training_tool）
- Pluggable memory provider 架构（未来插件化）
- Honcho 的 dialectic Q&A 完整实现（简化版替代）

---

## 9. 实施顺序

1. **Phase 1：** session_store.py + sessions.db（FTS5）
2. **Phase 2：** session_search.py（跨会话搜索）
3. **Phase 3：** user_modeler.py（USER.md 用户建模）
4. **Phase 4：** context_compressor.py（自动压缩）
5. **Phase 5：** skill_manager.py + instinct_evolver.py（本能进化）
6. **Phase 6：** 集成到现有命令（learn/evolve/ instincts-create）
7. **Phase 7：** MEMORY.md 仪表盘整合
