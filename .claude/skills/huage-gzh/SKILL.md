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
| `scripts/youtube_video_research.py` | YouTube 搜索 + 字幕抓取 | `YOUTUBE_API_KEY` + `yt-dlp` |
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
□ yt-dlp 已安装（字幕抓取）：brew install yt-dlp
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

---

## 去AI味规则（Tier 1 必删）

严禁在正文中出现以下词汇，发现即删：

- ~~首先、其次、最后、总之、综上所述~~
- ~~值得注意的是、毋庸置疑、众所周知~~
- ~~非常重要、至关重要~~
- ~~作为一个、让我们~~
- ~~delve、leverage、robust、comprehensive~~

详见：`rules/anti-ai.md`

---

## 预设风格库

| 风格 | 描述 | 去AI味强度 |
|------|------|-----------|
| 亲和力强 | 第一人称"我"、情绪化、适度自嘲、口语化 | 高 |
| 专业严谨 | 数据支撑、客观分析、逻辑严密、专业术语 | 中 |
| 幽默风趣 | 轻松调侃、生动比喻、口语化、适度吐槽 | 高 |
| 极简干货 | 精炼直击要点、少修饰、强化逻辑结构 | 低 |

---

## 输出路径规范

所有输出存入：`写作知识库/01-资源库/[YYYY-MM-DD]/[文章标题-slug]/`

```
[slug]/
├── 00-研究索引.md         # Qwen3-Max 综合研究摘要
├── 01-文章研究/          # 10-20篇文章来源
├── 02-视频研究/          # YouTube 视频整理
├── 03-学术参考/          # 学术论文摘要
├── 04-风格与大纲.md      # 确认的风格+标题+大纲
├── 05-正文.md           # 写好的文章
├── 06-封面图/           # 封面图
├── 07-配图/             # 配图
└── 08-排版预览/          # HTML 排版预览
    └── index.html
```

---

## 质量门控

每个 Phase 完成后必须通过以下检查再进入下一步：

- **Phase 01**：`00-研究索引.md` 存在，研究材料 ≥ 10 篇
- **Phase 02**：用户已确认风格+标题+大纲
- **Phase 03**：`05-正文.md` 字数 1500-2500，无 Tier 1 禁用词
- **Phase 04**：用户已确认配图方案（或跳过）
- **Phase 05**：`index.html` 在浏览器中正常显示
