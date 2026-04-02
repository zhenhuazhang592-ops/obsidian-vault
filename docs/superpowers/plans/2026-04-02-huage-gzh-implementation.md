# 华哥公众号 · 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建完整的 `huage-gzh` 公众号 AI 写作智能体 Skill，包含 Qwen3-Max 推理引擎集成、Doubao-Seedream-4.5 图像生成集成，以及完整的 7 步写作流程。

**Architecture:** Claude Code 作为工作流编排层（控制流程节奏、路由决策、调用 Phase），Qwen3-Max 作为核心推理引擎（实际执行研究分析、写作生成），Doubao-Seedream-4.5 通过 baoyu-image-gen 提供图像生成能力。

**Tech Stack:** Claude Code Skill System / Python DashScope API / Doubao ARK API / Bash / Markdown

---

## 文件结构

```
.claude/skills/huage-gzh/
├── SKILL.md                          # 主入口：触发词 + 全局编排 + Qwen3-Max 调用
├── scripts/
│   └── qwen_client.py                 # Qwen3-Max API 客户端（DashScope）
└── phases/
    ├── 01-research.md                 # 研究阶段：Tavily + YouTube
    ├── 02-style-outline.md            # 风格确认 + 标题大纲
    ├── 03-writing.md                 # 正文写作（内嵌去AI味规则）
    ├── 04-images.md                  # 配图方案 + 生成
    └── 05-output.md                 # HTML排版 + 预览

.claude/skills/baoyu-image-gen/
└── SKILL.md                          # 修改：新增 Doubao-Seedream-4.5 后端

写作知识库/01-资源库/[YYYY-MM-DD]/[文章标题]/   # 运行时生成的输出目录结构
```

---

## Task 1：创建 Skill 目录结构

**Files:**
- Create: `.claude/skills/huage-gzh/SKILL.md`
- Create: `.claude/skills/huage-gzh/scripts/`
- Create: `.claude/skills/huage-gzh/phases/`
- Create: `.claude/skills/huage-gzh/rules/`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p /Users/huage/Obsidian\ Vault/.claude/skills/huage-gzh/scripts
mkdir -p /Users/huage/Obsidian\ Vault/.claude/skills/huage-gzh/phases
mkdir -p /Users/huage/Obsidian\ Vault/.claude/skills/huage-gzh/rules
```

- [ ] **Step 2: 创建主 SKILL.md 骨架**

```markdown
---
name: huage-gzh
description: 公众号AI写作智能体。强制全链路：深度研究(Tavily+YouTube) → 风格确认 → 批量标题大纲 → 正文写作(去AI味,Qwen3-Max驱动) → 配图方案 → 封面+配图(Doubao-Seedream-4.5) → HTML排版预览。触发词：写公众号、帮我写篇公众号文章
---

# 华哥公众号 · huage-gzh

## 角色

你是华哥公众号智能体，由 Claude Code 编排层驱动，Qwen3-Max 作为核心推理引擎。

你的职责是：接收用户的公众号写作需求，执行完整的 7 步流程，最终输出一篇排版好的 HTML 文章供用户预览。

## 核心流程

1. [用户需求] → 提取主题
2. [Step 1] Tavily 深度研究（文章+学术论文）
3. [Step 2] YouTube 视频研究（并行）
4. [Step 3] 学习整理后的研究内容
5. [Step 4] 风格确认 → 批量标题大纲确认
6. [Step 5] Qwen3-Max 正文写作（严格去AI味）
7. [Step 6] 配图方案确认 → 生成封面+配图
8. [Step 7] HTML排版 → 浏览器预览

## 当前 Phase

请阅读当前 Step 对应的 phase 文件，并严格按照其中的指令执行：

- phases/01-research.md   → Step 1-3：研究阶段
- phases/02-style-outline.md → Step 4：风格+标题大纲
- phases/03-writing.md   → Step 5：正文写作
- phases/04-images.md     → Step 6：配图生成
- phases/05-output.md     → Step 7：排版预览

## 模型配置

- 核心推理：Qwen3-Max（DashScope API）
  - 调用脚本：scripts/qwen_client.py
  - 环境变量：DASHSCOPE_API_KEY
- 图像生成：Doubao-Seedream-4.5（baoyu-image-gen）
  - 模型标识：doubao-seedream-4.5
  - 环境变量：ARK_API_KEY
- 搜索：Tavily API + YouTube Data API v3

## 输出路径规范

所有输出存入：`写作知识库/01-资源库/[YYYY-MM-DD]/[文章标题-slug]/`

每个 Phase 完成后，在该路径下创建对应的子目录并写入文件。
```

- [ ] **Step 3: 提交**

```bash
cd /Users/huage/Obsidian\ Vault
git add .claude/skills/huage-gzh/SKILL.md
git commit -m "feat(huage-gzh): create skill directory structure and main SKILL.md"
```

---

## Task 2：Qwen3-Max API 客户端

**Files:**
- Create: `.claude/skills/huage-gzh/scripts/qwen_client.py`

- [ ] **Step 1: 创建 Qwen3-Max 客户端**

```python
#!/usr/bin/env python3
"""
Qwen3-Max 客户端 - 华哥公众号 huage-gzh 核心推理引擎
通过 DashScope API 调用 Qwen3-Max（qwen-max 模型）
"""

import os
import json
from typing import Optional

try:
    from openai import OpenAI
    _HAS_OPENAI = True
except ImportError:
    _HAS_OPENAI = False


class QwenClient:
    """Qwen3-Max API 客户端"""

    def __init__(self, api_key: Optional[str] = None):
        if not _HAS_OPENAI:
            raise RuntimeError("openai package required: pip install openai")

        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY not set. "
                "Set it via: export DASHSCOPE_API_KEY=your_key"
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    def chat(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: str = "qwen-max",
    ) -> str:
        """
        发送对话请求到 Qwen3-Max

        Args:
            messages: [{"role": "system"|"user"|"assistant", "content": str}, ...]
            temperature: 创造性写作用 0.7，精确分析用 0.3
            max_tokens: 最大输出 token 数
            model: 模型名称，默认 qwen-max（Qwen3-Max）

        Returns:
            模型回复的文本内容
        """
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def research_analyze(self, research_content: str, topic: str) -> str:
        """研究分析：Qwen3-Max 阅读研究材料，生成洞察摘要"""
        system = """你是一个专业的内容研究员。你的任务是将收集到的研究材料进行分析，
提取核心洞察，识别不同观点和立场，并生成供写作使用的摘要。

输出格式：
- 核心发现（3-5条）
- 关键数据点（带来源）
- 不同观点摘要（含反面证据）
- 可引用的金句和引用"""

        return self.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"主题：{topic}\n\n研究材料：\n{research_content}"}
            ],
            temperature=0.3,
            max_tokens=2048,
        )

    def generate_style_options(self) -> str:
        """生成4种预设风格描述，供用户选择"""
        system = """你是一个专业公众号内容策划师。根据华哥公众号的风格体系，
生成4种预设写作风格供用户选择。

每种风格输出：风格名称、特点描述、适用场景、语气示例。"""
        return self.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": "请输出4种预设风格：亲和力强、专业严谨、幽默风趣、极简干货。"}
            ],
            temperature=0.8,
            max_tokens=2048,
        )

    def generate_titles_and_outline(
        self,
        topic: str,
        style: str,
        research_summary: str,
    ) -> str:
        """生成3个标题选项 + 完整大纲"""
        system = """你是一个专业公众号内容策划师，擅长生成爆款标题和结构化大纲。

任务：根据主题、选定风格和研究摘要，一次性输出：
1. 3个爆款标题（覆盖不同类型：冲突对比/疑问引导/数字效果/否定反转）
2. 完整文章大纲（Markdown格式：H1标题 + H2核心论点 + H3小节）

格式要求：
```
## 标题选项

### 选项1：[标题]（类型：冲突对比）
### 选项2：[标题]（类型：疑问引导）
### 选项3：[标题]（类型：数字效果/否定反转）

## 大纲（基于用户选定的标题）

# [H1标题]
## [H2核心论点1]
### [H3小节1.1]
### [H3小节1.2]
## [H2核心论点2]
...
```
"""
        return self.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"主题：{topic}\n选定风格：{style}\n\n研究摘要：\n{research_summary}"}
            ],
            temperature=0.8,
            max_tokens=4096,
        )

    def write_article(
        self,
        topic: str,
        style: str,
        outline: str,
        research_summary: str,
        anti_ai_rules: str,
    ) -> str:
        """正文写作：严格遵循去AI味规则"""
        system = f"""你是一个资深公众号内容创作者，写作风格为：{style}。

你的核心原则：**每一句话都必须像真人写的，不能有任何AI味。**

{anti_ai_rules}

字数要求：目标 1500-2500 字，最多 3000 字。

Markdown格式：
- H1：标题（文章标题）
- H2：核心论点（每个论点一个H2）
- H3：小节（克制使用，每个H2最多1-2个H3）
- 不用 `---` 分割线
- 图片占位：`![配图描述](图片文件路径)`

写作流程：
1. 先在脑海中按大纲展开每个论点
2. 写每段时问自己："这像不像真人写的？"
3. 写完后通读，检查是否有AI高频词
4. 确保节奏有变化（长短段落交替）
"""
        return self.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"主题：{topic}\n\n选定风格：{style}\n\n确认的大纲：\n{outline}\n\n研究摘要（仅作参考，不直接引用，可化用数据和观点）：\n{research_summary}\n\n请开始写正文。"}
            ],
            temperature=0.7,
            max_tokens=8192,
        )

    def plan_image_scheme(
        self,
        article_content: str,
        topic: str,
    ) -> str:
        """规划配图方案：封面 + 内文配图"""
        system = """你是一个专业的内容视觉策划师。根据文章内容，规划配图方案。

输出格式：
```
## 封面图

- 类型：[概念图/场景图/信息图/摄影风]
- 风格：[写实/插画/中国风/极简]
- 配色关键词：[3-5个颜色关键词]
- 画面描述：[50字以内的画面描述，用于生成提示词]
- 尺寸：900x500px

## 文章配图（共N张）

### 配图1：[位置：H2核心论点1之后]
- 类型：[信息图/场景/对比]
- 风格：[与封面保持一致的风格]
- 画面描述：[30字]

### 配图2：[位置：H2核心论点2之后]
...
```
"""
        return self.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"主题：{topic}\n\n文章内容：\n{article_content}"}
            ],
            temperature=0.5,
            max_tokens=2048,
        )


def main():
    """CLI 入口：python qwen_client.py <method> [args...]"""
    import sys
    client = QwenClient()

    if len(sys.argv) < 2:
        print("Usage: python qwen_client.py <method> [args...]")
        print("Methods: research_analyze, generate_style_options, generate_titles_and_outline, write_article, plan_image_scheme")
        sys.exit(1)

    method = sys.argv[1]

    if method == "generate_style_options":
        print(client.generate_style_options())
    elif method == "research_analyze" and len(sys.argv) >= 4:
        content = sys.argv[2]
        topic = sys.argv[3]
        print(client.research_analyze(content, topic))
    elif method == "generate_titles_and_outline" and len(sys.argv) >= 5:
        topic = sys.argv[2]
        style = sys.argv[3]
        research = sys.argv[4]
        print(client.generate_titles_and_outline(topic, style, research))
    elif method == "write_article" and len(sys.argv) >= 6:
        topic = sys.argv[2]
        style = sys.argv[3]
        outline = sys.argv[4]
        research = sys.argv[5]
        anti_ai = sys.argv[6] if len(sys.argv) >= 7 else ""
        print(client.write_article(topic, style, outline, research, anti_ai))
    elif method == "plan_image_scheme" and len(sys.argv) >= 4:
        article = sys.argv[2]
        topic = sys.argv[3]
        print(client.plan_image_scheme(article, topic))
    else:
        print(f"Unknown method or missing args: {sys.argv}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证 QwenClient 可导入**

```bash
cd /Users/huage/Obsidian\ Vault
python3 -c "from .claude.skills.huage_gzh.scripts.qwen_client import QwenClient; print('QwenClient import OK')"
```

如果报错：`pip install openai` 后重试。

- [ ] **Step 3: 提交**

```bash
git add .claude/skills/huage-gzh/scripts/qwen_client.py
git commit -m "feat(huage-gzh): add Qwen3-Max client via DashScope API"
```

---

## Task 3：Doubao-Seedream-4.5 集成到 baoyu-image-gen

**Files:**
- Read: `.claude/skills/baoyu-image-gen/SKILL.md`
- Modify: `.claude/skills/baoyu-image-gen/SKILL.md`

- [ ] **Step 1: 读取现有 baoyu-image-gen SKILL.md，找到后端配置区块**

读取文件，重点关注：
- 现有后端配置格式（OpenAI / Google / DashScope / Replicate）
- 后端选择逻辑在哪里
- 环境变量定义

- [ ] **Step 2: 在 SKILL.md 中新增 Doubao-Seedream-4.5 后端配置**

在"Supported Backends"或类似章节下，添加：

```markdown
### Doubao-Seedream-4.5（豆包·即梦）

**模型标识**：`doubao-seedream-4.5`

**API Endpoint**：火山引擎 ARK API
- Base URL: `https://ark.cn-beijing.volces.com/api/v3`
- 模型名: `douban Seedream-4.5`

**环境变量**：
```bash
export ARK_API_KEY=your_ark_api_key
```

**能力**：
- ✅ 文本生成图像
- ✅ 参考图像（图生图）
- ✅ 纵横比控制
- ✅ 中文提示词优化

**优势场景**：
- 中国风插画
- 写实摄影风
- 公众号封面图
- 知识科普图
- 水果/食材特写

**调用示例**（Bash）：
```bash
curl -X POST https://ark.cn-beijing.volces.com/api/v3/images/generations \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "doubao-seedream-4.5",
    "prompt": "<英文提示词，来自 baoyu-image-gen 提示词生成>",
    "image_url": "<参考图URL（如果有）>",
    "aspect_ratio": "16:9"
  }'
```

**提示词语言**：Doubao-Seedream-4.5 英文提示词效果更佳，生成时需将中文提示词翻译为英文。
```

- [ ] **Step 3: 验证 SKILL.md 格式完整性**

读取修改后的文件，确认：
- 新增后端没有破坏原有格式
- frontmatter 完整
- 引用链接没有断裂

- [ ] **Step 4: 提交**

```bash
git add .claude/skills/baoyu-image-gen/SKILL.md
git commit -m "feat(baoyu-image-gen): add Doubao-Seedream-4.5 backend"
```

---

## Task 4：phases/03-writing.md（核心写作 + 去AI味规则）

**Files:**
- Create: `.claude/skills/huage-gzh/phases/03-writing.md`
- Create: `.claude/skills/huage-gzh/rules/anti-ai.md`

- [ ] **Step 1: 创建 phases/03-writing.md**

```markdown
# Phase 03：正文写作

## 执行条件

- Step 1-3（研究阶段）已完成
- Step 4（风格+标题大纲）已获得用户确认
- 确认的大纲文件存在于：`[输出目录]/04-风格与大纲.md`

## 前置输入

从上一 Phase 获取：
- `topic`：文章主题
- `style`：用户选定的写作风格
- `outline`：用户确认的大纲
- `research_summary`：研究摘要（来自 00-研究索引.md）

## 执行步骤

### Step 5.1：读取去AI味规则

读取：`rules/anti-ai.md`，作为系统提示词的一部分。

### Step 5.2：构造 Qwen3-Max 写作请求

调用 `scripts/qwen_client.py`：

```bash
python3 .claude/skills/huage-gzh/scripts/qwen_client.py \
  write_article \
  "[topic]" \
  "[style]" \
  "[outline文本]" \
  "[research_summary文本]" \
  "[anti_ai_rules文本]"
```

### Step 5.3：保存正文

输出文件：`[输出目录]/05-正文.md`

```markdown
---
title: [文章标题]
author: 华哥公众号
date: YYYY-MM-DD
style: [选定风格]
word_count: [字数]
---

# [文章标题]

[正文内容，包含 ![配图描述](07-配图/NN-type-slug.png) 占位符]
```

### Step 5.4：字数统计并校验

- 统计正文字数（不含 frontmatter）
- 如果 < 1200 字：补充论点和案例
- 如果 > 3000 字：删除最弱的段落
- 目标：1500-2500 字

### Step 5.5：去AI味自检

对照 `rules/anti-ai.md` 的快速检查清单，逐项核对：

```
- [ ] 无"首先/其次/最后/总之/综上所述"
- [ ] 无"值得注意的是/毋庸置疑/众所周知"
- [ ] 无 Tier 1 英文词汇（delve/leverage/robust/comprehensive）
- [ ] 有口语化表达
- [ ] 有长短段落交替
- [ ] 无每段都是3-4句的匀称结构
- [ ] 字数在 1500-2500 范围内
```

如有违规，手动修改或重新调用 Qwen3-Max 补充。

## 输出

- `[输出目录]/05-正文.md`
- 报告字数和去AI味自检结果

## 下一步

自动进入 Phase 04：`phases/04-images.md`（配图方案）
```

- [ ] **Step 2: 创建 rules/anti-ai.md（去AI味完整规则）**

```markdown
# 去AI味写作规则 · 华哥公众号

> 来源：01-输出内容/公众号/工具研究/ArticleSkill/去AI化润色.md
> 来源：01-输出内容/公众号/工具研究/avoid-ai-writing/SKILL.md

---

## 一、必删词汇（Tier 1 — 零容忍）

发现即替换，不接受任何例外：

### 中文连接词
- ~~首先、其次、再者、最后~~ → 删除或用自然过渡替代
- ~~总之、综上所述、总而言之~~ → 直接删，或用一句具体的话替代
- ~~此外、另外、与此同时~~ → 用"而且"、"并且"、"这时"替代
- ~~一方面...另一方面...~~ → 拆成两段各自陈述

### AI惯用语
- ~~值得注意的是~~ → 直接删，或"但有个问题——"
- ~~应该指出的是~~ → 直接删
- ~~毋庸置疑、毫无疑问~~ → 直接删，观点直接陈述
- ~~众所周知~~ → 直接删，或"大家都知道"
- ~~作为一个~~ → 改为"我是"、"做这行的人"
- ~~让我们~~ → 改为"咱们"、"我来"

### 空洞形容
- ~~非常重要、至关重要~~ → 直接删，不影响句意
- ~~不言而喻~~ → 直接删
- ~~具有重要意义~~ → 直接删

### 英文AI高频词（英文提示词中）
- ~~delve / delve into~~ → explore, dig into, look at
- ~~leverage~~ → use
- ~~robust~~ → strong, reliable, solid
- ~~comprehensive~~ → thorough, complete
- ~~utilize~~ → use
- ~~embark~~ → start, begin
- ~~pivotal~~ → key, critical
- ~~robust~~ → strong, reliable

---

## 二、必添元素（Tier 2 — 强化人味）

### 口语化表达（风格：亲和力强/幽默风趣）
插入位置：段落开头、转折处、强调处

- 说实话、
- 讲真、
- 我跟你说、
- 坦白讲、
- 怎么说呢、
- 我觉得、
- 据我观察、
- 以我的经验、

### 个人观点标记
在观点陈述前加：
- 我觉得，
- 我的看法是，
- 以我的经验，
- 讲真，
- 老实说，

### 不完美感
- 或许、
- 在多数情况下、
- 大概、
- 说起来、
- 这事儿说起来有点反常识，但：

---

## 三、节奏规则（Tier 3 — 结构性调整）

### 段落长短交替

**强制要求**：
- 每篇文章必须有 2-4 个 1-2 句话的**短段落**（语气强调/转折/吐槽）
- 长段落不超过 150 字
- 禁止：每段都是 3-4 句匀称结构
- 禁止：每段长度基本相同

**节奏示例**（实际写作时参考）：

```
一段80字的正常段落，说明论点。

但是。

这里其实有个问题很多人没注意到。（短段落，制造悬念）

接下来是一段120字的段落，展开说明那个问题是什么、
为什么重要、有什么数据支撑。这段稍微长一点，
因为需要把事情说清楚。

讲真，我第一次看到这个数据的时候也吓了一跳。（口语化短段落）
```

### 段落衔接

- 禁止：段落之间没有过渡，上一句说A下一句突然说Z
- 要求：相邻段落之间有1个过渡词或过渡句
- 过渡词库：`不过`、`话说回来`、`扯远了`、`言归正传`、`说到这里`

---

## 四、语态规则

### 被动改主动

- ~~被发现~~ → 我发现
- ~~被认为~~ → 我的看法是
- ~~被广泛使用~~ → 大家都在用

### 人称优先

- 优先使用"我"、"你"、"我们"
- 少用"人们"、"大家"、"用户"（必要时才用）

---

## 五、字数控制

| 指标 | 要求 |
|------|------|
| 目标字数 | 1500-2500 |
| 最少字数 | 1200 |
| 最多字数 | 3000 |
| 超限处理 | 删除最弱论点段落 |
| 不达标处理 | 补充案例和数据，深化现有论点 |

---

## 六、快速检查清单（写完必查）

```
□ 没有"首先/其次/最后/总之/综上所述"
□ 没有"值得注意的是/毋庸置疑/众所周知"
□ 没有"非常重要/至关重要"
□ 没有英文AI高频词（delve/leverage/robust/comprehensive）
□ 有2-4个短段落（1-2句话）
□ 没有每段都是3-4句的匀称结构
□ 有口语化表达（根据风格）
□ 有个人见解标记（"我觉得"等）
□ 被动语态已改为主动
□ 字数在 1500-2500 范围内
□ 没有用 `---` 分割线
□ 图片占位符格式正确：`![描述](路径.png)`
```

---

## 七、风格强度对照

| 风格 | Tier 2 口语化 | 短段落密度 | 个人见解 |
|------|--------------|-----------|---------|
| 亲和力强 | 高 | 3-4个 | 多 |
| 幽默风趣 | 高 | 2-3个 | 多 |
| 专业严谨 | 低（逻辑替代） | 1-2个 | 中 |
| 极简干货 | 极低 | 1个或无 | 少 |
```

- [ ] **Step 3: 提交**

```bash
git add .claude/skills/huage-gzh/phases/03-writing.md .claude/skills/huage-gzh/rules/anti-ai.md
git commit -m "feat(huage-gzh): add writing phase with full anti-AI rules"
```

---

## Task 5：phases/02-style-outline.md（风格确认 + 标题大纲）

**Files:**
- Create: `.claude/skills/huage-gzh/phases/02-style-outline.md`

- [ ] **Step 1: 创建 phases/02-style-outline.md**

```markdown
# Phase 02：风格确认 + 标题大纲

## 执行条件

- Step 1-3（研究阶段）已完成
- 研究摘要文件存在：`[输出目录]/00-研究索引.md`

## 前置输入

从 Phase 01 获取：
- `topic`：文章主题（从用户需求提取）
- `research_summary`：研究摘要（00-研究索引.md 的核心内容）

## 执行步骤

### Step 4.1：展示4种预设风格

调用 Qwen3-Max，展示4种预设风格描述：

```bash
python3 .claude/skills/huage-gzh/scripts/qwen_client.py generate_style_options
```

输出格式示例：

```
## 华哥公众号 · 写作风格选择

请从以下4种风格中选择一种（告诉我编号或名称）：

### 风格1：亲和力强
**特点**：第一人称"我"、情绪化表达、适度自嘲、口语化
**适用**：生活类、情感类、个人经历分享
**语气示例**："说实话，这个坑我也踩过..."

### 风格2：专业严谨
**特点**：数据支撑、客观分析、逻辑严密、专业术语
**适用**：科普类、行业分析、数据解读
**语气示例**："根据2024年最新研究，..."

### 风格3：幽默风趣
**特点**：轻松调侃、生动比喻、口语化、适度吐槽
**适用**：轻松话题、干货娱乐化
**语气示例**："这玩意儿，怎么说呢，直呼离谱..."

### 风格4：极简干货
**特点**：精炼直击要点、少修饰、强化逻辑结构
**适用**：工具介绍、方法论、教程类
**语气示例**："第一步：配置环境。第二步：..."
```

### Step 4.2：用户选择风格

等待用户回复（1/2/3/4 或风格名称）。

用户回复后，将选定风格记录到：`[输出目录]/04-风格与大纲.md`

```markdown
## 选定风格

风格：[名称]
选择时间：[YYYY-MM-DD HH:MM]
```

### Step 4.3：生成标题选项 + 大纲

用户选定风格后，立即调用：

```bash
python3 .claude/skills/huage-gzh/scripts/qwen_client.py \
  generate_titles_and_outline \
  "[topic]" \
  "[style]" \
  "[research_summary文本]"
```

Qwen3-Max 将一次性输出：
1. **3个爆款标题**（覆盖冲突对比/疑问引导/数字效果/否定反转各一种）
2. **完整大纲**（Markdown格式，用户确认后直接用于写作）

### Step 4.4：展示并请求确认

展示 Qwen3-Max 输出的标题+大纲，格式：

```
## 标题选项

### 选项1：[标题]（类型：冲突对比）
### 选项2：[标题]（类型：疑问引导）
### 选项3：[标题]（类型：数字效果/否定反转）

## 推荐大纲

# [H1标题]
## [H2核心论点1]
### [H3小节1.1]
### [H3小节1.2]
## [H2核心论点2]
...

---

请选择标题（1/2/3）或自行修改标题。
确认后，我开始写正文。
```

### Step 4.5：用户确认后保存

用户确认标题和大纲后：

```markdown
---
date: YYYY-MM-DD
style: [选定风格]
title: [用户确认的标题]
status: outline_confirmed
---

## 标题
[确认的标题]

## 大纲
[完整大纲内容]
```

保存到：`[输出目录]/04-风格与大纲.md`

## 输出

- `[输出目录]/04-风格与大纲.md`（含风格+标题+大纲）
- 进入 Phase 03：`phases/03-writing.md`（正文写作）

## 下一步

自动进入 Phase 03：`phases/03-writing.md`（正文写作）
```

- [ ] **Step 2: 提交**

```bash
git add .claude/skills/huage-gzh/phases/02-style-outline.md
git commit -m "feat(huage-gzh): add style selection and title-outline phase"
```

---

## Task 6：phases/01-research.md（研究阶段）

**Files:**
- Create: `.claude/skills/huage-gzh/phases/01-research.md`

- [ ] **Step 1: 创建 phases/01-research.md**

```markdown
# Phase 01：深度研究（Tavily + YouTube）

## 执行条件

- 用户已输入创作需求（主题）

## 执行步骤

### Step 1.1：提取主题，创建输出目录

从用户需求中提取主题（topic）和标题候选（可选）。

```bash
# 提取今天的日期
DATE=$(date +%Y-%m-%d)

# 创建输出目录结构
mkdir -p "写作知识库/01-资源库/${DATE}/[slug]/"
mkdir -p "写作知识库/01-资源库/${DATE}/[slug]/01-文章研究/"
mkdir -p "写作知识库/01-资源库/${DATE}/[slug]/02-视频研究/"
mkdir -p "写作知识库/01-资源库/${DATE}/[slug]/03-学术参考/"
mkdir -p "写作知识库/01-资源库/${DATE}/[slug]/06-封面图/"
mkdir -p "写作知识库/01-资源库/${DATE}/[slug]/07-配图/"
mkdir -p "写作知识库/01-资源库/${DATE}/[slug]/08-排版预览/"
```

其中 `[slug]` 为文章标题的 slug 格式（中文标题转拼音或英文slug）。

### Step 1.2：Tavily 深度研究（并行 Track A）

**目标**：搜索 10-20 篇高质量文章/学术论文，覆盖不同观点含反面。

使用 Tavily API（如无 Tavily Key，使用 WebSearch 替代）：

```bash
# Tavily 搜索示例（需要 tavily-python 包）
python3 -c "
from tavily import TavilyClient
import os

client = TavilyClient(api_key=os.environ['TAVILY_API_KEY'])

# 1. 通用文章搜索
articles = client.search(
    query='[topic] -广告',
    max_results=15,
    include_answer=True,
    include_raw_content=False
)

# 2. 学术论文搜索
academic = client.search(
    query='[topic] 学术研究 论文',
    max_results=5,
    include_answer=True,
)

# 输出：articles, academic
print('Articles:', len(articles['results']))
print('Academic:', len(academic['results']))
"
```

**如果 Tavily API 不可用**：使用 WebSearch 手动搜索，整理结果。

**入库**：`01-文章研究/` 和 `03-学术参考/`

每个来源一个文件：
```markdown
---
source: [URL或来源名称]
type: article|academic
date: YYYY-MM-DD
---

# [来源标题]

## 核心摘要
[3-5句话概括主要内容]

## 关键观点
- 观点1
- 观点2

## 可引用内容
> "[引用原文]"

## 来源链接
[URL]
```

### Step 1.3：YouTube 视频研究（并行 Track B）

**目标**：搜索相关 YouTube 视频，提取核心观点。

使用 `youtube-research-flow`（如已配置）：

```bash
cd /Users/huage/Obsidian\ Vault
python3 01-输出内容/youtube-research-flow/scripts/main.py \
  "[topic] 相关视频" \
  --max-results 10 \
  --analysis-type tutorial
```

或者使用 YouTube Data API v3 直接搜索。

**入库**：`02-视频研究/`

```markdown
# YouTube 视频：[视频标题]

## 基本信息
- 频道：[频道名]
- 时长：[时长]
- 观看：[播放量]
- 链接：[URL]

## 核心观点
[视频传达的主要观点，3-5条]

## 对文章有用的内容
[具体可以引用的内容、数据或故事]
```

### Step 1.4：Qwen3-Max 综合研究摘要

收集所有研究文件后，调用 Qwen3-Max 生成综合摘要：

```bash
python3 .claude/skills/huage-gzh/scripts/qwen_client.py \
  research_analyze \
  "[所有研究材料的合并文本]" \
  "[topic]"
```

输出保存到：`[输出目录]/00-研究索引.md`

```markdown
---
date: YYYY-MM-DD
topic: [主题]
research_depth: deep
sources:
  articles: [N篇]
  videos: [N个]
  academic: [N篇]
---

# [主题] · 研究摘要

## 核心发现

1. [发现1]
2. [发现2]
3. [发现3]

## 关键数据

| 数据 | 来源 | 备注 |
|------|------|------|
| ... | ... | ... |

## 不同观点

### 支持[主题]的观点
- ...

### 质疑或反面的观点
- ...

## 写作可用引用

> "[引用1]"
> "[引用2]"

## 研究空白
[还有哪些角度没有覆盖，可以作为差异化切入点]
```

## 研究输出清单

```
[输出目录]/
├── 00-研究索引.md         ✅ Qwen3-Max 生成
├── 01-文章研究/          ✅ 10-20篇
├── 02-视频研究/          ✅ YouTube 整理
└── 03-学术参考/          ✅ 学术论文摘要
```

## 错误处理

| 场景 | 处理 |
|------|------|
| Tavily API 失败 | 回退到 WebSearch，告知用户研究深度降低 |
| YouTube API 失败 | 跳过视频研究，专注于文章研究，告知用户 |
| Qwen3-Max API 失败 | 报错退出，提示检查 DASHSCOPE_API_KEY |
| 无研究材料 | 告知用户，建议更换主题或手动提供参考材料 |

## 下一步

- 研究完成 → 进入 Phase 02：`phases/02-style-outline.md`（风格+标题大纲）
```

- [ ] **Step 2: 提交**

```bash
git add .claude/skills/huage-gzh/phases/01-research.md
git commit -m "feat(huage-gzh): add research phase (Tavily + YouTube)"
```

---

## Task 7：phases/04-images.md（配图方案 + 生成）

**Files:**
- Create: `.claude/skills/huage-gzh/phases/04-images.md`

- [ ] **Step 1: 创建 phases/04-images.md**

```markdown
# Phase 04：配图方案 + 生成

## 执行条件

- Phase 03（正文写作）已完成
- `[输出目录]/05-正文.md` 存在

## 执行步骤

### Step 6.1：规划配图方案

调用 Qwen3-Max 根据正文内容规划配图：

```bash
python3 .claude/skills/huage-gzh/scripts/qwen_client.py \
  plan_image_scheme \
  "$(cat [输出目录]/05-正文.md)" \
  "[topic]"
```

输出格式：

```
## 封面图

- 类型：[类型]
- 风格：[风格]
- 配色：[关键词]
- 画面描述：[50字描述]
- 尺寸：900x500px

## 文章配图（共N张）

### 配图1：[位置]
- 类型：[类型]
- 风格：[风格]
- 画面描述：[30字]
```

### Step 6.2：展示配图方案（用户确认）

```
## 配图方案

### 封面图
- 类型：[类型]
- 风格：[风格]
- 画面描述：[描述]
- 生成模型：Doubao-Seedream-4.5

### 文章配图（共N张）

| 编号 | 位置 | 类型 | 风格 | 描述 |
|------|------|------|------|------|
| 01 | H2论点1后 | 信息图 | 写实 | [描述] |
| 02 | H2论点2后 | 场景图 | 插画 | [描述] |
| ... | ... | ... | ... | ... |

确认这个方案吗？确认后开始生成图片。
（图片生成预计需要 2-5 分钟）
```

### Step 6.3：用户确认后生成图片

**封面生成**：`baoyu-cover-image`

```bash
# 封面图生成
/baoyu-cover-image [输出目录]/05-正文.md \
  --type [类型] \
  --palette [配色] \
  --aspect 16:9 \
  --output [输出目录]/06-封面图/cover.png
```

**配图生成**：`baoyu-article-illustrator`

```bash
# 配图生成（每张配图）
# 参考 phases/04-images-images.md 的提示词生成流程
# 调用 Doubao-Seedream-4.5 后端
/baoyu-article-illustrator [输出目录]/05-正文.md \
  --type [类型] \
  --style [风格] \
  --backend doubao-seedream-4.5 \
  --output [输出目录]/07-配图/
```

**Doubao-Seedream-4.5 提示词要求**：
- 必须翻译为英文
- 包含画面描述 + 风格关键词 + 技术参数
- 示例：
```英文
A split-screen comparison of ripe and unripe avocados on a wooden
cutting board, soft morning light, photorealistic style, shallow
depth of field, warm tones, 16:9 aspect ratio, no text.
```

### Step 6.4：下载并保存图片

- 图片下载到：`[输出目录]/06-封面图/` 和 `[输出目录]/07-配图/`
- 更新 `05-正文.md` 中的图片占位符为实际文件路径

### Step 6.5：更新正文中的图片路径

编辑 `[输出目录]/05-正文.md`，将占位符替换为实际图片路径：

```
# 替换前
![配图描述](图片文件路径)

# 替换后
![配图描述](../07-配图/01-type-slug.png)
```

## 错误处理

| 场景 | 处理 |
|------|------|
| Doubao-Seedream-4.5 失败 | 回退到 baoyu-image-gen 其他后端（OpenAI DALL-E / Google Imagen），告知用户后端切换 |
| 图片生成超时 | 告知用户，询问是否继续等待或使用其他后端 |
| 用户取消 | 停在当前步骤，跳过图片生成，进入 Phase 05 |

## 下一步

配图完成（或跳过） → 进入 Phase 05：`phases/05-output.md`（HTML排版预览）
```

- [ ] **Step 2: 提交**

```bash
git add .claude/skills/huage-gzh/phases/04-images.md
git commit -m "feat(huage-gzh): add image generation phase"
```

---

## Task 8：phases/05-output.md（HTML排版 + 预览）

**Files:**
- Create: `.claude/skills/huage-gzh/phases/05-output.md`

- [ ] **Step 1: 创建 phases/05-output.md**

```markdown
# Phase 05：HTML排版 + 浏览器预览

## 执行条件

- Phase 03（正文写作）已完成
- Phase 04（配图）已完成或用户跳过

## 执行步骤

### Step 7.1：Markdown 转 HTML

使用 `baoyu-markdown-to-html`：

```bash
SKILL_DIR="/Users/huage/Obsidian Vault/.claude/skills/baoyu-markdown-to-html"
npx -y bun ${SKILL_DIR}/scripts/main.ts \
  "[输出目录]/05-正文.md" \
  --theme default \
  --color blue
```

### Step 7.2：选择主题（如果用户有偏好）

询问用户是否需要切换主题：

```
排版主题选项：
1. default（经典）- 传统排版，标题居中带底边，二级标题白字彩底
2. grace（优雅）- 文字阴影，圆角卡片，精致引用块
3. simple（简洁）- 现代极简风，不对称圆角，清爽留白
4. modern（现代）- 大圆角、药丸形标题、宽松行距

默认使用 default。如需切换，请告诉我主题名称。
```

### Step 7.3：复制图片到 HTML 同级目录

```bash
# 复制封面和配图到 HTML 同级 imgs/ 目录
mkdir -p "[HTML输出目录]/imgs"
cp "[输出目录]/06-封面图/cover.png" "[HTML输出目录]/imgs/cover.png"
cp "[输出目录]/07-配图/"*.png "[HTML输出目录]/imgs/"
```

### Step 7.4：浏览器预览

使用 `gstack/browse` 打开 HTML 预览：

```bash
open "[HTML文件路径].html"
# 或使用 gstack
/browse open "[HTML文件路径].html"
```

### Step 7.5：完成报告

```
## 华哥公众号 · 文章完成

**主题**：[文章标题]
**风格**：[选定风格]
**字数**：[N] 字
**配图**：[封面×1 + 配图×N张]

### 产出文件

- 文章正文：写作知识库/01-资源库/[YYYY-MM-DD]/[slug]/05-正文.md
- 封面图：.../06-封面图/cover.png
- 配图：.../07-配图/
- HTML排版：.../08-排版预览/index.html

### 下一步

1. 打开 index.html 预览效果
2. 如需调整图片或文字，修改后重新生成 HTML
3. 确认无误后，复制 HTML 内容到微信公众号后台编辑器
4. 在公众号后台替换封面图和内文图片
5. 发布！

---
🎉 文章创作完成！祝阅读量高高！
```

## 输出

- `[输出目录]/08-排版预览/index.html`
- 浏览器已打开预览
- 完整产出报告

## 下一步

全部完成。如需调整，修改对应文件后重新执行相关 Phase。
```

- [ ] **Step 2: 提交**

```bash
git add .claude/skills/huage-gzh/phases/05-output.md
git commit -m "feat(huage-gzh): add HTML output and preview phase"
```

---

## Task 9：组装完整 SKILL.md，整合所有 Phase

**Files:**
- Modify: `.claude/skills/huage-gzh/SKILL.md`

- [ ] **Step 1: 更新主 SKILL.md，添加完整触发逻辑和 Phase 引用**

```markdown
---
name: huage-gzh
description: 公众号AI写作智能体。强制全链路：深度研究(Tavily+YouTube) → 风格确认 → 批量标题大纲 → 正文写作(去AI味,Qwen3-Max驱动) → 配图方案 → 封面+配图(Doubao-Seedream-4.5) → HTML排版预览。触发词：写公众号、帮我写篇公众号文章、公众号创作
---

# 华哥公众号 · huage-gzh

> 强制全链路公众号 AI 写作智能体
> 核心推理：Qwen3-Max | 图像生成：Doubao-Seedream-4.5
> 触发词：`写公众号`、`帮我写篇公众号文章`、`公众号创作`

---

## 快速启动

当用户说"写公众号"或类似需求时，立即激活本 Skill。

**一句话引导用户**：
"好的，我来帮你创作一篇公众号文章。整个流程是：深度研究 → 确认风格和标题大纲 → 写正文 → 配图 → 排版预览。你只需要做选择题和最终确认。"

**从提取主题开始**：
- 从用户需求中提取主题（topic）
- 创建今天的输出目录：`写作知识库/01-资源库/[YYYY-MM-DD]/[slug]/`
- 告知用户开始研究阶段

---

## Phase 入口索引

| Phase | 文件 | 负责 |
|-------|------|------|
| Step 1-3 | `phases/01-research.md` | Tavily 研究 + YouTube 研究 + 综合摘要 |
| Step 4 | `phases/02-style-outline.md` | 风格选择 + 标题大纲确认 |
| Step 5 | `phases/03-writing.md` | Qwen3-Max 正文写作（去AI味） |
| Step 6 | `phases/04-images.md` | 配图方案 + Doubao-Seedream-4.5 生成 |
| Step 7 | `phases/05-output.md` | HTML排版 + 浏览器预览 |

---

## 技术依赖

| 工具 | 用途 | 环境变量 |
|------|------|---------|
| `scripts/qwen_client.py` | Qwen3-Max API | `DASHSCOPE_API_KEY` |
| `baoyu-image-gen` | 图像生成（含 Doubao-Seedream-4.5） | `ARK_API_KEY` |
| `baoyu-markdown-to-html` | Markdown → HTML | — |
| `gstack/browse` | 浏览器预览 | — |
| Tavily API | 深度搜索 | `TAVILY_API_KEY` |
| YouTube Data API v3 | 视频研究 | `YOUTUBE_API_KEY` |

---

## 环境检查清单（首次使用）

```
□ DASHSCOPE_API_KEY 已配置（Qwen3-Max）
□ ARK_API_KEY 已配置（Doubao-Seedream-4.5）
□ TAVILY_API_KEY 已配置（深度搜索）
□ YOUTUBE_API_KEY 已配置（YouTube研究）
□ baoyu-markdown-to-html 已安装
□ gstack 已配置
```

---

## 完整流程

```
用户："帮我写一篇关于[主题]的公众号文章"
  │
  ▼
[Phase 01: 研究]
  - 并行：Tavily 搜索（10-20篇）+ YouTube 研究
  - Qwen3-Max 综合摘要
  │
  ▼
[Phase 02: 风格+大纲] ← 用户参与
  - 展示4种风格 → 用户选
  - 输出3个标题+大纲 → 用户确认
  │
  ▼
[Phase 03: 正文写作]
  - Qwen3-Max 写作（严格去AI味规则）
  - 自检清单验证
  │
  ▼
[Phase 04: 配图] ← 用户参与
  - Qwen3-Max 规划配图方案 → 用户确认
  - Doubao-Seedream-4.5 生成封面+配图
  │
  ▼
[Phase 05: 排版预览]
  - Markdown → HTML（baoyu-markdown-to-html）
  - 浏览器打开预览
  │
  ▼
完成！用户复制 HTML 内容到公众号后台发布
```
```

- [ ] **Step 2: 提交**

```bash
git add .claude/skills/huage-gzh/SKILL.md
git commit -m "feat(huage-gzh): complete main SKILL.md with full orchestration"
```

---

## Task 10：端到端验证（用一篇真实文章跑通全流程）

**Files:**
- Run: 完整 7 步流程

- [ ] **Step 1: 准备测试主题**

从用户提供的需求中，选择一个真实主题（或者使用预设测试主题"牛油果的营养价值"）作为首次验证。

- [ ] **Step 2: 执行 Phase 01 研究**

```bash
# 检查环境变量
echo "DASHSCOPE: $(test -n $DASHSCOPE_API_KEY && echo OK || echo MISSING)"
echo "ARK: $(test -n $ARK_API_KEY && echo OK || echo MISSING)"

# 创建测试输出目录
DATE=$(date +%Y-%m-%d)
mkdir -p "写作知识库/01-资源库/${DATE}/测试牛油果营养/01-文章研究/"
```

- [ ] **Step 3: 执行 Phase 02-05（模拟验证 Prompt 逻辑）**

手动走一遍每个 Phase 的指令，确认：
- Qwen3-Max 客户端能正常调用
- 去AI味规则能生效（检查输出中无 Tier 1 词汇）
- 文件路径正确
- 流程衔接正确

- [ ] **Step 4: 记录验证结果**

更新设计文档 `docs/plans/2026-04-02-huage-gzh-design.md` 中的验证标准：

```
- [x] Qwen3-Max 客户端正常调用
- [ ] 去AI味规则生效（待正文写作验证）
- [ ] 配图方案能被用户理解并确认
- [ ] Doubao-Seedream-4.5 能生成封面和配图（待API Key配置后验证）
- [ ] HTML 预览在浏览器中正常显示
```

- [ ] **Step 5: 提交**

```bash
git add docs/plans/2026-04-02-huage-gzh-design.md
git commit -m "test(huage-gzh): add end-to-end verification tracking"
```

---

## 自查清单（写完计划后）

### 1. 设计覆盖检查

对照 `docs/plans/2026-04-02-huage-gzh-design.md`：

| 设计要求 | Task 覆盖 |
|---------|---------|
| 强制全链路研究 | Task 6 (01-research) |
| Qwen3-Max 驱动写作 | Task 2 (qwen_client) + Task 4 (03-writing) |
| Doubao-Seedream-4.5 集成 | Task 3 (baoyu-image-gen) |
| 4种预设风格 | Task 5 (02-style-outline) |
| 批量标题大纲确认 | Task 5 (02-style-outline) |
| 去AI味规则 | Task 4 (rules/anti-ai) |
| 配图半自动方案 | Task 7 (04-images) |
| HTML排版预览 | Task 8 (05-output) |
| 按日期归档输出 | Task 6 (01-research) |

### 2. 占位符检查

搜索计划中所有 `[...]` 占位符，确保每个都有具体说明：
- 所有 `[topic]` 有来源说明
- 所有 `[style]` 有选择逻辑
- 所有文件路径为完整绝对路径

### 3. 类型一致性检查

| 位置 | 类型/方法名 | 一致性 |
|------|-----------|------|
| `qwen_client.py` | `research_analyze()` | = `Task 2 Step 1` 调用 |
| `qwen_client.py` | `generate_style_options()` | = `Task 5 Step 4.1` 调用 |
| `qwen_client.py` | `generate_titles_and_outline()` | = `Task 5 Step 4.3` 调用 |
| `qwen_client.py` | `write_article()` | = `Task 4 Step 2` 调用 |
| `qwen_client.py` | `plan_image_scheme()` | = `Task 7 Step 6.1` 调用 |
| 输出目录 slug | `[slug]` | = 文章标题转拼音/英文 |
