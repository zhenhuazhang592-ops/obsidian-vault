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
