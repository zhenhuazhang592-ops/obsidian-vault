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

读取：`/Users/huage/Obsidian Vault/.claude/skills/huage-gzh/rules/anti-ai.md`，作为系统提示词的一部分。

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
