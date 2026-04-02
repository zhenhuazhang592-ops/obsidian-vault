# WeWrite Prompt 目录

> 来源：wewrite-main/SKILL.md 执行流程

本文档汇总 WeWrite 在 Claude Code 中的所有执行 Prompt 模板。

---

## 客户确认 Prompt

```
从用户消息中提取客户名称，读取配置：
读取: {skill_dir}/clients/{client}/style.yaml
```

---

## 热点抓取 Prompt

```bash
python3 {skill_dir}/scripts/fetch_hotspots.py --limit 30
```

---

## 选题生成 Prompt

**角色设定**：
```
你是一个公众号选题编辑。你的目标是从热点列表中挑出 10 个值得写的选题——既要有热度，又要跟客户定位匹配，还要有独特的切入角度。
```

**输入变量**：
- 热点列表（JSON）
- style.yaml 中的：topics、target_audience、blacklist、content_style
- history.yaml 中的：已发布文章的 topic_keywords 和 stats
- seo_keywords.py 输出：seo_score 和 related_keywords

**输出格式**：详见 [[选题评估规则]]

---

## 框架选择 Prompt

**角色设定**：
```
根据选题和客户风格，生成 5 套差异化写作框架供选择。每套框架是一个完整的文章骨架——不是写文章本身，而是告诉写作步骤"每一段写什么、怎么写"。
```

详见 [[写作框架库]]

---

## 文章写作 Prompt

**角色设定**：
```
你是这个公众号的主笔。你写的东西要像一个真人编辑写的——有观点、有个性、有瑕疵感。读者点开文章，应该觉得"这人挺懂的"，而不是"这是 AI 写的"。
```

**规则优先级**：
```
如果客户有 playbook.md，其中的规则覆盖本文件的通用规则。
playbook 是客户的个性化风格，本文件是通用底线。
```

详见 [[写作规范]]

---

## SEO 优化 Prompt

```
对初稿执行：
1. 生成 3 个备选标题（20-28 字），标注策略
2. 优化关键词密度
3. 去AI痕迹
4. 生成摘要（≤ 54 个中文字）
5. 推荐 5 个精准标签
6. 完读率优化
```

详见 [[SEO优化规则]]

---

## 视觉AI Prompt

详见 [[视觉AI模块]]

---

## 效果复盘 Prompt

**触发条件**：用户问"文章数据怎么样"、"效果复盘"、"看看表现"

```bash
python3 {skill_dir}/scripts/fetch_stats.py --client {client} --days 7
```

分析维度：
- 哪篇文章表现最好？为什么？
- 哪篇表现不好？可能的原因？
- 对后续选题/标题/框架的调整建议

---

## 客户 Onboard Prompt

**触发条件**：用户说"新建客户"、"导入历史文章"、"建 playbook"

### 1. 创建客户目录

```
{skill_dir}/clients/{client}/
├── style.yaml    # 复制 demo 模板，让用户填写
├── corpus/       # 用户放入历史推文 .md 文件
├── history.yaml  # 空初始化
└── lessons/      # 空目录
```

### 2. 生成 Playbook

```bash
python3 {skill_dir}/scripts/build_playbook.py --client {client}
```

### 3. 学习人工修改

```bash
python3 {skill_dir}/scripts/learn_edits.py --client {client} --draft {draft_path} --final {final_path}
```

---

## 编辑指令

| 指令 | 处理方式 |
|------|---------|
| 润色 | 优化用词和句式，保持内容不变 |
| 缩写 | 保留核心观点，压缩到指定字数 |
| 扩写 | 深化现有论点，扩展到指定字数 |
| 换语气 | 正式/口语/情绪三选一 |
| 换框架重写 | 回到 Step 4 |
| 换选题 | 回到 Step 3 |
