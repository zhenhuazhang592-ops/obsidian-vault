---
name: huage-agent
description: 华哥创作智能体统一入口。Routing 模式：识别意图 → 路由到专业 Skill + 知识预注入 + 会话归档。触发词：华哥、帮我写、创作、写公众号、做短剧、摄入、wiki。当用户提到任何创作、知识管理、学习进化相关的需求时使用。
---

# 华哥创作智能体 · huage-agent

> 统一入口 + 知识驱动 + 自我进化
> 核心理念：huage Agent + Obsidian + LLM-Wiki = 知识复利增长的创作 Agent
> 触发词：`华哥`、`帮我写`、`创作`、`写公众号`、`做短剧`、`摄入`、`wiki`

---

## 激活条件

当用户的请求涉及以下任一场景时，激活本 Skill：

1. **创作类**：写公众号、做短剧、写文章、生成内容
2. **知识管理类**：摄入来源、查询 wiki、检查 wiki 健康
3. **学习进化类**：提取模式、进化本能、查看用户画像
4. **记忆搜索类**：上次我们、之前做过、记得吗
5. **直接称呼**：华哥（作为通用入口触发）

---

## 路由表

| 意图关键词 | 路由目标 | 说明 |
|-----------|---------|------|
| 公众号 / 写文章 / gzh | `huage-gzh` | 公众号全链路写作 |
| 短剧 / 视频 / huage888 | `huage888` | 短剧预生产编排 |
| 摄入 / ingest / raw/ | `/wiki-ingest` | 源文件摄入 wiki |
| 查询 / wiki / 知识库 | `/wiki-query` | 查询 wiki 知识 |
| 检查 / lint / 健康 | `/wiki-lint` | Wiki 健康检查 |
| 图谱 / graph | `/wiki-graph` | 知识图谱 |
| 提取模式 / learn | `/learn` | 提取创作模式到本能库 |
| 进化 / evolve | `/evolve` | 本能进化检查 |
| 用户画像 / profile | `/user-profile` | 查看用户建模 |
| 上次 / 之前 / 记得 | `/session-search` | 跨会话记忆搜索 |
| 其他 | 直接处理 | 无匹配路由时自行处理 |

---

## 核心工作流

### Step 1：意图识别

从用户输入中提取意图，匹配路由表。

**识别规则**：
- 精确匹配优先（"写公众号" → huage-gzh）
- 模糊匹配其次（"帮我写个东西" → 追问类型）
- 无匹配 → 直接处理

### Step 2：知识预注入（创作类任务必做）

**仅对创作类任务（huage-gzh、huage888）执行**：

1. 从用户请求中提取主题关键词
2. 执行 `knowledge-recall` 模块（见 `knowledge-recall.md`）
3. 将召回的 wiki 知识注入创作上下文

**输出格式**：
```
📚 Wiki 知识召回：
- [[概念名]]：摘要...
- [[实体名]]：关键事实...
```

### Step 3：路由执行

调用匹配的专业 Skill 或命令，将知识注入结果作为额外上下文传入。

### Step 4：会话归档

任务完成后（创作类任务），执行：

1. **更新 MEMORY.md 仪表盘**：记录完成的任务、下一步、阻塞点
2. **提议回流**（创作完成后）：检测创作输出中是否有值得回流 wiki 的知识
   - 提示："创作完成！检测到可回流知识 [具体描述]，是否 ingest 到 wiki？"
3. **提议提取模式**（如果发现可复用模式）：
   - 提示："检测到可提取的创作模式 [具体描述]，运行 /learn 保存？"

---

## 知识闭环示意

```
         ┌──────────────────────────────┐
         │      wiki/ 知识库             │
         │  sources/ entities/ concepts/ │
         └──────────┬───────────────────┘
                    │
        知识预注入  │  创作回流
         (Step 2)  │  (Step 4)
            ┌──────┴──────┐
            │  huage-agent │
            │  (路由层)     │
            └──────┬──────┘
                   │
         ┌─────────┼─────────┐
         ▼         ▼         ▼
    huage-gzh  huage888   其他创作
    (公众号)   (短剧)      Skill
```

---

## 与 Obsidian 的协作

huage-agent 在 Obsidian Vault 中运行：

- **左 Obsidian**：用户在 Obsidian 中浏览 wiki、编辑笔记
- **右 huage-agent**：在 Claude Code 中执行创作、知识管理、学习进化
- **双向同步**：wiki 页面更新后 Obsidian 实时可见，Obsidian 中的 raw/ 文件可被 agent 摄入

---

## 技术依赖

| 依赖 | 用途 | 来源 |
|------|------|------|
| huage-gzh | 公众号写作 | `.claude/skills/huage-gzh/` |
| huage888 | 短剧编排 | `.claude/skills/huage888/` |
| wiki 命令 | 知识管理 | `.claude/commands/wiki-*.md` |
| /learn | 模式提取 | `.claude/commands/learn.md` |
| /evolve | 本能进化 | `.claude/commands/evolve.md` |
| wiki/ | 知识库 | `wiki/` 目录 |
| MEMORY.md | 会话状态 | `.claude/projects/.../memory/MEMORY.md` |

---

## 质量门控

- **知识预注入**：创作类任务必须执行，不可跳过
- **路由准确率**：意图识别后向用户确认路由目标
- **回流提议**：创作完成后必须检查是否有可回流知识
