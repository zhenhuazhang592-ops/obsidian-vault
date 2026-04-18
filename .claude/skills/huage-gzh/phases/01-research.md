# Phase 01：深度研究（Wiki + Tavily + YouTube）

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

### Step 0：Wiki 知识检索（新增）

在开始外部研究前，先查询 wiki 中已有知识，避免重复研究，复用已编译的知识。

**执行步骤**：

1. 调用 `/wiki-query [topic]` 获取相关页面
2. 读取匹配的 `wiki/sources/`、`wiki/entities/`、`wiki/concepts/` 页面
3. 提取已有知识：核心观点、引用、数据
4. 输出到 `[输出目录]/00-wiki-知识.md`

**输出格式**：

```markdown
---
date: YYYY-MM-DD
topic: [主题]
source: wiki
pages_used: [页面列表]
---

# Wiki 已有知识 · [主题]

## 相关概念

- [[ConceptName]] — 定义和关键原则

## 相关实体

- [[EntityName]] — 关联信息

## 可用引用

> "[引用内容]" — 来源

## 知识缺口（需要外部补充）

- [缺口1]
- [缺口2]
```

**如果 wiki 中无相关知识**：
- 告知用户"wiki 中暂无相关知识，将进行全新研究"
- 继续执行 Step 1.2-1.4

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

**目标**：主动搜索主题相关视频，提取字幕内容，整理为 Obsidian 笔记。

**依赖安装**：
```bash
# YouTube API（已有）
pip install google-api-python-client

# 字幕提取（新增）
brew install yt-dlp
```

**执行命令**：
```bash
cd /Users/huage/Obsidian\ Vault

python3 .claude/skills/huage-gzh/scripts/youtube_video_research.py \
  "[topic]" \
  --max 5 \
  --lang zh \
  --output "写作知识库/01-资源库/${DATE}/[slug]/02-视频研究/"
```

**脚本能力**（三步合一）：
1. **搜索** — YouTube Data API v3 主动搜索关键词，返回视频列表
2. **字幕** — yt-dlp 抓 auto-subtitle（中文优先，含英文兜底）
3. **输出** — 每个视频生成一个 Obsidian 格式 Markdown，含 frontmatter + 关键观点 + 字幕正文

**降级方案**：如果 `yt-dlp` 不可用：
```bash
python3 .claude/skills/huage-gzh/scripts/youtube_video_research.py \
  "[topic]" \
  --max 5 \
  --lang zh \
  --no-subtitle \
  --output "写作知识库/01-资源库/${DATE}/[slug]/02-视频研究/"
```

**入库**：`02-视频研究/`

输出结构：
```
02-视频研究/
├── 00-索引_xxx_YYYYMMDD_HHMMSS.md   # 视频清单索引
├── 01_youtube_title_1.md            # 视频笔记（含字幕）
├── 02_youtube_title_2.md
└── ...
```

单个视频笔记格式：
```markdown
---
source: "https://www.youtube.com/watch?v=xxx"
type: youtube-video
channel: "频道名"
date: 2026-04-02
views: 12345
tags: ["tag1", "tag2"]
subtitle_length: 1234
---

# 视频标题

**频道**: [频道名](链接)
**链接**: [YouTube](链接)
**发布日期**: 2026-04-02
**播放量**: 12,345

## 视频描述
...

## 关键观点
- 观点1
- 观点2

## 字幕内容
[字幕正文，最多 3000 字截断]
```

**字幕语言优先级**：`zh-Hans` → `zh` → `en`（无中文自动字幕则用英文）

**质量门控**：
- `00-索引_xxx.md` 存在
- 视频笔记 ≥ 3 个
- 如字幕获取率 < 50%，提示用户手动补充视频链接

### Step 1.4：Qwen3-Max 综合研究摘要

收集所有研究文件后，调用 Qwen3-Max 生成综合摘要：

```bash
python3 /Users/huage/Obsidian\ Vault/.claude/skills/huage-gzh/scripts/qwen_client.py \
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

### Step 1.5：知识缺口分析（新增）

对比 wiki 已有知识 vs 外部研究发现，识别增量和新矛盾。

**执行步骤**：

1. 读取 `00-wiki-知识.md` 和 `00-研究索引.md`
2. 识别新发现（wiki 中没有的知识）
3. 识别矛盾（wiki 与外部来源冲突的主张）
4. 输出到 `[输出目录]/00-缺口分析.md`

**输出格式**：

```markdown
---
date: YYYY-MM-DD
topic: [主题]
---

# 知识缺口分析

## Wiki 已覆盖

- [已覆盖1]
- [已覆盖2]

## 新发现（可补充 wiki）

- [新发现1] — 来源：[[外部来源]]
- [新发现2] — 来源：[[外部来源]]

## 矛盾点（需记录）

- [矛盾1]：wiki 说 X，外部来源说 Y
```

**用途**：
- 写作时优先使用 wiki 已编译知识（更可靠）
- 新发现标记为"待补充 wiki"
- 矛盾点在写作中客观呈现

## 研究输出清单

```
[输出目录]/
├── 00-wiki-知识.md        ✅ Wiki 已有知识（新增）
├── 00-研究索引.md         ✅ Qwen3-Max 生成
├── 00-缺口分析.md         ✅ 知识缺口分析（新增）
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
