# WeChat Master Agent 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个 5-Agent 编排系统（纯 Claude Code Skill），从选题研究到微信草稿箱推送的全链路自动化公众号内容生产。

**Architecture:** Master Orchestrator 通过 Claude Code 的 Agent tool 调度 5 个独立子 Agent（研究/创作/质检/视觉/发布），状态机驱动流程，5 个 Gate 节点由用户确认。Python 脚本负责排版引擎和微信 API 交互。

**Tech Stack:** Claude Code Skill（Markdown prompt 文件）+ Python 3.10+（markdown / BeautifulSoup4 / cssutils / Pygments / Pillow / requests / PyYAML）+ baoyu-article-illustrator + baoyu-cover-image

**Design Doc:** `docs/plans/2026-03-29-wechat-master-agent-design.md`

**Source Materials（已研究，可直接复用）：**
- gongzhonghao skill v2.5: `~/.claude/skills/gongzhonghao/`
- ArticleSkill: `01-输出内容/公众号/工具研究/ArticleSkill/`
- avoid-ai-writing: `01-输出内容/公众号/工具研究/avoid-ai-writing/`
- WeWrite: `01-输出内容/公众号/工具研究/wewrite/`

---

## Phase 1: 骨架搭建（Skill 目录 + Master Orchestrator）

### Task 1: 创建 Skill 目录结构

**Files:**
- Create: `~/.claude/skills/wechat-master/SKILL.md`
- Create: `~/.claude/skills/wechat-master/manifest.json`
- Create: `~/.claude/skills/wechat-master/agents/` (empty dir)
- Create: `~/.claude/skills/wechat-master/prompts/` (empty dir)
- Create: `~/.claude/skills/wechat-master/themes/` (empty dir)
- Create: `~/.claude/skills/wechat-master/scripts/` (empty dir)
- Create: `~/.claude/skills/wechat-master/references/` (empty dir)

**Step 1: 创建目录结构**

```bash
mkdir -p ~/.claude/skills/wechat-master/{agents,prompts,themes,scripts,references}
```

**Step 2: 创建 manifest.json**

```json
{
  "name": "wechat-master",
  "version": "1.0.0",
  "description": "5-Agent 公众号内容生产系统",
  "commands": {
    "write": {
      "description": "完整流程：选题→写作→质检→配图→发布",
      "modules": ["style-loader", "research-agent", "writing-agent", "qa-agent", "visual-agent", "publish-agent"],
      "gates": ["style_config", "topic_select", "title_select", "outline_confirm", "publish_confirm"]
    },
    "topic": {
      "description": "仅选题研究",
      "modules": ["style-loader", "research-agent"]
    },
    "title": {
      "description": "仅标题生成",
      "modules": ["writing-agent"]
    },
    "qa": {
      "description": "仅质检（去AI味+评分）",
      "modules": ["qa-agent"]
    },
    "publish": {
      "description": "仅排版+发布",
      "modules": ["publish-agent"]
    },
    "review": {
      "description": "数据回收+复盘",
      "modules": ["review"]
    },
    "style": {
      "description": "配置/修改风格",
      "modules": ["style-loader"]
    }
  },
  "agents": {
    "research": {"prompt": "agents/research-agent.md", "tools": ["WebSearch", "Grep", "Glob"]},
    "writing": {"prompt": "agents/writing-agent.md", "tools": ["Write", "Read"]},
    "qa": {"prompt": "agents/qa-agent.md", "tools": ["Read", "Edit"]},
    "visual": {"prompt": "agents/visual-agent.md", "tools": ["Skill"]},
    "publish": {"prompt": "agents/publish-agent.md", "tools": ["Bash", "Write", "Read"]}
  },
  "state_schema": {
    "topic": "string",
    "style_config": "object",
    "selected_topic": "object",
    "selected_title": "string",
    "outline": "array",
    "keywords": "object",
    "article_path": "string",
    "qa_score": "number",
    "cover_path": "string",
    "html_path": "string",
    "draft_media_id": "string"
  },
  "token_budget": {
    "skill_docs": 3000,
    "working_space": 7000,
    "max": 10000
  }
}
```

**Step 3: 创建 SKILL.md（Master Orchestrator）**

SKILL.md 是入口文件，负责命令路由和状态机控制。内容见 Task 2。

**Step 4: 验证目录结构**

```bash
find ~/.claude/skills/wechat-master -type f -o -type d | sort
```

Expected: 所有目录和 manifest.json 存在。

**Step 5: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/manifest.json && git commit -m "feat(wechat-master): init skill directory structure"
```

---

### Task 2: 编写 Master Orchestrator（SKILL.md）

**Files:**
- Create: `~/.claude/skills/wechat-master/SKILL.md`

**Step 1: 编写 SKILL.md**

SKILL.md 核心职责：
1. 命令路由（解析 `/wechat-master <command> <args>`）
2. 状态机控制（按状态推进 Agent 调度）
3. Gate 管理（5 个用户确认节点）
4. Agent 调度（通过 Agent tool 派发子 Agent）

```markdown
---
name: wechat-master
description: 5-Agent 公众号内容生产系统。Master Orchestrator 调度研究/创作/质检/视觉/发布 5 个 Agent，全链路生产高质量公众号文章并推送草稿箱。
---

# WeChat Master Agent

## 命令路由

| 命令 | 说明 |
|------|------|
| `/wechat-master write "主题"` | 完整流程 |
| `/wechat-master topic "主题"` | 仅选题研究 |
| `/wechat-master title "选题"` | 仅标题生成 |
| `/wechat-master qa <文章路径>` | 仅质检 |
| `/wechat-master publish <文章路径>` | 仅排版+发布 |
| `/wechat-master review` | 数据回收+复盘 |
| `/wechat-master style` | 配置风格 |

## 状态机

完整流程（write 命令）按以下状态推进，上一步未完成不得进入下一步：

```
INIT → STYLE_CONFIG ★ → RESEARCH ★ → TITLE_SELECT ★ → OUTLINE_CONFIRM ★ → WRITING → QA_R1 → QA_R2 → VISUAL → PUBLISH ★ → DONE
```

★ = 用户确认 Gate，必须等用户响应。

## 执行流程

### Step 0: 风格配置（STYLE_CONFIG）

在 Master 内完成，不派发 Agent。用 AskUserQuestion 一次性确认 6 项：

| 参数 | 选项 |
|------|------|
| 亲和力 | 强 / 中 / 弱 |
| 专业度 | 高 / 中 / 低 |
| 叙事风格 | 干货型 / 故事型 / 观点型 / 混合型 |
| 开头方式 | 数据 / 故事 / 问题 / 观点 / 场景 |
| 语气偏好 | 朋友聊天 / 专家分析 / 轻松幽默 |
| 段落长度 | 短（1-3行）/ 中（3-5行）/ 长（5行+）|

用户确认后生成 StyleConfig 对象，传递给后续 Agent。

### Step 1: 研究 Agent（RESEARCH）

<!-- [SECTION-START: research-dispatch] -->

**派发方式**：通过 Agent tool 启动子 Agent。

```
Agent tool 参数:
- prompt: 读取 agents/research-agent.md 的完整内容 + 注入 StyleConfig + 主题关键词
- subagent_type: general-purpose
```

**输入注入**：
- 主题关键词: `{topic}`
- StyleConfig: `{style_config}`

**输出期望**：3 个选题卡（TopicCard），格式见 prompts/topic-card-template.md

**Gate**: 用 AskUserQuestion 让用户从 3 个选题卡中选 1 个。

<!-- [SECTION-END: research-dispatch] -->

### Step 2: 创作 Agent（TITLE_SELECT → OUTLINE_CONFIRM → WRITING）

<!-- [SECTION-START: writing-dispatch] -->

创作 Agent 内部有 3 个子阶段，其中 2 个需要 Gate。

**派发方式**：通过 Agent tool 启动子 Agent。

```
Agent tool 参数:
- prompt: 读取 agents/writing-agent.md + 注入选定 TopicCard + StyleConfig + Keywords
- subagent_type: general-purpose
```

**注意**：创作 Agent 内部的标题选择和大纲确认需要 Agent 返回中间结果，Master 通过 AskUserQuestion 获取用户确认后，再次调用 Agent 继续（或用 SendMessage 继续同一 Agent）。

**实际执行**：
1. 第一轮调用 → Agent 返回 4 个标题 + 评分卡
2. Master 用 AskUserQuestion → 用户选标题
3. 第二轮调用（SendMessage）→ Agent 返回大纲
4. Master 用 AskUserQuestion → 用户确认大纲
5. 第三轮调用（SendMessage）→ Agent 返回完整文章
6. Master 获取 article_path

<!-- [SECTION-END: writing-dispatch] -->

### Step 3: 质检 Agent（QA_R1 → QA_R2）

<!-- [SECTION-START: qa-dispatch] -->

**派发方式**：通过 Agent tool 启动子 Agent。

```
Agent tool 参数:
- prompt: 读取 agents/qa-agent.md + 注入 article_path
- subagent_type: general-purpose
```

**输出期望**：修复后的文章 + 评分卡（5维度各20分，总分100）

**Gate**: 总分 < 60 → 自动退回创作 Agent（附修改指令），用户无需干预。总分 >= 60 → 继续。

<!-- [SECTION-END: qa-dispatch] -->

### Step 4: 视觉 Agent（VISUAL）

<!-- [SECTION-START: visual-dispatch] -->

**派发方式**：通过 Agent tool 启动子 Agent。

```
Agent tool 参数:
- prompt: 读取 agents/visual-agent.md + 注入 article_path
- subagent_type: general-purpose
```

视觉 Agent 内部调用两个 Skill：
1. `baoyu-article-illustrator`（章节配图）
2. `baoyu-cover-image`（封面图）

**输出期望**：配图路径列表 + 封面图路径

**降级**：图片生成失败 → 占位图 + 提示用户手动配图。不阻塞流程。

<!-- [SECTION-END: visual-dispatch] -->

### Step 5: 发布 Agent（PUBLISH）

<!-- [SECTION-START: publish-dispatch] -->

**派发方式**：通过 Agent tool 启动子 Agent。

```
Agent tool 参数:
- prompt: 读取 agents/publish-agent.md + 注入 article_path + cover_path + illustrations
- subagent_type: general-purpose
```

发布 Agent 执行：
1. 调用 `scripts/converter.py` 排版（Markdown → 微信 HTML）
2. 保存到 Obsidian vault
3. Gate ★: 返回 Master，Master 用 AskUserQuestion 确认是否推送
4. 用户确认 → 调用 `scripts/publisher.py` 推送草稿箱

**输出期望**：HTML 路径 + 草稿预览链接

<!-- [SECTION-END: publish-dispatch] -->

### Step 6: 数据闭环（review 命令单独触发）

通过 `/wechat-master review` 手动触发，不在 write 流程内。
读取微信后台数据 → 生成复盘卡 → 保存到 Obsidian vault。

## 错误处理

| 场景 | 处理 |
|------|------|
| Agent 调用失败 | 重试 1 次 → 仍失败告知用户 |
| 质检不通过（<60分）| 退回创作 Agent，最多重试 2 次 |
| 图片生成失败 | 占位图 + 提示手动配图 |
| 微信 API 失败 | 显示错误码 + 建议检查配置 |
| 用户取消 Gate | 终止流程，保存当前进度 |
```

**Step 2: 验证 SKILL.md 行数**

```bash
wc -l ~/.claude/skills/wechat-master/SKILL.md
```

Expected: < 200 行（符合 progressive-disclosure 规则）

**Step 3: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/SKILL.md && git commit -m "feat(wechat-master): master orchestrator with state machine and agent dispatch"
```

---

## Phase 2: 5 个 Agent Prompt 文件

### Task 3: 研究 Agent Prompt

**Files:**
- Create: `~/.claude/skills/wechat-master/agents/research-agent.md`
- Create: `~/.claude/skills/wechat-master/prompts/topic-card-template.md`

**Reference:**
- `~/.claude/skills/gongzhonghao/topic-research.md`（两阶段研究 + Gate 机制）
- `01-输出内容/公众号/工具研究/wewrite/选题评估规则.md`（三维度评分）

**Step 1: 创建选题卡模板 prompts/topic-card-template.md**

```markdown
# 选题卡模板

每个选题卡必须包含以下字段：

## 选题卡 N: {topic}

**切入角度**: {angle}
**目标读者**: {target_reader}
**核心观点**: {core_argument}（一句话）

**竞品参考**:
| 标题 | 来源 | 亮点 |
|------|------|------|
| {title} | {source} | {highlights} |

**关键词策略**:
- 核心词: {core_keywords}
- 长尾词: {long_tail_keywords}

**知识库素材**: {vault_refs}

**选题评分**: {score}/100
- 热度: {heat}/40
- 差异化: {diff}/30
- 知识储备: {knowledge}/30
```

**Step 2: 创建 agents/research-agent.md**

研究 Agent 的完整 Prompt。核心逻辑：
1. 阶段 A: 知识库检索（Grep/Glob 搜 Obsidian vault）
2. 阶段 B: 热点竞品分析（WebSearch 搜微博/头条/公众号/小红书）
3. 阶段 C: 输出 3 个选题卡

复用 gongzhonghao 的同义词扩展、竞品搜索策略、三维度评分。

Agent Prompt 要点：
- 明确输入格式（主题 + StyleConfig）
- 同义词扩展必须执行
- WebSearch 失败时降级为手动输入
- 输出严格按 topic-card-template.md 格式
- 评分规则：热度（40分）× 差异化（30分）× 知识储备（30分）

**Step 3: 验证文件存在**

```bash
cat ~/.claude/skills/wechat-master/agents/research-agent.md | head -5
cat ~/.claude/skills/wechat-master/prompts/topic-card-template.md | head -5
```

**Step 4: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/agents/research-agent.md skills/wechat-master/prompts/topic-card-template.md && git commit -m "feat(wechat-master): research agent prompt + topic card template"
```

---

### Task 4: 创作 Agent Prompt

**Files:**
- Create: `~/.claude/skills/wechat-master/agents/writing-agent.md`
- Create: `~/.claude/skills/wechat-master/prompts/title-scoring.md`
- Create: `~/.claude/skills/wechat-master/prompts/outline-template.md`

**Reference:**
- `~/.claude/skills/gongzhonghao/title-scoring.md`（5维度×10分评分 + A/B测试）
- `~/.claude/skills/gongzhonghao/prompts/outline-template.md`（五种框架 + 字数分配）
- `01-输出内容/公众号/工具研究/ArticleSkill/公众号爆款写作.md`（4种标题公式 + 3种文章结构）
- `~/.claude/skills/gongzhonghao/author-config.md`（风格配置 schema）

**Step 1: 创建 prompts/title-scoring.md**

复用 gongzhonghao 的 5 维度评分体系 + ArticleSkill 的 4 种标题公式：
- 8 种标题类型：冲突对比 / 疑问引导 / 数字效果 / 否定反转 / 悬念 / 情绪 / 盘点 / 蹭热点
- 5 维度评分（各 10 分）：打开欲望 / 意外感 / 受众明确度 / 传播潜力 / SEO 友好度
- A/B 测试：A 版（情绪钩子型）× 2 + B 版（干货信任型）× 2
- 标题检查清单 6 项

**Step 2: 创建 prompts/outline-template.md**

复用 gongzhonghao 的五种大纲框架 + ArticleSkill 的结构模板：
- 五种框架：干货教程 / 观点输出 / 故事叙事 / 热点解读 / 产品测评
- 每种框架的字数分配方案
- Hook 设计四选一
- 互动设计模块（文末话术 + 评论区运营）
- 大纲检查清单 8 项

**Step 3: 创建 agents/writing-agent.md**

创作 Agent Prompt 要点：
- 输入：选定 TopicCard + StyleConfig + Keywords
- 三阶段执行：标题（返回等用户选）→ 大纲（返回等用户确认）→ 正文
- 标题生成调用 prompts/title-scoring.md 规则
- 大纲生成调用 prompts/outline-template.md 规则
- 正文写作：按 StyleConfig 风格 + 大纲结构 + SEO 关键词嵌入
- 金句植入规则（每 500 字至少 1 句）
- 总字数 2000-3500 字
- 输出：完整 Markdown 文章（含 frontmatter），保存到 Obsidian vault

**Step 4: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/agents/writing-agent.md skills/wechat-master/prompts/title-scoring.md skills/wechat-master/prompts/outline-template.md && git commit -m "feat(wechat-master): writing agent + title scoring + outline template"
```

---

### Task 5: 质检 Agent Prompt

**Files:**
- Create: `~/.claude/skills/wechat-master/agents/qa-agent.md`
- Create: `~/.claude/skills/wechat-master/prompts/humanizer-rules.md`

**Reference:**
- `~/.claude/skills/gongzhonghao/humanizer-rules.md`（P0/P1/P2 三级分类 + 两轮审计）
- `01-输出内容/公众号/工具研究/avoid-ai-writing/SKILL.md`（36类模式 + 109词替换表）
- `~/.claude/rules/ai-taste.md`（华哥的 AI 品味规则）

**Step 1: 创建 prompts/humanizer-rules.md**

融合三个来源的去 AI 味规则，中文本地化版：

**P0（可信度杀手，立即修复）**：
1. 模糊归因（"研究表明"无来源 → 删除或补来源）
2. 虚假权威（"专家建议"无具体人 → 删除或补人名）
3. AI 协作痕迹（"作为 AI" → 删除）
4. 日期免责声明 → 删除
5. Cutoff disclaimers → 删除

**P1（明显 AI 味，发布前修复）**：
1. 过渡词滥用：首先/其次/此外/综上所述/值得注意的是/从某种意义上来说
2. 填充词：非常/极其/相当/非常重要/非常优秀
3. 句式单一：连续 3 句以上相同结构开头
4. "这"字开头连续出现
5. "的"字结构连续超 8 字无标点
6. 感叹句过多（>1/200字）
7. 格式化过度：emoji>3/千字 或 加粗>5/千字
8. 三段式法则（"有三个原因..."）
9. 破折号过度（每段超 1 次）
10. 同义词循环（同段同实体不同叫法 >2 次）

**P2（风格优化）**：
1. 节奏均匀（>80% 句子 15-22 字 → 加入短句和长句变化）
2. 段落长度均匀度
3. 朗读测试

**109 词中文替换表**（高频前 30 个）：
| 替换 | ← 原词 |
|------|--------|
| 删除 | 非常 |
| 删除 | 极其 |
| 删除 | 相当 |
| 具体说 | 很好/很重要 |
| 直接用动词 | 能够/进行/予以 |
| 而且/不过 | 此外 |
| 但 | 然而 |
| 并且 | 与此同时 |
| 直接说 | 综上所述/总的来说 |
| 说具体的 | 因素/情况/问题/作用 |

**评分卡（5 维度 × 20 分 = 100 分）**：

| 维度 | 满分 | 评分标准 |
|------|------|---------|
| 自然度 | 20 | P0 问题 0 个(10分) + P1 问题 ≤3 个(10分) |
| 可读性 | 20 | 句式变化(10分) + 节奏感(10分) |
| 信息密度 | 20 | 干货比例 >60%(10分) + 无水分段落(10分) |
| 故事性 | 20 | 有场景/案例(10分) + 有人物/细节(10分) |
| 传播力 | 20 | 金句 ≥3 个(10分) + 情绪触发点 ≥2 个(10分) |

**Step 2: 创建 agents/qa-agent.md**

质检 Agent Prompt 要点：
- 输入：article_path
- 两轮执行：R1（P0+P1 修复 + 节奏检查）→ R2（残留检测 + 评分卡）
- 读取 prompts/humanizer-rules.md 规则
- 直接用 Edit tool 修改文章
- 输出：修复后文章 + 评分卡 + FixReport 摘要
- 评分 < 60 → 明确告知 Master 需退回重写

**Step 3: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/agents/qa-agent.md skills/wechat-master/prompts/humanizer-rules.md && git commit -m "feat(wechat-master): qa agent + humanizer rules (36 patterns + 109 words CN)"
```

---

### Task 6: 视觉 Agent Prompt

**Files:**
- Create: `~/.claude/skills/wechat-master/agents/visual-agent.md`

**Reference:**
- `~/.claude/skills/baoyu-article-illustrator/SKILL.md`
- `~/.claude/skills/baoyu-cover-image/SKILL.md`

**Step 1: 创建 agents/visual-agent.md**

视觉 Agent Prompt 要点：
- 输入：article_path
- 两步执行：
  1. 调用 Skill tool → `baoyu-article-illustrator`（章节配图）
     - 参数：article_path + `--type auto` + `--style auto` + density balanced
     - 约束：相邻配图间隔 >= 300 字，不在开头和 CTA 处放图
  2. 调用 Skill tool → `baoyu-cover-image`（封面图）
     - 参数：article_path + `--aspect 16:9` + `--text title-only`
     - 约束：无写实人物、留白 40-60%
- EXTEND.md 检查：首次使用需初始化
- 降级策略：API 失败重试 1 次 → 仍失败用占位图
- 输出：illustrations 路径列表 + cover_path

**Step 2: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/agents/visual-agent.md && git commit -m "feat(wechat-master): visual agent (baoyu-article-illustrator + baoyu-cover-image)"
```

---

### Task 7: 发布 Agent Prompt

**Files:**
- Create: `~/.claude/skills/wechat-master/agents/publish-agent.md`

**Reference:**
- `~/.claude/skills/gongzhonghao/md2html.md`（排版规则）
- `~/.claude/skills/gongzhonghao/publish-command.md`（发布流程）

**Step 1: 创建 agents/publish-agent.md**

发布 Agent Prompt 要点：
- 输入：article_path + cover_path + illustrations 列表
- 四步执行：
  1. 排版：调用 `python3 scripts/converter.py --input {article_path} --theme {theme} --output {html_path}`
  2. 保存到 Obsidian: 复制文章到 `01-输出内容/公众号/已发布/YYYY-MM-DD-标题.md`
  3. 返回 Master 等用户确认推送
  4. 推送：调用 `python3 scripts/publisher.py --html {html_path} --cover {cover_path} --title {title} --author {author} --digest {digest}`
- 输出：html_path + draft_media_id + draft_url

**Step 2: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/agents/publish-agent.md && git commit -m "feat(wechat-master): publish agent (converter + wechat api)"
```

---

## Phase 3: Python 排版引擎（TDD）

### Task 8: 安装 Python 依赖

**Files:**
- Create: `~/.claude/skills/wechat-master/scripts/requirements.txt`

**Step 1: 创建 requirements.txt**

```
markdown>=3.5
beautifulsoup4>=4.12
cssutils>=2.9
Pygments>=2.15
Pillow>=10.0
requests>=2.31
PyYAML>=6.0
```

**Step 2: 安装依赖**

```bash
pip3 install -r ~/.claude/skills/wechat-master/scripts/requirements.txt
```

**Step 3: 验证安装**

```bash
python3 -c "import markdown, bs4, cssutils, pygments, PIL, requests, yaml; print('All deps OK')"
```

Expected: `All deps OK`

**Step 4: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/scripts/requirements.txt && git commit -m "feat(wechat-master): python dependencies for converter and publisher"
```

---

### Task 9: 创建排版主题（YAML）

**Files:**
- Create: `~/.claude/skills/wechat-master/themes/professional-clean.yaml`
- Create: `~/.claude/skills/wechat-master/themes/tech-modern.yaml`
- Create: `~/.claude/skills/wechat-master/themes/warm-editorial.yaml`
- Create: `~/.claude/skills/wechat-master/themes/minimal.yaml`

**Reference:**
- `01-输出内容/公众号/工具研究/wewrite/排版主题系统.md`（YAML schema + 4套预置主题）
- `~/.claude/skills/gongzhonghao/md2html.md`（华哥的排版规范：#d4881c 强调色、17px 正文）

**Step 1: 创建 professional-clean.yaml**

以 WeWrite 的 professional-clean 为基础，融入华哥的排版偏好（#d4881c 强调色）。

YAML schema：
```yaml
name: "主题名"
description: "一行描述"
colors:
  primary: "#hex"
  secondary: "#hex"
  text: "#hex"
  text_light: "#hex"
  background: "#hex"
  code_bg: "#hex"
  code_color: "#hex"
  quote_border: "#hex"
  quote_bg: "#hex"
  border_radius: "Npx"
base_css: |
  body { ... }
  h1 { ... }
  ...
```

每个主题覆盖 20+ 选择器：body, h1-h4, p, strong, em, code, pre, pre code, blockquote, blockquote p, ul, ol, li, table, thead, th, td, tr, img, a, hr。

微信适配硬约束（所有主题必须遵守）：
- font-size >= 15px
- 不用 position:fixed/sticky, transform, animation, filter
- 颜色用 #hex
- img max-width: 100%
- max-width: 680px（或 720px）

**Step 2: 创建其余 3 个主题文件**

- tech-modern.yaml: 紫蓝渐变，primary #7c3aed
- warm-editorial.yaml: 暖橙，primary #d97706
- minimal.yaml: 黑白极简，primary #1a1a1a

**Step 3: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/themes/*.yaml && git commit -m "feat(wechat-master): 4 YAML themes for wechat html formatting"
```

---

### Task 10: 排版引擎 theme.py（主题加载 + CSS 解析）

**Files:**
- Create: `~/.claude/skills/wechat-master/scripts/theme.py`
- Create: `~/.claude/skills/wechat-master/scripts/test_theme.py`

**Reference:**
- WeWrite `toolkit/theme.py` 的函数签名和逻辑（load_theme / get_inline_css_rules / _resolve_css_variables / _is_simple_selector）

**Step 1: 写测试 test_theme.py**

```python
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from theme import load_theme, list_themes, get_inline_css_rules

THEMES_DIR = os.path.join(os.path.dirname(__file__), "..", "themes")


def test_list_themes_returns_four():
    themes = list_themes(THEMES_DIR)
    assert len(themes) == 4
    assert "professional-clean" in themes


def test_load_theme_returns_dataclass():
    theme = load_theme("professional-clean", THEMES_DIR)
    assert theme.name == "professional-clean"
    assert "primary" in theme.colors
    assert len(theme.base_css) > 100


def test_load_theme_missing_raises():
    with pytest.raises(FileNotFoundError):
        load_theme("nonexistent", THEMES_DIR)


def test_get_inline_css_rules_has_body():
    theme = load_theme("professional-clean", THEMES_DIR)
    rules = get_inline_css_rules(theme)
    assert "body" in rules
    assert "font-size" in rules["body"]


def test_css_variable_replacement():
    from theme import Theme, get_inline_css_rules
    t = Theme(
        name="test",
        description="test",
        base_css="p { color: var(--primary); }",
        colors={"primary": "#ff0000"},
    )
    rules = get_inline_css_rules(t)
    assert rules["p"]["color"] == "#ff0000"


def test_complex_selectors_filtered():
    from theme import Theme, get_inline_css_rules
    t = Theme(
        name="test",
        description="test",
        base_css="p:hover { color: red; } p { color: blue; }",
        colors={},
    )
    rules = get_inline_css_rules(t)
    assert "p:hover" not in rules
    assert "p" in rules
```

**Step 2: 运行测试确认失败**

```bash
cd ~/.claude/skills/wechat-master/scripts && python3 -m pytest test_theme.py -v
```

Expected: FAIL（theme.py 不存在）

**Step 3: 实现 theme.py**

```python
"""主题加载与 CSS 解析模块。

读取 YAML 主题文件，解析 CSS 为 {selector: {property: value}} 字典，
供 converter.py 注入 HTML 内联样式。
"""
import logging
import os
import re
from dataclasses import dataclass, field

import cssutils
import yaml

cssutils.log.setLevel(logging.CRITICAL)


@dataclass
class Theme:
    name: str
    description: str
    base_css: str
    colors: dict = field(default_factory=dict)


def _default_themes_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "themes")


def load_theme(name: str, themes_dir: str | None = None) -> Theme:
    themes_dir = themes_dir or _default_themes_dir()
    for ext in (".yaml", ".yml"):
        path = os.path.join(themes_dir, f"{name}{ext}")
        if os.path.isfile(path):
            break
    else:
        raise FileNotFoundError(f"Theme '{name}' not found in {themes_dir}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for key in ("name", "description", "base_css", "colors"):
        if key not in data:
            raise ValueError(f"Theme '{name}' missing required field: {key}")

    return Theme(
        name=data["name"],
        description=data["description"],
        base_css=data["base_css"],
        colors=data.get("colors", {}),
    )


def list_themes(themes_dir: str | None = None) -> list[str]:
    themes_dir = themes_dir or _default_themes_dir()
    names = []
    for f in sorted(os.listdir(themes_dir)):
        if f.endswith((".yaml", ".yml")):
            names.append(f.rsplit(".", 1)[0])
    return names


def _resolve_css_variables(css_text: str, colors: dict) -> str:
    def replacer(match):
        var_name = match.group(1)
        key = var_name.lstrip("-")
        if key in colors:
            return colors[key]
        key_underscore = key.replace("-", "_")
        if key_underscore in colors:
            return colors[key_underscore]
        return match.group(0)

    return re.sub(r"var\(\s*--([a-zA-Z0-9_-]+)\s*\)", replacer, css_text)


def _is_simple_selector(selector: str) -> bool:
    for char in (":","@",">","+","~","[","*"):
        if char in selector:
            return False
    return True


def get_inline_css_rules(theme: Theme) -> dict[str, dict[str, str]]:
    resolved = _resolve_css_variables(theme.base_css, theme.colors)
    sheet = cssutils.parseString(resolved, validate=False)
    rules: dict[str, dict[str, str]] = {}
    for rule in sheet:
        if rule.type != rule.STYLE_RULE:
            continue
        for selector in rule.selectorText.split(","):
            selector = selector.strip()
            if not _is_simple_selector(selector):
                continue
            if selector not in rules:
                rules[selector] = {}
            for prop in rule.style:
                rules[selector][prop.name] = prop.value
    return rules
```

**Step 4: 运行测试确认通过**

```bash
cd ~/.claude/skills/wechat-master/scripts && python3 -m pytest test_theme.py -v
```

Expected: 6 passed

**Step 5: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/scripts/theme.py skills/wechat-master/scripts/test_theme.py && git commit -m "feat(wechat-master): theme loader with CSS variable resolution and inline rules"
```

---

### Task 11: 排版引擎 converter.py（Markdown → 微信 HTML）

**Files:**
- Create: `~/.claude/skills/wechat-master/scripts/converter.py`
- Create: `~/.claude/skills/wechat-master/scripts/test_converter.py`

**Reference:**
- WeWrite `toolkit/converter.py` 的转换管线（markdown → BS4 → 内联样式注入）
- `~/.claude/skills/gongzhonghao/md2html.md`（微信排版规则）

**Step 1: 写测试 test_converter.py**

```python
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from converter import md_to_wechat_html

THEMES_DIR = os.path.join(os.path.dirname(__file__), "..", "themes")


def test_basic_paragraph():
    html = md_to_wechat_html("Hello world", theme_name="professional-clean", themes_dir=THEMES_DIR)
    assert "<p" in html
    assert "Hello world" in html
    assert "style=" in html


def test_heading_conversion():
    html = md_to_wechat_html("# Title\n\n## Subtitle", theme_name="professional-clean", themes_dir=THEMES_DIR)
    assert "<h1" in html
    assert "<h2" in html
    assert "Title" in html


def test_inline_styles_no_style_tag():
    html = md_to_wechat_html("**bold** text", theme_name="professional-clean", themes_dir=THEMES_DIR)
    assert "<style" not in html
    assert "style=" in html


def test_image_max_width():
    md = "![alt](https://example.com/img.png)"
    html = md_to_wechat_html(md, theme_name="professional-clean", themes_dir=THEMES_DIR)
    assert "max-width" in html


def test_blockquote():
    md = "> This is a quote"
    html = md_to_wechat_html(md, theme_name="professional-clean", themes_dir=THEMES_DIR)
    assert "<blockquote" in html
    assert "border-left" in html


def test_code_block_highlighted():
    md = "```python\nprint('hello')\n```"
    html = md_to_wechat_html(md, theme_name="professional-clean", themes_dir=THEMES_DIR)
    assert "highlight" in html or "print" in html


def test_no_script_tags():
    md = "Normal text"
    html = md_to_wechat_html(md, theme_name="professional-clean", themes_dir=THEMES_DIR)
    assert "<script" not in html


def test_frontmatter_stripped():
    md = "---\ntitle: Test\ntags: [test]\n---\n\nContent here"
    html = md_to_wechat_html(md, theme_name="professional-clean", themes_dir=THEMES_DIR)
    assert "Content here" in html
    assert "---" not in html
```

**Step 2: 运行测试确认失败**

```bash
cd ~/.claude/skills/wechat-master/scripts && python3 -m pytest test_converter.py -v
```

Expected: FAIL

**Step 3: 实现 converter.py**

核心函数 `md_to_wechat_html(md_text, theme_name, themes_dir)`:
1. 剥离 YAML frontmatter
2. `markdown.markdown()` 转 HTML（启用 tables, fenced_code, codehilite 扩展）
3. `BeautifulSoup` 解析 HTML
4. 加载主题 → `get_inline_css_rules()` 获取样式字典
5. 遍历 DOM 所有元素，匹配选择器 → 注入 `style` 属性
6. 处理后代选择器（如 `pre code`、`blockquote p`）
7. 清理 `<script>` 标签
8. 输出纯内联样式 HTML 字符串

CLI 入口：
```bash
python3 converter.py --input article.md --theme professional-clean --output output.html
```

**Step 4: 运行测试确认通过**

```bash
cd ~/.claude/skills/wechat-master/scripts && python3 -m pytest test_converter.py -v
```

Expected: 8 passed

**Step 5: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/scripts/converter.py skills/wechat-master/scripts/test_converter.py && git commit -m "feat(wechat-master): markdown to wechat html converter with inline styles"
```

---

## Phase 4: 微信 API + 发布

### Task 12: 微信 API 封装 wechat_api.py

**Files:**
- Create: `~/.claude/skills/wechat-master/scripts/wechat_api.py`
- Create: `~/.claude/skills/wechat-master/scripts/test_wechat_api.py`
- Create: `~/.claude/skills/wechat-master/scripts/config.example.sh`

**Reference:**
- `~/.claude/skills/gongzhonghao/wechat-api.md`（3 个 API 端点）
- `~/.claude/skills/gongzhonghao/scripts/publish-draft.sh`（token 缓存 + 错误处理）

**Step 1: 创建 config.example.sh**

```bash
#!/bin/bash
# 微信公众号 API 配置
# 复制为 config.sh 并填入真实值
# ⚠️ config.sh 已在 .gitignore 中，不会被提交

export WECHAT_APPID="your_appid_here"
export WECHAT_APPSECRET="your_appsecret_here"
export WECHAT_AUTHOR="华哥"
```

**Step 2: 写测试 test_wechat_api.py**

```python
import os
import sys
import json
import time
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from wechat_api import WeChatAPI, TokenCache


def test_token_cache_write_and_read(tmp_path):
    cache = TokenCache(str(tmp_path / "token.json"))
    cache.save("test_token_123", expires_in=7200)
    token = cache.load()
    assert token == "test_token_123"


def test_token_cache_expired(tmp_path):
    cache = TokenCache(str(tmp_path / "token.json"))
    cache.save("old_token", expires_in=0)
    time.sleep(0.1)
    token = cache.load()
    assert token is None


def test_wechat_api_init():
    api = WeChatAPI(appid="test", appsecret="test")
    assert api.appid == "test"


def test_compress_image_skips_small(tmp_path):
    from wechat_api import compress_image
    from PIL import Image
    img_path = str(tmp_path / "small.png")
    img = Image.new("RGB", (100, 100), "white")
    img.save(img_path)
    result = compress_image(img_path, max_bytes=2 * 1024 * 1024)
    assert os.path.getsize(result) < 2 * 1024 * 1024
```

**Step 3: 运行测试确认失败**

```bash
cd ~/.claude/skills/wechat-master/scripts && python3 -m pytest test_wechat_api.py -v
```

Expected: FAIL

**Step 4: 实现 wechat_api.py**

核心类和函数：

```python
class TokenCache:
    def __init__(self, cache_path): ...
    def save(self, token, expires_in): ...
    def load(self) -> str | None: ...

class WeChatAPI:
    def __init__(self, appid, appsecret): ...
    def get_access_token(self) -> str: ...
    def upload_image(self, image_path) -> str: ...        # 返回 media_url
    def upload_thumb(self, image_path) -> str: ...         # 返回 thumb_media_id
    def create_draft(self, title, content, thumb_media_id, author, digest) -> dict: ...

def compress_image(path, max_bytes=2*1024*1024) -> str: ...
```

API 端点：
- GET `https://api.weixin.qq.com/cgi-bin/token` → access_token
- POST `https://api.weixin.qq.com/cgi-bin/media/upload` → media_id / url
- POST `https://api.weixin.qq.com/cgi-bin/draft/add` → media_id

Token 缓存：JSON 文件，有效期 6900s（提前 5 分钟刷新）。
图片压缩：Pillow 压缩到 2MB 以内。
错误处理：40001（token 失效重获）/ 40164（IP 不在白名单）/ 40007（素材错误）。

**Step 5: 运行测试确认通过**

```bash
cd ~/.claude/skills/wechat-master/scripts && python3 -m pytest test_wechat_api.py -v
```

Expected: 4 passed

**Step 6: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/scripts/wechat_api.py skills/wechat-master/scripts/test_wechat_api.py skills/wechat-master/scripts/config.example.sh && git commit -m "feat(wechat-master): wechat api wrapper with token cache and image compression"
```

---

### Task 13: 发布编排 publisher.py

**Files:**
- Create: `~/.claude/skills/wechat-master/scripts/publisher.py`
- Create: `~/.claude/skills/wechat-master/scripts/test_publisher.py`

**Step 1: 写测试 test_publisher.py**

```python
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from publisher import replace_local_images, extract_images_from_html


def test_extract_images_from_html():
    html = '<p>text</p><img src="local/img1.png"><img src="https://remote.com/img2.png">'
    local, remote = extract_images_from_html(html)
    assert len(local) == 1
    assert local[0] == "local/img1.png"
    assert len(remote) == 1


def test_replace_local_images():
    html = '<img src="local/img1.png">'
    mapping = {"local/img1.png": "https://mmbiz.qpic.cn/uploaded.png"}
    result = replace_local_images(html, mapping)
    assert "https://mmbiz.qpic.cn/uploaded.png" in result
    assert "local/img1.png" not in result
```

**Step 2: 运行测试确认失败**

```bash
cd ~/.claude/skills/wechat-master/scripts && python3 -m pytest test_publisher.py -v
```

**Step 3: 实现 publisher.py**

核心函数：
```python
def extract_images_from_html(html: str) -> tuple[list[str], list[str]]: ...
def replace_local_images(html: str, mapping: dict[str, str]) -> str: ...
def publish(html_path: str, cover_path: str, title: str, author: str, digest: str) -> dict: ...
```

`publish()` 编排流程：
1. 读取 HTML
2. 提取本地图片列表
3. 上传封面 → thumb_media_id
4. 逐个上传内文图片 → {local_path: remote_url}
5. 替换 HTML 中图片 src
6. 创建草稿
7. 返回 {draft_media_id, draft_url}

CLI 入口：
```bash
python3 publisher.py --html output.html --cover cover.png --title "标题" --author "华哥" --digest "摘要"
```

**Step 4: 运行测试确认通过**

```bash
cd ~/.claude/skills/wechat-master/scripts && python3 -m pytest test_publisher.py -v
```

Expected: 2 passed

**Step 5: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/scripts/publisher.py skills/wechat-master/scripts/test_publisher.py && git commit -m "feat(wechat-master): publish orchestrator with image upload and draft creation"
```

---

## Phase 5: 参考资料 + 收尾

### Task 14: 参考资料文件

**Files:**
- Create: `~/.claude/skills/wechat-master/references/wechat-constraints.md`
- Create: `~/.claude/skills/wechat-master/references/writing-frameworks.md`
- Create: `~/.claude/skills/wechat-master/references/style-guide.md`
- Create: `~/.claude/skills/wechat-master/prompts/review-template.md`

**Step 1: 创建 wechat-constraints.md**

从 WeWrite `微信平台限制.md` 提取核心约束：
- CSS 支持/不支持列表
- 图片限制（10 张、5MB）
- 文章长度（20000 字）
- 移动端适配要求

**Step 2: 创建 writing-frameworks.md**

融合 ArticleSkill 的 3 种文章结构 + gongzhonghao 的 5 种大纲框架：
- 工具介绍型（2000-3000 字）
- 方法教程型（2000-2500 字）
- 深度思考型（2500-3500 字）
- 观点输出型
- 热点解读型
- 每种框架的字数分配、结构公式、情绪曲线

**Step 3: 创建 style-guide.md**

从 gongzhonghao `author-config.md` 提取风格指南：
- 人设标签系统（7 种预设）
- 写作偏好参数
- 禁忌词清单
- 网感词偏好
- 情绪表达参数

**Step 4: 创建 prompts/review-template.md**

复盘卡模板：
```markdown
# 复盘卡: {title}

**发布日期**: {date}
**数据采集日期**: {review_date}

## 核心数据
| 指标 | 数值 | 历史均值 | 趋势 |
|------|------|---------|------|
| 阅读数 | | | |
| 完读率 | | | |
| 点赞数 | | | |
| 转发数 | | | |
| 收藏数 | | | |
| 评论数 | | | |

## 标题 CTR
阅读数 / 粉丝数 = {ctr}%

## 互动率
(点赞+转发+收藏+评论) / 阅读数 = {engagement}%

## 分析
- 表现好的: ...
- 待改进的: ...

## 学习点
- 标题策略: ...
- 内容策略: ...
- 发布时间: ...
```

**Step 5: Commit**

```bash
cd ~/.claude && git add skills/wechat-master/references/ skills/wechat-master/prompts/review-template.md && git commit -m "feat(wechat-master): reference docs + review template"
```

---

### Task 15: EXTEND.md + .gitignore + 最终验证

**Files:**
- Create: `~/.claude/skills/wechat-master/EXTEND.md`
- Create: `~/.claude/skills/wechat-master/.gitignore`

**Step 1: 创建 EXTEND.md**

```markdown
# WeChat Master - 扩展配置

## 依赖的外部 Skill

| Skill | 用途 | 必须 |
|-------|------|------|
| baoyu-article-illustrator | 章节配图 | 是（视觉 Agent） |
| baoyu-cover-image | 封面图 | 是（视觉 Agent） |

## 环境变量

| 变量 | 用途 | 获取方式 |
|------|------|---------|
| DOUBAO_API_KEY | 图片生成 | 火山引擎控制台 |
| WECHAT_APPID | 微信API | 微信公众平台 |
| WECHAT_APPSECRET | 微信API | 微信公众平台 |

## 首次使用清单

1. 安装 Python 依赖: `pip3 install -r scripts/requirements.txt`
2. 复制配置: `cp scripts/config.example.sh scripts/config.sh` 并填入真实值
3. 配置微信 IP 白名单
4. 确认 baoyu skills 的 EXTEND.md 已初始化
5. 运行测试: `cd scripts && python3 -m pytest -v`
```

**Step 2: 创建 .gitignore**

```
scripts/config.sh
scripts/__pycache__/
scripts/.pytest_cache/
*.pyc
.wechat_token_cache
```

**Step 3: 运行全部测试**

```bash
cd ~/.claude/skills/wechat-master/scripts && python3 -m pytest -v
```

Expected: All tests passed

**Step 4: 验证完整目录结构**

```bash
find ~/.claude/skills/wechat-master -type f | sort
```

Expected output:
```
~/.claude/skills/wechat-master/.gitignore
~/.claude/skills/wechat-master/EXTEND.md
~/.claude/skills/wechat-master/SKILL.md
~/.claude/skills/wechat-master/manifest.json
~/.claude/skills/wechat-master/agents/publish-agent.md
~/.claude/skills/wechat-master/agents/qa-agent.md
~/.claude/skills/wechat-master/agents/research-agent.md
~/.claude/skills/wechat-master/agents/visual-agent.md
~/.claude/skills/wechat-master/agents/writing-agent.md
~/.claude/skills/wechat-master/prompts/humanizer-rules.md
~/.claude/skills/wechat-master/prompts/outline-template.md
~/.claude/skills/wechat-master/prompts/review-template.md
~/.claude/skills/wechat-master/prompts/title-scoring.md
~/.claude/skills/wechat-master/prompts/topic-card-template.md
~/.claude/skills/wechat-master/references/style-guide.md
~/.claude/skills/wechat-master/references/wechat-constraints.md
~/.claude/skills/wechat-master/references/writing-frameworks.md
~/.claude/skills/wechat-master/scripts/config.example.sh
~/.claude/skills/wechat-master/scripts/converter.py
~/.claude/skills/wechat-master/scripts/publisher.py
~/.claude/skills/wechat-master/scripts/requirements.txt
~/.claude/skills/wechat-master/scripts/test_converter.py
~/.claude/skills/wechat-master/scripts/test_publisher.py
~/.claude/skills/wechat-master/scripts/test_theme.py
~/.claude/skills/wechat-master/scripts/test_wechat_api.py
~/.claude/skills/wechat-master/scripts/theme.py
~/.claude/skills/wechat-master/scripts/wechat_api.py
~/.claude/skills/wechat-master/themes/minimal.yaml
~/.claude/skills/wechat-master/themes/professional-clean.yaml
~/.claude/skills/wechat-master/themes/tech-modern.yaml
~/.claude/skills/wechat-master/themes/warm-editorial.yaml
```

**Step 5: Final Commit**

```bash
cd ~/.claude && git add skills/wechat-master/ && git commit -m "feat(wechat-master): complete 5-agent wechat content production system"
```

---

## Phase 6: 端到端测试

### Task 16: 端到端冒烟测试

**不写代码**，用真实主题跑一遍完整流程。

**Step 1: 测试排版引擎**

```bash
cd ~/.claude/skills/wechat-master/scripts
echo "# 测试标题\n\n这是一段测试内容。\n\n## 第二节\n\n这里有**加粗**和*斜体*。\n\n> 引用块\n\n- 列表项1\n- 列表项2" > /tmp/test-article.md
python3 converter.py --input /tmp/test-article.md --theme professional-clean --output /tmp/test-output.html
```

Expected: `/tmp/test-output.html` 生成，含内联样式，无 `<style>` 标签。

**Step 2: 用浏览器预览 HTML**

```bash
open /tmp/test-output.html
```

Expected: 排版美观，字体大小/颜色/间距符合主题定义。

**Step 3: 测试完整 Skill 流程**

在 Claude Code 中执行：
```
/wechat-master write "为什么越来越多人开始吃牛油果"
```

逐步验证：
- [ ] 风格配置 Gate 正常弹出
- [ ] 研究 Agent 返回 3 个选题卡
- [ ] 选题选择 Gate 正常
- [ ] 创作 Agent 返回 4 个标题
- [ ] 标题选择 Gate 正常
- [ ] 大纲确认 Gate 正常
- [ ] 正文生成完成
- [ ] 质检 Agent 返回评分卡（≥60）
- [ ] 视觉 Agent 生成配图 + 封面
- [ ] 发布 Agent 排版 HTML 生成
- [ ] 发布确认 Gate 正常
- [ ] 草稿箱推送成功

**Step 4: 记录问题并修复**

如有问题，逐个修复后重新测试对应环节。

---

## 任务依赖图

```
Task 1 (目录结构)
  └→ Task 2 (SKILL.md)
       └→ Task 3 (研究Agent)
       └→ Task 4 (创作Agent)
       └→ Task 5 (质检Agent)
       └→ Task 6 (视觉Agent)
       └→ Task 7 (发布Agent)
  └→ Task 8 (Python依赖)
       └→ Task 9 (YAML主题)
            └→ Task 10 (theme.py) [TDD]
                 └→ Task 11 (converter.py) [TDD]
       └→ Task 12 (wechat_api.py) [TDD]
            └→ Task 13 (publisher.py) [TDD]
  └→ Task 14 (参考资料)
  └→ Task 15 (EXTEND.md + 收尾)
       └→ Task 16 (端到端测试)
```

**可并行的任务组**：
- Task 3/4/5/6/7（5 个 Agent Prompt）可并行
- Task 9 + Task 12（主题 + 微信API）可并行
- Task 10/11 必须串行（theme.py → converter.py）
- Task 12/13 必须串行（wechat_api.py → publisher.py）
