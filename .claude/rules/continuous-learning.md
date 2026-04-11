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
