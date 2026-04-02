# WeChat Master Agent 系统设计

> 一个 Master Agent 调度 5 个专业 Agent，自动生产高质量公众号文章并推送草稿箱。
> 落地形态：纯 Claude Code Skill，零基础设施成本。

---

## 一、架构总览

```
用户: /wechat-master write "主题"
  │
  ▼
Master Orchestrator (wechat-master/SKILL.md)
  │
  │  状态机: INIT → STYLE → RESEARCH → CREATE → QA → VISUAL → PUBLISH → REVIEW
  │  Gate: 用户确认节点 ★ 标记
  │
  ├─ Step 0: 风格配置 ★ ─── Master 内完成，不派发 Agent
  ├─ Step 1: 研究 Agent ★
  ├─ Step 2: 创作 Agent ★
  ├─ Step 3: 质检 Agent（自动）
  ├─ Step 4: 视觉 Agent（自动）
  ├─ Step 5: 发布 Agent ★
  └─ Step 6: 数据闭环（定时/手动）
```

**用户确认节点（Gate ★）共 5 个**：

| Gate | 时机 | 用户操作 |
|------|------|---------|
| G1 | 风格配置 | 确认 6 项风格参数 |
| G2 | 选题选择 | 3 个选题卡选 1 |
| G3 | 标题选择 | A/B 版标题选 1 |
| G4 | 大纲确认 | 确认或调整大纲 |
| G5 | 发布确认 | 确认推送草稿箱 |

---

## 二、5 个 Agent 详细设计

### Agent 1: 研究 Agent（Research Agent）

**职责**：热点扫描 + 知识库检索 + 竞品分析 + SEO 关键词

**输入**：
- 用户提供的主题关键词
- StyleConfig（风格配置）

**执行流程**：
1. 热点扫描：WebSearch 抓取微博/头条/百度当日热点，匹配主题相关性
2. 知识库检索：Grep/Glob 搜索 Obsidian vault 中已有的相关素材
3. 竞品分析：WebSearch 搜索 3-5 篇同主题高质量公众号文章，提取标题/结构/亮点
4. SEO 关键词：生成核心词 + 长尾词列表

**输出**：3 个选题卡（TopicCard）

```yaml
TopicCard:
  topic: "选题标题"
  angle: "切入角度"
  target_reader: "目标读者画像"
  core_argument: "核心观点（一句话）"
  competitors:
    - title: "竞品文章标题"
      source: "来源公众号"
      highlights: "亮点/可借鉴之处"
  keywords:
    core: ["核心词1", "核心词2"]
    long_tail: ["长尾词1", "长尾词2", "长尾词3"]
  vault_refs: ["[[已有笔记1]]", "[[已有笔记2]]"]
  score: 85  # 选题评分（热度×差异化×知识储备）
```

**复用来源**：
- WeWrite `scripts/fetch_hotspots.py` 的三源聚合逻辑（转为 WebSearch 实现）
- WeWrite `references/topic-selection.md` 的三维度评分规则
- gongzhonghao `topic-research.md` 的选题模板

**Gate**: 用户从 3 个选题卡中选 1 个 → 进入创作 Agent

---

### Agent 2: 创作 Agent（Writing Agent）

**职责**：标题生成 + 大纲 + 正文写作

**输入**：
- 选定的 TopicCard
- StyleConfig
- SEO 关键词列表

**执行流程**：

**阶段 A — 标题（Gate ★）**：
1. 生成 A 版（情绪钩子型）× 2 + B 版（干货信任型）× 2 = 4 个标题
2. 每个标题附评分卡（吸引力/点击率/传播性，各 10 分）
3. 用户选定标题

**阶段 B — 大纲（Gate ★）**：
1. 基于选题 + 标题 + 关键词生成完整大纲
2. 大纲结构：开头钩子 → 3-5 个核心章节 → 结尾 CTA
3. 每个章节标注：核心论点 + 素材来源 + 预计字数
4. 用户确认或调整大纲

**阶段 C — 正文**：
1. 按大纲逐章节写作
2. 执行 StyleConfig 风格约束
3. 自然嵌入 SEO 关键词（核心词 3-5 次，长尾词各 1-2 次）
4. 金句植入（每 500 字至少 1 句可传播金句）
5. 总字数控制在 2000-3500 字

**输出**：完整 Markdown 文章（含 frontmatter）

**复用来源**：
- ArticleSkill 的 4 种标题公式 + 3 种文章结构
- ArticleSkill `作者配置模板.md` 的风格系统
- gongzhonghao `title-scoring.md` 的 A/B 评分卡
- gongzhonghao `prompts/outline-template.md` 的大纲模板

---

### Agent 3: 质检 Agent（QA Agent）

**职责**：去 AI 味两轮 + 节奏检测 + 爆款评分

**输入**：创作 Agent 输出的完整文章

**执行流程**：

**R1 — AI 痕迹修复**：
1. 36 类 AI 写作模式检测（avoid-ai-writing 规则体系）
   - 过渡词滥用（首先/其次/此外/综上所述）
   - 填充词（非常/极其/相当）
   - 虚假权威（无来源的"研究表明"）
   - 格式化过度（emoji/加粗过多）
   - 句式单一（连续 3 句同结构）
   - 情感空洞（感叹句过多）
2. 109 词替换表执行（中文本地化版）
3. 逐处修复，生成 FixReport

**R2 — 节奏与质量评分**：
1. 句子长度均匀度检测（80% 在 15-22 字 → 报警）
2. 段落长度均匀度检测
3. 同义词循环检测
4. 朗读流畅度测试

**爆款评分卡**：

| 维度 | 满分 | 说明 |
|------|------|------|
| 自然度 | 20 | AI 痕迹残留程度 |
| 可读性 | 20 | 句式变化 + 节奏感 |
| 信息密度 | 20 | 干货比例 vs 水分 |
| 故事性 | 20 | 是否有场景/案例/人物 |
| 传播力 | 20 | 金句数量 + 情绪触发点 |

**Gate**: 总分 < 60 → 退回创作 Agent 重写（附修改指令）

**复用来源**：
- avoid-ai-writing 的 36 类模式 + 109 词替换表 + 两轮检测机制
- ai-taste.md 规则（已在 rules/ 中）
- gongzhonghao `humanizer-rules.md`

---

### Agent 4: 视觉 Agent（Visual Agent）

**职责**：章节配图 + 封面图

**输入**：质检通过的完整文章

**执行流程**：

**章节配图**：调用 `baoyu-article-illustrator` skill
- 参数：文章路径 + type（auto） + style（auto） + density（balanced: 3-5 张）
- 后端：豆包 Doubao Seedream 5.0（主）/ Gemini（备）
- 输出：`illustrations/{slug}/*.png`，自动插入文章引用
- 约束：相邻配图间隔 >= 300 字，不在开头和结尾 CTA 处放图
- 前置条件：EXTEND.md 已配置（首次使用时初始化）

**封面图**：调用 `baoyu-cover-image` skill
- 参数：文章路径 + `--aspect 16:9` + `--text title-only`
- 后端：同上
- 输出：`cover-image/{slug}/cover.png`（1920×800，裁剪为 900×383）
- 约束：无写实人物、留白 40-60%、使用原始标题

**降级策略**：API 失败 → 重试 1 次 → 仍失败则占位图 + 提示用户手动配图

---

### Agent 5: 发布 Agent（Publish Agent）

**职责**：自研排版 + Obsidian 保存 + 草稿箱推送 + 数据回收

**输入**：带配图的完整文章 + 封面图

**执行流程**：

**阶段 A — 自研排版引擎**：

技术栈：Python（markdown + BeautifulSoup4 + cssutils + Pygments）

```
YAML 主题文件
  ↓ theme.py 读取 + CSS 变量替换
cssutils 解析为 {selector: {prop: value}} 字典
  ↓
markdown 库将 .md 转为标准 HTML
  ↓
BeautifulSoup 遍历 DOM，逐元素匹配选择器 → 注入内联 style
  ↓
输出：纯内联样式 HTML（微信兼容）
```

微信平台适配规则：
- 全量内联样式（禁用 `<style>` / `<link>`）
- 禁用 JS、position:fixed/sticky、transform、animation、filter
- 字体 >= 15px，图片宽度自适应
- 颜色用 `#hex`（不用 `rgba()`）
- 表格 <= 4 列
- 代码块用 Pygments 高亮

初始主题（4 套，YAML 自定义）：
1. professional-clean — 蓝色系，适合干货/科技
2. tech-modern — 紫蓝渐变，适合 AI/技术
3. warm-editorial — 暖橙，适合生活方式/故事
4. minimal — 黑白极简，适合深度长文

**阶段 B — 保存到 Obsidian vault**：
- 路径：`01-输出内容/公众号/已发布/YYYY-MM-DD-标题.md`
- frontmatter 包含：created, tags, status, title, keywords, score, theme

**阶段 C — 推送微信草稿箱（Gate ★）**：
1. 上传封面图 → 获取 `thumb_media_id`（永久素材）
2. 上传内文图片 → 替换 HTML 中 src 为微信 URL
3. 创建草稿（title / author / digest / content / thumb_media_id）
4. 返回草稿预览链接

微信 API 封装：
- access_token 获取 + 本地缓存（有效期 6900s，提前 5 分钟刷新）
- 图片上传含 2MB 大小检查 + 自动压缩
- 错误码处理（40001/40164/40007）

**阶段 D — 数据回收（手动或定时触发）**：
- `/wechat-master review` 命令触发
- 抓取阅读/转发/点赞/收藏数据
- 生成复盘卡：哪些段落阅读完成率高，哪些流失
- 学习循环：高分文章的特征 → 更新 StyleConfig 偏好

---

## 三、状态机与 Agent 间数据传递

### 状态机

```
INIT
 ↓ 用户输入主题
STYLE_CONFIG ★
 ↓ 风格确认
RESEARCH ★
 ↓ 选题确认
TITLE_SELECT ★
 ↓ 标题确认
OUTLINE_CONFIRM ★
 ↓ 大纲确认
WRITING
 ↓ 正文完成
QA_R1
 ↓ R1修复完成
QA_R2
 ↓ 评分>=60 → 继续 / <60 → 回退 WRITING
VISUAL
 ↓ 配图+封面完成
PUBLISH ★
 ↓ 用户确认推送
DONE
```

### 数据传递格式

Agent 间通过 JSON 状态对象传递：

```yaml
SessionState:
  topic: "主题关键词"
  style_config:
    tone: "朋友聊天"
    professional: "中"
    narrative: "故事型"
    intro_type: "问题"
    paragraph: "短"
    warmth: "高"
  selected_topic: TopicCard  # 研究Agent输出
  selected_title: "标题文本"
  title_score: {attract: 8, ctr: 9, spread: 7}
  outline: [...]  # 大纲结构
  keywords: {core: [...], long_tail: [...]}
  article_path: "path/to/article.md"  # 创作Agent输出
  qa_score: 75  # 质检Agent输出
  qa_report: "修复报告摘要"
  cover_path: "path/to/cover.png"  # 视觉Agent输出
  illustrations: ["path1.png", "path2.png"]
  html_path: "path/to/output.html"  # 发布Agent输出
  draft_media_id: "微信草稿ID"
  draft_url: "预览链接"
```

---

## 四、Skill 文件结构

```
~/.claude/skills/wechat-master/
├── SKILL.md                    # Master Orchestrator（入口+状态机+路由）
├── manifest.json               # 命令→模块→锚点元数据
├── EXTEND.md                   # 扩展配置（baoyu skills 依赖）
│
├── agents/                     # 5 个 Agent 的独立 Prompt
│   ├── research-agent.md       # 研究 Agent prompt
│   ├── writing-agent.md        # 创作 Agent prompt
│   ├── qa-agent.md             # 质检 Agent prompt
│   ├── visual-agent.md         # 视觉 Agent prompt
│   └── publish-agent.md        # 发布 Agent prompt
│
├── prompts/                    # 可复用的 Prompt 模板
│   ├── topic-card-template.md  # 选题卡模板
│   ├── title-scoring.md        # 标题评分规则
│   ├── outline-template.md     # 大纲模板
│   ├── humanizer-rules.md      # 去AI味规则（36类+109词中文版）
│   └── review-template.md      # 复盘卡模板
│
├── themes/                     # 排版主题（YAML）
│   ├── professional-clean.yaml
│   ├── tech-modern.yaml
│   ├── warm-editorial.yaml
│   └── minimal.yaml
│
├── scripts/                    # 执行脚本
│   ├── converter.py            # 自研排版引擎（md→微信HTML）
│   ├── wechat_api.py           # 微信API封装（token+上传+草稿）
│   ├── publisher.py            # 发布编排（图片上传→HTML回填→创建草稿）
│   └── config.example.sh       # 配置模板（APPID/SECRET）
│
└── references/                 # 参考资料（只读）
    ├── wechat-constraints.md   # 微信平台HTML限制
    ├── writing-frameworks.md   # 写作框架库
    └── style-guide.md          # 风格指南
```

---

## 五、命令列表

| 命令 | 说明 |
|------|------|
| `/wechat-master write "主题"` | 完整流程（12步全链路） |
| `/wechat-master topic "主题"` | 只做选题研究 |
| `/wechat-master title "选题"` | 只做标题生成 |
| `/wechat-master qa path/to/article.md` | 只做质检（去AI味+评分） |
| `/wechat-master publish path/to/article.md` | 只做排版+发布 |
| `/wechat-master review` | 数据回收+复盘 |
| `/wechat-master style` | 配置/修改风格 |

---

## 六、质量门（三道关）

| 关卡 | 位置 | 指标 | 阈值 | 不过怎么办 |
|------|------|------|------|-----------|
| 第一关 | 标题评分 | 吸引力+点击率+传播性 | 总分 >= 20/30 | 自动重新生成 |
| 第二关 | AI 检测 + 爆款评分 | 5维度各20分 | 总分 >= 60/100 | 退回创作Agent重写 |
| 第三关 | 发布前检查 | HTML合规+图片完整+元数据齐全 | 全部通过 | 标记问题，人工修复 |

---

## 七、数据闭环设计

```
发布文章
  ↓ 24h/48h/72h 后
/wechat-master review
  ↓
抓取数据（阅读/转发/点赞/收藏/完读率）
  ↓
生成复盘卡
  ↓
  ├─ 标题 CTR：实际阅读数 / 粉丝数
  ├─ 完读率：完读数 / 阅读数
  ├─ 互动率：(点赞+转发+收藏+评论) / 阅读数
  └─ 对比历史均值
  ↓
学习更新
  ├─ 高分文章 → 提取特征 → 更新 StyleConfig 偏好
  ├─ 低分文章 → 分析原因 → 调整选题/标题策略
  └─ 写入 Obsidian vault 复盘笔记
```

---

## 八、技术依赖

| 依赖 | 用途 | 安装方式 |
|------|------|---------|
| Python 3.10+ | 排版引擎+微信API | 系统已有 |
| markdown (>=3.5) | MD→HTML 解析 | pip install |
| beautifulsoup4 (>=4.12) | HTML DOM 操作 | pip install |
| cssutils (>=2.9) | CSS 解析 | pip install |
| Pygments (>=2.15) | 代码高亮 | pip install |
| Pillow (>=10.0) | 图片压缩 | pip install |
| requests | HTTP 调用 | pip install |
| PyYAML | 主题解析 | pip install |
| baoyu-article-illustrator | 章节配图 | 已安装 skill |
| baoyu-cover-image | 封面图 | 已安装 skill |
| DOUBAO_API_KEY | 图片生成 | 环境变量 |
| 微信 APPID/SECRET | 草稿箱推送 | config.sh |

---

## 九、实施优先级

| 阶段 | 内容 | 预计时间 |
|------|------|---------|
| P0 | Master Orchestrator + 研究Agent + 创作Agent | 第1天 |
| P1 | 质检Agent（去AI味+评分） | 第1天 |
| P2 | 自研排版引擎（converter.py） | 第2天 |
| P3 | 视觉Agent（对接 baoyu skills） | 第2天 |
| P4 | 发布Agent（微信API+草稿箱） | 第3天 |
| P5 | 数据闭环（review 命令） | 第3天 |
| P6 | 端到端测试 + 调优 | 第4天 |

---

## 十、与现有系统的关系

| 现有系统 | 关系 |
|---------|------|
| gongzhonghao skill v2.5 | **被替代**。新系统是全新设计，cherry-pick 了其中的 Prompt 模板 |
| WeWrite | 复用排版引擎设计思路（YAML主题+cssutils+BS4） |
| ArticleSkill | 复用写作方法论（标题公式+文章结构+风格系统） |
| avoid-ai-writing | 复用去AI味规则体系（36类+109词，中文本地化） |
| md2wechat | 参考排版底层代码，但不依赖其 API 服务 |
| baoyu-article-illustrator | 直接调用（配图） |
| baoyu-cover-image | 直接调用（封面） |
