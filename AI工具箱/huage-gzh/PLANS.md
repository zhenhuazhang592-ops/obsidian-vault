# 漠玫创作 · 公众号多Agent协同创作系统

> 版本：v1.0
> 更新：2026-04-13
> 状态：计划阶段

---

## 一、项目概述

### 1.1 定位

**漠玫创作**是一个可交互的公众号多Agent协同创作工具，通过多个专业Agent协作完成从主题策划到最终排版输出的完整创作流程。

### 1.2 核心价值

- **多Agent协同**：7个专业Agent各司其职，实时可见工作状态
- **质量门禁**：6维度评分 ≥85分通过，否则自动触发修改
- **风格学习**：从已发布文章学习写作风格，生成个性化指令
- **去AI味优化**：36种AI模式检测 + 3-tier词汇表替换
- **SEO/GEO双优**：关键词布局 + AI引用优化

### 1.3 已有基础

```
AI工具箱/huage-gzh/
├── cli.py              # CLI入口（v0.3）
├── core/
│   ├── message_hub.py  # 消息中心（已实现）
│   ├── llm_client.py   # LLM客户端（已实现）
│   └── style_fingerprint.py  # 风格指纹引擎（已实现）
├── agents/
│   ├── style_learner_agent.py  # 风格学习（已实现）
│   ├── planner_agent.py        # 规划中
│   ├── outline_agent.py        # 规划中
│   └── writer_agent.py        # 规划中
└── outputs/            # 输出目录
```

---

## 二、系统架构

### 2.1 Agent职责划分

```
┌─────────────────────────────────────────────────────────────────┐
│                        漠玫创作系统                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │ LeadAgent   │    │ PlannerAgent │    │ResearchAgent│          │
│  │  (主导)     │    │  (策划)      │    │  (研究)      │          │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘          │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │OutlineAgent │    │ WriterAgent │    │PolishAgent  │          │
│  │  (大纲)     │    │  (写作)     │    │  (润色)     │          │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘          │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │ReviewAgent  │    │ImageAgent   │    │PublishAgent │          │
│  │  (审查)     │    │  (配图)     │    │  (发布)     │          │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘          │
│         │                  │                  │                 │
└─────────┼──────────────────┼──────────────────┼───────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
      质量门禁           配图封面           排版输出
      (6维度)            (色系+风格)         (最终稿)
```

### 2.2 Agent详细职责

| Agent | 核心职责 | 输入 | 输出 |
|-------|---------|------|------|
| **LeadAgent** | 总调度、状态分发、用户交互协调 | 用户主题 | 协调信号 |
| **PlannerAgent** | 主题策划、受众画像、独特角度 | 主题 | 策划方案（3个选项） |
| **ResearchAgent** | Tavily深度搜索、Obsidian学习、风格分析 | 主题+关键词 | 研究报告 |
| **OutlineAgent** | 结构设计、SEO关键词布局 | 策划+研究 | 大纲（含关键词） |
| **WriterAgent** | 完整正文写作、风格注入 | 大纲+风格指令 | 初稿 |
| **PolishAgent** | 去AI味、GEO优化、SEO强化 | 初稿 | 润色稿 |
| **ReviewAgent** | 6维度质量审查（≥85分通过） | 润色稿 | 评分报告 |
| **ImageAgent** | 封面设计、配图风格、尺寸 | 文章主题 | 配图方案 |
| **PublishAgent** | 排版输出、格式转换 | 终稿+配图 | 完整发布稿 |

### 2.3 消息传递机制

基于已有的 `MessageHub`，扩展为7种消息类型：

```python
class MessageType(Enum):
    STATUS = "status"           # Agent状态更新
    PLAN_REQUEST = "plan_request"     # 策划请求
    PLAN_RESULT = "plan_result"       # 策划结果
    RESEARCH_REQUEST = "research_request"   # 研究请求
    RESEARCH_RESULT = "research_result"     # 研究结果
    OUTLINE_REQUEST = "outline_request"    # 大纲请求
    OUTLINE_RESULT = "outline_result"      # 大纲结果
    WRITE_REQUEST = "write_request"       # 写作请求
    WRITE_RESULT = "write_result"         # 写作结果
    POLISH_REQUEST = "polish_request"      # 润色请求
    POLISH_RESULT = "polish_result"        # 润色结果
    REVIEW_REQUEST = "review_request"     # 审查请求
    REVIEW_RESULT = "review_result"       # 审查结果
    IMAGE_REQUEST = "image_request"       # 配图请求
    IMAGE_RESULT = "image_result"         # 配图结果
    PUBLISH_RESULT = "publish_result"     # 发布结果
```

### 2.4 Worker Handoff模板

每个Agent完成任务后，输出标准Handoff Summary：

```markdown
## STATUS
- Role: [Agent名称]
- Status: completed / blocked / needs_input
- Confidence: [0-1]
- Checkpoint: [milestone]

## TASK
- Objective: [目标]
- Scope in: [包含范围]
- Scope out: [排除范围]
- Deliverable: [交付物]

## WHAT I DID
-

## KEY FINDINGS
-

## EVIDENCE
- Sources / 数据来源:
- 关键数据点:

## ARTIFACTS
- Files: [生成的文件]
- Outputs: [结构化输出]

## RISKS OR GAPS
-

## RECOMMENDED NEXT STEP
-
```

---

## 三、完整Pipeline流程

### 3.1 流程图

```
用户输入主题
     │
     ▼
┌─────────────┐
│ LeadAgent   │ ◄── 协调信号
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: 主题策划                                          │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│ │ PlannerAgent│───▶│ResearchAgent│───▶│ 用户确认    │      │
│ │  (3方案)    │    │  (深度研究) │    │  (选择/修改) │      │
│ └─────────────┘    └─────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: 大纲规划                                          │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│ │OutlineAgent │───▶│ 用户确认    │───▶│ StyleLearner│      │
│ │  (结构+SEO) │    │  (审核大纲) │    │  (注入风格) │      │
│ └─────────────┘    └─────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: 内容写作                                          │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│ │ WriterAgent │───▶│ 用户预览    │───▶│ PolishAgent │      │
│ │  (完整正文) │    │  (实时查看) │    │  (去AI+GEO) │      │
│ └─────────────┘    └─────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 4: 质量审查                                           │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│ │ReviewAgent  │───▶│ 评分判定    │───▶│ 循环修改?   │      │
│ │  (6维度)   │    │ ≥85分通过   │    │ (<85触发返回)│      │
│ └─────────────┘    └─────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 5: 配图封面                                          │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│ │ ImageAgent  │───▶│ 用户确认    │───▶│PublishAgent │      │
│ │ (色系+风格) │    │  (配图方案) │    │  (排版输出) │      │
│ └─────────────┘    └─────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 最终输出                                                    │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│ │ 文章预览    │    │ 质量报告    │    │ SEO分析     │      │
│ │ (完整)     │    │ (6维雷达)   │    │ (4项评分)   │      │
│ └─────────────┘    └─────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 用户确认节点

| 节点 | 内容 | 操作 |
|------|------|------|
| **确认点1** | 策划方案（3个选项） | 选择/修改/重新生成 |
| **确认点2** | 文章大纲 | 接受/修改/重新生成 |
| **确认点3** | 文章初稿预览 | 预览/触发润色 |
| **确认点4** | 润色稿+质量报告 | 确认/触发修改 |
| **确认点5** | 配图方案 | 确认/修改 |
| **确认点6** | 最终发布稿 | 确认/导出 |

---

## 四、每个Agent详细设计

### 4.1 LeadAgent

```python
class LeadAgent:
    """主导Agent：协调整个创作流程"""

    def run(self, input_data: dict) -> AgentResult:
        """
        输入: {"topic": "主题", "user_preferences": {...}}
        输出: AgentResult with full pipeline status
        """
        # 1. 初始化MessageHub
        hub = MessageHub()
        hub.set_session(f"momo-{int(time.time())}")

        # 2. 广播开始状态
        hub.publish(MessageType.STATUS, {
            "agent": "LeadAgent",
            "status": "started",
            "progress": "漠玫创作开始..."
        })

        # 3. 触发PlannerAgent
        planner = PlannerAgent(hub=hub, llm_client=self.llm_client)
        plan_result = planner.run({"topic": input_data["topic"], "num_options": 3})

        # 4. 等待用户确认（阻塞）
        confirmed_plan = self.wait_for_confirmation(plan_result, "plan")

        # 5. 触发ResearchAgent
        researcher = ResearchAgent(hub=hub, llm_client=self.llm_client)
        research_result = researcher.run({
            "topic": confirmed_plan["topic"],
            "keywords": confirmed_plan.get("seo_keywords", [])
        })

        # 6. 触发OutlineAgent
        outline_agent = OutlineAgent(hub=hub, llm_client=self.llm_client)
        outline_result = outline_agent.run({
            "topic": confirmed_plan["topic"],
            "research": research_result.output,
            "style_instructions": self.load_style_instructions()
        })

        # 7. 等待用户确认
        confirmed_outline = self.wait_for_confirmation(outline_result, "outline")

        # 8. 触发WriterAgent
        writer = WriterAgent(hub=hub, llm_client=self.llm_client)
        write_result = writer.run({
            "outline": confirmed_outline,
            "style_instructions": self.load_style_instructions()
        })

        # 9. 触发PolishAgent
        polisher = PolishAgent(hub=hub, llm_client=self.llm_client)
        polish_result = polisher.run({"draft": write_result.output})

        # 10. 触发ReviewAgent（质量门禁）
        reviewer = ReviewAgent(hub=hub, llm_client=self.llm_client)
        review_result = reviewer.run({"polished": polish_result.output})

        # 11. 质量判定循环
        while review_result.output["total_score"] < 85:
            # 返回修改
            revision_result = self.handle_revision(
                review_result.output["issues"],
                write_result.output
            )
            write_result = revision_result
            polish_result = polisher.run({"draft": write_result.output})
            review_result = reviewer.run({"polished": polish_result.output})

        # 12. 触发ImageAgent + PublishAgent
        image_agent = ImageAgent(hub=hub, llm_client=self.llm_client)
        image_result = image_agent.run({"topic": confirmed_plan["topic"]})

        publisher = PublishAgent(hub=hub)
        final_result = publisher.run({
            "article": review_result.output,
            "images": image_result.output
        })

        return AgentResult(success=True, output=final_result)
```

### 4.2 PlannerAgent

```python
class PlannerAgent:
    """主题策划Agent"""

    PROMPT_TEMPLATE = """
# 漠玫创作 · 主题策划Agent

## 你的任务
基于用户提供的初步主题，生成3个差异化的创作方案。

## 输出格式
每个方案包含：
1. **主题标题** — 吸引目标读者的标题
2. **受众画像** — 核心读者是谁？他们关心什么？
3. **独特角度** — 为什么这个角度值得写？
4. **内容承诺** — 读者能得到什么？
5. **内容调性** — 轻松/专业/深度/实用性

## 写作风格约束（来自风格学习）
{style_instructions}

## 禁止使用的AI词汇（去AI味）
- 词汇表Tier1（发现即替换）：delve, leverage, robust, comprehensive,
  crucial, pivotal, showcase, foster, intricate, vibrant, paradigm,
  tapestry, beacon, symphony, utilize, embark, commence, ascertain,
  endeavor, catalyze, facilitate, bolster, spearhead, unleash, galvanize

- 过渡词：Moreover, Furthermore, Additionally, In conclusion,
  It is worth noting that, Despite challenges, At the end of the day

## 输出
返回3个方案，每个包含：topic, target_audience, unique_angle,
content_promise, tone, title_options
"""
```

### 4.3 ResearchAgent

```python
class ResearchAgent:
    """深度研究Agent"""

    def run(self, input_data: dict) -> AgentResult:
        """
        输入: {"topic": "...", "keywords": [...]}
        输出: 研究报告（含Tavily搜索结果+Obsidian知识+风格参考）
        """
        topic = input_data["topic"]
        keywords = input_data.get("keywords", [])

        # 1. Tavily深度搜索
        tavily_results = self.tavily_search(topic, keywords, depth="advanced")

        # 2. Obsidian知识库搜索
        obsidian_notes = self.search_obsidian(topic)

        # 3. 已发布文章风格分析
        style_reference = self.analyze_published_articles(topic)

        # 4. 整合研究报告
        report = {
            "tavily_findings": tavily_results,
            "obsidian_notes": obsidian_notes,
            "style_reference": style_reference,
            "recommended_keywords": self.extract_keywords(tavily_results, keywords),
            "key_insights": self.summarize_insights(tavily_results)
        }

        return AgentResult(success=True, output=report)
```

### 4.4 OutlineAgent

```python
class OutlineAgent:
    """大纲规划Agent"""

    PROMPT_TEMPLATE = """
# 漠玫创作 · 大纲规划Agent

## 任务
基于策划方案和研究报告，生成完整的文章大纲。

## 输入
- 主题：{topic}
- 目标读者：{target_audience}
- 研究报告：{research_report}
- SEO关键词：{seo_keywords}

## 大纲结构要求
1. **开头钩子** — 用什么吸引读者？（场景/问题/数据/故事）
2. **H2段落** — 每个H2包含：
   - 段落主题
   - 关键论点（3-5个）
   - 字数目标
   - SEO关键词融入
3. **结尾** — 如何收尾？（总结/行动召唤/开放式）

## SEO关键词布局
- 核心关键词（出现3-5次）
- 长尾关键词（出现1-2次）
- 关键词密度：1-2%

## 去AI味检查
- 避免规则三强迫症
- 句长要有变化（短句+长句混合）
- 标题用句子大小写（非全大写）

## 输出格式
{
    "title": "文章标题",
    "opening_hook": "开头钩子描述",
    "outline": [
        {
            "h2": "H2标题",
            "key_points": ["要点1", "要点2"],
            "word_target": 500,
            "seo_keywords": ["关键词1", "关键词2"]
        }
    ],
    "closing": "结尾方案",
    "seo_keywords": {"primary": "...", "secondary": [...]}
}
"""
```

### 4.5 WriterAgent

```python
class WriterAgent:
    """内容写作Agent"""

    PROMPT_TEMPLATE = """
# 漠玫创作 · 内容写作Agent

## 任务
根据大纲，写出完整的公众号文章正文。

## 输入
- 大纲：{outline}
- 目标读者：{target_audience}
- 风格指令：{style_instructions}

## 写作风格（来自已发布文章分析）
- 句长：平均15-25字，短句40%，长句25%
- 口语化词：其实、大概、感觉、就是、不过、挺
- 第一人称：极高（我觉得、我发现、我记得）
- 段落结构：无H2层级，碎片化段落，短则一句
- 开头模式：场景切入 / 感悟开篇 / 日期/节气
- 情感表达：克制内敛，自嘲式幽默，让读者自己感受

## 去AI味核心规则
1. **句长变化**：必须混合短句（3-8字）和长句（20+字）
2. **具体化**：用数字、名字、日期替代模糊表述
3. **有声音**：有观点、偏好、反应
4. **赢得强调**：让内容本身有趣，不告诉读者什么有趣
5. **节奏感**：不要每个段落都是3-5句均匀分布

## AI词汇替换表（Tier1）
- delve → explore, dig into
- leverage → use
- robust → strong, reliable
- comprehensive → thorough, complete
- crucial → important, key
- utilize → use
- showcase → show, demonstrate
- foster → encourage, support
- pivotal → important, key

## 格式要求
- 使用标准Markdown
- H2用句子大小写（首字母大写即可）
- 加粗仅用于真正重要的词，每个H2最多一个
- 列表仅用于真正的列表内容

## 输出
{
    "title": "文章标题",
    "content": "完整Markdown正文",
    "word_count": 字数,
    "h2_count": H2数量,
    "ai_patterns_check": ["检测到的AI模式"]
}
"""
```

### 4.6 PolishAgent

```python
class PolishAgent:
    """润色优化Agent"""

    PROMPT_TEMPLATE = """
# 漠玫创作 · 润色优化Agent

## 任务
对初稿进行三重优化：去AI味 + GEO优化 + SEO强化

## 输入
- 初稿：{draft}
- SEO关键词：{seo_keywords}

## Phase 1: 去AI味（P0优先）

### P0 — 信誉杀手（立即修复）
- 截断免责声明（"As of my last update"）
- Chatbot残留（"I hope this helps!", "Great question!"）
- 模糊归因无来源（"Experts believe"）
- 意义膨胀（对常规事件夸大）

### P1 — 明显AI味（发布前修复）
- 词汇表违规（delve, leverage, robust等）
- "Let's" 过渡开场白
- 同段内同义词循环
- 公式化开头（"In the rapidly evolving world of..."）
- 加粗滥用、破折号>1/千字

### P2 — 风格抛光（时间允许）
- 通用结论（"The future looks bright"）
- 规则三强迫症
- 过渡词（Moreover, Furthermore, Additionally）

## Phase 2: GEO优化（AI引用优化）

### 使内容更易被AI引用
- 使用定义性陈述句
- 添加具体数据和案例
- 创造引用性短语（"根据X研究..."）
- 使用FAQ模式（问题+明确答案）

## Phase 3: SEO强化

### 关键词检查
- 核心关键词出现3-5次
- 长尾关键词出现1-2次
- 关键词密度1-2%
- 关键词在标题、H2、前100字中

### 内链建议
- 添加相关内链占位符

## 输出格式
{
    "polished_content": "润色后Markdown",
    "ai_patterns_removed": ["移除的AI模式列表"],
    "geo_improvements": ["GEO改进点"],
    "seo_score": 1-100,
    "changes_summary": "主要修改摘要"
}
"""
```

### 4.7 ReviewAgent

```python
class ReviewAgent:
    """质量审查Agent"""

    # 6维度评分标准（基于CORE-EEAT 80项简化）
    DIMENSIONS = {
        "contextual_clarity": {
            "name": "上下文清晰度",
            "weight": 0.20,
            "description": "主题明确、逻辑连贯、读者知道在读什么"
        },
        "organization": {
            "name": "结构组织",
            "weight": 0.15,
            "description": "开头钩子有力、H2结构清晰、结尾有收尾"
        },
        "referenceability": {
            "name": "可引用性",
            "weight": 0.15,
            "description": "有数据/案例/来源、容易被引用"
        },
        "exclusivity": {
            "name": "排他性/原创",
            "weight": 0.15,
            "description": "独特视角、非泛泛而谈、有个人见解"
        },
        "writing_quality": {
            "name": "写作质量",
            "weight": 0.20,
            "description": "去AI味达标、句长变化、有声音有观点"
        },
        "seo_geo": {
            "name": "SEO/GEO优化",
            "weight": 0.15,
            "description": "关键词布局合理、有结构化数据、有引用性内容"
        }
    }

    def run(self, input_data: dict) -> AgentResult:
        polished = input_data["polished"]

        # 逐维度评分
        scores = {}
        for dim_key, dim_info in self.DIMENSIONS.items():
            score = self.evaluate_dimension(polished, dim_key, dim_info)
            scores[dim_key] = score

        # 计算总分
        total_score = sum(
            scores[dim] * self.DIMENSIONS[dim]["weight"]
            for dim in scores
        )

        # 生成详细报告
        report = {
            "total_score": round(total_score, 1),
            "dimension_scores": {
                self.DIMENSIONS[dim]["name"]: {
                    "score": scores[dim],
                    "max": 100,
                    "weight": self.DIMENSIONS[dim]["weight"],
                    "issues": self.get_issues(dim, scores[dim])
                }
                for dim in scores
            },
            "pass": total_score >= 85,
            "issues": self.get_all_issues(scores),
            "recommendations": self.get_recommendations(scores)
        }

        return AgentResult(success=True, output=report)
```

### 4.8 ImageAgent

```python
class ImageAgent:
    """配图封面Agent"""

    def run(self, input_data: dict) -> AgentResult:
        topic = input_data["topic"]

        # 1. 封面设计
        cover_design = self.design_cover(topic)

        # 2. 配图风格建议
        image_style = self.suggest_image_style(topic)

        # 3. 配图位置规划
        image_positions = self.plan_image_positions(topic)

        result = {
            "cover": cover_design,
            "image_style": image_style,
            "image_positions": image_positions
        }

        return AgentResult(success=True, output=result)

    def design_cover(self, topic: str) -> dict:
        """设计封面"""
        # 基于主题生成配色方案
        color_palette = self.generate_color_palette(topic)

        return {
            "size": "900x383",  # 公众号封面比例
            "color_palette": color_palette,
            "layout": "centered_title",  # 或 split_image, text_only
            "font": "思源黑体",
            "suggestions": [
                "使用{color}作为主色调",
                "标题字数控制在10字以内",
                "添加简单背景图形增加层次感"
            ]
        }

    def suggest_image_style(self, topic: str) -> dict:
        """建议配图风格"""
        return {
            "style": "photography / illustration / infographic",
            "mood": "warm / professional / fresh",
            "color_scheme": "consistent with cover palette",
            "size_guide": {
                "header": "900x383",
                "inline": "800x450",
                "full_width": "900x500"
            }
        }
```

### 4.9 PublishAgent

```python
class PublishAgent:
    """排版输出Agent"""

    def run(self, input_data: dict) -> AgentResult:
        article = input_data["article"]
        images = input_data["images"]

        # 1. 应用排版模板
        formatted = self.apply_formatting(article, images)

        # 2. 生成话题标签
        hashtags = self.generate_hashtags(article)

        # 3. 生成完整预览
        preview = {
            "title": formatted["title"],
            "cover_image": images["cover"],
            "content": formatted["html"],
            "hashtags": hashtags,
            "word_count": formatted["word_count"]
        }

        # 4. 生成SEO报告
        seo_report = self.generate_seo_report(article)

        # 5. 生成质量报告（6维度雷达）
        quality_report = self.generate_quality_report(article)

        return AgentResult(success=True, output={
            "preview": preview,
            "seo_report": seo_report,
            "quality_report": quality_report,
            "files": {
                "markdown": formatted["markdown_path"],
                "html": formatted["html_path"],
                "meta": formatted["meta_path"]
            }
        })
```

---

## 五、用户交互界面设计

### 5.1 CLI交互流程

```bash
# 启动创作
huage-gzh create "你的文章主题"

# 预期输出：
# ============================================================
#   漠玫创作 · 公众号多Agent协同创作系统
# ============================================================
#
# 🔄 [LeadAgent] 启动中...
# 🔄 [PlannerAgent] 主题策划中...
#
# ─── ① 主题策划 ───
# ✅ [PlannerAgent] 完成（生成3个方案）
#
# ============================================================
# 📋 方案A：如何通过刻意练习快速掌握新技能
# ============================================================
# 目标读者：25-35岁职场人，想提升但时间有限
# 独特角度：从"1万小时定律"误区切入，实用主义
# 内容承诺：3个可立刻实践的微练习方法
# 调性：实用、有数据支撑、轻松
#
# 📣 标题选项：
#   1. 别再盲目练习了！高效学习只需要这3步
#   2. 为什么你看了100本书，生活还是没改变
#   3. 从"知道"到"做到"，只差这一步
#
# ────────────────────────────────────────────────────────
# 选择：A/B/C/重新生成/修改主题
# > _
```

### 5.2 实时状态显示

每个Agent工作时，实时显示：

```bash
🔄 [WriterAgent] 写作中...
   📝 已完成：引言部分（~200字）
   📝 进行中：H2-1「什么是刻意练习」（~500字）
   ⏳ 等待中：H2-2「3个微练习方法」
   ⏳ 等待中：H2-3「如何坚持」
```

### 5.3 质量报告展示

```
============================================================
📊 质量报告
============================================================

总评分：87/100 ✅ 通过

┌─────────────────────────────────────────────────────────┐
│                    6维雷达评分                          │
│                                                         │
│              上下文清晰度 ████████████░░ 92             │
│              结构组织     ██████████░░░░░ 85             │
│              可引用性     █████████░░░░░░ 78             │
│              排他性/原创  ████████████░░ 88             │
│              写作质量     ██████████░░░░░ 82             │
│              SEO/GEO优化  █████████░░░░░░ 80             │
│                                                         │
└─────────────────────────────────────────────────────────┘

⚠️ 建议改进：
1. 可引用性（78分）：添加2-3个具体数据来源
2. 写作质量（82分）：第3段句长过于均匀，增加变化

───────────────────────────────────────────────────────────
📈 SEO分析
───────────────────────────────────────────────────────────
SEO评分：85/100 ✅
GEO评分：82/100 ✅
去AI味：88/100 ✅
可读性：90/100 ✅

核心关键词「刻意练习」出现次数：4次（推荐3-5次）
关键词密度：1.8%（推荐1-2%）
```

### 5.4 最终预览

```bash
============================================================
📄 文章预览
============================================================

【封面图】
┌─────────────────────────────────────────────────────────┐
│                                                         │
│          别再盲目练习了！高效学习只需要这3步             │
│                                                         │
│          📷 [自动生成的封面图]                          │
│                                                         │
└─────────────────────────────────────────────────────────┘

【标题】别再盲目练习了！高效学习只需要这3步

【正文】
...（完整文章内容）...

【话题标签】
#高效学习 #刻意练习 #职场成长 #自我提升

【配图】
📷 图1：刻意练习 vs 普通练习对比图（P2）
📷 图2：3个微练习方法图解（P5）
📷 图3：坚持21天打卡记录（P8）

============================================================
✅ 创作完成！文件已保存至：
   outputs/2026-04-13-huage/create/
   ├── article.md      # Markdown源文件
   ├── article.html    # HTML排版文件
   ├── quality.json    # 质量报告
   └── seo.json        # SEO分析报告
============================================================
```

---

## 六、质量门禁设计

### 6.1 评分标准

| 维度 | 权重 | 评分规则 | 达标线 |
|------|------|----------|--------|
| 上下文清晰度 | 20% | 主题明确30%+逻辑连贯35%+读者友好35% | 75 |
| 结构组织 | 15% | 开头有力25%+H2清晰50%+结尾有收25% | 75 |
| 可引用性 | 15% | 有数据/案例30%+来源可靠30%+易引用40% | 75 |
| 排他性/原创 | 15% | 独特视角30%+个人见解40%+非泛泛30% | 75 |
| 写作质量 | 20% | 去AI味40%+句长变化30%+有声音30% | 75 |
| SEO/GEO优化 | 15% | 关键词布局25%+结构化数据25%+引用性50% | 75 |

### 6.2 门禁判定

```
总分 = Σ(维度分数 × 权重)

✅ 通过：总分 ≥ 85
⚠️ 修改：75 ≤ 总分 < 85（触发小修）
❌ 返回：总分 < 75（触发大改）
```

### 6.3 修改循环

```python
def handle_revision(issues: list, draft: dict) -> dict:
    """处理修改请求"""
    # 分类问题
    critical = [i for i in issues if i["severity"] == "critical"]
    major = [i for i in issues if i["severity"] == "major"]
    minor = [i for i in issues if i["severity"] == "minor"]

    if critical:
        # 大改：重新调用WriterAgent
        return rewrite_with_feedback(draft, critical + major)
    elif major:
        # 中改：调用PolishAgent针对性修改
        return polish_with_feedback(draft, major)
    else:
        # 小改：自动修复
        return auto_fix(draft, minor)
```

---

## 七、文件输出格式

### 7.1 输出目录结构

```
outputs/{date}-{topic-slug}/
├── article.md           # Markdown源文件（编辑用）
├── article.html          # HTML排版文件（发布用）
├── quality.json          # 质量报告（6维雷达数据）
├── seo.json              # SEO分析报告
├── images/
│   ├── cover.png         # 封面图
│   ├── image-1.png       # 内嵌配图1
│   ├── image-2.png       # 内嵌配图2
│   └── ...
└── meta.json             # 完整元数据
```

### 7.2 article.md格式

```markdown
---
title: "别再盲目练习了！高效学习只需要这3步"
date: 2026-04-13
tags: [高效学习, 刻意练习, 职场成长]
cover: ./images/cover.png
word_count: 2500
reading_time: "8分钟"
---

# 别再盲目练习了！高效学习只需要这3步

> 📌 配图位置：P2「刻意练习 vs 普通练习对比图」

## 开头钩子

你有没有过这种经历？
...

## H2标题

### H2-1标题

内容...

> 📌 配图位置：P5「3个微练习方法图解」

### H2-2标题

内容...

...
```

### 7.3 quality.json格式

```json
{
  "generated_at": "2026-04-13T18:00:00Z",
  "total_score": 87,
  "pass": true,
  "dimensions": {
    "contextual_clarity": {
      "score": 92,
      "name": "上下文清晰度",
      "issues": []
    },
    "organization": {
      "score": 85,
      "name": "结构组织",
      "issues": [
        {"type": "minor", "location": "H2-3", "suggestion": "结尾略显仓促，建议增加总结句"}
      ]
    }
  },
  "ai_patterns": {
    "removed_count": 12,
    "remaining": ["em_dash_overuse"]
  },
  "seo": {
    "keyword_density": 1.8,
    "primary_keyword_count": 4
  }
}
```

---

## 八、实施计划（修订版 v1.1）

> 更新：2026-04-13
> 按数据流重新划分Phase，每个Phase有独立产出，可小步验证

### Phase划分



### Phase 1：核心框架（1-2天）

**目标**：建立空跑流程骨架，用户确认节点可用

| 组件 | 文件 | 状态 |
|------|------|------|
| LeadAgent | agents/lead_agent.py | 新建 |
| MessageHub扩展 | core/message_hub.py | 已有-扩展 |
| CLI增强 | cli.py | 已有-扩展 |
| 用户确认节点 | core/confirm_nodes.py | 新建 |

**产出**：
- huage-gzh create 测试 能完整空跑
- 每个Agent状态实时显示
- 6个用户确认节点正常工作

**验收标准**：
- [ ] --dry-run 模式完整执行，输出流程图
- [ ] 6个用户确认节点都能响应输入
- [ ] MessageHub正确广播/订阅状态

### Phase 2：写作Pipeline（2-3天）

**目标**：完成初稿生成（不含润色）

| 组件 | 文件 | 状态 |
|------|------|------|
| PlannerAgent | agents/planner_agent.py | 新建 |
| ResearchAgent | agents/research_agent.py | 新建 |
| OutlineAgent | agents/outline_agent.py | 新建 |
| WriterAgent | agents/writer_agent.py | 新建 |
| Tavily集成 | core/tavily_client.py | 新建 |
| Obsidian搜索 | core/obsidian_search.py | 新建 |

**产出**：主题 → 3方案 → 研究报告 → 大纲 → 完整初稿

**验收标准**：
- [ ] PlannerAgent生成3个差异化方案
- [ ] ResearchAgent整合Tavily + Obsidian + 风格分析
- [ ] OutlineAgent生成含SEO关键词的大纲
- [ ] WriterAgent写出符合风格要求的初稿

### Phase 3：质量Pipeline（2-3天）

**目标**：完成质量门禁，产出通过审查的终稿

| 组件 | 文件 | 状态 |
|------|------|------|
| PolishAgent | agents/polish_agent.py | 新建 |
| ReviewAgent | agents/review_agent.py | 新建 |
| 质量门禁循环 | core/review_loop.py | 新建 |
| 去AI味检测 | core/ai_pattern_checker.py | 新建 |

**产出**：初稿 → 润色稿 → 6维质量报告 → 终稿（<85自动修改）

**验收标准**：
- [ ] PolishAgent移除36种AI模式
- [ ] ReviewAgent 6维评分与人工判断一致
- [ ] 质量循环正常工作（<85触发修改，≥85通过）

### Phase 4：输出Pipeline（1-2天）

**目标**：完成可发布的完整文章包

| 组件 | 文件 | 状态 |
|------|------|------|
| ImageAgent | agents/image_agent.py | 新建 |
| PublishAgent | agents/publish_agent.py | 新建 |
| 排版模板 | publishers/wechat_template.py | 新建 |
| SEO报告 | core/seo_reporter.py | 新建 |

**产出**：终稿 + 封面 + 配图 → 完整发布包（md + html + json）

**验收标准**：
- [ ] ImageAgent生成封面设计方案
- [ ] PublishAgent输出符合公众号格式的HTML
- [ ] 终端预览有质量雷达图和SEO分析

### 依赖关系



---

**计划状态**：v1.1 已修订
**下一步**：Phase 1 实现

---

## 九、技术约束## 九、技术约束

### 9.1 依赖

```txt
# requirements.txt
dashscope>=1.14.0        # 通义千问API
tavily-python>=0.3.0     # Tavily搜索API
openai>=1.0.0            # 通用LLM接口（备用）
typer>=0.9.0             # CLI框架
rich>=13.0.0             # 富文本输出
pillow>=10.0.0           # 图片处理
python-dotenv>=1.0.0     # 环境变量
```

### 9.2 环境变量

```bash
# .env.example
DASHSCOPE_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
OBSIDIAN_VAULT_PATH=/path/to/your/vault
DEFAULT_ARTICLE_DIR=/path/to/published/articles
```

### 9.3 速率限制

- Tavily搜索：20请求/分钟
- 通义千问：最大并发3请求
- 重试策略：指数退避（1s, 2s, 4s, 8s）

---

## 十、错误处理

### 10.1 错误分类

| 错误类型 | 处理策略 |
|----------|----------|
| LLM超时 | 降级到模板模式 + 提示用户 |
| Tavily失败 | 使用本地搜索替代 + 警告 |
| 质量不达标 | 循环修改（最多3次） |
| 用户中断 | 保存当前状态到checkpoint |

### 10.2 降级模式

```python
class FallbackMode:
    TEMPLATE = "template"      # 使用预设模板
    LOCAL_ONLY = "local_only"   # 仅使用本地知识
    MINIMAL = "minimal"        # 最简输出
```

---

## 十一、扩展方向

### 11.1 短期（1个月）

- 多平台适配（小红书、知乎、微博）
- 图片生成API集成（Midjourney、Stable Diffusion）
- 历史文章分析自动更新风格

### 11.2 中期（3个月）

- 多语言版本生成
- A/B标题测试
- 读者互动分析

### 11.3 长期（6个月）

- 个性化推荐引擎
- 自动化发布到多平台
- 数据驱动的选题建议

---

## 附录

### A. 去AI味词汇表（完整）

**Tier 1（发现即替换）**

| 原文 | 替换 |
|------|------|
| delve / delve into | explore, dig into, look at |
| leverage（动词）| use |
| utilize | use |
| robust | strong, reliable, solid |
| comprehensive | thorough, complete, full |
| crucial | important, key |
| pivotal | important, key, critical |
| showcase | show, demonstrate |
| foster | encourage, support, build |
| intricate | complex, detailed |
| vibrant | （描述具体特征）|
| paradigm | model, approach, framework |
| tapestry | （描述实际内容）|
| beacon | （完全重写）|
| symphony | （描述实际协调）|
| utilize | use |
| embark | start, begin |
| commence | start, begin |
| ascertain | find out, determine |
| endeavor | effort, attempt |
| catalyze | start, trigger |
| facilitate | enable, help, allow |
| bolster | support, strengthen |
| spearhead | lead, drive |
| unleash | release, enable |
| elevate | improve, raise |
| galvanize | motivate, rally |
| augment | add to, expand |
| cultivate | build, develop |
| illuminate | clarify, explain |
| elucidate | explain, clarify |
| juxtapose | compare, contrast |

**Tier 2（2个以上同段时替换）**

harness, navigate, foster, elevate, streamline, empower, bolster, spearhead, resonate, revolutionize, facilitate, underpin, nuanced, ecosystem, myriad, plethora, catalyze, reimagine, cornerstone, paramount

**Tier 3（高密度时替换）**

significant, innovative, effective, dynamic, scalable, compelling, unprecedented, exceptional, remarkable, sophisticated

### B. 已发布文章风格摘要

基于张二冬公众号文章分析：

- **开头模式**：场景切入（"早起开门看见..."）/ 感悟开篇 / 节气点题
- **句长特征**：平均15-25字，短句40%，长句25%
- **口语词**：其实、大概、感觉、就是、不过、挺
- **段落结构**：碎片化，无H2层级，短段落为主
- **情感表达**：克制内敛，自嘲式幽默，让读者自己感受
- **结尾方式**：开放式/诗意留白，不给标准答案

---

**计划状态**：✅ 已完成
**下一步**：等待用户确认后进入 Phase 1 实现
