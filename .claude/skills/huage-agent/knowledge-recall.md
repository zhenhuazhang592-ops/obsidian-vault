# Wiki 知识召回模块

> 用于 huage-agent 在启动创作 Skill 前，自动搜索并注入 wiki 中的相关知识

---

## 触发条件

以下场景必须执行知识召回：

1. **huage-gzh Phase 01**（研究阶段）— 从主题关键词召回相关知识
2. **huage888 Pipeline 启动前** — 从项目/主题召回相关知识

---

## 执行流程

### Step 1：提取关键词

从用户请求中提取主题关键词。

**示例**：
- 用户说："写一篇关于知识管理的公众号文章"
- 提取关键词：`知识管理`、`个人知识库`、`LLM`、`Wiki`

### Step 2：搜索 wiki

使用 Grep 工具搜索 `wiki/` 目录下匹配关键词的页面。

```
Grep "知识管理" wiki/ --output_mode files_with_matches
Grep "LLM" wiki/ --output_mode files_with_matches
```

### Step 3：读取匹配页面

对每个匹配的文件，读取其 Summary 和 Key Claims 部分：

```
Read wiki/concepts/LLM-Wiki.md
```

**提取内容**：
- `## Summary` 段落
- `## Key Claims` 列表
- `## Key Quotes`（如有）

### Step 4：格式化注入

将召回的知识格式化为创作上下文：

```markdown
📚 Wiki 知识召回（共 N 条）：

### [[LLM-Wiki]]
**摘要**：用 LLM 构建个人知识库的模式：编译而非检索，知识复利增长。
**关键主张**：
- LLM 解决了 Memex 无法解决的问题：谁来维护知识库
- 好的回答应该回流进 wiki，不消失在聊天历史中

### [[Compounding-Knowledge]]
**摘要**：复利增长的知识，wiki 的核心价值。
**关键主张**：
- 知识持久、累积、越用越有价值
```

### Step 5：注入创作上下文

将格式化后的知识注入到创作 Skill 的上下文中。

**注入位置**：
- huage-gzh：在 Phase 01 研究阶段开始时
- huage888：在 Pipeline 启动前

---

## 搜索策略

### 优先级

1. **概念页优先**：`wiki/concepts/` 下的页面
2. **实体页其次**：`wiki/entities/` 下的页面
3. **来源页最后**：`wiki/sources/` 下的页面

### 匹配规则

- 标题完全匹配 → 优先级最高
- Summary 包含关键词 → 优先级高
- Key Claims 包含关键词 → 优先级中
- 正文包含关键词 → 优先级低

### 数量限制

- 最多召回 **5 条**相关知识
- 避免注入过多噪音

---

## 质量控制

### 过滤噪音

以下情况不召回：
- 页面内容以"待填充"开头
- Summary 少于 10 字
- 与主题无明显关联

### 避免重复

- 同一概念页只召回一次
- 相似主张合并展示

---

## 示例输出

**输入**：用户说"写一篇关于 AI Agent 的公众号文章"

**执行**：
1. 提取关键词：`AI Agent`、`智能体`、`Agent`
2. 搜索 wiki/ 目录
3. 匹配：`wiki/concepts/LLM-Wiki.md`（提到 Agent 工作流）
4. 读取并格式化

**输出**：
```markdown
📚 Wiki 知识召回（共 1 条）：

### [[LLM-Wiki]]
**摘要**：用 LLM 构建个人知识库的模式：编译而非检索，知识复利增长。
**相关主张**：
- Agent 工作流：Ingest（摄入）→ Query（查询）→ Lint（健康检查）
- Schema 是让 Agent 从"通用聊天机器人"变成"有纪律的 wiki 维护者"的关键
```

---

## 与 wiki 系统的关系

```
wiki/                    ← 知识源
    │
    ▼
knowledge-recall.md      ← 召回模块（本文件）
    │
    ▼
huage-agent SKILL.md     ← 注入到创作上下文
    │
    ▼
huage-gzh / huage888     ← 创作 Skill 使用知识
```

---

## 注意事项

1. **不修改 wiki 内容**：召回是只读操作，不会修改 wiki 页面
2. **遵守 wiki-schema.md**：召回的页面格式应符合 wiki-schema.md 规范
3. **召回后验证**：如果召回的内容与主题无关，应过滤掉
4. **用户可见**：召回结果应向用户展示，增强可信度
