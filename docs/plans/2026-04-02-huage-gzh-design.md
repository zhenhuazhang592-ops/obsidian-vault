# 华哥公众号 · AI 写作智能体设计文档

> 版本：v1.0
> 日期：2026-04-02
> 状态：设计完成，待实现

---

## 一、系统定位

**名字**：华哥公众号（huage-gzh）

**一句话描述**：强制全链路公众号 AI 写作智能体，每次接收需求后自动完成深度研究 → 风格确认 → 批量标题大纲 → 正文写作（去AI味）→ 配图方案 → 封面生成 → HTML 排版预览。

**核心驱动模型**：Qwen3-Max（阿里通义千问，文章创作领域最优推理引擎）

---

## 二、技术架构

```
用户需求
    │
    ▼
┌─────────────────────────────────────────┐
│  Claude Code（工作流编排层）              │
│  - 控制流程节奏                         │
│  - 路由决策                            │
│  - 调用各 Phase Skill                  │
│  - 管理对话状态                         │
└─────────────────────────────────────────┘
    │
    ├──► Qwen3-Max API（核心推理引擎）     │
    │     - 研究分析                      │
    │     - 风格选择                      │
    │     - 标题大纲生成                  │
    │     - 正文写作 + 去AI味             │
    │     - 配图方案设计                  │
    │                                     │
    ├──► Tavily API（深度搜索）            │
    │     - 文章搜索                      │
    │     - 学术论文搜索                  │
    │                                     │
    ├──► YouTube Research Flow（视频研究）  │
    │                                     │
    ├──► Doubao-Seedream-4.5（图像生成）   │
    │     - 集成到 baoyu-image-gen         │
    │     - 封面生成                      │
    │     - 文章配图生成                  │
    │                                     │
    └──► baoyu-markdown-to-html（排版）    │
          - Markdown → 微信兼容 HTML       │
          - 浏览器预览                      │
```

---

## 三、核心决策

| 决策项  | 选择      | 原因                                  |
| ---- | ------- | ----------------------------------- |
| 研究模式 | 强制全链路   | 保证内容质量底线                            |
| 入库结构 | 按日期归档   | `写作知识库/01-资源库/[YYYY-MM-DD]/[文章标题]/` |
| 风格确认 | 预设风格库   | 华哥已有成熟风格体系                          |
| 确认流程 | 批量确认    | 效率与质量平衡                             |
| 配图流程 | 半自动     | 先展示方案，用户确认后再生成                      |
| 发布方式 | HTML 预览 | 用户自行复制到公众号后台                        |
| 研究深度 | 深度模式    | 10-20 篇，覆盖不同观点含反面                   |

---

## 四、七步核心流程

### Step 1：Tavily 深度研究

**触发**：用户输入创作需求

**执行**：
- 并行搜索文章 + 学术论文（10-20 篇）
- 覆盖不同观点，含反面证据
- 同步调用 Qwen3-Max 进行信息分析和摘要

**输出入库**：`写作知识库/01-资源库/[YYYY-MM-DD]/[文章标题]/`
```
00-研究索引.md        # 核心洞察摘要（Qwen3-Max 生成）
01-文章研究/          # 每篇一个 .md（来源/摘要/关键引用）
02-学术参考/         # 论文摘要和数据
```

---

### Step 2：YouTube 视频研究

**并行执行**：与 Step 1 同时进行，不阻塞

**执行**：`youtube-research-flow`
- YouTube Data API v3 搜索相关视频
- NotebookLM 整理分析
- 提取核心观点、视频笔记

**输出入库**：
```
02-视频研究/
  ├── 视频研究索引.md
  └── 视频N-标题.md
```

---

### Step 3：学习知识库内容

**触发**：Step 1 + Step 2 完成后

**执行**：Qwen3-Max 阅读整理后的研究内容
- 提取核心数据、关键引用
- 识别不同观点和立场
- 生成研究摘要供写作使用

---

### Step 4：风格 → 标题大纲（批量确认）

**第一轮确认：风格**
Qwen3-Max 输出 4 种预设风格，用户选一个：

| 风格 | 描述 |
|------|------|
| 亲和力强 | 口语化、情绪化、适度自嘲，第一人称"我" |
| 专业严谨 | 数据支撑、客观分析、逻辑严密、专业术语 |
| 幽默风趣 | 轻松调侃、生动比喻、口语化 |
| 极简干货 | 精炼直击要点、少修饰、强化逻辑结构 |

**第二轮确认：标题 + 大纲**
用户选定风格后，Qwen3-Max 一次性输出：
- 3 个标题选项（爆款类型：冲突对比/疑问引导/数字效果/否定反转）
- 完整大纲（H1 标题 / H2 核心论点 / H3 小节）

用户看完标题+大纲，一起确认。

---

### Step 5：正文写作

**驱动模型**：Qwen3-Max（核心推理引擎）

**写作规则**（基于现有去AI味文件，精炼整合）：

#### 必删词汇（Tier 1）
`首先、其次、再者、最后、总之、综上所述`、`值得注意的是、毋庸置疑、众所周知`、`非常重要、至关重要`、`作为一个、让我们`、`delve、leverage、robust、comprehensive`

#### 必添元素
- 口语化：`说实话、讲真、我跟你说、坦白讲、我觉得`
- 节奏变化：穿插1句话短段落，长短交替
- 主动语态优先
- 个人观点标记

#### 字数控制
- 目标：1500-2500 字
- 最少 1200，最多 3000

#### Markdown 格式
- H1：标题（converter 自动提取为微信标题字段）
- H2：核心论点
- H3：小节（克制使用，不滥用）
- 不用 `---` 分割线
- 图片用相对路径：`![描述](filename.jpg)`

---

### Step 6：配图（半自动）

**先展示方案**，Qwen3-Max 规划：
- 封面图 × 1（类型 + 风格 + 配色描述）
- 文章配图 × N（每张的位置、类型、风格描述）

用户确认方案后：
- 封面：`baoyu-cover-image` → Doubao-Seedream-4.5 生成
- 配图：`baoyu-article-illustrator` → Doubao-Seedream-4.5 生成

**Doubao-Seedream-4.5 集成到 baoyu-image-gen**：
- 在 `baoyu-image-gen` SKILL.md 中添加 Doubao-Seedream-4.5 作为新的 API 后端
- 模型标识：`doubao-seedream-4.5`
- 支持参考图 + 文本提示词

---

### Step 7：HTML 排版 + 预览

**执行**：`baoyu-markdown-to-html`
- 4 套主题可选：`default` / `grace` / `simple` / `modern`
- 输出微信兼容 HTML

**预览**：浏览器打开 HTML，用户确认效果后自行复制到公众号后台

---

## 五、Skill 文件结构

```
.claude/skills/huage-gzh/
├── SKILL.md                    # 主入口（触发词、流程编排、模型配置）
├── phases/
│   ├── 01-research.md          # 研究阶段（Tavily + YouTube 并行）
│   ├── 02-style-outline.md     # 风格确认 + 标题大纲生成
│   ├── 03-writing.md           # 正文写作（含去AI味完整规则）
│   ├── 04-images.md            # 配图方案 + 生成
│   └── 05-output.md           # 排版 + 预览
└── rules/
    └── anti-ai.md             # 去AI味规则（精炼自现有文件）
```

### SKILL.md 主入口结构

```yaml
name: huage-gzh
description: 公众号AI写作智能体 · 强制全链路研究 → 写作 → 配图 → 排版。核心推理：Qwen3-Max。触发词："写公众号"、"帮我写篇公众号文章"
```

### 核心提示词（SKILL.md 中嵌入）

```
## 角色定义
你是一个专业公众号内容创作者，由华哥公众号智能体驱动。
核心推理引擎：Qwen3-Max（通义千问 max 版，文章创作领域最优模型）
图像生成：Doubao-Seedream-4.5

## 底层编排逻辑
1. 接收用户需求 → 提取主题关键词
2. 并行启动：Tavily 研究 + YouTube 研究
3. 研究完成后 → 展示4种风格 → 用户选择
4. 用户选风格 → 一次性输出3个标题+大纲 → 用户确认
5. 用户确认 → Qwen3-Max 写正文（严格遵循去AI味规则）
6. 正文完成 → 展示配图方案 → 用户确认
7. 用户确认 → 生成封面+配图
8. 全部完成 → HTML排版 → 浏览器预览
```

---

## 六、模型集成细节

### Qwen3-Max 集成

**调用方式**：
```python
# 通过 DashScope API 调用 Qwen3-Max
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

response = client.chat.completions.create(
    model="qwen-max",
    messages=[
        {"role": "system", "content": "<Qwen3-Max 系统提示词>"},
        {"role": "user", "content": "<用户需求/写作指令>"}
    ],
    temperature=0.7,  # 创作场景适当随机性
    max_tokens=4096
)
```

**环境变量**：
- `DASHSCOPE_API_KEY`：阿里云 DashScope API Key

### Doubao-Seedream-4.5 集成到 baoyu-image-gen

**集成方式**：在 `baoyu-image-gen/SKILL.md` 中添加新的后端配置

**新增后端配置**：
```yaml
# 在 baoyu-image-gen/SKILL.md 中新增
doubao-seedream:
  model: Doubao-Seedream-4.5
  api_base: https://ark.cn-beijing.volces.com/api/v3
  supports_ref_img: true
  supports_aspect_ratio: true
  default_aspect: "16:9"
  strengths:
    - 中国风插画
    - 写实摄影风
    - 封面图
    - 知识科普图
```

**环境变量**：
- `ARK_API_KEY`：火山引擎 ARK API Key

---

## 七、去AI味规则（精炼版）

> 来源：`01-输出内容/公众号/工具研究/ArticleSkill/去AI化润色.md`
>        `01-输出内容/公众号/工具研究/avoid-ai-writing/SKILL.md`

### Tier 1 — 必删词汇

| 替换 | 原因 |
|------|------|
| 首先/其次/再者/最后 | AI机械化连接词 |
| 总之/综上所述/总而言之 | AI结尾套路 |
| 值得注意的是/应该说 | AI填充词 |
| 毋庸置疑/毫无疑问/众所周知 | AI虚假权威 |
| 非常重要/至关重要/不言而喻 | AI空洞形容 |
| 作为一个/让我们 | AI假协作口吻 |
| delve/leverage/robust/comprehensive | 英文AI高频词 |

### Tier 2 — 必添元素

| 元素 | 示例 |
|------|------|
| 口语化 | 说实话、讲真、我跟你说、坦白讲 |
| 个人观点 | 我觉得、据我观察、以我的经验 |
| 不完美感 | 或许、在多数情况下、一个不太精确但更生动的比喻 |

### Tier 3 — 节奏规则

- **段落长短交替**：穿插1句话短段落（语气强调/转折/吐槽）
- **长段落不超过150字**
- **禁止每段都是3-4句匀称结构**
- **禁止每段一样长**

### 段落节奏示例

```
一段80字的正常段落，说明论点。

但是。

这里其实有个问题很多人没注意到。（短段落，制造悬念）

接下来是一段120字的段落，展开说明那个问题是什么、
为什么重要、有什么数据支撑。

讲真，我第一次看到这个数据的时候也吓了一跳。（口语化短段落）
```

---

## 八、预设风格库

### 风格1：亲和力强

**特点**：第一人称"我"、情绪化表达、适度自嘲、口语化

**去AI味强度**：高
- 增加"说实话"、"这事儿"等口语
- 使用生动比喻
- 添加个人观点和吐槽
- 允许适度不完美感

### 风格2：专业严谨

**特点**：数据支撑、客观分析、逻辑严密、专业术语

**去AI味强度**：中
- 减少口语化，增强逻辑性
- 适度使用专业术语并解释
- 客观陈述，减少情绪化表达

### 风格3：幽默风趣

**特点**：轻松调侃、生动比喻、口语化

**去AI味强度**：高
- 增加"怎么说呢"、"直呼卧槽"等
- 使用生活化比喻
- 添加个人吐槽

### 风格4：极简干货

**特点**：精炼直击要点、少修饰、强化逻辑结构

**去AI味强度**：低
- 删除冗余表达
- 直击核心要点
- 减少形容词和修饰词
- 强化逻辑结构

---

## 九、输出结构（每篇文章文件夹）

```
写作知识库/01-资源库/YYYY-MM-DD/[文章标题]/
├── 00-研究索引.md           # 核心洞察摘要
├── 01-文章研究/
│   ├── 01-来源1.md
│   └── 02-来源2.md
├── 02-视频研究/
│   └── 视频研究索引.md
├── 03-学术参考/
│   └── 学术摘要.md
├── 04-风格与大纲.md         # 确认的风格 + 用户通过的标题大纲
├── 05-正文.md              # 写好的文章
├── 06-封面图/              # baoyu-cover-image 输出
├── 07-配图/                # baoyu-article-illustrator 输出
├── 08-排版预览/             # baoyu-markdown-to-html 输出
│   └── index.html
└── 09-元数据.yaml          # 创建时间/风格/字数/标签等
```

---

## 十、错误处理

| 场景 | 处理 |
|------|------|
| Tavily 搜索失败 | 回退到普通 WebSearch，告知用户研究深度降低 |
| YouTube API 失败 | 跳过视频研究，专注于文章研究，告知用户 |
| Qwen3-Max API 失败 | 报错退出，提示检查 API Key 配置 |
| Doubao-Seedream-4.5 失败 | 回退到 baoyu-image-gen 其他后端（OpenAI/Google） |
| 用户取消确认 | 停在当前步骤，等待用户新指令 |

---

## 十一、实现优先级

| 阶段 | 内容 | 依赖 |
|------|------|------|
| P0 | huage-gzh SKILL.md + phases/03-writing（核心写作） | Qwen3-Max API |
| P0 | 去AI味规则整合 | 现有文件已完备 |
| P1 | phases/01-research（Tavily + YouTube 研究） | Tavily API + YouTube API |
| P1 | Doubao-Seedream-4.5 集成到 baoyu-image-gen | ARK API Key |
| P2 | phases/02-style-outline（风格+标题大纲） | Qwen3-Max |
| P2 | phases/04-images（配图方案+生成） | baoyu-image-gen（含Doubao） |
| P3 | phases/05-output（HTML排版+预览） | baoyu-markdown-to-html |

---

## 十二、验证标准

- [x] Qwen3-Max 客户端正常调用（qwen_client.py，5个方法齐全，✅实际API调用成功）
- [x] 4种预设风格生成正常（Qwen3-Max generate_style_options 测试通过）
- [ ] 去AI味规则生效（待正文写作验证）
- [x] 配图方案能被用户理解并确认（phases/04-images.md 包含完整方案）
- [x] Doubao-Seedream-4.5 已集成到 baoyu-image-gen（✅实际图片生成成功，661KB）
- [x] HTML 预览流程完整（phases/05-output.md）
- [x] 完整流程端到端测试（Qwen3-Max ✅ + Doubao ✅）

### 实测记录（2026-04-02）

| 测试项 | 结果 | 备注 |
|--------|------|------|
| Qwen3-Max 初始化 | ✅ | DashScope API 正常 |
| generate_style_options() | ✅ | 4种风格输出正常 |
| Doubao-Seedream-4.5 生成 | ✅ | 661KB 图片生成成功 |
| 正确模型名 | `doubao-seedream-4-5-251128` | 原来写的是 `doubao-seedream-4.5`，已修正 |
| openai 包位置 | `/usr/bin/python3` | 树莓 3.14 无包，需用系统 Python |
