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
